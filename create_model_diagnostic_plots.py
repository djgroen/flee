#!/usr/bin/env python3
"""
Create multipanel diagnostic plots for model comparison (original, S1-only, S2-only, full S1/S2).
Journal-quality figures interrogating network topology, evacuation metrics, and cognitive dynamics.

Requires: run_model_comparison.py output in data/model_comparison/

Usage:
  python create_model_diagnostic_plots.py
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from flee.s1s2_model import compute_s2_move_probability
except ImportError:
    compute_s2_move_probability = None

sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = Path("data/model_comparison/figures")
BASE_DIR = Path("data/model_comparison")
TOPOLOGIES = ["ring", "linear", "star"]
VARIANTS = ["original", "s1_only", "s2_only", "full_s1s2"]
VARIANT_LABELS = {
    "original": "Original FLEE",
    "s1_only": "S1 only",
    "s2_only": "S2 only",
    "full_s1s2": "Full S1/S2",
}
VARIANT_COLORS = {
    "original": "#2166ac",
    "s1_only": "#2166ac",
    "s2_only": "#b2182b",
    "full_s1s2": "#1b7837",
}
# Original and S1-only use same color; S1-only dashed so overlap is visible
VARIANT_LINESTYLES = {
    "original": "-",
    "s1_only": "--",
    "s2_only": "-",
    "full_s1s2": "-",
}


def build_graph_from_topology(topology_name: str) -> "nx.Graph|None":
    """Build NetworkX graph from topology CSV files."""
    if nx is None:
        return None
    topo_dir = Path("topologies") / topology_name / "input_csv"
    if not topo_dir.exists():
        return None
    locations = pd.read_csv(topo_dir / "locations.csv")
    routes = pd.read_csv(topo_dir / "routes.csv")

    G = nx.Graph()
    for _, loc in locations.iterrows():
        x = loc.get("gps_x", loc.get("x", 0))
        y = loc.get("gps_y", loc.get("y", 0))
        G.add_node(loc["name"], x=float(x), y=float(y))

    for _, r in routes.iterrows():
        G.add_edge(r["name1"], r["name2"], weight=float(r["distance"]))

    return G


def load_conflict_per_node(topology_name: str) -> dict:
    """Load conflict value per node from conflicts.csv. Camps default to 0."""
    topo_dir = Path("topologies") / topology_name / "input_csv"
    conflict_map = {}
    cf = topo_dir / "conflicts.csv"
    if cf.exists():
        try:
            df = pd.read_csv(cf, comment="#", header=None, names=["date", "loc", "val"], skipinitialspace=True)
            for _, row in df.iterrows():
                conflict_map[str(row["loc"])] = float(row["val"])
        except Exception:
            pass
    return conflict_map


def compute_s2_move_prob_per_node(G, conflict_map: dict, kappa: float = 5.0) -> dict:
    """For each node, compute σ (S2 move probability) from safety gradient to best neighbor."""
    if compute_s2_move_probability is None:
        return {}
    sigma = {}
    for node in G.nodes():
        c_here = max(0.0, conflict_map.get(node, 0.0))
        if c_here <= 0 or node not in G:
            sigma[node] = 0.0
            continue
        c_best, d_best = c_here, 1.0
        for nbr in G.neighbors(node):
            c_nbr = max(0.0, conflict_map.get(nbr, 0.0))
            d = G[node][nbr].get("weight", 1.0)
            if c_nbr < c_best:
                c_best = c_nbr
                d_best = max(1.0, d)
        sigma[node] = compute_s2_move_probability(c_here, c_best, d_best, kappa)
    return sigma


def compute_distance_to_safety(G, weight_attr="weight") -> dict:
    """Shortest path length to nearest SafeZone. Smaller = closer to safety."""
    safe_nodes = [n for n in G.nodes() if "SafeZone" in str(n) or "safe" in str(n).lower()]
    if not safe_nodes:
        return {}
    dist = {}
    for n in G.nodes():
        if n in safe_nodes:
            dist[n] = 0.0
            continue
        try:
            d = min(
                nx.shortest_path_length(G, n, s, weight=weight_attr)
                for s in safe_nodes
                if nx.has_path(G, n, s)
            )
            dist[n] = d
        except (nx.NetworkXNoPath, ValueError):
            dist[n] = float("inf")
    return dist


def create_network_spatial_plots():
    """
    Static network plots with node color = conflict, node size = metric.
    Panels: S1 P_move, S2 σ, distance-to-safety. Journal-quality.
    """
    if nx is None:
        print("  Skipping network spatial plots (networkx not installed)")
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    kappa = 5.0
    s1_move = 0.3

    for topo in TOPOLOGIES:
        G = build_graph_from_topology(topo)
        if G is None:
            continue
        conflict_map = load_conflict_per_node(topo)
        sigma_map = compute_s2_move_prob_per_node(G, conflict_map, kappa)
        dist_to_safe = compute_distance_to_safety(G)
        if dist_to_safe:
            d_max = max(d for d in dist_to_safe.values() if np.isfinite(d)) or 1
            dist_norm = {n: 1.0 - (d / d_max) if np.isfinite(d) else 0.0 for n, d in dist_to_safe.items()}
        else:
            dist_norm = {}

        pos = {n: (G.nodes[n]["x"], G.nodes[n]["y"]) for n in G.nodes()}

        fig, axes = plt.subplots(1, 3, figsize=(14, 6))
        fig.suptitle(f"{topo.title()} topology: S1, S2, and structural metrics", fontsize=14, fontweight="bold")
        fig.subplots_adjust(right=0.88, wspace=0.25, top=0.88, bottom=0.12)

        panels = [
            ("S1: uniform P_move = 0.3", {n: (s1_move if conflict_map.get(n, 0) > 0 else 0.0) for n in G.nodes()}, "Node size ∝ P_move"),
            ("S2: P_move = σ (safety gradient)", sigma_map, "Node size ∝ σ"),
            ("Distance to nearest SafeZone", dist_norm, "Node size ∝ proximity to safety"),
        ]
        sc = None
        for ax, (title, size_map, size_label) in zip(axes, panels):
            node_colors = []
            node_sizes = []
            nodelist = []
            for n in G.nodes():
                c = max(0.0, min(1.0, conflict_map.get(n, 0.0)))
                node_colors.append(c)
                sz = size_map.get(n, 0.0) if size_map else 0.0
                node_sizes.append(300 + 1200 * sz)
                nodelist.append(n)

            nx.draw_networkx_edges(G, pos, ax=ax, edge_color="lightgray", width=1.5, alpha=0.7)
            sc = ax.scatter(
                [pos[n][0] for n in nodelist],
                [pos[n][1] for n in nodelist],
                c=node_colors,
                s=node_sizes,
                cmap="RdYlGn_r",
                vmin=0,
                vmax=1,
                alpha=0.85,
                edgecolors="black",
                linewidths=0.5,
            )
            ax.set_aspect("equal")
            ax.margins(0.12)
            ax.set_title(title, fontsize=11)
            ax.text(0.5, -0.05, size_label, transform=ax.transAxes, ha="center", fontsize=8, style="italic")
            ax.axis("off")

        if sc is not None:
            cbar_ax = fig.add_axes([0.91, 0.15, 0.02, 0.7])
            fig.colorbar(sc, cax=cbar_ax, label="Conflict intensity")

        out_path = OUTPUT_DIR / f"network_spatial_{topo}.png"
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved {out_path}")


def compute_topology_metrics(G) -> dict:
    """Compute network topology metrics."""
    if G is None or not nx.is_connected(G):
        return {}
    metrics = {}
    metrics["n_nodes"] = G.number_of_nodes()
    metrics["n_edges"] = G.number_of_edges()
    metrics["density"] = nx.density(G)
    metrics["diameter"] = nx.diameter(G)
    metrics["avg_path_length"] = nx.average_shortest_path_length(G, weight="weight")
    dc = nx.degree_centrality(G)
    bc = nx.betweenness_centrality(G, weight="weight")
    cc = nx.closeness_centrality(G, distance="weight")
    metrics["degree_centrality_mean"] = np.mean(list(dc.values()))
    metrics["betweenness_centrality_mean"] = np.mean(list(bc.values()))
    metrics["closeness_centrality_mean"] = np.mean(list(cc.values()))
    metrics["avg_clustering"] = nx.average_clustering(G)
    return metrics


def load_all_results() -> pd.DataFrame:
    """Load all results from model comparison runs."""
    rows = []
    for topo in TOPOLOGIES:
        for var in VARIANTS:
            d = BASE_DIR / topo / var
            if not d.exists():
                continue
            for p in d.glob("results_*.csv"):
                df = pd.read_csv(p)
                df["topology"] = topo
                df["variant"] = var
                rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def create_multipanel_diagnostic(df: pd.DataFrame, topo_metrics: dict):
    """Create main multipanel diagnostic figure (journal quality)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14, 12))
    fig.suptitle("Model Comparison: Original FLEE vs S1/S2 Variants", fontsize=14, fontweight="bold", y=1.02)

    # --- Panel A: Topology metrics (network structure) ---
    ax1 = fig.add_subplot(3, 3, 1)
    if topo_metrics:
        topo_names = list(topo_metrics.keys())
        metrics_to_plot = ["n_nodes", "n_edges", "density", "avg_path_length"]
        x = np.arange(len(topo_names))
        width = 0.2
        for i, m in enumerate(metrics_to_plot):
            vals = [topo_metrics[t].get(m, 0) for t in topo_names]
            if any(np.isfinite(v) for v in vals):
                ax1.bar(x + (i - 1.5) * width, vals, width, label=m.replace("_", " "))
        ax1.set_xticks(x)
        ax1.set_xticklabels(topo_names)
        ax1.set_ylabel("Value")
        ax1.set_title("(A) Network topology metrics")
        ax1.legend(fontsize=7)
        ax1.tick_params(axis="x", rotation=15)
    else:
        ax1.text(0.5, 0.5, "No topology data\n(install networkx)", ha="center", va="center")
        ax1.set_title("(A) Network topology metrics")

    # --- Panel B: Evacuation rate by variant × topology ---
    ax2 = fig.add_subplot(3, 3, 2)
    evac_rows = []
    for (topo, var), g in df.groupby(["topology", "variant"]):
        last = g[g["timestep"] == g["timestep"].max()]
        n = len(last)
        evacuated = last["location"].astype(str).str.contains("SafeZone", na=False).sum()
        evac_rows.append({"topology": topo, "variant": var, "rate": evacuated / n if n else 0})
    evac_df = pd.DataFrame(evac_rows)
    if not evac_df.empty:
        x = np.arange(len(TOPOLOGIES))
        width = 0.2
        for i, var in enumerate(VARIANTS):
            sub = evac_df[evac_df["variant"] == var]
            if sub.empty:
                continue
            rates = [sub[sub["topology"] == t]["rate"].values[0] if len(sub[sub["topology"] == t]) else 0 for t in TOPOLOGIES]
            ax2.bar(x + (i - 1.5) * width, rates, width, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var, None))
        ax2.set_xticks(x)
        ax2.set_xticklabels(TOPOLOGIES)
        ax2.set_ylabel("Final evacuation rate")
        ax2.set_title("(B) Evacuation success")
        ax2.legend(fontsize=7)
        ax2.set_ylim(0, 1.05)
    ax2.set_title("(B) Evacuation success")

    # --- Panel C: Mean P_S2 by variant × topology ---
    ax3 = fig.add_subplot(3, 3, 3)
    if not df.empty and "p_s2" in df.columns:
        agg = df.groupby(["topology", "variant"])["p_s2"].mean().reset_index()
        x = np.arange(len(TOPOLOGIES))
        width = 0.2
        for i, var in enumerate(VARIANTS):
            sub = agg[agg["variant"] == var]
            if sub.empty:
                continue
            vals = [sub[(sub["topology"] == t)]["p_s2"].values[0] if len(sub[(sub["topology"] == t)]) else 0 for t in TOPOLOGIES]
            ax3.bar(x + (i - 1.5) * width, vals, width, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var, None))
        ax3.set_xticks(x)
        ax3.set_xticklabels(TOPOLOGIES)
        ax3.set_ylabel("Mean P_S2")
        ax3.set_title("(C) Deliberation probability")
        ax3.legend(fontsize=7)
        ax3.set_ylim(0, 1.05)
    else:
        ax3.text(0.5, 0.5, "No P_S2 data", ha="center", va="center")
    ax3.set_title("(C) Mean P_S2")

    # --- Panel D: P_S2 over time by variant (aggregate topologies) ---
    ax4 = fig.add_subplot(3, 3, 4)
    if not df.empty and "p_s2" in df.columns:
        for var in VARIANTS:
            sub = df[df["variant"] == var]
            if sub.empty:
                continue
            t_agg = sub.groupby("timestep")["p_s2"].mean()
            ls = VARIANT_LINESTYLES.get(var, "-")
            ax4.plot(t_agg.index, t_agg.values, ls, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var, None), linewidth=2)
        ax4.set_xlabel("Timestep")
        ax4.set_ylabel("Mean P_S2")
        ax4.set_title("(D) P_S2 over time")
        ax4.legend(fontsize=7)
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 1.05)
    ax4.set_title("(D) P_S2 over time")

    # --- Panel E: Evacuation time (first SafeZone arrival) by variant ---
    ax5 = fig.add_subplot(3, 3, 5)
    if not df.empty:
        first_safe = df[df["location"].astype(str).str.contains("SafeZone", na=False)].groupby(["agent_id", "variant", "topology"])["timestep"].min().reset_index()
        for var in VARIANTS:
            sub = first_safe[first_safe["variant"] == var]["timestep"]
            if len(sub) > 0:
                ax5.hist(sub, bins=15, alpha=0.5, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var, None), density=True)
        ax5.set_xlabel("First evacuation timestep")
        ax5.set_ylabel("Density")
        ax5.set_title("(E) Evacuation timing")
        ax5.legend(fontsize=7)
    ax5.set_title("(E) Evacuation timing")

    # --- Panel F: P_S2 vs conflict (binned) by variant ---
    ax6 = fig.add_subplot(3, 3, 6)
    if not df.empty and "p_s2" in df.columns and "conflict" in df.columns:
        df_copy = df.copy()
        df_copy["conflict_bin"] = pd.cut(df_copy["conflict"], bins=np.linspace(0, 1, 11), include_lowest=True)
        agg = df_copy.dropna(subset=["conflict_bin"]).groupby(["conflict_bin", "variant"], observed=True).agg(
            mean_p_s2=("p_s2", "mean"), mean_conflict=("conflict", "mean")
        ).reset_index()
        for var in VARIANTS:
            sub = agg[agg["variant"] == var]
            if sub.empty:
                continue
            ls = VARIANT_LINESTYLES.get(var, "-")
            ax6.plot(sub["mean_conflict"], sub["mean_p_s2"], "o"+ls, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var, None), markersize=4)
        ax6.set_xlabel("Conflict intensity")
        ax6.set_ylabel("Mean P_S2")
        ax6.set_title("(F) P_S2 vs conflict")
        ax6.legend(fontsize=7)
        ax6.grid(True, alpha=0.3)
        ax6.set_ylim(0, 1.05)
    ax6.set_title("(F) P_S2 vs conflict")

    # --- Panel G: Centrality comparison (topology) ---
    ax7 = fig.add_subplot(3, 3, 7)
    if topo_metrics:
        topo_names = list(topo_metrics.keys())
        cent_metrics = ["degree_centrality_mean", "betweenness_centrality_mean", "closeness_centrality_mean"]
        x = np.arange(len(topo_names))
        width = 0.25
        for i, m in enumerate(cent_metrics):
            vals = [topo_metrics[t].get(m, 0) for t in topo_names]
            if any(np.isfinite(v) for v in vals):
                ax7.bar(x + (i - 1) * width, vals, width, label=m.replace("_", " ").replace("mean", ""))
        ax7.set_xticks(x)
        ax7.set_xticklabels(topo_names)
        ax7.set_ylabel("Centrality")
        ax7.set_title("(G) Centrality by topology")
        ax7.legend(fontsize=7)
        ax7.tick_params(axis="x", rotation=15)
    ax7.set_title("(G) Centrality")

    # --- Panel H: Experience distribution by variant ---
    ax8 = fig.add_subplot(3, 3, 8)
    if not df.empty and "experience" in df.columns:
        last_t = df["timestep"].max()
        last = df[df["timestep"] == last_t]
        for var in VARIANTS:
            sub = last[last["variant"] == var]["experience"]
            if len(sub) > 0:
                ax8.hist(sub, bins=20, alpha=0.5, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var, None), density=True)
        ax8.set_xlabel("Experience index")
        ax8.set_ylabel("Density")
        ax8.set_title("(H) Experience at final timestep")
        ax8.legend(fontsize=7)
    ax8.set_title("(H) Experience distribution")

    # --- Panel I: Summary table ---
    ax9 = fig.add_subplot(3, 3, 9)
    ax9.axis("off")
    if not df.empty:
        evac_rates = []
        for (topo, var), g in df.groupby(["topology", "variant"]):
            last = g[g["timestep"] == g["timestep"].max()]
            n = len(last)
            evacuated = last["location"].astype(str).str.contains("SafeZone", na=False).sum()
            evac_rates.append((topo, var, evacuated / n if n else 0.0))
        tbl_data = []
        for topo in TOPOLOGIES:
            row = [topo]
            for var in VARIANTS:
                r = [x for x in evac_rates if x[0] == topo and x[1] == var]
                row.append(f"{r[0][2]:.2f}" if r else "-")
            tbl_data.append(row)
        cols = ["Topology"] + [VARIANT_LABELS[v] for v in VARIANTS]
        table = ax9.table(cellText=tbl_data, colLabels=cols, loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 2)
        ax9.set_title("(I) Evacuation rate summary")
    ax9.set_title("(I) Summary")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "model_comparison_multipanel.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")

    # --- Arrival rate time series (sanity check: original ≈ s1_only) ---
    create_arrival_rate_figure(df)

    # --- Second figure: topology × variant heatmaps ---
    create_heatmap_figure(df, evac_df)
    return out_path


