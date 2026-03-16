#!/usr/bin/env python3
"""
Dimensionless Parameter Analysis for Refugee Simulations

Creates plots showing:
1. Dimensionless parameters (normalized distances, speeds, times)
2. Heuristic decision-making patterns (S1 vs S2)
3. Generalizability across different scales

This demonstrates that the model works across different spatial/temporal scales.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

plt.rcParams['figure.figsize'] = (14, 10)

# Optional seaborn for styling
try:
    import seaborn as sns
    sns.set_style("whitegrid")
except:
    pass


def load_scenario_results(scenario_dir):
    """Load results from a scenario directory."""
    result_files = sorted(scenario_dir.glob("*_results.json"))
    if not result_files:
        return None
    
    latest = result_files[-1]
    with open(latest, 'r') as f:
        return json.load(f)


def calculate_dimensionless_parameters(results):
    """Calculate dimensionless parameters from simulation results."""
    locations = results.get('locations', [])
    routes = results.get('routes', [])
    metrics = results.get('metrics', {})
    timesteps = metrics.get('timesteps', [])
    
    # Characteristic scales
    D_char = 100.0  # Characteristic distance (units)
    T_char = 10.0   # Characteristic time (timesteps)
    v_char = D_char / T_char  # Characteristic speed = 10 units/timestep
    
    # Calculate distances
    distances = []
    route_distances = []
    for route in routes:
        dist = route.get('distance', 0)
        if dist > 0:
            route_distances.append(dist)
            distances.append(dist / D_char)  # Normalized distance
    
    # Calculate speeds (from agent movement data)
    # Use max_move_speed from config or estimate from distances/times
    max_speed = 20.0  # units/timestep (from config)
    normalized_speed = max_speed / v_char  # Should be ~2.0
    
    # Calculate times (from simulation)
    if timesteps:
        total_time = max(timesteps)
        normalized_time = total_time / T_char
    else:
        normalized_time = 0
    
    # Calculate evacuation rates (dimensionless)
    num_agents = results.get('num_agents', 500)
    pop_by_location = metrics.get('population_by_location', {})
    
    # Find safe zones (camps/borders)
    safe_zones = [loc['name'] for loc in locations if loc.get('type') == 'camp']
    
    # Calculate final evacuation rate
    final_evac = 0
    for safe_zone in safe_zones:
        if safe_zone in pop_by_location:
            pops = pop_by_location[safe_zone]
            if pops:
                final_evac += pops[-1]
    
    evacuation_rate = final_evac / num_agents if num_agents > 0 else 0.0
    
    return {
        'normalized_distances': distances,
        'normalized_speed': normalized_speed,
        'normalized_time': normalized_time,
        'evacuation_rate': evacuation_rate,
        'route_distances': route_distances,
        'D_char': D_char,
        'T_char': T_char,
        'v_char': v_char,
    }


def plot_dimensionless_parameters(results_dir="data/refugee", output_file=None):
    """Create dimensionless parameter analysis plot."""
    results_dir = Path(results_dir)
    
    if output_file is None:
        output_file = results_dir / "figures" / "dimensionless_parameters.png"
    else:
        output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Find latest runs
    import glob
    import os
    
    scenario_types = ['Nearest_Border', 'Multiple_Routes', 'Social_Connections', 'Context_Transition']
    scenarios = []
    
    for scenario_type in scenario_types:
        runs = sorted(glob.glob(str(results_dir / f'run_{scenario_type}_*')), 
                     key=os.path.getmtime, reverse=True)
        if runs:
            scenario_dir = Path(runs[0])
            results = load_scenario_results(scenario_dir)
            if results:
                scenarios.append({
                    'name': scenario_type.replace('_', ' '),
                    'results': results,
                    'dir': scenario_dir
                })
    
    if not scenarios:
        print("❌ No scenarios found")
        return False
    
    # Calculate dimensionless parameters for each scenario
    dim_params = []
    for scenario in scenarios:
        params = calculate_dimensionless_parameters(scenario['results'])
        params['scenario'] = scenario['name']
        dim_params.append(params)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Normalized distances (all routes)
    ax = axes[0, 0]
    all_distances = []
    scenario_names = []
    for params in dim_params:
        distances = params['normalized_distances']
        all_distances.extend(distances)
        scenario_names.extend([params['scenario']] * len(distances))
    
    if all_distances:
        ax.hist(all_distances, bins=20, alpha=0.7, edgecolor='black', color='#3498db')
        ax.axvline(1.0, color='red', linestyle='--', linewidth=2, label='D_char = 1.0')
        ax.set_xlabel('Normalized Distance (d/D_char)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title('Normalized Route Distances', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # 2. Normalized speeds
    ax = axes[0, 1]
    speeds = [p['normalized_speed'] for p in dim_params]
    scenario_labels = [p['scenario'] for p in dim_params]
    
    bars = ax.bar(range(len(speeds)), speeds, color='#2ecc71', alpha=0.7, edgecolor='black')
    ax.axhline(1.0, color='red', linestyle='--', linewidth=2, label='v_char = 1.0')
    ax.set_xticks(range(len(speeds)))
    ax.set_xticklabels(scenario_labels, rotation=45, ha='right')
    ax.set_ylabel('Normalized Speed (v/v_char)', fontsize=12, fontweight='bold')
    ax.set_title('Normalized Movement Speeds', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 3. Normalized time vs evacuation rate
    ax = axes[1, 0]
    times = [p['normalized_time'] for p in dim_params]
    evac_rates = [p['evacuation_rate'] for p in dim_params]
    scenario_labels = [p['scenario'] for p in dim_params]
    
    scatter = ax.scatter(times, evac_rates, s=200, alpha=0.7, c=range(len(times)), 
                        cmap='viridis', edgecolors='black', linewidths=2)
    for i, label in enumerate(scenario_labels):
        ax.annotate(label, (times[i], evac_rates[i]), 
                   xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    ax.set_xlabel('Normalized Time (t/T_char)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Evacuation Rate', fontsize=12, fontweight='bold')
    ax.set_title('Evacuation Rate vs Normalized Time', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # 4. Dimensionless parameter summary table
    ax = axes[1, 1]
    ax.axis('off')
    
    # Create summary table
    table_data = []
    for params in dim_params:
        avg_dist = np.mean(params['normalized_distances']) if params['normalized_distances'] else 0
        table_data.append([
            params['scenario'],
            f"{avg_dist:.2f}",
            f"{params['normalized_speed']:.2f}",
            f"{params['normalized_time']:.2f}",
            f"{params['evacuation_rate']:.2%}"
        ])
    
    table = ax.table(cellText=table_data,
                    colLabels=['Scenario', 'Avg d/D_char', 'v/v_char', 't/T_char', 'Evac Rate'],
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style header
    for i in range(5):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax.set_title('Dimensionless Parameter Summary', fontsize=14, fontweight='bold', pad=20)
    
    plt.suptitle('Dimensionless Parameter Analysis: Generalizability Across Scales', 
                fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Dimensionless parameters plot saved: {output_file}")
    return True


def plot_heuristic_decision_making(results_dir="data/refugee", output_file=None):
    """Create heuristic decision-making analysis plot."""
    results_dir = Path(results_dir)
    
    if output_file is None:
        output_file = results_dir / "figures" / "heuristic_decision_making.png"
    else:
        output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Find latest runs
    import glob
    import os
    
    scenario_types = ['Nearest_Border', 'Multiple_Routes', 'Social_Connections', 'Context_Transition']
    scenarios = []
    
    for scenario_type in scenario_types:
        runs = sorted(glob.glob(str(results_dir / f'run_{scenario_type}_*')), 
                     key=os.path.getmtime, reverse=True)
        if runs:
            scenario_dir = Path(runs[0])
            results = load_scenario_results(scenario_dir)
            if results:
                scenarios.append({
                    'name': scenario_type.replace('_', ' '),
                    'results': results,
                })
    
    if not scenarios:
        print("❌ No scenarios found")
        return False
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. S2 activation by conflict level
    ax = axes[0, 0]
    conflict_levels = []
    s2_rates = []
    scenario_names = []
    
    for scenario in scenarios:
        results = scenario['results']
        locations = results.get('locations', [])
        metrics = results.get('metrics', {})
        s2_by_location = metrics.get('s2_activation_by_location', {})
        
        for loc in locations:
            loc_name = loc['name']
            conflict = loc.get('conflict', 0.0)
            if loc_name in s2_by_location and len(s2_by_location[loc_name]) > 0:
                # Use average S2 rate
                avg_s2 = np.mean(s2_by_location[loc_name])
                conflict_levels.append(conflict)
                s2_rates.append(avg_s2)
                scenario_names.append(scenario['name'])
    
    if conflict_levels:
        scatter = ax.scatter(conflict_levels, s2_rates, s=150, alpha=0.7, 
                           c=range(len(conflict_levels)), cmap='coolwarm',
                           edgecolors='black', linewidths=1.5)
        ax.set_xlabel('Conflict Level', fontsize=12, fontweight='bold')
        ax.set_ylabel('S2 Activation Rate', fontsize=12, fontweight='bold')
        ax.set_title('S2 Activation vs Conflict Level', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, 1.1)
    
    # 2. Route choice heuristics (S1 vs S2)
    ax = axes[0, 1]
    route_choices_data = []
    
    for scenario in scenarios:
        metrics = scenario['results'].get('metrics', {})
        route_choices = metrics.get('route_choices', {})
        
        for dest, data in route_choices.items():
            s1_count = data.get('S1', 0)
            s2_count = data.get('S2', 0)
            total = data.get('total', 0)
            if total > 0:
                route_choices_data.append({
                    'scenario': scenario['name'],
                    'destination': dest,
                    's1_pct': s1_count / total,
                    's2_pct': s2_count / total,
                    'total': total
                })
    
    if route_choices_data:
        destinations = [f"{d['scenario']}\n{d['destination']}" for d in route_choices_data]
        s1_pcts = [d['s1_pct'] * 100 for d in route_choices_data]
        s2_pcts = [d['s2_pct'] * 100 for d in route_choices_data]
        
        x = np.arange(len(destinations))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, s1_pcts, width, label='System 1', color='#e74c3c', alpha=0.7, edgecolor='black')
        bars2 = ax.bar(x + width/2, s2_pcts, width, label='System 2', color='#3498db', alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Route Choice', fontsize=12, fontweight='bold')
        ax.set_ylabel('Percentage of Agents (%)', fontsize=12, fontweight='bold')
        ax.set_title('Route Choice Heuristics: S1 vs S2', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(destinations, rotation=45, ha='right', fontsize=9)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 105)
    
    # 3. S2 activation over time (context transition)
    ax = axes[1, 0]
    for scenario in scenarios:
        if 'Context Transition' in scenario['name']:
            metrics = scenario['results'].get('metrics', {})
            timesteps = metrics.get('timesteps', [])
            s2_by_location = metrics.get('s2_activation_by_location', {})
            
            # Plot S2 rate for each location over time
            for loc_name, s2_rates in s2_by_location.items():
                if len(s2_rates) == len(timesteps):
                    ax.plot(timesteps, [r * 100 for r in s2_rates], 
                           label=loc_name, marker='o', markersize=4, linewidth=2)
            
            break
    
    ax.set_xlabel('Time (timesteps)', fontsize=12, fontweight='bold')
    ax.set_ylabel('S2 Activation Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Context Transition: S1 → S2 Over Time', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # 4. Heuristic summary: Decision-making patterns
    ax = axes[1, 1]
    ax.axis('off')
    
    # Create heuristic summary
    heuristic_text = """
    System 1 (Heuristic) Decision-Making:
    • Fast, automatic processing
    • Chooses nearest/shortest route
    • Dominant in high conflict (c > 0.5)
    • Low cognitive effort required
    
    System 2 (Deliberative) Decision-Making:
    • Slow, analytical processing
    • Compares routes, optimizes safety
    • Activated in low conflict (c < 0.3)
    • Requires cognitive capacity + opportunity
    
    Key Insight:
    Context-dependent processing:
    High conflict → S1 (survival mode)
    Low conflict → S2 (planning mode)
    """
    
    ax.text(0.1, 0.5, heuristic_text, fontsize=11, 
           verticalalignment='center', family='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax.set_title('Heuristic Decision-Making Summary', fontsize=14, fontweight='bold')
    
    plt.suptitle('Heuristic Decision-Making Patterns: Dual-Process Model', 
                fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Heuristic decision-making plot saved: {output_file}")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create dimensionless parameter and heuristic analysis plots")
    parser.add_argument("--results-dir", type=str, default="data/refugee",
                      help="Results directory")
    parser.add_argument("--type", type=str, choices=['dimensionless', 'heuristics', 'all'],
                       default='all', help="Type of plot to create")
    
    args = parser.parse_args()
    
    if args.type in ['dimensionless', 'all']:
        plot_dimensionless_parameters(args.results_dir)
    
    if args.type in ['heuristics', 'all']:
        plot_heuristic_decision_making(args.results_dir)
    
    print("\n✅ All analysis plots complete!")

