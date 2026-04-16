#!/usr/bin/env python3
"""
Day 3: First Fukushima run — zone-level P_S2, starting parameters.
Runs all four decision modes on the real Fukushima geography.
Parameters NOT calibrated (α=1.0, β=2.0, κ=5.0).
"""

import argparse
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from flee import flee
from flee import InputGeography
from flee.SimulationSettings import SimulationSettings
from flee.decision_engine import DecisionEngine

MODE_ORDER = ["original", "s1_only", "switch", "blend"]
PALETTE = {"original": "#888780", "s1_only": "#888780",
           "switch": "#BA7517", "blend": "#1D9E75"}
LINESTYLE = {"original": "-", "s1_only": "--", "switch": "-", "blend": "-"}

ZONES = {
    "inner": ["okuma", "futaba"],
    "mid":   ["namie", "tomioka", "naraha", "kawauchi", "minamisoma_south"],
    "outer": ["iitate", "minamisoma_north", "tamura", "hirono", "iwaki_north"],
}
ZONE_COLORS = {"inner": "#D35400", "mid": "#E67E22", "outer": "#2E86C1"}

CAMP_NAMES = {"koriyama", "fukushima_city", "iwaki_city"}


def setup_science_style(figwidth=3.5):
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7,
        "figure.dpi": 150, "savefig.dpi": 300,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.5,
    })
    return figwidth


def loc_to_zone(name):
    for zone, names in ZONES.items():
        if name in names:
            return zone
    if name in CAMP_NAMES:
        return "camp"
    return "unknown"


def load_config(input_dir):
    yml_path = Path(input_dir) / "simsetting.yml"
    if yml_path.exists():
        SimulationSettings.ReadFromYML(str(yml_path))
    else:
        for p in ["flee/simsetting.yml", "tests/empty.yml"]:
            if (REPO_ROOT / p).exists():
                SimulationSettings.ReadFromYML(str(REPO_ROOT / p))
                break

    # Override AFTER ReadFromYML — confirmed fix-sequence from Day 1
    # Hayano 2013: ~78% cleared by day 4 → effective per-step rate ~0.5
    SimulationSettings.move_rules["ConflictMoveChance"] = 0.5
    # Shimazaki 2012: ~20 km/h avg speed × 10h travel/day = 200 km/day
    SimulationSettings.move_rules["MaxMoveSpeed"] = 200
    SimulationSettings.move_rules["DefaultMoveChance"] = 0.3
    SimulationSettings.move_rules["CampMoveChance"] = 0.0
    SimulationSettings.move_rules["ConflictWeight"] = 0.01
    SimulationSettings.move_rules["AwarenessLevel"] = 1
    SimulationSettings.move_rules["FixedRoutes"] = False
    SimulationSettings.move_rules["PruningThreshold"] = 1.0
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.spawn_rules["conflict_driven_spawning"] = False
    SimulationSettings.spawn_rules["TakeFromPopulation"] = False
    SimulationSettings.log_levels["agent"] = 1  # enable distance_travelled tracking
    SimulationSettings.log_levels["init"] = 0


def distribute_agents_by_pop(e, lm, n_total, seed):
    """Place agents proportional to node population among non-camp nodes."""
    rng = np.random.default_rng(seed)

    spawn = {name: loc for name, loc in lm.items()
             if not getattr(loc, "camp", False)}
    pops = {}
    for name, loc in spawn.items():
        pop = getattr(loc, "pop", 0)
        if pop is None or pop == "" or pop == 0:
            pop = 1000
        pops[name] = int(pop)

    total_pop = sum(pops.values())
    counts = {}
    assigned = 0
    sorted_names = sorted(pops.keys(), key=lambda n: pops[n], reverse=True)
    for name in sorted_names[:-1]:
        c = max(1, round(n_total * pops[name] / total_pop))
        counts[name] = c
        assigned += c
    counts[sorted_names[-1]] = max(1, n_total - assigned)

    agents_added = []
    for name in sorted(counts.keys()):
        loc = lm[name]
        n = counts[name]
        exp_indices = rng.beta(2, 5, size=n)
        for exp_idx in exp_indices:
            e.addAgent(location=loc, attributes={})
            a = e.agents[-1]
            a.experience_index = float(exp_idx)
            agents_added.append(a)

    # Summary
    print(f"  Distributed {len(agents_added)} agents across {len(counts)} nodes:")
    for zone_name in ["inner", "mid", "outer"]:
        zone_locs = ZONES[zone_name]
        zone_count = sum(counts.get(n, 0) for n in zone_locs)
        zone_exp = [a.experience_index for a in agents_added
                    if getattr(a.location, "name", "") in zone_locs]
        mean_exp = np.mean(zone_exp) if zone_exp else 0
        print(f"    {zone_name}: {zone_count} agents, mean x={mean_exp:.3f}")
    camp_count = sum(1 for a in e.agents if getattr(a.location, "name", "") in CAMP_NAMES)
    print(f"    camp: {camp_count} agents (should be 0)")

    return agents_added


