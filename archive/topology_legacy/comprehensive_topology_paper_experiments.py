#!/usr/bin/env python3
"""
Comprehensive Refugee Paper Experiments (Scientific Reports Target)

This script generates complex, rationale-driven network topologies,
calculates 'a priori' network heuristics, runs Flee simulations,
and analyzes the correlation between heuristics and actual agent outcomes (travel time).

Topologies:
1. Hierarchical (Dendritic): Rural-to-urban flow.
2. Lattice (Grid) with Obstacles: Urban/road network.
3. Hub-and-Spoke with Cycles: Transit hubs.
4. Bottleneck (Funnel): Border crossing convergence.
"""

import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import seaborn as sns - removed to avoid scipy conflict
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

try:
    from flee import flee
    from flee.SimulationSettings import SimulationSettings
except ImportError:
    print("Error: Flee not found. Please ensure you are in the root of the flee-1 repository.")
    sys.exit(1)

# =============================================================================
# 1. Topology Generation
# =============================================================================

def generate_hierarchical_topology(num_levels=3, branching_factor=3):
    """
    Generates a dendritic/tree-like topology representing rural-to-urban flow.
    Rationale: Refugees often move from small villages -> towns -> cities -> camps.
    """
    G = nx.DiGraph()
    
    # Level 0: The Safe Zone (Root)
    G.add_node("SafeZone", type="camp", x=100, y=100, capacity=10000, conflict=0.0)
    
    # Generate levels
    current_level_nodes = ["SafeZone"]
    all_nodes = [("SafeZone", 0)] # (name, level)
    
    node_counter = 0
    
    for level in range(1, num_levels + 1):
        next_level_nodes = []
        for parent in current_level_nodes:
            # Determine number of children (variable branching)
            num_children = np.random.randint(2, branching_factor + 1)
            
            for _ in range(num_children):
                node_name = f"Loc_L{level}_{node_counter}"
                node_counter += 1
                
                # Assign type based on level
                if level == num_levels:
                    # Leaves are conflict zones (villages)
                    l_type = "conflict"
                    conflict = 1.0
                    capacity = -1
                else:
                    # Intermediate nodes are towns
                    l_type = "town"
                    conflict = 0.1 * level # Increasing conflict closer to source
                    capacity = 5000
                
                # Position (simple layout)
                # Angle spreads out based on parent
                parent_idx = current_level_nodes.index(parent)
                # This is a very rough layout, Flee doesn't strictly need accurate x/y for graph logic
                # but good for visualization.
                x = 100 - (level * 30) 
                y = 100 + (parent_idx - len(current_level_nodes)/2) * (100 / (level+1)) + np.random.normal(0, 5)
                
                G.add_node(node_name, type=l_type, x=x, y=y, capacity=capacity, conflict=conflict)
                G.add_edge(node_name, parent, distance=20.0) # Flow towards safe zone
                
                # Add lateral links (small probability) to allow some cross-movement
                if len(next_level_nodes) > 0 and np.random.random() < 0.2:
                    G.add_edge(node_name, next_level_nodes[-1], distance=15.0)
                    G.add_edge(next_level_nodes[-1], node_name, distance=15.0)
                
                next_level_nodes.append(node_name)
                
        current_level_nodes = next_level_nodes
        
    return G, "Hierarchical"

def generate_lattice_topology(rows=5, cols=5):
    """
    Generates a grid-like topology with some removed links/nodes (obstacles).
    Rationale: Urban environments or developed road networks where agents have 
    multiple path options.
    """
    G = nx.grid_2d_graph(rows, cols)
    G = nx.DiGraph(G) # Convert to directed
    
    # Relabel nodes to strings
    mapping = {node: f"Loc_{node[0]}_{node[1]}" for node in G.nodes()}
    G = nx.relabel_nodes(G, mapping)
    
    # Define Safe Zones (one corner) and Conflict Zones (opposite corner)
    safe_node = f"Loc_{rows-1}_{cols-1}"
    conflict_center = f"Loc_0_0"
    
    # Set attributes
    for node in G.nodes():
        # Distance calculation for basic layout
        parts = node.split('_')
        r, c = int(parts[1]), int(parts[2])
        
        G.nodes[node]['x'] = c * 20
        G.nodes[node]['y'] = r * 20
        
        if node == safe_node:
            G.nodes[node]['type'] = 'camp'
            G.nodes[node]['capacity'] = 20000
            G.nodes[node]['conflict'] = 0.0
        elif node == conflict_center:
            G.nodes[node]['type'] = 'conflict'
            G.nodes[node]['capacity'] = -1
            G.nodes[node]['conflict'] = 1.0
        else:
            # Gradient of conflict
            dist_to_conflict = np.sqrt(r**2 + c**2)
            G.nodes[node]['type'] = 'town'
            G.nodes[node]['capacity'] = 2000
            G.nodes[node]['conflict'] = max(0.0, 1.0 - dist_to_conflict/5.0)

    # Add random obstacles (remove nodes)
    nodes_to_remove = []
    for node in G.nodes():
        if node not in [safe_node, conflict_center] and np.random.random() < 0.15:
            nodes_to_remove.append(node)
    
    G.remove_nodes_from(nodes_to_remove)
    
    # Ensure connectivity: Check if path exists from conflict to safe
    if not nx.has_path(G, conflict_center, safe_node):
        # Restore nodes or recreate path
        # Simple fix: Add direct diagonal path of nodes back
        current = (0,0)
        target = (rows-1, cols-1)
        while current != target:
            r, c = current
            # Move towards target
            if r < target[0]: r += 1
            if c < target[1]: c += 1
            
            node_name = f"Loc_{r}_{c}"
            if node_name not in G:
                G.add_node(node_name, x=c*20, y=r*20, type='town', capacity=2000, conflict=0.5)
            
            # Connect to previous
            prev_name = f"Loc_{current[0]}_{current[1]}"
            if prev_name in G:
                G.add_edge(prev_name, node_name, distance=20.0)
                G.add_edge(node_name, prev_name, distance=20.0)
            
            current = (r, c)
            
    # Set edge distances for any newly added edges or existing ones
    for u, v in G.edges():
        G.edges[u, v]['distance'] = 20.0
        
    return G, "Lattice"

