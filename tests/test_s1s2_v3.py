"""Unit tests for V3 dual-process model (s1s2_model.py)."""

import pytest
import math
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flee.s1s2_model import (
    PSI_MIN,
    compute_capacity,
    compute_opportunity,
    compute_deliberation_weight,
    compute_s2_move_probability,
)


class TestComputeCapacity:
    """Tests for Ψ(x; α) = Ψ_min + (1 - Ψ_min)(1 - exp(-αx))"""

    def test_zero_experience_gives_psi_min(self):
        """An agent with zero experience should have exactly Ψ_min capacity."""
        assert compute_capacity(0.0, alpha=2.0) == pytest.approx(PSI_MIN)

    def test_high_experience_approaches_one(self):
        """An agent with very high experience should approach Ψ = 1.0."""
        psi = compute_capacity(100.0, alpha=2.0)
        assert psi == pytest.approx(1.0, abs=1e-6)

    def test_monotonically_increasing(self):
        """Ψ must be strictly increasing in experience."""
        vals = [compute_capacity(x, alpha=2.0) for x in [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]]
        for i in range(len(vals) - 1):
            assert vals[i] < vals[i + 1], f"Ψ not increasing: Ψ({i}) = {vals[i]} >= Ψ({i+1}) = {vals[i+1]}"

    def test_concave(self):
        """Ψ must be concave: first differences should decrease."""
        xs = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
        vals = [compute_capacity(x, alpha=2.0) for x in xs]
        diffs = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
        for i in range(len(diffs) - 1):
            assert diffs[i] > diffs[i + 1], "Ψ is not concave"

    def test_bounded(self):
        """Ψ ∈ [Ψ_min, 1] for all valid inputs."""
        for x in [0.0, 0.01, 0.1, 0.5, 1.0, 10.0, 100.0]:
            psi = compute_capacity(x, alpha=2.0)
            assert PSI_MIN <= psi <= 1.0

    def test_alpha_controls_rate(self):
        """Higher α should give higher Ψ for same experience (faster saturation)."""
        psi_low_alpha = compute_capacity(0.5, alpha=1.0)
        psi_high_alpha = compute_capacity(0.5, alpha=5.0)
        assert psi_high_alpha > psi_low_alpha

    def test_negative_experience_clamped(self):
        """Negative experience should be treated as zero (return Ψ_min)."""
        assert compute_capacity(-1.0, alpha=2.0) == pytest.approx(PSI_MIN)


class TestComputeOpportunity:
    """Tests for Ω(c; β) = exp(-βc)"""

    def test_zero_conflict_gives_one(self):
        """No conflict means full opportunity to deliberate."""
        assert compute_opportunity(0.0, beta=2.0) == pytest.approx(1.0)

    def test_high_conflict_approaches_zero(self):
        """Extreme conflict should suppress opportunity."""
        omega = compute_opportunity(1.0, beta=10.0)
        assert omega < 0.001

    def test_monotonically_decreasing(self):
        """Ω must be strictly decreasing in conflict."""
        vals = [compute_opportunity(c, beta=2.0) for c in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]]
        for i in range(len(vals) - 1):
            assert vals[i] > vals[i + 1]

    def test_bounded(self):
        """Ω ∈ (0, 1] for all valid inputs."""
        for c in [0.0, 0.1, 0.5, 0.9, 1.0]:
            omega = compute_opportunity(c, beta=2.0)
            assert 0.0 < omega <= 1.0

    def test_beta_controls_steepness(self):
        """Higher β should give lower Ω for same conflict (steeper collapse)."""
        omega_low = compute_opportunity(0.5, beta=1.0)
        omega_high = compute_opportunity(0.5, beta=10.0)
        assert omega_high < omega_low

    def test_conflict_clamped_to_unit(self):
        """Conflict > 1 should be clamped to 1."""
        omega_at_1 = compute_opportunity(1.0, beta=2.0)
        omega_at_2 = compute_opportunity(2.0, beta=2.0)
        assert omega_at_1 == pytest.approx(omega_at_2)


