#!/usr/bin/env python3
"""
Refactored S1/S2 dual-process decision-making implementation for FLEE.

Implements exact mathematical specifications with configurable parameters.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional


def clip(x: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clip value to bounds [min_val, max_val]."""
    return max(min_val, min(max_val, x))


def sigmoid(x: float, steepness: float = 6.0) -> float:
    """Sigmoid function: 1/(1+exp(-steepness*x))."""
    return 1.0 / (1.0 + math.exp(-steepness * x))


def connectivity_factor(connections: int, mode: str = "baseline") -> float:
    """
    Calculate connectivity factor fc.
    
    Args:
        connections: Number of connections (c)
        mode: "baseline" or "diminishing"
    
    Returns:
        fc: connectivity factor [0, 1]
    """
    if mode == "baseline":
        return clip(connections / 10.0)  # fc = min(1, c/10)
    elif mode == "diminishing":
        return connections / (1.0 + connections)  # fc_star = c/(1+c)
    else:
        raise ValueError(f"Unknown connectivity mode: {mode}")


def base_pressure(time: int, fc: float) -> float:
    """
    Calculate base pressure B(t).
    
    Formula: B(t) = min(0.4, 0.2*fc + 0.1*(1-exp(-t/10))*exp(-t/50))
    
    Args:
        time: Current time t
        fc: connectivity factor
    
    Returns:
        B(t): base pressure [0, 0.4]
    """
    time_stress = 0.1 * (1.0 - math.exp(-time / 10.0)) * math.exp(-time / 50.0)
    return clip(0.2 * fc + time_stress, max_val=0.4)


def conflict_pressure(time: int, conflict_intensity: float, fc: float, 
                     conflict_start_time: int = 0) -> float:
    """
    Calculate conflict pressure C(t).
    
    Formula: C(t) = min(0.4, I(t)*fc*exp(-max(0,t-tc)/20))
    
    Args:
        time: Current time t
        conflict_intensity: I(t) - conflict intensity [0, 1]
        fc: connectivity factor
        conflict_start_time: tc - when conflict started
    
    Returns:
        C(t): conflict pressure [0, 0.4]
    """
    # If conflict hasn't started yet, return 0
    if time < conflict_start_time:
        return 0.0
    
    time_since_conflict = time - conflict_start_time
    decay_factor = math.exp(-time_since_conflict / 20.0)
    return clip(conflict_intensity * fc * decay_factor, max_val=0.4)


def social_pressure(fc: float) -> float:
    """
    Calculate social pressure S(t).
    
    Formula: S(t) = min(0.2, 0.1*fc)
    
    Args:
        fc: connectivity factor
    
    Returns:
        S(t): social pressure [0, 0.2]
    """
    return clip(0.1 * fc, max_val=0.2)


def total_pressure(time: int, conflict_intensity: float, connections: int,
                  connectivity_mode: str = "baseline", 
                  conflict_start_time: int = 0) -> float:
    """
    Calculate total cognitive pressure P(t).
    
    Formula: P(t) = min(1, B(t) + C(t) + S(t))
    
    Args:
        time: Current time t
        conflict_intensity: I(t) - conflict intensity [0, 1]
        connections: Number of connections c
        connectivity_mode: "baseline" or "diminishing"
        conflict_start_time: tc - when conflict started
    
    Returns:
        P(t): total pressure [0, 1]
    """
    fc = connectivity_factor(connections, connectivity_mode)
    
    B = base_pressure(time, fc)
    C = conflict_pressure(time, conflict_intensity, fc, conflict_start_time)
    S = social_pressure(fc)
    
    return clip(B + C + S)


def base_sigmoid(pressure: float, threshold: float, steepness: float = 6.0) -> float:
    """
    Calculate base sigmoid probability.
    
    Formula: base = 1/(1+exp(-6*(P(t)-theta_i)))
    
    Args:
        pressure: P(t) - total pressure
        threshold: theta_i - individual threshold
        steepness: k - sigmoid steepness (default 6.0)
    
    Returns:
        base: base probability [0, 1]
    """
    return sigmoid(pressure - threshold, steepness)


