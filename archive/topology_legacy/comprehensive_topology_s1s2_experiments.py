#!/usr/bin/env python3
"""
Comprehensive and Rigorous S1/S2 Topology Experiments

This script implements a scientifically rigorous experimental framework to systematically
test how S1/S2 dual-process decision-making behavior varies across different network
topologies with proper controls, statistical power, and comprehensive metrics.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import yaml
import time
from pathlib import Path
import seaborn as sns
from scipy import stats
import networkx as nx
from itertools import product
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, '.')

@dataclass
class TopologySpec:
    """Specification for a network topology."""
    name: str
    description: str
    n_locations: int
    n_agents: int
    network_type: str
    parameters: Dict
    expected_properties: Dict

@dataclass
class S1S2Config:
    """S1/S2 configuration specification."""
    name: str
    description: str
    parameters: Dict

class ComprehensiveTopologyExperiment:
    """Comprehensive topology experiments with rigorous controls."""
    
    def __init__(self):
        self.results = {}
        self.network_metrics = {}
        
        # Define comprehensive topology specifications
        self.topology_specs = self._define_topology_specs()
        
        # Define S1/S2 configurations
        self.s1s2_configs = self._define_s1s2_configs()
        
        # Experimental parameters
        self.n_replicates = 10  # Increased for statistical power
        self.timesteps = 100    # Longer simulations
        self.random_seeds = list(range(1000, 1000 + self.n_replicates))
        
    def _define_topology_specs(self) -> List[TopologySpec]:
        """Define comprehensive topology specifications."""
        
        specs = []
        
        # 1. Linear Topologies (Chain-like)
        for n in [4, 8, 16]:
            specs.append(TopologySpec(
                name=f"linear_{n}",
                description=f"Linear chain with {n} locations",
                n_locations=n,
                n_agents=100,
                network_type="linear",
                parameters={"length": n, "spacing": 2.0},
                expected_properties={
                    "diameter": n-1,
                    "clustering": 0.0,
                    "centrality_variance": "high"
                }
            ))
        
        # 2. Star Topologies (Hub-and-spoke)
        for n in [4, 8, 16]:
            specs.append(TopologySpec(
                name=f"star_{n}",
                description=f"Star network with {n} locations (1 hub + {n-1} spokes)",
                n_locations=n,
                n_agents=100,
                network_type="star",
                parameters={"n_spokes": n-1, "hub_centrality": 1.0},
                expected_properties={
                    "diameter": 2,
                    "clustering": 0.0,
                    "centrality_variance": "very_high"
                }
            ))
        
        # 3. Grid Topologies (2D grids)
        for n in [4, 9, 16]:  # 2x2, 3x3, 4x4
            specs.append(TopologySpec(
                name=f"grid_{n}",
                description=f"Grid network with {n} locations ({int(np.sqrt(n))}x{int(np.sqrt(n))})",
                n_locations=n,
                n_agents=100,
                network_type="grid",
                parameters={"width": int(np.sqrt(n)), "height": int(np.sqrt(n))},
                expected_properties={
                    "diameter": 2 * (int(np.sqrt(n)) - 1),
                    "clustering": "moderate",
                    "centrality_variance": "low"
                }
            ))
        
        # 4. Random Topologies (Erdős-Rényi)
        for n in [8, 16]:
            for p in [0.2, 0.4, 0.6]:  # Different connection probabilities
                specs.append(TopologySpec(
                    name=f"random_{n}_p{p}",
                    description=f"Random network with {n} locations, p={p}",
                    n_locations=n,
                    n_agents=100,
                    network_type="random",
                    parameters={"n_nodes": n, "p_connect": p},
                    expected_properties={
                        "diameter": "variable",
                        "clustering": "low",
                        "centrality_variance": "moderate"
                    }
                ))
        
        # 5. Scale-free Topologies (Barabási-Albert)
        for n in [8, 16]:
            for m in [2, 4]:  # Different attachment parameters
                specs.append(TopologySpec(
                    name=f"scale_free_{n}_m{m}",
                    description=f"Scale-free network with {n} locations, m={m}",
                    n_locations=n,
                    n_agents=100,
                    network_type="scale_free",
                    parameters={"n_nodes": n, "m_attach": m},
                    expected_properties={
                        "diameter": "small",
                        "clustering": "high",
                        "centrality_variance": "very_high"
                    }
                ))
        
        # 6. Ring Topologies
        for n in [8, 16]:
            specs.append(TopologySpec(
                name=f"ring_{n}",
                description=f"Ring network with {n} locations",
                n_locations=n,
                n_agents=100,
                network_type="ring",
                parameters={"n_nodes": n},
                expected_properties={
                    "diameter": n // 2,
                    "clustering": 0.0,
                    "centrality_variance": "none"
                }
            ))
        
        return specs
    
    def _define_s1s2_configs(self) -> List[S1S2Config]:
        """Define comprehensive S1/S2 configurations."""
        
        configs = []
        
        # Baseline configurations
        configs.append(S1S2Config(
            name="baseline",
            description="Standard S1/S2 behavior with scaled move probabilities",
            parameters={
                "connectivity_mode": "baseline",
                "soft_capability": False,
                "pmove_s2_mode": "scaled",
                "eta": 0.5,
                "steepness": 6.0
            }
        ))
        
        # Constant S2 configurations
        configs.append(S1S2Config(
            name="constant_s2",
            description="Fixed high move probability for S2-capable agents",
            parameters={
                "connectivity_mode": "baseline",
                "soft_capability": False,
                "pmove_s2_mode": "constant",
                "pmove_s2_constant": 0.9
            }
        ))
        
        # Soft capability gate configurations
        configs.append(S1S2Config(
            name="soft_gate",
            description="Gradual S2 activation using sigmoid functions",
            parameters={
                "connectivity_mode": "baseline",
                "soft_capability": True,
                "pmove_s2_mode": "scaled",
                "eta": 0.5,
                "steepness": 6.0,
                "soft_gate_steepness": 8.0
            }
        ))
        
        # Diminishing connectivity configurations
        configs.append(S1S2Config(
            name="diminishing",
            description="Diminishing connectivity effects over time",
            parameters={
                "connectivity_mode": "diminishing",
                "soft_capability": False,
                "pmove_s2_mode": "scaled",
                "eta": 0.5,
                "steepness": 6.0
            }
        ))
        
        # High eta (more S2 activation)
        configs.append(S1S2Config(
            name="high_eta",
            description="High eta parameter for increased S2 activation",
            parameters={
                "connectivity_mode": "baseline",
                "soft_capability": False,
                "pmove_s2_mode": "scaled",
                "eta": 0.8,
                "steepness": 6.0
            }
        ))
        
        # Low eta (less S2 activation)
        configs.append(S1S2Config(
            name="low_eta",
            description="Low eta parameter for reduced S2 activation",
            parameters={
                "connectivity_mode": "baseline",
                "soft_capability": False,
                "pmove_s2_mode": "scaled",
                "eta": 0.2,
                "steepness": 6.0
            }
        ))
        
        return configs
    
    def create_topology_network(self, spec: TopologySpec) -> nx.Graph:
        """Create a network topology based on specification."""
        
        if spec.network_type == "linear":
            G = nx.path_graph(spec.n_locations)
            
        elif spec.network_type == "star":
            G = nx.star_graph(spec.n_locations - 1)
            
        elif spec.network_type == "grid":
            width = spec.parameters["width"]
            height = spec.parameters["height"]
            G = nx.grid_2d_graph(width, height)
            # Relabel nodes to be sequential
            mapping = {node: i for i, node in enumerate(G.nodes())}
            G = nx.relabel_nodes(G, mapping)
            
        elif spec.network_type == "random":
            n = spec.parameters["n_nodes"]
            p = spec.parameters["p_connect"]
            G = nx.erdos_renyi_graph(n, p, seed=42)
            
        elif spec.network_type == "scale_free":
            n = spec.parameters["n_nodes"]
            m = spec.parameters["m_attach"]
            G = nx.barabasi_albert_graph(n, m, seed=42)
            
        elif spec.network_type == "ring":
            n = spec.parameters["n_nodes"]
            G = nx.cycle_graph(n)
            
        else:
            raise ValueError(f"Unknown network type: {spec.network_type}")
        
        # Ensure the graph is connected
        if not nx.is_connected(G):
            # Add edges to make it connected
            components = list(nx.connected_components(G))
            for i in range(len(components) - 1):
                G.add_edge(list(components[i])[0], list(components[i+1])[0])
        
        return G
    
    def calculate_network_metrics(self, G: nx.Graph) -> Dict:
        """Calculate comprehensive network metrics."""
        
        metrics = {}
        
        # Basic metrics
        metrics["n_nodes"] = G.number_of_nodes()
        metrics["n_edges"] = G.number_of_edges()
        metrics["density"] = nx.density(G)
        
        # Connectivity metrics
        metrics["diameter"] = nx.diameter(G) if nx.is_connected(G) else float('inf')
        metrics["radius"] = nx.radius(G) if nx.is_connected(G) else float('inf')
        metrics["average_path_length"] = nx.average_shortest_path_length(G) if nx.is_connected(G) else float('inf')
        
        # Centrality metrics
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        
        metrics["degree_centrality_mean"] = np.mean(list(degree_centrality.values()))
        metrics["degree_centrality_std"] = np.std(list(degree_centrality.values()))
        metrics["betweenness_centrality_mean"] = np.mean(list(betweenness_centrality.values()))
        metrics["betweenness_centrality_std"] = np.std(list(betweenness_centrality.values()))
        metrics["closeness_centrality_mean"] = np.mean(list(closeness_centrality.values()))
        metrics["closeness_centrality_std"] = np.std(list(closeness_centrality.values()))
        
        # Clustering
        metrics["average_clustering"] = nx.average_clustering(G)
        metrics["transitivity"] = nx.transitivity(G)
        
        # Assortativity
        metrics["degree_assortativity"] = nx.degree_assortativity_coefficient(G)
        
        return metrics
    
    def create_topology_input_files(self, spec: TopologySpec, G: nx.Graph, output_dir: str):
        """Create input CSV files for a topology."""
        
        # Create locations file
        locations_data = []
        for i, node in enumerate(G.nodes()):
            # Calculate position (for visualization)
            pos = nx.spring_layout(G, seed=42)
            x, y = pos[node]
            
            # Determine location type
            if i == 0:  # First node is origin
                location_type = "conflict_zone"
                population = 10000
                conflict_intensity = 1.0
            elif i < spec.n_locations // 2:  # First half are towns
                location_type = "town"
                population = 0
                conflict_intensity = 0.0
            else:  # Second half are camps
                location_type = "camp"
                population = 0
                conflict_intensity = 0.0
            
            locations_data.append({
                "name": f"Location_{i}",
                "region": "TestRegion",
                "country": "TestCountry",
                "gps_x": float(x * 10),  # Scale for realistic distances
                "gps_y": float(y * 10),
                "location_type": location_type,
                "conflict_date": 0 if conflict_intensity > 0 else 0,
                "pop/cap": int(population)
            })
        
        locations_df = pd.DataFrame(locations_data)
        # Write CSV with comment header (FLEE expects header to start with #)
        with open(os.path.join(output_dir, "locations.csv"), 'w') as f:
            f.write("#name,region,country,gps_x,gps_y,location_type,conflict_date,pop/cap\n")
            locations_df.to_csv(f, index=False, header=False)
        
        # Create conflicts file (time series format)
        conflicts_data = []
        # Create header with Day and location names
        header = ["Day"] + [f"Location_{i}" for i in range(spec.n_locations)]
        conflicts_data.append(header)
        
        # Create conflict time series (conflict only at origin for first few days)
        for day in range(10):  # 10 days of conflict data
            row = [day]
            for i in range(spec.n_locations):
                if i == 0 and day < 5:  # Origin has conflict for first 5 days
                    row.append(1)
                else:
                    row.append(0)
            conflicts_data.append(row)
        
        conflicts_df = pd.DataFrame(conflicts_data[1:], columns=conflicts_data[0])
        conflicts_df.to_csv(os.path.join(output_dir, "conflicts.csv"), index=False)
        
        # Create links file
        links_data = []
        for edge in G.edges():
            # Calculate distance based on positions
            node1, node2 = edge
            pos1 = pos[node1]
            pos2 = pos[node2]
            distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) * 10
            
            links_data.append({
                "name1": f"Location_{node1}",
                "name2": f"Location_{node2}",
                "distance": float(max(1.0, distance)),  # Minimum distance of 1
                "forced_redirection": "0",
                "blocked": "0"
            })
        
        links_df = pd.DataFrame(links_data)
        # Write CSV with comment header (FLEE expects header to start with #)
        with open(os.path.join(output_dir, "routes.csv"), 'w') as f:
            f.write("#name1,name2,distance,forced_redirection,blocked\n")
            links_df.to_csv(f, index=False, header=False)
        
        # Create closures file (empty with comment header)
        with open(os.path.join(output_dir, "closures.csv"), 'w') as f:
            f.write("#name1,name2,closure_start,closure_end\n")
    
    def run_single_experiment(self, spec: TopologySpec, s1s2_config: S1S2Config, 
                            replicate_id: int, output_dir: str) -> Optional[Dict]:
        """Run a single experiment with comprehensive data collection."""
        
        np.random.seed(self.random_seeds[replicate_id])
        
        # Create network topology
        G = self.create_topology_network(spec)
        
        # Calculate network metrics
        network_metrics = self.calculate_network_metrics(G)
        
        # Create input files
        self.create_topology_input_files(spec, G, output_dir)
        
        # Create simulation config
        sim_config = {
            'log_levels': {'agent': 0, 'link': 0, 'camp': 0, 'conflict': 0, 'init': 0, 'granularity': 'location'},
            'spawn_rules': {'take_from_population': False, 'insert_day0': True},
            'move_rules': {
                'max_move_speed': 360.0,
                'max_walk_speed': 35.0,
                'foreign_weight': 1.0,
                'camp_weight': 1.0,
                'conflict_weight': 0.25,
                'conflict_movechance': 0.0,
                'camp_movechance': 0.001,
                'default_movechance': 0.3,
                'awareness_level': 1,
                'capacity_scaling': 1.0,
                'avoid_short_stints': False,
                'start_on_foot': False,
                'weight_power': 1.0,
                'movechance_pop_base': 10000.0,
                'movechance_pop_scale_factor': 0.5,
                'two_system_decision_making': 0.5,
                'conflict_threshold': 0.5,
                **s1s2_config.parameters
            },
            'optimisations': {'hasten': 1}
        }
        
        # Write config file
        config_file = os.path.join(output_dir, f"config_{spec.name}_{s1s2_config.name}_{replicate_id}.yml")
        with open(config_file, 'w') as f:
            yaml.dump(sim_config, f)
        
        try:
            # Import FLEE components
            from flee import flee
            from flee import InputGeography
            
            # Read simulation settings
            flee.SimulationSettings.ReadFromYML(config_file)
            
            # Create ecosystem
            e = flee.Ecosystem()
            
            # Create input geography
            ig = InputGeography.InputGeography()
            
            # Read input files
            ig.ReadConflictInputCSV(os.path.join(output_dir, "conflicts.csv"))
            ig.ReadLocationsFromCSV(os.path.join(output_dir, "locations.csv"))
            ig.ReadLinksFromCSV(os.path.join(output_dir, "routes.csv"))
            ig.ReadClosuresFromCSV(os.path.join(output_dir, "closures.csv"))
            
            # Store input geography in ecosystem
            e, lm = ig.StoreInputGeographyInEcosystem(e)
            
            # Get origin location
            origin_location = None
            for loc_name, loc in lm.items():
                if "Location_0" in loc_name:
                    origin_location = loc
                    break
            
            if origin_location is None:
                print(f"❌ No origin location found for {spec.name}!")
                return None
            
            # Create agents with diverse attributes
            agents = []
            for i in range(spec.n_agents):
                attributes = {
                    'connections': np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8], p=[0.1, 0.15, 0.2, 0.2, 0.15, 0.1, 0.05, 0.03, 0.02]),
                    'education_level': np.random.beta(2, 3),
                    'stress_tolerance': np.random.beta(3, 2),
                    's2_threshold': np.random.uniform(0.3, 0.7)
                }
                agent = flee.Person(origin_location, attributes)
                agents.append(agent)
            
            e.agents = agents
            
            # Run simulation with comprehensive data collection
            results = {
                'timesteps': [],
                's2_activation_rates': [],
                'move_rates': [],
                'evacuation_rates': [],
                'pressure_stats': [],
                'location_populations': [],
                'agent_attributes': [],
                'network_metrics': network_metrics,
                'topology_spec': spec.__dict__,
                's1s2_config': s1s2_config.__dict__
            }
            
            for t in range(self.timesteps):
                e.time = t
                e.evolve()
                
                # Collect comprehensive statistics
                s2_active_count = 0
                move_count = 0
                evacuated_count = 0
                pressures = []
                location_pops = {}
                agent_attrs = []
                
                for agent in agents:
                    # S2 activation
                    if hasattr(agent, 'cognitive_state') and agent.cognitive_state == "S2":
                        s2_active_count += 1
                    
                    # Movement status
                    if agent.location != origin_location:
                        move_count += 1
                        if agent.location.name != origin_location.name:
                            evacuated_count += 1
                    
                    # Cognitive pressure
                    pressure = agent.calculate_cognitive_pressure(t)
                    pressures.append(pressure)
                    
                    # Agent attributes
                    agent_attrs.append({
                        'connections': agent.attributes.get('connections', 0),
                        'education': agent.attributes.get('education_level', 0.5),
                        'stress_tolerance': agent.attributes.get('stress_tolerance', 0.5),
                        's2_threshold': agent.attributes.get('s2_threshold', 0.5),
                        'pressure': pressure,
                        'location': agent.location.name if agent.location else 'None'
                    })
                
                # Location populations
                for loc_name, loc in lm.items():
                    location_pops[loc_name] = loc.pop
                
                # Store results
                results['timesteps'].append(t)
                results['s2_activation_rates'].append(s2_active_count / len(agents))
                results['move_rates'].append(move_count / len(agents))
                results['evacuation_rates'].append(evacuated_count / len(agents))
                results['pressure_stats'].append({
                    'mean': np.mean(pressures),
                    'std': np.std(pressures),
                    'min': np.min(pressures),
                    'max': np.max(pressures),
                    'q25': np.percentile(pressures, 25),
                    'q75': np.percentile(pressures, 75)
                })
                results['location_populations'].append(location_pops.copy())
                results['agent_attributes'].append(agent_attrs)
            
            return results
            
        except Exception as e:
            print(f"❌ Error in experiment {spec.name}-{s1s2_config.name}-{replicate_id}: {e}")
            return None
        
        finally:
            # Clean up temporary files
            for file_pattern in [config_file, "conflicts.csv", "locations.csv", "routes.csv", "closures.csv"]:
                file_path = os.path.join(output_dir, file_pattern)
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    def run_comprehensive_experiments(self):
        """Run comprehensive experiments across all topology-S1/S2 combinations."""
        
        print("🧪 COMPREHENSIVE TOPOLOGY-S1/S2 EXPERIMENTS")
        print("=" * 80)
        print(f"Topologies: {len(self.topology_specs)}")
        print(f"S1/S2 Configs: {len(self.s1s2_configs)}")
        print(f"Replicates: {self.n_replicates}")
        print(f"Total Experiments: {len(self.topology_specs) * len(self.s1s2_configs) * self.n_replicates}")
        print()
        
        # Create output directory
        output_dir = "results/comprehensive_topology_experiments"
        os.makedirs(output_dir, exist_ok=True)
        
        experiment_results = {}
        total_experiments = len(self.topology_specs) * len(self.s1s2_configs) * self.n_replicates
        experiment_count = 0
        
        for spec in self.topology_specs:
            print(f"\n🌐 Testing Topology: {spec.name} ({spec.description})")
            print("-" * 60)
            
            experiment_results[spec.name] = {}
            
            for s1s2_config in self.s1s2_configs:
                print(f"  🔧 S1/S2 Config: {s1s2_config.name}")
                
                experiment_results[spec.name][s1s2_config.name] = []
                
                # Create topology-specific output directory
                topology_output_dir = os.path.join(output_dir, f"{spec.name}_{s1s2_config.name}")
                os.makedirs(topology_output_dir, exist_ok=True)
                
                for replicate in range(self.n_replicates):
                    experiment_count += 1
                    print(f"    📊 Replicate {replicate + 1}/{self.n_replicates} ({experiment_count}/{total_experiments})")
                    
                    result = self.run_single_experiment(
                        spec=spec,
                        s1s2_config=s1s2_config,
                        replicate_id=replicate,
                        output_dir=topology_output_dir
                    )
                    
                    if result is not None:
                        experiment_results[spec.name][s1s2_config.name].append(result)
                        
                        # Save individual result
                        result_file = os.path.join(topology_output_dir, f"result_{replicate}.json")
                        with open(result_file, 'w') as f:
                            # Convert numpy types to Python types for JSON serialization
                            json_result = self._convert_numpy_types(result)
                            json.dump(json_result, f, indent=2)
                        
                        print(f"      ✅ Success")
                    else:
                        print(f"      ❌ Failed")
        
        # Save comprehensive results
        self.results = experiment_results
        results_file = os.path.join(output_dir, "comprehensive_results.json")
        with open(results_file, 'w') as f:
            json_results = self._convert_numpy_types(experiment_results)
            json.dump(json_results, f, indent=2)
        
        print(f"\n🎉 COMPREHENSIVE EXPERIMENTS COMPLETE!")
        print(f"📁 Results saved in: {output_dir}")
        
        return experiment_results
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to Python types for JSON serialization."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj


def main():
    """Main function to run comprehensive topology experiments."""
    
    print("🧪 COMPREHENSIVE TOPOLOGY-S1/S2 EXPERIMENTS")
    print("=" * 80)
    print("This implements a scientifically rigorous experimental framework")
    print("to systematically test S1/S2 behavior across diverse network topologies.")
    print()
    
    # Create experiment instance
    experiment = ComprehensiveTopologyExperiment()
    
    # Run comprehensive experiments
    results = experiment.run_comprehensive_experiments()
    
    print("\n🎉 COMPREHENSIVE TOPOLOGY EXPERIMENTS COMPLETE!")
    print("\nKey features:")
    print("• 6 different topology types with multiple variants")
    print("• 6 different S1/S2 configurations")
    print("• 10 replicates per combination for statistical power")
    print("• Comprehensive network metrics and behavioral analysis")
    print("• Rigorous experimental controls and data collection")
    print("\nResults ready for comprehensive analysis!")


if __name__ == "__main__":
    main()
