#!/usr/bin/env python3
# Fukushima 2011 calibration simulation.
# Network: simplified radial geometry, 5 distance rings + 4 safe destinations.
# Timestep = 2 hours. Crisis onset at t=1 (t=0 is pre-crisis baseline).
# Population initialized from Hayano & Adachi (2013) Fig 3, 2011-03-11 04:00.
# Calibration targets: data/calibration_targets/fukushima_2011_targets.csv
# See main.tex Section 5.2 for phase definitions.

"""
Run Fukushima evacuation calibration: grid search over alpha, beta, kappa.
"""

import os
import sys
import random
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flee import flee
from flee.SimulationSettings import SimulationSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGETS_PATH = PROJECT_ROOT / "data" / "calibration_targets" / "fukushima_2011_targets.csv"
RESULTS_DIR = PROJECT_ROOT / "results" / "fukushima"

# Network: 5 rings + 4 safe destinations
# L0-L4: conflict linearly 1.0 -> 0.11, pop from Hayano 2011-03-11 04:00
FUKUSHIMA_LOCATIONS = [
    ("L0", 0.0, 0.0, 1.00, 12500, "conflict"),   # 0-5km
    ("L1", 5.0, 0.0, 0.78, 33800, "town"),       # 5-10km
    ("L2", 10.0, 0.0, 0.56, 14500, "town"),      # 10-15km
    ("L3", 15.0, 0.0, 0.33, 14800, "town"),      # 15-20km
    ("L4", 20.0, 0.0, 0.11, 40500, "town"),     # 20-25km
    ("S1", 70.0, 0.0, 0.0, 0, "camp"),          # Safe north
    ("S2", -30.0, 0.0, 0.0, 0, "camp"),         # Safe south
    ("S3", 20.0, 50.0, 0.0, 0, "camp"),        # Safe west
    ("S4", 20.0, -50.0, 0.0, 0, "camp"),        # Safe inland
]
# Links: L0-L1, L1-L2, L2-L3, L3-L4 (5km each), L4-S1,S2,S3,S4 (50km each)
FUKUSHIMA_LINKS = [
    ("L0", "L1", 5.0), ("L1", "L2", 5.0), ("L2", "L3", 5.0), ("L3", "L4", 5.0),
    ("L4", "S1", 50.0), ("L4", "S2", 50.0), ("L4", "S3", 50.0), ("L4", "S4", 50.0),
]

# Scale factor for agent count (full pop ~116k would be slow)
AGENT_SCALE = 0.02  # ~2320 agents
TIMESTEP_HOURS = 2
N_TIMESTEPS = 36  # 72h after crisis onset
SEED = 42

