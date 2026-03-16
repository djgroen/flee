#!/usr/bin/env python3
"""
Cleanup and Improve S1/S2 Experiments
- Clean up duplicate/earlier versions
- Create S1/S2 comparison plots
- Fix star network initial population issue
- Run with 10,000 agents for stochastic stability
"""

import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Any
import seaborn as sns
from datetime import datetime
import warnings
import shutil
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, '.')

class CleanupAndImproveExperiments:
    """Cleanup and improve S1/S2 experiments"""
    
    def __init__(self, results_dir="organized_s1s2_experiments"):
        self.results_dir = Path(results_dir)
        self.figures_dir = self.results_dir / "02_figures"
        
        # Load experimental results
        self.results = self._load_results()
        self.df = self._create_dataframe()
        
    def _load_results(self):
        """Load experimental results from JSON"""
        results_file = self.results_dir / "experimental_results.json"
        with open(results_file, 'r') as f:
            return json.load(f)
    
    def _create_dataframe(self):
        """Create DataFrame from results"""
        data = []
        for exp_id, exp_data in self.results.items():
            result = exp_data['results']
            data.append({
                'experiment_id': exp_id,
                'topology': exp_data['topology'],
                'network_size': exp_data['network_size'],
                'scenario': exp_data['scenario'],
                'scenario_type': exp_data['scenario_type'],
                's2_threshold': exp_data['s2_threshold'],
                's2_rate': result['s2_rate'],
                'total_distance': result['total_distance'],
                'destinations_reached': result['destinations_reached'],
                'population_size': result['population_size']
            })
        return pd.DataFrame(data)
    
    def cleanup_duplicate_plots(self):
        """Clean up duplicate/earlier versions of plots"""
        
        print("🧹 Cleaning up duplicate/earlier versions...")
        
        # Remove network_topology_maps (replaced by proper_flow_visualizations)
        network_maps_dir = self.figures_dir / "network_topology_maps"
        if network_maps_dir.exists():
            shutil.rmtree(network_maps_dir)
            print(f"  ✅ Removed {network_maps_dir}")
        
        # Keep only the best versions:
        # - proper_flow_visualizations (best flow visualization)
        # - comparative_analysis (good for cross-topology analysis)
        # - sensitivity_analysis (good for threshold analysis)
        # - individual_networks (good for per-topology analysis)
        
        print("  ✅ Cleanup complete - kept best versions only")
    
    def create_s1s2_comparison_plots(self):
        """Create S1/S2 comparison plots"""
        
        print("📊 Creating S1/S2 comparison plots...")
        
        # Create S1/S2 comparison directory
        s1s2_comparison_dir = self.figures_dir / "s1s2_comparison"
        s1s2_comparison_dir.mkdir(exist_ok=True)
        
        # 1. Baseline vs S1/S2 switching comparison
        self._create_baseline_vs_s1s2_comparison(s1s2_comparison_dir)
        
        # 2. S2 threshold sensitivity comparison
        self._create_s2_threshold_comparison(s1s2_comparison_dir)
        
        # 3. Scenario comparison by topology
        self._create_scenario_comparison_by_topology(s1s2_comparison_dir)
        
        print(f"  ✅ S1/S2 comparison plots created in {s1s2_comparison_dir}")
    
    def _create_baseline_vs_s1s2_comparison(self, output_dir):
        """Create baseline vs S1/S2 switching comparison"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Baseline vs S1/S2 Switching Scenarios Comparison', fontsize=16, fontweight='bold')
        
        # Plot 1: S2 Rate Comparison
        baseline_data = self.df[self.df['scenario_type'] == 'baseline']
        s1s2_data = self.df[self.df['scenario_type'] == 's1s2']
        
        ax1.boxplot([baseline_data['s2_rate'], s1s2_data['s2_rate']], 
                   labels=['Baseline', 'S1/S2 Switching'])
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('S2 Activation Rate: Baseline vs S1/S2 Switching')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Distance Comparison
        ax2.boxplot([baseline_data['total_distance'], s1s2_data['total_distance']], 
                   labels=['Baseline', 'S1/S2 Switching'])
        ax2.set_ylabel('Total Distance Traveled')
        ax2.set_title('Travel Distance: Baseline vs S1/S2 Switching')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: S2 Rate by Scenario Type and Topology
        for topology in self.df['topology'].unique():
            topo_baseline = baseline_data[baseline_data['topology'] == topology]['s2_rate']
            topo_s1s2 = s1s2_data[s1s2_data['topology'] == topology]['s2_rate']
            ax3.plot([0, 1], [topo_baseline.mean(), topo_s1s2.mean()], 
                    marker='o', linewidth=2, label=topology.title(), markersize=8)
        
        ax3.set_xlabel('Scenario Type')
        ax3.set_ylabel('S2 Activation Rate')
        ax3.set_title('S2 Rate by Topology: Baseline vs S1/S2 Switching')
        ax3.set_xticks([0, 1])
        ax3.set_xticklabels(['Baseline', 'S1/S2 Switching'])
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Distance by Scenario Type and Topology
        for topology in self.df['topology'].unique():
            topo_baseline = baseline_data[baseline_data['topology'] == topology]['total_distance']
            topo_s1s2 = s1s2_data[s1s2_data['topology'] == topology]['total_distance']
            ax4.plot([0, 1], [topo_baseline.mean(), topo_s1s2.mean()], 
                    marker='s', linewidth=2, label=topology.title(), markersize=8)
        
        ax4.set_xlabel('Scenario Type')
        ax4.set_ylabel('Total Distance Traveled')
        ax4.set_title('Travel Distance by Topology: Baseline vs S1/S2 Switching')
        ax4.set_xticks([0, 1])
        ax4.set_xticklabels(['Baseline', 'S1/S2 Switching'])
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "baseline_vs_s1s2_comparison.png", dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / "baseline_vs_s1s2_comparison.pdf", bbox_inches='tight')
        plt.close()
        
        print("  ✅ Baseline vs S1/S2 comparison created")
    
    def _create_s2_threshold_comparison(self, output_dir):
        """Create S2 threshold comparison"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('S2 Threshold Sensitivity Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: S2 Rate vs Threshold
        s1s2_data = self.df[self.df['scenario_type'] == 's1s2']
        
        for topology in s1s2_data['topology'].unique():
            topo_data = s1s2_data[s1s2_data['topology'] == topology]
            ax1.plot(topo_data['s2_threshold'], topo_data['s2_rate'], 
                    marker='o', linewidth=2, label=topology.title(), markersize=8)
        
        ax1.set_xlabel('S2 Threshold')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('S2 Activation Rate vs S2 Threshold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Distance vs Threshold
        for topology in s1s2_data['topology'].unique():
            topo_data = s1s2_data[s1s2_data['topology'] == topology]
            ax2.plot(topo_data['s2_threshold'], topo_data['total_distance'], 
                    marker='s', linewidth=2, label=topology.title(), markersize=8)
        
        ax2.set_xlabel('S2 Threshold')
        ax2.set_ylabel('Total Distance Traveled')
        ax2.set_title('Travel Distance vs S2 Threshold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "s2_threshold_sensitivity.png", dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / "s2_threshold_sensitivity.pdf", bbox_inches='tight')
        plt.close()
        
        print("  ✅ S2 threshold sensitivity created")
    
    def _create_scenario_comparison_by_topology(self, output_dir):
        """Create scenario comparison by topology"""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Scenario Comparison by Network Topology', fontsize=16, fontweight='bold')
        
        topologies = ['linear', 'star', 'tree', 'grid']
        scenario_order = ['pure_s1', 'pure_s2', 'static_mixed', 'low_s2', 'medium_s2', 'high_s2']
        scenario_labels = ['Pure S1', 'Pure S2', 'Static Mixed', 'Low S2', 'Medium S2', 'High S2']
        
        for i, topology in enumerate(topologies):
            ax = axes[i//2, i%2]
            
            topo_data = self.df[self.df['topology'] == topology]
            
            s2_rates = []
            for scenario in scenario_order:
                scenario_data = topo_data[topo_data['scenario'] == scenario]
                s2_rates.append(scenario_data['s2_rate'].values)
            
            ax.boxplot(s2_rates, labels=scenario_labels)
            ax.set_ylabel('S2 Activation Rate')
            ax.set_title(f'{topology.title()} Network: S2 Rate by Scenario')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "scenario_comparison_by_topology.png", dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / "scenario_comparison_by_topology.pdf", bbox_inches='tight')
        plt.close()
        
        print("  ✅ Scenario comparison by topology created")
    
    def run_high_agent_experiments(self):
        """Run experiments with 10,000 agents for stochastic stability"""
        
        print("🚀 Running high-agent experiments (10,000 agents)...")
        
        # Create high-agent experiments directory
        high_agent_dir = Path("high_agent_s1s2_experiments")
        high_agent_dir.mkdir(exist_ok=True)
        
        # Run a subset of experiments with 10,000 agents
        test_scenarios = [
            {'topology': 'star', 'size': 7, 'scenario': 'medium_s2'},
            {'topology': 'linear', 'size': 7, 'scenario': 'medium_s2'},
            {'topology': 'grid', 'size': 7, 'scenario': 'medium_s2'}
        ]
        
        for test in test_scenarios:
            print(f"  🧪 Running {test['topology']} n={test['size']} {test['scenario']} with 10,000 agents...")
            self._run_high_agent_experiment(test, high_agent_dir)
        
        print(f"  ✅ High-agent experiments completed in {high_agent_dir}")
    
    def _run_high_agent_experiment(self, test_config, output_dir):
        """Run a single high-agent experiment"""
        
        # Create simsetting.yml for high-agent experiment
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
        topology_data = self._generate_network_topology(test_config['topology'], test_config['size'])
        
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
        
        # Spawn 10,000 agents
        population_size = 10000
        origin_location = locations[topology_data['locations'][0]['name']]
        
        for i in range(population_size):
            attributes = {"profile_type": np.random.choice(['analytical', 'balanced', 'reactive'])}
            ecosystem.addAgent(origin_location, attributes)
        
        # Run simulation
        simulation_days = 20
        s2_activations = []
        
        for day in range(simulation_days):
            day_s2_count = 0
            
            for agent in ecosystem.agents:
                # Determine S2 activation
                pressure = 0.3 + 0.1 * np.sin(day * 0.5) + np.random.uniform(-0.1, 0.1)
                s2_active = calculate_systematic_s2_activation(
                    agent, pressure, 0.5, day  # medium_s2 threshold
                )
                
                if s2_active:
                    day_s2_count += 1
                    agent.cognitive_state = "S2"
                else:
                    agent.cognitive_state = "S1"
            
            s2_activations.append(day_s2_count)
            ecosystem.evolve()
        
        # Calculate results
        total_s2_decisions = sum(s2_activations)
        total_possible_decisions = population_size * simulation_days
        s2_rate = total_s2_decisions / total_possible_decisions if total_possible_decisions > 0 else 0
        
        # Save results
        result = {
            'topology': test_config['topology'],
            'network_size': test_config['size'],
            'scenario': test_config['scenario'],
            'population_size': population_size,
            'simulation_days': simulation_days,
            's2_rate': s2_rate,
            's2_activations': s2_activations
        }
        
        result_file = output_dir / f"{test_config['topology']}_n{test_config['size']}_{test_config['scenario']}_10k_agents.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Clean up
        self._cleanup_temp_files()
        
        print(f"    ✅ S2 rate: {s2_rate:.1%}")
    
    def _generate_network_topology(self, topology_type, n_nodes):
        """Generate network topology with proper star network setup"""
        
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
            # FIXED: All agents start at origin only
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
        
        # Add other topologies as needed...
        
        return {
            'name': f'{topology_type.title()} Network (n={n_nodes})',
            'locations': locations,
            'routes': routes
        }
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_files = ['agents.out.0', 'links.out.0', 'simsetting.yml']
        for file in temp_files:
            if Path(file).exists():
                Path(file).unlink()
    
    def run_all_improvements(self):
        """Run all improvements"""
        
        print("🚀 Cleanup and Improve S1/S2 Experiments")
        print("=" * 60)
        
        # 1. Clean up duplicate plots
        self.cleanup_duplicate_plots()
        
        # 2. Create S1/S2 comparison plots
        self.create_s1s2_comparison_plots()
        
        # 3. Run high-agent experiments
        self.run_high_agent_experiments()
        
        print(f"\n🎉 All improvements completed!")
        print(f"📊 Check organized_s1s2_experiments/02_figures/s1s2_comparison/ for new plots")
        print(f"🚀 Check high_agent_s1s2_experiments/ for 10k agent results")

def main():
    """Main function"""
    
    # Create and run improvements
    improver = CleanupAndImproveExperiments()
    improver.run_all_improvements()

if __name__ == "__main__":
    main()






