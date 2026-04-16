#!/usr/bin/env python3
"""
Day 4: Sobol Sensitivity Analysis on Fukushima Topology
Saltelli 2008 design — n_samples=24, D=3 parameters (α, β, κ), 192 model evaluations.
Computes first-order (S1) and total-order (ST) Sobol indices for 5 QoIs.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = REPO_ROOT / "figures" / "fukushima"

PROBLEM = {
    "num_vars": 3,
    "names": ["alpha", "beta", "kappa"],
    "bounds": [[0.5, 5.0], [1.0, 10.0], [1.0, 20.0]],
}

QOI_KEYS = ["hayano_t4", "mid_ps2_trough", "mid_ps2_dip",
            "mid_ps2_recovery", "blend_inner_t7"]

QOI_LABELS = {
    "hayano_t4": "Hayano t=4\ndeparture",
    "mid_ps2_trough": "Mid P$_{S2}$\ntrough",
    "mid_ps2_dip": "Mid P$_{S2}$\ndip",
    "mid_ps2_recovery": "Mid P$_{S2}$\nrecovery",
    "blend_inner_t7": "Blend inner\nt=7 speedup",
}

PARAM_COLORS = {"alpha": "#3498DB", "beta": "#E67E22", "kappa": "#1ABC9C"}
PARAM_LABELS = {"alpha": r"$\alpha$", "beta": r"$\beta$", "kappa": r"$\kappa$"}


def run_single(args_tuple):
    """Run a single Fukushima simulation and return QoIs."""
    run_id, alpha, beta, kappa, n_steps, seed, results_dir = args_tuple
    out_json = str(results_dir / f"sobol_run_{run_id}.json")

    cmd = [
        sys.executable, str(REPO_ROOT / "scripts" / "run_fukushima_day3.py"),
        "--alpha", str(alpha),
        "--beta", str(beta),
        "--kappa", str(kappa),
        "--modes", "blend", "original",
        "--output-json", out_json,
        "--n-steps", str(n_steps),
        "--seed", str(seed),
    ]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            cwd=str(REPO_ROOT),
        )
        if proc.returncode != 0:
            print(f"  [WARN] Run {run_id} failed: {proc.stderr[-300:]}")
            return run_id, None

        with open(out_json) as f:
            qois = json.load(f)
        return run_id, qois

    except Exception as exc:
        print(f"  [ERROR] Run {run_id}: {exc}")
        return run_id, None


def run_campaign(n_samples, n_steps, seed, n_workers):
    """Generate Saltelli samples, run all evaluations, collect results."""
    print(f"Generating Saltelli samples: n={n_samples}, D={PROBLEM['num_vars']}")
    X = sobol_sample.sample(PROBLEM, n_samples, calc_second_order=True)
    n_runs = X.shape[0]
    print(f"  Total model evaluations: {n_runs}")

    run_dir = RESULTS_DIR / "sobol_runs"
    run_dir.mkdir(parents=True, exist_ok=True)

    tasks = []
    for i in range(n_runs):
        alpha, beta, kappa = X[i]
        tasks.append((i, alpha, beta, kappa, n_steps, seed, run_dir))

    print(f"Running {n_runs} simulations with {n_workers} workers...")
    t0 = time.time()

    results = {}
    with Pool(n_workers) as pool:
        for run_id, qois in pool.imap_unordered(run_single, tasks):
            results[run_id] = qois
            done = sum(1 for v in results.values() if v is not None)
            if done % 20 == 0 or done == n_runs:
                elapsed = time.time() - t0
                print(f"  {done}/{n_runs} completed ({elapsed:.0f}s)")

    elapsed = time.time() - t0
    print(f"All runs completed in {elapsed:.1f}s")

    failed = [i for i, v in results.items() if v is None]
    if failed:
        print(f"  WARNING: {len(failed)} failed runs: {failed[:10]}...")

    rows = []
    for i in range(n_runs):
        q = results.get(i)
        if q is None:
            continue
        rows.append({
            "run_id": i,
            "alpha": X[i, 0],
            "beta": X[i, 1],
            "kappa": X[i, 2],
            **q,
        })

    df = pd.DataFrame(rows)
    raw_path = RESULTS_DIR / "sobol_day4_raw.csv"
    df.to_csv(raw_path, index=False)
    print(f"Saved {len(df)} results to {raw_path}")

    return X, df


def compute_indices(X, df):
    """Compute Sobol indices using SALib."""
    print("\nComputing Sobol indices...")

    all_indices = {}
    for qoi in QOI_KEYS:
        Y = np.array([df.loc[df["run_id"] == i, qoi].values[0]
                       for i in range(len(X)) if i in df["run_id"].values])

        if len(Y) < len(X):
            print(f"  [WARN] {qoi}: only {len(Y)}/{len(X)} valid runs")
            Y_full = np.full(len(X), np.nan)
            valid_ids = df["run_id"].values
            for idx, run_id in enumerate(range(len(X))):
                if run_id in valid_ids:
                    Y_full[run_id] = df.loc[df["run_id"] == run_id, qoi].values[0]
            mask = ~np.isnan(Y_full)
            if mask.sum() < len(X) * 0.9:
                print(f"  [SKIP] {qoi}: too many failures")
                continue
            Y_full[np.isnan(Y_full)] = np.nanmean(Y_full)
            Y = Y_full

        Si = sobol_analyze.analyze(PROBLEM, Y, calc_second_order=True,
                                    print_to_console=False)
        all_indices[qoi] = Si
        print(f"  {qoi}: S1={Si['S1']}, ST={Si['ST']}")

    idx_rows = []
    for qoi, Si in all_indices.items():
        for j, pname in enumerate(PROBLEM["names"]):
            idx_rows.append({
                "qoi": qoi,
                "parameter": pname,
                "S1": Si["S1"][j],
                "S1_conf": Si["S1_conf"][j],
                "ST": Si["ST"][j],
                "ST_conf": Si["ST_conf"][j],
            })

    idx_df = pd.DataFrame(idx_rows)
    idx_path = RESULTS_DIR / "sobol_day4_indices.csv"
    idx_df.to_csv(idx_path, index=False)
    print(f"Saved Sobol indices to {idx_path}")

    return all_indices, idx_df


def fig_S1_sobol_bar(idx_df, out_dir):
    """S1: Horizontal bar chart of first-order and total-order Sobol indices."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    fig.suptitle("Sobol Sensitivity Indices — Fukushima Topology (n=192)\n"
                 "Saltelli 2008 design, first and total order", fontsize=10)

    y_pos = np.arange(len(QOI_KEYS))
    bar_width = 0.25

    for panel_idx, (ax, col, title) in enumerate([
        (ax1, "S1", "First-Order (S1)"),
        (ax2, "ST", "Total-Order (ST)"),
    ]):
        for j, pname in enumerate(PROBLEM["names"]):
            sub = idx_df[idx_df["parameter"] == pname]
            vals = [sub.loc[sub["qoi"] == q, col].values[0] for q in QOI_KEYS]
            confs = [sub.loc[sub["qoi"] == q, f"{col}_conf"].values[0] for q in QOI_KEYS]
            ax.barh(y_pos + j * bar_width, vals, bar_width,
                    xerr=confs, label=PARAM_LABELS[pname],
                    color=PARAM_COLORS[pname], alpha=0.85,
                    capsize=2, error_kw={"linewidth": 0.8})

        ax.axvline(0.05, color="gray", ls="--", lw=0.8, alpha=0.7, label="S=0.05")
        ax.set_xlabel(title)
        ax.set_yticks(y_pos + bar_width)
        ax.set_yticklabels([QOI_LABELS.get(q, q) for q in QOI_KEYS], fontsize=7)
        ax.set_xlim(-0.1, 1.0)
        ax.legend(fontsize=7, loc="lower right")
        ax.grid(axis="x", alpha=0.2)

    fig.tight_layout()
    fig.savefig(out_dir / "S1_sobol_indices.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved S1_sobol_indices.png")


