#!/usr/bin/env python3
"""
Systematic Topology Sensitivity Analysis
Target: Scientific Reports

This script systematically generates 8 fundamental topology types across varying scales (N),
runs Flee simulations, and aggregates metrics to determine topological sensitivity.
"""

import networkx as nx
import numpy as np
import pandas as pd
import os
import sys
import yaml
from pathlib import Path
from topology_generator import get_topology

# Add current directory to path
sys.path.insert(0, '.')

try:
    from flee import flee
    from flee.SimulationSettings import SimulationSettings
except ImportError:
    print("Error: Flee not found.")
    sys.exit(1)

def run_simulation(G, topology_type, scale_N, run_id, output_base="systematic_results"):
    """Runs a single simulation for a given graph."""
    
    # Setup Directory
    output_dir = Path(output_base) / f"{topology_type}_N{scale_N}_Run{run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Config
    sim_settings = {
        "log_levels": {"agent": 1, "link": 0, "camp": 0, "init": 0},
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
            "two_system_decision_making": True
        },
        "optimisations": {"hasten": 1}
    }
    with open(output_dir / "simsetting.yml", "w") as f:
        yaml.dump(sim_settings, f)
        
    # 2. Write Network Files
    loc_data = []
    for n, attr in G.nodes(data=True):
        loc_data.append({
            'name': n, 
            'x': attr.get('x',0), 
            'y': attr.get('y',0), 
            'location_type': attr['type'], 
            'movechance': 1.0 if attr['type']=='conflict' else 0.001 if attr['type']=='camp' else 0.5,
            'capacity': attr['capacity'], 
            'pop': 0, 
            'conflict': attr['conflict'], 
            'country': 'unknown', 
            'region': 'unknown', 
            'conflict_date': 0
        })
    pd.DataFrame(loc_data).to_csv(output_dir / "locations.csv", index=False)
    
    route_data = [{'from': u, 'to': v, 'distance': d['distance']} for u, v, d in G.edges(data=True)]
    pd.DataFrame(route_data).to_csv(output_dir / "routes.csv", index=False)
    
    # 3. Initialize Flee
    try:
        SimulationSettings.ReadFromYML(str(output_dir / "simsetting.yml"))
        e = flee.Ecosystem()
        
        df_loc = pd.read_csv(output_dir / "locations.csv")
        for _, row in df_loc.iterrows():
            l = e.addLocation(row['name'], x=row['x'], y=row['y'], location_type=row['location_type'], movechance=row['movechance'], capacity=row['capacity'])
            l.conflict = row['conflict']
            
        df_route = pd.read_csv(output_dir / "routes.csv")
        for _, row in df_route.iterrows():
            e.linkUp(row['from'], row['to'], float(row['distance']))
            
        # 4. Spawn Agents
        conflict_nodes = [n for n, attr in G.nodes(data=True) if attr['type'] == 'conflict']
        agents_per_node = 200 # Fixed load per source
        
        total_spawned = 0
        for c in conflict_nodes:
            locs = [l for l in e.locations if l.name == c]
            if locs:
                l = locs[0]
                for i in range(agents_per_node):
                    e.addAgent(l, {"agent_id": f"{c}_{i}"})
                    total_spawned += 1
                    
        print(f"   [{topology_type} N={scale_N}] Running with {total_spawned} agents...", flush=True)
        
        # 5. Run Loop
        cwd = os.getcwd()
        os.chdir(output_dir)
        try:
            if os.path.exists("agents.out.0"): os.remove("agents.out.0")
            for t in range(50):
                e.evolve()
        finally:
            os.chdir(cwd)
            
        # 6. Analyze
        log_path = output_dir / "agents.out.0"
        if not log_path.exists(): return None
        
        safe_zones = [n for n, attr in G.nodes(data=True) if attr['type'] == 'camp']
        arrivals = {}
        
        with open(log_path, 'r') as f:
            header_line = f.readline()
            if not header_line: return None
            cols = [c.strip() for c in header_line.replace('#','').split(',')]
            t_idx = cols.index('time')
            id_idx = cols.index('rank-agentid')
            loc_idx = cols.index('current_location')
            
            for line in f:
                p = [x.strip() for x in line.split(',')]
                if len(p) < len(cols): continue
                try:
                    t = int(p[t_idx])
                    aid = p[id_idx]
                    loc = p[loc_idx]
                    if loc in safe_zones and aid not in arrivals:
                        arrivals[aid] = t
                except: continue
                
        times = list(arrivals.values())
        avg_time = np.mean(times) if times else 0
        arrival_rate = len(arrivals) / total_spawned if total_spawned > 0 else 0
        
        # Ideal Time (Average shortest path from all conflict nodes to nearest safe)
        ideal_times = []
        for c in conflict_nodes:
            try:
                dists = [nx.shortest_path_length(G, c, s, weight='distance') for s in safe_zones]
                if dists:
                    ideal_times.append(min(dists) / 20.0) # max speed 20
            except: pass
        avg_ideal = np.mean(ideal_times) if ideal_times else 1.0
        
        return {
            "Topology": topology_type,
            "Scale_N": scale_N,
            "Nodes": len(G.nodes()),
            "Edges": len(G.edges()),
            "Agents": total_spawned,
            "AvgTravelTime": avg_time,
            "AvgIdealTime": avg_ideal,
            "DelayFactor": avg_time / avg_ideal if avg_ideal > 0 else 0,
            "ArrivalRate": arrival_rate
        }
        
    except Exception as e:
        print(f"   Error in {topology_type}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    topology_types = [
        "Linear", "Dendritic", "Lattice", "HubAndSpoke", 
        "Bottleneck", "Parallel", "SmallWorld", "Random"
    ]
    scales = [20, 50, 100] # Sensitivity Analysis
    
    results = []
    
    print("🚀 Starting Systematic Topology Sweep...")
    
    for topo in topology_types:
        for N in scales:
            print(f"\n🏗️ Generating {topo} (Scale ~{N})...")
            try:
                G = get_topology(topo, size_scale=N)
                res = run_simulation(G, topo, N, run_id=1)
                if res:
                    results.append(res)
                    print(f"   ✅ {topo} N={N}: Delay={res['DelayFactor']:.2f}, Arrivals={res['ArrivalRate']:.2f}")
            except Exception as e:
                print(f"   ❌ Generation Failed: {e}")
                
    # Save Summary
    df = pd.read_csv("systematic_results/summary.csv") if os.path.exists("systematic_results/summary.csv") else pd.DataFrame()
    new_df = pd.DataFrame(results)
    final_df = pd.concat([df, new_df])
    
    os.makedirs("systematic_results", exist_ok=True)
    final_df.to_csv("systematic_results/summary.csv", index=False)
    print("\n💾 Results saved to systematic_results/summary.csv")
    
    # Generate Plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(12, 8))
    for topo in topology_types:
        subset = final_df[final_df['Topology'] == topo].sort_values('Scale_N')
        if not subset.empty:
            plt.plot(subset['Scale_N'], subset['DelayFactor'], marker='o', label=topo, linewidth=2)
            
    plt.xlabel('Network Scale (Target Nodes)')
    plt.ylabel('Delay Factor (Actual/Ideal)')
    plt.title('Topological Sensitivity: Efficiency vs Scale')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('systematic_results/sensitivity_plot.png')
    print("📊 Plot saved to systematic_results/sensitivity_plot.png")

if __name__ == "__main__":
    main()

