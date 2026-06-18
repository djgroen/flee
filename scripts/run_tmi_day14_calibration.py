#!/usr/bin/env python3
"""Day 14 -- Stage-1 CMC calibration grid for TMI (Task B).

The TMI analogue of Fukushima Day-8 Stage-1: at Fukushima CMC was physically
anchored and (alpha, beta, kappa) were fit; at TMI alpha/beta/kappa are LOCKED
at the Fukushima transfer values and CMC is the SINGLE free parameter. We run
the calibration in ``blend`` mode on the TMI OSM network, t_max = T_SCHED = 19,
5 seeds averaged per grid point, under BOTH panic-clamp states (ON and OFF).

This module is also the Day-14 *library*: the diagnostic, clamp-decision,
robustness and plotting scripts import its run helper, QoI extractor, empirical
targets and grid (Day-8 -> Day-9 reuse style).

CMC grid: fine [0.00, 0.12] step 0.01 (where Day 13 expects the answer), coarse
{0.15, 0.20, 0.25, 0.30} above.

Outputs::
    results/tmi/day14_calibration_grid.csv
        cmc, clamp, total_evac, evac_inner, evac_middle, evac_outer,
        frac_inner_by_t10, zeigler_gap, misfit  (+ reporting columns)

Usage::
    python3 scripts/run_tmi_day14_calibration.py            # full grid on+off
    python3 scripts/run_tmi_day14_calibration.py --quick    # coarse smoke
"""
from __future__ import annotations

import argparse
import contextlib
import io
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import tmi_common_day12 as tc  # noqa: E402

RES = REPO / "results" / "tmi"

# --- Locked Fukushima transfer parameters (DO NOT calibrate today) ----------
ALPHA_LOCKED = tc.FROZEN_ALPHA   # 1.6667
BETA_LOCKED = tc.FROZEN_BETA     # 2.1667
KAPPA_LOCKED = tc.FROZEN_KAPPA   # 18.407
FUKUSHIMA_CMC = 0.25             # locked Fukushima CMC, for contrast

# --- Run configuration ------------------------------------------------------
MODE = "blend"
T_MAX = tc.T_MAX                 # 19 = T_SCHED
N_AGENTS = 1000
SEEDS = [0, 1, 2, 3, 4]
PEAK_T = 10                      # Governor advisory; clamp fires here
REGION_MI = 20.0                # 20-mi population denominator (empirical scope)

# Day-12 total-evac convention (so check 41 is the EXACT flip of check 26):
#   total_evac_rate_20mi = evac_frac_town * town_pop / POP_20MI
# The model represents ~258k of the 20-mi region's 663.5k residents as mobile
# town agents; the established QoI scales the modeled evac fraction by that
# population ratio. We reuse this definition verbatim from
# run_tmi_day12_first_run.per_run_metrics() for comparability.
TOWN_POP = 258000.0              # sum of all town populations (locations.csv)
POP_20MI = tc.POP_20MI          # 663500.0
POP_SCALE = TOWN_POP / POP_20MI  # ~= 0.3889

# --- CMC grid (fine where the answer is expected, coarse above) -------------
CMC_FINE = [round(x, 2) for x in np.arange(0.00, 0.1201, 0.01)]   # 0.00..0.12
CMC_COARSE = [0.15, 0.20, 0.25, 0.30]
CMC_GRID = CMC_FINE + CMC_COARSE

# --- Empirical targets (Task 0.4) -------------------------------------------
TARGET_TOTAL_EVAC = 0.21
TARGET_EVAC = {"inner": 0.55, "middle": 0.50, "outer": 0.16}
TARGET_FRAC_INNER_BY_T10 = 0.77
EVAC_BAND = (0.15, 0.30)

# Misfit weights (QoIs 1-2 are primary). Total evac is the CMC-driven primary.
W_TOTAL = 1.0
W_ZONE = {"inner": 1.0, "middle": 1.0, "outer": 1.0}


# ---------------------------------------------------------------------------
# QoI extraction (operates on tmi_common_day12.run_one dataframes)
# ---------------------------------------------------------------------------

def _departure_timesteps(adf: pd.DataFrame) -> pd.Series:
    """First timestep each agent leaves its t=0 origin node (NaN if never)."""
    origin = adf[adf["timestep"] == 0].set_index("agent_id")["location"]
    merged = adf.merge(origin.rename("origin"), on="agent_id", how="left")
    moved = merged[merged["location"] != merged["origin"]]
    if moved.empty:
        return pd.Series(dtype=float)
    return moved.groupby("agent_id")["timestep"].min()


