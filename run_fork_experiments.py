#!/usr/bin/env python3
"""
Run S1/S2 experiments on your fork: ring, star, linear topologies with varying α, β.
Results go to data/experiments/ for analysis and plotting.
Run from repo root: python run_fork_experiments.py
"""
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

def main():
    from run_nuclear_parameter_sweep import ParameterSweeper

    base = Path("data/experiments")
    base.mkdir(parents=True, exist_ok=True)
    config_dir = base / "configs"
    config_dir.mkdir(exist_ok=True)

    # Small configs for quick runs (override n_agents, n_timesteps)
    topo_configs = {
        "ring": Path("configs/ring_topology.yml"),
        "star": Path("configs/star_topology.yml"),
        "linear": Path("configs/linear_topology.yml"),
    }
    n_agents = 500
    n_timesteps = 100
    for name, src in topo_configs.items():
        with open(src) as f:
            c = yaml.safe_load(f)
        c["simulation"]["n_agents"] = n_agents
        c["simulation"]["n_timesteps"] = n_timesteps
        out = config_dir / f"{name}_small.yml"
        with open(out, "w") as f:
            yaml.dump(c, f)

    sweeper = ParameterSweeper(output_base_dir=str(base))
    alpha_range = [1.0, 2.0]
    beta_range = [1.0, 2.0]
    n_replicates = 1
    seeds = list(range(n_replicates))

    for topology in topo_configs:
        config_file = config_dir / f"{topology}_small.yml"
        output_dir = base / topology
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {topology} topology ===")
        for alpha in alpha_range:
            for beta in beta_range:
                for seed in seeds:
                    print(f"  α={alpha}, β={beta}, seed={seed}")
                    try:
                        res = sweeper.run_single_simulation(
                            topology, config_file, alpha, beta, seed, output_dir
                        )
                        m = sweeper.extract_metrics(res, topology, alpha, beta, seed)
                        sweeper.summary_results.append(m)
                    except Exception as e:
                        print(f"  FAIL: {e}")
                        import traceback
                        traceback.print_exc()

    if sweeper.summary_results:
        import pandas as pd
        summary_df = pd.DataFrame(sweeper.summary_results)
        summary_path = base / "parameter_sweep_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"\n✅ Summary saved to {summary_path}")
    print("\nNext: python analyze_fork_experiments.py  (reads data/experiments/)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
