#!/usr/bin/env python3
"""
Standardised harness for running all 4 decision modes on synthetic topologies.
Produces identical output schema for all modes for figure generation.
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Standardized output layout: output/results/synthetic/<topology>/
OUTPUT_ROOT = REPO_ROOT / "output"
DEFAULT_RESULTS_DIR = OUTPUT_ROOT / "results" / "synthetic"

from flee import flee
from flee import InputGeography
from flee.SimulationSettings import SimulationSettings
from flee.decision_engine import DecisionEngine
from flee.network_builder import build_network


def load_config(yml_path=None):
    """Load or create minimal simulation config."""
    if yml_path and Path(yml_path).exists():
        SimulationSettings.ReadFromYML(str(yml_path))
    else:
        for p in ["flee/simsetting.yml", "tests/empty.yml", "empty.yml"]:
            if (REPO_ROOT / p).exists():
                SimulationSettings.ReadFromYML(str(REPO_ROOT / p))
                break
    SimulationSettings.move_rules["MovechancePopBase"] = 10000.0
    SimulationSettings.move_rules["MovechancePopScaleFactor"] = 0.0
    SimulationSettings.move_rules["AwarenessLevel"] = 1
    SimulationSettings.move_rules["FixedRoutes"] = False
    SimulationSettings.move_rules["PruningThreshold"] = 1.0
    # Camps as true sinks: agents at safe zones never leave
    SimulationSettings.move_rules["CampMoveChance"] = 0.0
    # Prevent return to conflict/disaster zone
    SimulationSettings.move_rules["ConflictWeight"] = 0.01
    SimulationSettings.spawn_rules["conflict_driven_spawning"] = False
    SimulationSettings.spawn_rules["TakeFromPopulation"] = False
    SimulationSettings.log_levels["agent"] = 0
    SimulationSettings.log_levels["init"] = 0


def run_one(input_dir, mode, n_agents, n_steps, alpha, beta, kappa,
            run_seed, topology='linear'):
    """Run one simulation for given mode and seed."""
    load_config()
    SimulationSettings.ConflictInputFile = str(Path(input_dir) / "conflicts.csv")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True

    # Override decision mode AFTER ReadFromYML (YAML has decision_mode=blend by default)
    SimulationSettings.move_rules["decision_mode"] = mode
    SimulationSettings.move_rules["s1s2_model_params"] = {
        "alpha": alpha,
        "beta": beta,
        "kappa": kappa,
    }
    SimulationSettings.move_rules["decision_engine"] = DecisionEngine.create(
        mode,
        {"s1s2_model_params": SimulationSettings.move_rules["s1s2_model_params"]},
    )
    SimulationSettings.move_rules["s2_weight_override"] = None

    random.seed(run_seed)
    np.random.seed(run_seed)

    e = flee.Ecosystem()
    ig = InputGeography.InputGeography()
    ig.ReadLocationsFromCSV(str(Path(input_dir) / "locations.csv"))
    ig.ReadLinksFromCSV(str(Path(input_dir) / "routes.csv"))
    ig.ReadClosuresFromCSV(str(Path(input_dir) / "closures.csv"))
    if SimulationSettings.ConflictInputFile and Path(SimulationSettings.ConflictInputFile).exists():
        ig.ReadConflictInputCSV(SimulationSettings.ConflictInputFile)
    e, lm = ig.StoreInputGeographyInEcosystem(e)

    # Find conflict source and camp
    source_name = None
    camp_names = [k for k, v in lm.items() if getattr(v, "camp", False)]
    for name, loc in lm.items():
        if "conflict" in getattr(loc, "location_type", "").lower():
            source_name = name
            break
    if source_name is None:
        source_name = list(lm.keys())[0]
    source = lm[source_name]

    def _distribute_agents(e, lm, topology, n_agents_per_node, seed):
        """
        Place n_agents_per_node agents at each eligible location.
        Experience indices drawn from Beta(2,5): mean=0.28, skewed low,
        reflecting that most people have limited prior crisis experience.

        Eligible locations by topology:
          linear:         source + all towns (not camp)
          ring:           ring towns only (not source, not camp)
                          source is at centre with no residents
          star:           source + all spoke towns (not camp)
          fully_connected: all non-camp nodes
        """
        rng = np.random.default_rng(seed)

        all_names = list(lm.keys())

        if topology == 'ring':
            spawn_names = [
                n for n in all_names
                if 'source' not in n.lower()
                and 'camp' not in n.lower()
            ]
        else:
            spawn_names = [
                n for n in all_names
                if 'camp' not in n.lower()
            ]

        agents_added = []
        for loc_name in spawn_names:
            loc = lm[loc_name]
            exp_indices = rng.beta(2, 5, size=n_agents_per_node)
            for exp_idx in exp_indices:
                e.addAgent(location=loc, attributes={})
                a = e.agents[-1]
                a.experience_index = float(exp_idx)
                agents_added.append(a)

        print(f"  Distributed {len(agents_added)} agents across "
              f"{len(spawn_names)} locations "
              f"({n_agents_per_node} per node, topology={topology})")
        return agents_added

    _distribute_agents(e, lm, topology, n_agents, run_seed)

    # Source location distance for distance_from_source
    source_loc = source.endpoint if hasattr(source, "endpoint") else source

    agents_per_timestep = []
    for t in range(n_steps + 1):
        if t > 0:
            ig.AddNewConflictZones(e, t)
        e.evolve()

        row_agents = []
        for agent_id, a in enumerate(e.agents):
            loc = a.location
            if loc is None:
                continue
            ep = getattr(loc, "endpoint", loc)
            loc_name = getattr(ep, "name", str(loc))
            loc_type = getattr(ep, "location_type", "town")
            try:
                dist = source_loc.calculateDistance(loc)
            except Exception:
                dist = 0.0
            s2 = getattr(a, "s2_activation_prob", 0.0)
            moved = getattr(a, "places_travelled", 0) > 1
            row_agents.append({
                "agent_id": agent_id,
                "timestep": t,
                "location": loc_name,
                "location_type": loc_type,
                "decision_mode": mode,
                "s2_weight": s2,
                "moved": moved,
                "distance_from_source_km": dist,
            })
        agents_per_timestep.append((t, row_agents))

    # Compute first-departure timestep per agent
    first_departure = {}
    for t, rows in agents_per_timestep:
        for r in rows:
            aid = r["agent_id"]
            if r["moved"] and aid not in first_departure:
                first_departure[aid] = t

    return agents_per_timestep, first_departure, lm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topology", default="linear")
    ap.add_argument("--n-nodes", type=int, default=6)
    ap.add_argument("--modes", nargs="+", default=["original", "s1_only", "switch", "blend"])
    ap.add_argument("--n-agents", type=int, default=500)
    ap.add_argument("--n-steps", type=int, default=72)
    ap.add_argument("--alpha", type=float, default=2.0)
    ap.add_argument("--beta", type=float, default=2.0)
    ap.add_argument("--kappa", type=float, default=5.0)
    ap.add_argument("--n-runs", type=int, default=10)
    ap.add_argument("--output-dir", type=Path, default=None,
                    help="Defaults to output/results/synthetic/<topology>/")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    args.output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_RESULTS_DIR / args.topology
    input_dir = args.output_dir / "input_csv"
    input_dir.mkdir(parents=True, exist_ok=True)

    # Build network (topology-specific kwargs)
    if args.topology == "linear":
        kwargs = {}  # use default n=7 (source + 5 towns + camp)
    elif args.topology in ("ring", "star"):
        kwargs = {"n": args.n_nodes} if args.topology == "ring" else {"n_spokes": args.n_nodes}
    else:
        kwargs = {"nodes": args.n_nodes}
    network_stats = build_network(args.topology, input_dir, **kwargs)
    with open(args.output_dir / "network_stats.json", "w") as f:
        json.dump(network_stats, f, indent=2)

    # Seed sequence for fair comparison
    rng = np.random.default_rng(args.seed)
    run_seeds = [int(rng.integers(0, 2**31)) for _ in range(args.n_runs)]

    all_results = {}
    for mode in args.modes:
        print(f"  Running {mode}...", end=" ", flush=True)
        mode_agents = []
        mode_summaries = []
        for run_id, run_seed in enumerate(run_seeds):
            agents_per_timestep, first_departure, lm = run_one(
                str(input_dir), mode, args.n_agents, args.n_steps,
                args.alpha, args.beta, args.kappa, run_seed,
                topology=args.topology,
            )
            mode_agents.append((run_id, agents_per_timestep, first_departure))
            # Summary per timestep
            for t, rows in agents_per_timestep:
                if not rows:
                    continue
                n_departed = sum(1 for r in rows if r["moved"])
                mean_s2 = np.mean([r["s2_weight"] for r in rows])
                mean_dist = np.mean([r["distance_from_source_km"] for r in rows])
                mode_summaries.append({
                    "run_id": run_id,
                    "decision_mode": mode,
                    "timestep": t,
                    "n_departed": n_departed,
                    "pct_departed": 100.0 * n_departed / len(rows),
                    "mean_s2_weight": mean_s2,
                    "mean_distance_km": mean_dist,
                })
        all_results[mode] = {"agents": mode_agents, "summaries": mode_summaries}
        print("OK")

    # Write agents CSV per mode (one file per mode, all runs)
    for mode in args.modes:
        rows = all_results[mode]["agents"]
        out_path = args.output_dir / f"agents_{mode}.csv"
        with open(out_path, "w") as f:
            f.write("run_id,agent_id,timestep,location,location_type,decision_mode,s2_weight,moved,distance_from_source_km\n")
            for run_id, agents_per_timestep, _ in rows:
                for t, agent_rows in agents_per_timestep:
                    for r in agent_rows:
                        f.write(f"{run_id},{r['agent_id']},{t},{r['location']},{r['location_type']},{mode},{r['s2_weight']:.6f},{r['moved']},{r['distance_from_source_km']:.4f}\n")
        print(f"Wrote {out_path}")

    # Summary CSV (all modes)
    out_path = args.output_dir / "summary_all_modes.csv"
    with open(out_path, "w") as f:
        f.write("run_id,decision_mode,timestep,n_departed,pct_departed,mean_s2_weight,mean_distance_km\n")
        for mode in args.modes:
            for row in all_results[mode]["summaries"]:
                f.write(f"{row['run_id']},{row['decision_mode']},{row['timestep']},{row['n_departed']},{row['pct_departed']:.4f},{row['mean_s2_weight']:.6f},{row['mean_distance_km']:.4f}\n")
    print(f"Wrote {out_path}")
    print(f"Done. Output in {args.output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
