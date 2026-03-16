"""This module contains all the definitions for yMMSL."""
from collections import OrderedDict
from typing import Any, List, Optional, Union, cast
from typing import Dict     # noqa

import yatiml

from ymmsl.component import Operator    # noqa
from ymmsl.component import Component
from ymmsl.identity import Identifier, Reference


class Conduit:
    """A conduit transports data between simulation components.

    A conduit has two endpoints, which are references to a port on a
    simulation component. These references must be of one of the
    following forms:

    - component.port
    - namespace.component.port (or several namespace prefixes)

    Attributes:
        sender: The sending port that this conduit is connected to.
        receiver: The receiving port that this conduit is connected to.

    """

    def __init__(self, sender: str, receiver: str) -> None:
        """Create a Conduit.

        Args:
            sender: The sending component and port, as a Reference.
            receiver: The receiving component and port, as a
                    Reference.

        """
        self.sender = Reference(sender)
        self.receiver = Reference(receiver)

        self.__check_reference(self.sender)
        self.__check_reference(self.receiver)

    def __str__(self) -> str:
        """Return a string representation of the object."""
        return 'Conduit({} -> {})'.format(self.sender, self.receiver)

    def __eq__(self, other: Any) -> bool:
        """Returns whether the conduits connect the same ports."""
        if not isinstance(other, Conduit):
            return NotImplemented
        return self.sender == other.sender and self.receiver == other.receiver

    @staticmethod
    def __check_reference(ref: Reference) -> None:
        """Checks an endpoint for validity."""
        # check that subscripts are at the end
        for i, part in enumerate(ref):
            if isinstance(part, int):
                if (i+1) < len(ref) and isinstance(ref[i+1], Identifier):
                    raise ValueError('Reference {} contains a subscript that'
                                     ' is not at the end, which is not allowed'
                                     ' in conduits.'.format(ref))

        # check that the length is at least 2
        if len(Conduit.__stem(ref)) < 2:
            raise ValueError((
                    'Senders and receivers in conduits must have a component'
                    ' name, a period, and then a port name and optionally a'
                    ' slot. Reference {} is missing either the component or'
                    ' the port. Did you perhaps type a comma or an underscore'
                    ' instead of a period? It should be "component.port"'
                    ).format(ref))

    def sending_component(self) -> Reference:
        """Returns a reference to the sending component."""
        return cast(Reference, self.__stem(self.sender)[:-1])

    def sending_port(self) -> Identifier:
        """Returns the identity of the sending port."""
        # We've checked that it's an Identifier during construction
        return cast(Identifier, self.__stem(self.sender)[-1])

    def sending_slot(self) -> List[int]:
        """Returns the slot on the sending port.

        If no slot was given, an empty list is returned.

        Returns:
            A list of slot indexes.

        """
        return self.__slot(self.sender)

    def receiving_component(self) -> Reference:
        """Returns a reference to the receiving component."""
        return cast(Reference, self.__stem(self.receiver)[:-1])

    def receiving_port(self) -> Identifier:
        """Returns the identity of the receiving port."""
        return cast(Identifier, self.__stem(self.receiver)[-1])

    def receiving_slot(self) -> List[int]:
        """Returns the slot on the receiving port.

        If no slot was given, an empty list is returned.

        Returns:
            A list of slot indexes.

        """
        return self.__slot(self.receiver)

    @staticmethod
    def __slot(reference: Reference) -> List[int]:
        """Extracts the slot from the given reference.

        The slot is the list of contiguous ints at the end of the
        reference. If the reference does not end in an int, returns
        an empty list.
        """
        result = list()     # type: List[int]
        i = len(reference) - 1
        while isinstance(reference[i], int):
            result.insert(0, cast(int, reference[i]))
            i -= 1
        return result

    @staticmethod
    def __stem(reference: Reference) -> Reference:
        """Extracts the part of the reference before the slot.

        If there is no slot, returns the whole reference.
        """
        i = len(reference)
        while isinstance(reference[i-1], int):
            i -= 1
        return reference[:i]    # type: ignore


class MulticastConduit:
    """Multicast conduits connect multiple input ports to a single output port.

    In yMMSL they are expressed as a mapping:

    .. code-block:: yaml

        sender.port:
        - receiver1.port
        - receiver2.port

    This class is only used in the parsing and storing of the yMMSL file.
    Once parsed and populated in :class:`Model`, a multicast is identified by
    two or more conduits with the same :attr:`Conduit.sender`.
    """

    def __init__(self, sender: str, receiver: List[str]) -> None:
        """Create a Multicast Conduit.

        Args:
            sender: The sending component and port, as a Reference.
            receiver: The receiving components and ports, as a list of
                    References.
        """
        self.sender = sender
        # note: attribute must be called receiver to transparently work with
        # seq_attribute_to_map and map_attribute_to_seq in
        # Model._yatiml_savorize and Model._yatiml_sweeten
        self.receiver = receiver
        self._conduits = [Conduit(sender, recv) for recv in receiver]

    def as_conduits(self) -> List[Conduit]:
        """Retrieve the conduits that are part of this multicast conduit.

        Returns:
            A list of conduits, one conduit for each receiver.
        """
        return self._conduits


AnyConduit = Union[Conduit, MulticastConduit]


class ModelReference:
    """Describes a reference (by name) to a model.

    Attributes:
        name: The name of the simulation model this refers to.

    """
    def __init__(self, name: str) -> None:
        """Create a ModelReference.

        Arguments:
            name: Name of the model to refer to.

        """
        self.name = Identifier(name)