def modifiers(education: float, stress_tolerance: float, connections: int, time: int) -> float:
    """
    Calculate individual modifiers.
    
    Formula: modifiers = 0.05*e + 0.03*tau + min(0.01*c,0.05) - min(0.001*t,0.03) + min(0.002*t,0.05)
    
    Args:
        education: e - education level [0, 1]
        stress_tolerance: tau - stress tolerance [0, 1]
        connections: c - number of connections
        time: t - current time
    
    Returns:
        modifiers: combined modifiers
    """
    education_boost = 0.05 * education
    stress_boost = 0.03 * stress_tolerance
    social_support = clip(0.01 * connections, max_val=0.05)
    fatigue_penalty = clip(0.001 * time, max_val=0.03)
    learning_boost = clip(0.002 * time, max_val=0.05)
    
    return education_boost + stress_boost + social_support - fatigue_penalty + learning_boost


def hard_capability_gate(connections: int, timesteps_since_departure: int, 
                        education: float) -> bool:
    """
    Hard capability gate: HARD OR condition.
    
    Formula: 1[c≥1] OR 1[Δt≥3] OR 1[e≥0.3]
    
    Args:
        connections: c - number of connections
        timesteps_since_departure: Δt - time since departure
        education: e - education level [0, 1]
    
    Returns:
        True if agent is S2 capable
    """
    return (connections >= 1) or (timesteps_since_departure >= 3) or (education >= 0.3)


def soft_capability_gate(connections: int, timesteps_since_departure: int, 
                        education: float, steepness: float = 8.0) -> float:
    """
    Soft capability gate: continuous probability.
    
    Formula: soft_OR = 1 - (1-sig(c-0.5))(1-sig(Δt-3))(1-sig(e-0.3))
    
    Args:
        connections: c - number of connections
        timesteps_since_departure: Δt - time since departure
        education: e - education level [0, 1]
        steepness: a - sigmoid steepness [6, 12]
    
    Returns:
        Soft capability probability [0, 1]
    """
    sig_c = sigmoid(connections - 0.5, steepness)
    sig_t = sigmoid(timesteps_since_departure - 3, steepness)
    sig_e = sigmoid(education - 0.3, steepness)
    
    return 1.0 - (1.0 - sig_c) * (1.0 - sig_t) * (1.0 - sig_e)


def s2_activation_probability(pressure: float, threshold: float, 
                            education: float, stress_tolerance: float,
                            connections: int, time: int,
                            capability_gate: float = 1.0,
                            steepness: float = 6.0) -> float:
    """
    Calculate S2 activation probability.
    
    Formula: pS2 = gate * clip(base + modifiers, 0, 1)
    
    Args:
        pressure: P(t) - total pressure
        threshold: theta_i - individual threshold
        education: e - education level [0, 1]
        stress_tolerance: tau - stress tolerance [0, 1]
        connections: c - number of connections
        time: t - current time
        capability_gate: gate - capability gate value [0, 1]
        steepness: k - sigmoid steepness
    
    Returns:
        pS2: S2 activation probability [0, 1]
    """
    base = base_sigmoid(pressure, threshold, steepness)
    mods = modifiers(education, stress_tolerance, connections, time)
    
    return capability_gate * clip(base + mods)


def s2_move_probability(pressure: float, location_movechance: float, 
                       eta: float = 0.5) -> float:
    """
    Calculate S2 move probability.
    
    Formula: clip(mu_loc*(1 + eta*P(t)), 0, 1)
    
    Args:
        pressure: P(t) - total pressure
        location_movechance: mu_loc - base location move chance
        eta: scaling factor [0.2, 0.8]
    
    Returns:
        S2 move probability [0, 1]
    """
    eta = clip(eta, 0.2, 0.8)  # Ensure eta in [0.2, 0.8]
    return clip(location_movechance * (1.0 + eta * pressure))


