#!/usr/bin/env python3
"""
Generate full figure and animation set for team presentation.
Synthetic: S1-S4. Fukushima: F1-F5. Summary: F0.

Run from project root: python plots/generate_figures.py
Requires: Run runscripts/run_fukushima.py and synthetic/run_comparison_ring.py first.
"""

import csv
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_FUKUSHIMA = PROJECT_ROOT / "results" / "fukushima"
RESULTS_SYNTHETIC = PROJECT_ROOT / "results" / "synthetic"
SYNTHETIC_RING = PROJECT_ROOT / "synthetic" / "results" / "comparison_ring"
OUTPUT_SYNTHETIC = PROJECT_ROOT / "plots" / "output" / "synthetic"
OUTPUT_FUKUSHIMA = PROJECT_ROOT / "plots" / "output" / "fukushima"
OUTPUT_ROOT = PROJECT_ROOT / "plots" / "output"
HAYANO_PATH = PROJECT_ROOT / "data" / "observations" / "fukushima_2011" / "hayano_2013_fig3_hourly.csv"
T0 = pd.Timestamp("2011-03-11 14:46")
OUTAGE_START = pd.Timestamp("2011-03-13 06:00")
OUTAGE_END = pd.Timestamp("2011-03-14 12:00")
TIMESTEP_HOURS = 2

PALETTE = {
    "S1_dominant": "#E69F00",
    "S2_dominant": "#0072B2",
    "phase1": "#D55E00",
    "phase2": "#009E73",
    "baseline": "#CC79A7",
    "data": "#000000",
    "model": "#0072B2",
    "conflict": "#D55E00",
}

# Municipality coordinates (lat, lon) for Fukushima maps
LOCATIONS = {
    "Futaba": (37.438, 141.008),
    "Okuma": (37.402, 141.031),
    "Namie": (37.488, 141.004),
    "Tomioka": (37.349, 141.025),
    "Naraha": (37.283, 141.028),
    "Minamisoma": (37.641, 140.958),
    "Iitate": (37.580, 140.756),
    "Kawauchi": (37.327, 140.766),
    "Hirono": (37.201, 141.040),
    "Iwaki": (37.050, 140.887),
    "Koriyama": (37.401, 140.368),
    "Fukushima": (37.750, 140.468),
    "Fukushima_City": (37.761, 140.475),
    "Sendai": (38.269, 140.872),
    "NPP": (37.421, 141.033),
}

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def _ensure_dirs():
    OUTPUT_SYNTHETIC.mkdir(parents=True, exist_ok=True)
    OUTPUT_FUKUSHIMA.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


# =============================================================================
# SYNTHETIC FIGURES
# =============================================================================

