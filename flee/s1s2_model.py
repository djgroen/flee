"""
V3 Dual-Process S1/S2 Model — Continuous Mixture Architecture

Mathematical Model (nuclear reduced form):
    Ψ(x; α) = Ψ_min + (1 - Ψ_min)(1 - exp(-αx))   # Cognitive capacity
    Ω(c; β) = exp(-βc)                                # Structural opportunity
    P_S2 = Ψ × Ω                                      # Deliberation reliability
    σ = 1 / (1 + exp(-κ·(c_here - c_best)/d_best))    # S2 move probability

Free parameters: α, β, κ
Architectural constant: Ψ_min = 0.1
"""

import math

PSI_MIN = 0.1  # Baseline deliberative capacity (Assumption 1 in theory doc)


def compute_capacity(experience_index: float, alpha: float = 2.0) -> float:
    """Cognitive capacity: Ψ(x; α) = Ψ_min + (1 - Ψ_min)(1 - exp(-αx))"""
    return PSI_MIN + (1.0 - PSI_MIN) * (1.0 - math.exp(-alpha * max(0.0, experience_index)))


def compute_opportunity(conflict_intensity: float, beta: float = 2.0) -> float:
    """Structural opportunity: Ω(c; β) = exp(-βc)"""
    return math.exp(-beta * max(0.0, min(1.0, conflict_intensity)))


def compute_deliberation_weight(experience_index: float, conflict_intensity: float,
                                 alpha: float = 2.0, beta: float = 2.0) -> float:
    """Deliberation reliability weight: P_S2 = Ψ × Ω (continuous, NOT a probability for Bernoulli draw)."""
    return compute_capacity(experience_index, alpha) * compute_opportunity(conflict_intensity, beta)


def compute_s2_move_probability(conflict_here: float, conflict_best: float,
                                 distance_best: float, kappa: float = 5.0) -> float:
    """S2 move probability: σ = logistic(κ · (c_here - c_best) / d_best)

    Nuclear reduced form: pure safety-per-distance evaluation, no social ties.
    """
    if distance_best <= 0:
        distance_best = 1.0  # Prevent division by zero; same-location fallback
    safety_signal = kappa * (conflict_here - conflict_best) / distance_best
    # Clamp to prevent overflow
    safety_signal = max(-20.0, min(20.0, safety_signal))
    return 1.0 / (1.0 + math.exp(-safety_signal))