def combined_move_probability(s1_move_prob: float, s2_move_prob: float, 
                            s2_activation_prob: float) -> float:
    """
    Calculate combined move probability.
    
    Formula: pmove = (1 - pS2)*pmove_S1 + pS2*pmove_S2
    
    Args:
        s1_move_prob: pmove_S1 - S1 move probability
        s2_move_prob: pmove_S2 - S2 move probability
        s2_activation_prob: pS2 - S2 activation probability
    
    Returns:
        Combined move probability [0, 1]
    """
    return (1.0 - s2_activation_prob) * s1_move_prob + s2_activation_prob * s2_move_prob


class S1S2Config:
    """Configuration for S1/S2 system."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize with default configuration."""
        defaults = {
            "connectivity_mode": "baseline",  # "baseline" or "diminishing"
            "soft_capability": False,  # True for soft gate, False for hard gate
            "pmove_s2_mode": "scaled",  # "scaled" or "constant"
            "pmove_s2_constant": 0.9,  # Fixed value for constant mode [0.8, 0.95]
            "eta": 0.5,  # Scaling factor for scaled mode [0.2, 0.8]
            "steepness": 6.0,  # Sigmoid steepness
            "soft_gate_steepness": 8.0,  # Steepness for soft capability gate [6, 12]
        }
        
        self.config = defaults.copy()
        if config_dict:
            self.config.update(config_dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)


def calculate_s1s2_move_probability(
    time: int,
    conflict_intensity: float,
    connections: int,
    timesteps_since_departure: int,
    education: float,
    stress_tolerance: float,
    threshold: float,
    location_movechance: float,
    s1_move_prob: float,
    config: S1S2Config,
    conflict_start_time: int = 0
) -> Tuple[float, float, bool]:
    """
    Calculate S1/S2 move probability with exact mathematical specifications.
    
    Args:
        time: Current time t
        conflict_intensity: I(t) - conflict intensity [0, 1]
        connections: c - number of connections
        timesteps_since_departure: Δt - time since departure
        education: e - education level [0, 1]
        stress_tolerance: tau - stress tolerance [0, 1]
        threshold: theta_i - individual threshold
        location_movechance: mu_loc - base location move chance
        s1_move_prob: pmove_S1 - S1 move probability
        config: S1S2Config - configuration object
        conflict_start_time: tc - when conflict started
    
    Returns:
        Tuple of (move_probability, s2_activation_prob, s2_active)
    """
    # Calculate total pressure
    pressure = total_pressure(
        time, conflict_intensity, connections,
        config.get("connectivity_mode"), conflict_start_time
    )
    
    # Calculate capability gate
    if config.get("soft_capability", False):
        capability_gate = soft_capability_gate(
            connections, timesteps_since_departure, education,
            config.get("soft_gate_steepness", 8.0)
        )
    else:
        capability_gate = 1.0 if hard_capability_gate(
            connections, timesteps_since_departure, education
        ) else 0.0
    
    # Calculate S2 activation probability
    s2_activation_prob = s2_activation_probability(
        pressure, threshold, education, stress_tolerance,
        connections, time, capability_gate, config.get("steepness", 6.0)
    )
    
    # Calculate S2 move probability
    if config.get("pmove_s2_mode") == "constant":
        s2_move_prob = config.get("pmove_s2_constant", 0.9)
    else:  # "scaled"
        s2_move_prob = s2_move_probability(
            pressure, location_movechance, config.get("eta", 0.5)
        )
    
    # Calculate combined move probability
    move_prob = combined_move_probability(s1_move_prob, s2_move_prob, s2_activation_prob)
    
    # Determine if S2 is active (for logging/tracking)
    s2_active = s2_activation_prob > 0.5  # Threshold for "active"
    
    return move_prob, s2_activation_prob, s2_active
