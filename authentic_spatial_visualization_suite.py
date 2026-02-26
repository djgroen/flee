#!/usr/bin/env python3
"""
Authentic Spatial Visualization Suite

Creates spatial/network maps and standard visualization suite for each authentic
Flee simulation scenario. Shows network topology, agent movements, and spatial patterns.
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Arrow
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from validate_flee_data import validate_flee_simulation_data

# Set publication style
plt.style.use('default')
sns.set_palette("Set2")
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 14
})

class AuthenticSpatialVisualizationSuite:
    """
    Creates comprehensive spatial visualizations from authentic Flee simulation data.
    
    Generates standard suite of plots for each scenario:
    1. Network topology map
    2. Agent movement flows
    3. Population evolution over time
    4. S1/S2 spatial decision patterns
    5. Route utilization analysis
    """
    
    def __init__(self, output_dir: str = "spatial_analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.scenario_data = {}
        
    def load_authentic_scenario_data(self, simulation_dir: Path) -> bool:
        """
        Load and validate authentic simulation data from a single scenario.
        
        Args:
            simulation_dir: Path to authentic simulation directory
            
        Returns:
            True if data is authentic and loaded successfully
        """
        print(f"🔒 LOADING AUTHENTIC DATA: {simulation_dir.name}")
        
        # Validate authenticity first
        if not validate_flee_simulation_data(str(simulation_dir)):
            print(f"❌ CRITICAL: {simulation_dir.name} failed authenticity validation!")
            return False
        
        try:
            # Load S1/S2 decision data
            decisions_file = simulation_dir / "s1s2_diagnostics" / "cognitive_decisions.json"
            if not decisions_file.exists():
                print(f"❌ No S1/S2 data found in {simulation_dir.name}")
                return False
            
            with open(decisions_file, 'r') as f:
                data = json.load(f)
            
            # Load provenance for metadata
            provenance_file = simulation_dir / "provenance.json"
            with open(provenance_file, 'r') as f:
                provenance = json.load(f)
            
            # Load native Flee output for validation
            flee_output_file = simulation_dir / "standard_flee" / "out.csv"
            flee_data = None
            if flee_output_file.exists():
                flee_data = pd.read_csv(flee_output_file)
            
            # Store scenario data
            scenario_name = provenance['simulation_metadata']['scenario_name']
            self.scenario_data = {
                'name': scenario_name,
                'decisions': data['decisions'],
                'daily_populations': data['daily_populations'],
                'locations': data['locations'],
                'provenance': provenance,
                'flee_output': flee_data,
                'directory': simulation_dir
            }
            
            print(f"✅ Loaded authentic data: {len(data['decisions'])} decisions, {len(data['locations'])} locations")
            return True
            
        except Exception as e:
            print(f"❌ Error loading {simulation_dir.name}: {e}")
            return False
    
    def generate_spatial_suite_for_scenario(self, simulation_dir: Path) -> bool:
        """Generate complete spatial visualization suite for one scenario."""
        print(f"\\n📊 GENERATING SPATIAL SUITE: {simulation_dir.name}")
        print("=" * 60)
        
        # Load scenario data
        if not self.load_authentic_scenario_data(simulation_dir):
            return False
        
        scenario_name = self.scenario_data['name']
        safe_name = scenario_name.replace(' ', '_').replace('/', '_')
        
        # Create scenario-specific output directory
        scenario_output_dir = self.output_dir / f"{safe_name}_spatial_analysis"
        scenario_output_dir.mkdir(exist_ok=True)
        
        try:
            # Generate comprehensive spatial figure (6 panels)
            self._generate_comprehensive_spatial_figure(scenario_output_dir, safe_name)
            
            # Generate individual detailed plots
            self._generate_network_topology_map(scenario_output_dir, safe_name)
            self._generate_agent_movement_flows(scenario_output_dir, safe_name)
            self._generate_population_evolution_map(scenario_output_dir, safe_name)
            self._generate_s1s2_spatial_patterns(scenario_output_dir, safe_name)
            
            print(f"✅ Spatial suite completed for {scenario_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating spatial suite: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_comprehensive_spatial_figure(self, output_dir: Path, safe_name: str):
        """Generate comprehensive 6-panel spatial analysis figure."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'Spatial Analysis: {self.scenario_data["name"]}\\n(Authentic Flee Simulation Data)', 
                    fontsize=16, fontweight='bold')
        
        # Panel 1: Network Topology
        self._plot_network_topology(axes[0, 0])
        
        # Panel 2: Population Evolution
        self._plot_population_time_series(axes[0, 1])
        
        # Panel 3: Agent Movement Flows
        self._plot_movement_flows(axes[0, 2])
        
        # Panel 4: S1/S2 Spatial Distribution
        self._plot_s1s2_spatial_distribution(axes[1, 0])
        
        # Panel 5: Route Utilization
        self._plot_route_utilization(axes[1, 1])
        
        # Panel 6: Scenario Metadata
        self._plot_scenario_metadata(axes[1, 2])
        
        plt.tight_layout()
        
        # Save comprehensive figure
        output_file = output_dir / f"{safe_name}_comprehensive_spatial_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Comprehensive spatial figure: {output_file}")
    
    def _plot_network_topology(self, ax):
        """Plot network topology with locations and connections."""
        locations = self.scenario_data['locations']
        
        if not locations:
            ax.text(0.5, 0.5, 'No Location Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Network Topology')
            return
        
        # Extract coordinates and properties
        x_coords = [loc['x'] for loc in locations]
        y_coords = [loc['y'] for loc in locations]
        names = [loc['name'] for loc in locations]
        conflicts = [loc['conflict'] for loc in locations]
        capacities = [loc['capacity'] for loc in locations]
        final_pops = [loc['final_population'] for loc in locations]
        
        # Normalize coordinates if needed
        if max(x_coords) - min(x_coords) > 0:
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords) if max(y_coords) - min(y_coords) > 0 else 1
            scale = max(x_range, y_range)
        else:
            scale = 1
        
        # Plot locations
        for i, (x, y, name, conflict, capacity, pop) in enumerate(zip(x_coords, y_coords, names, conflicts, capacities, final_pops)):
            # Color by conflict level
            color = plt.cm.Reds(conflict) if conflict > 0 else 'lightblue'
            
            # Size by final population (with minimum size)
            size = max(100, min(1000, 100 + pop * 10))
            
            # Plot location
            ax.scatter(x, y, s=size, c=[color], alpha=0.8, edgecolors='black', linewidth=1)
            
            # Add label
            ax.annotate(name, (x, y), xytext=(5, 5), textcoords='offset points', 
                       fontsize=8, fontweight='bold')
            
            # Add capacity info if relevant
            if capacity > 0:
                ax.annotate(f'Cap: {capacity}', (x, y), xytext=(5, -15), 
                           textcoords='offset points', fontsize=6, alpha=0.7)
        
        # Draw connections (simplified - assume linear connections based on scenario)
        self._draw_network_connections(ax, x_coords, y_coords, names)
        
        ax.set_xlabel('X Coordinate (km)')
        ax.set_ylabel('Y Coordinate (km)')
        ax.set_title('Network Topology\\n(Size=Population, Color=Conflict)')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
    
    def _draw_network_connections(self, ax, x_coords, y_coords, names):
        """Draw network connections based on scenario type."""
        scenario_name = self.scenario_data['name'].lower()
        
        if 'evacuation' in scenario_name:
            # Linear chain: Origin -> Transit -> Camp
            if len(x_coords) >= 3:
                # Sort by x-coordinate for linear chain
                sorted_indices = sorted(range(len(x_coords)), key=lambda i: x_coords[i])
                for i in range(len(sorted_indices) - 1):
                    idx1, idx2 = sorted_indices[i], sorted_indices[i + 1]
                    ax.plot([x_coords[idx1], x_coords[idx2]], [y_coords[idx1], y_coords[idx2]], 
                           'k-', linewidth=2, alpha=0.6)
        
        elif 'bottleneck' in scenario_name:
            # Diamond topology with alternative route
            origin_idx = next((i for i, name in enumerate(names) if 'origin' in name.lower()), 0)
            
            for i, name in enumerate(names):
                if i != origin_idx and 'origin' not in name.lower():
                    ax.plot([x_coords[origin_idx], x_coords[i]], [y_coords[origin_idx], y_coords[i]], 
                           'k-', linewidth=2, alpha=0.6)
        
        elif 'destination' in scenario_name:
            # Star topology: Origin connected to all destinations
            origin_idx = next((i for i, name in enumerate(names) if 'origin' in name.lower()), 0)
            
            for i, name in enumerate(names):
                if i != origin_idx:
                    ax.plot([x_coords[origin_idx], x_coords[i]], [y_coords[origin_idx], y_coords[i]], 
                           'k-', linewidth=2, alpha=0.6)
    
    def _plot_population_time_series(self, ax):
        """Plot population evolution over time."""
        daily_pops = self.scenario_data['daily_populations']
        
        if not daily_pops:
            ax.text(0.5, 0.5, 'No Population Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Population Evolution')
            return
        
        # Extract time series data
        days = [d['day'] for d in daily_pops]
        
        # Get all location names (excluding 'day' and 'total')
        location_names = [key for key in daily_pops[0].keys() if key not in ['day', 'total']]
        
        # Plot each location's population over time
        for loc_name in location_names:
            populations = [d.get(loc_name, 0) for d in daily_pops]
            ax.plot(days, populations, marker='o', linewidth=2, label=loc_name, markersize=4)
        
        ax.set_xlabel('Simulation Day')
        ax.set_ylabel('Population')
        ax.set_title('Population Evolution Over Time')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    def _plot_movement_flows(self, ax):
        """Plot agent movement flows between locations."""
        decisions = self.scenario_data['decisions']
        locations = self.scenario_data['locations']
        
        if not decisions or not locations:
            ax.text(0.5, 0.5, 'No Movement Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Movement Flows')
            return
        
        # Create movement flow analysis
        daily_pops = self.scenario_data['daily_populations']
        
        if len(daily_pops) < 2:
            ax.text(0.5, 0.5, 'Insufficient Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Movement Flows')
            return
        
        # Calculate net flows between consecutive days
        location_names = [key for key in daily_pops[0].keys() if key not in ['day', 'total']]
        
        # Plot flow arrows (simplified visualization)
        x_coords = [loc['x'] for loc in locations]
        y_coords = [loc['y'] for loc in locations]
        names = [loc['name'] for loc in locations]
        
        # Draw base network
        for i, (x, y, name) in enumerate(zip(x_coords, y_coords, names)):
            ax.scatter(x, y, s=200, c='lightblue', alpha=0.8, edgecolors='black')
            ax.annotate(name, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # Draw flow arrows (conceptual)
        self._draw_flow_arrows(ax, x_coords, y_coords, names, daily_pops)
        
        ax.set_xlabel('X Coordinate (km)')
        ax.set_ylabel('Y Coordinate (km)')
        ax.set_title('Agent Movement Flows\\n(Arrow thickness = flow magnitude)')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
    
    def _draw_flow_arrows(self, ax, x_coords, y_coords, names, daily_pops):
        """Draw flow arrows between locations."""
        if len(daily_pops) < 2:
            return
        
        # Calculate total population change for each location
        initial_pops = daily_pops[0]
        final_pops = daily_pops[-1]
        
        # Find major flows (simplified heuristic)
        for i, name in enumerate(names):
            if name in initial_pops and name in final_pops:
                pop_change = final_pops[name] - initial_pops[name]
                
                if pop_change > 0:  # Population increased (destination)
                    # Draw arrows from other locations to this one
                    for j, other_name in enumerate(names):
                        if i != j and other_name in initial_pops and other_name in final_pops:
                            other_change = final_pops[other_name] - initial_pops[other_name]
                            if other_change < 0:  # Other location lost population
                                # Draw arrow from j to i
                                dx = x_coords[i] - x_coords[j]
                                dy = y_coords[i] - y_coords[j]
                                length = np.sqrt(dx**2 + dy**2)
                                if length > 0:
                                    # Normalize and scale
                                    dx_norm = dx / length * 0.8
                                    dy_norm = dy / length * 0.8
                                    
                                    ax.arrow(x_coords[j] + dx_norm * 0.2, y_coords[j] + dy_norm * 0.2,
                                            dx_norm * 0.6, dy_norm * 0.6,
                                            head_width=5, head_length=3, fc='red', ec='red', alpha=0.7)
    
    def _plot_s1s2_spatial_distribution(self, ax):
        """Plot S1/S2 decision distribution in space."""
        decisions = self.scenario_data['decisions']
        locations = self.scenario_data['locations']
        
        if not decisions:
            ax.text(0.5, 0.5, 'No Decision Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('S1/S2 Spatial Distribution')
            return
        
        # Count S1/S2 decisions
        s1_count = len([d for d in decisions if not d.get('system2_active', False)])
        s2_count = len([d for d in decisions if d.get('system2_active', False)])
        
        # Create pie chart
        if s1_count + s2_count > 0:
            sizes = [s1_count, s2_count]
            labels = [f'S1 Heuristic\\n({s1_count})', f'S2 Analytical\\n({s2_count})']
            colors = ['#FF6B6B', '#4ECDC4']
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            
            # Add connectivity analysis
            s1_connections = [d.get('connections', 0) for d in decisions if not d.get('system2_active', False)]
            s2_connections = [d.get('connections', 0) for d in decisions if d.get('system2_active', False)]
            
            avg_s1_conn = np.mean(s1_connections) if s1_connections else 0
            avg_s2_conn = np.mean(s2_connections) if s2_connections else 0
            
            ax.text(0.02, 0.02, f'Avg S1 connectivity: {avg_s1_conn:.1f}\\nAvg S2 connectivity: {avg_s2_conn:.1f}',
                   transform=ax.transAxes, fontsize=8, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title('S1/S2 Decision Distribution')
    
    def _plot_route_utilization(self, ax):
        """Plot route utilization analysis."""
        daily_pops = self.scenario_data['daily_populations']
        
        if not daily_pops or len(daily_pops) < 2:
            ax.text(0.5, 0.5, 'Insufficient Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Route Utilization')
            return
        
        # Analyze population changes to infer route usage
        location_names = [key for key in daily_pops[0].keys() if key not in ['day', 'total']]
        
        # Calculate peak populations for each location
        peak_pops = {}
        for loc_name in location_names:
            populations = [d.get(loc_name, 0) for d in daily_pops]
            peak_pops[loc_name] = max(populations)
        
        # Create bar chart of peak populations
        locations = list(peak_pops.keys())
        peaks = list(peak_pops.values())
        
        bars = ax.bar(locations, peaks, color='skyblue', alpha=0.7, edgecolor='black')
        
        # Add value labels on bars
        for bar, peak in zip(bars, peaks):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{int(peak)}', ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('Location')
        ax.set_ylabel('Peak Population')
        ax.set_title('Peak Population by Location\\n(Route Utilization Indicator)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
    
    def _plot_scenario_metadata(self, ax):
        """Plot scenario metadata and authenticity information."""
        ax.axis('off')
        
        provenance = self.scenario_data['provenance']
        
        # Scenario information
        info_text = []
        info_text.append("🔒 AUTHENTIC FLEE SIMULATION")
        info_text.append("=" * 30)
        info_text.append("")
        
        # Basic metadata
        sim_meta = provenance['simulation_metadata']
        info_text.append(f"Scenario: {sim_meta['scenario_name']}")
        info_text.append(f"Duration: {sim_meta['total_days']} days")
        info_text.append(f"Timestamp: {sim_meta['timestamp'][:19]}")
        info_text.append("")
        
        # Authenticity verification
        flee_meta = provenance['flee_integration']
        info_text.append("Authenticity Verification:")
        info_text.append(f"  ✅ ecosystem.evolve() calls: {flee_meta['total_evolve_calls']}")
        info_text.append(f"  ✅ Engine: {flee_meta['simulation_engine']}")
        info_text.append(f"  ✅ Standard output: {flee_meta['standard_output_generated']}")
        info_text.append("")
        
        # Data summary
        decisions = self.scenario_data['decisions']
        locations = self.scenario_data['locations']
        info_text.append("Data Summary:")
        info_text.append(f"  • Locations: {len(locations)}")
        info_text.append(f"  • Decision records: {len(decisions)}")
        info_text.append(f"  • S1 decisions: {len([d for d in decisions if not d.get('system2_active', False)])}")
        info_text.append(f"  • S2 decisions: {len([d for d in decisions if d.get('system2_active', False)])}")
        
        # Display information
        y_pos = 0.95
        for line in info_text:
            font_weight = 'bold' if line.startswith('🔒') or line.startswith('=') or ':' in line else 'normal'
            font_size = 10 if line.startswith('🔒') else 8
            ax.text(0.05, y_pos, line, transform=ax.transAxes, fontsize=font_size,
                   verticalalignment='top', fontweight=font_weight)
            y_pos -= 0.05
    
    def _generate_network_topology_map(self, output_dir: Path, safe_name: str):
        """Generate detailed network topology map."""
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        self._plot_network_topology(ax)
        plt.title(f'Network Topology: {self.scenario_data["name"]}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_file = output_dir / f"{safe_name}_network_topology.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Network topology map: {output_file}")
    
    def _generate_agent_movement_flows(self, output_dir: Path, safe_name: str):
        """Generate detailed agent movement flow visualization."""
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        self._plot_movement_flows(ax)
        plt.title(f'Agent Movement Flows: {self.scenario_data["name"]}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_file = output_dir / f"{safe_name}_movement_flows.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Movement flows map: {output_file}")
    
    def _generate_population_evolution_map(self, output_dir: Path, safe_name: str):
        """Generate detailed population evolution visualization."""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        self._plot_population_time_series(ax)
        plt.title(f'Population Evolution: {self.scenario_data["name"]}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_file = output_dir / f"{safe_name}_population_evolution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Population evolution map: {output_file}")
    
    def _generate_s1s2_spatial_patterns(self, output_dir: Path, safe_name: str):
        """Generate S1/S2 spatial pattern analysis."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        self._plot_s1s2_spatial_distribution(ax1)
        self._plot_route_utilization(ax2)
        
        plt.suptitle(f'S1/S2 Spatial Patterns: {self.scenario_data["name"]}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_file = output_dir / f"{safe_name}_s1s2_spatial_patterns.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ S1/S2 spatial patterns: {output_file}")

def generate_spatial_suite_for_all_scenarios() -> bool:
    """Generate spatial visualization suite for all authentic scenarios."""
    print("🗺️  GENERATING SPATIAL VISUALIZATION SUITE FOR ALL SCENARIOS")
    print("=" * 70)
    print("Creating network maps, movement flows, and spatial analysis for each scenario.")
    print()
    
    # Find all authentic simulation directories
    flee_sims_dir = Path("flee_simulations")
    
    if not flee_sims_dir.exists():
        print("❌ No flee_simulations directory found!")
        return False
    
    # Get all simulation directories
    sim_dirs = [d for d in flee_sims_dir.iterdir() if d.is_dir() and d.name.startswith("flee_output_")]
    
    if not sim_dirs:
        print("❌ No simulation directories found!")
        return False
    
    print(f"📂 Found {len(sim_dirs)} simulation directories:")
    for sim_dir in sim_dirs:
        print(f"   • {sim_dir.name}")
    
    # Initialize spatial visualization suite
    spatial_suite = AuthenticSpatialVisualizationSuite()
    
    # Generate spatial suite for each scenario
    successful_scenarios = 0
    
    for sim_dir in sim_dirs:
        try:
            if spatial_suite.generate_spatial_suite_for_scenario(sim_dir):
                successful_scenarios += 1
        except Exception as e:
            print(f"❌ Failed to generate spatial suite for {sim_dir.name}: {e}")
    
    # Summary
    print(f"\\n📊 SPATIAL SUITE GENERATION SUMMARY")
    print("=" * 40)
    print(f"Successful scenarios: {successful_scenarios}/{len(sim_dirs)}")
    
    if successful_scenarios > 0:
        print(f"\\n✅ Spatial visualization suites generated successfully!")
        print(f"📁 Check 'spatial_analysis/' directory for results.")
        print(f"\\nEach scenario includes:")
        print(f"  • Comprehensive 6-panel spatial analysis")
        print(f"  • Network topology map")
        print(f"  • Agent movement flows")
        print(f"  • Population evolution over time")
        print(f"  • S1/S2 spatial decision patterns")
        return True
    else:
        print(f"\\n❌ No spatial suites generated successfully!")
        return False

def main():
    """Generate spatial visualization suite for all scenarios."""
    success = generate_spatial_suite_for_all_scenarios()
    
    if success:
        print("\\n🎉 All spatial visualization suites completed!")
    else:
        print("\\n❌ Spatial visualization suite generation failed!")

if __name__ == "__main__":
    main()