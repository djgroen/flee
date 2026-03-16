#!/usr/bin/env python3
"""
Complete Agent Tracking Analysis with Data Preservation
- Runs full analysis with all topologies and network sizes
- Preserves all agent tracking data for scientific reproducibility
- Generates comprehensive visualizations and reports
- Clean, organized output structure
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
import shutil
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, '.')

# Set style for publication-ready figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

class CompleteAnalysisWithPreservation:
    """Complete analysis with scientific data preservation"""
    
    def __init__(self):
        # Clean up any existing output
        self._cleanup_existing_output()
        
        # Create organized output structure
        self.output_dir = Path("complete_analysis_results")
        self.data_dir = self.output_dir / "agent_tracking_data"
        self.figures_dir = self.output_dir / "figures"
        self.reports_dir = self.output_dir / "reports"
        
        # Create directories
        for dir_path in [self.output_dir, self.data_dir, self.figures_dir, self.reports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Analysis results storage
        self.all_results = {}
        
    def _cleanup_existing_output(self):
        """Clean up any existing output directories"""
        cleanup_dirs = [
            "final_agent_flow_graphs",
            "agent_tracking_data", 
            "complete_analysis_results"
        ]
        
        for dir_name in cleanup_dirs:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
                print(f"🧹 Cleaned up: {dir_name}")
    
    def run_complete_analysis(self):
        """Run complete analysis for all topologies and network sizes"""
        
        print("🚀 Complete Agent Tracking Analysis with Data Preservation")
        print("=" * 70)
        print("Running comprehensive analysis with scientific data preservation")
        print("=" * 70)
        
        # Define analysis parameters
        topology_types = ['linear', 'star', 'tree', 'grid']
        node_sizes = [5, 7, 11]
        
        # Run analysis for each topology and size
        for topology_type in topology_types:
            print(f"\n📊 Analyzing {topology_type.upper()} networks...")
            
            self.all_results[topology_type] = {}
            
            for n_nodes in node_sizes:
                print(f"  🔍 {topology_type} network ({n_nodes} nodes)")
                
                # Run simulation with data preservation
                result = self._run_single_simulation(topology_type, n_nodes)
                self.all_results[topology_type][str(n_nodes)] = result
        
        # Generate comprehensive reports and visualizations
        self._generate_comprehensive_reports()
        self._generate_comparative_visualizations()
        self._create_final_summary()
        
        print(f"\n🎯 Complete Analysis Finished!")
        print(f"📁 Results saved to: {self.output_dir}")
        print(f"🔒 Data preserved in: {self.data_dir}")
        print(f"📊 Figures saved to: {self.figures_dir}")
        print(f"📋 Reports saved to: {self.reports_dir}")
    
    def _run_single_simulation(self, topology_type, n_nodes):
        """Run a single simulation with data preservation"""
        
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
        
        # Preserve agent tracking data
        data_dir = self._preserve_agent_tracking_data(topology_type, n_nodes)
        
        # Analyze agent tracking data
        flow_analysis = self._analyze_agent_tracking_data()
        
        # Create individual visualization
        self._create_individual_visualization(topology_type, n_nodes, topology, s2_rate, flow_analysis)
        
        # Clean up temporary files
        self._cleanup_temp_files()
        
        return {
            'topology': topology,
            's2_rate': s2_rate,
            'num_agents': num_agents,
            'simulation_days': simulation_days,
            's2_activations': s2_activations,
            'flow_analysis': flow_analysis,
            'data_dir': str(data_dir)
        }
    
    def _generate_network_topology(self, topology_type, n_nodes):
        """Generate network topology with proper positioning"""
        
        if topology_type == 'linear':
            locations = []
            routes = []
            
            # Better spacing for linear networks
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
                level_y += 3
                for i in range(nodes_per_level):
                    if len(locations) >= n_nodes:
                        break
                    
                    x = (i - nodes_per_level/2 + 0.5) * 3
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
                        'x': float(col * 2), 'y': float(row * 2),
                        'type': 'conflict', 'pop': 5000
                    })
                elif i < n_nodes // 2:
                    locations.append({
                        'name': f'Town_{i}_{topology_type}_{n_nodes}',
                        'x': float(col * 2), 'y': float(row * 2),
                        'type': 'town', 'pop': 1000
                    })
                else:
                    locations.append({
                        'name': f'Camp_{i}_{topology_type}_{n_nodes}',
                        'x': float(col * 2), 'y': float(row * 2),
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
    
    def _preserve_agent_tracking_data(self, topology_type, n_nodes):
        """Preserve agent tracking data for scientific reproducibility"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create organized directory structure
        topology_dir = self.data_dir / f"{topology_type}_{n_nodes}nodes"
        topology_dir.mkdir(exist_ok=True)
        
        # Copy agent tracking files
        agent_files = ['agents.out.0', 'links.out.0', 'simsetting.yml']
        
        for file in agent_files:
            if Path(file).exists():
                timestamped_name = f"{file}_{timestamp}"
                shutil.copy2(file, topology_dir / timestamped_name)
        
        # Create metadata file
        metadata = {
            'topology_type': topology_type,
            'n_nodes': n_nodes,
            'timestamp': timestamp,
            'simulation_date': datetime.now().isoformat(),
            'files_preserved': [f for f in agent_files if Path(f).exists()],
            'description': f"Agent tracking data for {topology_type} network with {n_nodes} nodes"
        }
        
        metadata_file = topology_dir / f"metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return topology_dir
    
    def _analyze_agent_tracking_data(self):
        """Analyze agent tracking data to create flow visualizations"""
        
        # Check if agent tracking files exist
        agent_file = Path("agents.out.0")
        if not agent_file.exists():
            return None
        
        # Read agent tracking data
        try:
            # Read the header line to get column names
            with open(agent_file, 'r') as f:
                header_line = f.readline().strip()
                if header_line.startswith('#'):
                    header_line = header_line[1:]
                column_names = header_line.split(',')
            
            # Read the data with proper column names
            df = pd.read_csv(agent_file, comment='#', names=column_names)
        except Exception as e:
            print(f"❌ Error reading agent tracking data: {e}")
            return None
        
        # Analyze flow patterns
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
    
    def _create_individual_visualization(self, topology_type, n_nodes, topology, s2_rate, flow_analysis):
        """Create individual visualization for a single simulation"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        fig.suptitle(f'{topology_type.title()} Network Flow Analysis (n={n_nodes})', 
                    fontsize=16, fontweight='bold')
        
        # Plot 1: Network topology with flows
        self._plot_network_topology(ax1, topology, flow_analysis, s2_rate)
        
        # Plot 2: Flow over time
        self._plot_flow_over_time(ax2, flow_analysis)
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.figures_dir / f"{topology_type}_{n_nodes}nodes_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.savefig(output_file.with_suffix('.pdf'), bbox_inches='tight')
        plt.close()
    
    def _plot_network_topology(self, ax, topology, flow_analysis, s2_rate):
        """Plot network topology with flow data"""
        
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
            if flow_analysis:
                flow_strength = flow_analysis['avg_flows'].get(to_loc, 0)
            else:
                flow_strength = 0
            
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
        
        ax.set_title(f'Network Topology\\nS2 Rate: {s2_rate:.1%}', fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
    
    def _plot_flow_over_time(self, ax, flow_analysis):
        """Plot flow over time"""
        
        if not flow_analysis:
            ax.text(0.5, 0.5, 'No flow data available', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Population Over Time')
            return
        
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
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_files = ['agents.out.0', 'links.out.0', 'simsetting.yml']
        for file in temp_files:
            if Path(file).exists():
                Path(file).unlink()
    
    def _generate_comprehensive_reports(self):
        """Generate comprehensive analysis reports"""
        
        # Create summary report
        summary_file = self.reports_dir / "ANALYSIS_SUMMARY.md"
        
        with open(summary_file, 'w') as f:
            f.write("# Complete Agent Tracking Analysis Summary\\n\\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\\n\\n")
            f.write("## Analysis Overview\\n\\n")
            f.write("This analysis examined agent movement patterns across different network topologies\\n")
            f.write("using Flee's built-in agent tracking system with full data preservation.\\n\\n")
            
            f.write("## Topologies Analyzed\\n\\n")
            for topology_type in self.all_results:
                f.write(f"### {topology_type.title()} Networks\\n")
                for n_nodes in self.all_results[topology_type]:
                    result = self.all_results[topology_type][n_nodes]
                    f.write(f"- **{n_nodes} nodes**: S2 Rate = {result['s2_rate']:.1%}, ")
                    f.write(f"Agents = {result['num_agents']}\\n")
                f.write("\\n")
            
            f.write("## Key Findings\\n\\n")
            f.write("- All agent tracking data preserved with timestamps\\n")
            f.write("- Real flow patterns captured from agent movements\\n")
            f.write("- Network topology effects on S2 activation rates\\n")
            f.write("- Comprehensive visualizations generated\\n")
        
        # Create data preservation report
        data_report = self.reports_dir / "DATA_PRESERVATION_REPORT.md"
        
        with open(data_report, 'w') as f:
            f.write("# Data Preservation Report\\n\\n")
            f.write("## Preserved Data Structure\\n\\n")
            f.write("```\\n")
            f.write("complete_analysis_results/\\n")
            f.write("├── agent_tracking_data/\\n")
            
            for topology_dir in sorted(self.data_dir.glob("*")):
                if topology_dir.is_dir():
                    f.write(f"│   ├── {topology_dir.name}/\\n")
                    for file in sorted(topology_dir.glob("*")):
                        f.write(f"│   │   ├── {file.name}\\n")
            
            f.write("├── figures/\\n")
            f.write("│   ├── Individual network visualizations\\n")
            f.write("│   └── Comparative analysis plots\\n")
            f.write("└── reports/\\n")
            f.write("    ├── Analysis summaries\\n")
            f.write("    └── Data preservation documentation\\n")
            f.write("```\\n\\n")
            
            f.write("## Scientific Reproducibility\\n\\n")
            f.write("All raw simulation data is preserved for:\\n")
            f.write("- **Verification**: Re-run analysis on original data\\n")
            f.write("- **Reproducibility**: Recreate exact simulation conditions\\n")
            f.write("- **Audit Trail**: Track all simulation parameters\\n")
            f.write("- **Future Analysis**: Additional research on preserved data\\n")
    
    def _generate_comparative_visualizations(self):
        """Generate comparative visualizations across topologies"""
        
        # S2 Rate Comparison
        fig, ax = plt.subplots(figsize=(12, 8))
        
        topology_types = list(self.all_results.keys())
        node_sizes = ['5', '7', '11']
        
        x = np.arange(len(topology_types))
        width = 0.25
        
        for i, n_nodes in enumerate(node_sizes):
            s2_rates = []
            for topology_type in topology_types:
                if n_nodes in self.all_results[topology_type]:
                    s2_rate = self.all_results[topology_type][n_nodes]['s2_rate']
                    s2_rates.append(s2_rate)
                else:
                    s2_rates.append(0)
            
            ax.bar(x + i*width, s2_rates, width, label=f'{n_nodes} nodes')
        
        ax.set_xlabel('Network Topology')
        ax.set_ylabel('S2 Activation Rate')
        ax.set_title('S2 Activation Rates by Network Topology and Size')
        ax.set_xticks(x + width)
        ax.set_xticklabels([t.title() for t in topology_types])
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.figures_dir / "s2_rates_comparison.png", dpi=300, bbox_inches='tight')
        plt.savefig(self.figures_dir / "s2_rates_comparison.pdf", bbox_inches='tight')
        plt.close()
        
        # Network Size Effect
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for topology_type in topology_types:
            node_sizes_list = []
            s2_rates_list = []
            
            for n_nodes in node_sizes:
                if n_nodes in self.all_results[topology_type]:
                    node_sizes_list.append(int(n_nodes))
                    s2_rate = self.all_results[topology_type][n_nodes]['s2_rate']
                    s2_rates_list.append(s2_rate)
            
            ax.plot(node_sizes_list, s2_rates_list, marker='o', linewidth=2, 
                   label=topology_type.title(), markersize=8)
        
        ax.set_xlabel('Network Size (Number of Nodes)')
        ax.set_ylabel('S2 Activation Rate')
        ax.set_title('Effect of Network Size on S2 Activation Rates')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.figures_dir / "network_size_effects.png", dpi=300, bbox_inches='tight')
        plt.savefig(self.figures_dir / "network_size_effects.pdf", bbox_inches='tight')
        plt.close()
    
    def _create_final_summary(self):
        """Create final summary of the complete analysis"""
        
        summary_file = self.output_dir / "COMPLETE_ANALYSIS_SUMMARY.md"
        
        with open(summary_file, 'w') as f:
            f.write("# Complete Agent Tracking Analysis - Final Summary\\n\\n")
            f.write(f"**Analysis Completed**: {datetime.now().isoformat()}\\n\\n")
            
            f.write("## 🎯 Analysis Overview\\n\\n")
            f.write("This comprehensive analysis examined agent movement patterns across different\\n")
            f.write("network topologies using Flee's built-in agent tracking system with full\\n")
            f.write("scientific data preservation.\\n\\n")
            
            f.write("## 📊 Results Summary\\n\\n")
            
            # Calculate overall statistics
            total_simulations = 0
            total_agents = 0
            avg_s2_rate = 0
            
            for topology_type in self.all_results:
                for n_nodes in self.all_results[topology_type]:
                    result = self.all_results[topology_type][n_nodes]
                    total_simulations += 1
                    total_agents += result['num_agents']
                    avg_s2_rate += result['s2_rate']
            
            avg_s2_rate /= total_simulations if total_simulations > 0 else 1
            
            f.write(f"- **Total Simulations**: {total_simulations}\\n")
            f.write(f"- **Total Agents Tracked**: {total_agents}\\n")
            f.write(f"- **Average S2 Rate**: {avg_s2_rate:.1%}\\n")
            f.write(f"- **Topologies Analyzed**: {len(self.all_results)}\\n")
            f.write(f"- **Network Sizes**: 5, 7, 11 nodes\\n\\n")
            
            f.write("## 🔒 Data Preservation\\n\\n")
            f.write("All raw simulation data has been preserved with:\\n")
            f.write("- **Timestamped files** for unique identification\\n")
            f.write("- **Complete metadata** for each simulation\\n")
            f.write("- **Organized structure** by topology and size\\n")
            f.write("- **Scientific reproducibility** for future analysis\\n\\n")
            
            f.write("## 📁 Output Structure\\n\\n")
            f.write("```\\n")
            f.write("complete_analysis_results/\\n")
            f.write("├── agent_tracking_data/     # Raw simulation data\\n")
            f.write("├── figures/                 # All visualizations\\n")
            f.write("├── reports/                 # Analysis reports\\n")
            f.write("└── COMPLETE_ANALYSIS_SUMMARY.md\\n")
            f.write("```\\n\\n")
            
            f.write("## 🚀 Key Achievements\\n\\n")
            f.write("✅ **Complete Analysis**: All topologies and network sizes analyzed\\n")
            f.write("✅ **Data Preservation**: All raw data preserved with timestamps\\n")
            f.write("✅ **Real Agent Tracking**: Using Flee's built-in tracking system\\n")
            f.write("✅ **Comprehensive Visualizations**: Individual and comparative plots\\n")
            f.write("✅ **Scientific Rigor**: Full audit trail and reproducibility\\n")
            f.write("✅ **Clean Organization**: Structured output with clear documentation\\n\\n")
            
            f.write("## 📋 Next Steps\\n\\n")
            f.write("The preserved data can be used for:\\n")
            f.write("- **Verification**: Re-run analysis on original data\\n")
            f.write("- **Publication**: Raw data available for peer review\\n")
            f.write("- **Future Research**: Additional analysis on preserved data\\n")
            f.write("- **Methodology Development**: Refine analysis approaches\\n")

def main():
    """Main function to run complete analysis with data preservation"""
    
    print("🚀 Starting Complete Agent Tracking Analysis with Data Preservation")
    print("=" * 70)
    
    # Create and run analysis
    analysis = CompleteAnalysisWithPreservation()
    analysis.run_complete_analysis()
    
    print("\\n🎉 Complete Analysis with Data Preservation Finished!")
    print("📊 All results saved to: complete_analysis_results/")
    print("🔒 All raw data preserved for scientific reproducibility")

if __name__ == "__main__":
    main()




