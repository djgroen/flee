#!/usr/bin/env python3
"""
Task 2 diagnostic: Run single simulations with varying beta, collect Omega values,
plot distribution of Omega vs beta to check if Omega(beta) is nonlinear (sigmoid).

Output: data/easyvvuq/s1s2_campaign/figures/omega_vs_beta_diagnostic.png
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

from run_nuclear_parameter_sweep import ParameterSweeper


def main():
    campaign_dir = repo_root / "data" / "easyvvuq" / "s1s2_campaign"
    omega_dir = campaign_dir / "omega_diagnostic"
    omega_dir.mkdir(parents=True, exist_ok=True)

    # Beta values spanning the prior [0.5, 4.0]
    beta_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    alpha = 2.0
    seed = 0
    topology = "ring"

    config_dir = repo_root / "data" / "fork_experiments" / "configs"
    config_file = config_dir / f"{topology}_small.yml"
    if not config_file.exists():
        config_file = repo_root / "configs" / f"{topology}_topology.yml"

    sweeper = ParameterSweeper(output_base_dir=str(omega_dir))
    all_omega = []

    for beta in beta_values:
        print(f"Running beta={beta} ...")
        res_path = sweeper.run_single_simulation(topology, config_file, alpha, beta, seed, omega_dir)
        df = pd.read_csv(res_path)
        df["beta_input"] = beta
        all_omega.append(df[["beta_input", "omega", "conflict"]].copy())

    combined = pd.concat(all_omega, ignore_index=True)

    # Plot: distribution of Omega vs beta input
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: violin/box plot of Omega distribution per beta
    ax = axes[0]
    parts = ax.violinplot(
        [combined[combined["beta_input"] == b]["omega"].values for b in beta_values],
        positions=range(len(beta_values)),
        showmeans=True,
        showmedians=True,
    )
    ax.set_xticks(range(len(beta_values)))
    ax.set_xticklabels([str(b) for b in beta_values])
    ax.set_xlabel("beta (input)")
    ax.set_ylabel("Omega")
    ax.set_title("Distribution of Ω(conflict; β) across agents/timesteps")
    ax.set_ylim(-0.05, 1.05)
    ax.axhline(0.5, color="gray", ls="--", alpha=0.5)

    # Right: mean Omega vs beta (shows sigmoid shape)
    ax = axes[1]
    mean_omega = combined.groupby("beta_input")["omega"].mean()
    std_omega = combined.groupby("beta_input")["omega"].std()
    ax.errorbar(
        mean_omega.index,
        mean_omega.values,
        yerr=std_omega.values,
        fmt="o-",
        capsize=4,
        label="mean Ω ± std",
    )
    ax.set_xlabel("beta (input)")
    ax.set_ylabel("mean Omega")
    ax.set_title("Ω(β) nonlinearity: sigmoid in β×(1-conflict)")
    ax.legend()
    ax.set_ylim(-0.05, 1.05)

    fig.suptitle("Omega vs beta diagnostic: Ω(c;β)=sigmoid(β×(1-c)) is nonlinear in β")
    fig.tight_layout()
    out_path = campaign_dir / "figures" / "omega_vs_beta_diagnostic.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
