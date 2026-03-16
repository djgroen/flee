import enum
import logging
import os
from pathlib import Path
import re
from typing import (
        Any, AnyStr, Callable, cast, Dict, IO, List, overload, TypeVar, Union
        )  # noqa
from typing_extensions import ClassVar, Type    # noqa

import yaml

from yatiml.constructors import (
        Constructor, EnumConstructor, PathConstructor, UserStringConstructor)
from yatiml.exceptions import RecognitionError, SeasoningError
from yatiml.helpers import Node
from yatiml.introspection import class_subobjects
from yatiml.irecognizer import format_rec_error
from yatiml.recognizer import Recognizer
from yatiml.util import (
        generic_type_args, is_generic_sequence, is_generic_mapping,
        is_generic_union, is_string_like, scalar_type_to_tag, strip_tags,
        type_to_desc)

logger = logging.getLogger(__name__)


class Loader(yaml.SafeLoader):
    """The YAtiML Loader class.

    Derive your own Loader class from this one, then add classes to it
    using :func:`add_to_loader`.

    .. warning::

        This class is **deprecated**, and will be removed in a
        future version. You should use :meth:`load_function`
        instead.
    """
    _registered_classes = None      # type: ClassVar[Dict[str, Type]]
    _additional_classes = None      # type: ClassVar[Dict[Type, str]]
    document_type = type(None)      # type: ClassVar[Type]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a Loader."""
        super().__init__(*args, **kwargs)

        self.__patch_floats()
        self.__patch_bools()
        self.__recognizer = Recognizer(
                self._registered_classes, self._additional_classes)

    def get_single_node(self) -> yaml.Node:
        """Hook used when loading a single document.

        This is the hook we use to hook yatiml into PyYAML. It is
        called by the yaml library when the user uses load() to load a
        YAML document.

        Returns:
            A processed node representing the document.
        """
        node = cast(yaml.Node, super().get_single_node())
        if node is not None:
            node = self.__process_node(node, type(self).document_type)
        return node

    def get_node(self) -> yaml.Node:
        """Hook used when reading a multi-document stream.

        This is the hook we use to hook yatiml into PyYAML. It is
        called by the yaml library when the user uses load_all() to
        load multiple documents from a stream.

        Returns:
            A processed node representing the document.
        """
        node = cast(yaml.Node, super().get_node())
        if node is not None:
            node = self.__process_node(node, type(self).document_type)
        return node

    def __type_to_tag(self, type_: Type) -> str:
        """Convert a type to the corresponding YAML tag.

        Args:
            type_: The type to convert

        Returns:
            A string containing the YAML tag.
        """
        if type_ in scalar_type_to_tag:
            return scalar_type_to_tag[type_]

        if is_generic_sequence(type_):
            return 'tag:yaml.org,2002:seq'

        if is_generic_mapping(type_):
            return 'tag:yaml.org,2002:map'

        if type_ in self._registered_classes.values():
            return '!{}'.format(type_.__name__)

        if type_ in self._additional_classes:
            return self._additional_classes[type_]

        raise RuntimeError((
            'Unknown type {} in type_to_tag,'  # pragma: no cover
            ' please report a YAtiML bug.').format(type_))

    def __savorize(self, node: yaml.Node, expected_type: Type) -> yaml.Node:
        """Removes syntactic sugar from the node.

        This calls _yatiml_savorize(), first on the class's base
        classes, then on the class itself.

        Args:
            node: The node to modify.
            expected_type: The type to assume this type is.
        """
        logger.debug('Savorizing node assuming type {}'.format(
            expected_type.__name__))

        for base_class in expected_type.__bases__:
            if base_class in self._registered_classes.values():
                node = self.__savorize(node, base_class)

        if '_yatiml_savorize' in expected_type.__dict__:
            logger.debug('Calling {}._yatiml_savorize()'.format(
                expected_type.__name__))
            cnode = Node(node)
            expected_type._yatiml_savorize(cnode)
            node = cnode.yaml_node
        return node

    def __process_node(self, node: yaml.Node,
                       expected_type: Type) -> yaml.Node:
        """Processes a node.

        This is the main function that implements yatiml's
        functionality. It figures out how to interpret this node
        (recognition), then applies syntactic sugar, and finally
        recurses to the subnodes, if any.

        Args:
            node: The node to process.
            expected_type: The type we expect this node to be.

        Returns:
            The transformed node, or a transformed copy.
        """
        logger.info('Processing node {} expecting type {}'.format(
            node, expected_type))

        # figure out how to interpret this node
        recognized_types, result = self.__recognizer.recognize(
            node, expected_type)

        if len(recognized_types) != 1:
            raise RecognitionError(format_rec_error(result))

        recognized_type = next(iter(recognized_types))

        # remove syntactic sugar
        logger.debug('Savorizing node {}'.format(node))
        if recognized_type in self._registered_classes.values():
            try:
                node = self.__savorize(node, recognized_type)
            except SeasoningError as e:
                raise RecognitionError(
                        '{}\n{}'.format(node.start_mark, e.args[0]))
        logger.debug('Savorized, now {}'.format(node))

        # process subnodes
        logger.debug('Recursing into subnodes')
        if is_generic_sequence(recognized_type):
            if node.tag != 'tag:yaml.org,2002:seq':
                raise RecognitionError('{}\nExpected {} here'.format(
                    node.start_mark,
                    type_to_desc(expected_type)))
            node.value = [
                    self.__process_node(
                        item, generic_type_args(recognized_type)[0])
                    for item in node.value]

        elif is_generic_mapping(recognized_type):
            if node.tag != 'tag:yaml.org,2002:map':
                raise RecognitionError('{}\nExpected {} here'.format(
                    node.start_mark, type_to_desc(expected_type)))
            node.value = [(
                    self.__process_node(
                        key_node, generic_type_args(recognized_type)[0]),
                    self.__process_node(
                        value_node, generic_type_args(recognized_type)[1]))
                    for key_node, value_node in node.value]

        elif recognized_type in self._registered_classes.values():
            if (not issubclass(recognized_type, enum.Enum)
                    and not is_string_like(recognized_type)):
                for attr_name, type_, _ in class_subobjects(recognized_type):
                    cnode = Node(node)
                    if cnode.has_attribute(attr_name):
                        subnode = cnode.get_attribute(attr_name)
                        new_subnode = self.__process_node(
                            subnode.yaml_node, type_)
                        cnode.set_attribute(attr_name, new_subnode)
        else:
            logger.debug('Not a generic class or a user-defined class, not'
                         ' recursing')

        if recognized_type is Any:
            strip_tags(self, node)
        else:
            node.tag = self.__type_to_tag(recognized_type)
        logger.debug('Finished processing node {}'.format(node))
        return node

    def __patch_floats(self) -> None:
        """Make floats be parsed as YAML 1.2 floats.

        YAML 1.1 has some really weird ideas on what a float is. This
        was fixed in YAML 1.2, which ruamel.yaml parses by default.
        However, we switched to PyYAML, which is still on YAML 1.1, so
        that we're now stuck with weird that weird float format. This
        function patches PyYAMLs resolvers to replace the YAML 1.1
        float format with the YAML 1.2 float format. That means we're
        now accepting a mix of YAML 1.1 and YAML 1.2, but so be it.
        The YAML mess isn't really fixable anyway.
        """
        yaml12_float_regex = re.compile(
                r'^(?:'
                # sign
                r'[-+]?'
                # content
                r'(?:'
                # float numbers
                r'  (?:[0-9]+[eE][-+]?[0-9]+'
                r'  |[0-9]+\.([eE][-+]?[0-9]+)?'
                r'  |[0-9]*\.[0-9]+([eE][-+]?[0-9]+)?'
                r'  )'
                # infinity
                r'|\.(?:inf|Inf|INF)'
                # not a number
                r'|\.(?:nan|NaN|NAN)'
                r'))', re.X)

        new_implicit_resolvers = dict()

        for first, resolvers in self.yaml_implicit_resolvers.items():
            new_resolvers = []
            for tag, regex in resolvers:
                if tag == 'tag:yaml.org,2002:float':
                    new_resolvers.append((tag, yaml12_float_regex))
                else:
                    new_resolvers.append((tag, regex))
            new_implicit_resolvers[first] = new_resolvers

        self.yaml_implicit_resolvers = new_implicit_resolvers

    def __patch_bools(self) -> None:
        """Make booleans be parsed as YAML 1.2 bools.

        YAML 1.1 recognises a whole list of words as booleans,
        including yes, no, y, n, on, off, false, true with
        different capitalisations. That can get confusing
        because who else interprets 'on' as a boolean? This got
        fixed in YAML 1.2, which only does a few versions of
        true and false.

        This patches PyYAMLs resolvers to replace YAML 1.1 bools
        with YAML 1.2 bools.
        """
        yaml12_bool_regex = re.compile(
                r'^(?:true|True|TRUE|false|False|FALSE)', re.X)

        new_implicit_resolvers = dict()

        for first, resolvers in self.yaml_implicit_resolvers.items():
            new_resolvers = []
            for tag, regex in resolvers:
                if tag == 'tag:yaml.org,2002:bool':
                    if first in 'tTfF':
                        new_resolvers.append((tag, yaml12_bool_regex))
                else:
                    new_resolvers.append((tag, regex))

            if new_resolvers:
                new_implicit_resolvers[first] = new_resolvers

        self.yaml_implicit_resolvers = new_implicit_resolvers


