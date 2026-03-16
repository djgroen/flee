#!/usr/bin/env python3
"""
Parameter Sweep Experiments for Refugee Dynamics
Target: Scientific Reports

This script runs a series of experiments varying:
1. Network Scale (Number of Nodes/Levels/Grid Size)
2. Network Connectivity (Grid dimensions, Branching factors)
3. Population Size (Number of Agents)

It calculates dimensionless parameters for each run to identify scaling laws.
"""

import networkx as nx
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Force headless backend to prevent GUI crashes
import matplotlib.pyplot as plt
import os
import sys
import json
import yaml
from pathlib import Path
import time

# Add current directory to path
sys.path.insert(0, '.')

try:
    from flee import flee
    from flee.SimulationSettings import SimulationSettings
except ImportError:
    print("Error: Flee not found. Please ensure you are in the root of the flee-1 repository.")
    sys.exit(1)

# =============================================================================
# 1. Flexible Topology Generators
# =============================================================================

def generate_lattice_varied(rows=5, cols=5, obstacle_prob=0.1):
    """Generates a lattice with variable dimensions and obstacle density."""
    G = nx.grid_2d_graph(rows, cols)
    G = nx.DiGraph(G)
    
    mapping = {node: f"Loc_{node[0]}_{node[1]}" for node in G.nodes()}
    G = nx.relabel_nodes(G, mapping)
    
    safe_node = f"Loc_{rows-1}_{cols-1}"
    conflict_center = f"Loc_0_0"
    
    for node in G.nodes():
        parts = node.split('_')
        r, c = int(parts[1]), int(parts[2])
        
        G.nodes[node]['x'] = c * 20
        G.nodes[node]['y'] = r * 20
        G.nodes[node]['type'] = 'town'
        G.nodes[node]['capacity'] = 2000
        G.nodes[node]['conflict'] = 0.0
        
        if node == safe_node:
            G.nodes[node]['type'] = 'camp'
            G.nodes[node]['capacity'] = 50000
        elif node == conflict_center:
            G.nodes[node]['type'] = 'conflict'
            G.nodes[node]['capacity'] = -1
            G.nodes[node]['conflict'] = 1.0

    # Remove obstacles
    nodes_to_remove = []
    for node in G.nodes():
        if node not in [safe_node, conflict_center] and np.random.random() < obstacle_prob:
            nodes_to_remove.append(node)
    G.remove_nodes_from(nodes_to_remove)
    
    # Ensure connectivity
    if not nx.has_path(G, conflict_center, safe_node):
        # Fallback: simple diagonal path restoration
        current = (0,0)
        target = (rows-1, cols-1)
        while current != target:
            r, c = current
            if r < target[0]: r += 1
            if c < target[1]: c += 1
            node_name = f"Loc_{r}_{c}"
            if node_name not in G:
                G.add_node(node_name, x=c*20, y=r*20, type='town', capacity=2000, conflict=0.0)
            
            prev_name = f"Loc_{current[0]}_{current[1]}"
            if prev_name in G:
                G.add_edge(prev_name, node_name, distance=20.0)
                G.add_edge(node_name, prev_name, distance=20.0)
            current = (r, c)

    for u, v in G.edges():
        G.edges[u, v]['distance'] = 20.0
        
    return G

def generate_hierarchical_varied(levels=3, branching=3):
    """Generates hierarchical topology with variable depth and width."""
    G = nx.DiGraph()
    G.add_node("SafeZone", type="camp", x=100, y=100, capacity=50000, conflict=0.0)
    
    current_level_nodes = ["SafeZone"]
    node_counter = 0
    
    for level in range(1, levels + 1):
        next_level_nodes = []
        for parent in current_level_nodes:
            # Fixed branching for consistency in this experiment, or slightly random
            num_children = branching 
            
            for _ in range(num_children):
                node_name = f"Loc_L{level}_{node_counter}"
                node_counter += 1
                
                l_type = "conflict" if level == levels else "town"
                conflict = 1.0 if l_type == "conflict" else 0.0
                capacity = -1 if l_type == "conflict" else 5000
                
                x = 100 - (level * 30)
                y = 100 + (len(next_level_nodes) - num_children/2) * 10 
                
                G.add_node(node_name, type=l_type, x=x, y=y, capacity=capacity, conflict=conflict)
                G.add_edge(node_name, parent, distance=20.0)
                next_level_nodes.append(node_name)
        current_level_nodes = next_level_nodes
    return G

# =============================================================================
# 2. Simulation Runner
# =============================================================================

