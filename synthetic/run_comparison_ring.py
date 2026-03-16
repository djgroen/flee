#!/usr/bin/env python3
"""
Run four-condition comparison on minimal topology.

# Topology: 10-location linear chain, conflict 1.0 (L0) -> 0.0 (L9).
# Phase boundaries t* and t** are derived from the simulated P_S2
# trajectory, not hardcoded. See main.tex Section 5.2 eqs. (tstar),
# (tstarstar) and find_tstar() / find_tstarstar() in this file.
# Pre-crisis baseline (t=0): conflict=0 on all locations, Omega=1,
# P_S2=Psi for every agent. movechance≈0 so no displacement occurs.
# Conflict is imposed from t=1 onward, triggering Phase 1.
# movechance=0.5 at conflict locations: empirically grounded departure
# rate allowing Phase 1 to persist. See main.tex Section 5.2.
# beta=4.0 for full_mixture only: Omega(c=1.0)=e^{-4}≈0.018.

Conditions:
  - original_flee: TwoSystemDecisionMaking=False (baseline)
  - s1_only: P_S2 forced to 0
  - s2_only: P_S2 forced to 1
  - full_mixture: P_S2 = Psi × Omega (alpha=2.0, beta=4.0, kappa=5.0)

Usage: python synthetic/run_comparison_ring.py
"""

import os
import sys
import random
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from flee import flee
from flee.SimulationSettings import SimulationSettings


def find_tstar(mean_s2_series):
    """
    t* = argmin of population-mean P_S2 for t >= 1.
    mean_s2_series is a list indexed from t=0.
    Returns integer timestep of the minimum.
    Phase 1 ends here. See main.tex eq. (tstar).
    """
    values_from_t1 = mean_s2_series[1:]
    tstar = int(np.argmin(values_from_t1)) + 1
    return tstar


def find_tstarstar(mean_s2_series, tstar, epsilon=0.002):
    """
    t** = first t > t* where change in mean P_S2 drops below epsilon.
    Represents plateau onset of Phase 2.
    Returns integer timestep, or len(mean_s2_series)-1 if no plateau
    detected within simulation window.
    Phase 2 ends here. See main.tex eq. (tstarstar).
    """
    for t in range(tstar + 1, len(mean_s2_series)):
        if abs(mean_s2_series[t] - mean_s2_series[t - 1]) < epsilon:
            return t
    return len(mean_s2_series) - 1


# Linear chain: L0 (conflict 1.0) -> L1 -> ... -> L9 (conflict 0.0)
# Coordinates along x-axis for distance calculation
# movechance=0.5 at conflict locations: empirically grounded departure
# rate allowing Phase 1 to persist for multiple timesteps before the
# population disperses. Fukushima data shows ~30-50% of households
# departed within 24h of the evacuation order. See main.tex Section 5.2.
CHAIN_LOCATIONS = [
    (f"L{i}", float(i * 100), 0.0, 1.0 - i / 9.0, "conflict" if i == 0 else "town")
    for i in range(10)
]
CHAIN_LINKS = [(f"L{i}", f"L{i+1}", 100.0) for i in range(9)]

CONDITIONS = {
    "original_flee": {
        "two_system_decision_making": False,
        "s2_weight_override": None,
        "s1s2_model": {"alpha": 2.0, "beta": 2.0, "kappa": 5.0},
    },
    "s1_only": {
        "two_system_decision_making": True,
        "s2_weight_override": 0,
        "s1s2_model": {"alpha": 2.0, "beta": 2.0, "kappa": 5.0},
    },
    "s2_only": {
        "two_system_decision_making": True,
        "s2_weight_override": 1,
        "s1s2_model": {"alpha": 2.0, "beta": 2.0, "kappa": 5.0},
    },
    "full_mixture": {
        "two_system_decision_making": True,
        "s2_weight_override": None,
        # beta=4.0 for full_mixture: at c=1.0, Omega=e^{-4}≈0.018, producing genuine
        # acute suppression. See main.tex Section 7.
        "s1s2_model": {"alpha": 2.0, "beta": 4.0, "kappa": 5.0},
    },
}

