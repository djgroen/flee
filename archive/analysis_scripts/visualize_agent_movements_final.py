#!/usr/bin/env python3
"""
Final Enhanced Agent Movement Visualization

Features:
- Clear network topology with visible edges
- LARGE, visible individual agents (size 200+)
- S1 vs S2 behavioral differences
- Individual agent S2 state tracking
- Topology-specific layouts clearly visible
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from pathlib import Path
import json
from scipy.spatial.distance import cdist

plt.rcParams['figure.figsize'] = (18, 14)


def load_agent_logs(results_dir, topology_name):
    """Load agent logs from agents.out files."""
    topology_file = results_dir / f'agents_{topology_name.lower()}.out'
    
    if topology_file.exists():
        agents_file = topology_file
    else:
        agents_files = list(results_dir.glob("agents.out.*"))
        if not agents_files:
            print(f"⚠️  No agents.out files found for {topology_name}")
            return None
        agents_file = agents_files[0]
    
    print(f"   Loading agent logs from: {agents_file.name}")
    
    data = []
    with open(agents_file, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split(',')
            if len(parts) >= 6:
                try:
                    time = int(parts[0])
                    agent_id = parts[1]
                    current_loc = parts[3]
                    gps_x = float(parts[4])
                    gps_y = float(parts[5])
                    
                    data.append({
                        'time': time,
                        'agent_id': agent_id,
                        'current_location': current_loc,
                        'x': gps_x,
                        'y': gps_y
                    })
                except (ValueError, IndexError):
                    continue
    
    if not data:
        return None
    
    return pd.DataFrame(data)


def load_agent_s2_states(results_dir, topology_name):
    """Load individual agent S2 states from JSON."""
    json_files = sorted(results_dir.glob("nuclear_evacuation_detailed_*.json"))
    if not json_files:
        return None
    
    latest = json_files[-1]
    with open(latest, 'r') as f:
        results = json.load(f)
    
    topology_result = [r for r in results if r['topology'] == topology_name]
    if not topology_result:
        return None
    
    return topology_result[0].get('agent_s2_states_by_time', {})


def create_final_animation(results_dir, topology_name, output_file, fps=2):
    """Create final enhanced animation."""
    
    print(f"\n🎬 Creating FINAL animation for {topology_name} topology...")
    
    # Load data
    agent_df = load_agent_logs(results_dir, topology_name)
    if agent_df is None or len(agent_df) == 0:
        print(f"❌ No agent data available")
        return False
    
    # Load S2 states
    agent_s2_states = load_agent_s2_states(results_dir, topology_name)
    
    # Load topology structure
    json_files = sorted(results_dir.glob("nuclear_evacuation_detailed_*.json"))
    locations, routes = [], []
    s2_rates = []
    
    if json_files:
        with open(json_files[-1], 'r') as f:
            results = json.load(f)
        topology_result = [r for r in results if r['topology'] == topology_name]
        if topology_result:
            result = topology_result[0]
            locations = result.get('locations', [])
            routes = result.get('routes', [])
            s2_rates = result.get('s2_activations_by_time', [])
    
    timesteps = sorted(agent_df['time'].unique())
    agents = agent_df['agent_id'].unique()
    print(f"   Found {len(agents)} agents across {len(timesteps)} timesteps")
    print(f"   Network: {len(locations)} locations, {len(routes)} routes")
    
    # Create figure with larger size
    fig, ax = plt.subplots(figsize=(18, 14))
    
    # Color scheme
    colors = {
        'S1': '#e74c3c',  # Red
        'S2': '#2ecc71',  # Green
        'SafeZone': '#3498db',  # Blue
        'Facility': '#e67e22',  # Orange
        'Location': '#95a5a6',  # Gray
        'Route': '#34495e',  # Dark gray
        'Background': '#f8f9fa'  # Very light gray
    }
    
    # Draw network topology (STATIC BACKGROUND)
    ax.set_facecolor(colors['Background'])
    
    # Draw routes/edges (THICK, VISIBLE)
    location_dict = {loc['name']: loc for loc in locations}
    for route in routes:
        from_loc = location_dict.get(route['from'])
        to_loc = location_dict.get(route['to'])
        if from_loc and to_loc:
            ax.plot([from_loc['x'], to_loc['x']], 
                   [from_loc['y'], to_loc['y']], 
                   'k-', linewidth=2.5, alpha=0.4, zorder=1, linestyle='-')
    
    # Draw locations (LARGE, VISIBLE)
    for loc in locations:
        x, y = loc['x'], loc['y']
        name = loc['name']
        conflict = loc.get('conflict', 0.0)
        
        if 'SafeZone' in name:
            ax.scatter(x, y, s=800, c=colors['SafeZone'], marker='s', 
                      alpha=0.5, zorder=3, edgecolors='black', linewidths=4)
            ax.text(x, y + 25, 'SAFE', ha='center', fontsize=14, fontweight='bold', 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        elif 'Facility' in name:
            ax.scatter(x, y, s=800, c=colors['Facility'], marker='*', 
                      alpha=0.5, zorder=3, edgecolors='black', linewidths=4)
            ax.text(x, y + 25, 'FACILITY', ha='center', fontsize=14, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            # Color by conflict level
            alpha = 0.4 + (1 - conflict) * 0.3
            ax.scatter(x, y, s=300, c=colors['Location'], marker='o', 
                      alpha=alpha, zorder=2, edgecolors='black', linewidths=2)
    
    # Initialize agent plots (VERY LARGE)
    scatter_s1 = ax.scatter([], [], c=colors['S1'], s=250, alpha=0.85, 
                           label='System 1 (Reactive/Flocking)', zorder=15, 
                           edgecolors='darkred', linewidths=3, marker='o')
    scatter_s2 = ax.scatter([], [], c=colors['S2'], s=250, alpha=0.85, 
                           label='System 2 (Deliberative/Individual)', zorder=15, 
                           edgecolors='darkgreen', linewidths=3, marker='s')
    
    # Title
    title = ax.text(0.5, 0.98, '', transform=ax.transAxes, 
                   ha='center', fontsize=20, fontweight='bold')
    subtitle = ax.text(0.5, 0.94, '', transform=ax.transAxes, 
                      ha='center', fontsize=16)
    
    ax.set_xlabel('X Coordinate', fontsize=16)
    ax.set_ylabel('Y Coordinate', fontsize=16)
    ax.legend(loc='upper left', fontsize=14, framealpha=0.95, markerscale=1.5)
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=1)
    
    # Set axis limits
    all_x = [loc['x'] for loc in locations] + list(agent_df['x'])
    all_y = [loc['y'] for loc in locations] + list(agent_df['y'])
    x_min, x_max = min(all_x) - 40, max(all_x) + 40
    y_min, y_max = min(all_y) - 40, max(all_y) + 40
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    
    def animate(frame):
        """Animation function."""
        t = timesteps[frame] if frame < len(timesteps) else timesteps[-1]
        
        t_data = agent_df[agent_df['time'] == t]
        if len(t_data) == 0:
            return scatter_s1, scatter_s2, title, subtitle
        
        # Use actual S2 states if available, otherwise use location proxy
        if agent_s2_states and t in agent_s2_states:
            # Use actual S2 states from simulation
            states = agent_s2_states[t]
            s1_positions = []
            s2_positions = []
            
            for agent_id, state in states.items():
                if state.get('s2_active', False):
                    s2_positions.append([state['x'], state['y']])
                else:
                    s1_positions.append([state['x'], state['y']])
            
            if len(s1_positions) > 0:
                scatter_s1.set_offsets(np.array(s1_positions))
                scatter_s1.set_sizes([250] * len(s1_positions))
            else:
                scatter_s1.set_offsets(np.empty((0, 2)))
            
            if len(s2_positions) > 0:
                scatter_s2.set_offsets(np.array(s2_positions))
                scatter_s2.set_sizes([250] * len(s2_positions))
            else:
                scatter_s2.set_offsets(np.empty((0, 2)))
        else:
            # Fallback: use location-based proxy
            s1_agents = t_data[t_data['current_location'].str.contains('Facility|Ring1|NearFacility', na=False, regex=True)]
            s2_agents = t_data[~t_data['current_location'].str.contains('Facility|Ring1|NearFacility', na=False, regex=True)]
            
            if len(s1_agents) > 0:
                scatter_s1.set_offsets(np.c_[s1_agents['x'], s1_agents['y']])
                scatter_s1.set_sizes([250] * len(s1_agents))
            else:
                scatter_s1.set_offsets(np.empty((0, 2)))
            
            if len(s2_agents) > 0:
                scatter_s2.set_offsets(np.c_[s2_agents['x'], s2_agents['y']])
                scatter_s2.set_sizes([250] * len(s2_agents))
            else:
                scatter_s2.set_offsets(np.empty((0, 2)))
        
        # Update title
        s2_rate = s2_rates[t] if t < len(s2_rates) else 0.0
        title.set_text(f'{topology_name} Topology - Time Step {t}')
        subtitle.set_text(f'S2 Activation: {s2_rate:.1f}% | Total Agents: {len(t_data)}')
        
        return scatter_s1, scatter_s2, title, subtitle
    
    # Create animation
    print(f"   Creating animation with {len(timesteps)} frames...")
    anim = animation.FuncAnimation(fig, animate, frames=len(timesteps), 
                                  interval=1000/fps, blit=False, repeat=True)
    
    # Save
    print(f"   Saving to {output_file}...")
    try:
        anim.save(output_file, writer='ffmpeg', fps=fps, bitrate=1800)
        print(f"✅ Animation saved: {output_file}")
        return True
    except Exception as e:
        print(f"⚠️  ffmpeg not available, saving as GIF...")
        output_gif = output_file.with_suffix('.gif')
        try:
            anim.save(output_gif, writer='pillow', fps=fps)
            print(f"✅ Animation saved as GIF: {output_gif}")
            return True
        except Exception as e2:
            print(f"❌ Error: {e2}")
            return False
    finally:
        plt.close(fig)


def create_all_final_animations(results_dir=None):
    """Create final animations for all topologies."""
    if results_dir is None:
        results_dir = Path("data/results")
    else:
        results_dir = Path(results_dir)
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    topologies = ['Ring', 'Star', 'Linear']
    
    print("\n" + "="*70)
    print("CREATING FINAL ENHANCED AGENT MOVEMENT ANIMATIONS")
    print("="*70)
    
    for topology in topologies:
        output_file = results_dir / f'{topology.lower()}_agent_movements_final.mp4'
        create_final_animation(results_dir, topology, output_file, fps=2)
    
    print("\n✅ Final animation creation complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = "nuclear_evacuation_results"
    
    create_all_final_animations(results_dir)