ALPHA_RANGE = [0.5, 1.0, 2.0, 3.0, 5.0]
BETA_RANGE = [1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
KAPPA_RANGE = [1.0, 3.0, 5.0, 10.0, 20.0]

# Target timesteps (each step = 2h): t=15h->step8, t=20h->step10, t=33h->step17, t=72h->step36
TARGET_STEPS = {15: 8, 20: 10, 33: 17, 72: 36}
ZONE_TO_LOC = {"<5km": "L0", "5–10km": "L1", "10–15km": "L2", "15–20km": "L3", "<20km_combined": ["L0", "L1", "L2", "L3"]}


def find_tstar(mean_s2_series):
    """t* = argmin of mean P_S2 for t >= 1."""
    values_from_t1 = mean_s2_series[1:]
    return int(np.argmin(values_from_t1)) + 1


def find_tstarstar(mean_s2_series, tstar, epsilon=0.002):
    """t** = first t > t* where change in mean P_S2 drops below epsilon."""
    for t in range(tstar + 1, len(mean_s2_series)):
        if abs(mean_s2_series[t] - mean_s2_series[t - 1]) < epsilon:
            return t
    return len(mean_s2_series) - 1


def build_ecosystem(alpha, beta, kappa):
    """Build Fukushima network with given S1S2 parameters."""
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    SimulationSettings.move_rules["s2_weight_override"] = None
    SimulationSettings.move_rules["s1s2_model_params"] = {"alpha": alpha, "beta": beta, "kappa": kappa}

    ecosystem = flee.Ecosystem()
    loc_map = {}
    for name, x, y, conflict, pop, loc_type in FUKUSHIMA_LOCATIONS:
        movechance = 0.5 if conflict > 0.5 else 0.3
        if loc_type == "camp":
            movechance = 0.001
        cap = 100000 if loc_type == "camp" else 50000
        loc = ecosystem.addLocation(
            name=name, x=x, y=y, region="R1", country="C1",
            location_type=loc_type, movechance=movechance, capacity=cap, pop=0,
        )
        loc.conflict = 0.0  # Pre-crisis
        loc_map[name] = loc

    for a, b, dist in FUKUSHIMA_LINKS:
        ecosystem.linkUp(a, b, dist)

    return ecosystem, loc_map


def run_simulation(alpha, beta, kappa, seed=None):
    """Run one 36-timestep simulation, return per-step metrics and target frac_remaining."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    for path in ["conflict_input/fukushima_2011/simsetting.yml", "flee/simsetting.yml", "test_data/test_settings.yml"]:
        if (PROJECT_ROOT / path).exists():
            SimulationSettings.ReadFromYML(str(PROJECT_ROOT / path))
            break
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.move_rules["AwarenessLevel"] = 1
    SimulationSettings.move_rules["FixedRoutes"] = False
    SimulationSettings.move_rules["PruningThreshold"] = 1.0
    SimulationSettings.log_levels["agent"] = 0
    SimulationSettings.log_levels["init"] = 0

    ecosystem, loc_map = build_ecosystem(alpha, beta, kappa)

    # Insert agents at L0-L4 proportionally to population
    pops = [12500, 33800, 14500, 14800, 40500]
    total = sum(pops)
    for i, (name, _, _, _, _, _) in enumerate(FUKUSHIMA_LOCATIONS[:5]):
        n = max(1, int(pops[i] / total * AGENT_SCALE * total))
        for _ in range(n):
            ecosystem.insertAgent(loc_map[name], {})

    # Override experience_index: Exponential(1.5) clipped [0, 3]
    for a in ecosystem.agents:
        a.experience_index = min(3.0, max(0.0, np.random.exponential(1.5)))

    # Pre-crisis step
    for loc in loc_map.values():
        loc.conflict = 0.0
    for name, _, _, conflict, _, _ in FUKUSHIMA_LOCATIONS[:5]:
        loc_map[name].movechance = 0.001
    ecosystem.evolve()

    # Impose conflict (from t=1 onward)
    for name, x, y, conflict, pop, loc_type in FUKUSHIMA_LOCATIONS:
        loc_map[name].conflict = conflict
        if name in ["L0", "L1", "L2", "L3", "L4"]:
            loc_map[name].movechance = 0.5 if conflict > 0.5 else 0.3

    rows = []
    baseline = {f"L{i}": pops[i] for i in range(5)}

    def record_row(step):
        pop_L0 = loc_map["L0"].numAgents
        pop_L1 = loc_map["L1"].numAgents
        pop_L2 = loc_map["L2"].numAgents
        pop_L3 = loc_map["L3"].numAgents
        pop_L4 = loc_map["L4"].numAgents
        s2_weights = [getattr(a, "s2_activation_prob", 0.0) for a in ecosystem.agents if a.location]
        rows.append({
            "step": step,
            "L0": pop_L0, "L1": pop_L1, "L2": pop_L2, "L3": pop_L3, "L4": pop_L4,
            "frac_L0": pop_L0 / baseline["L0"],
            "frac_L1": pop_L1 / baseline["L1"],
            "frac_L2": pop_L2 / baseline["L2"],
            "frac_L3": pop_L3 / baseline["L3"],
            "frac_L4": pop_L4 / baseline["L4"],
            "frac_L0L3": (pop_L0 + pop_L1 + pop_L2 + pop_L3) / (12500 + 33800 + 14500 + 14800),
            "mean_s2": np.mean(s2_weights) if s2_weights else 0.0,
            "std_s2": np.std(s2_weights) if len(s2_weights) > 1 else 0.0,
        })

    record_row(0)

    for t in range(1, N_TIMESTEPS + 1):
        ecosystem.evolve()
        record_row(t)

    return rows


def compute_loss(rows, targets_df):
    """Weighted sum of squared differences: sum((model - target)^2 / uncertainty^2)."""
    usable = targets_df[targets_df["usable"] == True]
    loss = 0.0
    model_vals = {}
    for _, row in usable.iterrows():
        tid = row["target_id"]
        if tid == "T5":
            continue
        t_h = row["hours_since_t0"]
        step = TARGET_STEPS.get(int(t_h), int(t_h / TIMESTEP_HOURS))
        if step >= len(rows):
            step = len(rows) - 1
        r = rows[step]
        zone = row["zone"]
        target_val = row["empirical_value"]
        unc = row.get("uncertainty", 0.2)
        if unc <= 0:
            unc = 0.2
        if zone == "<20km_combined":
            model_val = r["frac_L0L3"]
        else:
            loc = ZONE_TO_LOC.get(zone, zone)
            model_val = r.get(f"frac_{loc}", np.nan)
        if not np.isnan(model_val) and not np.isnan(target_val):
            loss += ((model_val - target_val) ** 2) / (unc ** 2)
        model_vals[tid] = model_val
    return loss, model_vals


def main():
    if not TARGETS_PATH.exists():
        print(f"ERROR: Run runscripts/derive_fukushima_targets.py first. Missing {TARGETS_PATH}")
        return 1

    targets_df = pd.read_csv(TARGETS_PATH)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for alpha in ALPHA_RANGE:
        for beta in BETA_RANGE:
            for kappa in KAPPA_RANGE:
                rows = run_simulation(alpha, beta, kappa, seed=SEED)
                loss, model_vals = compute_loss(rows, targets_df)
                results.append({
                    "alpha": alpha, "beta": beta, "kappa": kappa,
                    "loss": loss,
                    "T1_model": model_vals.get("T1", np.nan),
                    "T2_model": model_vals.get("T2", np.nan),
                    "T3_model": model_vals.get("T3", np.nan),
                    "T4_model": model_vals.get("T4", np.nan),
                })

    res_df = pd.DataFrame(results)
    res_df.to_csv(RESULTS_DIR / "grid_search.csv", index=False)
    print(f"Wrote {RESULTS_DIR / 'grid_search.csv'}")

    top5 = res_df.nsmallest(5, "loss")
    print("\n=== Top 5 parameter sets by loss ===")
    print(top5.to_string(index=False))

    # Best run for report and save trajectory for plotting
    best = res_df.loc[res_df["loss"].idxmin()]
    rows = run_simulation(best["alpha"], best["beta"], best["kappa"], seed=SEED)
    traj_df = pd.DataFrame(rows)
    traj_df["hours_since_t0"] = traj_df["step"] * TIMESTEP_HOURS
    traj_df.to_csv(RESULTS_DIR / "best_fit_trajectory.csv", index=False)
    mean_s2_series = [r["mean_s2"] for r in rows]
    tstar = find_tstar(mean_s2_series)
    tstarstar = find_tstarstar(mean_s2_series, tstar)

    # Empirical values from targets
    t1_row = targets_df[targets_df["target_id"] == "T1"].iloc[0]
    t2_row = targets_df[targets_df["target_id"] == "T2"].iloc[0]
    t3_row = targets_df[targets_df["target_id"] == "T3"].iloc[0]
    t4_row = targets_df[targets_df["target_id"] == "T4"].iloc[0]

    obs1, obs2, obs3, obs4 = t1_row["empirical_value"], t2_row["empirical_value"], t3_row["empirical_value"], t4_row["empirical_value"]
    m1, m2, m3, m4 = best["T1_model"], best["T2_model"], best["T3_model"], best["T4_model"]

    print("\n=== FUKUSHIMA CALIBRATION REPORT ===")
    print(f"Best parameters: alpha={best['alpha']}, beta={best['beta']}, kappa={best['kappa']}")
    print(f"Loss: {best['loss']:.6f}")
    print("\nCalibration target performance:")
    print(f"  T1 (<5km at t=15h):     observed={obs1:.4f}, modeled={m1:.4f}, diff={m1-obs1:.4f}")
    print(f"  T2 (<5km at t=20h):     observed={obs2:.4f}, modeled={m2:.4f}, diff={m2-obs2:.4f}")
    print(f"  T3 (15-20km at t=33h):  observed={obs3:.4f}, modeled={m3:.4f}, diff={m3-obs3:.4f}")
    print(f"  T4 (<20km at t=72h):    observed={obs4:.4f}, modeled={m4:.4f}, diff={m4-obs4:.4f}")
    print(f"\nPhase boundaries (best-fit run):")
    print(f"  t*  = {tstar} (Phase 1 minimum)")
    print(f"  t** = {tstarstar} (Phase 2 plateau onset)")
    print("\nAll 32 unit tests: run pytest tests/test_s1s2_v3.py and confirm passing.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