def fig_s1_network_animation():
    """S1: Network animation - chain with P_S2 colored nodes."""
    ah_path = RESULTS_SYNTHETIC / "agent_history.csv"
    ps2_path = RESULTS_SYNTHETIC / "ps2_timeseries.csv"
    pb_path = SYNTHETIC_RING / "phase_boundaries.csv"
    if not ah_path.exists() or not ps2_path.exists() or not pb_path.exists():
        print("S1: Missing data. Run synthetic/run_comparison_ring.py first.")
        return False

    ah = pd.read_csv(ah_path)
    ps2 = pd.read_csv(ps2_path)
    pb = pd.read_csv(pb_path).iloc[0]
    tstar = int(pb["tstar"])
    tstarstar = int(pb["tstarstar"])
    mean_s2_t0 = float(pb["mean_s2_t0"])

    # Chain layout: L0 at 0, L1 at 1, ... L9 at 9
    chain_x = {f"L{i}": i for i in range(10)}
    chain_y = {f"L{i}": 0 for i in range(10)}
    # Link names like "L:L0:L1" - use startpoint
    for k in list(chain_x.keys()):
        for suffix in ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"]:
            if f"L:{k}:{suffix}" in ah["location"].values or f"L:{suffix}:{k}" in ah["location"].values:
                pass  # links use midpoint; we'll approximate
    # For link locations, use first part
    def loc_to_xy(loc):
        if pd.isna(loc) or loc == "":
            return 0, 0
        for i in range(10):
            if loc == f"L{i}":
                return chain_x[loc], chain_y[loc]
            if loc.startswith(f"L{i}:") or f":L{i}" in loc:
                return i, 0
        return 0, 0

    steps = sorted(ah["step"].unique())
    n_steps = len(steps)

    fig, (ax_net, ax_ts) = plt.subplots(1, 2, figsize=(12, 5))
    ax_net.set_aspect("equal")
    ax_ts.set_xlim(0, n_steps - 1)
    ax_ts.set_ylim(0, 1)
    ax_ts.set_xlabel("Step")
    ax_ts.set_ylabel("Population-mean $P_{S2}$")
    ax_ts.axhline(mean_s2_t0, color=PALETTE["baseline"], linestyle="--", alpha=0.7)
    ax_ts.axvspan(1, tstar, alpha=0.2, color=PALETTE["phase1"])
    ax_ts.axvspan(tstar, tstarstar, alpha=0.2, color=PALETTE["phase2"])
    ts_line, = ax_ts.plot([], [], color=PALETTE["model"], linewidth=2)
    ts_vline = ax_ts.axvline(0, color="gray", linestyle="-", alpha=0.8)

    node_circles = []
    node_texts = []
    for i in range(10):
        circ = ax_net.add_patch(plt.Circle((i, 0), 0.15, color=PALETTE["S1_dominant"], ec="black", zorder=5))
        node_circles.append(circ)
        txt = ax_net.text(i, 0, "0", ha="center", va="center", fontsize=8, zorder=6)
        node_texts.append(txt)
    ax_net.set_xlim(-0.5, 9.5)
    ax_net.set_ylim(-0.5, 0.5)
    ax_net.set_xlabel("Location (chain)")
    ax_net.set_xticks(range(10))
    ax_net.set_xticklabels([f"L{i}" for i in range(10)])

    def init():
        return []

    def animate(frame):
        step = steps[frame]
        step_df = ah[ah["step"] == step]
        # Mean P_S2 per location
        loc_means = step_df.groupby("location")["s2_weight"].mean()
        loc_counts = step_df.groupby("location").size()
        for i in range(10):
            loc = f"L{i}"
            mean_ps2 = loc_means.get(loc, 0.5)
            count = int(loc_counts.get(loc, 0))
            # Color: orange (0) -> blue (1)
            r = 1 - mean_ps2
            g = 0.6
            b = mean_ps2
            node_circles[i].set_facecolor((r * 0.9 + 0.1, g, b * 0.9 + 0.1))
            node_circles[i].set_edgecolor(PALETTE["conflict"] if i == 0 else "black")
            node_texts[i].set_text(str(count))
        # Time series
        sub = ps2[ps2["step"] <= step]
        if len(sub) > 0:
            ts_line.set_data(sub["step"].values, sub["mean_ps2"].values)
        ts_vline.set_xdata([frame])
        ax_net.set_title(f"Step {step} (t={step * 2}h)")
        return node_circles + node_texts + [ts_line, ts_vline]

    try:
        from matplotlib.animation import FuncAnimation
        anim = FuncAnimation(fig, animate, frames=n_steps, init_func=init, blit=False, interval=100)
        anim.save(OUTPUT_SYNTHETIC / "S1_network_animation.mp4", writer="ffmpeg", fps=10, dpi=150)
        print("S1: Saved S1_network_animation.mp4")
        try:
            anim.save(OUTPUT_SYNTHETIC / "S1_network_animation.gif", writer="pillow", fps=8, dpi=120)
            print("S1: Saved S1_network_animation.gif")
        except Exception as e2:
            print(f"S1: GIF skipped ({e2})")
    except Exception as e:
        print(f"S1: Could not save MP4 ({e}). Trying GIF...")
        try:
            anim = FuncAnimation(fig, animate, frames=n_steps, init_func=init, blit=False, interval=125)
            anim.save(OUTPUT_SYNTHETIC / "S1_network_animation.gif", writer="pillow", fps=8, dpi=120)
            print("S1: Saved S1_network_animation.gif")
        except Exception as e2:
            print(f"S1: Animation failed: {e2}")
    plt.close()
    return True