def run_one(input_dir, mode, n_agents, n_steps, alpha, beta, kappa, seed):
    """Run one simulation, return per-timestep agent data."""
    load_config(input_dir)
    SimulationSettings.ConflictInputFile = str(Path(input_dir) / "conflicts.csv")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    SimulationSettings.move_rules["decision_mode"] = mode
    SimulationSettings.move_rules["s1s2_model_params"] = {
        "alpha": alpha, "beta": beta, "kappa": kappa,
    }
    SimulationSettings.move_rules["decision_engine"] = DecisionEngine.create(
        mode,
        {"s1s2_model_params": SimulationSettings.move_rules["s1s2_model_params"]},
    )
    SimulationSettings.move_rules["s2_weight_override"] = None

    random.seed(seed)
    np.random.seed(seed)

    e = flee.Ecosystem()
    ig = InputGeography.InputGeography()
    ig.ReadLocationsFromCSV(str(Path(input_dir) / "locations.csv"))
    ig.ReadLinksFromCSV(str(Path(input_dir) / "routes.csv"))
    ig.ReadClosuresFromCSV(str(Path(input_dir) / "closures.csv"))
    if Path(SimulationSettings.ConflictInputFile).exists():
        ig.ReadConflictInputCSV(SimulationSettings.ConflictInputFile)
    e, lm = ig.StoreInputGeographyInEcosystem(e)

    agents_added = distribute_agents_by_pop(e, lm, n_agents, seed)

    # Verify critical overrides survived ReadFromYML + StoreInputGeography
    mms = SimulationSettings.move_rules["MaxMoveSpeed"]
    cmc = SimulationSettings.move_rules["ConflictMoveChance"]
    dmc = SimulationSettings.move_rules["DefaultMoveChance"]
    print(f"  [verify] MaxMoveSpeed={mms}, ConflictMoveChance={cmc}, DefaultMoveChance={dmc}")

    # Record initial zone for each agent (before any evolve)
    initial_zone = {}
    for aid, a in enumerate(e.agents):
        loc = a.location
        ep = getattr(loc, "endpoint", loc)
        loc_name = getattr(ep, "name", str(loc))
        initial_zone[aid] = loc_to_zone(loc_name)

    agents_data = []
    arrival_records = []
    arrived_at_camp = set()

    for t in range(n_steps + 1):
        if t > 0:
            ig.AddNewConflictZones(e, t)
            if hasattr(ig, "conflicts"):
                for cname, cvals in ig.conflicts.items():
                    if t < len(cvals):
                        cur, prev = cvals[t], cvals[t - 1]
                        if prev > 1e-6 and cur > 1e-6 and abs(cur - prev) > 1e-6:
                            e.set_conflict_intensity(cname, cur)
        e.evolve()

        for aid, a in enumerate(e.agents):
            loc = a.location
            if loc is None:
                continue
            ep = getattr(loc, "endpoint", loc)
            loc_name = getattr(ep, "name", str(loc))
            loc_type = getattr(ep, "location_type", "town")
            s2 = getattr(a, "s2_activation_prob", 0.0)
            moved = getattr(a, "places_travelled", 0) > 1
            zone = loc_to_zone(loc_name)
            conflict = max(0.0, getattr(ep, "conflict", 0.0))

            # Record first arrival at camp with FLEE's internal distance_travelled
            if zone == "camp" and aid not in arrived_at_camp:
                arrived_at_camp.add(aid)
                path_km = getattr(a, "distance_travelled", 0.0)
                arrival_records.append({
                    "agent_id": aid,
                    "initial_zone": initial_zone.get(aid, "unknown"),
                    "camp_node": loc_name,
                    "arrival_timestep": t,
                    "path_length_km": float(path_km),
                    "experience_x": getattr(a, "experience_index", 0.0),
                    "decision_mode": mode,
                })

            agents_data.append({
                "timestep": t, "agent_id": aid, "location": loc_name,
                "location_type": loc_type, "zone": zone,
                "initial_zone": initial_zone.get(aid, zone),
                "s2_weight": s2, "moved": moved,
                "conflict_intensity": conflict,
                "decision_mode": mode,
            })

    arrival_df = pd.DataFrame(arrival_records) if arrival_records else pd.DataFrame()
    return pd.DataFrame(agents_data), lm, arrival_df


