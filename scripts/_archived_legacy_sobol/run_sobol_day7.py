#!/usr/bin/env python3
"""
Day 7 — Full Sobol sensitivity re-run on the real Fukushima OSM network.

Replaces the Day 4 analysis. Day 4 used the broken perception layer that
made κ structurally insensitive; Day 6 confirmed κ is now identifiable
after the Day 4b refactor. Day 7 runs a Saltelli design with four free
parameters (α, β, κ, ConflictMoveChance), six QoIs, on the route6_closed
scenario with the precomputed conflict potential field.

Sections (matches the Day 7 prompt):
  §1 Saltelli design, n_samples=32, D=4 → N=32×(2×4+2)=320 evaluations
  §2 Six QoIs
  §3 Simulation config: route6_closed, blend mode, 300 agents, 72 steps,
     3 ensemble members per Sobol sample
  §4 Bootstrap CIs (SALib num_resamples=500, conf_level=0.95)
  §5 Interaction analysis (ST − S1) heatmap
  §6 κ characterization scatter
  §7 CMC separability mini-analysis (3 CMC levels × n=24, D=3 → 192 each)
  §8 Day 4 comparison
  §9 Figures D7-1 .. D7-5

Use --quick for a 4-sample smoke test that exercises the full pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from SALib.analyze import sobol as sobol_analyze  # noqa: E402
from SALib.sample import sobol as sobol_sample  # noqa: E402

from scripts import run_day5_scenarios as d5  # noqa: E402
from scripts import run_fukushima_day3 as d3  # noqa: E402
from flee.SimulationSettings import SimulationSettings  # noqa: E402

RES_D7 = REPO / "results" / "day7"
FIG_D7 = REPO / "figures" / "fukushima" / "day7"

PROBLEM = {
    "num_vars": 4,
    "names": ["alpha", "beta", "kappa", "cmc"],
    "bounds": [[0.5, 5.0], [1.0, 10.0], [1.0, 20.0], [0.25, 0.75]],
}
PROBLEM_3D = {
    "num_vars": 3,
    "names": ["alpha", "beta", "kappa"],
    "bounds": [[0.5, 5.0], [1.0, 10.0], [1.0, 20.0]],
}

QOI_KEYS = ["hayano_t4", "mid_ps2_trough", "mid_ps2_dip",
            "mid_ps2_recovery", "corridor_inland_pct", "blend_inner_t7"]

QOI_LABELS = {
    "hayano_t4":           "Hayano t=4\ndeparture",
    "mid_ps2_trough":      "Mid P$_{S2}$\ntrough",
    "mid_ps2_dip":         "Mid P$_{S2}$\ndip",
    "mid_ps2_recovery":    "Mid P$_{S2}$\nrecovery",
    "corridor_inland_pct": "Inland-corridor\nfraction",
    "blend_inner_t7":      "Blend inner\nt=7",
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


# --------------------------- QoI computation ---------------------------------

def compute_qois(adf: pd.DataFrame, arrivals: pd.DataFrame) -> dict:
    """Compute the six Day 7 QoIs from a single (params, member) blend run."""
    out: dict = {k: 0.0 for k in QOI_KEYS}

    blend = adf[adf["decision_mode"] == "blend"]
    if blend.empty:
        return out

    # hayano_t4: inner+mid blend departures by t=4
    im = blend[blend["initial_zone"].isin(["inner", "mid"])][
        "agent_id"].unique()
    if len(im):
        c = blend[(blend["agent_id"].isin(im)) & (blend["zone"] == "camp")]
        first = c.groupby("agent_id")["timestep"].min()
        out["hayano_t4"] = float((first <= 4).sum() / len(im))

    # P_S2 trace in the mid zone
    mid = set(d3.ZONES["mid"])
    mid_active = blend[blend["location"].isin(mid)]
    if not mid_active.empty:
        by_t = mid_active.groupby("timestep")["s2_weight"].mean()
        if len(by_t):
            trough = float(by_t.min())
            out["mid_ps2_trough"] = trough
            ps2_t0 = float(by_t.iloc[0]) if 0 in by_t.index else float(by_t.iloc[0])
            out["mid_ps2_dip"] = max(0.0, ps2_t0 - trough)
            t28 = by_t.loc[28] if 28 in by_t.index else by_t.iloc[-1]
            out["mid_ps2_recovery"] = float(max(0.0, float(t28) - trough))

    # corridor_inland_pct: fraction of fork-origin agents passing through
    # the kawauchi inland node
    fork_at_t0 = blend[(blend["timestep"] == 0)
                       & (blend["location"].isin(FORK_ORIGINS))]
    fork_ids = set(fork_at_t0["agent_id"].unique())
    if fork_ids:
        used_inland = (blend[(blend["agent_id"].isin(fork_ids))
                             & (blend["location"].isin(INLAND_NODES))]
                       ["agent_id"].unique())
        out["corridor_inland_pct"] = float(len(used_inland) / len(fork_ids))

    # blend_inner_t7: pure-blend inner clearance at t=7 (no original baseline
    # in the same run — we report the absolute clearance, matching the Day 5
    # convention used for κ-sweep diagnostics)
    inner = blend[blend["initial_zone"] == "inner"]["agent_id"].unique()
    if len(inner):
        c = blend[(blend["agent_id"].isin(inner)) & (blend["zone"] == "camp")]
        first = c.groupby("agent_id")["timestep"].min()
        out["blend_inner_t7"] = float((first <= 7).sum() / len(inner))

    return out


# --------------------------- per-eval simulation -----------------------------

def _run_eval(input_dir: Path, conflict_file: str,
              alpha: float, beta: float, kappa: float, cmc: float,
              n_agents: int, n_steps: int,
              n_members: int, seed_base: int,
              ) -> dict:
    """Run n_members ensemble for one parameter vector; return mean QoIs."""
    orig_load = d3.load_config

    def patched(input_dir_str):
        orig_load(input_dir_str)
        SimulationSettings.move_rules["ConflictMoveChance"] = float(cmc)

    d3.load_config = patched
    try:
        ensemble = []
        for m in range(n_members):
            seed = seed_base + m
            adf, _lm, arr = d5._run_member(
                input_dir, conflict_file, "blend",
                n_agents, n_steps,
                alpha, beta, kappa, seed, "beta",
            )
            ensemble.append(compute_qois(adf, arr))
    finally:
        d3.load_config = orig_load

    out = {}
    for k in QOI_KEYS:
        out[k] = float(np.mean([e[k] for e in ensemble]))
    return out


# --------------------------- Sobol driver ------------------------------------

def run_sobol_campaign(problem: dict, n_samples: int,
                       n_agents: int, n_steps: int, n_members: int,
                       cmc_fixed: float | None = None,
                       seed_base: int = 7000000,
                       quiet: bool = False) -> tuple[np.ndarray, pd.DataFrame]:
    """Generate Saltelli samples and run all evaluations.

    If ``cmc_fixed`` is not None, the design is over (α, β, κ) only and
    every run uses CMC=cmc_fixed. Otherwise CMC is the 4th sampled dim.

    Returns (X, results_df) where X is the (N, D) Saltelli matrix and
    results_df has one row per evaluation with [run_id, *params, *qois].
    """
    spec = d5.scenario_specs(REPO)["route6_closed"]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]

    X = sobol_sample.sample(problem, n_samples, calc_second_order=False)
    n_eval = X.shape[0]
    if not quiet:
        print(f"[Sobol] generated {n_eval} samples for D={problem['num_vars']}, "
              f"n_samples={n_samples}")

    rows = []
    t0 = time.time()
    for i, x in enumerate(X):
        params = dict(zip(problem["names"], x.tolist()))
        if cmc_fixed is not None:
            params["cmc"] = float(cmc_fixed)
        seed = seed_base + i * 7
        if not quiet and (i % max(1, n_eval // 20) == 0 or i == n_eval - 1):
            elapsed = time.time() - t0
            rate = (i + 1) / max(1e-6, elapsed)
            eta = (n_eval - i - 1) / max(1e-6, rate)
            print(f"  eval {i+1:4d}/{n_eval}  "
                  f"α={params['alpha']:.2f} β={params['beta']:.2f} "
                  f"κ={params['kappa']:.2f} cmc={params['cmc']:.2f}  "
                  f"({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")
        qois = _run_eval(
            input_dir, conflict_file,
            params["alpha"], params["beta"], params["kappa"], params["cmc"],
            n_agents, n_steps, n_members, seed,
        )
        rows.append({"run_id": i, **params, **qois})

    df = pd.DataFrame(rows)
    return X, df


# --------------------------- analysis ----------------------------------------

def analyze_sobol(problem: dict, results: pd.DataFrame,
                  n_resamples: int = 500,
                  conf_level: float = 0.95) -> pd.DataFrame:
    """Run SALib sobol.analyze() per QoI; return tidy CI table."""
    rows = []
    for qoi in QOI_KEYS:
        Y = results[qoi].values.astype(float)
        if np.allclose(Y, Y[0]):
            for p in problem["names"]:
                rows.append({"qoi": qoi, "parameter": p,
                             "S1": 0.0, "S1_conf": 0.0,
                             "S1_CI_low": 0.0, "S1_CI_high": 0.0,
                             "ST": 0.0, "ST_conf": 0.0,
                             "ST_CI_low": 0.0, "ST_CI_high": 0.0,
                             "interaction": 0.0,
                             "constant_output": True})
            continue
        Si = sobol_analyze.analyze(
            problem, Y, calc_second_order=False,
            num_resamples=n_resamples,
            conf_level=conf_level,
            print_to_console=False,
            seed=int(np.frombuffer(qoi.encode(), dtype=np.uint8).sum()),
        )
        for j, p in enumerate(problem["names"]):
            S1 = float(Si["S1"][j])
            S1_c = float(Si["S1_conf"][j])
            ST = float(Si["ST"][j])
            ST_c = float(Si["ST_conf"][j])
            rows.append({
                "qoi": qoi, "parameter": p,
                "S1": S1, "S1_conf": S1_c,
                "S1_CI_low": S1 - S1_c, "S1_CI_high": S1 + S1_c,
                "ST": ST, "ST_conf": ST_c,
                "ST_CI_low": ST - ST_c, "ST_CI_high": ST + ST_c,
                "interaction": max(0.0, ST - S1),
                "constant_output": False,
            })
    return pd.DataFrame(rows)


def flag_insensitivity(idx_df: pd.DataFrame) -> pd.DataFrame:
    """Annotate ST CI spanning zero as 'effectively insensitive'."""
    idx_df = idx_df.copy()
    idx_df["ST_includes_zero"] = (idx_df["ST_CI_low"] <= 0.0) & (
        idx_df["ST_CI_high"] >= 0.0)
    idx_df["effectively_insensitive"] = (
        (idx_df["ST"] < 0.05) | idx_df["ST_includes_zero"])
    return idx_df


# --------------------------- figures -----------------------------------------

def _setup_mpl():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8,
        "axes.titlesize": 9, "axes.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.5, "figure.dpi": 150,
    })


def fig_d7_1(idx_df: pd.DataFrame, out_dir: Path) -> None:
    _setup_mpl()
    params = list(PROBLEM["names"])
    fig, axes = plt.subplots(2, len(QOI_KEYS), figsize=(15, 5.5),
                             sharey="row")
    width = 0.6
    for col, qoi in enumerate(QOI_KEYS):
        sub = idx_df[idx_df["qoi"] == qoi].set_index("parameter")
        x = np.arange(len(params))
        for ax_idx, key in enumerate(("S1", "ST")):
            ax = axes[ax_idx, col]
            vals = [sub.loc[p, key] if p in sub.index else 0.0 for p in params]
            errs = [sub.loc[p, f"{key}_conf"] if p in sub.index else 0.0
                    for p in params]
            colors = [PARAM_COLORS[p] for p in params]
            ax.bar(x, vals, width, yerr=errs, color=colors,
                   edgecolor="white", linewidth=0.4, capsize=3,
                   error_kw={"linewidth": 0.7, "ecolor": "#333"})
            ax.axhline(0.05, color="#888", ls="--", lw=0.6, alpha=0.6)
            ax.axhline(0.0, color="#333", lw=0.4)
            ax.set_xticks(x)
            ax.set_xticklabels([PARAM_LABELS[p] for p in params], fontsize=8)
            if col == 0:
                ax.set_ylabel(f"{key} index", fontsize=8)
            if ax_idx == 0:
                ax.set_title(QOI_LABELS[qoi], fontsize=8)
            ax.set_ylim(-0.1, 1.05)
            ax.grid(axis="y", alpha=0.2)

    fig.suptitle("Day 7 Fig D7-1 — Sobol S1 and ST indices with 95% bootstrap "
                 "CIs (route6_closed, real Fukushima network)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = out_dir / "D7-1_sobol_indices.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


def fig_d7_2(idx_df: pd.DataFrame, out_dir: Path) -> None:
    _setup_mpl()
    params = list(PROBLEM["names"])
    H = np.zeros((len(params), len(QOI_KEYS)))
    for j, p in enumerate(params):
        for i, q in enumerate(QOI_KEYS):
            sub = idx_df[(idx_df["qoi"] == q) & (idx_df["parameter"] == p)]
            if not sub.empty:
                H[j, i] = float(sub["interaction"].iloc[0])
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    im = ax.imshow(H, aspect="auto", cmap="magma_r", vmin=0,
                   vmax=max(0.4, float(H.max())))
    ax.set_xticks(np.arange(len(QOI_KEYS)))
    ax.set_xticklabels([QOI_LABELS[q].replace("\n", " ") for q in QOI_KEYS],
                       rotation=20, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(params)))
    ax.set_yticklabels([PARAM_LABELS[p] for p in params], fontsize=10)
    for j in range(len(params)):
        for i in range(len(QOI_KEYS)):
            ax.text(i, j, f"{H[j, i]:.2f}", ha="center", va="center",
                    color="white" if H[j, i] > 0.2 else "black",
                    fontsize=7)
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Interaction = ST − S1", fontsize=8)
    fig.suptitle("Day 7 Fig D7-2 — Interaction magnitude per parameter × QoI",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = out_dir / "D7-2_interactions.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


def fig_d7_3(results: pd.DataFrame, out_dir: Path) -> None:
    _setup_mpl()
    fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharex=True)
    norm = plt.Normalize(vmin=PROBLEM["bounds"][1][0],
                         vmax=PROBLEM["bounds"][1][1])
    cmap = plt.cm.viridis
    for ax, qoi in zip(axes.flat, QOI_KEYS):
        sc = ax.scatter(results["kappa"], results[qoi],
                        c=results["beta"], cmap=cmap, norm=norm,
                        s=18, alpha=0.7, edgecolor="white", linewidth=0.3)
        ax.set_title(QOI_LABELS[qoi].replace("\n", " "), fontsize=8)
        ax.set_xlabel("κ", fontsize=8)
        ax.grid(True, alpha=0.2)
        ax.set_xscale("log")
    cbar = fig.colorbar(sc, ax=axes.flat[2], fraction=0.046, pad=0.04)
    cbar.set_label("β", fontsize=8)
    fig.suptitle("Day 7 Fig D7-3 — QoI vs κ, colored by β "
                 "(all 320 Sobol samples)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = out_dir / "D7-3_kappa_scatter_by_beta.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


def fig_d7_4(idx_df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Side-by-side ST comparison: Day 4 vs Day 7 (4 shared QoIs × 3 params)."""
    _setup_mpl()
    shared = ["hayano_t4", "mid_ps2_trough",
              "mid_ps2_dip", "mid_ps2_recovery"]
    params3 = ["alpha", "beta", "kappa"]
    fig, axes = plt.subplots(1, len(shared), figsize=(13, 3.6), sharey=True)
    width = 0.38
    rows = []
    for ax, qoi in zip(axes, shared):
        x = np.arange(len(params3))
        d4 = [DAY4_REFERENCE[qoi][p] for p in params3]
        d7 = [(idx_df[(idx_df["qoi"] == qoi) & (idx_df["parameter"] == p)]
               ["ST"].iloc[0]
               if not idx_df[(idx_df["qoi"] == qoi)
                             & (idx_df["parameter"] == p)].empty
               else 0.0)
              for p in params3]
        d7_err = [(idx_df[(idx_df["qoi"] == qoi) & (idx_df["parameter"] == p)]
                   ["ST_conf"].iloc[0]
                   if not idx_df[(idx_df["qoi"] == qoi)
                                 & (idx_df["parameter"] == p)].empty
                   else 0.0)
                  for p in params3]
        ax.bar(x - width / 2, d4, width, color="#888780",
               edgecolor="white", linewidth=0.4, label="Day 4 (broken κ)")
        ax.bar(x + width / 2, d7, width, yerr=d7_err,
               color="#1D9E75", edgecolor="white", linewidth=0.4,
               capsize=3, label="Day 7 (real network)",
               error_kw={"linewidth": 0.7, "ecolor": "#333"})
        ax.axhline(0.05, color="#888", ls="--", lw=0.6, alpha=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels([PARAM_LABELS[p] for p in params3])
        ax.set_title(QOI_LABELS[qoi].replace("\n", " "), fontsize=8)
        ax.grid(axis="y", alpha=0.2)
        ax.set_ylim(0, 1.0)
        for p, v4, v7 in zip(params3, d4, d7):
            rows.append({"qoi": qoi, "parameter": p,
                         "ST_day4": v4, "ST_day7": v7,
                         "delta": v7 - v4})
    axes[0].set_ylabel("Total-order Sobol index ST", fontsize=8)
    axes[0].legend(fontsize=7, loc="upper right")
    fig.suptitle("Day 7 Fig D7-4 — ST comparison: Day 4 (synthetic, κ broken) "
                 "vs Day 7 (real network, κ identifiable)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = out_dir / "D7-4_day4_vs_day7.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")
    return pd.DataFrame(rows)


def fig_d7_5(sep_df: pd.DataFrame, out_dir: Path) -> None:
    _setup_mpl()
    params3 = ["alpha", "beta", "kappa"]
    qois = QOI_KEYS
    fig, axes = plt.subplots(1, len(qois), figsize=(15, 3.4), sharey=True)
    cmcs = sorted(sep_df["cmc"].unique())
    for ax, qoi in zip(axes, qois):
        for p in params3:
            ys = []
            yerr = []
            for c in cmcs:
                sub = sep_df[(sep_df["cmc"] == c)
                             & (sep_df["qoi"] == qoi)
                             & (sep_df["parameter"] == p)]
                ys.append(float(sub["ST"].iloc[0]) if not sub.empty else 0.0)
                yerr.append(float(sub["ST_conf"].iloc[0]) if not sub.empty
                            else 0.0)
            ax.errorbar(cmcs, ys, yerr=yerr,
                        marker="o", lw=1.2, ms=5,
                        color=PARAM_COLORS[p], capsize=3,
                        label=PARAM_LABELS[p])
        ax.axhline(0.05, color="#888", ls="--", lw=0.6, alpha=0.6)
        ax.set_xlabel("ConflictMoveChance")
        ax.set_title(QOI_LABELS[qoi].replace("\n", " "), fontsize=8)
        ax.grid(True, alpha=0.2)
        ax.set_ylim(0, 1.05)
    axes[0].set_ylabel("ST (cognitive params at fixed CMC)", fontsize=8)
    axes[0].legend(fontsize=7, loc="upper right")
    fig.suptitle("Day 7 Fig D7-5 — CMC separability: ST(α, β, κ) at three "
                 "fixed CMC levels", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    out = out_dir / "D7-5_cmc_separability.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


# --------------------------- main --------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-samples",     type=int, default=32)
    ap.add_argument("--n-agents",      type=int, default=300)
    ap.add_argument("--n-steps",       type=int, default=72)
    ap.add_argument("--ensemble",      type=int, default=3)
    ap.add_argument("--cmc-n-samples", type=int, default=24,
                    help="Saltelli n for the §7 CMC separability mini-runs")
    ap.add_argument("--cmc-ensemble",  type=int, default=1)
    ap.add_argument("--bootstrap",     type=int, default=500)
    ap.add_argument("--skip-cmc-sep", action="store_true",
                    help="skip Section 7 CMC separability mini-analysis")
    ap.add_argument("--quick", action="store_true",
                    help="4-sample smoke test of the full pipeline")
    args = ap.parse_args()

    if args.quick:
        args.n_samples = 4
        args.n_agents = 200
        args.ensemble = 1
        args.cmc_n_samples = 4
        args.cmc_ensemble = 1
        print(f"[quick] n_samples={args.n_samples}, n_agents={args.n_agents}, "
              f"ensemble={args.ensemble}, "
              f"cmc_n_samples={args.cmc_n_samples}")

    RES_D7.mkdir(parents=True, exist_ok=True)
    FIG_D7.mkdir(parents=True, exist_ok=True)

    # --- §1–4: main Saltelli campaign ---------------------------------------
    print(f"\n=== Day 7 §1–4: main Saltelli campaign "
          f"(D=4, n={args.n_samples}) ===")
    t0 = time.time()
    X, results = run_sobol_campaign(
        PROBLEM, args.n_samples,
        args.n_agents, args.n_steps, args.ensemble,
        cmc_fixed=None, seed_base=7000000,
    )
    main_runtime = time.time() - t0
    print(f"  main campaign: {len(results)} evals × {args.ensemble} members "
          f"in {main_runtime:.1f}s")

    raw_path = RES_D7 / "sobol_raw_results.csv"
    results.to_csv(raw_path, index=False)
    print(f"  wrote {raw_path}")

    idx_df = analyze_sobol(PROBLEM, results,
                           n_resamples=args.bootstrap, conf_level=0.95)
    idx_df = flag_insensitivity(idx_df)
    idx_path = RES_D7 / "sobol_indices.csv"
    idx_df.to_csv(idx_path, index=False)
    print(f"  wrote {idx_path}")

    interactions = idx_df[["qoi", "parameter", "S1", "ST", "interaction",
                           "ST_includes_zero", "effectively_insensitive"]]
    interactions.to_csv(RES_D7 / "interaction_magnitudes.csv", index=False)

    # --- §7: CMC separability -----------------------------------------------
    sep_df = pd.DataFrame()
    sep_runtime = 0.0
    if not args.skip_cmc_sep:
        print(f"\n=== Day 7 §7: CMC separability "
              f"(D=3, n={args.cmc_n_samples}, 3 CMC levels) ===")
        t1 = time.time()
        rows = []
        for cmc in (0.25, 0.50, 0.75):
            print(f"  -- CMC fixed at {cmc:.2f} --")
            _Xc, res_c = run_sobol_campaign(
                PROBLEM_3D, args.cmc_n_samples,
                args.n_agents, args.n_steps, args.cmc_ensemble,
                cmc_fixed=cmc, seed_base=7100000 + int(cmc * 1000),
                quiet=True,
            )
            idx_c = analyze_sobol(PROBLEM_3D, res_c,
                                  n_resamples=args.bootstrap,
                                  conf_level=0.95)
            idx_c["cmc"] = cmc
            rows.append(idx_c)
        sep_df = pd.concat(rows, ignore_index=True)
        sep_path = RES_D7 / "cmc_separability.csv"
        sep_df.to_csv(sep_path, index=False)
        sep_runtime = time.time() - t1
        print(f"  wrote {sep_path} ({sep_runtime:.1f}s)")

    # --- Day 4 comparison ----------------------------------------------------
    print("\n=== Day 7 §8: Day 4 vs Day 7 comparison ===")
    cmp_df = fig_d7_4(idx_df, FIG_D7)
    cmp_path = RES_D7 / "day4_vs_day7_comparison.csv"
    cmp_df.to_csv(cmp_path, index=False)
    print(f"  wrote {cmp_path}")
    print(cmp_df.to_string(index=False, float_format=lambda v: f"{v:7.3f}"))

    # --- Figures -------------------------------------------------------------
    fig_d7_1(idx_df, FIG_D7)
    fig_d7_2(idx_df, FIG_D7)
    fig_d7_3(results, FIG_D7)
    if not sep_df.empty:
        fig_d7_5(sep_df, FIG_D7)

    # --- Design summary ------------------------------------------------------
    summary = {
        "n_samples":      args.n_samples,
        "n_evaluations":  int(len(results)),
        "n_members":      args.ensemble,
        "n_agents":       args.n_agents,
        "n_steps":        args.n_steps,
        "bootstrap_resamples": args.bootstrap,
        "scenario":       "route6_closed",
        "mode":           "blend",
        "parameter_ranges": dict(zip(PROBLEM["names"], PROBLEM["bounds"])),
        "main_campaign_runtime_sec": round(main_runtime, 1),
        "cmc_sep_runtime_sec":      round(sep_runtime, 1),
        "total_simulations":        int(len(results)) * args.ensemble
                                    + (3 * args.cmc_n_samples
                                       * (2 * 3 + 2) * args.cmc_ensemble
                                       if not args.skip_cmc_sep else 0),
    }
    (RES_D7 / "sobol_design_summary.json").write_text(
        json.dumps(summary, indent=2))
    print(f"\n  wrote {(RES_D7 / 'sobol_design_summary.json')}")

    # --- Diagnostics gate ----------------------------------------------------
    print("\n=== Day 7 diagnostics gate ===")
    gate = []

    beta_trough = idx_df[(idx_df["qoi"] == "mid_ps2_trough")
                         & (idx_df["parameter"] == "beta")]
    bt = float(beta_trough["ST"].iloc[0]) if not beta_trough.empty else 0.0
    gate.append(("β ST for mid_ps2_trough", f"D4=0.80; D7={bt:.3f}",
                 bt > 0.30, "β dominance"))

    kappa_rows = idx_df[idx_df["parameter"] == "kappa"]
    kappa_passing = kappa_rows[
        (kappa_rows["ST"] > 0.05) & (~kappa_rows["ST_includes_zero"])]
    n_k = len(kappa_passing)
    gate.append(("κ ST > 0.05 with CI excluding 0",
                 f"{n_k} QoI(s)",
                 n_k >= 1, "κ identifiability"))

    if not sep_df.empty:
        max_drift = 0.0
        worst = None
        for p in ("alpha", "beta", "kappa"):
            for q in QOI_KEYS:
                vals = sep_df[(sep_df["parameter"] == p)
                              & (sep_df["qoi"] == q)]["ST"].values
                if len(vals) >= 2:
                    drift = float(np.max(vals) - np.min(vals))
                    if drift > max_drift:
                        max_drift = drift
                        worst = (p, q, drift)
        ok = (max_drift < 0.15)
        gate.append(("CMC separability (max ST drift)",
                     f"{max_drift:.3f}"
                     + (f" at {worst[0]}/{worst[1]}" if worst else ""),
                     ok, "two-stage Day 8 design"))

    n_with_ci = int((idx_df["S1_conf"] > 0).sum() + (idx_df["ST_conf"] > 0).sum())
    gate.append(("Bootstrap CIs computed",
                 f"{n_with_ci} indices have non-zero CI",
                 n_with_ci > 0, "paper reporting"))

    for label, observed, ok, why in gate:
        flag = "PASS" if ok else "FAIL"
        print(f"  [{flag}] {label}: {observed}  ({why})")

    print("\n=== Day 7 complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