def create_arrival_rate_figure(df: pd.DataFrame):
    """
    Arrival rate time series at SafeZones — sanity check.
    Original and S1-only should overlay (identical by design: P_S2≈0).
    """
    if df.empty:
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe = df[df["location"].astype(str).str.contains("SafeZone", na=False)]
    if safe.empty:
        return
    first_arrival = safe.groupby(["agent_id", "variant", "topology"])["timestep"].min().reset_index()
    first_arrival.columns = ["agent_id", "variant", "topology", "first_timestep"]

    t_max = int(df["timestep"].max())
    timesteps = np.arange(0, t_max + 1)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle("Arrival rate at SafeZones — Original & S1-only: same color (solid/dashed); should overlay", fontsize=12, fontweight="bold")

    # Panel (a): New arrivals per timestep by variant — main sanity check (original & S1 same color)
    ax = axes[0, 0]
    for var in VARIANTS:
        sub = first_arrival[first_arrival["variant"] == var]
        if sub.empty:
            continue
        rates = [len(sub[sub["first_timestep"] == t]) for t in timesteps]
        ls = VARIANT_LINESTYLES.get(var, "-")
        ax.plot(timesteps, rates, ls, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var), linewidth=2)
    ax.set_xlabel("Timestep")
    ax.set_ylabel("New arrivals")
    ax.set_title("(a) New arrivals by variant (Original ≈ S1-only)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel (b): Cumulative arrivals by variant
    ax = axes[0, 1]
    for var in VARIANTS:
        sub = first_arrival[first_arrival["variant"] == var]
        if sub.empty:
            continue
        cum = [len(sub[sub["first_timestep"] <= t]) for t in timesteps]
        ls = VARIANT_LINESTYLES.get(var, "-")
        ax.plot(timesteps, cum, ls, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var), linewidth=2)
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Cumulative arrivals")
    ax.set_title("(b) Cumulative arrivals by variant")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel (c): Ring topology — cumulative by variant (4 lines)
    ax = axes[1, 0]
    for var in VARIANTS:
        sub = first_arrival[(first_arrival["topology"] == "ring") & (first_arrival["variant"] == var)]
        if sub.empty:
            continue
        cum = [len(sub[sub["first_timestep"] <= t]) for t in timesteps]
        ls = VARIANT_LINESTYLES.get(var, "-")
        ax.plot(timesteps, cum, ls, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var), linewidth=2)
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Cumulative arrivals")
    ax.set_title("(c) Ring: cumulative by variant")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel (d): Star topology — cumulative by variant
    ax = axes[1, 1]
    for var in VARIANTS:
        sub = first_arrival[(first_arrival["topology"] == "star") & (first_arrival["variant"] == var)]
        if sub.empty:
            continue
        cum = [len(sub[sub["first_timestep"] <= t]) for t in timesteps]
        ls = VARIANT_LINESTYLES.get(var, "-")
        ax.plot(timesteps, cum, ls, label=VARIANT_LABELS[var], color=VARIANT_COLORS.get(var), linewidth=2)
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Cumulative arrivals")
    ax.set_title("(d) Star: cumulative by variant")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "model_comparison_arrival_rates.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def create_heatmap_figure(df: pd.DataFrame, evac_df: pd.DataFrame):
    """Create heatmap summary figure."""
    if df.empty:
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    # Evacuation rate heatmap
    ax = axes[0, 0]
    if not evac_df.empty:
        pivot = evac_df.pivot_table(values="rate", index="topology", columns="variant")
        pivot = pivot.reindex(index=TOPOLOGIES, columns=VARIANTS)
        im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=1, cmap="RdYlGn")
        ax.set_xticks(np.arange(len(VARIANTS)))
        ax.set_xticklabels([VARIANT_LABELS[v] for v in VARIANTS], rotation=30, ha="right")
        ax.set_yticks(np.arange(len(TOPOLOGIES)))
        ax.set_yticklabels(TOPOLOGIES)
        for i in range(len(TOPOLOGIES)):
            for j in range(len(VARIANTS)):
                val = pivot.values[i, j]
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="black", fontsize=10)
        plt.colorbar(im, ax=ax, label="Evacuation rate")
    ax.set_title("Evacuation rate: topology × variant")

    # Mean P_S2 heatmap
    ax = axes[0, 1]
    if "p_s2" in df.columns:
        agg = df.groupby(["topology", "variant"])["p_s2"].mean().reset_index()
        pivot = agg.pivot_table(values="p_s2", index="topology", columns="variant")
        pivot = pivot.reindex(index=TOPOLOGIES, columns=VARIANTS)
        im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=1, cmap="viridis")
        ax.set_xticks(np.arange(len(VARIANTS)))
        ax.set_xticklabels([VARIANT_LABELS[v] for v in VARIANTS], rotation=30, ha="right")
        ax.set_yticks(np.arange(len(TOPOLOGIES)))
        ax.set_yticklabels(TOPOLOGIES)
        for i in range(len(TOPOLOGIES)):
            for j in range(len(VARIANTS)):
                val = pivot.values[i, j]
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="white" if val > 0.5 else "black", fontsize=10)
        plt.colorbar(im, ax=ax, label="Mean P_S2")
    ax.set_title("Mean P_S2: topology × variant")

    # Peak P_S2 heatmap
    ax = axes[1, 0]
    if "p_s2" in df.columns:
        agg = df.groupby(["topology", "variant"])["p_s2"].max().reset_index()
        pivot = agg.pivot_table(values="p_s2", index="topology", columns="variant")
        pivot = pivot.reindex(index=TOPOLOGIES, columns=VARIANTS)
        im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=1, cmap="plasma")
        ax.set_xticks(np.arange(len(VARIANTS)))
        ax.set_xticklabels([VARIANT_LABELS[v] for v in VARIANTS], rotation=30, ha="right")
        ax.set_yticks(np.arange(len(TOPOLOGIES)))
        ax.set_yticklabels(TOPOLOGIES)
        for i in range(len(TOPOLOGIES)):
            for j in range(len(VARIANTS)):
                val = pivot.values[i, j]
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="white" if val > 0.5 else "black", fontsize=10)
        plt.colorbar(im, ax=ax, label="Peak P_S2")
    ax.set_title("Peak P_S2: topology × variant")

    # Avg evacuation time heatmap
    ax = axes[1, 1]
    if not df.empty:
        first_safe = df[df["location"].astype(str).str.contains("SafeZone", na=False)].groupby(["agent_id", "variant", "topology"])["timestep"].min().reset_index()
        agg = first_safe.groupby(["topology", "variant"])["timestep"].mean().reset_index()
        pivot = agg.pivot_table(values="timestep", index="topology", columns="variant")
        pivot = pivot.reindex(index=TOPOLOGIES, columns=VARIANTS)
        im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(np.arange(len(VARIANTS)))
        ax.set_xticklabels([VARIANT_LABELS[v] for v in VARIANTS], rotation=30, ha="right")
        ax.set_yticks(np.arange(len(TOPOLOGIES)))
        ax.set_yticklabels(TOPOLOGIES)
        for i in range(len(TOPOLOGIES)):
            for j in range(len(VARIANTS)):
                val = pivot.values[i, j]
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", color="white" if val > pivot.values.mean() else "black", fontsize=10)
        plt.colorbar(im, ax=ax, label="Avg evacuation time")
    ax.set_title("Avg evacuation time: topology × variant")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "model_comparison_heatmaps.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def main():
    if not BASE_DIR.exists():
        print(f"Run run_model_comparison.py first. Expected: {BASE_DIR}/")
        return 1

    df = load_all_results()
    if df.empty:
        print("No results_*.csv found in data/model_comparison/")
        print("Creating network spatial plots only (no model comparison data)...")
        create_network_spatial_plots()
        return 1

    topo_metrics = {}
    for topo in TOPOLOGIES:
        G = build_graph_from_topology(topo)
        if G is not None:
            topo_metrics[topo] = compute_topology_metrics(G)

    print("Creating diagnostic plots...")
    evac = []
    for (topo, var), g in df.groupby(["topology", "variant"]):
        last = g[g["timestep"] == g["timestep"].max()]
        n = len(last)
        evacuated = last["location"].astype(str).str.contains("SafeZone", na=False).sum()
        evac.append({"topology": topo, "variant": var, "rate": evacuated / n if n else 0})
    evac_df = pd.DataFrame(evac)

    create_multipanel_diagnostic(df, topo_metrics)  # also creates heatmaps

    print("Creating static network spatial plots...")
    create_network_spatial_plots()

    print(f"\nDone. Figures in {OUTPUT_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