# ── Figures ──

def fig_F1_departure_by_zone(all_agents, out_dir, n_steps):
    """F1: 4-panel departure curves by zone, one panel per mode."""
    figwidth = setup_science_style(7.0)
    fig, axes = plt.subplots(2, 2, figsize=(figwidth, figwidth * 0.7), sharex=True, sharey=True)
    fig.suptitle("Cumulative Departure Fraction by Zone\n"
                 "(α=1.0, β=2.0, κ=5.0 — starting values)", fontsize=9)

    for ax, mode in zip(axes.flat, MODE_ORDER):
        mdf = all_agents[all_agents["decision_mode"] == mode]
        for zone in ["inner", "mid", "outer"]:
            zone_ids = mdf[mdf["initial_zone"] == zone]["agent_id"].unique()
            total_zone = len(zone_ids)
            if total_zone == 0:
                continue

            # First timestep each agent reaches camp
            camp_rows = mdf[(mdf["agent_id"].isin(zone_ids)) & (mdf["zone"] == "camp")]
            first_camp = camp_rows.groupby("agent_id")["timestep"].min().to_dict()

            times = list(range(n_steps + 1))
            cum_frac = [sum(1 for ft in first_camp.values() if ft <= t) / total_zone
                        for t in times]
            ax.plot(times, cum_frac, color=ZONE_COLORS[zone], lw=1.5,
                    label=f"{zone} ({total_zone})")

        ax.axvline(4, color="gray", ls="--", lw=0.6, alpha=0.7)
        ax.axhline(0.78, color="gray", ls=":", lw=0.6, alpha=0.7)
        ax.set_title(mode.replace("_", " "), fontsize=8)
        ax.set_xlim(0, min(30, n_steps))
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.2)
        if ax in axes[1]:
            ax.set_xlabel("Time (days)")
        if ax in axes[:, 0]:
            ax.set_ylabel("Cumulative departed")
        ax.legend(fontsize=5, loc="lower right")

    fig.tight_layout()
    fig.savefig(out_dir / "F1_departure_curves_by_zone.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved F1_departure_curves_by_zone.png")


def fig_F2_ps2_by_zone(blend_df, out_dir, n_steps):
    """F2: P_S2 time series by zone (blend mode only)."""
    figwidth = setup_science_style(7.0)
    fig, ax1 = plt.subplots(figsize=(figwidth, figwidth * 0.4))

    for zone in ["inner", "mid", "outer"]:
        zone_locs = set(ZONES[zone])
        zdf = blend_df[(blend_df["zone"] == zone)]
        if zdf.empty:
            continue
        agg = zdf.groupby("timestep")["s2_weight"].agg(["mean", "std", "count"]).reset_index()
        mask = agg["count"] >= 3
        t = agg.loc[mask, "timestep"].values
        m = agg.loc[mask, "mean"].values
        s = agg.loc[mask, "std"].fillna(0).values
        ax1.fill_between(t, m - s, m + s, alpha=0.15, color=ZONE_COLORS[zone])
        ax1.plot(t, m, color=ZONE_COLORS[zone], lw=1.5, label=f"{zone}")

    # Global active mean
    active = blend_df[blend_df["zone"] != "camp"]
    if not active.empty:
        g = active.groupby("timestep")["s2_weight"].mean()
        ax1.plot(g.index, g.values, color="black", ls="--", lw=0.8, alpha=0.6,
                 label="global active")

    # Conflict intensity on secondary axis
    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    inner_conflict = blend_df[blend_df["location"] == "okuma"].groupby("timestep")["conflict_intensity"].mean()
    if not inner_conflict.empty:
        ax2.plot(inner_conflict.index, inner_conflict.values, color="gray", ls=":",
                 lw=0.8, alpha=0.5, label="conflict (okuma)")
        ax2.set_ylabel("Conflict intensity", fontsize=7)
        ax2.set_ylim(0, 1.2)

    ax1.set_xlabel("Time (days)")
    ax1.set_ylabel("Mean P_S2 (active agents)")
    ax1.set_xlim(0, min(40, n_steps))
    ax1.set_ylim(0, 0.6)
    ax1.legend(fontsize=6, loc="upper right")
    ax1.grid(True, alpha=0.2)
    ax1.set_title("P_S2 by Evacuation Zone — Blend Mode, Starting Values\n"
                   "(α=1.0, β=2.0, κ=5.0)", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "F2_ps2_by_zone_blend.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved F2_ps2_by_zone_blend.png")


