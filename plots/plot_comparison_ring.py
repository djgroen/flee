#!/usr/bin/env python3
"""
Generate publication-quality diagnostic plots for comparison_ring simulation.

Run from project root: python plots/plot_comparison_ring.py
Output: plots/output/fig1_ps2_trajectory.png, fig2_condition_comparison.png,
        fig3_psi_distribution.png, fig4_ps2_envelope.png
"""

import os
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results" / "comparison_ring"
OUTPUT_DIR = PROJECT_ROOT / "plots" / "output"

COLORS = {
    "original_flee": "#888888",
    "s1_only": "#2166ac",
    "s2_only": "#d6604d",
    "full_mixture": "#1a9641",
    "baseline": "#000000",
    "tstar": "#d6604d",
    "tstarstar": "#2166ac",
}

N_AGENTS = 500
ALPHA = 2.0
PSI_MIN = 0.1

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})


def _load_csv(filename):
    """Load CSV as list of dicts. Return None if missing."""
    path = RESULTS_DIR / filename
    if not path.exists():
        print(f"  Skipping: {filename} not found")
        return None
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def _load_phase_boundaries():
    """Load phase_boundaries.csv. Return dict or None."""
    rows = _load_csv("phase_boundaries.csv")
    if not rows:
        return None
    r = rows[0]
    return {
        "tstar": int(r["tstar"]),
        "tstarstar": int(r["tstarstar"]),
        "mean_s2_t0": float(r["mean_s2_t0"]),
    }


def fig1_ps2_trajectory():
    """Figure 1: P_S2 trajectory with phase markers."""
    fm = _load_csv("full_mixture.csv")
    pb = _load_phase_boundaries()
    if not fm or not pb:
        return False

    timesteps = [int(r["timestep"]) for r in fm]
    mean_s2 = [float(r["mean_s2_weight"]) for r in fm]
    std_s2 = [float(r["std_s2_weight"]) for r in fm]
    tstar = pb["tstar"]
    tstarstar = pb["tstarstar"]
    mean_s2_t0 = pb["mean_s2_t0"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 72)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Timestep", fontsize=12)
    ax.set_ylabel("Population-mean $P_{S2}$", fontsize=12)
    ax.tick_params(labelsize=10)
    ax.set_title("Dual-process $P_{S2}$ trajectory — synthetic 10-location chain", fontsize=13)

    ax.fill_between(timesteps, np.array(mean_s2) - np.array(std_s2),
                    np.array(mean_s2) + np.array(std_s2),
                    color=COLORS["full_mixture"], alpha=0.2)
    ax.plot(timesteps, mean_s2, color=COLORS["full_mixture"], linewidth=2, label="full_mixture")

    ax.axhline(mean_s2_t0, color=COLORS["baseline"], linestyle="--", linewidth=1.5,
               label="Pre-crisis baseline ($\\Psi$)")

    ax.axvline(tstar, color=COLORS["tstar"], linestyle="--", linewidth=1.5,
               label="Phase 1 end ($t^*$)")
    ax.axvline(tstarstar, color=COLORS["tstarstar"], linestyle="--", linewidth=1.5,
               label="Phase 2 end ($t^{**}$)")

    y_top = 0.95
    ax.text((0 + tstar) / 2, y_top, "Phase 1", ha="center", fontsize=9)
    ax.text((tstar + tstarstar) / 2, y_top, "Phase 2", ha="center", fontsize=9)
    ax.text((tstarstar + 72) / 2, y_top, "Post", ha="center", fontsize=9)

    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig1_ps2_trajectory.png", dpi=300, bbox_inches="tight")
    plt.close()
    return True


def fig2_condition_comparison():
    """Figure 2: Four-condition departure comparison."""
    conditions = ["original_flee", "s1_only", "s2_only", "full_mixture"]
    data = {}
    for c in conditions:
        rows = _load_csv(f"{c}.csv")
        if not rows:
            return False
        data[c] = rows

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 72)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Timestep", fontsize=12)
    ax.set_ylabel("Cumulative fraction departed", fontsize=12)
    ax.tick_params(labelsize=10)
    ax.set_title("Departure dynamics by condition — synthetic 10-location chain", fontsize=13)

    for c in conditions:
        rows = data[c]
        timesteps = [int(r["timestep"]) for r in rows]
        num_moved = [int(r["num_agents_moved"]) for r in rows]
        frac = [n / N_AGENTS for n in num_moved]
        ax.plot(timesteps, frac, color=COLORS[c], linewidth=2, label=c)

    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig2_condition_comparison.png", dpi=300, bbox_inches="tight")
    plt.close()
    return True