def fig_S2_scatter(df, out_dir):
    """S2: 5×3 scatter grid of parameter vs QoI with LOWESS smoother."""
    fig, axes = plt.subplots(5, 3, figsize=(10, 14))
    fig.suptitle("Parameter–QoI Scatter Plots (192 runs)", fontsize=10, y=0.995)

    params = PROBLEM["names"]

    for row, qoi in enumerate(QOI_KEYS):
        for col, pname in enumerate(params):
            ax = axes[row, col]
            x = df[pname].values
            y = df[qoi].values

            ax.scatter(x, y, s=8, alpha=0.4, color=PARAM_COLORS[pname],
                       edgecolors="none")

            try:
                from statsmodels.nonparametric.smoothers_lowess import lowess
                smooth = lowess(y, x, frac=0.4)
                ax.plot(smooth[:, 0], smooth[:, 1], "r-", lw=1.5)
            except ImportError:
                z = np.polyfit(x, y, 2)
                xfit = np.linspace(x.min(), x.max(), 50)
                ax.plot(xfit, np.polyval(z, xfit), "r-", lw=1.5)

            if row == 0:
                ax.set_title(PARAM_LABELS[pname], fontsize=9)
            if col == 0:
                ax.set_ylabel(QOI_LABELS.get(qoi, qoi), fontsize=7)
            if row == len(QOI_KEYS) - 1:
                ax.set_xlabel(PARAM_LABELS[pname], fontsize=8)

            ax.tick_params(labelsize=6)
            ax.grid(True, alpha=0.15)

    fig.tight_layout()
    fig.savefig(out_dir / "S2_scatter_param_qoi.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved S2_scatter_param_qoi.png")


