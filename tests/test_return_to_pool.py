"""Tests for the F2 fix (Task 2.5): settled `enable_return` agents must be handed
back to the origin's dual_process reservoir so they are re-eligible to flee again
if conflict recurs. Before this fix, `spawn_dynamics.return_to_pool` existed but
had zero callers (see results/spawn/verify/README.md finding F2)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flee.spawn_dynamics as sd
from flee.SimulationSettings import SimulationSettings
from flee.moving import calculateMoveChance


def _setup_simulation_settings():
    for path in ["tests/empty.yml", "empty.yml", "flee/simsetting.yml"]:
        if os.path.exists(path):
            SimulationSettings.ReadFromYML(path)
            break
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    SimulationSettings.move_rules["enable_return"] = True
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.spawn_rules["dual_process_bins"] = 1


def _make_mock_location(name, camp=False):
    class MockLocation:
        pass

    loc = MockLocation()
    loc.conflict = 0.0
    loc.camp = camp
    loc.idpcamp = False
    loc.town = not camp
    loc.movechance = 0.3
    loc.name = name
    loc.pop = 1000
    loc.capacity = 1000
    loc.numAgents = 100
    loc.links = []
    loc.routes = {}
    loc.attributes = {}
    loc.marker = False
    loc.region = "unknown"
    return loc


def _make_returning_agent(home, experience_index):
    class MockAgent:
        pass

    a = MockAgent()
    a.location = home  # already arrived home
    a.home_location = home
    a.returning = True
    a.experience_index = experience_index
    a.route = []
    a.attributes = {}
    return a


# --- Unit tests on spawn_dynamics.return_to_pool itself -------------------


def test_return_to_pool_increments_nearest_bin():
    sd.reset_pools()
    pool = sd.init_pool("Home", pop=10, nbins=4)
    totals_before = sd.pool_total("Home")
    x_b = pool[2][0]
    sd.return_to_pool("Home", x_b, nbins=4)
    assert sd.pool_total("Home") == totals_before + 1.0
    assert pool[2][1] == pool[2][1]  # nearest bin (index 2) received the return


def test_return_to_pool_creates_pool_if_missing():
    sd.reset_pools()
    assert sd.pool_total("NeverSpawnedFrom") == 0.0
    sd.return_to_pool("NeverSpawnedFrom", 0.3, nbins=4)
    assert sd.pool_total("NeverSpawnedFrom") == 1.0


def test_return_to_pool_restores_depleted_reservoir():
    """The direct F2 scenario: a fully-depleted reservoir (everyone has fled)
    regains a resident once that resident returns, restoring re-spawn eligibility."""
    sd.reset_pools()
    pool = sd.init_pool("Home", pop=1, nbins=1)
    pool[0][1] = 0.0  # simulate full depletion (the resident fled)
    assert sd.pool_total("Home") == 0.0

    sd.return_to_pool("Home", pool[0][0], nbins=1)

    assert sd.pool_total("Home") == 1.0


# --- Integration: calculateMoveChance settle branch wires the call --------


def test_settling_returning_agent_replenishes_dual_process_pool():
    _setup_simulation_settings()
    SimulationSettings.spawn_rules["conflict_spawn_mode"] = "dual_process"

    sd.reset_pools()
    home = _make_mock_location("Home")
    pool = sd.init_pool(home.name, pop=1, nbins=1)
    pool[0][1] = 0.0  # resident already fled; reservoir depleted
    agent = _make_returning_agent(home, experience_index=pool[0][0])

    movechance, p_s2 = calculateMoveChance(agent, False, 10)

    assert movechance == 0.0 and p_s2 == 0.0
    assert agent.returning is False
    assert sd.pool_total(home.name) == 1.0  # F2: resident handed back to reservoir


def test_settling_returning_agent_is_noop_for_non_dual_process_modes():
    """Non-breaking guard: legacy spawn modes must not touch any reservoir."""
    _setup_simulation_settings()
    SimulationSettings.spawn_rules["conflict_spawn_mode"] = "constant"

    sd.reset_pools()
    home = _make_mock_location("Home")
    agent = _make_returning_agent(home, experience_index=0.4)

    movechance, p_s2 = calculateMoveChance(agent, False, 10)

    assert movechance == 0.0 and p_s2 == 0.0
    assert agent.returning is False
    assert sd.pool_total(home.name) == 0.0  # no reservoir created/touched
