#!/usr/bin/env python3
"""
Animate Agent Movements in Nuclear Evacuation Simulations

Creates animated movies showing:
- Agent positions over time
- S2 activation states (color-coded)
- Evacuation paths
- Network topology
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from pathlib import Path
import json
import glob
import re

plt.rcParams['figure.figsize'] = (14, 10)


def load_agent_logs(results_dir, topology_name):
    """Load agent logs from agents.out files."""
    # Try topology-specific file first
    topology_file = results_dir / f'agents_{topology_name.lower()}.out'
    
    if topology_file.exists():
        agents_file = topology_file
    else:
        # Fallback to generic agents.out files
        agents_files = sorted(results_dir.glob("agents.out.*"))
        if not agents_files:
            print(f"⚠️  No agents.out files found for {topology_name}")
            return None
        agents_file = agents_files[0]
    
    print(f"   Loading agent logs from: {agents_file.name}")
    
    # Read agents.out file
    # Format: time,rank-agentid,original_location,current_location,gps_x,gps_y,...
    data = []
    with open(agents_file, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split(',')
            if len(parts) >= 6:
                try:
                    time = int(parts[0])
                    agent_id = parts[1]  # rank-agentid
                    original_loc = parts[2]
                    current_loc = parts[3]
                    gps_x = float(parts[4])
                    gps_y = float(parts[5])
                    
                    data.append({
                        'time': time,
                        'agent_id': agent_id,
                        'original_location': original_loc,
                        'current_location': current_loc,
                        'x': gps_x,
                        'y': gps_y
                    })
                except (ValueError, IndexError):
                    continue
    
    if not data:
        print(f"⚠️  No valid agent data found in {agents_file}")
        return None
    
    df = pd.DataFrame(data)
    return df


def load_topology_data(results_dir):
    """Load topology information from JSON results."""
    json_files = sorted(results_dir.glob("nuclear_evacuation_detailed_*.json"))
    if not json_files:
        return None
    
    latest = json_files[-1]
    with open(latest, 'r') as f:
        return json.load(f)


def create_animation(results_dir, topology_name, output_file, fps=2):
    """Create animated movie of agent movements."""
    
    print(f"\n🎬 Creating animation for {topology_name} topology...")
    
    # Load agent data
    agent_df = load_agent_logs(results_dir, topology_name)
    if agent_df is None or len(agent_df) == 0:
        print(f"❌ No agent data available for {topology_name}")
        return False
    
    # Load topology results
    results = load_topology_data(results_dir)
    if results:
        topology_result = [r for r in results if r['topology'] == topology_name]
        if topology_result:
            s2_rates = topology_result[0].get('s2_activations_by_time', [])
        else:
            s2_rates = []
    else:
        s2_rates = []
    
    # Get unique timesteps
    timesteps = sorted(agent_df['time'].unique())
    if not timesteps:
        print(f"❌ No timesteps found in agent data")
        return False
    
    # Get unique agents
    agents = agent_df['agent_id'].unique()
    print(f"   Found {len(agents)} agents across {len(timesteps)} timesteps")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Color scheme
    colors = {
        'S1': '#e74c3c',  # Red for System 1
        'S2': '#2ecc71',  # Green for System 2
        'SafeZone': '#3498db',  # Blue for safe zones
        'Facility': '#e67e22',  # Orange for facility
        'Ring': '#95a5a6',  # Gray for ring locations
        'Route': '#34495e'  # Dark gray for routes
    }
    
    # Draw network topology (static background)
    # Extract unique locations from agent data
    unique_locs = agent_df[['current_location', 'x', 'y']].drop_duplicates(subset='current_location')
    for _, loc in unique_locs.iterrows():
        if 'SafeZone' in loc['current_location']:
            ax.scatter(loc['x'], loc['y'], s=300, c=colors['SafeZone'], 
                      marker='s', alpha=0.3, zorder=1, edgecolors='black', linewidths=2)
            ax.text(loc['x'], loc['y'] + 15, 'Safe Zone', ha='center', fontsize=10, fontweight='bold')
        elif 'Facility' in loc['current_location']:
            ax.scatter(loc['x'], loc['y'], s=300, c=colors['Facility'], 
                      marker='*', alpha=0.3, zorder=1, edgecolors='black', linewidths=2)
            ax.text(loc['x'], loc['y'] + 15, 'Facility', ha='center', fontsize=10, fontweight='bold')
        else:
            ax.scatter(loc['x'], loc['y'], s=100, c=colors['Ring'], 
                      marker='o', alpha=0.2, zorder=1, edgecolors='gray', linewidths=1)
    
    # Initialize empty plots for agents
    scatter_s1 = ax.scatter([], [], c=colors['S1'], s=80, alpha=0.7, 
                           label='System 1 (Reactive)', zorder=5, edgecolors='darkred', linewidths=1)
    scatter_s2 = ax.scatter([], [], c=colors['S2'], s=80, alpha=0.7, 
                           label='System 2 (Deliberative)', zorder=5, edgecolors='darkgreen', linewidths=1)
    
    # Title and labels
    title = ax.text(0.5, 0.95, '', transform=ax.transAxes, 
                   ha='center', fontsize=16, fontweight='bold')
    subtitle = ax.text(0.5, 0.90, '', transform=ax.transAxes, 
                      ha='center', fontsize=12)
    
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Set axis limits based on data
    x_min, x_max = agent_df['x'].min() - 20, agent_df['x'].max() + 20
    y_min, y_max = agent_df['y'].min() - 20, agent_df['y'].max() + 20
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    
    # Track agent trajectories (last N positions)
    trajectory_length = 5
    agent_trajectories = {agent: [] for agent in agents}
    
    def animate(frame):
        """Animation function for each frame."""
        t = timesteps[frame] if frame < len(timesteps) else timesteps[-1]
        
        # Get agent positions at this timestep
        t_data = agent_df[agent_df['time'] == t]
        
        if len(t_data) == 0:
            return scatter_s1, scatter_s2
        
        # Separate agents by location type
        # S1 agents: at high-conflict locations (Facility, Ring1)
        # S2 agents: at safer locations (Ring2, Ring3, SafeZone)
        s1_agents = t_data[t_data['current_location'].str.contains('Facility|Ring1', na=False, regex=True)]
        s2_agents = t_data[~t_data['current_location'].str.contains('Facility|Ring1', na=False, regex=True)]
        
        # Update scatter plots
        if len(s1_agents) > 0:
            scatter_s1.set_offsets(np.c_[s1_agents['x'], s1_agents['y']])
        else:
            scatter_s1.set_offsets(np.empty((0, 2)))
        
        if len(s2_agents) > 0:
            scatter_s2.set_offsets(np.c_[s2_agents['x'], s2_agents['y']])
        else:
            scatter_s2.set_offsets(np.empty((0, 2)))
        
        # Update title
        s2_rate = s2_rates[t] if t < len(s2_rates) else 0.0
        title.set_text(f'{topology_name} Topology - Time Step {t}')
        subtitle.set_text(f'S2 Activation Rate: {s2_rate:.1f}% | Agents: {len(t_data)}')
        
        # Draw trajectories
        for agent_id in agents:
            agent_data = t_data[t_data['agent_id'] == agent_id]
            if len(agent_data) > 0:
                pos = (agent_data.iloc[0]['x'], agent_data.iloc[0]['y'])
                agent_trajectories[agent_id].append(pos)
                if len(agent_trajectories[agent_id]) > trajectory_length:
                    agent_trajectories[agent_id].pop(0)
                
                # Draw trajectory line
                if len(agent_trajectories[agent_id]) > 1:
                    traj = np.array(agent_trajectories[agent_id])
                    ax.plot(traj[:, 0], traj[:, 1], 'k-', alpha=0.2, linewidth=1, zorder=1)
        
        return scatter_s1, scatter_s2, title, subtitle
    
    # Create animation
    print(f"   Creating animation with {len(timesteps)} frames...")
    anim = animation.FuncAnimation(fig, animate, frames=len(timesteps), 
                                  interval=1000/fps, blit=False, repeat=True)
    
    # Save animation
    print(f"   Saving to {output_file}...")
    try:
        anim.save(output_file, writer='ffmpeg', fps=fps, bitrate=1800)
        print(f"✅ Animation saved: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving animation: {e}")
        print("   Note: Requires ffmpeg. Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
        # Fallback: save as GIF using Pillow
        try:
            output_gif = output_file.with_suffix('.gif')
            anim.save(output_gif, writer='pillow', fps=fps)
            print(f"✅ Animation saved as GIF: {output_gif}")
            return True
        except Exception as e2:
            print(f"❌ Error saving GIF: {e2}")
            return False
    finally:
        plt.close(fig)


def create_all_animations(results_dir=None):
    """Create animations for all topologies."""
    if results_dir is None:
        results_dir = Path("nuclear_evacuation_results")
    else:
        results_dir = Path(results_dir)
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    topologies = ['Ring', 'Star', 'Linear']
    
    print("\n" + "="*70)
    print("CREATING AGENT MOVEMENT ANIMATIONS")
    print("="*70)
    
    for topology in topologies:
        output_file = results_dir / f'{topology.lower()}_agent_movements.mp4'
        create_animation(results_dir, topology, output_file, fps=2)
    
    print("\n✅ Animation creation complete!")
    print(f"   Check {results_dir} for .mp4 or .gif files")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = "nuclear_evacuation_results"
    
    create_all_animations(results_dir)

