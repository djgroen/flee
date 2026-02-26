#!/usr/bin/env python3
"""
Refugee Movement Visualization: Agent Animations

Creates animated visualizations for refugee simulation scenarios showing:
- Agent movements colored by S1/S2 cognitive state
- Route choices (nearest border vs. calculated routes)
- Social connection effects
- Context-dependent processing (high conflict → S1, recovery → S2)

Matches nuclear animation formatting and style.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from pathlib import Path
import json
from collections import defaultdict

plt.rcParams['figure.figsize'] = (18, 14)


def load_refugee_results(scenario_dir):
    """Load refugee simulation results from JSON."""
    result_files = sorted(scenario_dir.glob("*_results.json"))
    if not result_files:
        return None
    
    latest = result_files[-1]
    with open(latest, 'r') as f:
        return json.load(f)


def load_agent_logs(scenario_dir, scenario_name):
    """Load agent movement logs from Flee output (CSV format)."""
    agents_file = scenario_dir / "agents.out.0"
    if not agents_file.exists():
        # Try alternative location
        agents_file = scenario_dir.parent / "agents.out.0"
        if not agents_file.exists():
            return None
    
    try:
        # Read CSV format (Flee outputs CSV with header starting with #)
        # First, read the header line (starts with #)
        with open(agents_file, 'r') as f:
            header_line = f.readline().strip()
            if header_line.startswith('#'):
                header_line = header_line[1:]  # Remove #
            # Parse header - handle trailing comma
            header_cols = [col.strip() for col in header_line.split(',')]
            # Remove empty trailing column if present
            if header_cols and header_cols[-1] == '':
                header_cols = header_cols[:-1]
        
        # Read the CSV file (skip the comment line, handle bad lines)
        # Read as strings first to handle variable column counts, then assign names
        try:
            df = pd.read_csv(agents_file, comment='#', header=None, 
                           on_bad_lines='skip', engine='python', sep=',', 
                           skipinitialspace=True, dtype=str)
        except TypeError:
            # Older pandas version
            df = pd.read_csv(agents_file, comment='#', header=None, 
                           error_bad_lines=False, warn_bad_lines=False, engine='python', 
                           sep=',', skipinitialspace=True, dtype=str)
        
        # Drop rows with all NaN or empty
        df = df.dropna(how='all')
        # Remove rows where first column (time) is empty
        if len(df.columns) > 0:
            df = df[df.iloc[:, 0].notna() & (df.iloc[:, 0] != '')]
        
        # Assign column names (handle variable number of columns)
        num_cols = len(df.columns)
        num_header_cols = len(header_cols)
        if num_cols == num_header_cols:
            df.columns = header_cols
        elif num_cols > num_header_cols:
            # Extra column (likely trailing empty column from trailing comma)
            df.columns = header_cols + [f'extra_col_{i}' for i in range(num_cols - num_header_cols)]
            # Drop empty trailing columns
            for col in df.columns[num_header_cols:]:
                if df[col].isna().all() or (df[col].astype(str).str.strip() == '').all():
                    df = df.drop(columns=[col])
        else:
            # Fewer columns than header - use what we have
            df.columns = header_cols[:num_cols]
        
        # Map column names (Flee uses different names)
        # Extract agent ID from rank-agentid format (e.g., "0-0" -> 0)
        if 'rank-agentid' in df.columns:
            # Safely extract agent ID: split on '-' and take last part, convert to int
            def extract_agent_id(val):
                try:
                    if pd.isna(val):
                        return 0
                    val_str = str(val)
                    if '-' in val_str:
                        return int(val_str.split('-')[-1])
                    else:
                        return int(val_str)
                except (ValueError, AttributeError):
                    return 0
            df['agent_id'] = df['rank-agentid'].apply(extract_agent_id)
        elif 'agent_id' not in df.columns:
            # Fallback: use index
            df['agent_id'] = df.index
        
        # Map location column
        if 'current_location' in df.columns:
            df['location'] = df['current_location'].astype(str)
        elif 'location' not in df.columns:
            df['location'] = 'Unknown'
        
        # Map coordinate columns
        if 'gps_x' in df.columns:
            df['x'] = pd.to_numeric(df['gps_x'], errors='coerce')
        if 'gps_y' in df.columns:
            df['y'] = pd.to_numeric(df['gps_y'], errors='coerce')
        
        # Map time column
        if 'time' in df.columns:
            df['time'] = pd.to_numeric(df['time'], errors='coerce').fillna(0).astype(int)
        else:
            df['time'] = 0
        
        # Drop rows with missing coordinates
        df = df.dropna(subset=['x', 'y'])
        
        # Ensure we have required columns
        required_cols = ['time', 'agent_id', 'location', 'x', 'y']
        if not all(col in df.columns for col in required_cols):
            print(f"⚠️  Missing required columns. Available: {df.columns.tolist()}")
            return None
        
        # Select only required columns
        df = df[required_cols].copy()
        
        # Convert types
        df['time'] = df['time'].astype(int)
        df['agent_id'] = df['agent_id'].astype(int)
        df['x'] = df['x'].astype(float)
        df['y'] = df['y'].astype(float)
        
        return df
    except Exception as e:
        print(f"⚠️  Error loading agent logs: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_refugee_animation(scenario_dir, scenario_name, output_file, fps=3):
    """
    Create animation for refugee scenario showing agent movements.
    Matches nuclear animation formatting and style.
    
    Args:
        scenario_dir: Directory containing scenario results
        scenario_name: Name of scenario
        output_file: Output file path (MP4)
        fps: Frames per second
    """
    
    print(f"\n🎬 Creating animation for scenario: {scenario_name}")
    
    # Load results
    results = load_refugee_results(scenario_dir)
    if not results:
        print(f"❌ No results found in {scenario_dir}")
        return False
    
    # Load agent logs
    agent_df = load_agent_logs(scenario_dir, scenario_name)
    
    # Get topology structure
    locations = results.get('locations', [])
    routes = results.get('routes', [])
    metrics = results.get('metrics', {})
    
    # Get agent states from metrics
    agent_states = metrics.get('agent_states', [])
    
    # Get timesteps
    timesteps = metrics.get('timesteps', [])
    if not timesteps:
        print(f"❌ No timesteps found")
        return False
    
    print(f"   Found {len(timesteps)} timesteps")
    print(f"   Network: {len(locations)} locations, {len(routes)} routes")
    
    # Create figure (match nuclear animation size)
    fig, ax = plt.subplots(figsize=(18, 14))
    
    # Color scheme (match nuclear animations)
    colors = {
        'S1': '#e74c3c',  # Red for System 1 (reactive/flocking)
        'S2': '#2ecc71',  # Green for System 2 (deliberative/individual)
        'SafeZone': '#3498db',  # Blue
        'Facility': '#e67e22',  # Orange
        'Location': '#95a5a6',  # Gray
        'Route': '#34495e',  # Dark gray
        'Background': '#f8f9fa',  # Very light gray
    }
    
    # Draw network topology (STATIC BACKGROUND - match nuclear style)
    ax.set_facecolor(colors['Background'])
    
    # Draw routes/edges
    location_dict = {loc['name']: loc for loc in locations}
    for route in routes:
        from_loc = location_dict.get(route['from'])
        to_loc = location_dict.get(route['to'])
        if from_loc and to_loc:
            ax.plot([from_loc['x'], to_loc['x']], 
                   [from_loc['y'], to_loc['y']], 
                   'k-', linewidth=2.5, alpha=0.4, zorder=1)
    
    # Draw locations - USE TYPE FIELD, match nuclear style
    # Store safe zone text objects for updating population counts
    safe_zone_texts = {}  # location_name -> text_object
    
    for loc in locations:
        x, y = loc['x'], loc['y']
        name = loc['name']
        loc_type = loc.get('type', 'town')  # Get actual type from location data
        conflict = loc.get('conflict', 0.0)
        
        # Safe zones (camps) - VERY DISTINCT (match nuclear style)
        if loc_type == 'camp' or 'SafeZone' in name or 'Border' in name:
            ax.scatter(x, y, s=1200, c='#2ecc71', marker='s',  # Green square, larger
                      alpha=0.8, zorder=3, edgecolors='darkgreen', linewidths=5)
            # Label with "SAFE ZONE" and placeholder for population count
            safe_zone_texts[name] = ax.text(x, y + 30, 'SAFE ZONE\n(0)', ha='center', 
                   fontsize=14, fontweight='bold', 
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', 
                            edgecolor='darkgreen', linewidth=2, alpha=0.9),
                   zorder=20)  # High zorder to stay on top
        # Conflict zone - DISTINCT (match nuclear style)
        elif loc_type == 'conflict' or 'Conflict' in name:
            ax.scatter(x, y, s=1200, c='#e74c3c', marker='*',  # Red star, larger
                      alpha=0.8, zorder=3, edgecolors='darkred', linewidths=5)
            ax.text(x, y + 30, 'CONFLICT ZONE', ha='center', fontsize=16, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', 
                            edgecolor='darkred', linewidth=2, alpha=0.9))
        # Towns (intermediate locations) - SMALLER, DIFFERENT COLOR
        else:
            alpha = 0.5 + (1 - conflict) * 0.3
            ax.scatter(x, y, s=200, c='#95a5a6', marker='o',  # Gray circle, smaller
                      alpha=alpha, zorder=2, edgecolors='#7f8c8d', linewidths=1.5)
    
    # Prepare agent data (match nuclear style - use x,y coordinates directly)
    # Create agent position dictionary from metrics
    agent_positions = {}  # timestep -> {agent_id: (x, y, state)}
    
    # PREFERRED: Use agent_df (has all agents at all timesteps with actual coordinates)
    if agent_df is not None and len(agent_df) > 0:
        print(f"   Using agent log data (all agents, all timesteps)")
        print(f"   Agent log: {len(agent_df)} rows, {agent_df['time'].nunique()} timesteps")
        # Get available timesteps from agent log (may differ from metrics timesteps)
        available_timesteps = sorted(agent_df['time'].unique())
        print(f"   Available timesteps in log: {min(available_timesteps)} to {max(available_timesteps)}")
        
        # Use available timesteps from agent log instead of metrics timesteps
        # This ensures we don't try to animate timesteps that don't exist
        timesteps = available_timesteps
        print(f"   Using {len(timesteps)} timesteps from agent log: {timesteps[0]} to {timesteps[-1]}")
        
        for t in timesteps:
            agent_positions[t] = {}
            
            # Use closest available timestep if exact match not found
            if t not in available_timesteps:
                # Find closest available timestep
                closest_t = min(available_timesteps, key=lambda x: abs(x - t))
                if abs(closest_t - t) <= 1:  # Only use if within 1 timestep
                    t = closest_t
                else:
                    continue  # Skip if too far away
            
            t_data = agent_df[agent_df['time'] == t]
            print(f"   Timestep {t}: {len(t_data)} agents")
            for _, row in t_data.iterrows():
                agent_id = f"agent_{int(row['agent_id'])}"  # Match ID format
                agent_id_num = int(row['agent_id'])  # Numeric ID for deterministic hashing
                x, y = float(row['x']), float(row['y'])
                location_name = str(row.get('location', 'Unknown'))
                
                # Check if agent is in a safe zone (camp) - still need jitter to prevent overlap!
                is_safe_zone = ('camp' in location_name.lower() or 
                               'border' in location_name.lower() or 
                               'safezone' in location_name.lower() or
                               location_name.startswith('Border'))
                
                # Check if agent is on a route (travelling) - use origin location coordinates
                is_travelling = location_name.startswith('L:') or ':' in location_name
                if is_travelling:
                    # Extract origin location from route name (e.g., "L:ConflictZone:Town1" -> "ConflictZone")
                    origin_loc = location_name.split(':')[1] if ':' in location_name else location_name
                    # Find origin location coordinates
                    origin_coords = location_dict.get(origin_loc)
                    if origin_coords:
                        # Use origin location, but interpolate position along route
                        # For now, use origin location to show they're starting from there
                        x, y = origin_coords['x'], origin_coords['y']
                        location_name = origin_loc  # Use origin location for jitter calculation
                
                # Add DETERMINISTIC jitter based on agent ID and location
                # Same agent at same location = same offset every timestep
                # Different agents at same location = different offsets (no overlap)
                # IMPORTANT: Apply to ALL locations (including safe zones) to prevent overlap
                offset_radius = 30.0 if not is_safe_zone else 25.0  # Slightly smaller for safe zones
                # Use hash of agent_id + location_name to generate consistent but unique offsets
                import hashlib
                hash_input = f"{agent_id_num}_{location_name}".encode('utf-8')
                hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
                # Use hash to generate deterministic but pseudo-random offsets
                # Use both x and y from different parts of hash to ensure uniqueness
                np.random.seed(hash_value % (2**32))  # Seed from hash
                offset_x = np.random.uniform(-offset_radius, offset_radius)
                # Use a different seed derived from hash for y to ensure independence
                np.random.seed((hash_value + 12345) % (2**32))  # Different seed for y
                offset_y = np.random.uniform(-offset_radius, offset_radius)
                x += offset_x
                y += offset_y
                
                # Try to get cognitive state from metrics (if available)
                # IMPORTANT: Agents in safe zones can be S2, so don't default to S1
                cognitive_state = 'S1'  # Default
                for state_entry in agent_states:
                    if state_entry['timestep'] == t:
                        for agent in state_entry['agents']:
                            # Match by agent ID (handle different ID formats)
                            agent_entry_id = str(agent.get('id', ''))
                            if agent_entry_id == str(agent_id) or agent_entry_id == str(int(row['agent_id'])):
                                cognitive_state = agent.get('cognitive_state', 'S1')
                                break
                
                # If in safe zone and we don't have cognitive state, check if connections suggest S2 capability
                if is_safe_zone and cognitive_state == 'S1':
                    # Try to infer from connections (if agent has connections >= 2, might be S2 capable)
                    # But we'll keep S1 as default since we don't have full state info
                    pass
                
                agent_positions[t][agent_id] = (x, y, cognitive_state)
        
        # Debug: Check first few timesteps
        print(f"   Sample agent positions: t=0 has {len(agent_positions.get(0, {}))} agents")
        if 0 in agent_positions and len(agent_positions[0]) > 0:
            sample_agent = list(agent_positions[0].values())[0]
            print(f"   Sample agent data: x={sample_agent[0]:.1f}, y={sample_agent[1]:.1f}, state={sample_agent[2]}")
    else:
        # Fallback: Use agent_states from metrics
        print(f"   Using agent_states from metrics (limited timesteps)")
        for state_entry in agent_states:
            t = state_entry['timestep']
            agent_positions[t] = {}
            
            for agent in state_entry['agents']:
                agent_id = agent['id']
                cognitive_state = agent.get('cognitive_state', 'S1')
                
                # Use stored x,y coordinates if available (preferred)
                if 'x' in agent and 'y' in agent:
                    x, y = agent['x'], agent['y']
                else:
                    # Fallback: get from location
                    loc_name = agent['location']
                    loc = location_dict.get(loc_name)
                    if loc:
                        x, y = loc['x'], loc['y']
                        # Add small random offset to prevent overlap
                        x += np.random.uniform(-10, 10)
                        y += np.random.uniform(-10, 10)
                    else:
                        continue  # Skip if location not found
                
                agent_positions[t][agent_id] = (x, y, cognitive_state)
    
    # Initialize agent plots (match nuclear style)
    scatter_s1 = ax.scatter([], [], c=colors['S1'], s=100, alpha=0.8, 
                           label='System 1 (Reactive/Flocking)', zorder=15, 
                           edgecolors='darkred', linewidths=1.5, marker='o')
    scatter_s2 = ax.scatter([], [], c=colors['S2'], s=100, alpha=0.8, 
                           label='System 2 (Deliberative/Individual)', zorder=15, 
                           edgecolors='darkgreen', linewidths=1.5, marker='s')
    
    # Title and subtitle (match nuclear style)
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
        """Animation function (match nuclear style)."""
        # Make sure we don't go beyond available timesteps
        if frame >= len(timesteps):
            frame = len(timesteps) - 1
        t = timesteps[frame]
        
        # Update title and subtitle
        title.set_text(f'{scenario_name}')
        subtitle.set_text(f'Timestep {t}')
        
        # Get agent positions for this timestep
        t_positions = agent_positions.get(t, {})
        
        # Separate agents by state
        s1_agents = [(x, y) for x, y, state in t_positions.values() if state == 'S1']
        s2_agents = [(x, y) for x, y, state in t_positions.values() if state == 'S2']
        
        # Update scatter plots (match nuclear style - with sizes)
        marker_size = max(8, min(60, 6000 / max(len(t_positions), 1)))  # Dynamic size based on agent count
        
        if s1_agents:
            s1_positions = [[x, y] for x, y in s1_agents]
            scatter_s1.set_offsets(np.array(s1_positions))
            scatter_s1.set_sizes([marker_size] * len(s1_positions))
            scatter_s1.set_alpha(0.8)
        else:
            scatter_s1.set_offsets(np.empty((0, 2)))
            scatter_s1.set_alpha(0)
        
        if s2_agents:
            s2_positions = [[x, y] for x, y in s2_agents]
            scatter_s2.set_offsets(np.array(s2_positions))
            scatter_s2.set_sizes([marker_size] * len(s2_positions))
            scatter_s2.set_alpha(0.8)
        else:
            scatter_s2.set_offsets(np.empty((0, 2)))
            scatter_s2.set_alpha(0)
        
        # Update population counters
        pop_by_loc = metrics.get('population_by_location', {})
        for loc_name, text_obj in safe_zone_texts.items():
            if loc_name in pop_by_loc and len(pop_by_loc[loc_name]) > frame:
                pop = pop_by_loc[loc_name][frame]
                text_obj.set_text(f'SAFE ZONE\n({int(pop)})')
        
        return [scatter_s1, scatter_s2, title, subtitle] + list(safe_zone_texts.values())
    
    # Create animation
    print(f"   Creating animation ({len(timesteps)} frames)...")
    anim = animation.FuncAnimation(fig, animate, frames=len(timesteps),
                                   interval=1000/fps, blit=False, repeat=True)
    
    # Save animation (match nuclear style - use imageio for MP4)
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
                # Use imageio.v2 to avoid deprecation warning
                try:
                    import imageio.v2 as imageio_v2
                    writer.append_data(imageio_v2.imread(frame_file))
                except ImportError:
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
            print(f"   Note: Install imageio for MP4: pip install imageio")
            saved = True
        except Exception as e2:
            print(f"❌ Failed to save animation: {e2}")
            saved = False
    
    plt.close()
    return saved


def create_all_animations(results_dir="refugee_simulation_results"):
    """Create animations for all scenarios."""
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
    print(f"Creating animations for {len(scenario_dirs)} scenarios")
    print(f"{'='*60}")
    
    for scenario_dir in scenario_dirs:
        scenario_name = scenario_dir.name.replace('_', ' ')
        
        # Create animation (use MP4 format like nuclear)
        # Save animations in dedicated animations folder
        animations_dir = results_dir / "animations"
        animations_dir.mkdir(exist_ok=True)
        output_file = animations_dir / f"{scenario_name.replace(' ', '_')}_animation.mp4"
        create_refugee_animation(scenario_dir, scenario_name, output_file, fps=3)
    
    print(f"\n{'='*60}")
    print(f"All animations complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create refugee movement animations")
    parser.add_argument("--scenario", type=str, help="Specific scenario directory name")
    parser.add_argument("--results-dir", type=str, default="refugee_simulation_results",
                      help="Results directory")
    parser.add_argument("--fps", type=int, default=3, help="Frames per second")
    
    args = parser.parse_args()
    
    if args.scenario:
        # Single scenario
        scenario_dir = Path(args.results_dir) / args.scenario
        if not scenario_dir.exists():
            print(f"❌ Scenario directory not found: {scenario_dir}")
        else:
            # Save animations in dedicated animations folder
            animations_dir = scenario_dir.parent / "animations"
            animations_dir.mkdir(exist_ok=True)
            output_file = animations_dir / f"{args.scenario}_animation.mp4"
            create_refugee_animation(scenario_dir, args.scenario, output_file, fps=args.fps)
    else:
        # All scenarios
        create_all_animations(args.results_dir)
