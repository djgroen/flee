#!/usr/bin/env python3
"""Day 12 Task B — TMI 4-mode first run with N=5 replicates.

Mirrors the Fukushima Day 3 protocol on the TMI network using the FROZEN
Fukushima parameters (no retuning). Produces the QoI table comparing each mode
against tmi_empirical_data.json, with mean +/- std across seeds [0..4].

Outputs:
  results/tmi/day12_first_run_qoi_table.csv     (deliverable: mode x 6 QoIs)
  results/tmi/day12_first_run_timeseries.csv     (per mode/seed/timestep metrics)
  results/tmi/day12_first_run_summary.json       (headline numbers for commit)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tmi_common_day12 import (  # noqa: E402
    REPO, TMI, MODE_ORDER, MIXTURE_MODE, T_MAX, POP_20MI,
    FROZEN_ALPHA, FROZEN_BETA, FROZEN_KAPPA, FROZEN_CMC,
    load_locations, run_one,
)

RESULTS = REPO / "results" / "tmi"
SEEDS = [0, 1, 2, 3, 4]
N_AGENTS = 2000
ZONES = ["inner", "middle", "outer"]


def _zone_pops(locinfo):
    pops = {z: 0 for z in ZONES}
    for v in locinfo.values():
        if v["zone"] in pops:
            pops[v["zone"]] += v["pop"]
    return pops


def per_run_metrics(agents, arrivals, mobility, locinfo):
    """Scalar metrics for one (mode, seed) run."""
    m = {}
    init_zone = agents.groupby("agent_id")["initial_zone"].first()
    n_total = init_zone.shape[0]
    arrived_ids = set(arrivals["agent_id"]) if not arrivals.empty else set()

    # Zone evac rates + total.
    for z in ZONES:
        zids = init_zone[init_zone == z].index
        n = len(zids)
        nev = sum(1 for i in zids if i in arrived_ids)
        m[f"evac_rate_{z}"] = nev / n if n else float("nan")
    m["evac_frac_town"] = len(arrived_ids) / n_total if n_total else 0.0
    town_pop = sum(v["pop"] for v in locinfo.values() if v["ltype"] != "camp")
    m["total_evac_rate_20mi"] = m["evac_frac_town"] * town_pop / POP_20MI

    # Inner-zone departures by t=10 (reached camp by t<=10).
    inner_ids = set(init_zone[init_zone == "inner"].index)
    if inner_ids and not arrivals.empty:
        a_inner = arrivals[arrivals["agent_id"].isin(inner_ids)]
        m["inner_departed_by_t10"] = (a_inner["arrival_timestep"] <= 10).sum() / len(inner_ids)
    else:
        m["inner_departed_by_t10"] = float("nan")

    # Advisory-window mobility spike: mobility(t=10) and mobility(t=5).
    mob = mobility.set_index("timestep")["mobility_rate"]
    m["mobility_t5"] = float(mob.get(5, float("nan")))
    m["mobility_t10"] = float(mob.get(10, float("nan")))
    m["mobility_spike_delta"] = m["mobility_t10"] - m["mobility_t5"]

    # Path-length-at-arrival, inner vs outer (arrivers only).
    if not arrivals.empty:
        pin = arrivals[arrivals["initial_zone"] == "inner"]["path_length_km"]
        pout = arrivals[arrivals["initial_zone"] == "outer"]["path_length_km"]
        m["path_inner_mean"] = float(pin.mean()) if len(pin) else float("nan")
        m["path_outer_mean"] = float(pout.mean()) if len(pout) else float("nan")
        m["path_inner_minus_outer"] = m["path_inner_mean"] - m["path_outer_mean"]
    else:
        m["path_inner_mean"] = m["path_outer_mean"] = m["path_inner_minus_outer"] = float("nan")

    # Camp fill by horizon: of agents that DEPARTED (ever left origin), fraction
    # in a camp at t_max.
    final = agents[agents["timestep"] == T_MAX].set_index("agent_id")
    moved_ever = agents.groupby("agent_id")["moved_this_step"].any()
    departed_ids = moved_ever[moved_ever].index
    if len(departed_ids):
        in_camp_final = final.reindex(departed_ids)["in_camp"].fillna(False)
        m["camp_fill_of_evacuees"] = float(in_camp_final.mean())
    else:
        m["camp_fill_of_evacuees"] = float("nan")
    return m


def cum_departure_timeseries(arrivals, locinfo, mode, seed, init_zone):
    """Cumulative camp-arrival fraction by zone over time (for the figure)."""
    rows = []
    for z in ZONES:
        zids = set(init_zone[init_zone == z].index)
        n = len(zids)
        if not arrivals.empty:
            az = arrivals[arrivals["agent_id"].isin(zids)]
            arr_t = az["arrival_timestep"].values
        else:
            arr_t = np.array([])
        for t in range(T_MAX + 1):
            frac = (np.sum(arr_t <= t) / n) if n else 0.0
            rows.append({"decision_mode": mode, "seed": seed, "timestep": t,
                         "zone": z, "cum_departed_frac": frac, "zone_n": n})
    return rows


# QoI acceptance bands (model_mean within -> within_range True).
QOI_SPECS = [
    # (qoi_name, metric_key, empirical_target, source, band_lo, band_hi, kind)
    ("total_evac_rate_20mi", "total_evac_rate_20mi", 0.21,
     "derived 140k/663.5k (sanity)", 0.15, 0.30, "range"),
    ("evac_rate_inner", "evac_rate_inner", 0.55,
     "Zeigler 1981 Table III (1-6mi)", 0.45, 0.65, "range"),
    ("evac_rate_middle", "evac_rate_middle", 0.50,
     "Zeigler 1981 Table III (7-12mi)", 0.40, 0.60, "range"),
    ("evac_rate_outer", "evac_rate_outer", 0.16,
     "Zeigler 1981 Table III (13+mi)", 0.10, 0.25, "range"),
    ("inner_departed_by_t10", "inner_departed_by_t10", 0.77,
     "Zeigler inner by Friday", 0.77, 1.01, "range"),
    ("advisory_mobility_spike", "mobility_spike_delta", 0.0,
     "mobility(t10)>mobility(t5)", 1e-9, 1e9, "range"),
    ("path_inner_lt_outer_km", "path_inner_minus_outer", 0.0,
     "Zeigler P3: inner<outer (gap<0)", -1e9, -1e-9, "range"),
    ("camp_fill_of_evacuees", "camp_fill_of_evacuees", 0.90,
     ">=90% of departers in camps", 0.90, 1.01, "range"),
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    locinfo = load_locations()

    print(f"TMI Day 12 first run | modes={MODE_ORDER} | seeds={SEEDS} | "
          f"n_agents={N_AGENTS} | t_max={T_MAX}")
    print(f"Frozen: alpha={FROZEN_ALPHA} beta={FROZEN_BETA} kappa={FROZEN_KAPPA} "
          f"CMC={FROZEN_CMC}")
    print(f"Zone pops: {_zone_pops(locinfo)}  town_pop="
          f"{sum(v['pop'] for v in locinfo.values() if v['ltype']!='camp')}")

    per_run = {m: [] for m in MODE_ORDER}
    ts_rows = []
    dep_rows = []

    for mode in MODE_ORDER:
        for seed in SEEDS:
            agents, arrivals, mobility = run_one(mode, N_AGENTS, T_MAX, seed)
            metrics = per_run_metrics(agents, arrivals, mobility, locinfo)
            per_run[mode].append(metrics)
            for _, r in mobility.iterrows():
                ts_rows.append({"decision_mode": mode, "seed": seed,
                                "timestep": int(r["timestep"]),
                                "mobility_rate": float(r["mobility_rate"]),
                                "n_active": int(r["n_active"])})
            init_zone = agents.groupby("agent_id")["initial_zone"].first()
            dep_rows.extend(cum_departure_timeseries(arrivals, locinfo, mode, seed, init_zone))
        ev = np.mean([d["evac_frac_town"] for d in per_run[mode]])
        print(f"  {mode:10}: town evac {ev:.3f} | "
              f"inner/mid/outer "
              f"{np.mean([d['evac_rate_inner'] for d in per_run[mode]]):.2f}/"
              f"{np.mean([d['evac_rate_middle'] for d in per_run[mode]]):.2f}/"
              f"{np.mean([d['evac_rate_outer'] for d in per_run[mode]]):.2f}")

    # QoI table: 4 modes x 8 QoI rows, mean & std across seeds.
    qoi_rows = []
    for mode in MODE_ORDER:
        dd = per_run[mode]
        for qoi_name, key, target, source, lo, hi, _kind in QOI_SPECS:
            vals = np.array([d[key] for d in dd], dtype=float)
            mean = float(np.nanmean(vals))
            std = float(np.nanstd(vals))
            within = bool(lo <= mean <= hi) if not np.isnan(mean) else False
            qoi_rows.append({
                "mode": mode, "qoi_name": qoi_name,
                "model_mean": round(mean, 5), "model_std": round(std, 5),
                "empirical_target": target, "empirical_source": source,
                "within_range": within,
            })
    qoi_df = pd.DataFrame(qoi_rows)
    qoi_path = RESULTS / "day12_first_run_qoi_table.csv"
    qoi_df.to_csv(qoi_path, index=False)
    print(f"\nWrote {qoi_path}  ({qoi_df.shape[0]} rows = "
          f"{qoi_df['mode'].nunique()} modes x {qoi_df['qoi_name'].nunique()} QoIs)")

    pd.DataFrame(ts_rows).to_csv(RESULTS / "day12_first_run_timeseries.csv", index=False)
    pd.DataFrame(dep_rows).to_csv(RESULTS / "day12_departure_by_zone.csv", index=False)

    # Headline numbers (mixture mode) for the commit header.
    mix = qoi_df[qoi_df["mode"] == MIXTURE_MODE].set_index("qoi_name")
    summary = {
        "n_agents": N_AGENTS, "seeds": SEEDS, "t_max": T_MAX,
        "frozen": {"alpha": FROZEN_ALPHA, "beta": FROZEN_BETA,
                   "kappa": FROZEN_KAPPA, "conflict_movechance": FROZEN_CMC},
        "mixture_mode": MIXTURE_MODE,
        "total_evac_rate_20mi_mean": float(mix.loc["total_evac_rate_20mi", "model_mean"]),
        "evac_rate_inner": float(mix.loc["evac_rate_inner", "model_mean"]),
        "evac_rate_middle": float(mix.loc["evac_rate_middle", "model_mean"]),
        "evac_rate_outer": float(mix.loc["evac_rate_outer", "model_mean"]),
        "mobility_t5": float(np.nanmean([d["mobility_t5"] for d in per_run[MIXTURE_MODE]])),
        "mobility_t10": float(np.nanmean([d["mobility_t10"] for d in per_run[MIXTURE_MODE]])),
        "path_inner_mean": float(np.nanmean([d["path_inner_mean"] for d in per_run[MIXTURE_MODE]])),
        "path_outer_mean": float(np.nanmean([d["path_outer_mean"] for d in per_run[MIXTURE_MODE]])),
        "p4_shadow_evac_outer": float(mix.loc["evac_rate_outer", "model_mean"]),
    }
    with (RESULTS / "day12_first_run_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print("Summary:", json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
