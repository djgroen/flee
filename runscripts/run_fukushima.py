#!/usr/bin/env python3
# Fukushima 2011 calibration simulation.
# Network: realistic municipality-level from conflict_input/fukushima_2011/.
# Timestep = 2 hours. t=0 is pre-crisis baseline, t=1 is crisis onset (earthquake).
# Conflict onset via conflicts.csv (evacuation orders at steps 4, 8, 14).
# Calibration targets: data/calibration_targets/fukushima_2011_targets.csv

"""
Run Fukushima evacuation calibration: grid search over alpha, beta, kappa.
Uses InputGeography and conflicts.csv for time-varying conflict onset.
"""

import math
import os
import sys
import random
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Run movechance scaling verification when calibration runs
from scripts.build_fukushima_network import verify_movechance_scaling
verify_movechance_scaling()

from flee import flee, InputGeography
from flee.SimulationSettings import SimulationSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "conflict_input" / "fukushima_2011"
TARGETS_PATH = PROJECT_ROOT / "data" / "calibration_targets" / "fukushima_2011_targets.csv"
RESULTS_DIR = PROJECT_ROOT / "results" / "fukushima"

# Scale factor for agent count (full pop ~138k would be slow)
AGENT_SCALE = 0.02
TIMESTEP_HOURS = 2
N_TIMESTEPS = 200
# 200 steps = 400h ≈ 17 days at 2h/step.
# Extended from 72 to allow phase structure to fully develop.
# With conflict_movechance=0.25 and max_move_speed=20, expected
# transit time from NPP to safe destination:
#   - Move decision: 1/0.25 = 4 steps average per location
#   - Network length: ~9 locations to safe destination
#   - Expected transit: ~36 steps (~72h)
# At 200 steps all agents should reach safe destinations and P_S2
# should recover, allowing t* to be identified well within the window.
# Fukushima outer zone dynamics (Iitate, Minamisoma) extended
# to ~day 7-10; 200 steps covers this comfortably.
SEED = 42

