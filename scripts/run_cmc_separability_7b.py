#!/usr/bin/env python3
"""
Day 7b Section 5 -- CMC separability re-run at adequate sample size.

For each fixed CMC level in {0.25, 0.50, 0.75}, run a full D=3 Saltelli
design over (alpha, beta, kappa) with n_samples=200 (-> 1000 evaluations
per level, 3000 total). For each (QoI, parameter) cell, compute the
maximum drift in ST across the three CMC levels:

    max_drift = max(ST_at_cmc) - min(ST_at_cmc)
    separable  = max_drift <= 0.15

The result tells the Day 8 calibration design whether (alpha, beta, kappa)
sensitivity is invariant to CMC. If it is, Stage 1 of the two-stage
calibration can fix CMC; if it is not, CMC must enter Stage 1.

Usage::

    python3 scripts/run_cmc_separability_7b.py --n-samples 200 --ensemble 3
    python3 scripts/run_cmc_separability_7b.py --quick --n-samples 4
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import run_sobol_day7b as d7b  # noqa: E402

PROBLEM_3D = {
    "num_vars": 3,
    "names": ["alpha", "beta", "kappa"],
    "bounds": [[0.5, 5.0], [1.0, 10.0], [1.0, 20.0]],
}

CMC_LEVELS = [0.25, 0.50, 0.75]

DAY7_SEP_PATH = REPO / "results" / "day7" / "cmc_separability.csv"


def _load_day7_verdict() -> Dict:
    """Return Day 7 separability verdict per (QoI, Param) for cross-comparison."""
    if not DAY7_SEP_PATH.exists():
        return {}
    df = pd.read_csv(DAY7_SEP_PATH)
    out = {}
    if "separable" in df.columns:
        for _, r in df.iterrows():
            out[(r["qoi"], r["parameter"])] = bool(r["separable"])
    return out


def main():
    ap = argparse.ArgumentParser(description="Day 7b CMC separability re-run.")
    ap.add_argument("--n-samples", type=int, default=200)
    ap.add_argument("--ensemble", type=int, default=3)
    ap.add_argument("--n-agents", type=int, default=300)
    ap.add_argument("--n-steps", type=int, default=72)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--parallel", action="store_true")
    ap.add_argument("--n-workers", type=int,
                    default=max(1, ((__import__("os").cpu_count() or 2) - 1)))
    args = ap.parse_args()

    if args.quick:
        args.n_samples = 4

    out_dir = REPO / "results" / "day7b"
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    indices_per_level: Dict[float, pd.DataFrame] = {}
    raw_per_level: List[pd.DataFrame] = []
    acceptance_per_level: Dict[float, dict] = {}
    n_samples_used_per_level: Dict[float, int] = {}

    def _check_acceptance(idx_df: pd.DataFrame) -> dict:
        neg = idx_df[idx_df["S_first"] < -0.01]
        over1 = idx_df[idx_df["ST"] > 1.01]
        wide = idx_df[(idx_df["ST"] > 0.10)
                      & (idx_df["CI_width"] > 0.40)]
        return {
            "n_negative_S_first": int(len(neg)),
            "n_ST_exceeds_1": int(len(over1)),
            "n_wide_CI": int(len(wide)),
            "hard_fail": bool(len(neg) > 0 or len(over1) > 0),
            "soft_warn": bool(len(wide) > 0),
        }

    for cmc in CMC_LEVELS:
        n_samples_this = args.n_samples
        for attempt in (1, 2):
            print("\n" + "=" * 72)
            print(f"CMC separability  --  fixed CMC = {cmc:.2f}, "
                  f"n_samples={n_samples_this}, ensemble={args.ensemble}, "
                  f"attempt={attempt}")
            print("=" * 72)
            _, results = d7b.run_sobol_campaign(
                PROBLEM_3D,
                n_samples=n_samples_this,
                n_agents=args.n_agents,
                n_steps=args.n_steps,
                n_members=args.ensemble,
                cmc_fixed=cmc,
                parallel=args.parallel,
                n_workers=args.n_workers,
                seed=7000000 + int(round(cmc * 1000)) + (100 * attempt),
            )
            results = results.copy()
            results["cmc_fixed"] = cmc
            results["n_samples_used"] = n_samples_this
            idx = d7b.analyze_sobol(PROBLEM_3D, results, n_resamples=1000)
            acc = _check_acceptance(idx)
            acc["n_samples"] = n_samples_this
            acc["attempt"] = attempt
            print(f"  [accept@cmc={cmc:.2f}] negS_first={acc['n_negative_S_first']}, "
                  f"ST>1={acc['n_ST_exceeds_1']}, wideCI={acc['n_wide_CI']}")
            if (not acc["hard_fail"]) or attempt == 2:
                indices_per_level[cmc] = idx
                raw_per_level.append(results)
                acceptance_per_level[cmc] = acc
                n_samples_used_per_level[cmc] = n_samples_this
                idx.to_csv(out_dir / f"sobol_indices_cmc_{int(round(cmc*100)):03d}.csv",
                           index=False)
                break
            print(f"  [accept] HARD FAIL at cmc={cmc:.2f} n={n_samples_this}; "
                  f"bumping to n_samples=300 and retrying")
            n_samples_this = 300

    # Stitch raw results
    raw = pd.concat(raw_per_level, ignore_index=True)
    raw.to_csv(out_dir / "raw_results_cmc_separability.csv", index=False)

    # Build separability table
    day7_verdict = _load_day7_verdict()
    rows = []
    for qoi in d7b.QOI_KEYS:
        for p in PROBLEM_3D["names"]:
            sts: List[float] = []
            cis_lo: List[float] = []
            cis_hi: List[float] = []
            cis_str: List[str] = []
            for cmc in CMC_LEVELS:
                row = indices_per_level[cmc][
                    (indices_per_level[cmc]["qoi"] == qoi)
                    & (indices_per_level[cmc]["parameter"] == p)]
                if not len(row):
                    sts.append(np.nan)
                    cis_lo.append(np.nan)
                    cis_hi.append(np.nan)
                    cis_str.append("nan")
                else:
                    st = float(row["ST"].iloc[0])
                    lo = float(row["ST_CI_low"].iloc[0])
                    hi = float(row["ST_CI_high"].iloc[0])
                    sts.append(st)
                    cis_lo.append(lo)
                    cis_hi.append(hi)
                    cis_str.append(f"[{lo:.3f}, {hi:.3f}]")
            sts_arr = np.asarray(sts, dtype=float)
            if np.all(np.isnan(sts_arr)):
                continue
            max_drift = float(np.nanmax(sts_arr) - np.nanmin(sts_arr))
            separable = bool(max_drift <= 0.15)
            d7v = day7_verdict.get((qoi, p), None)
            changed = ((d7v is not None) and (d7v != separable))
            rows.append({
                "QoI": qoi, "Param": p,
                "ST_cmc025": sts[0], "ST_cmc025_CI": cis_str[0],
                "ST_cmc050": sts[1], "ST_cmc050_CI": cis_str[1],
                "ST_cmc075": sts[2], "ST_cmc075_CI": cis_str[2],
                "Max_drift": max_drift,
                "Separable": separable,
                "Day7_verdict": d7v,
                "Changed": bool(changed),
            })
    sep_df = pd.DataFrame(rows)
    sep_path = out_dir / "cmc_separability_full.csv"
    sep_df.to_csv(sep_path, index=False)
    print("\n=== CMC separability table ===\n")
    print(sep_df.to_string(index=False))

    # Summary stats
    n_total = len(sep_df)
    n_sep = int(sep_df["Separable"].sum())
    n_flip = int(sep_df["Changed"].fillna(False).sum())
    proc_qois = ["mid_ps2_trough", "mid_ps2_dip"]
    proc_sub = sep_df[sep_df["QoI"].isin(proc_qois)]
    n_proc_sep = int(proc_sub["Separable"].sum())
    n_proc = len(proc_sub)
    out_qois = ["hayano_t4", "corridor_inland_pct", "blend_inner_t7"]
    out_sub = sep_df[sep_df["QoI"].isin(out_qois)]
    n_out_sep = int(out_sub["Separable"].sum())
    n_out = len(out_sub)

    summary = {
        "n_samples_requested": int(args.n_samples),
        "n_samples_used": {f"{cmc:.2f}": int(n_samples_used_per_level[cmc])
                            for cmc in CMC_LEVELS},
        "n_eval_per_level": {f"{cmc:.2f}":
                              int(n_samples_used_per_level[cmc] *
                                  (PROBLEM_3D["num_vars"] + 2))
                              for cmc in CMC_LEVELS},
        "n_levels": int(len(CMC_LEVELS)),
        "ensemble_members": int(args.ensemble),
        "total_evaluations": int(sum(
            n_samples_used_per_level[cmc] * (PROBLEM_3D["num_vars"] + 2)
            for cmc in CMC_LEVELS)),
        "acceptance_per_level": {f"{cmc:.2f}": acceptance_per_level[cmc]
                                  for cmc in CMC_LEVELS},
        "elapsed_min": (time.time() - t0) / 60.0,
        "cells_total": n_total,
        "cells_separable": n_sep,
        "cells_changed_from_day7": n_flip,
        "process_qoi_separable": f"{n_proc_sep}/{n_proc}",
        "outcome_qoi_separable": f"{n_out_sep}/{n_out}",
    }
    with (out_dir / "cmc_separability_summary.json").open("w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n[sep] separability table -> {sep_path}")
    print(f"[sep] summary -> {out_dir/'cmc_separability_summary.json'}")
    print(f"[sep] elapsed: {summary['elapsed_min']:.1f} min")


if __name__ == "__main__":
    main()
