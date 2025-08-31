#!/usr/bin/env python3
"""
Minimal Flee Scenario Test

Creates and runs the simplest possible Flee scenario to test basic execution.
"""

import sys
import os
from pathlib import Path

def initialize_simulation_settings():
    """Initialize SimulationSettings with minimal required parameters."""
    print("🔧 Initializing SimulationSettings...")
    
    try:
        from flee.SimulationSettings import SimulationSettings
        
        # Set minimal required parameters that Flee expects
        SimulationSettings.move_rules = {
            # Basic movement parameters
            "MaxMoveSpeed": 360.0,
            "MaxWalkSpeed": 35.0,
            "MaxCrossingSpeed": 20.0,
            
            # Weight parameters
            "ForeignWeight": 1.0,
            "CampWeight": 1.0,
            "ConflictWeight": 0.25,
            
            # Move chance parameters
            "ConflictMoveChance": 1.0,
            "CampMoveChance": 0.001,
            "IDPCampMoveChance": 0.1,
            "DefaultMoveChance": 0.3,
            
            # Other required parameters
            "AwarenessLevel": 1,
            "CapacityBuffer": 0.9,
            "CapacityScaling": 1.0,
            "AvoidShortStints": False,
            "StartOnFoot": False,
            "DistanceSoftening": 10.0,
            "WeightSoftening": 0.0,
            "WeightPower": 1.0,
            "DistancePower": 1.0,
            "StayCloseToHome": False,
            "HomeDistancePower": 0.5,
            "UsePopForLocWeight": False,
            "PopPowerForLocWeight": 0.1,
            "MovechancePopBase": 10000.0,
            "MovechancePopScaleFactor": 0.0,
            "PruningThreshold": 1.0,
            "FixedRoutes": False,
            "FloodRulesEnabled": False,
            
            # Cognitive parameters (our additions)
            "TwoSystemDecisionMaking": False,
            "conflict_threshold": 0.5,
            "average_social_connectivity": 0.1
        }
        
        # Set other required settings
        SimulationSettings.log_levels = {
            "agent": 0,
            "link": 0,
            "camp": 0,
            "init": 0,
            "conflict": 0,
            "idp_totals": 0,
            "granularity": "location"
        }
        
        SimulationSettings.spawn_rules = {
            "TakeFromPopulation": False,
            "InsertDayZeroRefugeesInCamps": True,
            "EmptyCampsOnDay0": False,
            "conflict_zone_spawning_only": True,
            "flood_zone_spawning_only": False,
            "camps_are_sinks": False,
            "read_from_agents_csv_file": False,
            "sum_from_camps": True,
            "conflict_driven_spawning": False,
            "flood_driven_spawning": False,
            "AverageSocialConnectivity": 3.0,
            "conflict_spawn_decay": None,
            "conflict_spawn_decay_interval": 30
        }
        
        SimulationSettings.optimisations = {
            "PopulationScaleDownFactor": 1
        }
        
        SimulationSettings.UseV1Rules = False
        SimulationSettings.farming = False
        
        print("✅ SimulationSettings initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize SimulationSettings: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_flee_objects():
    """Test creating basic Flee objects with proper settings."""
    print("\n🔍 Testing basic Flee object creation...")
    
    try:
        from flee.flee import Person, Location, Link
        
        # Create locations
        origin = Location("Origin", x=0, y=0, capacity=1000, location_type="conflict_zone")
        print(f"✅ Created origin: {origin.name}")
        print(f"   - Conflict: {origin.conflict}")
        print(f"   - Move chance: {origin.movechance}")
        
        camp = Location("Camp", x=100, y=0, capacity=500, location_type="camp")
        print(f"✅ Created camp: {camp.name}")
        print(f"   - Camp flag: {camp.camp}")
        print(f"   - Move chance: {camp.movechance}")
        
        # Create link
        link = Link(origin, camp, distance=100, forced_redirection=False)
        print(f"✅ Created link: {link.startpoint.name} -> {link.endpoint.name}")
        print(f"   - Distance: {link.distance}km")
        
        # Create agents
        agents = []
        for i in range(5):
            agent = Person(origin)
            agents.append(agent)
        
        print(f"✅ Created {len(agents)} agents")
        print(f"   - Origin population: {origin.numAgents}")
        
        # Test agent attributes
        agent = agents[0]
        print(f"   - Agent location: {agent.location.name}")
        print(f"   - Agent travelling: {agent.travelling}")
        
        # Check for cognitive attributes
        if hasattr(agent, 'cognitive_state'):
            print(f"   - Cognitive state: {agent.cognitive_state}")
        else:
            print("   - No cognitive attributes yet")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic object creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_minimal_simulation_step():
    """Test running a single simulation step."""
    print("\n🔍 Testing minimal simulation step...")
    
    try:
        from flee.flee import Person, Location, Link
        
        # Create simple scenario
        origin = Location("Origin", x=0, y=0, capacity=1000, location_type="conflict_zone")
        camp = Location("Camp", x=100, y=0, capacity=500, location_type="camp")
        link = Link(origin, camp, distance=100, forced_redirection=False)
        
        # Create agents
        agents = []
        for i in range(3):
            agent = Person(origin)
            agents.append(agent)
        
        print(f"Initial state:")
        print(f"   - Origin population: {origin.numAgents}")
        print(f"   - Camp population: {camp.numAgents}")
        
        # Try to evolve agents for one time step
        time = 0
        moved_agents = 0
        
        for agent in agents:
            initial_location = agent.location.name
            
            # Call evolve method (this is the main simulation step)
            agent.evolve(None, time=time)  # e parameter can be None for basic test
            
            if agent.location.name != initial_location:
                moved_agents += 1
                print(f"   - Agent moved from {initial_location} to {agent.location.name}")
        
        print(f"After simulation step:")
        print(f"   - Origin population: {origin.numAgents}")
        print(f"   - Camp population: {camp.numAgents}")
        print(f"   - Agents that moved: {moved_agents}")
        
        if moved_agents > 0:
            print("✅ Agent movement detected!")
        else:
            print("⚠️  No agent movement (this might be normal with low move chances)")
        
        return True
        
    except Exception as e:
        print(f"❌ Simulation step failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_minimal_scenario_files():
    """Create minimal scenario files for testing."""
    print("\n🔧 Creating minimal scenario files...")
    
    try:
        # Create test scenario directory
        scenario_dir = Path("test_minimal_scenario")
        scenario_dir.mkdir(exist_ok=True)
        
        # Create locations.csv
        locations_csv = scenario_dir / "locations.csv"
        with open(locations_csv, 'w') as f:
            f.write("#name,region,country,lat,lon,location_type,conflict_date,pop/cap\n")
            f.write("Origin,TestRegion,TestCountry,0.0,0.0,conflict_zone,,1000\n")
            f.write("Camp,TestRegion,TestCountry,1.0,0.0,camp,,500\n")
        
        print(f"✅ Created {locations_csv}")
        
        # Create routes.csv
        routes_csv = scenario_dir / "routes.csv"
        with open(routes_csv, 'w') as f:
            f.write("#name1,name2,distance,forced_redirection\n")
            f.write("Origin,Camp,100,0\n")
        
        print(f"✅ Created {routes_csv}")
        
        # Create conflicts.csv
        conflicts_csv = scenario_dir / "conflicts.csv"
        with open(conflicts_csv, 'w') as f:
            f.write("#Day,Origin,Camp\n")
            f.write("0,1.0,0.0\n")
            f.write("1,1.0,0.0\n")
            f.write("2,0.8,0.0\n")
            f.write("3,0.6,0.0\n")
            f.write("4,0.4,0.0\n")
        
        print(f"✅ Created {conflicts_csv}")
        
        # Create simsetting.yml (minimal)
        simsetting_yml = scenario_dir / "simsetting.yml"
        with open(simsetting_yml, 'w') as f:
            f.write("""# Minimal Flee simulation settings
log_levels:
  agent: 0
  link: 0
  camp: 0
  conflict: 0
  init: 1
  granularity: location

spawn_rules:
  take_from_population: false
  insert_day0: true

move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 1.0
  camp_movechance: 0.001
  default_movechance: 0.3
  awareness_level: 1
  capacity_scaling: 1.0
  avoid_short_stints: false
  start_on_foot: false
  weight_softening: 0.0
  
  # Cognitive parameters
  two_system_decision_making: false
  conflict_threshold: 0.5

optimisations:
  hasten: 1
""")
        
        print(f"✅ Created {simsetting_yml}")
        
        return str(scenario_dir)
        
    except Exception as e:
        print(f"❌ Failed to create scenario files: {e}")
        return None

def main():
    """Run minimal Flee scenario tests."""
    print("=" * 60)
    print("MINIMAL FLEE SCENARIO TEST")
    print("=" * 60)
    
    tests = [
        ("Initialize Settings", initialize_simulation_settings),
        ("Basic Objects", test_basic_flee_objects),
        ("Simulation Step", test_minimal_simulation_step),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Create scenario files
    scenario_dir = create_minimal_scenario_files()
    if scenario_dir:
        print(f"\n📁 Created minimal scenario in: {scenario_dir}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Minimal Flee scenario works!")
        print("\n📋 Next Steps:")
        print("   1. Test running actual Flee simulation with scenario files")
        print("   2. Add cognitive parameters to SimulationSettings")
        print("   3. Implement cognitive decision logic in Person class")
        return True
    else:
        print("⚠️  Some basic functionality is still broken.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)