def fig_S3_interaction_heatmap(idx_df, out_dir):
    """S3: Heatmap of ST - S1 (interaction magnitude)."""
    params = PROBLEM["names"]

    interaction = np.zeros((len(params), len(QOI_KEYS)))
    for i, pname in enumerate(params):
        for j, qoi in enumerate(QOI_KEYS):
            row = idx_df[(idx_df["parameter"] == pname) & (idx_df["qoi"] == qoi)]
            if not row.empty:
                interaction[i, j] = row["ST"].values[0] - row["S1"].values[0]

    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(interaction, aspect="auto", cmap="YlOrRd", vmin=0,
                   vmax=max(0.3, interaction.max()))

    ax.set_xticks(range(len(QOI_KEYS)))
    ax.set_xticklabels([QOI_LABELS.get(q, q) for q in QOI_KEYS], fontsize=7,
                       rotation=30, ha="right")
    ax.set_yticks(range(len(params)))
    ax.set_yticklabels([PARAM_LABELS[p] for p in params], fontsize=9)

    for i in range(len(params)):
        for j in range(len(QOI_KEYS)):
            ax.text(j, i, f"{interaction[i, j]:.3f}", ha="center", va="center",
                    fontsize=8, color="white" if interaction[i, j] > 0.15 else "black")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("ST - S1 (interaction effect)", fontsize=8)
    ax.set_title("Parameter Interaction Magnitudes (ST − S1)\n"
                 "Higher values = effect depends on other parameters", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "S3_interaction_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved S3_interaction_heatmap.png")


def fig_S4_hayano_coverage(df, out_dir):
    """S4: Hayano target coverage scatter."""
    fig, ax = plt.subplots(figsize=(8, 4))

    sorted_df = df.sort_values("hayano_t4").reset_index(drop=True)
    x = np.arange(len(sorted_df))
    y = sorted_df["hayano_t4"].values
    colors = sorted_df["beta"].values

    sc = ax.scatter(x, y, c=colors, cmap="viridis", s=15, alpha=0.8,
                    edgecolors="none")
    cbar = fig.colorbar(sc, ax=ax, shrink=0.8)
    cbar.set_label(r"$\beta$ value", fontsize=8)

    ax.axhspan(0.50, 0.95, color="green", alpha=0.1, label="Hayano range [0.50, 0.95]")
    ax.axhline(0.78, color="green", ls="--", lw=1.0, alpha=0.8, label="Observed 0.78")

    in_range = ((y >= 0.50) & (y <= 0.95)).sum()
    crosses_78 = (y >= 0.78).sum()
    ax.set_title(f"Hayano t=4 Departure Across Design Space (n={len(df)})\n"
                 f"{in_range}/{len(df)} in [0.50, 0.95]; "
                 f"{crosses_78}/{len(df)} reach 0.78", fontsize=9)
    ax.set_xlabel("Run index (sorted by hayano_t4)", fontsize=8)
    ax.set_ylabel("hayano_t4", fontsize=8)
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
    fig.savefig(out_dir / "S4_hayano_coverage.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved S4_hayano_coverage.png")


