#!/usr/bin/env python3
"""
Generate high-fidelity nuclear evacuation topologies (Ring, Star, Linear) for FLEE simulations.
Creates locations.csv and routes.csv for each topology with more nodes and realism.
"""

import os
import csv
import numpy as np
from pathlib import Path

def write_flee_csvs(output_dir, locations, routes):
    """Write standard FLEE input CSVs."""
    output_dir = Path(output_dir)
    input_dir = output_dir / "input_csv"
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # locations.csv
    # Header: name, region, country, gps_x, gps_y, location_type, conflict_date, pop, movechance, capacity
    with open(input_dir / "locations.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "region", "country", "gps_x", "gps_y", "location_type", "conflict_date", "pop", "movechance", "capacity"])
        for loc in locations:
            writer.writerow([
                loc["name"], 
                loc.get("region", "Region1"), 
                loc.get("country", "CountryA"),
                loc["x"], loc["y"], 
                loc["type"], 
                loc.get("conflict_date", 0),
                loc.get("pop", 0),
                loc.get("movechance", 0.0),
                loc.get("capacity", -1)
            ])
            
    # routes.csv
    # Header: name1, name2, distance
    with open(input_dir / "routes.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name1", "name2", "distance"])
        for route in routes:
            writer.writerow([route["from"], route["to"], route["distance"]])
            
    # conflicts.csv
    with open(input_dir / "conflicts.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["# year-month-day", "location", "conflict_value"])
        for loc in locations:
            if loc["type"] == "conflict" or loc.get("conflict", 0) > 0:
                writer.writerow(["0-1-1", loc["name"], loc.get("conflict", 1.0)])

    # closures.csv (empty)
    with open(input_dir / "closures.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["closure_type", "name1", "name2", "start_date", "end_date"])

    # sim_period.csv
    with open(input_dir / "sim_period.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["30"]) # 30 days default

def generate_ring_hf():
    """Concentric rings radiating from Facility - High Fidelity."""
    # Central Facility (Origin)
    locations = [{"name": "Facility", "x": 0, "y": 0, "type": "conflict", "conflict": 1.0, "pop": 0, "movechance": 1.0}]
    routes = []
    
    # Rings 1 to 5
    n_rings = 5
    nodes_per_ring = [4, 8, 12, 16, 20]
    radii = [20, 45, 75, 110, 150]
    conflicts = [0.8, 0.6, 0.4, 0.2, 0.1]
    
    for r_idx in range(n_rings):
        n_nodes = nodes_per_ring[r_idx]
        radius = radii[r_idx]
        conflict = conflicts[r_idx]
        
        for i in range(n_nodes):
            angle = 2 * np.pi * i / n_nodes
            name = f"Ring{r_idx+1}_Node{i}"
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            locations.append({"name": name, "x": round(x, 2), "y": round(y, 2), "type": "town", "conflict": conflict, "pop": 0, "movechance": 1.0})
            
            # Connect to Facility if first ring
            if r_idx == 0:
                routes.append({"from": "Facility", "to": name, "distance": radius})
            else:
                # Connect to nearest nodes in previous ring
                prev_n = nodes_per_ring[r_idx-1]
                prev_idx = int(i * prev_n / n_nodes)
                prev_name = f"Ring{r_idx}_Node{prev_idx}"
                routes.append({"from": prev_name, "to": name, "distance": radius - radii[r_idx-1]})
                
            # Connect to neighbors in same ring
            next_i = (i + 1) % n_nodes
            next_name = f"Ring{r_idx+1}_Node{next_i}"
            dist = 2 * radius * np.sin(np.pi / n_nodes)
            routes.append({"from": name, "to": next_name, "distance": round(dist, 2)})
            
    # Safe Zones at the edge (cardinal axes: 0°, 90°, 180°, 270° — avoids diagonal cross pattern)
    for i in range(4):
        angle = 2 * np.pi * i / 4
        name = f"SafeZone_{i}"
        radius = 200
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        locations.append({"name": name, "x": round(x, 2), "y": round(y, 2), "type": "camp", "conflict": 0.0, "capacity": 5000})
        
        # Connect to nearest ring nodes
        ring_idx = int(i * nodes_per_ring[-1] / 4)
        ring_name = f"Ring5_Node{ring_idx}"
        routes.append({"from": ring_name, "to": name, "distance": 50})

    write_flee_csvs("topologies/ring", locations, routes)

def generate_star_hf():
    """Hub-and-spoke radiating from Hub - High Fidelity."""
    locations = [{"name": "Hub", "x": 0, "y": 0, "type": "conflict", "conflict": 1.0, "pop": 0, "movechance": 1.0}]
    routes = []
    
    n_spokes = 8
    nodes_per_spoke = 6
    dist_step = 30
    
    for s in range(n_spokes):
        angle = 2 * np.pi * s / n_spokes
        prev_name = "Hub"
        
        for n in range(nodes_per_spoke):
            name = f"Spoke{s+1}_Node{n+1}"
            radius = (n + 1) * dist_step
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            # Higher conflict closer to hub
            conflict = max(0.1, 1.0 - (n + 1) * 0.15)
            locations.append({"name": name, "x": round(x, 2), "y": round(y, 2), "type": "town", "conflict": round(conflict, 2), "pop": 0, "movechance": 1.0})
            
            routes.append({"from": prev_name, "to": name, "distance": dist_step})
            prev_name = name
            
            # Cross-connections between spokes (web-like)
            if n > 1 and n < 5:
                prev_spoke = (s - 1) % n_spokes
                prev_spoke_name = f"Spoke{prev_spoke+1}_Node{n+1}"
                dist = 2 * radius * np.sin(np.pi / n_spokes)
                routes.append({"from": prev_spoke_name, "to": name, "distance": round(dist, 2)})

        # Safe Zone at the end of each spoke
        sz_name = f"SafeZone_{s+1}"
        radius = (nodes_per_spoke + 1) * dist_step
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        locations.append({"name": sz_name, "x": round(x, 2), "y": round(y, 2), "type": "camp", "conflict": 0.0, "capacity": 2500})
        routes.append({"from": prev_name, "to": sz_name, "distance": dist_step})

    write_flee_csvs("topologies/star", locations, routes)

def generate_linear_hf():
    """Single corridor with branches - High Fidelity."""
    locations = [{"name": "Facility", "x": 0, "y": 0, "type": "conflict", "conflict": 1.0, "pop": 0, "movechance": 1.0}]
    routes = []
    
    main_len = 10
    dist_step = 40
    
    # Main highway
    prev_name = "Facility"
    for i in range(main_len):
        name = f"Main_{i+1}"
        x = (i + 1) * dist_step
        y = 0
        conflict = max(0.1, 1.0 - (i + 1) * 0.1)
        locations.append({"name": name, "x": round(x, 2), "y": round(y, 2), "type": "town", "conflict": round(conflict, 2), "pop": 0, "movechance": 1.0})
        routes.append({"from": prev_name, "to": name, "distance": dist_step})
        
        # Side branches
        if i % 3 == 1:
            for side in [-1, 1]:
                side_name = f"Side_{i+1}_{'L' if side < 0 else 'R'}"
                locations.append({"name": side_name, "x": round(x, 2), "y": round(side * 50, 2), "type": "town", "conflict": round(conflict, 2), "pop": 0, "movechance": 1.0})
                routes.append({"from": name, "to": side_name, "distance": 50})
                
        prev_name = name
        
    # Multiple Safe Zones at the end
    for i, offset in enumerate([-50, 0, 50]):
        sz_name = f"SafeZone_{i+1}"
        locations.append({"name": sz_name, "x": round(main_len * dist_step + 60, 2), "y": offset, "type": "camp", "conflict": 0.0, "capacity": 5000})
        routes.append({"from": prev_name, "to": sz_name, "distance": 60})

    write_flee_csvs("topologies/linear", locations, routes)

if __name__ == "__main__":
    generate_ring_hf()
    generate_star_hf()
    generate_linear_hf()
    print("High-fidelity topologies generated in topologies/")
