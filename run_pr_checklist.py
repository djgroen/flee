#!/usr/bin/env python3
"""
Minimal local checklist for S1/S2 PR: default-off and default-on runs.
Run from repo root: python run_pr_checklist.py
"""
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

def main():
    from run_nuclear_parameter_sweep import ParameterSweeper

    base_dir = Path("data/pr_checklist")
    base_dir.mkdir(parents=True, exist_ok=True)
    config_dir = base_dir / "configs"
    config_dir.mkdir(exist_ok=True)
    out_off = base_dir / "default_off"
    out_on = base_dir / "default_on"
    out_off.mkdir(exist_ok=True)
    out_on.mkdir(exist_ok=True)

    ring_config_path = Path("configs/ring_topology.yml")
    with open(ring_config_path) as f:
        config = yaml.safe_load(f)

    # Reduce size for quick run
    config["simulation"]["n_agents"] = 200
    config["simulation"]["n_timesteps"] = 5

    sweeper = ParameterSweeper(output_base_dir=str(base_dir))

    # --- 1. Default-off (S1/S2 disabled) ---
    config_off = config.copy()
    config_off["move_rules"] = dict(config["move_rules"])
    config_off["move_rules"]["two_system_decision_making"] = False
    config_off_path = config_dir / "ring_s1s2_off.yml"
    with open(config_off_path, "w") as f:
        yaml.dump(config_off, f)

    print("PR checklist 1/2: Running with two_system_decision_making=False (default-off)...")
    try:
        res_off = sweeper.run_single_simulation(
            topology_name="ring",
            config_file=config_off_path,
            alpha=2.0,
            beta=2.0,
            seed=0,
            output_dir=out_off,
        )
        print("  OK default-off run completed:", res_off)
    except Exception as e:
        print("  FAIL default-off:", e)
        return 1

    # --- 2. Default-on (S1/S2 enabled) ---
    config_on = config.copy()
    config_on["move_rules"] = dict(config["move_rules"])
    config_on["move_rules"]["two_system_decision_making"] = True
    config_on_path = config_dir / "ring_s1s2_on.yml"
    with open(config_on_path, "w") as f:
        yaml.dump(config_on, f)

    print("PR checklist 2/2: Running with two_system_decision_making=True (default-on)...")
    try:
        res_on = sweeper.run_single_simulation(
            topology_name="ring",
            config_file=config_on_path,
            alpha=2.0,
            beta=2.0,
            seed=0,
            output_dir=out_on,
        )
        print("  OK default-on run completed:", res_on)
    except Exception as e:
        print("  FAIL default-on:", e)
        return 1

    # Verify default-on output has p_s2
    import pandas as pd
    df = pd.read_csv(res_on)
    if "p_s2" not in df.columns:
        print("  FAIL default-on: results CSV missing 'p_s2' column")
        return 1
    print("  OK results contain 'p_s2' (S2 activation probability)")

    print("\nPR checklist passed. Safe to open PR.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
