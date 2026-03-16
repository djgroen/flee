#!/usr/bin/env python3
"""
Analyze S1/S2 fork experiments: load results and create plots.
Run after run_fork_experiments.py or run_nuclear_parameter_sweep.py.
Saves figures to {base}/figures/ (default: data/experiments/figures/).

Layouts (topologies): ring, star, linear.
- ring: Facility at center, concentric rings of nodes, SafeZones on outer ring.
- star: Hub at center, spokes to SafeZones.
- linear: Facility → Main chain with side branches → SafeZones.
All plots aggregate across these three topologies unless noted (e.g. per-topology lines).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def load_all_results(base_dir: Path):
    """Load all results_*.csv from topology subdirs."""
    base_dir = Path(base_dir)
    rows = []
    for topo_dir in base_dir.iterdir():
        if not topo_dir.is_dir() or topo_dir.name in ("configs", "figures"):
            continue
        for p in topo_dir.glob("results_*.csv"):
            df = pd.read_csv(p)
            # Parse alpha, beta, seed from filename: results_a1.0_b2.0_s0.csv
            stem = p.stem.replace("results_", "")
            parts = stem.split("_")
            a, b, s = None, None, None
            for x in parts:
                if x.startswith("a"):
                    a = float(x[1:])
                elif x.startswith("b"):
                    b = float(x[1:])
                elif x.startswith("s"):
                    s = int(x[1:])
            df["topology"] = topo_dir.name
            df["alpha"] = a
            df["beta"] = b
            df["seed"] = s
            rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)

def plot_p_s2_vs_conflict(df: pd.DataFrame, out_dir: Path):
    """P_S2 vs conflict intensity (binned). Model: high conflict → low P_S2."""
    fig, ax = plt.subplots(figsize=(6, 4))
    df = df.copy()
    df["conflict_bin"] = pd.cut(df["conflict"], bins=np.linspace(0, 1, 11), include_lowest=True)
    agg = (
        df.dropna(subset=["conflict_bin"])
        .groupby(["conflict_bin", "topology"], observed=True)
        .agg(mean_p_s2=("p_s2", "mean"), mean_conflict=("conflict", "mean"))
        .reset_index()
    )
    for topo in agg["topology"].unique():
        sub = agg[agg["topology"] == topo]
        ax.plot(sub["mean_conflict"], sub["mean_p_s2"], "o-", label=topo, markersize=6)
    ax.set_xlabel("Conflict intensity (location)")
    ax.set_ylabel("Mean P_S2")
    ax.set_title("P_S2 vs conflict (model: Ω(c) → 0 as c → 1)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(out_dir / "p_s2_vs_conflict.png", dpi=150, bbox_inches="tight")
    fig.savefig(out_dir / "p_s2_vs_conflict.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  Saved p_s2_vs_conflict.png/.pdf")

def plot_p_s2_over_time(df: pd.DataFrame, out_dir: Path):
    """Mean P_S2 over timesteps by topology. Y-axis zooms to data range to show variation."""
    fig, ax = plt.subplots(figsize=(6, 4))
    agg = df.groupby(["timestep", "topology"], as_index=False)["p_s2"].mean()
    for topo in agg["topology"].unique():
        sub = agg[agg["topology"] == topo]
        ax.plot(sub["timestep"], sub["p_s2"], "o-", label=topo, markersize=3, alpha=0.9)
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Mean P_S2")
    ax.set_title("Mean P_S2 over time (agents gain experience)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    # Zoom y-axis to data range so slope is visible (was flat with 0–1)
    lo, hi = agg["p_s2"].min(), agg["p_s2"].max()
    margin = max(0.03, (hi - lo) * 0.2) if hi > lo else 0.05
    ax.set_ylim(max(0, lo - margin), min(1, hi + margin))
    fig.tight_layout()
    fig.savefig(out_dir / "p_s2_over_time.png", dpi=150, bbox_inches="tight")
    fig.savefig(out_dir / "p_s2_over_time.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  Saved p_s2_over_time.png/.pdf")

def compute_evacuation_from_results(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute evacuation rate from raw results (handles SafeZone_0, SafeZone_1, etc.)."""
    rows = []
    for (topo, a, b, s), g in df.groupby(["topology", "alpha", "beta", "seed"]):
        last_t = g["timestep"].max()
        last = g[g["timestep"] == last_t]
        n = len(last)
        evacuated = last["location"].astype(str).str.contains("SafeZone", na=False).sum()
        rows.append({"topology": topo, "alpha": a, "beta": b, "seed": s, "final_evacuation_rate": evacuated / n if n else 0})
    return pd.DataFrame(rows)

