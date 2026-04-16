#!/usr/bin/env python3
"""
Create journal-quality figures for synthetic linear experiments.
Reads results/synthetic/linear/summary_all_modes.csv and agents_*.csv.

Science style: 3.5" or 7" width, Arial 8pt, 300 DPI, PNG+SVG.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Standardized output layout: output/results/synthetic/<topology>, output/figures/synthetic/<topology>
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = PROJECT_ROOT / "output"
RESULTS_BASE = OUTPUT_ROOT / "results" / "synthetic"
FIGURES_BASE = OUTPUT_ROOT / "figures" / "synthetic"

TOPOLOGIES = ["linear", "ring", "star", "fully_connected"]

# Color palette
PALETTE = {
    "original": "#888780",
    "s1_only": "#378ADD",
    "switch": "#BA7517",
    "blend": "#1D9E75",
}

MODE_ORDER = ["original", "s1_only", "switch", "blend"]

# Parameters for param box
PARAMS = {
    "alpha": 2.0,
    "beta": 2.0,
    "kappa": 5.0,
    "n_agents": 500,
    "n_runs": 10,
}


def setup_science_style(figwidth=3.5):
    """Apply Science-style figure settings."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.5,
    })
    return figwidth


def _results_dir(topology: str, schedule: str = "static") -> Path:
    """Return the results directory for a topology + schedule combination."""
    if schedule == "static":
        return RESULTS_BASE / topology
    return RESULTS_BASE / f"{topology}_{schedule}"


def load_data(topology: str, schedule: str = "static"):
    """Load summary and agents CSVs for given topology and schedule."""
    data_dir = _results_dir(topology, schedule)
    summary_path = data_dir / "summary_all_modes.csv"
    if not summary_path.exists():
        raise FileNotFoundError(
            f"Run runscripts/run_synthetic.py --topology {topology} first. Expected: {summary_path}"
        )

    summary = pd.read_csv(summary_path)
    agents_dfs = []
    for mode in MODE_ORDER:
        p = data_dir / f"agents_{mode}.csv"
        if p.exists():
            df = pd.read_csv(p)
            df["mode"] = mode
            agents_dfs.append(df)
    agents = pd.concat(agents_dfs, ignore_index=True) if agents_dfs else pd.DataFrame()

    return summary, agents


def add_param_box(ax, x=0.98, y=0.98):
    """Add parameter annotation box in top-right."""
    lines = [
        f"α={PARAMS['alpha']}, β={PARAMS['beta']}, κ={PARAMS['kappa']}",
        f"N_agents={PARAMS['n_agents']}, N_runs={PARAMS['n_runs']}",
    ]
    text = "\n".join(lines)
    ax.annotate(
        text,
        xy=(x, y),
        xycoords="axes fraction",
        fontsize=6,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.9),
    )


def _moved_mask(series):
    """Boolean mask for moved column (handles bool or string from CSV)."""
    if series.dtype == bool:
        return series == True  # noqa: E712
    return series.astype(str).str.lower().isin(("true", "1"))


def compute_ci(values, confidence=0.95):
    """Return (mean, lower, upper) for 95% CI."""
    n = len(values)
    if n < 2:
        return np.mean(values), np.mean(values), np.mean(values)
    mean = np.mean(values)
    sem = np.std(values, ddof=1) / np.sqrt(n)
    h = sem * stats.t.ppf((1 + confidence) / 2, n - 1)
    return mean, mean - h, mean + h


def fig1_departure_curves(summary, out_dir):
    """FIG 1: Cumulative % departed vs time (0–72 h), 4 lines with 95% CI bands, dashed at t=6 and t=24."""
    figwidth = setup_science_style(3.5)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.7))

    summary_sub = summary[summary["timestep"] <= 72]
    for mode in MODE_ORDER:
        sub = summary_sub[summary_sub["decision_mode"] == mode]
        if sub.empty:
            continue
        times = []
        means = []
        cis_lo = []
        cis_hi = []
        for t in range(73):
            row = sub[sub["timestep"] == t]
            if row.empty:
                times.append(t)
                means.append(np.nan)
                cis_lo.append(np.nan)
                cis_hi.append(np.nan)
            else:
                vals = row["pct_departed"].values
                m, lo, hi = compute_ci(vals)
                times.append(t)
                means.append(m)
                cis_lo.append(lo)
                cis_hi.append(hi)
        times = np.array(times)
        means = np.array(means)
        cis_lo = np.array(cis_lo)
        cis_hi = np.array(cis_hi)
        valid = ~np.isnan(means)
        if valid.any():
            ax.fill_between(times[valid], cis_lo[valid], cis_hi[valid], alpha=0.25, color=PALETTE[mode])
            ax.plot(times[valid], means[valid], color=PALETTE[mode], label=mode.replace("_", " "), lw=1.5)

    ax.axvline(6, color="gray", linestyle="--", lw=0.8, alpha=0.7)
    ax.axvline(24, color="gray", linestyle="--", lw=0.8, alpha=0.7)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Cumulative % departed")
    ax.set_xlim(0, 72)
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    add_param_box(ax)
    fig.tight_layout()
    for ext in ["png", "svg"]:
        fig.savefig(out_dir / f"fig1_departure_curves.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved fig1_departure_curves.png, .svg")