def set_document_type(loader_cls: Type, type_: Type) -> None:
    """Set the type corresponding to the whole document.

    Args:
        loader_cls: The loader class to set the document type for.
        type_: The type to loader should process the document into.

    .. warning::

        This function is **deprecated**, and will be removed in a
        future version. You should use :meth:`load_function` instead.
    """
    loader_cls.document_type = type_

    if loader_cls._registered_classes is None:
        loader_cls._registered_classes = dict()


# Python errors if we define classes as Union[List[Type], Type]
# So List[Type] it is, and if the user ignores that and passes
# a single class, it'll work anyway, with a little mypy override.
def add_to_loader(loader_cls: Type, classes: List[Type]) -> None:
    """Registers one or more classes with a YAtiML loader.

    Once a class has been registered, it can be recognized and
    constructed when reading a YAML text.

    Args:
        loader_cls: The loader to register the classes with.
        classes: The class(es) to register, a plain Python class or a
                list of them.

    .. warning::

        This function is **deprecated**, and will be removed in a
        future version. You should use :meth:`load_function` instead.
    """
    if not isinstance(classes, list):
        classes = [classes]  # type: ignore

    for class_ in classes:
        tag = '!{}'.format(class_.__name__)
        if issubclass(class_, enum.Enum):
            loader_cls.add_constructor(tag, EnumConstructor(class_))
        elif is_string_like(class_):
            loader_cls.add_constructor(tag, UserStringConstructor(class_))
        else:
            loader_cls.add_constructor(tag, Constructor(class_))

        if loader_cls._registered_classes is None:
            loader_cls._registered_classes = dict()
        loader_cls._registered_classes[tag] = class_