def generate_hub_and_spoke_topology():
    """
    Generates a Hub-and-Spoke network with cycles.
    Rationale: Models major transit hubs with some redundancy.
    """
    G = nx.DiGraph()
    
    # Central Hub
    G.add_node("CentralHub", type="town", x=100, y=100, capacity=10000, conflict=0.1)
    
    # Ring of Spoke Towns (Transit)
    spokes = []
    num_spokes = 6
    radius = 40
    for i in range(num_spokes):
        angle = 2 * np.pi * i / num_spokes
        x = 100 + radius * np.cos(angle)
        y = 100 + radius * np.sin(angle)
        name = f"Spoke_{i}"
        G.add_node(name, type="town", x=x, y=y, capacity=3000, conflict=0.3)
        spokes.append(name)
        
        # Connect to Hub (bidirectional)
        G.add_edge(name, "CentralHub", distance=30.0)
        G.add_edge("CentralHub", name, distance=30.0)
        
    # Connect Spokes to form a ring (Cycles)
    for i in range(num_spokes):
        u = spokes[i]
        v = spokes[(i+1) % num_spokes]
        G.add_edge(u, v, distance=25.0)
        G.add_edge(v, u, distance=25.0)
        
    # Safe Zones (connected to some spokes)
    G.add_node("SafeZone_North", type="camp", x=100, y=180, capacity=10000, conflict=0.0)
    G.add_edge(spokes[1], "SafeZone_North", distance=40.0)
    G.add_edge(spokes[2], "SafeZone_North", distance=40.0)
    
    # Conflict Zones (Outer rim)
    for i in range(8):
        angle = 2 * np.pi * (i + 0.5) / 8
        x = 100 + 80 * np.cos(angle)
        y = 100 + 80 * np.sin(angle)
        name = f"Village_{i}"
        G.add_node(name, type="conflict", x=x, y=y, capacity=-1, conflict=1.0)
        
        # Connect to nearest spoke
        # Find nearest spoke index
        nearest_spoke_idx = int((angle / (2 * np.pi)) * num_spokes) % num_spokes
        G.add_edge(name, spokes[nearest_spoke_idx], distance=50.0)
        
    return G, "HubAndSpoke"

def generate_bottleneck_topology():
    """
    Generates a funnel shape: Many sources -> Few Transit -> One Border.
    Rationale: Border crossings are bottlenecks. High congestion risk.
    """
    G = nx.DiGraph()
    
    # 1. Border Post (Safe Zone)
    G.add_node("BorderPost", type="camp", x=200, y=100, capacity=20000, conflict=0.0)
    
    # 2. Transit Hubs (The Bottleneck)
    G.add_node("TransitHub", type="town", x=150, y=100, capacity=5000, conflict=0.2)
    G.add_edge("TransitHub", "BorderPost", distance=50.0)
    
    # 3. Feeder Towns
    for i in range(3):
        name = f"Feeder_{i}"
        G.add_node(name, type="town", x=100, y=50 + i*50, capacity=3000, conflict=0.5)
        G.add_edge(name, "TransitHub", distance=50.0)
        # Add lateral connection
        if i > 0:
            G.add_edge(f"Feeder_{i-1}", name, distance=30.0)
            G.add_edge(name, f"Feeder_{i-1}", distance=30.0)
            
    # 4. Conflict Zones (Origins)
    for i in range(5):
        name = f"Village_{i}"
        G.add_node(name, type="conflict", x=0, y=20 + i*40, capacity=-1, conflict=1.0)
        # Connect to random feeder
        feeder = f"Feeder_{np.random.randint(0,3)}"
        G.add_edge(name, feeder, distance=100.0)
        
    return G, "Bottleneck"

