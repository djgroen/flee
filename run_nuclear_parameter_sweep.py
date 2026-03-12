#!/usr/bin/env python3
"""
Run nuclear evacuation parameter sweep across topologies and (alpha, beta) ranges.
Generates results for paper figures, including standard FLEE output files.
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
import yaml
import shutil
from datetime import datetime

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

from flee import flee
from flee.SimulationSettings import SimulationSettings
from flee.moving import calculateMoveChance
from flee.flee import Person
from flee.Diagnostics import write_agents

class ParameterSweeper:
    def __init__(self, output_base_dir="data/results"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.summary_results = []

    def load_topology(self, input_dir):
        """Load locations and routes from CSV files."""
        input_dir = Path(input_dir) / "input_csv"
        locations = pd.read_csv(input_dir / "locations.csv")
        routes = pd.read_csv(input_dir / "routes.csv")
        return locations, routes

    def run_single_simulation(self, topology_name, config_file, alpha, beta, seed, output_dir):
        """Run single FLEE simulation with specified parameters."""
        # Load base config
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        # Override parameters
        config['move_rules']['s1s2_model']['alpha'] = alpha
        config['move_rules']['s1s2_model']['beta'] = beta
        
        # Update SimulationSettings
        temp_config_path = output_dir / f"temp_config_a{alpha}_b{beta}_s{seed}.yml"
        with open(temp_config_path, 'w') as f:
            yaml.dump(config, f)
        
        SimulationSettings.ReadFromYML(str(temp_config_path))
        
        # Initialize Ecosystem
        ecosystem = flee.Ecosystem()
        # Reset seed for repeatability
        import random
        random.seed(seed)
        np.random.seed(seed)

        # Load topology
        input_dir = config['network']['input_dir']
        input_dir_path = Path(input_dir) / "input_csv"
        locations_df, routes_df = self.load_topology(input_dir)
        
        location_map = {}
        for _, loc in locations_df.iterrows():
            location = ecosystem.addLocation(
                name=loc['name'],
                x=loc['gps_x'], y=loc['gps_y'],
                location_type=loc['location_type'],
                movechance=loc['movechance'],
                capacity=loc['capacity'],
                pop=0
            )
            location_map[loc['name']] = location

        # Set conflicts
        # Conflicts are now loaded from the topology's locations.csv
        for _, loc_row in locations_df.iterrows():
            if loc_row['name'] in location_map:
                location_map[loc_row['name']].conflict = loc_row.get('conflict', 0.0)
                # If locations.csv doesn't have conflict, we need a fallback.
                # But our hf generator includes it in the conflict field of locations if we are lucky
                # Actually, our generator doesn't put 'conflict' in locations.csv header, it puts it in conflicts.csv
                # Let's fix that in the generator or load it here from conflicts.csv
        
        # Correctly load conflicts from conflicts.csv
        conflicts_file = input_dir_path / "conflicts.csv"
        if conflicts_file.exists():
            # Use sep=None, engine='python' to auto-detect delimiter (usually comma)
            conf_df = pd.read_csv(conflicts_file, comment='#', header=None, names=['date', 'loc', 'val'], skipinitialspace=True)
            for _, row in conf_df.iterrows():
                if row['loc'] in location_map:
                    location_map[row['loc']].conflict = float(row['val'])

        # Add routes
        for _, route in routes_df.iterrows():
            ecosystem.linkUp(route['name1'], route['name2'], route['distance'])

        # Spawn agents
        spawn_location_name = config['agents']['spawn_location']
        spawn_location = location_map[spawn_location_name]
        n_agents = config['simulation']['n_agents']
        
        agents = []
        for i in range(n_agents):
            agent = Person(spawn_location, {})
            ecosystem.agents.append(agent)
            agents.append(agent)

        # Prepare out.csv header
        header = "Day,Date,"
        for loc in ecosystem.locations:
            header += f"{loc.name} sim,"
        header += "Total refugees\n"
        
        out_csv_path = output_dir / f"out_a{alpha}_b{beta}_s{seed}.csv"
        with open(out_csv_path, "w") as f:
            f.write(header)

        # Run simulation
        n_timesteps = config['simulation']['n_timesteps']
        history = []
        
        # Ensure agents.out.0 is unique for this run
        # FLEE writes to the current working directory by default.
        # We'll work in the output directory.
        old_cwd = os.getcwd()
        os.chdir(str(output_dir))
        
        try:
            for t in range(n_timesteps):
                # Record metrics BEFORE evolve for the initial state if needed
                # but standard FLEE does it after evolve.
                ecosystem.evolve()
                
                # Write out.csv line
                line = f"{t},{ecosystem.date_string},"
                total_pop = 0
                for loc in ecosystem.locations:
                    line += f"{loc.numAgents},"
                    total_pop += loc.numAgents
                line += f"{total_pop}\n"
                
                with open(out_csv_path.name, "a") as f:
                    f.write(line)
                
                # Record custom metrics for my aggregation (incl. omega for diagnostics)
                for agent in agents:
                    conflict = getattr(agent.location, 'conflict', 0.0) if agent.location and hasattr(agent.location, 'conflict') else 0.0
                    conflict = max(0.0, conflict)
                    z = beta * (1.0 - conflict)
                    omega = 1.0 / (1.0 + np.exp(-z)) if -20 <= z <= 20 else (1.0 if z > 20 else 0.0)
                    history.append({
                        'timestep': t,
                        'agent_id': id(agent),
                        'location': agent.location.name if agent.location else "None",
                        'p_s2': getattr(agent, 's2_activation_prob', 0.0),
                        'omega': omega,
                        'experience': agent.experience_index,
                        'conflict': conflict
                    })

            # After loop, rename agents.out.0 to a unique name
            if os.path.exists("agents.out.0"):
                shutil.move("agents.out.0", f"agents_a{alpha}_b{beta}_s{seed}.out")
        finally:
            os.chdir(old_cwd)

        # Save detailed results
        results_df = pd.DataFrame(history)
        results_path = output_dir / f"results_a{alpha}_b{beta}_s{seed}.csv"
        results_df.to_csv(results_path, index=False)
        
        # Cleanup temp config
        if temp_config_path.exists():
            temp_config_path.unlink()
        
        return results_path

    def extract_metrics(self, result_file, topology_name, alpha, beta, seed):
        """Extract key metrics from simulation results."""
        df = pd.read_csv(result_file)
        last_t = df['timestep'].max()
        last_df = df[df['timestep'] == last_t]
        n_agents = len(last_df)
        # Safe zones: SafeZone, SafeZone_0, SafeZone_1, etc., or camp locations
        loc_str = last_df['location'].astype(str)
        evacuated = loc_str.str.contains('SafeZone', na=False).sum()
        avg_p_s2 = df['p_s2'].mean()
        peak_p_s2 = df['p_s2'].max()
        first_safe = df[df['location'].astype(str).str.contains('SafeZone', na=False)].groupby('agent_id')['timestep'].min()
        avg_evac_time = first_safe.mean() if not first_safe.empty else last_t
        
        metrics = {
            'topology': topology_name,
            'alpha': alpha,
            'beta': beta,
            'seed': seed,
            'avg_p_s2': avg_p_s2,
            'peak_p_s2': peak_p_s2,
            'final_evacuation_rate': evacuated / n_agents,
            'avg_evacuation_time': avg_evac_time
        }
        for loc in df['location'].unique():
            if loc != "None":
                metrics[f'p_s2_{loc}'] = df[df['location'] == loc]['p_s2'].mean()
        return metrics

    def sweep(self, limited=False):
        """Main parameter sweep."""
        if limited:
            alpha_range = [2.0]
            beta_range = [2.0]
            n_replicates = 1
        else:
            alpha_range = [0.5, 2.0, 3.0]
            beta_range = [0.5, 2.0, 3.0]
            n_replicates = 1

        topologies = ['ring', 'star', 'linear']

        for topology in topologies:
            print(f"\n=== Sweeping {topology} topology ===")
            config_file = Path(f"configs/{topology}_topology.yml")
            output_dir = self.output_base_dir / topology
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for alpha in alpha_range:
                for beta in beta_range:
                    print(f"  α={alpha}, β={beta}")
                    for seed in range(n_replicates):
                        res_file = self.run_single_simulation(topology, config_file, alpha, beta, seed, output_dir)
                        metrics = self.extract_metrics(res_file, topology, alpha, beta, seed)
                        self.summary_results.append(metrics)
                        
        # Save summary
        summary_df = pd.DataFrame(self.summary_results)
        summary_df.to_csv(self.output_base_dir / 'parameter_sweep_summary.csv', index=False)
        print(f"\n✅ Sweep complete. Summary saved to {self.output_base_dir / 'parameter_sweep_summary.csv'}")

if __name__ == "__main__":
    sweeper = ParameterSweeper()
    # Run a full sweep now that it produces standard FLEE outputs
    sweeper.sweep()
