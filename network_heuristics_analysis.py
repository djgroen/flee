#!/usr/bin/env python3
"""
Network Heuristics Analysis from FLEE Simulation Output

Analyzes agent route choices using network metrics to quantify differences
between System 1 (heuristic) and System 2 (deliberative) navigation strategies.
Calculates dimensionless parameters from FLEE simulation outputs.
"""

import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
import json
import re
try:
    from scipy import stats
    HAS_SCIPY = True
except (ImportError, ValueError):
    HAS_SCIPY = False
    print("WARNING: scipy not available, statistical tests will be skipped")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# Step 1: Load and Parse FLEE Agent Output
# ============================================================================

def load_agents_flee_format(agents_file):
    """
    Load agents.out.0 file with flexible column parsing.
    
    Returns:
        df: DataFrame with columns [timestep, agent_id, location, ...]
    """
    # Read header line to get column names using csv module for proper parsing
    import csv
    columns = None
    with open(agents_file, 'r') as f:
        first_line = f.readline()
        if first_line.startswith('#'):
            header_line = first_line[1:].strip()
            # Parse CSV-style (handles quoted fields and trailing commas)
            columns = list(csv.reader([header_line]))[0]
            # Remove empty trailing columns (from trailing comma)
            columns = [c.strip() for c in columns if c.strip()]
        else:
            raise ValueError(f"Expected header line starting with #, got: {first_line[:50]}")
    
    if columns is None or len(columns) == 0:
        raise ValueError(f"Could not parse header line from {agents_file}")
    
    # Read CSV using csv module to handle trailing commas correctly
    rows = []
    with open(agents_file, 'r') as f:
        reader = csv.reader(f)
        # Skip header
        next(reader)
        # Read all data rows
        for row in reader:
            # Pad or trim row to match column count
            if len(row) < len(columns):
                row.extend([''] * (len(columns) - len(row)))
            elif len(row) > len(columns):
                row = row[:len(columns)]
            rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=columns)
    
    # Clean up - remove completely empty rows
    df = df.dropna(how='all')
    
    # Debug: Check if we got any data
    if len(df) == 0:
        print(f"  WARNING: No data rows after reading CSV from {agents_file}")
        print(f"    Columns expected: {columns[:5]}...")
        return pd.DataFrame()
    
    # Standardize column names (FLEE uses different conventions)
    # Note: Header has 'time' (not '#time') after we strip the '#'
    column_map = {
        'time': 'timestep',  # Most important - header has 'time'
        '#time': 'timestep',  # Fallback
        'Time': 'timestep',
        'rank-agentid': 'agent_id',
        'agent': 'agent_id',
        'current_location': 'location',
        'Location': 'location',
        'gps_x': 'x',
        'gps_y': 'y'
    }
    
    # Only rename columns that exist
    existing_columns = {k: v for k, v in column_map.items() if k in df.columns}
    if existing_columns:
        df = df.rename(columns=existing_columns)
    
    # Parse agent_id if in "rank-agentid" format (e.g., "0-123" -> 123)
    if 'agent_id' in df.columns and df['agent_id'].dtype == 'object':
        def parse_agent_id(x):
            if pd.isna(x):
                return np.nan
            x_str = str(x)
            if '-' in x_str:
                return int(x_str.split('-')[-1])
            try:
                return int(x_str)
            except:
                return np.nan
        
        df['agent_id'] = df['agent_id'].apply(parse_agent_id)
    
    # Convert types
    df['timestep'] = pd.to_numeric(df['timestep'], errors='coerce')
    df['agent_id'] = pd.to_numeric(df['agent_id'], errors='coerce')
    
    # Handle route locations (e.g., "L:ConflictZone:Town1")
    # Extract origin location for agents on routes
    def extract_location(loc_str):
        if pd.isna(loc_str):
            return np.nan
        loc_str = str(loc_str).strip()
        if not loc_str or loc_str == '':
            return np.nan
        if loc_str.startswith('L:'):
            # Route format: L:Origin:Dest -> use Origin
            parts = loc_str.split(':')
            if len(parts) >= 2:
                return parts[1]
        return loc_str
    
    # Apply location extraction if location column exists
    if 'location' in df.columns:
        df['location'] = df['location'].apply(extract_location)
    elif 'current_location' in df.columns:
        # Use current_location if location doesn't exist after rename
        df['location'] = df['current_location'].apply(extract_location)
    else:
        print(f"  WARNING: No location column found. Available columns: {list(df.columns)}")
        return pd.DataFrame()
    
    # Check which required columns exist
    required_cols = ['timestep', 'agent_id', 'location']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"    WARNING: Missing required columns: {missing_cols}")
        print(f"    Available columns: {list(df.columns)}")
        return pd.DataFrame()
    
    # Remove rows with missing critical data
    df = df.dropna(subset=required_cols)
    
    return df