def run_experiment(G, agents_per_conflict, run_id, output_base="data/sweep"):
    """Runs a single experiment and returns metrics."""
    topology_name = f"Run_{run_id}"
    output_dir = Path(output_base) / topology_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write Settings
    sim_settings = {
        "log_levels": {"agent": 1, "link": 0, "camp": 0, "init": 0},
        "spawn_rules": {"take_from_population": False, "insert_day0": True},
        "move_rules": {
            "max_move_speed": 20.0,
            "max_walk_speed": 8.0,
            "camp_movechance": 0.001,
            "conflict_movechance": 1.0,
            "default_movechance": 0.5,
            "two_system_decision_making": True
        },
        "optimisations": {"hasten": 1}
    }
    with open(output_dir / "simsetting.yml", "w") as f:
        yaml.dump(sim_settings, f)
        
    # Write Graph to CSVs
    loc_data = []
    for n, attr in G.nodes(data=True):
        loc_data.append({
            'name': n, 'x': attr.get('x',0), 'y': attr.get('y',0), 
            'location_type': attr['type'], 
            'movechance': 1.0 if attr['type']=='conflict' else 0.001 if attr['type']=='camp' else 0.5,
            'capacity': attr['capacity'], 'pop': 0, 'conflict': attr['conflict'], 'country': 'unknown', 'region': 'unknown', 'conflict_date': 0
        })
    pd.DataFrame(loc_data).to_csv(output_dir / "locations.csv", index=False)
    
    route_data = [{'from': u, 'to': v, 'distance': d['distance']} for u, v, d in G.edges(data=True)]
    pd.DataFrame(route_data).to_csv(output_dir / "routes.csv", index=False)
    
    print(f"   [Run {run_id}] Config files written.", flush=True)

    # Initialize & Run
    try:
        SimulationSettings.ReadFromYML(str(output_dir / "simsetting.yml"))
        e = flee.Ecosystem()
        
        print(f"   [Run {run_id}] Loading locations...", flush=True)
        df_loc = pd.read_csv(output_dir / "locations.csv")
        for _, row in df_loc.iterrows():
            l = e.addLocation(row['name'], x=row['x'], y=row['y'], location_type=row['location_type'], movechance=row['movechance'], capacity=row['capacity'])
            l.conflict = row['conflict']
            
        print(f"   [Run {run_id}] Loading routes...", flush=True)
        df_route = pd.read_csv(output_dir / "routes.csv")
        for _, row in df_route.iterrows():
            e.linkUp(row['from'], row['to'], float(row['distance']))
            
        print(f"   [Run {run_id}] Spawning agents...", flush=True)
        conflict_nodes = [n for n, attr in G.nodes(data=True) if attr['type'] == 'conflict']
        total_agents = 0
        for c in conflict_nodes:
            # Find location safely
            loc_list = [loc for loc in e.locations if loc.name == c]
            if not loc_list:
                print(f"   [Run {run_id}] Warning: Conflict node {c} not found in ecosystem.", flush=True)
                continue
            l = loc_list[0]
            
            for i in range(agents_per_conflict):
                e.addAgent(l, {"agent_id": f"{c}_{i}", "education_level": 0.5, "connections": 2})
                total_agents += 1
                
        print(f"   [Run {run_id}] Starting simulation with {total_agents} agents...", flush=True)
        # Run
        sim_days = 60
        cwd = os.getcwd()
        os.chdir(output_dir)
        try:
            if os.path.exists("agents.out.0"): os.remove("agents.out.0")
            for t in range(sim_days):
                e.evolve()
                if t % 10 == 0: print(f"   [Run {run_id}] Day {t}", flush=True)
        except Exception as e_sim:
            print(f"   [Run {run_id}] Simulation failed: {e_sim}", flush=True)
            import traceback
            traceback.print_exc()
            return None
        finally:
            os.chdir(cwd)
            
    except Exception as e_setup:
        print(f"   [Run {run_id}] Setup failed: {e_setup}", flush=True)
        import traceback
        traceback.print_exc()
        return None

    print(f"   [Run {run_id}] Simulation finished.", flush=True)

    # Analyze Logs
    print(f"   [Run {run_id}] Analyzing logs...", flush=True)
    log_path = output_dir / "agents.out.0"
    if not log_path.exists(): 
        print(f"   [Run {run_id}] Log file missing!", flush=True)
        return None
    
    # Calculate travel times
    safe_zones = [n for n, attr in G.nodes(data=True) if attr['type'] == 'camp']
    arrivals = {}
    try:
        with open(log_path, 'r') as f:
            header_line = f.readline()
            if not header_line:
                print(f"   [Run {run_id}] Log file empty!", flush=True)
                return None
                
            header = header_line.replace('#','').strip().split(',')
            cols = [c.strip() for c in header]
            try:
                t_idx = cols.index('time')
                id_idx = cols.index('rank-agentid')
                loc_idx = cols.index('current_location')
            except ValueError as e:
                print(f"   [Run {run_id}] Error parsing header: {e}. Header: {header}", flush=True)
                return None
                
            for line in f:
                p = [x.strip() for x in line.split(',')]
                if len(p) < len(cols): continue
                try:
                    t = int(p[t_idx])
                    aid = p[id_idx]
                    loc = p[loc_idx]
                    if loc in safe_zones and aid not in arrivals:
                        arrivals[aid] = t
                except ValueError:
                    continue
    except Exception as e_read:
        print(f"   [Run {run_id}] Error reading log: {e_read}", flush=True)
        return None
                
    times = list(arrivals.values())
    avg_time = np.mean(times) if times else 0
    print(f"   [Run {run_id}] Found {len(times)} arrivals. Avg Time: {avg_time}", flush=True)
    
    # Ideal Time (Graph Distance)
    # Calculate shortest path from all conflict nodes to nearest safe zone
    ideal_times = []
    for c in conflict_nodes:
        try:
            dists = [nx.shortest_path_length(G, c, s, weight='distance') for s in safe_zones]
            min_dist = min(dists)
            ideal_times.append(min_dist / 20.0) # max_speed = 20
        except:
            pass
    avg_ideal_time = np.mean(ideal_times) if ideal_times else 0
    
    # Dimensionless Parameters
    N = len(G.nodes())
    E = len(G.edges())
    # 1. Connectivity (Average Degree)
    k = 2 * E / N if N > 0 else 0
    # 2. Agent Saturation (Agents / Total Capacity of non-conflict)
    # Total capacity: towns + camps
    total_cap = sum([d['capacity'] for n, d in G.nodes(data=True) if d['capacity'] > 0])
    saturation = total_agents / total_cap if total_cap > 0 else 0
    # 3. Delay Factor
    delay = avg_time / avg_ideal_time if avg_ideal_time > 0 else 0
    
    return {
        "RunID": run_id,
        "Topology": "Lattice" if "Lattice" in str(run_id) else "Hierarchical",
        "Nodes": N,
        "Edges": E,
        "Agents": total_agents,
        "AvgDegree": k,
        "Saturation": saturation,
        "AvgIdealTime": avg_ideal_time,
        "AvgActualTime": avg_time,
        "DelayFactor": delay,
        "ArrivalRate": len(arrivals) / total_agents if total_agents > 0 else 0
    }

