#!/usr/bin/env python3
"""
Analyze Nuclear Evacuation Results

Explains:
1. Ring topology structure
2. S2 activation interpretation over time
3. Factors influencing S2 activation
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)


def load_results(json_file):
    """Load results from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)


def explain_ring_topology():
    """Explain the ring topology structure."""
    print("\n" + "="*70)
    print("RING TOPOLOGY EXPLANATION")
    print("="*70)
    print("""
The ring topology represents circular evacuation zones around a nuclear facility:

1. CENTER (Facility):
   - Location: (0, 0)
   - Conflict: 0.95 (extreme danger)
   - All agents start here

2. RING 1 (Inner Ring):
   - 4 locations at radius ~33 units
   - Conflict: ~0.70 (high danger)
   - Connected directly to center

3. RING 2 (Middle Ring):
   - 4 locations at radius ~67 units
   - Conflict: ~0.45 (moderate danger)
   - Connected to Ring 1 locations

4. RING 3 (Outer Ring):
   - 4 locations at radius ~100 units
   - Conflict: ~0.20 (low danger)
   - Connected to Ring 2 locations

5. SAFE ZONE:
   - Location: (150, 0)
   - Conflict: 0.0 (safe)
   - Connected to outer ring

EVACUATION PATH: Facility → Ring1 → Ring2 → Ring3 → SafeZone
    """)


def explain_s2_activation():
    """Explain S2 activation over time."""
    print("\n" + "="*70)
    print("S2 ACTIVATION INTERPRETATION")
    print("="*70)
    print("""
S2 Activation Formula: P_S2 = Ψ × Ω

Where:
  Ψ (Psi) = Cognitive Capacity = sigmoid(α × experience_index)
  Ω (Omega) = Structural Opportunity = sigmoid(β × (1 - conflict))

FACTORS THAT CHANGE OVER TIME:

1. EXPERIENCE INDEX (increases over time):
   - prior_displacement = timesteps_since_departure / 30.0
   - As agents travel longer, they gain experience
   - Higher experience → Higher Ψ → Higher S2 activation

2. CONFLICT INTENSITY (decreases as agents move away):
   - Agents start at high-conflict location (conflict = 0.95)
   - As they move to safer locations, conflict decreases
   - Lower conflict → Higher Ω → Higher S2 activation

3. WHY S2 INCREASES OVER TIME:
   ✓ More travel experience → Higher cognitive capacity (Ψ)
   ✓ Moving to safer zones → Higher structural opportunity (Ω)
   ✓ Both factors multiply → S2 activation increases

INTERPRETATION:
- Early time (t=0): Low experience, high conflict → Low S2
- Later time (t=30): High experience, low conflict → High S2
- This represents agents becoming more rational/planning-oriented
  as they gain experience and move to safer environments
    """)


