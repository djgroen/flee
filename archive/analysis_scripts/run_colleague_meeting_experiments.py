#!/usr/bin/env python3
"""
Colleague Meeting Experiments: S1/S2 Topology Sensitivity

CRITICAL REQUIREMENTS:
1. MUST run actual Flee simulation (NO synthetic data)
2. All agents start from single origin node
3. Multiple topologies: star, linear, hierarchical, regular grid, irregular grid
4. S1/S2 switching scenarios: baseline, low_s2, medium_s2, high_s2
5. Normalized metrics for comparison
6. Clear visualization of topology effects

For meeting demonstration.
"""

import sys
from pathlib import Path
import json
import time as time_module
import yaml
import csv
import numpy as np

# Add flee to path
sys.path.append('.')

from flee import flee
from flee.SimulationSettings import SimulationSettings
from flee import InputGeography
from flee.datamanager import handle_refugee_data


class TopologyGenerator:
    """Generate different network topologies for testing."""
    
    def __init__(self, size=8):
        self.size = size
        self.base_distance = 100.0  # km
    
    def generate_star(self):
        """Star: Central origin with spokes to camps."""
        locations = [{'name': 'Origin', 'type': 'conflict', 'lat': 0.0, 'lon': 0.0, 'pop': 5000}]
        
        # Camps arranged in circle
        for i in range(1, self.size):
            angle = 2 * np.pi * i / (self.size - 1)
            lat = self.base_distance * np.cos(angle) / 111.0  # Convert km to degrees
            lon = self.base_distance * np.sin(angle) / 111.0
            locations.append({
                'name': f'Camp_{i}',
                'type': 'camp',
                'lat': lat,
                'lon': lon,
                'pop': 0
            })
        
        # Routes: origin to all camps (star pattern)
        routes = []
        for i in range(1, self.size):
            routes.append({'from': 'Origin', 'to': f'Camp_{i}', 'distance': self.base_distance})
        
        return locations, routes
    
    def generate_linear(self):
        """Linear: Origin → Town → Town → ... → Camp."""
        locations = [{'name': 'Origin', 'type': 'conflict', 'lat': 0.0, 'lon': 0.0, 'pop': 5000}]
        
        for i in range(1, self.size):
            lat = i * self.base_distance / 111.0
            loc_type = 'camp' if i == self.size - 1 else 'town'
            locations.append({
                'name': f'Node_{i}',
                'type': loc_type,
                'lat': lat,
                'lon': 0.0,
                'pop': 0
            })
        
        # Routes: sequential chain
        routes = []
        for i in range(self.size - 1):
            from_name = 'Origin' if i == 0 else f'Node_{i}'
            to_name = f'Node_{i+1}'
            routes.append({'from': from_name, 'to': to_name, 'distance': self.base_distance})
        
        return locations, routes
    
    def generate_hierarchical(self):
        """Hierarchical: Origin → Hub → Branches → Camps (tree structure)."""
        locations = [{'name': 'Origin', 'type': 'conflict', 'lat': 0.0, 'lon': 0.0, 'pop': 5000}]
        
        # Hub
        locations.append({'name': 'Hub', 'type': 'town', 'lat': self.base_distance / 111.0, 'lon': 0.0, 'pop': 0})
        
        # Branches and camps
        num_branches = (self.size - 2) // 2
        for i in range(num_branches):
            angle = (i - num_branches/2) * 0.5
            lat = 2 * self.base_distance / 111.0
            lon = lat * np.tan(angle)
            
            # Branch
            locations.append({
                'name': f'Branch_{i}',
                'type': 'town',
                'lat': lat,
                'lon': lon,
                'pop': 0
            })
            
            # Camp at end of branch
            locations.append({
                'name': f'Camp_{i}',
                'type': 'camp',
                'lat': 3 * self.base_distance / 111.0,
                'lon': lon * 1.5,
                'pop': 0
            })
        
        # Routes: hierarchical tree
        routes = [
            {'from': 'Origin', 'to': 'Hub', 'distance': self.base_distance}
        ]
        
        for i in range(num_branches):
            routes.append({'from': 'Hub', 'to': f'Branch_{i}', 'distance': self.base_distance})
            routes.append({'from': f'Branch_{i}', 'to': f'Camp_{i}', 'distance': self.base_distance})
        
        return locations, routes
    
    def generate_regular_grid(self):
        """Regular grid: Origin at corner, regular spacing."""
        grid_size = int(np.sqrt(self.size))
        locations = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                if i * grid_size + j >= self.size:
                    break
                
                name = 'Origin' if (i == 0 and j == 0) else f'Node_{i}_{j}'
                loc_type = 'conflict' if (i == 0 and j == 0) else ('camp' if (i == grid_size-1 or j == grid_size-1) else 'town')
                pop = 5000 if (i == 0 and j == 0) else 0
                
                locations.append({
                    'name': name,
                    'type': loc_type,
                    'lat': i * self.base_distance / 111.0,
                    'lon': j * self.base_distance / 111.0,
                    'pop': pop
                })
        
        # Routes: grid connections (4-connected)
        routes = []
        for i in range(grid_size):
            for j in range(grid_size):
                if i * grid_size + j >= self.size:
                    break
                
                name = 'Origin' if (i == 0 and j == 0) else f'Node_{i}_{j}'
                
                # Connect right
                if j < grid_size - 1 and i * grid_size + j + 1 < self.size:
                    to_name = 'Origin' if (i == 0 and j + 1 == 0) else f'Node_{i}_{j+1}'
                    routes.append({'from': name, 'to': to_name, 'distance': self.base_distance})
                
                # Connect down
                if i < grid_size - 1 and (i + 1) * grid_size + j < self.size:
                    to_name = f'Node_{i+1}_{j}'
                    routes.append({'from': name, 'to': to_name, 'distance': self.base_distance})
        
        return locations, routes
    
    def generate_irregular_grid(self):
        """Irregular grid: Varying distances and connections."""
        grid_size = int(np.sqrt(self.size))
        locations = []
        
        # Add some randomness to positions
        np.random.seed(42)  # Reproducible
        
        for i in range(grid_size):
            for j in range(grid_size):
                if i * grid_size + j >= self.size:
                    break
                
                # Add irregular spacing
                lat_offset = np.random.uniform(-0.3, 0.3) * self.base_distance / 111.0 if not (i == 0 and j == 0) else 0
                lon_offset = np.random.uniform(-0.3, 0.3) * self.base_distance / 111.0 if not (i == 0 and j == 0) else 0
                
                name = 'Origin' if (i == 0 and j == 0) else f'Node_{i}_{j}'
                loc_type = 'conflict' if (i == 0 and j == 0) else ('camp' if (i == grid_size-1 or j == grid_size-1) else 'town')
                pop = 5000 if (i == 0 and j == 0) else 0
                
                locations.append({
                    'name': name,
                    'type': loc_type,
                    'lat': i * self.base_distance / 111.0 + lat_offset,
                    'lon': j * self.base_distance / 111.0 + lon_offset,
                    'pop': pop
                })
        
        # Routes: irregular connections with varying distances
        routes = []
        for i in range(grid_size):
            for j in range(grid_size):
                if i * grid_size + j >= self.size:
                    break
                
                name = 'Origin' if (i == 0 and j == 0) else f'Node_{i}_{j}'
                loc_idx = i * grid_size + j
                
                # Connect right
                if j < grid_size - 1 and i * grid_size + j + 1 < self.size:
                    to_name = 'Origin' if (i == 0 and j + 1 == 0) else f'Node_{i}_{j+1}'
                    # Calculate actual distance
                    dist = np.sqrt((locations[loc_idx]['lat'] - locations[loc_idx+1]['lat'])**2 + 
                                 (locations[loc_idx]['lon'] - locations[loc_idx+1]['lon'])**2) * 111.0
                    routes.append({'from': name, 'to': to_name, 'distance': dist})
                
                # Connect down
                if i < grid_size - 1 and (i + 1) * grid_size + j < self.size:
                    to_idx = (i + 1) * grid_size + j
                    if to_idx < len(locations):
                        to_name = f'Node_{i+1}_{j}'
                        dist = np.sqrt((locations[loc_idx]['lat'] - locations[to_idx]['lat'])**2 + 
                                     (locations[loc_idx]['lon'] - locations[to_idx]['lon'])**2) * 111.0
                        routes.append({'from': name, 'to': to_name, 'distance': dist})
        
        return locations, routes


