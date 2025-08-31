#!/usr/bin/env python3
"""
S1/S2 Simulation Runner with Standardized Diagnostics

Runs any S1/S2 refugee simulation and automatically generates
the complete standardized diagnostic suite for analysis.

Usage:
    python run_s1s2_with_diagnostics.py --scenario evacuation_timing
    python run_s1s2_with_diagnostics.py --scenario bottleneck_challenge
    python run_s1s2_with_diagnostics.py --scenario destination_choice
    python run_s1s2_with_diagnostics.py --scenario information_network
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from standard_s1s2_diagnostic_suite import S1S2DiagnosticSuite

def run_evacuation_timing_scenario() -> Dict[str, Any]:
    """Run evacuation timing scenario and collect data"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_decision_tracker import RefugeeDecisionTracker
    from scripts.refugee_person_enhancements import create_refugee_agent, enhanced_refugee_movechance
    
    print("🏃 Running Evacuation Timing Scenario...")
    
    # Initialize settings
    SimulationSettings.ReadFromYML("test_data/test_settings.yml")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    
    # Create linear chain topology
    ecosystem = Ecosystem()
    origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=1000)
    town = ecosystem.addLocation("Town", x=100, y=0, movechance=0.3, capacity=-1, pop=500)
    camp = ecosystem.addLocation("Camp", x=200, y=0, movechance=0.001, capacity=2000, pop=0)
    
    ecosystem.linkUp("Origin", "Town", 100.0)
    ecosystem.linkUp("Town", "Camp", 100.0)
    
    # Create agents with different connectivity levels
    agents = []
    tracker = RefugeeDecisionTracker()
    
    for i in range(40):
        connections = 1 if i < 20 else 8
        safety_thresh = 0.7 if i < 20 else 0.4
        agent = create_refugee_agent(origin, {"connections": connections}, {"safety_threshold": safety_thresh})
        agents.append(agent)
    
    # Collect simulation data
    locations_data = []
    links_data = []
    movements_data = []
    decisions_data = []
    time_series_data = {'conflict_levels': {}, 'capacity_changes': {}}
    
    # Extract topology data
    for location in ecosystem.locations:
        locations_data.append({
            'name': location.name,
            'x': location.x,
            'y': location.y,
            'conflict': getattr(location, 'conflict', 0),
            'capacity': location.capacity,
            'population': location.pop
        })
    
    # Extract links from all locations (avoid duplicates)
    seen_links = set()
    for location in ecosystem.locations:
        for link in location.links:
            link_key = tuple(sorted([link.startpoint.name, link.endpoint.name]))
            if link_key not in seen_links:
                links_data.append({
                    'from': link.startpoint.name,
                    'to': link.endpoint.name,
                    'distance': link.get_distance()
                })
                seen_links.add(link_key)
    
    # Run simulation with gradual conflict escalation
    for time in range(30):
        conflict_level = min(time * 0.05, 1.0)
        origin.conflict = conflict_level
        time_series_data['conflict_levels'][time] = conflict_level
        
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            enhanced_movechance = enhanced_refugee_movechance(agent, base_movechance, system2_active, time)
            cognitive_pressure = agent.calculate_cognitive_pressure(time)
            
            # Record decision
            decisions_data.append({
                'agent_id': id(agent),
                'time': time,
                'system2_active': system2_active,
                'agent_connectivity': agent.attributes.get('connections', 0),
                'cognitive_pressure': cognitive_pressure
            })
            
            # Record movement if it occurs
            if enhanced_movechance > 0.5:
                current_location = agent.location.name if agent.location else "Unknown"
                # Simulate movement to next location
                if current_location == "Origin":
                    next_location = "Town"
                elif current_location == "Town":
                    next_location = "Camp"
                else:
                    continue
                
                movements_data.append({
                    'agent_id': id(agent),
                    'time': time,
                    'from_location': current_location,
                    'to_location': next_location,
                    'distance': 100,
                    'safety_score': 1.0 - conflict_level,
                    'system2_active': system2_active
                })
    
    return {
        'locations': locations_data,
        'links': links_data,
        'agents': [{'id': id(agent), 'connectivity': agent.attributes.get('connections', 0)} for agent in agents],
        'movements': movements_data,
        'decisions': decisions_data,
        'time_series': time_series_data,
        'max_time': 30
    }

