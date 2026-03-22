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

# Paths (1 timestep = 1 hour)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "results" / "synthetic" / "linear"
OUT_DIR = PROJECT_ROOT / "figures" / "synthetic"

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


def load_data():
    """Load summary and agents CSVs."""
    summary_path = DATA_DIR / "summary_all_modes.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Run runscripts/run_synthetic.py first. Expected: {summary_path}")

    summary = pd.read_csv(summary_path)
    agents_dfs = []
    for mode in MODE_ORDER:
        p = DATA_DIR / f"agents_{mode}.csv"
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
    """FIG 2: Mean P_S2 vs time, switch and blend only, ±1 SD shaded."""
    figwidth = setup_science_style(3.5)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.7))

    for mode in ["switch", "blend"]:
        sub = summary[summary["decision_mode"] == mode]
        if sub.empty:
            continue
        agg = sub.groupby("timestep")["mean_s2_weight"].agg(["mean", "std"]).reset_index()
        agg["std"] = agg["std"].fillna(0)
        t = agg["timestep"].values
        m = agg["mean"].values
        s = agg["std"].values
        ax.fill_between(t, m - s, m + s, alpha=0.3, color=PALETTE[mode])
        ax.plot(t, m, color=PALETTE[mode], label=mode, lw=1.5)

    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Mean P_S2")
    ax.set_xlim(0, summary["timestep"].max() if not summary.empty else 72)
    ax.set_ylim(0, 1.05)
    ax.legend()
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


def create_animation(agents, summary, out_dir):
    """Create anim_linear_blend.mp4 and .gif: agent positions by node, color=P_S2."""
    blend = agents[agents["mode"] == "blend"] if not agents.empty else pd.DataFrame()
    if blend.empty:
        print("  Skipped animation (no blend data)")
        return

    # Node order: source, town_00, town_01, town_02, town_03, camp
    node_order = ["source", "town_00", "town_01", "town_02", "town_03", "camp"]
    times = sorted(blend["timestep"].unique())
    if not times:
        return

    setup_science_style(3.5)
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.set_xlim(-0.5, len(node_order) - 0.5)
    ax.set_ylim(-50, 550)
    ax.set_xticks(range(len(node_order)))
    ax.set_xticklabels(node_order, rotation=45)
    ax.set_ylabel("Agent index (stacked)")
    ax.set_title("Agent positions (color = P_S2)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Inset: mean P_S2 over time
    ax_inset = fig.add_axes([0.15, 0.65, 0.25, 0.22])
    sub = summary[summary["decision_mode"] == "blend"]
    if not sub.empty:
        by_t = sub.groupby("timestep")["mean_s2_weight"].mean()
        ax_inset.plot(by_t.index, by_t.values, color=PALETTE["blend"], lw=1)
    ax_inset.set_xlabel("Time (h)")
    ax_inset.set_ylabel("Mean P_S2")
    ax_inset.set_xlim(0, max(times))
    ax_inset.set_ylim(0, 1)
    ax_inset.spines["top"].set_visible(False)
    ax_inset.spines["right"].set_visible(False)

    scat = ax.scatter([], [], s=2, c=[], cmap="viridis", vmin=0, vmax=1)

    def init():
        scat.set_offsets(np.empty((0, 2)))
        scat.set_array(np.array([]))
        return [scat]

    def update(frame):
        t = times[min(frame, len(times) - 1)]
        sub = blend[(blend["timestep"] == t) & (blend["run_id"] == 0)]
        if sub.empty:
            sub = blend[(blend["timestep"] == t)]
        xs, ys, colors = [], [], []
        for node_idx, node in enumerate(node_order):
            at_node = sub[sub["location"] == node]
            for i, (_, row) in enumerate(at_node.iterrows()):
                xs.append(node_idx + 0.02 * np.random.randn())
                ys.append(i * 2)
                colors.append(row["s2_weight"] if "s2_weight" in row else 0)
        if xs:
            scat.set_offsets(np.c_[xs, ys])
            scat.set_array(np.array(colors))
        else:
            scat.set_offsets(np.empty((0, 2)))
            scat.set_array(np.array([]))
        ax.set_title(f"t = {t} h")
        return [scat]

    from matplotlib.animation import FuncAnimation, PillowWriter
    anim = FuncAnimation(fig, update, frames=len(times), init_func=init, interval=100)
    try:
        anim.save(out_dir / "anim_linear_blend.mp4", writer="ffmpeg", fps=6)
        print("  Saved anim_linear_blend.mp4")
    except Exception:
        pass
    try:
        anim.save(out_dir / "anim_linear_blend.gif", writer=PillowWriter(fps=6))
        print("  Saved anim_linear_blend.gif")
    except Exception:
        pass
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_science_style(3.5)

    try:
        summary, agents = load_data()
    except FileNotFoundError as e:
        print(str(e))
        return 1

    print("Creating figures in", OUT_DIR)
    fig1_departure_curves(summary, OUT_DIR)
    fig2_ps2_timeseries(summary, OUT_DIR)
    fig3_first_departure_violins(agents, OUT_DIR)
    fig4_distance_vs_time(summary, OUT_DIR)
    create_table1_stats(summary, agents, OUT_DIR)
    create_animation(agents, summary, OUT_DIR)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
