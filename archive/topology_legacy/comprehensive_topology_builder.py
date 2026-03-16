#!/usr/bin/env python3
"""
Comprehensive Topology Builder for Scientific Reports Paper
Generates complex network topologies with specific rationales:
1. Bottleneck (Bridge)
2. Urban-Rural Interface
3. Parallel Paths (Risk Gradient)
4. River Crossing (Geographic Barrier)

Output: Creates directories with input CSVs (locations.csv, routes.csv) for each topology.
"""

import os
import csv
import shutil
import numpy as np
from pathlib import Path

class TopologyBuilder:
    def __init__(self, output_base_dir="comprehensive_topologies"):
        self.base_dir = Path(output_base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def _write_csvs(self, name, locations, routes):
        """Write locations and routes to CSV files in a standard Flee directory structure."""
        sim_dir = self.base_dir / name
        input_dir = sim_dir / "input_csv"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Write locations.csv
        with open(input_dir / "locations.csv", "w") as f:
            writer = csv.writer(f)
            # Standard Flee header
            writer.writerow(["name", "region", "country", "gps_x", "gps_y", "location_type", "conflict_date", "pop", "movechance", "capacity"])
            
            for loc in locations:
                # Defaults
                region = loc.get("region", "Region1")
                country = loc.get("country", "CountryA")
                conflict_date = loc.get("conflict_date", 0)
                pop = loc.get("pop", 0)
                movechance = loc.get("movechance", 0.0) # Default handled by Flee based on type, but can override
                capacity = loc.get("capacity", -1)
                
                # Flee expects movechance=1.0 for conflict, 0.001 for camps usually, but let's be explicit if needed
                # Actually Flee usually ignores this column if location_type is set, unless specific overrides
                
                writer.writerow([
                    loc["name"], region, country, 
                    loc["x"], loc["y"], 
                    loc["type"], conflict_date, 
                    pop, movechance, capacity
                ])

        # Write routes.csv
        with open(input_dir / "routes.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["name1", "name2", "distance"])
            for route in routes:
                writer.writerow([route["from"], route["to"], route["distance"]])
                
        # Write closures.csv (empty)
        with open(input_dir / "closures.csv", "w") as f:
            f.write("closure_type,name1,name2,start_date,end_date\n")
            
        print(f"✅ Created topology: {name}")
        return sim_dir

    def build_bottleneck(self):
        """
        Topology 1: The Bottleneck
        Rationale: High betweenness centrality node (Bridge) that becomes a congestion point.
        Structure: 
            - 3 Origin Towns (Conflict) feeding into...
            - 2 Junctions feeding into...
            - 1 Bridge (Bottleneck) feeding into...
            - 1 Distribution Hub feeding into...
            - 2 Camps (Safe)
        """
        locations = [
            # Origins (High Conflict)
            {"name": "Origin_A", "x": 0, "y": 100, "type": "conflict", "pop": 5000},
            {"name": "Origin_B", "x": 0, "y": 0,   "type": "conflict", "pop": 5000},
            {"name": "Origin_C", "x": 0, "y": -100, "type": "conflict", "pop": 5000},
            
            # Junctions
            {"name": "Junction_North", "x": 50, "y": 50, "type": "town", "pop": 1000},
            {"name": "Junction_South", "x": 50, "y": -50, "type": "town", "pop": 1000},
            
            # The Bottleneck
            {"name": "The_Bridge", "x": 100, "y": 0, "type": "town", "pop": 500},
            
            # Hub
            {"name": "Safe_Hub", "x": 150, "y": 0, "type": "town", "pop": 2000},
            
            # Camps
            {"name": "Camp_Alpha", "x": 200, "y": 50, "type": "camp", "capacity": 10000},
            {"name": "Camp_Beta",  "x": 200, "y": -50, "type": "camp", "capacity": 10000},
            
            # Alternative Long Route (Bypass) - Very long, skips bridge
            {"name": "Mountain_Pass", "x": 100, "y": 150, "type": "town", "pop": 100}
        ]
        
        routes = [
            # Feeding the junctions
            {"from": "Origin_A", "to": "Junction_North", "distance": 60},
            {"from": "Origin_B", "to": "Junction_North", "distance": 60},
            {"from": "Origin_B", "to": "Junction_South", "distance": 60},
            {"from": "Origin_C", "to": "Junction_South", "distance": 60},
            
            # Feeding the bridge
            {"from": "Junction_North", "to": "The_Bridge", "distance": 60},
            {"from": "Junction_South", "to": "The_Bridge", "distance": 60},
            
            # Crossing the bridge
            {"from": "The_Bridge", "to": "Safe_Hub", "distance": 50},
            
            # To camps
            {"from": "Safe_Hub", "to": "Camp_Alpha", "distance": 60},
            {"from": "Safe_Hub", "to": "Camp_Beta", "distance": 60},
            
            # The Bypass (Long but safer/less congested?)
            {"from": "Origin_A", "to": "Mountain_Pass", "distance": 120},
            {"from": "Mountain_Pass", "to": "Camp_Alpha", "distance": 150}
        ]
        
        return self._write_csvs("bottleneck", locations, routes)

    def build_urban_rural(self):
        """
        Topology 2: Urban-Rural Interface
        Rationale: Dense, grid-like urban area (high choice, confusion) transitioning to sparse rural roads.
        Structure: 3x3 Grid (Urban) -> Single exit highway -> Rural forks -> Camps.
        """
        locations = []
        routes = []
        
        # 3x3 Grid (Urban Center) - x from 0 to 40, y from -20 to 20
        # Center at 20,0 is the conflict epicenter
        for i in range(3):
            for j in range(3):
                name = f"CityBlock_{i}_{j}"
                x = i * 20
                y = (j - 1) * 20
                
                # Center is high conflict
                l_type = "conflict" if (i == 1 and j == 1) else "town"
                pop = 2000 if l_type == "conflict" else 500
                
                locations.append({"name": name, "x": x, "y": y, "type": l_type, "pop": pop})
                
        # Grid connections
        for i in range(3):
            for j in range(3):
                curr = f"CityBlock_{i}_{j}"
                # East
                if i < 2:
                    next_node = f"CityBlock_{i+1}_{j}"
                    routes.append({"from": curr, "to": next_node, "distance": 20})
                # North (y increases)
                if j < 2:
                    next_node = f"CityBlock_{i}_{j+1}"
                    routes.append({"from": curr, "to": next_node, "distance": 20})
                    
        # Exit Highway (from CityBlock_2_1, the east-center node)
        locations.append({"name": "Highway_Exit", "x": 80, "y": 0, "type": "town", "pop": 200})
        routes.append({"from": "CityBlock_2_1", "to": "Highway_Exit", "distance": 40})
        
        # Rural Forks
        locations.append({"name": "Rural_Junction", "x": 120, "y": 0, "type": "town", "pop": 100})
        routes.append({"from": "Highway_Exit", "to": "Rural_Junction", "distance": 40})
        
        # Camps
        locations.append({"name": "Camp_North", "x": 160, "y": 40, "type": "camp", "capacity": 5000})
        locations.append({"name": "Camp_South", "x": 160, "y": -40, "type": "camp", "capacity": 5000})
        
        routes.append({"from": "Rural_Junction", "to": "Camp_North", "distance": 60})
        routes.append({"from": "Rural_Junction", "to": "Camp_South", "distance": 60})
        
        return self._write_csvs("urban_rural", locations, routes)

    def build_parallel_paths(self):
        """
        Topology 3: Parallel Paths (Risk Gradient)
        Rationale: Choice between short/risky and long/safe.
        Structure: Origin -> Split into 3 paths -> Destination.
        """
        locations = [
            {"name": "Conflict_Origin", "x": 0, "y": 0, "type": "conflict", "pop": 10000},
            {"name": "Safe_Border", "x": 200, "y": 0, "type": "camp", "capacity": 20000}
        ]
        
        routes = []
        
        # Path 1: The "Direct Line" (Shortest, will have high conflict in sim settings)
        # 2 stops, total dist 200
        locations.append({"name": "Path1_Stop1", "x": 70, "y": 0, "type": "town", "pop": 500})
        locations.append({"name": "Path1_Stop2", "x": 140, "y": 0, "type": "town", "pop": 500})
        routes.append({"from": "Conflict_Origin", "to": "Path1_Stop1", "distance": 70})
        routes.append({"from": "Path1_Stop1", "to": "Path1_Stop2", "distance": 70})
        routes.append({"from": "Path1_Stop2", "to": "Safe_Border", "distance": 60})
        
        # Path 2: The "Moderate Curve" (Medium length, medium safety)
        # 3 stops, arc up, total dist ~240
        locations.append({"name": "Path2_Stop1", "x": 50, "y": 40, "type": "town", "pop": 200})
        locations.append({"name": "Path2_Stop2", "x": 100, "y": 60, "type": "town", "pop": 200})
        locations.append({"name": "Path2_Stop3", "x": 150, "y": 40, "type": "town", "pop": 200})
        routes.append({"from": "Conflict_Origin", "to": "Path2_Stop1", "distance": 65})
        routes.append({"from": "Path2_Stop1", "to": "Path2_Stop2", "distance": 55})
        routes.append({"from": "Path2_Stop2", "to": "Path2_Stop3", "distance": 55})
        routes.append({"from": "Path2_Stop3", "to": "Safe_Border", "distance": 65})
        
        # Path 3: The "Long Way Round" (Longest, Safest)
        # 4 stops, wide arc down, total dist ~320
        locations.append({"name": "Path3_Stop1", "x": 40, "y": -60, "type": "town", "pop": 100})
        locations.append({"name": "Path3_Stop2", "x": 80, "y": -80, "type": "town", "pop": 100})
        locations.append({"name": "Path3_Stop3", "x": 120, "y": -80, "type": "town", "pop": 100})
        locations.append({"name": "Path3_Stop4", "x": 160, "y": -60, "type": "town", "pop": 100})
        routes.append({"from": "Conflict_Origin", "to": "Path3_Stop1", "distance": 75})
        routes.append({"from": "Path3_Stop1", "to": "Path3_Stop2", "distance": 45})
        routes.append({"from": "Path3_Stop2", "to": "Path3_Stop3", "distance": 40})
        routes.append({"from": "Path3_Stop3", "to": "Path3_Stop4", "distance": 45})
        routes.append({"from": "Path3_Stop4", "to": "Safe_Border", "distance": 75})
        
        return self._write_csvs("parallel_paths", locations, routes)

    def build_river_crossing(self):
        """
        Topology 4: River Crossing
        Rationale: Geographic barrier forcing convergence.
        Structure: 
            - Left Bank (Conflict area) with scattered towns.
            - River (Barrier) with 2 bridges.
            - Right Bank (Safe area) with camps.
        """
        locations = []
        routes = []
        
        # Left Bank (Conflict)
        left_bank_nodes = [
            {"name": "LB_City", "x": 0, "y": 0, "type": "conflict", "pop": 8000},
            {"name": "LB_North", "x": 0, "y": 50, "type": "town", "pop": 1000},
            {"name": "LB_South", "x": 0, "y": -50, "type": "town", "pop": 1000},
            {"name": "LB_Coast", "x": -40, "y": 0, "type": "town", "pop": 1500}
        ]
        locations.extend(left_bank_nodes)
        
        # Connect Left Bank
        routes.append({"from": "LB_Coast", "to": "LB_City", "distance": 40})
        routes.append({"from": "LB_City", "to": "LB_North", "distance": 50})
        routes.append({"from": "LB_City", "to": "LB_South", "distance": 50})
        
        # Bridges (The Crossings)
        locations.append({"name": "Bridge_North", "x": 50, "y": 40, "type": "town", "pop": 200})
        locations.append({"name": "Bridge_South", "x": 50, "y": -40, "type": "town", "pop": 200})
        
        # Connect to bridges
        routes.append({"from": "LB_North", "to": "Bridge_North", "distance": 50})
        routes.append({"from": "LB_South", "to": "Bridge_South", "distance": 50})
        routes.append({"from": "LB_City", "to": "Bridge_North", "distance": 70}) # Diagonal
        routes.append({"from": "LB_City", "to": "Bridge_South", "distance": 70}) # Diagonal
        
        # Right Bank (Safe)
        locations.append({"name": "RB_Hub", "x": 100, "y": 0, "type": "town", "pop": 1000})
        locations.append({"name": "Camp_Safe", "x": 150, "y": 0, "type": "camp", "capacity": 15000})
        
        # Connect from bridges
        routes.append({"from": "Bridge_North", "to": "RB_Hub", "distance": 65})
        routes.append({"from": "Bridge_South", "to": "RB_Hub", "distance": 65})
        routes.append({"from": "RB_Hub", "to": "Camp_Safe", "distance": 50})
        
        # Direct bridge connection? No, force through Hub.
        
        return self._write_csvs("river_crossing", locations, routes)

def main():
    builder = TopologyBuilder()
    builder.build_bottleneck()
    builder.build_urban_rural()
    builder.build_parallel_paths()
    builder.build_river_crossing()
    print("\n✅ All comprehensive topologies generated in 'comprehensive_topologies/'")

if __name__ == "__main__":
    main()

