"""Focused tests for the Day-15 model extensions:
  * conflict-dependent System-1 move chance  (flag: cmc_conflict_dependent)
  * S2-driven camp return                     (flag: enable_return)

Both flags default to False so the 84 baseline model tests are unaffected; these
tests exercise the flag-on paths. Mock helpers mirror tests/test_s1s2_integration.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _setup(two_system=True, alpha=2.0, beta=2.0, kappa=5.0):
    from flee.SimulationSettings import SimulationSettings
    for path in ["tests/empty.yml", "empty.yml", "flee/simsetting.yml"]:
        if os.path.exists(path):
            SimulationSettings.ReadFromYML(path)
            break
    mr = SimulationSettings.move_rules
    mr["TwoSystemDecisionMaking"] = two_system
    mr["s1s2_model_params"] = {"alpha": alpha, "beta": beta, "kappa": kappa}
    mr["MovechancePopBase"] = 10000.0
    mr["MovechancePopScaleFactor"] = 0.0
    mr["AwarenessLevel"] = 1
    mr["FixedRoutes"] = False
    mr["PruningThreshold"] = 1.0
    mr["WeightSoftening"] = 0.0
    mr["DistanceSoftening"] = 10.0
    mr["DistancePower"] = 1.0
    mr["WeightPower"] = 1.0
    mr["sys2_weight_override"] = None
    mr["enable_panic_clamp"] = False   # isolate the conflict-dependent term
    # clear Day-15 flags by default
    mr["cmc_conflict_dependent"] = False
    mr["enable_return"] = False
    mr["decision_engine"] = None
    mr["decision_mode"] = "blend"
    return SimulationSettings


def _link(endpoint_conflict, distance=1.0, name="Ep"):
    class Ep:
        def __init__(self):
            self.conflict = endpoint_conflict
            self.name = name
            self.marker = False
            self.camp = False
            self.pop = 1000
            self.capacity = 1000
            self.numAgents = 0
            self.attributes = {}
            self.region = "x"
            self.links = []

        def getScore(self, _):
            return 1.0
    ep = Ep()

    class Link:
        def __init__(self, e, d):
            self._e, self._d = e, d

        @property
        def endpoint(self):
            return self._e

        def get_distance(self):
            return self._d
        numAgents = 0
    return Link(ep, distance)


def _loc(conflict=0.5, camp=False, movechance=0.3, links=None, name="Loc"):
    class L:
        pass
    loc = L()
    loc.conflict = conflict
    loc.camp = camp
    loc.idpcamp = False
    loc.town = False
    loc.movechance = movechance
    loc.name = name
    loc.pop = 1000
    loc.capacity = 1000
    loc.numAgents = 100
    loc.links = links if links is not None else []
    loc.routes = {}
    loc.attributes = {}
    loc.marker = False
    loc.region = "x"
    return loc


def _agent(location, experience_index=0.5, home_location=None):
    class A:
        pass
    a = A()
    a.location = location
    a.experience_index = experience_index
    a.route = []
    a.attributes = {}
    a.home_location = home_location if home_location is not None else location
    a.returning = False
    a.sys2_activation_prob = 0.0
    return a


# --------------------------------------------------------------------------
# Task B2: conflict-dependent System-1 move chance
# --------------------------------------------------------------------------

class TestConflictDependentCMC:
    def test_default_off_is_unchanged(self):
        """Flag off: at c=1 (S2 suppressed) blended ~ location.movechance, NOT cmax."""
        from flee import moving
        ss = _setup(beta=5.0)
        ss.move_rules["ConflictMoveChance"] = 0.1
        ss.move_rules["conflict_movechance_max"] = 0.9
        ss.move_rules["cmc_conflict_dependent"] = False
        loc = _loc(conflict=1.0, movechance=0.3, links=[_link(0.9, 1.0)])
        a = _agent(loc, experience_index=1.0)
        blended, _ = moving.calculateMoveChance(a, False, 0)
        assert abs(blended - 0.3) <= 0.05, (
            f"flag off should leave System-1 movechance at 0.3, got {blended}")

    def test_on_rises_with_conflict(self):
        """Flag on: blended at c=1 ~ cmax, and strictly greater than at c=0."""
        from flee import moving
        ss = _setup(beta=5.0)
        ss.move_rules["ConflictMoveChance"] = 0.0   # base
        ss.move_rules["conflict_movechance_max"] = 0.8
        ss.move_rules["cmc_conflict_dependent"] = True

        loc_hi = _loc(conflict=1.0, movechance=0.0, links=[_link(0.9, 1.0)])
        b_hi, _ = moving.calculateMoveChance(_agent(loc_hi, 1.0), False, 0)
        ss.move_rules["decision_engine"] = None  # rebuild engine cleanly
        loc_lo = _loc(conflict=0.0, movechance=0.0, links=[_link(0.0, 1.0)])
        b_lo, _ = moving.calculateMoveChance(_agent(loc_lo, 1.0), False, 0)

        assert b_hi > b_lo, f"conflict-dependent CMC should raise movechance with c: {b_hi} !> {b_lo}"
        assert abs(b_hi - 0.8) <= 0.06, f"at c=1 (S2 suppressed) blended ~ cmax 0.8, got {b_hi}"


# --------------------------------------------------------------------------
# Task C: S2-driven camp return
# --------------------------------------------------------------------------

class TestReturnMechanism:
    def _camp_setup(self, home_conflict, time, enable, return_start=16):
        from flee import moving
        ss = _setup()
        ss.move_rules["enable_return"] = enable
        ss.move_rules["return_start_t"] = return_start
        ss.move_rules["return_conflict_threshold"] = 0.15
        ss.move_rules["return_rate"] = 0.5
        home = _loc(conflict=home_conflict, name="Home", movechance=0.3)
        camp = _loc(conflict=0.0, camp=True, movechance=0.0, name="Camp")
        a = _agent(camp, experience_index=2.0, home_location=home)
        return moving, a

    def test_default_off_camp_agent_stays(self):
        moving, a = self._camp_setup(home_conflict=0.0, time=20, enable=False)
        mc, w = moving.calculateMoveChance(a, False, 20)
        assert mc == 0.0 and w == 0.0
        assert a.returning is False

    def test_on_recovered_home_triggers_return(self):
        moving, a = self._camp_setup(home_conflict=0.0, time=20, enable=True)
        mc, w = moving.calculateMoveChance(a, False, 20)
        assert mc > 0.0, f"return should fire when home recovered & window open: {mc}"
        assert w > 0.0 and a.returning is True

    def test_on_before_window_no_return(self):
        moving, a = self._camp_setup(home_conflict=0.0, time=5, enable=True)
        mc, w = moving.calculateMoveChance(a, False, 5)
        assert mc == 0.0 and a.returning is False

    def test_on_home_still_in_conflict_no_return(self):
        moving, a = self._camp_setup(home_conflict=0.5, time=20, enable=True)
        mc, w = moving.calculateMoveChance(a, False, 20)
        assert mc == 0.0 and a.returning is False