# =============================================================================
# PARAMETER GRID SEARCH
# =============================================================================
# Cognitive parameters — free, inferred from data
ALPHA_RANGE = [0.5, 1.0, 2.0, 3.0, 5.0]
BETA_RANGE = [1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
KAPPA_RANGE = [1.0, 3.0, 5.0, 10.0, 20.0]

# Physical constraint — fixed empirically, not swept
# max_move_speed = 20.0 km/step (10 km/h, lower bound probe-car data)
# conflict_movechance = 0.25 (derived from Hayano 2013 inner zone clearing)
# See simsetting.yml for full derivation comments.
FIXED_MAX_SPEED = 20.0

# tau* raw formula (t * v / d_star) produces values in implicit "days" when
# t is in steps and 1 step = 2h (e.g. 200 steps => 400h => ~17 days scale).
# Test bounds [0.1, 10.0] assume years. Normalize: tau_star_years = tau_star_raw / 365.25
DAYS_PER_YEAR = 365.25

# Target timesteps: t=15h->step8, t=20h->step10, t=33h->step17, t=72h->step36
TARGET_STEPS = {15: 8, 20: 10, 33: 17, 72: 36}

# Paths for d* computation
CONFLICTS_CSV = INPUT_DIR / "conflicts.csv"
LOCATIONS_CSV = INPUT_DIR / "locations.csv"
ROUTES_CSV = INPUT_DIR / "routes.csv"

# Municipality to zone mapping for calibration (Hayano distance zones)
# <5km: Futaba + Okuma; 5–10km: Namie; 10–15km: Tomioka; 15–20km: Naraha
ZONE_TO_MUNIS = {
    "<5km": ["Futaba", "Okuma"],
    "5–10km": ["Namie"],
    "10–15km": ["Tomioka"],
    "15–20km": ["Naraha"],
    "<20km_combined": ["Futaba", "Okuma", "Namie", "Tomioka", "Naraha"],
}

# Population baseline (2010 census) for zone aggregation
MUNI_POP = {
    "Futaba": 6900, "Okuma": 11500, "Namie": 20500, "Tomioka": 15800,
    "Naraha": 7700, "Minamisoma": 70000, "Kawauchi": 2800, "Iitate": 6200,
}

SOURCE_MUNIS = ["Futaba", "Okuma", "Namie", "Tomioka", "Naraha", "Minamisoma", "Kawauchi", "Iitate"]

# NPP (nearest plant) reference for d* computation
NPP_LOCATIONS = ["Futaba", "Okuma"]

# Zone groups for multi-wave phase analysis (Fukushima has 3 ordered evacuation waves)
FUKUSHIMA_ZONES = {
    "inner_3km": ["Futaba", "Okuma"],
    "inner_3km_onset": 1,
    "zone_10km": ["Namie", "Tomioka", "Naraha"],
    "zone_10km_onset": 8,
    "zone_20km": ["Minamisoma", "Iitate", "Kawauchi"],
    "zone_20km_onset": 14,
}

# Map origin_location -> zone for agent_history
ORIGIN_TO_ZONE = {}
for zone, locs in [("inner_3km", ["Futaba", "Okuma"]), ("zone_10km", ["Namie", "Tomioka", "Naraha"]), ("zone_20km", ["Minamisoma", "Iitate", "Kawauchi"])]:
    for loc in locs:
        ORIGIN_TO_ZONE[loc] = zone


def compute_zone_phase_boundaries(history_df, zone_groups, beta, v, d_star):
    """
    Compute Phase 1/2 boundaries separately for each ordered evacuation zone.

    Fukushima has three ordered waves; global population-mean P_S2 is their
    superposition. Zone-level analysis recovers the two-phase structure for
    each wave independently.
    """
    EPS = 0.002
    results = {}

    zone_labels = [k for k in zone_groups if not k.endswith("_onset")]
    for zone_label in zone_labels:
        locations = zone_groups[zone_label]
        onset_key = zone_label + "_onset"
        if onset_key not in zone_groups:
            continue
        t_onset = zone_groups[onset_key]

        zone_mask = history_df["origin_location"].isin(locations)
        zone_df = history_df[zone_mask]
        if zone_df.empty:
            continue

        zone_ps2 = zone_df.groupby("step")["s2_weight"].mean()

        post_onset = zone_ps2[zone_ps2.index >= t_onset]
        if post_onset.empty:
            continue
        t_star = int(post_onset.idxmin())

        post_tstar = zone_ps2[zone_ps2.index > t_star]
        t_starstar = None
        for t in sorted(post_tstar.index):
            if t - 1 in zone_ps2.index and abs(zone_ps2[t] - zone_ps2[t - 1]) < EPS:
                t_starstar = int(t)
                break
        if t_starstar is None:
            t_starstar = int(zone_ps2.index[-1])

        tau_star_raw = ((t_star - t_onset) * v / d_star) if d_star > 0 else float("inf")
        tau_star = tau_star_raw / DAYS_PER_YEAR if tau_star_raw != float("inf") else tau_star_raw

        n_agents = int(zone_df[zone_df["step"] == 0].shape[0]) if 0 in zone_df["step"].values else int(zone_mask.sum() // (zone_df["step"].nunique() or 1))
        results[zone_label] = {
            "t_conflict_onset": t_onset,
            "t_star": t_star,
            "t_starstar": t_starstar,
            "tau_star": tau_star,
            "ps2_at_onset": float(zone_ps2.get(t_onset, float("nan"))),
            "ps2_at_tstar": float(zone_ps2.get(t_star, float("nan"))),
            "ps2_at_tstarstar": float(zone_ps2.get(t_starstar, float("nan"))),
            "n_agents": n_agents,
        }

    return results


def compute_characteristic_distance(beta, conflicts_csv, locations_csv, routes_csv, quiet=False):
    """
    Compute d*(beta) = network distance from NPP to the location
    where conflict = ln(2)/beta (the Omega=0.5 threshold).

    Uses the conflict schedule in conflicts.csv to find which location
    has conflict closest to c* = ln(2)/beta at step 8 (after orders fire).
    Returns distance in km from L0 (nearest NPP location) to that location
    using the routes.csv link distances.
    """
    import networkx as nx

    c_star = math.log(2) / beta
    if not quiet:
        print(f"[d*] beta={beta:.2f}, c*={c_star:.3f} (Omega=0.5 threshold)")

    # Load conflict values at step 8
    conflicts_df = pd.read_csv(conflicts_csv)
    # Row 8 = step 8 (0-indexed)
    if len(conflicts_df) <= 8:
        print("[d*] conflicts.csv has insufficient rows for step 8")
        return 0.0
    row8 = conflicts_df.iloc[8]
    conflict_cols = [c for c in conflicts_df.columns if c not in ("Day", "#Day") and str(c).strip()]

    # Find location with conflict closest to c_star (only consider conflict > 0:
    # locations with conflict=0 are not yet in the zone)
    best_name = None
    best_conflict = None
    best_diff = float("inf")
    for col in conflict_cols:
        try:
            val = float(row8[col])
        except (ValueError, TypeError):
            continue
        if val <= 0:
            continue
        diff = abs(val - c_star)
        if diff < best_diff:
            best_diff = diff
            best_name = col.strip()
            best_conflict = val

    if best_name is None:
        if not quiet:
            print("[d*] No valid conflict values at step 8")
        return 0.0

    # Build graph from routes
    routes_df = pd.read_csv(routes_csv)
    name1_col = "name1" if "name1" in routes_df.columns else routes_df.columns[0]
    name2_col = "name2" if "name2" in routes_df.columns else routes_df.columns[1]
    dist_col = "distance" if "distance" in routes_df.columns else routes_df.columns[2]
    G = nx.Graph()
    for _, r in routes_df.iterrows():
        n1, n2 = str(r[name1_col]).strip(), str(r[name2_col]).strip()
        d = float(r[dist_col])
        G.add_edge(n1, n2, weight=d)

    # Shortest path from each NPP location to best_name; use minimum
    d_star_km = float("inf")
    for npp in NPP_LOCATIONS:
        if npp not in G or best_name not in G:
            continue
        try:
            length = nx.shortest_path_length(G, npp, best_name, weight="weight")
            if length < d_star_km:
                d_star_km = length
        except nx.NetworkXNoPath:
            continue

    if d_star_km == float("inf"):
        d_star_km = 0.0
        if not quiet:
            print(f"[d*] No path from NPP to {best_name}")

    if not quiet:
        print(f"[d*] Closest location: {best_name} (conflict={best_conflict:.3f} at step 8, "
              f"distance from NPP={d_star_km:.1f} km)")
        print(f"[d*] d*(beta={beta:.1f}) = {d_star_km:.1f} km")
    return d_star_km


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
    """Build ecosystem from InputGeography with given S1S2 parameters."""
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    SimulationSettings.move_rules["s2_weight_override"] = None
    SimulationSettings.move_rules["s1s2_model_params"] = {"alpha": alpha, "beta": beta, "kappa": kappa}

    SimulationSettings.ConflictInputFile = str(INPUT_DIR / "conflicts.csv")

    e = flee.Ecosystem()
    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV(str(INPUT_DIR / "locations.csv"))
    ig.ReadLinksFromCSV(str(INPUT_DIR / "routes.csv"))
    ig.ReadClosuresFromCSV(str(INPUT_DIR / "closures.csv"))
    ig.ReadConflictInputCSV(str(INPUT_DIR / "conflicts.csv"))
    e, lm = ig.StoreInputGeographyInEcosystem(e)

    return e, lm, ig


def run_simulation(alpha, beta, kappa, seed=None, collect_agent_history=False):
    """Run one N_TIMESTEPS simulation, return per-step metrics.
    When collect_agent_history=True, also returns agent_history_df for zone-level phase analysis.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    for path in [
        str(INPUT_DIR / "simsetting.yml"),
        str(PROJECT_ROOT / "flee" / "simsetting.yml"),
        str(PROJECT_ROOT / "test_data" / "test_settings.yml"),
    ]:
        if Path(path).exists():
            SimulationSettings.ReadFromYML(path)
            break

    SimulationSettings.move_rules["MaxMoveSpeed"] = float(FIXED_MAX_SPEED)
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.move_rules["FixedRoutes"] = False
    SimulationSettings.move_rules["PruningThreshold"] = 1.0
    SimulationSettings.log_levels["agent"] = 0
    SimulationSettings.log_levels["init"] = 0
    SimulationSettings.ConflictInputFile = str(INPUT_DIR / "conflicts.csv")

    ecosystem, loc_map, ig = build_ecosystem(alpha, beta, kappa)

    # Insert agents proportionally to population at source municipalities
    total_pop = sum(MUNI_POP.get(m, 0) for m in SOURCE_MUNIS)
    for m in SOURCE_MUNIS:
        if m not in loc_map:
            continue
        pop = MUNI_POP.get(m, 0)
        n = max(0, int(pop / total_pop * AGENT_SCALE * total_pop))
        for _ in range(n):
            ecosystem.insertAgent(loc_map[m], {"origin_location": m})

    # Override experience_index: Exponential(1.5) clipped [0, 3]
    for a in ecosystem.agents:
        a.experience_index = min(3.0, max(0.0, np.random.exponential(1.5)))

    # Pre-crisis step (t=0)
    ig.AddNewConflictZones(ecosystem, 0)
    ecosystem.evolve()

    baseline = {}
    for zone, munis in ZONE_TO_MUNIS.items():
        baseline[zone] = sum(loc_map[m].numAgents for m in munis if m in loc_map)
    # Also record per-muni baseline for frac
    muni_baseline = {m: loc_map[m].numAgents for m in SOURCE_MUNIS if m in loc_map}

    rows = []
    agent_history = [] if collect_agent_history else None

    def record_row(step):
        muni_pops = {m: loc_map[m].numAgents for m in SOURCE_MUNIS if m in loc_map}
        zone_pops = {}
        for zone, munis in ZONE_TO_MUNIS.items():
            zone_pops[zone] = sum(muni_pops.get(m, 0) for m in munis)
        zone_fracs = {}
        for zone, munis in ZONE_TO_MUNIS.items():
            base = sum(muni_baseline.get(m, 0) for m in munis)
            zone_fracs[zone] = zone_pops[zone] / base if base > 0 else 0.0
        s2_weights = [getattr(a, "s2_activation_prob", 0.0) for a in ecosystem.agents if a.location]
        row = {"step": step, "mean_s2": np.mean(s2_weights) if s2_weights else 0.0}
        row["std_s2"] = np.std(s2_weights) if len(s2_weights) > 1 else 0.0
        for k, v in zone_fracs.items():
            row[f"frac_{k}"] = v
        for m in SOURCE_MUNIS:
            base = muni_baseline.get(m, 1)
            row[f"frac_{m}"] = muni_pops.get(m, 0) / base if base > 0 else 0.0
        rows.append(row)
        if collect_agent_history:
            for agent_id, a in enumerate(ecosystem.agents):
                origin = a.attributes.get("origin_location", None)
                if origin is not None:
                    s2 = getattr(a, "s2_activation_prob", 0.0)
                    origin_zone = ORIGIN_TO_ZONE.get(origin, "other")
                    loc = a.location
                    if loc is None:
                        loc_name, lat, lon, conflict = "", float("nan"), float("nan"), float("nan")
                    else:
                        # When travelling, loc is a Link; use endpoint
                        ep = getattr(loc, "endpoint", loc)
                        loc_name = getattr(ep, "name", str(loc))
                        # flee uses x=lon, y=lat (InputGeography gps_x->x, gps_y->y)
                        lon = getattr(ep, "x", float("nan"))
                        lat = getattr(ep, "y", float("nan"))
                        conflict = getattr(ep, "conflict", -1.0)
                        if conflict < 0:
                            conflict = float("nan")
                    agent_history.append({
                        "step": step,
                        "agent_id": agent_id,
                        "location": loc_name,
                        "s2_weight": s2,
                        "origin_location": origin,
                        "origin_zone": origin_zone,
                        "lat": lat,
                        "lon": lon,
                        "conflict_at_location": conflict,
                    })

    record_row(0)

    for t in range(1, N_TIMESTEPS + 1):
        ig.AddNewConflictZones(ecosystem, t)
        ecosystem.evolve()
        record_row(t)

    if collect_agent_history:
        agent_history_df = pd.DataFrame(agent_history)
        return rows, agent_history_df
    return rows


def compute_loss(rows, targets_df):
    """Weighted sum of squared differences."""
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
        zone_key = zone.replace("–", "–")  # keep en-dash
        model_val = r.get(f"frac_{zone_key}", r.get(f"frac_{zone}", np.nan))
        if not np.isnan(model_val) and not np.isnan(target_val):
            loss += ((model_val - target_val) ** 2) / (unc ** 2)
        model_vals[tid] = model_val
    return loss, model_vals


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run reduced grid (2 speeds, 1 alpha/beta/kappa) for testing")
    args = parser.parse_args()

    if not TARGETS_PATH.exists():
        print(f"ERROR: Run runscripts/derive_fukushima_targets.py first. Missing {TARGETS_PATH}")
        return 1

    targets_df = pd.read_csv(TARGETS_PATH)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    alpha_r = [1.0] if args.quick else ALPHA_RANGE
    beta_r = [2.0] if args.quick else BETA_RANGE
    kappa_r = [5.0] if args.quick else KAPPA_RANGE

    # Cache d*(beta) per unique beta
    d_star_cache = {}

    results = []
    for alpha in alpha_r:
        for beta in beta_r:
            for kappa in kappa_r:
                rows = run_simulation(alpha, beta, kappa, seed=SEED)
                loss, model_vals = compute_loss(rows, targets_df)
                mean_s2_series = [r["mean_s2"] for r in rows]
                tstar = find_tstar(mean_s2_series)
                if beta not in d_star_cache:
                    d_star_cache[beta] = compute_characteristic_distance(
                        beta, str(CONFLICTS_CSV), str(LOCATIONS_CSV), str(ROUTES_CSV), quiet=True
                    )
                d_star = d_star_cache[beta]
                tau_star_raw = (tstar * FIXED_MAX_SPEED) / d_star if d_star > 0 else float("inf")
                tau_star = tau_star_raw / DAYS_PER_YEAR if tau_star_raw != float("inf") else tau_star_raw
                results.append({
                    "alpha": alpha, "beta": beta, "kappa": kappa,
                    "loss": loss,
                    "T1_model": model_vals.get("T1", np.nan),
                    "T2_model": model_vals.get("T2", np.nan),
                    "T3_model": model_vals.get("T3", np.nan),
                    "T4_model": model_vals.get("T4", np.nan),
                    "tau_star": tau_star,
                })

    res_df = pd.DataFrame(results)
    res_df.to_csv(RESULTS_DIR / "grid_search.csv", index=False)
    print(f"Wrote {RESULTS_DIR / 'grid_search.csv'}")

    top5 = res_df.nsmallest(5, "loss")
    print("\n=== Top 5 parameter sets by loss ===")
    print(top5.to_string(index=False))

    best = res_df.loc[res_df["loss"].idxmin()]
    rows, agent_history_df = run_simulation(
        best["alpha"], best["beta"], best["kappa"], seed=SEED, collect_agent_history=True
    )
    traj_df = pd.DataFrame(rows)
    traj_df["hours_since_t0"] = traj_df["step"] * TIMESTEP_HOURS
    traj_df.to_csv(RESULTS_DIR / "best_fit_trajectory.csv", index=False)
    mean_s2_series = [r["mean_s2"] for r in rows]
    tstar = find_tstar(mean_s2_series)
    tstarstar = find_tstarstar(mean_s2_series, tstar)

    t1_row = targets_df[targets_df["target_id"] == "T1"].iloc[0]
    t2_row = targets_df[targets_df["target_id"] == "T2"].iloc[0]
    t3_row = targets_df[targets_df["target_id"] == "T3"].iloc[0]
    t4_row = targets_df[targets_df["target_id"] == "T4"].iloc[0]

    obs1, obs2, obs3, obs4 = t1_row["empirical_value"], t2_row["empirical_value"], t3_row["empirical_value"], t4_row["empirical_value"]
    m1, m2, m3, m4 = best["T1_model"], best["T2_model"], best["T3_model"], best["T4_model"]
    best_alpha, best_beta, best_kappa = best["alpha"], best["beta"], best["kappa"]

    print("\n=== FUKUSHIMA CALIBRATION REPORT ===")
    print("Physical constraints (fixed empirically):")
    print("  conflict_movechance = 0.25  (Hayano 2013, inner zone clearing)")
    print("  max_move_speed      = 20.0  (Shimazaki 2012, probe-car data)")
    print("  default_movechance  = 0.005 (shelter-in-place compliance)")
    print("Cognitive parameters (free, grid-searched):")
    print(f"  Best: alpha={best_alpha}, beta={best_beta}, kappa={best_kappa}")
    print(f"Loss: {best['loss']:.6f}")
    print("\nCalibration target performance:")
    print(f"  T1 (<5km at t=15h):     observed={obs1:.2f}, modeled={m1:.4f}, diff={m1-obs1:.4f}")
    print(f"  T2 (<5km at t=20h):     observed={obs2:.2f}, modeled={m2:.4f}, diff={m2-obs2:.4f}")
    print(f"  T3 (15-20km at t=33h):  observed={obs3:.2f}, modeled={m3:.4f}, diff={m3-obs3:.4f}")
    print(f"  T4 (<20km at t=72h):    observed={obs4:.3f}, modeled={m4:.4f}, diff={m4-obs4:.4f}")
    print(f"\nPhase boundaries (best-fit run):")
    print(f"  t*  = {tstar} (Phase 1 minimum — end of acute S1-dominated response)")
    print(f"  t** = {tstarstar} (Phase 2 plateau onset — Psi heterogeneity visible)")

    # Dimensionless Phase 1 duration tau* (raw formula gives days; normalize to years)
    best_beta = best["beta"]
    d_star = compute_characteristic_distance(
        best_beta, str(CONFLICTS_CSV), str(LOCATIONS_CSV), str(ROUTES_CSV)
    )
    tau_star_raw = (tstar * FIXED_MAX_SPEED) / d_star if d_star > 0 else float("inf")
    tau_star = tau_star_raw / DAYS_PER_YEAR if tau_star_raw != float("inf") else tau_star_raw
    print("\nDimensionless Phase 1 duration (tau* in years):")
    print(f"  d*(beta={best_beta:.1f}) = {d_star:.1f} km")
    print(f"  t* = {tstar} steps")
    print(f"  v  = {FIXED_MAX_SPEED} km/step")
    print(f"  tau* = t* * v / d* = {tau_star:.2f}")
    print("  Target: tau* ≈ 1.0")
    print("\n  tau* interpretation:")
    print("    tau* < 1: Phase 1 ends before median agent reaches Omega=0.5 zone (fast evacuation)")
    print("    tau* ≈ 1: Well-calibrated — phase transition matches spatial scale")
    print("    tau* >> 1: Simulation window too short or max_move_speed too slow")

    if tstar > N_TIMESTEPS - 5:
        print(f"\nWARNING: t*={tstar} is within 5 steps of simulation end.")
        print(f"         tau*={tau_star:.2f} may be an artifact of simulation window.")
        print("         Consider extending N_TIMESTEPS further or increasing max_move_speed.")

    # Write phase_boundaries.csv for integration tests
    phase_df = pd.DataFrame([{
        "tstar": tstar,
        "tstarstar": tstarstar,
        "tau_star": tau_star,
        "mean_s2_t0": rows[0]["mean_s2"],
        "mean_s2_tstar": rows[tstar]["mean_s2"] if tstar < len(rows) else np.nan,
        "mean_s2_tstarstar": rows[tstarstar]["mean_s2"] if tstarstar < len(rows) else np.nan,
        "std_s2_tstar": rows[tstar]["std_s2"] if tstar < len(rows) else np.nan,
        "std_s2_tstarstar": rows[tstarstar]["std_s2"] if tstarstar < len(rows) else np.nan,
    }])
    phase_df.to_csv(RESULTS_DIR / "phase_boundaries.csv", index=False)
    print(f"\nWrote {RESULTS_DIR / 'phase_boundaries.csv'}")

    # Zone-level phase analysis (Fukushima has 3 ordered waves; global tau* is superposition)
    print("\n=== ZONE-LEVEL PHASE ANALYSIS ===")
    print("(Two-phase structure per ordered evacuation wave)")
    zone_results = compute_zone_phase_boundaries(
        agent_history_df, FUKUSHIMA_ZONES, beta=best_beta,
        v=FIXED_MAX_SPEED, d_star=d_star
    )
    print(f"{'Zone':<12} {'Onset':>6} {'t*':>5} {'t**':>5} {'tau*':>7} "
          f"{'P_S2(onset)':>11} {'P_S2(t*)':>10} {'P_S2(t**)':>10}")
    print("-" * 70)
    for zone, r in zone_results.items():
        tau_ok = 0.5 <= r["tau_star"] <= 3.0
        flag = " OK" if tau_ok else " !!"
        print(f"{zone:<12} {r['t_conflict_onset']:>6} {r['t_star']:>5} "
              f"{r['t_starstar']:>5} {r['tau_star']:>7.2f}{flag} "
              f"{r['ps2_at_onset']:>11.3f} {r['ps2_at_tstar']:>10.3f} "
              f"{r['ps2_at_tstarstar']:>10.3f}")
    print()
    print("tau* interpretation: distance-normalized Phase 1 duration.")
    print("Target tau* in [0.5, 3.0] per zone.")
    print("Zones outside range flagged with !!")

    import csv
    zone_csv = RESULTS_DIR / "zone_phase_boundaries.csv"
    with open(zone_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "zone", "t_conflict_onset", "t_star", "t_starstar",
            "tau_star", "ps2_at_onset", "ps2_at_tstar", "ps2_at_tstarstar",
            "n_agents"
        ])
        writer.writeheader()
        for zone, r in zone_results.items():
            writer.writerow({"zone": zone, **r})
    print(f"Zone phase boundaries saved to {zone_csv}")

    # Save full agent history and zone P_S2 time series for plotting
    agent_history_df.to_csv(RESULTS_DIR / "agent_history.csv", index=False)
    print(f"Agent history saved to {RESULTS_DIR / 'agent_history.csv'}")

    zone_ps2_list = []
    for zone_label in ["inner_3km", "zone_10km", "zone_20km"]:
        zm = agent_history_df["origin_zone"] == zone_label
        zd = agent_history_df[zm]
        if zd.empty:
            continue
        grp = zd.groupby("step")["s2_weight"].agg(["mean", "std"])
        grp = grp.rename(columns={"mean": "mean_ps2", "std": "std_ps2"})
        grp["zone"] = zone_label
        grp = grp.reset_index()
        zone_ps2_list.append(grp)
    if zone_ps2_list:
        zone_ps2_df = pd.concat(zone_ps2_list, ignore_index=True)
        zone_ps2_df.to_csv(RESULTS_DIR / "zone_ps2_timeseries.csv", index=False)
        print(f"Zone P_S2 time series saved to {RESULTS_DIR / 'zone_ps2_timeseries.csv'}")

    # Shelter-in-place diagnostic: Tomioka and Naraha population fraction by step
    SHELTER_STEPS = [1, 4, 8, 12, 14, 30, 60, 100, 200]
    print("\n[SHELTER-IN-PLACE CHECK] Tomioka population fraction by step:")
    for s in SHELTER_STEPS:
        if s < len(rows):
            frac = rows[s].get("frac_Tomioka", np.nan)
            marker = "  <- conflict order fires here" if s == 8 else ("  <- 20km order fires here" if s == 14 else "")
            print(f"  step {s:2d}:  {frac:.2f}{marker}")
    print("[SHELTER-IN-PLACE CHECK] Naraha population fraction by step:")
    for s in SHELTER_STEPS:
        if s < len(rows):
            frac = rows[s].get("frac_Naraha", np.nan)
            marker = "  <- conflict order fires here" if s == 8 else ("  <- 20km order fires here" if s == 14 else "")
            print(f"  step {s:2d}:  {frac:.2f}{marker}")

    # Inner zone clearing check (Futaba+Okuma, <5km) — Hayano data: ~95% cleared by step 9
    INNER_STEPS = [5, 9, 12]
    frac_key = "frac_<5km"
    print("\n[INNER ZONE CLEARING CHECK] Futaba+Okuma (<5km) fraction remaining by step:")
    for s in INNER_STEPS:
        if s < len(rows):
            frac = rows[s].get(frac_key, np.nan)
            print(f"  step {s:2d}:  {frac:.2f}  (Hayano: ~0.05-0.15 at step 9)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