def create_experiment_files(topology_name, s2_scenario, topology_data, exp_dir):
    """Create all necessary Flee input files."""
    
    locations, routes = topology_data
    
    # Create directories
    input_csv_dir = exp_dir / "input_csv"
    source_data_dir = exp_dir / "source_data"
    input_csv_dir.mkdir(parents=True, exist_ok=True)
    source_data_dir.mkdir(parents=True, exist_ok=True)
    
    # S2 threshold mapping
    s2_thresholds = {
        'baseline': 0.0,      # No S2 switching
        'low_s2': 0.3,        # S2 activates easily
        'medium_s2': 0.5,     # Balanced
        'high_s2': 0.7        # S2 activates under high pressure
    }
    
    s2_threshold = s2_thresholds[s2_scenario]
    
    # 1. locations.csv
    with open(input_csv_dir / "locations.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#name', 'region', 'country', 'gps_x', 'gps_y', 'location_type', 'conflict_date', 'pop/cap'])
        for loc in locations:
            writer.writerow([
                loc['name'], 'region1', 'country1', loc['lat'], loc['lon'],
                loc['type'], 0, loc['pop']
            ])
    
    # 2. routes.csv
    with open(input_csv_dir / "routes.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#name1', 'name2', 'distance'])
        for route in routes:
            writer.writerow([route['from'], route['to'], route['distance']])
    
    # 3. conflicts.csv (conflict at origin starts day 2)
    conflict_locations = [loc['name'] for loc in locations if loc['type'] == 'conflict']
    with open(input_csv_dir / "conflicts.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#Day'] + conflict_locations)
        for day in range(21):
            conflict_values = [0.0, 0.0] + [1.0] * 19  # No conflict days 0-1, then high conflict
            writer.writerow([day] + [conflict_values[day]])
    
    # 4. closures.csv (empty)
    with open(input_csv_dir / "closures.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#closure_type', 'name1', 'name2', 'closure_start', 'closure_end'])
    
    # 5. simsetting.yml
    simsetting_content = f"""log_levels:
  agent: 1
  link: 1
  camp: 0
  conflict: 0
  init: 0
  granularity: location
spawn_rules:
  take_from_population: False
  insert_day0: True
move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 0.0
  camp_movechance: 0.001
  default_movechance: 0.3
  awareness_level: 1
  capacity_scaling: 1.0
  avoid_short_stints: False
  start_on_foot: False
  weight_power: 1.0
  movechance_pop_base: 5000.0
  movechance_pop_scale_factor: 0.5
  two_system_decision_making: {s2_threshold}
optimisations:
  hasten: 1
"""
    
    with open(exp_dir / "simsetting.yml", 'w') as f:
        f.write(simsetting_content)
    
    # 6. sim_period.csv
    with open(input_csv_dir / "sim_period.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['startdate', '2013-01-01'])
        writer.writerow(['length', '20'])
    
    # 7. data_layout.csv
    all_locations = [loc['name'] for loc in locations if loc['type'] in ['camp', 'conflict']]
    with open(source_data_dir / "data_layout.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Location', 'refugees.csv'])
        for loc in all_locations:
            writer.writerow([loc, 'refugees.csv'])
    
    # 8. refugees.csv
    with open(source_data_dir / "refugees.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date'] + all_locations)
        for day in range(21):
            date = f'2023-01-{day+1:02d}'
            writer.writerow([date] + [0] * len(all_locations))
    
    print(f"   ✅ Created input files for {topology_name}_{s2_scenario}")


def run_experiment(topology_name, s2_scenario, exp_dir, population=5000):
    """Run a single Flee experiment."""
    
    print(f"\n{'='*70}")
    print(f"🚀 Running: {topology_name}_{s2_scenario}")
    print(f"{'='*70}")
    
    try:
        # Load settings
        SimulationSettings.ReadFromYML(exp_dir / "simsetting.yml")
        
        # Create ecosystem
        e = flee.Ecosystem()
        
        # Create input geography
        ig = InputGeography.InputGeography()
        
        # Read input files
        flee.SimulationSettings.ConflictInputFile = str(exp_dir / "input_csv" / "conflicts.csv")
        ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
        ig.ReadLocationsFromCSV(str(exp_dir / "input_csv" / "locations.csv"))
        ig.ReadLinksFromCSV(str(exp_dir / "input_csv" / "routes.csv"))
        ig.ReadClosuresFromCSV(str(exp_dir / "input_csv" / "closures.csv"))
        
        # Store in ecosystem
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        
        # Create refugee data handler
        d = handle_refugee_data.RefugeeTable(
            csvformat="generic",
            data_directory=str(exp_dir / "source_data"),
            start_date="2013-01-01",
            data_layout="data_layout.csv"
        )
        
        # Find origin
        origin_location = None
        for loc_name, loc in lm.items():
            if "Origin" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            raise ValueError("No origin location found!")
        
        # Spawn agents at origin ONLY
        print(f"   👥 Spawning {population} agents at {origin_location.name}...")
        for i in range(population):
            agent_attributes = {
                'connections': 5,
                'education_level': 0.5 + (i % 5) * 0.1,
                'stress_tolerance': 0.6,
                's2_threshold': SimulationSettings.move_rules.get("TwoSystemDecisionMaking", 0.5),
                'cognitive_profile': 'balanced',
                'education': 0.5 + (i % 5) * 0.1
            }
            agent = flee.Person(origin_location, agent_attributes)
            e.agents.append(agent)
        
        print(f"   ✅ Spawned {len(e.agents)} agents at origin")
        
        # Run simulation
        simulation_days = 20
        print(f"   🏃 Running Flee simulation for {simulation_days} days...")
        
        s2_activations = []
        agent_locations = []
        
        for day in range(simulation_days):
            # Count S2 activations
            day_s2 = sum(1 for a in e.agents if hasattr(a, 'decision_history') and 
                        any(d.get('decision_type') == 'S2' for d in a.decision_history))
            s2_activations.append(day_s2)
            
            # Track locations
            loc_counts = {}
            for agent in e.agents:
                loc_name = agent.location.name if agent.location else 'Unknown'
                loc_counts[loc_name] = loc_counts.get(loc_name, 0) + 1
            agent_locations.append(loc_counts)
            
            # Evolve
            e.evolve()
            
            if day % 5 == 0:
                s2_rate = (day_s2 / len(e.agents)) * 100 if e.agents else 0
                print(f"      Day {day}: {len(e.agents)} agents, S2: {s2_rate:.1f}%")
        
        # Calculate metrics
        total_s2 = sum(s2_activations)
        s2_rate = (total_s2 / (len(e.agents) * simulation_days)) * 100 if e.agents else 0
        
        # Camp populations
        final_camps = {}
        for loc_name, loc in lm.items():
            if loc.location_type == "camp":
                final_camps[loc_name] = loc.numAgents
        
        # Network metrics
        num_locations = len(lm)
        num_routes = len(routes)
        avg_degree = (2 * num_routes) / num_locations if num_locations > 0 else 0
        
        results = {
            'topology': topology_name,
            's2_scenario': s2_scenario,
            'population': population,
            'days': simulation_days,
            's2_activation_rate': s2_rate,
            'total_s2_activations': total_s2,
            'final_camp_populations': final_camps,
            'num_locations': num_locations,
            'num_routes': num_routes,
            'avg_degree': avg_degree,
            's2_activations_over_time': s2_activations,
            'agent_locations_over_time': agent_locations,
            'status': 'SUCCESS'
        }
        
        # Save results
        with open(exp_dir / "experiment_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"   ✅ SUCCESS: S2 rate = {s2_rate:.1f}%")
        return results
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {
            'topology': topology_name,
            's2_scenario': s2_scenario,
            'status': 'FAILED',
            'error': str(e)
        }


def main():
    """Run all colleague meeting experiments."""
    
    print("=" * 70)
    print("🎓 COLLEAGUE MEETING EXPERIMENTS")
    print("=" * 70)
    print()
    print("CRITICAL: Running ACTUAL Flee simulations (NO synthetic data)")
    print()
    print("Configuration:")
    print("  • Topologies: star, linear, hierarchical, regular_grid, irregular_grid")
    print("  • S2 Scenarios: baseline, low_s2, medium_s2, high_s2")
    print("  • Population: 5,000 agents per experiment")
    print("  • Duration: 20 days")
    print("  • Total: 20 experiments (5 topologies × 4 scenarios)")
    print()
    print("=" * 70)
    print()
    
    # Generate topologies
    topo_gen = TopologyGenerator(size=8)
    topologies = {
        'star': topo_gen.generate_star(),
        'linear': topo_gen.generate_linear(),
        'hierarchical': topo_gen.generate_hierarchical(),
        'regular_grid': topo_gen.generate_regular_grid(),
        'irregular_grid': topo_gen.generate_irregular_grid()
    }
    
    s2_scenarios = ['baseline', 'low_s2', 'medium_s2', 'high_s2']
    
    # Create experiment directories and files
    experiments_dir = Path("colleague_meeting_experiments")
    experiments_dir.mkdir(exist_ok=True)
    
    print("📁 Creating experiment files...")
    for topo_name, topo_data in topologies.items():
        for s2_scenario in s2_scenarios:
            exp_name = f"{topo_name}_{s2_scenario}"
            exp_dir = experiments_dir / exp_name
            exp_dir.mkdir(exist_ok=True)
            create_experiment_files(topo_name, s2_scenario, topo_data, exp_dir)
    
    print()
    print("✅ All experiment files created")
    print()
    
    # Run experiments
    all_results = []
    
    for topo_name in topologies.keys():
        for s2_scenario in s2_scenarios:
            exp_name = f"{topo_name}_{s2_scenario}"
            exp_dir = experiments_dir / exp_name
            
            result = run_experiment(topo_name, s2_scenario, exp_dir, population=5000)
            all_results.append(result)
    
    # Save summary
    summary_file = Path("results/data/colleague_meeting_results.json")
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': time_module.strftime('%Y-%m-%d %H:%M:%S'),
            'total_experiments': len(all_results),
            'successful': len([r for r in all_results if r['status'] == 'SUCCESS']),
            'failed': len([r for r in all_results if r['status'] == 'FAILED']),
            'experiments': all_results
        }, f, indent=2)
    
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total experiments: {len(all_results)}")
    print(f"Successful: {len([r for r in all_results if r['status'] == 'SUCCESS'])}")
    print(f"Failed: {len([r for r in all_results if r['status'] == 'FAILED'])}")
    print()
    print(f"Results saved to: {summary_file}")
    print()


if __name__ == "__main__":
    main()

