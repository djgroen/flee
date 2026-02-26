#!/usr/bin/env python3
"""
Single run for EasyVVUQ: reads params from input.json, runs S1/S2 simulation, writes output.json.
Called by EasyVVUQ executor with run directory as cwd.
"""
import json
import sys
from pathlib import Path

# Add repo root
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

def main():
    run_dir = Path.cwd().resolve()
    # Config uses relative paths; run from repo root so topologies/ resolves
    import os
    os.chdir(repo_root)
    input_file = run_dir / "input.json"
    if not input_file.exists():
        print("ERROR: input.json not found in", run_dir, file=sys.stderr)
        sys.exit(1)
    with open(input_file) as f:
        params = json.load(f)
    alpha = float(params["alpha"])
    beta = float(params["beta"])
    p_s2 = float(params.get("p_s2", 0.8))
    topology_raw = params.get("topology", "ring")
    # Map 0,1,2 to ring,star,linear (EasyVVUQ samples topology as int)
    if isinstance(topology_raw, (int, float)):
        topology = ["ring", "star", "linear"][int(topology_raw) % 3]
    else:
        topology = str(topology_raw)
    seed = int(params.get("seed", 0))
    n_timesteps = int(params.get("n_timesteps", 100))
    n_agents = int(params.get("n_agents", 500))

    from run_nuclear_parameter_sweep import ParameterSweeper
    import yaml

    config_dir = repo_root / "data" / "fork_experiments" / "configs"
    config_file = config_dir / f"{topology}_small.yml"
    if not config_file.exists():
        config_file = repo_root / "configs" / f"{topology}_topology.yml"
    with open(config_file) as f:
        config = yaml.safe_load(f)
    config["simulation"]["n_agents"] = n_agents
    config["simulation"]["n_timesteps"] = n_timesteps
    config["move_rules"]["s1s2_model"]["alpha"] = alpha
    config["move_rules"]["s1s2_model"]["beta"] = beta
    config["move_rules"]["s1s2_model"]["p_s2"] = p_s2

    output_dir = run_dir
    sweeper = ParameterSweeper(output_base_dir=str(run_dir))
    temp_config = output_dir / "temp_config.yml"
    with open(temp_config, "w") as f:
        yaml.dump(config, f)

    res_path = sweeper.run_single_simulation(topology, temp_config, alpha, beta, seed, output_dir)
    if temp_config.exists():
        temp_config.unlink()

    df = __import__("pandas").read_csv(res_path)
    last = df[df["timestep"] == df["timestep"].max()]
    n = len(last)
    evacuated = last["location"].astype(str).str.contains("SafeZone", na=False).sum()
    evacuation_rate = evacuated / n if n else 0.0
    mean_p_s2 = float(df["p_s2"].mean())

    output = {"evacuation_rate": evacuation_rate, "mean_p_s2": mean_p_s2}
    with open(run_dir / "output.json", "w") as f:
        json.dump(output, f, indent=2)
    return 0

if __name__ == "__main__":
    sys.exit(main())
