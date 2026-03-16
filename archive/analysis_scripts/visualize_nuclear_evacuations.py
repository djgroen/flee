#!/usr/bin/env python3
"""
Visualize Nuclear Evacuation Simulation Results

Creates comparison plots for the three topologies:
1. Ring/Circular - Evacuation zones
2. Star/Hub-and-Spoke - Central facility with radiating routes
3. Linear - Single evacuation corridor
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)


def load_results(json_file):
    """Load results from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)


def validate_aggregate_vs_individual(result):
    """Validate aggregate statistics match individual agent logs."""
    if 'agent_s2_states_by_time' not in result:
        print(f"⚠️  Warning: No individual agent data for {result['topology']}")
        return True
    
    agent_states = result['agent_s2_states_by_time']
    aggregate_s2 = result['s2_activations_by_time']
    
    # Recalculate from individual data
    recalculated_s2 = []
    for t in range(len(aggregate_s2)):
        if str(t) in agent_states:
            agents = agent_states[str(t)]
            s2_count = sum(1 for a in agents.values() if a.get('s2_active', False))
            total = len(agents)
            rate = (s2_count / total * 100) if total > 0 else 0.0
            recalculated_s2.append(rate)
        else:
            recalculated_s2.append(0.0)
    
    # Compare (allow small floating point differences)
    max_diff = max(abs(a - r) for a, r in zip(aggregate_s2, recalculated_s2))
    if max_diff > 1.0:  # More than 1% difference
        print(f"⚠️  Warning: {result['topology']} aggregate vs individual S2 rates differ by up to {max_diff:.2f}%")
        return False
    else:
        print(f"✅ {result['topology']}: Aggregate matches individual data (max diff: {max_diff:.2f}%)")
        return True