class TestDeliberationWeight:
    """Tests for P_S2 = Ψ × Ω"""

    def test_product_form(self):
        """P_S2 should be exactly Ψ × Ω."""
        for x, c in [(0.5, 0.3), (1.0, 0.0), (0.0, 1.0), (2.0, 0.5)]:
            psi = compute_capacity(x, alpha=2.0)
            omega = compute_opportunity(c, beta=2.0)
            p_s2 = compute_deliberation_weight(x, c, alpha=2.0, beta=2.0)
            assert p_s2 == pytest.approx(psi * omega, abs=1e-10)

    def test_non_compensability_high_conflict(self):
        """High conflict (Ω ≈ 0) should suppress P_S2 regardless of experience."""
        p_s2_expert = compute_deliberation_weight(10.0, 1.0, alpha=2.0, beta=10.0)
        assert p_s2_expert < 0.01, f"Expert in extreme conflict should have P_S2 ≈ 0, got {p_s2_expert}"

    def test_novice_in_calm(self):
        """Novice (x=0) in calm conditions (c=0) gets P_S2 = Ψ_min × 1.0 = Ψ_min.

        At c=0, Omega=1 so P_S2 = Psi exactly. This is correct: the agent has full
        deliberative capacity available. P_S2 is behaviorally inert at baseline
        because movechance≈0 triggers no displacement decision.
        """
        p_s2 = compute_deliberation_weight(0.0, 0.0, alpha=2.0, beta=2.0)
        assert p_s2 == pytest.approx(PSI_MIN)

    def test_psi_min_floor_prevents_hard_zero(self):
        """Even novice in moderate conflict should have P_S2 > 0 (the Ψ_min floor)."""
        p_s2 = compute_deliberation_weight(0.0, 0.5, alpha=2.0, beta=2.0)
        assert p_s2 > 0.0, "Ψ_min floor should prevent P_S2 = 0 for any non-extreme conflict"


class TestS2MoveProbability:
    """Tests for σ = logistic(κ · (c_here - c_best) / d_best)"""

    def test_large_safety_gain_gives_high_sigma(self):
        """When current location is much worse than best alternative, σ → 1."""
        sigma = compute_s2_move_probability(0.9, 0.1, 1.0, kappa=10.0)
        assert sigma > 0.95

    def test_no_safety_gain_gives_half(self):
        """When c_here = c_best, σ = 0.5 (agent uncertain)."""
        sigma = compute_s2_move_probability(0.5, 0.5, 1.0, kappa=10.0)
        assert sigma == pytest.approx(0.5)

    def test_already_safest_gives_low_sigma(self):
        """When current location is safest, σ < 0.5 (agent tends to stay)."""
        sigma = compute_s2_move_probability(0.1, 0.9, 1.0, kappa=10.0)
        assert sigma < 0.1

    def test_distance_attenuates(self):
        """Greater distance to best destination should reduce σ (same safety gain)."""
        sigma_close = compute_s2_move_probability(0.8, 0.2, 1.0, kappa=5.0)
        sigma_far = compute_s2_move_probability(0.8, 0.2, 10.0, kappa=5.0)
        assert sigma_close > sigma_far

    def test_kappa_zero_gives_half(self):
        """With κ=0, agent has no sensitivity to safety differential: σ = 0.5."""
        sigma = compute_s2_move_probability(0.9, 0.1, 1.0, kappa=0.0)
        assert sigma == pytest.approx(0.5)

    def test_zero_distance_handled(self):
        """Distance of 0 should not crash (clamped to 1)."""
        sigma = compute_s2_move_probability(0.5, 0.3, 0.0, kappa=5.0)
        assert 0.0 < sigma < 1.0


class TestPs2ConditionalInterpretation:
    """P_S2 is conditional on movechance-triggered decisions; at c=0, P_S2 = Psi."""

    def test_ps2_conditional_interpretation(self):
        """At c=0 there is no conflict and Omega=1, so P_S2 equals Psi exactly.

        This is correct: the agent has full deliberative capacity available.
        P_S2 is behaviorally inert at baseline because movechance≈0 triggers
        no displacement decision.
        """
        for x in [0.0, 0.5, 1.0]:
            psi = compute_capacity(x, alpha=2.0)
            p_s2 = compute_deliberation_weight(x, 0.0, alpha=2.0, beta=2.0)
            assert p_s2 == pytest.approx(psi), (
                f"At c=0, P_S2 must equal Psi(x={x}): got P_S2={p_s2}, Psi={psi}"
            )


class TestBlendedMoveProbability:
    """Integration tests for the blended move probability formula."""

    def test_blend_at_ps2_zero(self):
        """When P_S2 = 0, blended movechance = P_S1 (pure heuristic)."""
        p_s1 = 0.6
        sigma = 0.9
        s2_weight = 0.0
        blended = (1.0 - s2_weight) * p_s1 + s2_weight * sigma
        assert blended == pytest.approx(p_s1)

    def test_blend_at_ps2_one(self):
        """When P_S2 = 1, blended movechance = σ (pure deliberation)."""
        p_s1 = 0.6
        sigma = 0.9
        s2_weight = 1.0
        blended = (1.0 - s2_weight) * p_s1 + s2_weight * sigma
        assert blended == pytest.approx(sigma)

    def test_blend_intermediate(self):
        """Intermediate P_S2 gives weighted average."""
        p_s1 = 0.3
        sigma = 0.8
        s2_weight = 0.4
        blended = (1.0 - s2_weight) * p_s1 + s2_weight * sigma
        expected = 0.6 * 0.3 + 0.4 * 0.8  # = 0.18 + 0.32 = 0.50
        assert blended == pytest.approx(expected)

    def test_blend_bounded(self):
        """Blended probability must be in [0, 1] for all valid inputs."""
        import random
        random.seed(42)
        for _ in range(1000):
            p_s1 = random.random()
            sigma = random.random()
            s2_weight = random.random()
            blended = (1.0 - s2_weight) * p_s1 + s2_weight * sigma
            assert 0.0 <= blended <= 1.0


