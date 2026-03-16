from collections import OrderedDict
import inspect
import logging
import pathlib
from typing import Any, cast
from typing_extensions import TYPE_CHECKING, Type

import yaml

from yatiml.helpers import Node

if TYPE_CHECKING:
    from yatiml.dumper import Dumper  # noqa: F401

logger = logging.getLogger(__name__)


class Representer:
    """A yaml Representer class for user-defined types.

    For PyYAML to dump a class correctly, it needs a representer
    function for that class. YAtiML provides this generic representer
    which represents classes based on their public attributes by
    default, with an optional user override using a member function.
    """

    def __init__(self, class_: Type) -> None:
        """Creates a new Representer for the given class.

        Args:
            class_: The class to represent.
        """
        self.class_ = class_

    def __call__(self, dumper: 'Dumper', data: Any) -> yaml.Node:
        """Represents the class as a MappingNode.

        Args:
            dumper: The dumper to use.
            data: The user-defined object to dump.

        Returns:
            A yaml.Node representing the object.
        """
        # make a dict with attributes
        logger.info('Representing {} of class {}'.format(
            data, self.class_.__name__))
        if hasattr(data, '_yatiml_attributes'):
            logger.debug('Found _yatiml_attributes()')
            attributes = data._yatiml_attributes()
            if attributes is None:
                raise RuntimeError(('{}._yatiml_attributes() returned None,'
                                    ' where a dict was expected.').format(
                                        self.class_.__name__))
        else:
            logger.debug(
                'No _yatiml_attributes() found, using public attributes')
            argspec = inspect.getfullargspec(data.__init__)
            attribute_names = list(argspec.args[1:])
            attrs = [(name, getattr(data, name)) for name in attribute_names
                     if name != '_yatiml_extra']
            if '_yatiml_extra' in attribute_names:
                if not hasattr(data, '_yatiml_extra'):
                    raise RuntimeError(
                        ('Class {} takes _yatiml_extra but has '
                         ' no _yatiml_extra attribute, and no '
                         ' _yatiml_attributes().').format(
                             self.class_.__name__))
                attrs.extend(data._yatiml_extra.items())
            attributes = OrderedDict(attrs)

        # convert to a yaml.MappingNode
        represented = dumper.represent_mapping('tag:yaml.org,2002:map',
                                               attributes)  # type: yaml.Node

        # sweeten
        cnode = Node(represented)
        self.__sweeten(dumper, self.class_, cnode)
        # __sweeten() checks this, so can cast safely
        represented = cast(yaml.Node, cnode.yaml_node)

        logger.debug('End representing {}'.format(data))
        return represented

    def __sweeten(self, dumper: 'Dumper', class_: Type, node: Node) -> None:
        """Applies the user's _yatiml_sweeten() function(s), if any.

        Sweetening is done for the base classes first, then for the
        derived classes, down the hierarchy to the class we're
        constructing.

        Args:
            dumper: The dumper that is dumping this object.
            class_: The type of the object to be dumped.
            represented_object: The object to be dumped.
        """
        for base_class in class_.__bases__:
            if base_class in dumper.yaml_representers:
                self.__sweeten(dumper, base_class, node)
        if '_yatiml_sweeten' in class_.__dict__:
            logger.debug('Sweetening {} for class {}'.format(
                node, class_.__name__))
            class_._yatiml_sweeten(node)
            if not isinstance(node.yaml_node, yaml.Node):
                raise RuntimeError(
                        ('After sweetening an object of class {},'
                         ' node.yaml_node is not a yaml.Node. Please'
                         ' check your _yatiml_sweeten() function.'
                         ).format(class_.__name__))


class EnumRepresenter:
    """A yaml Representer class for user-defined enum types.

    For PyYAML to dump a class correctly, it needs a representer
    function for that class. YAtiML provides this generic representer
    which represents enum classes based on the names of their values by
    default, with an optional user override using a member function.
    """

    def __init__(self, class_: Type) -> None:
        """Creates a new Representer for the given class.

        Args:
            class_: The class to represent.
        """
        self.class_ = class_

    def __call__(self, dumper: 'Dumper', data: Any) -> yaml.Node:
        """Represents the class as a ScalarNode.

        Args:
            dumper: The dumper to use.
            data: The user-defined object to dump.

        Returns:
            A yaml.Node representing the object.
        """
        # make a ScalarNode of type str with name of value
        logger.info('Representing {} of class {}'.format(
            data, self.class_.__name__))

        # convert to a yaml.ScalarNode
        start_mark = yaml.error.Mark('Generated node', 0, 0, 0, None, 0)
        end_mark = start_mark
        represented = yaml.ScalarNode(
                'tag:yaml.org,2002:str',
                data.name, start_mark, end_mark)    # type: yaml.Node

        # sweeten
        snode = Node(represented)
        if hasattr(self.class_, '_yatiml_sweeten'):
            self.class_._yatiml_sweeten(snode)
            represented = snode.yaml_node

        logger.debug('End representing {}'.format(data))
        return represented


class UserStringRepresenter:
    """A yaml Representer class for user-defined string types.

    For PyYAML to dump a class correctly, it needs a representer
    function for that class. YAtiML provides this generic representer
    which represents user-defined string classes as strings.
    """

    def __init__(self, class_: Type) -> None:
        """Creates a new Representer for the given class.

        Args:
            class_: The class to represent.
        """
        self.class_ = class_

    def __call__(self, dumper: 'Dumper', data: Any) -> yaml.Node:
        """Represents the class as a Node.

        Args:
            dumper: The dumper to use.
            data: The user-defined object to dump.

        Returns:
            A yaml.Node representing the object.
        """
        # make a ScalarNode of type str with name of value
        logger.info('Representing {} of class {}'.format(
            data, self.class_.__name__))

        # convert to a yaml.ScalarNode
        represented = dumper.represent_str(str(data))   # type: yaml.Node

        # sweeten
        snode = Node(represented)
        if hasattr(self.class_, '_yatiml_sweeten'):
            self.class_._yatiml_sweeten(snode)
            if not isinstance(snode.yaml_node, yaml.Node):
                raise RuntimeError(
                        ('After sweetening an object of class {},'
                         ' node.yaml_node is not a yaml.Node. Please'
                         ' check your _yatiml_sweeten() function.'
                         ).format(self.class_.__name__))
            represented = snode.yaml_node

        logger.debug('End representing {}'.format(data))
        return represented


class PathRepresenter:
    """A yaml Representer class for pathlib.Path.

    For PyYAML to dump a class correctly, it needs a representer
    function for that class. YAtiML provides this representer for
    pathlib.Path objects.
    """

    def __call__(self, dumper: 'Dumper', path: pathlib.Path) -> yaml.Node:
        """Represents the class as a Node.

        Args:
            dumper: The dumper to use.
            path: The Path object to dump.

        Returns:
            A yaml.Node representing the object.
        """
        logger.info('Representing {} of class pathlib.Path'.format(path))

        represented = dumper.represent_str(str(path))   # type: yaml.Node

        logger.debug('End representing {}'.format(path))
        return represented
