#!/usr/bin/env python3
"""
Visualize EasyVVUQ campaign results and parameter sensitivities.

Usage:
  python visualize_easyvvuq.py [--campaign-dir PATH]
  # Default: data/easyvvuq/s1s2_campaign

Output: figures in campaign_dir/figures/
- param_vs_evacuation.png: scatter plots (alpha, beta, p_s2 vs evacuation_rate)
- pairplot.png: parameter correlations and relationships
- correlation_heatmap.png: correlation matrix
- sobol_indices.png: first-order and total-effect Sobol indices (α, β, p_s2, topology) for both QoIs
- diagnostic_sampling.png: sampler uniformity check (from run_easyvvuq_campaign.py)
- omega_vs_beta_diagnostic.png: Omega(β) nonlinearity (from run_omega_diagnostic.py)
"""
import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))


def main():
    parser = argparse.ArgumentParser(description="Visualize EasyVVUQ results")
    parser.add_argument(
        "--campaign-dir",
        type=Path,
        default=repo_root / "data" / "easyvvuq" / "s1s2_campaign",
        help="Campaign directory with collated_results.csv",
    )
    parser.add_argument("--dpi", type=int, default=150, help="Figure DPI")
    args = parser.parse_args()

    campaign_dir = Path(args.campaign_dir)
    csv_path = campaign_dir / "collated_results.csv"
    if not csv_path.exists():
        print(f"Run the campaign first. Expected: {csv_path}")
        return 1

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    df = pd.read_csv(csv_path)
    # Drop placeholder row (run_id 0 with alpha=0) if present
    if "run_id" in df.columns and "alpha" in df.columns and len(df) > 1:
        df = df[~((df["run_id"] == 0) & (df["alpha"] == 0))]
    fig_dir = campaign_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Map topology 0,1,2 -> ring,star,linear (always recompute from topology)
    if "topology" in df.columns:
        def _topo_name(x):
            try:
                return ["ring", "star", "linear"][int(float(x)) % 3]
            except (ValueError, TypeError):
                return "ring"
        df["topology_name"] = df["topology"].apply(_topo_name)

    params = ["alpha", "beta", "p_s2"]
    if "topology" in df.columns:
        params = params + ["topology"]
    qois = ["evacuation_rate", "mean_p_s2"]

    # 1. Scatter: each param vs evacuation_rate (color by topology if present)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, p in zip(axes, ["alpha", "beta", "p_s2"]):
        if "topology_name" in df.columns:
            for topo in df["topology_name"].unique():
                sub = df[df["topology_name"] == topo]
                ax.scatter(sub[p], sub["evacuation_rate"], alpha=0.7, s=50, label=topo)
            ax.legend(fontsize=8)
        else:
            ax.scatter(df[p], df["evacuation_rate"], alpha=0.7, s=50)
        ax.set_xlabel(p)
        ax.set_ylabel("Evacuation rate")
        ax.set_title(f"{p} vs evacuation")
        ax.grid(True, alpha=0.3)
    fig.suptitle("Parameter sensitivity (scatter)")
    fig.tight_layout()
    fig.savefig(fig_dir / "param_vs_evacuation.png", dpi=args.dpi, bbox_inches="tight")
    fig.savefig(fig_dir / "param_vs_evacuation.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved param_vs_evacuation.png/.pdf")

    # 2. Evacuation by topology (if topology varied)
    if "topology_name" in df.columns:
        fig, ax = plt.subplots(figsize=(5, 4))
        topo_order = ["ring", "star", "linear"]
        data = [df[df["topology_name"] == t]["evacuation_rate"].values 
                for t in topo_order if t in df["topology_name"].values]
        labels = [t for t in topo_order if t in df["topology_name"].values]
        if data:
            ax.boxplot(data, tick_labels=labels)
            ax.set_xlabel("Topology")
            ax.set_ylabel("Evacuation rate")
            ax.set_title("Evacuation rate by topology")
        fig.tight_layout()
        fig.savefig(fig_dir / "evacuation_by_topology.png", dpi=args.dpi, bbox_inches="tight")
        fig.savefig(fig_dir / "evacuation_by_topology.pdf", bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved evacuation_by_topology.png/.pdf")

    # 3. Correlation heatmap
    cols = [c for c in params + qois if c in df.columns]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right")
    ax.set_yticklabels(cols)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=10)
    plt.colorbar(im, ax=ax, label="Correlation")
    ax.set_title("Parameter & QoI correlations")
    fig.tight_layout()
    fig.savefig(fig_dir / "correlation_heatmap.png", dpi=args.dpi, bbox_inches="tight")
    fig.savefig(fig_dir / "correlation_heatmap.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved correlation_heatmap.png/.pdf")

    # 4. Pair plot (params + evacuation_rate)
    try:
        import seaborn as sns
        plot_df = df[params + ["evacuation_rate"]].copy()
        plot_df["evacuation_rate"] = plot_df["evacuation_rate"].round(2)
        g = sns.pairplot(plot_df, diag_kind="kde", plot_kws={"alpha": 0.7})
        g.fig.suptitle("Parameter relationships and evacuation rate", y=1.02)
        g.savefig(fig_dir / "pairplot.png", dpi=args.dpi, bbox_inches="tight")
        g.savefig(fig_dir / "pairplot.pdf", bbox_inches="tight")
        plt.close("all")
        print(f"  Saved pairplot.png/.pdf")
    except ImportError:
        print("  Skipping pairplot (install seaborn for pair plots)")

    # 5. Sobol indices (SALib from Saltelli-style data, or EasyVVUQ if available)
    sobol_params = ["alpha", "beta", "p_s2", "topology"]
    sobol_done = False

    # Try SALib when we have Saltelli-sized data (N*(D+2) for D=4 params)
    try:
        from SALib.analyze import sobol as sobol_analyze
        # Saltelli: n_samples = N*(D+2), so 192 = 32*6 for D=4
        n_min = 6 * 4  # minimum N=4 for 4 params
        if len(df) >= n_min and len(df) % 6 == 0 and all(p in df.columns for p in sobol_params):
            problem = {
                "num_vars": 4,
                "names": sobol_params,
                "bounds": [[0.5, 4.0], [0.5, 4.0], [0.3, 1.0], [0, 2]],
            }
            Si_evac = sobol_analyze.analyze(problem, df["evacuation_rate"].values, calc_second_order=False)
            Si_p_s2 = sobol_analyze.analyze(problem, df["mean_p_s2"].values, calc_second_order=False)

            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            width = 0.35
            x = np.arange(len(sobol_params))
            for ax, (Si, qoi, title) in zip(
                axes,
                [
                    (Si_evac, "evacuation_rate", "evacuation_rate"),
                    (Si_p_s2, "mean_p_s2", "mean_p_s2"),
                ],
            ):
                first = Si["S1"]
                total = Si["ST"]
                ax.bar(x - width / 2, first, width, label="First order")
                ax.bar(x + width / 2, total, width, label="Total effect")
                ax.set_xticks(x)
                ax.set_xticklabels([r"$\alpha$", r"$\beta$", r"$p_{S2}$", "topology"])
                ax.set_ylabel("Sobol index")
                ax.set_title(title)
                ax.legend()
                ax.grid(True, alpha=0.3, axis="y")
                ax.set_ylim(0, 1.05)
            fig.suptitle("First-order and total-effect Sobol indices", y=1.02)
            fig.tight_layout()
            fig.savefig(fig_dir / "sobol_indices.png", dpi=args.dpi, bbox_inches="tight")
            fig.savefig(fig_dir / "sobol_indices.pdf", bbox_inches="tight")
            plt.close(fig)
            print(f"  Saved sobol_indices.png/.pdf")
            sobol_done = True
    except ImportError:
        pass
    except Exception as e:
        pass

    # Fallback: EasyVVUQ QMCAnalysis if available
    if not sobol_done:
        try:
            import easyvvuq as uq
            db_paths = list(campaign_dir.rglob("campaign.db"))
            if db_paths:
                db_path = db_paths[0]
                campaign = uq.Campaign(
                    name="s1s2_sensitivity",
                    db_location=f"sqlite:///{db_path}",
                    work_dir=str(campaign_dir),
                )
                campaign.set_app("s1s2_sensitivity")
                last = campaign.get_last_analysis()
                if last is not None and hasattr(last, "sobols_first"):
                    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
                    width = 0.35
                    for ax, qoi in zip(axes, qois):
                        first = [float(np.atleast_1d(last.sobols_first(qoi, p))[0]) for p in sobol_params]
                        total = [float(np.atleast_1d(last.sobols_total(qoi, p))[0]) for p in sobol_params]
                        x = np.arange(len(sobol_params))
                        ax.bar(x - width / 2, first, width, label="First order")
                        ax.bar(x + width / 2, total, width, label="Total effect")
                        ax.set_xticks(x)
                        ax.set_xticklabels([r"$\alpha$", r"$\beta$", r"$p_{S2}$", "topology"])
                        ax.set_ylabel("Sobol index")
                        ax.set_title(qoi)
                        ax.legend()
                        ax.grid(True, alpha=0.3, axis="y")
                    fig.suptitle("First-order and total-effect Sobol indices", y=1.02)
                    fig.tight_layout()
                    fig.savefig(fig_dir / "sobol_indices.png", dpi=args.dpi, bbox_inches="tight")
                    fig.savefig(fig_dir / "sobol_indices.pdf", bbox_inches="tight")
                    plt.close(fig)
                    print(f"  Saved sobol_indices.png/.pdf")
                    sobol_done = True
        except Exception:
            pass

    if not sobol_done:
        print("  No Sobol analysis (run: python run_easyvvuq_campaign.py --sobol, pip install SALib)")

    # 6. Topology maps: network layouts with evacuation stats (presentation-ready)
    try:
        topo_dir_base = repo_root / "topologies"
        topo_order = ["ring", "star", "linear"]
        evac_means = {}
        if "topology_name" in df.columns:
            for t in topo_order:
                sub = df[df["topology_name"] == t]
                evac_means[t] = sub["evacuation_rate"].mean() * 100 if len(sub) else 0

        fig, axes = plt.subplots(1, 3, figsize=(14, 5))
        fig.patch.set_facecolor("white")
        for ax, topo in zip(axes, topo_order):
            topo_dir = topo_dir_base / topo / "input_csv"
            if not topo_dir.exists():
                ax.axis("off")
                ax.text(0.5, 0.5, f"{topo}\n(no data)", ha="center", va="center")
                continue
            locs = pd.read_csv(topo_dir / "locations.csv")
            routes = pd.read_csv(topo_dir / "routes.csv")
            coord = {row["name"]: (float(row["gps_x"]), float(row["gps_y"])) for _, row in locs.iterrows()}
            # Draw edges
            for _, row in routes.iterrows():
                n1, n2 = row["name1"], row["name2"]
                if n1 in coord and n2 in coord:
                    ax.plot([coord[n1][0], coord[n2][0]], [coord[n1][1], coord[n2][1]], "k-", lw=0.8, alpha=0.4, zorder=0)
            # Draw nodes by type
            for _, row in locs.iterrows():
                x, y = float(row["gps_x"]), float(row["gps_y"])
                name = row["name"]
                loc_type = str(row.get("location_type", "town")).lower()
                if "camp" in loc_type or "SafeZone" in name:
                    ax.scatter(x, y, s=120, c="#27ae60", marker="s", edgecolors="white", linewidths=1.5, zorder=3, label="Safe zone" if name == locs.iloc[0]["name"] else "")
                elif "conflict" in loc_type or "Facility" in name or "Hub" in name:
                    ax.scatter(x, y, s=200, c="#e74c3c", marker="^", edgecolors="white", linewidths=1.5, zorder=3, label="Origin" if name == locs.iloc[0]["name"] else "")
                else:
                    ax.scatter(x, y, s=40, c="#3498db", alpha=0.7, edgecolors="white", linewidths=0.5, zorder=2)
            evac = evac_means.get(topo, 0)
            ax.set_title(f"{topo.capitalize()}\n{evac:.0f}% evacuated", fontsize=12, fontweight="bold")
            ax.set_aspect("equal")
            ax.axis("off")
        fig.suptitle("Evacuation network topologies — S1/S2 dual-process model", fontsize=14, fontweight="bold", y=1.02)
        fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.02, wspace=0.15)
        fig.savefig(fig_dir / "presentation_summary.png", dpi=200, bbox_inches="tight", facecolor="white")
        fig.savefig(fig_dir / "presentation_summary.pdf", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"  Saved presentation_summary.png/.pdf (topology maps)")
    except Exception as e:
        print(f"  Topology maps skipped: {e}")

    print(f"\nFigures saved to: {fig_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