def fig_F3_mode_comparison(all_agents, out_dir, n_steps):
    """F3: Global active-mean P_S2 for all modes, with Day 2 reference."""
    figwidth = setup_science_style(7.0)
    fig, ax1 = plt.subplots(figsize=(figwidth, figwidth * 0.4))

    for mode in MODE_ORDER:
        mdf = all_agents[(all_agents["decision_mode"] == mode) & (all_agents["zone"] != "camp")]
        if mdf.empty:
            continue
        agg = mdf.groupby("timestep")["s2_weight"].mean()
        ax1.plot(agg.index, agg.values, color=PALETTE[mode], ls=LINESTYLE[mode],
                 lw=1.5, label=mode.replace("_", " "))

    # Day 2 linear-escalate reference
    day2_path = REPO_ROOT / "output" / "results" / "synthetic" / "linear_escalate" / "summary_all_modes.csv"
    if day2_path.exists():
        d2 = pd.read_csv(day2_path)
        d2_blend = d2[d2["decision_mode"] == "blend"]
        if "mean_s2_weight_active" in d2_blend.columns:
            agg2 = d2_blend.groupby("timestep")["mean_s2_weight_active"].mean()
            ax1.plot(agg2.index, agg2.values, color="#cccccc", lw=0.8, ls="-",
                     alpha=0.5, label="Day 2 synthetic (linear)")

    # Conflict on secondary axis
    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    blend_df = all_agents[all_agents["decision_mode"] == "blend"]
    inner_c = blend_df[blend_df["location"] == "okuma"].groupby("timestep")["conflict_intensity"].mean()
    if not inner_c.empty:
        ax2.plot(inner_c.index, inner_c.values, color="gray", ls=":", lw=0.8, alpha=0.4)
        ax2.set_ylabel("Conflict (okuma)", fontsize=7)
        ax2.set_ylim(0, 1.2)

    ax1.set_xlabel("Time (days)")
    ax1.set_ylabel("Mean P_S2 (active agents)")
    ax1.set_xlim(0, min(40, n_steps))
    ax1.set_ylim(0, 0.6)
    ax1.legend(fontsize=6, loc="upper right")
    ax1.grid(True, alpha=0.2)
    ax1.set_title("Mode Comparison — Global Active P_S2\n(α=1.0, β=2.0, κ=5.0)", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "F3_mode_comparison_global.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved F3_mode_comparison_global.png")