N_AGENTS = 500
N_TIMESTEPS = 72
SEED = 42
OUTPUT_DIR = REPO_ROOT / "synthetic" / "results" / "comparison_ring"


def build_ecosystem(condition_name):
    """Build ecosystem with minimal ring topology and condition-specific settings."""
    cond = CONDITIONS[condition_name]
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = cond["two_system_decision_making"]
    SimulationSettings.move_rules["s1s2_model_params"] = cond["s1s2_model"].copy()
    if cond["s2_weight_override"] is not None:
        SimulationSettings.move_rules["s2_weight_override"] = cond["s2_weight_override"]
    elif "s2_weight_override" in SimulationSettings.move_rules:
        SimulationSettings.move_rules["s2_weight_override"] = None

    ecosystem = flee.Ecosystem()
    loc_map = {}
    # movechance=0.5 for conflict locations (L0); 0.3 for towns.
    # Pre-crisis: conflict=0 on all locations; impose conflict after t=0.
    for name, x, y, conflict, loc_type in CHAIN_LOCATIONS:
        movechance = 0.5 if loc_type == "conflict" else 0.3
        pop = 1000 if name == "L0" else 0
        loc = ecosystem.addLocation(
            name=name, x=x, y=y, region="R1", country="C1",
            location_type=loc_type, movechance=movechance, capacity=10000, pop=pop,
        )
        loc.conflict = 0.0  # Pre-crisis: no conflict until imposed after t=0
        loc_map[name] = loc

    for a, b, dist in CHAIN_LINKS:
        ecosystem.linkUp(a, b, dist)

    return ecosystem, loc_map