def fig2_ps2_timeseries(summary, out_dir):
    """FIG 2: Mean P_S2 vs time, switch and blend.

    If *mean_s2_weight_active* column exists (excludes camp agents),
    plot it as the primary solid line; dashed line shows all-agents mean.
    """
    figwidth = setup_science_style(3.5)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.7))
    has_active = "mean_s2_weight_active" in summary.columns

    for mode in ["switch", "blend"]:
        sub = summary[summary["decision_mode"] == mode]
        if sub.empty:
            continue
        col = "mean_s2_weight_active" if has_active else "mean_s2_weight"
        agg = sub.groupby("timestep")[col].agg(["mean", "std"]).reset_index()
        agg["std"] = agg["std"].fillna(0)
        t = agg["timestep"].values
        m = agg["mean"].values
        s = agg["std"].values
        ax.fill_between(t, m - s, m + s, alpha=0.2, color=PALETTE[mode])
        label = f"{mode} (active)" if has_active else mode
        ax.plot(t, m, color=PALETTE[mode], label=label, lw=1.5)

        if has_active:
            agg_all = sub.groupby("timestep")["mean_s2_weight"].agg(["mean"]).reset_index()
            ax.plot(agg_all["timestep"].values, agg_all["mean"].values,
                    color=PALETTE[mode], ls="--", lw=0.8, alpha=0.5,
                    label=f"{mode} (all)")

    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Mean P_S2")
    ax.set_xlim(0, summary["timestep"].max() if not summary.empty else 72)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=6)
    ax.grid(True, alpha=0.3)
    add_param_box(ax)
    fig.tight_layout()
    for ext in ["png", "svg"]:
        fig.savefig(out_dir / f"fig2_ps2_timeseries.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved fig2_ps2_timeseries.png, .svg")


def fig3_first_departure_violins(agents, out_dir):
    """FIG 3: Violin plots of first-departure timestep per mode."""
    if agents.empty:
        print("  Skipping fig3 (no agents data)")
        return

    # First departure = first timestep when moved==True (location != source)
    first_dep = []
    for (run_id, mode), g in agents.groupby(["run_id", "mode"]):
        # Per agent: min timestep where moved==True
        for agent_id, ag in g.groupby("agent_id"):
            moved = ag[_moved_mask(ag["moved"])]
            if not moved.empty:
                first_t = moved["timestep"].min()
                first_dep.append({"run_id": run_id, "mode": mode, "agent_id": agent_id, "first_departure": first_t})
    if not first_dep:
        print("  Skipping fig3 (no departure events)")
        return

    df = pd.DataFrame(first_dep)

    figwidth = setup_science_style(3.5)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.7))

    positions = []
    violins = []
    for i, mode in enumerate(MODE_ORDER):
        sub = df[df["mode"] == mode]
        if sub.empty:
            continue
        parts = ax.violinplot(
            [sub["first_departure"].values],
            positions=[i],
            widths=0.7,
            showmeans=True,
            showmedians=True,
        )
        for pc in parts["bodies"]:
            pc.set_facecolor(PALETTE[mode])
            pc.set_alpha(0.7)
        positions.append(i)
        violins.append(mode)

    ax.set_xticks(positions)
    ax.set_xticklabels([m.replace("_", " ") for m in violins])
    ax.set_ylabel("First-departure timestep (hours)")
    ax.set_xlabel("Decision mode")
    ax.grid(True, alpha=0.3, axis="y")
    add_param_box(ax)
    fig.tight_layout()
    for ext in ["png", "svg"]:
        fig.savefig(out_dir / f"fig3_first_departure_violins.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved fig3_first_departure_violins.png, .svg")