def identifiability_report(idx_df, df):
    """Run identifiability checks and generate report."""
    lines = []
    lines.append("=" * 70)
    lines.append("SOBOL IDENTIFIABILITY REPORT — Day 4")
    lines.append("=" * 70)
    lines.append("")

    all_pass = True
    params = PROBLEM["names"]

    # Check 1: α sensitivity — ST(α) > 0.05 for at least one QoI
    alpha_STs = idx_df[idx_df["parameter"] == "alpha"]["ST"].values
    alpha_max_ST = alpha_STs.max()
    alpha_sensitive = alpha_max_ST > 0.05
    status = "PASS" if alpha_sensitive else "FLAG"
    lines.append(f"CHECK 1 α sensitivity: max ST(α) = {alpha_max_ST:.4f} → {status}")
    if not alpha_sensitive:
        lines.append("  ACTION: α is potentially unidentifiable. Consider fixing α=1.0")
        lines.append("  for nuclear paper. α becomes identifiable only with dynamic Psi")
        lines.append("  (protracted displacement scenarios).")

    # Check 1b: κ sensitivity diagnostic
    kappa_STs = idx_df[idx_df["parameter"] == "kappa"]["ST"].values
    kappa_max_ST = kappa_STs.max()
    kappa_sensitive = kappa_max_ST > 0.05
    status = "PASS" if kappa_sensitive else "FLAG"
    lines.append(f"CHECK 1b κ sensitivity: max ST(κ) = {kappa_max_ST:.4f} → {status}")
    if not kappa_sensitive:
        lines.append("  DIAGNOSIS: κ insensitive because info_mode='official_zones' with")
        lines.append("  in_official_zone never set on locations. perceived_here = perceived_best")
        lines.append("  = 0.1 always → sigma = 0.5 regardless of κ.")
        lines.append("  ACTION: κ becomes identifiable with heterogeneous radiation")
        lines.append("  (dosimeter mode or plume model). Fix κ=5.0 for nuclear paper")
        all_pass = False

    # Check 2: β dominance for mid_ps2_trough and mid_ps2_dip
    for qoi in ["mid_ps2_trough", "mid_ps2_dip"]:
        qoi_STs = idx_df[idx_df["qoi"] == qoi]
        max_param = qoi_STs.loc[qoi_STs["ST"].idxmax(), "parameter"]
        beta_ST = qoi_STs[qoi_STs["parameter"] == "beta"]["ST"].values[0]
        is_dom = max_param == "beta"
        status = "PASS" if is_dom else "WARN"
        lines.append(f"CHECK 2 β dominance ({qoi}): β ST={beta_ST:.4f}, "
                     f"max param={max_param} → {status}")
        if not is_dom:
            all_pass = False

    # Check 3: κ role for hayano_t4
    hayano_STs = idx_df[idx_df["qoi"] == "hayano_t4"]
    kappa_ST = hayano_STs[hayano_STs["parameter"] == "kappa"]["ST"].values[0]
    ranked = hayano_STs.sort_values("ST", ascending=False)["parameter"].tolist()
    kappa_rank = ranked.index("kappa") + 1
    kappa_ok = kappa_rank <= 2
    status = "PASS" if kappa_ok else "WARN"
    lines.append(f"CHECK 3 κ for hayano_t4: ST={kappa_ST:.4f}, rank={kappa_rank} → {status}")
    if not kappa_ok:
        all_pass = False

    # Check 4: Three-phase robustness — mid_ps2_dip > 0.10 for >90% of runs
    dip_vals = df["mid_ps2_dip"].values
    frac_above = (dip_vals > 0.10).mean()
    robust = frac_above > 0.90
    status = "PASS" if robust else "WARN"
    lines.append(f"CHECK 4 Three-phase robustness: {frac_above:.1%} runs have "
                 f"dip>0.10 → {status}")
    if not robust:
        viable = df[df["mid_ps2_dip"] > 0.10]
        lines.append(f"  Viable parameter ranges:")
        for p in params:
            lines.append(f"    {p}: [{viable[p].min():.2f}, {viable[p].max():.2f}]")
        all_pass = False

    # Check 5: Interaction magnitude — mean (ST - S1) < 0.15
    interactions = idx_df["ST"].values - idx_df["S1"].values
    mean_interaction = interactions.mean()
    low_interaction = mean_interaction < 0.15
    status = "PASS" if low_interaction else "WARN"
    lines.append(f"CHECK 5 Mean interaction (ST-S1): {mean_interaction:.4f} → {status}")
    if not low_interaction:
        lines.append("  ACTION: High interactions — joint calibration required on Day 7")
        all_pass = False

    # Check 6: Hayano 0.78 reachable
    max_hayano = df["hayano_t4"].max()
    reaches_78 = max_hayano >= 0.78
    status = "PASS" if reaches_78 else "FAIL"
    lines.append(f"CHECK 6 Hayano 0.78 reachable: max={max_hayano:.4f} → {status}")
    if not reaches_78:
        lines.append("  ACTION: No parameter combo reaches 0.78. Check "
                     "conflict_movechance, network connectivity, or conflict schedule.")
        all_pass = False

    lines.append("")
    lines.append(f"OVERALL: {'ALL PASS' if all_pass else 'ISSUES FLAGGED — see actions'}")
    lines.append("")

    # Summary table
    lines.append("PARAMETER SENSITIVITY SUMMARY TABLE")
    lines.append("-" * 70)
    header = f"{'Param':<8} " + " ".join(f"{'S1('+q+')':>14}" for q in QOI_KEYS)
    lines.append(header)
    for pname in params:
        sub = idx_df[idx_df["parameter"] == pname]
        vals = []
        for q in QOI_KEYS:
            s1 = sub.loc[sub["qoi"] == q, "S1"].values[0]
            st = sub.loc[sub["qoi"] == q, "ST"].values[0]
            vals.append(f"{s1:.3f}/{st:.3f}")
        lines.append(f"{pname:<8} " + " ".join(f"{v:>14}" for v in vals))
    lines.append("(format: S1/ST per cell)")
    lines.append("-" * 70)

    report = "\n".join(lines)
    print(report)

    report_path = RESULTS_DIR / "sobol_day4_identifiability.txt"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nSaved identifiability report to {report_path}")

    return all_pass


