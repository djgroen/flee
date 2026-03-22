"""
4-mode Decision Engine for FLEE dual-process model.

Modes: original, s1_only, switch, blend
Math from s1s2_model.py unchanged; factory pattern enables comparative runs.
"""

import random
from abc import ABC, abstractmethod
from typing import Tuple

from flee.s1s2_model import compute_deliberation_weight, compute_s2_move_probability


class DecisionEngine(ABC):
    """Abstract base for all decision modes."""

    def __init__(self, alpha: float = 2.0, beta: float = 2.0, kappa: float = 5.0):
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa

    @classmethod
    def create(cls, mode: str, config: dict) -> "DecisionEngine":
        """Factory: valid modes are original, s1_only, switch, blend."""
        params = config.get("s1s2_model_params", {})
        alpha = float(params.get("alpha", 2.0))
        beta = float(params.get("beta", 2.0))
        kappa = float(params.get("kappa", 5.0))

        if mode == "original":
            return OriginalFLEE(alpha=alpha, beta=beta, kappa=kappa)
        elif mode == "s1_only":
            return S1OnlyEngine(alpha=alpha, beta=beta, kappa=kappa)
        elif mode == "switch":
            return SwitchEngine(alpha=alpha, beta=beta, kappa=kappa)
        elif mode == "blend":
            return BlendEngine(alpha=alpha, beta=beta, kappa=kappa)
        else:
            raise ValueError(f"Invalid decision_mode: {mode}. Use: original, s1_only, switch, blend")

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
        """Blend S1 and S2 route weights."""
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
    Uses existing movechance and selectRoute without any S1/S2 modification.
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


class S1OnlyEngine(DecisionEngine):
    """
    Dual-process module active but P_S2 forced to 0.
    Should produce identical results to OriginalFLEE — this equivalence
    is itself a validation check. Any divergence indicates a bug.
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
    Bernoulli draw: u ~ U(0,1). If u < P_S2: pure S2. Else: pure S1.
    Population expectation identical to BlendEngine.
    Individual trajectories are all-or-nothing.
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
        if random.random() < p:
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
        return w_s2 if random.random() < p else w_s1


class BlendEngine(DecisionEngine):
    """
    Continuous mixture: P_move = (1-P_S2)*S1 + P_S2*sigma
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
