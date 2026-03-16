#!/usr/bin/env python3
"""
Standalone diagnostic script for movechance and AddNewConflictZones reclassification.
Investigates why T3_model stays low despite rescaling movechance.
Does not modify any existing simulation files, input CSVs, or test files.
"""

import copy
import os
import random
import sys
from pathlib import Path

import numpy as np

# Add project root for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flee import flee, InputGeography
from flee.SimulationSettings import SimulationSettings

INPUT_DIR = PROJECT_ROOT / "conflict_input" / "fukushima_2011"
RESULTS_DIR = PROJECT_ROOT / "results" / "fukushima"
AGENT_SCALE = 0.02
SEED = 42

MUNI_POP = {
    "Futaba": 6900, "Okuma": 11500, "Namie": 20500, "Tomioka": 15800,
    "Naraha": 7700, "Minamisoma": 70000, "Kawauchi": 2800, "Iitate": 6200,
}
SOURCE_MUNIS = ["Futaba", "Okuma", "Namie", "Tomioka", "Naraha", "Minamisoma", "Kawauchi", "Iitate"]


def _location_type(loc):
    """Derive effective location type from Location attributes."""
    if loc.conflict > 0:
        return "conflict"
    if loc.camp:
        return "camp"
    if loc.town:
        return "town"
    return "other"


def _load_simsetting():
    """Load simsetting from same paths as run_fukushima."""
    for path in [
        str(INPUT_DIR / "simsetting.yml"),
        str(PROJECT_ROOT / "flee" / "simsetting.yml"),
        str(PROJECT_ROOT / "test_data" / "test_settings.yml"),
    ]:
        if Path(path).exists():
            SimulationSettings.ReadFromYML(path)
            return
    raise FileNotFoundError("No simsetting.yml found")


def _apply_run_overrides():
    """Apply overrides; max_move_speed comes from simsetting (no override)."""
    # SimulationSettings.move_rules["MaxMoveSpeed"] from simsetting
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.move_rules["FixedRoutes"] = False
    SimulationSettings.move_rules["PruningThreshold"] = 1.0
    SimulationSettings.log_levels["agent"] = 0
    SimulationSettings.log_levels["init"] = 0
    SimulationSettings.ConflictInputFile = str(INPUT_DIR / "conflicts.csv")


def build_ecosystem(tomioka_intensity_override=None):
    """Build ecosystem. If tomioka_intensity_override is set, use it for Tomioka at step 8."""
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    SimulationSettings.move_rules["s2_weight_override"] = None
    # Use s1s2_model_params from simsetting (already loaded)
    SimulationSettings.ConflictInputFile = str(INPUT_DIR / "conflicts.csv")

    e = flee.Ecosystem()
    ig = InputGeography.InputGeography()
    ig.ReadLocationsFromCSV(str(INPUT_DIR / "locations.csv"))
    ig.ReadLinksFromCSV(str(INPUT_DIR / "routes.csv"))
    ig.ReadClosuresFromCSV(str(INPUT_DIR / "closures.csv"))
    ig.ReadConflictInputCSV(str(INPUT_DIR / "conflicts.csv"))

    if tomioka_intensity_override is not None:
        lst = list(ig.conflicts["Tomioka"])
        if len(lst) > 8:
            lst[8] = tomioka_intensity_override
        ig.conflicts["Tomioka"] = lst

    e, lm = ig.StoreInputGeographyInEcosystem(e)
    return e, lm, ig


def insert_agents(e, loc_map):
    """Insert agents same as run_fukushima."""
    total_pop = sum(MUNI_POP.get(m, 0) for m in SOURCE_MUNIS)
    for m in SOURCE_MUNIS:
        if m not in loc_map:
            continue
        pop = MUNI_POP.get(m, 0)
        n = max(0, int(pop / total_pop * AGENT_SCALE * total_pop))
        for _ in range(n):
            e.insertAgent(loc_map[m], {})
    for a in e.agents:
        a.experience_index = min(3.0, max(0.0, np.random.exponential(1.5)))