class Model(ModelReference):
    """Describes a simulation model.

    A model consists of a number of components connected by
    conduits.

    Note that there may be no conduits, if there is only a single
    component. In that case, the conduits argument may be
    omitted when constructing the object, and also from the YAML file;
    the `conduits` attribute will then be set to an empty list.

    Attributes:
        name: The name by which this simulation model is known to
                the system.
        components: A list of components making up the
                model.
        conduits: A list of conduits connecting the components.

    """
    def __init__(self, name: str,
                 components: List[Component],
                 conduits: Optional[List[AnyConduit]] = None) -> None:
        """Create a Model.

        Args:
            name: Name of this model.
            components: A list of components making up the model.
            conduits: A list of conduits connecting the components.
        """
        super().__init__(name)
        self.components = components

        self.conduits = list()      # type: List[Conduit]
        if conduits:
            for conduit in conduits:
                if isinstance(conduit, Conduit):
                    self.conduits.append(conduit)
                if isinstance(conduit, MulticastConduit):
                    self.conduits.extend(conduit.as_conduits())

    def update(self, overlay: 'Model') -> None:
        """Overlay another model definition on top of this one.

        This updates the object with the name, components and conduits
        given in the argument. The name is overwritten, and components
        are overwritten if they have the same name as an existing
        argument or else added.

        Conduits are added. If a receiving port was already connected, the
        old conduit is removed. If a sending port was already connected, the
        new conduit is added and the sending port acts as a multicast port.

        Args:
            overlay: A Model definition to overlay on top of this one.
        """
        self.name = overlay.name
        # update components
        for newc in overlay.components:
            for i, oldc in enumerate(self.components):
                if oldc.name == newc.name:
                    self.components[i] = newc
                    break
            else:
                self.components.append(newc)

        # remove overwritten conduits
        for newt in overlay.conduits:
            for oldt in self.conduits.copy():
                # Multiple conduits can be connected to one sending port
                # (multicast), only overwrite connections to a receiving port
                if oldt.receiver == newt.receiver:
                    self.conduits.remove(oldt)

        # add new conduits
        self.conduits.extend(overlay.conduits)

    def check_consistent(self) -> None:
        """Checks that the model is internally consistent.

        This checks whether all conduits are connected to existing
        components, and will raise a RuntimeError with an explanation
        if one is not.
        """
        def component_exists(name: Reference) -> bool:
            for comp in self.components:
                if comp.name == name:
                    return True
            return False

        def component_has_receiving_port(
                component: Reference, port: Identifier) -> bool:
            if port == 'muscle_settings_in':
                return True
            for comp in self.components:
                if comp.name == component:
                    if not comp.ports:
                        return True

                    try:
                        if comp.ports.operator(port).allows_receiving():
                            return True
                    except KeyError:
                        pass
            return False

        def component_has_sending_port(
                component: Reference, port: Identifier) -> bool:
            for comp in self.components:
                if comp.name == component:
                    if not comp.ports:
                        return True

                    try:
                        if comp.ports.operator(port).allows_sending():
                            return True
                    except KeyError:
                        pass
            return False

        receivers_seen = set()
        for conduit in self.conduits:
            scomp = conduit.sending_component()
            if not component_exists(scomp):
                raise RuntimeError(
                    'Unknown sending component "{}" of {}'.format(
                        scomp, conduit))

            rcomp = conduit.receiving_component()
            if not component_exists(rcomp):
                raise RuntimeError(
                    'Unknown receiving component "{}" of {}'.format(
                        rcomp, conduit))

            sport = conduit.sending_port()
            if not component_has_sending_port(scomp, sport):
                raise RuntimeError(
                        'Invalid conduit "{}": component "{}" does not'
                        ' have a sending port "{}"'.format(
                            conduit, scomp, sport))

            rport = conduit.receiving_port()
            if not component_has_receiving_port(rcomp, rport):
                raise RuntimeError(
                        'Invalid conduit "{}": component "{}" does not'
                        ' have a receiving port "{}"'.format(
                            conduit, rcomp, rport))

            if conduit.receiver in receivers_seen:
                raise RuntimeError(
                        'Receiving port "{}" is connected by multiple'
                        ' conduits.'.format(conduit.receiver))
            receivers_seen.add(conduit.receiver)

    def __conduits_for_export(self) -> List[AnyConduit]:
        """Process conduits and identify MulticastConduits for exporting.

        Returns:
            A list of Conduits and MulticastConduits.
        """
        cond_dct = OrderedDict()  # type: OrderedDict[Reference, List[Conduit]]
        for conduit in self.conduits:
            cond_dct.setdefault(conduit.sender, []).append(conduit)
        conduit_list = []   # type: List[AnyConduit]
        for sender, conduits in cond_dct.items():
            if len(conduits) == 1:
                conduit_list.append(conduits[0])
            else:
                conduit_list.append(MulticastConduit(
                        str(sender),
                        [str(conduit.receiver) for conduit in conduits]))
        return conduit_list

    def _yatiml_attributes(self) -> OrderedDict:
        return OrderedDict([
            ('name', self.name),
            ('components', self.components),
            ('conduits', self.__conduits_for_export())])

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_mapping()
        node.require_attribute('name')
        node.require_attribute('components')

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('components', 'name', 'implementation')
        node.map_attribute_to_seq('conduits', 'sender', 'receiver')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('components', 'name', 'implementation')
        if len(node.get_attribute('conduits').seq_items()) == 0:
            node.remove_attribute('conduits')
        node.seq_attribute_to_map('conduits', 'sender', 'receiver')