def fig_F4_network_snapshot(blend_df, lm, out_dir, t_snapshot=4):
    """F4: Network diagram at t=4 (peak conflict), nodes sized by remaining pop."""
    try:
        import networkx as nx
    except ImportError:
        print("  Skipping F4 (networkx not installed)")
        return

    figwidth = setup_science_style(7.0)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.7))

    snap = blend_df[blend_df["timestep"] == t_snapshot]
    loc_counts = snap["location"].value_counts()

    G = nx.Graph()
    pos = {}
    for name, loc in lm.items():
        x = getattr(loc, "x", 0)
        y = getattr(loc, "y", 0)
        G.add_node(name)
        pos[name] = (x, y)

    routes_path = REPO_ROOT / "input" / "fukushima_day3" / "routes.csv"
    if routes_path.exists():
        import csv
        with open(routes_path) as f:
            for row in csv.reader(f):
                if not row or row[0].startswith("#"):
                    continue
                n1 = row[0].strip('"')
                n2 = row[1].strip('"')
                G.add_edge(n1, n2)

    zone_map = {n: z for z, ns in ZONES.items() for n in ns}
    for c in CAMP_NAMES:
        zone_map[c] = "camp"
    color_map = {"inner": "#D35400", "mid": "#E67E22", "outer": "#2E86C1",
                 "camp": "#27AE60", "unknown": "#95A5A6"}

    node_colors = [color_map.get(zone_map.get(n, "unknown"), "#95A5A6") for n in G.nodes()]
    node_sizes = [max(50, int(loc_counts.get(n, 0)) * 3) for n in G.nodes()]

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="lightgray", width=1.0)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, alpha=0.85, edgecolors="gray", linewidths=0.5)

    # Labels with conflict intensity
    labels = {}
    for n in G.nodes():
        count = int(loc_counts.get(n, 0))
        conf = snap[snap["location"] == n]["conflict_intensity"].mean() if not snap[snap["location"] == n].empty else 0
        if conf > 0.01:
            labels[n] = f"{n}\n({count}, c={conf:.1f})"
        else:
            labels[n] = f"{n}\n({count})"
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=5)

    ax.set_title(f"Network State at t={t_snapshot} (Peak Conflict — Day 4 / Unit 2 Explosion)\n"
                 "(α=1.0, β=2.0, κ=5.0)", fontsize=8)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_dir / "F4_network_snapshot_t4.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved F4_network_snapshot_t4.png")


def fig_F4b_path_length(arrival_df, out_dir):
    """F4b: Path-length-at-arrival distributions by mode and zone."""
    if arrival_df.empty:
        print("  No arrival data for F4b")
        return

    figwidth = setup_science_style(7.0)

    # Figure 1: Violin + strip plot by mode and zone
    fig, axes = plt.subplots(1, 4, figsize=(figwidth * 1.6, figwidth * 0.5),
                             sharey=True)
    modes_present = [m for m in MODE_ORDER if m in arrival_df["decision_mode"].unique()]

    for ax_idx, mode in enumerate(modes_present):
        ax = axes[ax_idx] if len(modes_present) > 1 else axes
        mdf = arrival_df[arrival_df["decision_mode"] == mode]

        zone_data = []
        zone_labels = []
        zone_colors_list = []
        for zone in ["inner", "mid", "outer"]:
            zd = mdf[mdf["initial_zone"] == zone]["path_length_km"].values
            if len(zd) > 0:
                zone_data.append(zd)
                zone_labels.append(zone)
                zone_colors_list.append(ZONE_COLORS.get(zone, "#888"))

        if zone_data:
            parts = ax.violinplot(zone_data, positions=range(len(zone_data)),
                                  showmeans=True, showmedians=True)
            for i, pc in enumerate(parts["bodies"]):
                pc.set_facecolor(zone_colors_list[i])
                pc.set_alpha(0.3)

            for i, zd in enumerate(zone_data):
                jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(zd))
                ax.scatter(np.full(len(zd), i) + jitter, zd, s=5, alpha=0.4,
                           color=zone_colors_list[i], edgecolors="none")

        ax.set_xticks(range(len(zone_labels)))
        ax.set_xticklabels(zone_labels, fontsize=7)
        ax.set_title(mode.replace("_", " "), fontsize=8)
        if ax_idx == 0:
            ax.set_ylabel("Path length (km)", fontsize=8)
        ax.grid(axis="y", alpha=0.2)

    fig.suptitle("Path Length at Arrival by Mode and Zone", fontsize=9, y=1.02)
    fig.tight_layout()
    fig.savefig(out_dir / "F4b_path_length_distributions.png", dpi=300,
                bbox_inches="tight")
    plt.close(fig)
    print("  Saved F4b_path_length_distributions.png")

    # Figure 2: Path length vs experience, colored by mode
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.5))

    for mode in modes_present:
        mdf = arrival_df[arrival_df["decision_mode"] == mode]
        ax.scatter(mdf["experience_x"], mdf["path_length_km"], s=10, alpha=0.4,
                   color=PALETTE.get(mode, "#888"), label=mode.replace("_", " "),
                   edgecolors="none")

        # Linear trend
        if len(mdf) > 5:
            z = np.polyfit(mdf["experience_x"], mdf["path_length_km"], 1)
            xfit = np.linspace(0, 1, 50)
            ax.plot(xfit, np.polyval(z, xfit), color=PALETTE.get(mode, "#888"),
                    lw=1.5, ls="--")

    ax.set_xlabel("Experience index (x)", fontsize=8)
    ax.set_ylabel("Path length at arrival (km)", fontsize=8)
    ax.set_title("Path Length vs Experience — Deliberation Quality Test", fontsize=9)
    ax.legend(fontsize=6, loc="upper right")
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
    fig.savefig(out_dir / "F4b_path_length_vs_experience.png", dpi=300,
                bbox_inches="tight")
    plt.close(fig)
    print("  Saved F4b_path_length_vs_experience.png")


