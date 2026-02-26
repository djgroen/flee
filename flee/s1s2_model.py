"""
Parsimonious Dual-Process S1/S2 Decision-Making Model

This module implements the theoretical model for crisis decision-making:
Deliberation requires BOTH cognitive capacity AND structural opportunity.

Mathematical Model:
    Ψ(x; α) = 1/(1 + e^(-αx))              # Cognitive capacity (Psi)
    Ω(c; β) = 1/(1 + e^(-β(1-c)))          # Structural opportunity (Omega)
    P_S2 = Ψ × Ω                           # Deliberation probability
    p_move = (1 - P_S2) · movechance + P_S2 · p_s2  # Final move probability

Where:
    x = experience-based capacity index
    c = conflict intensity [0, 1]
    α = cognitive capacity sensitivity
    β = structural opportunity sensitivity
"""

import math
import numpy as np
from typing import Tuple, Dict, Any


def compute_capacity(experience_index, alpha=2.0):
    """
    Cognitive capacity: Ψ(x; α) = sigmoid(α * x)
    
    Args:
        experience_index: Agent's experience-based capacity [0, ∞)
        alpha: Sensitivity parameter (default: 2.0)
    
    Returns:
        Cognitive capacity [0, 1]
    """
    z = alpha * experience_index
    if z > 20:
        return 1.0
    elif z < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


def compute_opportunity(conflict_intensity, beta=2.0):
    """
    Structural opportunity: Ω(c; β) = sigmoid(β * (1 - c))
    
    Args:
        conflict_intensity: Threat level [0, 1], where 1 = extreme threat
        beta: Sensitivity parameter (default: 2.0)
    
    Returns:
        Structural opportunity [0, 1]
    """
    z = beta * (1.0 - conflict_intensity)
    if z > 20:
        return 1.0
    elif z < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


def compute_deliberation_probability(experience_index, conflict_intensity, alpha=2.0, beta=2.0):
    """
    Deliberation probability: P_S2 = Ψ × Ω
    
    This is the core of the model - multiplicative form based on necessary conditions logic.
    """
    psi = compute_capacity(experience_index, alpha)
    omega = compute_opportunity(conflict_intensity, beta)
    return psi * omega


def calculate_move_probability_s1s2(
    experience_index: float,
    conflict: float,
    movechance: float,
    alpha: float = 2.0,
    beta: float = 2.0,
    p_s2: float = 0.8
) -> Tuple[float, float]:
    """
    Parsimonious dual-process S1/S2 model.
    
    Args:
        experience_index: Experience-based capacity index x
        conflict: Location conflict intensity [0, 1]
        movechance: Location movechance [0, 1] (S1 probability)
        alpha: Cognitive capacity weight
        beta: Structural opportunity weight
        p_s2: S2 move probability (FIXED parameter, default: 0.8)
    
    Returns:
        (p_move, p_s2_active): final move probability and S2 activation probability
    """
    p_s2_active = compute_deliberation_probability(experience_index, conflict, alpha, beta)
    
    # Weighted combination of S1 and S2 move probabilities
    p_move = (1.0 - p_s2_active) * movechance + p_s2_active * p_s2
    
    return p_move, p_s2_active


def calculate_experience_index(
    prior_displacement: float = 0.0,
    local_knowledge: float = 0.0,
    conflict_exposure: float = 0.0,
    connections: int = 0,
    age_factor: float = 0.5,
    education_level: float = 0.5
) -> float:
    """
    Calculate experience-based capacity index x.
    
    Weights match emphasis on experience over education.
    
    Args:
        prior_displacement: Days/timesteps since departure (normalized)
        local_knowledge: Knowledge of local area/route [0, 1]
        conflict_exposure: Prior exposure to conflict situations [0, 1]
        connections: Number of social connections (normalized to [0, 1])
        age_factor: Age-related experience factor [0, 1]
        education_level: Education level [0, 1]
        
    Returns:
        Experience index x
    """
    x = (
        prior_displacement * 0.25 +      # Travel experience
        local_knowledge * 0.25 +          # Local knowledge
        conflict_exposure * 0.20 +        # Conflict experience
        min(connections / 10.0, 1.0) * 0.15 +  # Social connections
        age_factor * 0.10 +               # Age/experience
        education_level * 0.05             # Education
    )
    return x