def compute_qois(adf: pd.DataFrame, locinfo: dict) -> dict:
    """Calibration QoIs for one run, scoped to the 20-mi population.

    Returns total_evac (20-mi), per-zone evac (inner/middle/outer within 20 mi),
    frac_inner_by_t10, the timing-based Zeigler gap, plus reporting extras.
    """
    out = {k: float("nan") for k in (
        "total_evac", "total_evac_all", "evac_frac_town", "evac_inner",
        "evac_middle", "evac_outer", "frac_inner_by_t10", "zeigler_gap",
        "median_dep_inner", "median_dep_outer")}
    if adf.empty:
        return out

    t0 = adf[adf["timestep"] == 0]
    agent_zone = t0.set_index("agent_id")["initial_zone"]
    origin_loc = t0.set_index("agent_id")["location"]
    origin_dist = origin_loc.map(
        lambda nm: locinfo.get(nm, {}).get("dist_mi", float("nan")))
    in20 = origin_dist[origin_dist <= REGION_MI].index

    t_end = adf["timestep"].max()
    end = adf[adf["timestep"] == t_end].set_index("agent_id")
    in_camp_end = end["in_camp"]

    # (1) total evac over the 20-mi population -- Day-12 convention (check 26):
    #     evac_frac_town (all modelled town agents arrived) * town_pop / POP_20MI.
    out["evac_frac_town"] = float(in_camp_end.sum() / len(agent_zone))
    out["total_evac"] = out["evac_frac_town"] * POP_SCALE
    # Raw within-20-mi fraction kept for reference (not the calibration QoI).
    if len(in20):
        out["total_evac_all"] = float(
            in_camp_end.reindex(in20).fillna(False).sum() / len(in20))

    # (2) evac rate by zone (zones restricted to <= 20 mi for fair comparison).
    for z in ("inner", "middle", "outer"):
        ids = agent_zone[(agent_zone == z) & (agent_zone.index.isin(in20))].index
        if len(ids):
            out[f"evac_{z}"] = float(
                in_camp_end.reindex(ids).fillna(False).sum() / len(ids))

    # (3) fraction of inner-zone agents departed by t=10.
    dep = _departure_timesteps(adf)
    inner_ids = agent_zone[agent_zone == "inner"].index
    if len(inner_ids):
        d_inner = dep.reindex(inner_ids)
        out["frac_inner_by_t10"] = float((d_inner <= PEAK_T).sum()
                                         / len(inner_ids))

    # (4) timing-based Zeigler gap: median_departure(outer) - inner.
    def _zmed(z):
        ids = agent_zone[agent_zone == z].index
        d = dep.reindex(ids).dropna()
        return float(d.median()) if len(d) else float("nan")
    out["median_dep_inner"] = _zmed("inner")
    out["median_dep_outer"] = _zmed("outer")
    if not (np.isnan(out["median_dep_inner"]) or np.isnan(out["median_dep_outer"])):
        out["zeigler_gap"] = out["median_dep_outer"] - out["median_dep_inner"]
    return out


def misfit(q: dict) -> float:
    """Weighted SSE on the PRIMARY QoIs (total evac + zone rates)."""
    terms = []
    if not np.isnan(q["total_evac"]):
        terms.append(W_TOTAL * (q["total_evac"] - TARGET_TOTAL_EVAC) ** 2)
    for z in ("inner", "middle", "outer"):
        v = q[f"evac_{z}"]
        if not np.isnan(v):
            terms.append(W_ZONE[z] * (v - TARGET_EVAC[z]) ** 2)
    return float(np.sum(terms)) if terms else float("nan")


# ---------------------------------------------------------------------------
# Run helper -- one (cmc, clamp) grid point, averaged over seeds
# ---------------------------------------------------------------------------

def run_point(cmc: float, enable_panic_clamp: bool, locinfo: dict,
              n_agents: int = N_AGENTS, seeds=SEEDS) -> dict:
    """Run one (cmc, clamp) point over ``seeds`` and return the mean QoIs."""
    per_seed = []
    for s in seeds:
        with contextlib.redirect_stdout(io.StringIO()):
            adf, _arr, _mob = tc.run_one(
                MODE, n_agents, T_MAX, s,
                alpha=ALPHA_LOCKED, beta=BETA_LOCKED, kappa=KAPPA_LOCKED,
                cmc=cmc, enable_panic_clamp=enable_panic_clamp)
        per_seed.append(compute_qois(adf, locinfo))
    keys = per_seed[0].keys()
    mean = {k: float(np.nanmean([d[k] for d in per_seed])) for k in keys}
    mean["misfit"] = misfit(mean)
    return mean


