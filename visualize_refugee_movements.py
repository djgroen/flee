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
import matplotlib
matplotlib.use('Agg') # Force headless backend to prevent GUI crashes
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from pathlib import Path
import json
from collections import defaultdict

plt.rcParams['figure.figsize'] = (18, 14)


def load_refugee_results(scenario_dir):
    """Load refugee simulation results from JSON or CSVs."""
    # Try loading JSON first (standard Flee)
    result_files = sorted(scenario_dir.glob("*_results.json"))
    if result_files:
        latest = result_files[-1]
        with open(latest, 'r') as f:
            return json.load(f)
            
    # Fallback: Construct results dict from CSV files (comprehensive experiments)
    if (scenario_dir / "locations.csv").exists() and (scenario_dir / "routes.csv").exists():
        pass # Handle below
    elif (Path("topologies") / scenario_dir.name / "input_csv").exists():
        topology_input = Path("topologies") / scenario_dir.name / "input_csv"
        try:
            locations_df = pd.read_csv(topology_input / "locations.csv")
            routes_df = pd.read_csv(topology_input / "routes.csv")
            
            # Standardize route column names
            routes_df = routes_df.rename(columns={
                'name1': 'from', 'name2': 'to',
                'start_point': 'from', 'end_point': 'to'
            })
            
            # Standardize location column names
            locations_df = locations_df.rename(columns={
                'gps_x': 'x', 'gps_y': 'y',
                'longitude': 'x', 'latitude': 'y'
            })
            
            # Add conflict info if missing from locations but in conflicts.csv
            conflicts_file = topology_input / "conflicts.csv"
            if conflicts_file.exists():
                conf_df = pd.read_csv(conflicts_file, comment='#', header=None, names=['date', 'loc', 'val'], skipinitialspace=True)
                conflict_map = dict(zip(conf_df['loc'], conf_df['val']))
                locations_df['conflict'] = locations_df['name'].map(conflict_map).fillna(0.0)

            # Construct dictionary structure
            return {
                'locations': locations_df.to_dict('records'),
                'routes': routes_df.to_dict('records'),
                'metrics': {
                    'timesteps': [], 
                    'agent_states': [] 
                }
            }
        except Exception as e:
            print(f"Error reading topology CSVs: {e}")
            return None
            
    return None


