#!/usr/bin/env python3
"""
Unit tests for refactored S1/S2 implementation.

Tests exact mathematical specifications and bounds.
"""

import pytest
import numpy as np
from s1s2_refactored import (
    clip, sigmoid, connectivity_factor, base_pressure, conflict_pressure,
    social_pressure, total_pressure, base_sigmoid, modifiers,
    hard_capability_gate, soft_capability_gate, s2_activation_probability,
    s2_move_probability, combined_move_probability, S1S2Config,
    calculate_s1s2_move_probability
)


class TestBasicFunctions:
    """Test basic utility functions."""
    
    def test_clip(self):
        """Test clipping function."""
        assert clip(0.5) == 0.5
        assert clip(-0.1) == 0.0
        assert clip(1.5) == 1.0
        assert clip(0.3, 0.2, 0.8) == 0.3
        assert clip(0.1, 0.2, 0.8) == 0.2
        assert clip(0.9, 0.2, 0.8) == 0.8
    
    def test_sigmoid(self):
        """Test sigmoid function."""
        assert sigmoid(0.0) == 0.5
        assert sigmoid(100.0) == pytest.approx(1.0, abs=1e-10)
        assert sigmoid(-100.0) == pytest.approx(0.0, abs=1e-10)
        assert sigmoid(1.0, 6.0) == pytest.approx(0.9975, abs=1e-3)


class TestConnectivityFactor:
    """Test connectivity factor calculations."""
    
    def test_baseline_mode(self):
        """Test baseline connectivity mode."""
        assert connectivity_factor(0, "baseline") == 0.0
        assert connectivity_factor(5, "baseline") == 0.5
        assert connectivity_factor(10, "baseline") == 1.0
        assert connectivity_factor(15, "baseline") == 1.0
    
    def test_diminishing_mode(self):
        """Test diminishing connectivity mode."""
        assert connectivity_factor(0, "diminishing") == 0.0
        assert connectivity_factor(1, "diminishing") == 0.5
        assert connectivity_factor(2, "diminishing") == pytest.approx(2/3, abs=1e-10)
        assert connectivity_factor(10, "diminishing") == pytest.approx(10/11, abs=1e-10)


class TestPressureComponents:
    """Test pressure component calculations."""
    
    def test_base_pressure_bounds(self):
        """Test base pressure is bounded [0, 0.4]."""
        for t in range(0, 200, 10):
            for fc in [0.0, 0.5, 1.0]:
                B = base_pressure(t, fc)
                assert 0.0 <= B <= 0.4, f"Base pressure {B} out of bounds at t={t}, fc={fc}"
    
    def test_base_pressure_monotonicity(self):
        """Test base pressure increases with connectivity."""
        t = 10
        B1 = base_pressure(t, 0.5)
        B2 = base_pressure(t, 0.8)
        assert B2 >= B1, "Base pressure should increase with connectivity"
    
    def test_conflict_pressure_bounds(self):
        """Test conflict pressure is bounded [0, 0.4]."""
        for t in range(0, 100, 10):
            for I in [0.0, 0.5, 1.0]:
                for fc in [0.0, 0.5, 1.0]:
                    C = conflict_pressure(t, I, fc)
                    assert 0.0 <= C <= 0.4, f"Conflict pressure {C} out of bounds"
    
    def test_conflict_pressure_monotonicity(self):
        """Test conflict pressure increases with intensity."""
        t, fc = 10, 0.5
        C1 = conflict_pressure(t, 0.3, fc)
        C2 = conflict_pressure(t, 0.7, fc)
        assert C2 >= C1, "Conflict pressure should increase with intensity"
    
    def test_conflict_pressure_decay(self):
        """Test conflict pressure decays after conflict start."""
        I, fc = 1.0, 0.5
        tc = 10
        
        C_before = conflict_pressure(5, I, fc, tc)  # Before conflict
        C_during = conflict_pressure(10, I, fc, tc)  # At conflict start
        C_after = conflict_pressure(20, I, fc, tc)  # After conflict
        
        assert C_before == 0.0, "No conflict pressure before conflict starts"
        assert C_during > 0.0, "Conflict pressure should be positive at start"
        assert C_after < C_during, "Conflict pressure should decay after start"
    
    def test_social_pressure_bounds(self):
        """Test social pressure is bounded [0, 0.2]."""
        for fc in [0.0, 0.5, 1.0, 2.0]:
            S = social_pressure(fc)
            assert 0.0 <= S <= 0.2, f"Social pressure {S} out of bounds"
    
    def test_total_pressure_bounds(self):
        """Test total pressure is bounded [0, 1]."""
        for t in range(0, 100, 10):
            for I in [0.0, 0.5, 1.0]:
                for c in [0, 5, 10]:
                    P = total_pressure(t, I, c)
                    assert 0.0 <= P <= 1.0, f"Total pressure {P} out of bounds"