def fig_s2_ps2_timeseries():
    """S2: P_S2 time series with phase markers."""
    ps2_path = RESULTS_SYNTHETIC / "ps2_timeseries.csv"
    pb_path = SYNTHETIC_RING / "phase_boundaries.csv"
    if not ps2_path.exists() or not pb_path.exists():
        print("S2: Missing data.")
        return False

    ps2 = pd.read_csv(ps2_path)
    pb = pd.read_csv(pb_path).iloc[0]
    tstar = int(pb["tstar"])
    tstarstar = int(pb["tstarstar"])
    mean_s2_t0 = float(pb["mean_s2_t0"])

    fig, ax = plt.subplots(figsize=(8, 5))
    steps = ps2["step"].values
    mean_s2 = ps2["mean_ps2"].values
    std_s2 = ps2["std_ps2"].values
    ax.fill_between(steps, mean_s2 - std_s2, mean_s2 + std_s2, color=PALETTE["model"], alpha=0.3)
    ax.plot(steps, mean_s2, color=PALETTE["model"], linewidth=2)
    ax.axvline(0, color=PALETTE["conflict"], linestyle="--", linewidth=1.5, label="Crisis onset")
    ax.axvline(tstar, color=PALETTE["phase1"], linewidth=2, label="$t^*$ (Phase 1 end)")
    ax.axvline(tstarstar, color=PALETTE["phase2"], linewidth=2, label="$t^{**}$ (Phase 2 plateau)")
    ax.axhline(mean_s2_t0, color=PALETTE["baseline"], linestyle=":", linewidth=1.5, label="Pre-crisis baseline ($\\bar{\\Psi}$)")
    ax.text(1, 0.95, "Phase 1: S1-dominated", color=PALETTE["phase1"], fontsize=10)
    ax.text((tstar + tstarstar) / 2, 0.95, "Phase 2: Differentiated", color=PALETTE["phase2"], fontsize=10)
    tau_star = (tstar - 1) * 360 / 100 if tstar > 1 else 0  # v=360, d*=100
    ax.text(0.98, 0.02, f"$\\tau^*$={tau_star:.2f}\n$\\alpha$=2, $\\beta$=4, $\\kappa$=5",
            transform=ax.transAxes, fontsize=9, va="bottom", ha="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    ax.set_xlim(0, len(steps) - 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Timestep")
    ax.set_ylabel("$P_{S2}$")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT_SYNTHETIC / "S2_ps2_timeseries.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("S2: Saved S2_ps2_timeseries.png")
    return True


