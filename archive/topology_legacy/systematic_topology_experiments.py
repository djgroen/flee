#!/usr/bin/env python3
"""
Systematic Topology Experiments for Refugee Dynamics
Target: Scientific Reports

Methodology:
1. Define 8 Fundamental Topologies.
2. For each topology, generate variations in:
   - Size (N): Number of nodes (Small=20, Medium=50, Large=100)
   - Connectivity (K): Edge density (Sparse vs Dense)
3. Run Flee simulations for each variation.
4. Analyze scaling laws of Delay Factor vs N and K.
"""

import networkx as nx
import numpy as np
import pandas as pd
import os
import sys
import yaml
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

try:
    from flee import flee
    from flee.SimulationSettings import SimulationSettings
except ImportError:
    print("Error: Flee not found. Please ensure you are in the root of the flee-1 repository.")
    sys.exit(1)

# =============================================================================
# 1. Fundamental Topology Generators
# =============================================================================

def set_node_attributes(G, safe_nodes, conflict_nodes):
    """Helper to set standard attributes for Flee."""
    for n in G.nodes():
        G.nodes[n]['type'] = 'town'
        G.nodes[n]['capacity'] = 2000
        G.nodes[n]['conflict'] = 0.0
        
        # Default layout if not set
        if 'x' not in G.nodes[n]: G.nodes[n]['x'] = np.random.uniform(0, 200)
        if 'y' not in G.nodes[n]: G.nodes[n]['y'] = np.random.uniform(0, 200)
            
    for n in safe_nodes:
        G.nodes[n]['type'] = 'camp'
        G.nodes[n]['capacity'] = 50000
        G.nodes[n]['conflict'] = 0.0
        
    for n in conflict_nodes:
        G.nodes[n]['type'] = 'conflict'
        G.nodes[n]['capacity'] = -1
        G.nodes[n]['conflict'] = 1.0
        
    # Set edge distances
    for u, v in G.edges():
        if 'distance' not in G.edges[u,v]:
            p1 = np.array([G.nodes[u]['x'], G.nodes[u]['y']])
            p2 = np.array([G.nodes[v]['x'], G.nodes[v]['y']])
            dist = np.linalg.norm(p1 - p2)
            G.edges[u,v]['distance'] = max(10.0, dist) # Min distance 10km

    return G

# 1. Linear Chain
def gen_linear(N, dense=False):
    G = nx.path_graph(N, create_using=nx.DiGraph)
    # Layout: Horizontal line
    for i in range(N):
        G.nodes[i]['x'] = i * 20
        G.nodes[i]['y'] = 100
        
    # If dense, add skip-links (next-next neighbor)
    if dense:
        for i in range(N-2):
            G.add_edge(i, i+2)
            
    G = set_node_attributes(G, safe_nodes=[N-1], conflict_nodes=[0])
    return G, "Linear"

