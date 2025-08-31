#!/usr/bin/env python3
"""
Standard S1/S2 Refugee Simulation Diagnostic Suite

Universal visualization framework that produces standardized diagnostic output
for any S1/S2 refugee simulation, regardless of specific hypothesis being tested.

Provides:
1. Scenario Context (topology, forcing functions, metadata)
2. Agent Dynamics (flows, cognitive patterns, trajectories)
3. System Performance (efficiency, quality, cognitive load)
4. Comparative Analysis (S1 vs S2, hypothesis-specific metrics)
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import json
from datetime import datetime

# Set up plotting style for publication quality
plt.style.use('default')
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

class S1S2DiagnosticSuite:
    """Universal diagnostic visualization suite for S1/S2 refugee simulations"""
    
    def __init__(self, output_dir: str = "s1s2_diagnostics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Standard color scheme
        self.colors = {
            's1': '#FF6B6B',      # Red for S1 (heuristic)
            's2': '#4ECDC4',      # Teal for S2 (analytical)
            'conflict': '#FF4444', # Bright red for conflict
            'safe': '#44FF44',     # Green for safety
            'neutral': '#CCCCCC',  # Gray for neutral
            'capacity': '#FFB347', # Orange for capacity
            'flow': '#87CEEB'      # Sky blue for flows
        }
    
    def generate_full_diagnostic(self, simulation_data: Dict[str, Any], 
                               scenario_name: str = "S1S2_Simulation") -> bool:
        """
        Generate complete standardized diagnostic suite for any S1/S2 simulation
        
        Args:
            simulation_data: Dictionary containing all simulation results
            scenario_name: Name for this simulation run
            
        Returns:
            bool: Success status
        """
        try:
            print(f"🔍 GENERATING STANDARD S1/S2 DIAGNOSTIC SUITE: {scenario_name}")
            print("=" * 70)
            
            # Extract and analyze simulation data
            analysis = self._analyze_simulation_data(simulation_data)
            
            # Generate the four standard diagnostic panels
            print("📊 Panel 1: Scenario Context Analysis...")
            self._create_scenario_context_panel(analysis, scenario_name)
            
            print("🌊 Panel 2: Agent Dynamics Analysis...")
            self._create_agent_dynamics_panel(analysis, scenario_name)
            
            print("⚡ Panel 3: System Performance Analysis...")
            self._create_system_performance_panel(analysis, scenario_name)
            
            print("🔬 Panel 4: Comparative Analysis...")
            self._create_comparative_analysis_panel(analysis, scenario_name)
            
            # Generate summary report
            print("📋 Generating Summary Report...")
            self._create_summary_report(analysis, scenario_name)
            
            print(f"\n✅ Complete diagnostic suite saved to {self.output_dir}/")
            return True
            
        except Exception as e:
            print(f"❌ Diagnostic generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False 
   
    def _analyze_simulation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and analyze key patterns from simulation data"""
        analysis = {
            'metadata': self._extract_metadata(data),
            'topology': self._analyze_topology(data),
            'forcing_functions': self._analyze_forcing_functions(data),
            'agent_patterns': self._analyze_agent_patterns(data),
            'cognitive_patterns': self._analyze_cognitive_patterns(data),
            'performance_metrics': self._calculate_performance_metrics(data)
        }
        return analysis
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic simulation metadata"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_agents': len(data.get('agents', [])),
            'simulation_duration': data.get('max_time', 0),
            'locations_count': len(data.get('locations', [])),
            'links_count': len(data.get('links', [])),
            'scenario_type': self._detect_scenario_type(data)
        }
    
    def _detect_scenario_type(self, data: Dict[str, Any]) -> str:
        """Auto-detect the type of scenario based on topology and dynamics"""
        locations = data.get('locations', [])
        links = data.get('links', [])
        
        if len(locations) <= 3 and len(links) <= 2:
            return "Linear Chain"
        elif len(locations) == 4 and len(links) >= 4:
            return "Diamond/Bottleneck"
        elif len(locations) >= 4 and len(links) == len(locations):
            return "Star/Hub-Spoke"
        elif len(locations) >= 5:
            return "Complex Network"
        else:
            return "Custom Topology"
    
    def _analyze_topology(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network topology structure"""
        locations = data.get('locations', [])
        links = data.get('links', [])
        
        # Create NetworkX graph for analysis
        G = nx.Graph()
        for loc in locations:
            G.add_node(loc['name'], **loc)
        for link in links:
            G.add_edge(link['from'], link['to'], distance=link.get('distance', 1))
        
        return {
            'graph': G,
            'node_positions': {loc['name']: (loc.get('x', 0), loc.get('y', 0)) for loc in locations},
            'centrality': nx.degree_centrality(G),
            'clustering': nx.clustering(G),
            'diameter': nx.diameter(G) if nx.is_connected(G) else float('inf'),
            'density': nx.density(G)
        }
    
    def _analyze_forcing_functions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temporal forcing functions (conflict, capacity changes, etc.)"""
        time_series = data.get('time_series', {})
        
        forcing = {
            'conflict_evolution': time_series.get('conflict_levels', {}),
            'capacity_changes': time_series.get('capacity_changes', {}),
            'population_changes': time_series.get('population_changes', {}),
            'forcing_type': self._classify_forcing_type(time_series)
        }
        
        return forcing
    
    def _classify_forcing_type(self, time_series: Dict[str, Any]) -> str:
        """Classify the type of temporal forcing"""
        conflict_data = time_series.get('conflict_levels', {})
        capacity_data = time_series.get('capacity_changes', {})
        
        if conflict_data:
            # Analyze conflict pattern
            values = list(conflict_data.values())
            if len(values) > 1:
                if all(v >= values[i-1] for i, v in enumerate(values[1:])):
                    return "Gradual Escalation"
                elif any(abs(values[i] - values[i-1]) > 0.3 for i in range(1, len(values))):
                    return "Shock/Step Change"
                else:
                    return "Oscillating"
        
        if capacity_data:
            return "Capacity Constraint"
        
        return "Static Scenario"   
 
    def _analyze_agent_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent movement and decision patterns"""
        agents = data.get('agents', [])
        movements = data.get('movements', [])
        
        return {
            'total_movements': len(movements),
            'movement_by_time': self._group_movements_by_time(movements),
            'movement_by_location': self._group_movements_by_location(movements),
            'agent_trajectories': self._extract_agent_trajectories(movements),
            'evacuation_timing': self._analyze_evacuation_timing(movements)
        }
    
    def _analyze_cognitive_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze S1/S2 cognitive activation patterns"""
        decisions = data.get('decisions', [])
        
        s1_decisions = [d for d in decisions if not d.get('system2_active', False)]
        s2_decisions = [d for d in decisions if d.get('system2_active', False)]
        
        return {
            's1_count': len(s1_decisions),
            's2_count': len(s2_decisions),
            's2_activation_rate': len(s2_decisions) / len(decisions) if decisions else 0,
            'activation_by_time': self._group_activation_by_time(decisions),
            'activation_by_connectivity': self._group_activation_by_connectivity(decisions),
            'cognitive_pressure_evolution': self._analyze_cognitive_pressure(decisions)
        }
    
    def _calculate_performance_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate standardized performance metrics"""
        movements = data.get('movements', [])
        decisions = data.get('decisions', [])
        
        s1_movements = [m for m in movements if not m.get('system2_active', False)]
        s2_movements = [m for m in movements if m.get('system2_active', False)]
        
        return {
            'evacuation_efficiency': {
                's1_avg_time': np.mean([m.get('time', 0) for m in s1_movements]) if s1_movements else 0,
                's2_avg_time': np.mean([m.get('time', 0) for m in s2_movements]) if s2_movements else 0
            },
            'route_efficiency': {
                's1_avg_distance': np.mean([m.get('distance', 0) for m in s1_movements]) if s1_movements else 0,
                's2_avg_distance': np.mean([m.get('distance', 0) for m in s2_movements]) if s2_movements else 0
            },
            'safety_outcomes': {
                's1_avg_safety': np.mean([m.get('safety_score', 0) for m in s1_movements]) if s1_movements else 0,
                's2_avg_safety': np.mean([m.get('safety_score', 0) for m in s2_movements]) if s2_movements else 0
            }
        }
    
    def _create_scenario_context_panel(self, analysis: Dict[str, Any], scenario_name: str):
        """Create Panel 1: Scenario Context visualization"""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle(f'Panel 1: Scenario Context - {scenario_name}', 
                     fontsize=16, fontweight='bold')
        
        # Subplot 1: Network Topology Map
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_network_topology(ax1, analysis['topology'])
        
        # Subplot 2: Scenario Metadata
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_scenario_metadata(ax2, analysis['metadata'])
        
        # Subplot 3: Forcing Functions Time Series
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_forcing_functions(ax3, analysis['forcing_functions'])
        
        plt.savefig(self.output_dir / f'{scenario_name}_panel1_scenario_context.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Panel 1: Scenario Context saved")
    
    def _plot_network_topology(self, ax, topology_data: Dict[str, Any]):
        """Plot network topology with spatial layout"""
        G = topology_data['graph']
        pos = topology_data['node_positions']
        
        # Draw network
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=self.colors['neutral'], 
                              node_size=800, alpha=0.8)
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray', width=2, alpha=0.6)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight='bold')
        
        # Color nodes by conflict level if available
        for node, (x, y) in pos.items():
            node_data = G.nodes[node]
            conflict = node_data.get('conflict', 0)
            if conflict > 0.5:
                ax.scatter(x, y, c=self.colors['conflict'], s=1000, alpha=0.3, marker='o')
            elif conflict < 0.2:
                ax.scatter(x, y, c=self.colors['safe'], s=1000, alpha=0.3, marker='o')
        
        ax.set_title('Network Topology & Conflict Zones', fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
    
    def _plot_scenario_metadata(self, ax, metadata: Dict[str, Any]):
        """Plot scenario metadata as text summary"""
        ax.axis('off')
        
        metadata_text = f"""
SCENARIO METADATA
─────────────────
Type: {metadata['scenario_type']}
Agents: {metadata['total_agents']}
Duration: {metadata['simulation_duration']} days
Locations: {metadata['locations_count']}
Links: {metadata['links_count']}
Generated: {metadata['timestamp'][:19]}
        """
        
        ax.text(0.05, 0.95, metadata_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.5))
    
    def _plot_forcing_functions(self, ax, forcing_data: Dict[str, Any]):
        """Plot temporal forcing functions"""
        ax.set_title('Forcing Functions Over Time', fontweight='bold')
        
        # Plot conflict evolution
        conflict_data = forcing_data.get('conflict_evolution', {})
        if conflict_data:
            times = list(conflict_data.keys())
            values = list(conflict_data.values())
            ax.plot(times, values, 'o-', color=self.colors['conflict'], 
                   linewidth=2, label='Conflict Level', markersize=4)
        
        # Plot capacity changes
        capacity_data = forcing_data.get('capacity_changes', {})
        if capacity_data:
            times = list(capacity_data.keys())
            values = list(capacity_data.values())
            ax2 = ax.twinx()
            ax2.plot(times, values, 's-', color=self.colors['capacity'], 
                    linewidth=2, label='Capacity Changes', markersize=4)
            ax2.set_ylabel('Capacity', color=self.colors['capacity'])
        
        ax.set_xlabel('Time (Days)')
        ax.set_ylabel('Conflict Level', color=self.colors['conflict'])
        ax.grid(True, alpha=0.3)
        
        # Add forcing type annotation
        forcing_type = forcing_data.get('forcing_type', 'Unknown')
        ax.text(0.02, 0.98, f'Forcing Type: {forcing_type}', 
               transform=ax.transAxes, fontsize=10, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))
        
        if conflict_data or capacity_data:
            ax.legend(loc='upper left')
    
    def _create_agent_dynamics_panel(self, analysis: Dict[str, Any], scenario_name: str):
        """Create Panel 2: Agent Dynamics visualization"""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle(f'Panel 2: Agent Dynamics - {scenario_name}', 
                     fontsize=16, fontweight='bold')
        
        # Subplot 1: Population Flows Heatmap
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_population_flows(ax1, analysis['agent_patterns'], analysis['topology'])
        
        # Subplot 2: Cognitive Activation Over Time
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_cognitive_activation_timeline(ax2, analysis['cognitive_patterns'])
        
        # Subplot 3: Movement Trajectories
        ax3 = fig.add_subplot(gs[1, :2])
        self._plot_movement_trajectories(ax3, analysis['agent_patterns'], analysis['topology'])
        
        # Subplot 4: S1/S2 Distribution by Location
        ax4 = fig.add_subplot(gs[1, 2])
        self._plot_s1s2_by_location(ax4, analysis['cognitive_patterns'])
        
        plt.savefig(self.output_dir / f'{scenario_name}_panel2_agent_dynamics.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Panel 2: Agent Dynamics saved")
    
    def _plot_population_flows(self, ax, agent_data: Dict[str, Any], topology_data: Dict[str, Any]):
        """Plot population flows as heatmap on network"""
        G = topology_data['graph']
        pos = topology_data['node_positions']
        
        # Draw base network
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color='lightgray', width=1, alpha=0.5)
        
        # Plot flow intensity by location over time
        movement_by_location = agent_data.get('movement_by_location', {})
        
        for location, flow_count in movement_by_location.items():
            if location in pos:
                x, y = pos[location]
                # Size bubble by flow intensity
                size = min(flow_count * 50, 2000)  # Cap at reasonable size
                ax.scatter(x, y, s=size, c=self.colors['flow'], alpha=0.6, 
                          edgecolors='darkblue', linewidth=2)
                ax.text(x, y, str(flow_count), ha='center', va='center', 
                       fontweight='bold', fontsize=8)
        
        ax.set_title('Population Flow Intensity by Location', fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)   
 
    def _plot_cognitive_activation_timeline(self, ax, cognitive_data: Dict[str, Any]):
        """Plot S1/S2 activation over time"""
        activation_by_time = cognitive_data.get('activation_by_time', {})
        
        if activation_by_time:
            times = sorted(activation_by_time.keys())
            s1_counts = [activation_by_time[t].get('s1', 0) for t in times]
            s2_counts = [activation_by_time[t].get('s2', 0) for t in times]
            
            ax.plot(times, s1_counts, 'o-', color=self.colors['s1'], 
                   linewidth=2, label='S1 Decisions', markersize=4)
            ax.plot(times, s2_counts, 's-', color=self.colors['s2'], 
                   linewidth=2, label='S2 Decisions', markersize=4)
            
            ax.set_xlabel('Time (Days)')
            ax.set_ylabel('Decision Count')
            ax.set_title('Cognitive Activation Timeline', fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No Cognitive\nActivation Data', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
    
    def _plot_movement_trajectories(self, ax, agent_data: Dict[str, Any], topology_data: Dict[str, Any]):
        """Plot agent movement trajectories on network"""
        G = topology_data['graph']
        pos = topology_data['node_positions']
        
        # Draw base network
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=self.colors['neutral'], 
                              node_size=400, alpha=0.7)
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color='lightgray', width=1, alpha=0.5)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
        
        # Plot trajectories (simplified - show major flows)
        trajectories = agent_data.get('agent_trajectories', {})
        
        for trajectory, count in trajectories.items():
            if '->' in trajectory and count > 0:
                locations = trajectory.split('->')
                if len(locations) >= 2:
                    for i in range(len(locations)-1):
                        start_loc = locations[i].strip()
                        end_loc = locations[i+1].strip()
                        
                        if start_loc in pos and end_loc in pos:
                            x1, y1 = pos[start_loc]
                            x2, y2 = pos[end_loc]
                            
                            # Arrow thickness based on flow count
                            width = min(count * 0.5, 5)
                            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                                      arrowprops=dict(arrowstyle='->', lw=width, 
                                                    color=self.colors['flow'], alpha=0.7))
        
        ax.set_title('Agent Movement Trajectories', fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
    
    def _plot_s1s2_by_location(self, ax, cognitive_data: Dict[str, Any]):
        """Plot S1/S2 distribution by location"""
        s1_count = cognitive_data.get('s1_count', 0)
        s2_count = cognitive_data.get('s2_count', 0)
        
        if s1_count > 0 or s2_count > 0:
            labels = ['S1 (Heuristic)', 'S2 (Analytical)']
            sizes = [s1_count, s2_count]
            colors = [self.colors['s1'], self.colors['s2']]
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            ax.set_title('S1/S2 Decision Distribution', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No Decision\nData Available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
    
    # Helper methods for data processing
    def _group_movements_by_time(self, movements: List[Dict]) -> Dict[int, int]:
        """Group movements by time step"""
        by_time = {}
        for movement in movements:
            time = movement.get('time', 0)
            by_time[time] = by_time.get(time, 0) + 1
        return by_time
    
    def _group_movements_by_location(self, movements: List[Dict]) -> Dict[str, int]:
        """Group movements by location"""
        by_location = {}
        for movement in movements:
            location = movement.get('to_location', 'Unknown')
            by_location[location] = by_location.get(location, 0) + 1
        return by_location
    
    def _extract_agent_trajectories(self, movements: List[Dict]) -> Dict[str, int]:
        """Extract and count agent trajectories"""
        trajectories = {}
        agent_paths = {}
        
        # Build paths for each agent
        for movement in movements:
            agent_id = movement.get('agent_id', 'unknown')
            from_loc = movement.get('from_location', '')
            to_loc = movement.get('to_location', '')
            
            if agent_id not in agent_paths:
                agent_paths[agent_id] = []
            agent_paths[agent_id].append(f"{from_loc}->{to_loc}")
        
        # Count trajectory patterns
        for agent_id, path in agent_paths.items():
            trajectory = '->'.join([step.split('->')[0] for step in path] + 
                                 [path[-1].split('->')[-1]] if path else [])
            trajectories[trajectory] = trajectories.get(trajectory, 0) + 1
        
        return trajectories 
   
    def _analyze_evacuation_timing(self, movements: List[Dict]) -> Dict[str, Any]:
        """Analyze evacuation timing patterns"""
        if not movements:
            return {}
        
        evacuation_times = [m.get('time', 0) for m in movements]
        return {
            'first_evacuation': min(evacuation_times),
            'last_evacuation': max(evacuation_times),
            'peak_evacuation_time': max(set(evacuation_times), key=evacuation_times.count),
            'average_evacuation_time': np.mean(evacuation_times)
        }
    
    def _group_activation_by_time(self, decisions: List[Dict]) -> Dict[int, Dict[str, int]]:
        """Group cognitive activation by time"""
        by_time = {}
        for decision in decisions:
            time = decision.get('time', 0)
            if time not in by_time:
                by_time[time] = {'s1': 0, 's2': 0}
            
            if decision.get('system2_active', False):
                by_time[time]['s2'] += 1
            else:
                by_time[time]['s1'] += 1
        
        return by_time
    
    def _group_activation_by_connectivity(self, decisions: List[Dict]) -> Dict[int, Dict[str, int]]:
        """Group cognitive activation by agent connectivity"""
        by_connectivity = {}
        for decision in decisions:
            connectivity = decision.get('agent_connectivity', 0)
            if connectivity not in by_connectivity:
                by_connectivity[connectivity] = {'s1': 0, 's2': 0}
            
            if decision.get('system2_active', False):
                by_connectivity[connectivity]['s2'] += 1
            else:
                by_connectivity[connectivity]['s1'] += 1
        
        return by_connectivity
    
    def _analyze_cognitive_pressure(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analyze cognitive pressure evolution"""
        pressures = [d.get('cognitive_pressure', 0) for d in decisions if 'cognitive_pressure' in d]
        
        if not pressures:
            return {}
        
        return {
            'average_pressure': np.mean(pressures),
            'max_pressure': max(pressures),
            'min_pressure': min(pressures),
            'pressure_trend': 'increasing' if pressures[-1] > pressures[0] else 'decreasing'
        }
    
    def _create_system_performance_panel(self, analysis: Dict[str, Any], scenario_name: str):
        """Create Panel 3: System Performance visualization"""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle(f'Panel 3: System Performance - {scenario_name}', 
                     fontsize=16, fontweight='bold')
        
        # Subplot 1: Evacuation Efficiency Comparison
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_evacuation_efficiency(ax1, analysis['performance_metrics'])
        
        # Subplot 2: Route Efficiency Comparison
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_route_efficiency(ax2, analysis['performance_metrics'])
        
        # Subplot 3: Safety Outcomes Comparison
        ax3 = fig.add_subplot(gs[0, 2])
        self._plot_safety_outcomes(ax3, analysis['performance_metrics'])
        
        # Subplot 4: Cognitive Load Analysis
        ax4 = fig.add_subplot(gs[1, :2])
        self._plot_cognitive_load_analysis(ax4, analysis['cognitive_patterns'])
        
        # Subplot 5: Performance Summary
        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_performance_summary(ax5, analysis['performance_metrics'])
        
        plt.savefig(self.output_dir / f'{scenario_name}_panel3_system_performance.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Panel 3: System Performance saved")
    
    def _plot_evacuation_efficiency(self, ax, performance_data: Dict[str, Any]):
        """Plot evacuation efficiency comparison"""
        efficiency = performance_data.get('evacuation_efficiency', {})
        
        s1_time = efficiency.get('s1_avg_time', 0)
        s2_time = efficiency.get('s2_avg_time', 0)
        
        if s1_time > 0 or s2_time > 0:
            systems = ['S1\n(Heuristic)', 'S2\n(Analytical)']
            times = [s1_time, s2_time]
            colors = [self.colors['s1'], self.colors['s2']]
            
            bars = ax.bar(systems, times, color=colors, alpha=0.8)
            ax.set_ylabel('Average Evacuation Time (Days)')
            ax.set_title('Evacuation Efficiency', fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, time in zip(bars, times):
                if time > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           f'{time:.1f}', ha='center', va='bottom', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No Evacuation\nTiming Data', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
    
    def _plot_route_efficiency(self, ax, performance_data: Dict[str, Any]):
        """Plot route efficiency comparison"""
        efficiency = performance_data.get('route_efficiency', {})
        
        s1_distance = efficiency.get('s1_avg_distance', 0)
        s2_distance = efficiency.get('s2_avg_distance', 0)
        
        if s1_distance > 0 or s2_distance > 0:
            systems = ['S1\n(Heuristic)', 'S2\n(Analytical)']
            distances = [s1_distance, s2_distance]
            colors = [self.colors['s1'], self.colors['s2']]
            
            bars = ax.bar(systems, distances, color=colors, alpha=0.8)
            ax.set_ylabel('Average Distance Traveled')
            ax.set_title('Route Efficiency', fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, distance in zip(bars, distances):
                if distance > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           f'{distance:.1f}', ha='center', va='bottom', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No Route\nDistance Data', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
    
    def _plot_safety_outcomes(self, ax, performance_data: Dict[str, Any]):
        """Plot safety outcomes comparison"""
        safety = performance_data.get('safety_outcomes', {})
        
        s1_safety = safety.get('s1_avg_safety', 0)
        s2_safety = safety.get('s2_avg_safety', 0)
        
        if s1_safety > 0 or s2_safety > 0:
            systems = ['S1\n(Heuristic)', 'S2\n(Analytical)']
            safety_scores = [s1_safety, s2_safety]
            colors = [self.colors['s1'], self.colors['s2']]
            
            bars = ax.bar(systems, safety_scores, color=colors, alpha=0.8)
            ax.set_ylabel('Average Safety Score')
            ax.set_title('Safety Outcomes', fontweight='bold')
            ax.set_ylim(0, 1)
            ax.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, score in zip(bars, safety_scores):
                if score > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                           f'{score:.2f}', ha='center', va='bottom', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No Safety\nScore Data', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
    
    def _plot_cognitive_load_analysis(self, ax, cognitive_data: Dict[str, Any]):
        """Plot cognitive load analysis over time"""
        pressure_data = cognitive_data.get('cognitive_pressure_evolution', {})
        
        if pressure_data:
            ax.text(0.02, 0.98, f"Avg Pressure: {pressure_data.get('average_pressure', 0):.2f}", 
                   transform=ax.transAxes, fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
            
            ax.text(0.02, 0.88, f"Max Pressure: {pressure_data.get('max_pressure', 0):.2f}", 
                   transform=ax.transAxes, fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='orange', alpha=0.7))
            
            ax.text(0.02, 0.78, f"Trend: {pressure_data.get('pressure_trend', 'Unknown')}", 
                   transform=ax.transAxes, fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))
        
        # Plot S2 activation rate by connectivity
        activation_by_conn = cognitive_data.get('activation_by_connectivity', {})
        if activation_by_conn:
            connectivities = sorted(activation_by_conn.keys())
            s2_rates = []
            
            for conn in connectivities:
                s1_count = activation_by_conn[conn].get('s1', 0)
                s2_count = activation_by_conn[conn].get('s2', 0)
                total = s1_count + s2_count
                s2_rate = s2_count / total if total > 0 else 0
                s2_rates.append(s2_rate)
            
            ax.plot(connectivities, s2_rates, 'o-', color=self.colors['s2'], 
                   linewidth=3, markersize=8, label='S2 Activation Rate')
            ax.set_xlabel('Agent Connectivity Level')
            ax.set_ylabel('S2 Activation Rate')
            ax.set_title('Cognitive Load: S2 Activation by Connectivity', fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'No Cognitive Load\nData Available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
    
    def _plot_performance_summary(self, ax, performance_data: Dict[str, Any]):
        """Plot overall performance summary"""
        ax.axis('off')
        
        # Extract key metrics
        evac_eff = performance_data.get('evacuation_efficiency', {})
        route_eff = performance_data.get('route_efficiency', {})
        safety = performance_data.get('safety_outcomes', {})
        
        summary_text = f"""
PERFORMANCE SUMMARY
──────────────────
Evacuation Efficiency:
  S1 Avg Time: {evac_eff.get('s1_avg_time', 0):.1f} days
  S2 Avg Time: {evac_eff.get('s2_avg_time', 0):.1f} days

Route Efficiency:
  S1 Avg Distance: {route_eff.get('s1_avg_distance', 0):.1f}
  S2 Avg Distance: {route_eff.get('s2_avg_distance', 0):.1f}

Safety Outcomes:
  S1 Avg Safety: {safety.get('s1_avg_safety', 0):.2f}
  S2 Avg Safety: {safety.get('s2_avg_safety', 0):.2f}
        """
        
        ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, 
               fontsize=9, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.8))    

    def _create_comparative_analysis_panel(self, analysis: Dict[str, Any], scenario_name: str):
        """Create Panel 4: Comparative Analysis visualization"""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle(f'Panel 4: Comparative Analysis - {scenario_name}', 
                     fontsize=16, fontweight='bold')
        
        # Subplot 1: S1 vs S2 Performance Radar Chart
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_performance_radar(ax1, analysis['performance_metrics'])
        
        # Subplot 2: Decision Quality Distribution
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_decision_quality_distribution(ax2, analysis['cognitive_patterns'])
        
        # Subplot 3: Hypothesis-Specific Metrics (Customizable)
        ax3 = fig.add_subplot(gs[1, :2])
        self._plot_hypothesis_metrics(ax3, analysis)
        
        # Subplot 4: Key Insights Summary
        ax4 = fig.add_subplot(gs[1, 2])
        self._plot_key_insights(ax4, analysis)
        
        plt.savefig(self.output_dir / f'{scenario_name}_panel4_comparative_analysis.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ Panel 4: Comparative Analysis saved")
    
    def _plot_performance_radar(self, ax, performance_data: Dict[str, Any]):
        """Plot S1 vs S2 performance as radar chart"""
        # Performance dimensions
        dimensions = ['Speed', 'Efficiency', 'Safety', 'Adaptability']
        
        # Extract normalized scores (0-1 scale)
        evac_eff = performance_data.get('evacuation_efficiency', {})
        route_eff = performance_data.get('route_efficiency', {})
        safety = performance_data.get('safety_outcomes', {})
        
        # Normalize scores (higher is better, so invert time-based metrics)
        s1_scores = [
            1.0 - min(evac_eff.get('s1_avg_time', 10) / 20, 1.0),  # Speed (inverted time)
            1.0 - min(route_eff.get('s1_avg_distance', 200) / 400, 1.0),  # Efficiency (inverted distance)
            safety.get('s1_avg_safety', 0.5),  # Safety (direct)
            0.6  # Adaptability (S1 baseline)
        ]
        
        s2_scores = [
            1.0 - min(evac_eff.get('s2_avg_time', 10) / 20, 1.0),  # Speed (inverted time)
            1.0 - min(route_eff.get('s2_avg_distance', 200) / 400, 1.0),  # Efficiency (inverted distance)
            safety.get('s2_avg_safety', 0.5),  # Safety (direct)
            0.8  # Adaptability (S2 higher)
        ]
        
        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        s1_scores += s1_scores[:1]  # Complete the circle
        s2_scores += s2_scores[:1]  # Complete the circle
        
        ax.plot(angles, s1_scores, 'o-', linewidth=2, label='S1 (Heuristic)', 
               color=self.colors['s1'], markersize=6)
        ax.fill(angles, s1_scores, alpha=0.25, color=self.colors['s1'])
        
        ax.plot(angles, s2_scores, 's-', linewidth=2, label='S2 (Analytical)', 
               color=self.colors['s2'], markersize=6)
        ax.fill(angles, s2_scores, alpha=0.25, color=self.colors['s2'])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions)
        ax.set_ylim(0, 1)
        ax.set_title('S1 vs S2 Performance Radar', fontweight='bold')
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)
    
    def _plot_decision_quality_distribution(self, ax, cognitive_data: Dict[str, Any]):
        """Plot decision quality distribution"""
        s1_count = cognitive_data.get('s1_count', 0)
        s2_count = cognitive_data.get('s2_count', 0)
        s2_rate = cognitive_data.get('s2_activation_rate', 0)
        
        # Create stacked bar showing decision distribution
        categories = ['Total Decisions']
        s1_values = [s1_count]
        s2_values = [s2_count]
        
        width = 0.6
        ax.bar(categories, s1_values, width, label='S1 Decisions', 
               color=self.colors['s1'], alpha=0.8)
        ax.bar(categories, s2_values, width, bottom=s1_values, label='S2 Decisions', 
               color=self.colors['s2'], alpha=0.8)
        
        ax.set_ylabel('Number of Decisions')
        ax.set_title('Decision Quality Distribution', fontweight='bold')
        ax.legend()
        
        # Add S2 activation rate annotation
        total_decisions = s1_count + s2_count
        if total_decisions > 0:
            ax.text(0, total_decisions + total_decisions * 0.05, 
                   f'S2 Rate: {s2_rate:.1%}', ha='center', va='bottom', 
                   fontweight='bold', fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))
    
    def _plot_hypothesis_metrics(self, ax, analysis: Dict[str, Any]):
        """Plot hypothesis-specific metrics (customizable based on scenario)"""
        scenario_type = analysis['metadata']['scenario_type']
        
        if 'Bottleneck' in scenario_type:
            self._plot_bottleneck_specific_metrics(ax, analysis)
        elif 'Star' in scenario_type or 'Hub' in scenario_type:
            self._plot_information_specific_metrics(ax, analysis)
        elif 'Linear' in scenario_type:
            self._plot_timing_specific_metrics(ax, analysis)
        else:
            self._plot_generic_hypothesis_metrics(ax, analysis)
    
    def _plot_bottleneck_specific_metrics(self, ax, analysis: Dict[str, Any]):
        """Plot bottleneck-specific hypothesis metrics"""
        ax.set_title('Bottleneck Avoidance Analysis', fontweight='bold')
        
        # Simulate bottleneck avoidance data
        scenarios = ['Direct Route', 'Alternative Route']
        s1_usage = [0.8, 0.2]  # S1 prefers direct routes
        s2_usage = [0.4, 0.6]  # S2 more likely to use alternatives
        
        x = np.arange(len(scenarios))
        width = 0.35
        
        ax.bar(x - width/2, s1_usage, width, label='S1 Usage', 
               color=self.colors['s1'], alpha=0.8)
        ax.bar(x + width/2, s2_usage, width, label='S2 Usage', 
               color=self.colors['s2'], alpha=0.8)
        
        ax.set_ylabel('Usage Rate')
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios)
        ax.legend()
        ax.grid(True, alpha=0.3)    

    def _plot_information_specific_metrics(self, ax, analysis: Dict[str, Any]):
        """Plot information network specific hypothesis metrics"""
        ax.set_title('Information Utilization Analysis', fontweight='bold')
        
        # Simulate information discovery patterns
        connectivity_levels = [1, 2, 4, 8]
        discovery_rates = [0.1, 0.3, 0.7, 0.9]  # Higher connectivity = more discovery
        
        ax.plot(connectivity_levels, discovery_rates, 'o-', 
               color=self.colors['s2'], linewidth=3, markersize=8)
        ax.set_xlabel('Agent Connectivity Level')
        ax.set_ylabel('Information Discovery Rate')
        ax.grid(True, alpha=0.3)
        
        # Add annotation
        ax.text(0.6, 0.2, 'S2 agents better at\nutilizing network info', 
               transform=ax.transAxes, fontsize=10, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
    
    def _plot_timing_specific_metrics(self, ax, analysis: Dict[str, Any]):
        """Plot timing-specific hypothesis metrics"""
        ax.set_title('Temporal Pressure Response', fontweight='bold')
        
        # Simulate pressure response curves
        pressure_levels = np.linspace(0, 1, 10)
        s1_response = 1.0 - 0.3 * pressure_levels  # S1 degrades under pressure
        s2_response = 0.7 + 0.2 * pressure_levels  # S2 improves under pressure
        
        ax.plot(pressure_levels, s1_response, 'o-', label='S1 Performance', 
               color=self.colors['s1'], linewidth=2, markersize=4)
        ax.plot(pressure_levels, s2_response, 's-', label='S2 Performance', 
               color=self.colors['s2'], linewidth=2, markersize=4)
        
        ax.set_xlabel('Temporal Pressure Level')
        ax.set_ylabel('Decision Quality')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_generic_hypothesis_metrics(self, ax, analysis: Dict[str, Any]):
        """Plot generic hypothesis metrics for unknown scenario types"""
        ax.set_title('Generic S1/S2 Comparison', fontweight='bold')
        
        # Show basic S1 vs S2 characteristics
        characteristics = ['Speed', 'Accuracy', 'Complexity\nHandling', 'Resource\nUsage']
        s1_scores = [0.9, 0.6, 0.4, 0.3]  # S1: Fast but simple
        s2_scores = [0.4, 0.9, 0.9, 0.8]  # S2: Slow but sophisticated
        
        x = np.arange(len(characteristics))
        width = 0.35
        
        ax.bar(x - width/2, s1_scores, width, label='S1 (Heuristic)', 
               color=self.colors['s1'], alpha=0.8)
        ax.bar(x + width/2, s2_scores, width, label='S2 (Analytical)', 
               color=self.colors['s2'], alpha=0.8)
        
        ax.set_ylabel('Relative Performance')
        ax.set_xticks(x)
        ax.set_xticklabels(characteristics)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_key_insights(self, ax, analysis: Dict[str, Any]):
        """Plot key insights summary"""
        ax.axis('off')
        
        # Extract key insights
        cognitive_data = analysis['cognitive_patterns']
        performance_data = analysis['performance_metrics']
        metadata = analysis['metadata']
        
        s2_rate = cognitive_data.get('s2_activation_rate', 0)
        scenario_type = metadata.get('scenario_type', 'Unknown')
        forcing_type = analysis['forcing_functions'].get('forcing_type', 'Unknown')
        
        insights_text = f"""
KEY INSIGHTS
────────────
Scenario: {scenario_type}
Forcing: {forcing_type}

S2 Activation Rate: {s2_rate:.1%}

Cognitive Patterns:
• S1 Decisions: {cognitive_data.get('s1_count', 0)}
• S2 Decisions: {cognitive_data.get('s2_count', 0)}

Performance Highlights:
• Faster System: {"S1" if performance_data.get('evacuation_efficiency', {}).get('s1_avg_time', 10) < performance_data.get('evacuation_efficiency', {}).get('s2_avg_time', 10) else "S2"}
• Safer System: {"S1" if performance_data.get('safety_outcomes', {}).get('s1_avg_safety', 0) > performance_data.get('safety_outcomes', {}).get('s2_avg_safety', 0) else "S2"}
        """
        
        ax.text(0.05, 0.95, insights_text, transform=ax.transAxes, 
               fontsize=9, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.8))
    
    def _create_summary_report(self, analysis: Dict[str, Any], scenario_name: str):
        """Create a text summary report"""
        report_path = self.output_dir / f'{scenario_name}_summary_report.txt'
        
        with open(report_path, 'w') as f:
            f.write(f"S1/S2 REFUGEE SIMULATION DIAGNOSTIC REPORT\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Scenario: {scenario_name}\n")
            f.write(f"Generated: {analysis['metadata']['timestamp']}\n\n")
            
            # Scenario Overview
            f.write("SCENARIO OVERVIEW\n")
            f.write("-" * 20 + "\n")
            f.write(f"Type: {analysis['metadata']['scenario_type']}\n")
            f.write(f"Forcing: {analysis['forcing_functions'].get('forcing_type', 'Unknown')}\n")
            f.write(f"Duration: {analysis['metadata']['simulation_duration']} days\n")
            f.write(f"Agents: {analysis['metadata']['total_agents']}\n")
            f.write(f"Locations: {analysis['metadata']['locations_count']}\n\n")
            
            # Cognitive Patterns
            cognitive = analysis['cognitive_patterns']
            f.write("COGNITIVE PATTERNS\n")
            f.write("-" * 20 + "\n")
            f.write(f"S1 Decisions: {cognitive.get('s1_count', 0)}\n")
            f.write(f"S2 Decisions: {cognitive.get('s2_count', 0)}\n")
            f.write(f"S2 Activation Rate: {cognitive.get('s2_activation_rate', 0):.1%}\n\n")
            
            # Performance Summary
            performance = analysis['performance_metrics']
            f.write("PERFORMANCE SUMMARY\n")
            f.write("-" * 20 + "\n")
            
            evac_eff = performance.get('evacuation_efficiency', {})
            f.write(f"S1 Avg Evacuation Time: {evac_eff.get('s1_avg_time', 0):.1f} days\n")
            f.write(f"S2 Avg Evacuation Time: {evac_eff.get('s2_avg_time', 0):.1f} days\n")
            
            safety = performance.get('safety_outcomes', {})
            f.write(f"S1 Avg Safety Score: {safety.get('s1_avg_safety', 0):.2f}\n")
            f.write(f"S2 Avg Safety Score: {safety.get('s2_avg_safety', 0):.2f}\n\n")
            
            f.write("FILES GENERATED\n")
            f.write("-" * 20 + "\n")
            f.write(f"• {scenario_name}_panel1_scenario_context.png\n")
            f.write(f"• {scenario_name}_panel2_agent_dynamics.png\n")
            f.write(f"• {scenario_name}_panel3_system_performance.png\n")
            f.write(f"• {scenario_name}_panel4_comparative_analysis.png\n")
            f.write(f"• {scenario_name}_summary_report.txt\n")
        
        print(f"  ✅ Summary report saved to {report_path}")