def run_diagnostics(all_agents, n_steps):
    """Run Day 3 success criteria checks."""
    print("\n=== DIAGNOSTICS ===")
    all_pass = True

    # Check 1: Camp filter — no agents initially distributed to camp
    initial_camp = all_agents[all_agents["initial_zone"] == "camp"]
    camp_ok = initial_camp["agent_id"].nunique() == 0
    n_initial_camp = initial_camp["agent_id"].nunique()
    print(f"CHECK 1 Camp filter (0 agents spawned at camp): "
          f"{'PASS' if camp_ok else 'FAIL'} ({n_initial_camp} spawned)")
    if not camp_ok:
        all_pass = False

    # Check 2: Mode separation (original == s1_only)
    orig = all_agents[all_agents["decision_mode"] == "original"]
    s1 = all_agents[all_agents["decision_mode"] == "s1_only"]
    if not orig.empty and not s1.empty:
        dep_orig = orig.groupby("agent_id")["moved"].any()
        dep_s1 = s1.groupby("agent_id")["moved"].any()
        ks_stat, ks_p = stats.ks_2samp(dep_orig.astype(int), dep_s1.astype(int))
        mode_ok = ks_p > 0.05
        print(f"CHECK 2 Mode separation (KS p={ks_p:.4f}): {'PASS' if mode_ok else 'FAIL'}")
        if not mode_ok:
            all_pass = False
    else:
        print("CHECK 2 Mode separation: SKIP (missing data)")

    # Check 3: Hayano 78% target — inner+mid departure at t=4
    blend = all_agents[all_agents["decision_mode"] == "blend"]
    im_ids = blend[blend["initial_zone"].isin(["inner", "mid"])]["agent_id"].unique()
    total_im = len(im_ids)
    if total_im > 0:
        camp_rows = blend[(blend["agent_id"].isin(im_ids)) & (blend["zone"] == "camp")]
        first_camp = camp_rows.groupby("agent_id")["timestep"].min()
        dep_by_t4 = (first_camp <= 4).sum()
        dep_frac = dep_by_t4 / total_im
        hayano_ok = 0.50 <= dep_frac <= 0.95
        print(f"CHECK 3 Hayano 78% (inner+mid dep at t=4): {dep_frac:.3f} "
              f"({dep_by_t4}/{total_im}) [0.50-0.95] {'PASS' if hayano_ok else 'FAIL'}")
        if not hayano_ok:
            all_pass = False
    else:
        print("CHECK 3 Hayano: SKIP (no inner/mid agents)")

    # Check 4: Zone P_S2 ordering at t=1 (by current location zone)
    t1_blend = blend[blend["timestep"] == 1]
    zone_ps2 = {}
    for zone in ["inner", "mid", "outer"]:
        zone_locs = set(ZONES[zone])
        zdf = t1_blend[t1_blend["location"].isin(zone_locs)]
        zone_ps2[zone] = zdf["s2_weight"].mean() if not zdf.empty else float("nan")
    o, m, i = zone_ps2.get("outer", 0), zone_ps2.get("mid", 0), zone_ps2.get("inner", 0)
    order_ok = (not np.isnan(o) and not np.isnan(m) and not np.isnan(i)
                and o > m > i)
    print(f"CHECK 4 Zone P_S2 ordering t=1: outer={o:.3f} > mid={m:.3f} > "
          f"inner={i:.3f} {'PASS' if order_ok else 'FAIL'}")
    if not order_ok:
        all_pass = False

    # Check 5: Three-phase (mid zone) — dip then recovery
    mid_locs = set(ZONES["mid"])
    mid_active = blend[blend["location"].isin(mid_locs)]
    if not mid_active.empty:
        by_t = mid_active.groupby("timestep")["s2_weight"].mean()
        if len(by_t) > 2:
            init_v = by_t.iloc[0]
            min_v = by_t.min()
            dip = init_v - min_v
            min_t = by_t.idxmin()
            post = by_t[by_t.index > min_t]
            recov = (post.max() - min_v) if len(post) > 0 else 0
            three_ok = dip > 0.05 and recov > 0.03
            print(f"CHECK 5 Three-phase mid zone: init={init_v:.3f}, "
                  f"min={min_v:.3f} at t={min_t}, dip={dip:.3f}, "
                  f"recovery={recov:.3f} {'PASS' if three_ok else 'FAIL'}")
            if not three_ok:
                all_pass = False
        else:
            print("CHECK 5 Three-phase: SKIP (insufficient timesteps)")
    else:
        print("CHECK 5 Three-phase: SKIP (no mid-zone active agents)")

    # Check 6: No NaN in P_S2
    nan_count = all_agents["s2_weight"].isna().sum()
    nan_ok = nan_count == 0
    print(f"CHECK 6 No NaN in P_S2: {'PASS' if nan_ok else 'FAIL'} ({nan_count} NaN)")
    if not nan_ok:
        all_pass = False

    # Extra diagnostics
    print("\n--- Departure fractions by zone at key timesteps ---")
    for mode in MODE_ORDER:
        if mode not in all_agents["decision_mode"].values:
            continue
        mdf = all_agents[all_agents["decision_mode"] == mode]
        for zone in ["inner", "mid", "outer"]:
            zids = mdf[mdf["initial_zone"] == zone]["agent_id"].unique()
            n = len(zids)
            if n == 0:
                continue
            camp_r = mdf[(mdf["agent_id"].isin(zids)) & (mdf["zone"] == "camp")]
            fc = camp_r.groupby("agent_id")["timestep"].min()
            fracs = [f"t={t}: {(fc <= t).sum()/n:.2f}" for t in [1, 2, 4, 7, 14, 30]]
            print(f"  {mode}/{zone} (n={n}): {', '.join(fracs)}")

    print(f"\n=== ALL CHECKS: {'PASS' if all_pass else 'FAIL'} ===")
    return all_pass


