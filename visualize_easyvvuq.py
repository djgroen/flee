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
- sobol_indices.png: first-order Sobol indices (if QMC/MC sampler was used)
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

    # 5. Sobol indices (only if QMC/MC sampler was used)
    # RandomSampler does not produce Sobol indices. For Sobol, re-run with:
    #   sampler = uq.sampling.QMCSampler(vary=vary, n_mc_samples=256)
    #   campaign.set_sampler(sampler)
    # then run campaign and apply QMCAnalysis
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
                sobol_params = [p for p in ["alpha", "beta", "p_s2", "topology"] 
                                if p in (last.inputs if hasattr(last, "inputs") else [])]
                if not sobol_params:
                    sobol_params = ["alpha", "beta", "p_s2"]
                for qoi in qois:
                    try:
                        first = [float(last.sobols_first(qoi, p)) for p in sobol_params]
                        total = [float(last.sobols_total(qoi, p)) for p in sobol_params]
                        x = np.arange(len(sobol_params))
                        width = 0.35
                        fig, ax = plt.subplots(figsize=(6, 4))
                        ax.bar(x - width / 2, first, width, label="First order")
                        ax.bar(x + width / 2, total, width, label="Total order")
                        ax.set_xticks(x)
                        ax.set_xticklabels(sobol_params)
                        ax.set_ylabel("Sobol index")
                        ax.set_title(f"Sensitivity indices: {qoi}")
                        ax.legend()
                        ax.grid(True, alpha=0.3, axis="y")
                        fig.tight_layout()
                        fig.savefig(
                            fig_dir / f"sobol_{qoi}.png",
                            dpi=args.dpi,
                            bbox_inches="tight",
                        )
                        plt.close(fig)
                        print(f"  Saved sobol_{qoi}.png")
                    except Exception:
                        pass
            else:
                print("  No Sobol analysis (run: python run_easyvvuq_campaign.py --sobol)")
        else:
            print("  No campaign.db found; skipping Sobol plots")
    except Exception:
        print("  No Sobol analysis (run: python run_easyvvuq_campaign.py --sobol)")

    print(f"\nFigures saved to: {fig_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