def main():
    ap = argparse.ArgumentParser(description="Day 4: Sobol Sensitivity Analysis")
    ap.add_argument("--n-samples", type=int, default=24)
    ap.add_argument("--n-steps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-workers", type=int, default=min(8, cpu_count()))
    ap.add_argument("--skip-runs", action="store_true",
                    help="Skip simulation runs, load from existing CSV")
    ap.add_argument("--figures-only", action="store_true",
                    help="Only regenerate figures from existing data")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = RESULTS_DIR / "sobol_day4_raw.csv"

    if args.skip_runs or args.figures_only:
        print("Loading existing results...")
        df = pd.read_csv(raw_path)
        n_runs = len(df)
        X = df[["alpha", "beta", "kappa"]].values
        X_full = sobol_sample.sample(PROBLEM, args.n_samples, calc_second_order=True)
    else:
        X_full, df = run_campaign(args.n_samples, args.n_steps, args.seed, args.n_workers)

    # Compute Sobol indices
    idx_path = RESULTS_DIR / "sobol_day4_indices.csv"
    if args.figures_only and idx_path.exists():
        idx_df = pd.read_csv(idx_path)
        all_indices = None
    else:
        all_indices, idx_df = compute_indices(X_full, df)

    # Figures
    print("\nGenerating figures...")
    fig_S1_sobol_bar(idx_df, FIGURES_DIR)
    fig_S2_scatter(df, FIGURES_DIR)
    fig_S3_interaction_heatmap(idx_df, FIGURES_DIR)
    fig_S4_hayano_coverage(df, FIGURES_DIR)

    # Identifiability report
    print("\nRunning identifiability checks...")
    identifiability_report(idx_df, df)

    print("\nDay 4 complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