# =============================================================================
# 3. Main Sweep
# =============================================================================

def main():
    print("🧪 Starting Parameter Sweep...")
    
    results = []
    run_counter = 0
    
    # Experiment 1: Lattice Scaling (Vary Grid Size, fixed density)
    print("   Experiment Set 1: Lattice Scaling")
    for size in [4, 6, 8, 10]:
        G = generate_lattice_varied(rows=size, cols=size, obstacle_prob=0.1)
        # Scale agents with size to keep "pressure" roughly constant? 
        # Or keep agents constant to see density effect?
        # Let's vary agents to create different saturations
        for agents in [100, 500]:
            res = run_experiment(G, agents, f"Lat_{size}x{size}_A{agents}")
            if res: results.append(res)
            print(f"   -> Finished Lat_{size}x{size}_A{agents}")
            
    # Experiment 2: Hierarchical Depth (Vary Levels)
    print("   Experiment Set 2: Hierarchical Depth")
    for levels in [2, 3, 4]:
        G = generate_hierarchical_varied(levels=levels, branching=3)
        for agents in [100, 500]:
            res = run_experiment(G, agents, f"Hier_L{levels}_A{agents}")
            if res: results.append(res)
            print(f"   -> Finished Hier_L{levels}_A{agents}")

    # Experiment 3: Obstacle Density (Connectivity variation)
    print("   Experiment Set 3: Lattice Connectivity")
    size = 8
    for obs in [0.0, 0.2, 0.4]:
        G = generate_lattice_varied(rows=size, cols=size, obstacle_prob=obs)
        res = run_experiment(G, 200, f"Lat_Obs{int(obs*100)}")
        if res: results.append(res)
        print(f"   -> Finished Lat_Obs{int(obs*100)}")

    # Save Results
    df = pd.DataFrame(results)
    Path("data/sweep").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/sweep/sweep_summary.csv", index=False)
    print("✅ Sweep Complete. Results saved to data/sweep/sweep_summary.csv")
    
    # Plotting
    plot_sweep_results(df)

def plot_sweep_results(df):
    output_dir = Path("data/sweep")
    
    # 1. Delay Factor vs Saturation
    plt.figure(figsize=(10, 6))
    for topo in df['Topology'].unique():
        subset = df[df['Topology'] == topo]
        plt.scatter(subset['Saturation'], subset['DelayFactor'], label=topo, s=100)
    plt.xlabel("Agent Saturation (Agents / Capacity)")
    plt.ylabel("Delay Factor (Actual / Ideal Time)")
    plt.title("Impact of Congestion on Travel Delay")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "delay_vs_saturation.png")
    plt.close()
    
    # 2. Delay vs Network Size (Nodes)
    plt.figure(figsize=(10, 6))
    for topo in df['Topology'].unique():
        subset = df[df['Topology'] == topo]
        plt.scatter(subset['Nodes'], subset['DelayFactor'], label=topo, s=100)
    plt.xlabel("Network Size (Nodes)")
    plt.ylabel("Delay Factor")
    plt.title("Scaling of Delay with Network Size")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "delay_vs_size.png")
    plt.close()

if __name__ == "__main__":
    main()