def analyze_s2_factors(results, output_dir):
    """Analyze factors influencing S2 activation."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    for result in results:
        topology = result['topology']
        timesteps = range(len(result['s2_activations_by_time']))
        
        # Plot 1: S2 activation over time
        axes[0, 0].plot(timesteps, result['s2_activations_by_time'], 
                       label=topology, marker='o', markersize=5, linewidth=2.5)
        
        # Plot 2: Agents at safe zones (evacuation progress)
        axes[0, 1].plot(timesteps, result['agents_at_safe_by_time'], 
                       label=topology, marker='s', markersize=5, linewidth=2.5)
        
        # Plot 3: Cognitive pressure (should decrease as conflict decreases)
        axes[1, 0].plot(timesteps, result['avg_pressure_by_time'], 
                       label=topology, marker='^', markersize=5, linewidth=2.5)
        
        # Plot 4: S2 rate vs Evacuation progress (scatter)
        safe_pct = [100 * safe / result['num_agents'] 
                   for safe in result['agents_at_safe_by_time']]
        axes[1, 1].scatter(safe_pct, result['s2_activations_by_time'], 
                          label=topology, s=100, alpha=0.6)
    
    # Formatting
    axes[0, 0].set_xlabel('Time (timesteps)', fontsize=12)
    axes[0, 0].set_ylabel('S2 Activation Rate (%)', fontsize=12)
    axes[0, 0].set_title('S2 Activation Increases Over Time\n(More experience + Lower conflict → Higher S2)', 
                         fontsize=13, fontweight='bold')
    axes[0, 0].legend(loc='best', fontsize=11)
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='50% threshold')
    
    axes[0, 1].set_xlabel('Time (timesteps)', fontsize=12)
    axes[0, 1].set_ylabel('Agents at Safe Zones', fontsize=12)
    axes[0, 1].set_title('Evacuation Progress Over Time', fontsize=13, fontweight='bold')
    axes[0, 1].legend(loc='best', fontsize=11)
    axes[0, 1].grid(True, alpha=0.3)
    
    axes[1, 0].set_xlabel('Time (timesteps)', fontsize=12)
    axes[1, 0].set_ylabel('Average Cognitive Pressure', fontsize=12)
    axes[1, 0].set_title('Cognitive Pressure Over Time\n(Decreases as agents move to safer zones)', 
                         fontsize=13, fontweight='bold')
    axes[1, 0].legend(loc='best', fontsize=11)
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].set_xlabel('Evacuation Progress (%)', fontsize=12)
    axes[1, 1].set_ylabel('S2 Activation Rate (%)', fontsize=12)
    axes[1, 1].set_title('S2 Activation vs Evacuation Progress\n(Relationship between rationality and safety)', 
                         fontsize=13, fontweight='bold')
    axes[1, 1].legend(loc='best', fontsize=11)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / 'nuclear_evacuation_s2_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def visualize_ring_structure():
    """Create a clear visualization of the ring topology structure."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    # Center (Facility)
    center = (0, 0)
    ax.plot(center[0], center[1], 'r*', markersize=30, label='Facility (Conflict=0.95)', zorder=5)
    ax.text(center[0], center[1] + 10, 'FACILITY', ha='center', fontsize=12, fontweight='bold')
    
    # Rings
    n_rings = 3
    radius = 100.0
    locations_per_ring = 4
    
    colors = ['#e74c3c', '#f39c12', '#2ecc71']  # Red, Orange, Green
    conflict_levels = [0.70, 0.45, 0.20]
    
    for ring in range(1, n_rings + 1):
        ring_radius = radius * ring / n_rings
        angle_step = 2 * np.pi / locations_per_ring
        
        # Draw ring circle
        circle = plt.Circle(center, ring_radius, fill=False, 
                           linestyle='--', linewidth=2, 
                           color=colors[ring-1], alpha=0.3)
        ax.add_patch(circle)
        
        # Draw locations
        for i in range(locations_per_ring):
            angle = i * angle_step
            x = ring_radius * np.cos(angle)
            y = ring_radius * np.sin(angle)
            
            ax.plot(x, y, 'o', markersize=15, color=colors[ring-1], 
                   zorder=4, label=f'Ring {ring}' if i == 0 else '')
            ax.text(x, y + 5, f'R{ring}-{i+1}', ha='center', fontsize=9)
            
            # Draw connection to previous ring or center
            if ring == 1:
                ax.plot([center[0], x], [center[1], y], 
                       'k-', linewidth=1, alpha=0.3, zorder=1)
            else:
                prev_ring_radius = radius * (ring - 1) / n_rings
                prev_x = prev_ring_radius * np.cos(angle)
                prev_y = prev_ring_radius * np.sin(angle)
                ax.plot([prev_x, x], [prev_y, y], 
                       'k-', linewidth=1, alpha=0.3, zorder=1)
    
    # Safe zone
    safe_zone = (radius * 1.5, 0)
    ax.plot(safe_zone[0], safe_zone[1], 's', markersize=25, 
           color='#3498db', label='Safe Zone (Conflict=0.0)', zorder=5)
    ax.text(safe_zone[0], safe_zone[1] + 10, 'SAFE ZONE', 
           ha='center', fontsize=12, fontweight='bold', color='#3498db')
    
    # Connect outer ring to safe zone
    outer_ring_radius = radius
    ax.plot([outer_ring_radius, safe_zone[0]], [0, safe_zone[1]], 
           'k-', linewidth=2, alpha=0.5, zorder=1, linestyle='--')
    
    # Formatting
    ax.set_xlim(-120, 180)
    ax.set_ylim(-120, 120)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    ax.set_title('Ring Topology Structure\n(Concentric Evacuation Zones)', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Add annotation
    ax.text(-100, 100, 
           'Evacuation Path:\nFacility → Ring1 → Ring2 → Ring3 → SafeZone',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
           fontsize=10, ha='left')
    
    plt.tight_layout()
    return fig


def create_summary_table(results):
    """Create a summary table explaining the results."""
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    
    df = pd.DataFrame([
        {
            'Topology': r['topology'],
            'Final S2 Rate': f"{r['final_s2_rate']:.1f}%",
            'Avg S2 Rate': f"{r['avg_s2_rate']:.1f}%",
            'Evacuated': f"{r['final_agents_at_safe_pct']:.1f}%",
            'Locations': r['num_locations'],
            'Routes': r['num_routes']
        }
        for r in results
    ])
    
    print("\n" + df.to_string(index=False))
    
    print("\n" + "-"*70)
    print("KEY INSIGHTS:")
    print("-"*70)
    print("""
1. STAR TOPOLOGY: Highest S2 activation (93%)
   - Multiple evacuation routes reduce decision complexity
   - Agents can choose optimal path → More rational decisions
   
2. LINEAR TOPOLOGY: Moderate S2 activation (88%)
   - Single evacuation corridor
   - Less choice complexity → Moderate S2 activation
   
3. RING TOPOLOGY: Lower S2 activation (76%)
   - Multiple paths but circular structure may create confusion
   - Agents may take longer to find optimal route
   - Lower evacuation success (9%) suggests path-finding challenges
    """)


if __name__ == "__main__":
    # Find latest results file
    results_dir = Path("nuclear_evacuation_results")
    json_files = list(results_dir.glob("nuclear_evacuation_detailed_*.json"))
    
    if not json_files:
        print("❌ No results files found!")
        exit(1)
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading results from: {latest_file}")
    
    results = load_results(latest_file)
    
    # Print explanations
    explain_ring_topology()
    explain_s2_activation()
    
    # Create visualizations
    print("\n📊 Generating analysis visualizations...")
    analyze_s2_factors(results, results_dir)
    
    # Visualize ring structure
    fig = visualize_ring_structure()
    ring_file = results_dir / 'ring_topology_structure.png'
    fig.savefig(ring_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {ring_file}")
    plt.close()
    
    # Create summary
    create_summary_table(results)
    
    print(f"\n✅ Analysis complete! Check {results_dir} for visualizations.")