def fig4_distance_vs_time(summary, out_dir):
    """FIG 4: Mean distance from source vs time, 4 lines with 95% CI."""
    figwidth = setup_science_style(3.5)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.7))

    for mode in MODE_ORDER:
        sub = summary[summary["decision_mode"] == mode]
        if sub.empty:
            continue
        times = []
        means = []
        cis_lo = []
        cis_hi = []
        for t in sub["timestep"].unique():
            row = sub[sub["timestep"] == t]
            vals = row["mean_distance_km"].values
            m, lo, hi = compute_ci(vals)
            times.append(t)
            means.append(m)
            cis_lo.append(lo)
            cis_hi.append(hi)
        times = np.array(times)
        means = np.array(means)
        cis_lo = np.array(cis_lo)
        cis_hi = np.array(cis_hi)
        ax.fill_between(times, cis_lo, cis_hi, alpha=0.25, color=PALETTE[mode])
        ax.plot(times, means, color=PALETTE[mode], label=mode.replace("_", " "), lw=1.5)

    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Mean distance from source (km)")
    ax.set_xlim(0, summary["timestep"].max() if not summary.empty else 72)
    ax.set_ylim(0, None)
    ax.legend()
    ax.grid(True, alpha=0.3)
    add_param_box(ax)
    fig.tight_layout()
    for ext in ["png", "svg"]:
        fig.savefig(out_dir / f"fig4_distance_vs_time.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved fig4_distance_vs_time.png, .svg")


def _get_first_departures(agents):
    """Extract first-departure timestep per agent (first timestep when moved==True)."""
    first_dep = []
    for (run_id, mode), g in agents.groupby(["run_id", "mode"]):
        for agent_id, ag in g.groupby("agent_id"):
            moved = ag[_moved_mask(ag["moved"])]
            if not moved.empty:
                first_dep.append({"mode": mode, "first_departure": moved["timestep"].min()})
    return pd.DataFrame(first_dep) if first_dep else pd.DataFrame(columns=["mode", "first_departure"])


def create_table1_stats(summary, agents, out_dir):
    """Create table1_stats.csv with Mean dep. time, SD, 50% dep. by, 90% dep. by, KS tests, variance ratio."""
    rows = []

    # Per-mode stats from summary (pct_departed over time) + first-departure from agents
    df_fd = _get_first_departures(agents) if not agents.empty else pd.DataFrame()

    for mode in MODE_ORDER:
        row = {"mode": mode}

        # 50% and 90% departed by (from summary)
        sub_sum = summary[summary["decision_mode"] == mode]
        if not sub_sum.empty:
            agg = sub_sum.groupby("timestep")["pct_departed"].mean().reset_index()
            p50_row = agg[agg["pct_departed"] >= 50]
            p90_row = agg[agg["pct_departed"] >= 90]
            row["p50_departed_by_h"] = float(p50_row["timestep"].min()) if not p50_row.empty else np.nan
            row["p90_departed_by_h"] = float(p90_row["timestep"].min()) if not p90_row.empty else np.nan
        else:
            row["p50_departed_by_h"] = np.nan
            row["p90_departed_by_h"] = np.nan

        # Mean/SD first-departure time from agents
        if not df_fd.empty:
            sub_fd = df_fd[df_fd["mode"] == mode]
            if not sub_fd.empty:
                row["mean_dep_time_h"] = float(sub_fd["first_departure"].mean())
                row["sd_dep_time_h"] = float(sub_fd["first_departure"].std())
            else:
                row["mean_dep_time_h"] = np.nan
                row["sd_dep_time_h"] = np.nan
        else:
            row["mean_dep_time_h"] = np.nan
            row["sd_dep_time_h"] = np.nan

        rows.append(row)

    table = pd.DataFrame(rows)

    # KS tests and variance ratio
    ks_original_vs_s1 = np.nan
    ks_switch_vs_blend = np.nan
    var_ratio = np.nan

    if not df_fd.empty:
        for (a, b) in [("original", "s1_only"), ("switch", "blend")]:
            va = df_fd[df_fd["mode"] == a]["first_departure"].values
            vb = df_fd[df_fd["mode"] == b]["first_departure"].values
            if len(va) > 0 and len(vb) > 0:
                stat, pval = stats.ks_2samp(va, vb)
                if (a, b) == ("original", "s1_only"):
                    ks_original_vs_s1 = pval
                else:
                    ks_switch_vs_blend = pval

        switch_std = table[table["mode"] == "switch"]["sd_dep_time_h"].values
        blend_std = table[table["mode"] == "blend"]["sd_dep_time_h"].values
        if len(switch_std) and len(blend_std) and blend_std[0] > 0:
            var_ratio = float(switch_std[0] / blend_std[0])

    # Reorder columns: mean_dep_time_h, sd_dep_time_h, p50, p90, then add KS and var_ratio columns
    col_order = ["mode", "mean_dep_time_h", "sd_dep_time_h", "p50_departed_by_h", "p90_departed_by_h"]
    table = table[col_order]
    table["KS_original_vs_s1_only_pvalue"] = ks_original_vs_s1
    table["KS_switch_vs_blend_pvalue"] = ks_switch_vs_blend
    table["variance_ratio_std_switch_over_std_blend"] = var_ratio

    table.to_csv(out_dir / "table1_stats.csv", index=False)
    print("  Saved table1_stats.csv")


