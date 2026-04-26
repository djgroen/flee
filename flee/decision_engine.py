"""
4-mode Decision Engine for the FLEE dual-process (System 1 / System 2) model.

Modes: ``original``, ``sys1_only``, ``switch``, ``blend``.
Day 7b renamed the cognitive mode string to ``sys1_only`` to remove the
collision with sobol first-order index notation. Math from
:mod:`flee.dual_process_model` unchanged; factory pattern enables
comparative runs.
"""

from abc import ABC, abstractmethod
from typing import Tuple

from flee.dual_process_model import (
    compute_deliberation_weight,
    compute_s2_move_probability,
)


class DecisionEngine(ABC):
    """Abstract base for all decision modes."""

    def __init__(self, alpha: float = 2.0, beta: float = 2.0, kappa: float = 5.0):
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa

    # Legacy aliases preserved so old YAML configs and CSVs still resolve to
    # the post-rename modes (sobol vs cognitive disambiguation, Day 7b).
    # New callers should use the canonical 'sys1_only'/'sys2_only' names.
    _MODE_ALIASES = {"s1_only": "sys1_only", "s2_only": "sys2_only"}  # sobol-cognitive back-compat

    @classmethod
    def create(cls, mode: str, config: dict) -> "DecisionEngine":
        """Factory: valid modes are original, sys1_only, switch, blend."""
        mode = cls._MODE_ALIASES.get(mode, mode)
        params = config.get("s1s2_model_params", {})
        alpha = float(params.get("alpha", 2.0))
        beta = float(params.get("beta", 2.0))
        kappa = float(params.get("kappa", 5.0))
        switch_threshold = float(params.get("switch_threshold", 0.5))

        if mode == "original":
            return OriginalFLEE(alpha=alpha, beta=beta, kappa=kappa)
        elif mode == "sys1_only":
            return Sys1OnlyEngine(alpha=alpha, beta=beta, kappa=kappa)
        elif mode == "switch":
            return SwitchEngine(alpha=alpha, beta=beta, kappa=kappa, threshold=switch_threshold)
        elif mode == "blend":
            return BlendEngine(alpha=alpha, beta=beta, kappa=kappa)
        else:
            raise ValueError(
                f"Invalid decision_mode: {mode}. "
                "Use: original, sys1_only, switch, blend")

    @abstractmethod
    def compute_move_probability(
        self,
        movechance_s1: float,
        experience_index: float,
        conflict_intensity: float,
        rad_here: float,
        rad_best: float,
        distance_best: float,
    ) -> Tuple[float, float]:
        """Returns (move_probability, p_s2_weight)."""
        pass

    @abstractmethod
    def compute_destination_weight(
        self,
        w_s1: float,
        w_s2: float,
        experience_index: float,
        conflict_intensity: float,
    ) -> float:
        """Blend System-1 and System-2 route weights."""
        pass

    def _p_s2(self, experience_index: float, conflict_intensity: float) -> float:
        return compute_deliberation_weight(
            experience_index, conflict_intensity, self.alpha, self.beta
        )

    def _sigma(self, rad_here: float, rad_best: float, distance_best: float) -> float:
        return compute_s2_move_probability(
            rad_here, rad_best, distance_best, self.kappa
        )


class OriginalFLEE(DecisionEngine):
    """
    Unmodified FLEE behavior. P_S2 forced to 0.
    Uses existing movechance and selectRoute without any System-1/System-2 modification.
    This is the scientific baseline — the model as published before this work.
    """

    def compute_move_probability(
        self,
        movechance_s1: float,
        experience_index: float,
        conflict_intensity: float,
        rad_here: float,
        rad_best: float,
        distance_best: float,
    ) -> Tuple[float, float]:
        return (movechance_s1, 0.0)

    def compute_destination_weight(
        self,
        w_s1: float,
        w_s2: float,
        experience_index: float,
        conflict_intensity: float,
    ) -> float:
        return w_s1


class Sys1OnlyEngine(DecisionEngine):
    """
    Dual-process module active but P_S2 forced to 0 (System 1 only).
    Should produce identical results to OriginalFLEE — this equivalence
    is itself a validation check. Any divergence indicates a bug.

    Renamed from ``S1OnlyEngine`` in Day 7b. The legacy name is preserved
    as a class alias below for back-compat with older test fixtures.
    """

    def compute_move_probability(
        self,
        movechance_s1: float,
        experience_index: float,
        conflict_intensity: float,
        rad_here: float,
        rad_best: float,
        distance_best: float,
    ) -> Tuple[float, float]:
        return (movechance_s1, 0.0)

    def compute_destination_weight(
        self,
        w_s1: float,
        w_s2: float,
        experience_index: float,
        conflict_intensity: float,
    ) -> float:
        return w_s1


class SwitchEngine(DecisionEngine):
    """
    Threshold-based switch: if P_S2 >= threshold use System-2 (sigma), else
    System-1 (movechance). Deterministic given P_S2 -- no Bernoulli draw.
    High-deliberation agents use System 2, low-deliberation agents use System 1.
    """

    def __init__(self, alpha: float = 2.0, beta: float = 2.0, kappa: float = 5.0,
                 threshold: float = 0.5):
        super().__init__(alpha=alpha, beta=beta, kappa=kappa)
        self.threshold = threshold

    def compute_move_probability(
        self,
        movechance_s1: float,
        experience_index: float,
        conflict_intensity: float,
        rad_here: float,
        rad_best: float,
        distance_best: float,
    ) -> Tuple[float, float]:
        p = self._p_s2(experience_index, conflict_intensity)
        if p >= self.threshold:
            result = self._sigma(rad_here, rad_best, distance_best)
        else:
            result = movechance_s1
        if conflict_intensity > 0.9:
            result = max(result, 0.95)
        return (min(1.0, result), p)

    def compute_destination_weight(
        self,
        w_s1: float,
        w_s2: float,
        experience_index: float,
        conflict_intensity: float,
    ) -> float:
        p = self._p_s2(experience_index, conflict_intensity)
        return w_s2 if p >= self.threshold else w_s1


class BlendEngine(DecisionEngine):
    """
    Continuous mixture: P_move = (1-P_S2)*movechance + P_S2*sigma
    Current implementation in moving.py — refactored here.
    """

    def compute_move_probability(
        self,
        movechance_s1: float,
        experience_index: float,
        conflict_intensity: float,
        rad_here: float,
        rad_best: float,
        distance_best: float,
    ) -> Tuple[float, float]:
        p = self._p_s2(experience_index, conflict_intensity)
        s = self._sigma(rad_here, rad_best, distance_best)
        blended = (1.0 - p) * movechance_s1 + p * s
        if conflict_intensity > 0.9:
            blended = max(blended, 0.95)
        return (min(1.0, blended), p)

    def compute_destination_weight(
        self,
        w_s1: float,
        w_s2: float,
        experience_index: float,
        conflict_intensity: float,
    ) -> float:
        p = self._p_s2(experience_index, conflict_intensity)
        return (1.0 - p) * w_s1 + p * w_s2


# Legacy alias kept for back-compat with old test fixtures (Day 7b rename).
S1OnlyEngine = Sys1OnlyEngine
