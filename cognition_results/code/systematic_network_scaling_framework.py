#!/usr/bin/env python3
"""
Systematic Network Scaling Framework

Creates scientifically defensible network topologies using core network metrics
and organized results management for dual-process S2 testing.
"""

import sys
import os
import json
import random
import math
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# Add current directory to path
sys.path.insert(0, '.')

# Import Flee components
from flee.flee import Ecosystem, Person
from flee.SimulationSettings import SimulationSettings
from flee import moving, spawning

# Import our optimized S2 functions
from real_flee_with_figures import calculate_systematic_s2_activation

@dataclass
class NetworkMetrics:
    """Core network metrics for scientific analysis"""
    n_nodes: int
    n_edges: int
    avg_degree: float
    clustering_coefficient: float
    avg_path_length: float
    diameter: int
    density: float
    assortativity: float
    modularity: float
    betweenness_centrality: float

@dataclass
class ExperimentConfig:
    """Configuration for systematic experiments"""
    base_nodes: int = 5
    scaling_factor: float = 1.5
    max_nodes: int = 50
    topology_types: List[str] = None
    s2_target_range: Tuple[float, float] = (0.20, 0.30)
    
    def __post_init__(self):
        if self.topology_types is None:
            self.topology_types = ['linear', 'star', 'tree', 'grid', 'random', 'scale_free']

