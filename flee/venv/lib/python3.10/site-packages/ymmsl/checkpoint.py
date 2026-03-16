"""Definitions for describing checkpoints."""

from typing import List, Optional, Union

import yaml
import yatiml


class CheckpointRule:
    """Defines a checkpoint rule.

    There are two flavors of rules: :class:`CheckpointRangeRule` and
    :class:`CheckpointAtRule`. Do not use this class directly.
    """


class CheckpointRangeRule(CheckpointRule):
    """Defines a range of checkpoint moments.

    If ``start`` is supplied, this rule specifies a checkpoint at: ``start``,
    ``start + every``, ``start + 2*every``, etc., for as long as
    ``start + n*every <= stop``, with ``n`` a whole number. If stop is not
    given, the range continues indefinitely.

    Start may be omitted, in which case a checkpoint is defined for ``0``,
    ``every``, ``2*every``, etc. Note that in this case the range also extends
    to negative numbers (``-every``, ``-2*every``, etc.), as simulated time may
    be negative (e.g. in rocket launch, ``t=0`` is generally taken as lift-off
    time, but events already take place before that moment).

    Attributes:
        start: Start of the range.
        stop: Stopping criterium of the range.
        every: Step size of the range, must be positive.
    """

    def __init__(self,
                 start: Optional[Union[float, int]] = None,
                 stop: Optional[Union[float, int]] = None,
                 every: Union[float, int] = 0) -> None:
        """Create a checkpoint range.

        Args:
            start: Start of the range. Defaults to None.
            stop: Stop criterium of the range. Defaults to None.
            every: Step size, must be larger than 0.
        """
        if every <= 0:
            raise ValueError(f"Invalid every {every} in checkpoint range:"
                             " must be larger than 0.")
        if start is not None and stop is not None and start > stop:
            raise ValueError(f"Invalid start {start} and stop {stop} in"
                             "checkpoint range: stop cannot be smaller than"
                             " start.")
        self.start = start
        self.stop = stop
        self.every = every

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_attribute('every')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute("start").is_scalar(type(None)):
            node.remove_attribute("start")

        if node.get_attribute("stop").is_scalar(type(None)):
            node.remove_attribute("stop")


class CheckpointAtRule(CheckpointRule):
    """Defines an "at" checkpoint rule.

    An "at" checkpoint rule creates a snapshot at the specified moments.

    Attributes:
        at: List of checkpoints.
    """

    def __init__(self, at: Optional[List[Union[float, int]]]) -> None:
        """Create checkpoint rules.

        Args:
            at: List of checkpoints. Defaults to None.
        """
        if at is None:
            at = []
        self.at = at
        self.at.sort()

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_attribute('at')

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.has_attribute('at'):
            if (node.has_attribute_type('at', int) or
                    node.has_attribute_type('at', float)):
                attr = node.get_attribute('at')
                start_mark = attr.yaml_node.start_mark
                end_mark = attr.yaml_node.end_mark
                new_seq = yaml.nodes.SequenceNode(
                        'tag:yaml.org,2002:seq', [attr.yaml_node], start_mark,
                        end_mark)
                node.set_attribute('at', new_seq)


class Checkpoints:
    """Defines checkpoints in a configuration.

    There are three checkpoint triggers: `at_end`, `wallclock_time` and
    `simulation_time`. The `at_end` trigger specifies that a checkpoint should
    be created just before the workflow finishes. The `wallclock_time` trigger
    is based on the elapsed real time since starting the muscle_manager in
    seconds. The `simulation_time` trigger is based on the time in the
    simulation as reported by the instances.

    Note that the `simulation_time` trigger assumes a shared concept of time
    among all components of the model.

    Attributes:
        at_end: Whether a checkpoint should be created just before ending the
            workflow.
        wallclock_time: Checkpoint rules for the wallclock_time trigger.
        simulation_time: Checkpoint rules for the simulation_time trigger.
    """
    def __init__(self,
                 at_end: bool = False,
                 wallclock_time: Optional[List[CheckpointRule]] = None,
                 simulation_time: Optional[List[CheckpointRule]] = None
                 ) -> None:
        """Create checkpoint definitions.

        Args:
            wallclock_time: Checkpoint rules for the wallclock_time trigger.
            simulation_time: Checkpoint rules for the simulation_time trigger.
        """
        self.at_end = at_end
        if wallclock_time is None:
            wallclock_time = []
        if simulation_time is None:
            simulation_time = []
        self.wallclock_time = wallclock_time
        self.simulation_time = simulation_time

    def __bool__(self) -> bool:
        """Evaluate to true iff any rules are defined."""
        return (self.at_end or
                bool(self.wallclock_time) or
                bool(self.simulation_time))

    def update(self, overlay: 'Checkpoints') -> None:
        """Update this checkpoints with the given overlay.

        Sets `at_end` to True if it is set in the overlay, otherwise `at_end`
        remains as is. Updates the checkpoint rules for wallclock time and
        simulation time. See :meth:`CheckpointRules.update`.
        """
        self.at_end |= overlay.at_end
        self.wallclock_time.extend(overlay.wallclock_time)
        self.simulation_time.extend(overlay.simulation_time)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if not node.get_attribute("at_end").get_value():
            node.remove_attribute("at_end")

        wallclock_time = node.get_attribute("wallclock_time")
        if wallclock_time.is_scalar(type(None)) or (
                wallclock_time.is_sequence() and wallclock_time.is_empty()):
            node.remove_attribute("wallclock_time")

        simulation_time = node.get_attribute("simulation_time")
        if simulation_time.is_scalar(type(None)) or (
                simulation_time.is_sequence() and simulation_time.is_empty()):
            node.remove_attribute("simulation_time")