def _load_map_data(results_dir: Path) -> tuple:
    """Load coord_map (name->(x,y)), edge segments, and loc_info for map visualization."""
    loc_path = results_dir / "input_csv" / "locations.csv"
    route_path = results_dir / "input_csv" / "routes.csv"
    cols = ["name", "region", "country", "gps_x", "gps_y", "location_type", "conflict_date", "pop/cap"]
    coord_map = {}
    loc_info = {}
    if loc_path.exists():
        try:
            df = pd.read_csv(loc_path, comment="#", header=None, names=cols)
            for _, row in df.iterrows():
                name = str(row["name"]).strip('"')
                x, y = float(row["gps_x"]), float(row["gps_y"])
                coord_map[name] = (x, y)
                loc_type = str(row.get("location_type", "town")).lower()
                loc_info[name] = {"x": x, "y": y, "type": "conflict" if "conflict" in loc_type else ("camp" if "camp" in loc_type else "town")}
        except Exception:
            pass

    segments = []
    if route_path.exists():
        try:
            rt = pd.read_csv(route_path, comment="#", header=None, names=["name1", "name2", "distance", "forced_redirection"])
            for _, row in rt.iterrows():
                n1 = str(row["name1"]).strip('"') if hasattr(row["name1"], "strip") else str(row["name1"])
                n2 = str(row["name2"]).strip('"') if hasattr(row["name2"], "strip") else str(row["name2"])
                if n1 in coord_map and n2 in coord_map:
                    segments.append([coord_map[n1], coord_map[n2]])
        except Exception:
            pass

    return coord_map, segments, loc_info