def extract_qois(all_agents):
    """Extract scalar QoIs for Sobol analysis."""
    blend = all_agents[all_agents["decision_mode"] == "blend"]
    orig = all_agents[all_agents["decision_mode"] == "original"] if "original" in all_agents["decision_mode"].values else None

    # QoI 1: hayano_t4 — inner+mid departure fraction at t=4
    im_ids = blend[blend["initial_zone"].isin(["inner", "mid"])]["agent_id"].unique()
    total_im = len(im_ids)
    if total_im > 0:
        camp_rows = blend[(blend["agent_id"].isin(im_ids)) & (blend["zone"] == "camp")]
        first_camp = camp_rows.groupby("agent_id")["timestep"].min()
        hayano_t4 = float((first_camp <= 4).sum() / total_im)
    else:
        hayano_t4 = 0.0

    # QoI 2-4: mid-zone P_S2 dynamics
    mid_locs = set(ZONES["mid"])
    mid_active = blend[blend["location"].isin(mid_locs)]
    if not mid_active.empty:
        by_t = mid_active.groupby("timestep")["s2_weight"].mean()
        init_ps2 = by_t.iloc[0] if len(by_t) > 0 else 0.315
        mid_ps2_trough = float(by_t.min())
        mid_ps2_dip = float(init_ps2 - mid_ps2_trough)
        min_t = by_t.idxmin()
        post = by_t[by_t.index > min_t]
        t28 = by_t.get(28, by_t.iloc[-1] if len(by_t) > 0 else 0)
        mid_ps2_recovery = float(t28 - mid_ps2_trough)
    else:
        mid_ps2_trough = 0.0
        mid_ps2_dip = 0.0
        mid_ps2_recovery = 0.0

    # QoI 5: blend_inner_t7 — blend vs original inner-zone departure speedup
    inner_ids_blend = blend[blend["initial_zone"] == "inner"]["agent_id"].unique()
    n_inner = len(inner_ids_blend)
    blend_inner_t7_frac = 0.0
    if n_inner > 0:
        camp_b = blend[(blend["agent_id"].isin(inner_ids_blend)) & (blend["zone"] == "camp")]
        fc_b = camp_b.groupby("agent_id")["timestep"].min()
        blend_inner_t7_frac = float((fc_b <= 7).sum() / n_inner)

    orig_inner_t7_frac = 0.0
    if orig is not None and not orig.empty:
        inner_ids_orig = orig[orig["initial_zone"] == "inner"]["agent_id"].unique()
        n_orig = len(inner_ids_orig)
        if n_orig > 0:
            camp_o = orig[(orig["agent_id"].isin(inner_ids_orig)) & (orig["zone"] == "camp")]
            fc_o = camp_o.groupby("agent_id")["timestep"].min()
            orig_inner_t7_frac = float((fc_o <= 7).sum() / n_orig)

    blend_inner_t7 = blend_inner_t7_frac - orig_inner_t7_frac

    return {
        "hayano_t4": round(hayano_t4, 4),
        "mid_ps2_trough": round(mid_ps2_trough, 4),
        "mid_ps2_dip": round(mid_ps2_dip, 4),
        "mid_ps2_recovery": round(mid_ps2_recovery, 4),
        "blend_inner_t7": round(blend_inner_t7, 4),
    }


