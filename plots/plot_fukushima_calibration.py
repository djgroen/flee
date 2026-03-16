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
OBS_PATH = PROJECT_ROOT / "conflict_validation" / "fukushima_2011" / "hayano_2013_fig3_hourly.csv"
INPUT_DIR = PROJECT_ROOT / "conflict_input" / "fukushima_2011"
OUTPUT_DIR = PROJECT_ROOT / "plots" / "output"

T0 = pd.Timestamp("2011-03-11 14:46")
BASELINE_TIME = pd.Timestamp("2011-03-11 04:00")
OUTAGE_START = pd.Timestamp("2011-03-13 06:00")
OUTAGE_END = pd.Timestamp("2011-03-14 12:00")
TIMESTEP_HOURS = 2

ZONE_COLS = ["<5km", "5–10km", "10–15km", "15–20km"]
# New run uses zone names directly (frac_<5km, frac_5–10km, etc.)
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

        # Modeled: green line (traj has frac_<5km, frac_5–10km, etc.)
        ax.plot(
            traj_df["hours_since_t0"],
            traj_df[frac_col],
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

    # Figure 2: max_move_speed sensitivity (2x2, one subplot per target)
    TARGET_IDS = ["T1", "T2", "T3", "T4"]
    TARGET_OBS = {
        "T1": 0.2752, "T2": 0.1514, "T3": 0.5225, "T4": 0.0145,
    }
    TARGET_LABELS = {
        "T1": "<5km at t=15h",
        "T2": "<5km at t=20h",
        "T3": "15-20km at t=33h",
        "T4": "<20km at t=72h",
    }
    if "max_move_speed" in grid_df.columns:
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        axes = axes.flatten()
        for i, tid in enumerate(TARGET_IDS):
            ax = axes[i]
            col = f"{tid}_model"
            if col not in grid_df.columns:
                continue
            speeds = sorted(grid_df["max_move_speed"].unique())
            medians = []
            q25s = []
            q75s = []
            for sp in speeds:
                sub = grid_df[grid_df["max_move_speed"] == sp][col]
                medians.append(sub.median())
                q25s.append(sub.quantile(0.25))
                q75s.append(sub.quantile(0.75))
            obs = TARGET_OBS[tid]
            ax.fill_between(speeds, q25s, q75s, alpha=0.3, color="#1a9641")
            ax.plot(speeds, medians, color="#1a9641", linewidth=2, label="Model (median)")
            ax.axhline(obs, color="black", linestyle="--", linewidth=1.5, label="Observed")
            ax.axhspan(obs * 0.8, obs * 1.2, alpha=0.2, color="gray")
            ax.set_xlabel("max_move_speed (km per 2h step)")
            ax.set_ylabel("Modeled value")
            ax.set_title(f"T{i+1}: {TARGET_LABELS[tid]}")
            ax.set_xlim(min(speeds), max(speeds))
            ax.legend(loc="best", fontsize=8)
            ax2 = ax.twiny()
            ax2.set_xlim(ax.get_xlim())
            ax2.set_xticks(speeds)
            ax2.set_xticklabels([f"{s/2:.1f}" for s in speeds])
            ax2.set_xlabel("Implied speed (km/h)")
        fig.suptitle("Physical constraint sensitivity: max_move_speed", fontsize=12)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "fig_fukushima_speed_sensitivity.png", dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved {OUTPUT_DIR / 'fig_fukushima_speed_sensitivity.png'}")

    # Figure 3: Loss surface (alpha vs beta at best kappa and best max_move_speed)
    if "max_move_speed" in grid_df.columns:
        best_speed = best["max_move_speed"]
        best_kappa_df = grid_df[(grid_df["kappa"] == best_kappa) & (grid_df["max_move_speed"] == best_speed)]
    else:
        best_kappa_df = grid_df[grid_df["kappa"] == best_kappa]
    if best_kappa_df.empty:
        best_kappa_df = grid_df
        best_kappa = grid_df["kappa"].iloc[0]

    pivot = best_kappa_df.pivot_table(index="alpha", columns="beta", values="loss", aggfunc="min")
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

    # Figure 3: Network map
    if INPUT_DIR.exists():
        loc_df = pd.read_csv(INPUT_DIR / "locations.csv")
        loc_df.columns = [c.lstrip("#") for c in loc_df.columns]
        loc_df = loc_df[loc_df.iloc[:, 0].astype(str).str.strip() != ""]
        routes_df = pd.read_csv(INPUT_DIR / "routes.csv")
        routes_df.columns = [c.lstrip("#") for c in routes_df.columns]
        routes_df = routes_df[routes_df["name1"].astype(str).str.strip() != ""]

        # Use gps_x=lon, gps_y=lat
        lon_col = "gps_x" if "gps_x" in loc_df.columns else "lon"
        lat_col = "gps_y" if "gps_y" in loc_df.columns else "lat"
        loc_df["lon"] = loc_df[lon_col]
        loc_df["lat"] = loc_df[lat_col]

        NPP_LAT, NPP_LON = 37.4213, 141.0329

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_aspect("equal")

        # Concentric circles at 10, 20, 30 km
        for r in [10, 20, 30]:
            theta = np.linspace(0, 2 * np.pi, 100)
            lat_c = NPP_LAT + (r / 111.0) * np.cos(theta)
            lon_c = NPP_LON + (r / (111.0 * np.cos(np.radians(NPP_LAT)))) * np.sin(theta)
            ax.plot(lon_c, lat_c, "k--", alpha=0.5, linewidth=1)

        # Routes: line width ~ 1/distance
        for _, row in routes_df.iterrows():
            n1, n2, d = row["name1"], row["name2"], row["distance"]
            loc1 = loc_df[loc_df["name"] == n1].iloc[0]
            loc2 = loc_df[loc_df["name"] == n2].iloc[0]
            lw = max(0.5, 20.0 / (d + 1))
            ax.plot([loc1["lon"], loc2["lon"]], [loc1["lat"], loc2["lat"]], "gray", linewidth=lw, alpha=0.7)

        # Locations: color by type
        for _, row in loc_df.iterrows():
            lt = row["location_type"]
            if "conflict" in str(lt).lower():
                color = "red"
            elif "camp" in str(lt).lower():
                color = "green"
            else:
                color = "blue"
            pop = row.get("pop/cap", row.get("population", 0))
            ax.scatter(row["lon"], row["lat"], c=color, s=80, zorder=5, edgecolors="black")
            ax.annotate(f"{row['name']}\n({pop:,.0f})", (row["lon"], row["lat"]), fontsize=7, ha="center")

        ax.scatter(NPP_LON, NPP_LAT, marker="*", s=400, c="black", zorder=10, edgecolors="white")
        ax.annotate("NPP", (NPP_LON, NPP_LAT), fontsize=9, ha="center", fontweight="bold")

        # Timeline inset: evacuation order steps
        ax_inset = fig.add_axes([0.15, 0.65, 0.25, 0.2])
        ax_inset.set_xlim(0, 36)
        ax_inset.set_ylim(0, 1)
        ax_inset.axvline(4, color="red", linestyle="--", alpha=0.7, label="3km (step 4)")
        ax_inset.axvline(8, color="orange", linestyle="--", alpha=0.7, label="10km (step 8)")
        ax_inset.axvline(14, color="blue", linestyle="--", alpha=0.7, label="20km (step 14)")
        ax_inset.set_xlabel("Timestep")
        ax_inset.set_title("Evacuation orders")
        ax_inset.legend(fontsize=6)

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("Fukushima 2011 evacuation network")
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "fig_fukushima_network.png", dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved {OUTPUT_DIR / 'fig_fukushima_network.png'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
