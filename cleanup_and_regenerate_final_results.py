#!/usr/bin/env python3
"""
Cleanup and Regenerate Final Results
- Clean up all old output folders
- Keep only the latest agent tracking flow graphs
- Fix linear network positioning issue
"""

import os
import shutil
import sys
from pathlib import Path

def cleanup_old_folders():
    """Remove all old output folders"""
    
    folders_to_remove = [
        "cognition_results",
        "corrected_flow_diagrams", 
        "detailed_flow_analysis",
        "final_network_flow_results",
        "initial_distribution_results",
        "network_flow_diagrams",
        "weighted_network_graphs",
        "agent_flow_graphs"  # Will be recreated
    ]
    
    print("🧹 Cleaning up old output folders...")
    
    for folder in folders_to_remove:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"   ✅ Removed: {folder}")
        else:
            print(f"   ⏭️  Not found: {folder}")
    
    # Remove old script files
    old_scripts = [
        "create_agent_tracking_flow_graphs.py",
        "create_corrected_flow_diagrams.py", 
        "create_detailed_flow_analysis.py",
        "create_network_flow_diagram.py",
        "create_weighted_network_graphs.py"
    ]
    
    for script in old_scripts:
        if Path(script).exists():
            Path(script).unlink()
            print(f"   ✅ Removed: {script}")

