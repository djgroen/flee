#!/usr/bin/env python3
"""
Refugee Topology Generator

Generates network topologies specifically designed for testing S1/S2 cognitive differences
in refugee displacement scenarios. Creates evacuation routes, bottlenecks, and
hub-and-spoke refugee networks in Flee-compatible format.
"""

import csv
import random
import math
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Location:
    """Represents a location in the refugee network"""
    name: str
    x: float
    y: float
    location_type: str  # 'conflict', 'town', 'camp', 'idpcamp'
    population: int
    capacity: int = -1  # -1 for unlimited
    safety_score: float = 0.5
    livelihood_score: float = 0.3
    
@dataclass
class Route:
    """Represents a route between two locations"""
    name1: str
    name2: str
    distance: float
    forced_redirection: int = 0

class RefugeeTopologyGenerator:
    """Generates refugee-specific network topologies for S1/S2 testing"""
    
    def __init__(self, output_dir: str = "refugee_topologies"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_linear_evacuation_route(self, 
                                        n_intermediate: int = 1,
                                        segment_distance: float = 100.0,
                                        origin_population: int = 10000,
                                        camp_capacity: int = 5000) -> str:
        """Generate linear evacuation route: Origin → Town → Camp"""
        
        locations = []
        routes = []
        
        # Create origin (conflict zone)
        locations.append(Location(
            name="Origin",
            x=0.0,
            y=0.0,
            location_type="conflict",
            population=origin_population,
            safety_score=0.1,  # Very unsafe
            livelihood_score=0.2
        ))
        
        # Create intermediate towns
        for i in range(n_intermediate):
            locations.append(Location(
                name=f"Town_{i+1}",
                x=(i+1) * segment_distance,
                y=0.0,
                location_type="town",
                population=random.randint(1000, 3000),
                safety_score=0.4 + (i * 0.1),  # Gradually safer
                livelihood_score=0.3 + (i * 0.1)
            ))
        
        # Create final camp
        locations.append(Location(
            name="Camp",
            x=(n_intermediate + 1) * segment_distance,
            y=0.0,
            location_type="camp",
            population=0,
            capacity=camp_capacity,
            safety_score=0.8,  # Safe
            livelihood_score=0.4
        ))
        
        # Create routes connecting adjacent locations
        for i in range(len(locations) - 1):
            routes.append(Route(
                name1=locations[i].name,
                name2=locations[i+1].name,
                distance=segment_distance
            ))
        
        # Save topology
        topology_name = f"linear_evacuation_{n_intermediate}towns"
        self._save_topology(topology_name, locations, routes)
        return topology_name
    
    def generate_bottleneck_scenario(self,
                                   bottleneck_capacity: int = 100,
                                   camp_a_distance: float = 50.0,
                                   camp_b_distance: float = 200.0,
                                   origin_population: int = 5000) -> str:
        """Generate bottleneck scenario: Origin → Bottleneck → {Camp_A, Camp_B}"""
        
        locations = [
            Location(
                name="Origin",
                x=0.0,
                y=0.0,
                location_type="conflict",
                population=origin_population,
                safety_score=0.1,
                livelihood_score=0.2
            ),
            Location(
                name="Bottleneck",
                x=100.0,
                y=0.0,
                location_type="town",
                population=bottleneck_capacity,  # Limited capacity
                capacity=bottleneck_capacity,
                safety_score=0.5,
                livelihood_score=0.3
            ),
            Location(
                name="Camp_A_Close",
                x=100.0 + camp_a_distance,
                y=50.0,
                location_type="camp",
                population=0,
                capacity=2000,
                safety_score=0.6,  # Safe but limited
                livelihood_score=0.3
            ),
            Location(
                name="Camp_B_Better",
                x=100.0 + camp_b_distance,
                y=-50.0,
                location_type="camp",
                population=0,
                capacity=5000,
                safety_score=0.8,  # Safer and better
                livelihood_score=0.6
            )
        ]
        
        routes = [
            Route("Origin", "Bottleneck", 100.0),
            Route("Bottleneck", "Camp_A_Close", camp_a_distance),
            Route("Bottleneck", "Camp_B_Better", camp_b_distance)
        ]
        
        topology_name = "bottleneck_scenario"
        self._save_topology(topology_name, locations, routes)
        return topology_name
    
    def generate_star_refugee_network(self,
                                    n_camps: int = 4,
                                    hub_population: int = 2000,
                                    radius: float = 150.0,
                                    origin_population: int = 8000) -> str:
        """Generate star topology: Origin → Hub → Multiple Camps"""
        
        locations = [
            Location(
                name="Origin",
                x=0.0,
                y=0.0,
                location_type="conflict",
                population=origin_population,
                safety_score=0.1,
                livelihood_score=0.2
            ),
            Location(
                name="Hub",
                x=100.0,
                y=0.0,
                location_type="town",
                population=hub_population,
                safety_score=0.5,
                livelihood_score=0.4
            )
        ]
        
        routes = [
            Route("Origin", "Hub", 100.0)
        ]
        
        # Create camps in a circle around the hub
        camp_configs = [
            {"name": "Camp_North", "safety": 0.7, "livelihood": 0.4, "capacity": 3000},
            {"name": "Camp_East", "safety": 0.8, "livelihood": 0.6, "capacity": 4000},
            {"name": "Camp_South", "safety": 0.6, "livelihood": 0.3, "capacity": 2000},
            {"name": "Camp_West", "safety": 0.9, "livelihood": 0.5, "capacity": 5000}
        ]
        
        for i in range(min(n_camps, len(camp_configs))):
            angle = (2 * math.pi * i) / n_camps
            camp_x = 100.0 + radius * math.cos(angle)
            camp_y = radius * math.sin(angle)
            
            config = camp_configs[i]
            locations.append(Location(
                name=config["name"],
                x=camp_x,
                y=camp_y,
                location_type="camp",
                population=0,
                capacity=config["capacity"],
                safety_score=config["safety"],
                livelihood_score=config["livelihood"]
            ))
            
            routes.append(Route("Hub", config["name"], radius))
        
        topology_name = f"star_refugee_{n_camps}camps"
        self._save_topology(topology_name, locations, routes)
        return topology_name
    
    def generate_multi_destination_choice(self,
                                        origin_population: int = 6000) -> str:
        """Generate scenario testing destination choice: Close_Safe vs Medium_Balanced vs Far_Excellent"""
        
        locations = [
            Location(
                name="Origin",
                x=0.0,
                y=0.0,
                location_type="conflict",
                population=origin_population,
                safety_score=0.1,
                livelihood_score=0.2
            ),
            Location(
                name="Close_Safe",
                x=80.0,
                y=0.0,
                location_type="camp",
                population=0,
                capacity=2000,
                safety_score=0.7,  # Safe but limited opportunities
                livelihood_score=0.3
            ),
            Location(
                name="Medium_Balanced",
                x=0.0,
                y=150.0,
                location_type="camp",
                population=0,
                capacity=4000,
                safety_score=0.8,  # Good balance
                livelihood_score=0.5
            ),
            Location(
                name="Far_Excellent",
                x=-200.0,
                y=100.0,
                location_type="camp",
                population=0,
                capacity=6000,
                safety_score=0.9,  # Excellent but distant
                livelihood_score=0.7
            )
        ]
        
        routes = [
            Route("Origin", "Close_Safe", 80.0),
            Route("Origin", "Medium_Balanced", 150.0),
            Route("Origin", "Far_Excellent", 224.0)  # sqrt(200^2 + 100^2)
        ]
        
        topology_name = "multi_destination_choice"
        self._save_topology(topology_name, locations, routes)
        return topology_name
    
    def _save_topology(self, topology_name: str, locations: List[Location], routes: List[Route]) -> None:
        """Save topology to Flee-compatible CSV files"""
        
        # Create topology directory
        topo_dir = self.output_dir / topology_name
        topo_dir.mkdir(exist_ok=True)
        
        # Save locations.csv
        locations_file = topo_dir / "locations.csv"
        with open(locations_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'population'])
            
            for loc in locations:
                # Convert to Flee format
                conflict_date = "2023-01-01" if loc.location_type == "conflict" else ""
                writer.writerow([
                    loc.name,
                    "TestRegion",
                    "TestCountry", 
                    loc.y,  # lat
                    loc.x,  # lon
                    loc.location_type,
                    conflict_date,
                    loc.population
                ])
        
        # Save routes.csv
        routes_file = topo_dir / "routes.csv"
        with open(routes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name1', 'name2', 'distance', 'forced_redirection'])
            
            for route in routes:
                writer.writerow([
                    route.name1,
                    route.name2,
                    route.distance,
                    route.forced_redirection
                ])
        
        # Save additional refugee-specific attributes
        attributes_file = topo_dir / "location_attributes.csv"
        with open(attributes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'safety_score', 'livelihood_score', 'capacity'])
            
            for loc in locations:
                writer.writerow([
                    loc.name,
                    loc.safety_score,
                    loc.livelihood_score,
                    loc.capacity if loc.capacity > 0 else ""
                ])
        
        print(f"✅ Generated topology '{topology_name}' with {len(locations)} locations and {len(routes)} routes")
        print(f"   Saved to: {topo_dir}")