def create_animation(agents, summary, out_dir, topology: str, results_dir: Path):
    """Create anim_<topology>_blend.mp4 and .gif: map-based network with agents at GPS coords, color=P_S2."""
    blend = agents[agents["mode"] == "blend"] if not agents.empty else pd.DataFrame()
    if blend.empty:
        print("  Skipped animation (no blend data)")
        return

    coord_map, segments, loc_info = _load_map_data(results_dir)
    if not coord_map:
        print("  Skipped animation (no locations)")
        return

    times = sorted(blend["timestep"].unique())
    if not times:
        return

    rng = np.random.default_rng(42)
    jitter = 2.0

    setup_science_style(3.5)
    from matplotlib.collections import LineCollection
    from matplotlib.animation import FuncAnimation, PillowWriter

    fig, ax = plt.subplots(figsize=(10, 8))

    # Draw network edges
    if segments:
        lc = LineCollection(segments, colors="lightgray", linewidths=1.2, zorder=0)
        ax.add_collection(lc)

    # Draw nodes by type: conflict=star, camp=square, town=circle (with updatable counters)
    node_texts = {}
    for name, info in loc_info.items():
        x, y = info["x"], info["y"]
        t = info["type"]
        if t == "conflict":
            ax.scatter(x, y, s=400, c="#D35400", marker="*", alpha=0.9, zorder=1,
                       edgecolors="#873600", linewidths=1.5)
            node_texts[name] = ax.text(x, y + 18, f"{name}\n(0)", ha="center", fontsize=9,
                                       fontweight="bold", bbox=dict(boxstyle="round,pad=0.2",
                                       facecolor="#F5B7B1", edgecolor="#873600", alpha=0.9), zorder=10)
        elif t == "camp":
            ax.scatter(x, y, s=300, c="#27AE60", marker="s", alpha=0.8, zorder=1,
                       edgecolors="#1E8449", linewidths=1.5)
            node_texts[name] = ax.text(x, y + 18, f"{name}\n(0)", ha="center", fontsize=9,
                                       fontweight="bold", bbox=dict(boxstyle="round,pad=0.2",
                                       facecolor="#D5F5E3", edgecolor="#1E8449", alpha=0.9), zorder=10)
        else:
            ax.scatter(x, y, s=80, c="#95a5a6", marker="o", alpha=0.6, zorder=1,
                       edgecolors="#7f8c8d", linewidths=1)
            node_texts[name] = ax.text(x, y + 12, "(0)", ha="center", fontsize=8, alpha=0.8, zorder=10)

    scat = ax.scatter([], [], s=25, c=[], cmap="viridis", vmin=0, vmax=1, alpha=0.85, zorder=2)
    title = ax.text(0.5, 0.98, "", transform=ax.transAxes, ha="center", fontsize=12, fontweight="bold")
    subtitle = ax.text(0.5, 0.94, "", transform=ax.transAxes, ha="center", fontsize=10)

    xs_all = [c[0] for c in coord_map.values()]
    ys_all = [c[1] for c in coord_map.values()]
    margin = max(25, 0.1 * (max(xs_all) - min(xs_all)) if xs_all else 25)
    ax.set_xlim(min(xs_all) - margin, max(xs_all) + margin)
    ax.set_ylim(min(ys_all) - margin, max(ys_all) + margin)
    ax.set_aspect("equal")
    ax.set_xlabel("x (km)")
    ax.set_ylabel("y (km)")
    plt.colorbar(scat, ax=ax, label="P_S2")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    def init():
        scat.set_offsets(np.empty((0, 2)))
        scat.set_array(np.array([]))
        for name, txt in node_texts.items():
            txt.set_text(f"{name}\n(0)" if loc_info[name]["type"] != "town" else "(0)")
        title.set_text(f"{topology} — t=0")
        subtitle.set_text("")
        return [scat]

    def update(frame):
        t = times[min(frame, len(times) - 1)]
        sub = blend[(blend["timestep"] == t) & (blend["run_id"] == 0)]
        if sub.empty:
            sub = blend[(blend["timestep"] == t)]
        loc_counts = sub["location"].value_counts() if not sub.empty else pd.Series(dtype=int)
        for name, txt in node_texts.items():
            cnt = int(loc_counts.get(name, 0))
            if loc_info[name]["type"] == "town":
                txt.set_text(f"({cnt})")
            else:
                txt.set_text(f"{name}\n({cnt})")
        coords, colors = [], []
        for _, row in sub.iterrows():
            loc = row.get("location")
            if pd.isna(loc) or str(loc) == "nan" or loc not in coord_map:
                continue
            x, y = coord_map[loc]
            if jitter > 0:
                x += rng.uniform(-jitter, jitter)
                y += rng.uniform(-jitter, jitter)
            coords.append([x, y])
            colors.append(row.get("s2_weight", 0.5))
        if coords:
            scat.set_offsets(np.array(coords))
            scat.set_array(np.array(colors))
        else:
            scat.set_offsets(np.empty((0, 2)))
            scat.set_array(np.array([]))

        mean_s2 = sub["s2_weight"].mean() if "s2_weight" in sub.columns and not sub.empty else 0
        n_dep = 0
        if "moved" in sub.columns:
            m = sub["moved"]
            if m.dtype == bool:
                n_dep = (m == True).sum()  # noqa: E712
            else:
                n_dep = m.astype(str).str.lower().isin(("true", "1")).sum()
        title.set_text(f"{topology} topology — t={t} h")
        subtitle.set_text(f"Mean P_S2: {mean_s2:.2f} | Departed: {n_dep}/{len(sub)}")
        return [scat]

    anim = FuncAnimation(fig, update, frames=len(times), init_func=init, interval=100)
    stem = f"anim_{topology}_blend"
    try:
        anim.save(out_dir / f"{stem}.mp4", writer="ffmpeg", fps=6)
        print(f"  Saved {stem}.mp4")
    except Exception:
        pass
    try:
        anim.save(out_dir / f"{stem}.gif", writer=PillowWriter(fps=6))
        print(f"  Saved {stem}.gif")
    except Exception:
        pass
    plt.close(fig)


