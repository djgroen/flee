#!/usr/bin/env python3
"""
Run four model variants across topologies: original FLEE, S1-only, S2-only, full S1/S2.
Outputs to data/model_comparison/{topology}/{variant}/ for diagnostic plotting.

Variants:
  1. original  — two_system_decision_making: false (baseline FLEE, S1/S2 block never entered)
  2. s1_only   — two_system: true, α≈0, β→∞ → P_S2≈0 (heuristic only; designed to match original)
  3. s2_only   — two_system: true, α→∞, β≈0 → P_S2≈1 (deliberative only)
  4. full_s1s2 — two_system: true, α=2, β=2, κ=5 (full mixture)

Note: original and s1_only are designed to be identical (sanity check). If they differ, that's a bug.

Caveat: Original FLEE route selection uses AwarenessLevel (default 1) to look beyond immediate
neighbors when scoring routes — so it has deliberative/look-ahead elements. S2 mode increases
AwarenessLevel further. The S1/S2 distinction here is mainly move probability (location vs
safety-differential), not routing look-ahead.

Usage:
  python generate_nuclear_topologies.py   # if topologies/ missing
  python run_model_comparison.py
  python create_model_diagnostic_plots.py
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
import yaml
import shutil

sys.path.insert(0, str(Path(__file__).parent))

from flee import flee
from flee.SimulationSettings import SimulationSettings
from flee.flee import Person

VARIANTS = {
    "original": {
        "two_system_decision_making": False,
        "s1s2_model": {"alpha": 2.0, "beta": 2.0, "kappa": 5.0},
    },
    "s1_only": {
        "two_system_decision_making": True,
        "s1s2_model": {"alpha": 0.001, "beta": 100.0, "kappa": 5.0},
    },
    "s2_only": {
        "two_system_decision_making": True,
        "s1s2_model": {"alpha": 100.0, "beta": 0.001, "kappa": 5.0},
    },
    "full_s1s2": {
        "two_system_decision_making": True,
        "s1s2_model": {"alpha": 2.0, "beta": 2.0, "kappa": 5.0},
    },
}


def load_topology(input_dir):
    """Load locations and routes from CSV files."""
    input_dir = Path(input_dir) / "input_csv"
    locations = pd.read_csv(input_dir / "locations.csv")
    routes = pd.read_csv(input_dir / "routes.csv")
    return locations, routes


def run_single_simulation(topology_name, config_file, variant_name, seed, output_dir):
    """Run one FLEE simulation for a given model variant."""
    with open(config_file) as f:
        config = yaml.safe_load(f)

    variant = VARIANTS[variant_name]
    config["move_rules"]["two_system_decision_making"] = variant["two_system_decision_making"]
    config["move_rules"]["s1s2_model"] = variant["s1s2_model"].copy()

    temp_config_path = output_dir / f"temp_config_{variant_name}_s{seed}.yml"
    with open(temp_config_path, "w") as f:
        yaml.dump(config, f)

    SimulationSettings.ReadFromYML(str(temp_config_path))

    ecosystem = flee.Ecosystem()
    import random
    random.seed(seed)
    np.random.seed(seed)

    input_dir = config["network"]["input_dir"]
    input_dir_path = Path(input_dir) / "input_csv"
    locations_df, routes_df = load_topology(input_dir)

    location_map = {}
    for _, loc in locations_df.iterrows():
        location = ecosystem.addLocation(
            name=loc["name"],
            x=loc["gps_x"],
            y=loc["gps_y"],
            location_type=loc["location_type"],
            movechance=loc["movechance"],
            capacity=loc["capacity"],
            pop=0,
        )
        location_map[loc["name"]] = location

    for _, loc_row in locations_df.iterrows():
        if loc_row["name"] in location_map:
            location_map[loc_row["name"]].conflict = loc_row.get("conflict", 0.0)

    conflicts_file = input_dir_path / "conflicts.csv"
    if conflicts_file.exists():
        conf_df = pd.read_csv(
            conflicts_file,
            comment="#",
            header=None,
            names=["date", "loc", "val"],
            skipinitialspace=True,
        )
        for _, row in conf_df.iterrows():
            if row["loc"] in location_map:
                location_map[row["loc"]].conflict = float(row["val"])

    for _, route in routes_df.iterrows():
        ecosystem.linkUp(route["name1"], route["name2"], route["distance"])

    spawn_location_name = config["agents"]["spawn_location"]
    spawn_location = location_map[spawn_location_name]
    n_agents = config["simulation"]["n_agents"]

    agents = []
    for i in range(n_agents):
        agent = Person(spawn_location, {})
        ecosystem.agents.append(agent)
        agents.append(agent)

    header = "Day,Date,"
    for loc in ecosystem.locations:
        header += f"{loc.name} sim,"
    header += "Total refugees\n"

    out_csv_path = output_dir / f"out_{variant_name}_s{seed}.csv"
    with open(out_csv_path, "w") as f:
        f.write(header)

    n_timesteps = config["simulation"]["n_timesteps"]
    history = []

    old_cwd = os.getcwd()
    os.chdir(str(output_dir))

    try:
        for t in range(n_timesteps):
            ecosystem.evolve()

            line = f"{t},{ecosystem.date_string},"
            total_pop = 0
            for loc in ecosystem.locations:
                line += f"{loc.numAgents},"
                total_pop += loc.numAgents
            line += f"{total_pop}\n"
            with open(out_csv_path.name, "a") as f:
                f.write(line)

            for agent in agents:
                conflict = (
                    getattr(agent.location, "conflict", 0.0)
                    if agent.location and hasattr(agent.location, "conflict")
                    else 0.0
                )
                conflict = max(0.0, conflict)
                history.append({
                    "timestep": t,
                    "agent_id": id(agent),
                    "location": agent.location.name if agent.location else "None",
                    "p_s2": getattr(agent, "s2_activation_prob", 0.0),
                    "experience": agent.experience_index,
                    "conflict": conflict,
                    "variant": variant_name,
                    "topology": topology_name,
                })

        if os.path.exists("agents.out.0"):
            shutil.move("agents.out.0", f"agents_{variant_name}_s{seed}.out")
    finally:
        os.chdir(old_cwd)

    results_df = pd.DataFrame(history)
    results_path = output_dir / f"results_{variant_name}_s{seed}.csv"
    results_df.to_csv(results_path, index=False)

    if temp_config_path.exists():
        temp_config_path.unlink()

    return results_path


def main():
    import argparse
    p = argparse.ArgumentParser(description="Run 4 model variants (original, S1-only, S2-only, full S1/S2) across topologies.")
    p.add_argument("--quick", action="store_true", help="Use 500 agents, 15 timesteps for fast testing")
    args = p.parse_args()

    base = Path("data/model_comparison")
    base.mkdir(parents=True, exist_ok=True)

    topologies = ["ring", "linear", "star"]
    config_dir = Path("configs")
    seed = 0

    for topology in topologies:
        config_file = config_dir / f"{topology}_topology.yml"
        if not config_file.exists():
            print(f"  Skip {topology}: config not found")
            continue

        if args.quick:
            with open(config_file) as f:
                cfg = yaml.safe_load(f)
            cfg["simulation"]["n_agents"] = 500
            cfg["simulation"]["n_timesteps"] = 15
            quick_config = base / "configs" / f"{topology}_quick.yml"
            quick_config.parent.mkdir(parents=True, exist_ok=True)
            with open(quick_config, "w") as f:
                yaml.dump(cfg, f)
            config_file = quick_config

        for variant_name in VARIANTS:
            output_dir = base / topology / variant_name
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"  {topology} / {variant_name}...", end=" ", flush=True)
            try:
                run_single_simulation(topology, config_file, variant_name, seed, output_dir)
                print("OK")
            except Exception as e:
                print(f"FAIL: {e}")
                import traceback
                traceback.print_exc()

    print(f"\nDone. Results in {base}/")
    print("Next: python create_model_diagnostic_plots.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
