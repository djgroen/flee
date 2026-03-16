import inspect
import logging
import os
import pathlib
import traceback
from collections import OrderedDict
from typing import Dict, Any, Generator, List, Union
from typing_extensions import TYPE_CHECKING, Type

import yaml

from yatiml.exceptions import RecognitionError
from yatiml.introspection import class_subobjects
from yatiml.util import (
        bool_union_fix, diagnose_extraneous_key, diagnose_missing_key,
        generic_type_args, is_generic_sequence, is_generic_mapping,
        is_generic_union, strip_tags, type_to_desc)

if TYPE_CHECKING:
    from yatiml.loader import Loader  # noqa: F401

logger = logging.getLogger(__name__)


class Constructor:
    """A constructor for user classes to register with YAML."""

    def __init__(self, class_: Type) -> None:
        """Create a constructor

        Args:
            class_: The class that this is a constructor for.
        """
        self.class_ = class_

    def __call__(self, loader: 'Loader',
                 node: yaml.Node) -> Generator[Any, None, None]:
        """Construct an object from a yaml node.

        This constructs an object of the user-defined type that this
        is the constructor for. It is registered with the yaml library,
        and called by it. Recursion is handled by calling the yaml
        library, so we only need to construct an object using the keys
        and values of the given MappingNode, and those values have been
        converted recursively for us.

        Since Python does not do type checks, we do a type check
        manually, to ensure that the class's constructor gets the types
        it expects. This avoids confusing errors, but moreover is a
        security feature that ensures that regardless of the content
        of the YAML file, we produce the objects that the programmer
        defined and expects.

        Note that this yields rather than returns, in a somewhat odd
        way. That's directly from the PyYAML documentation.

        Args:
            loader: The yatiml.loader that is creating this object.
            node: The node to construct from.

        Yields:
            The incomplete constructed object.
        """
        logger.debug('Constructing an object of type {}'.format(
            self.class_.__name__))
        if not isinstance(node, yaml.MappingNode):
            raise RecognitionError((
                    'An error occurred:\n{}\nExpected a MappingNode. There'
                    ' is probably something wrong with your _yatiml_savorize()'
                    ' function.').format(node.start_mark))

        self.__loader = loader

        # figure out which keys are extra and strip them of tags
        # to prevent constructing objects we haven't type checked
        argspec = inspect.getfullargspec(self.class_.__init__)
        self.__strip_extra_attributes(node, argspec.args)

        # create object and let yaml lib construct subobjects
        new_obj = self.class_.__new__(self.class_)  # type: ignore
        yield new_obj
        mapping = loader.construct_mapping(node, deep=True)

        # do type check
        try:
            self.__check_no_missing_attributes(node, mapping)
            self.__type_check_attributes(node, mapping, argspec)
        except RecognitionError as e:
            raise RecognitionError('An error occurred:\n{}'.format(e))

        # construct object, this should work now
        try:
            logger.debug('Calling __init__')
            if '_yatiml_extra' in argspec.args:
                attrs = self.__split_off_extra_attributes(
                    mapping, argspec.args)
                new_obj.__init__(**attrs)

            else:
                new_obj.__init__(**mapping)

        except Exception as e:
            raise RecognitionError(
                    'An error occurred:\n{}\n{}'.format(node.start_mark, e))
        logger.debug('Done constructing {}'.format(self.class_.__name__))

    def __split_off_extra_attributes(self, mapping: Dict,
                                     known_attrs: List[str]) -> Dict:
        """Separates the extra attributes in mapping into _yatiml_extra.

        This returns a mapping containing all key-value pairs from
        mapping whose key is in known_attrs, and an additional key
        _yatiml_extra which maps to a dict containing the remaining
        key-value pairs.

        Args:
            mapping: The mapping to split
            known_attrs: Attributes that should be kept in the main
                    map, and not moved to _yatiml_extra.

        Returns:
            A map with attributes reorganised as described above.
        """
        attr_names = list(mapping.keys())
        main_attrs = mapping.copy()
        extra_attrs = OrderedDict(mapping.items())
        for name in attr_names:
            if name not in known_attrs or name == '_yatiml_extra':
                del (main_attrs[name])
            else:
                del (extra_attrs[name])
        main_attrs['_yatiml_extra'] = extra_attrs
        return main_attrs

    def __type_matches(self, obj: Any, type_: Type) -> bool:
        """Checks that the object matches the given type.

        Like isinstance(), but will work with union types using Union,
        Dict and List.

        Args:
            obj: The object to check
            type_: The type to check against

        Returns:
            True iff obj is of type type_
        """
        if is_generic_union(type_):
            for t in generic_type_args(type_):
                if self.__type_matches(obj, t):
                    return True
            return False
        elif is_generic_sequence(type_):
            if not isinstance(obj, list):
                return False
            for item in obj:
                if not self.__type_matches(item, generic_type_args(type_)[0]):
                    return False
            return True
        elif is_generic_mapping(type_):
            if not isinstance(obj, dict):
                return False
            for key, value in obj.items():
                if not isinstance(key, generic_type_args(type_)[0]):
                    return False
                if not self.__type_matches(value, generic_type_args(type_)[1]):
                    return False
            return True
        elif type_ is bool_union_fix:
            return isinstance(obj, bool)
        elif type_ is Any:
            return True
        else:
            return isinstance(obj, type_)

    def __check_no_missing_attributes(self, node: yaml.MappingNode,
                                      mapping: Dict) -> None:
        """Checks that all required attributes are present.

        Also checks that they're of the correct type.

        Args:
            node: The node we're constructing an object from.
            mapping: The mapping with subobjects of this object.

        Raises:
            RecognitionError: if an attribute is missing or the type
                is incorrect.
        """
        logger.debug('Checking presence of required attributes')
        for name, type_, required in class_subobjects(self.class_):
            if required and name not in mapping:
                got = [kn.value for kn, _ in node.value]
                msg = diagnose_missing_key(name, got, self.class_)
                raise RecognitionError('{}\n{}'.format(node.start_mark, msg))
            if name in mapping and not self.__type_matches(
                    mapping[name], type_):
                raise RecognitionError(
                        '{}\nAttribute "{}" is {}, expected {}'.format(
                            node.start_mark, name,
                            type_to_desc(type(mapping[name])),
                            type_to_desc(type_)))

    def __type_check_attributes(self, node: yaml.Node, mapping: Dict,
                                argspec: inspect.FullArgSpec) -> None:
        """Ensure all attributes have a matching constructor argument.

        This checks that there is a constructor argument with a
        matching type for each existing attribute.

        If the class has a _yatiml_extra attribute, then extra
        attributes are okay and no error will be raised if they exist.

        Args:
            node: The node we're processing
            mapping: The mapping with constructed subobjects
            constructor_attrs: The attributes of the constructor,
                    including self and _yatiml_extra, if applicable
        """
        logger.debug('Checking for extraneous attributes')
        logger.debug('Constructor arguments: {}, mapping: {}'.format(
            argspec.args, list(mapping.keys())))
        for key, value in mapping.items():
            if not isinstance(key, str):
                raise RecognitionError(
                        '{}\nExpected a string'.format(node.start_mark))
            if key not in argspec.args and '_yatiml_extra' not in argspec.args:
                key_node = [kn for kn, _ in node.value if kn.value == key][0]
                msg = diagnose_extraneous_key(
                        key, list(mapping.keys()), self.class_)
                raise RecognitionError(
                        '{}\n{}'.format(key_node.start_mark, msg))

            if key in argspec.args and key in argspec.annotations:
                if not self.__type_matches(value, argspec.annotations[key]):
                    value_node = [
                            vn for kn, vn in node.value if kn.value == key][0]
                    raise RecognitionError((
                            '{}\nExpected attribute "{}" to be {} but it is {}'
                            ).format(
                                    value_node.start_mark, key,
                                    type_to_desc(argspec.annotations[key]),
                                    type_to_desc(type(value))))

    def __strip_extra_attributes(self, node: yaml.Node,
                                 known_attrs: List[str]) -> None:
        """Strips tags from extra attributes.

        This prevents nodes under attributes that are not part of our
        data model from being converted to objects. They'll be plain
        CommentedMaps instead, which then get converted to OrderedDicts
        for the user.

        Args:
            node: The node to process
            known_attrs: The attributes to not strip
        """
        known_keys = list(known_attrs)
        if 'self' not in known_keys:
            raise RuntimeError('The __init__ method of {} does not have a'
                               ' "self" attribute! Please add one, this is'
                               ' not a valid constructor.'.format(
                                   self.class_.__name__))
        known_keys.remove('self')
        if '_yatiml_extra' in known_keys:
            known_keys.remove('_yatiml_extra')

        for key_node, value_node in node.value:
            if (not isinstance(key_node, yaml.ScalarNode)
                    or key_node.tag != 'tag:yaml.org,2002:str'):
                raise RecognitionError(
                    '{}\nExpected a string here.'.format(node.start_mark))
            if key_node.value not in known_keys:
                strip_tags(self.__loader, value_node)