def plot_temporal_dynamics(results, output_dir):
    """Plot temporal dynamics of S2 activation and evacuation."""
    
    # Validate aggregate vs individual data
    print("\n🔍 Validating aggregate statistics against individual agent logs...")
    for result in results:
        validate_aggregate_vs_individual(result)
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    for result in results:
        topology = result['topology']
        timesteps = range(len(result['s2_activations_by_time']))
        
        # S2 activation rate over time
        axes[0].plot(timesteps, result['s2_activations_by_time'], 
                    label=topology, marker='o', markersize=4, linewidth=2)
        
        # Agents at safe zones over time
        axes[1].plot(timesteps, result['agents_at_safe_by_time'], 
                    label=topology, marker='s', markersize=4, linewidth=2)
        
        # Average cognitive pressure over time
        axes[2].plot(timesteps, result['avg_pressure_by_time'], 
                    label=topology, marker='^', markersize=4, linewidth=2)
    
    axes[0].set_ylabel('S2 Activation Rate (%)', fontsize=12)
    axes[0].set_title('System 2 Activation Over Time', fontsize=14, fontweight='bold')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].set_ylabel('Agents at Safe Zones', fontsize=12)
    axes[1].set_xlabel('Time (timesteps)', fontsize=12)
    axes[1].set_title('Evacuation Progress Over Time', fontsize=14, fontweight='bold')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    
    # Add percentage on right axis for evacuation
    ax1_twin = axes[1].twinx()
    for result in results:
        topology = result['topology']
        timesteps = range(len(result['agents_at_safe_by_time']))
        num_agents = result['num_agents']
        pct_safe = [a / num_agents * 100 for a in result['agents_at_safe_by_time']]
        ax1_twin.plot(timesteps, pct_safe, label=f'{topology} (%)', 
                      linestyle='--', alpha=0.5, linewidth=1)
    ax1_twin.set_ylabel('Evacuation Progress (%)', fontsize=10, alpha=0.7)
    ax1_twin.tick_params(axis='y', labelsize=9)
    
    axes[2].set_ylabel('Average Cognitive Pressure', fontsize=12)
    axes[2].set_xlabel('Time (timesteps)', fontsize=12)
    axes[2].set_title('Cognitive Pressure Over Time', fontsize=14, fontweight='bold')
    axes[2].legend(loc='best')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / 'nuclear_evacuation_temporal_dynamics.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_topology_comparison(results, output_dir):
    """Create comparison bar chart across topologies."""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    topologies = [r['topology'] for r in results]
    s2_rates = [r['avg_s2_rate'] for r in results]
    final_safe = [r['final_agents_at_safe_pct'] for r in results]
    max_s2 = [r['max_s2_rate'] for r in results]
    avg_pressure = [r['avg_pressure'] for r in results]
    
    # Average S2 rate
    axes[0, 0].bar(topologies, s2_rates, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[0, 0].set_ylabel('Average S2 Rate (%)', fontsize=12)
    axes[0, 0].set_title('Average System 2 Activation Rate', fontsize=13, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(s2_rates):
        axes[0, 0].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')
    
    # Final evacuation success
    axes[0, 1].bar(topologies, final_safe, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[0, 1].set_ylabel('Agents at Safe Zones (%)', fontsize=12)
    axes[0, 1].set_title('Final Evacuation Success Rate', fontsize=13, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(final_safe):
        axes[0, 1].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
    
    # Maximum S2 rate
    axes[1, 0].bar(topologies, max_s2, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[1, 0].set_ylabel('Maximum S2 Rate (%)', fontsize=12)
    axes[1, 0].set_title('Peak System 2 Activation', fontsize=13, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(max_s2):
        axes[1, 0].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')
    
    # Average cognitive pressure
    axes[1, 1].bar(topologies, avg_pressure, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[1, 1].set_ylabel('Average Cognitive Pressure', fontsize=12)
    axes[1, 1].set_title('Average Cognitive Pressure', fontsize=13, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(avg_pressure):
        axes[1, 1].text(i, v + 0.01, f'{v:.3f}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    output_file = output_dir / 'nuclear_evacuation_topology_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_network_diagrams(results, output_dir):
    """Create network diagrams from actual topology data."""
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    topology_order = ['Ring', 'Star', 'Linear']
    
    for idx, topology_name in enumerate(topology_order):
        ax = axes[idx]
        
        # Find result for this topology
        result = next((r for r in results if r['topology'] == topology_name), None)
        if not result:
            ax.text(0.5, 0.5, f'No data for {topology_name}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{topology_name} Topology', fontsize=12, fontweight='bold')
            ax.axis('off')
            continue
        
        locations = result.get('locations', [])
        routes = result.get('routes', [])
        
        if not locations or not routes:
            ax.text(0.5, 0.5, f'No topology data for {topology_name}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{topology_name} Topology', fontsize=12, fontweight='bold')
            ax.axis('off')
            continue
        
        # Normalize coordinates for better visualization
        loc_dict = {loc['name']: loc for loc in locations}
        all_x = [loc['x'] for loc in locations]
        all_y = [loc['y'] for loc in locations]
        
        if not all_x or not all_y:
            ax.text(0.5, 0.5, f'No coordinate data for {topology_name}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{topology_name} Topology', fontsize=12, fontweight='bold')
            ax.axis('off')
            continue
        
        # Calculate normalization (scale to fit in reasonable bounds)
        x_range = max(all_x) - min(all_x) if max(all_x) != min(all_x) else 1.0
        y_range = max(all_y) - min(all_y) if max(all_y) != min(all_y) else 1.0
        max_range = max(x_range, y_range, 1.0)
        
        # Draw routes first (so they're behind nodes)
        for route in routes:
            from_loc = loc_dict.get(route['from'])
            to_loc = loc_dict.get(route['to'])
            if from_loc and to_loc:
                ax.plot([from_loc['x'], to_loc['x']], 
                       [from_loc['y'], to_loc['y']], 
                       'b-', alpha=0.3, linewidth=1, zorder=1)
        
        # Draw locations
        facility_drawn = False
        safezone_drawn = False
        
        for loc in locations:
            x, y = loc['x'], loc['y']
            name = loc['name']
            conflict = loc.get('conflict', 0.0)
            
            if 'Facility' in name:
                ax.plot(x, y, 'ro', markersize=20, zorder=3, 
                       label='Facility' if not facility_drawn else '')
                ax.text(x, y - max_range * 0.05, 'Facility', 
                       ha='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
                facility_drawn = True
            elif 'SafeZone' in name:
                ax.plot(x, y, 'gs', markersize=18, zorder=3,
                       label='Safe Zone' if not safezone_drawn else '')
                # Show safe zone number if multiple
                if 'SafeZone' in name and len([l for l in locations if 'SafeZone' in l['name']]) > 1:
                    safe_num = name.replace('SafeZone', '').strip() or '1'
                    ax.text(x, y - max_range * 0.05, f'Safe{safe_num}', 
                           ha='center', fontsize=8, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
                else:
                    ax.text(x, y - max_range * 0.05, 'Safe', 
                           ha='center', fontsize=8, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
                safezone_drawn = True
            else:
                # Regular location - color by conflict level
                color_intensity = 1.0 - conflict  # Higher conflict = darker
                ax.plot(x, y, 'o', color=(color_intensity * 0.5, color_intensity * 0.5, 1.0),
                       markersize=8, zorder=2, alpha=0.7)
        
        # Set axis limits with padding
        x_margin = max_range * 0.1
        y_margin = max_range * 0.1
        ax.set_xlim(min(all_x) - x_margin, max(all_x) + x_margin)
        ax.set_ylim(min(all_y) - y_margin, max(all_y) + y_margin)
        ax.set_aspect('equal')
        ax.set_title(f'{topology_name} Topology\n({len(locations)} locations, {len(routes)} routes)', 
                    fontsize=12, fontweight='bold')
        ax.axis('off')
        if facility_drawn or safezone_drawn:
            ax.legend(loc='upper right', fontsize=8)
    
    plt.tight_layout()
    output_file = output_dir / 'nuclear_evacuation_network_diagrams.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_experience_dynamics(results, output_dir):
    """Plot temporal dynamics of experience levels."""
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    for result in results:
        topology = result['topology']
        agent_states = result.get('agent_s2_states_by_time', {})
        
        if not agent_states:
            print(f"⚠️  Warning: No agent state data for {topology}")
            continue
        
        timesteps = sorted([int(t) for t in agent_states.keys()])
        
        # Calculate experience metrics over time
        avg_experience = []
        high_exp_pct = []
        low_exp_pct = []
        
        for t in timesteps:
            states = agent_states.get(str(t), {})
            if not states:
                avg_experience.append(0.0)
                high_exp_pct.append(0.0)
                low_exp_pct.append(0.0)
                continue
            
            experience_values = [s.get('experience_index', 0.0) for s in states.values()]
            if experience_values:
                avg_exp = np.mean(experience_values)
                exp_threshold = np.median(experience_values)
                high_count = sum(1 for exp in experience_values if exp >= exp_threshold)
                low_count = len(experience_values) - high_count
                
                avg_experience.append(avg_exp)
                high_exp_pct.append(high_count / len(experience_values) * 100)
                low_exp_pct.append(low_count / len(experience_values) * 100)
            else:
                avg_experience.append(0.0)
                high_exp_pct.append(0.0)
                low_exp_pct.append(0.0)
        
        # Average experience index over time
        axes[0].plot(timesteps, avg_experience, 
                    label=topology, marker='o', markersize=4, linewidth=2)
        
        # High experience percentage over time
        axes[1].plot(timesteps, high_exp_pct, 
                    label=f'{topology} (High)', marker='s', markersize=4, linewidth=2)
        
        # Low experience percentage over time
        axes[2].plot(timesteps, low_exp_pct, 
                    label=f'{topology} (Low)', marker='^', markersize=4, linewidth=2, linestyle='--')
    
    axes[0].set_ylabel('Average Experience Index', fontsize=12)
    axes[0].set_title('Average Experience Index Over Time', fontsize=14, fontweight='bold')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].set_ylabel('High Experience Agents (%)', fontsize=12)
    axes[1].set_xlabel('Time (timesteps)', fontsize=12)
    axes[1].set_title('High Experience Agents Over Time', fontsize=14, fontweight='bold')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    axes[1].axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='50% threshold')
    
    axes[2].set_ylabel('Low Experience Agents (%)', fontsize=12)
    axes[2].set_xlabel('Time (timesteps)', fontsize=12)
    axes[2].set_title('Low Experience Agents Over Time', fontsize=14, fontweight='bold')
    axes[2].legend(loc='best')
    axes[2].grid(True, alpha=0.3)
    axes[2].axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='50% threshold')
    
    plt.tight_layout()
    output_file = output_dir / 'nuclear_evacuation_experience_dynamics.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_experience_comparison(results, output_dir):
    """Create comparison plots for experience metrics across topologies."""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    topologies = []
    avg_experience = []
    final_high_exp_pct = []
    experience_growth = []
    experience_std = []
    
    for result in results:
        topology = result['topology']
        agent_states = result.get('agent_s2_states_by_time', {})
        
        if not agent_states:
            continue
        
        timesteps = sorted([int(t) for t in agent_states.keys()])
        
        # Calculate overall metrics
        all_experience = []
        initial_experience = []
        final_experience = []
        
        for t in timesteps:
            states = agent_states.get(str(t), {})
            if states:
                exp_values = [s.get('experience_index', 0.0) for s in states.values()]
                all_experience.extend(exp_values)
                
                if t == timesteps[0]:
                    initial_experience = exp_values
                if t == timesteps[-1]:
                    final_experience = exp_values
        
        if all_experience:
            topologies.append(topology)
            avg_experience.append(np.mean(all_experience))
            experience_std.append(np.std(all_experience))
            
            # Final high experience percentage
            if final_experience:
                exp_threshold = np.median(final_experience)
                high_count = sum(1 for exp in final_experience if exp >= exp_threshold)
                final_high_exp_pct.append(high_count / len(final_experience) * 100)
            else:
                final_high_exp_pct.append(0.0)
            
            # Experience growth (final - initial)
            if initial_experience and final_experience:
                growth = np.mean(final_experience) - np.mean(initial_experience)
                experience_growth.append(growth)
            else:
                experience_growth.append(0.0)
    
    # Average experience index
    axes[0, 0].bar(topologies, avg_experience, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[0, 0].set_ylabel('Average Experience Index', fontsize=12)
    axes[0, 0].set_title('Average Experience Index', fontsize=13, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(avg_experience):
        axes[0, 0].text(i, v + 0.01, f'{v:.3f}', ha='center', fontweight='bold')
    
    # Final high experience percentage
    axes[0, 1].bar(topologies, final_high_exp_pct, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[0, 1].set_ylabel('High Experience Agents (%)', fontsize=12)
    axes[0, 1].set_title('Final High Experience Percentage', fontsize=13, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    axes[0, 1].axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    for i, v in enumerate(final_high_exp_pct):
        axes[0, 1].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
    
    # Experience growth
    axes[1, 0].bar(topologies, experience_growth, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[1, 0].set_ylabel('Experience Growth', fontsize=12)
    axes[1, 0].set_title('Experience Index Growth (Final - Initial)', fontsize=13, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    axes[1, 0].axhline(y=0, color='black', linestyle='-', linewidth=1)
    for i, v in enumerate(experience_growth):
        axes[1, 0].text(i, v + 0.005 if v >= 0 else v - 0.01, f'{v:.3f}', ha='center', fontweight='bold')
    
    # Experience standard deviation (heterogeneity)
    axes[1, 1].bar(topologies, experience_std, color=['#e74c3c', '#3498db', '#2ecc71'], alpha=0.7)
    axes[1, 1].set_ylabel('Experience Std Dev', fontsize=12)
    axes[1, 1].set_title('Experience Heterogeneity (Std Dev)', fontsize=13, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(experience_std):
        axes[1, 1].text(i, v + 0.005, f'{v:.3f}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    output_file = output_dir / 'nuclear_evacuation_experience_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_population_by_location_type(results, output_dir):
    """Plot population distribution by location type (camp, town, conflict) over time."""
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    for result in results:
        topology = result['topology']
        timesteps = range(len(result.get('population_by_type_time', [])))
        
        if 'population_by_type_time' not in result or not result['population_by_type_time']:
            print(f"⚠️  Warning: No population_by_type_time data for {topology}")
            continue
        
        pop_data = result['population_by_type_time']
        
        # Extract population by type
        camp_pop = [p.get('camp', 0) for p in pop_data]
        town_pop = [p.get('town', 0) for p in pop_data]
        conflict_pop = [p.get('conflict', 0) for p in pop_data]
        
        # Plot for this topology
        axes[0].plot(timesteps, camp_pop, label=f'{topology} (Camps)', 
                    marker='s', markersize=4, linewidth=2)
        axes[1].plot(timesteps, town_pop, label=f'{topology} (Towns)', 
                    marker='o', markersize=4, linewidth=2)
        axes[2].plot(timesteps, conflict_pop, label=f'{topology} (Conflict)', 
                    marker='*', markersize=4, linewidth=2)
    
    axes[0].set_ylabel('Population in Camps', fontsize=12, fontweight='bold')
    axes[0].set_title('Population in Safe Zones (Camps) Over Time', fontsize=14, fontweight='bold')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].set_ylabel('Population in Towns', fontsize=12, fontweight='bold')
    axes[1].set_title('Population in Intermediate Locations (Towns) Over Time', fontsize=14, fontweight='bold')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].set_ylabel('Population in Conflict Zones', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Time (timesteps)', fontsize=12)
    axes[2].set_title('Population at Facility (Conflict Zone) Over Time', fontsize=14, fontweight='bold')
    axes[2].legend(loc='best')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / 'nuclear_evacuation_population_by_type.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_capacity_and_population(results, output_dir):
    """Plot capacity and final population by location type."""
    
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    
    topologies = [r['topology'] for r in results]
    
    for idx, result in enumerate(results):
        topology = result['topology']
        locations = result['locations']
        
        # Group by type
        by_type = {'camp': [], 'town': [], 'conflict': []}
        for loc in locations:
            loc_type = loc.get('type', 'town')
            if loc_type in by_type:
                by_type[loc_type].append(loc)
        
        # Calculate capacity by type
        capacity_by_type = {}
        for loc_type, locs in by_type.items():
            total_cap = sum(loc.get('capacity', -1) for loc in locs if loc.get('capacity', -1) > 0)
            if total_cap > 0:
                capacity_by_type[loc_type] = total_cap
            else:
                capacity_by_type[loc_type] = -1  # Unlimited
        
        # Get final population by type
        final_pop_by_type = {'camp': 0, 'town': 0, 'conflict': 0}
        if 'population_by_type_time' in result and result['population_by_type_time']:
            final_pop = result['population_by_type_time'][-1]
            final_pop_by_type = {k: final_pop.get(k, 0) for k in final_pop_by_type.keys()}
        
        # Plot 1: Capacity by type
        types = [t for t in capacity_by_type.keys() if capacity_by_type[t] > 0]
        caps = [capacity_by_type[t] for t in types]
        colors_map = {'camp': '#2ecc71', 'town': '#95a5a6', 'conflict': '#e74c3c'}
        
        if caps:
            bars1 = axes[0, idx].bar(types, caps, 
                                    color=[colors_map.get(t, '#3498db') for t in types],
                                    alpha=0.7, edgecolor='black', linewidth=2)
            axes[0, idx].set_ylabel('Total Capacity', fontsize=11, fontweight='bold')
            axes[0, idx].set_title(f'{topology}: Capacity by Type', fontsize=12, fontweight='bold')
            axes[0, idx].set_xticklabels([t.capitalize() for t in types], fontsize=10)
            axes[0, idx].grid(True, alpha=0.3, axis='y')
            
            for bar in bars1:
                height = bar.get_height()
                axes[0, idx].text(bar.get_x() + bar.get_width()/2., height,
                                f'{int(height):,}', ha='center', va='bottom', fontweight='bold')
        else:
            axes[0, idx].text(0.5, 0.5, 'Unlimited\ncapacity', 
                            ha='center', va='center', fontsize=12, transform=axes[0, idx].transAxes)
            axes[0, idx].set_title(f'{topology}: Capacity by Type', fontsize=12, fontweight='bold')
        
        # Plot 2: Final population by type
        types_pop = list(final_pop_by_type.keys())
        pops = [final_pop_by_type[t] for t in types_pop]
        
        bars2 = axes[1, idx].bar(types_pop, pops,
                                color=[colors_map.get(t, '#3498db') for t in types_pop],
                                alpha=0.7, edgecolor='black', linewidth=2)
        axes[1, idx].set_ylabel('Final Population', fontsize=11, fontweight='bold')
        axes[1, idx].set_title(f'{topology}: Final Population by Type', fontsize=12, fontweight='bold')
        axes[1, idx].set_xticklabels([t.capitalize() for t in types_pop], fontsize=10)
        axes[1, idx].grid(True, alpha=0.3, axis='y')
        
        for bar in bars2:
            height = bar.get_height()
            axes[1, idx].text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    plt.suptitle('Capacity and Population by Location Type', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_file = output_dir / 'nuclear_evacuation_capacity_and_population.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def main():
    """Main visualization function."""
    
    output_dir = Path("nuclear_evacuation_results")
    output_dir.mkdir(exist_ok=True)
    
    # Find most recent JSON results file
    json_files = list(output_dir.glob("nuclear_evacuation_detailed_*.json"))
    if not json_files:
        print("❌ No results files found. Run nuclear_evacuation_simulations.py first.")
        return
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading results from: {latest_file}")
    
    results = load_results(latest_file)
    
    print(f"\n📊 Generating visualizations...")
    plot_temporal_dynamics(results, output_dir)
    plot_topology_comparison(results, output_dir)
    plot_network_diagrams(results, output_dir)
    plot_experience_dynamics(results, output_dir)
    plot_experience_comparison(results, output_dir)
    plot_population_by_location_type(results, output_dir)
    plot_capacity_and_population(results, output_dir)
    
    print(f"\n✅ All visualizations saved to: {output_dir}")


if __name__ == "__main__":
    main()

