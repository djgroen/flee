#!/usr/bin/env python3
"""
Day 7b -- Full Sobol sensitivity re-run on the real Fukushima OSM network at
adequate sample size (n_samples=200, D=4, total 1200 evaluations).

Day 7 used n_samples=32 / 192 evaluations and produced negative S_first
values, ST > 1, and CIs that span >50% of [0,1] for several QoIs. SALib
recommends >= 1000 total evaluations for reliable indices at D=4. Day 7b
re-runs the full Sobol design and uses the cleaned ``S_first`` / ``ST``
column convention adopted by the Day 7b notation rename. The Day 7
indices are discarded and replaced by the Day 7b output for all
calibration purposes.

The script:
    * generates a Saltelli quasi-random design (n_samples=200, calc_second_order=False)
      across (alpha, beta, kappa, conflict_movechance);
    * runs each parameter vector in BOTH the ``sys1_only`` and ``blend``
      cognitive modes -- the differential between the two is needed for
      ``blend_inner_t7`` and lets us compute corridor/Hayano QoIs in either
      regime in a single sweep;
    * computes six QoIs per evaluation (averaged over an ensemble of N
      members);
    * remaps the SALib output dict immediately to the post-Day-7b
      ``S_first`` / ``ST`` convention (no ``raw['S1']`` access elsewhere);
    * computes 95% bootstrap CIs (num_resamples=1000);
    * writes per-cell tables, ``sobol_design_summary.json``, and the
      Day 7b figures D7b-1 .. D7b-5.

Usage::

    python3 scripts/run_sobol_day7b.py --n-samples 200 --ensemble 3
    python3 scripts/run_sobol_day7b.py --quick --n-samples 20    # smoke
    python3 scripts/run_sobol_day7b.py --n-samples 200 --parallel --n-workers 4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# SALib gates
from SALib.analyze import sobol as sobol_analyze  # noqa: E402
from SALib.sample import sobol as sobol_sample  # noqa: E402

from scripts import run_day5_scenarios as d5  # noqa: E402
from scripts import run_fukushima_day3 as d3  # noqa: E402
from flee.SimulationSettings import SimulationSettings  # noqa: E402

RES = REPO / "results" / "day7b"
FIG = REPO / "figures" / "fukushima" / "day7b"
DAY7_INDICES = REPO / "results" / "day7" / "sobol_indices.csv"
DAY4_INDICES = REPO / "results" / "day4" / "sobol_indices.csv"

PROBLEM_4D = {
    "num_vars": 4,
    "names": ["alpha", "beta", "kappa", "cmc"],
    "bounds": [[0.5, 5.0], [1.0, 10.0], [1.0, 20.0], [0.25, 0.75]],
}

QOI_KEYS = [
    "hayano_t4",
    "mid_ps2_trough",
    "mid_ps2_dip",
    "mid_ps2_recovery",
    "corridor_inland_pct",
    "blend_inner_t7",
]

QOI_LABELS = {
    "hayano_t4":           "Hayano t=4\ndeparture",
    "mid_ps2_trough":      r"Mid $P_{S2}$" + "\ntrough",
    "mid_ps2_dip":         r"Mid $P_{S2}$" + "\ndip",
    "mid_ps2_recovery":    r"Mid $P_{S2}$" + "\nrecovery",
    "corridor_inland_pct": "Inland\ncorridor",
    "blend_inner_t7":      "Blend-Sys1\ninner t=7",
}

PARAM_COLORS = {"alpha": "#3498DB", "beta": "#E67E22",
                "kappa": "#1ABC9C", "cmc": "#9B59B6"}
PARAM_LABELS = {"alpha": r"$\alpha$", "beta": r"$\beta$",
                "kappa": r"$\kappa$", "cmc": "CMC"}

DAY4_REFERENCE = {
    "hayano_t4":        {"alpha": 0.395, "beta": 0.270, "kappa": 0.0},
    "mid_ps2_trough":   {"alpha": 0.159, "beta": 0.800, "kappa": 0.0},
    "mid_ps2_dip":      {"alpha": 0.659, "beta": 0.213, "kappa": 0.0},
    "mid_ps2_recovery": {"alpha": 0.616, "beta": 0.862, "kappa": 0.0},
    "blend_inner_t7":   {"alpha": 0.602, "beta": 0.665, "kappa": 0.0},
}

FORK_ORIGINS = {"tomioka", "okuma", "futaba", "namie", "naraha"}
INLAND_NODES = {"kawauchi"}


# ----------------------------------------------------------------------------
# QoI computation
# ----------------------------------------------------------------------------

def _inner_clearance_at_t7(adf: pd.DataFrame) -> float:
    """Fraction of agents starting in the inner zone that arrive at a camp by t=7."""
    inner_ids = adf[adf["initial_zone"] == "inner"]["agent_id"].unique()
    if len(inner_ids) == 0:
        return 0.0
    arrived = adf[(adf["agent_id"].isin(inner_ids)) & (adf["zone"] == "camp")]
    first = arrived.groupby("agent_id")["timestep"].min()
    return float((first <= 7).sum() / len(inner_ids))


def _hayano_t4(adf: pd.DataFrame) -> float:
    """Inner+mid blend departures by t=4 (matches the synoptic Hayano statistic)."""
    im = adf[adf["initial_zone"].isin(["inner", "mid"])]["agent_id"].unique()
    if len(im) == 0:
        return 0.0
    arrived = adf[(adf["agent_id"].isin(im)) & (adf["zone"] == "camp")]
    first = arrived.groupby("agent_id")["timestep"].min()
    return float((first <= 4).sum() / len(im))


def _corridor_inland_pct(adf: pd.DataFrame) -> float:
    fork = adf[(adf["timestep"] == 0) & (adf["location"].isin(FORK_ORIGINS))]
    fork_ids = set(fork["agent_id"].unique())
    if not fork_ids:
        return 0.0
    used = (adf[(adf["agent_id"].isin(fork_ids))
                & (adf["location"].isin(INLAND_NODES))]
            ["agent_id"].unique())
    return float(len(used) / len(fork_ids))


def _ps2_metrics(adf: pd.DataFrame) -> Tuple[float, float, float]:
    """Return (trough, dip, recovery) for the mid-zone blend P_S2 trace."""
    mid_locs = set(d3.ZONES["mid"])
    mid = adf[adf["location"].isin(mid_locs)]
    if mid.empty:
        return 0.0, 0.0, 0.0
    by_t = mid.groupby("timestep")["sys2_weight"].mean()
    if by_t.empty:
        return 0.0, 0.0, 0.0
    trough = float(by_t.min())
    p0 = float(by_t.iloc[0])
    p28 = float(by_t.loc[28]) if 28 in by_t.index else float(by_t.iloc[-1])
    dip = max(0.0, p0 - trough)
    recovery = max(0.0, p28 - trough)
    return trough, dip, recovery


def compute_blend_qois(adf: pd.DataFrame) -> Dict[str, float]:
    blend = adf[adf["decision_mode"] == "blend"]
    if blend.empty:
        return {k: 0.0 for k in QOI_KEYS} | {"_inner_t7_abs": 0.0}
    trough, dip, recovery = _ps2_metrics(blend)
    out = {
        "hayano_t4":           _hayano_t4(blend),
        "mid_ps2_trough":      trough,
        "mid_ps2_dip":         dip,
        "mid_ps2_recovery":    recovery,
        "corridor_inland_pct": _corridor_inland_pct(blend),
        # placeholder: the final ``blend_inner_t7`` is computed at the
        # caller as (blend_inner_t7_abs - sys1_inner_t7_abs) so that the
        # QoI captures the behavioural differential, not the absolute
        # clearance. Both individual values are returned for diagnostics.
        "blend_inner_t7":      0.0,
        "_inner_t7_abs":       _inner_clearance_at_t7(blend),
    }
    return out


def compute_sys1_qois(adf: pd.DataFrame) -> Dict[str, float]:
    sub = adf[adf["decision_mode"] == "sys1_only"]
    if sub.empty:
        return {"hayano_t4": 0.0, "corridor_inland_pct": 0.0, "_inner_t7_abs": 0.0}
    return {
        "hayano_t4":           _hayano_t4(sub),
        "corridor_inland_pct": _corridor_inland_pct(sub),
        "_inner_t7_abs":       _inner_clearance_at_t7(sub),
    }


# ----------------------------------------------------------------------------
# Per-evaluation simulation driver
# ----------------------------------------------------------------------------

@contextmanager
def _patch_cmc(cmc_value: float):
    """Inject a CMC override into d3.load_config for the duration of a run."""
    orig = d3.load_config

    def patched(input_dir_str):
        orig(input_dir_str)
        SimulationSettings.move_rules["ConflictMoveChance"] = float(cmc_value)

    d3.load_config = patched
    try:
        yield
    finally:
        d3.load_config = orig


def run_one_eval(
    input_dir: Path,
    conflict_file: str,
    alpha: float,
    beta: float,
    kappa: float,
    cmc: float,
    n_agents: int,
    n_steps: int,
    n_members: int,
    sample_idx: int,
    modes: Iterable[str] = ("sys1_only", "blend"),
) -> Dict[str, float]:
    """Run ``n_members`` ensemble for one (alpha, beta, kappa, cmc) vector.

    The run is replayed in both ``sys1_only`` and ``blend`` cognitive modes
    so we can compute the behavioural differential ``blend_inner_t7``.
    Returns the ensemble-mean QoI dict (six canonical keys plus diagnostic
    extras prefixed with ``sys1_`` / ``blend_inner_abs_``).
    """
    blend_runs: list[Dict[str, float]] = []
    sys1_runs: list[Dict[str, float]] = []
    with _patch_cmc(cmc):
        for m in range(n_members):
            seed = sample_idx * 1009 + m  # 1009 prime, avoids alignment with N
            for mode in modes:
                np.random.seed(seed)
                try:
                    adf, _lm, _arr = d5._run_member(
                        input_dir, conflict_file, mode,
                        n_agents, n_steps,
                        alpha, beta, kappa, seed, "beta",
                    )
                except Exception:
                    print(f"[run_one_eval] sample {sample_idx} member {m} "
                          f"mode={mode} failed:", file=sys.stderr)
                    traceback.print_exc()
                    continue
                if mode == "blend":
                    blend_runs.append(compute_blend_qois(adf))
                else:
                    sys1_runs.append(compute_sys1_qois(adf))

    def _mean(rows, key, default=0.0):
        vals = [r.get(key, default) for r in rows]
        return float(np.mean(vals)) if vals else default

    blend_inner_abs = _mean(blend_runs, "_inner_t7_abs")
    sys1_inner_abs  = _mean(sys1_runs,  "_inner_t7_abs")

    out = {
        "hayano_t4":           _mean(blend_runs, "hayano_t4"),
        "mid_ps2_trough":      _mean(blend_runs, "mid_ps2_trough"),
        "mid_ps2_dip":         _mean(blend_runs, "mid_ps2_dip"),
        "mid_ps2_recovery":    _mean(blend_runs, "mid_ps2_recovery"),
        "corridor_inland_pct": _mean(blend_runs, "corridor_inland_pct"),
        "blend_inner_t7":      blend_inner_abs - sys1_inner_abs,
        # diagnostic extras (not used in Sobol analysis)
        "blend_inner_abs":     blend_inner_abs,
        "sys1_inner_abs":      sys1_inner_abs,
        "sys1_hayano_t4":      _mean(sys1_runs, "hayano_t4"),
        "sys1_inland_pct":     _mean(sys1_runs, "corridor_inland_pct"),
    }
    return out


# ----------------------------------------------------------------------------
# Sobol campaign (serial / parallel)
# ----------------------------------------------------------------------------

def _eval_chunk(args):
    """Worker entry point used by multiprocessing.Pool.imap_unordered."""
    (idx, params, input_dir, conflict_file,
     n_agents, n_steps, n_members) = args
    qois = run_one_eval(
        input_dir, conflict_file,
        params["alpha"], params["beta"], params["kappa"], params["cmc"],
        n_agents, n_steps, n_members, sample_idx=idx,
    )
    return idx, params, qois


def run_sobol_campaign(
    problem: dict,
    n_samples: int,
    n_agents: int,
    n_steps: int,
    n_members: int,
    cmc_fixed: Optional[float] = None,
    parallel: bool = False,
    n_workers: int = 1,
    seed: int = 7000000,
) -> Tuple[np.ndarray, pd.DataFrame]:
    """Generate Saltelli samples and execute every evaluation."""
    spec = d5.scenario_specs(REPO)["route6_closed"]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    X = sobol_sample.sample(problem, n_samples, calc_second_order=False, seed=seed)
    n_eval = X.shape[0]
    expected = n_samples * (problem["num_vars"] + 2)
    print(f"[sobol] D={problem['num_vars']} n_samples={n_samples} "
          f"-> {n_eval} evaluations (expected {expected})")

    work = []
    for i, x in enumerate(X):
        params = dict(zip(problem["names"], x.tolist()))
        if cmc_fixed is not None and "cmc" not in params:
            params["cmc"] = float(cmc_fixed)
        work.append((i, params, input_dir, conflict_file,
                     n_agents, n_steps, n_members))

    rows: list[dict] = []
    t0 = time.time()
    progress_step = max(1, n_eval // 20)

    if parallel and n_workers > 1:
        from multiprocessing import Pool
        with Pool(processes=n_workers) as pool:
            for k, (idx, params, qois) in enumerate(
                    pool.imap_unordered(_eval_chunk, work, chunksize=1)):
                rows.append({"run_id": idx, **params, **qois})
                if (k + 1) % progress_step == 0 or k == n_eval - 1:
                    elapsed = time.time() - t0
                    rate = (k + 1) / max(1e-6, elapsed)
                    eta = (n_eval - k - 1) / max(1e-6, rate)
                    print(f"  [par] {k+1:5d}/{n_eval}  "
                          f"({elapsed:6.0f}s elapsed, ETA {eta:6.0f}s, "
                          f"{rate:.2f} eval/s)")
    else:
        for k, item in enumerate(work):
            idx, params, qois = _eval_chunk(item)
            rows.append({"run_id": idx, **params, **qois})
            if (k + 1) % progress_step == 0 or k == n_eval - 1:
                elapsed = time.time() - t0
                rate = (k + 1) / max(1e-6, elapsed)
                eta = (n_eval - k - 1) / max(1e-6, rate)
                print(f"  [ser] {k+1:5d}/{n_eval}  "
                      f"({elapsed:6.0f}s elapsed, ETA {eta:6.0f}s, "
                      f"{rate:.2f} eval/s)")

    df = pd.DataFrame(rows).sort_values("run_id").reset_index(drop=True)
    return X, df


# ----------------------------------------------------------------------------
# SALib analysis with S_first remap
# ----------------------------------------------------------------------------

def _analyze_one(problem: dict, Y: np.ndarray,
                 n_resamples: int = 1000,
                 conf_level: float = 0.95,
                 seed: int = 0) -> Optional[dict]:
    if np.allclose(Y, Y[0]):
        return None
    raw = sobol_analyze.analyze(
        problem, Y,
        calc_second_order=False,
        num_resamples=n_resamples,
        conf_level=conf_level,
        print_to_console=False,
        seed=seed,
    )
    # Remap immediately. After this point, never touch raw['S1'] again.
    return {
        "S_first":      np.asarray(raw["S1"], dtype=float),
        "S_first_conf": np.asarray(raw["S1_conf"], dtype=float),
        "ST":           np.asarray(raw["ST"], dtype=float),
        "ST_conf":      np.asarray(raw["ST_conf"], dtype=float),
    }


def analyze_sobol(problem: dict, results: pd.DataFrame,
                  n_resamples: int = 1000,
                  conf_level: float = 0.95) -> pd.DataFrame:
    rows = []
    for qoi in QOI_KEYS:
        Y = results[qoi].values.astype(float)
        seed = int(np.frombuffer(qoi.encode(), dtype=np.uint8).sum())
        idx = _analyze_one(problem, Y, n_resamples, conf_level, seed)
        if idx is None:
            for p in problem["names"]:
                rows.append({"qoi": qoi, "parameter": p,
                             "S_first": 0.0, "S_first_conf": 0.0,
                             "S_first_CI_low": 0.0, "S_first_CI_high": 0.0,
                             "ST": 0.0, "ST_conf": 0.0,
                             "ST_CI_low": 0.0, "ST_CI_high": 0.0,
                             "CI_width": 0.0,
                             "constant_output": True,
                             "Insensitive_flag": True})
            continue
        for j, p in enumerate(problem["names"]):
            sf  = float(idx["S_first"][j])
            sfc = float(idx["S_first_conf"][j])
            st  = float(idx["ST"][j])
            stc = float(idx["ST_conf"][j])
            insens = (st < 0.05) or (st - stc <= 0.0 <= st + stc)
            rows.append({
                "qoi": qoi, "parameter": p,
                "S_first": sf,        "S_first_conf": sfc,
                "S_first_CI_low":  sf - sfc,
                "S_first_CI_high": sf + sfc,
                "ST": st,             "ST_conf": stc,
                "ST_CI_low":  st - stc,
                "ST_CI_high": st + stc,
                "CI_width": 2.0 * stc,
                "constant_output": False,
                "Insensitive_flag": bool(insens),
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Acceptance checks (Section 4 gate)
# ----------------------------------------------------------------------------

def check_index_validity(idx_df: pd.DataFrame) -> Tuple[bool, list[str]]:
    failures: list[str] = []
    for _, r in idx_df.iterrows():
        qoi = r["qoi"]; param = r["parameter"]
        sf = r["S_first"]; st = r["ST"]; ciw = r["CI_width"]
        if sf < -0.01:
            failures.append(f"FAIL: {qoi}/{param} S_first={sf:.3f} < 0")
        if st > 1.01:
            failures.append(f"FAIL: {qoi}/{param} ST={st:.3f} > 1")
        if st > 0.10 and ciw > 0.40:
            failures.append(f"WARN: {qoi}/{param} ST={st:.3f} but CI_width={ciw:.3f}")
    hard_fail = any(f.startswith("FAIL:") for f in failures)
    return (not hard_fail, failures)


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------

def _setup_mpl():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8,
        "axes.titlesize": 9, "axes.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False,
    })


def fig_d7b_1_primary(idx_df: pd.DataFrame, out_path: Path) -> None:
    """Fig D7b-1 -- primary sensitivity summary with CIs and flagging."""
    _setup_mpl()
    fig, axes = plt.subplots(2, 6, figsize=(15.5, 5.5),
                             sharey="row")
    params = PROBLEM_4D["names"]
    y = np.arange(len(params))
    for col, qoi in enumerate(QOI_KEYS):
        sub = idx_df[idx_df["qoi"] == qoi].set_index("parameter").reindex(params)
        for row, key in enumerate(("S_first", "ST")):
            ax = axes[row, col]
            xs   = sub[key].values
            errs = sub[f"{key}_conf"].values
            for i, p in enumerate(params):
                ax.errorbar(xs[i], y[i], xerr=errs[i],
                            fmt="o" if key == "S_first" else "^",
                            color=PARAM_COLORS[p], capsize=3,
                            mfc="white" if key == "S_first" else PARAM_COLORS[p],
                            ms=6 if key == "S_first" else 7)
                if key == "ST" and xs[i] > 0.10 and 2 * errs[i] > 0.30:
                    ax.text(xs[i], y[i] + 0.20, "*", color="#e1b300",
                            ha="center", va="bottom", fontsize=12,
                            fontweight="bold")
                ci_str = f"({2*errs[i]:.2f})"
                ax.text(xs[i] + max(0.02, errs[i] + 0.02), y[i],
                        ci_str, fontsize=6.5, color="#555", va="center")
            ax.axvline(0.05, ls=":", color="#999", lw=0.7)
            ax.axvline(0.0,  ls="-", color="#222", lw=0.4)
            ax.set_xlim(-0.05, 1.10)
            ax.set_yticks(y)
            ax.set_yticklabels([PARAM_LABELS[p] for p in params])
            if row == 0:
                ax.set_title(QOI_LABELS[qoi])
            if col == 0:
                lbl = ("First-order index (S_first)" if key == "S_first"
                       else "Total-order index (ST)")
                ax.set_ylabel(lbl)
    fig.suptitle("Day 7b - Sobol indices on the real Fukushima OSM network "
                 "(n_samples=200, 1200 evaluations, 95% bootstrap CIs)",
                 y=1.02, fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_d7b_2_interaction(idx_df: pd.DataFrame, out_path: Path) -> None:
    """Fig D7b-2 -- (ST - S_first) heatmap."""
    _setup_mpl()
    params = PROBLEM_4D["names"]
    M = np.zeros((len(params), len(QOI_KEYS)))
    for i, p in enumerate(params):
        for j, q in enumerate(QOI_KEYS):
            row = idx_df[(idx_df["qoi"] == q) & (idx_df["parameter"] == p)]
            if len(row):
                M[i, j] = max(0.0, float(row["ST"].iloc[0]) - float(row["S_first"].iloc[0]))
    fig, ax = plt.subplots(figsize=(8.8, 3.2))
    im = ax.imshow(M, cmap="Blues", vmin=0.0, vmax=max(0.5, M.max() + 0.05),
                   aspect="auto")
    ax.set_xticks(range(len(QOI_KEYS)))
    ax.set_xticklabels([QOI_LABELS[q].replace("\n", " ") for q in QOI_KEYS],
                       rotation=22, ha="right")
    ax.set_yticks(range(len(params)))
    ax.set_yticklabels([PARAM_LABELS[p] for p in params])
    for i in range(len(params)):
        for j in range(len(QOI_KEYS)):
            colour = "white" if M[i, j] > 0.30 else "black"
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                    color=colour, fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label(r"Interaction magnitude  $S_T - S_\mathrm{first}$")
    mean_int = float(M.mean())
    ax.set_title(f"Day 7b - Interaction magnitudes "
                 f"(mean across grid: {mean_int:.3f})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_d7b_3_kappa_scatter(results: pd.DataFrame, out_path: Path) -> None:
    """Fig D7b-3 -- conditional kappa scatter for two QoIs, coloured by beta quintile."""
    _setup_mpl()
    qois = ["mid_ps2_recovery", "corridor_inland_pct"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    cmap = plt.get_cmap("plasma")
    bins = np.quantile(results["beta"].values, np.linspace(0, 1, 6))
    bins[0] -= 1e-9; bins[-1] += 1e-9
    quint = np.digitize(results["beta"].values, bins) - 1
    quint = np.clip(quint, 0, 4)
    for ax, qoi in zip(axes, qois):
        for q in range(5):
            mask = quint == q
            if not mask.any():
                continue
            ax.scatter(results.loc[mask, "kappa"], results.loc[mask, qoi],
                       s=10, alpha=0.55,
                       color=cmap(q / 4.0),
                       label=fr"$\beta$ Q{q+1}: [{bins[q]:.1f}, {bins[q+1]:.1f}]")
        ax.set_xlabel(r"$\kappa$")
        ax.set_ylabel(qoi)
        ax.set_title(QOI_LABELS[qoi].replace("\n", " "))
    axes[0].legend(loc="best", fontsize=6.5, frameon=False)

    # Verdict text
    verdicts = []
    for qoi in qois:
        slopes = []
        for q in range(5):
            mask = quint == q
            if mask.sum() < 5:
                slopes.append(np.nan); continue
            x = results.loc[mask, "kappa"].values
            y = results.loc[mask, qoi].values
            slopes.append(float(np.polyfit(x, y, 1)[0]))
        if any(math.isnan(s) for s in slopes):
            verdicts.append(f"{qoi}: insufficient samples")
            continue
        low_slope = float(np.mean(slopes[:2]))
        hi_slope  = float(np.mean(slopes[3:]))
        if abs(low_slope) > 2 * abs(hi_slope) and abs(low_slope) > 1e-3:
            verdicts.append(f"{qoi}: kappa influence stronger at low beta (CONFIRMED)")
        elif abs(hi_slope) > 2 * abs(low_slope) and abs(hi_slope) > 1e-3:
            verdicts.append(f"{qoi}: kappa influence stronger at HIGH beta (REVERSED)")
        elif abs(low_slope) < 1e-3 and abs(hi_slope) < 1e-3:
            verdicts.append(f"{qoi}: kappa effect ABSENT in both regimes")
        else:
            verdicts.append(f"{qoi}: kappa effect present in both regimes (MIXED)")
    fig.suptitle("Day 7b - Conditional kappa scatter coloured by beta quintile\n"
                 + "  ".join(verdicts),
                 fontsize=8.5, y=1.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_d7b_4_ci_heat(idx_df: pd.DataFrame, out_path: Path) -> None:
    """Fig D7b-4 -- bootstrap CI width heatmap."""
    _setup_mpl()
    params = PROBLEM_4D["names"]
    M = np.zeros((len(params), len(QOI_KEYS)))
    for i, p in enumerate(params):
        for j, q in enumerate(QOI_KEYS):
            row = idx_df[(idx_df["qoi"] == q) & (idx_df["parameter"] == p)]
            if len(row):
                M[i, j] = float(row["CI_width"].iloc[0])

    cmap_segments = [
        (0.00, "#1B7838"),
        (0.10, "#1B7838"),
        (0.30, "#F1B400"),
        (0.50, "#A30B0B"),
        (1.00, "#4D0000"),
    ]
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "ci_w", [(p, c) for p, c in cmap_segments], N=256)

    fig, ax = plt.subplots(figsize=(8.8, 3.2))
    im = ax.imshow(M, cmap=cmap, vmin=0.0, vmax=max(0.5, M.max() + 0.05),
                   aspect="auto")
    ax.set_xticks(range(len(QOI_KEYS)))
    ax.set_xticklabels([QOI_LABELS[q].replace("\n", " ") for q in QOI_KEYS],
                       rotation=22, ha="right")
    ax.set_yticks(range(len(params)))
    ax.set_yticklabels([PARAM_LABELS[p] for p in params])
    for i in range(len(params)):
        for j in range(len(QOI_KEYS)):
            v = M[i, j]
            colour = "white" if v > 0.25 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color=colour, fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label(r"CI width  $2 \cdot S_{T,conf}$")
    n_red = int((M > 0.30).sum())
    n_yellow = int(((M > 0.10) & (M <= 0.30)).sum())
    ax.set_title(
        f"Day 7b - Bootstrap CI widths (red cells: {n_red}, "
        f"yellow cells: {n_yellow}, max={M.max():.2f})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _safe_load_day7_indices() -> pd.DataFrame:
    if not DAY7_INDICES.exists():
        return pd.DataFrame(columns=["qoi", "parameter", "ST"])
    df = pd.read_csv(DAY7_INDICES)
    return df


def fig_d7b_5_three_way(idx_df_7b: pd.DataFrame, out_path: Path) -> None:
    _setup_mpl()
    qois = ["hayano_t4", "mid_ps2_trough", "mid_ps2_dip", "mid_ps2_recovery"]
    params = ["alpha", "beta", "kappa"]
    df7 = _safe_load_day7_indices()
    fig, axes = plt.subplots(1, 4, figsize=(15.0, 3.6), sharey=True)
    width = 0.25
    x = np.arange(len(params))
    for ax, qoi in zip(axes, qois):
        st4 = [DAY4_REFERENCE.get(qoi, {}).get(p, 0.0) for p in params]
        st7 = [
            float(df7[(df7["qoi"] == qoi) & (df7["parameter"] == p)]["ST"].iloc[0])
            if not df7.empty else 0.0
            for p in params
        ]
        st7b = [
            float(idx_df_7b[(idx_df_7b["qoi"] == qoi)
                             & (idx_df_7b["parameter"] == p)]["ST"].iloc[0])
            for p in params
        ]
        ax.bar(x - width, st4,  width, color="#888888", label="Day 4")
        ax.bar(x,        st7,  width, color="#E67E22", label="Day 7")
        ax.bar(x + width, st7b, width, color="#3498DB", label="Day 7b")
        for i, p in enumerate(params):
            d4_to_7b = abs(st4[i] - st7b[i])
            d7_to_7b = abs(st7[i] - st7b[i])
            if d7_to_7b > 0.15:
                tag = ("artifact" if abs(st4[i] - st7b[i])
                                     < abs(st4[i] - st7[i]) else "real")
                ax.text(x[i] + width, max(st7b[i], st7[i]) + 0.05, "*",
                        color="#E63946", ha="center", fontsize=12,
                        fontweight="bold")
                ax.text(x[i] + width, max(st7b[i], st7[i]) + 0.10, tag,
                        color="#E63946", ha="center", fontsize=6.5)
        ax.set_xticks(x)
        ax.set_xticklabels([PARAM_LABELS[p] for p in params])
        ax.set_title(QOI_LABELS[qoi].replace("\n", " "))
        ax.set_ylim(0, max(1.0, max(max(st4 + st7 + st7b) + 0.15, 1.0)))
    axes[0].set_ylabel("Total-order index ST")
    axes[0].legend(loc="upper right", fontsize=7)
    fig.suptitle("Day 7b - Day 4 vs Day 7 vs Day 7b ST comparison "
                 "(* = |Day7-Day7b| > 0.15)", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Output tables
# ----------------------------------------------------------------------------

def write_table_1_indices(idx_df: pd.DataFrame, out: Path) -> None:
    cols = ["qoi", "parameter", "S_first", "S_first_CI_low", "S_first_CI_high",
            "ST", "ST_CI_low", "ST_CI_high", "CI_width", "Insensitive_flag"]
    out_df = idx_df.rename(columns={"qoi": "QoI", "parameter": "Param"})[
        ["QoI", "Param"] + cols[2:]]
    out_df.to_csv(out, index=False)


def write_table_2_interactions(idx_df: pd.DataFrame, out: Path) -> None:
    rows = []
    for _, r in idx_df.iterrows():
        sf = float(r["S_first"]); st = float(r["ST"])
        inter = max(0.0, st - sf)
        pct = (100.0 * inter / st) if st > 1e-6 else 0.0
        rows.append({
            "QoI": r["qoi"], "Param": r["parameter"],
            "S_first": sf, "ST": st,
            "interaction": inter, "interaction_pct": pct,
        })
    pd.DataFrame(rows).to_csv(out, index=False)


def write_table_4_three_way(idx_df_7b: pd.DataFrame, out: Path) -> None:
    df7 = _safe_load_day7_indices()
    rows = []
    qois = ["hayano_t4", "mid_ps2_trough", "mid_ps2_dip", "mid_ps2_recovery"]
    for qoi in qois:
        for p in ["alpha", "beta", "kappa", "cmc"]:
            st4 = DAY4_REFERENCE.get(qoi, {}).get(p, np.nan)
            st7 = (float(df7[(df7["qoi"] == qoi) & (df7["parameter"] == p)]["ST"].iloc[0])
                   if not df7.empty
                      and len(df7[(df7["qoi"] == qoi) & (df7["parameter"] == p)])
                   else np.nan)
            row = idx_df_7b[(idx_df_7b["qoi"] == qoi)
                            & (idx_df_7b["parameter"] == p)]
            st7b = float(row["ST"].iloc[0]) if len(row) else np.nan
            d_4_7b = (st7b - st4) if not np.isnan(st4) else np.nan
            interp = "STABLE"
            if not (np.isnan(st4) or np.isnan(st7) or np.isnan(st7b)):
                if abs(st7b - st4) >= 0.10:
                    if abs(st7 - st7b) < 0.10 and abs(st4 - st7b) >= 0.10:
                        interp = "PERCEPTION_FIX"
                    elif abs(st7 - st7b) >= 0.15 and abs(st4 - st7b) < abs(st4 - st7):
                        interp = "ESTIMATION_ARTIFACT"
                    else:
                        interp = "GENUINE_SHIFT"
                if p == "cmc" and st7b > 0.50:
                    interp = "CMC_ABSORPTION"
            rows.append({
                "QoI": qoi, "Param": p,
                "ST_day4": st4, "ST_day7": st7, "ST_day7b": st7b,
                "Delta_4_to_7b": d_4_7b, "Interpretation": interp,
            })
    pd.DataFrame(rows).to_csv(out, index=False)


# ----------------------------------------------------------------------------
# Smoke / sample-size estimation
# ----------------------------------------------------------------------------

def estimate_runtime(n_eval_main: int, n_eval_sep: int,
                     n_smoke: int, n_members: int) -> Tuple[float, float, float]:
    """Run a small smoke benchmark and extrapolate runtimes."""
    spec = d5.scenario_specs(REPO)["route6_closed"]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    rng = np.random.default_rng(20260205)
    bounds = np.array(PROBLEM_4D["bounds"])
    samples = rng.uniform(bounds[:, 0], bounds[:, 1], size=(n_smoke, 4))

    t0 = time.time()
    for i, x in enumerate(samples):
        run_one_eval(input_dir, conflict_file,
                     x[0], x[1], x[2], x[3],
                     n_agents=300, n_steps=72,
                     n_members=n_members, sample_idx=i)
    elapsed = time.time() - t0
    per = elapsed / max(1, n_smoke)
    main_min = per * n_eval_main / 60.0
    sep_min  = per * n_eval_sep  / 60.0
    print(f"\n[smoke] {n_smoke} evals in {elapsed:.1f}s  "
          f"({per:.2f}s/eval, {n_members} ensemble members)")
    print(f"[smoke] projected main campaign: {main_min:.1f} min")
    print(f"[smoke] projected separability   : {sep_min:.1f} min")
    return per, main_min, sep_min


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Day 7b Sobol main campaign.")
    ap.add_argument("--n-samples", type=int, default=200,
                    help="Saltelli n_samples (D=4 -> n*(D+2) = total evals).")
    ap.add_argument("--ensemble", type=int, default=3,
                    help="Ensemble members per parameter vector.")
    ap.add_argument("--n-agents", type=int, default=300)
    ap.add_argument("--n-steps", type=int, default=72)
    ap.add_argument("--quick", action="store_true",
                    help="Tiny smoke run (overrides --n-samples to 4).")
    ap.add_argument("--smoke-only", action="store_true",
                    help="Run only the runtime smoke benchmark, then exit.")
    ap.add_argument("--parallel", action="store_true",
                    help="Use multiprocessing.Pool for the campaign.")
    ap.add_argument("--n-workers", type=int,
                    default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()

    RES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    if args.quick:
        args.n_samples = 4

    print("=" * 72)
    print(f"Day 7b Sobol  --  n_samples={args.n_samples}, "
          f"ensemble={args.ensemble}, n_agents={args.n_agents}, "
          f"n_steps={args.n_steps}")
    print(f"Parallel: {args.parallel} (workers={args.n_workers})")
    print("=" * 72)

    n_eval = args.n_samples * (PROBLEM_4D["num_vars"] + 2)
    n_eval_sep = 200 * (3 + 2) * 3  # for projection only
    print(f"[size] Main campaign: D=4, n_samples={args.n_samples} "
          f"-> {n_eval} evaluations")
    print(f"[size] CMC sep mini : D=3, n_samples=200, 3 levels -> "
          f"{n_eval_sep} evaluations (run separately)")

    if args.smoke_only:
        estimate_runtime(n_eval, n_eval_sep, n_smoke=10, n_members=args.ensemble)
        return

    # --- Main campaign ---
    t_main = time.time()
    X, results = run_sobol_campaign(
        PROBLEM_4D,
        n_samples=args.n_samples,
        n_agents=args.n_agents,
        n_steps=args.n_steps,
        n_members=args.ensemble,
        parallel=args.parallel,
        n_workers=args.n_workers,
    )
    main_runtime = time.time() - t_main
    print(f"\n[main] campaign complete in {main_runtime/60:.2f} min "
          f"({main_runtime/max(1,len(results)):.2f}s/eval)")

    raw_path = RES / "raw_results.csv"
    results.to_csv(raw_path, index=False)
    print(f"[main] raw results -> {raw_path}")

    # --- Sobol indices ---
    idx_df = analyze_sobol(PROBLEM_4D, results, n_resamples=1000)
    write_table_1_indices(idx_df, RES / "sobol_indices_full.csv")
    write_table_2_interactions(idx_df, RES / "interaction_magnitudes.csv")
    write_table_4_three_way(idx_df, RES / "day4_day7_day7b_comparison.csv")

    # --- Acceptance gate ---
    ok, failures = check_index_validity(idx_df)
    print("\n" + "=" * 72)
    print("Acceptance criteria report")
    print("=" * 72)
    if failures:
        for f in failures:
            print(f"  {f}")
    else:
        print("  All Day 7b acceptance criteria PASS.")

    # --- Figures ---
    fig_d7b_1_primary(idx_df,    FIG / "D7b-1_sobol_primary.png")
    fig_d7b_2_interaction(idx_df, FIG / "D7b-2_interaction_heatmap.png")
    fig_d7b_3_kappa_scatter(results, FIG / "D7b-3_kappa_conditional_scatter.png")
    fig_d7b_4_ci_heat(idx_df,    FIG / "D7b-4_ci_width_heatmap.png")
    fig_d7b_5_three_way(idx_df,  FIG / "D7b-5_three_way_comparison.png")
    print(f"[fig] wrote D7b-1..5 to {FIG}")

    # --- Design summary JSON ---
    summary = {
        "n_samples": int(args.n_samples),
        "D": int(PROBLEM_4D["num_vars"]),
        "calc_second_order": False,
        "total_evaluations": int(n_eval),
        "ensemble_members_per_eval": int(args.ensemble),
        "scenario": "route6_closed",
        "modes_run": ["sys1_only", "blend"],
        "n_agents": int(args.n_agents),
        "n_steps": int(args.n_steps),
        "main_campaign_runtime_min": main_runtime / 60.0,
        "acceptance_pass": bool(ok),
        "acceptance_failures": failures,
    }
    with (RES / "sobol_design_summary.json").open("w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"[main] design summary -> {RES/'sobol_design_summary.json'}")


if __name__ == "__main__":
    main()