def load_cognitive_states_from_json(results_file):
    """
    Load cognitive states from JSON results file.
    
    Expected structure:
    {
        "metrics": {
            "agent_states": [
                {
                    "timestep": 0,
                    "agents": [
                        {
                            "id": "agent_0",
                            "location": "ConflictZone",
                            "cognitive_state": "S1",
                            ...
                        }
                    ]
                }
            ]
        }
    }
    
    Returns:
        df: DataFrame with [timestep, agent_id, cognitive_state, location]
    """
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    agent_states = []
    metrics = data.get('metrics', {})
    states_list = metrics.get('agent_states', [])
    
    for timestep_data in states_list:
        timestep = timestep_data.get('timestep', 0)
        agents = timestep_data.get('agents', [])
        
        for agent in agents:
            agent_id_str = agent.get('id', '')
            # Extract numeric ID from "agent_123" format
            agent_id = None
            if 'agent_' in agent_id_str:
                try:
                    agent_id = int(agent_id_str.split('_')[1])
                except:
                    continue
            else:
                try:
                    agent_id = int(agent_id_str)
                except:
                    continue
            
            if agent_id is not None:
                agent_states.append({
                    'timestep': timestep,
                    'agent_id': agent_id,
                    'cognitive_state': agent.get('cognitive_state', 'S1'),
                    'location': agent.get('location', ''),
                    'connections': agent.get('connections', 0)
                })
    
    return pd.DataFrame(agent_states)


def extract_agent_paths(agents_df):
    """
    Reconstruct complete path for each agent from timestep data.
    
    Returns:
        paths_df: DataFrame with [agent_id, path, start_time, end_time, 
                  start_location, end_location, path_length]
    """
    paths = []
    
    for agent_id in agents_df['agent_id'].unique():
        agent_data = agents_df[agents_df['agent_id'] == agent_id].sort_values('timestep')
        
        if len(agent_data) == 0:
            continue
        
        # Get path (remove consecutive duplicates - agent stayed at location)
        full_path = agent_data['location'].tolist()
        unique_path = [full_path[0]]
        for loc in full_path[1:]:
            if loc != unique_path[-1]:
                unique_path.append(loc)
        
        paths.append({
            'agent_id': agent_id,
            'path': unique_path,
            'start_time': agent_data['timestep'].iloc[0],
            'end_time': agent_data['timestep'].iloc[-1],
            'start_location': unique_path[0],
            'end_location': unique_path[-1],
            'path_length': len(unique_path)
        })
    
    return pd.DataFrame(paths)


# ============================================================================
# Step 2: Build Network Graph from Topology Files
# ============================================================================

def build_network_from_files(scenario_name, data_dir='./'):
    """
    Build NetworkX graph from locations and routes CSV files.
    
    Returns:
        G: NetworkX Graph with node attributes
        conflict_zone: Name of starting conflict node
        safe_zones: List of destination node names
    """
    # Load topology
    locations_file = Path(data_dir) / f'locations_{scenario_name}.csv'
    routes_file = Path(data_dir) / f'routes_{scenario_name}.csv'
    
    if not locations_file.exists():
        # Try in run directory
        run_dirs = list(Path(data_dir).glob(f'run_{scenario_name}_*'))
        if run_dirs:
            locations_file = run_dirs[0] / f'locations_{scenario_name}.csv'
            routes_file = run_dirs[0] / f'routes_{scenario_name}.csv'
    
    locations = pd.read_csv(locations_file)
    routes = pd.read_csv(routes_file)
    
    # Create graph
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, loc in locations.iterrows():
        G.add_node(
            loc['name'],
            x=float(loc['x']),
            y=float(loc['y']),
            conflict=float(loc['conflict']),
            location_type=loc['location_type'],
            capacity=float(loc.get('capacity', 0))
        )
    
    # Add edges with distance weights
    for _, route in routes.iterrows():
        if route['from'] in G.nodes and route['to'] in G.nodes:
            G.add_edge(
                route['from'], 
                route['to'], 
                weight=float(route['distance'])
            )
    
    # Identify special nodes
    conflict_zones = locations[locations['location_type'] == 'conflict']['name'].tolist()
    safe_zones = locations[locations['location_type'] == 'camp']['name'].tolist()
    
    conflict_zone = conflict_zones[0] if conflict_zones else None
    
    return G, conflict_zone, safe_zones