class SystematicNetworkScaler:
    """Systematic network scaling using core network metrics"""
    
    def __init__(self, config: ExperimentConfig, results_dir="systematic_network_results"):
        self.config = config
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Create organized subdirectories
        self.create_results_structure()
        
        # Load optimized S2 parameters
        self.optimal_params = self._load_optimal_s2_parameters()
        
        # Network scaling sequence
        self.network_sizes = self._generate_network_sizes()
        
    def create_results_structure(self):
        """Create organized results directory structure"""
        subdirs = [
            'raw_data',
            'figures', 
            'analysis',
            'reports',
            'network_metrics',
            's2_analysis'
        ]
        
        for subdir in subdirs:
            (self.results_dir / subdir).mkdir(exist_ok=True)
            
        print(f"📁 Created organized results structure: {self.results_dir}")
    
    def _generate_network_sizes(self) -> List[int]:
        """Generate network sizes using geometric progression"""
        sizes = []
        current_size = self.config.base_nodes
        
        while current_size <= self.config.max_nodes:
            sizes.append(int(current_size))
            current_size *= self.config.scaling_factor
            
        return sizes
    
    def _load_optimal_s2_parameters(self):
        """Load optimized S2 parameters"""
        try:
            with open('s2_optimization_results.json', 'r') as f:
                results = json.load(f)
                if isinstance(results, list):
                    best_result = max(results, key=lambda x: x.get('s2_rate', 0))
                    return {
                        'base_threshold': best_result.get('base_threshold', 0.45),
                        'profile_adjustments': {
                            'analytical': -0.15,
                            'balanced': 0.0,
                            'reactive': 0.15
                        }
                    }
                else:
                    return results.get('best_parameters', {
                        'base_threshold': 0.45,
                        'profile_adjustments': {
                            'analytical': -0.15,
                            'balanced': 0.0,
                            'reactive': 0.15
                        }
                    })
        except (FileNotFoundError, KeyError, ValueError):
            return {
                'base_threshold': 0.45,
                'profile_adjustments': {
                    'analytical': -0.15,
                    'balanced': 0.0,
                    'reactive': 0.15
                }
            }
    
    def generate_network_topology(self, topology_type: str, n_nodes: int) -> Dict[str, Any]:
        """Generate network topology using NetworkX"""
        
        if topology_type == 'linear':
            G = nx.path_graph(n_nodes)
        elif topology_type == 'star':
            G = nx.star_graph(n_nodes - 1)
        elif topology_type == 'tree':
            G = nx.balanced_tree(2, int(math.log2(n_nodes)))
            # Trim to exact node count
            if G.number_of_nodes() > n_nodes:
                nodes_to_remove = list(G.nodes())[n_nodes:]
                G.remove_nodes_from(nodes_to_remove)
        elif topology_type == 'grid':
            # Create square grid, pad if needed
            grid_size = int(math.ceil(math.sqrt(n_nodes)))
            G = nx.grid_2d_graph(grid_size, grid_size)
            # Trim to exact node count
            if G.number_of_nodes() > n_nodes:
                nodes_to_remove = list(G.nodes())[n_nodes:]
                G.remove_nodes_from(nodes_to_remove)
        elif topology_type == 'random':
            G = nx.erdos_renyi_graph(n_nodes, 0.3)
        elif topology_type == 'scale_free':
            G = nx.barabasi_albert_graph(n_nodes, 2)
        else:
            raise ValueError(f"Unknown topology type: {topology_type}")
        
        # Ensure connectivity
        if not nx.is_connected(G):
            G = nx.connected_component_subgraphs(G)[0]
        
        # Convert to our format
        return self._networkx_to_flee_format(G, topology_type, n_nodes)
    
    def _networkx_to_flee_format(self, G: nx.Graph, topology_type: str, n_nodes: int) -> Dict[str, Any]:
        """Convert NetworkX graph to Flee format"""
        
        # Create locations
        locations = []
        for i, node in enumerate(G.nodes()):
            if i == 0:
                # First node is origin (conflict zone)
                locations.append({
                    'name': f'Origin_{topology_type}_{n_nodes}',
                    'x': float(i), 'y': 0.0,
                    'type': 'conflict', 'pop': 5000
                })
            elif i < n_nodes // 2:
                # Middle nodes are towns
                locations.append({
                    'name': f'Town_{i}_{topology_type}_{n_nodes}',
                    'x': float(i), 'y': 0.0,
                    'type': 'town', 'pop': 1000
                })
            else:
                # Later nodes are camps
                locations.append({
                    'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                    'x': float(i), 'y': 0.0,
                    'type': 'camp', 'pop': 2000
                })
        
        # Create routes
        routes = []
        for edge in G.edges():
            routes.append({
                'from': locations[list(G.nodes()).index(edge[0])]['name'],
                'to': locations[list(G.nodes()).index(edge[1])]['name'],
                'distance': 100.0
            })
        
        return {
            'name': f'{topology_type.title()} Network (n={n_nodes})',
            'hypothesis': f'H: {topology_type} topology with {n_nodes} nodes',
            'locations': locations,
            'routes': routes,
            'graph': G
        }
    
    def calculate_network_metrics(self, topology: Dict[str, Any]) -> NetworkMetrics:
        """Calculate core network metrics"""
        
        G = topology['graph']
        
        return NetworkMetrics(
            n_nodes=G.number_of_nodes(),
            n_edges=G.number_of_edges(),
            avg_degree=2 * G.number_of_edges() / G.number_of_nodes(),
            clustering_coefficient=nx.average_clustering(G),
            avg_path_length=nx.average_shortest_path_length(G),
            diameter=nx.diameter(G),
            density=nx.density(G),
            assortativity=nx.degree_assortativity_coefficient(G),
            modularity=self._calculate_modularity(G),
            betweenness_centrality=np.mean(list(nx.betweenness_centrality(G).values()))
        )
    
    def _calculate_modularity(self, G: nx.Graph) -> float:
        """Calculate modularity using community detection"""
        try:
            communities = nx.community.greedy_modularity_communities(G)
            return nx.community.modularity(G, communities)
        except:
            return 0.0
    
    def run_systematic_scaling_experiment(self):
        """Run systematic network scaling experiment"""
        
        print("🚀 Running Systematic Network Scaling Experiment")
        print(f"   Network sizes: {self.network_sizes}")
        print(f"   Topology types: {self.config.topology_types}")
        print(f"   Results directory: {self.results_dir}")
        
        all_results = {}
        
        for topology_type in self.config.topology_types:
            print(f"\n📊 Testing {topology_type} topology...")
            topology_results = {}
            
            for n_nodes in self.network_sizes:
                print(f"   🔍 Testing {topology_type} with {n_nodes} nodes...")
                
                # Generate topology
                topology = self.generate_network_topology(topology_type, n_nodes)
                
                # Calculate network metrics
                metrics = self.calculate_network_metrics(topology)
                
                # Run Flee simulation
                simulation_results = self._run_flee_simulation(topology, metrics)
                
                # Store results
                topology_results[n_nodes] = {
                    'topology': topology,
                    'metrics': metrics.__dict__,
                    'simulation': simulation_results
                }
                
                print(f"      ✅ S2 rate: {simulation_results['s2_rate']:.1%}")
            
            all_results[topology_type] = topology_results
        
        # Save and analyze results
        self._save_results(all_results)
        self._generate_analysis(all_results)
        
        return all_results
    
    def _run_flee_simulation(self, topology: Dict[str, Any], metrics: NetworkMetrics) -> Dict[str, Any]:
        """Run Flee simulation with network-aware S2 parameters"""
        
        # Setup Flee simulation
        SimulationSettings.ReadFromYML("flee/simsetting.yml")
        ecosystem = Ecosystem()
        
        # Add locations
        locations = {}
        for loc in topology['locations']:
            location = ecosystem.addLocation(
                name=loc['name'],
                x=loc['x'], y=loc['y'],
                movechance=0.3 if loc['type'] == 'town' else (0.001 if loc['type'] == 'camp' else 1.0),
                capacity=loc['pop'] if loc['type'] == 'camp' else -1,
                pop=0
            )
            locations[loc['name']] = location
        
        # Add routes
        for route in topology['routes']:
            ecosystem.linkUp(route['from'], route['to'], route['distance'])
        
        # Spawn agents
        num_agents = min(50, metrics.n_nodes * 5)  # Scale agents with network size
        origin_location = locations[topology['locations'][0]['name']]
        
        for i in range(num_agents):
            attributes = {"profile_type": random.choice(['analytical', 'balanced', 'reactive'])}
            ecosystem.addAgent(origin_location, attributes)
        
        # Run simulation with network-aware S2 parameters
        simulation_days = 20
        s2_activations = []
        
        # Calculate network-aware threshold
        threshold = self._calculate_network_aware_threshold(metrics)
        
        for day in range(simulation_days):
            day_s2_count = 0
            for agent in ecosystem.agents:
                # Calculate cognitive pressure based on network metrics
                pressure = self._calculate_network_aware_pressure(agent, day, metrics)
                
                # Use network-aware S2 activation
                s2_active = calculate_systematic_s2_activation(agent, pressure, threshold, day)
                
                if s2_active:
                    day_s2_count += 1
                    agent.cognitive_state = "S2"
                else:
                    agent.cognitive_state = "S1"
            
            s2_activations.append(day_s2_count)
            ecosystem.evolve()
        
        # Calculate S2 rate
        total_s2_decisions = sum(s2_activations)
        total_possible_decisions = num_agents * simulation_days
        s2_rate = total_s2_decisions / total_possible_decisions if total_possible_decisions > 0 else 0
        
        return {
            's2_rate': s2_rate,
            's2_activations': s2_activations,
            'num_agents': num_agents,
            'simulation_days': simulation_days,
            'threshold': threshold
        }
    
    def _calculate_network_aware_threshold(self, metrics: NetworkMetrics) -> float:
        """Calculate S2 threshold based on network metrics"""
        
        base_threshold = self.optimal_params['base_threshold']
        
        # Use multiple network metrics for threshold calculation
        complexity_score = (
            metrics.avg_degree * 0.3 +
            metrics.clustering_coefficient * 0.2 +
            (1.0 / metrics.avg_path_length) * 0.2 +
            metrics.density * 0.2 +
            metrics.betweenness_centrality * 0.1
        )
        
        # Adjust threshold based on complexity
        if complexity_score < 0.3:
            return base_threshold + 0.2  # Higher threshold for simple networks
        elif complexity_score < 0.6:
            return base_threshold + 0.1
        elif complexity_score < 0.8:
            return base_threshold
        else:
            return base_threshold - 0.1  # Lower threshold for complex networks
    
    def _calculate_network_aware_pressure(self, agent, time: int, metrics: NetworkMetrics) -> float:
        """Calculate cognitive pressure based on network metrics"""
        
        base_pressure = 0.3
        time_factor = 0.1 * math.sin(time * 0.5)
        
        # Network complexity factor
        complexity_factor = (
            metrics.avg_degree * 0.1 +
            metrics.clustering_coefficient * 0.1 +
            (1.0 / metrics.avg_path_length) * 0.1
        )
        
        random_factor = random.uniform(-0.1, 0.1)
        
        pressure = base_pressure + time_factor + complexity_factor + random_factor
        return max(0.0, min(1.0, pressure))
    
    def _save_results(self, all_results: Dict[str, Any]):
        """Save all results in organized structure"""
        
        # Save raw data
        raw_data_file = self.results_dir / 'raw_data' / 'systematic_scaling_results.json'
        with open(raw_data_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        # Save network metrics
        metrics_file = self.results_dir / 'network_metrics' / 'network_metrics_summary.json'
        metrics_summary = {}
        
        for topology_type, topology_results in all_results.items():
            metrics_summary[topology_type] = {}
            for n_nodes, result in topology_results.items():
                metrics_summary[topology_type][n_nodes] = result['metrics']
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_summary, f, indent=2)
        
        print(f"✅ Results saved to: {self.results_dir}")
    
    def _generate_analysis(self, all_results: Dict[str, Any]):
        """Generate comprehensive analysis"""
        
        print("📊 Generating systematic analysis...")
        
        # Create comprehensive figure
        fig, axes = plt.subplots(3, 2, figsize=(15, 18))
        fig.suptitle('Systematic Network Scaling: S2 Activation Analysis', fontsize=16, fontweight='bold')
        
        # Extract data for plotting
        topology_types = list(all_results.keys())
        network_sizes = self.network_sizes
        
        # Plot 1: S2 Rate vs Network Size
        ax1 = axes[0, 0]
        for topology_type in topology_types:
            s2_rates = []
            for n_nodes in network_sizes:
                if n_nodes in all_results[topology_type]:
                    s2_rates.append(all_results[topology_type][n_nodes]['simulation']['s2_rate'])
                else:
                    s2_rates.append(0)
            
            ax1.plot(network_sizes, s2_rates, marker='o', label=topology_type, linewidth=2)
        
        ax1.set_title('S2 Activation Rate vs Network Size')
        ax1.set_xlabel('Number of Nodes')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Network Metrics vs S2 Rate
        ax2 = axes[0, 1]
        for topology_type in topology_types:
            avg_degrees = []
            s2_rates = []
            for n_nodes in network_sizes:
                if n_nodes in all_results[topology_type]:
                    metrics = all_results[topology_type][n_nodes]['metrics']
                    avg_degrees.append(metrics['avg_degree'])
                    s2_rates.append(all_results[topology_type][n_nodes]['simulation']['s2_rate'])
            
            ax2.scatter(avg_degrees, s2_rates, label=topology_type, alpha=0.7, s=50)
        
        ax2.set_title('Average Degree vs S2 Activation Rate')
        ax2.set_xlabel('Average Degree')
        ax2.set_ylabel('S2 Activation Rate')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Clustering Coefficient vs S2 Rate
        ax3 = axes[1, 0]
        for topology_type in topology_types:
            clustering_coeffs = []
            s2_rates = []
            for n_nodes in network_sizes:
                if n_nodes in all_results[topology_type]:
                    metrics = all_results[topology_type][n_nodes]['metrics']
                    clustering_coeffs.append(metrics['clustering_coefficient'])
                    s2_rates.append(all_results[topology_type][n_nodes]['simulation']['s2_rate'])
            
            ax3.scatter(clustering_coeffs, s2_rates, label=topology_type, alpha=0.7, s=50)
        
        ax3.set_title('Clustering Coefficient vs S2 Activation Rate')
        ax3.set_xlabel('Clustering Coefficient')
        ax3.set_ylabel('S2 Activation Rate')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Path Length vs S2 Rate
        ax4 = axes[1, 1]
        for topology_type in topology_types:
            path_lengths = []
            s2_rates = []
            for n_nodes in network_sizes:
                if n_nodes in all_results[topology_type]:
                    metrics = all_results[topology_type][n_nodes]['metrics']
                    path_lengths.append(metrics['avg_path_length'])
                    s2_rates.append(all_results[topology_type][n_nodes]['simulation']['s2_rate'])
            
            ax4.scatter(path_lengths, s2_rates, label=topology_type, alpha=0.7, s=50)
        
        ax4.set_title('Average Path Length vs S2 Activation Rate')
        ax4.set_xlabel('Average Path Length')
        ax4.set_ylabel('S2 Activation Rate')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Network Density vs S2 Rate
        ax5 = axes[2, 0]
        for topology_type in topology_types:
            densities = []
            s2_rates = []
            for n_nodes in network_sizes:
                if n_nodes in all_results[topology_type]:
                    metrics = all_results[topology_type][n_nodes]['metrics']
                    densities.append(metrics['density'])
                    s2_rates.append(all_results[topology_type][n_nodes]['simulation']['s2_rate'])
            
            ax5.scatter(densities, s2_rates, label=topology_type, alpha=0.7, s=50)
        
        ax5.set_title('Network Density vs S2 Activation Rate')
        ax5.set_xlabel('Network Density')
        ax5.set_ylabel('S2 Activation Rate')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # Plot 6: Summary Statistics
        ax6 = axes[2, 1]
        summary_stats = []
        for topology_type in topology_types:
            s2_rates = []
            for n_nodes in network_sizes:
                if n_nodes in all_results[topology_type]:
                    s2_rates.append(all_results[topology_type][n_nodes]['simulation']['s2_rate'])
            
            if s2_rates:
                summary_stats.append({
                    'topology': topology_type,
                    'mean_s2': np.mean(s2_rates),
                    'std_s2': np.std(s2_rates),
                    'min_s2': np.min(s2_rates),
                    'max_s2': np.max(s2_rates)
                })
        
        topologies = [stat['topology'] for stat in summary_stats]
        means = [stat['mean_s2'] for stat in summary_stats]
        stds = [stat['std_s2'] for stat in summary_stats]
        
        bars = ax6.bar(topologies, means, yerr=stds, capsize=5, alpha=0.7)
        ax6.set_title('S2 Activation Rate Summary by Topology')
        ax6.set_ylabel('Mean S2 Activation Rate')
        ax6.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, mean in zip(bars, means):
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{mean:.1%}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Save figure
        figure_file = self.results_dir / 'figures' / 'systematic_network_scaling_analysis.png'
        plt.savefig(figure_file, dpi=300, bbox_inches='tight')
        plt.savefig(figure_file.with_suffix('.pdf'), bbox_inches='tight')
        plt.close()
        
        print(f"✅ Analysis saved: {figure_file}")
        
        # Generate summary report
        self._generate_summary_report(all_results, summary_stats)
    
    def _generate_summary_report(self, all_results: Dict[str, Any], summary_stats: List[Dict]):
        """Generate comprehensive summary report"""
        
        report_file = self.results_dir / 'reports' / 'systematic_scaling_summary.md'
        
        with open(report_file, 'w') as f:
            f.write("# Systematic Network Scaling: S2 Activation Analysis\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Overview\n\n")
            f.write("This report presents results from systematic network scaling experiments testing S2 activation rates across different network topologies and sizes.\n\n")
            
            f.write("## Experimental Design\n\n")
            f.write(f"- **Network sizes:** {self.network_sizes} (geometric progression)\n")
            f.write(f"- **Topology types:** {', '.join(self.config.topology_types)}\n")
            f.write(f"- **Scaling factor:** {self.config.scaling_factor}\n")
            f.write(f"- **S2 target range:** {self.config.s2_target_range[0]:.1%} - {self.config.s2_target_range[1]:.1%}\n\n")
            
            f.write("## Key Findings\n\n")
            
            for stat in summary_stats:
                f.write(f"### {stat['topology'].title()} Topology\n\n")
                f.write(f"- **Mean S2 rate:** {stat['mean_s2']:.1%} ± {stat['std_s2']:.1%}\n")
                f.write(f"- **Range:** {stat['min_s2']:.1%} - {stat['max_s2']:.1%}\n")
                f.write(f"- **Variation:** {stat['std_s2']:.1%}\n\n")
            
            f.write("## Network Metrics Analysis\n\n")
            f.write("The analysis examines relationships between core network metrics and S2 activation rates:\n\n")
            f.write("- **Average Degree:** Number of connections per node\n")
            f.write("- **Clustering Coefficient:** Local connectivity patterns\n")
            f.write("- **Average Path Length:** Network efficiency\n")
            f.write("- **Network Density:** Overall connectivity\n")
            f.write("- **Betweenness Centrality:** Node importance\n\n")
            
            f.write("## Recommendations\n\n")
            f.write("1. **Scale network sizes** systematically using geometric progression\n")
            f.write("2. **Use core network metrics** for scientifically defensible analysis\n")
            f.write("3. **Organize results** in structured directories\n")
            f.write("4. **Validate findings** with statistical analysis\n")
            f.write("5. **Generate publication-ready** figures and tables\n\n")
        
        print(f"✅ Summary report saved: {report_file}")

def main():
    """Main function to run systematic network scaling"""
    print("🌐 Systematic Network Scaling Framework")
    print("=" * 60)
    print("Using core network metrics and organized results management")
    print("=" * 60)
    
    # Create experiment configuration
    config = ExperimentConfig(
        base_nodes=5,
        scaling_factor=1.5,
        max_nodes=25,  # Start smaller for testing
        topology_types=['linear', 'star', 'tree', 'grid'],
        s2_target_range=(0.20, 0.30)
    )
    
    # Create scaler
    scaler = SystematicNetworkScaler(config)
    
    # Run systematic experiment
    results = scaler.run_systematic_scaling_experiment()
    
    print("\n🎯 Systematic Network Scaling Complete!")
    print(f"   Results organized in: {scaler.results_dir}")
    print(f"   Network sizes tested: {scaler.network_sizes}")
    print(f"   Topology types: {config.topology_types}")
    print("   Analysis: Core network metrics + organized results")

if __name__ == "__main__":
    main()