def fig3_psi_distribution():
    """Figure 3: Agent Psi distribution at initialization."""
    fm = _load_csv("full_mixture.csv")
    if not fm:
        return False

    # Get t=0 row for mean and std
    row0 = next((r for r in fm if int(r["timestep"]) == 0), None)
    if not row0:
        return False
    mean_psi = float(row0["mean_s2_weight"])
    std_psi = float(row0["std_s2_weight"])

    # Reconstruct implied Psi distribution: Psi = Psi_min + (1 - Psi_min)(1 - e^{-alpha*x})
    # with x ~ Uniform(0,1). Invert: Psi -> x = -ln(1 - (Psi - Psi_min)/(1 - Psi_min)) / alpha
    # For sampling: x ~ U(0,1), Psi = Psi_min + (1 - Psi_min)(1 - exp(-alpha*x))
    np.random.seed(42)
    x = np.random.uniform(0, 1, N_AGENTS)
    psi_vals = PSI_MIN + (1 - PSI_MIN) * (1 - np.exp(-ALPHA * x))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 1)
    ax.set_xlabel("Cognitive capacity $\\Psi$", fontsize=12)
    ax.set_ylabel("Number of agents", fontsize=12)
    ax.tick_params(labelsize=10)
    ax.set_title("Agent cognitive capacity distribution at initialization", fontsize=13)

    ax.hist(psi_vals, bins=20, color=COLORS["full_mixture"], alpha=0.7, edgecolor="white")
    ax.axvline(mean_psi, color=COLORS["baseline"], linestyle="--", linewidth=1.5,
               label="Mean $\\Psi$")
    ax.axvline(PSI_MIN, color=COLORS["tstar"], linestyle="--", linewidth=1.5,
               label="$\\Psi_{\\min}$")

    ax.text(0.98, 0.98, f"$\\alpha = {ALPHA}$, $n = {N_AGENTS}$",
            transform=ax.transAxes, fontsize=9, ha="right", va="top")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig3_psi_distribution.png", dpi=300, bbox_inches="tight")
    plt.close()
    return True


def fig4_ps2_envelope():
    """Figure 4: P_S2 envelope (min/mean/max)."""
    dist = _load_csv("full_mixture_s2_distribution.csv")
    fm = _load_csv("full_mixture.csv")
    pb = _load_phase_boundaries()
    if not dist or not fm or not pb:
        return False

    timesteps = [int(r["timestep"]) for r in dist]
    min_s2 = [float(r["min_s2_weight"]) for r in dist]
    mean_s2 = [float(r["mean_s2_weight"]) for r in dist]
    max_s2 = [float(r["max_s2_weight"]) for r in dist]

    # Get std from full_mixture for mean±std band
    std_by_t = {int(r["timestep"]): float(r["std_s2_weight"]) for r in fm}
    std_s2 = [std_by_t.get(t, 0) for t in timesteps]

    tstar = pb["tstar"]
    tstarstar = pb["tstarstar"]
    mean_s2_t0 = pb["mean_s2_t0"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 72)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Timestep", fontsize=12)
    ax.set_ylabel("$P_{S2}$", fontsize=12)
    ax.tick_params(labelsize=10)
    ax.set_title("$P_{S2}$ population envelope — high-$\\Psi$/low-$\\Psi$ divergence", fontsize=13)

    ax.fill_between(timesteps, min_s2, max_s2, color=COLORS["full_mixture"], alpha=0.15,
                    label="Agent range (min–max)")
    mean_arr = np.array(mean_s2)
    std_arr = np.array(std_s2)
    ax.fill_between(timesteps, mean_arr - std_arr, mean_arr + std_arr,
                    color=COLORS["full_mixture"], alpha=0.25, label="±1 std")
    ax.plot(timesteps, mean_s2, color=COLORS["full_mixture"], linewidth=2)

    ax.axhline(mean_s2_t0, color=COLORS["baseline"], linestyle="--", linewidth=1.5,
               label="Pre-crisis baseline")
    ax.axvline(tstar, color=COLORS["tstar"], linestyle="--", linewidth=1.5)
    ax.axvline(tstarstar, color=COLORS["tstarstar"], linestyle="--", linewidth=1.5)

    # Annotate Phase 2 spreading
    mid_t = (tstar + tstarstar) / 2
    mid_y = 0.5
    ax.annotate("Phase 2: $\\Psi$ heterogeneity emerges", xy=(mid_t, mid_y),
                xytext=(mid_t + 15, 0.6), fontsize=9,
                arrowprops=dict(arrowstyle="->", color="gray"),
                ha="left")

    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig4_ps2_envelope.png", dpi=300, bbox_inches="tight")
    plt.close()
    return True


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    if fig1_ps2_trajectory():
        count += 1
    if fig2_condition_comparison():
        count += 1
    if fig3_psi_distribution():
        count += 1
    if fig4_ps2_envelope():
        count += 1

    print(f"Saved {count} figures to plots/output/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
