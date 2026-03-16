#!/usr/bin/env python3
"""
S1/S2 Dual-Process Experiments
- Demonstrates value and sensitivity of S1/S2 switching
- Baseline vs S1/S2 scenarios with consistent population
- Systematic experimental matrix
"""

import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, '.')

class S1S2Experiments:
    """S1/S2 dual-process experimental framework"""
    
    def __init__(self, output_dir="s1s2_experiments"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Experimental parameters
        self.topology_types = ['linear', 'star', 'tree', 'grid']
        self.network_sizes = [5, 7, 11]
        
        # Population consistency: constant density per node (5 agents/node)
        # This maintains constant decision-making complexity across network sizes
        self.population_map = {5: 25, 7: 35, 11: 55}
        
        # Baseline scenarios (no S1/S2 switching)
        self.baseline_scenarios = {
            'pure_s1': {'s2_threshold': 1.0, 'description': 'Pure System 1 (reactive)'},
            'pure_s2': {'s2_threshold': 0.0, 'description': 'Pure System 2 (deliberative)'},
            'static_mixed': {'s2_threshold': 0.5, 'description': 'Static mixed (50/50)'}
        }
        
        # S1/S2 switching scenarios
        self.s1s2_scenarios = {
            'low_s2': {'s2_threshold': 0.3, 'description': 'Low S2 activation'},
            'medium_s2': {'s2_threshold': 0.5, 'description': 'Medium S2 activation'},
            'high_s2': {'s2_threshold': 0.7, 'description': 'High S2 activation'}
        }
        
        # Results storage
        self.results = {}
        
    def run_experiment(self, topology, n_nodes, scenario_name, scenario_config):
        """Run a single experiment"""
        
        print(f"🧪 {scenario_name} | {topology} | n={n_nodes}")
        
        # Create simsetting.yml
        simsetting_content = f"""log_levels:
  agent: 1
  link: 1
  camp: 0
  conflict: 0
  init: 0
  granularity: location
spawn_rules:
  take_from_population: False
  insert_day0: True
move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 1.0
  camp_movechance: 0.001
  default_movechance: 0.3
  awareness_level: 1
  capacity_scaling: 1.0
  avoid_short_stints: False
  start_on_foot: False
  weight_power: 1.0
optimisations:
  hasten: 1
"""
        
        with open("simsetting.yml", "w") as f:
            f.write(simsetting_content)
        
        # Import Flee components
        from flee.flee import Ecosystem, Person
        from flee.SimulationSettings import SimulationSettings
        from flee.moving import calculate_systematic_s2_activation
        
        # Setup simulation
        SimulationSettings.ReadFromYML("simsetting.yml")
        ecosystem = Ecosystem()
        
        # Generate network topology
        topology_data = self._generate_network_topology(topology, n_nodes)
        
        # Add locations
        locations = {}
        for loc in topology_data['locations']:
            location = ecosystem.addLocation(
                name=loc['name'],
                x=loc['x'], y=loc['y'],
                movechance=0.3 if loc['type'] == 'town' else (0.001 if loc['type'] == 'camp' else 1.0),
                capacity=loc['pop'] if loc['type'] == 'camp' else -1,
                pop=0
            )
            locations[loc['name']] = location
        
        # Add routes
        for route in topology_data['routes']:
            ecosystem.linkUp(route['from'], route['to'], route['distance'])
        
        # Spawn agents with consistent population
        population_size = self.population_map[n_nodes]
        origin_location = locations[topology_data['locations'][0]['name']]
        
        for i in range(population_size):
            attributes = {"profile_type": np.random.choice(['analytical', 'balanced', 'reactive'])}
            ecosystem.addAgent(origin_location, attributes)
        
        # Run simulation
        simulation_days = 20
        s2_activations = []
        total_distance = 0
        destinations_reached = set()
        
        for day in range(simulation_days):
            day_s2_count = 0
            for agent in ecosystem.agents:
                # Determine S2 activation based on scenario
                if scenario_name in self.baseline_scenarios:
                    # Baseline scenarios: fixed behavior
                    if scenario_name == 'pure_s1':
                        s2_active = False
                    elif scenario_name == 'pure_s2':
                        s2_active = True
                    else:  # static_mixed
                        s2_active = np.random.random() < 0.5
                else:
                    # S1/S2 switching scenarios: dynamic behavior
                    pressure = 0.3 + 0.1 * np.sin(day * 0.5) + np.random.uniform(-0.1, 0.1)
                    s2_active = calculate_systematic_s2_activation(
                        agent, pressure, scenario_config['s2_threshold'], day
                    )
                
                if s2_active:
                    day_s2_count += 1
                    agent.cognitive_state = "S2"
                else:
                    agent.cognitive_state = "S1"
                
                # Track metrics
                if hasattr(agent, 'distance_travelled'):
                    total_distance += agent.distance_travelled
                if hasattr(agent, 'current_location'):
                    destinations_reached.add(agent.current_location.name)
            
            s2_activations.append(day_s2_count)
            ecosystem.evolve()
        
        # Calculate metrics
        total_s2_decisions = sum(s2_activations)
        total_possible_decisions = population_size * simulation_days
        s2_rate = total_s2_decisions / total_possible_decisions if total_possible_decisions > 0 else 0
        
        # Preserve agent tracking data
        self._preserve_data(topology, n_nodes, scenario_name)
        
        # Clean up temporary files
        self._cleanup_temp_files()
        
        return {
            's2_rate': s2_rate,
            'total_distance': total_distance,
            'destinations_reached': len(destinations_reached),
            's2_activations': s2_activations,
            'population_size': population_size,
            'simulation_days': simulation_days,
            'scenario_type': 'baseline' if scenario_name in self.baseline_scenarios else 's1s2'
        }
    
    def _generate_network_topology(self, topology_type, n_nodes):
        """Generate network topology"""
        
        locations = []
        routes = []
        
        if topology_type == 'linear':
            for i in range(n_nodes):
                if i == 0:
                    locations.append({
                        'name': f'Origin_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,
                        'type': 'conflict', 'pop': 5000
                    })
                elif i < n_nodes // 2:
                    locations.append({
                        'name': f'Town_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,
                        'type': 'town', 'pop': 1000
                    })
                else:
                    locations.append({
                        'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,
                        'type': 'camp', 'pop': 2000
                    })
            
            for i in range(n_nodes - 1):
                routes.append({
                    'from': locations[i]['name'],
                    'to': locations[i + 1]['name'],
                    'distance': 100.0
                })
        
        elif topology_type == 'star':
            # Origin at center
            locations.append({
                'name': f'Origin_{topology_type}_{n_nodes}',
                'x': 0.0, 'y': 0.0,
                'type': 'conflict', 'pop': 5000
            })
            
            # Hub
            locations.append({
                'name': f'Hub_{topology_type}_{n_nodes}',
                'x': 3.0, 'y': 0.0,
                'type': 'town', 'pop': 1000
            })
            
            # Camps in star pattern
            for i in range(2, n_nodes):
                angle = 2 * np.pi * (i - 2) / (n_nodes - 2)
                x = 6.0 * np.cos(angle)
                y = 6.0 * np.sin(angle)
                locations.append({
                    'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                    'x': x, 'y': y,
                    'type': 'camp', 'pop': 2000
                })
            
            # Create star connections
            routes.append({
                'from': locations[0]['name'],
                'to': locations[1]['name'],
                'distance': 100.0
            })
            
            for i in range(2, n_nodes):
                routes.append({
                    'from': locations[1]['name'],
                    'to': locations[i]['name'],
                    'distance': 100.0
                })
        
        # Add tree and grid topologies as needed
        
        return {
            'name': f'{topology_type.title()} Network (n={n_nodes})',
            'locations': locations,
            'routes': routes
        }
    
    def _preserve_data(self, topology, n_nodes, scenario_name):
        """Preserve agent tracking data"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = self.output_dir / "agent_tracking_data"
        data_dir.mkdir(exist_ok=True)
        
        topology_dir = data_dir / f"{topology}_{n_nodes}nodes_{scenario_name}"
        topology_dir.mkdir(exist_ok=True)
        
        # Copy agent tracking files
        agent_files = ['agents.out.0', 'links.out.0', 'simsetting.yml']
        
        for file in agent_files:
            if Path(file).exists():
                timestamped_name = f"{file}_{timestamp}"
                import shutil
                shutil.copy2(file, topology_dir / timestamped_name)
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_files = ['agents.out.0', 'links.out.0', 'simsetting.yml']
        for file in temp_files:
            if Path(file).exists():
                Path(file).unlink()
    
    def run_experimental_suite(self):
        """Run the complete experimental suite"""
        
        print("🚀 S1/S2 Dual-Process Experimental Suite")
        print("=" * 60)
        
        # Calculate total experiments
        total_experiments = (
            len(self.topology_types) * 
            len(self.network_sizes) * 
            (len(self.baseline_scenarios) + len(self.s1s2_scenarios))
        )
        
        print(f"📊 Running {total_experiments} experiments:")
        print(f"   - Topologies: {len(self.topology_types)}")
        print(f"   - Network sizes: {len(self.network_sizes)}")
        print(f"   - Baseline scenarios: {len(self.baseline_scenarios)}")
        print(f"   - S1/S2 scenarios: {len(self.s1s2_scenarios)}")
        print()
        
        experiment_count = 0
        
        # Run baseline experiments
        print("🔬 Running Baseline Experiments...")
        for topology in self.topology_types:
            for n_nodes in self.network_sizes:
                for scenario_name, scenario_config in self.baseline_scenarios.items():
                    experiment_count += 1
                    print(f"[{experiment_count}/{total_experiments}] ", end="")
                    
                    result = self.run_experiment(topology, n_nodes, scenario_name, scenario_config)
                    
                    exp_id = f"{topology}_{n_nodes}_{scenario_name}"
                    self.results[exp_id] = {
                        'topology': topology,
                        'network_size': n_nodes,
                        'scenario': scenario_name,
                        'scenario_type': 'baseline',
                        's2_threshold': scenario_config['s2_threshold'],
                        'description': scenario_config['description'],
                        'results': result
                    }
        
        # Run S1/S2 experiments
        print("\n🧠 Running S1/S2 Switching Experiments...")
        for topology in self.topology_types:
            for n_nodes in self.network_sizes:
                for scenario_name, scenario_config in self.s1s2_scenarios.items():
                    experiment_count += 1
                    print(f"[{experiment_count}/{total_experiments}] ", end="")
                    
                    result = self.run_experiment(topology, n_nodes, scenario_name, scenario_config)
                    
                    exp_id = f"{topology}_{n_nodes}_{scenario_name}"
                    self.results[exp_id] = {
                        'topology': topology,
                        'network_size': n_nodes,
                        'scenario': scenario_name,
                        'scenario_type': 's1s2',
                        's2_threshold': scenario_config['s2_threshold'],
                        'description': scenario_config['description'],
                        'results': result
                    }
        
        # Save results and create analysis
        self._save_results()
        self._create_analysis()
        
        print(f"\n🎯 Experimental Suite Complete!")
        print(f"📊 Results saved to: {self.output_dir}")
    
    def _save_results(self):
        """Save experimental results"""
        
        results_file = self.output_dir / "experimental_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"💾 Results saved: {results_file}")
    
    def _create_analysis(self):
        """Create analysis and visualizations"""
        
        # Create summary DataFrame
        summary_data = []
        
        for exp_id, exp_data in self.results.items():
            summary_data.append({
                'experiment_id': exp_id,
                'topology': exp_data['topology'],
                'network_size': exp_data['network_size'],
                'scenario': exp_data['scenario'],
                'scenario_type': exp_data['scenario_type'],
                's2_threshold': exp_data['s2_threshold'],
                's2_rate': exp_data['results']['s2_rate'],
                'total_distance': exp_data['results']['total_distance'],
                'destinations_reached': exp_data['results']['destinations_reached'],
                'population_size': exp_data['results']['population_size']
            })
        
        df = pd.DataFrame(summary_data)
        
        # Save summary
        summary_file = self.output_dir / "experimental_summary.csv"
        df.to_csv(summary_file, index=False)
        
        # Create visualizations
        self._create_visualizations(df)
        
        print(f"📊 Analysis saved: {summary_file}")
    
    def _create_visualizations(self, df):
        """Create analysis visualizations"""
        
        figures_dir = self.output_dir / "figures"
        figures_dir.mkdir(exist_ok=True)
        
        # S2 Rate Comparison
        plt.figure(figsize=(12, 8))
        
        # Group by scenario type and topology
        for scenario_type in ['baseline', 's1s2']:
            subset = df[df['scenario_type'] == scenario_type]
            
            for topology in self.topology_types:
                topo_subset = subset[subset['topology'] == topology]
                
                plt.scatter(topo_subset['s2_threshold'], topo_subset['s2_rate'], 
                           label=f'{topology} ({scenario_type})', alpha=0.7, s=100)
        
        plt.xlabel('S2 Threshold')
        plt.ylabel('S2 Activation Rate')
        plt.title('S2 Activation Rate vs S2 Threshold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(figures_dir / "s2_rate_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Distance vs S2 Rate
        plt.figure(figsize=(12, 8))
        
        for scenario_type in ['baseline', 's1s2']:
            subset = df[df['scenario_type'] == scenario_type]
            plt.scatter(subset['s2_rate'], subset['total_distance'], 
                       label=scenario_type, alpha=0.7, s=100)
        
        plt.xlabel('S2 Activation Rate')
        plt.ylabel('Total Distance Traveled')
        plt.title('Travel Distance vs S2 Activation Rate')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(figures_dir / "distance_vs_s2_rate.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Visualizations saved to: {figures_dir}")

def main():
    """Main function to run S1/S2 experiments"""
    
    print("🧪 S1/S2 Dual-Process Experiments")
    print("=" * 60)
    
    # Create and run experiments
    experiments = S1S2Experiments()
    experiments.run_experimental_suite()
    
    print("\n🎉 S1/S2 Experiments Complete!")

if __name__ == "__main__":
    main()
