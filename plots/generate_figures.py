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

# NPP reference; other locations loaded from conflict_input (gps_x=lon, gps_y=lat)
NPP_LAT, NPP_LON = 37.421, 141.033
NPP_COORDS = (NPP_LAT, NPP_LON)
INPUT_DIR = PROJECT_ROOT / "conflict_input" / "fukushima_2011"

# Map extent (excludes Sendai, removes excess ocean)
LON_MIN, LON_MAX = 140.30, 141.20
LAT_MIN, LAT_MAX = 37.00, 37.90

# Label offsets (dlon, dlat in degrees). Coastal cluster → ocean (east); inland → west.
LABEL_OFFSETS = {
    # Coastal cluster — push into ocean (east) with leader lines, kept close to coast
    "Namie": (0.06, 0.03),
    "Futaba": (0.06, 0.01),
    "Okuma": (0.06, -0.02),
    "Tomioka": (0.06, -0.05),
    "Naraha": (0.05, -0.03),
    # Inland — push west/northwest (land side, no overlap)
    "Minamisoma": (-0.04, 0.03),
    "Iitate": (-0.06, 0.02),
    "Kawauchi": (-0.08, -0.02),
    # Destinations — already isolated, minimal offset
    "Fukushima City": (-0.04, 0.02),
    "Fukushima_City": (-0.04, 0.02),
    "Koriyama": (-0.04, 0.00),
    "Iwaki": (0.00, -0.03),
}
EXCLUDE_LOCATIONS = {"Sendai"}

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
    """Load Hayano 2013 Fig. 3 hourly data. Baseline = pre-earthquake (04:00 March 11)."""
    if not HAYANO_PATH.exists():
        return None
    df = pd.read_csv(HAYANO_PATH)
    df["datetime"] = pd.to_datetime(
        df["Date/Time"].apply(lambda s: f"2011-{s.strip()}"),
        format="%Y-%m/%d %H:%M",
        errors="coerce",
    )
    df = df.dropna(subset=["datetime"])
    df["hours_since_t0"] = (df["datetime"] - T0).dt.total_seconds() / 3600
    # Use pre-earthquake baseline (04:00 March 11, before earthquake at 14:46)
    baseline_target = pd.Timestamp("2011-03-11 04:00:00")
    baseline_row = df[df["datetime"] == baseline_target]
    if baseline_row.empty:
        baseline_row = df.iloc[[0]]
    for col in ["<5km", "5–10km", "10–15km", "15–20km"]:
        if col in df.columns:
            baseline = baseline_row[col].values[0]
            if baseline > 0:
                frac = df[col] / baseline
                df[f"frac_{col}"] = np.clip(frac, 0, 1)
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

    # T1: <5km fraction ≤ 0.40 at t=15h; T2: <5km fraction ≤ 0.10 at t=20h
    # T3: 15-20km fraction ≈ 0.52 at t=33h; T4: <20km total ≤ 0.05 at t=72h
    T_TARGETS = [
        (15, "frac_<5km", "T1", "#D55E00"),
        (20, "frac_<5km", "T2", "#D55E00"),
        (33, "frac_15–20km", "T3", "#009E73"),
        (72, "frac_<20km_combined", "T4", "#009E73"),
    ]

    def _model_at_h(traj_df, hours):
        """Interpolate model fraction at given hours."""
        h = traj_df["hours_since_t0"].values
        idx = np.searchsorted(h, hours)
        idx = np.clip(idx, 1, len(traj_df) - 1)
        lo, hi = traj_df.iloc[idx - 1], traj_df.iloc[idx]
        t_lo, t_hi = float(lo["hours_since_t0"]), float(hi["hours_since_t0"])
        w = (hours - t_lo) / (t_hi - t_lo) if t_hi > t_lo else 0
        return (1 - w) * lo + w * hi

    panels = [
        ("<5km", "frac_<5km", "0–5 km", [15, 20]),  # T1, T2
        ("5–10km", "frac_5–10km", "5–10 km", []),
        ("15–20km", "frac_15–20km", "15–20 km", [33, 72]),  # T3, T4
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (zone, frac_col, title, t_hours) in zip(axes, panels):
        if frac_col not in traj.columns:
            frac_col = f"frac_{zone}"
        usable = obs[~(obs["datetime"].between(OUTAGE_START, OUTAGE_END))]
        hayano_frac = np.clip(usable[frac_col].values, 0, 1)
        ax.errorbar(
            usable["hours_since_t0"],
            hayano_frac,
            yerr=0.2 * hayano_frac,
            fmt="o",
            color=PALETTE["data"],
            markersize=4,
            capsize=2,
            alpha=0.7,
        )
        model_frac = np.clip(traj[frac_col].values, 0, 1)
        ax.plot(
            traj["hours_since_t0"],
            model_frac,
            color=PALETTE["model"],
            linewidth=2,
            label="Model",
        )
        ax.axvspan(outage_start_h, outage_end_h, color="gray", alpha=0.3)
        for h, lab in [(13.3, "3km"), (15, "10km"), (27.6, "20km")]:
            ax.axvline(h, color="gray", linestyle="--", alpha=0.7)
        # T1–T4 vertical lines and model dots
        for t_h, t_frac_col, t_label, t_color in T_TARGETS:
            if t_h not in t_hours:
                continue
            if t_frac_col not in traj.columns:
                continue
            ax.axvline(t_h, color=t_color, linestyle="--", linewidth=1.2, alpha=0.8)
            row = _model_at_h(traj, t_h)
            val = np.clip(float(row[t_frac_col]), 0, 1)
            ax.scatter([t_h], [val], s=60, c=t_color, zorder=5, edgecolors="black")
            ax.annotate(
                t_label,
                (t_h, val),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                color=t_color,
                fontweight="bold",
            )
        ax.set_xlim(-5, 150)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Hours since earthquake")
        ax.set_ylabel("Fraction remaining")
        ax.set_title(title)
        ax.legend(loc="upper right", fontsize=8)
    fig.suptitle("Departure validation: Model vs Hayano 2013", fontsize=12)
    fig.text(
        0.5,
        0.01,
        "Baseline = pre-earthquake residential population (Hayano 2013, Fig. 3)",
        ha="center",
        fontsize=9,
        style="italic",
        color="#555555",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(OUTPUT_FUKUSHIMA / "F2_departure_validation.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F2: Saved F2_departure_validation.png")
    return True


def fig_f3_zone_ps2_timeseries():
    """F3: Zone-level P_S2 time series — main panel 0–50, inset 0–200."""
    zp_path = RESULTS_FUKUSHIMA / "zone_ps2_timeseries.csv"
    if not zp_path.exists():
        print("F3: Missing zone_ps2_timeseries.csv")
        return False

    df = pd.read_csv(zp_path)
    ZONE_STYLE = {
        "inner_3km": {"color": "#E69F00", "label": "Inner (<3 km)", "onset": 1},
        "zone_10km": {"color": "#009E73", "label": "10 km zone", "onset": 8},
        "zone_20km": {"color": "#CC79A7", "label": "20 km zone", "onset": 14},
    }

    # Build ps2_mean dict: zone -> (steps, mean_ps2)
    ps2_mean = {}
    steps_all = np.arange(0, max(df["step"].max() + 1, 201))
    for zone in ZONE_STYLE:
        sub = df[df["zone"] == zone]
        if sub.empty:
            continue
        sub = sub.sort_values("step")
        steps = sub["step"].values
        mean_ps2 = sub["mean_ps2"].values
        # Interpolate to full step range for inset
        mean_interp = np.interp(steps_all, steps, mean_ps2)
        ps2_mean[zone] = (steps_all, mean_interp)

    fig, ax_main = plt.subplots(figsize=(10, 5))
    ax_main.set_xlim(0, 50)
    ax_main.set_ylim(0, 1.0)

    for zone, style in ZONE_STYLE.items():
        if zone not in ps2_mean:
            continue
        steps, mean_ps2 = ps2_mean[zone]
        ax_main.plot(steps, mean_ps2, color=style["color"], linewidth=2.5, label=style["label"])
        ax_main.axvline(
            style["onset"],
            color=style["color"],
            linewidth=1.2,
            linestyle="--",
            alpha=0.8,
        )
        ax_main.annotate(
            style["label"].split()[0] + "\norder",
            xy=(style["onset"], 0.85),
            xytext=(style["onset"] + 2, 0.92),
            fontsize=8,
            color=style["color"],
            arrowprops=dict(arrowstyle="->", color=style["color"], lw=1.0),
        )

    ax_main.set_xlabel("Step (1 step = 2h)", fontsize=11)
    ax_main.set_ylabel("$P_{S2}$ (deliberation weight)", fontsize=11)
    ax_main.set_title("Zone-level $P_{S2}$: Sequential conflict suppression", fontsize=12)
    ax_main.legend(loc="upper right", fontsize=9)

    # Inset: long-run view steps 0–200
    ax_inset = ax_main.inset_axes([0.55, 0.15, 0.40, 0.35])
    for zone, style in ZONE_STYLE.items():
        if zone not in ps2_mean:
            continue
        steps, mean_ps2 = ps2_mean[zone]
        ax_inset.plot(steps, mean_ps2, color=style["color"], linewidth=1.2)
    ax_inset.set_xlim(0, 200)
    ax_inset.set_ylim(0, 1.0)
    ax_inset.set_xlabel("Step", fontsize=7)
    ax_inset.set_ylabel("$P_{S2}$", fontsize=7)
    ax_inset.tick_params(labelsize=7)
    ax_inset.set_title("Full run (200 steps)", fontsize=7)

    fig.tight_layout()
    fig.savefig(OUTPUT_FUKUSHIMA / "F3_zone_ps2_timeseries.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F3: Saved F3_zone_ps2_timeseries.png")
    return True


def fig_f4_spatial_snapshots():
    """F4: Spatial P_S2 snapshots at t=1, 8, 14, 50 with Cartopy basemap."""
    ah_path = RESULTS_FUKUSHIMA / "agent_history.csv"
    if not ah_path.exists():
        print("F4: Missing agent_history.csv")
        return False

    locs, pops = _load_fukushima_locations()
    if not locs:
        print("F4: Missing conflict_input/fukushima_2011/locations.csv")
        return False

    ah = pd.read_csv(ah_path)
    SNAPSHOT_STEPS = [1, 8, 14, 50]
    SNAPSHOT_LABELS = [
        "Step 1 (t=2h): Inner zone order",
        "Step 8 (t=16h): 10 km order",
        "Step 14 (t=28h): 20 km order",
        "Step 50 (t=100h): Late evacuation",
    ]

    for loc in ah["location"].unique():
        if loc and loc not in EXCLUDE_LOCATIONS and loc not in locs:
            row = ah[ah["location"] == loc].iloc[0]
            if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                locs[loc] = (float(row["lat"]), float(row["lon"]))
                pops[loc] = pops.get(loc, 0)

    use_cartopy = False
    tr = None
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        use_cartopy = True
        tr = ccrs.PlateCarree()
    except ImportError:
        pass

    if use_cartopy:
        fig, axes = plt.subplots(
            2, 2, figsize=(14, 12), subplot_kw={"projection": ccrs.PlateCarree()}
        )
        axes = axes.flatten()
        for ax in axes:
            ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND, facecolor="#e8e4dc", zorder=0)
            ax.add_feature(cfeature.OCEAN, facecolor="#b3d9ff", zorder=0)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8, zorder=2)
            ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5, zorder=2)
    else:
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        axes = axes.flatten()
        for ax in axes:
            ax.set_xlim(LON_MIN, LON_MAX)
            ax.set_ylim(LAT_MIN, LAT_MAX)
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")

    for ax, step, title in zip(axes, SNAPSHOT_STEPS, SNAPSHOT_LABELS):
        sub = ah[ah["step"] == step]
        if sub.empty:
            ax.set_title(title)
            continue
        loc_means = sub.groupby("location")["s2_weight"].mean()
        _draw_fukushima_map(ax, loc_means, step, locs, pops, use_cartopy, tr, add_colorbar=False)
        ax.set_title(title)
        if not use_cartopy:
            ax.set_aspect("equal")

    # Single shared colorbar to the right of the 2×2 grid
    fig.subplots_adjust(right=0.88)
    cbar_ax = fig.add_axes([0.91, 0.15, 0.02, 0.7])
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize
    ps2_cmap = matplotlib.colormaps["RdYlBu_r"]
    sm = ScalarMappable(cmap=ps2_cmap, norm=Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label("$P_{S2}$ (deliberation weight)", fontsize=11)
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.ax.tick_params(labelsize=8)

    fig.savefig(OUTPUT_FUKUSHIMA / "F4_spatial_snapshots.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F4: Saved F4_spatial_snapshots.png")
    return True


def fig_f5_loss_landscape():
    """F5: Calibration loss landscape. X=alpha, Y=beta.
    Shows how well different (α, β) fit the Hayano targets at best κ.
    Skipped when grid has < 4 points (run full calibration: python runscripts/run_fukushima.py).
    """
    from matplotlib.colors import Normalize

    grid_path = RESULTS_FUKUSHIMA / "grid_search.csv"
    if not grid_path.exists():
        print("F5: Missing grid_search.csv")
        return False

    df = pd.read_csv(grid_path)
    best = df.loc[df["loss"].idxmin()]
    best_kappa = best["kappa"]
    sub = df[df["kappa"] == best_kappa]
    pivot = sub.pivot_table(index="beta", columns="alpha", values="loss", aggfunc="min")
    if pivot.size < 4:
        print("F5: Skipped — grid has < 4 points. Run full calibration (no --quick) for loss landscape.")
        return False

    alphas = pivot.columns.values
    betas = pivot.index.values
    loss_values = pivot.values.flatten()
    best_loss = loss_values.min()

    # Normalize colormap to show variation: vmin=min, vmax=75th percentile
    vmin = loss_values.min()
    vmax = np.percentile(loss_values, 75)
    if vmax <= vmin:
        vmax = vmin + 0.01
    norm = Normalize(vmin=vmin, vmax=vmax)

    levels = [best_loss * x for x in [1.1, 1.25, 1.5, 2.0]]

    fig, ax = plt.subplots(figsize=(8, 6))
    xlo, xhi = alphas[0], alphas[-1]
    ylo, yhi = betas[0], betas[-1]
    if xlo == xhi:
        xlo, xhi = xlo - 0.5, xhi + 0.5
    if ylo == yhi:
        ylo, yhi = ylo - 0.5, yhi + 0.5
    im = ax.imshow(
        pivot.values,
        extent=[xlo, xhi, yhi, ylo],
        aspect="auto",
        cmap="viridis_r",
        norm=norm,
    )
    if pivot.size >= 4:
        ax.contour(alphas, betas, pivot.values, levels=levels, colors="white", linewidths=0.5)
    ax.plot(best["alpha"], best["beta"], "*", color="white", markersize=15, markeredgecolor="black")
    plt.colorbar(im, ax=ax, label="Calibration loss")
    ax.set_xlabel("$\\alpha$")
    ax.set_ylabel("$\\beta$")

    n_alpha = len(df["alpha"].unique())
    n_beta = len(df["beta"].unique())
    title = f"Calibration loss at $\\kappa$={best_kappa:.0f} (lower = better fit to Hayano)"
    if n_alpha < 4 or n_beta < 4:
        title += f"\n(sparse grid: {n_alpha}α × {n_beta}β — run full calibration for detail)"
    ax.set_title(title, fontsize=10)

    if vmax - vmin < 0.05:
        fig.text(
            0.5,
            0.01,
            f"Note: Loss range = {vmax - vmin:.3f}. "
            f"Flat landscape indicates weak α-identifiability at κ={best_kappa:.0f}. "
            f"β dominates calibration loss.",
            ha="center",
            fontsize=9,
            style="italic",
            color="#555555",
        )
        fig.tight_layout(rect=[0, 0.05, 1, 1])
    else:
        fig.tight_layout()

    ax.text(
        0.02,
        0.98,
        f"T3={best['T3_model']:.3f}",
        transform=ax.transAxes,
        fontsize=10,
        va="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )
    fig.savefig(OUTPUT_FUKUSHIMA / "F5_loss_landscape.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("F5: Saved F5_loss_landscape.png")
    return True


def _load_fukushima_locations():
    """Load locations from conflict_input. Returns (locs, pops).
    locs: dict name -> (lat, lon). pops: dict name -> population.
    Excludes Sendai (not part of evacuation network).
    """
    loc_path = INPUT_DIR / "locations.csv"
    if not loc_path.exists():
        return {}, {}
    df = pd.read_csv(loc_path)
    df.columns = [c.lstrip("#") for c in df.columns]
    locs, pops = {}, {}
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name or name in EXCLUDE_LOCATIONS:
            continue
        try:
            lon = float(row.get("gps_x", row.get("lon", 0)))
            lat = float(row.get("gps_y", row.get("lat", 0)))
            pop = int(float(row.get("pop/cap", row.get("pop", 1000))))
            locs[name] = (lat, lon)
            pops[name] = pop
        except (ValueError, TypeError):
            pass
    return locs, pops


def _draw_fukushima_map(ax, loc_means, step, locs, pops, use_cartopy, tr, add_colorbar=True):
    """Shared map drawing for F1 and F4. Call after ax has projection/extent set."""
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    scatter_kw = {"transform": tr} if tr is not None else {}
    plot_kw = {"transform": tr} if tr is not None else {}

    # Routes < 60 km only (no long-haul spider-web)
    routes_path = INPUT_DIR / "routes.csv"
    if routes_path.exists():
        routes_df = pd.read_csv(routes_path)
        routes_df.columns = [c.lstrip("#") for c in routes_df.columns]
        n1_col = "name1" if "name1" in routes_df.columns else routes_df.columns[0]
        n2_col = "name2" if "name2" in routes_df.columns else routes_df.columns[1]
        dist_col = "distance" if "distance" in routes_df.columns else routes_df.columns[2]
        for _, row in routes_df.iterrows():
            a, b = str(row[n1_col]).strip(), str(row[n2_col]).strip()
            dist = float(row.get(dist_col, 999))
            if dist >= 60 or a not in locs or b not in locs:
                continue
            lat1, lon1 = locs[a]
            lat2, lon2 = locs[b]
            ax.plot([lon1, lon2], [lat1, lat2], color="#cccccc", linewidth=0.4, alpha=0.3, zorder=1, **plot_kw)

    # NPP star (red, no label)
    ax.scatter(NPP_LON, NPP_LAT, marker="*", s=180, c="#c0392b", zorder=10, **scatter_kw)

    # Western semicircles (90° to 270°) with labels
    for radius_km in [3, 10, 20, 30]:
        radius_deg_lat = radius_km / 111.0
        radius_deg_lon = radius_km / (111.0 * np.cos(np.radians(NPP_LAT)))
        theta = np.linspace(90, 270, 200)
        lons = NPP_LON + radius_deg_lon * np.cos(np.radians(theta))
        lats = NPP_LAT + radius_deg_lat * np.sin(np.radians(theta))
        ax.plot(lons, lats, "--", color="#888888", linewidth=0.7, alpha=0.6, zorder=2, **plot_kw)
        label_lon = NPP_LON - radius_deg_lon - 0.02
        label_lat = NPP_LAT
        txt_kw = {"transform": tr} if tr is not None else {}
        ax.text(label_lon, label_lat, f"{radius_km} km", fontsize=7, color="#888888", ha="right", zorder=3, **txt_kw)

    # Nodes scaled by population
    POP_SCALE = 0.003
    center_lon, center_lat = 140.8, 37.45
    txt_kw = {"transform": tr} if tr is not None else {}
    for name, (lat, lon) in locs.items():
        mean_ps2 = loc_means.get(name, 0.5)
        pop = pops.get(name, 1000)
        node_size = np.clip(np.sqrt(pop) * POP_SCALE * 1000, 40, 300)
        ax.scatter(lon, lat, c=[(1 - mean_ps2, 0.6, mean_ps2)], s=node_size, edgecolors="black", zorder=5, **scatter_kw)
        if name in LABEL_OFFSETS:
            dlon, dlat = LABEL_OFFSETS[name]
            label_lon = lon + dlon
            label_lat = lat + dlat
            # Leader line for offset labels
            if abs(dlon) > 0.08 or abs(dlat) > 0.04:
                line_end_lon = label_lon - 0.01 * np.sign(dlon) if dlon != 0 else label_lon
                ax.plot(
                    [lon, line_end_lon],
                    [lat, label_lat],
                    color="#999999",
                    linewidth=0.5,
                    alpha=0.6,
                    zorder=3,
                    **plot_kw,
                )
            ax.text(
                label_lon,
                label_lat,
                name.replace("_", " "),
                fontsize=8,
                ha="center",
                va="center",
                zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.85),
                **txt_kw,
            )
        else:
            dx = lon - center_lon
            dy = lat - center_lat
            norm = max((dx**2 + dy**2) ** 0.5, 0.01)
            xytext = (24 * dx / norm, 24 * dy / norm)
            ax.annotate(
                name.replace("_", " "),
                (lon, lat),
                xytext=xytext,
                textcoords="offset points",
                fontsize=9,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.9),
            )

    # Colorbar for P_S2 (optional; F4 uses shared colorbar)
    if add_colorbar:
        ps2_cmap = matplotlib.colormaps["RdYlBu_r"]
        sm = ScalarMappable(cmap=ps2_cmap, norm=Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation="vertical", fraction=0.03, pad=0.02, shrink=0.6)
        cbar.set_label("P_S2 (deliberation weight)", fontsize=9)
        cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
        cbar.ax.tick_params(labelsize=8)

    ax.set_title(f"Fukushima evacuation — Step {step} (t={step*2}h)", fontsize=11, pad=6)


def fig_f1_map_animation():
    """F1: Geographic map with Natural Earth basemap and FLEE evacuation network."""
    ah_path = RESULTS_FUKUSHIMA / "agent_history.csv"
    if not ah_path.exists():
        print("F1: Missing agent_history.csv")
        return False

    locs, pops = _load_fukushima_locations()
    if not locs:
        print("F1: Missing conflict_input/fukushima_2011/locations.csv")
        return False

    ah = pd.read_csv(ah_path)
    use_cartopy = False
    tr = None
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        use_cartopy = True
        tr = ccrs.PlateCarree()
    except ImportError:
        print("F1: Install cartopy for geographic basemap (pip install cartopy)")

    for step in [1, 14]:
        sub = ah[ah["step"] == step]
        loc_means = sub.groupby("location")["s2_weight"].mean()
        if use_cartopy:
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND, facecolor="#e8e4dc", zorder=0)
            ax.add_feature(cfeature.OCEAN, facecolor="#b3d9ff", zorder=0)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8, zorder=2)
            ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5, zorder=2)
        else:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.set_xlim(LON_MIN, LON_MAX)
            ax.set_ylim(LAT_MIN, LAT_MAX)
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")

        _draw_fukushima_map(ax, loc_means, step, locs, pops, use_cartopy, tr)
        if not use_cartopy:
            ax.set_aspect("equal")
        fig.tight_layout()
        out_name = f"F1_map_frame_step{step}.png"
        fig.savefig(OUTPUT_FUKUSHIMA / out_name, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"F1: Saved {out_name}")
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
        model_frac = np.clip(traj["frac_15–20km"].values, 0, 1)
        ax.plot(traj["hours_since_t0"], model_frac, color=PALETTE["model"], linewidth=2)
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
