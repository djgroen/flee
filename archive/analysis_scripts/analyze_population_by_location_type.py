#!/usr/bin/env python3
"""
Analyze Population Distribution by Location Type

Shows:
1. Population in camps vs towns vs conflict zones
2. Capacity of each location type
3. Population density (population / capacity)
4. Temporal evolution of population by type
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
from collections import defaultdict

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)


def load_agent_logs(agent_log_file):
    """Load agent logs and extract location populations."""
    if not agent_log_file or not Path(agent_log_file).exists():
        return None
    
    try:
        # Read agent log file
        df = pd.read_csv(agent_log_file, sep=' ', skipinitialspace=True)
        
        # Agent log format: time agent_id location x y ...
        # Group by time and location to count population
        if 'location' in df.columns and 'time' in df.columns:
            pop_by_time_location = df.groupby(['time', 'location']).size().reset_index(name='population')
            return pop_by_time_location
        else:
            print(f"⚠️  Warning: Agent log format unexpected. Columns: {df.columns.tolist()}")
            return None
    except Exception as e:
        print(f"⚠️  Warning: Could not load agent logs: {e}")
        return None


def analyze_population_by_type(results_file, output_dir):
    """Analyze population distribution by location type."""
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Process each topology
    for result in results:
        topology = result['topology']
        locations = result['locations']
        agent_log_file = result.get('agent_logs_file')
        
        print(f"\n📊 Analyzing {topology} topology...")
        
        # Group locations by type
        locations_by_type = defaultdict(list)
        for loc in locations:
            loc_type = loc.get('type', 'town')
            locations_by_type[loc_type].append({
                'name': loc['name'],
                'capacity': loc.get('capacity', -1),
                'conflict': loc.get('conflict', 0.0)
            })
        
        # Load agent logs to get population
        agent_data = load_agent_logs(agent_log_file)
        
        if agent_data is not None:
            # Get final timestep
            final_time = agent_data['time'].max()
            final_pop = agent_data[agent_data['time'] == final_time]
            
            # Map locations to types
            loc_to_type = {}
            for loc_type, locs in locations_by_type.items():
                for loc in locs:
                    loc_to_type[loc['name']] = loc_type
            
            # Calculate population by type
            pop_by_type = defaultdict(int)
            capacity_by_type = defaultdict(int)
            
            for _, row in final_pop.iterrows():
                loc_name = row['location']
                pop = row['population']
                loc_type = loc_to_type.get(loc_name, 'unknown')
                pop_by_type[loc_type] += pop
            
            # Calculate capacity by type
            for loc_type, locs in locations_by_type.items():
                for loc in locs:
                    cap = loc['capacity']
                    if cap > 0:
                        capacity_by_type[loc_type] += cap
                    else:
                        capacity_by_type[loc_type] = -1  # Unlimited
            
            print(f"  Final population by type:")
            for loc_type in sorted(pop_by_type.keys()):
                pop = pop_by_type[loc_type]
                cap = capacity_by_type[loc_type]
                cap_str = f"{cap:,}" if cap > 0 else "unlimited"
                print(f"    {loc_type}: {pop} agents (capacity: {cap_str})")
            
            # Create temporal plot
            create_temporal_population_plot(agent_data, locations_by_type, loc_to_type, 
                                          topology, output_dir)
        
        # Create capacity comparison plot
        create_capacity_comparison_plot(locations_by_type, topology, output_dir)
    
    print(f"\n✅ Analysis complete. Plots saved to: {output_dir}")


def create_temporal_population_plot(agent_data, locations_by_type, loc_to_type, 
                                   topology, output_dir):
    """Create plot showing population over time by location type."""
    
    # Calculate population by type for each timestep
    times = sorted(agent_data['time'].unique())
    pop_by_type_time = defaultdict(list)
    
    for t in times:
        t_data = agent_data[agent_data['time'] == t]
        pop_by_type_t = defaultdict(int)
        
        for _, row in t_data.iterrows():
            loc_name = row['location']
            pop = row['population']
            loc_type = loc_to_type.get(loc_name, 'unknown')
            pop_by_type_t[loc_type] += pop
        
        for loc_type in ['camp', 'town', 'conflict']:
            pop_by_type_time[loc_type].append(pop_by_type_t.get(loc_type, 0))
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for loc_type, color, label in [
        ('camp', '#2ecc71', 'Safe Zones (Camps)'),
        ('town', '#95a5a6', 'Towns (Intermediate)'),
        ('conflict', '#e74c3c', 'Facility (Conflict)')
    ]:
        if loc_type in pop_by_type_time:
            ax.plot(times, pop_by_type_time[loc_type], 
                   color=color, linewidth=2.5, label=label, marker='o', markersize=4)
    
    ax.set_xlabel('Time (timesteps)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Population', fontsize=12, fontweight='bold')
    ax.set_title(f'{topology} Topology: Population by Location Type Over Time', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / f'{topology.lower()}_population_by_type_temporal.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  📊 Saved: {output_file.name}")


def create_capacity_comparison_plot(locations_by_type, topology, output_dir):
    """Create plot comparing capacity across location types."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Number of locations by type
    type_counts = {loc_type: len(locs) for loc_type, locs in locations_by_type.items()}
    colors = {'camp': '#2ecc71', 'town': '#95a5a6', 'conflict': '#e74c3c'}
    
    bars1 = ax1.bar(type_counts.keys(), type_counts.values(), 
                    color=[colors.get(t, '#3498db') for t in type_counts.keys()],
                    alpha=0.7, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Number of Locations', fontsize=11, fontweight='bold')
    ax1.set_title('Number of Locations by Type', fontsize=12, fontweight='bold')
    ax1.set_xticklabels([t.capitalize() for t in type_counts.keys()], fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    # Plot 2: Total capacity by type
    capacity_by_type = {}
    for loc_type, locs in locations_by_type.items():
        total_cap = sum(loc['capacity'] for loc in locs if loc['capacity'] > 0)
        if total_cap > 0:
            capacity_by_type[loc_type] = total_cap
        else:
            capacity_by_type[loc_type] = -1  # Unlimited
    
    # Filter out unlimited
    finite_capacity = {k: v for k, v in capacity_by_type.items() if v > 0}
    
    if finite_capacity:
        bars2 = ax2.bar(finite_capacity.keys(), finite_capacity.values(),
                       color=[colors.get(t, '#3498db') for t in finite_capacity.keys()],
                       alpha=0.7, edgecolor='black', linewidth=2)
        ax2.set_ylabel('Total Capacity', fontsize=11, fontweight='bold')
        ax2.set_title('Total Capacity by Location Type', fontsize=12, fontweight='bold')
        ax2.set_xticklabels([t.capitalize() for t in finite_capacity.keys()], fontsize=10)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}', ha='center', va='bottom', fontweight='bold')
    else:
        ax2.text(0.5, 0.5, 'All locations have\nunlimited capacity', 
                ha='center', va='center', fontsize=12, transform=ax2.transAxes)
        ax2.set_title('Total Capacity by Location Type', fontsize=12, fontweight='bold')
    
    plt.suptitle(f'{topology} Topology: Location Type Analysis', 
                fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_file = output_dir / f'{topology.lower()}_location_type_capacity.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  📊 Saved: {output_file.name}")


if __name__ == "__main__":
    results_dir = Path("nuclear_evacuation_results")
    
    # Find latest results
    result_files = sorted(results_dir.glob("nuclear_evacuation_detailed_*.json"))
    if not result_files:
        print("❌ No results files found!")
        exit(1)
    
    latest = result_files[-1]
    print(f"📂 Loading results from: {latest.name}")
    
    analyze_population_by_type(latest, results_dir)