class TestCapabilityGates:
    """Test capability gate functions."""
    
    def test_hard_capability_gate(self):
        """Test hard capability gate logic."""
        # Should be True: connections >= 1
        assert hard_capability_gate(1, 0, 0.0) == True
        assert hard_capability_gate(5, 0, 0.0) == True
        
        # Should be True: timesteps >= 3
        assert hard_capability_gate(0, 3, 0.0) == True
        assert hard_capability_gate(0, 5, 0.0) == True
        
        # Should be True: education >= 0.3
        assert hard_capability_gate(0, 0, 0.3) == True
        assert hard_capability_gate(0, 0, 0.5) == True
        
        # Should be False: none of the conditions met
        assert hard_capability_gate(0, 0, 0.0) == False
        assert hard_capability_gate(0, 1, 0.2) == False
        assert hard_capability_gate(0, 2, 0.2) == False
    
    def test_soft_capability_gate_bounds(self):
        """Test soft capability gate is bounded [0, 1]."""
        for c in range(0, 10):
            for t in range(0, 10):
                for e in [0.0, 0.2, 0.5, 0.8]:
                    gate = soft_capability_gate(c, t, e)
                    assert 0.0 <= gate <= 1.0, f"Soft gate {gate} out of bounds"
    
    def test_soft_capability_gate_continuity(self):
        """Test soft capability gate is continuous."""
        # Test continuity around thresholds
        gate1 = soft_capability_gate(0.4, 2.5, 0.25)
        gate2 = soft_capability_gate(0.6, 3.5, 0.35)
        
        # Should be smooth transition, not discrete
        assert abs(gate2 - gate1) < 1.0, "Soft gate should be continuous"


class TestModifiers:
    """Test modifier calculations."""
    
    def test_modifiers_bounds(self):
        """Test modifiers are bounded."""
        for e in [0.0, 0.5, 1.0]:
            for tau in [0.0, 0.5, 1.0]:
                for c in range(0, 20):
                    for t in range(0, 200):
                        mods = modifiers(e, tau, c, t)
                        # Modifiers can be negative (fatigue penalty)
                        assert -0.1 <= mods <= 0.2, f"Modifiers {mods} out of reasonable bounds"


class TestS2Activation:
    """Test S2 activation probability."""
    
    def test_s2_activation_bounds(self):
        """Test S2 activation probability is bounded [0, 1]."""
        for pressure in [0.0, 0.3, 0.5, 0.7, 1.0]:
            for threshold in [0.3, 0.5, 0.7]:
                for gate in [0.0, 0.5, 1.0]:
                    prob = s2_activation_probability(
                        pressure, threshold, 0.5, 0.5, 5, 10, gate
                    )
                    assert 0.0 <= prob <= 1.0, f"S2 activation {prob} out of bounds"
    
    def test_s2_activation_gate_effect(self):
        """Test capability gate affects S2 activation."""
        pressure, threshold = 0.6, 0.5
        
        prob_no_gate = s2_activation_probability(
            pressure, threshold, 0.5, 0.5, 5, 10, 0.0
        )
        prob_full_gate = s2_activation_probability(
            pressure, threshold, 0.5, 0.5, 5, 10, 1.0
        )
        
        assert prob_no_gate == 0.0, "No gate should give zero probability"
        assert prob_full_gate > 0.0, "Full gate should give positive probability"


