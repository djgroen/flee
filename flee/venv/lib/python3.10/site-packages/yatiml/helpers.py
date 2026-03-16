from copy import copy
import os
from typing import (  # noqa: F401
    Any,
    List,
    NewType,
    Optional,
    Set,
    Union,
    cast)
from typing_extensions import Type

import yaml
from yaml.error import Mark

from yatiml.exceptions import RecognitionError, SeasoningError
from yatiml.introspection import defaulted_attributes
from yatiml.irecognizer import IRecognizer, format_rec_error
from yatiml.util import ScalarType, scalar_type_to_tag

_Any = NewType('_Any', int)


class Node:
    """A wrapper class for yaml Nodes that provides utility functions.

    This class defines a number of helper function for you to use
    when writing ``_yatiml_sweeten()`` and ``_yatiml_savorize()``
    functions. It also gives access to the underlying `yaml.Node`, so
    you can do anything PyYAML can do if you're willing to dive
    into its internals.

    Attributes:
        yaml_node: The wrapped yaml Node. You can read and modify this,
                yourself if you want, or replace it completely with a
                new yaml.Node.
    """

    def __init__(self, node: yaml.Node) -> None:
        """Create a Node for a particular node.

        The member functions will act on the contained node.

        Args:
            node: The node to provide help for.
        """
        self.yaml_node = node

    def __str__(self) -> str:
        """Convert to a human-readable string."""
        return 'Node({})'.format(self.yaml_node)

    def is_scalar(self, typ: Union[Type, None] = _Any) -> bool:
        """Returns ``True`` iff this represents a scalar node.

        If a type is given, checks that the node represents this
        type. Type may be ``str``, ``int``, ``float``, ``bool``, or
        ``None``.

        If no type is given, then any of the above types will return
        ``True``.
        """
        if isinstance(self.yaml_node, yaml.ScalarNode):
            if typ != _Any and typ in scalar_type_to_tag:
                if typ is None:
                    typ = type(None)
                return cast(str, self.yaml_node.tag) == scalar_type_to_tag[typ]

            if typ is _Any:
                return True
            raise ValueError('Invalid scalar type passed to is_scalar()')
        return False

    def is_mapping(self) -> bool:
        """Returns ``True`` iff this represents a mapping node."""
        return isinstance(self.yaml_node, yaml.MappingNode)

    def is_sequence(self) -> bool:
        """Returns ``True`` iff this represents a sequence node."""
        return isinstance(self.yaml_node, yaml.SequenceNode)

    # Functions for Scalar nodes

    def get_value(self) -> ScalarType:
        """Returns the value of a scalar node.

        Use :meth:`is_scalar` to check which type the node has.
        """
        if self.yaml_node.tag == 'tag:yaml.org,2002:str':
            return str(self.yaml_node.value)
        if self.yaml_node.tag == 'tag:yaml.org,2002:int':
            return int(self.yaml_node.value)
        if self.yaml_node.tag == 'tag:yaml.org,2002:float':
            return float(self.yaml_node.value)
        if self.yaml_node.tag == 'tag:yaml.org,2002:bool':
            return self.yaml_node.value in ['TRUE', 'True', 'true']
        if self.yaml_node.tag == 'tag:yaml.org,2002:null':
            return None
        raise RuntimeError('This node with tag "{}" is not of the right type'
                           ' for get_value()'.format(self.yaml_node.tag))

    def set_value(self, value: ScalarType) -> None:
        """Sets the value of the node to a scalar value.

        After this, ``is_scalar(type(value))`` will return ``True``.

        Args:
            value: The value to set this node to, a ``str``, ``int``,
                    ``float``, ``bool``, or ``None``.
        """
        if isinstance(value, bool):
            value_str = 'true' if value else 'false'
        else:
            value_str = str(value)
        start_mark = self.yaml_node.start_mark
        end_mark = self.yaml_node.end_mark
        # If we're of a class type, then we want to keep that tag so that the
        # correct Constructor is called. If we're a built-in type, set the tag
        # to the appropriate YAML tag.
        tag = self.yaml_node.tag
        if tag.startswith('tag:yaml.org,2002:'):
            tag = scalar_type_to_tag[type(value)]
        new_node = yaml.ScalarNode(tag, value_str, start_mark, end_mark)
        self.yaml_node = new_node

    # Functions for Mapping nodes

    def make_mapping(self) -> None:
        """Replaces the node with a new, empty mapping.

        Note that this will work on the Node object that is passed to
        a ``_yatiml_savorize()`` or ``_yatiml_sweeten()`` function, but
        not on any of its attributes or items. If you need to set an
        attribute to a complex value, build a ``yaml.Node``
        representing it and use :meth:`set_attribute` with that.
        """
        start_mark = Mark('generated node', 0, 0, 0, None, 0)
        end_mark = Mark('generated node', 0, 0, 0, None, 0)
        self.yaml_node = yaml.MappingNode('tag:yaml.org,2002:map', list(),
                                          start_mark, end_mark)

    def has_attribute(self, attribute: str) -> bool:
        """Whether the node has an attribute with the given name.

        Use only if :meth:`is_mapping` returns ``True``.

        Args:
            attribute: The name of the attribute to check for.

        Returns:
            True iff the attribute is present.
        """
        return any([
            key_node.value == attribute for key_node, _ in self.yaml_node.value
        ])

    def has_attribute_type(self, attribute: str, typ: Optional[Type]) -> bool:
        """Whether the given attribute exists and has a compatible type.

        Returns true iff the attribute exists and is an instance of
        the given type. Matching between types passed as typ and
        yaml node types is as follows:

        +---------+-------------------------------------------+
        |   typ   |                 yaml                      |
        +=========+===========================================+
        |   str   |      ScalarNode containing string         |
        +---------+-------------------------------------------+
        |   int   |      ScalarNode containing int            |
        +---------+-------------------------------------------+
        |  float  |      ScalarNode containing float          |
        +---------+-------------------------------------------+
        |   bool  |      ScalarNode containing bool           |
        +---------+-------------------------------------------+
        |   None  |      ScalarNode containing null           |
        +---------+-------------------------------------------+
        |   list  |      SequenceNode                         |
        +---------+-------------------------------------------+
        |   dict  |      MappingNode                          |
        +---------+-------------------------------------------+

        Args:
            attribute: The name of the attribute to check.
            typ: The type to check against.

        Returns:
            ``True`` iff the attribute exists and matches the type.
        """
        if not self.has_attribute(attribute):
            return False

        attr_node = self.get_attribute(attribute).yaml_node

        if typ in scalar_type_to_tag:
            tag = scalar_type_to_tag[typ]
            return cast(str, attr_node.tag) == tag
        elif typ == list:
            return isinstance(attr_node, yaml.SequenceNode)
        elif typ == dict:
            return isinstance(attr_node, yaml.MappingNode)

        raise ValueError('Invalid argument for typ attribute')

    def get_attribute(self, attribute: str) -> 'Node':
        """Returns the node representing the given attribute's value.

        Use only if :meth:`is_mapping` returns true.

        Args:
            attribute: The name of the attribute to retrieve.

        Raises:
            KeyError: If the attribute does not exist.

        Returns:
            A node representing the value.
        """
        matches = [
            value_node for key_node, value_node in self.yaml_node.value
            if key_node.value == attribute
        ]
        if len(matches) != 1:
            raise SeasoningError(
                'Key not found, or found multiple times: {}'.format(
                    attribute))
        return Node(matches[0])

    def set_attribute(self, attribute: str,
                      value: Union[ScalarType, yaml.Node]) -> None:
        """Sets the attribute to the given value.

        Use only if :meth:`is_mapping` returns ``True``.

        If the attribute does not exist, this adds a new attribute,
        if it does, it will be overwritten.

        If value is a ``str``, ``int``, ``float``, ``bool`` or ``None``,
        the attribute will be set to this value. If you want to set the
        value to a list or dict containing other values, build a
        yaml.Node and pass it here.

        Args:
            attribute: Name of the attribute whose value to change.
            value: The value to set.
        """
        start_mark = Mark('generated node', 0, 0, 0, None, 0)
        end_mark = Mark('generated node', 0, 0, 0, None, 0)
        if isinstance(value, str):
            value_node = yaml.ScalarNode(
                    'tag:yaml.org,2002:str', value,
                    start_mark, end_mark)  # type: yaml.Node
        elif isinstance(value, bool):
            value_str = 'true' if value else 'false'
            value_node = yaml.ScalarNode('tag:yaml.org,2002:bool', value_str,
                                         start_mark, end_mark)
        elif isinstance(value, int):
            value_node = yaml.ScalarNode('tag:yaml.org,2002:int', str(value),
                                         start_mark, end_mark)
        elif isinstance(value, float):
            value_node = yaml.ScalarNode('tag:yaml.org,2002:float', str(value),
                                         start_mark, end_mark)
        elif value is None:
            value_node = yaml.ScalarNode('tag:yaml.org,2002:null', '',
                                         start_mark, end_mark)
        elif isinstance(value, yaml.Node):
            value_node = value
        else:
            raise TypeError('Invalid kind of value passed to set_attribute()')

        attr_index = self.__attr_index(attribute)
        if attr_index is not None:
            key_node = self.yaml_node.value[attr_index][0]
            self.yaml_node.value[attr_index] = key_node, value_node
        else:
            key_node = yaml.ScalarNode('tag:yaml.org,2002:str', attribute,
                                       start_mark, end_mark)
            self.yaml_node.value.append((key_node, value_node))
            if isinstance(self.yaml_node, yaml.MappingNode):
                self.yaml_node.flow_style = False

    def remove_attribute(self, attribute: str) -> None:
        """Remove an attribute from the node.

        Use only if :meth:`is_mapping` returns ``True``.

        Args:
            attribute: The name of the attribute to remove.
        """
        attr_index = self.__attr_index(attribute)
        if attr_index is not None:
            self.yaml_node.value.pop(attr_index)

    def remove_attributes_with_default_values(self, cls: Type) -> None:
        """Remove attributes with default values.

        If you have a class with many optional attributes, then saving
        it to YAML may yield a very large dictionary with many values
        set to e.g. ``None``. If there's no risk of creating an
        ambiguity, then you may want to remove any attributes whose
        value matches the default.

        This function can be used in ``_yatiml_sweeten()`` to do that.
        For ``cls``, pass the ``cls`` first argument of
        ``_yatiml_sweeten()``.

        If the default for the parameter is not the same as the default
        of the attribute, for example in this common situation:

        .. code-block:: python

            def __init__(
                    self, my_list: Optional[List[int]] = None) -> None:
                if my_list is None:
                    my_list = list()
                self.my_list = my_list


        then this function will not remove the attribute if it is an
        empty list, because it compares with ``None`` in the type
        annotation. To fix that, you can define ``_yatiml_defaults`` like
        this:

        .. code-block:: python

            def __init__(
                    self, my_list: Optional[List[int]] = None) -> None:
                if my_list is None:
                    my_list = list()
                self.my_list = my_list

            _yatiml_defaults = {'my_list': []}  # type: Dict[str, Any]

            @classmethod
            def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
                node.remove_attributes_with_default_values(cls)


        Note that this function currently only works for the built-in
        types ``bool``, ``float``, ``int``, ``str`` and for ``None``
        values, not for classes or enums.

        Use only if :meth:`is_mapping` returns ``True``.

        Args:
            cls: The class we're sweetening.
        """
        def matches(value_node: yaml.Node, default: Any) -> bool:
            if value_node.tag == 'tag:yaml.org,2002:null':
                return default is None

            if value_node.tag == 'tag:yaml.org,2002:int':
                return int(value_node.value) == int(default)

            if value_node.tag == 'tag:yaml.org,2002:float':
                return float(value_node.value) == float(default)

            if value_node.tag == 'tag:yaml.org,2002:bool':
                if default is False:
                    return (
                            str(value_node.value).lower() == 'n' or
                            str(value_node.value).lower() == 'no' or
                            str(value_node.value).lower() == 'false' or
                            str(value_node.value).lower() == 'off')
                elif default is True:
                    return (
                            str(value_node.value).lower() == 'y' or
                            str(value_node.value).lower() == 'yes' or
                            str(value_node.value).lower() == 'true' or
                            str(value_node.value).lower() == 'on')
                return False

            return bool(value_node.value == default)

        defaults = defaulted_attributes(cls)

        self.yaml_node.value = [
                (name_node, value_node)
                for name_node, value_node in self.yaml_node.value
                if (
                    name_node.value not in defaults or
                    not matches(value_node, defaults[name_node.value]))]

    def rename_attribute(self, attribute: str, new_name: str) -> None:
        """Renames an attribute.

        Use only if :meth:`is_mapping` returns ``True``.

        If the attribute does not exist, this will do nothing.

        Args:
            attribute: The (old) name of the attribute to rename.
            new_name: The new name to rename it to.
        """
        for key_node, _ in self.yaml_node.value:
            if key_node.value == attribute:
                key_node.value = new_name
                break

    def unders_to_dashes_in_keys(self) -> None:
        """Replaces underscores with dashes in key names.

        For each attribute in a mapping, this replaces any underscores
        in its keys with dashes. Handy because Python does not
        accept dashes in identifiers, while some YAML-based formats use
        dashes in their keys.
        """
        for key_node, _ in self.yaml_node.value:
            key_node.value = key_node.value.replace('_', '-')

    def dashes_to_unders_in_keys(self) -> None:
        """Replaces dashes with underscores in key names.

        For each attribute in a mapping, this replaces any dashes in
        its keys with underscores. Handy because Python does not
        accept dashes in identifiers, while some YAML-based file
        formats use dashes in their keys.
        """
        for key_node, _ in self.yaml_node.value:
            key_node.value = key_node.value.replace('-', '_')

    def seq_attribute_to_map(self,
                             attribute: str,
                             key_attribute: str,
                             value_attribute: Optional[str] = None,
                             strict: Optional[bool] = True) -> None:
        """Converts a sequence attribute to a map.

        This function takes an attribute of this Node that is
        a sequence of mappings and turns it into a mapping of mappings.
        It assumes that each of the mappings in the original sequence
        has an attribute containing a unique value, which it will use
        as a key for the new outer mapping.

        An example probably helps. If you have a Node representing
        this piece of YAML::

            items:
            - item_id: item1
              description: Basic widget
              price: 100.0
            - item_id: item2
              description: Premium quality widget
              price: 200.0

        and call ``seq_attribute_to_map('items', 'item_id')``, then the
        Node will be modified to represent this::

            items:
              item1:
                description: Basic widget
                price: 100.0
              item2:
                description: Premium quality widget
                price: 200.0

        which is often more intuitive for people to read and write.

        If the attribute does not exist, or is not a sequence of
        mappings, this function will silently do nothing. If the keys
        are not unique and strict is ``False``, it will also do
        nothing. If the keys are not unique and strict is ``True``, it
        will raise an error.

        With thanks to the makers of the Common Workflow Language for
        the idea.

        Args:
            attribute: Name of the attribute whose value to modify.
            key_attribute: Name of the attribute in each item to use
                    as a key for the new mapping.
            value_attribute: Name of the attribute in each item to use
                    for the value in the new mapping, if only a key and
                    value have been given.
            strict: Whether to give an error if the intended keys are
                    not unique.

        Raises:
            yatiml.SeasoningError: If the keys are not unique and
                    strict is ``True``.
        """
        if not self.has_attribute(attribute):
            return

        attr_node = self.get_attribute(attribute)
        if not attr_node.is_sequence():
            return

        start_mark = attr_node.yaml_node.start_mark
        end_mark = attr_node.yaml_node.end_mark

        # check that all list items are mappings and that the keys are unique
        # strings
        seen_keys = set()  # type: Set[str]
        for item in attr_node.seq_items():
            key_attr_node = item.get_attribute(key_attribute)
            if not key_attr_node.is_scalar(str):
                raise SeasoningError('Expected a string here')
            if key_attr_node.get_value() in seen_keys:
                if strict:
                    raise SeasoningError(
                        ('Found a duplicate key "{}": {} when'
                         ' converting from sequence to mapping'.format(
                             key_attribute, key_attr_node.get_value())))
                return
            seen_keys.add(key_attr_node.get_value())  # type: ignore

        # construct mapping
        mapping_values = list()
        for item in attr_node.seq_items():
            # we've already checked that it's a SequenceNode above
            key_node = item.get_attribute(key_attribute).yaml_node
            item.remove_attribute(key_attribute)
            if value_attribute is not None:
                value_node = item.get_attribute(value_attribute).yaml_node
                if len(item.yaml_node.value) == 1:
                    # no other attributes, use short form
                    mapping_values.append((key_node, value_node))
                else:
                    mapping_values.append((key_node, item.yaml_node))
            else:
                mapping_values.append((key_node, item.yaml_node))

        # create mapping node
        mapping = yaml.MappingNode('tag:yaml.org,2002:map', mapping_values,
                                   start_mark, end_mark)
        self.set_attribute(attribute, mapping)

    def map_attribute_to_seq(self,
                             attribute: str,
                             key_attribute: str,
                             value_attribute: Optional[str] = None) -> None:
        """Converts a mapping attribute to a sequence.

        This function takes an attribute of this Node whose value
        is a mapping or a mapping of mappings and turns it into a
        sequence of mappings. Each entry in the original mapping is
        converted to an entry in the list. If only a key attribute is
        given, then each entry in the original mapping must map to a
        (sub)mapping. This submapping becomes the corresponding list
        entry, with the key added to it as an additional attribute. If
        a value attribute is also given, then an entry in the original
        mapping may map to any object. If the mapped-to object is a
        mapping, the conversion is as before, otherwise a new
        submapping is created, and key and value are added using the
        given key and value attribute names.

        An example probably helps. If you have a Node representing
        this piece of YAML::

            items:
              item1:
                description: Basic widget
                price: 100.0
              item2:
                description: Premium quality widget
                price: 200.0

        and call ``map_attribute_to_seq('items', 'item_id')``, then the
        Node will be modified to represent this::

            items:
            - item_id: item1
              description: Basic widget
              price: 100.0
            - item_id: item2
              description: Premium quality widget
              price: 200.0

        which once converted to an object is often easier to deal with
        in code.

        Slightly more complicated, this YAML::

            items:
              item1: Basic widget
              item2:
                description: Premium quality widget
                price: 200.0

        when passed through

        .. code-block:: python

          map_attribute_to_seq('items', 'item_id', 'description')

        will result in the equivalent of::

            items:
            - item_id: item1
              description: Basic widget
            - item_id: item2
              description: Premium quality widget
              price: 200.0

        If the attribute does not exist, or is not a mapping, this
        function will silently do nothing.

        With thanks to the makers of the Common Workflow Language for
        the idea.

        Args:
            attribute: Name of the attribute whose value to modify.
            key_attribute: Name of the new attribute in each item to
                    add with the value of the key.
            value_attribute: Name of the new attribute in each item to
                    add with the value of the key.
        """
        if not self.has_attribute(attribute):
            return

        attr_node = self.get_attribute(attribute)
        if not attr_node.is_mapping():
            return

        start_mark = attr_node.yaml_node.start_mark
        end_mark = attr_node.yaml_node.end_mark
        object_list = []
        for item_key, item_value in attr_node.yaml_node.value:
            item_value_node = Node(item_value)
            if not item_value_node.is_mapping():
                if value_attribute is None:
                    return      # invalid format
                ynode = item_value_node.yaml_node
                item_value_node.make_mapping()
                item_value_node.yaml_node.start_mark = item_key.start_mark
                item_value_node.yaml_node.end_mark = item_value.end_mark
                item_value_node.set_attribute(value_attribute, ynode)

            item_value_node.set_attribute(key_attribute, item_key.value)
            object_list.append(item_value_node.yaml_node)
        seq_node = yaml.SequenceNode('tag:yaml.org,2002:seq', object_list,
                                     start_mark, end_mark)
        self.set_attribute(attribute, seq_node)

    def index_attribute_to_map(
            self,
            attribute: str,
            key_attribute: str,
            value_attribute: Optional[str] = None
            ) -> None:
        """Converts an index attribute to a map.

        It is often convenient to represent a collection of objects by
        a dict mapping a name of each object to that object (let's call
        that an *index*). If each object knows its own name, then the
        name is stored twice, which is not nice to have to type and
        keep synchronised in YAML.

        In YAML, such an index is a mapping of mappings, where the key
        of the outer mapping matches the value of one of the items in
        the corresponding inner mapping. This function removes the
        redundant key/value from the inner mapping. If that leaves only
        a single key in the inner mapping, and it matches
        ``value_attribute``, then the value corresponding to that key
        becomes the value for the item in the outer mapping.

        An example probably helps. Let's say we have a class
        ``Employee`` and a ``Company`` which has employees:

        .. code-block:: python

          class Employee:
              def __init__(self, name: str, role: str) -> None:
                  ...

          class Company:
              def __init__(
                      self, employees: Dict[str, Employee]
                      ) -> None:
                  ...

          my_company = Company({
              'Mary': Employee('Mary', 'Director'),
              'Vishnu': Employee('Vishnu', 'Sales'),
              'Susan': Employee('Susan', 'Engineering')})

        By default, this will turn into the following YAML when saved:

        .. code-block:: yaml

          employees:
            Mary:
              name: Mary
              role: Director
            Vishnu:
              name: Vishnu
              role: Sales
            Susan:
              name: Susan
              role: Engineering

        If you call
        ``node.index_attribute_to_map('employees', 'name')`` in
        ``Company._yatiml_sweeten()``, then the output will be

        .. code-block:: yaml

          employees:
            Mary:
              role: Director
            Vishnu:
              role: Sales
            Susan:
              role: Engineering

        If you call
        ``node.index_attribute_to_map('employees', 'name', 'role')``
        then it will turn into

        .. code-block:: yaml

          employees:
            Mary: Director
            Vishnu: Sales
            Susan: Engineering

        If the attribute does not exist, or is not a mapping of
        mappings, this function will silently do nothing.

        See :meth:`map_attribute_to_index` for the reverse.

        With thanks to the makers of the Common Workflow Language for
        the idea.

        Args:
            attribute: Name of the attribute whose value to modify.
            key_attribute: Name of the attribute in each item to
                    remove.
            value_attribute: Name of the attribute in each item to use
                    for the value in the new mapping, if only a key and
                    value have been given.
        """
        if not self.has_attribute(attribute):
            return

        attr_node = self.get_attribute(attribute)
        if not attr_node.is_mapping():
            return

        new_value = list()
        for key_node, value_node in attr_node.yaml_node.value:
            if not isinstance(value_node, yaml.MappingNode):
                raise SeasoningError(
                    'Values must be mappings for key "{}"'.format(attribute))

            # filter out key atttribute
            value_node.value = [
                    (k, v) for k, v in value_node.value
                    if k.value != key_attribute]

            # replace mapping with value attribute, if it's the only one
            if (
                    len(value_node.value) == 1 and
                    value_node.value[0][0].value == value_attribute):
                new_value.append((key_node, value_node.value[0][1]))
            else:
                new_value.append((key_node, value_node))

        attr_node.yaml_node.value = new_value

    def map_attribute_to_index(
            self,
            attribute: str,
            key_attribute: str,
            value_attribute: Optional[str] = None) -> None:
        """Converts a mapping attribute to an index .

        It is often convenient to represent a collection of objects by
        a dict mapping a name of each object to that object (let's call
        that an *index*). If each object knows its own name, then the
        name is stored twice, which is not nice to have to type and
        keep synchronised in YAML.

        In YAML, such an index is a mapping of mappings, where the key
        of the outer mapping matches the value of one of the items in
        the corresponding inner mapping.

        This function enables a short-hand notation for the above,
        where the name of the object is mentioned only in the key of
        the mapping and not again in the values, and, if
        ``value_attribute`` is specified, converting any entries with
        a scalar value (rather than a mapping) to a mapping with
        ''value_attribute'' as the key and the original value as the
        value.

        An example probably helps. Let's say we have a class
        ``Employee`` and a ``Company`` which has employees:

        .. code-block:: python

          class Employee:
              def __init__(
                      self, name: str, role: str, hours: int = 40
                      ) -> None:
                  ...

          class Company:
              def __init__(
                      self, employees: Dict[str, Employee]
                      ) -> None:
                  ...

          my_company = Company({
              'Mary': Employee('Mary', 'Director'),
              'Vishnu': Employee('Vishnu', 'Sales'),
              'Susan': Employee('Susan', 'Engineering')})

        By default, to load this from YAML, you have to write:

        .. code-block:: yaml

          employees:
            Mary:
              name: Mary
              role: Director
            Vishnu:
              name: Vishnu
              role: Sales
            Susan:
              name: Susan
              role: Engineering

        If you call
        ``node.map_attribute_to_index('employees', 'name')`` in
        ``Company._yatiml_savorize()``, then the following will also
        work:

        .. code-block:: yaml

          employees:
            Mary:
              role: Director
            Vishnu:
              role: Sales
            Susan:
              role: Engineering

        And if you call
        ``node.map_attribute_to_index('employees', 'name', 'role')``
        then you can also write:

        .. code-block:: yaml

          employees:
            Mary: Director
            Vishnu: Sales
            Susan: Engineering

        If the attribute does not exist, or is not a mapping of
        mappings, this function will silently do nothing.

        See :meth:`index_attribute_to_map` for the reverse.

        With thanks to the makers of the Common Workflow Language for
        the idea.

        Args:
            attribute: Name of the attribute whose value to modify.
            key_attribute: Name of the attribute in each item to
                    add, with the value of the key.
            value_attribute: Name of the attribute in each item to use
                    for the value in the new mapping, if only a key and
                    value have been given.
        """
        if not self.has_attribute(attribute):
            return

        attr_node = self.get_attribute(attribute)
        if not attr_node.is_mapping():
            return

        new_value = list()
        for key_node, value_node in attr_node.yaml_node.value:
            if (
                    not isinstance(value_node, yaml.MappingNode) and
                    value_attribute is not None):
                new_key = yaml.ScalarNode(
                        'tag:yaml.org,2002:str', value_attribute,
                        value_node.start_mark, value_node.end_mark)
                new_mapping = yaml.MappingNode(
                        'tag:yaml.org,2002:map', [(new_key, value_node)],
                        value_node.start_mark, value_node.end_mark)
            else:
                new_mapping = value_node

            if isinstance(new_mapping, yaml.MappingNode):
                key_key = yaml.ScalarNode(
                        'tag:yaml.org,2002:str', key_attribute,
                        key_node.start_mark, key_node.end_mark)
                new_mapping.value.append((key_key, copy(key_node)))

            new_value.append((key_node, new_mapping))

        attr_node.yaml_node.value = new_value

    # Functions for sequences

    def is_empty(self) -> bool:
        """Returns whether a sequence or mapping is empty.

        Use only if :meth:`is_sequence` or :meth:`is_mapping` returns
        ``True``.
        """
        return len(self.yaml_node.value) == 0

    def seq_items(self) -> List['Node']:
        """Returns the items in the sequence.

        Use only if :meth:`is_sequence` returns ``True``.
        """
        return list(map(Node, self.yaml_node.value))

    # Private helpers

    def __attr_index(self, attribute: str) -> Optional[int]:
        """Finds an attribute's index in the yaml_node.value list."""
        attr_index = None
        for i, (key_node, _) in enumerate(self.yaml_node.value):
            if key_node.value == attribute:
                attr_index = i
                break
        return attr_index


