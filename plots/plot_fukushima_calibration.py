#!/usr/bin/env python3
"""
Produce Fukushima calibration diagnostic plots.

Reads: results/fukushima/grid_search.csv, best_fit_trajectory.csv,
       data/observations/fukushima_2011/hayano_2013_fig3_hourly.csv
Output: plots/output/fig_fukushima_best_fit.png, fig_fukushima_loss_surface.png

Run from project root: python plots/plot_fukushima_calibration.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GRID_PATH = PROJECT_ROOT / "results" / "fukushima" / "grid_search.csv"
TRAJ_PATH = PROJECT_ROOT / "results" / "fukushima" / "best_fit_trajectory.csv"
OBS_PATH = PROJECT_ROOT / "data" / "observations" / "fukushima_2011" / "hayano_2013_fig3_hourly.csv"
OUTPUT_DIR = PROJECT_ROOT / "plots" / "output"

T0 = pd.Timestamp("2011-03-11 14:46")
BASELINE_TIME = pd.Timestamp("2011-03-11 04:00")
OUTAGE_START = pd.Timestamp("2011-03-13 06:00")
OUTAGE_END = pd.Timestamp("2011-03-14 12:00")
TIMESTEP_HOURS = 2

ZONE_COLS = ["<5km", "5–10km", "10–15km", "15–20km"]
ZONE_TO_LOC = {"<5km": "L0", "5–10km": "L1", "10–15km": "L2", "15–20km": "L3"}
TARGET_HOURS = [15, 20, 33, 72]
EVENT_HOURS = {"3km order": 6.6, "10km order": 15.0, "20km order": 27.6}

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def load_observed():
    """Load observed data with frac_remaining and hours_since_t0."""
    df = pd.read_csv(OBS_PATH)
    df["datetime"] = df["Date/Time"].apply(
        lambda s: pd.to_datetime(f"2011-{s.strip()}", format="%Y-%m/%d %H:%M", errors="coerce")
    )
    df = df.dropna(subset=["datetime"])
    df["hours_since_t0"] = (df["datetime"] - T0).dt.total_seconds() / 3600.0

    baseline_row = df[df["datetime"] == BASELINE_TIME].iloc[0]
    for col in ZONE_COLS:
        if col in df.columns and col in baseline_row and baseline_row[col] > 0:
            df[f"frac_{col}"] = df[col] / baseline_row[col]
    return df


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not GRID_PATH.exists() or not TRAJ_PATH.exists():
        print("Run fukushima/run_fukushima.py first to generate grid_search.csv and best_fit_trajectory.csv")
        return 1
    if not OBS_PATH.exists():
        print(f"Observation file not found: {OBS_PATH}")
        return 1

    grid_df = pd.read_csv(GRID_PATH)
    traj_df = pd.read_csv(TRAJ_PATH)
    obs_df = load_observed()

    best = grid_df.loc[grid_df["loss"].idxmin()]
    best_kappa = best["kappa"]

    # Model trajectory: step -> hours
    traj_df["hours_since_t0"] = traj_df["step"] * TIMESTEP_HOURS

    # Outage window in hours
    outage_start_h = (OUTAGE_START - T0).total_seconds() / 3600
    outage_end_h = (OUTAGE_END - T0).total_seconds() / 3600

    # Figure 1: Four subplots, one per zone
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()

    for i, zone in enumerate(ZONE_COLS):
        ax = axes[i]
        loc = ZONE_TO_LOC[zone]
        frac_col = f"frac_{zone}"

        # Observed: black dots with ±20% uncertainty
        usable = obs_df[~(obs_df["datetime"].between(OUTAGE_START, OUTAGE_END))]
        ax.errorbar(
            usable["hours_since_t0"],
            usable[frac_col],
            yerr=0.2 * usable[frac_col],
            fmt="o",
            color="black",
            markersize=4,
            capsize=2,
            alpha=0.7,
        )

        # Modeled: green line
        ax.plot(
            traj_df["hours_since_t0"],
            traj_df[f"frac_{loc}"],
            color="#1a9641",
            linewidth=2,
            label="Model (best fit)",
        )

        # Target timepoints: vertical dashed
        for th in TARGET_HOURS:
            ax.axvline(th, color="gray", linestyle="--", linewidth=1, alpha=0.7)

        # Network outage: gray shade
        ax.axvspan(outage_start_h, outage_end_h, color="gray", alpha=0.3)

        # Key events: vertical dotted
        for _, h in EVENT_HOURS.items():
            ax.axvline(h, color="blue", linestyle=":", linewidth=1, alpha=0.5)

        ax.set_xlim(-5, 80)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Hours since t=0")
        ax.set_ylabel("Fraction remaining")
        dist_str = zone.replace("–", "-").replace("<5km", "0-5km")
        ax.set_title(f"{zone} ({dist_str} from NPP)")
        ax.legend(loc="upper right", fontsize=8)

    fig.suptitle("Fukushima 2011 calibration — best fit vs observed", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig_fukushima_best_fit.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'fig_fukushima_best_fit.png'}")

    # Figure 2: Loss surface (alpha vs beta at best kappa)
    best_kappa_df = grid_df[grid_df["kappa"] == best_kappa]
    if best_kappa_df.empty:
        best_kappa_df = grid_df
        best_kappa = grid_df["kappa"].iloc[0]

    pivot = best_kappa_df.pivot(index="alpha", columns="beta", values="loss")
    alphas = pivot.index.values
    betas = pivot.columns.values

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(
        pivot.values,
        extent=[betas[0], betas[-1], alphas[-1], alphas[0]],
        aspect="auto",
        cmap="viridis_r",
    )
    plt.colorbar(im, ax=ax, label="Calibration loss")

    # Mark minimum
    min_idx = np.unravel_index(np.argmin(pivot.values), pivot.values.shape)
    best_alpha = alphas[min_idx[0]]
    best_beta = betas[min_idx[1]]
    ax.plot(best_beta, best_alpha, "*", color="red", markersize=15, markeredgecolor="white")

    ax.set_xlabel("beta")
    ax.set_ylabel("alpha")
    ax.set_title(f"Parameter sensitivity — alpha vs beta at kappa={best_kappa}")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig_fukushima_loss_surface.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {OUTPUT_DIR / 'fig_fukushima_loss_surface.png'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