class TestMoveProbabilities:
    """Test move probability calculations."""
    
    def test_s2_move_probability_bounds(self):
        """Test S2 move probability is bounded [0, 1]."""
        for pressure in [0.0, 0.5, 1.0]:
            for mu_loc in [0.0, 0.3, 0.8]:
                for eta in [0.2, 0.5, 0.8]:
                    prob = s2_move_probability(pressure, mu_loc, eta)
                    assert 0.0 <= prob <= 1.0, f"S2 move prob {prob} out of bounds"
    
    def test_combined_move_probability_bounds(self):
        """Test combined move probability is bounded [0, 1]."""
        for s1_prob in [0.0, 0.3, 0.8]:
            for s2_prob in [0.0, 0.5, 1.0]:
                for s2_activation in [0.0, 0.3, 0.7, 1.0]:
                    prob = combined_move_probability(s1_prob, s2_prob, s2_activation)
                    assert 0.0 <= prob <= 1.0, f"Combined move prob {prob} out of bounds"
    
    def test_combined_move_probability_extremes(self):
        """Test combined move probability at extremes."""
        # Pure S1 (s2_activation = 0)
        prob = combined_move_probability(0.3, 0.8, 0.0)
        assert prob == 0.3, "Pure S1 should return S1 probability"
        
        # Pure S2 (s2_activation = 1)
        prob = combined_move_probability(0.3, 0.8, 1.0)
        assert prob == 0.8, "Pure S2 should return S2 probability"


class TestConfiguration:
    """Test configuration system."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = S1S2Config()
        assert config.get("connectivity_mode") == "baseline"
        assert config.get("soft_capability") == False
        assert config.get("pmove_s2_mode") == "scaled"
        assert config.get("eta") == 0.5
    
    def test_custom_config(self):
        """Test custom configuration values."""
        custom = {
            "connectivity_mode": "diminishing",
            "soft_capability": True,
            "eta": 0.7
        }
        config = S1S2Config(custom)
        assert config.get("connectivity_mode") == "diminishing"
        assert config.get("soft_capability") == True
        assert config.get("eta") == 0.7
        assert config.get("pmove_s2_mode") == "scaled"  # Default preserved


class TestIntegration:
    """Test integrated S1/S2 calculation."""
    
    def test_integration_bounds(self):
        """Test integrated calculation produces bounded results."""
        config = S1S2Config()
        
        for t in range(0, 50, 10):
            move_prob, s2_activation, s2_active = calculate_s1s2_move_probability(
                time=t,
                conflict_intensity=0.5,
                connections=5,
                timesteps_since_departure=3,
                education=0.6,
                stress_tolerance=0.5,
                threshold=0.5,
                location_movechance=0.3,
                s1_move_prob=0.2,
                config=config
            )
            
            assert 0.0 <= move_prob <= 1.0, f"Move probability {move_prob} out of bounds"
            assert 0.0 <= s2_activation <= 1.0, f"S2 activation {s2_activation} out of bounds"
            assert isinstance(s2_active, bool), "S2 active should be boolean"
    
    def test_connectivity_mode_effect(self):
        """Test connectivity mode affects results."""
        config_baseline = S1S2Config({"connectivity_mode": "baseline"})
        config_diminishing = S1S2Config({"connectivity_mode": "diminishing"})
        
        move_prob1, _, _ = calculate_s1s2_move_probability(
            time=10, conflict_intensity=0.5, connections=5,
            timesteps_since_departure=3, education=0.6, stress_tolerance=0.5,
            threshold=0.5, location_movechance=0.3, s1_move_prob=0.2,
            config=config_baseline
        )
        
        move_prob2, _, _ = calculate_s1s2_move_probability(
            time=10, conflict_intensity=0.5, connections=5,
            timesteps_since_departure=3, education=0.6, stress_tolerance=0.5,
            threshold=0.5, location_movechance=0.3, s1_move_prob=0.2,
            config=config_diminishing
        )
        
        # Results should be different for different connectivity modes
        assert move_prob1 != move_prob2, "Different connectivity modes should give different results"
    
    def test_pmove_s2_mode_effect(self):
        """Test S2 move probability mode affects results."""
        config_scaled = S1S2Config({"pmove_s2_mode": "scaled"})
        config_constant = S1S2Config({"pmove_s2_mode": "constant", "pmove_s2_constant": 0.9})
        
        move_prob1, _, _ = calculate_s1s2_move_probability(
            time=10, conflict_intensity=0.5, connections=5,
            timesteps_since_departure=3, education=0.6, stress_tolerance=0.5,
            threshold=0.5, location_movechance=0.3, s1_move_prob=0.2,
            config=config_scaled
        )
        
        move_prob2, _, _ = calculate_s1s2_move_probability(
            time=10, conflict_intensity=0.5, connections=5,
            timesteps_since_departure=3, education=0.6, stress_tolerance=0.5,
            threshold=0.5, location_movechance=0.3, s1_move_prob=0.2,
            config=config_constant
        )
        
        # Results should be different for different S2 move modes
        assert move_prob1 != move_prob2, "Different S2 move modes should give different results"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])