def run_condition(condition_name):
    """Run one condition and return per-timestep metrics."""
    random.seed(SEED)
    np.random.seed(SEED)

    # Load base config
    for path in ["flee/simsetting.yml", "test_data/test_settings.yml"]:
        full_path = REPO_ROOT / path
        if full_path.exists():
            SimulationSettings.ReadFromYML(str(full_path))
            break
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.move_rules["AwarenessLevel"] = 1
    SimulationSettings.move_rules["FixedRoutes"] = False
    SimulationSettings.move_rules["PruningThreshold"] = 1.0
    SimulationSettings.log_levels["agent"] = 0
    SimulationSettings.log_levels["init"] = 0

    ecosystem, loc_map = build_ecosystem(condition_name)
    origin = loc_map["L0"]

    for _ in range(N_AGENTS):
        ecosystem.insertAgent(origin, {})

    rows = []
    agents_moved = set()

    def record_row(timestep):
        s2_weights = []
        blended_vals = []
        distances = []
        for a in ecosystem.agents:
            if a.location is None:
                continue
            s2_weights.append(getattr(a, "s2_activation_prob", 0.0))
            if not getattr(a, "travelling", False):
                blended_vals.append(getattr(a, "_last_blended_movechance", 0.0))
            if a.places_travelled > 1:
                agents_moved.add(id(a))
            try:
                d = a.home_location.calculateDistance(a.location)
            except Exception:
                d = 0.0
            distances.append(d)

        mean_s2 = np.mean(s2_weights) if s2_weights else 0.0
        std_s2 = np.std(s2_weights) if len(s2_weights) > 1 else 0.0
        mean_blended = np.mean(blended_vals) if blended_vals else 0.0
        num_moved = len(agents_moved)
        mean_dist = np.mean(distances) if distances else 0.0

        rows.append({
            "timestep": timestep,
            "mean_s2_weight": mean_s2,
            "mean_blended_movechance": mean_blended,
            "std_s2_weight": std_s2,
            "num_agents_moved": num_moved,
            "mean_distance_from_origin": mean_dist,
            "min_s2_weight": min(s2_weights) if s2_weights else 0.0,
            "max_s2_weight": max(s2_weights) if s2_weights else 0.0,
        })

    # Pre-crisis baseline (t=0): conflict=0 on all locations, Omega=1,
    # P_S2=Psi for every agent. movechance≈0 so no displacement occurs.
    # This is the analytic reference point from main.tex Section 5.2.
    # Conflict is imposed from t=1 onward, triggering Phase 1.
    origin.movechance = 0.001  # ≈0 so no displacement at pre-crisis
    ecosystem.evolve()
    record_row(timestep=0)

    # Impose conflict on all locations
    for name, x, y, conflict, loc_type in CHAIN_LOCATIONS:
        loc_map[name].conflict = conflict
    origin.movechance = 0.5  # Empirically grounded for crisis phase

    # Run t=1 through t=72
    for t in range(1, N_TIMESTEPS + 1):
        ecosystem.evolve()
        record_row(timestep=t)

    return rows


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for cond_name in CONDITIONS:
        print(f"  Running {cond_name}...", end=" ", flush=True)
        try:
            rows = run_condition(cond_name)
            out_path = OUTPUT_DIR / f"{cond_name}.csv"
            with open(out_path, "w") as f:
                f.write("timestep,mean_s2_weight,mean_blended_movechance,std_s2_weight,num_agents_moved,mean_distance_from_origin\n")
                for r in rows:
                    f.write(f"{r['timestep']},{r['mean_s2_weight']:.6f},{r['mean_blended_movechance']:.6f},{r['std_s2_weight']:.6f},{r['num_agents_moved']},{r['mean_distance_from_origin']:.4f}\n")
            print(f"OK -> {out_path}")

            # full_mixture: write S2 distribution, compute phase boundaries
            if cond_name == "full_mixture":
                dist_path = OUTPUT_DIR / "full_mixture_s2_distribution.csv"
                with open(dist_path, "w") as f:
                    f.write("timestep,min_s2_weight,mean_s2_weight,max_s2_weight\n")
                    for r in rows:
                        f.write(f"{r['timestep']},{r['min_s2_weight']:.6f},{r['mean_s2_weight']:.6f},{r['max_s2_weight']:.6f}\n")
                print(f"     -> {dist_path}")

                mean_s2_series = [r["mean_s2_weight"] for r in rows]
                tstar = find_tstar(mean_s2_series)
                tstarstar = find_tstarstar(mean_s2_series, tstar)
                mean_s2_t0 = mean_s2_series[0]
                mean_s2_tstar = mean_s2_series[tstar]
                mean_s2_tstarstar = mean_s2_series[tstarstar]
                std_s2_tstar = rows[tstar]["std_s2_weight"]
                std_s2_tstarstar = rows[tstarstar]["std_s2_weight"]

                phase_path = OUTPUT_DIR / "phase_boundaries.csv"
                with open(phase_path, "w") as f:
                    f.write("tstar,tstarstar,mean_s2_t0,mean_s2_tstar,mean_s2_tstarstar,std_s2_tstar,std_s2_tstarstar\n")
                    f.write(f"{tstar},{tstarstar},{mean_s2_t0:.6f},{mean_s2_tstar:.6f},{mean_s2_tstarstar:.6f},{std_s2_tstar:.6f},{std_s2_tstarstar:.6f}\n")
                print(f"     -> {phase_path}")

                print(f"[PHASE] t*={tstar}, t**={tstarstar}")
                print(f"[PHASE] mean_P_S2: t=0={mean_s2_t0:.4f}, t*={mean_s2_tstar:.4f}, t**={mean_s2_tstarstar:.4f}")
                print(f"[PHASE] std_P_S2:  t*={std_s2_tstar:.4f}, t**={std_s2_tstarstar:.4f}")
        except Exception as e:
            print(f"FAIL: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nDone. CSVs in {OUTPUT_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