def test_refugee_topology_generator():
    """Test the RefugeeTopologyGenerator"""
    print("🧪 Testing RefugeeTopologyGenerator...")
    
    generator = RefugeeTopologyGenerator("test_topologies")
    
    # Test linear evacuation route
    print("\\n1. Generating linear evacuation route...")
    linear_topo = generator.generate_linear_evacuation_route(
        n_intermediate=2, 
        origin_population=8000,
        camp_capacity=4000
    )
    
    # Test bottleneck scenario
    print("\\n2. Generating bottleneck scenario...")
    bottleneck_topo = generator.generate_bottleneck_scenario(
        bottleneck_capacity=150,
        origin_population=6000
    )
    
    # Test star refugee network
    print("\\n3. Generating star refugee network...")
    star_topo = generator.generate_star_refugee_network(
        n_camps=4,
        origin_population=10000
    )
    
    # Test multi-destination choice
    print("\\n4. Generating multi-destination choice scenario...")
    choice_topo = generator.generate_multi_destination_choice(
        origin_population=5000
    )
    
    print(f"\\n✅ Generated {4} refugee topologies:")
    print(f"   - {linear_topo}")
    print(f"   - {bottleneck_topo}")
    print(f"   - {star_topo}")
    print(f"   - {choice_topo}")
    
    print("\\n✅ RefugeeTopologyGenerator test completed successfully!")

if __name__ == "__main__":
    test_refugee_topology_generator()