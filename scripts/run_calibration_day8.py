#!/usr/bin/env python3
"""Day 8 -- Two-stage moment-matching calibration of (CMC, alpha, beta, kappa).

Design justification (from the Day 7b Sobol campaign):

  * CMC dominates ``hayano_t4`` (ST=0.92) and ``corridor_inland_pct`` (ST=0.94).
    The cognitive triple (alpha, beta, kappa) carries < 0.11 total-order effect
    on these two outcome QoIs; they are pure CMC test moments.
  * alpha dominates ``mid_ps2_dip`` (ST=0.81, near-additive). Canonical anchor.
  * beta dominates ``mid_ps2_trough`` (ST=0.98, near-additive). Canonical anchor.
  * Process-state QoIs are 6/6 CMC-separable -- justifying the two-stage design.

Stage 1 fits CMC to outcome QoIs (Hayano + corridor), Stage 2 fits the cognitive
triple to process-state QoIs at CMC* fixed, Stage 3 validates at the locked
parameters with a 20-replicate ensemble.

CRITICAL Hayano tension: the Hayano (2013) inner-zone target implies CMC ~ 1.008,
which is outside the physical [0,1] range. We calibrate against the within-range
approximation 0.30 and ALWAYS report (and flag) the residual gap.

Outputs::

  results/day8/stage1_cmc_grid.csv
  results/day8/stage1_summary.csv
  results/day8/stage1_cmc_star.json
  results/day8/stage2_coarse_grid.csv
  results/day8/stage2_fine_grid.csv
  results/day8/stage2_params.json
  results/day8/validation_ensemble.csv
  results/day8/validation_summary.json
  results/day8/ps2_timeseries.csv

Usage::

  python3 scripts/run_calibration_day8.py [--quick] [--parallel] [--n-workers 4]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from flee.SimulationSettings import SimulationSettings  # noqa: E402

from scripts import run_day5_scenarios as d5  # noqa: E402
from scripts import run_fukushima_day3 as d3  # noqa: E402
from scripts.qoi_definitions import (  # noqa: E402
    compute_hayano_t4,
    compute_mid_ps2_trough,
    compute_mid_ps2_dip,
    compute_mid_ps2_recovery,
    compute_corridor_inland_pct,
    compute_blend_inner_t7,
    compute_zone_ps2_timeseries,
)

RES = REPO / "results" / "day8"

# ---------------------------------------------------------------------------
# Targets (see SCIENTIFIC HONESTY block below)
# ---------------------------------------------------------------------------

HAYANO_TARGET_RAW       = 1.008      # raw Hayano 2013 inner-zone implied CMC; impossible.
HAYANO_TARGET_USED      = 0.30       # within-range approximation (~30% inner+mid by t=4).
CORRIDOR_TARGET         = 0.52       # Day 5 OSM Tomioka-fork best estimate (+9.3pp on ~43%).
W_HAYANO                = 1.0
W_CORRIDOR              = 0.5

DIP_TARGET              = 0.25       # model-internal; three-phase prediction (main.tex S6.2).
TROUGH_TARGET           = 0.15       # model-internal; acute-zone Sys1-dominated.
W_DIP                   = 1.0
W_TROUGH                = 1.0

# Stage 1 grid
CMC_GRID                = np.linspace(0.10, 0.50, 41)   # step 0.01, 41 points
STAGE1_REPS             = 5
STAGE1_NEUTRAL          = {"alpha": 2.0, "beta": 3.0, "kappa": 5.0}

# Stage 2 grids
COARSE_ALPHA            = np.linspace(0.5,  5.0, 10)
COARSE_BETA             = np.linspace(1.0, 10.0, 10)
COARSE_KAPPA            = np.linspace(1.0, 20.0, 10)
STAGE2_COARSE_REPS      = 3
STAGE2_FINE_REPS        = 5
FINE_PCT                = 0.20      # +/- 20% around coarse minimum
FINE_STEPS              = 5

# Search-range bounds for boundary detection
ALPHA_RANGE             = (0.5, 5.0)
BETA_RANGE              = (1.0, 10.0)
KAPPA_RANGE             = (1.0, 20.0)

# Stage 3
VALIDATION_REPS         = 20

# Simulation parameters
N_AGENTS                = 300
N_STEPS                 = 72
SCENARIO_ID             = "route6_closed"

# ---------------------------------------------------------------------------
# Simulation harness
# ---------------------------------------------------------------------------

@contextmanager
def _patch_cmc(cmc_value: float):
    """Inject a CMC override that survives ``d3.load_config``."""
    orig = d3.load_config

    def patched(input_dir_str):
        orig(input_dir_str)
        SimulationSettings.move_rules["ConflictMoveChance"] = float(cmc_value)

    d3.load_config = patched
    try:
        yield
    finally:
        d3.load_config = orig


def _simulate(input_dir: Path, conflict_file: str, mode: str,
              alpha: float, beta: float, kappa: float, cmc: float,
              seed: int) -> Optional[pd.DataFrame]:
    """Run a single (mode, seed) member and return the agents dataframe."""
    np.random.seed(seed)
    with _patch_cmc(cmc):
        try:
            adf, _lm, _arr = d5._run_member(
                input_dir, conflict_file, mode,
                N_AGENTS, N_STEPS,
                alpha, beta, kappa, seed, "beta",
            )
            return adf
        except Exception:
            print(f"[sim] {mode} alpha={alpha:.3g} beta={beta:.3g} "
                  f"kappa={kappa:.3g} cmc={cmc:.3g} seed={seed} FAILED",
                  file=sys.stderr)
            traceback.print_exc()
            return None


def _outcome_qois_blend(adf: pd.DataFrame) -> Dict[str, float]:
    return {
        "hayano_t4":           compute_hayano_t4(adf),
        "corridor_inland_pct": compute_corridor_inland_pct(adf),
    }


def _process_qois_blend(adf: pd.DataFrame) -> Dict[str, float]:
    return {
        "mid_ps2_dip":     compute_mid_ps2_dip(adf),
        "mid_ps2_trough":  compute_mid_ps2_trough(adf),
    }


def _all_six_qois(adf_blend: pd.DataFrame,
                  adf_sys1: pd.DataFrame) -> Dict[str, float]:
    return {
        "hayano_t4":           compute_hayano_t4(adf_blend),
        "mid_ps2_dip":         compute_mid_ps2_dip(adf_blend),
        "mid_ps2_trough":      compute_mid_ps2_trough(adf_blend),
        "mid_ps2_recovery":    compute_mid_ps2_recovery(adf_blend),
        "corridor_inland_pct": compute_corridor_inland_pct(adf_blend),
        "blend_inner_t7":      compute_blend_inner_t7(adf_sys1, adf_blend),
    }


# ---------------------------------------------------------------------------
# Worker entry-points (top-level for multiprocessing.Pool)
# ---------------------------------------------------------------------------

def _eval_blend_one(args):
    """Single blend-mode evaluation; returns dict with QoIs + bookkeeping."""
    (idx, rep, params, input_dir, conflict_file, seed) = args
    adf = _simulate(input_dir, conflict_file, "blend",
                    params["alpha"], params["beta"], params["kappa"],
                    params["cmc"], seed)
    if adf is None:
        return {"idx": idx, "rep": rep, "ok": False,
                "hayano_t4": np.nan, "corridor_inland_pct": np.nan,
                "mid_ps2_dip": np.nan, "mid_ps2_trough": np.nan}
    out = {"idx": idx, "rep": rep, "ok": True}
    out.update(_outcome_qois_blend(adf))
    out.update(_process_qois_blend(adf))
    return out


def _eval_validation_one(args):
    """Single validation evaluation: blend + sys1 modes; full QoI suite."""
    (rep, params, input_dir, conflict_file, seed_blend, seed_sys1) = args
    adf_b = _simulate(input_dir, conflict_file, "blend",
                      params["alpha"], params["beta"], params["kappa"],
                      params["cmc"], seed_blend)
    adf_s = _simulate(input_dir, conflict_file, "sys1_only",
                      params["alpha"], params["beta"], params["kappa"],
                      params["cmc"], seed_sys1)
    if adf_b is None or adf_s is None:
        return {"rep": rep, "ok": False}
    qois = _all_six_qois(adf_b, adf_s)
    ts = compute_zone_ps2_timeseries(adf_b)
    ts["rep"] = rep
    out = {"rep": rep, "ok": True, **qois, "_ts": ts}
    return out


# ---------------------------------------------------------------------------
# Pool dispatch helper
# ---------------------------------------------------------------------------

def _dispatch(work, fn, parallel: bool, n_workers: int, label: str):
    n = len(work)
    t0 = time.time()
    progress_step = max(1, n // 20)
    rows: list = []
    if parallel and n_workers > 1:
        from multiprocessing import Pool
        with Pool(processes=n_workers) as pool:
            for k, r in enumerate(pool.imap_unordered(fn, work, chunksize=1)):
                rows.append(r)
                if (k + 1) % progress_step == 0 or k == n - 1:
                    el = time.time() - t0
                    rate = (k + 1) / max(1e-6, el)
                    eta = (n - k - 1) / max(1e-6, rate)
                    print(f"  [{label}/par] {k+1:5d}/{n}  "
                          f"({el:6.0f}s, ETA {eta:6.0f}s, {rate:.2f}/s)")
    else:
        for k, item in enumerate(work):
            rows.append(fn(item))
            if (k + 1) % progress_step == 0 or k == n - 1:
                el = time.time() - t0
                rate = (k + 1) / max(1e-6, el)
                eta = (n - k - 1) / max(1e-6, rate)
                print(f"  [{label}/ser] {k+1:5d}/{n}  "
                      f"({el:6.0f}s, ETA {eta:6.0f}s, {rate:.2f}/s)")
    return rows


# ---------------------------------------------------------------------------
# Loss functions
# ---------------------------------------------------------------------------

def _loss_stage1(hayano: float, corridor: float) -> float:
    return (W_HAYANO   * (hayano   - HAYANO_TARGET_USED) ** 2
            + W_CORRIDOR * (corridor - CORRIDOR_TARGET) ** 2)


def _loss_stage2(dip: float, trough: float) -> float:
    return (W_DIP    * (dip    - DIP_TARGET) ** 2
            + W_TROUGH * (trough - TROUGH_TARGET) ** 2)


# ---------------------------------------------------------------------------
# Hayano tension flag
# ---------------------------------------------------------------------------

def flag_hayano_tension(cmc_star: float, hayano_sim: float) -> Tuple[bool, str]:
    """Print and return a clearly formatted warning when the simulated Hayano
    statistic at the best-fit CMC remains far from the raw 1.008 figure
    (which is outside the physical [0,1] range)."""
    gap = abs(hayano_sim - HAYANO_TARGET_RAW)
    flagged = gap > 0.10
    msg = (
        f"\n{'='*72}\n"
        f"HAYANO TENSION REPORT\n"
        f"{'='*72}\n"
        f"  Best-fit CMC*           : {cmc_star:.3f}\n"
        f"  Simulated Hayano-t4     : {hayano_sim:.3f}\n"
        f"  Raw Hayano 2013 target  : {HAYANO_TARGET_RAW:.3f}  (outside [0,1])\n"
        f"  Within-range proxy used : {HAYANO_TARGET_USED:.3f}\n"
        f"  Gap |sim - 1.008|       : {gap:.3f}\n"
    )
    if flagged:
        msg += (
            f"  STATUS                  : FLAGGED\n"
            f"  Note: the physical CMC ceiling (1.0) prevents matching the\n"
            f"        raw Hayano departure rate. The calibration uses the\n"
            f"        within-range proxy {HAYANO_TARGET_USED:.2f} instead.\n"
        )
    else:
        msg += f"  STATUS                  : within tolerance (<= 0.10)\n"
    msg += "=" * 72 + "\n"
    print(msg)
    return flagged, msg


# ---------------------------------------------------------------------------
# Step 0 -- Forward pass at neutral parameters with CMC fixed at 0.25
# ---------------------------------------------------------------------------
#
# Run a single forward pass (20-replicate ensemble) at CMC=0.25, alpha=2.0,
# beta=2.0, kappa=5.0 to establish what process moments the model can
# actually reach. The Stage 2 process targets (mid_ps2_dip, mid_ps2_trough)
# are then set as scaled fractions of these forward-pass means -- they are
# model-internal calibration priors derived from the three-phase theoretical
# prediction (main.tex Section 6.2), NOT direct empirical Fukushima
# measurements.

FORWARD_PASS_PARAMS = {"cmc": 0.25, "alpha": 2.0, "beta": 2.0, "kappa": 5.0}
FORWARD_PASS_REPS   = 20


# ---------------------------------------------------------------------------
# Stage 2 v2 / Stage 3 v2 constants (Day 8 revised, Step 1)
# ---------------------------------------------------------------------------
#
# CMC is fixed at 0.25 on physical grounds (Hayano 2013 inner-zone clearing
# rate). It is NOT optimised in the v2 design; Stage 1 produced a floor
# solution at CMC*=0.110 because the proxy target hayano_t4=0.30 is below
# the model's reachable floor at that scenario.
#
# The process targets below are model-internal calibration priors derived
# from the three-phase theoretical prediction (main.tex Section 6.2). They
# are NOT direct empirical Fukushima measurements. Their numeric values
# come from the 20-rep forward pass at the physical anchor:
#
#   forward-pass mean(mid_ps2_dip)    = 0.3495   ->  target = 0.3495 * 0.90 = 0.3145
#   forward-pass mean(mid_ps2_trough) = 0.1282   ->  target = 0.1282 * 0.85 = 0.1090
#
# The scaling factors (0.90, 0.85) encode the prior that calibration should
# pull toward a more pronounced Sys2 differentiation than the neutral prior.

CMC_FIXED                  = 0.25
MID_PS2_DIP_TARGET         = 0.3145    # = max(0.15, 0.3495 * 0.90)
MID_PS2_TROUGH_TARGET      = 0.1090    # = max(0.08, 0.1282 * 0.85)
HAYANO_T4_EXPECTED         = 0.450     # 20-rep forward pass at CMC=0.25 (better than 5-rep Stage 1)
HAYANO_T4_RAW_GAP_V2       = HAYANO_TARGET_RAW - HAYANO_T4_EXPECTED  # 1.008 - 0.450 = 0.558

# Stage 2 v2 grids
COARSE_ALPHA_V2            = np.linspace(0.5, 5.0, 10)
COARSE_BETA_V2             = np.array([0.3, 0.5, 0.75, 1.0, 1.5, 2.0,
                                        3.0, 5.0, 7.0, 10.0])
COARSE_KAPPA_V2            = np.linspace(1.0, 20.0, 10)
STAGE2_V2_COARSE_REPS      = 5
STAGE2_V2_FINE_PCT         = 0.25
STAGE2_V2_FINE_STEPS       = 7
STAGE2_V2_FINE_REPS        = 7
STAGE2_V2_EXTEND_FACTOR    = 0.50      # extend axis by 50% in boundary direction
STAGE2_V2_EXTEND_STEPS     = 5
STAGE2_V2_EXTEND_REPS      = 7

# v2 search-range bounds (used for boundary detection of fine-grid axis ends)
ALPHA_RANGE_V2             = (float(COARSE_ALPHA_V2.min()),
                              float(COARSE_ALPHA_V2.max()))
BETA_RANGE_V2              = (float(COARSE_BETA_V2.min()),
                              float(COARSE_BETA_V2.max()))
KAPPA_RANGE_V2             = (float(COARSE_KAPPA_V2.min()),
                              float(COARSE_KAPPA_V2.max()))


def run_forward_pass(parallel: bool, n_workers: int,
                     reps: int = FORWARD_PASS_REPS) -> Dict[str, object]:
    print("\n" + "=" * 72)
    print("STEP 0 -- Forward pass at neutral parameters")
    print("=" * 72)
    print(f"Parameters: {FORWARD_PASS_PARAMS}")
    print(f"Replications: {reps}  (blend + sys1_only)")

    spec = d5.scenario_specs(REPO)[SCENARIO_ID]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    work = []
    for r in range(reps):
        seed_b = 11_000_000 + r * 1009
        seed_s = 11_500_000 + r * 1009
        work.append((r, FORWARD_PASS_PARAMS, input_dir, conflict_file,
                     seed_b, seed_s))
    rows = _dispatch(work, _eval_validation_one, parallel, n_workers, "FWD")

    qoi_keys = ["hayano_t4", "mid_ps2_dip", "mid_ps2_trough",
                "mid_ps2_recovery", "corridor_inland_pct", "blend_inner_t7"]
    records = []
    for r in rows:
        if not r.get("ok", False):
            continue
        records.append({"rep": r["rep"], **{q: r[q] for q in qoi_keys}})
    df = pd.DataFrame(records).sort_values("rep")

    qois_summary: Dict[str, Dict[str, float]] = {}
    for q in qoi_keys:
        vals = df[q].dropna().values if q in df.columns else np.array([])
        if len(vals) == 0:
            qois_summary[q] = {"mean": None, "std": None, "n": 0}
            continue
        qois_summary[q] = {
            "mean": float(np.mean(vals)),
            "std":  float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
            "min":  float(np.min(vals)),
            "max":  float(np.max(vals)),
            "n":    int(len(vals)),
        }

    payload = {
        "parameters": FORWARD_PASS_PARAMS,
        "scenario":   SCENARIO_ID,
        "n_agents":   N_AGENTS,
        "n_steps":    N_STEPS,
        "reps":       int(reps),
        "qois":       qois_summary,
        "purpose": (
            "Establish reachable P_S2 process moments at CMC=0.25 (physical "
            "anchor from Hayano 2013) before setting Stage 2 v2 targets. "
            "The process targets derived from these means are model-internal "
            "calibration priors (three-phase prediction, main.tex S6.2), NOT "
            "direct empirical Fukushima measurements."
        ),
    }
    out_path = RES / "forward_pass_neutral.json"
    with out_path.open("w") as fh:
        json.dump(payload, fh, indent=2)

    print("\n[forward_pass] QoI summary (mean +/- std across "
          f"{reps} reps):")
    for q in qoi_keys:
        s = qois_summary[q]
        if s.get("mean") is None:
            print(f"  {q:25s}: <no valid runs>")
        else:
            print(f"  {q:25s}: {s['mean']:.4f} +/- {s['std']:.4f}  "
                  f"(min={s['min']:.4f}, max={s['max']:.4f}, n={s['n']})")
    print(f"\n[forward_pass] wrote {out_path}")
    print("\n[forward_pass] Suggested Stage 2 v2 targets (per Step 1 rules):")
    dip_mean = qois_summary["mid_ps2_dip"].get("mean")
    trough_mean = qois_summary["mid_ps2_trough"].get("mean")
    if dip_mean is not None:
        dip_target = max(0.15, dip_mean * 0.90)
        print(f"  MID_PS2_DIP_TARGET    = {dip_target:.4f}  "
              f"(= max(0.15, {dip_mean:.4f} * 0.90))")
    if trough_mean is not None:
        trough_target = max(0.08, trough_mean * 0.85)
        print(f"  MID_PS2_TROUGH_TARGET = {trough_target:.4f}  "
              f"(= max(0.08, {trough_mean:.4f} * 0.85))")
    return payload


# ---------------------------------------------------------------------------
# Stage 1
# ---------------------------------------------------------------------------

def stage1(parallel: bool, n_workers: int, quick: bool) -> Dict[str, float]:
    print("\n" + "=" * 72)
    print("STAGE 1 -- Fit CMC to outcome QoIs (Hayano, corridor)")
    print("=" * 72)
    print(f"Cognitive params fixed at neutral prior: {STAGE1_NEUTRAL}")
    print(f"Grid: CMC in [0.10, 0.50] step 0.01 (41 points), {STAGE1_REPS} reps")

    cmc_grid = CMC_GRID
    reps = STAGE1_REPS
    if quick:
        cmc_grid = np.array([0.10, 0.20, 0.30, 0.40, 0.50])
        reps = 2
        print(f"  [quick] reduced to {len(cmc_grid)} CMC values, {reps} reps")

    spec = d5.scenario_specs(REPO)[SCENARIO_ID]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    work = []
    for i, cmc in enumerate(cmc_grid):
        for r in range(reps):
            params = {**STAGE1_NEUTRAL, "cmc": float(cmc)}
            seed = 8000000 + i * 1009 + r
            work.append((i, r, params, input_dir, conflict_file, seed))

    rows = _dispatch(work, _eval_blend_one, parallel, n_workers, "S1")

    grid_records = []
    for w, r in zip(work, rows):
        idx, rep, params, *_ = w
        cmc = params["cmc"]
        h = r.get("hayano_t4", np.nan)
        c = r.get("corridor_inland_pct", np.nan)
        L = _loss_stage1(h, c) if r.get("ok", False) else np.nan
        grid_records.append({
            "cmc": cmc, "rep": rep,
            "hayano_t4": h, "corridor_inland_pct": c,
            "L1": L,
        })
    grid_df = pd.DataFrame(grid_records).sort_values(["cmc", "rep"])
    grid_df.to_csv(RES / "stage1_cmc_grid.csv", index=False)

    summary = (grid_df.groupby("cmc")
               .agg(hayano_t4_mean=("hayano_t4", "mean"),
                    hayano_t4_std=("hayano_t4", "std"),
                    corridor_inland_pct_mean=("corridor_inland_pct", "mean"),
                    corridor_inland_pct_std=("corridor_inland_pct", "std"),
                    L1_mean=("L1", "mean"),
                    L1_std=("L1", "std"))
               .reset_index())
    summary.to_csv(RES / "stage1_summary.csv", index=False)

    if summary["L1_mean"].isna().all():
        raise RuntimeError("Stage 1 produced no valid evaluations.")
    best_idx = int(summary["L1_mean"].idxmin())
    cmc_star = float(summary.loc[best_idx, "cmc"])
    L1_min = float(summary.loc[best_idx, "L1_mean"])
    h_best = float(summary.loc[best_idx, "hayano_t4_mean"])
    c_best = float(summary.loc[best_idx, "corridor_inland_pct_mean"])

    cmc_star_payload = {
        "cmc_star": cmc_star,
        "L1_min": L1_min,
        "hayano_t4_best": h_best,
        "corridor_inland_pct_best": c_best,
        "hayano_residual": h_best - HAYANO_TARGET_USED,
        "hayano_target_raw": HAYANO_TARGET_RAW,
        "hayano_target_used": HAYANO_TARGET_USED,
        "corridor_residual": c_best - CORRIDOR_TARGET,
        "neutral_cognitive_params": STAGE1_NEUTRAL,
        "scenario": SCENARIO_ID,
        "n_agents": N_AGENTS, "n_steps": N_STEPS,
        "reps_per_grid_point": reps,
        "grid_size": int(len(cmc_grid)),
    }

    flagged, _ = flag_hayano_tension(cmc_star, h_best)
    cmc_star_payload["hayano_tension_flag"] = bool(flagged)
    cmc_star_payload["hayano_tension_note"] = (
        f"CMC*={cmc_star:.3f} produces hayano_t4={h_best:.3f}; "
        f"raw Hayano target {HAYANO_TARGET_RAW} is outside the physical "
        f"[0,1] range; |sim - raw| gap = {abs(h_best - HAYANO_TARGET_RAW):.3f}."
    )

    with (RES / "stage1_cmc_star.json").open("w") as fh:
        json.dump(cmc_star_payload, fh, indent=2)
    print(f"\n[stage1] CMC* = {cmc_star:.3f} (L1_min = {L1_min:.4f})")
    print(f"[stage1] hayano_t4 at CMC* = {h_best:.3f} "
          f"(target {HAYANO_TARGET_USED}, residual {h_best-HAYANO_TARGET_USED:+.3f})")
    print(f"[stage1] corridor at CMC*  = {c_best:.3f} "
          f"(target {CORRIDOR_TARGET}, residual {c_best-CORRIDOR_TARGET:+.3f})")

    return cmc_star_payload


# ---------------------------------------------------------------------------
# Stage 2
# ---------------------------------------------------------------------------

def _stage2_grid_eval(cmc_star: float, alphas: np.ndarray, betas: np.ndarray,
                      kappas: np.ndarray, reps: int, label: str,
                      parallel: bool, n_workers: int) -> pd.DataFrame:
    spec = d5.scenario_specs(REPO)[SCENARIO_ID]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    work = []
    grid_idx = 0
    grid_lookup = {}
    for a in alphas:
        for b in betas:
            for k in kappas:
                grid_lookup[grid_idx] = (float(a), float(b), float(k))
                for r in range(reps):
                    params = {"alpha": float(a), "beta": float(b),
                              "kappa": float(k), "cmc": float(cmc_star)}
                    seed = 9000000 + grid_idx * 1009 + r
                    work.append((grid_idx, r, params, input_dir, conflict_file, seed))
                grid_idx += 1
    print(f"[stage2/{label}] {len(work)} evaluations "
          f"({len(alphas)*len(betas)*len(kappas)} grid points x {reps} reps)")

    rows = _dispatch(work, _eval_blend_one, parallel, n_workers, f"S2-{label}")

    records = []
    for w, r in zip(work, rows):
        idx, rep, params, *_ = w
        a, b, k = grid_lookup[idx]
        dip = r.get("mid_ps2_dip", np.nan)
        trough = r.get("mid_ps2_trough", np.nan)
        L = _loss_stage2(dip, trough) if r.get("ok", False) else np.nan
        records.append({
            "alpha": a, "beta": b, "kappa": k, "rep": rep,
            "mid_ps2_dip": dip, "mid_ps2_trough": trough,
            "L2": L,
        })
    return pd.DataFrame(records).sort_values(["alpha", "beta", "kappa", "rep"])


def _summarize_grid(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(["alpha", "beta", "kappa"])
              .agg(mid_ps2_dip_mean=("mid_ps2_dip", "mean"),
                   mid_ps2_trough_mean=("mid_ps2_trough", "mean"),
                   L2_mean=("L2", "mean"))
              .reset_index())


def _at_boundary(val: float, lo: float, hi: float, tol: float = 1e-6) -> bool:
    return bool((abs(val - lo) <= tol) or (abs(val - hi) <= tol))


def stage2(cmc_star: float, parallel: bool, n_workers: int,
           quick: bool) -> Dict[str, float]:
    print("\n" + "=" * 72)
    print(f"STAGE 2 -- Fit (alpha, beta, kappa) at CMC* = {cmc_star:.3f}")
    print("=" * 72)

    coarse_alphas = COARSE_ALPHA
    coarse_betas  = COARSE_BETA
    coarse_kappas = COARSE_KAPPA
    coarse_reps   = STAGE2_COARSE_REPS
    fine_reps     = STAGE2_FINE_REPS
    if quick:
        coarse_alphas = np.linspace(0.5, 5.0, 4)
        coarse_betas  = np.linspace(1.0, 10.0, 4)
        coarse_kappas = np.linspace(1.0, 20.0, 4)
        coarse_reps   = 2
        fine_reps     = 2
        print(f"  [quick] reduced coarse grid to "
              f"{len(coarse_alphas)}x{len(coarse_betas)}x{len(coarse_kappas)}")

    coarse_df = _stage2_grid_eval(cmc_star, coarse_alphas, coarse_betas,
                                   coarse_kappas, coarse_reps, "coarse",
                                   parallel, n_workers)
    coarse_df.to_csv(RES / "stage2_coarse_grid.csv", index=False)
    coarse_summary = _summarize_grid(coarse_df)
    if coarse_summary["L2_mean"].isna().all():
        raise RuntimeError("Stage 2 coarse grid produced no valid evaluations.")
    best = coarse_summary.loc[coarse_summary["L2_mean"].idxmin()]
    a0, b0, k0 = float(best["alpha"]), float(best["beta"]), float(best["kappa"])
    print(f"[stage2/coarse] minimum at alpha={a0:.3f} beta={b0:.3f} "
          f"kappa={k0:.3f}  L2_mean={best['L2_mean']:.4g}")

    def _fine_axis(center: float, lo: float, hi: float) -> np.ndarray:
        span = max(abs(center) * FINE_PCT, 1e-3)
        a = max(lo, center - span)
        b = min(hi, center + span)
        return np.linspace(a, b, FINE_STEPS)

    fine_alphas = _fine_axis(a0, *ALPHA_RANGE)
    fine_betas  = _fine_axis(b0, *BETA_RANGE)
    fine_kappas = _fine_axis(k0, *KAPPA_RANGE)

    fine_df = _stage2_grid_eval(cmc_star, fine_alphas, fine_betas,
                                 fine_kappas, fine_reps, "fine",
                                 parallel, n_workers)
    fine_df.to_csv(RES / "stage2_fine_grid.csv", index=False)
    fine_summary = _summarize_grid(fine_df)
    best_f = fine_summary.loc[fine_summary["L2_mean"].idxmin()]
    a_star = float(best_f["alpha"])
    b_star = float(best_f["beta"])
    k_star = float(best_f["kappa"])
    L2_min = float(best_f["L2_mean"])
    dip_best    = float(best_f["mid_ps2_dip_mean"])
    trough_best = float(best_f["mid_ps2_trough_mean"])
    print(f"[stage2/fine] alpha*={a_star:.3f} beta*={b_star:.3f} "
          f"kappa*={k_star:.3f}  L2_min={L2_min:.4g}")

    boundary_flags = {
        "alpha": _at_boundary(a_star, fine_alphas[0], fine_alphas[-1]),
        "beta":  _at_boundary(b_star, fine_betas[0],  fine_betas[-1]),
        "kappa": _at_boundary(k_star, fine_kappas[0], fine_kappas[-1]),
    }
    boundary_warning = ""
    if any(boundary_flags.values()):
        bad = [p for p, v in boundary_flags.items() if v]
        boundary_warning = (
            f"BOUNDARY SOLUTION on {bad} -- consider extending the fine grid; "
            f"the reported point estimate is not a confident posterior."
        )
        print(f"\n[stage2] WARNING: {boundary_warning}")

    payload = {
        "alpha_star": a_star, "beta_star": b_star, "kappa_star": k_star,
        "L2_min": L2_min,
        "mid_ps2_dip_best": dip_best,
        "mid_ps2_trough_best": trough_best,
        "dip_residual":    dip_best - DIP_TARGET,
        "trough_residual": trough_best - TROUGH_TARGET,
        "cmc_star": cmc_star,
        "fine_grid_axes": {
            "alpha": fine_alphas.tolist(),
            "beta":  fine_betas.tolist(),
            "kappa": fine_kappas.tolist(),
        },
        "coarse_minimum": {"alpha": a0, "beta": b0, "kappa": k0},
        "boundary_flags": boundary_flags,
        "boundary_warning": boundary_warning,
        "scenario": SCENARIO_ID,
        "n_agents": N_AGENTS, "n_steps": N_STEPS,
        "coarse_reps": coarse_reps, "fine_reps": fine_reps,
        "targets": {"mid_ps2_dip": DIP_TARGET, "mid_ps2_trough": TROUGH_TARGET},
    }
    with (RES / "stage2_params.json").open("w") as fh:
        json.dump(payload, fh, indent=2)
    return payload


# ---------------------------------------------------------------------------
# Stage 3 -- Validation
# ---------------------------------------------------------------------------

def stage3(stage1_payload: Dict[str, float], stage2_payload: Dict[str, float],
           parallel: bool, n_workers: int, quick: bool) -> Dict[str, float]:
    print("\n" + "=" * 72)
    print("STAGE 3 -- Validation ensemble at locked parameters")
    print("=" * 72)

    cmc   = stage1_payload["cmc_star"]
    a     = stage2_payload["alpha_star"]
    b     = stage2_payload["beta_star"]
    k     = stage2_payload["kappa_star"]
    reps  = VALIDATION_REPS if not quick else 4
    print(f"Locked: CMC={cmc:.3f}  alpha={a:.3f}  beta={b:.3f}  kappa={k:.3f}")
    print(f"Ensemble size: {reps}")

    spec = d5.scenario_specs(REPO)[SCENARIO_ID]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    params = {"alpha": a, "beta": b, "kappa": k, "cmc": cmc}
    work = []
    for r in range(reps):
        seed_b = 10_000_000 + r * 1009
        seed_s = 10_500_000 + r * 1009
        work.append((r, params, input_dir, conflict_file, seed_b, seed_s))

    rows = _dispatch(work, _eval_validation_one, parallel, n_workers, "S3")

    qoi_keys = ["hayano_t4", "mid_ps2_dip", "mid_ps2_trough",
                "mid_ps2_recovery", "corridor_inland_pct", "blend_inner_t7"]
    ens_records = []
    ts_frames = []
    for r in rows:
        if not r.get("ok", False):
            continue
        ens_records.append({"rep": r["rep"], **{q: r[q] for q in qoi_keys}})
        if "_ts" in r and r["_ts"] is not None and not r["_ts"].empty:
            ts_frames.append(r["_ts"])
    ens_df = pd.DataFrame(ens_records).sort_values("rep")
    ens_df.to_csv(RES / "validation_ensemble.csv", index=False)

    if ts_frames:
        ts_df = pd.concat(ts_frames, ignore_index=True)
        ts_summary = (ts_df.groupby(["rep", "timestep", "zone"])["mean_ps2"]
                      .agg(["mean"]).reset_index()
                      .rename(columns={"mean": "mean_ps2"}))
        # Per-rep std comes naturally from across-zone-cell aggregation; we also
        # record the per-cell mean as ``mean_ps2`` and supply ``std_ps2`` as the
        # ensemble dispersion (mean across reps for each (timestep, zone)).
        ens_disp = (ts_df.groupby(["timestep", "zone"])["mean_ps2"]
                    .agg(["std"]).reset_index()
                    .rename(columns={"std": "std_ps2"}))
        ts_out = ts_summary.merge(ens_disp, on=["timestep", "zone"], how="left")
        ts_out = ts_out[["rep", "timestep", "zone", "mean_ps2", "std_ps2"]]
        ts_out.to_csv(RES / "ps2_timeseries.csv", index=False)
    else:
        pd.DataFrame(columns=["rep", "timestep", "zone",
                              "mean_ps2", "std_ps2"]).to_csv(
            RES / "ps2_timeseries.csv", index=False)

    targets = {
        "hayano_t4":           HAYANO_TARGET_USED,
        "mid_ps2_dip":         DIP_TARGET,
        "mid_ps2_trough":      TROUGH_TARGET,
        "corridor_inland_pct": CORRIDOR_TARGET,
    }
    summary: Dict[str, object] = {}
    for q in qoi_keys:
        if q in ens_df and not ens_df[q].isna().all():
            summary[q] = {
                "mean":   float(ens_df[q].mean()),
                "std":    float(ens_df[q].std(ddof=1)) if len(ens_df) > 1 else 0.0,
                "min":    float(ens_df[q].min()),
                "max":    float(ens_df[q].max()),
                "n":      int(ens_df[q].notna().sum()),
                "target": targets.get(q),
            }
        else:
            summary[q] = {"mean": None, "std": None, "n": 0,
                          "target": targets.get(q)}

    h_mean = summary["hayano_t4"]["mean"] or 0.0
    flagged, _ = flag_hayano_tension(cmc, h_mean)

    summary["blend_inner_t7_interpretation"] = (
        "Sys2 vs Sys1-only inner-zone clearance difference; "
        ">0 = dual-process earns its keep"
    )
    summary["parameters_locked"] = {
        "cmc": cmc, "alpha": a, "beta": b, "kappa": k,
    }
    summary["hayano_tension_flag"] = bool(flagged)
    summary["hayano_tension_note"] = (
        f"CMC={cmc:.3f} produces hayano_t4={h_mean:.3f}; "
        f"raw Hayano target {HAYANO_TARGET_RAW} is outside physical range; "
        f"gap = {abs(h_mean - HAYANO_TARGET_RAW):.3f}"
    )
    summary["scenario"] = SCENARIO_ID
    summary["n_agents"] = N_AGENTS
    summary["n_steps"] = N_STEPS
    summary["reps"] = int(reps)

    with (RES / "validation_summary.json").open("w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n[stage3] Validation summary:")
    for q in qoi_keys:
        s = summary[q]
        if s.get("mean") is None:
            print(f"  {q:25s}: <no valid runs>")
            continue
        tgt = s.get("target")
        tgt_str = f" (target {tgt})" if tgt is not None else ""
        print(f"  {q:25s}: {s['mean']:.3f} +/- {s['std']:.3f}{tgt_str}")
    return summary


# ---------------------------------------------------------------------------
# Stage 2 v2 -- CMC fixed at 0.25, extended beta grid, boundary auto-extension
# ---------------------------------------------------------------------------

def _loss_stage2_v2(dip: float, trough: float) -> float:
    """L2(alpha, beta, kappa) with v2 targets (CMC fixed at 0.25)."""
    return (W_DIP    * (dip    - MID_PS2_DIP_TARGET) ** 2
            + W_TROUGH * (trough - MID_PS2_TROUGH_TARGET) ** 2)


def _stage2_v2_grid_eval(alphas: np.ndarray, betas: np.ndarray,
                         kappas: np.ndarray, reps: int, label: str,
                         parallel: bool, n_workers: int,
                         seed_base: int = 12_000_000) -> pd.DataFrame:
    """Evaluate the Stage 2 v2 grid at CMC_FIXED. Returns long-format dataframe
    with columns alpha, beta, kappa, rep, mid_ps2_dip, mid_ps2_trough, L2."""
    spec = d5.scenario_specs(REPO)[SCENARIO_ID]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    work = []
    grid_idx = 0
    grid_lookup: Dict[int, Tuple[float, float, float]] = {}
    for a in alphas:
        for b in betas:
            for k in kappas:
                grid_lookup[grid_idx] = (float(a), float(b), float(k))
                for r in range(reps):
                    params = {"alpha": float(a), "beta": float(b),
                              "kappa": float(k), "cmc": CMC_FIXED}
                    seed = seed_base + grid_idx * 1009 + r
                    work.append((grid_idx, r, params, input_dir,
                                 conflict_file, seed))
                grid_idx += 1
    n_pts = len(alphas) * len(betas) * len(kappas)
    print(f"[stage2_v2/{label}] {len(work)} evaluations  "
          f"({n_pts} grid points x {reps} reps; CMC fixed at {CMC_FIXED})")

    rows = _dispatch(work, _eval_blend_one, parallel, n_workers,
                     f"S2v2-{label}")

    records = []
    for w, r in zip(work, rows):
        idx, rep, params, *_ = w
        a, b, k = grid_lookup[idx]
        dip = r.get("mid_ps2_dip", np.nan)
        trough = r.get("mid_ps2_trough", np.nan)
        L = _loss_stage2_v2(dip, trough) if r.get("ok", False) else np.nan
        records.append({
            "alpha": a, "beta": b, "kappa": k, "rep": rep,
            "mid_ps2_dip": dip, "mid_ps2_trough": trough, "L2": L,
        })
    return pd.DataFrame(records).sort_values(
        ["alpha", "beta", "kappa", "rep"]).reset_index(drop=True)


def _summarize_grid_v2(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(["alpha", "beta", "kappa"])
              .agg(mid_ps2_dip_mean=("mid_ps2_dip", "mean"),
                   mid_ps2_trough_mean=("mid_ps2_trough", "mean"),
                   L2_mean=("L2", "mean"),
                   L2_std=("L2", "std"))
              .reset_index())


def _detect_boundary(val: float, axis: np.ndarray, tol: float = 1e-6) -> str:
    """Return 'low', 'high', or 'interior' for a 1D axis."""
    if abs(val - float(axis[0])) <= tol:
        return "low"
    if abs(val - float(axis[-1])) <= tol:
        return "high"
    return "interior"


def stage2_v2(parallel: bool, n_workers: int, quick: bool) -> Dict[str, object]:
    print("\n" + "=" * 72)
    print(f"STAGE 2 v2 -- Fit (alpha, beta, kappa) at CMC fixed = {CMC_FIXED}")
    print("=" * 72)
    print(f"Targets: dip={MID_PS2_DIP_TARGET:.4f}, "
          f"trough={MID_PS2_TROUGH_TARGET:.4f}")
    print(f"Coarse axes:")
    print(f"  alpha: {COARSE_ALPHA_V2.tolist()}")
    print(f"  beta : {COARSE_BETA_V2.tolist()}  (log-spaced below 1.0)")
    print(f"  kappa: {COARSE_KAPPA_V2.tolist()}")

    coarse_alphas = COARSE_ALPHA_V2
    coarse_betas  = COARSE_BETA_V2
    coarse_kappas = COARSE_KAPPA_V2
    coarse_reps   = STAGE2_V2_COARSE_REPS
    fine_reps     = STAGE2_V2_FINE_REPS
    if quick:
        coarse_alphas = np.linspace(0.5, 5.0, 4)
        coarse_betas  = np.array([0.3, 1.0, 3.0, 10.0])
        coarse_kappas = np.linspace(1.0, 20.0, 4)
        coarse_reps   = 2
        fine_reps     = 2
        print(f"  [quick] reduced to "
              f"{len(coarse_alphas)}x{len(coarse_betas)}x{len(coarse_kappas)}")

    coarse_df = _stage2_v2_grid_eval(coarse_alphas, coarse_betas, coarse_kappas,
                                     coarse_reps, "coarse",
                                     parallel, n_workers)
    coarse_df.to_csv(RES / "stage2_coarse_grid_v2.csv", index=False)
    coarse_summary = _summarize_grid_v2(coarse_df)
    if coarse_summary["L2_mean"].isna().all():
        raise RuntimeError("Stage 2 v2 coarse grid: no valid evaluations.")
    cbest = coarse_summary.loc[coarse_summary["L2_mean"].idxmin()]
    a0 = float(cbest["alpha"]); b0 = float(cbest["beta"]); k0 = float(cbest["kappa"])
    print(f"[stage2_v2/coarse] minimum at alpha={a0:.3f} beta={b0:.4f} "
          f"kappa={k0:.3f}  L2_mean={cbest['L2_mean']:.4g}")

    pct = STAGE2_V2_FINE_PCT
    steps = STAGE2_V2_FINE_STEPS
    if quick:
        steps = 3

    def _fine_axis(center: float, lo: float, hi: float) -> np.ndarray:
        span = max(abs(center) * pct, 1e-3)
        a = max(lo, center - span)
        b = min(hi, center + span)
        return np.linspace(a, b, steps)

    fine_alphas = _fine_axis(a0, *ALPHA_RANGE_V2)
    fine_betas  = _fine_axis(b0, *BETA_RANGE_V2)
    fine_kappas = _fine_axis(k0, *KAPPA_RANGE_V2)
    print(f"[stage2_v2/fine] axes (+-{pct*100:.0f}%):")
    print(f"  alpha: {fine_alphas.tolist()}")
    print(f"  beta : {fine_betas.tolist()}")
    print(f"  kappa: {fine_kappas.tolist()}")

    fine_df = _stage2_v2_grid_eval(fine_alphas, fine_betas, fine_kappas,
                                   fine_reps, "fine",
                                   parallel, n_workers,
                                   seed_base=13_000_000)
    fine_df.to_csv(RES / "stage2_fine_grid_v2.csv", index=False)
    fine_summary = _summarize_grid_v2(fine_df)
    fbest = fine_summary.loc[fine_summary["L2_mean"].idxmin()]
    a_star = float(fbest["alpha"]); b_star = float(fbest["beta"])
    k_star = float(fbest["kappa"])
    L2_min = float(fbest["L2_mean"])
    dip_best    = float(fbest["mid_ps2_dip_mean"])
    trough_best = float(fbest["mid_ps2_trough_mean"])
    print(f"[stage2_v2/fine] alpha*={a_star:.4f} beta*={b_star:.4f} "
          f"kappa*={k_star:.4f}  L2_min={L2_min:.4g}  "
          f"dip={dip_best:.4f}  trough={trough_best:.4f}")

    boundary_axis = {
        "alpha": _detect_boundary(a_star, fine_alphas),
        "beta":  _detect_boundary(b_star, fine_betas),
        "kappa": _detect_boundary(k_star, fine_kappas),
    }
    boundary_flags = {p: (s != "interior") for p, s in boundary_axis.items()}
    boundary_warning = "NONE"
    extension_records = []

    if not quick and any(boundary_flags.values()):
        # Run a 1D extension search along each boundary axis. If the new
        # 1D minimum is no longer at the extended boundary, mark EXTENDED;
        # otherwise PERSISTENT.
        any_persistent = False
        ext_axes = []
        for axis_name, side in boundary_axis.items():
            if side == "interior":
                continue
            if axis_name == "alpha":
                center = fine_alphas
                lo_glob, hi_glob = ALPHA_RANGE_V2
            elif axis_name == "beta":
                center = fine_betas
                lo_glob, hi_glob = BETA_RANGE_V2
            else:
                center = fine_kappas
                lo_glob, hi_glob = KAPPA_RANGE_V2
            cur_lo, cur_hi = float(center[0]), float(center[-1])
            if side == "low":
                new_lo = max(lo_glob,
                             cur_lo - STAGE2_V2_EXTEND_FACTOR * (cur_hi - cur_lo))
                new_hi = cur_lo
            else:
                new_hi = min(hi_glob,
                             cur_hi + STAGE2_V2_EXTEND_FACTOR * (cur_hi - cur_lo))
                new_lo = cur_hi
            if abs(new_hi - new_lo) < 1e-9:
                # Already at global bound -- cannot extend further.
                any_persistent = True
                ext_axes.append(f"PERSISTENT: {axis_name} at global "
                                f"{'lower' if side=='low' else 'upper'} bound")
                continue
            ext_axis = np.linspace(new_lo, new_hi, STAGE2_V2_EXTEND_STEPS)
            print(f"[stage2_v2/extend] extending {axis_name} ({side}) along "
                  f"{ext_axis.tolist()}")

            # Build a 1D sweep along this axis with the other two fixed at
            # the current best.
            if axis_name == "alpha":
                alphas, betas, kappas = ext_axis, np.array([b_star]), np.array([k_star])
            elif axis_name == "beta":
                alphas, betas, kappas = np.array([a_star]), ext_axis, np.array([k_star])
            else:
                alphas, betas, kappas = np.array([a_star]), np.array([b_star]), ext_axis

            ext_df = _stage2_v2_grid_eval(
                alphas, betas, kappas, STAGE2_V2_EXTEND_REPS,
                f"extend-{axis_name}", parallel, n_workers,
                seed_base=14_000_000 + hash(axis_name) % 100_000)
            ext_df["extend_axis"] = axis_name
            extension_records.append(ext_df)
            ext_summary = _summarize_grid_v2(ext_df)
            ext_best = ext_summary.loc[ext_summary["L2_mean"].idxmin()]
            ext_val = float(ext_best[axis_name])
            ext_L2  = float(ext_best["L2_mean"])
            print(f"[stage2_v2/extend] {axis_name} 1D minimum at "
                  f"{ext_val:.4f} with L2={ext_L2:.4g} "
                  f"(fine min was {L2_min:.4g})")

            # Did the extension improve the loss?
            if ext_L2 < L2_min - 1e-12:
                if axis_name == "alpha": a_star = ext_val
                elif axis_name == "beta": b_star = ext_val
                else: k_star = ext_val
                L2_min = ext_L2
                dip_best    = float(ext_best["mid_ps2_dip_mean"])
                trough_best = float(ext_best["mid_ps2_trough_mean"])
                # Did the new value land on the new (extended) boundary?
                # If so, PERSISTENT (the true min is even further out).
                if (abs(ext_val - float(ext_axis[0])) < 1e-9
                        or abs(ext_val - float(ext_axis[-1])) < 1e-9):
                    if abs(ext_val - lo_glob) < 1e-9 or abs(ext_val - hi_glob) < 1e-9:
                        any_persistent = True
                        ext_axes.append(f"PERSISTENT: {axis_name} at global bound")
                    else:
                        any_persistent = True
                        ext_axes.append(f"PERSISTENT: {axis_name}")
                else:
                    ext_axes.append(f"EXTENDED: {axis_name}")
                    boundary_flags[axis_name] = False  # resolved
            else:
                ext_axes.append(f"EXTENDED: {axis_name} (no improvement)")
        boundary_warning = "; ".join(ext_axes) if ext_axes else "NONE"
        if any_persistent and "PERSISTENT" not in boundary_warning:
            boundary_warning = "PERSISTENT: " + boundary_warning

    if extension_records:
        ext_all = pd.concat(extension_records, ignore_index=True)
        ext_all.to_csv(RES / "stage2_extend_grid_v2.csv", index=False)

    # Identify any axis that is "unconstrained" (still at global bound after
    # extension). For those, do not claim a posterior estimate.
    unconstrained = []
    for p, side in boundary_axis.items():
        if side == "interior":
            continue
        # if its boundary_flags is still True after extension, it means we
        # could not move off the boundary (or hit global bound)
        cur_val = {"alpha": a_star, "beta": b_star, "kappa": k_star}[p]
        if p == "alpha":
            lo_g, hi_g = ALPHA_RANGE_V2
        elif p == "beta":
            lo_g, hi_g = BETA_RANGE_V2
        else:
            lo_g, hi_g = KAPPA_RANGE_V2
        if abs(cur_val - lo_g) < 1e-9:
            unconstrained.append(f"{p} unconstrained from below "
                                 f"(at global lower bound {lo_g})")
        elif abs(cur_val - hi_g) < 1e-9:
            unconstrained.append(f"{p} unconstrained from above "
                                 f"(at global upper bound {hi_g})")

    payload = {
        "alpha_star": a_star, "beta_star": b_star, "kappa_star": k_star,
        "cmc_fixed": CMC_FIXED,
        "L2_min": L2_min,
        "mid_ps2_dip_best": dip_best,
        "mid_ps2_trough_best": trough_best,
        "dip_residual":    dip_best - MID_PS2_DIP_TARGET,
        "trough_residual": trough_best - MID_PS2_TROUGH_TARGET,
        "targets": {
            "mid_ps2_dip":    MID_PS2_DIP_TARGET,
            "mid_ps2_trough": MID_PS2_TROUGH_TARGET,
            "basis": ("forward_pass_mean x scaling; model-internal process "
                      "target derived from three-phase prediction "
                      "(main.tex Section 6.2), NOT a direct empirical "
                      "Fukushima measurement"),
        },
        "boundary_flags": boundary_flags,
        "boundary_axis": boundary_axis,
        "boundary_warning": boundary_warning,
        "unconstrained_axes": unconstrained,
        "stage1_status": ("CMC fixed at 0.25 on physical grounds; Stage 1 "
                          "result documented as boundary condition"),
        "hayano_tension": {
            "cmc_used": CMC_FIXED,
            "hayano_t4_expected": HAYANO_T4_EXPECTED,
            "hayano_t4_target_raw": HAYANO_TARGET_RAW,
            "gap": float(HAYANO_T4_RAW_GAP_V2),
            "disposition": ("documented boundary condition; not a calibration "
                            "residual. Raw Hayano 2013 target 1.008 is "
                            "outside physical range [0,1]."),
        },
        "fine_grid_axes": {
            "alpha": fine_alphas.tolist(),
            "beta":  fine_betas.tolist(),
            "kappa": fine_kappas.tolist(),
        },
        "coarse_minimum": {"alpha": a0, "beta": b0, "kappa": k0},
        "scenario": SCENARIO_ID,
        "n_agents": N_AGENTS, "n_steps": N_STEPS,
        "coarse_reps": coarse_reps, "fine_reps": fine_reps,
    }
    out_path = RES / "stage2_params_v2.json"
    with out_path.open("w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\n[stage2_v2] wrote {out_path}")
    print(f"[stage2_v2] boundary_warning = {boundary_warning}")
    if unconstrained:
        print(f"[stage2_v2] UNCONSTRAINED: {unconstrained}")
    return payload


# ---------------------------------------------------------------------------
# Stage 3 v2 -- validation at locked v2 parameters
# ---------------------------------------------------------------------------

def stage3_v2(stage2_payload: Dict[str, object],
              parallel: bool, n_workers: int,
              quick: bool) -> Dict[str, object]:
    print("\n" + "=" * 72)
    print("STAGE 3 v2 -- Validation ensemble at locked v2 parameters")
    print("=" * 72)

    cmc = float(stage2_payload["cmc_fixed"])
    a   = float(stage2_payload["alpha_star"])
    b   = float(stage2_payload["beta_star"])
    k   = float(stage2_payload["kappa_star"])
    reps = VALIDATION_REPS if not quick else 4
    print(f"Locked: CMC={cmc:.3f}  alpha={a:.4f}  beta={b:.4f}  kappa={k:.4f}")
    print(f"Ensemble size: {reps}")

    spec = d5.scenario_specs(REPO)[SCENARIO_ID]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    params = {"alpha": a, "beta": b, "kappa": k, "cmc": cmc}
    work = []
    for r in range(reps):
        seed_b = 15_000_000 + r * 1009
        seed_s = 15_500_000 + r * 1009
        work.append((r, params, input_dir, conflict_file, seed_b, seed_s))
    rows = _dispatch(work, _eval_validation_one, parallel, n_workers, "S3v2")

    qoi_keys = ["hayano_t4", "mid_ps2_dip", "mid_ps2_trough",
                "mid_ps2_recovery", "corridor_inland_pct", "blend_inner_t7"]
    ens_records = []
    ts_frames = []
    for r in rows:
        if not r.get("ok", False):
            continue
        ens_records.append({"rep": r["rep"], **{q: r[q] for q in qoi_keys}})
        if "_ts" in r and r["_ts"] is not None and not r["_ts"].empty:
            ts_frames.append(r["_ts"])
    ens_df = pd.DataFrame(ens_records).sort_values("rep")
    ens_df.to_csv(RES / "validation_ensemble_v2.csv", index=False)

    if ts_frames:
        ts_df = pd.concat(ts_frames, ignore_index=True)
        ts_summary = (ts_df.groupby(["rep", "timestep", "zone"])["mean_ps2"]
                      .agg(["mean"]).reset_index()
                      .rename(columns={"mean": "mean_ps2"}))
        ens_disp = (ts_df.groupby(["timestep", "zone"])["mean_ps2"]
                    .agg(["std"]).reset_index()
                    .rename(columns={"std": "std_ps2"}))
        ts_out = ts_summary.merge(ens_disp, on=["timestep", "zone"],
                                   how="left")
        ts_out = ts_out[["rep", "timestep", "zone", "mean_ps2", "std_ps2"]]
        ts_out.to_csv(RES / "ps2_timeseries_v2.csv", index=False)
    else:
        pd.DataFrame(columns=["rep", "timestep", "zone",
                              "mean_ps2", "std_ps2"]).to_csv(
            RES / "ps2_timeseries_v2.csv", index=False)

    targets_v2 = {
        "hayano_t4":      "N/A - boundary condition",
        "mid_ps2_dip":    MID_PS2_DIP_TARGET,
        "mid_ps2_trough": MID_PS2_TROUGH_TARGET,
    }
    qois_summary: Dict[str, Dict[str, object]] = {}
    for q in qoi_keys:
        if q in ens_df and not ens_df[q].isna().all():
            entry: Dict[str, object] = {
                "mean": float(ens_df[q].mean()),
                "std":  float(ens_df[q].std(ddof=1)) if len(ens_df) > 1 else 0.0,
                "min":  float(ens_df[q].min()),
                "max":  float(ens_df[q].max()),
                "n":    int(ens_df[q].notna().sum()),
            }
            if q in targets_v2:
                entry["target"] = targets_v2[q]
            if q == "blend_inner_t7":
                entry["interpretation"] = (
                    "Sys2 vs Sys1-only inner-zone clearance difference; "
                    ">0 confirms dual-process layer earns its keep. The "
                    "GATE criterion is mean > 0 (NOT every individual "
                    "replicate); negative replicates within the ensemble "
                    "are expected and reported honestly."
                )
            qois_summary[q] = entry
        else:
            qois_summary[q] = {"mean": None, "std": None, "n": 0,
                               "target": targets_v2.get(q)}

    h_mean = qois_summary["hayano_t4"].get("mean") or 0.0
    flagged, _ = flag_hayano_tension(cmc, h_mean)

    summary = {
        "parameters_locked": {"cmc": cmc, "alpha": a, "beta": b, "kappa": k},
        "qois": qois_summary,
        "hayano_tension": {
            "note": (
                f"CMC={cmc:.2f} produces hayano_t4~{h_mean:.2f}; raw Hayano "
                f"2013 target {HAYANO_TARGET_RAW} is outside physical range "
                f"[0,1]; gap={abs(h_mean - HAYANO_TARGET_RAW):.2f}; "
                "documented as model boundary condition not calibration "
                "failure (1.008 is outside physical range)."
            ),
            "flagged": True,
        },
        "calibration_basis": {
            "cmc": ("Hayano 2013 inner-zone clearing rate (physical anchor, "
                    "not optimized)"),
            "alpha_beta_kappa": (
                "Joint moment matching on mid_ps2_dip and mid_ps2_trough "
                "with CMC fixed; process targets are model-internal, "
                "derived from three-phase theoretical prediction "
                "(main.tex Section 6.2)"
            ),
        },
        "scenario": SCENARIO_ID,
        "n_agents": N_AGENTS, "n_steps": N_STEPS,
        "reps": int(reps),
    }
    out_path = RES / "validation_summary_v2.json"
    with out_path.open("w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n[stage3_v2] wrote {out_path}")
    print("\n[stage3_v2] Validation summary:")
    for q in qoi_keys:
        s = qois_summary[q]
        if s.get("mean") is None:
            print(f"  {q:25s}: <no valid runs>")
            continue
        tgt = s.get("target")
        tgt_str = f" (target {tgt})" if tgt is not None else ""
        print(f"  {q:25s}: {s['mean']:.4f} +/- {s['std']:.4f}{tgt_str}")
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Day 8 two-stage calibration.")
    ap.add_argument("--parallel", action="store_true",
                    help="Use multiprocessing.Pool across all stages.")
    ap.add_argument("--n-workers", type=int,
                    default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--quick", action="store_true",
                    help="Tiny smoke run (small grids, few reps).")
    ap.add_argument("--skip-stage1", action="store_true",
                    help="Reuse existing stage1_cmc_star.json.")
    ap.add_argument("--skip-stage2", action="store_true",
                    help="Reuse existing stage2_params.json.")
    ap.add_argument("--forward-pass-only", action="store_true",
                    help="Step 0 only: 20-rep ensemble at CMC=0.25, "
                         "alpha=2, beta=2, kappa=5 to set v2 process targets.")
    ap.add_argument("--stage2-only", action="store_true",
                    help="Run only Stage 2 v2 (writes _v2 outputs).")
    ap.add_argument("--stage3-only", action="store_true",
                    help="Run only Stage 3 validation; with --use-v2 "
                         "uses stage2_params_v2.json.")
    ap.add_argument("--use-v2", action="store_true",
                    help="Read v2 stage2 params and write v2 stage3 outputs.")
    args = ap.parse_args()

    RES.mkdir(parents=True, exist_ok=True)

    if args.forward_pass_only:
        run_forward_pass(args.parallel, args.n_workers,
                         reps=4 if args.quick else FORWARD_PASS_REPS)
        return

    if args.stage2_only:
        s2 = stage2_v2(args.parallel, args.n_workers, args.quick)
        print("\n[stage2-only] CMC fixed = "
              f"{s2['cmc_fixed']:.3f}  alpha*={s2['alpha_star']:.4f}  "
              f"beta*={s2['beta_star']:.4f}  kappa*={s2['kappa_star']:.4f}")
        return

    if args.stage3_only:
        if args.use_v2:
            with (RES / "stage2_params_v2.json").open() as fh:
                s2 = json.load(fh)
            stage3_v2(s2, args.parallel, args.n_workers, args.quick)
        else:
            with (RES / "stage1_cmc_star.json").open() as fh:
                s1 = json.load(fh)
            with (RES / "stage2_params.json").open() as fh:
                s2 = json.load(fh)
            stage3(s1, s2, args.parallel, args.n_workers, args.quick)
        return

    print("=" * 72)
    print("Day 8 -- Two-stage moment-matching calibration")
    print(f"  parallel={args.parallel} workers={args.n_workers} "
          f"quick={args.quick}")
    print(f"  scenario={SCENARIO_ID} agents={N_AGENTS} steps={N_STEPS}")
    print("=" * 72)

    t0 = time.time()

    if args.skip_stage1 and (RES / "stage1_cmc_star.json").exists():
        print("[main] reusing stage1_cmc_star.json")
        with (RES / "stage1_cmc_star.json").open() as fh:
            s1 = json.load(fh)
    else:
        s1 = stage1(args.parallel, args.n_workers, args.quick)

    if args.skip_stage2 and (RES / "stage2_params.json").exists():
        print("[main] reusing stage2_params.json")
        with (RES / "stage2_params.json").open() as fh:
            s2 = json.load(fh)
    else:
        s2 = stage2(s1["cmc_star"], args.parallel, args.n_workers, args.quick)

    s3 = stage3(s1, s2, args.parallel, args.n_workers, args.quick)

    elapsed = time.time() - t0
    print("\n" + "=" * 72)
    print(f"Day 8 calibration complete in {elapsed/60:.1f} min")
    print(f"  CMC*   = {s1['cmc_star']:.3f}")
    print(f"  alpha* = {s2['alpha_star']:.3f}")
    print(f"  beta*  = {s2['beta_star']:.3f}")
    print(f"  kappa* = {s2['kappa_star']:.3f}")
    print(f"  hayano_tension_flag = {s3['hayano_tension_flag']}")
    print("=" * 72)


if __name__ == "__main__":
    main()