# =============================================================================
# 2. Heuristics Calculation
# =============================================================================

def calculate_network_heuristics(G):
    """
    Calculates network metrics that agents might use as heuristics (or that describe the topology).
    Returns a dict of metrics for the graph and per-node.
    """
    metrics = {}
    
    # 1. Shortest Path to Safe Zone (for every node)
    # Find safe zones
    safe_zones = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'camp']
    
    node_metrics = {}
    for node in G.nodes():
        min_dist = float('inf')
        nearest_safe = None
        
        for sz in safe_zones:
            try:
                dist = nx.shortest_path_length(G, node, sz, weight='distance')
                if dist < min_dist:
                    min_dist = dist
                    nearest_safe = sz
            except nx.NetworkXNoPath:
                continue
        
        node_metrics[node] = {
            'dist_to_safe': min_dist if min_dist != float('inf') else -1,
            'nearest_safe': nearest_safe
        }
        
    # 2. Betweenness Centrality (proxy for potential congestion)
    betweenness = nx.betweenness_centrality(G, weight='distance')
    for node, bc in betweenness.items():
        node_metrics[node]['betweenness'] = bc
        
    metrics['node_metrics'] = node_metrics
    metrics['avg_clustering'] = nx.average_clustering(G.to_undirected()) # Approximation
    
    return metrics

# =============================================================================
# 3. Flee Simulation Integration
# =============================================================================

def run_flee_simulation(G, topology_name, output_dir="data/comprehensive"):
    """
    Converts NetworkX graph to Flee inputs, runs simulation, and logs agent travel times.
    """
    output_dir = Path(output_dir) / topology_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Starting simulation for {topology_name}...")
    
    # 1. Setup Simulation Settings
    sim_settings = {
        "log_levels": {"agent": 1, "link": 0, "camp": 1, "init": 0}, # Agent logging ON
        "spawn_rules": {
            "take_from_population": False,
            "insert_day0": True
        },
        "move_rules": {
            "max_move_speed": 20.0,
            "max_walk_speed": 8.0,
            "camp_movechance": 0.001,
            "conflict_movechance": 1.0,
            "default_movechance": 0.5,
            "two_system_decision_making": True, # Use S1/S2
            "s1s2_model": {
                "enabled": True,
                "alpha": 1.0,
                "beta": 1.0,
                "p_s2": 0.9
            }
        },
        "optimisations": {"hasten": 1}
    }
    
    with open(output_dir / "simsetting.yml", "w") as f:
        yaml.dump(sim_settings, f)
        
    # 2. Convert Graph to Flee Ecosystem
    # Note: We can't easily use Flee's CSV readers here without writing files first.
    # So we'll write the CSVs, then read them in.
    
    # Locations CSV
    loc_df_data = []
    for node, attr in G.nodes(data=True):
        loc_df_data.append({
            'name': node,
            'region': 'unknown',
            'x': attr['x'],
            'y': attr['y'],
            'location_type': attr['type'],
            'movechance': 1.0 if attr['type']=='conflict' else 0.001 if attr['type']=='camp' else 0.5,
            'capacity': attr['capacity'],
            'pop': 0,
            'country': 'unknown',
            'conflict': attr['conflict'],
            'conflict_date': 0
        })
    pd.DataFrame(loc_df_data).to_csv(output_dir / "locations.csv", index=False)
    
    # Routes CSV
    route_df_data = []
    for u, v, attr in G.edges(data=True):
        route_df_data.append({
            'from': u,
            'to': v,
            'distance': attr.get('distance', 10.0)
        })
    pd.DataFrame(route_df_data).to_csv(output_dir / "routes.csv", index=False)
    
    # 3. Initialize Flee
    SimulationSettings.ReadFromYML(str(output_dir / "simsetting.yml"))
    e = flee.Ecosystem()
    
    # Load locations
    locations_df = pd.read_csv(output_dir / "locations.csv")
    for _, row in locations_df.iterrows():
        loc = e.addLocation(
            name=row['name'],
            x=row['x'],
            y=row['y'],
            location_type=row['location_type'],
            movechance=row['movechance'],
            capacity=row['capacity']
        )
        loc.conflict = row['conflict']
        
    # Load routes
    routes_df = pd.read_csv(output_dir / "routes.csv")
    for _, row in routes_df.iterrows():
        e.linkUp(row['from'], row['to'], float(row['distance']))
        
    # 4. Spawn Agents
    # Spawn in conflict zones
    conflict_nodes = [n for n, attr in G.nodes(data=True) if attr['type'] == 'conflict']
    
    for c_node in conflict_nodes:
        # Find the Flee location object
        loc_obj = next(l for l in e.locations if l.name == c_node)
        # Add 500 agents per conflict node
        for i in range(500):
            # Varied attributes for S1/S2
            attr = {
                "connections": np.random.randint(0, 10),
                "education_level": np.random.random(),
                "agent_id": f"{c_node}_{i}"
            }
            e.addAgent(loc_obj, attr)
            
    print(f"👥 Spawned {500 * len(conflict_nodes)} agents.")
    
    # 5. Run Simulation
    sim_days = 50
    # Store start times (implicitly t=0 for all)
    # To track arrival times, we monitor the agents.out file or internal state
    
    # We will use the agent logger built into Flee, but we need to run it inside the output dir
    cwd = os.getcwd()
    os.chdir(output_dir)
    
    try:
        # Clear old logs
        if os.path.exists("agents.out.0"):
            os.remove("agents.out.0")
            
        for t in range(sim_days):
            e.evolve()
            if t % 10 == 0:
                print(f"📅 Day {t}/{sim_days}")
                
        print("✅ Simulation complete.")
        
    finally:
        os.chdir(cwd)
        
    return e