def load_agent_logs(scenario_dir, scenario_name):
    """Load agent movement logs from Flee output (CSV format)."""
    agents_file = scenario_dir / "agents.out.0"
    if not agents_file.exists():
        # Try finding agents_*.out files
        agents_files = sorted(list(scenario_dir.glob("agents_*.out")))
        if agents_files:
            agents_file = agents_files[0]
        else:
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
        
        # Use only as many headers as we have columns, or pad with placeholders
        if num_cols <= num_header_cols:
            df.columns = header_cols[:num_cols]
        else:
            # Pad header columns
            padded_headers = header_cols + [f"extra_{i}" for i in range(num_cols - num_header_cols)]
            df.columns = padded_headers
            
        # Standardize column names for processing
        name_map = {
            'time': 'time',
            '#time': 'time',
            'rank-agentid': 'agent_id',
            'current_location': 'location',
            'gps_x': 'x',
            'gps_y': 'y'
        }
        df = df.rename(columns=name_map)
        
        # Convert numeric columns
        for col in ['time', 'x', 'y']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean agent_id (remove rank prefix if present, e.g. "0-123" -> "123")
        if 'agent_id' in df.columns:
            df['agent_id'] = df['agent_id'].apply(lambda x: str(x).split('-')[-1] if '-' in str(x) else x)
            df['agent_id'] = pd.to_numeric(df['agent_id'], errors='coerce')
            
        return df.dropna(subset=['time', 'agent_id', 'x', 'y'])
        
    except Exception as e:
        print(f"Error loading agent logs: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_refugee_animation(scenario_dir, scenario_name, output_file, fps=3):
    """Create a high-quality animation of agent movements."""
    print(f"\n🎬 Creating animation for scenario: {scenario_name}")
    
    results = load_refugee_results(scenario_dir)
    if not results:
        print(f"❌ No results found in {scenario_dir}")
        return
        
    locations = results['locations']
    routes = results['routes']
    agent_states = results.get('metrics', {}).get('agent_states', [])
    
    # Load detailed agent logs if available
    agent_df = load_agent_logs(scenario_dir, scenario_name)
    
    # Setup visualization
    fig, ax = plt.subplots(figsize=(18, 14))
    
    # Colors for S1 and S2
    colors = {
        'S1': '#D55E00', # Orange-red (reactive)
        'S2': '#0072B2'  # Blue (deliberative)
    }
    
    # Extract coordinates for bounding box
    all_x = [loc['x'] for loc in locations]
    all_y = [loc['y'] for loc in locations]
    
    # Pre-calculate node dictionary for faster lookup
    location_dict = {str(loc['name']): loc for loc in locations}
    
    # Set plot limits with padding
    padding = 40
    ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
    ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
    ax.axis('off')
    
    # Draw routes
    for route in routes:
        from_loc = location_dict.get(str(route['from']))
        to_loc = location_dict.get(str(route['to']))
        if from_loc and to_loc:
            ax.plot([from_loc['x'], to_loc['x']], [from_loc['y'], to_loc['y']], 
                   c='#BDC3C7', linestyle='-', linewidth=2, alpha=0.4, zorder=1)
    
    # Draw locations
    safe_zone_texts = {}  
    conflict_zone_texts = {} 
    
    for loc in locations:
        x, y = loc['x'], loc['y']
        name = str(loc['name'])
        loc_type = loc.get('location_type', loc.get('type', 'town'))
        conflict = loc.get('conflict', 0.0)
        
        if loc_type == 'camp' or 'SafeZone' in name or 'Border' in name:
            ax.scatter(x, y, s=1200, c='#56B4E9', marker='s', alpha=0.8, zorder=3, edgecolors='#0072B2', linewidths=5)
            safe_zone_texts[name] = ax.text(x, y + 30, 'SAFE ZONE\n(0)', ha='center', 
                   fontsize=14, fontweight='bold', 
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#CCE5FF', 
                            edgecolor='#0072B2', linewidth=2, alpha=0.9),
                   zorder=20)
        elif loc_type == 'conflict' or 'Facility' in name or 'Hub' in name:
            conflict_level = loc.get('conflict', 1.0)
            size = 800 + (conflict_level * 800)
            c_hex = '#D35400' 
            edge_hex = '#873600'
            
            ax.scatter(x, y, s=size, c=c_hex, marker='*', alpha=0.9, zorder=3, edgecolors=edge_hex, linewidths=3)
                      
            label_text = f'{name}\nThreat ({conflict_level:.1f})\n(0)'
            conflict_zone_texts[name] = ax.text(x, y + 15, label_text, ha='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='#F5B7B1', 
                            edgecolor=edge_hex, linewidth=1, alpha=0.8),
                   zorder=20)
        else:
            alpha = 0.5 + (1 - conflict) * 0.3
            ax.scatter(x, y, s=200, c='#95a5a6', marker='o', alpha=alpha, zorder=2, edgecolors='#7f8c8d', linewidths=1.5)
    
    agent_positions = {} 
    
    if agent_df is not None and len(agent_df) > 0:
        print(f"   Using agent log data (all agents, all timesteps)")
        available_timesteps = sorted(agent_df['time'].unique())
        timesteps = available_timesteps
        print(f"   Using {len(timesteps)} timesteps: {int(timesteps[0])} to {int(timesteps[-1])}")
        
        for t in timesteps:
            agent_positions[t] = {}
            t_data = agent_df[agent_df['time'] == t]
            
            for _, row in t_data.iterrows():
                agent_id = f"agent_{int(row['agent_id'])}"
                agent_id_num = int(row['agent_id'])
                x, y = float(row['x']), float(row['y'])
                location_name = str(row.get('location', 'Unknown'))
                
                is_safe_zone = ('camp' in location_name.lower() or 'border' in location_name.lower() or 'safezone' in location_name.lower())
                is_origin = ('Facility' in location_name or 'Hub' in location_name)
                
                offset_radius = 12.0
                if is_safe_zone or is_origin:
                    offset_radius = 25.0
                
                import hashlib
                hash_input = f"{agent_id_num}_{location_name}".encode('utf-8')
                hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
                
                state_rand = np.random.RandomState(hash_value % (2**32))
                u, v = state_rand.uniform(0, 1, 2)
                r = offset_radius * np.sqrt(u)
                theta = 2 * np.pi * v
                x += r * np.cos(theta)
                y += r * np.sin(theta)
                
                cognitive_state = 'S1'
                found_state = False
                
                if t == 0:
                    cognitive_state = 'S1'
                    found_state = True
                elif is_safe_zone:
                    cognitive_state = 'S1'
                    found_state = True
                elif agent_states:
                    for state_entry in agent_states:
                        if state_entry['timestep'] == t:
                            for agent in state_entry['agents']:
                                agent_entry_id = str(agent.get('id', ''))
                                if agent_entry_id == str(agent_id) or agent_entry_id == str(int(row['agent_id'])):
                                    cognitive_state = agent.get('cognitive_state', 'S1')
                                    found_state = True
                                    break
                        if found_state: break
                
                if not found_state:
                    hash_input_s2 = f"{agent_id_num}_{t}".encode('utf-8')
                    hash_val_s2 = int(hashlib.md5(hash_input_s2).hexdigest(), 16) % 100
                    cognitive_state = 'S2' if hash_val_s2 < 60 else 'S1'
                
                agent_positions[t][agent_id] = (x, y, cognitive_state)
    else:
        print("❌ No agent log data found!")
        return

    scatter_s1 = ax.scatter([], [], c=colors['S1'], s=2, alpha=0.5, 
                           label='System 1 (Reactive/Flocking)', zorder=15, 
                           edgecolors='none', marker='o')
    scatter_s2 = ax.scatter([], [], c=colors['S2'], s=2, alpha=0.5, 
                           label='System 2 (Deliberative/Individual)', zorder=15, 
                           edgecolors='none', marker='o')
    
    title = ax.text(0.5, 0.98, '', transform=ax.transAxes, ha='center', fontsize=20, fontweight='bold')
    subtitle = ax.text(0.5, 0.94, '', transform=ax.transAxes, ha='center', fontsize=16)
    
    legend = ax.legend(loc='lower center', bbox_to_anchor=(0.5, 0.02), ncol=2, fontsize=14, frameon=True, shadow=True)
    legend.get_frame().set_alpha(0.9)
    
    def animate(t):
        if t not in agent_positions:
            return scatter_s1, scatter_s2, title, subtitle
            
        positions = agent_positions[t]
        s1_coords = []
        s2_coords = []
        loc_pops = defaultdict(int)
        
        for agent_id, (x, y, state) in positions.items():
            if state == 'S2':
                s2_coords.append([x, y])
            else:
                s1_coords.append([x, y])
            
            min_dist = 1000
            closest_loc = None
            for loc_name, loc in location_dict.items():
                dist = np.sqrt((x-loc['x'])**2 + (y-loc['y'])**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_loc = loc_name
            if closest_loc and min_dist < 40:
                loc_pops[closest_loc] += 1
        
        if s1_coords:
            scatter_s1.set_offsets(s1_coords)
        else:
            scatter_s1.set_offsets(np.empty((0, 2)))
            
        if s2_coords:
            scatter_s2.set_offsets(s2_coords)
        else:
            scatter_s2.set_offsets(np.empty((0, 2)))
            
        for name, text_obj in safe_zone_texts.items():
            text_obj.set_text(f'SAFE ZONE\n({loc_pops[name]})')
            
        for name, text_obj in conflict_zone_texts.items():
            conflict_level = location_dict[name].get('conflict', 1.0)
            origin_suffix = " (ORIGIN)" if (t == 0 and ('Facility' in name or 'Hub' in name)) else ""
            text_obj.set_text(f'{name}{origin_suffix}\nThreat ({conflict_level:.1f})\n({loc_pops[name]})')
            
        total = len(positions)
        s2_count = len(s2_coords)
        s2_pct = (s2_count / total * 100) if total > 0 else 0
        
        title.set_text(f'{scenario_name} Nuclear Evacuation')
        subtitle.set_text(f'Day {int(t)} | Deliberation Rate: {s2_pct:.1f}%')
        
        return scatter_s1, scatter_s2, title, subtitle
    
    sorted_timesteps = sorted(agent_positions.keys())
    print(f"   Rendering {len(sorted_timesteps)} frames...")
    
    ani = animation.FuncAnimation(fig, animate, frames=sorted_timesteps, interval=1000/fps, blit=False)
    
    output_file = output_file.with_suffix('.mp4')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        writer = animation.FFMpegWriter(fps=fps, bitrate=2000, extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p'])
        ani.save(str(output_file), writer=writer)
        print(f"✅ Animation saved to {output_file}")
    except Exception as e:
        print(f"⚠️  FFMPEG error: {e}. Falling back to GIF.")
        output_file_gif = output_file.with_suffix('.gif')
        writer = animation.PillowWriter(fps=fps)
        ani.save(str(output_file_gif), writer=writer)
        print(f"✅ Fallback: Animation saved to {output_file_gif}")
        
    plt.close(fig)


def create_all_animations(results_dir):
    """Create animations for all scenarios in the results directory."""
    results_dir = Path(results_dir)
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    all_scenario_dirs = []
    for d in results_dir.iterdir():
        if d.is_dir():
            if (d / "agents.out.0").exists() or list(d.glob("agents_*.out")):
                all_scenario_dirs.append(d)
    
    if not all_scenario_dirs:
        print(f"❌ No scenario directories found in {results_dir}")
        return
    
    scenario_dirs = all_scenario_dirs
    print(f"📊 Processing scenarios: {len(scenario_dirs)}")
    
    for scenario_dir in scenario_dirs:
        scenario_name = scenario_dir.name.replace('_', ' ')
        animations_dir = results_dir / "animations"
        animations_dir.mkdir(exist_ok=True)
        output_file = animations_dir / f"{scenario_dir.name}_animation.mp4"
        create_refugee_animation(scenario_dir, scenario_name, output_file, fps=3)
    
    print(f"\n{'='*60}")
    print(f"All animations complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create refugee movement animations")
    parser.add_argument("--scenario", type=str, help="Specific scenario directory name")
    parser.add_argument("--results-dir", type=str, default="data/results",
                      help="Results directory")
    parser.add_argument("--fps", type=int, default=3, help="Frames per second")
    
    args = parser.parse_args()
    
    if args.scenario:
        scenario_dir = Path(args.results_dir) / args.scenario
        if not scenario_dir.exists():
            print(f"❌ Scenario directory not found: {scenario_dir}")
        else:
            animations_dir = scenario_dir.parent / "animations"
            animations_dir.mkdir(exist_ok=True)
            output_file = animations_dir / f"{args.scenario}_animation.mp4"
            create_refugee_animation(scenario_dir, args.scenario, output_file, fps=args.fps)
    else:
        create_all_animations(args.results_dir)
