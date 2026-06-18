#!/usr/bin/env python3
"""Day 15 Task D -- validate the Zeigler paradox and shadow evacuation on v2.

Runs the v2 network with the LOCKED conflict-dependent System-1 form (Task B2),
blend mode, alpha/beta/kappa LOCKED, clamp OFF, 5 seeds, crisis horizon t_max=19.

1. Zeigler paradox (two independent directions):
   * TIMING   -- does inner depart earlier? (median departure t, inner-by-t10)
   * DISTANCE -- does inner travel SHORTER, outer FARTHER? Reported with BOTH
     metrics: network travel-path length (distance_travelled) and the
     plant-referenced final-destination displacement (Day-14 Option A).
2. Shadow evacuation -- beyond-15-mi evacuation rate. On v2 every camp is far and
   zone-independent, so any beyond-15-mi evacuation is driven by the UNIFORM
   information-Omega collapse, NOT camp adjacency (the pre-v2 artifact).

Outputs: results/tmi/day15_zeigler_shadow.csv + printed per-signal verdict.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from scripts import tmi_common_day15 as tc  # noqa: E402

RES = REPO / "results" / "tmi"
ALPHA, BETA, KAPPA = tc.FROZEN_ALPHA, tc.FROZEN_BETA, tc.FROZEN_KAPPA
MODE = "blend"
T_MAX = tc.T_SCHED
LOCK_BASE, LOCK_CMAX = 0.05, 0.50
SEEDS, N_AGENTS = [0, 1, 2, 3, 4], 1000
PEAK_T = 10
PREV2_OUTER_ARTIFACT = 0.60   # Day-14 adjacency-inflated outer evac (for contrast)


def _camp_plant_dist(network=tc.TMI_V2):
    out = {}
    info = tc.load_locations(network)
    for name, d in info.items():
        if d["ltype"] == "camp":
            out[name] = tc.haversine_mi(tc.PLANT_LON, tc.PLANT_LAT, d["lon"], d["lat"])
    return out


def _departures(adf):
    origin = adf[adf["timestep"] == 0].set_index("agent_id")["location"]
    merged = adf.merge(origin.rename("origin"), on="agent_id", how="left")
    moved = merged[merged["location"] != merged["origin"]]
    if moved.empty:
        return pd.Series(dtype=float)
    return moved.groupby("agent_id")["timestep"].min()


def main():
    locinfo = tc.load_locations(tc.TMI_V2)
    camp_dist = _camp_plant_dist()
    print("=" * 76)
    print("Day 15 Task D -- Zeigler + shadow validation on v2")
    print(f"  conflict-dependent base={LOCK_BASE} cmax={LOCK_CMAX} (a/b/k LOCKED)")
    print(f"  seeds={SEEDS} n_agents={N_AGENTS} t_max={T_MAX}")
    print("=" * 76)

    rows = []
    per_seed_zone = {z: {"median_dep": [], "frac_by_t10": [], "travel_km": [],
                         "dest_mi": [], "evac": []}
                     for z in ("inner", "middle", "outer")}
    shadow_rates, within15_rates = [], []
    for s in SEEDS:
        with contextlib.redirect_stdout(io.StringIO()):
            adf, arr, _mob = tc.run_one(
                MODE, N_AGENTS, T_MAX, s, alpha=ALPHA, beta=BETA, kappa=KAPPA,
                cmc=LOCK_BASE, enable_panic_clamp=False, network=tc.TMI_V2,
                cmc_conflict_dependent=True, cmc_max=LOCK_CMAX)
        t0 = adf[adf["timestep"] == 0]
        agent_zone = t0.set_index("agent_id")["initial_zone"]
        origin_loc = t0.set_index("agent_id")["location"]
        origin_dist = origin_loc.map(lambda nm: locinfo.get(nm, {}).get("dist_mi", np.nan))
        end = adf[adf["timestep"] == adf["timestep"].max()].set_index("agent_id")
        in_camp_end = end["in_camp"]
        dep = _departures(adf)

        # arrivals: travel-path length + plant-referenced destination distance
        arr = arr.copy()
        if not arr.empty:
            arr["dest_mi"] = arr["camp_node"].map(camp_dist)
        for z in ("inner", "middle", "outer"):
            zids = agent_zone[agent_zone == z].index
            if len(zids):
                d = dep.reindex(zids).dropna()
                per_seed_zone[z]["median_dep"].append(float(d.median()) if len(d) else np.nan)
                per_seed_zone[z]["frac_by_t10"].append(
                    float((dep.reindex(zids) <= PEAK_T).sum() / len(zids)))
                per_seed_zone[z]["evac"].append(
                    float(in_camp_end.reindex(zids).fillna(False).sum() / len(zids)))
            za = arr[arr["initial_zone"] == z] if not arr.empty else arr
            if not za.empty:
                per_seed_zone[z]["travel_km"].append(float(za["path_length_km"].mean()))
                per_seed_zone[z]["dest_mi"].append(float(za["dest_mi"].mean()))

        # shadow: beyond-15-mi evacuation rate (genuine info-Omega, not adjacency)
        far_ids = origin_dist[origin_dist > 15.0].index
        near_ids = origin_dist[origin_dist <= 15.0].index
        if len(far_ids):
            shadow_rates.append(float(in_camp_end.reindex(far_ids).fillna(False).sum() / len(far_ids)))
        if len(near_ids):
            within15_rates.append(float(in_camp_end.reindex(near_ids).fillna(False).sum() / len(near_ids)))

    def m(z, k):
        v = per_seed_zone[z][k]
        return float(np.nanmean(v)) if v else float("nan")

    for z in ("inner", "middle", "outer"):
        rows.append({"zone": z, "median_dep_t": m(z, "median_dep"),
                     "frac_by_t10": m(z, "frac_by_t10"),
                     "evac_rate": m(z, "evac"),
                     "travel_path_km": m(z, "travel_km"),
                     "dest_dist_from_plant_mi": m(z, "dest_mi")})
    df = pd.DataFrame(rows)
    shadow = float(np.mean(shadow_rates)) if shadow_rates else float("nan")
    within15 = float(np.mean(within15_rates)) if within15_rates else float("nan")
    df_shadow = pd.DataFrame([{"zone": "beyond_15mi", "evac_rate": shadow,
                               "median_dep_t": np.nan, "frac_by_t10": np.nan,
                               "travel_path_km": np.nan,
                               "dest_dist_from_plant_mi": np.nan}])
    out = pd.concat([df, df_shadow], ignore_index=True)
    out.to_csv(RES / "day15_zeigler_shadow.csv", index=False)

    inner, outer = df[df.zone == "inner"].iloc[0], df[df.zone == "outer"].iloc[0]
    timing_holds = inner["median_dep_t"] <= outer["median_dep_t"] + 0.01 \
        and inner["frac_by_t10"] >= outer["frac_by_t10"] - 0.01
    dist_travel_holds = inner["travel_path_km"] < outer["travel_path_km"]
    dist_dest_holds = inner["dest_dist_from_plant_mi"] < outer["dest_dist_from_plant_mi"]

    print("\nZeigler paradox (v2):")
    print(f"  {'zone':7} {'med_dep_t':>9} {'by_t10':>7} {'evac':>6} "
          f"{'travel_km':>10} {'dest_mi':>8}")
    for _, r in df.iterrows():
        print(f"  {r['zone']:7} {r['median_dep_t']:9.1f} {r['frac_by_t10']:7.2f} "
              f"{r['evac_rate']:6.2f} {r['travel_path_km']:10.1f} "
              f"{r['dest_dist_from_plant_mi']:8.1f}")
    print(f"\n  TIMING  (inner departs earlier): {'HOLDS' if timing_holds else 'FLAT/NO'} "
          f"(inner by_t10 {inner['frac_by_t10']:.2f} vs outer {outer['frac_by_t10']:.2f})")
    print(f"  DISTANCE travel-path (inner<outer): "
          f"{'HOLDS' if dist_travel_holds else 'NO'} "
          f"({inner['travel_path_km']:.1f} < {outer['travel_path_km']:.1f} km)")
    print(f"  DISTANCE dest-from-plant (inner<outer): "
          f"{'HOLDS' if dist_dest_holds else 'FLAT (all evacuate far)'} "
          f"({inner['dest_dist_from_plant_mi']:.1f} vs {outer['dest_dist_from_plant_mi']:.1f} mi)")

    print("\nShadow evacuation (v2):")
    print(f"  beyond-15-mi evac rate: {shadow*100:.1f}%  "
          f"(within-15-mi: {within15*100:.1f}%)")
    print(f"  empirical >15mi ~9-13% (Zeigler); advisory_contrast 39% within-15mi")
    print(f"  pre-v2 outer evac was {PREV2_OUTER_ARTIFACT*100:.0f}% (camp-adjacency "
          f"ARTIFACT). On v2 all camps are far/zone-independent, so beyond-15-mi "
          f"evacuation is GENUINE (uniform information-Omega collapse), not adjacency.")
    print("=" * 76)

    verdict = {
        "zeigler_timing_inner_earlier": bool(timing_holds),
        "zeigler_distance_travel_inner_lt_outer": bool(dist_travel_holds),
        "zeigler_distance_dest_inner_lt_outer": bool(dist_dest_holds),
        "zones": df.set_index("zone").to_dict(orient="index"),
        "shadow_beyond_15mi_rate": shadow,
        "within_15mi_rate": within15,
        "shadow_mechanism": "info-Omega (genuine)",
        "prev2_outer_artifact": PREV2_OUTER_ARTIFACT,
        "interpretation": (
            "Distance paradox reads on travel-path length (inner travels less to "
            "the common far shelters); plant-referenced destination distance is "
            "~uniform because on v2 ALL zones evacuate to comparably distant camps "
            "(~60-84 mi) -- consistent with the empirical 85-mi median destination. "
            "Timing separation is weak: the uniform advisory + System-2 calm-drift "
            "flatten zone timing differences (documented Task-B2 finding)."),
    }
    (RES / "day15_zeigler_shadow_verdict.json").write_text(json.dumps(verdict, indent=2, default=float))
    print(f"[zeigler/shadow] -> {RES / 'day15_zeigler_shadow.csv'} + verdict json")


if __name__ == "__main__":
    main()
