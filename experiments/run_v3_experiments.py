#!/usr/bin/env python3
"""
V3 Dual-Process Experiments — Parameter sweeps, trajectories, and config generation.

Runs 6 experiments:
  1. Parameter sweep heatmaps (α × β)
  2. 72-hour conflict trajectory
  3. Non-compensability validation
  4. Population heterogeneity
  5. Generate simsetting.yml files for 4 comparison runs
  6. Topology comparison (ring, linear, star) — requires topologies/ from generate_nuclear_topologies.py

Usage:
  mkdir -p experiments/outputs
  python generate_nuclear_topologies.py   # if topologies/ missing
  python experiments/run_v3_experiments.py
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from flee.s1s2_model import (
    compute_capacity,
    compute_opportunity,
    compute_deliberation_weight,
    compute_s2_move_probability,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")


def experiment_1_heatmaps():
    """
    Experiment 1: Parameter sweep heatmaps for the V3 dual-process model.

    Generates heatmaps of:
      - Mean P_S2 across a synthetic agent population
      - Variance in P_S2 (heterogeneity measure)
      - Mean blended movechance

    Over grids of (α, β) at fixed κ.
    """
    print("Experiment 1: Parameter sweep heatmaps...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    N_AGENTS = 1000
    np.random.seed(42)
    experience_population = np.random.beta(2, 5, size=N_AGENTS)

    alphas = np.linspace(0.5, 5.0, 20)
    betas = np.linspace(0.5, 10.0, 20)
    kappa_fixed = 5.0

    def sweep_alpha_beta(conflict_level, kappa_fixed=5.0):
        mean_ps2 = np.zeros((len(betas), len(alphas)))
        var_ps2 = np.zeros((len(betas), len(alphas)))
        mean_blend = np.zeros((len(betas), len(alphas)))

        for i, beta in enumerate(betas):
            for j, alpha in enumerate(alphas):
                ps2_vals = []
                blend_vals = []
                for x in experience_population:
                    ps2 = compute_deliberation_weight(float(x), conflict_level, alpha, beta)
                    sigma = compute_s2_move_probability(conflict_level, 0.1, 2.0, kappa_fixed)
                    p_s1 = 0.3
                    blend = (1.0 - ps2) * p_s1 + ps2 * sigma
                    ps2_vals.append(ps2)
                    blend_vals.append(blend)
                mean_ps2[i, j] = np.mean(ps2_vals)
                var_ps2[i, j] = np.var(ps2_vals)
                mean_blend[i, j] = np.mean(blend_vals)

        return mean_ps2, var_ps2, mean_blend

    for c_label, c_val in [("low", 0.1), ("medium", 0.5), ("high", 0.9)]:
        mean_ps2, var_ps2, mean_blend = sweep_alpha_beta(c_val, kappa_fixed)

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        for ax, data, title in zip(
            axes,
            [mean_ps2, var_ps2, mean_blend],
            [f"Mean P_S2 (c={c_val})", f"Var P_S2 (c={c_val})", f"Mean P_move (c={c_val})"],
        ):
            im = ax.imshow(
                data,
                origin="lower",
                aspect="auto",
                extent=[alphas[0], alphas[-1], betas[0], betas[-1]],
            )
            ax.set_xlabel("α (capacity rate)")
            ax.set_ylabel("β (opportunity steepness)")
            ax.set_title(title)
            plt.colorbar(im, ax=ax)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, f"heatmap_alpha_beta_c{c_label}.png"), dpi=150)
        plt.close()

    print(f"  Saved heatmaps to {OUTPUT_DIR}/")


def experiment_2_trajectory():
    """
    Experiment 2: Conflict trajectory — 72-hour evacuation simulation.

    Synthetic scenario:
      - Agent starts at conflict=0.9 (near reactor)
      - Conflict decays as agent moves: c(t) = 0.9 * exp(-t/24)
      - Track P_S2, σ, and blended P_move over 72 hours

    Tests the two-phase prediction:
      Phase 1 (early): P_S2 suppressed by high conflict, heuristic flight
      Phase 2 (later): Ω recovers, P_S2 rises to agent's Ψ ceiling
    """
    print("Experiment 2: 72-hour conflict trajectory...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timesteps = np.arange(0, 73)

    agents = {
        "Novice (x=0.1)": 0.1,
        "Moderate (x=0.4)": 0.4,
        "Experienced (x=0.8)": 0.8,
    }

    alpha, beta, kappa = 2.0, 3.0, 5.0
    p_s1 = 0.3

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for label, x in agents.items():
        psi = compute_capacity(x, alpha)

        ps2_trace = []
        sigma_trace = []
        blend_trace = []
        omega_trace = []

        for t in timesteps:
            c_here = 0.9 * np.exp(-t / 24.0)
            c_best = max(0.0, c_here - 0.2)
            d_best = 2.0

            omega = compute_opportunity(c_here, beta)
            ps2 = psi * omega
            sigma = compute_s2_move_probability(c_here, c_best, d_best, kappa)
            blend = (1.0 - ps2) * p_s1 + ps2 * sigma

            omega_trace.append(omega)
            ps2_trace.append(ps2)
            sigma_trace.append(sigma)
            blend_trace.append(blend)

        axes[0, 0].plot(timesteps, omega_trace, label=label)
        axes[0, 1].plot(timesteps, ps2_trace, label=label)
        axes[1, 0].plot(timesteps, sigma_trace, label=label)
        axes[1, 1].plot(timesteps, blend_trace, label=label)

    for ax, title, ylabel in zip(
        axes.flat,
        ["Ω (Structural Opportunity)", "P_S2 (Deliberation Weight)", "σ (S2 Move Probability)", "P_move (Blended)"],
        ["Ω", "P_S2", "σ", "P_move"],
    ):
        ax.set_xlabel("Hours since evacuation onset")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        ax.set_xlim(0, 72)
        ax.set_ylim(0, 1.05)
        if "Blended" in title:
            ax.axhline(y=p_s1, color="gray", linestyle="--", alpha=0.5)
        ax.grid(True, alpha=0.3)

    plt.suptitle("V3 Dual-Process: 72-Hour Nuclear Evacuation Trajectory", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "trajectory_72hr.png"), dpi=150)
    plt.close()

    print(f"  Saved trajectory to {OUTPUT_DIR}/trajectory_72hr.png")


def experiment_3_non_compensability():
    """
    Experiment 3: Non-compensability validation.

    At high conflict (c > 0.9), increasing α should NOT meaningfully increase P_S2.
    """
    print("Experiment 3: Non-compensability validation...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    alphas = np.linspace(0.5, 10.0, 50)
    conflicts = [0.1, 0.3, 0.5, 0.7, 0.9, 0.99]
    beta = 3.0
    x_experienced = 0.8

    fig, ax = plt.subplots(figsize=(10, 6))
    for c in conflicts:
        ps2_vals = [compute_deliberation_weight(x_experienced, c, a, beta) for a in alphas]
        ax.plot(alphas, ps2_vals, label=f"c = {c}")

    ax.set_xlabel("α (capacity rate)")
    ax.set_ylabel("P_S2")
    ax.set_title("Non-Compensability: P_S2 vs α at varying conflict (experienced agent, x=0.8)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "non_compensability.png"), dpi=150)
    plt.close()

    print(f"  Saved to {OUTPUT_DIR}/non_compensability.png")


def experiment_4_heterogeneity():
    """
    Experiment 4: Population heterogeneity in P_S2.

    For Beta(2,5) experience distribution, show P_S2 distribution at different conflict levels.
    Variance is highest at intermediate conflict, lowest at extremes.
    """
    print("Experiment 4: Population heterogeneity...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    N = 5000
    np.random.seed(42)
    population_x = np.random.beta(2, 5, size=N)
    alpha, beta = 2.0, 3.0

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    conflicts = [0.0, 0.3, 0.6, 0.95]

    for ax, c in zip(axes, conflicts):
        ps2_vals = [compute_deliberation_weight(float(x), c, alpha, beta) for x in population_x]
        ax.hist(ps2_vals, bins=50, density=True, alpha=0.7, edgecolor="black", linewidth=0.5)
        ax.set_xlabel("P_S2")
        ax.set_ylabel("Density")
        ax.set_title(f"c = {c}\nmean={np.mean(ps2_vals):.3f}, var={np.var(ps2_vals):.4f}")
        ax.set_xlim(0, 1)

    plt.suptitle("Population P_S2 Distribution at Varying Conflict Levels", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "population_heterogeneity.png"), dpi=150)
    plt.close()

    print(f"  Saved to {OUTPUT_DIR}/population_heterogeneity.png")


def experiment_5_configs():
    """
    Experiment 5: Generate simsetting.yml files for the 4 comparison runs.

    Run 1: Original FLEE       — two_system_decision_making: false
    Run 2: S1-only             — alpha: 0.001, beta: 100 (P_S2 ≈ 0)
    Run 3: S2-only             — alpha: 100, beta: 0.001 (P_S2 ≈ 1)
    Run 4: Full mixture        — alpha: 2.0, beta: 3.0, kappa: 5.0
    """
    print("Experiment 5: Generate comparison run configs...")
    import yaml

    os.makedirs(CONFIG_DIR, exist_ok=True)

    base_config = {
        "log_levels": {"agent": 0, "link": 0, "camp": 0, "conflict": 0, "init": 0, "granularity": "location"},
        "spawn_rules": {"take_from_population": False, "insert_day0": True},
        "move_rules": {
            "max_move_speed": 360.0,
            "max_walk_speed": 35.0,
            "foreign_weight": 1.0,
            "camp_weight": 1.0,
            "conflict_weight": 0.25,
            "conflict_movechance": 1.0,
            "camp_movechance": 0.001,
            "default_movechance": 0.3,
            "awareness_level": 1,
            "capacity_scaling": 1.0,
            "avoid_short_stints": False,
            "start_on_foot": False,
            "weight_power": 1.0,
        },
        "optimisations": {"hasten": 1},
    }

    runs = {
        "run1_baseline": {
            "two_system_decision_making": False,
        },
        "run2_s1_only": {
            "two_system_decision_making": True,
            "s1s2_model": {"alpha": 0.001, "beta": 100.0, "kappa": 5.0},
        },
        "run3_s2_only": {
            "two_system_decision_making": True,
            "s1s2_model": {"alpha": 100.0, "beta": 0.001, "kappa": 5.0},
        },
        "run4_full_mixture": {
            "two_system_decision_making": True,
            "s1s2_model": {"alpha": 2.0, "beta": 3.0, "kappa": 5.0},
        },
    }

    for name, overrides in runs.items():
        config = yaml.safe_load(yaml.dump(base_config))
        config["move_rules"].update(overrides)
        path = os.path.join(CONFIG_DIR, f"simsetting_{name}.yml")
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"  Written: {path}")

    print("\n  Run each with: python run.py input_csv experiments/configs/simsetting_runN.yml")


def experiment_6_topology_comparison():
    """
    Experiment 6: Topology comparison (ring, linear, star).

    Runs quick FLEE simulations across topologies using ParameterSweeper.
    Requires: python generate_nuclear_topologies.py (topologies/ must exist).
    """
    print("Experiment 6: Topology comparison...")
    import yaml
    from pathlib import Path

    topo_output = os.path.join(OUTPUT_DIR, "topology_comparison")
    os.makedirs(topo_output, exist_ok=True)

    # Ensure topologies exist
    for topo in ["ring", "linear", "star"]:
        loc_path = Path(f"topologies/{topo}/input_csv/locations.csv")
        if not loc_path.exists():
            print(f"  WARNING: {loc_path} not found. Run: python generate_nuclear_topologies.py")
            return

    config_dir = Path(CONFIG_DIR)
    config_dir.mkdir(exist_ok=True)

    topologies = [
        ("ring", "configs/ring_topology.yml", "Facility"),
        ("linear", "configs/linear_topology.yml", "Facility"),
        ("star", "configs/star_topology.yml", "Hub"),
    ]

    from run_nuclear_parameter_sweep import ParameterSweeper

    sweeper = ParameterSweeper(output_base_dir=topo_output)
    alpha, beta, seed = 2.0, 2.0, 0

    for topo_name, config_path, _ in topologies:
        cfg_path = Path(config_path)
        if not cfg_path.exists():
            print(f"  Skip {topo_name}: {config_path} not found")
            continue
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
        cfg["simulation"]["n_agents"] = 200
        cfg["simulation"]["n_timesteps"] = 10
        quick_cfg = config_dir / f"topology_quick_{topo_name}.yml"
        with open(quick_cfg, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)

        out_dir = Path(topo_output) / topo_name
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            res = sweeper.run_single_simulation(topo_name, quick_cfg, alpha, beta, seed, out_dir)
            print(f"  {topo_name}: {res}")
        except Exception as e:
            print(f"  {topo_name}: FAILED - {e}")

    print(f"  Output: {topo_output}/")


def main():
    print("V3 Dual-Process Experiments\n" + "=" * 40)
    experiment_1_heatmaps()
    experiment_2_trajectory()
    experiment_3_non_compensability()
    experiment_4_heterogeneity()
    experiment_5_configs()
    experiment_6_topology_comparison()
    print("\nAll experiments complete.")


if __name__ == "__main__":
    main()