# ============================================================================
# Step 3: Calculate Network Metrics for Each Agent Path
# ============================================================================

def calculate_path_metrics(G, path, conflict_zone, destination):
    """
    Calculate comprehensive network metrics for agent path.
    
    Returns dict with dimensionless parameters:
        - path_efficiency: actual / shortest
        - safety_score: 1 - mean(conflict)
        - route_directness: euclidean / path_distance
        - conflict_exposure: weighted sum of conflict
        - hop_count: number of nodes
    """
    metrics = {}
    
    # Validate path
    if len(path) < 2:
        return {k: np.nan for k in ['path_efficiency', 'safety_score', 
                'route_directness', 'conflict_exposure', 'hop_count',
                'actual_length', 'shortest_length', 'used_shortest_path',
                'conflict_weighted_cost']}
    
    # Filter path to only include nodes that exist in graph
    valid_path = [node for node in path if node in G.nodes]
    if len(valid_path) < 2:
        return {k: np.nan for k in ['path_efficiency', 'safety_score', 
                'route_directness', 'conflict_exposure', 'hop_count',
                'actual_length', 'shortest_length', 'used_shortest_path',
                'conflict_weighted_cost']}
    
    # 1. Shortest path calculation
    try:
        if conflict_zone and conflict_zone in G.nodes and destination in G.nodes:
            shortest_path = nx.shortest_path(G, conflict_zone, destination, weight='weight')
            shortest_length = nx.shortest_path_length(G, conflict_zone, destination, weight='weight')
        else:
            # Try using first and last nodes of path
            if valid_path[0] in G.nodes and valid_path[-1] in G.nodes:
                shortest_path = nx.shortest_path(G, valid_path[0], valid_path[-1], weight='weight')
                shortest_length = nx.shortest_path_length(G, valid_path[0], valid_path[-1], weight='weight')
            else:
                shortest_length = np.nan
                shortest_path = []
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        shortest_length = np.nan
        shortest_path = []
    
    # 2. Actual path length
    actual_length = 0
    for i in range(len(valid_path) - 1):
        if G.has_edge(valid_path[i], valid_path[i+1]):
            actual_length += G[valid_path[i]][valid_path[i+1]]['weight']
        else:
            # Path includes edge not in graph - calculate euclidean distance
            try:
                x1, y1 = G.nodes[valid_path[i]]['x'], G.nodes[valid_path[i]]['y']
                x2, y2 = G.nodes[valid_path[i+1]]['x'], G.nodes[valid_path[i+1]]['y']
                euclidean = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                actual_length += euclidean
            except:
                actual_length += np.nan
    
    # 3. Path efficiency (dimensionless)
    if not np.isnan(shortest_length) and shortest_length > 0:
        metrics['path_efficiency'] = actual_length / shortest_length
    else:
        metrics['path_efficiency'] = np.nan
    
    # 4. Safety score (inverse of conflict exposure)
    conflict_values = []
    for node in valid_path:
        if node in G.nodes:
            conflict_values.append(G.nodes[node]['conflict'])
    
    if conflict_values:
        mean_conflict = np.mean(conflict_values)
        metrics['conflict_exposure'] = mean_conflict
        metrics['safety_score'] = 1.0 - mean_conflict
    else:
        metrics['conflict_exposure'] = np.nan
        metrics['safety_score'] = np.nan
    
    # 5. Route directness (geometric efficiency)
    try:
        start_x, start_y = G.nodes[valid_path[0]]['x'], G.nodes[valid_path[0]]['y']
        end_x, end_y = G.nodes[valid_path[-1]]['x'], G.nodes[valid_path[-1]]['y']
        euclidean_dist = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        if actual_length > 0:
            metrics['route_directness'] = euclidean_dist / actual_length
        else:
            metrics['route_directness'] = np.nan
    except (KeyError, TypeError):
        metrics['route_directness'] = np.nan
    
    # 6. Hop count
    metrics['hop_count'] = len(valid_path) - 1
    
    # 7. Store raw values
    metrics['actual_length'] = actual_length
    metrics['shortest_length'] = shortest_length
    
    # 8. Conflict-weighted path cost (dimensionless)
    conflict_weighted_cost = 0
    for i in range(len(valid_path) - 1):
        if G.has_edge(valid_path[i], valid_path[i+1]) and valid_path[i] in G.nodes:
            edge_weight = G[valid_path[i]][valid_path[i+1]]['weight']
            node_conflict = G.nodes[valid_path[i]]['conflict']
            conflict_weighted_cost += edge_weight * (1 + node_conflict)
    
    metrics['conflict_weighted_cost'] = conflict_weighted_cost
    
    # 9. Used shortest path? (binary indicator)
    if shortest_path:
        # Compare path sequences (order matters)
        metrics['used_shortest_path'] = int(valid_path == shortest_path)
    else:
        metrics['used_shortest_path'] = np.nan
    
    return metrics