def main():
    ap = argparse.ArgumentParser(description="Day 3: First Fukushima run")
    ap.add_argument("--input-dir", default="input/fukushima_day3")
    ap.add_argument("--output-dir", default="figures/fukushima")
    ap.add_argument("--n-steps", type=int, default=60)
    ap.add_argument("--n-agents", type=int, default=1200)
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--beta", type=float, default=2.0)
    ap.add_argument("--kappa", type=float, default=5.0)
    ap.add_argument("--modes", nargs="+", default=MODE_ORDER)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output-json", default=None,
                    help="Write QoI scalars to JSON file (for Sobol campaign)")
    args = ap.parse_args()

    input_dir = str(REPO_ROOT / args.input_dir)
    out_dir = Path(REPO_ROOT / args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_dfs = []
    all_arrivals = []
    lm_ref = None
    for mode in args.modes:
        print(f"\n  Running {mode}...")
        df, lm, arrivals = run_one(input_dir, mode, args.n_agents, args.n_steps,
                                   args.alpha, args.beta, args.kappa, args.seed)
        all_dfs.append(df)
        all_arrivals.append(arrivals)
        if lm_ref is None:
            lm_ref = lm
        print(f"  {mode}: {len(df)} rows, {len(arrivals)} arrivals")

    all_agents = pd.concat(all_dfs, ignore_index=True)

    # JSON QoI output mode (for Sobol campaign)
    if args.output_json:
        qois = extract_qois(all_agents)
        import json
        Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w") as f:
            json.dump(qois, f)
        print(f"QoIs -> {args.output_json}: {qois}")
        return 0

    # Save raw data
    all_agents.to_csv(out_dir / "agents_all_modes.csv", index=False)
    print(f"\nSaved agents_all_modes.csv ({len(all_agents)} rows)")

    # Save path-length arrival data
    if all_arrivals:
        arrival_df = pd.concat([a for a in all_arrivals if not a.empty], ignore_index=True)
        if not arrival_df.empty:
            results_dir = REPO_ROOT / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            for mode in arrival_df["decision_mode"].unique():
                mode_arr = arrival_df[arrival_df["decision_mode"] == mode]
                mode_arr.to_csv(results_dir / f"path_length_{mode}.csv", index=False)
                print(f"  Saved path_length_{mode}.csv ({len(mode_arr)} arrivals)")
            arrival_df.to_csv(results_dir / "path_length_all.csv", index=False)
            fig_F4b_path_length(arrival_df, out_dir)
        else:
            arrival_df = pd.DataFrame()
    else:
        arrival_df = pd.DataFrame()

    # Figures
    print("\nGenerating figures...")
    blend_df = all_agents[all_agents["decision_mode"] == "blend"]

    fig_F1_departure_by_zone(all_agents, out_dir, args.n_steps)
    fig_F2_ps2_by_zone(blend_df, out_dir, args.n_steps)
    fig_F3_mode_comparison(all_agents, out_dir, args.n_steps)
    fig_F4_network_snapshot(blend_df, lm_ref, out_dir, t_snapshot=4)

    # Diagnostics
    passed = run_diagnostics(all_agents, args.n_steps)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
