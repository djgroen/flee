#!/usr/bin/env python3
"""
Parameter sweep over α and β for Fukushima (nuclear) scenario across Ring, Star, and Linear
topologies. Wraps the existing run logic from run_nuclear_parameter_sweep; does not modify
any existing simulation files.

Output: sweep_results.csv with columns
  alpha, beta, topology, peak_s2, peak_week, final_s2, three_phase_detected
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# So we can import from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_nuclear_parameter_sweep import ParameterSweeper

# Grid and scenario
ALPHA_VALUES = [0.2, 0.4, 0.6, 0.8, 1.0]
BETA_VALUES = [0.2, 0.4, 0.6, 0.8, 1.0]
TOPOLOGIES = ["ring", "star", "linear"]
SEED = 0

# S2 threshold used in FLEE (moving.py: system2_active = p_s2_active > 0.5)
S2_THRESHOLD = 0.5


def extract_sweep_metrics(result_path: Path) -> dict:
    """
    From a single run's results CSV (timestep, agent_id, p_s2, ...), compute:
    - peak_s2: max over time of (fraction of agents with p_s2 > S2_THRESHOLD)
    - peak_week: 0-based week index at which peak_s2 occurs (week = timestep // 7)
    - final_s2: S2 activation rate at last timestep
    - three_phase_detected: True if pattern S1→S2→S1 (low → high → low) is present
    """
    df = pd.read_csv(result_path)
    timesteps = sorted(df["timestep"].unique())
    if not timesteps:
        return {
            "peak_s2": np.nan,
            "peak_week": np.nan,
            "final_s2": np.nan,
            "three_phase_detected": False,
        }

    n_agents = len(df[df["timestep"] == timesteps[0]])
    if n_agents == 0:
        return {
            "peak_s2": np.nan,
            "peak_week": np.nan,
            "final_s2": np.nan,
            "three_phase_detected": False,
        }

    # Daily S2 activation rate (fraction of agents with p_s2 > threshold)
    daily_s2_rate = []
    for t in timesteps:
        at_t = df[df["timestep"] == t]
        frac_s2 = (at_t["p_s2"] > S2_THRESHOLD).mean()
        daily_s2_rate.append(frac_s2)

    peak_s2 = float(np.max(daily_s2_rate))
    peak_idx = int(np.argmax(daily_s2_rate))
    peak_timestep = timesteps[peak_idx]
    peak_week = peak_timestep // 7
    final_s2 = float(daily_s2_rate[-1])

    # Three-phase (S1→S2→S1): peak in the middle, with lower S2 in first and last quarters
    n = len(daily_s2_rate)
    if n < 4:
        three_phase_detected = False
    else:
        first_quarter = daily_s2_rate[: max(1, n // 4)]
        last_quarter = daily_s2_rate[-max(1, n // 4) :]
        mean_first = np.mean(first_quarter)
        mean_last = np.mean(last_quarter)
        peak_in_middle = (peak_idx >= n // 4) and (peak_idx < n - n // 4)
        three_phase_detected = (
            peak_in_middle
            and mean_first < peak_s2 * 0.85
            and mean_last < peak_s2 * 0.85
        )

    return {
        "peak_s2": peak_s2,
        "peak_week": peak_week,
        "final_s2": final_s2,
        "three_phase_detected": three_phase_detected,
    }


def main():
    output_base = Path("data/results")
    output_base.mkdir(parents=True, exist_ok=True)
    sweeper = ParameterSweeper(output_base_dir=str(output_base))

    total = len(ALPHA_VALUES) * len(BETA_VALUES) * len(TOPOLOGIES)
    current = 0
    rows = []

    for alpha in ALPHA_VALUES:
        for beta in BETA_VALUES:
            for topology in TOPOLOGIES:
                current += 1
                config_file = Path(__file__).resolve().parent / "configs" / f"{topology}_topology.yml"
                out_dir = output_base / topology
                out_dir.mkdir(parents=True, exist_ok=True)

                print(f"[{current}/{total}] α={alpha}, β={beta}, topology={topology} ... ", end="", flush=True)
                try:
                    result_path = sweeper.run_single_simulation(
                        topology_name=topology,
                        config_file=config_file,
                        alpha=alpha,
                        beta=beta,
                        seed=SEED,
                        output_dir=out_dir,
                    )
                    metrics = extract_sweep_metrics(result_path)
                    row = {
                        "alpha": alpha,
                        "beta": beta,
                        "topology": topology,
                        "peak_s2": metrics["peak_s2"],
                        "peak_week": metrics["peak_week"],
                        "final_s2": metrics["final_s2"],
                        "three_phase_detected": metrics["three_phase_detected"],
                    }
                    rows.append(row)
                    print(
                        f"peak_s2={row['peak_s2']:.3f} week={row['peak_week']} "
                        f"final_s2={row['final_s2']:.3f} 3phase={row['three_phase_detected']}"
                    )
                except Exception as e:
                    print(f"FAILED: {e}")
                    rows.append({
                        "alpha": alpha,
                        "beta": beta,
                        "topology": topology,
                        "peak_s2": np.nan,
                        "peak_week": np.nan,
                        "final_s2": np.nan,
                        "three_phase_detected": False,
                    })

    out_csv = output_base / "sweep_results.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\nSaved {out_csv} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
