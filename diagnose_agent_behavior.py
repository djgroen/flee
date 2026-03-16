#!/usr/bin/env python3
"""
Diagnostic script to understand why agents are staying in towns instead of moving to safe zones.
"""

import json
import sys
from pathlib import Path

def analyze_agent_logs(log_file, num_agents_to_check=20):
    """Analyze agent logs to see where agents are and why they're not moving to camps."""
    
    print(f"🔍 Analyzing agent logs: {log_file}")
    print("="*70)
    
    if not Path(log_file).exists():
        print(f"❌ File not found: {log_file}")
        return
    
    # Read agent log (format: timestep, agent_id, location, x, y, ...)
    agent_positions = {}  # agent_id -> list of (timestep, location, x, y)
    agent_locations_by_time = {}  # timestep -> {location: count}
    
    with open(log_file, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 4:
                continue
            
            try:
                timestep = int(parts[0])
                agent_id = parts[1]
                location = parts[2]
                x = float(parts[3])
                y = float(parts[4])
                
                if agent_id not in agent_positions:
                    agent_positions[agent_id] = []
                agent_positions[agent_id].append((timestep, location, x, y))
                
                if timestep not in agent_locations_by_time:
                    agent_locations_by_time[timestep] = {}
                agent_locations_by_time[timestep][location] = agent_locations_by_time[timestep].get(location, 0) + 1
            except (ValueError, IndexError):
                continue
    
    # Analyze final positions
    final_timestep = max(agent_locations_by_time.keys()) if agent_locations_by_time else 0
    print(f"\n📊 Final Timestep: {final_timestep}")
    
    if final_timestep in agent_locations_by_time:
        print(f"\n📍 Final Location Distribution (t={final_timestep}):")
        locations = agent_locations_by_time[final_timestep]
        total = sum(locations.values())
        
        # Categorize by type
        camps = {}
        towns = {}
        conflict = {}
        
        for loc, count in sorted(locations.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            if 'SafeZone' in loc or 'camp' in loc.lower():
                camps[loc] = count
            elif 'Facility' in loc or 'conflict' in loc.lower():
                conflict[loc] = count
            else:
                towns[loc] = count
            
            print(f"  {loc:30s}: {count:4d} agents ({pct:5.1f}%)")
        
        print(f"\n📈 Summary by Type:")
        print(f"  Camps:     {sum(camps.values()):4d} agents ({sum(camps.values())/total*100:5.1f}%)")
        print(f"  Towns:     {sum(towns.values()):4d} agents ({sum(towns.values())/total*100:5.1f}%)")
        print(f"  Conflict:  {sum(conflict.values()):4d} agents ({sum(conflict.values())/total*100:5.1f}%)")
    
    # Track a few agents' trajectories
    print(f"\n🛤️  Sample Agent Trajectories (first {num_agents_to_check} agents):")
    sample_agents = list(agent_positions.keys())[:num_agents_to_check]
    
    for agent_id in sample_agents:
        trajectory = agent_positions[agent_id]
        if len(trajectory) > 0:
            start = trajectory[0]
            end = trajectory[-1]
            locations_visited = [loc for _, loc, _, _ in trajectory]
            unique_locations = len(set(locations_visited))
            
            print(f"\n  Agent {agent_id}:")
            print(f"    Start (t={start[0]}): {start[1]}")
            print(f"    End   (t={end[0]}): {end[1]}")
            print(f"    Unique locations visited: {unique_locations}")
            if unique_locations > 1:
                print(f"    Path: {' → '.join(locations_visited[:10])}{'...' if len(locations_visited) > 10 else ''}")
            
            # Check if agent reached a camp
            if 'SafeZone' in end[1] or 'camp' in end[1].lower():
                print(f"    ✅ Reached safe zone!")
            elif 'Facility' in end[1] or 'conflict' in end[1].lower():
                print(f"    ⚠️  Still in conflict zone!")
            else:
                print(f"    ⚠️  Stuck in intermediate location (town)")

def analyze_simulation_results(results_file):
    """Analyze simulation results JSON to check routes and locations."""
    
    print(f"\n🔍 Analyzing simulation results: {results_file}")
    print("="*70)
    
    if not Path(results_file).exists():
        print(f"❌ File not found: {results_file}")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    for result in results:
        topology = result['topology']
        print(f"\n📐 {topology} Topology:")
        
        # Check routes
        routes = result.get('routes', [])
        print(f"\n  Routes ({len(routes)} total):")
        
        routes_to_camps = []
        routes_from_towns = []
        
        for route in routes:
            from_loc = route['from']
            to_loc = route['to']
            
            if 'SafeZone' in to_loc or 'camp' in to_loc.lower():
                routes_to_camps.append(route)
            if 'Route' in from_loc or 'town' in from_loc.lower() or 'Location' in from_loc:
                routes_from_towns.append(route)
        
        print(f"    Routes TO camps: {len(routes_to_camps)}")
        for r in routes_to_camps[:5]:  # Show first 5
            print(f"      {r['from']} → {r['to']} (distance: {r['distance']:.1f})")
        if len(routes_to_camps) > 5:
            print(f"      ... and {len(routes_to_camps)-5} more")
        
        print(f"    Routes FROM towns: {len(routes_from_towns)}")
        
        # Check locations
        locations = result.get('locations', [])
        print(f"\n  Locations ({len(locations)} total):")
        
        camps = [loc for loc in locations if loc.get('type') == 'camp' or 'SafeZone' in loc.get('name', '')]
        towns = [loc for loc in locations if loc.get('type') == 'town' or 'Route' in loc.get('name', '') or 'Location' in loc.get('name', '')]
        conflict = [loc for loc in locations if loc.get('type') == 'conflict' or 'Facility' in loc.get('name', '')]
        
        print(f"    Camps:    {len(camps)}")
        print(f"    Towns:    {len(towns)}")
        print(f"    Conflict: {len(conflict)}")
        
        # Check final population
        pop_by_type = result.get('population_by_type_time', [])
        if pop_by_type:
            final_pop = pop_by_type[-1]
            print(f"\n  Final Population Distribution:")
            print(f"    Camps:    {final_pop.get('camp', 0):4d} agents")
            print(f"    Towns:    {final_pop.get('town', 0):4d} agents")
            print(f"    Conflict: {final_pop.get('conflict', 0):4d} agents")

if __name__ == '__main__':
    results_dir = Path('nuclear_evacuation_results')
    
    # Find latest results
    result_files = sorted(results_dir.glob('nuclear_evacuation_detailed_*.json'))
    if result_files:
        latest_results = result_files[-1]
        analyze_simulation_results(latest_results)
    
    # Find agent logs
    agent_logs = {
        'ring': results_dir / 'agents_ring.out',
        'star': results_dir / 'agents_star.out',
        'linear': results_dir / 'agents_linear.out'
    }
    
    for topology, log_file in agent_logs.items():
        if log_file.exists():
            print("\n" + "="*70)
            analyze_agent_logs(log_file, num_agents_to_check=10)
        else:
            print(f"\n⚠️  Agent log not found: {log_file}")