# 2. Dendritic (Hierarchical)
def gen_dendritic(N, dense=False):
    # Balanced tree approximation
    branching = 3 if dense else 2
    height = int(np.log(N)/np.log(branching))
    G = nx.balanced_tree(branching, height, create_using=nx.DiGraph)
    # Direction: Leaves -> Root (Refugees flee TO the root/safe zone)
    G = G.reverse()
    
    # Prune to exact N
    if len(G) > N:
        nodes_to_remove = list(G.nodes())[N:]
        G.remove_nodes_from(nodes_to_remove)
    
    # Layout (Radial or hierarchial)
    pos = nx.spring_layout(G) # Simple fallback
    for n, p in pos.items():
        G.nodes[n]['x'] = p[0] * 200 + 100
        G.nodes[n]['y'] = p[1] * 200 + 100

    # Root is Safe, Leaves are Conflict
    leaves = [x for x in G.nodes() if G.in_degree(x) == 0]
    # If graph reversed, leaves are now sources (in-degree 0 from perspective of flow? No, balanced_tree creates edges parent->child. 
    # reversed: child->parent. So leaves (sources) have in-degree 0.
    
    root = 0
    G = set_node_attributes(G, safe_nodes=[root], conflict_nodes=leaves[:max(1, len(leaves)//2)])
    return G, "Dendritic"

# 3. Grid / Lattice
def gen_lattice(N, dense=False):
    side = int(np.sqrt(N))
    G = nx.grid_2d_graph(side, side)
    G = nx.DiGraph(G)
    
    # Flatten names
    mapping = {n: i for i, n in enumerate(G.nodes())}
    G = nx.relabel_nodes(G, mapping)
    
    # Layout
    for i in range(side):
        for j in range(side):
            idx = i*side + j
            if idx in G:
                G.nodes[idx]['x'] = j * 20
                G.nodes[idx]['y'] = i * 20
                
    # If NOT dense, remove random edges (obstacles)
    if not dense:
        edges = list(G.edges())
        num_remove = int(len(edges) * 0.3)
        idxs = np.random.choice(len(edges), num_remove, replace=False)
        for i in idxs:
            G.remove_edge(*edges[i])
            
    # Ensure connectivity
    safe = side*side - 1
    conflict = 0
    if not nx.has_path(G, conflict, safe):
         G.add_edge(conflict, safe) # Fail-safe direct link if disconnected
         
    G = set_node_attributes(G, safe_nodes=[safe], conflict_nodes=[conflict])
    return G, "Lattice"

# 4. Star / Hub-and-Spoke
def gen_star(N, dense=False):
    G = nx.DiGraph()
    center = 0
    G.add_node(center, x=100, y=100)
    
    # Spokes
    for i in range(1, N):
        angle = 2 * np.pi * i / (N-1)
        G.add_node(i, x=100 + 80*np.cos(angle), y=100 + 80*np.sin(angle))
        # Spoke -> Hub
        G.add_edge(i, center)
        # Hub -> Spoke (if dense, bidirectional)
        if dense:
            G.add_edge(center, i)
            
    # If dense, add ring connections
    if dense:
        for i in range(1, N-1):
            G.add_edge(i, i+1)
        G.add_edge(N-1, 1)

    # Center is Safe, Outer nodes are Conflict
    G = set_node_attributes(G, safe_nodes=[center], conflict_nodes=[1, 2, 3])
    return G, "Star"

# 5. Bottleneck
def gen_bottleneck(N, dense=False):
    G = nx.DiGraph()
    
    # Two clusters connected by a bridge
    n1 = N // 2
    n2 = N - n1
    
    # Cluster 1 (Source)
    for i in range(n1):
        G.add_node(i, x=np.random.uniform(0, 50), y=np.random.uniform(50, 150))
    
    # Cluster 2 (Destination)
    for i in range(n1, N):
        G.add_node(i, x=np.random.uniform(150, 200), y=np.random.uniform(50, 150))
        
    # Intra-cluster edges
    prob = 0.5 if dense else 0.2
    for i in range(n1):
        for j in range(n1):
            if i!=j and np.random.random() < prob: G.add_edge(i, j)
            
    for i in range(n1, N):
        for j in range(n1, N):
            if i!=j and np.random.random() < prob: G.add_edge(i, j)
            
    # Bridge (Bottleneck)
    bridge_start = n1 - 1
    bridge_end = n1
    G.add_edge(bridge_start, bridge_end)
    
    G = set_node_attributes(G, safe_nodes=[N-1], conflict_nodes=[0])
    return G, "Bottleneck"

# 6. Parallel Routes
def gen_parallel(N, dense=False):
    G = nx.DiGraph()
    start = 0
    end = N-1
    G.add_node(start, x=0, y=100)
    G.add_node(end, x=200, y=100)
    
    num_paths = 3 if dense else 2
    nodes_per_path = (N-2) // num_paths
    
    current_node = 1
    for p in range(num_paths):
        prev = start
        y_offset = (p - (num_paths-1)/2) * 50
        
        for k in range(nodes_per_path):
            if current_node >= end: break
            G.add_node(current_node, x=100 + (k-(nodes_per_path/2))*20, y=100+y_offset)
            G.add_edge(prev, current_node)
            prev = current_node
            current_node += 1
        G.add_edge(prev, end)
        
    G = set_node_attributes(G, safe_nodes=[end], conflict_nodes=[start])
    return G, "Parallel"

# 7. Cycle (Ring)
def gen_cycle(N, dense=False):
    G = nx.cycle_graph(N, create_using=nx.DiGraph)
    # Layout
    radius = 80
    for i in range(N):
        angle = 2 * np.pi * i / N
        G.nodes[i]['x'] = 100 + radius * np.cos(angle)
        G.nodes[i]['y'] = 100 + radius * np.sin(angle)
        
    # If dense, add chords
    if dense:
        for i in range(N):
            target = (i + N//2) % N
            G.add_edge(i, target)
            
    # Safe zone at 0, conflict at opposite side
    G = set_node_attributes(G, safe_nodes=[0], conflict_nodes=[N//2])
    return G, "Cycle"

# 8. Small World
def gen_small_world(N, dense=False):
    k = 4 if dense else 2
    G = nx.watts_strogatz_graph(N, k, 0.3)
    G = nx.DiGraph(G)
    
    # Layout
    pos = nx.circular_layout(G)
    for n, p in pos.items():
        G.nodes[n]['x'] = p[0] * 100 + 100
        G.nodes[n]['y'] = p[1] * 100 + 100
        
    G = set_node_attributes(G, safe_nodes=[0], conflict_nodes=[N//2])
    return G, "SmallWorld"


# =============================================================================
# 2. Experiment Runner
# =============================================================================

def run_simulation(G, name, output_base="data/systematic"):
    output_dir = Path(output_base) / name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Write SimSettings
    sim_settings = {
        "log_levels": {"agent": 1, "link": 0, "camp": 0, "init": 0},
        "spawn_rules": {
            "take_from_population": False,
            "insert_day0": True
        },
        "move_rules": {
            "max_move_speed": 360.0,
            "max_walk_speed": 35.0,
            "camp_movechance": 0.001,
            "conflict_movechance": 1.0,
            "default_movechance": 0.5,
            "two_system_decision_making": True
        },
        "optimisations": {"hasten": 1}
    }
    with open(output_dir / "simsetting.yml", "w") as f:
        yaml.dump(sim_settings, f)

    # 2. Write CSVs
    loc_data = []
    for n, attr in G.nodes(data=True):
        loc_data.append({
            'name': str(n), 'x': attr['x'], 'y': attr['y'], 
            'location_type': attr['type'], 
            'movechance': 1.0 if attr['type']=='conflict' else 0.001 if attr['type']=='camp' else 0.5,
            'capacity': attr['capacity'], 'pop': 0, 
            'conflict': attr['conflict'], 'country': 'unknown', 'region': 'unknown', 'conflict_date': 0
        })
    pd.DataFrame(loc_data).to_csv(output_dir / "locations.csv", index=False)
    
    route_data = [{'from': str(u), 'to': str(v), 'distance': d.get('distance', 10.0)} for u, v, d in G.edges(data=True)]
    pd.DataFrame(route_data).to_csv(output_dir / "routes.csv", index=False)
    
    # 3. Run Flee
    # Note: We are using python library calls, not shell commands, for speed/control
    try:
        SimulationSettings.ReadFromYML(str(output_dir / "simsetting.yml"))
        e = flee.Ecosystem()
        
        # Load Locations
        df_loc = pd.read_csv(output_dir / "locations.csv", dtype={'name': str})
        for _, row in df_loc.iterrows():
            l = e.addLocation(row['name'], x=row['x'], y=row['y'], location_type=row['location_type'], movechance=row['movechance'], capacity=row['capacity'])
            l.conflict = row['conflict']
            
        # Load Routes
        df_route = pd.read_csv(output_dir / "routes.csv", dtype={'from': str, 'to': str})
        for _, row in df_route.iterrows():
            e.linkUp(row['from'], row['to'], float(row['distance']))
            
        # Spawn Agents
        conflict_locs = [l for l in e.locations if l.movechance == 1.0]
        if not conflict_locs:
             print(f"Skipping {name}: No conflict zones.")
             return None
             
        for l in conflict_locs:
            for i in range(200): # Standardize agent count per conflict zone
                e.addAgent(l, {"agent_id": f"{l.name}_{i}", "education_level": 0.5})
                
        # Evolve
        cwd = os.getcwd()
        os.chdir(output_dir)
        try:
            if os.path.exists("agents.out.0"): os.remove("agents.out.0")
            for t in range(100):
                e.evolve()
        finally:
            os.chdir(cwd)
            
        # Analyze Travel Time
        log_path = output_dir / "agents.out.0"
        if not log_path.exists(): return None
        
        # Simple parsing
        # (Using robust parsing similar to previous script)
        arrivals = {}
        safe_names = [l.name for l in e.locations if l.capacity > 10000] # Assumption based on generator
        
        with open(log_path, 'r') as f:
            header = f.readline().replace('#','').strip().split(',')
            try:
                t_idx = [i for i, c in enumerate(header) if 'time' in c.strip()][0]
                id_idx = [i for i, c in enumerate(header) if 'agentid' in c.strip()][0]
                loc_idx = [i for i, c in enumerate(header) if 'location' in c.strip()][0]
                
                for line in f:
                    parts = line.split(',')
                    if len(parts) < len(header): continue
                    t = int(parts[t_idx])
                    aid = parts[id_idx]
                    loc = parts[loc_idx].strip()
                    
                    if loc in safe_names and aid not in arrivals:
                        arrivals[aid] = t
            except Exception as e:
                print(f"Log parsing error in {name}: {e}")
                return None
                
        times = list(arrivals.values())
        avg_time = np.mean(times) if times else 0
        return {"Name": name, "AvgTime": avg_time, "Arrivals": len(times)}

    except Exception as e:
        print(f"Simulation error in {name}: {e}")
        import traceback
        traceback.print_exc()
        return None


# =============================================================================
# 3. Main Loop
# =============================================================================

def main():
    generators = {
        "Linear": gen_linear,
        "Dendritic": gen_dendritic,
        "Lattice": gen_lattice,
        "Star": gen_star,
        "Bottleneck": gen_bottleneck,
        "Parallel": gen_parallel,
        "Cycle": gen_cycle,
        "SmallWorld": gen_small_world
    }
    
    results = []
    
    # Sensitivity Sweep
    # Sizes: N=20 (Small), N=50 (Medium), N=100 (Large)
    # Density: False (Sparse), True (Dense)
    
    sizes = [20, 50, 100]
    densities = [False, True]
    
    print("🚀 Starting Systematic Topology Sweep...")
    
    for topo_name, gen_func in generators.items():
        for N in sizes:
            for dense in densities:
                run_name = f"{topo_name}_N{N}_{'Dense' if dense else 'Sparse'}"
                print(f"   -> Processing {run_name}...")
                
                G, _ = gen_func(N, dense)
                res = run_simulation(G, run_name)
                
                if res:
                    res["Topology"] = topo_name
                    res["N"] = N
                    res["Dense"] = dense
                    results.append(res)
                    
    # Save Summary
    df = pd.DataFrame(results)
    Path("data/systematic").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/systematic/summary.csv", index=False)
    print("✅ Sweep Complete. Results saved.")

if __name__ == "__main__":
    main()

