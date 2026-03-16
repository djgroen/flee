#!/usr/bin/env python3
"""
Analyze Network Heuristics for Comprehensive Topologies
Calculates a priori network metrics (betweenness, shortest paths, etc.) 
to compare against simulation outcomes.
"""

import os
import csv
import json
import networkx as nx
import numpy as np
from pathlib import Path

class NetworkAnalyzer:
    def __init__(self, base_dir="comprehensive_topologies"):
        self.base_dir = Path(base_dir)
        
    def analyze_all(self):
        """Analyze all topologies found in the base directory."""
        if not self.base_dir.exists():
            print(f"❌ Base directory {self.base_dir} not found.")
            return

        for topo_dir in self.base_dir.iterdir():
            if topo_dir.is_dir():
                self.analyze_topology(topo_dir)

    def analyze_topology(self, topo_dir):
        """Analyze a single topology directory."""
        print(f"\n🔍 Analyzing {topo_dir.name}...")
        
        input_dir = topo_dir / "input_csv"
        locations_file = input_dir / "locations.csv"
        routes_file = input_dir / "routes.csv"
        
        if not locations_file.exists() or not routes_file.exists():
            print(f"   ⚠️ Missing CSV files in {topo_dir.name}")
            return

        # Build Graph
        G = nx.Graph() # Flee is undirected for movement usually, but routes are defined undirected?
        # Flee routes are typically bidirectional unless specified. Let's assume undirected for centrality.
        
        # Read Locations (Nodes)
        locations = {}
        origins = []
        destinations = []
        
        with open(locations_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['name']
                l_type = row['location_type']
                G.add_node(name, type=l_type, pos=(float(row['gps_x']), float(row['gps_y'])))
                locations[name] = row
                
                if "conflict" in l_type.lower():
                    origins.append(name)
                if "camp" in l_type.lower():
                    destinations.append(name)

        # Read Routes (Edges)
        with open(routes_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                u = row['name1']
                v = row['name2']
                dist = float(row['distance'])
                G.add_edge(u, v, weight=dist)

        # Calculate Metrics
        metrics = {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "origins": origins,
            "destinations": destinations,
            "centrality": {},
            "paths": {}
        }

        # 1. Centrality
        betweenness = nx.betweenness_centrality(G, weight='weight')
        closeness = nx.closeness_centrality(G, distance='weight')
        degree = nx.degree_centrality(G)
        
        for node in G.nodes():
            metrics["centrality"][node] = {
                "betweenness": betweenness[node],
                "closeness": closeness[node],
                "degree": degree[node]
            }

        # 2. Path Analysis (Origin -> Destination)
        for org in origins:
            for dst in destinations:
                if nx.has_path(G, org, dst):
                    path_key = f"{org}_to_{dst}"
                    
                    # Shortest Path (Weighted by distance)
                    shortest_path = nx.shortest_path(G, source=org, target=dst, weight='weight')
                    shortest_len = nx.shortest_path_length(G, source=org, target=dst, weight='weight')
                    
                    # All Simple Paths (limited to reasonable cutoff to avoid explosion)
                    # For small graphs this is fine.
                    simple_paths = list(nx.all_simple_paths(G, source=org, target=dst, cutoff=len(G.nodes)))
                    
                    metrics["paths"][path_key] = {
                        "shortest_path": shortest_path,
                        "shortest_distance": shortest_len,
                        "num_simple_paths": len(simple_paths),
                        "path_options": []
                    }
                    
                    # Analyze each simple path
                    for path in simple_paths:
                        # Calculate total distance
                        dist = sum(G[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                        # Max betweenness on path (bottleneck factor)
                        max_bet = max(betweenness[n] for n in path if n != org and n != dst) if len(path) > 2 else 0
                        
                        metrics["paths"][path_key]["path_options"].append({
                            "path": path,
                            "total_distance": dist,
                            "bottleneck_centrality": max_bet,
                            "efficiency": shortest_len / dist # 1.0 is optimal
                        })

        # Save Metrics
        output_file = topo_dir / "network_metrics.json"
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
            
        print(f"   ✅ Metrics saved to {output_file}")
        
        # Quick summary print
        max_bet_node = max(betweenness, key=betweenness.get)
        print(f"   🔹 Max Betweenness: {max_bet_node} ({betweenness[max_bet_node]:.3f})")
        print(f"   🔹 Paths analyzed: {len(metrics['paths'])}")

if __name__ == "__main__":
    analyzer = NetworkAnalyzer()
    analyzer.analyze_all()