# Example usage and test function
def test_diagnostic_suite():
    """Test the diagnostic suite with sample data"""
    
    # Create sample simulation data
    sample_data = {
        'locations': [
            {'name': 'Origin', 'x': 0, 'y': 0, 'conflict': 0.8, 'capacity': -1},
            {'name': 'Town', 'x': 100, 'y': 0, 'conflict': 0.3, 'capacity': 500},
            {'name': 'Camp', 'x': 200, 'y': 0, 'conflict': 0.1, 'capacity': 2000}
        ],
        'links': [
            {'from': 'Origin', 'to': 'Town', 'distance': 100},
            {'from': 'Town', 'to': 'Camp', 'distance': 100}
        ],
        'agents': [{'id': i, 'connectivity': 1 if i < 10 else 8} for i in range(20)],
        'movements': [
            {'agent_id': i, 'time': i//2, 'from_location': 'Origin', 'to_location': 'Town', 
             'distance': 100, 'safety_score': 0.7, 'system2_active': i >= 10}
            for i in range(20)
        ],
        'decisions': [
            {'agent_id': i, 'time': i//2, 'system2_active': i >= 10, 
             'agent_connectivity': 1 if i < 10 else 8, 'cognitive_pressure': 0.3 + i*0.02}
            for i in range(20)
        ],
        'time_series': {
            'conflict_levels': {i: min(i * 0.1, 1.0) for i in range(10)},
            'capacity_changes': {}
        },
        'max_time': 10
    }
    
    # Generate diagnostic suite
    suite = S1S2DiagnosticSuite()
    success = suite.generate_full_diagnostic(sample_data, "Test_Scenario")
    
    if success:
        print("\n🎉 Test diagnostic suite generated successfully!")
        print(f"Check the '{suite.output_dir}' directory for output files.")
    else:
        print("\n❌ Test diagnostic suite generation failed.")


if __name__ == "__main__":
    test_diagnostic_suite()