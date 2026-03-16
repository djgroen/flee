#!/usr/bin/env python3
"""
Minimal FLEE test to isolate the CSV reading issue.
"""

import sys
import os
import pandas as pd
import yaml

# Add current directory to path
sys.path.insert(0, '.')

def test_minimal_flee():
    """Test minimal FLEE setup to isolate the issue."""
    
    print("🔍 Testing minimal FLEE setup...")
    
    # Create a minimal test directory
    test_dir = "minimal_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a minimal locations.csv file
    locations_data = [
        {"name": "Location_0", "region": "TestRegion", "country": "TestCountry", 
         "gps_x": 0.0, "gps_y": 0.0, "location_type": "conflict_zone", 
         "conflict_date": 0, "pop/cap": 10000},
        {"name": "Location_1", "region": "TestRegion", "country": "TestCountry", 
         "gps_x": 1.0, "gps_y": 1.0, "location_type": "camp", 
         "conflict_date": 0, "pop/cap": 0}
    ]
    
    locations_df = pd.DataFrame(locations_data)
    # Write CSV with comment header (FLEE expects header to start with #)
    with open(os.path.join(test_dir, "locations.csv"), 'w') as f:
        f.write("#name,region,country,gps_x,gps_y,location_type,conflict_date,pop/cap\n")
        locations_df.to_csv(f, index=False, header=False)
    
    # Create a minimal conflicts.csv file
    conflicts_data = [
        {"Day": 0, "Location_0": 1, "Location_1": 0},
        {"Day": 1, "Location_0": 1, "Location_1": 0},
        {"Day": 2, "Location_0": 0, "Location_1": 0}
    ]
    
    conflicts_df = pd.DataFrame(conflicts_data)
    conflicts_df.to_csv(os.path.join(test_dir, "conflicts.csv"), index=False)
    
    # Create a minimal routes.csv file
    routes_data = [
        {"name1": "Location_0", "name2": "Location_1", "distance": 1.0, 
         "forced_redirection": "0", "blocked": "0"}
    ]
    
    routes_df = pd.DataFrame(routes_data)
    # Write CSV with comment header (FLEE expects header to start with #)
    with open(os.path.join(test_dir, "routes.csv"), 'w') as f:
        f.write("#name1,name2,distance,forced_redirection,blocked\n")
        routes_df.to_csv(f, index=False, header=False)
    
    # Create a minimal closures.csv file (empty with comment header)
    with open(os.path.join(test_dir, "closures.csv"), 'w') as f:
        f.write("#name1,name2,closure_start,closure_end\n")
    
    # Create a minimal config file
    config = {
        'log_levels': {'agent': 0, 'link': 0, 'camp': 0, 'conflict': 0, 'init': 0, 'granularity': 'location'},
        'spawn_rules': {'take_from_population': False, 'insert_day0': True},
        'move_rules': {
            'max_move_speed': 360.0,
            'max_walk_speed': 35.0,
            'foreign_weight': 1.0,
            'camp_weight': 1.0,
            'conflict_weight': 0.25,
            'conflict_movechance': 0.0,
            'camp_movechance': 0.001,
            'default_movechance': 0.3,
            'awareness_level': 1,
            'capacity_scaling': 1.0,
            'avoid_short_stints': False,
            'start_on_foot': False,
            'weight_power': 1.0,
            'movechance_pop_base': 10000.0,
            'movechance_pop_scale_factor': 0.5,
            'two_system_decision_making': 0.5,
            'conflict_threshold': 0.5,
            'connectivity_mode': 'baseline',
            'soft_capability': False,
            'pmove_s2_mode': 'scaled',
            'eta': 0.5,
            'steepness': 6.0
        },
        'optimisations': {'hasten': 1}
    }
    
    config_file = os.path.join(test_dir, "config.yml")
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    print("✅ Created minimal test files")
    
    # Test FLEE step by step
    try:
        print("\n🔍 Testing FLEE step by step...")
        
        from flee import flee
        from flee import InputGeography
        
        print("1. Reading simulation settings...")
        flee.SimulationSettings.ReadFromYML(config_file)
        print("✅ Simulation settings read")
        
        print("2. Creating ecosystem...")
        e = flee.Ecosystem()
        print("✅ Ecosystem created")
        
        print("3. Creating input geography...")
        ig = InputGeography.InputGeography()
        print("✅ Input geography created")
        
        print("4. Reading conflicts CSV...")
        ig.ReadConflictInputCSV(os.path.join(test_dir, "conflicts.csv"))
        print("✅ Conflicts CSV read")
        
        print("5. Reading locations CSV...")
        ig.ReadLocationsFromCSV(os.path.join(test_dir, "locations.csv"))
        print("✅ Locations CSV read")
        
        print("6. Reading routes CSV...")
        ig.ReadLinksFromCSV(os.path.join(test_dir, "routes.csv"))
        print("✅ Routes CSV read")
        
        print("7. Reading closures CSV...")
        ig.ReadClosuresFromCSV(os.path.join(test_dir, "closures.csv"))
        print("✅ Closures CSV read")
        
        print("8. Storing input geography in ecosystem...")
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        print("✅ Input geography stored")
        
        print("9. Creating agents...")
        origin_location = None
        for loc_name, loc in lm.items():
            if "Location_0" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            print("❌ No origin location found!")
            return False
        
        print(f"✅ Found origin location: {origin_location.name}")
        
        # Create a few agents
        agents = []
        for i in range(5):  # Just 5 agents for testing
            attributes = {
                'connections': 2,
                'education_level': 0.5,
                'stress_tolerance': 0.5,
                's2_threshold': 0.5
            }
            agent = flee.Person(origin_location, attributes)
            agents.append(agent)
        
        e.agents = agents
        print(f"✅ Created {len(agents)} agents")
        
        print("10. Running simulation...")
        for t in range(3):  # Just 3 timesteps for testing
            e.time = t
            e.evolve()
            print(f"  Timestep {t} completed")
        
        print("✅ Simulation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in FLEE execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Don't clean up for debugging
        # import shutil
        # shutil.rmtree(test_dir, ignore_errors=True)
        pass

if __name__ == "__main__":
    success = test_minimal_flee()
    if success:
        print("\n🎉 Minimal FLEE test passed!")
    else:
        print("\n❌ Minimal FLEE test failed!")
