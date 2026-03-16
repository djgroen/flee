#!/usr/bin/env python3
"""
Comprehensive test of S1/S2 system functionality
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_s1s2_comprehensive():
    """Comprehensive test of S1/S2 system"""
    
    print("🧪 Comprehensive S1/S2 System Test")
    print("=" * 60)
    
    # Change to experiment directory
    exp_dir = Path("proper_10k_agent_experiments/star_n4_medium_s2_10k")
    original_dir = os.getcwd()
    os.chdir(exp_dir)
    
    try:
        # Import Flee components
        from flee import flee
        from flee.datamanager import handle_refugee_data, read_period
        from flee import InputGeography
        from flee.moving import calculateMoveChance, selectRoute, calculate_systematic_s2_activation
        
        # Read simulation settings
        flee.SimulationSettings.ReadFromYML("simsetting.yml")
        s2_threshold = flee.SimulationSettings.move_rules.get('TwoSystemDecisionMaking', 0.0)
        print(f"⚙️ S2 threshold: {s2_threshold}")
        print(f"🔧 TwoSystemDecisionMaking enabled: {bool(s2_threshold)}")
        
        # Create ecosystem
        e = flee.Ecosystem()
        
        # Create input geography
        ig = InputGeography.InputGeography()
        
        # Read input files
        flee.SimulationSettings.ConflictInputFile = "input_csv/conflicts.csv"
        ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
        ig.ReadLocationsFromCSV("input_csv/locations.csv")
        ig.ReadLinksFromCSV("input_csv/routes.csv")
        ig.ReadClosuresFromCSV("input_csv/closures.csv")
        
        # Store input geography in ecosystem
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        
        # Create test agents with different attributes
        origin_location = None
        for loc_name, loc in lm.items():
            if "Origin" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            print("❌ No origin location found!")
            return
        
        print(f"📍 Testing with origin location: {origin_location.name}")
        print(f"📍 Origin conflict intensity: {getattr(origin_location, 'conflict', 'N/A')}")
        
        # Test 1: S1 vs S2 move chance differences
        print(f"\n🔬 Test 1: S1 vs S2 Move Chance Differences")
        print("-" * 50)
        
        # Create agents with different cognitive profiles
        test_agents = [
            ("High Education", {'connections': 8, 'education_level': 0.9, 'stress_tolerance': 0.7, 's2_threshold': 0.5}),
            ("Low Education", {'connections': 2, 'education_level': 0.2, 'stress_tolerance': 0.3, 's2_threshold': 0.5}),
            ("High Stress Tolerance", {'connections': 5, 'education_level': 0.5, 'stress_tolerance': 0.9, 's2_threshold': 0.5}),
            ("Low Stress Tolerance", {'connections': 5, 'education_level': 0.5, 'stress_tolerance': 0.1, 's2_threshold': 0.5}),
        ]
        
        for agent_name, attributes in test_agents:
            agent = flee.Person(origin_location, attributes)
            
            print(f"\n👤 {agent_name}:")
            print(f"  - Connections: {agent.attributes.get('connections', 0)}")
            print(f"  - Education: {agent.attributes.get('education_level', 0.5)}")
            print(f"  - Stress tolerance: {agent.attributes.get('stress_tolerance', 0.5)}")
            
            # Test move chances at different times
            for time in [0, 10, 20]:
                movechance_s1, system2_active = calculateMoveChance(agent, False, time)
                cognitive_pressure = agent.calculate_cognitive_pressure(time)
                
                print(f"  Time {time}: Pressure={cognitive_pressure:.3f}, S2={system2_active}, MoveChance={movechance_s1:.3f}")
        
        # Test 2: Route selection differences
        print(f"\n🔬 Test 2: S1 vs S2 Route Selection Differences")
        print("-" * 50)
        
        # Create a test agent
        test_agent = flee.Person(origin_location, {
            'connections': 5,
            'education_level': 0.7,
            'stress_tolerance': 0.6,
            's2_threshold': 0.5
        })
        
        # Test route selection with S1 and S2
        time = 10
        cognitive_pressure = test_agent.calculate_cognitive_pressure(time)
        system2_active = calculate_systematic_s2_activation(
            test_agent, cognitive_pressure, test_agent.attributes.get('s2_threshold', 0.5), time
        )
        
        print(f"🧠 Cognitive pressure: {cognitive_pressure:.3f}")
        print(f"🧠 System 2 active: {system2_active}")
        
        # Test route selection
        try:
            route_s1 = selectRoute(test_agent, time=time, system2_active=False)
            route_s2 = selectRoute(test_agent, time=time, system2_active=True)
            
            print(f"🛣️ S1 Route: {route_s1}")
            print(f"🛣️ S2 Route: {route_s2}")
            
            # Check if routes are different
            if route_s1 != route_s2:
                print("✅ S1 and S2 routes are different - System working correctly!")
            else:
                print("⚠️ S1 and S2 routes are the same - may need investigation")
                
        except Exception as e:
            print(f"❌ Error in route selection: {e}")
        
        # Test 3: System 2 activation probability over time
        print(f"\n🔬 Test 3: System 2 Activation Probability Over Time")
        print("-" * 50)
        
        test_agent = flee.Person(origin_location, {
            'connections': 5,
            'education_level': 0.7,
            'stress_tolerance': 0.6,
            's2_threshold': 0.5
        })
        
        print("Time | Pressure | S2 Rate | Avg MoveChance")
        print("-" * 40)
        
        for time in range(0, 21, 5):
            activations = 0
            movechances = []
            
            for trial in range(100):
                movechance, system2_active = calculateMoveChance(test_agent, False, time)
                movechances.append(movechance)
                if system2_active:
                    activations += 1
            
            avg_movechance = sum(movechances) / len(movechances)
            s2_rate = activations / 100
            cognitive_pressure = test_agent.calculate_cognitive_pressure(time)
            
            print(f"{time:4d} | {cognitive_pressure:8.3f} | {s2_rate:7.1%} | {avg_movechance:13.3f}")
        
        # Test 4: Parameter differences between S1 and S2
        print(f"\n🔬 Test 4: Parameter Differences Between S1 and S2")
        print("-" * 50)
        
        # Store original parameters
        original_awareness = flee.SimulationSettings.move_rules["AwarenessLevel"]
        original_weight_softening = flee.SimulationSettings.move_rules["WeightSoftening"]
        original_distance_power = flee.SimulationSettings.move_rules["DistancePower"]
        original_pruning_threshold = flee.SimulationSettings.move_rules["PruningThreshold"]
        
        print(f"Original parameters:")
        print(f"  AwarenessLevel: {original_awareness}")
        print(f"  WeightSoftening: {original_weight_softening}")
        print(f"  DistancePower: {original_distance_power}")
        print(f"  PruningThreshold: {original_pruning_threshold}")
        
        # Test S2 parameter modification
        test_agent = flee.Person(origin_location, {
            'connections': 5,
            'education_level': 0.7,
            'stress_tolerance': 0.6,
            's2_threshold': 0.5
        })
        
        # Force S2 activation by setting high cognitive pressure
        test_agent.attributes['connections'] = 10  # High connectivity
        cognitive_pressure = test_agent.calculate_cognitive_pressure(20)
        
        print(f"\nHigh pressure scenario (pressure={cognitive_pressure:.3f}):")
        
        # Test route selection with S2 active
        route_s2 = selectRoute(test_agent, time=20, system2_active=True)
        
        print(f"S2 parameters after route selection:")
        print(f"  AwarenessLevel: {flee.SimulationSettings.move_rules['AwarenessLevel']}")
        print(f"  WeightSoftening: {flee.SimulationSettings.move_rules['WeightSoftening']}")
        print(f"  DistancePower: {flee.SimulationSettings.move_rules['DistancePower']}")
        print(f"  PruningThreshold: {flee.SimulationSettings.move_rules['PruningThreshold']}")
        
        # Check if parameters were restored
        params_restored = (
            flee.SimulationSettings.move_rules["AwarenessLevel"] == original_awareness and
            flee.SimulationSettings.move_rules["WeightSoftening"] == original_weight_softening and
            flee.SimulationSettings.move_rules["DistancePower"] == original_distance_power and
            flee.SimulationSettings.move_rules["PruningThreshold"] == original_pruning_threshold
        )
        
        if params_restored:
            print("✅ Parameters were correctly restored after S2 route selection")
        else:
            print("❌ Parameters were not restored correctly")
        
        print(f"\n🎉 Comprehensive S1/S2 test completed!")
        
    except Exception as e:
        print(f"❌ Error during comprehensive test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    test_s1s2_comprehensive()