def fig_s3_ps2_distribution():
    """S3: P_S2 distribution violins at t=0, t*, t**."""
    ah_path = RESULTS_SYNTHETIC / "agent_history.csv"
    pb_path = SYNTHETIC_RING / "phase_boundaries.csv"
    if not ah_path.exists() or not pb_path.exists():
        print("S3: Missing data.")
        return False

    ah = pd.read_csv(ah_path)
    pb = pd.read_csv(pb_path).iloc[0]
    tstar = int(pb["tstar"])
    tstarstar = int(pb["tstarstar"])

    moments = [
        (0, "Pre-crisis\n($P_{S2}=\\Psi$)"),
        (tstar, "Phase 1 end\n($\\Omega$ suppression)"),
        (tstarstar, "Phase 2 plateau\n($\\Psi$ heterogeneity)"),
    ]
    data = []
    labels = []
    for t, label in moments:
        sub = ah[ah["step"] == t]["s2_weight"]
        if len(sub) > 0:
            data.append(sub.values)
            labels.append(label)

    if not data:
        print("S3: No data at key moments.")
        return False

    fig, ax = plt.subplots(figsize=(8, 5))
    parts = ax.violinplot(data, positions=range(len(data)), showmeans=True, showmedians=True)
    for pc in parts["bodies"]:
        pc.set_facecolor(PALETTE["model"])
        pc.set_alpha(0.7)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel("$P_{S2}$")
    ax.set_xlabel("Simulation phase")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(OUTPUT_SYNTHETIC / "S3_ps2_distribution.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("S3: Saved S3_ps2_distribution.png")
    return True


def fig_s4_tau_sensitivity():
    """S4: tau* sensitivity heatmap over alpha, beta."""
    grid_path = RESULTS_FUKUSHIMA / "grid_search.csv"
    if not grid_path.exists():
        print("S4: Skipped - no grid data.")
        return False

    df = pd.read_csv(grid_path)
    best = df.loc[df["loss"].idxmin()]
    best_kappa = best["kappa"]
    best_alpha, best_beta = best["alpha"], best["beta"]
    sub = df[df["kappa"] == best_kappa]
    pivot = sub.pivot_table(index="alpha", columns="beta", values="tau_star", aggfunc="min")
    alphas = pivot.index.values
    betas = pivot.columns.values
    xlo, xhi = betas[0], betas[-1]
    ylo, yhi = alphas[0], alphas[-1]
    if xlo == xhi:
        xlo, xhi = xlo - 0.5, xhi + 0.5
    if ylo == yhi:
        ylo, yhi = ylo - 0.5, yhi + 0.5

    fig, ax = plt.subplots(figsize=(8, 6))
    vals = np.ma.masked_outside(pivot.values, 0.1, 10)
    vals = np.ma.filled(vals, np.nan)
    im = ax.imshow(vals, extent=[xlo, xhi, yhi, ylo],
                   aspect="auto", cmap="viridis", vmin=0.1, vmax=10)
    if pivot.size >= 4:
        ax.contour(betas, alphas, pivot.values, levels=[0.5, 1.0, 2.0, 3.0], colors="white", linewidths=0.5)
    ax.plot(best_beta, best_alpha, "*", color="white", markersize=15, markeredgecolor="black")
    plt.colorbar(im, ax=ax, label="$\\tau^*$ (dimensionless Phase 1 duration)")
    ax.set_xlabel("$\\beta$")
    ax.set_ylabel("$\\alpha$")
    ax.set_title("$\\tau^*$ sensitivity ($\\alpha$ vs $\\beta$ at best $\\kappa$)")
    fig.tight_layout()
    fig.savefig(OUTPUT_SYNTHETIC / "S4_tau_sensitivity.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("S4: Saved S4_tau_sensitivity.png")
    return True


# =============================================================================
# FUKUSHIMA FIGURES
# =============================================================================

def _load_hayano():
    if not HAYANO_PATH.exists():
        return None
    df = pd.read_csv(HAYANO_PATH)
    df["datetime"] = pd.to_datetime(df["Date/Time"].apply(lambda s: f"2011-{s.strip()}"), format="%Y-%m/%d %H:%M", errors="coerce")
    df = df.dropna(subset=["datetime"])
    df["hours_since_t0"] = (df["datetime"] - T0).dt.total_seconds() / 3600
    baseline = df[df["datetime"] == pd.Timestamp("2011-03-11 04:00")].iloc[0]
    for col in ["<5km", "5–10km", "10–15km", "15–20km"]:
        if col in df.columns and col in baseline and baseline[col] > 0:
            df[f"frac_{col}"] = df[col] / baseline[col]
    return df


def fig_f2_departure_validation():
    """F2: Departure curves vs Hayano - three distance bands."""
    traj_path = RESULTS_FUKUSHIMA / "best_fit_trajectory.csv"
    if not traj_path.exists():
        print("F2: Missing best_fit_trajectory.csv")
        return False
    obs = _load_hayano()
    if obs is None:
        print("F2: Missing Hayano data.")
        return False

    traj = pd.read_csv(traj_path)
    traj["hours_since_t0"] = traj["step"] * TIMESTEP_HOURS
    outage_start_h = (OUTAGE_START - T0).total_seconds() / 3600
    outage_end_h = (OUTAGE_END - T0).total_seconds() / 3600

    panels = [
        ("<5km", "frac_<5km", "0–5 km"),
        ("5–10km", "frac_5–10km", "5–10 km"),
        ("15–20km", "frac_15–20km", "15–20 km"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (zone, frac_col, title) in zip(axes, panels):
        if frac_col not in traj.columns:
            frac_col = f"frac_{zone}"
        usable = obs[~(obs["datetime"].between(OUTAGE_START, OUTAGE_END))]
        ax.errorbar(usable["hours_since_t0"], usable[frac_col], yerr=0.2 * usable[frac_col],
                    fmt="o", color=PALETTE["data"], markersize=4, capsize=2, alpha=0.7)
        ax.plot(traj["hours_since_t0"], traj[frac_col], color=PALETTE["model"], linewidth=2, label="Model")
        ax.axvspan(outage_start_h, outage_end_h, color="gray", alpha=0.3)
        for h, lab in [(13.3, "3km"), (15, "10km"), (27.6, "20km")]:
            ax.axvline(h, color="gray", linestyle="--", alpha=0.7)
        ax.set_xlim(-5, 150)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Hours since earthquake")
        ax.set_ylabel("Fraction remaining")
        ax.set_title(title)
        ax.legend(loc="upper right", fontsize=8)
    fig.suptitle("Departure validation: Model vs Hayano 2013", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUTPUT_FUKUSHIMA / "F2_departure_validation.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F2: Saved F2_departure_validation.png")
    return True


def fig_f3_zone_ps2_timeseries():
    """F3: Zone-level P_S2 time series."""
    zp_path = RESULTS_FUKUSHIMA / "zone_ps2_timeseries.csv"
    if not zp_path.exists():
        print("F3: Missing zone_ps2_timeseries.csv")
        return False

    df = pd.read_csv(zp_path)
    zones = ["inner_3km", "zone_10km", "zone_20km"]
    colors = [PALETTE["S1_dominant"], "#009E73", "#CC79A7"]
    onsets = {"inner_3km": 1, "zone_10km": 8, "zone_20km": 14}

    fig, ax = plt.subplots(figsize=(10, 5))
    for zone, color in zip(zones, colors):
        sub = df[df["zone"] == zone]
        if sub.empty:
            continue
        steps = sub["step"].values
        mean_ps2 = sub["mean_ps2"].values
        std_ps2 = sub["std_ps2"].fillna(0).values
        ax.plot(steps, mean_ps2, color=color, linewidth=2, label=zone)
        ax.fill_between(steps, mean_ps2 - 0.5 * std_ps2, mean_ps2 + 0.5 * std_ps2, color=color, alpha=0.2)
        ax.axvline(onsets[zone], color=color, linestyle="--", alpha=0.7)
    ax.set_xlabel("Step")
    ax.set_ylabel("$P_{S2}$")
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right")
    ax.text(0.98, 0.02, "Multi-wave structure: each order suppresses population-mean $P_{S2}$",
            transform=ax.transAxes, fontsize=9, va="bottom", ha="right")
    fig.tight_layout()
    fig.savefig(OUTPUT_FUKUSHIMA / "F3_zone_ps2_timeseries.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F3: Saved F3_zone_ps2_timeseries.png")
    return True


def fig_f4_spatial_snapshots():
    """F4: Spatial P_S2 snapshots at t=1, 8, 14, 50."""
    ah_path = RESULTS_FUKUSHIMA / "agent_history.csv"
    if not ah_path.exists():
        print("F4: Missing agent_history.csv")
        return False

    ah = pd.read_csv(ah_path)
    steps_plot = [1, 8, 14, 50]
    titles = ["t=1: Inner zone order", "t=8: 10 km order", "t=14: 20 km order", "t=50: Late evacuation"]

    # Build loc -> (lat, lon) from data for locations not in LOCATIONS
    loc_coords = dict(LOCATIONS)
    for loc in ah["location"].unique():
        if loc and loc not in loc_coords:
            row = ah[ah["location"] == loc].iloc[0]
            if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                loc_coords[loc] = (float(row["lat"]), float(row["lon"]))

    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    axes = axes.flatten()
    npp = LOCATIONS["NPP"]

    for ax, step, title in zip(axes, steps_plot, titles):
        sub = ah[ah["step"] == step]
        if sub.empty:
            ax.set_title(title)
            continue
        loc_means = sub.groupby("location")["s2_weight"].mean()
        ax.scatter(npp[1], npp[0], marker="*", s=300, c="black", zorder=10)
        ax.annotate("NPP", (npp[1], npp[0]), fontsize=9, ha="center", fontweight="bold")
        for loc in loc_means.index:
            if loc == "NPP" or loc not in loc_coords:
                continue
            lat, lon = loc_coords[loc]
            mean_ps2 = loc_means[loc]
            ax.scatter(lon, lat, c=[(1 - mean_ps2, 0.6, mean_ps2)], s=100, edgecolors="black", zorder=5)
            ax.annotate(loc.replace("_", " "), (lon, lat), fontsize=7, ha="center")
        for r in [3, 10, 20, 30]:
            theta = np.linspace(0, 2 * np.pi, 50)
            lat_c = npp[0] + (r / 111) * np.cos(theta)
            lon_c = npp[1] + (r / (111 * np.cos(np.radians(npp[0])))) * np.sin(theta)
            ax.plot(lon_c, lat_c, "k--", alpha=0.3, linewidth=0.5)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(f"Step {step}: {title}")
        ax.set_aspect("equal")

    fig.tight_layout()
    fig.savefig(OUTPUT_FUKUSHIMA / "F4_spatial_snapshots.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F4: Saved F4_spatial_snapshots.png")
    return True


def fig_f5_loss_landscape():
    """F5: Calibration loss landscape. X=alpha, Y=beta."""
    grid_path = RESULTS_FUKUSHIMA / "grid_search.csv"
    if not grid_path.exists():
        print("F5: Missing grid_search.csv")
        return False

    df = pd.read_csv(grid_path)
    best = df.loc[df["loss"].idxmin()]
    best_kappa = best["kappa"]
    sub = df[df["kappa"] == best_kappa]
    pivot = sub.pivot_table(index="beta", columns="alpha", values="loss", aggfunc="min")
    alphas = pivot.columns.values
    betas = pivot.index.values
    best_loss = pivot.min().min()
    levels = [best_loss * x for x in [1.1, 1.25, 1.5, 2.0]]

    fig, ax = plt.subplots(figsize=(8, 6))
    xlo, xhi = alphas[0], alphas[-1]
    ylo, yhi = betas[0], betas[-1]
    if xlo == xhi:
        xlo, xhi = xlo - 0.5, xhi + 0.5
    if ylo == yhi:
        ylo, yhi = ylo - 0.5, yhi + 0.5
    im = ax.imshow(pivot.values, extent=[xlo, xhi, yhi, ylo],
                   aspect="auto", cmap="viridis_r")
    if pivot.size >= 4:
        ax.contour(alphas, betas, pivot.values, levels=levels, colors="white", linewidths=0.5)
    ax.plot(best["alpha"], best["beta"], "*", color="white", markersize=15, markeredgecolor="black")
    plt.colorbar(im, ax=ax, label="Calibration loss")
    ax.set_xlabel("$\\alpha$")
    ax.set_ylabel("$\\beta$")
    ax.set_title(f"Loss landscape at $\\kappa$={best_kappa:.0f}")
    ax.text(0.02, 0.98, f"T3={best['T3_model']:.3f}", transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    fig.tight_layout()
    fig.savefig(OUTPUT_FUKUSHIMA / "F5_loss_landscape.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F5: Saved F5_loss_landscape.png")
    return True


def fig_f1_map_animation():
    """F1: Geographic map animation (simplified - single frame if animation fails)."""
    ah_path = RESULTS_FUKUSHIMA / "agent_history.csv"
    if not ah_path.exists():
        print("F1: Missing agent_history.csv")
        return False
    # Save a static frame as fallback; full animation would require many frames
    ah = pd.read_csv(ah_path)
    step = 14  # Representative frame
    sub = ah[ah["step"] == step]
    loc_means = sub.groupby("location")["s2_weight"].mean()
    npp = LOCATIONS["NPP"]
    fig, ax = plt.subplots(figsize=(10, 8))
    for name, (lat, lon) in LOCATIONS.items():
        if name == "NPP":
            ax.scatter(lon, lat, marker="*", s=400, c="black", zorder=10)
            ax.annotate("NPP", (lon, lat), fontsize=10, ha="center", fontweight="bold")
            continue
        mean_ps2 = loc_means.get(name, 0.5)
        ax.scatter(lon, lat, c=[(1 - mean_ps2, 0.6, mean_ps2)], s=150, edgecolors="black", zorder=5)
        ax.annotate(name, (lon, lat), fontsize=8, ha="center")
    for r in [3, 10, 20, 30]:
        theta = np.linspace(0, 2 * np.pi, 50)
        lat_c = npp[0] + (r / 111) * np.cos(theta)
        lon_c = npp[1] + (r / (111 * np.cos(np.radians(npp[0])))) * np.sin(theta)
        ax.plot(lon_c, lat_c, "k--", alpha=0.5, linewidth=1)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Fukushima evacuation network — Step {step} (t={step*2}h)")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(OUTPUT_FUKUSHIMA / "F1_map_frame.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F1: Saved F1_map_frame.png (static; full animation requires ffmpeg)")
    return True


# =============================================================================
# SUMMARY F0
# =============================================================================

def fig_f0_summary():
    """F0: 2x2 summary for slide deck."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # A: S2 compact
    ps2_path = RESULTS_SYNTHETIC / "ps2_timeseries.csv"
    pb_path = SYNTHETIC_RING / "phase_boundaries.csv"
    if ps2_path.exists() and pb_path.exists():
        ps2 = pd.read_csv(ps2_path)
        pb = pd.read_csv(pb_path).iloc[0]
        ax = axes[0, 0]
        ax.plot(ps2["step"], ps2["mean_ps2"], color=PALETTE["model"], linewidth=2)
        ax.axvline(int(pb["tstar"]), color=PALETTE["phase1"], linestyle="--")
        ax.axvline(int(pb["tstarstar"]), color=PALETTE["phase2"], linestyle="--")
        ax.set_xlabel("Step")
        ax.set_ylabel("$P_{S2}$")
        ax.set_title("A. Synthetic $P_{S2}$ time series")
        ax.set_ylim(0, 1)

    # B: S3 compact
    ah_path = RESULTS_SYNTHETIC / "agent_history.csv"
    if ah_path.exists() and pb_path.exists():
        ah = pd.read_csv(ah_path)
        pb = pd.read_csv(pb_path).iloc[0]
        tstar, tstarstar = int(pb["tstar"]), int(pb["tstarstar"])
        data = [ah[ah["step"] == t]["s2_weight"].values for t in [0, tstar, tstarstar]]
        ax = axes[0, 1]
        ax.violinplot(data, positions=[0, 1, 2], showmeans=True)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["Pre-crisis", "Phase 1 end", "Phase 2"])
        ax.set_ylabel("$P_{S2}$")
        ax.set_title("B. $P_{S2}$ distribution")
        ax.set_ylim(0, 1)

    # C: F2 15-20km panel only
    traj_path = RESULTS_FUKUSHIMA / "best_fit_trajectory.csv"
    obs = _load_hayano()
    if traj_path.exists() and obs is not None:
        traj = pd.read_csv(traj_path)
        traj["hours_since_t0"] = traj["step"] * TIMESTEP_HOURS
        ax = axes[1, 0]
        usable = obs[~(obs["datetime"].between(OUTAGE_START, OUTAGE_END))]
        ax.errorbar(usable["hours_since_t0"], usable["frac_15–20km"], yerr=0.2 * usable["frac_15–20km"],
                    fmt="o", color=PALETTE["data"], markersize=3, capsize=1, alpha=0.7)
        ax.plot(traj["hours_since_t0"], traj["frac_15–20km"], color=PALETTE["model"], linewidth=2)
        ax.set_xlabel("Hours since earthquake")
        ax.set_ylabel("Fraction remaining")
        ax.set_title("C. 15–20 km departure validation")
        ax.set_xlim(-5, 80)
        ax.set_ylim(0, 1.05)

    # D: F3
    zp_path = RESULTS_FUKUSHIMA / "zone_ps2_timeseries.csv"
    if zp_path.exists():
        df = pd.read_csv(zp_path)
        ax = axes[1, 1]
        for zone, color in [("inner_3km", PALETTE["S1_dominant"]), ("zone_10km", "#009E73"), ("zone_20km", "#CC79A7")]:
            sub = df[df["zone"] == zone]
            if not sub.empty:
                ax.plot(sub["step"], sub["mean_ps2"], color=color, linewidth=2, label=zone)
        ax.set_xlabel("Step")
        ax.set_ylabel("$P_{S2}$")
        ax.set_title("D. Zone-level $P_{S2}$ time series")
        ax.legend(loc="upper right", fontsize=8)
        ax.set_ylim(0, 1)

    fig.suptitle("FLEE Dual-Process Model: Synthetic Validation and Fukushima Calibration", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT_ROOT / "F0_summary_2x2.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F0: Saved F0_summary_2x2.png")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    _ensure_dirs()
    count = 0
    # Synthetic
    if fig_s2_ps2_timeseries():
        count += 1
    if fig_s3_ps2_distribution():
        count += 1
    if fig_s4_tau_sensitivity():
        count += 1
    if fig_s1_network_animation():
        count += 1
    # Fukushima
    if fig_f2_departure_validation():
        count += 1
    if fig_f3_zone_ps2_timeseries():
        count += 1
    if fig_f4_spatial_snapshots():
        count += 1
    if fig_f5_loss_landscape():
        count += 1
    if fig_f1_map_animation():
        count += 1
    # Summary
    if fig_f0_summary():
        count += 1
    print(f"\nGenerated {count} figures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