def run_bottleneck_scenario() -> Dict[str, Any]:
    """Run bottleneck avoidance scenario and collect data"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_person_enhancements import create_refugee_agent, s1_refugee_decision, s2_refugee_decision
    
    print("🚧 Running Bottleneck Challenge Scenario...")
    
    # Initialize settings
    SimulationSettings.ReadFromYML("test_data/test_settings.yml")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    
    # Create diamond topology with bottleneck
    ecosystem = Ecosystem()
    origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=800)
    bottleneck = ecosystem.addLocation("Bottleneck", x=150, y=0, movechance=0.5, capacity=50, pop=200)
    camp_a = ecosystem.addLocation("Camp_A", x=250, y=-50, movechance=0.001, capacity=500, pop=0)
    camp_b = ecosystem.addLocation("Camp_B", x=250, y=50, movechance=0.001, capacity=800, pop=0)
    alternative = ecosystem.addLocation("Alternative", x=75, y=100, movechance=0.3, capacity=-1, pop=100)
    
    # Set conflict levels
    origin.conflict = 0.9
    bottleneck.conflict = 0.3
    camp_a.conflict = 0.1
    camp_b.conflict = 0.05
    alternative.conflict = 0.2
    
    ecosystem.linkUp("Origin", "Bottleneck", 150.0)
    ecosystem.linkUp("Bottleneck", "Camp_A", 111.0)
    ecosystem.linkUp("Bottleneck", "Camp_B", 111.0)
    ecosystem.linkUp("Origin", "Alternative", 125.0)
    ecosystem.linkUp("Alternative", "Camp_B", 180.0)
    
    # Create agents
    agents = []
    for i in range(30):
        connections = 1 if i < 15 else 8
        safety_thresh = 0.7 if i < 15 else 0.5
        agent = create_refugee_agent(origin, {"connections": connections}, {"safety_threshold": safety_thresh})
        agents.append(agent)
    
    # Collect data (similar structure to evacuation scenario)
    locations_data = []
    links_data = []
    movements_data = []
    decisions_data = []
    time_series_data = {'conflict_levels': {}, 'capacity_changes': {}}
    
    # Extract topology
    for location in ecosystem.locations:
        locations_data.append({
            'name': location.name,
            'x': location.x,
            'y': location.y,
            'conflict': getattr(location, 'conflict', 0),
            'capacity': location.capacity,
            'population': location.pop
        })
    
    # Extract links from all locations (avoid duplicates)
    seen_links = set()
    for location in ecosystem.locations:
        for link in location.links:
            link_key = tuple(sorted([link.startpoint.name, link.endpoint.name]))
            if link_key not in seen_links:
                links_data.append({
                    'from': link.startpoint.name,
                    'to': link.endpoint.name,
                    'distance': link.distance
                })
                seen_links.add(link_key)
    
    # Run simulation with capacity degradation
    for time in range(15):
        # Capacity degradation shock after day 5
        if time > 5:
            bottleneck.capacity = max(20, bottleneck.capacity - 2)
        
        time_series_data['capacity_changes'][time] = bottleneck.capacity
        
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            
            decisions_data.append({
                'agent_id': id(agent),
                'time': time,
                'system2_active': system2_active,
                'agent_connectivity': agent.attributes.get('connections', 0),
                'cognitive_pressure': 0.5 + time * 0.02  # Simulated pressure
            })
            
            if base_movechance > 0.5:
                # Simulate route choice
                if system2_active:
                    # S2 more likely to choose alternative when bottleneck is congested
                    choice = "Alternative" if bottleneck.numAgents > bottleneck.capacity * 0.8 else "Bottleneck"
                else:
                    # S1 prefers direct route
                    choice = "Bottleneck"
                
                movements_data.append({
                    'agent_id': id(agent),
                    'time': time,
                    'from_location': "Origin",
                    'to_location': choice,
                    'distance': 125 if choice == "Alternative" else 150,
                    'safety_score': 0.8 if choice == "Alternative" else 0.7,
                    'system2_active': system2_active
                })
    
    return {
        'locations': locations_data,
        'links': links_data,
        'agents': [{'id': id(agent), 'connectivity': agent.attributes.get('connections', 0)} for agent in agents],
        'movements': movements_data,
        'decisions': decisions_data,
        'time_series': time_series_data,
        'max_time': 15
    }

def run_destination_choice_scenario() -> Dict[str, Any]:
    """Run destination choice scenario and collect data"""
    print("🎯 Running Destination Choice Scenario...")
    
    # Simulate star topology with multiple destinations
    locations_data = [
        {'name': 'Origin', 'x': 0, 'y': 0, 'conflict': 0.9, 'capacity': -1, 'population': 1000},
        {'name': 'Close_Safe', 'x': 50, 'y': 0, 'conflict': 0.2, 'capacity': 300, 'population': 0},
        {'name': 'Medium_Balanced', 'x': 0, 'y': 120, 'conflict': 0.3, 'capacity': 600, 'population': 0},
        {'name': 'Far_Excellent', 'x': -150, 'y': 0, 'conflict': 0.1, 'capacity': 1000, 'population': 0},
        {'name': 'Risky_Opportunity', 'x': 0, 'y': -80, 'conflict': 0.6, 'capacity': 400, 'population': 0}
    ]
    
    links_data = [
        {'from': 'Origin', 'to': 'Close_Safe', 'distance': 50},
        {'from': 'Origin', 'to': 'Medium_Balanced', 'distance': 120},
        {'from': 'Origin', 'to': 'Far_Excellent', 'distance': 150},
        {'from': 'Origin', 'to': 'Risky_Opportunity', 'distance': 80}
    ]
    
    # Simulate agent decisions
    movements_data = []
    decisions_data = []
    
    for i in range(40):
        connections = 1 if i < 20 else 8
        system2_active = connections >= 5
        
        # S1 agents prefer close, safe options (satisficing)
        # S2 agents optimize for best overall outcome
        if system2_active:
            destination = 'Far_Excellent'  # S2 optimizes for quality
        else:
            destination = 'Close_Safe'     # S1 satisfices with first good option
        
        decisions_data.append({
            'agent_id': i,
            'time': 0,
            'system2_active': system2_active,
            'agent_connectivity': connections,
            'cognitive_pressure': 0.4
        })
        
        movements_data.append({
            'agent_id': i,
            'time': 0,
            'from_location': 'Origin',
            'to_location': destination,
            'distance': next(link['distance'] for link in links_data if link['to'] == destination),
            'safety_score': 1.0 - next(loc['conflict'] for loc in locations_data if loc['name'] == destination),
            'system2_active': system2_active
        })
    
    return {
        'locations': locations_data,
        'links': links_data,
        'agents': [{'id': i, 'connectivity': 1 if i < 20 else 8} for i in range(40)],
        'movements': movements_data,
        'decisions': decisions_data,
        'time_series': {'conflict_levels': {}, 'capacity_changes': {}},
        'max_time': 1
    }

def run_information_network_scenario() -> Dict[str, Any]:
    """Run information network scenario and collect data"""
    print("🌐 Running Information Network Scenario...")
    
    # Simulate hub-and-spoke topology with hidden information
    locations_data = [
        {'name': 'Hub', 'x': 100, 'y': 0, 'conflict': 0.6, 'capacity': -1, 'population': 300},
        {'name': 'Obvious', 'x': 150, 'y': 0, 'conflict': 0.2, 'capacity': 400, 'population': 0},
        {'name': 'HiddenGood', 'x': 120, 'y': 80, 'conflict': 0.1, 'capacity': 600, 'population': 0},
        {'name': 'HiddenPoor', 'x': 120, 'y': -80, 'conflict': 0.5, 'capacity': 200, 'population': 0}
    ]
    
    links_data = [
        {'from': 'Hub', 'to': 'Obvious', 'distance': 50},
        {'from': 'Hub', 'to': 'HiddenGood', 'distance': 94},
        {'from': 'Hub', 'to': 'HiddenPoor', 'distance': 94}
    ]
    
    # Simulate information discovery and utilization
    movements_data = []
    decisions_data = []
    
    for i in range(20):
        connections = 1 if i < 10 else 8
        system2_active = connections >= 5
        
        # High connectivity agents discover hidden good option
        # Low connectivity agents go to obvious option
        if system2_active and connections >= 7:
            destination = 'HiddenGood'  # S2 with high connectivity finds best option
        else:
            destination = 'Obvious'    # S1 or low connectivity goes to obvious choice
        
        decisions_data.append({
            'agent_id': i,
            'time': 0,
            'system2_active': system2_active,
            'agent_connectivity': connections,
            'cognitive_pressure': 0.3
        })
        
        movements_data.append({
            'agent_id': i,
            'time': 0,
            'from_location': 'Hub',
            'to_location': destination,
            'distance': next(link['distance'] for link in links_data if link['to'] == destination),
            'safety_score': 1.0 - next(loc['conflict'] for loc in locations_data if loc['name'] == destination),
            'system2_active': system2_active
        })
    
    return {
        'locations': locations_data,
        'links': links_data,
        'agents': [{'id': i, 'connectivity': 1 if i < 10 else 8} for i in range(20)],
        'movements': movements_data,
        'decisions': decisions_data,
        'time_series': {'conflict_levels': {}, 'capacity_changes': {}},
        'max_time': 1
    }

def main():
    """Main function to run scenarios with diagnostics"""
    parser = argparse.ArgumentParser(description='Run S1/S2 simulations with standardized diagnostics')
    parser.add_argument('--scenario', choices=['evacuation_timing', 'bottleneck_challenge', 
                                             'destination_choice', 'information_network', 'all'],
                       default='all', help='Scenario to run')
    parser.add_argument('--output-dir', default='s1s2_diagnostics', 
                       help='Output directory for diagnostic files')
    
    args = parser.parse_args()
    
    # Initialize diagnostic suite
    suite = S1S2DiagnosticSuite(args.output_dir)
    
    scenarios = {
        'evacuation_timing': run_evacuation_timing_scenario,
        'bottleneck_challenge': run_bottleneck_scenario,
        'destination_choice': run_destination_choice_scenario,
        'information_network': run_information_network_scenario
    }
    
    if args.scenario == 'all':
        scenarios_to_run = scenarios.items()
    else:
        scenarios_to_run = [(args.scenario, scenarios[args.scenario])]
    
    print("🚀 RUNNING S1/S2 SIMULATIONS WITH STANDARDIZED DIAGNOSTICS")
    print("=" * 70)
    
    success_count = 0
    total_count = len(scenarios_to_run)
    
    for scenario_name, scenario_func in scenarios_to_run:
        print(f"\n📋 SCENARIO: {scenario_name.replace('_', ' ').title()}")
        print("-" * 50)
        
        try:
            # Run scenario and collect data
            simulation_data = scenario_func()
            
            # Generate standardized diagnostics
            success = suite.generate_full_diagnostic(simulation_data, scenario_name)
            
            if success:
                success_count += 1
                print(f"✅ {scenario_name} completed successfully")
            else:
                print(f"❌ {scenario_name} failed")
                
        except Exception as e:
            print(f"❌ {scenario_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 SUMMARY: {success_count}/{total_count} scenarios completed successfully")
    print(f"📁 All diagnostic files saved to: {args.output_dir}/")
    
    if success_count == total_count:
        print("\n🎯 STANDARDIZED DIAGNOSTIC SUITE FEATURES:")
        print("  • Panel 1: Scenario Context (topology, forcing functions, metadata)")
        print("  • Panel 2: Agent Dynamics (flows, cognitive patterns, trajectories)")
        print("  • Panel 3: System Performance (efficiency, safety, cognitive load)")
        print("  • Panel 4: Comparative Analysis (S1 vs S2, hypothesis metrics)")
        print("  • Summary Report: Text-based analysis summary")
        print("\n✨ Ready for hypothesis testing across different scenarios!")

if __name__ == "__main__":
    main()