class _AnyYAML:
    """Dummy class for load_function default value."""


T = TypeVar('T')


# https://github.com/python/mypy/issues/3737
@overload
def load_function() -> Callable[[Union[str, Path, IO[AnyStr]]], Any]: ...


@overload
def load_function(
        result: Type[T], *args: Type
        ) -> Callable[[Union[str, Path, IO[AnyStr]]], T]: ...


def load_function(result=_AnyYAML, *args):     # type: ignore
    """Create a load function for the given type.

    This function returns a callable object which takes an input
    (``str`` with YAML input, ``pathlib.Path``, or an open stream) and
    tries to load an object of the type given as the first argument.
    Any user-defined classes needed by the result must be passed as
    the remaining arguments.

    Note that mypy will give an error if you try to pass some of the
    special type-like objects from ``typing``. ``typing.Dict`` and
    ``typing.List`` seem to be okay, but ``typing.Union``,
    ``typing.Optional``, and abstract containers
    ``typing.Sequence``, ``typing.Mapping``,
    ``typing.MutableSequence`` and ``typing.MutableMapping`` will
    give an error. They are supported however, and work fine,
    there is just no way presently to explain to mypy that they
    are okay.

    So, if you want to tell YAtiML that your YAML file may contain
    either a string or an int, you can use ``Union[str, int]`` for the
    first argument, but you'll have to add a ``# type: ignore`` or two
    to tell mypy to ignore the issue. The resulting Callable will have
    return type ``Any`` in this case.

    Examples:

        .. code-block:: python

          load_int_dict = yatiml.load_function(Dict[str, int])
          my_dict = load_int_dict('x: 1')

        .. code-block:: python

          load_config = yatiml.load_function(Config, Setting)
          my_config = load_config(Path('config.yaml'))

          # or

          with open('config.yaml', 'r') as f:
              my_config = load_config(f)

        Here, ``Config`` is the top-level class, and ``Setting`` is
        another class that is used by ``Config`` somewhere.

        .. code-block:: python

          # Needs an ignore, on each line if split over two lines
          load_int_or_str = yatiml.load_function(     # type: ignore
                  Union[int, str])                    # type: ignore

    Args:
        result: The top level type, return type of the function.
        *args: Any other (custom) types needed.

    Returns:
        A function that can load YAML input from a string, Path or
        stream and convert it to an object of the first type given.
    """
    class UserLoader(Loader):
        pass

    # add loaders for additional types
    if UserLoader._additional_classes is None:
        UserLoader._additional_classes = dict()
    UserLoader.add_constructor('!Path', PathConstructor())
    UserLoader._additional_classes[Path] = '!Path'

    additional_types = (Path,)

    # add loaders for user types
    user_classes = list(args)
    if not (
            is_generic_mapping(result) or
            is_generic_sequence(result) or
            is_generic_union(result) or
            result is Any):
        if result not in additional_types and result not in user_classes:
            user_classes.append(result)

    add_to_loader(UserLoader, user_classes)
    if result is _AnyYAML:
        set_document_type(UserLoader, Any)      # type: ignore
    else:
        set_document_type(UserLoader, result)

    class LoadFunction:
        """Validates YAML input and constructs objects."""
        def __init__(self, loader: Type[Loader]) -> None:
            """Create a LoadFunction."""
            self.loader = loader

        def __call__(
                self, source: Union[str, Path, IO[AnyStr]]
                ) -> T:  # type: ignore
            """Load a YAML document from a source.

            The source can be a string containing YAML, a pathlib.Path
            containing a path to a file to load, or a stream (e.g. an
            open file handle returned by open()).

            Args:
                source: The source to load from.

            Returns:
                An object loaded from the file.

            Raises:
                yatiml.RecognitionError: If the input is invalid.
            """

            if isinstance(source, Path):
                with source.open('r') as f:
                    return cast(T, yaml.load(f, Loader=self.loader))
            else:
                return cast(T, yaml.load(source, Loader=self.loader))

    return LoadFunction(UserLoader)