class UnknownNode:
    """Utility functions for recognizing nodes.

    This class defines a number of helper function for you to use
    when writing _yatiml_recognize() functions.

    Attributes:
        yaml_node: The yaml.Node wrapped by this object.
    """

    def __init__(self, recognizer: IRecognizer, node: yaml.Node) -> None:
        """Create an UnknownNode for a particular mapping node.

        The member functions will act on the contained node.

        Args:
            node: The node to operate on.
        """
        self.__recognizer = recognizer
        self.yaml_node = node

    def __str__(self) -> str:
        """Convert to a human-readable string."""
        return 'UnknownNode({})'.format(self.yaml_node)

    def require_scalar(self, *args: Type) -> None:
        """Require the node to be a scalar.

        If additional arguments are passed, these are taken as a list
        of valid types; if the node matches one of these, then it is
        accepted.

        Example:
            .. code-block:: python

              # Match either an int or a string
              node.require_scalar(int, str)

        Arguments:
            args: One or more types to match one of.
        """
        node = Node(self.yaml_node)
        if len(args) == 0:
            if not node.is_scalar():
                raise RecognitionError('A scalar is required')
        else:
            for typ in args:
                if node.is_scalar(typ):
                    return
            raise RecognitionError('A scalar of type {} is required'.format(
                    args))

    def require_mapping(self) -> None:
        """Require the node to be a mapping."""
        if not isinstance(self.yaml_node, yaml.MappingNode):
            raise RecognitionError('A mapping is required here')

    def require_sequence(self) -> None:
        """Require the node to be a sequence."""
        if not isinstance(self.yaml_node, yaml.SequenceNode):
            raise RecognitionError('A sequence is required here')

    def require_attribute(
            self, attribute: str, typ: Union[None, Type] = _Any) -> None:
        """Require an attribute on the node to exist.

        This implies that the node must be a mapping.

        If ``typ`` is given, the attribute must have this type.

        Args:
            attribute: The name of the attribute / mapping key.
            typ: The type the attribute must have.
        """
        self.require_mapping()
        attr_nodes = [
            value_node for key_node, value_node in self.yaml_node.value
            if key_node.value == attribute
        ]
        if len(attr_nodes) == 0:
            raise RecognitionError(
                    'Missing required attribute "{}"'.format(attribute))
        attr_node = attr_nodes[0]

        if typ != _Any:
            recognized_types, result = self.__recognizer.recognize(
                attr_node, cast(Type, typ))
            if len(recognized_types) == 0:
                raise RecognitionError(format_rec_error(result))

    def require_attribute_value(
            self, attribute: str,
            value: Union[int, str, float, bool, None]) -> None:
        """Require an attribute on the node to have a particular value.

        This requires the attribute to exist, and to have the given
        value and corresponding type.

        Args:
            attribute: The name of the attribute / mapping key.
            value: The value the attribute must have to recognize an
                    object of this type.

        Raises:
            yatiml.RecognitionError: If the attribute does not exist,
                    or does not have the required value.
        """
        self.require_mapping()
        found = False
        for key_node, value_node in self.yaml_node.value:
            if (key_node.tag == 'tag:yaml.org,2002:str'
                    and key_node.value == attribute):
                found = True
                node = Node(value_node)
                if not node.is_scalar(type(value)):
                    raise RecognitionError(
                            ('Incorrect attribute type where value {}'
                             ' of type {} was required').format(
                                value, type(value)))
                if node.get_value() != value:
                    raise RecognitionError((
                        'Incorrect attribute value {} where {} was required'
                            ).format(value_node.value, value))

        if not found:
            raise RecognitionError(
                    'Required key "{}" not found'.format(attribute))

    def require_attribute_value_not(
            self, attribute: str,
            value: Union[int, str, float, bool, None]) -> None:
        """Require an attribute on the node to not have a given value.

        This requires the attribute to exist, and to not have the given
        value.

        Args:
            attribute: The name of the attribute / mapping key.
            value: The value the attribute must not have to recognize an
                    object of this type.

        Raises:
            yatiml.RecognitionError: If the attribute does not exist,
                    or has the required value.
        """
        self.require_mapping()
        found = False
        for key_node, value_node in self.yaml_node.value:
            if (key_node.tag == 'tag:yaml.org,2002:str'
                    and key_node.value == attribute):
                found = True
                node = Node(value_node)
                if not node.is_scalar(type(value)):
                    return
                if node.get_value() == value:
                    raise RecognitionError(
                            (
                                'Incorrect attribute value {} where {} was not'
                                ' allowed').format(value_node.value, value))

        if not found:
            raise RecognitionError(
                    'Required key "{}" not found'.format(attribute))