# ---------------------------------------------------------------------------
# Grid driver
# ---------------------------------------------------------------------------

def run_grid(cmc_grid, clamp_states, n_agents, seeds) -> pd.DataFrame:
    locinfo = tc.load_locations()
    rows = []
    total = len(cmc_grid) * len(clamp_states)
    t0 = time.time()
    k = 0
    for enable in clamp_states:
        for cmc in cmc_grid:
            q = run_point(cmc, enable, locinfo, n_agents, seeds)
            rows.append({"cmc": cmc, "clamp": "on" if enable else "off", **q})
            k += 1
            el = time.time() - t0
            print(f"  [{k:3d}/{total}] clamp={'on' if enable else 'off':3s} "
                  f"cmc={cmc:.2f} total_evac={q['total_evac']:.3f} "
                  f"in/mid/out={q['evac_inner']:.2f}/{q['evac_middle']:.2f}/"
                  f"{q['evac_outer']:.2f} misfit={q['misfit']:.4f} "
                  f"({el:.0f}s)")
    cols = ["cmc", "clamp", "total_evac", "evac_inner", "evac_middle",
            "evac_outer", "frac_inner_by_t10", "zeigler_gap", "misfit",
            "evac_frac_town", "total_evac_all", "median_dep_inner",
            "median_dep_outer"]
    return pd.DataFrame(rows)[cols]


def best_fit(df: pd.DataFrame, clamp: str) -> pd.Series:
    sub = df[df["clamp"] == clamp].dropna(subset=["misfit"])
    return sub.loc[sub["misfit"].idxmin()]


def main():
    ap = argparse.ArgumentParser(description="Day 14 TMI CMC calibration grid.")
    ap.add_argument("--quick", action="store_true",
                    help="Coarse smoke grid, 2 seeds.")
    ap.add_argument("--clamp", choices=["on", "off", "both"], default="both")
    args = ap.parse_args()

    RES.mkdir(parents=True, exist_ok=True)
    cmc_grid = CMC_GRID
    seeds = SEEDS
    n_agents = N_AGENTS
    if args.quick:
        cmc_grid = [0.00, 0.05, 0.10, 0.20, 0.30]
        seeds = [0, 1]
        n_agents = 500

    clamp_states = ({"on": [True], "off": [False],
                     "both": [True, False]}[args.clamp])

    print("=" * 72)
    print("Day 14 TMI CMC calibration  (alpha/beta/kappa LOCKED)")
    print(f"  alpha={ALPHA_LOCKED} beta={BETA_LOCKED} kappa={KAPPA_LOCKED}")
    print(f"  mode={MODE} t_max={T_MAX} n_agents={n_agents} seeds={seeds}")
    print(f"  CMC grid ({len(cmc_grid)}): {cmc_grid}")
    print(f"  clamp states: {['on' if e else 'off' for e in clamp_states]}")
    print(f"  targets: total={TARGET_TOTAL_EVAC} zones={TARGET_EVAC} "
          f"band={EVAC_BAND}")
    print("=" * 72)

    df = run_grid(cmc_grid, clamp_states, n_agents, seeds)
    out = RES / "day14_calibration_grid.csv"
    df.to_csv(out, index=False)
    print(f"\n[calibration] grid -> {out} ({len(df)} rows)")

    for enable in clamp_states:
        clamp = "on" if enable else "off"
        b = best_fit(df, clamp)
        print(f"\n[best-fit | clamp {clamp.upper()}] "
              f"CMC*={b['cmc']:.2f}  misfit={b['misfit']:.4f}")
        print(f"   total_evac={b['total_evac']:.3f} (target {TARGET_TOTAL_EVAC}, "
              f"band {EVAC_BAND}: "
              f"{'IN' if EVAC_BAND[0] <= b['total_evac'] <= EVAC_BAND[1] else 'OUT'})")
        print(f"   zone evac inner/mid/out = {b['evac_inner']:.2f}/"
              f"{b['evac_middle']:.2f}/{b['evac_outer']:.2f}  "
              f"(targets {TARGET_EVAC['inner']}/{TARGET_EVAC['middle']}/"
              f"{TARGET_EVAC['outer']})")
        print(f"   frac_inner_by_t10={b['frac_inner_by_t10']:.2f} "
              f"(target >{TARGET_FRAC_INNER_BY_T10})  "
              f"zeigler_gap={b['zeigler_gap']:.2f} "
              f"({'correct sign' if b['zeigler_gap'] > 0 else 'WRONG sign'})")


if __name__ == "__main__":
    main()
