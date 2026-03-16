#!/usr/bin/env python3
"""
Compare Initial Population Distributions
Analyzes different initial population distribution strategies and their effects on network flow patterns
"""

import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Any
import seaborn as sns

# Add current directory to path
sys.path.insert(0, '.')

# Set style for publication-ready figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

class InitialPopulationDistributionComparator:
    """Compare different initial population distribution strategies"""
    
    def __init__(self, output_dir="population_distribution_comparison"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Define different distribution strategies
        self.distribution_strategies = {
            'single_origin': {
                'name': 'Single Origin',
                'description': 'All agents start at one conflict location',
                'color': 'red'
            },
            'multiple_origins': {
                'name': 'Multiple Origins',
                'description': 'Agents distributed across multiple conflict locations',
                'color': 'orange'
            },
            'population_weighted': {
                'name': 'Population Weighted',
                'description': 'Agents distributed based on location population',
                'color': 'blue'
            },
            'conflict_intensity': {
                'name': 'Conflict Intensity',
                'description': 'Agents distributed based on conflict levels',
                'color': 'purple'
            },
            'uniform_distribution': {
                'name': 'Uniform Distribution',
                'description': 'Agents evenly distributed across all locations',
                'color': 'green'
            }
        }
    
    def create_network_topology(self, topology_type="linear", n_nodes=5):
        """Create network topology"""
        
        if topology_type == 'linear':
            locations = []
            routes = []
            
            for i in range(n_nodes):
                # Add some vertical variation for better 2D positioning
                y_variation = 0.5 * np.sin(i * 0.3)
                
                if i == 0:
                    locations.append({
                        'name': f'Conflict_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': y_variation,
                        'type': 'conflict', 'pop': 5000, 'conflict_level': 1.0
                    })
                elif i < n_nodes // 2:
                    locations.append({
                        'name': f'Town_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': y_variation,
                        'type': 'town', 'pop': 1000, 'conflict_level': 0.0
                    })
                else:
                    locations.append({
                        'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': y_variation,
                        'type': 'camp', 'pop': 2000, 'conflict_level': 0.0
                    })
            
            # Create linear connections
            for i in range(n_nodes - 1):
                routes.append({
                    'from': locations[i]['name'],
                    'to': locations[i + 1]['name'],
                    'distance': 100.0
                })
        
        elif topology_type == 'star':
            locations = []
            routes = []
            
            # Origin at center
            locations.append({
                'name': f'Conflict_0_{topology_type}_{n_nodes}',
                'x': 0.0, 'y': 0.0,
                'type': 'conflict', 'pop': 5000, 'conflict_level': 1.0
            })
            
            # Hub
            locations.append({
                'name': f'Hub_{topology_type}_{n_nodes}',
                'x': 2.0, 'y': 0.0,
                'type': 'town', 'pop': 1000, 'conflict_level': 0.0
            })
            
            # Camps in star pattern
            for i in range(2, n_nodes):
                angle = 2 * np.pi * (i - 2) / (n_nodes - 2)
                x = 4.0 * np.cos(angle)
                y = 4.0 * np.sin(angle)
                locations.append({
                    'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                    'x': x, 'y': y,
                    'type': 'camp', 'pop': 2000, 'conflict_level': 0.0
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
        
        return {
            'name': f'{topology_type.title()} Network (n={n_nodes})',
            'locations': locations,
            'routes': routes
        }
    
    def distribute_agents(self, locations, strategy, num_agents=50):
        """Distribute agents according to different strategies"""
        
        agent_distribution = {}
        
        if strategy == 'single_origin':
            # All agents start at the first conflict location
            conflict_locations = [loc for loc in locations if loc['type'] == 'conflict']
            if conflict_locations:
                agent_distribution[conflict_locations[0]['name']] = num_agents
            else:
                agent_distribution[locations[0]['name']] = num_agents
        
        elif strategy == 'multiple_origins':
            # Distribute agents across all conflict locations
            conflict_locations = [loc for loc in locations if loc['type'] == 'conflict']
            if len(conflict_locations) > 1:
                agents_per_location = num_agents // len(conflict_locations)
                remainder = num_agents % len(conflict_locations)
                
                for i, loc in enumerate(conflict_locations):
                    agents = agents_per_location + (1 if i < remainder else 0)
                    agent_distribution[loc['name']] = agents
            else:
                agent_distribution[conflict_locations[0]['name']] = num_agents
        
        elif strategy == 'population_weighted':
            # Distribute agents based on population
            total_pop = sum(loc['pop'] for loc in locations)
            for loc in locations:
                if loc['pop'] > 0:
                    agents = int((loc['pop'] / total_pop) * num_agents)
                    agent_distribution[loc['name']] = agents
            
            # Ensure total agents matches target
            current_total = sum(agent_distribution.values())
            if current_total < num_agents:
                # Add remaining agents to largest population location
                largest_loc = max(agent_distribution.keys(), key=lambda k: agent_distribution[k])
                agent_distribution[largest_loc] += (num_agents - current_total)
        
        elif strategy == 'conflict_intensity':
            # Distribute agents based on conflict levels
            conflict_locations = [loc for loc in locations if loc['conflict_level'] > 0]
            if conflict_locations:
                total_conflict = sum(loc['conflict_level'] for loc in conflict_locations)
                for loc in conflict_locations:
                    agents = int((loc['conflict_level'] / total_conflict) * num_agents)
                    agent_distribution[loc['name']] = agents
                
                # Ensure total agents matches target
                current_total = sum(agent_distribution.values())
                if current_total < num_agents:
                    largest_loc = max(agent_distribution.keys(), key=lambda k: agent_distribution[k])
                    agent_distribution[largest_loc] += (num_agents - current_total)
            else:
                agent_distribution[locations[0]['name']] = num_agents
        
        elif strategy == 'uniform_distribution':
            # Distribute agents evenly across all locations
            agents_per_location = num_agents // len(locations)
            remainder = num_agents % len(locations)
            
            for i, loc in enumerate(locations):
                agents = agents_per_location + (1 if i < remainder else 0)
                agent_distribution[loc['name']] = agents
        
        return agent_distribution
    
    def run_simulation_with_distribution(self, topology_type="linear", n_nodes=5, strategy="single_origin"):
        """Run simulation with specific agent distribution strategy"""
        
        print(f"🔄 Running {strategy} distribution for {topology_type} network ({n_nodes} nodes)")
        
        # Import Flee components
        from flee.flee import Ecosystem, Person
        from flee.SimulationSettings import SimulationSettings
        from flee import moving, spawning
        from flee.moving import calculate_systematic_s2_activation
        
        # Create simsetting.yml with agent tracking enabled
        simsetting_content = f"""log_levels:
  agent: 1  # Enable agent tracking
  link: 1   # Enable link tracking
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
        
        # Write simsetting.yml
        with open("simsetting.yml", "w") as f:
            f.write(simsetting_content)
        
        # Setup Flee simulation
        SimulationSettings.ReadFromYML("simsetting.yml")
        ecosystem = Ecosystem()
        
        # Generate network topology
        topology = self.create_network_topology(topology_type, n_nodes)
        
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
        
        # Distribute agents according to strategy
        num_agents = min(50, n_nodes * 5)
        agent_distribution = self.distribute_agents(topology['locations'], strategy, num_agents)
        
        # Spawn agents according to distribution
        for loc_name, num_agents_at_loc in agent_distribution.items():
            if num_agents_at_loc > 0 and loc_name in locations:
                for i in range(num_agents_at_loc):
                    attributes = {"profile_type": np.random.choice(['analytical', 'balanced', 'reactive'])}
                    ecosystem.addAgent(locations[loc_name], attributes)
        
        # Run simulation with agent tracking
        simulation_days = 20
        s2_activations = []
        
        for day in range(simulation_days):
            day_s2_count = 0
            for agent in ecosystem.agents:
                # Calculate cognitive pressure
                pressure = 0.3 + 0.1 * np.sin(day * 0.5) + np.random.uniform(-0.1, 0.1)
                
                # Use systematic S2 activation
                s2_active = calculate_systematic_s2_activation(agent, pressure, 0.5, day)
                
                if s2_active:
                    day_s2_count += 1
                    agent.cognitive_state = "S2"
                else:
                    agent.cognitive_state = "S1"
            
            s2_activations.append(day_s2_count)
            ecosystem.evolve()  # This will write agent tracking files
        
        # Calculate S2 rate
        total_s2_decisions = sum(s2_activations)
        total_possible_decisions = num_agents * simulation_days
        s2_rate = total_s2_decisions / total_possible_decisions if total_possible_decisions > 0 else 0
        
        return {
            'topology': topology,
            'agent_distribution': agent_distribution,
            's2_rate': s2_rate,
            'num_agents': num_agents,
            'simulation_days': simulation_days,
            's2_activations': s2_activations
        }
    
    def analyze_agent_tracking_data(self):
        """Analyze agent tracking data"""
        
        # Check if agent tracking files exist
        agent_file = Path("agents.out.0")
        if not agent_file.exists():
            print(f"⚠️  Agent tracking file not found: {agent_file}")
            return None
        
        # Read agent tracking data
        try:
            # Read the header line to get column names
            with open(agent_file, 'r') as f:
                header_line = f.readline().strip()
                if header_line.startswith('#'):
                    header_line = header_line[1:]  # Remove the # symbol
                column_names = header_line.split(',')
            
            # Read the data with proper column names
            df = pd.read_csv(agent_file, comment='#', names=column_names)
            print(f"✅ Loaded agent tracking data: {len(df)} records")
        except Exception as e:
            print(f"❌ Error reading agent tracking data: {e}")
            return None
        
        # Analyze flow patterns
        flow_analysis = self._analyze_flow_patterns(df)
        
        return flow_analysis
    
    def _analyze_flow_patterns(self, df):
        """Analyze flow patterns from agent tracking data"""
        
        # Group by time and location to get population counts
        daily_populations = df.groupby(['time', 'current_location']).size().unstack(fill_value=0)
        
        # Calculate flows between locations
        flows = {}
        for i in range(len(daily_populations) - 1):
            current_day = daily_populations.iloc[i]
            next_day = daily_populations.iloc[i + 1]
            
            for loc in current_day.index:
                if loc in next_day.index:
                    flow = max(0, next_day[loc] - current_day[loc])
                    if loc not in flows:
                        flows[loc] = []
                    flows[loc].append(flow)
        
        # Calculate average flows
        avg_flows = {loc: np.mean(flows[loc]) if flows[loc] else 0 for loc in flows}
        
        return {
            'daily_populations': daily_populations.to_dict(),
            'flows': flows,
            'avg_flows': avg_flows,
            'total_agents': len(df['rank-agentid'].unique())
        }
    
    def compare_distributions(self, topology_type="linear", n_nodes=5):
        """Compare all distribution strategies for a given topology"""
        
        print(f"📊 Comparing population distributions for {topology_type} network ({n_nodes} nodes)")
        
        results = {}
        
        for strategy, strategy_info in self.distribution_strategies.items():
            print(f"\n🔄 Testing {strategy_info['name']} distribution...")
            
            # Run simulation
            simulation_result = self.run_simulation_with_distribution(topology_type, n_nodes, strategy)
            
            # Analyze agent tracking data
            flow_analysis = self.analyze_agent_tracking_data()
            
            if flow_analysis is not None:
                results[strategy] = {
                    'simulation': simulation_result,
                    'flow_analysis': flow_analysis,
                    'strategy_info': strategy_info
                }
            
            # Clean up agent tracking files
            self._cleanup_agent_files()
        
        # Create comparison visualization
        self._create_distribution_comparison(results, topology_type, n_nodes)
        
        return results
    
    def _create_distribution_comparison(self, results, topology_type, n_nodes):
        """Create comprehensive comparison visualization"""
        
        fig = plt.figure(figsize=(24, 16))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        fig.suptitle(f'Initial Population Distribution Comparison: {topology_type.title()} Network (n={n_nodes})', 
                    fontsize=20, fontweight='bold')
        
        # Plot 1: Initial agent distributions
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_initial_distributions(ax1, results)
        
        # Plot 2: S2 activation rates comparison
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_s2_rates_comparison(ax2, results)
        
        # Plot 3: Flow strength comparison
        ax3 = fig.add_subplot(gs[0, 2])
        self._plot_flow_strength_comparison(ax3, results)
        
        # Plot 4: Network topology with different distributions
        ax4 = fig.add_subplot(gs[0, 3])
        self._plot_network_topology_comparison(ax4, results, topology_type, n_nodes)
        
        # Plot 5-8: Individual distribution network plots
        for i, (strategy, result) in enumerate(results.items()):
            if i < 4:  # Only plot first 4 strategies
                ax = fig.add_subplot(gs[1, i])
                self._plot_individual_distribution(ax, result, strategy, topology_type, n_nodes)
        
        # Plot 9-12: Population over time for each distribution
        for i, (strategy, result) in enumerate(results.items()):
            if i < 4:  # Only plot first 4 strategies
                ax = fig.add_subplot(gs[2, i])
                self._plot_population_over_time(ax, result, strategy)
        
        # Save figure
        output_file = self.output_dir / f"{topology_type}_population_distribution_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.savefig(output_file.with_suffix('.pdf'), bbox_inches='tight')
        
        print(f"✅ Distribution comparison saved: {output_file}")
    
    def _plot_initial_distributions(self, ax, results):
        """Plot initial agent distributions"""
        
        strategies = list(results.keys())
        distributions = []
        colors = []
        
        for strategy in strategies:
            result = results[strategy]
            agent_dist = result['simulation']['agent_distribution']
            total_agents = sum(agent_dist.values())
            
            # Create distribution summary
            dist_summary = {}
            for loc, count in agent_dist.items():
                if 'conflict' in loc.lower():
                    dist_summary['Conflict'] = dist_summary.get('Conflict', 0) + count
                elif 'town' in loc.lower() or 'hub' in loc.lower():
                    dist_summary['Town'] = dist_summary.get('Town', 0) + count
                elif 'camp' in loc.lower():
                    dist_summary['Camp'] = dist_summary.get('Camp', 0) + count
            
            distributions.append(dist_summary)
            colors.append(results[strategy]['strategy_info']['color'])
        
        # Plot as stacked bar chart
        x = np.arange(len(strategies))
        width = 0.6
        
        conflict_counts = [d.get('Conflict', 0) for d in distributions]
        town_counts = [d.get('Town', 0) for d in distributions]
        camp_counts = [d.get('Camp', 0) for d in distributions]
        
        ax.bar(x, conflict_counts, width, label='Conflict', color='red', alpha=0.7)
        ax.bar(x, town_counts, width, bottom=conflict_counts, label='Town', color='orange', alpha=0.7)
        ax.bar(x, camp_counts, width, bottom=np.array(conflict_counts) + np.array(town_counts), 
               label='Camp', color='green', alpha=0.7)
        
        ax.set_xlabel('Distribution Strategy')
        ax.set_ylabel('Number of Agents')
        ax.set_title('Initial Agent Distribution by Strategy')
        ax.set_xticks(x)
        ax.set_xticklabels([results[s]['strategy_info']['name'] for s in strategies], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_s2_rates_comparison(self, ax, results):
        """Plot S2 activation rates comparison"""
        
        strategies = list(results.keys())
        s2_rates = [results[s]['simulation']['s2_rate'] for s in strategies]
        colors = [results[s]['strategy_info']['color'] for s in strategies]
        
        bars = ax.bar(strategies, s2_rates, color=colors, alpha=0.7)
        ax.set_xlabel('Distribution Strategy')
        ax.set_ylabel('S2 Activation Rate')
        ax.set_title('S2 Activation Rates by Distribution')
        ax.set_xticklabels([results[s]['strategy_info']['name'] for s in strategies], rotation=45)
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, rate in zip(bars, s2_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{rate:.1%}', ha='center', va='bottom', fontweight='bold')
    
    def _plot_flow_strength_comparison(self, ax, results):
        """Plot flow strength comparison"""
        
        strategies = list(results.keys())
        flow_strengths = []
        
        for strategy in strategies:
            result = results[strategy]
            avg_flows = result['flow_analysis']['avg_flows']
            total_flow = sum(avg_flows.values())
            flow_strengths.append(total_flow)
        
        colors = [results[s]['strategy_info']['color'] for s in strategies]
        bars = ax.bar(strategies, flow_strengths, color=colors, alpha=0.7)
        ax.set_xlabel('Distribution Strategy')
        ax.set_ylabel('Total Flow Strength')
        ax.set_title('Total Flow Strength by Distribution')
        ax.set_xticklabels([results[s]['strategy_info']['name'] for s in strategies], rotation=45)
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, strength in zip(bars, flow_strengths):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{strength:.1f}', ha='center', va='bottom', fontweight='bold')
    
    def _plot_network_topology_comparison(self, ax, results, topology_type, n_nodes):
        """Plot network topology comparison"""
        
        # Use the first result to get topology
        first_result = list(results.values())[0]
        topology = first_result['simulation']['topology']
        locations = topology['locations']
        routes = topology['routes']
        
        # Create network graph
        G = nx.DiGraph()
        
        # Add nodes
        node_positions = {}
        node_colors = []
        node_sizes = []
        
        for loc in locations:
            name = loc['name']
            x, y = loc['x'], loc['y']
            
            G.add_node(name)
            node_positions[name] = (x, y)
            
            # Color by type
            if 'conflict' in name.lower():
                node_colors.append('red')
                node_sizes.append(1500)
            elif 'town' in name.lower() or 'hub' in name.lower():
                node_colors.append('orange')
                node_sizes.append(1200)
            elif 'camp' in name.lower():
                node_colors.append('green')
                node_sizes.append(1300)
            else:
                node_colors.append('gray')
                node_sizes.append(1000)
        
        # Add edges
        for route in routes:
            G.add_edge(route['from'], route['to'])
        
        # Draw network
        nx.draw_networkx_nodes(G, node_positions, 
                              node_color=node_colors, 
                              node_size=node_sizes, 
                              alpha=0.8, ax=ax)
        
        nx.draw_networkx_edges(G, node_positions, 
                              edge_color='gray', 
                              width=2, 
                              alpha=0.7, 
                              arrows=True, 
                              arrowsize=20, 
                              arrowstyle='->', ax=ax)
        
        nx.draw_networkx_labels(G, node_positions, 
                               font_size=8, 
                               font_weight='bold', ax=ax)
        
        ax.set_title(f'{topology_type.title()} Network Topology')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
    
    def _plot_individual_distribution(self, ax, result, strategy, topology_type, n_nodes):
        """Plot individual distribution network"""
        
        topology = result['simulation']['topology']
        locations = topology['locations']
        routes = topology['routes']
        agent_distribution = result['simulation']['agent_distribution']
        s2_rate = result['simulation']['s2_rate']
        
        # Create network graph
        G = nx.DiGraph()
        
        # Add nodes with size based on agent distribution
        node_positions = {}
        node_colors = []
        node_sizes = []
        
        for loc in locations:
            name = loc['name']
            x, y = loc['x'], loc['y']
            
            G.add_node(name)
            node_positions[name] = (x, y)
            
            # Size based on agent distribution
            agent_count = agent_distribution.get(name, 0)
            base_size = 1000
            size_multiplier = 1 + (agent_count / 10)  # Scale with agent count
            node_sizes.append(base_size * size_multiplier)
            
            # Color by type
            if 'conflict' in name.lower():
                node_colors.append('red')
            elif 'town' in name.lower() or 'hub' in name.lower():
                node_colors.append('orange')
            elif 'camp' in name.lower():
                node_colors.append('green')
            else:
                node_colors.append('gray')
        
        # Add edges
        for route in routes:
            G.add_edge(route['from'], route['to'])
        
        # Draw network
        nx.draw_networkx_nodes(G, node_positions, 
                              node_color=node_colors, 
                              node_size=node_sizes, 
                              alpha=0.8, ax=ax)
        
        nx.draw_networkx_edges(G, node_positions, 
                              edge_color='gray', 
                              width=2, 
                              alpha=0.7, 
                              arrows=True, 
                              arrowsize=20, 
                              arrowstyle='->', ax=ax)
        
        # Add agent count labels
        for loc in locations:
            name = loc['name']
            agent_count = agent_distribution.get(name, 0)
            if agent_count > 0:
                x, y = loc['x'], loc['y']
                ax.annotate(f'{agent_count}', 
                           xy=(x, y),
                           ha='center', va='center',
                           fontsize=8, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.2', 
                                    facecolor='white', 
                                    alpha=0.9,
                                    edgecolor='black',
                                    linewidth=0.5))
        
        strategy_name = result['strategy_info']['name']
        ax.set_title(f'{strategy_name}\nS2 Rate: {s2_rate:.1%}')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
    
    def _plot_population_over_time(self, ax, result, strategy):
        """Plot population over time for a specific distribution"""
        
        daily_populations = result['flow_analysis']['daily_populations']
        
        # Plot population over time for each location
        for loc in daily_populations:
            if loc in daily_populations:
                times = list(daily_populations[loc].keys())
                populations = list(daily_populations[loc].values())
                ax.plot(times, populations, label=loc, linewidth=2, marker='o', markersize=3)
        
        strategy_name = result['strategy_info']['name']
        ax.set_xlabel('Time (Days)')
        ax.set_ylabel('Population')
        ax.set_title(f'{strategy_name} - Population Over Time')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    def _cleanup_agent_files(self):
        """Clean up agent tracking files"""
        agent_files = ['agents.out.0', 'links.out.0', 'simsetting.yml']
        for file in agent_files:
            if Path(file).exists():
                Path(file).unlink()
    
    def run_comprehensive_comparison(self):
        """Run comprehensive comparison across all topologies and distributions"""
        
        print("🌐 Comprehensive Initial Population Distribution Comparison")
        print("=" * 70)
        print("Comparing different initial population distribution strategies")
        print("=" * 70)
        
        topology_types = ['linear', 'star']
        node_sizes = [5, 7]
        
        for topology_type in topology_types:
            for n_nodes in node_sizes:
                print(f"\n📊 Comparing distributions for {topology_type} network ({n_nodes} nodes)")
                self.compare_distributions(topology_type, n_nodes)
        
        print("\n🎯 Comprehensive Comparison Complete!")
        print("📊 Analysis includes:")
        print("   - Single origin vs multiple origins")
        print("   - Population-weighted distribution")
        print("   - Conflict intensity-based distribution")
        print("   - Uniform distribution")
        print("   - S2 activation rate comparisons")
        print("   - Flow strength analysis")
        print("   - Population dynamics over time")

def main():
    """Main function to run population distribution comparison"""
    
    # Create comparator
    comparator = InitialPopulationDistributionComparator()
    
    # Run comprehensive comparison
    comparator.run_comprehensive_comparison()

if __name__ == "__main__":
    main()
