#!/usr/bin/env python3
"""
EasyVVUQ sensitivity analysis for S1/S2 parameters (alpha, beta, p_s2).
Runs a campaign, computes basic stats and optionally Sobol indices.

Usage:
  pip install easyvvuq chaospy
  python run_easyvvuq_campaign.py              # quick run, 16 samples (ring/star/linear)
  python run_easyvvuq_campaign.py --sobol       # Sobol indices (~200 runs)
  python run_easyvvuq_campaign.py -n 64         # 64 random samples
  python run_easyvvuq_campaign.py --diagnostic-only  # sampler uniformity check only

Topology is varied: 0=ring, 1=star, 2=linear.

Then visualize:
  python visualize_easyvvuq.py

Omega vs beta diagnostic (model nonlinearity):
  python run_omega_diagnostic.py

Output: data/easyvvuq/s1s2_campaign/ with results, figures/, and diagnostic_sampling.png.
"""
import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

def main():
    parser = argparse.ArgumentParser(description="EasyVVUQ S1/S2 sensitivity campaign")
    parser.add_argument("-n", "--samples", type=int, default=16, help="Number of samples")
    parser.add_argument("--sobol", action="store_true", help="Use MCSampler for Sobol indices")
    parser.add_argument("--diagnostic-only", action="store_true", help="Run sampler diagnostic only, no simulations")
    args = parser.parse_args()

    try:
        import easyvvuq as uq
        import chaospy as cp
        import numpy as np
        from scipy import stats as scipy_stats
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        print("Install EasyVVUQ and chaospy: pip install easyvvuq chaospy")
        print("Error:", e)
        return 1

    campaign_dir = repo_root / "data" / "easyvvuq" / "s1s2_campaign"
    campaign_dir.mkdir(parents=True, exist_ok=True)

    # Parameters (topology: 0=ring, 1=star, 2=linear)
    params = {
        "alpha": {"default": 2.0, "min": 0.5, "max": 4.0, "type": "float"},
        "beta": {"default": 2.0, "min": 0.5, "max": 4.0, "type": "float"},
        "p_s2": {"default": 0.8, "min": 0.3, "max": 1.0, "type": "float"},
        "topology": {"default": 0, "min": 0, "max": 2, "type": "integer"},
        "seed": {"default": 0, "type": "integer"},
        "n_timesteps": {"default": 100, "type": "integer"},
        "n_agents": {"default": 500, "type": "integer"},
    }

    vary = {
        "alpha": cp.Uniform(0.5, 4.0),
        "beta": cp.Uniform(0.5, 4.0),
        "p_s2": cp.Uniform(0.3, 1.0),
        "topology": cp.DiscreteUniform(0, 2),  # 0=ring, 1=star, 2=linear
    }

    # --- Task 1: Diagnostic block (checks sampler output before any simulation) ---
    n_samples = args.samples
    if args.sobol:
        n_mc = max(32, n_samples)
        diag_sampler = uq.sampling.MCSampler(vary=vary, n_mc_samples=n_mc)
        diag_samples = []
        try:
            while True:
                diag_samples.append(next(diag_sampler))
        except StopIteration:
            pass
    else:
        diag_sampler = uq.sampling.RandomSampler(vary=vary)
        diag_samples = [next(diag_sampler) for _ in range(n_samples)]
    alpha_arr = np.array([s["alpha"] for s in diag_samples])
    beta_arr = np.array([s["beta"] for s in diag_samples])
    p_s2_arr = np.array([s["p_s2"] for s in diag_samples])

    param_configs = [
        ("alpha", alpha_arr, 0.5, 4.0),
        ("beta", beta_arr, 0.5, 4.0),
        ("p_s2", p_s2_arr, 0.3, 1.0),
    ]
    print("\n=== Sampler diagnostic (raw samples, before simulation) ===")
    beta_ks_pvalue = None
    for name, arr, low, high in param_configs:
        ks_stat, ks_pvalue = scipy_stats.kstest(arr, "uniform", args=(low, high - low))
        if name == "beta":
            beta_ks_pvalue = ks_pvalue
        print(f"  {name}: min={arr.min():.4f} max={arr.max():.4f} mean={arr.mean():.4f} std={arr.std():.4f}")
        print(f"         KS stat={ks_stat:.4f} p-value={ks_pvalue:.4f} {'(uniform OK)' if ks_pvalue > 0.05 else '(REJECT uniform)'}")

    # Task 3: Assert uniform beta coverage; if failed, fall back to rule='random' for uniformity
    use_random_rule = False
    if beta_ks_pvalue is not None and beta_ks_pvalue <= 0.05:
        print("\nWARNING: Beta sampler rejected uniformity (KS p < 0.05). Using rule='random' for MCSampler.")
        use_random_rule = True

    # Save diagnostic_sampling.png
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    for ax, (name, arr, low, high) in zip(axes, param_configs):
        ax.hist(arr, bins=min(30, max(10, len(arr) // 5)), density=True, alpha=0.7, color="steelblue", edgecolor="white")
        try:
            kde = scipy_stats.gaussian_kde(arr)
            x = np.linspace(low, high, 200)
            ax.plot(x, kde(x), "b-", lw=2, label="KDE")
        except Exception:
            pass
        ax.axhline(1.0 / (high - low), color="black", ls="--", lw=1.5, label="Uniform")
        ks_stat, ks_pvalue = scipy_stats.kstest(arr, "uniform", args=(low, high - low))
        ax.set_title(f"{name}\nKS={ks_stat:.3f} p={ks_pvalue:.3f}")
        ax.set_xlabel(name)
        ax.set_ylabel("density")
        ax.legend(loc="upper right", fontsize=8)
        ax.set_xlim(low, high)
    fig.suptitle("Sampler output diagnostic (raw parameter samples)")
    fig.tight_layout()
    diag_path = campaign_dir / "figures" / "diagnostic_sampling.png"
    diag_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(diag_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {diag_path}")

    if args.diagnostic_only:
        return 0

    # Use built-in encoder/decoder (EasyVVUQ 1.3 uses actions, not encoder/decoder in add_app)
    template_path = repo_root / "input.json.template"
    encoder = uq.encoders.GenericEncoder(
        template_fname=str(template_path),
        target_filename="input.json",
    )
    decoder = uq.decoders.JSONDecoder(
        target_filename="output.json",
        output_columns=["evacuation_rate", "mean_p_s2"],
    )
    single_script = repo_root / "run_easyvvuq_single.py"
    cmd = f"python {single_script}"
    actions = uq.actions.local_execute(
        encoder, cmd, decoder, root=str(campaign_dir)
    )

    campaign = uq.Campaign(
        name="s1s2_sensitivity",
        work_dir=str(campaign_dir),
        params=params,
        actions=actions,
    )

    # Create fresh sampler for campaign (diagnostic consumed the previous one)
    if args.sobol:
        sampler = uq.sampling.MCSampler(
            vary=vary,
            n_mc_samples=n_mc,
            rule="random" if use_random_rule else "latin_hypercube",
        )
        campaign.set_sampler(sampler)
        print(f"Sobol mode: MCSampler with n_mc={n_mc} (~{n_mc * 5} runs)")
    else:
        sampler = uq.sampling.RandomSampler(vary=vary)
        campaign.set_sampler(sampler)

    campaign.execute(nsamples=0 if args.sobol else n_samples).collate()
    df = campaign.get_collation_result()
    # Map topology 0,1,2 -> ring,star,linear for readability
    if "topology" in df.columns:
        def _topo_name(x):
            try:
                return ["ring", "star", "linear"][int(float(x)) % 3]
            except (ValueError, TypeError):
                return "ring"
        df["topology_name"] = df["topology"].apply(_topo_name)
    print("\n=== Collated results ===")
    cols = ["alpha", "beta", "p_s2", "topology_name", "evacuation_rate", "mean_p_s2"]
    cols = [c for c in cols if c in df.columns]
    print(df[cols].to_string())

    # Basic stats
    try:
        stats = uq.analysis.BasicStats(qoi_cols=["evacuation_rate", "mean_p_s2"])
        campaign.apply_analysis(stats)
        print("\n=== Basic statistics ===")
        print(campaign.get_last_analysis())
    except Exception as e:
        print("BasicStats failed:", e)

    # Sobol indices (only when using MCSampler)
    if args.sobol:
        try:
            qmc_analysis = uq.analysis.QMCAnalysis(
                sampler=sampler,
                qoi_cols=["evacuation_rate", "mean_p_s2"],
            )
            campaign.apply_analysis(qmc_analysis)
            sobol = campaign.get_last_analysis()
            sobol_params = ["alpha", "beta", "p_s2", "topology"]
            print("\n=== First-order Sobol indices (evacuation_rate) ===")
            for p in sobol_params:
                print(f"  {p}: {sobol.sobols_first('evacuation_rate', p):.4f}")
            print("\n=== Total-order Sobol indices (evacuation_rate) ===")
            for p in sobol_params:
                print(f"  {p}: {sobol.sobols_total('evacuation_rate', p):.4f}")
            print("\nRun: python visualize_easyvvuq.py  # for Sobol bar charts")
        except Exception as e:
            print("QMCAnalysis failed:", e)

    # Save collated CSV
    out_csv = campaign_dir / "collated_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