# =============================================================================
# 4. Analysis
# =============================================================================

def analyze_travel_times(topology_name, safe_zone_names, output_dir="comprehensive_results"):
    """
    Parses agent logs to calculate travel times.
    Travel Time = Arrival Time at Camp - Start Time (0)
    """
    log_path = Path(output_dir) / topology_name / "agents.out.0"
    if not log_path.exists():
        print(f"❌ Log not found: {log_path}")
        return None
        
    print(f"📊 Analyzing log: {log_path}")
    
    # Parse the log file (simple CSV)
    # Expected cols: #time, rank-agentid, ... current_location, ...
    # We need to find the FIRST time an agent appears in a 'camp' location.
    
    arrivals = {} # agent_id -> arrival_time
    
    with open(log_path, 'r') as f:
        header = f.readline() # Skip header
        # Parse header to find indices
        cols = [c.strip() for c in header.replace('#','').split(',')]
        try:
            idx_time = cols.index('time')
            idx_id = cols.index('rank-agentid')
            idx_loc = cols.index('current_location')
        except ValueError:
            print("❌ Could not parse log header.")
            return None
            
        for line in f:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < len(cols): continue
            
            time = int(parts[idx_time])
            agent_id = parts[idx_id]
            loc = parts[idx_loc]
            
            # Check if this location is a camp/safe zone
            if loc in safe_zone_names:
                if agent_id not in arrivals:
                    arrivals[agent_id] = time
    
    if not arrivals:
        print(f"⚠️ No arrivals found in simulation logs for {topology_name}. Safe zones: {safe_zone_names}")
        return []
        
    travel_times = list(arrivals.values())
    avg_time = np.mean(travel_times)
    print(f"⏱️ Average Travel Time: {avg_time:.2f} days (N={len(travel_times)})")
    
    return travel_times

# =============================================================================
# Main Execution
# =============================================================================

def main():
    print("🌍 GENERATING COMPREHENSIVE REFUGEE TOPOLOGIES")
    print("==============================================")
    
    topologies = [
        generate_hierarchical_topology(),
        generate_lattice_topology(),
        generate_bottleneck_topology(),
        generate_hub_and_spoke_topology()
    ]
    
    results = {}
    
    for G, name in topologies:
        print(f"\n🏗️ Processing Topology: {name}")
        print(f"   Nodes: {len(G.nodes())}, Edges: {len(G.edges())}")
        
        # 1. Calc Heuristics
        heuristics = calculate_network_heuristics(G)
        # Average distance to safe zone from conflict nodes
        conflict_nodes = [n for n, attr in G.nodes(data=True) if attr['type'] == 'conflict']
        avg_heuristic_dist = np.mean([heuristics['node_metrics'][n]['dist_to_safe'] for n in conflict_nodes])
        print(f"   Avg Heuristic Distance (from conflict): {avg_heuristic_dist:.2f}")
        
        # 2. Run Simulation
        e = run_flee_simulation(G, name)
        
        # 3. Analyze
        # Get safe zone names from graph
        safe_zones = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'camp']
        travel_times = analyze_travel_times(name, safe_zones)
        
        results[name] = {
            "avg_travel_time": np.mean(travel_times) if travel_times else -1,
            "heuristic_distance": avg_heuristic_dist,
            "arrival_count": len(travel_times) if travel_times else 0,
            "node_count": len(G.nodes()),
            "edge_count": len(G.edges())
        }
        
    # Summary
    print("\n📝 SUMMARY RESULTS")
    print(json.dumps(results, indent=2))
    
    # Save results
    out_dir = Path("data/comprehensive")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "summary.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()

