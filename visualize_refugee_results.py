#!/usr/bin/env python3
"""
Refugee Simulation Results Visualization

Creates static plots and analysis for refugee scenarios:
- Network diagrams
- Decision analysis (route choices, S1 vs S2)
- Connection effects on S2 activation
- Context-dependent processing evidence
- Summary comparison across scenarios

Separate from nuclear visualizations - designed for refugee scenarios.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
from collections import defaultdict

# Optional seaborn for styling (skip if there are compatibility issues)
_seaborn_available = False
try:
    import seaborn as sns
    sns.set_style("whitegrid")
    _seaborn_available = True
except (ImportError, ValueError, Exception):
    # Skip seaborn if there are any issues (numpy/scipy compatibility, etc.)
    pass

plt.rcParams['figure.figsize'] = (14, 10)


def load_scenario_results(scenario_dir):
    """Load results from a scenario directory."""
    result_files = sorted(scenario_dir.glob("*_results.json"))
    if not result_files:
        return None
    
    latest = result_files[-1]
    with open(latest, 'r') as f:
        return json.load(f)


def plot_network_diagram(scenario_dir, scenario_name, output_file):
    """Create network diagram for a scenario."""
    results = load_scenario_results(scenario_dir)
    if not results:
        return False
    
    locations = results.get('locations', [])
    routes = results.get('routes', [])
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Color scheme
    colors = {
        'camp': '#2ecc71',  # Green
        'conflict': '#c0392b',  # Dark red
        'town': '#95a5a6',  # Gray
        'route': '#34495e',  # Dark gray
    }
    
    # Draw routes
    location_dict = {loc['name']: loc for loc in locations}
    for route in routes:
        from_loc = location_dict.get(route['from'])
        to_loc = location_dict.get(route['to'])
        if from_loc and to_loc:
            ax.plot([from_loc['x'], to_loc['x']], 
                   [from_loc['y'], to_loc['y']], 
                   color=colors['route'], linewidth=2, alpha=0.4, zorder=1)
    
    # Draw locations
    for loc in locations:
        x, y = loc['x'], loc['y']
        loc_type = loc.get('type', 'town')
        conflict = loc.get('conflict', 0.0)
        
        if loc_type == 'camp':
            color = colors['camp']
            marker = 's'
            size = 600
            edgecolor = 'darkgreen'
            linewidth = 3
        elif loc_type == 'conflict':
            color = colors['conflict']
            marker = '*'
            size = 600
            edgecolor = 'darkred'
            linewidth = 3
        else:
            color = colors['town']
            marker = 'o'
            size = 300
            edgecolor = '#7f8c8d'
            linewidth = 1.5
        
        ax.scatter(x, y, s=size, marker=marker, c=color,
                  edgecolors=edgecolor, linewidths=linewidth, zorder=2)
        
        # Add label with conflict level
        label = loc['name']
        if conflict > 0:
            label += f'\n(c={conflict:.1f})'
        ax.text(x, y + 12, label, ha='center', va='bottom',
               fontsize=9, fontweight='bold' if loc_type in ['camp', 'conflict'] else 'normal')
    
    # Set limits
    if locations:
        all_x = [loc['x'] for loc in locations]
        all_y = [loc['y'] for loc in locations]
        x_margin = (max(all_x) - min(all_x)) * 0.2
        y_margin = (max(all_y) - min(all_y)) * 0.2
        ax.set_xlim(min(all_x) - x_margin, max(all_x) + x_margin)
        ax.set_ylim(min(all_y) - y_margin, max(all_y) + y_margin)
    
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'{scenario_name}\nNetwork Topology', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Network diagram saved: {output_file}")
    return True


def plot_decision_analysis(scenario_dir, scenario_name, output_file):
    """Plot decision analysis: route choices, S1 vs S2."""
    results = load_scenario_results(scenario_dir)
    if not results:
        return False
    
    metrics = results.get('metrics', {})
    route_choices = metrics.get('route_choices', {})
    s2_by_location = metrics.get('s2_activation_by_location', {})
    timesteps = metrics.get('timesteps', [])
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Route choices (if applicable)
    if route_choices:
        ax = axes[0, 0]
        destinations = list(route_choices.keys())
        s1_counts = [route_choices[d].get('S1', 0) for d in destinations]
        s2_counts = [route_choices[d].get('S2', 0) for d in destinations]
        
        x = np.arange(len(destinations))
        width = 0.35
        
        ax.bar(x - width/2, s1_counts, width, label='System 1', color='#e74c3c', alpha=0.7)
        ax.bar(x + width/2, s2_counts, width, label='System 2', color='#3498db', alpha=0.7)
        
        ax.set_xlabel('Destination')
        ax.set_ylabel('Number of Agents')
        ax.set_title('Route Choices by Cognitive State')
        ax.set_xticks(x)
        ax.set_xticklabels(destinations, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        axes[0, 0].text(0.5, 0.5, 'No route choice data', 
                        ha='center', va='center', transform=axes[0, 0].transAxes)
        axes[0, 0].axis('off')
    
    # 2. S2 activation by location over time
    ax = axes[0, 1]
    for loc_name, s2_rates in s2_by_location.items():
        if len(s2_rates) == len(timesteps):
            ax.plot(timesteps, [r * 100 for r in s2_rates], 
                   label=loc_name, marker='o', markersize=3, linewidth=2)
    
    ax.set_xlabel('Time (timesteps)')
    ax.set_ylabel('S2 Activation Rate (%)')
    ax.set_title('S2 Activation by Location Over Time')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # 3. Population by location type
    ax = axes[1, 0]
    pop_by_type = metrics.get('population_by_type', {})
    if pop_by_type and timesteps:
        # Get time series data
        type_data = defaultdict(list)
        for t in timesteps:
            # Get population at this timestep (approximate from final)
            # This is simplified - ideally we'd track over time
            pass
        
        # For now, show final distribution
        types = ['conflict', 'town', 'camp']
        final_pops = []
        for t in types:
            # Get from population_by_location
            total = 0
            locations = results.get('locations', [])
            for loc in locations:
                if loc.get('type') == t:
                    loc_name = loc['name']
                    if loc_name in metrics.get('population_by_location', {}):
                        pops = metrics['population_by_location'][loc_name]
                        if pops:
                            total += pops[-1]
            final_pops.append(total)
        
        ax.bar(types, final_pops, color=['#c0392b', '#95a5a6', '#2ecc71'], alpha=0.7)
        ax.set_ylabel('Population')
        ax.set_title('Final Population by Location Type')
        ax.grid(True, alpha=0.3)
    else:
        axes[1, 0].text(0.5, 0.5, 'No population data', 
                        ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 0].axis('off')
    
    # 4. Connection statistics
    ax = axes[1, 1]
    conn_stats = metrics.get('connection_stats', {})
    if conn_stats:
        times = sorted(conn_stats.keys())
        means = [conn_stats[t]['mean'] for t in times]
        stds = [conn_stats[t]['std'] for t in times]
        
        ax.plot(times, means, marker='o', linewidth=2, label='Mean', color='#3498db')
        ax.fill_between(times, 
                        [m - s for m, s in zip(means, stds)],
                        [m + s for m, s in zip(means, stds)],
                        alpha=0.3, color='#3498db', label='±1 SD')
        
        ax.set_xlabel('Time (timesteps)')
        ax.set_ylabel('Connections')
        ax.set_title('Social Connections Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        axes[1, 1].text(0.5, 0.5, 'No connection data', 
                        ha='center', va='center', transform=axes[1, 1].transAxes)
        axes[1, 1].axis('off')
    
    plt.suptitle(f'{scenario_name}: Decision Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Decision analysis saved: {output_file}")
    return True


def plot_summary_comparison(results_dir="refugee_simulation_results", output_file=None):
    """Create summary comparison across all scenarios."""
    results_dir = Path(results_dir)
    
    if output_file is None:
        output_file = results_dir / "refugee_scenarios_summary_comparison.png"
    
    # Load all scenarios
    scenario_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
    scenarios = []
    
    for scenario_dir in scenario_dirs:
        results = load_scenario_results(scenario_dir)
        if results:
            scenarios.append({
                'name': scenario_dir.name.replace('_', ' '),
                'results': results
            })
    
    if not scenarios:
        print("❌ No scenarios found")
        return False
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Average S2 activation by scenario
    ax = axes[0, 0]
    scenario_names = []
    avg_s2_rates = []
    
    for scenario in scenarios:
        metrics = scenario['results'].get('metrics', {})
        s2_by_location = metrics.get('s2_activation_by_location', {})
        
        # Calculate overall average
        all_rates = []
        for loc_name, rates in s2_by_location.items():
            all_rates.extend(rates)
        
        avg_s2 = np.mean(all_rates) * 100 if all_rates else 0.0
        scenario_names.append(scenario['name'])
        avg_s2_rates.append(avg_s2)
    
    bars = ax.barh(scenario_names, avg_s2_rates, color='#3498db', alpha=0.7)
    ax.set_xlabel('Average S2 Activation Rate (%)')
    ax.set_title('Average S2 Activation by Scenario')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, avg_s2_rates)):
        ax.text(val + 1, i, f'{val:.1f}%', va='center', fontweight='bold')
    
    # 2. Final evacuation success
    ax = axes[0, 1]
    final_evac_rates = []
    
    for scenario in scenarios:
        metrics = scenario['results'].get('metrics', {})
        pop_by_type = metrics.get('population_by_type', {})
        # Get final population in camps
        locations = scenario['results'].get('locations', [])
        camp_names = [loc['name'] for loc in locations if loc.get('type') == 'camp']
        
        total_in_camps = 0
        for camp_name in camp_names:
            if camp_name in metrics.get('population_by_location', {}):
                pops = metrics['population_by_location'][camp_name]
                if pops:
                    total_in_camps += pops[-1]
        
        num_agents = scenario['results'].get('num_agents', 500)
        evac_rate = (total_in_camps / num_agents * 100) if num_agents > 0 else 0.0
        final_evac_rates.append(evac_rate)
    
    bars = ax.barh(scenario_names, final_evac_rates, color='#2ecc71', alpha=0.7)
    ax.set_xlabel('Evacuation Success Rate (%)')
    ax.set_title('Final Evacuation Success')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, final_evac_rates)):
        ax.text(val + 1, i, f'{val:.1f}%', va='center', fontweight='bold')
    
    # 3. Peak S2 activation
    ax = axes[1, 0]
    peak_s2_rates = []
    
    for scenario in scenarios:
        metrics = scenario['results'].get('metrics', {})
        s2_by_location = metrics.get('s2_activation_by_location', {})
        
        peak = 0.0
        for loc_name, rates in s2_by_location.items():
            if rates:
                peak = max(peak, max(rates) * 100)
        
        peak_s2_rates.append(peak)
    
    bars = ax.barh(scenario_names, peak_s2_rates, color='#9b59b6', alpha=0.7)
    ax.set_xlabel('Peak S2 Activation Rate (%)')
    ax.set_title('Peak S2 Activation by Scenario')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, peak_s2_rates)):
        ax.text(val + 1, i, f'{val:.1f}%', va='center', fontweight='bold')
    
    # 4. Average connections
    ax = axes[1, 1]
    avg_connections = []
    
    for scenario in scenarios:
        metrics = scenario['results'].get('metrics', {})
        conn_stats = metrics.get('connection_stats', {})
        
        if conn_stats:
            means = [conn_stats[t]['mean'] for t in sorted(conn_stats.keys())]
            avg_conn = np.mean(means) if means else 0.0
        else:
            avg_conn = 0.0
        
        avg_connections.append(avg_conn)
    
    bars = ax.barh(scenario_names, avg_connections, color='#e67e22', alpha=0.7)
    ax.set_xlabel('Average Connections')
    ax.set_title('Average Social Connections by Scenario')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, avg_connections)):
        ax.text(val + 0.1, i, f'{val:.2f}', va='center', fontweight='bold')
    
    plt.suptitle('Refugee Scenarios: Summary Comparison', fontsize=18, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Summary comparison saved: {output_file}")
    return True


def create_all_visualizations(results_dir="refugee_simulation_results"):
    """Create all visualizations for all scenarios."""
    results_dir = Path(results_dir)
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    # Find all scenario directories (only run_* directories)
    scenario_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('run_')]
    
    if not scenario_dirs:
        print(f"❌ No scenario directories found in {results_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"Creating visualizations for {len(scenario_dirs)} scenarios")
    print(f"{'='*60}")
    
    # Create output directory for figures
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    # Create visualizations for each scenario
    for scenario_dir in scenario_dirs:
        scenario_name = scenario_dir.name.replace('_', ' ')
        print(f"\n📊 Processing: {scenario_name}")
        
        # Network diagram
        network_file = figures_dir / f"{scenario_name.replace(' ', '_')}_network.png"
        plot_network_diagram(scenario_dir, scenario_name, network_file)
        
        # Decision analysis
        decision_file = figures_dir / f"{scenario_name.replace(' ', '_')}_decisions.png"
        plot_decision_analysis(scenario_dir, scenario_name, decision_file)
    
    # Summary comparison
    print(f"\n📊 Creating summary comparison...")
    summary_file = figures_dir / "summary_comparison.png"
    plot_summary_comparison(results_dir, summary_file)
    
    print(f"\n{'='*60}")
    print(f"All visualizations complete!")
    print(f"Figures saved to: {figures_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create refugee simulation visualizations")
    parser.add_argument("--results-dir", type=str, default="refugee_simulation_results",
                      help="Results directory")
    parser.add_argument("--scenario", type=str, help="Specific scenario directory name")
    parser.add_argument("--type", type=str, choices=['network', 'decisions', 'summary', 'all'],
                       default='all', help="Type of visualization")
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    
    if args.scenario:
        # Single scenario
        scenario_dir = results_dir / args.scenario
        if not scenario_dir.exists():
            print(f"❌ Scenario directory not found: {scenario_dir}")
        else:
            scenario_name = args.scenario.replace('_', ' ')
            figures_dir = results_dir / "figures"
            figures_dir.mkdir(exist_ok=True)
            
            if args.type in ['network', 'all']:
                network_file = figures_dir / f"{args.scenario}_network.png"
                plot_network_diagram(scenario_dir, scenario_name, network_file)
            
            if args.type in ['decisions', 'all']:
                decision_file = figures_dir / f"{args.scenario}_decisions.png"
                plot_decision_analysis(scenario_dir, scenario_name, decision_file)
    else:
        # All scenarios
        if args.type == 'summary':
            figures_dir = results_dir / "figures"
            figures_dir.mkdir(exist_ok=True)
            summary_file = figures_dir / "summary_comparison.png"
            plot_summary_comparison(results_dir, summary_file)
        else:
            create_all_visualizations(args.results_dir)