def _get_conflict_intensity(schedule, t):
    """Return conflict intensity at timestep *t* for a named schedule."""
    if schedule == "static":
        return 1.0 if t >= 1 else 0.0
    elif schedule == "pulse":
        if t < 1:
            return 0.0
        return 1.0 if t <= 12 else 0.2
    elif schedule == "escalate":
        if t < 1:
            return 0.0
        if t <= 7:
            return 0.3
        return 1.0 if t <= 19 else 0.1
    return 0.0


SCHEDULE_COLORS = {"static": "#888780", "pulse": "#378ADD", "escalate": "#1D9E75"}


def fig5_schedule_comparison(topology, out_dir):
    """Fig 5: P_S2 timeseries for static/pulse/escalate on one topology (blend mode)."""
    figwidth = setup_science_style(7.0)
    fig, ax1 = plt.subplots(figsize=(figwidth, figwidth * 0.45))
    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)

    max_t = 0
    found_any = False
    for schedule in ("static", "pulse", "escalate"):
        try:
            summary, _ = load_data(topology, schedule)
        except FileNotFoundError:
            continue
        blend = summary[summary["decision_mode"] == "blend"]
        if blend.empty:
            continue
        found_any = True
        col = "mean_s2_weight_active" if "mean_s2_weight_active" in summary.columns else "mean_s2_weight"
        agg = blend.groupby("timestep")[col].agg(["mean", "std"]).reset_index()
        agg["std"] = agg["std"].fillna(0)
        t = agg["timestep"].values
        m = agg["mean"].values
        s = agg["std"].values
        max_t = max(max_t, int(t.max()))
        color = SCHEDULE_COLORS[schedule]
        ax1.fill_between(t, m - s, m + s, alpha=0.2, color=color)
        ax1.plot(t, m, color=color, label=f"P_S2 ({schedule})", lw=1.5)

        conflict_t = np.arange(0, int(t.max()) + 1)
        conflict_i = [_get_conflict_intensity(schedule, int(tt)) for tt in conflict_t]
        ax2.plot(conflict_t, conflict_i, "--", color=color, alpha=0.5, lw=0.8)

    if not found_any:
        plt.close(fig)
        print("  Skipping fig5 (no schedule data found)")
        return

    ax1.set_xlabel("Time (hours)")
    ax1.set_ylabel("Mean P_S2 (blend mode)")
    ax2.set_ylabel("Conflict intensity (dashed)")
    ax1.set_xlim(0, max_t)
    ax1.set_ylim(0, 0.6)
    ax2.set_ylim(0, 1.2)
    ax1.legend(loc="upper left", fontsize=7)
    ax1.grid(True, alpha=0.3)
    add_param_box(ax1)
    fig.tight_layout()
    for ext in ["png", "svg"]:
        fig.savefig(out_dir / f"fig5_schedule_comparison.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved fig5_schedule_comparison.png, .svg")


def process_topology(topology: str, schedule: str = "static") -> int:
    """Generate figures and animation for one topology + schedule."""
    if schedule == "static":
        out_dir = FIGURES_BASE / topology
    else:
        out_dir = FIGURES_BASE / f"{topology}_{schedule}"
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_science_style(3.5)

    try:
        summary, agents = load_data(topology, schedule)
    except FileNotFoundError as e:
        print(str(e))
        return 1

    results_dir = _results_dir(topology, schedule)
    print(f"Creating figures for {topology} ({schedule}) in {out_dir}")
    fig1_departure_curves(summary, out_dir)
    fig2_ps2_timeseries(summary, out_dir)
    fig3_first_departure_violins(agents, out_dir)
    fig4_distance_vs_time(summary, out_dir)
    create_table1_stats(summary, agents, out_dir)
    create_animation(agents, summary, out_dir, topology, results_dir)

    # Fig 5 only makes sense in the base topology dir (compares across schedules)
    if schedule != "static":
        base_out = FIGURES_BASE / topology
        base_out.mkdir(parents=True, exist_ok=True)
        fig5_schedule_comparison(topology, base_out)

    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate figures for synthetic experiments")
    parser.add_argument("--topology", default="linear",
                        help="Topology to process (or 'all' for all)")
    parser.add_argument("--schedule", default="static",
                        choices=["static", "pulse", "escalate"],
                        help="Conflict schedule (affects result directory)")
    args = parser.parse_args()

    topologies = TOPOLOGIES if args.topology == "all" else [args.topology]
    if args.topology != "all" and args.topology not in TOPOLOGIES:
        print(f"Unknown topology: {args.topology}. Use one of {TOPOLOGIES} or 'all'")
        return 1

    for topo in topologies:
        if process_topology(topo, args.schedule) != 0:
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
