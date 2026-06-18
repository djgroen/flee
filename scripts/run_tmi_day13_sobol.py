#!/usr/bin/env python3
"""Day 13 -- TMI four-factor Sobol campaign (Tasks A, B, C).

Mirrors the Fukushima Day-7b Sobol analysis on the TMI network, adding
``conflict_movechance`` (CMC) as a fourth factor alongside alpha/beta/kappa.
Full-mixture (``blend``) mode only -- the sole mode where alpha/beta/kappa act
and CMC enters via the System-1 move chance.

Sampler   : SALib Saltelli, base N (power of two), calc_second_order=True
            -> total samples = N*(2D+2) = N*10 for D=4 (Day-13 spec / gate #32).
Noise ctrl: each sample = MEAN QoI over 3 fixed seeds [0,1,2].
Clamp     : Task A/B run with the panic clamp ON  -> day13_sobol_evals.csv
            Task C  re-runs the SAME design clamp OFF -> day13_sobol_evals_noclamp.csv

QoIs are tiered by expected signal (the clamp + CMC saturation kills variance in
the obvious mobilisation QoIs); see ``QOI_TIERS``.

Usage::
    python3 scripts/run_tmi_day13_sobol.py --both            # clamp on + off
    python3 scripts/run_tmi_day13_sobol.py                   # clamp on only
    python3 scripts/run_tmi_day13_sobol.py --no-clamp        # clamp off only
    python3 scripts/run_tmi_day13_sobol.py --quick           # N=8 smoke
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from SALib.sample import sobol as sobol_sample  # noqa: E402

from scripts import tmi_common_day12 as tc  # noqa: E402

RES = REPO / "results" / "tmi"

PEAK_T = 10           # conflict peak (c=1.0); clamp fires here only
PRE_PEAK_T = 8        # strictly before c crosses 0.9 (c[9]=0.75, c[10]=1.0)
SHADOW_MI = 15.0      # outer shadow-evac distance threshold
SEEDS = [0, 1, 2]

# Factor order is fixed; CMC is the new fourth factor.
PROBLEM = {
    "num_vars": 4,
    "names": ["cmc", "alpha", "beta", "kappa"],
    "bounds": [[0.0, 0.30], [0.5, 5.0], [1.0, 10.0], [1.0, 20.0]],
}
SAMPLE_SEED = 13000000

# QoI tiering (Task B).
QOI_TIERS = {
    # Tier 1 -- primary identifiability QoIs (clamp-insensitive)
    "frac_by_t8":            1,
    "median_departure":      1,
    "peak_ps2":              1,
    "zone_ps2_spread_t10":   1,
    # Tier 2 -- Zeigler / differential QoIs (timing-based, NOT path-based)
    "gap_median_departure":  2,
    "gap_frac_by_t8":        2,
    # Tier 3 -- saturated QoIs (compute but flag)
    "total_evac":            3,
    "shadow_evac":           3,
}
QOI_KEYS = list(QOI_TIERS.keys())
ZONES3 = ["inner", "middle", "outer"]


# ---------------------------------------------------------------------------
# QoI extraction (Task B) -- operates on Day-12 run_one dataframes
# ---------------------------------------------------------------------------

def _departure_timesteps(adf: pd.DataFrame) -> pd.Series:
    """First timestep each agent leaves its t=0 origin node. NaN if never."""
    origin = adf[adf["timestep"] == 0].set_index("agent_id")["location"]
    merged = adf.merge(origin.rename("origin"), on="agent_id", how="left")
    moved = merged[merged["location"] != merged["origin"]]
    if moved.empty:
        return pd.Series(dtype=float)
    return moved.groupby("agent_id")["timestep"].min()


def _zone_of_agent(adf: pd.DataFrame) -> pd.Series:
    return adf[adf["timestep"] == 0].set_index("agent_id")["initial_zone"]


def compute_qois(adf: pd.DataFrame, locinfo: dict) -> dict:
    """Compute the eight tiered QoIs for one simulation run."""
    out = {k: float("nan") for k in QOI_KEYS}
    if adf.empty:
        return out

    agent_zone = _zone_of_agent(adf)
    all_ids = agent_zone.index
    n_all = len(all_ids)
    dep = _departure_timesteps(adf)  # indexed by agent_id

    # --- Tier 1.1: fraction departed by t<=8 (pre-clamp) ---
    out["frac_by_t8"] = float((dep <= PRE_PEAK_T).sum() / n_all) if n_all else float("nan")

    # --- Tier 1.2: median departure timestep over departers ---
    out["median_departure"] = float(dep.median()) if len(dep) else float("nan")

    # --- Tier 1.3: peak mean P_S2 over active agents ---
    active = adf[~adf["in_camp"]]
    if not active.empty:
        by_t = active.groupby("timestep")["sys2_weight"].mean()
        out["peak_ps2"] = float(by_t.max()) if len(by_t) else float("nan")

    # --- Tier 1.4: zone P_S2 spread at t=peak (std across zone means) ---
    at_peak = active[active["timestep"] == PEAK_T]
    zmeans = []
    for z in ZONES3:
        zsub = at_peak[at_peak["initial_zone"] == z]
        if not zsub.empty:
            zmeans.append(float(zsub["sys2_weight"].mean()))
    out["zone_ps2_spread_t10"] = float(np.std(zmeans)) if len(zmeans) >= 2 else float("nan")

    # --- Tier 2: inner/outer differential timing QoIs ---
    def _zone_median_dep(z):
        ids = agent_zone[agent_zone == z].index
        d = dep.reindex(ids).dropna()
        return float(d.median()) if len(d) else float("nan")

    def _zone_frac_t8(z):
        ids = agent_zone[agent_zone == z].index
        if len(ids) == 0:
            return float("nan")
        d = dep.reindex(ids)
        return float((d <= PRE_PEAK_T).sum() / len(ids))

    md_inner, md_outer = _zone_median_dep("inner"), _zone_median_dep("outer")
    out["gap_median_departure"] = (md_outer - md_inner
                                   if not (np.isnan(md_inner) or np.isnan(md_outer))
                                   else float("nan"))
    f_inner, f_outer = _zone_frac_t8("inner"), _zone_frac_t8("outer")
    out["gap_frac_by_t8"] = (f_inner - f_outer
                             if not (np.isnan(f_inner) or np.isnan(f_outer))
                             else float("nan"))

    # --- Tier 3.1: total town evac rate at horizon end (saturated) ---
    t_end = adf["timestep"].max()
    end = adf[adf["timestep"] == t_end]
    out["total_evac"] = float(end["in_camp"].sum() / n_all) if n_all else float("nan")

    # --- Tier 3.2: shadow evac (>15 mi origin) at horizon end ---
    origin_loc = adf[adf["timestep"] == 0].set_index("agent_id")["location"]
    origin_dist = origin_loc.map(lambda nm: locinfo.get(nm, {}).get("dist_mi", float("nan")))
    far_ids = origin_dist[origin_dist > SHADOW_MI].index
    if len(far_ids):
        far_end = end[end["agent_id"].isin(far_ids)]
        out["shadow_evac"] = float(far_end["in_camp"].sum() / len(far_ids))
    return out


# ---------------------------------------------------------------------------
# Campaign driver
# ---------------------------------------------------------------------------

def run_campaign(n_base: int, n_agents: int, enable_panic_clamp: bool,
                 out_csv: Path) -> pd.DataFrame:
    locinfo = tc.load_locations()
    X = sobol_sample.sample(PROBLEM, n_base, calc_second_order=True,
                            seed=SAMPLE_SEED)
    n_samples = X.shape[0]
    expected = n_base * (2 * PROBLEM["num_vars"] + 2)
    clamp_tag = "ON" if enable_panic_clamp else "OFF"
    print(f"[sobol|clamp {clamp_tag}] D={PROBLEM['num_vars']} N={n_base} "
          f"-> {n_samples} samples (expected {expected}); "
          f"seeds={SEEDS}; total runs={n_samples * len(SEEDS)}")

    rows = []
    t0 = time.time()
    step = max(1, n_samples // 20)
    for i, x in enumerate(X):
        cmc, alpha, beta, kappa = (float(x[0]), float(x[1]),
                                   float(x[2]), float(x[3]))
        for seed in SEEDS:
            adf, _arr, _mob = tc.run_one(
                "blend", n_agents, tc.T_MAX, seed,
                alpha=alpha, beta=beta, kappa=kappa, cmc=cmc,
                enable_panic_clamp=enable_panic_clamp,
            )
            q = compute_qois(adf, locinfo)
            rows.append({
                "sample_idx": i, "seed": seed,
                "clamp": "on" if enable_panic_clamp else "off",
                "cmc": cmc, "alpha": alpha, "beta": beta, "kappa": kappa,
                **q,
            })
        if (i + 1) % step == 0 or i == n_samples - 1:
            el = time.time() - t0
            rate = (i + 1) / max(1e-6, el)
            eta = (n_samples - i - 1) / max(1e-6, rate)
            print(f"  [{clamp_tag}] {i+1:4d}/{n_samples} samples "
                  f"({el:6.0f}s, ETA {eta:6.0f}s, {rate:.2f} samp/s)")

    df = pd.DataFrame(rows).sort_values(["sample_idx", "seed"]).reset_index(drop=True)
    df.to_csv(out_csv, index=False)
    print(f"[sobol|clamp {clamp_tag}] raw evals -> {out_csv} "
          f"({len(df)} rows, {time.time()-t0:.0f}s)")
    return df


def write_design_json(n_base: int, n_agents: int, did_clamp_off: bool) -> None:
    n_samples = n_base * (2 * PROBLEM["num_vars"] + 2)
    summary = {
        "problem": PROBLEM,
        "n_base": int(n_base),
        "is_power_of_two": (n_base & (n_base - 1) == 0) and n_base > 0,
        "calc_second_order": True,
        "total_samples": int(n_samples),
        "total_samples_formula": "N*(2D+2)=N*10",
        "seeds": SEEDS,
        "seeds_per_sample": len(SEEDS),
        "total_runs_clamp_on": int(n_samples * len(SEEDS)),
        "total_runs_clamp_off": int(n_samples * len(SEEDS)) if did_clamp_off else 0,
        "n_agents": int(n_agents),
        "mode": "blend",
        "t_max": tc.T_MAX,
        "peak_t": PEAK_T,
        "pre_peak_t": PRE_PEAK_T,
        "shadow_mi": SHADOW_MI,
        "qoi_tiers": QOI_TIERS,
        "factor_ranges": dict(zip(PROBLEM["names"], PROBLEM["bounds"])),
    }
    with (RES / "day13_sobol_design.json").open("w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"[sobol] design summary -> {RES/'day13_sobol_design.json'}")


def main():
    ap = argparse.ArgumentParser(description="Day 13 TMI 4-factor Sobol campaign.")
    ap.add_argument("--n-base", type=int, default=64,
                    help="Saltelli base sample N (power of two).")
    ap.add_argument("--n-agents", type=int, default=1000)
    ap.add_argument("--no-clamp", action="store_true",
                    help="Run clamp-OFF design only (Task C).")
    ap.add_argument("--both", action="store_true",
                    help="Run clamp-ON then clamp-OFF designs (Tasks A/B + C).")
    ap.add_argument("--quick", action="store_true",
                    help="Smoke run: N=8.")
    args = ap.parse_args()

    RES.mkdir(parents=True, exist_ok=True)
    n_base = 8 if args.quick else args.n_base

    print("=" * 72)
    print(f"Day 13 TMI Sobol  --  N={n_base}, n_agents={args.n_agents}, "
          f"factors={PROBLEM['names']}")
    print("=" * 72)

    did_off = False
    if args.no_clamp:
        run_campaign(n_base, args.n_agents, enable_panic_clamp=False,
                     out_csv=RES / "day13_sobol_evals_noclamp.csv")
        did_off = True
    else:
        run_campaign(n_base, args.n_agents, enable_panic_clamp=True,
                     out_csv=RES / "day13_sobol_evals.csv")
        if args.both:
            run_campaign(n_base, args.n_agents, enable_panic_clamp=False,
                         out_csv=RES / "day13_sobol_evals_noclamp.csv")
            did_off = True

    write_design_json(n_base, args.n_agents, did_off or args.both)


if __name__ == "__main__":
    main()
