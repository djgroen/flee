from abc import ABCMeta
import enum
from inspect import isclass
import logging
import os
import pathlib
from datetime import date
from textwrap import indent
from typing import Any, Dict, List
from typing_extensions import Type

import yaml

from yatiml.exceptions import RecognitionError
from yatiml.helpers import Node, UnknownNode
from yatiml.introspection import class_subobjects
from yatiml.irecognizer import IRecognizer, RecError, RecResult, REC_OK
from yatiml.util import (
        bool_union_fix, cjoin, diagnose_missing_key, generic_type_args,
        is_abstract, is_generic_mapping, is_generic_sequence, is_generic_union,
        is_string_like, scalar_type_to_tag, type_to_desc)


logger = logging.getLogger(__name__)


class Recognizer(IRecognizer):
    """Functions for recognizing objects as types."""

    def __init__(
            self, registered_classes: Dict[str, Type],
            additional_classes: Dict[Type, str]) -> None:
        """Create a Recognizer.

        Args:
            registered_classes: The registered tags and corresponding
                    classes.
        """
        self.__registered_classes = registered_classes
        self.__additional_classes = additional_classes

    def __recognize_scalar(self, node: yaml.Node,
                           expected_type: Type) -> RecResult:
        """Recognize a node that we expect to be a scalar.

        Args:
            node: The node to recognize.
            expected_type: The type it is expected to be.

        Returns:
            A list of recognized types and an error message
        """
        logger.debug('Recognizing as a scalar')
        if (isinstance(node, yaml.ScalarNode)
                and node.tag == scalar_type_to_tag[expected_type]):
            return {expected_type}, REC_OK
        message = '{}\nExpected {}'.format(
            node.start_mark, type_to_desc(expected_type))
        return set(), (message, [])

    def __recognize_additional(
            self, node: yaml.Node, expected_type: Type) -> RecResult:
        """Recognize a node that we expect to be an additional type.

        Args:
            node: The node to recognize.
            expected_type: The type it is expected to be.

        Returns:
            A list of recognized types and an error message
        """
        logger.debug('Recognizing as an additional type')

        if expected_type == pathlib.Path:
            if (isinstance(node, yaml.ScalarNode)
                    and node.tag == 'tag:yaml.org,2002:str'):
                return {expected_type}, REC_OK

        message = '{}\nExpected {}'.format(
            node.start_mark, type_to_desc(expected_type))
        return set(), (message, [])

    def __recognize_list(self, node: yaml.Node,
                         expected_type: Type) -> RecResult:
        """Recognize a node that we expect to be a list of some kind.

        Args:
            node: The node to recognize.
            expected_type: List[...something...]

        Returns
            expected_type and an error message
        """
        logger.debug('Recognizing as a list')
        if not isinstance(node, yaml.SequenceNode):
            message = '{}\nExpected a list'.format(node.start_mark)
            return set(), (message, [])
        item_type = generic_type_args(expected_type)[0]
        for item in node.value:
            recognized_types, result = self.recognize(item, item_type)
            if len(recognized_types) == 0:
                message = '{}\nExpected {}'.format(
                        item.start_mark, type_to_desc(expected_type))
                return set(), (message, [result])
            if len(recognized_types) > 1:
                recognized_types = {
                    List[t]  # type: ignore
                    for t in recognized_types
                }
                return recognized_types, result

        return {expected_type}, REC_OK

    def __recognize_dict(self, node: yaml.Node,
                         expected_type: Type) -> RecResult:
        """Recognize a node that we expect to be a dict of some kind.

        Args:
            node: The node to recognize.
            expected_type: Dict[str, ...something...]

        Returns:
            expected_type if it was recognized, [] otherwise.
        """
        logger.debug('Recognizing as a dict')
        key_type = generic_type_args(expected_type)[0]
        if (
                not isclass(key_type)
                or not is_string_like(key_type)):
            raise RuntimeError(
                'YAtiML only supports dicts with strings as keys')
        if not isinstance(node, yaml.MappingNode):
            message = '{}\nExpected a dict/mapping here'.format(
                node.start_mark)
            return set(), (message, [])

        value_type = generic_type_args(expected_type)[1]
        for key, value in node.value:
            recognized_key_types, kresult = self.recognize(key, key_type)
            if len(recognized_key_types) == 0:
                return set(), kresult
            if len(recognized_key_types) > 1:
                return {
                    Dict[t, value_type]  # type: ignore
                    for t in recognized_key_types
                }, kresult  # type: ignore

            recognized_value_types, vresult = self.recognize(
                    value, value_type)
            if len(recognized_value_types) == 0:
                return set(), vresult
            if len(recognized_value_types) > 1:
                return {
                    Dict[key_type, t]  # type: ignore
                    for t in recognized_value_types
                }, vresult  # type: ignore

        return {expected_type}, REC_OK

    def __recognize_union(self, node: yaml.Node,
                          expected_type: Type) -> RecResult:
        """Recognize a node that we expect to be one of a union of types.

        Args:
            node: The node to recognize.
            expected_type: Union[...something...]

        Returns:
            The specific type that was recognized, multiple, or none.
        """
        logger.debug('Recognizing as a union')
        recognized_types = set()
        causes = []
        union_types = generic_type_args(expected_type)
        logger.debug('Union types {}'.format(union_types))
        for i, possible_type in enumerate(union_types):
            recognized_type, result = self.recognize(node, possible_type)
            if len(recognized_type) == 0:
                causes.append(result)
            recognized_types |= recognized_type
        if bool in recognized_types and bool_union_fix in recognized_types:
            recognized_types.remove(bool_union_fix)

        if len(recognized_types) == 0:
            message = (
                    '{}\nExpected one of the following types,'
                    ' but failed to match all of them:').format(
                            node.start_mark)
            return recognized_types, (message, causes)
        elif len(recognized_types) > 1:
            message = ('{}\nCould not determine which of the following types'
                       ' this is: {}').format(
                               node.start_mark,
                               cjoin('or', map(type_to_desc, recognized_types))
                               )
            return recognized_types, (message, causes)

        return recognized_types, REC_OK

    def __recognize_user_class(self, node: yaml.Node,
                               expected_type: Type) -> RecResult:
        """Recognize a user-defined class in the node.

        This tries to recognize only exactly the specified class. It
        recurses down into the class's attributes, but not to its
        subclasses. See also __recognize_user_classes().

        Args:
            node: The node to recognize.
            expected_type: A user-defined class.

        Returns:
            A list containing the user-defined class, or an empty list.
        """
        logger.debug('Recognizing as a user-defined class')
        loc_str = '{}\n'.format(node.start_mark)
        if '_yatiml_recognize' in expected_type.__dict__:
            try:
                unode = UnknownNode(self, node)
                expected_type._yatiml_recognize(unode)
                return {expected_type}, REC_OK

            except TypeError as e:
                raise RuntimeError(
                        '{}._yatiml_recognize() is of the wrong type.'
                        ' The correct type is _yatiml_recognize('
                        'cls, node: yatiml.UnknownNode) -> None.'
                        ' Or did you forget to make it a @classmethod?'.format(
                                expected_type.__name__)) from e

            except RecognitionError as e:
                if e.args:
                    message = '{}{}'.format(loc_str, e.args[0])
                else:
                    message = '{}Error recognizing {}'.format(
                        loc_str, type_to_desc(expected_type))
                return set(), (message, [])

        else:
            if issubclass(expected_type, enum.Enum):
                if (
                        not isinstance(node, yaml.ScalarNode)
                        or node.tag not in (
                            'tag:yaml.org,2002:str', 'tag:yaml.org,2002:bool')
                        ):
                    message = '{}Expected a string matching {}'.format(
                        loc_str, type_to_desc(expected_type))
                    return set(), (message, [])
                else:
                    # don't read this as a bool but as a string
                    node.tag = 'tag:yaml.org,2002:str'
            elif is_string_like(expected_type):
                if (not isinstance(node, yaml.ScalarNode)
                        or node.tag != 'tag:yaml.org,2002:str'):
                    message = '{}Expected a string matching {}'.format(
                        loc_str, type_to_desc(expected_type))
                    return set(), (message, [])
            else:
                # auto-recognize based on constructor signature
                if not isinstance(node, yaml.MappingNode):
                    req_attrs = [
                            '"{}"'.format(a)
                            for a, _, r in class_subobjects(expected_type)
                            if r]
                    message = (
                            '{}Expected a dict/mapping here with keys {}'
                            ).format(loc_str, cjoin('and', req_attrs))
                    return set(), (message, [])

                for attr_name, type_, required in class_subobjects(
                        expected_type):
                    cnode = Node(node)
                    # try exact match first, dashes if that doesn't match
                    for name in [attr_name, attr_name.replace('_', '-')]:
                        if cnode.has_attribute(name):
                            subnode = cnode.get_attribute(name)
                            recognized_types, result = self.recognize(
                                subnode.yaml_node, type_)
                            if len(recognized_types) == 0:
                                attr_key_node = [
                                    kn for kn, _ in node.value
                                    if kn.value == name][0]
                                loc_str = indent(
                                        str(attr_key_node.start_mark),
                                        '  ')
                                message = 'Error in attribute "{}"\n{}'.format(
                                                name, loc_str)
                                return set(), (message, [result])
                            break
                    else:
                        if required:
                            keys = [kn.value for kn, _ in node.value]
                            message = diagnose_missing_key(
                                    attr_name, keys, expected_type)
                            message = '{}{}'.format(loc_str, message)
                            return set(), (message, [])

            return {expected_type}, REC_OK

    def __recognize_user_classes(
            self, node: yaml.Node, expected_type: Type, top: bool = True
            ) -> RecResult:
        """Recognize a user-defined class in the node.

        This returns a list of classes from the inheritance hierarchy
        headed by expected_type which match the given node and which
        do not have a registered derived class that matches the given
        node. So, the returned classes are the most derived matching
        classes that inherit from expected_type.

        This function recurses down the user's inheritance hierarchy.

        Args:
            node: The node to recognize.
            expected_type: A user-defined class.
            top: Whether this is the topmost recursive call.

        Returns:
            A list containing matched user-defined classes.
        """
        logger.debug('Recognizing user class {}'.format(
            expected_type.__name__))
        recognized_subclasses = set()
        message = ''
        causes = []
        for other_class in self.__registered_classes.values():
            if expected_type in other_class.__bases__:
                sub_subclasses, result = self.__recognize_user_classes(
                    node, other_class, False)
                recognized_subclasses |= sub_subclasses
                if len(sub_subclasses) == 0:
                    causes.append(result)

        logger.debug('Recognized subclasses of {}: {}'.format(
                expected_type.__name__, recognized_subclasses))

        if len(recognized_subclasses) == 0:
            if not is_abstract(expected_type):
                recognized_subclasses, result = self.__recognize_user_class(
                    node, expected_type)
                if len(recognized_subclasses) == 0:
                    causes.append(result)
            else:
                logger.debug('Not considering {} as it is abstract'.format(
                        expected_type.__name__))

        if len(recognized_subclasses) == 0:
            message = 'Failed to recognize {}'.format(
                    type_to_desc(expected_type))
            if top:
                message += '\n{}'.format(indent(str(node.start_mark), '  '))
            return set(), (message, causes)

        if len(recognized_subclasses) > 1:
            # Let the user disambiguate with an explicit tag
            if node.tag in self.__registered_classes:
                typ = self.__registered_classes[node.tag]
                if typ in recognized_subclasses:
                    return {typ}, REC_OK

            message = ('Could not determine which of the following types'
                       ' this is: {}').format(cjoin(
                           'or', map(type_to_desc, recognized_subclasses)))
            return recognized_subclasses, (message, causes)

        # Tags that don't match with what we recognized are an error,
        # because silently ignoring the conflict would get confusing.
        if not node.tag.startswith('tag:yaml.org,2002'):
            if node.tag in self.__registered_classes:
                tagged_class = self.__registered_classes[node.tag]
                if tagged_class not in recognized_subclasses:
                    message = ('{}\nExpected a {} and found it, but there\'s'
                               ' a tag here claiming this is a(n) {}. That'
                               ' makes no sense.').format(
                                       node.start_mark, expected_type.__name__,
                                       tagged_class.__name__)
                    logger.debug(message)
                    return set(), (message, [])
            else:
                message = ('{}\nExpected a {} and found it, but there\'s'
                           ' a tag here claiming this is a(n) {}, which type'
                           ' I don\'t know.').format(
                                   node.start_mark,
                                   expected_type.__name__, node.tag[1:])
                logger.debug(message)
                return set(), (message, [])

        return recognized_subclasses, REC_OK

    def recognize(self, node: yaml.Node, expected_type: Type) -> RecResult:
        """Figure out how to interpret this node.

        This is not quite a type check. This function makes a list of
        all types that match the expected type and also the node, and
        returns that list. The goal here is not to test validity, but
        to determine how to process this node further.

        That said, it will recognize built-in types only in case of
        an exact match.

        Args:
            node: The YAML node to recognize.
            expected_type: The type we expect this node to be, based
                    on the context provided by our type definitions.

        Returns:
            A list of matching types.
        """
        logger.debug('Recognizing {} as a {}'.format(node, expected_type))
        recognized_types = None     # type: Any
        if expected_type in (
                str, int, float, bool, bool_union_fix, date, None,
                type(None)):
            recognized_types, result = self.__recognize_scalar(
                    node, expected_type)
        elif expected_type in self.__additional_classes:
            recognized_types, result = self.__recognize_additional(
                    node, expected_type)
        elif is_generic_union(expected_type):
            recognized_types, result = self.__recognize_union(
                     node, expected_type)
        elif is_generic_sequence(expected_type):
            recognized_types, result = self.__recognize_list(
                    node, expected_type)
        elif is_generic_mapping(expected_type):
            recognized_types, result = self.__recognize_dict(
                    node, expected_type)
        elif expected_type in self.__registered_classes.values():
            recognized_types, result = self.__recognize_user_classes(
                    node, expected_type)
        elif expected_type in (Any,):
            recognized_types, result = [Any], REC_OK

        if recognized_types is None:
            raise RecognitionError(
                ('Could not recognize for type {},'
                 ' is it registered?').format(expected_type.__name__))
        logger.debug('Recognized types {} matching {}'.format(
            recognized_types, expected_type))
        return recognized_types, result
