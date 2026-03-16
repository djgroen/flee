#!/usr/bin/env python3
"""
Corrected Agent Movement Visualization

Shows:
- ALL individual agents (one marker per agent)
- Agents colored by CURRENT S1/S2 decision state (not location)
- Small offsets for agents at same location (so all are visible)
- Network topology clearly visible
- S1 flocking behavior (clustering of red agents)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from pathlib import Path
import json
from collections import defaultdict

plt.rcParams['figure.figsize'] = (18, 14)


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


def load_topology_structure(results_dir, topology_name):
    """Load topology structure (locations and routes) from JSON."""
    json_files = sorted(results_dir.glob("nuclear_evacuation_detailed_*.json"))
    if not json_files:
        return None, None
    
    latest = json_files[-1]
    with open(latest, 'r') as f:
        results = json.load(f)
    
    topology_result = [r for r in results if r['topology'] == topology_name]
    if not topology_result:
        return None, None
    
    result = topology_result[0]
    locations = result.get('locations', [])
    routes = result.get('routes', [])
    
    return locations, routes


def create_corrected_animation(results_dir, topology_name, output_file, fps=3, mode='s1s2'):
    """
    Create corrected animation showing ALL individual agents.
    
    Args:
        results_dir: Directory containing results
        topology_name: Name of topology ('Ring', 'Star', 'Linear')
        output_file: Output file path
        fps: Frames per second
        mode: Visualization mode - 's1s2' (S1/S2 state) or 'experience' (high/low experience)
    """
    
    print(f"\n🎬 Creating CORRECTED animation for {topology_name} topology...")
    print(f"   Mode: {mode.upper()}")
    
    # Load agent S2 states (this has the actual decision states)
    agent_s2_states = load_agent_s2_states(results_dir, topology_name)
    if not agent_s2_states:
        print(f"❌ No agent S2 state data available")
        return False
    
    # Load topology structure
    locations, routes = load_topology_structure(results_dir, topology_name)
    if not locations:
        print(f"❌ No topology structure found")
        return False
    
    # Get timesteps
    timesteps = sorted([int(t) for t in agent_s2_states.keys()])
    if not timesteps:
        print(f"❌ No timesteps found")
        return False
    
    # Count agents
    first_timestep = agent_s2_states[str(timesteps[0])]
    num_agents = len(first_timestep)
    print(f"   Found {num_agents} agents across {len(timesteps)} timesteps")
    print(f"   Network: {len(locations)} locations, {len(routes)} routes")
    
    # Load S2 rates for display
    json_files = sorted(results_dir.glob("nuclear_evacuation_detailed_*.json"))
    s2_rates = []
    if json_files:
        with open(json_files[-1], 'r') as f:
            results = json.load(f)
        topology_result = [r for r in results if r['topology'] == topology_name]
        if topology_result:
            s2_rates = topology_result[0].get('s2_activations_by_time', [])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(18, 14))
    
    # Color scheme
    colors = {
        'S1': '#e74c3c',  # Red for S1 (reactive/flocking)
        'S2': '#2ecc71',  # Green for S2 (deliberative/individual)
        'SafeZone': '#3498db',  # Blue
        'Facility': '#e67e22',  # Orange
        'Location': '#95a5a6',  # Gray
        'Route': '#34495e',  # Dark gray
        'Background': '#f8f9fa',  # Very light gray
        # Experience colors
        'LowExpS1': '#ff6b6b',   # Light red for low exp S1
        'HighExpS1': '#c92a2a',  # Dark red for high exp S1
        'LowExpS2': '#51cf66',  # Light green for low exp S2
        'HighExpS2': '#2b8a3e'   # Dark green for high exp S2
    }
    
    # Draw network topology (STATIC BACKGROUND)
    ax.set_facecolor(colors['Background'])
    
    # Draw routes/edges
    location_dict = {loc['name']: loc for loc in locations}
    for route in routes:
        from_loc = location_dict.get(route['from'])
        to_loc = location_dict.get(route['to'])
        if from_loc and to_loc:
            ax.plot([from_loc['x'], to_loc['x']], 
                   [from_loc['y'], to_loc['y']], 
                   'k-', linewidth=2.5, alpha=0.4, zorder=1, linestyle='-')
    
    # Draw locations - USE TYPE FIELD, not just name
    # Store safe zone text objects for updating population counts
    safe_zone_texts = {}  # location_name -> text_object
    
    for loc in locations:
        x, y = loc['x'], loc['y']
        name = loc['name']
        loc_type = loc.get('type', 'town')  # Get actual type from location data
        conflict = loc.get('conflict', 0.0)
        
        # Safe zones (camps) - VERY DISTINCT
        if loc_type == 'camp' or 'SafeZone' in name:
            ax.scatter(x, y, s=1200, c='#2ecc71', marker='s',  # Green square, larger
                      alpha=0.8, zorder=3, edgecolors='darkgreen', linewidths=5)
            # Label with "SAFE ZONE" and placeholder for population count
            safe_zone_texts[name] = ax.text(x, y + 30, 'SAFE ZONE\n(0)', ha='center', 
                   fontsize=14, fontweight='bold', 
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', 
                            edgecolor='darkgreen', linewidth=2, alpha=0.9),
                   zorder=20)  # High zorder to stay on top
        # Facility (conflict zone) - DISTINCT
        elif loc_type == 'conflict' or 'Facility' in name:
            ax.scatter(x, y, s=1200, c='#e74c3c', marker='*',  # Red star, larger
                      alpha=0.8, zorder=3, edgecolors='darkred', linewidths=5)
            ax.text(x, y + 30, 'FACILITY', ha='center', fontsize=16, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', 
                            edgecolor='darkred', linewidth=2, alpha=0.9))
        # Towns (intermediate locations) - SMALLER, DIFFERENT COLOR
        else:
            alpha = 0.5 + (1 - conflict) * 0.3
            ax.scatter(x, y, s=200, c='#95a5a6', marker='o',  # Gray circle, smaller
                      alpha=alpha, zorder=2, edgecolors='#7f8c8d', linewidths=1.5)
            # Optional: label intermediate locations (can be removed if too cluttered)
            # ax.text(x, y - 15, name.split('_')[-1] if '_' in name else name[:8], 
            #        ha='center', fontsize=8, alpha=0.6)
    
    # Initialize agent plots based on mode
    if mode == 's1s2':
        # MODE 1: S1/S2 State (original)
        scatter_s1 = ax.scatter([], [], c=colors['S1'], s=100, alpha=0.8, 
                               label='System 1 (Reactive/Flocking)', zorder=15, 
                               edgecolors='darkred', linewidths=1.5, marker='o')
        scatter_s2 = ax.scatter([], [], c=colors['S2'], s=100, alpha=0.8, 
                               label='System 2 (Deliberative/Individual)', zorder=15, 
                               edgecolors='darkgreen', linewidths=1.5, marker='s')
        scatter_plots = [scatter_s1, scatter_s2]
    else:
        # MODE 2: Experience Levels
        scatter_s1_low = ax.scatter([], [], c=colors['LowExpS1'], s=80, alpha=0.7, 
                                   label='S1 (Low Experience)', zorder=14, 
                                   edgecolors='darkred', linewidths=1, marker='o')
        scatter_s1_high = ax.scatter([], [], c=colors['HighExpS1'], s=120, alpha=0.9, 
                                    label='S1 (High Experience)', zorder=15, 
                                    edgecolors='darkred', linewidths=2, marker='o')
        scatter_s2_low = ax.scatter([], [], c=colors['LowExpS2'], s=80, alpha=0.7, 
                                   label='S2 (Low Experience)', zorder=14, 
                                   edgecolors='darkgreen', linewidths=1, marker='s')
        scatter_s2_high = ax.scatter([], [], c=colors['HighExpS2'], s=120, alpha=0.9, 
                                    label='S2 (High Experience)', zorder=15, 
                                    edgecolors='darkgreen', linewidths=2, marker='s')
        scatter_plots = [scatter_s1_low, scatter_s1_high, scatter_s2_low, scatter_s2_high]
    
    # Title
    title = ax.text(0.5, 0.98, '', transform=ax.transAxes, 
                   ha='center', fontsize=20, fontweight='bold')
    subtitle = ax.text(0.5, 0.94, '', transform=ax.transAxes, 
                      ha='center', fontsize=16)
    
    ax.set_xlabel('X Coordinate', fontsize=16)
    ax.set_ylabel('Y Coordinate', fontsize=16)
    ax.legend(loc='upper left', fontsize=14, framealpha=0.95, markerscale=1.5)
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=1)
    
    # Set FIXED axis limits based on topology structure (same throughout animation)
    all_x = [loc['x'] for loc in locations]
    all_y = [loc['y'] for loc in locations]
    x_min, x_max = min(all_x) - 50, max(all_x) + 50
    y_min, y_max = min(all_y) - 50, max(all_y) + 50
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    
    def animate(frame):
        """Animation function - shows ALL agents with their current S1/S2 state or experience level."""
        t = timesteps[frame] if frame < len(timesteps) else timesteps[-1]
        
        # Get agent states for this timestep
        t_states = agent_s2_states.get(str(t), {})
        if not t_states:
            if mode == 's1s2':
                return scatter_plots[0], scatter_plots[1], title, subtitle
            else:
                return scatter_plots[0], scatter_plots[1], scatter_plots[2], scatter_plots[3], title, subtitle
        
        if mode == 's1s2':
            # MODE 1: Separate by S1/S2 state only
            s1_positions = []
            s2_positions = []
            
            for agent_id, state in t_states.items():
                x = state.get('x', 0.0)
                y = state.get('y', 0.0)
                cognitive_state = state.get('cognitive_state', 'S1')
                s2_active = state.get('s2_active', False)
                
                if cognitive_state == 'S2' or s2_active:
                    s2_positions.append([x, y])
                else:
                    s1_positions.append([x, y])
            
            # Update scatter plots
            marker_size = max(8, min(60, 6000 / num_agents))  # Increased base size
            
            if len(s1_positions) > 0:
                scatter_plots[0].set_offsets(np.array(s1_positions))
                scatter_plots[0].set_sizes([marker_size] * len(s1_positions))
            else:
                scatter_plots[0].set_offsets(np.empty((0, 2)))
            
            if len(s2_positions) > 0:
                scatter_plots[1].set_offsets(np.array(s2_positions))
                scatter_plots[1].set_sizes([marker_size] * len(s2_positions))
            else:
                scatter_plots[1].set_offsets(np.empty((0, 2)))
            
            # Count agents at each safe zone location
            location_counts = {}  # location_name -> count
            for agent_id, state in t_states.items():
                location_name = state.get('location', '')
                if 'SafeZone' in location_name or location_name in safe_zone_texts:
                    location_counts[location_name] = location_counts.get(location_name, 0) + 1
            
            # Update safe zone population counters
            for loc_name, text_obj in safe_zone_texts.items():
                count = location_counts.get(loc_name, 0)
                # Extract base name (e.g., "SafeZone1" -> "SafeZone 1")
                display_name = loc_name.replace('SafeZone', 'Safe Zone ')
                text_obj.set_text(f'{display_name}\n({count} agents)')
            
            # Update title
            s2_rate = s2_rates[t] if t < len(s2_rates) else 0.0
            total_at_safe = sum(location_counts.values())
            title.set_text(f'{topology_name} Topology - Time Step {t} | {num_agents} Agents')
            subtitle.set_text(f'S2 Activation: {s2_rate:.1f}% | S1: {len(s1_positions)} | S2: {len(s2_positions)} | At Safe Zones: {total_at_safe}')
            
            return_items = [scatter_plots[0], scatter_plots[1], title, subtitle] + list(safe_zone_texts.values())
            return tuple(return_items)
        
        else:
            # MODE 2: Separate by S1/S2 AND experience level
            s1_low_positions = []
            s1_high_positions = []
            s2_low_positions = []
            s2_high_positions = []
            
            # Calculate experience threshold (median)
            experience_values = [state.get('experience_index', 0.0) for state in t_states.values()]
            if experience_values:
                exp_threshold = np.median(experience_values)
            else:
                exp_threshold = 0.4  # Default
            
            for agent_id, state in t_states.items():
                x = state.get('x', 0.0)
                y = state.get('y', 0.0)
                cognitive_state = state.get('cognitive_state', 'S1')
                s2_active = state.get('s2_active', False)
                experience_index = state.get('experience_index', 0.0)
                
                is_high_exp = experience_index >= exp_threshold
                
                if cognitive_state == 'S2' or s2_active:
                    if is_high_exp:
                        s2_high_positions.append([x, y])
                    else:
                        s2_low_positions.append([x, y])
                else:
                    if is_high_exp:
                        s1_high_positions.append([x, y])
                    else:
                        s1_low_positions.append([x, y])
            
            # Update scatter plots
            marker_size = max(8, min(60, 6000 / num_agents))  # Increased base size
            marker_size_large = int(marker_size * 1.8)  # Larger for high experience
            
            for scatter, positions, size in [
                (scatter_plots[0], s1_low_positions, marker_size),
                (scatter_plots[1], s1_high_positions, marker_size_large),
                (scatter_plots[2], s2_low_positions, marker_size),
                (scatter_plots[3], s2_high_positions, marker_size_large)
            ]:
                if len(positions) > 0:
                    scatter.set_offsets(np.array(positions))
                    scatter.set_sizes([size] * len(positions))
                else:
                    scatter.set_offsets(np.empty((0, 2)))
            
            # Count agents at each safe zone location
            location_counts = {}  # location_name -> count
            for agent_id, state in t_states.items():
                location_name = state.get('location', '')
                if 'SafeZone' in location_name or location_name in safe_zone_texts:
                    location_counts[location_name] = location_counts.get(location_name, 0) + 1
            
            # Update safe zone population counters
            for loc_name, text_obj in safe_zone_texts.items():
                count = location_counts.get(loc_name, 0)
                display_name = loc_name.replace('SafeZone', 'Safe Zone ')
                text_obj.set_text(f'{display_name}\n({count} agents)')
            
            # Update title with experience stats
            s2_rate = s2_rates[t] if t < len(s2_rates) else 0.0
            high_exp_count = len(s1_high_positions) + len(s2_high_positions)
            low_exp_count = len(s1_low_positions) + len(s2_low_positions)
            total_at_safe = sum(location_counts.values())
            title.set_text(f'{topology_name} Topology - Time Step {t} | {num_agents} Agents')
            subtitle.set_text(f'S2: {s2_rate:.1f}% | High Exp: {high_exp_count} | Low Exp: {low_exp_count} | At Safe Zones: {total_at_safe}')
            
            return_items = [scatter_plots[0], scatter_plots[1], scatter_plots[2], scatter_plots[3], title, subtitle] + list(safe_zone_texts.values())
            return tuple(return_items)
            
            return scatter_plots[0], scatter_plots[1], scatter_plots[2], scatter_plots[3], title, subtitle
    
    # Create animation
    print(f"   Creating animation with {len(timesteps)} frames...")
    anim = animation.FuncAnimation(fig, animate, frames=len(timesteps), 
                                  interval=1000/fps, blit=False, repeat=True)
    
    # Save as MP4 (Mac-friendly format)
    print(f"   Saving to {output_file}...")
    
    saved = False
    
    # Method 1: Try imageio first (works without ffmpeg, Mac-friendly)
    try:
        import imageio
        print(f"   Using imageio to create MP4...")
        
        # Save frames as temporary images
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp()
        frame_files = []
        
        print(f"   Rendering {len(timesteps)} frames...")
        for i in range(len(timesteps)):
            animate(i)
            frame_file = os.path.join(temp_dir, f'frame_{i:04d}.png')
            fig.savefig(frame_file, dpi=100, bbox_inches='tight', facecolor='white')
            frame_files.append(frame_file)
            if (i + 1) % 5 == 0:
                print(f"      Rendered {i+1}/{len(timesteps)} frames...")
        
        # Create MP4 from frames
        print(f"   Creating MP4 video...")
        # Try with ffmpeg plugin, fallback to default
        try:
            writer = imageio.get_writer(str(output_file), fps=fps, codec='libx264', quality=8)
        except ValueError:
            # Fallback: use default codec
            writer = imageio.get_writer(str(output_file), fps=fps)
        
        with writer:
            for i, frame_file in enumerate(frame_files):
                writer.append_data(imageio.imread(frame_file))
                if (i + 1) % 5 == 0:
                    print(f"      Encoded {i+1}/{len(frame_files)} frames...")
        
        # Cleanup
        for frame_file in frame_files:
            os.remove(frame_file)
        os.rmdir(temp_dir)
        
        print(f"✅ Animation saved as MP4 using imageio: {output_file}")
        saved = True
    except ImportError:
        print(f"⚠️  imageio not available. Install with: pip install imageio")
    except Exception as e:
        print(f"⚠️  imageio failed: {e}")
        import traceback
        traceback.print_exc()
    
    if not saved:
        # Final fallback: GIF
        print(f"⚠️  Video writers not available, saving as GIF...")
        output_gif = output_file.with_suffix('.gif')
        try:
            anim.save(output_gif, writer='pillow', fps=fps)
            print(f"✅ Animation saved as GIF: {output_gif}")
            print(f"   Note: Install ffmpeg for MP4: brew install ffmpeg")
            saved = True
        except Exception as e2:
            print(f"❌ Error saving GIF: {e2}")
            saved = False
    
    plt.close(fig)
    return saved


def create_all_corrected_animations(results_dir=None, mode='s1s2'):
    """
    Create corrected animations for all topologies.
    
    Args:
        results_dir: Directory containing results
        mode: 's1s2' for S1/S2 state visualization, 'experience' for experience level visualization
    """
    if results_dir is None:
        results_dir = Path("nuclear_evacuation_results")
    else:
        results_dir = Path(results_dir)
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    topologies = ['Ring', 'Star', 'Linear']
    
    mode_label = "S1/S2 Decision State" if mode == 's1s2' else "Experience Levels"
    print("\n" + "="*70)
    print(f"CREATING CORRECTED AGENT MOVEMENT ANIMATIONS")
    print(f"Mode: {mode_label}")
    print("="*70)
    
    for topology in topologies:
        suffix = '_s1s2' if mode == 's1s2' else '_experience'
        output_file = results_dir / f'{topology.lower()}_agent_movements{suffix}.mp4'
        create_corrected_animation(results_dir, topology, output_file, fps=3, mode=mode)
    
    print(f"\n✅ {mode_label} animation creation complete!")


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Create agent movement animations')
    parser.add_argument('--results-dir', type=str, default='nuclear_evacuation_results',
                       help='Directory containing simulation results')
    parser.add_argument('--mode', type=str, choices=['s1s2', 'experience', 'both'], 
                       default='both',
                       help='Visualization mode: s1s2 (S1/S2 state), experience (high/low experience), or both')
    
    args = parser.parse_args()
    
    if args.mode == 'both':
        # Create both versions
        create_all_corrected_animations(args.results_dir, mode='s1s2')
        create_all_corrected_animations(args.results_dir, mode='experience')
    else:
        create_all_corrected_animations(args.results_dir, mode=args.mode)