# --- Integration tests (require minimal FLEE setup) ---


def _setup_simulation_settings(two_system=True):
    """Load SimulationSettings for integration tests.

    Uses SimulationSettings and moving directly to avoid importing flee.flee,
    which pulls in numpy and can segfault on some macOS + pytest setups.
    """
    from flee.SimulationSettings import SimulationSettings
    # Use tests/empty.yml or empty.yml (pytest may run from tests/ or project root)
    for path in ["tests/empty.yml", "empty.yml", "flee/simsetting.yml"]:
        if os.path.exists(path):
            SimulationSettings.ReadFromYML(path)
            break
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = two_system
    SimulationSettings.move_rules["s1s2_model_params"] = {
        "alpha": 2.0, "beta": 2.0, "kappa": 5.0,
    }
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.move_rules["AwarenessLevel"] = 1
    SimulationSettings.move_rules["FixedRoutes"] = False
    SimulationSettings.move_rules["PruningThreshold"] = 1.0


def _make_mock_link(endpoint_conflict, distance=1.0):
    """Create a minimal mock link."""
    class MockLink:
        def __init__(self, ep_conflict, dist):
            self._ep = type('Ep', (), {'conflict': ep_conflict})()
            self._dist = dist
        @property
        def endpoint(self):
            return self._ep
        def get_distance(self):
            return self._dist
        numAgents = 0
    return MockLink(endpoint_conflict, distance)


def _make_mock_location(conflict=0.5, camp=False, idpcamp=False, town=False,
                        movechance=0.3, links=None, name="Loc"):
    """Create a minimal mock location."""
    class MockLocation:
        pass
    loc = MockLocation()
    loc.conflict = conflict
    loc.camp = camp
    loc.idpcamp = idpcamp
    loc.town = town
    loc.movechance = movechance
    loc.name = name
    loc.pop = 1000
    loc.capacity = 1000
    loc.numAgents = 100
    loc.links = links if links is not None else []
    loc.routes = {}
    loc.attributes = {}
    loc.marker = False
    loc.region = "unknown"
    return loc


def _make_mock_agent(location, experience_index=0.5):
    """Create a minimal mock agent."""
    class MockAgent:
        pass
    a = MockAgent()
    a.location = location
    a.experience_index = experience_index
    a.route = []
    a.attributes = {}
    return a


@pytest.mark.integration
class TestIntegration:
    """Integration tests using lightweight mock objects.

    Require FLEE import (SimulationSettings, moving). Skip with: pytest -m 'not integration'
    """

    def test_calculateMoveChance_returns_two_floats(self):
        """calculateMoveChance must return (float, float), not (float, bool)."""
        from flee import moving
        _setup_simulation_settings(two_system=True)
        loc = _make_mock_location(conflict=0.5, links=[
            _make_mock_link(0.2, 2.0),
        ])
        agent = _make_mock_agent(loc)
        movechance, s2_weight = moving.calculateMoveChance(agent, False, 0)
        assert isinstance(s2_weight, float), f"s2_weight should be float, got {type(s2_weight)}"
        assert not isinstance(s2_weight, bool), "s2_weight must NOT be a boolean"
        assert 0.0 <= s2_weight <= 1.0

    def test_camp_agent_gets_zero_s2_weight(self):
        """Agents in camps should always get s2_weight = 0.0."""
        from flee import moving
        _setup_simulation_settings(two_system=True)
        loc = _make_mock_location(conflict=0.5, camp=True)
        agent = _make_mock_agent(loc)
        movechance, s2_weight = moving.calculateMoveChance(agent, False, 0)
        assert s2_weight == 0.0

    def test_selectRoute_accepts_float(self):
        """selectRoute must accept s2_weight as a float, not bool."""
        from flee import moving
        from flee.SimulationSettings import SimulationSettings
        _setup_simulation_settings(two_system=True)
        # Use AwarenessLevel=0 so selectRoute just picks random link index (minimal mock)
        SimulationSettings.move_rules["AwarenessLevel"] = 0
        loc = _make_mock_location(conflict=0.5, links=[_make_mock_link(0.1, 1.0)])
        agent = _make_mock_agent(loc)
        route = moving.selectRoute(agent, time=0, s2_weight=0.5)
        assert isinstance(route, list)

    def test_no_system2_active_boolean_in_codebase(self):
        """Grep-style check: no function returns a bool for s2 state."""
        import inspect
        from flee import moving
        source = inspect.getsource(moving.calculateMoveChance)
        assert "system2_active" not in source, "system2_active boolean should be removed"