# ============================================================================
# Step 4: Complete Analysis Pipeline
# ============================================================================

def analyze_scenario(scenario_name, agents_file, results_file, data_dir='./'):
    """
    Complete analysis for one scenario.
    
    Returns:
        results_df: DataFrame with network metrics per agent
    """
    print(f"\nAnalyzing {scenario_name}...")
    
    # 1. Build network
    print("  Building network graph...")
    G, conflict_zone, safe_zones = build_network_from_files(scenario_name, data_dir)
    print(f"  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"  Conflict zone: {conflict_zone}, Safe zones: {safe_zones}")
    
    # 2. Load agent movement data
    print("  Loading agent data...")
    try:
        agents_df = load_agents_flee_format(agents_file)
        if len(agents_df) == 0:
            print(f"  WARNING: load_agents_flee_format returned empty DataFrame")
            return pd.DataFrame()
        print(f"  Loaded {len(agents_df)} timestep records for {agents_df['agent_id'].nunique()} agents")
    except Exception as e:
        print(f"  ERROR loading agent data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    
    # 3. Load cognitive states
    print("  Loading cognitive states...")
    if Path(results_file).exists():
        cognitive_df = load_cognitive_states_from_json(results_file)
        print(f"  Loaded cognitive states for {len(cognitive_df)} agent-timestep pairs")
        
        # Merge cognitive states into agents_df
        agents_df = agents_df.merge(
            cognitive_df[['timestep', 'agent_id', 'cognitive_state']],
            on=['timestep', 'agent_id'],
            how='left'
        )
        
        # Fill missing cognitive states (use most recent state for agent)
        for agent_id in agents_df['agent_id'].unique():
            agent_mask = agents_df['agent_id'] == agent_id
            agent_data = agents_df[agent_mask]
            if agent_data['cognitive_state'].notna().any():
                # Forward fill and back fill
                agents_df.loc[agent_mask, 'cognitive_state'] = (
                    agents_df.loc[agent_mask, 'cognitive_state']
                    .fillna(method='ffill')
                    .fillna(method='bfill')
                )
    else:
        print(f"  WARNING: {results_file} not found, using placeholder cognitive states")
        agents_df['cognitive_state'] = 'S1'  # Default
    
    # 4. Extract paths
    print("  Extracting agent paths...")
    paths_df = extract_agent_paths(agents_df)
    print(f"  Extracted {len(paths_df)} complete agent paths")
    
    # 5. Add cognitive state to paths (use state at end of path)
    print("  Assigning cognitive states to paths...")
    path_cognitive_states = []
    for _, path in paths_df.iterrows():
        agent_data = agents_df[
            (agents_df['agent_id'] == path['agent_id']) & 
            (agents_df['timestep'] == path['end_time'])
        ]
        if len(agent_data) > 0 and 'cognitive_state' in agent_data.columns:
            state = agent_data['cognitive_state'].iloc[0]
            # Convert to numeric: S1 -> 1, S2 -> 2
            if pd.notna(state):
                if str(state).upper() == 'S1':
                    state_num = 1
                elif str(state).upper() == 'S2':
                    state_num = 2
                else:
                    state_num = 1  # Default
            else:
                state_num = 1
        else:
            state_num = 1  # Default to S1
        
        path_cognitive_states.append(state_num)
    
    paths_df['cognitive_state'] = path_cognitive_states
    
    # 6. Calculate network metrics
    print("  Calculating network metrics...")
    results = []
    for idx, agent in paths_df.iterrows():
        # Determine destination (use end_location, or first safe zone if not a safe zone)
        destination = agent['end_location']
        if destination not in safe_zones and safe_zones:
            # Agent didn't reach a safe zone, use closest safe zone as reference
            destination = safe_zones[0]
        
        metrics = calculate_path_metrics(
            G, agent['path'], conflict_zone, destination
        )
        
        result = {
            'scenario': scenario_name,
            'agent_id': agent['agent_id'],
            'cognitive_state': agent['cognitive_state'],
            'start_location': agent['start_location'],
            'end_location': agent['end_location'],
            'path_length_nodes': agent['path_length'],
            'travel_time': agent['end_time'] - agent['start_time'],
            **metrics
        }
        results.append(result)
    
    results_df = pd.DataFrame(results)
    print(f"  Calculated metrics for {len(results_df)} agents")
    if len(results_df) > 0 and 'cognitive_state' in results_df.columns:
        print(f"  S1 agents: {len(results_df[results_df['cognitive_state']==1])}, "
              f"S2 agents: {len(results_df[results_df['cognitive_state']==2])}")
    else:
        print(f"  WARNING: No cognitive state data available")
    
    return results_df


def analyze_all_scenarios(data_dir='./data/refugee'):
    """
    Run analysis across all four scenarios.
    """
    # Find latest run directories
    scenarios = ['Multiple_Routes', 'Nearest_Border', 'Social_Connections', 'Context_Transition']
    
    all_results = []
    
    for scenario_name in scenarios:
        # Find latest run directory for this scenario
        run_dirs = sorted(Path(data_dir).glob(f'run_{scenario_name}_*'), reverse=True)
        
        if not run_dirs:
            print(f"WARNING: No run directory found for {scenario_name}, skipping...")
            continue
        
        run_dir = run_dirs[0]
        agents_file = run_dir / 'agents.out.0'
        results_file = run_dir / f'{scenario_name}_results.json'
        
        if not agents_file.exists():
            print(f"WARNING: {agents_file} not found, skipping {scenario_name}...")
            continue
        
        try:
            results_df = analyze_scenario(scenario_name, str(agents_file), 
                                        str(results_file), str(run_dir))
            all_results.append(results_df)
        except Exception as e:
            print(f"ERROR analyzing {scenario_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not all_results:
        print("ERROR: No scenarios successfully analyzed!")
        return None
    
    # Combine all scenarios
    combined_df = pd.concat(all_results, ignore_index=True)
    
    # Save results
    output_file = Path(data_dir) / 'network_heuristics_analysis.csv'
    combined_df.to_csv(output_file, index=False)
    print(f"\n✅ Saved complete analysis to: {output_file}")
    
    return combined_df


# ============================================================================
# Step 5: Statistical Summary and Comparison
# ============================================================================

def summarize_s1_s2_differences(results_df):
    """
    Generate statistical summary comparing S1 vs S2 navigation strategies.
    """
    print("\n" + "="*60)
    print("STATISTICAL SUMMARY: S1 vs S2 Navigation Heuristics")
    print("="*60)
    
    metrics = ['path_efficiency', 'safety_score', 'conflict_exposure', 
               'route_directness', 'hop_count', 'conflict_weighted_cost']
    
    for scenario in results_df['scenario'].unique():
        print(f"\n{scenario}:")
        print("-" * 40)
        
        scenario_data = results_df[results_df['scenario'] == scenario]
        s1 = scenario_data[scenario_data['cognitive_state'] == 1]
        s2 = scenario_data[scenario_data['cognitive_state'] == 2]
        
        print(f"  S1 agents: n={len(s1)}")
        print(f"  S2 agents: n={len(s2)}")
        
        for metric in metrics:
            if metric not in scenario_data.columns:
                continue
            
            s1_data = s1[metric].dropna()
            s2_data = s2[metric].dropna()
            
            if len(s1_data) == 0 or len(s2_data) == 0:
                continue
            
            s1_mean = s1_data.mean()
            s2_mean = s2_data.mean()
            
            if len(s1_data) > 2 and len(s2_data) > 2:
                if HAS_SCIPY:
                    try:
                        t_stat, p_val = stats.ttest_ind(s1_data, s2_data)
                        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
                    except:
                        p_val, sig = np.nan, "N/A"
                else:
                    p_val, sig = np.nan, "N/A (no scipy)"
            else:
                p_val, sig = np.nan, "N/A"
            
            print(f"    {metric:25s}: S1={s1_mean:.3f}, S2={s2_mean:.3f}, p={p_val:.4f} {sig}")
    
    # Overall summary
    print("\n" + "="*60)
    print("OVERALL PATTERNS (All Scenarios Combined):")
    print("="*60)
    
    s1_all = results_df[results_df['cognitive_state'] == 1]
    s2_all = results_df[results_df['cognitive_state'] == 2]
    
    for metric in metrics:
        if metric not in results_df.columns:
            continue
        
        s1_data = s1_all[metric].dropna()
        s2_data = s2_all[metric].dropna()
        
        if len(s1_data) == 0 or len(s2_data) == 0:
            continue
        
        s1_mean = s1_data.mean()
        s2_mean = s2_data.mean()
        s1_std = s1_data.std()
        
        if len(s1_data) > 2 and len(s2_data) > 2:
            if HAS_SCIPY:
                try:
                    t_stat, p_val = stats.ttest_ind(s1_data, s2_data)
                    effect_size = (s2_mean - s1_mean) / s1_std if s1_std > 0 else 0
                except:
                    p_val, effect_size = np.nan, np.nan
            else:
                p_val, effect_size = np.nan, np.nan
        else:
            p_val, effect_size = np.nan, np.nan
        
        print(f"  {metric:25s}: S1={s1_mean:.3f}, S2={s2_mean:.3f}")
        if not np.isnan(p_val):
            print(f"                        Difference={s2_mean-s1_mean:+.3f}, "
                  f"Cohen's d={effect_size:.3f}, p={p_val:.4f}")


# ============================================================================
# Step 6: Generate Figure
# ============================================================================

def create_network_heuristics_figure(results_df, output_file='agu_figures/fig5_network_heuristics.png'):
    """
    Create publication figure showing S1 vs S2 navigation strategies via network metrics.
    """
    # Define colors and markers
    scenario_colors = {
        'Multiple_Routes': '#56B4E9', 
        'Nearest_Border': '#E69F00',
        'Social_Connections': '#009E73', 
        'Context_Transition': '#CC79A7'
    }
    markers = ['o', 's', 'D', '^']
    
    # Colorblind-friendly colors (Okabe-Ito palette)
    # S1: Orange (warm, urgent, heuristic)
    # S2: Blue (cool, deliberative, analytical)
    s1_color = '#E69F00'  # Okabe-Ito orange
    s2_color = '#56B4E9'  # Okabe-Ito blue
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), dpi=150)
    
    # Panel 1: Scatter plot showing mean ± std for each scenario
    # Each point represents one scenario's S1 or S2 agents (summary statistics)
    ax1 = axes[0]
    
    scenario_list = list(results_df['scenario'].unique())
    scenario_labels = {
        'Multiple_Routes': 'MR',
        'Nearest_Border': 'NB',
        'Social_Connections': 'SC',
        'Context_Transition': 'CT'
    }
    
    # Plot summary statistics (mean) for each scenario
    for i, scenario in enumerate(scenario_list):
        scenario_data = results_df[results_df['scenario'] == scenario]
        
        s1_data = scenario_data[scenario_data['cognitive_state'] == 1]
        s2_data = scenario_data[scenario_data['cognitive_state'] == 2]
        
        # Plot S1 mean with error bars
        if len(s1_data) > 0:
            s1_eff = s1_data['path_efficiency'].dropna()
            s1_safe = s1_data['safety_score'].dropna()
            if len(s1_eff) > 0 and len(s1_safe) > 0:
                ax1.errorbar(s1_eff.mean(), s1_safe.mean(),
                           xerr=s1_eff.std(), yerr=s1_safe.std(),
                           marker=markers[i % len(markers)], markersize=15,
                           color=s1_color, markeredgecolor='black', markeredgewidth=2,
                           capsize=5, capthick=2, elinewidth=2, alpha=0.8,
                           label=f'{scenario_labels.get(scenario, scenario)} S1' if i < 2 else '')
        
        # Plot S2 mean with error bars
        if len(s2_data) > 0:
            s2_eff = s2_data['path_efficiency'].dropna()
            s2_safe = s2_data['safety_score'].dropna()
            if len(s2_eff) > 0 and len(s2_safe) > 0:
                ax1.errorbar(s2_eff.mean(), s2_safe.mean(),
                           xerr=s2_eff.std(), yerr=s2_safe.std(),
                           marker=markers[i % len(markers)], markersize=15,
                           color=s2_color, markeredgecolor='black', markeredgewidth=2,
                           capsize=5, capthick=2, elinewidth=2, alpha=0.8,
                           label=f'{scenario_labels.get(scenario, scenario)} S2' if i < 2 else '')
    
    ax1.set_xlabel('Path Efficiency (actual / shortest)', fontsize=18, fontweight='bold')
    ax1.set_ylabel('Safety Score (1 - conflict exposure)', fontsize=18, fontweight='bold')
    ax1.set_title('Navigation Strategy Tradeoffs\n(Mean ± Std per Scenario)', fontsize=20, fontweight='bold', pad=15)
    ax1.tick_params(labelsize=14)
    ax1.grid(alpha=0.3)
    
    # Add strategy regions
    ax1.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=2)
    ax1.text(0.95, 0.95, 'S1: Shortest path\n(efficient, risky)',
            transform=ax1.transAxes, fontsize=14, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='#FFE6CC', alpha=0.7, edgecolor='#E69F00', linewidth=2))
    ax1.text(0.05, 0.05, 'S2: Safety-weighted\n(longer, safer)',
            transform=ax1.transAxes, fontsize=14, va='bottom',
            bbox=dict(boxstyle='round', facecolor='#CCE5FF', alpha=0.7, edgecolor='#56B4E9', linewidth=2))
    
    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=s1_color,
              markersize=12, markeredgecolor='black', markeredgewidth=2,
              label='System 1', linestyle='None'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=s2_color,
              markersize=12, markeredgecolor='black', markeredgewidth=2,
              label='System 2', linestyle='None')
    ]
    ax1.legend(handles=legend_elements, fontsize=14, loc='upper left')
    
    # Panel 2: Bar comparison of key metrics
    ax2 = axes[1]
    
    metrics_to_plot = ['path_efficiency', 'safety_score', 'conflict_exposure']
    metric_labels = ['Path\nEfficiency', 'Safety\nScore', 'Conflict\nExposure']
    
    s1_means = []
    s2_means = []
    for m in metrics_to_plot:
        if m in results_df.columns:
            s1_data = results_df[results_df['cognitive_state']==1][m].dropna()
            s2_data = results_df[results_df['cognitive_state']==2][m].dropna()
            if len(s1_data) > 0 and len(s2_data) > 0:
                s1_means.append(s1_data.mean())
                s2_means.append(s2_data.mean())
            else:
                s1_means.append(0)
                s2_means.append(0)
        else:
            s1_means.append(0)
            s2_means.append(0)
    
    x = np.arange(len(metric_labels))
    width = 0.35
    
    bars1 = ax2.bar(x - width/2, s1_means, width, label='System 1',
                    color=s1_color, edgecolor='black', linewidth=1.5)
    bars2 = ax2.bar(x + width/2, s2_means, width, label='System 2',
                    color=s2_color, edgecolor='black', linewidth=1.5)
    
    ax2.set_ylabel('Metric Value', fontsize=18, fontweight='bold')
    ax2.set_title('Network Metric Comparison', fontsize=20, fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(metric_labels, fontsize=15)
    ax2.tick_params(axis='y', labelsize=14)
    ax2.legend(fontsize=16, loc='upper right')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}',
                        ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Overall title
    fig.suptitle('Navigation Heuristics: S1 vs S2 Cognitive Processing\n(4 Topologies, 500 Agents Each)',
                fontsize=24, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\n✅ Figure saved to: {output_path}")
    
    plt.close()
    
    return output_path


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Complete analysis pipeline.
    """
    print("="*60)
    print("NETWORK HEURISTICS ANALYSIS")
    print("="*60)
    
    # Set your data directory
    data_dir = './data/refugee'
    
    # Step 1: Run analysis
    results_df = analyze_all_scenarios(data_dir)
    
    if results_df is None or len(results_df) == 0:
        print("ERROR: No results generated!")
        return
    
    # Step 2: Generate summary statistics
    summarize_s1_s2_differences(results_df)
    
    # Step 3: Create visualization
    create_network_heuristics_figure(results_df)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    print(f"Results saved to: {data_dir}/network_heuristics_analysis.csv")
    print(f"Figure saved to: agu_figures/fig5_network_heuristics.png")


if __name__ == "__main__":
    main()