class EnumConstructor:
    """A constructor for user enum classes to register with YAML.

    This constructor should be used in place of Constructor for enums,
    i.e. classes derived from enum.Enum.
    """

    def __init__(self, class_: Type) -> None:
        """Create a constructor

        Args:
            class_: The class that this is a constructor for.
        """
        self.class_ = class_

    def __call__(self, loader: 'Loader',
                 node: yaml.Node) -> Generator[Any, None, None]:
        """Construct an enum value from a yaml node.

        This constructs an object of the user-defined enum that this
        is the constructor for. It is registered with the yaml library,
        and called by it.

        Note that this yields rather than returns, in a somewhat odd
        way. That's directly from the PyYAML documentation.

        Args:
            loader: The yatiml.loader that is creating this object.
            node: The node to construct from.

        Yields:
            The incomplete constructed object.
        """
        logger.debug('Constructing an object of type {}'.format(
            self.class_.__name__))

        msg = (
                'An error occurred:\n{}\nExpected a string matching {}.'
                ).format(node.start_mark, type_to_desc(self.class_))

        if (
                not isinstance(node, yaml.ScalarNode) or
                not isinstance(node.value, str)):
            raise RecognitionError(msg)

        # PyYAML expects us to yield an incomplete object, but enums are
        # immutable, so we'll have to make the whole thing right away.
        try:
            new_obj = self.class_[node.value]
        except KeyError:
            raise RecognitionError(msg)
        yield new_obj


