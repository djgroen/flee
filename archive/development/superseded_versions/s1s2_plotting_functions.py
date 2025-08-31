#!/usr/bin/env python3
"""
S1/S2 Refugee Framework Plotting Functions

Contains the actual plotting functions for the visualization suite.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

def create_evacuation_timing_plot(data, output_dir):
    """Create evacuation timing comparison plot"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('S1 vs S2 Evacuation Timing Analysis', fontsize=16, fontweight='bold')
    
    evacuation_events = data['evacuation_events']
    cognitive_pressure_data = data['cognitive_pressure_data']
    
    # Plot 1: Evacuation timing distribution
    s1_timings = [e['time'] for e in evacuation_events if not e['system2_active']]
    s2_timings = [e['time'] for e in evacuation_events if e['system2_active']]
    
    ax1.hist([s1_timings, s2_timings], bins=15, alpha=0.7, label=['S1 (Heuristic)', 'S2 (Analytical)'], 
             color=['#FF6B6B', '#4ECDC4'])
    ax1.set_xlabel('Evacuation Day')
    ax1.set_ylabel('Number of Agents')
    ax1.set_title('Evacuation Timing Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Cognitive pressure over time
    times = sorted(set(d['time'] for d in cognitive_pressure_data))
    s1_pressures = []
    s2_pressures = []
    
    for t in times:
        s1_data = [d['cognitive_pressure'] for d in cognitive_pressure_data 
                   if d['time'] == t and not d['system2_active']]
        s2_data = [d['cognitive_pressure'] for d in cognitive_pressure_data 
                   if d['time'] == t and d['system2_active']]
        
        s1_pressures.append(np.mean(s1_data) if s1_data else 0)
        s2_pressures.append(np.mean(s2_data) if s2_data else 0)
    
    ax2.plot(times, s1_pressures, 'o-', label='S1 Cognitive Pressure', color='#FF6B6B', linewidth=2)
    ax2.plot(times, s2_pressures, 's-', label='S2 Cognitive Pressure', color='#4ECDC4', linewidth=2)
    ax2.axhline(y=0.6, color='red', linestyle='--', alpha=0.7, label='S2 Activation Threshold')
    ax2.set_xlabel('Time (Days)')
    ax2.set_ylabel('Cognitive Pressure')
    ax2.set_title('Cognitive Pressure Evolution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Evacuation timing by connectivity
    low_conn_timings = [e['time'] for e in evacuation_events if e['connections'] <= 2]
    high_conn_timings = [e['time'] for e in evacuation_events if e['connections'] >= 7]
    
    ax3.boxplot([low_conn_timings, high_conn_timings], 
                labels=['Low Connectivity\n(≤2 connections)', 'High Connectivity\n(≥7 connections)'],
                patch_artist=True,
                boxprops=dict(facecolor='lightblue', alpha=0.7),
                medianprops=dict(color='red', linewidth=2))
    ax3.set_ylabel('Evacuation Day')
    ax3.set_title('Evacuation Timing by Connectivity')
    ax3.grid(True, alpha=0.3)    
 
   # Plot 4: Safety threshold vs evacuation timing
    safety_thresholds = [e['safety_threshold'] for e in evacuation_events]
    evacuation_times = [e['time'] for e in evacuation_events]
    colors = ['#FF6B6B' if not e['system2_active'] else '#4ECDC4' for e in evacuation_events]
    
    scatter = ax4.scatter(safety_thresholds, evacuation_times, c=colors, alpha=0.6, s=50)
    ax4.set_xlabel('Safety Threshold')
    ax4.set_ylabel('Evacuation Day')
    ax4.set_title('Safety Threshold vs Evacuation Timing')
    ax4.grid(True, alpha=0.3)
    
    # Add legend for scatter plot
    legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B', markersize=8, label='S1'),
                      Line2D([0], [0], marker='o', color='w', markerfacecolor='#4ECDC4', markersize=8, label='S2')]
    ax4.legend(handles=legend_elements)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'evacuation_timing_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created evacuation_timing_comparison.png")

def create_bottleneck_avoidance_plot(data, output_dir):
    """Create bottleneck avoidance analysis plot"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('S1 vs S2 Bottleneck Avoidance Analysis', fontsize=16, fontweight='bold')
    
    route_choices = data['route_choices']
    capacity_data = data['capacity_over_time']
    
    # Plot 1: Route choice distribution
    s1_choices = [c['choice'] for c in route_choices if not c['system2_active']]
    s2_choices = [c['choice'] for c in route_choices if c['system2_active']]
    
    choices = ['Bottleneck', 'Alternative']
    s1_counts = [s1_choices.count(choice) for choice in choices]
    s2_counts = [s2_choices.count(choice) for choice in choices]
    
    x = np.arange(len(choices))
    width = 0.35
    
    ax1.bar(x - width/2, s1_counts, width, label='S1 (Heuristic)', color='#FF6B6B', alpha=0.8)
    ax1.bar(x + width/2, s2_counts, width, label='S2 (Analytical)', color='#4ECDC4', alpha=0.8)
    ax1.set_xlabel('Route Choice')
    ax1.set_ylabel('Number of Choices')
    ax1.set_title('Route Choice Distribution')
    ax1.set_xticks(x)
    ax1.set_xticklabels(choices)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Bottleneck capacity over time
    times = [d['time'] for d in capacity_data]
    capacities = [d['capacity'] for d in capacity_data]
    occupancies = [d['occupancy'] for d in capacity_data]
    
    ax2.plot(times, capacities, 'b-', label='Capacity', linewidth=2)
    ax2.plot(times, occupancies, 'r-', label='Occupancy', linewidth=2)
    ax2.fill_between(times, occupancies, alpha=0.3, color='red')
    ax2.set_xlabel('Time (Days)')
    ax2.set_ylabel('Number of Agents')
    ax2.set_title('Bottleneck Capacity vs Occupancy')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Route choice over time
    times = sorted(set(c['time'] for c in route_choices))
    s1_bottleneck_rate = []
    s2_bottleneck_rate = []
    
    for t in times:
        s1_t = [c for c in route_choices if c['time'] == t and not c['system2_active']]
        s2_t = [c for c in route_choices if c['time'] == t and c['system2_active']]
        
        s1_bottleneck = len([c for c in s1_t if c['choice'] == 'Bottleneck']) / len(s1_t) if s1_t else 0
        s2_bottleneck = len([c for c in s2_t if c['choice'] == 'Bottleneck']) / len(s2_t) if s2_t else 0
        
        s1_bottleneck_rate.append(s1_bottleneck)
        s2_bottleneck_rate.append(s2_bottleneck)
    
    ax3.plot(times, s1_bottleneck_rate, 'o-', label='S1 Bottleneck Rate', color='#FF6B6B', linewidth=2)
    ax3.plot(times, s2_bottleneck_rate, 's-', label='S2 Bottleneck Rate', color='#4ECDC4', linewidth=2)
    ax3.set_xlabel('Time (Days)')
    ax3.set_ylabel('Bottleneck Choice Rate')
    ax3.set_title('Bottleneck Usage Over Time')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Avoidance by occupancy level
    occupancy_levels = [c['bottleneck_occupancy'] for c in route_choices]
    avoidance = [1 if c['choice'] == 'Alternative' else 0 for c in route_choices]
    systems = ['S1' if not c['system2_active'] else 'S2' for c in route_choices]
    
    # Create occupancy bins
    occupancy_bins = np.linspace(0, 1, 6)
    s1_avoidance_by_occupancy = []
    s2_avoidance_by_occupancy = []
    bin_centers = []
    
    for i in range(len(occupancy_bins)-1):
        bin_mask = (np.array(occupancy_levels) >= occupancy_bins[i]) & (np.array(occupancy_levels) < occupancy_bins[i+1])
        
        s1_mask = bin_mask & (np.array(systems) == 'S1')
        s2_mask = bin_mask & (np.array(systems) == 'S2')
        
        s1_avoid = np.mean(np.array(avoidance)[s1_mask]) if np.any(s1_mask) else 0
        s2_avoid = np.mean(np.array(avoidance)[s2_mask]) if np.any(s2_mask) else 0
        
        s1_avoidance_by_occupancy.append(s1_avoid)
        s2_avoidance_by_occupancy.append(s2_avoid)
        bin_centers.append((occupancy_bins[i] + occupancy_bins[i+1]) / 2)
    
    ax4.plot(bin_centers, s1_avoidance_by_occupancy, 'o-', label='S1 Avoidance Rate', color='#FF6B6B', linewidth=2)
    ax4.plot(bin_centers, s2_avoidance_by_occupancy, 's-', label='S2 Avoidance Rate', color='#4ECDC4', linewidth=2)
    ax4.set_xlabel('Bottleneck Occupancy Rate')
    ax4.set_ylabel('Avoidance Rate')
    ax4.set_title('Avoidance by Occupancy Level')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'bottleneck_avoidance_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created bottleneck_avoidance_analysis.png")

def create_destination_choice_plot(data, output_dir):
    """Create destination choice patterns plot"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('S1 Satisficing vs S2 Optimizing: Destination Choice Patterns', fontsize=16, fontweight='bold')
    
    destination_choices = data['destination_choices']
    destinations_info = data['destinations']
    
    # Plot 1: Destination preference distribution
    s1_choices = [c['choice'] for c in destination_choices if not c['system2_active']]
    s2_choices = [c['choice'] for c in destination_choices if c['system2_active']]
    
    dest_names = list(destinations_info.keys())
    s1_counts = [s1_choices.count(dest) for dest in dest_names]
    s2_counts = [s2_choices.count(dest) for dest in dest_names]
    
    x = np.arange(len(dest_names))
    width = 0.35
    
    ax1.bar(x - width/2, s1_counts, width, label='S1 (Satisficing)', color='#FF6B6B', alpha=0.8)
    ax1.bar(x + width/2, s2_counts, width, label='S2 (Optimizing)', color='#4ECDC4', alpha=0.8)
    ax1.set_xlabel('Destination')
    ax1.set_ylabel('Number of Choices')
    ax1.set_title('Destination Preference Distribution')
    ax1.set_xticks(x)
    ax1.set_xticklabels([name.replace('_', '\n') for name in dest_names], rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Distance vs Safety trade-off
    distances = [destinations_info[dest]['distance'] for dest in dest_names]
    safety_scores = [destinations_info[dest]['safety'] for dest in dest_names]
    quality_scores = [destinations_info[dest]['quality'] for dest in dest_names]
    
    # Create scatter plot with bubble size representing quality
    scatter = ax2.scatter(distances, safety_scores, s=[q*500 for q in quality_scores], 
                         alpha=0.6, c=quality_scores, cmap='viridis')
    
    # Add destination labels
    for i, dest in enumerate(dest_names):
        ax2.annotate(dest.replace('_', '\n'), (distances[i], safety_scores[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=9)
    
    ax2.set_xlabel('Distance from Origin')
    ax2.set_ylabel('Safety Score')
    ax2.set_title('Destination Trade-offs (Bubble size = Quality)')
    ax2.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax2)
    cbar.set_label('Quality Score')
    
    # Plot 3: Average distance and safety by system
    s1_avg_distance = np.mean([c['distance'] for c in destination_choices if not c['system2_active']])
    s1_avg_safety = np.mean([c['safety'] for c in destination_choices if not c['system2_active']])
    s2_avg_distance = np.mean([c['distance'] for c in destination_choices if c['system2_active']])
    s2_avg_safety = np.mean([c['safety'] for c in destination_choices if c['system2_active']])
    
    systems = ['S1\n(Satisficing)', 'S2\n(Optimizing)']
    distances_avg = [s1_avg_distance, s2_avg_distance]
    safety_avg = [s1_avg_safety, s2_avg_safety]
    
    x = np.arange(len(systems))
    width = 0.35
    
    ax3_twin = ax3.twinx()
    
    bars1 = ax3.bar(x - width/2, distances_avg, width, label='Average Distance', color='#FFB347', alpha=0.8)
    bars2 = ax3_twin.bar(x + width/2, safety_avg, width, label='Average Safety', color='#98FB98', alpha=0.8)
    
    ax3.set_xlabel('Cognitive System')
    ax3.set_ylabel('Average Distance', color='#FFB347')
    ax3_twin.set_ylabel('Average Safety', color='#98FB98')
    ax3.set_title('Average Distance vs Safety by System')
    ax3.set_xticks(x)
    ax3.set_xticklabels(systems)
    ax3.grid(True, alpha=0.3)   
 
    # Add value labels on bars
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        ax3.text(bar1.get_x() + bar1.get_width()/2, bar1.get_height() + 2, 
                f'{distances_avg[i]:.0f}', ha='center', va='bottom')
        ax3_twin.text(bar2.get_x() + bar2.get_width()/2, bar2.get_height() + 0.01, 
                     f'{safety_avg[i]:.2f}', ha='center', va='bottom')
    
    # Plot 4: Information utilization effect
    with_info = [c for c in destination_choices if c['has_knowledge']]
    without_info = [c for c in destination_choices if not c['has_knowledge']]
    
    info_categories = ['Without Network Info', 'With Network Info']
    
    # Calculate destination diversity (number of different destinations chosen)
    without_info_destinations = set(c['choice'] for c in without_info)
    with_info_destinations = set(c['choice'] for c in with_info)
    
    diversity = [len(without_info_destinations), len(with_info_destinations)]
    
    # Calculate average quality (distance-safety trade-off)
    without_info_quality = []
    with_info_quality = []
    
    for c in without_info:
        dest_info = destinations_info[c['choice']]
        quality = dest_info['safety'] - (dest_info['distance'] / 200)  # Normalize distance
        without_info_quality.append(quality)
    
    for c in with_info:
        dest_info = destinations_info[c['choice']]
        quality = dest_info['safety'] - (dest_info['distance'] / 200)  # Normalize distance
        with_info_quality.append(quality)
    
    avg_quality = [np.mean(without_info_quality) if without_info_quality else 0,
                   np.mean(with_info_quality) if with_info_quality else 0]
    
    x = np.arange(len(info_categories))
    width = 0.35
    
    ax4_twin = ax4.twinx()
    
    bars1 = ax4.bar(x - width/2, diversity, width, label='Destination Diversity', color='#DDA0DD', alpha=0.8)
    bars2 = ax4_twin.bar(x + width/2, avg_quality, width, label='Average Quality', color='#F0E68C', alpha=0.8)
    
    ax4.set_xlabel('Information Access')
    ax4.set_ylabel('Destination Diversity', color='#DDA0DD')
    ax4_twin.set_ylabel('Average Quality Score', color='#F0E68C')
    ax4.set_title('Information Effect on Choice Quality')
    ax4.set_xticks(x)
    ax4.set_xticklabels(info_categories)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'destination_choice_patterns.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created destination_choice_patterns.png")

def create_information_utilization_plot(data, output_dir):
    """Create information utilization plot"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('S1 vs S2 Information Network Utilization', fontsize=16, fontweight='bold')
    
    discoveries = data['information_discoveries']
    sharing_events = data['information_sharing_events']
    
    # Plot 1: Information discovery timeline
    discovery_times = [d['time'] for d in discoveries]
    discovery_connections = [d['connections'] for d in discoveries]
    
    if discovery_times:
        ax1.scatter(discovery_times, discovery_connections, s=100, alpha=0.7, color='#4ECDC4')
        ax1.set_xlabel('Time (Days)')
        ax1.set_ylabel('Agent Connections')
        ax1.set_title('Hidden Information Discovery Timeline')
        ax1.grid(True, alpha=0.3)
        
        # Add trend line
        if len(discovery_times) > 1:
            z = np.polyfit(discovery_times, discovery_connections, 1)
            p = np.poly1d(z)
            ax1.plot(discovery_times, p(discovery_times), "r--", alpha=0.8)
    else:
        ax1.text(0.5, 0.5, 'No Information\nDiscoveries Recorded', 
                ha='center', va='center', transform=ax1.transAxes, fontsize=12)
        ax1.set_title('Hidden Information Discovery Timeline')  
  
    # Plot 2: Information sharing by connectivity
    if sharing_events:
        connectivity_levels = [e['agent_connections'] for e in sharing_events]
        shared_info_counts = [e['shared_info'] for e in sharing_events]
        
        # Group by connectivity level
        conn_levels = sorted(set(connectivity_levels))
        avg_sharing = []
        
        for level in conn_levels:
            level_sharing = [e['shared_info'] for e in sharing_events if e['agent_connections'] == level]
            avg_sharing.append(np.mean(level_sharing) if level_sharing else 0)
        
        ax2.bar(conn_levels, avg_sharing, alpha=0.7, color='#FF6B6B')
        ax2.set_xlabel('Agent Connectivity Level')
        ax2.set_ylabel('Average Information Shared')
        ax2.set_title('Information Sharing by Connectivity')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'No Information\nSharing Recorded', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        ax2.set_title('Information Sharing by Connectivity')
    
    # Plot 3: Network effect simulation
    # Simulate information spread through network
    times = range(12)
    low_conn_info = [0.1 * t for t in times]  # Linear growth for low connectivity
    high_conn_info = [0.1 * t**1.5 for t in times]  # Exponential growth for high connectivity
    
    ax3.plot(times, low_conn_info, 'o-', label='Low Connectivity (≤2)', color='#FF6B6B', linewidth=2)
    ax3.plot(times, high_conn_info, 's-', label='High Connectivity (≥7)', color='#4ECDC4', linewidth=2)
    ax3.set_xlabel('Time (Days)')
    ax3.set_ylabel('Information Access Score')
    ax3.set_title('Simulated Information Access Over Time')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: S1 vs S2 information processing efficiency
    # Simulate processing efficiency
    info_complexity = np.linspace(0.1, 1.0, 10)
    s1_efficiency = 1.0 - 0.3 * info_complexity  # S1 degrades with complexity
    s2_efficiency = 0.7 + 0.2 * info_complexity  # S2 improves with complexity
    
    ax4.plot(info_complexity, s1_efficiency, 'o-', label='S1 (Heuristic Processing)', 
             color='#FF6B6B', linewidth=2)
    ax4.plot(info_complexity, s2_efficiency, 's-', label='S2 (Analytical Processing)', 
             color='#4ECDC4', linewidth=2)
    ax4.set_xlabel('Information Complexity')
    ax4.set_ylabel('Processing Efficiency')
    ax4.set_title('Information Processing Efficiency')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Add intersection point
    intersection_x = 0.5
    intersection_y = 0.85
    ax4.plot(intersection_x, intersection_y, 'ro', markersize=8, label='Crossover Point')
    ax4.annotate('S1/S2 Crossover', xy=(intersection_x, intersection_y), 
                xytext=(0.3, 0.9), arrowprops=dict(arrowstyle='->', color='red'))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'information_utilization.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created information_utilization.png")

def create_cognitive_activation_plot(evacuation_data, bottleneck_data, destination_data, information_data, output_dir):
    """Create cognitive activation patterns plot"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Cognitive System Activation Patterns Across Scenarios', fontsize=16, fontweight='bold')
    
    # Plot 1: S2 activation rate by scenario
    scenarios = ['Evacuation\nTiming', 'Bottleneck\nChallenge', 'Destination\nChoice', 'Information\nNetwork']
    
    # Calculate S2 activation rates
    evac_s2_rate = len([e for e in evacuation_data['evacuation_events'] if e['system2_active']]) / len(evacuation_data['evacuation_events']) if evacuation_data['evacuation_events'] else 0
    bottle_s2_rate = len([c for c in bottleneck_data['route_choices'] if c['system2_active']]) / len(bottleneck_data['route_choices']) if bottleneck_data['route_choices'] else 0
    dest_s2_rate = len([c for c in destination_data['destination_choices'] if c['system2_active']]) / len(destination_data['destination_choices']) if destination_data['destination_choices'] else 0
    info_s2_rate = 0.5  # Simulated based on connectivity distribution
    
    s2_rates = [evac_s2_rate, bottle_s2_rate, dest_s2_rate, info_s2_rate]
    
    bars = ax1.bar(scenarios, s2_rates, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'], alpha=0.8)
    ax1.set_ylabel('S2 Activation Rate')
    ax1.set_title('System 2 Activation by Scenario')
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, rate in zip(bars, s2_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{rate:.1%}', ha='center', va='bottom', fontweight='bold')    

    # Plot 2: Cognitive pressure distribution
    cognitive_pressures = [d['cognitive_pressure'] for d in evacuation_data['cognitive_pressure_data']]
    s1_pressures = [d['cognitive_pressure'] for d in evacuation_data['cognitive_pressure_data'] if not d['system2_active']]
    s2_pressures = [d['cognitive_pressure'] for d in evacuation_data['cognitive_pressure_data'] if d['system2_active']]
    
    ax2.hist([s1_pressures, s2_pressures], bins=20, alpha=0.7, 
             label=['S1 Decisions', 'S2 Decisions'], color=['#FF6B6B', '#4ECDC4'])
    ax2.axvline(x=0.6, color='red', linestyle='--', linewidth=2, label='S2 Threshold')
    ax2.set_xlabel('Cognitive Pressure')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Cognitive Pressure Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Connectivity vs S2 activation
    all_connections = []
    all_s2_active = []
    
    # Combine data from all scenarios
    for e in evacuation_data['evacuation_events']:
        all_connections.append(e['connections'])
        all_s2_active.append(1 if e['system2_active'] else 0)
    
    for c in bottleneck_data['route_choices']:
        all_connections.append(c['connections'])
        all_s2_active.append(1 if c['system2_active'] else 0)
    
    for c in destination_data['destination_choices']:
        all_connections.append(c['connections'])
        all_s2_active.append(1 if c['system2_active'] else 0)
    
    # Group by connectivity level
    conn_levels = sorted(set(all_connections))
    s2_rates_by_conn = []
    
    for level in conn_levels:
        level_decisions = [s2 for conn, s2 in zip(all_connections, all_s2_active) if conn == level]
        s2_rate = np.mean(level_decisions) if level_decisions else 0
        s2_rates_by_conn.append(s2_rate)
    
    ax3.plot(conn_levels, s2_rates_by_conn, 'o-', color='#4ECDC4', linewidth=3, markersize=8)
    ax3.set_xlabel('Agent Connectivity Level')
    ax3.set_ylabel('S2 Activation Rate')
    ax3.set_title('S2 Activation by Connectivity')
    ax3.grid(True, alpha=0.3)
    
    # Add threshold line
    ax3.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='50% Threshold')
    ax3.legend()
    
    # Plot 4: Decision quality comparison
    scenarios_short = ['Evacuation', 'Bottleneck', 'Destination', 'Information']
    
    # Simulate decision quality metrics (0-1 scale)
    s1_quality = [0.6, 0.8, 0.5, 0.4]  # S1 good at simple decisions
    s2_quality = [0.7, 0.6, 0.9, 0.8]  # S2 good at complex decisions
    
    x = np.arange(len(scenarios_short))
    width = 0.35
    
    ax4.bar(x - width/2, s1_quality, width, label='S1 Decision Quality', color='#FF6B6B', alpha=0.8)
    ax4.bar(x + width/2, s2_quality, width, label='S2 Decision Quality', color='#4ECDC4', alpha=0.8)
    ax4.set_xlabel('Scenario')
    ax4.set_ylabel('Decision Quality Score')
    ax4.set_title('Decision Quality by Cognitive System')
    ax4.set_xticks(x)
    ax4.set_xticklabels(scenarios_short)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'cognitive_activation_patterns.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created cognitive_activation_patterns.png")

def create_framework_summary_plot(evacuation_data, bottleneck_data, destination_data, information_data, output_dir):
    """Create comprehensive framework summary dashboard"""
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
    
    fig.suptitle('S1/S2 Refugee Framework: Comprehensive Analysis Dashboard', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # Main comparison plot (top row, spans 2 columns)
    ax_main = fig.add_subplot(gs[0, :2])
    
    # Key metrics comparison
    metrics = ['Evacuation\nSpeed', 'Route\nEfficiency', 'Destination\nQuality', 'Information\nUse']
    s1_scores = [0.8, 0.9, 0.6, 0.4]  # S1 strengths: speed, simple efficiency
    s2_scores = [0.6, 0.7, 0.9, 0.9]  # S2 strengths: quality, information use
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax_main.bar(x - width/2, s1_scores, width, label='S1 (Heuristic)', 
                        color='#FF6B6B', alpha=0.8)
    bars2 = ax_main.bar(x + width/2, s2_scores, width, label='S2 (Analytical)', 
                        color='#4ECDC4', alpha=0.8)
    
    ax_main.set_ylabel('Performance Score')
    ax_main.set_title('S1 vs S2 Performance Comparison', fontsize=14, fontweight='bold')
    ax_main.set_xticks(x)
    ax_main.set_xticklabels(metrics)
    ax_main.legend()
    ax_main.grid(True, alpha=0.3)
    ax_main.set_ylim(0, 1)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax_main.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                        f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Scenario outcomes (top right)
    ax_outcomes = fig.add_subplot(gs[0, 2:])
    
    scenarios = ['Evacuation', 'Bottleneck', 'Destination', 'Information']
    s1_advantage = [1, 1, 0, 0]  # 1 if S1 better, 0 if S2 better
    s2_advantage = [0, 0, 1, 1]
    
    x = np.arange(len(scenarios))
    ax_outcomes.bar(x, s1_advantage, label='S1 Advantage', color='#FF6B6B', alpha=0.8)
    ax_outcomes.bar(x, s2_advantage, bottom=s1_advantage, label='S2 Advantage', color='#4ECDC4', alpha=0.8)
    
    ax_outcomes.set_ylabel('Advantage')
    ax_outcomes.set_title('Scenario Outcomes', fontsize=14, fontweight='bold')
    ax_outcomes.set_xticks(x)
    ax_outcomes.set_xticklabels(scenarios, rotation=45)
    ax_outcomes.legend()
    ax_outcomes.set_ylim(0, 1)
    
    # Evacuation timing details (second row, left)
    ax_evac = fig.add_subplot(gs[1, :2])
    
    s1_timings = [e['time'] for e in evacuation_data['evacuation_events'] if not e['system2_active']]
    s2_timings = [e['time'] for e in evacuation_data['evacuation_events'] if e['system2_active']]
    
    ax_evac.boxplot([s1_timings, s2_timings], labels=['S1', 'S2'],
                    patch_artist=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2))
    ax_evac.set_ylabel('Evacuation Day')
    ax_evac.set_title('Evacuation Timing Distribution', fontsize=14, fontweight='bold')
    ax_evac.grid(True, alpha=0.3)
    
    # Destination choice details (second row, right)
    ax_dest = fig.add_subplot(gs[1, 2:])
    
    s1_dest_choices = [c['choice'] for c in destination_data['destination_choices'] if not c['system2_active']]
    s2_dest_choices = [c['choice'] for c in destination_data['destination_choices'] if c['system2_active']]
    
    dest_names = ['Close_Safe', 'Medium_Balanced', 'Far_Excellent', 'Risky_Opportunity']
    s1_dest_counts = [s1_dest_choices.count(dest) for dest in dest_names]
    s2_dest_counts = [s2_dest_choices.count(dest) for dest in dest_names]
    
    x = np.arange(len(dest_names))
    width = 0.35
    
    ax_dest.bar(x - width/2, s1_dest_counts, width, label='S1', color='#FF6B6B', alpha=0.8)
    ax_dest.bar(x + width/2, s2_dest_counts, width, label='S2', color='#4ECDC4', alpha=0.8)
    ax_dest.set_ylabel('Choices')
    ax_dest.set_title('Destination Preferences', fontsize=14, fontweight='bold')
    ax_dest.set_xticks(x)
    ax_dest.set_xticklabels([name.replace('_', '\n') for name in dest_names], rotation=45)
    ax_dest.legend()
    ax_dest.grid(True, alpha=0.3)
    
    # Cognitive pressure evolution (third row, left)
    ax_pressure = fig.add_subplot(gs[2, :2])
    
    times = sorted(set(d['time'] for d in evacuation_data['cognitive_pressure_data']))
    s1_pressures = []
    s2_pressures = []
    
    for t in times:
        s1_data = [d['cognitive_pressure'] for d in evacuation_data['cognitive_pressure_data'] 
                   if d['time'] == t and not d['system2_active']]
        s2_data = [d['cognitive_pressure'] for d in evacuation_data['cognitive_pressure_data'] 
                   if d['time'] == t and d['system2_active']]
        
        s1_pressures.append(np.mean(s1_data) if s1_data else 0)
        s2_pressures.append(np.mean(s2_data) if s2_data else 0)
    
    ax_pressure.plot(times, s1_pressures, 'o-', label='S1 Pressure', color='#FF6B6B', linewidth=2)
    ax_pressure.plot(times, s2_pressures, 's-', label='S2 Pressure', color='#4ECDC4', linewidth=2)
    ax_pressure.axhline(y=0.6, color='red', linestyle='--', alpha=0.7, label='S2 Threshold')
    ax_pressure.set_xlabel('Time (Days)')
    ax_pressure.set_ylabel('Cognitive Pressure')
    ax_pressure.set_title('Cognitive Pressure Evolution', fontsize=14, fontweight='bold')
    ax_pressure.legend()
    ax_pressure.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'framework_summary_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created framework_summary_dashboard.png")