def plot_evacuation_by_params(raw_df: pd.DataFrame, out_dir: Path):
    """Final evacuation rate by topology, α, β (computed from raw results)."""
    evac = compute_evacuation_from_results(raw_df)
    if evac.empty:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    topologies = evac["topology"].unique()
    x = np.arange(len(topologies))
    width = 0.2
    for i, (alpha, beta) in enumerate([(1.0, 1.0), (1.0, 2.0), (2.0, 1.0), (2.0, 2.0)]):
        sub = evac[(evac["alpha"] == alpha) & (evac["beta"] == beta)]
        if sub.empty:
            continue
        rates = [sub[sub["topology"] == t]["final_evacuation_rate"].values[0] if len(sub[sub["topology"] == t]) else 0 for t in topologies]
        off = (i - 1.5) * width
        ax.bar(x + off, rates, width, label=f"α={alpha}, β={beta}")
    ax.set_xticks(x)
    ax.set_xticklabels(topologies)
    ax.set_ylabel("Final evacuation rate")
    ax.set_title("Evacuation success by topology and (α, β)")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(out_dir / "evacuation_by_params.png", dpi=150, bbox_inches="tight")
    fig.savefig(out_dir / "evacuation_by_params.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  Saved evacuation_by_params.png/.pdf")

def plot_summary_heatmap(raw_df: pd.DataFrame, out_dir: Path):
    """Avg P_S2 and peak P_S2 by topology × (α, β), computed from raw results."""
    if raw_df.empty:
        return
    agg = raw_df.groupby(["topology", "alpha", "beta", "seed"]).agg(
        avg_p_s2=("p_s2", "mean"), peak_p_s2=("p_s2", "max")
    ).reset_index()
    df = agg.groupby(["topology", "alpha", "beta"]).agg(
        avg_p_s2=("avg_p_s2", "mean"), peak_p_s2=("peak_p_s2", "mean")
    ).reset_index()
    for metric, title in [("avg_p_s2", "Mean P_S2"), ("peak_p_s2", "Peak P_S2")]:
        if metric not in df.columns:
            continue
        pivot = df.pivot_table(values=metric, index="topology", columns=["alpha", "beta"], aggfunc="mean")
        fig, ax = plt.subplots(figsize=(5, 3))
        im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=1, cmap="viridis")
        ncol = len(pivot.columns)
        ax.set_xticks(np.arange(ncol))
        ax.set_xticklabels([f"({a},{b})" for (a, b) in pivot.columns])
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xlabel("(α, β)")
        plt.colorbar(im, ax=ax, label=metric)
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(out_dir / f"heatmap_{metric}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    print("  Saved heatmap_avg_p_s2.png, heatmap_peak_p_s2.png")

def main():
    import argparse
    p = argparse.ArgumentParser(description="Analyze S1/S2 results and create heatmaps, P_S2 plots.")
    p.add_argument("--base", default="data/experiments", help="Base dir with topology subdirs (ring/, linear/, star/) containing results_*.csv")
    args = p.parse_args()
    base = Path(args.base)
    if not base.exists():
        print(f"Base dir {base} not found. Run run_fork_experiments.py or run_nuclear_parameter_sweep.py first.")
        return 1
    out_dir = base / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_all_results(base)
    if df.empty:
        print(f"No results_*.csv found under {base}/.")
        return 1

    print("Creating plots in", out_dir)
    plot_p_s2_vs_conflict(df, out_dir)
    plot_p_s2_over_time(df, out_dir)
    plot_evacuation_by_params(df, out_dir)
    plot_summary_heatmap(df, out_dir)

    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