class UserStringConstructor:
    """A constructor for user-defined string classes to register with YAML.

    This constructor should be used in place of Constructor for
    user-defined strings, i.e. classes derived from str or
    collections.UserString.
    """

    def __init__(self, class_: Type) -> None:
        """Create a constructor

        Args:
            class_: The class that this is a constructor for.
        """
        self.class_ = class_

    def __call__(self, loader: 'Loader',
                 node: yaml.Node) -> Generator[Any, None, None]:
        """Construct an user string value from a yaml node.

        This constructs an object of the user-defined string class that
        this is the constructor for. It is registered with the yaml
        library, and called by it.

        Note that this yields rather than returns, in a somewhat odd
        way. That's directly from the PyYAML documentation.

        Args:
            loader: The yatiml.loader that is creating this object.
            node: The node to construct from.

        Yields:
            The incomplete constructed object.
        """
        logger.debug('Constructing an object of type {}'.format(
            self.class_.__name__))

        if not isinstance(node, yaml.ScalarNode) or not isinstance(
                node.value, str):
            raise RecognitionError(
                ('{}\nExpected a string matching {}.').format(
                    node.start_mark, type_to_desc(self.class_)))

        # PyYAML expects us to yield an incomplete object, but strings are
        # immutable, so we'll have to make the whole thing right away.
        try:
            new_obj = self.class_(node.value)
        except Exception as e:
            raise RecognitionError(
                    'An error occurred:\n{}\n{}'.format(node.start_mark, e))
        yield new_obj


class PathConstructor:
    """A constructor for pathlib.Path objects.

    This constructor expects a string and produces a Path object.
    """

    def __call__(
            self, loader: 'Loader', node: yaml.Node
            ) -> Generator[Any, None, None]:
        """Construct a Path object from a yaml node.

        This expects the node to contain a string with the path.

        Args:
            loader: The yatiml.loader that is creating this object.
            node: The node to construct from.

        Yields:
            The incomplete constructed object.
        """
        logger.debug('Constructing an object of type pathlib.Path')

        if not isinstance(node, yaml.ScalarNode) or not isinstance(
                node.value, str):
            raise RecognitionError(
                    ('{}\nExpected a string containing a Path.').format(
                        node.start_mark))

        # PyYAML expects us to yield an incomplete object, but Paths are
        # special, so we'll have to make the whole thing right away.
        new_obj = pathlib.Path(node.value)
        yield new_obj