def create_final_agent_tracking_script():
    """Create the final agent tracking script with fixed linear positioning"""
    
    script_content = '''#!/usr/bin/env python3
"""
Final Agent Tracking Flow Graph Generator
- Uses Flee's built-in agent tracking for proper flow visualization
- Fixed linear network positioning
- Clean, organized output
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

class FinalAgentTrackingFlowGenerator:
    """Create flow graphs using Flee's built-in agent tracking"""
    
    def __init__(self, output_dir="final_agent_flow_graphs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def create_agent_tracking_simulation(self, topology_type="linear", n_nodes=5):
        """Create a simulation with agent tracking enabled"""
        
        print(f"📊 Creating {topology_type} network simulation with agent tracking...")
        
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
        
        # Import Flee components
        from flee.flee import Ecosystem, Person
        from flee.SimulationSettings import SimulationSettings
        from flee import moving, spawning
        from flee.moving import calculate_systematic_s2_activation
        
        # Setup Flee simulation
        SimulationSettings.ReadFromYML("simsetting.yml")
        ecosystem = Ecosystem()
        
        # Generate network topology
        topology = self._generate_network_topology(topology_type, n_nodes)
        
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
        num_agents = min(50, n_nodes * 5)
        origin_location = locations[topology['locations'][0]['name']]
        
        for i in range(num_agents):
            attributes = {"profile_type": np.random.choice(['analytical', 'balanced', 'reactive'])}
            ecosystem.addAgent(origin_location, attributes)
        
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
            's2_rate': s2_rate,
            'num_agents': num_agents,
            'simulation_days': simulation_days,
            's2_activations': s2_activations
        }
    
    def _generate_network_topology(self, topology_type, n_nodes):
        """Generate network topology with proper positioning"""
        
        if topology_type == 'linear':
            locations = []
            routes = []
            
            # FIXED: Better spacing for linear networks
            for i in range(n_nodes):
                if i == 0:
                    locations.append({
                        'name': f'Origin_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,  # Better spacing
                        'type': 'conflict', 'pop': 5000
                    })
                elif i < n_nodes // 2:
                    locations.append({
                        'name': f'Town_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,  # Better spacing
                        'type': 'town', 'pop': 1000
                    })
                else:
                    locations.append({
                        'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                        'x': float(i * 2), 'y': 0.0,  # Better spacing
                        'type': 'camp', 'pop': 2000
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
                'name': f'Origin_{topology_type}_{n_nodes}',
                'x': 0.0, 'y': 0.0,
                'type': 'conflict', 'pop': 5000
            })
            
            # Hub
            locations.append({
                'name': f'Hub_{topology_type}_{n_nodes}',
                'x': 3.0, 'y': 0.0,  # Better spacing
                'type': 'town', 'pop': 1000
            })
            
            # Camps in star pattern
            for i in range(2, n_nodes):
                angle = 2 * np.pi * (i - 2) / (n_nodes - 2)
                x = 6.0 * np.cos(angle)  # Better spacing
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
        
        elif topology_type == 'tree':
            locations = []
            routes = []
            
            # Origin
            locations.append({
                'name': f'Origin_{topology_type}_{n_nodes}',
                'x': 0.0, 'y': 0.0,
                'type': 'conflict', 'pop': 5000
            })
            
            # Create tree structure with better spacing
            current_level = 1
            nodes_per_level = 2
            level_y = 0
            
            while len(locations) < n_nodes:
                level_y += 3  # Better vertical spacing
                for i in range(nodes_per_level):
                    if len(locations) >= n_nodes:
                        break
                    
                    x = (i - nodes_per_level/2 + 0.5) * 3  # Better horizontal spacing
                    y = level_y
                    
                    if len(locations) < n_nodes // 2:
                        locations.append({
                            'name': f'Town_{len(locations)}_{topology_type}_{n_nodes}',
                            'x': x, 'y': y,
                            'type': 'town', 'pop': 1000
                        })
                    else:
                        locations.append({
                            'name': f'Camp_{len(locations)}_{topology_type}_{n_nodes}',
                            'x': x, 'y': y,
                            'type': 'camp', 'pop': 2000
                        })
                
                nodes_per_level *= 2
            
            # Create tree connections
            for i in range(1, len(locations)):
                parent_idx = (i - 1) // 2
                routes.append({
                    'from': locations[parent_idx]['name'],
                    'to': locations[i]['name'],
                    'distance': 100.0
                })
        
        elif topology_type == 'grid':
            locations = []
            routes = []
            
            # Create square grid with better spacing
            grid_size = int(np.ceil(np.sqrt(n_nodes)))
            
            for i in range(n_nodes):
                row = i // grid_size
                col = i % grid_size
                
                if i == 0:
                    locations.append({
                        'name': f'Origin_{topology_type}_{n_nodes}',
                        'x': float(col * 2), 'y': float(row * 2),  # Better spacing
                        'type': 'conflict', 'pop': 5000
                    })
                elif i < n_nodes // 2:
                    locations.append({
                        'name': f'Town_{i}_{topology_type}_{n_nodes}',
                        'x': float(col * 2), 'y': float(row * 2),  # Better spacing
                        'type': 'town', 'pop': 1000
                    })
                else:
                    locations.append({
                        'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                        'x': float(col * 2), 'y': float(row * 2),  # Better spacing
                        'type': 'camp', 'pop': 2000
                    })
            
            # Create grid connections
            for i in range(n_nodes):
                row = i // grid_size
                col = i % grid_size
                
                # Right neighbor
                if col < grid_size - 1 and i + 1 < n_nodes:
                    routes.append({
                        'from': locations[i]['name'],
                        'to': locations[i + 1]['name'],
                        'distance': 100.0
                    })
                
                # Bottom neighbor
                if row < grid_size - 1 and i + grid_size < n_nodes:
                    routes.append({
                        'from': locations[i]['name'],
                        'to': locations[i + grid_size]['name'],
                        'distance': 100.0
                    })
        
        return {
            'name': f'{topology_type.title()} Network (n={n_nodes})',
            'locations': locations,
            'routes': routes
        }
    
    def analyze_agent_tracking_data(self, topology_type="linear", n_nodes=5):
        """Analyze agent tracking data to create flow visualizations"""
        
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
        flow_analysis = self._analyze_flow_patterns(df, topology_type, n_nodes)
        
        return flow_analysis
    
    def _analyze_flow_patterns(self, df, topology_type, n_nodes):
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
    
    def create_flow_visualization(self, topology_type="linear", n_nodes=5):
        """Create complete flow visualization with agent tracking"""
        
        print(f"🌐 Creating flow visualization for {topology_type} network ({n_nodes} nodes)")
        
        # Run simulation with agent tracking
        simulation_result = self.create_agent_tracking_simulation(topology_type, n_nodes)
        
        # Analyze agent tracking data
        flow_analysis = self.analyze_agent_tracking_data(topology_type, n_nodes)
        
        if flow_analysis is None:
            print("❌ Could not analyze agent tracking data")
            return
        
        # Create visualization
        self._plot_agent_flow_graph(simulation_result, flow_analysis, topology_type, n_nodes)
        
        # Clean up agent tracking files
        self._cleanup_agent_files()
    
    def _plot_agent_flow_graph(self, simulation_result, flow_analysis, topology_type, n_nodes):
        """Plot agent flow graph using tracking data"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        fig.suptitle(f'{topology_type.title()} Network Flow Analysis (n={n_nodes}) - Agent Tracking Data', 
                    fontsize=16, fontweight='bold')
        
        # Plot 1: Network topology with flows
        self._plot_network_topology(ax1, simulation_result, flow_analysis)
        
        # Plot 2: Flow over time
        self._plot_flow_over_time(ax2, flow_analysis)
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.output_dir / f"{topology_type}_agent_flow_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.savefig(output_file.with_suffix('.pdf'), bbox_inches='tight')
        
        print(f"✅ Agent flow analysis saved: {output_file}")
    
    def _plot_network_topology(self, ax, simulation_result, flow_analysis):
        """Plot network topology with flow data"""
        
        topology = simulation_result['topology']
        locations = topology['locations']
        routes = topology['routes']
        s2_rate = simulation_result['s2_rate']
        
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
            if 'origin' in name.lower() or 'conflict' in name.lower():
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
        
        # Add edges with flow data
        edge_colors = []
        edge_widths = []
        
        for route in routes:
            from_loc = route['from']
            to_loc = route['to']
            G.add_edge(from_loc, to_loc)
            
            # Get flow strength from analysis
            flow_strength = flow_analysis['avg_flows'].get(to_loc, 0)
            
            # Edge properties based on flow
            if flow_strength > 5:
                edge_colors.append('purple')
                edge_widths.append(6)
            elif flow_strength > 2:
                edge_colors.append('blue')
                edge_widths.append(4)
            elif flow_strength > 0.5:
                edge_colors.append('lightblue')
                edge_widths.append(3)
            else:
                edge_colors.append('lightgray')
                edge_widths.append(2)
        
        # Draw network
        nx.draw_networkx_nodes(G, node_positions, 
                              node_color=node_colors, 
                              node_size=node_sizes, 
                              alpha=0.8, ax=ax)
        
        # Draw edges
        for i, (u, v, data) in enumerate(G.edges(data=True)):
            nx.draw_networkx_edges(G, node_positions, 
                                  edgelist=[(u, v)], 
                                  edge_color=edge_colors[i], 
                                  width=edge_widths[i], 
                                  alpha=0.7, 
                                  arrows=True, 
                                  arrowsize=20, 
                                  arrowstyle='->', ax=ax)
        
        # Add labels
        nx.draw_networkx_labels(G, node_positions, 
                               font_size=8, 
                               font_weight='bold', ax=ax)
        
        # Add flow labels
        for i, (u, v, data) in enumerate(G.edges(data=True)):
            start_pos = node_positions[u]
            end_pos = node_positions[v]
            mid_x = (start_pos[0] + end_pos[0]) / 2
            mid_y = (start_pos[1] + end_pos[1]) / 2
            
            flow_strength = flow_analysis['avg_flows'].get(v, 0)
            if flow_strength > 0.5:
                ax.annotate(f'{flow_strength:.1f}', 
                           xy=(mid_x, mid_y),
                           ha='center', va='center',
                           fontsize=9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.2', 
                                    facecolor='white', 
                                    alpha=0.9,
                                    edgecolor='black',
                                    linewidth=0.5))
        
        ax.set_title(f'Network Topology\\nS2 Rate: {s2_rate:.1%}', fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
    
    def _plot_flow_over_time(self, ax, flow_analysis):
        """Plot flow over time"""
        
        daily_populations = flow_analysis['daily_populations']
        
        # Plot population over time for each location
        for loc in daily_populations:
            if loc in daily_populations:
                times = list(daily_populations[loc].keys())
                populations = list(daily_populations[loc].values())
                ax.plot(times, populations, label=loc, linewidth=2, marker='o', markersize=4)
        
        ax.set_xlabel('Time (Days)')
        ax.set_ylabel('Population')
        ax.set_title('Population Over Time (Agent Tracking)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
    
    def _cleanup_agent_files(self):
        """Clean up agent tracking files"""
        agent_files = ['agents.out.0', 'links.out.0', 'simsetting.yml']
        for file in agent_files:
            if Path(file).exists():
                Path(file).unlink()
    
    def create_all_topology_flows(self):
        """Create flow visualizations for all topology types"""
        
        topology_types = ['linear', 'star', 'tree', 'grid']
        node_sizes = [5, 7, 11]
        
        for topology_type in topology_types:
            for n_nodes in node_sizes:
                print(f"\\n📊 Creating {topology_type} network ({n_nodes} nodes)")
                self.create_flow_visualization(topology_type, n_nodes)

def main():
    """Main function to generate final agent tracking flow graphs"""
    
    print("🌐 Final Agent Tracking Flow Graph Generator")
    print("=" * 60)
    print("Using Flee's built-in agent tracking with improved positioning")
    print("=" * 60)
    
    # Create generator
    generator = FinalAgentTrackingFlowGenerator()
    
    # Create flow visualizations for all topologies
    generator.create_all_topology_flows()
    
    print("\\n🎯 Final Agent Tracking Flow Graphs Complete!")
    print("📊 Features:")
    print("   - Real agent movement data from Flee")
    print("   - Fixed linear network positioning")
    print("   - Proper flow calculations")
    print("   - Network topology with actual positioning")
    print("   - Population over time tracking")

if __name__ == "__main__":
    main()
'''
    
    with open("final_agent_tracking_flow_generator.py", "w") as f:
        f.write(script_content)
    
    print("✅ Created: final_agent_tracking_flow_generator.py")

def main():
    """Main cleanup and regeneration function"""
    
    print("🧹 Cleanup and Regenerate Final Results")
    print("=" * 60)
    
    # Step 1: Clean up old folders
    cleanup_old_folders()
    
    # Step 2: Create final script
    create_final_agent_tracking_script()
    
    print("\n🎯 Cleanup Complete!")
    print("📁 Only one output folder will be created: final_agent_flow_graphs")
    print("🔧 Fixed linear network positioning issue")
    print("📊 Ready to generate final results")

if __name__ == "__main__":
    main()