def run_diagnostics():
    """Run all five diagnostics."""
    random.seed(SEED)
    np.random.seed(SEED)

    # Movechance scaling verification (from build_fukushima_network)
    from scripts.build_fukushima_network import verify_movechance_scaling
    verify_movechance_scaling()

    # -------------------------------------------------------------------------
    # Diagnostic 5 — Simsetting check (do first)
    # -------------------------------------------------------------------------
    _load_simsetting()
    _apply_run_overrides()
    print("\n[SIMSETTING CHECK]")
    print(f"  conflict_movechance = {SimulationSettings.move_rules.get('ConflictMoveChance', 'N/A')}")
    print(f"  default_movechance  = {SimulationSettings.move_rules.get('DefaultMoveChance', 'N/A')}")
    print(f"  camp_movechance     = {SimulationSettings.move_rules.get('CampMoveChance', 'N/A')}")
    print(f"  max_move_speed      = {SimulationSettings.move_rules.get('MaxMoveSpeed', 'N/A')}")
    print(f"  awareness_level     = {SimulationSettings.move_rules.get('AwarenessLevel', 'N/A')}")

    # -------------------------------------------------------------------------
    # Build ecosystem and monkey-patch AddNewConflictZones (Diagnostic 3)
    # -------------------------------------------------------------------------
    e, loc_map, ig = build_ecosystem()

    original_add = ig.AddNewConflictZones
    add_calls = []

    def patched_add(ecosys, t):
        add_calls.append(t)
        print(f"[AddNewConflictZones] called at step t={t}")
        return original_add(ecosys, t)

    ig.AddNewConflictZones = patched_add

    insert_agents(e, loc_map)
    tomioka_loc = loc_map.get("Tomioka")
    naraha_loc = loc_map.get("Naraha")
    tomioka_baseline = tomioka_loc.numAgents if tomioka_loc else 0
    naraha_baseline = naraha_loc.numAgents if naraha_loc else 0

    # Pre-crisis step (t=0)
    ig.AddNewConflictZones(e, 0)
    e.evolve()

    # -------------------------------------------------------------------------
    # Diagnostics 1, 2, 3 — Run steps 1–20, print location state and departures
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("Diagnostic 1 — Location type reclassification (Tomioka, Naraha)")
    print("Diagnostic 2 — Departure counts per step")
    print("Diagnostic 3 — AddNewConflictZones calls (above)")
    print("=" * 70)

    tomioka_fracs_08 = {}  # for Diagnostic 4
    step8_type = "N/A"
    for t in range(1, 21):
        pop_tomioka_before = tomioka_loc.numAgents if tomioka_loc else 0
        pop_naraha_before = naraha_loc.numAgents if naraha_loc else 0

        ig.AddNewConflictZones(e, t)

        # Diagnostic 1 — after AddNewConflictZones, before evolve
        if tomioka_loc:
            ttype = _location_type(tomioka_loc)
            print(f"[STEP {t:02d}] Tomioka: type={ttype}, "
                  f"movechance={tomioka_loc.movechance:.4f}, "
                  f"conflict={tomioka_loc.conflict:.3f}")
        if naraha_loc:
            ntype = _location_type(naraha_loc)
            print(f"[STEP {t:02d}] Naraha:  type={ntype}, "
                  f"movechance={naraha_loc.movechance:.4f}, "
                  f"conflict={naraha_loc.conflict:.3f}")

        e.evolve()

        # Diagnostic 2 — after evolve
        pop_tomioka_after = tomioka_loc.numAgents if tomioka_loc else 0
        pop_naraha_after = naraha_loc.numAgents if naraha_loc else 0
        departed_t = pop_tomioka_before - pop_tomioka_after
        departed_n = pop_naraha_before - pop_naraha_after
        frac_t = pop_tomioka_after / tomioka_baseline if tomioka_baseline > 0 else 0
        frac_n = pop_naraha_after / naraha_baseline if naraha_baseline > 0 else 0
        print(f"[STEP {t:02d}] Tomioka: pop={pop_tomioka_after}, "
              f"departed_this_step={departed_t}, "
              f"fraction_remaining={frac_t:.3f}")
        print(f"[STEP {t:02d}] Naraha:  pop={pop_naraha_after}, "
              f"departed_this_step={departed_n}, "
              f"fraction_remaining={frac_n:.3f}")
        print()

        if t in (8, 10, 12, 14):
            tomioka_fracs_08[t] = frac_t
        if t == 8 and tomioka_loc:
            step8_type = _location_type(tomioka_loc)

    # -------------------------------------------------------------------------
    # Diagnostic 4 — Run with Tomioka intensity 1.0 at step 8
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("Diagnostic 4 — Tomioka intensity 0.8 vs 1.0 at step 8")
    print("=" * 70)

    _load_simsetting()
    _apply_run_overrides()
    e2, loc_map2, ig2 = build_ecosystem(tomioka_intensity_override=1.0)
    insert_agents(e2, loc_map2)
    tomioka_loc2 = loc_map2.get("Tomioka")
    tomioka_baseline2 = tomioka_loc2.numAgents if tomioka_loc2 else 0

    ig2.AddNewConflictZones(e2, 0)
    e2.evolve()

    tomioka_fracs_10 = {}
    for t in range(1, 15):
        ig2.AddNewConflictZones(e2, t)
        e2.evolve()
        if t in (8, 10, 12, 14):
            pop = tomioka_loc2.numAgents if tomioka_loc2 else 0
            tomioka_fracs_10[t] = pop / tomioka_baseline2 if tomioka_baseline2 > 0 else 0

    print("[INTENSITY TEST] Tomioka fraction remaining:")
    for step in (8, 10, 12, 14):
        frac_08 = tomioka_fracs_08.get(step, float("nan"))
        frac_10 = tomioka_fracs_10.get(step, float("nan"))
        print(f"  step {step:2d}: intensity=0.8 -> {frac_08:.4f}, intensity=1.0 -> {frac_10:.4f}")

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"AddNewConflictZones called at step 8: {8 in add_calls}")
    print(f"Tomioka type at step 8 (after AddNewConflictZones): {step8_type} (expected: conflict if reclassification worked)")
    print()


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_diagnostics()


if __name__ == "__main__":
    main()
