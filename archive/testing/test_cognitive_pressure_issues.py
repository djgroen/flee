#!/usr/bin/env python3
"""
Test cognitive pressure calculation issues
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_cognitive_pressure_issues():
    """Test cognitive pressure calculation for issues"""
    
    print("🧪 Testing Cognitive Pressure Calculation Issues")
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
        
        # Read simulation settings
        flee.SimulationSettings.ReadFromYML("simsetting.yml")
        
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
        
        # Get origin location
        origin_location = None
        for loc_name, loc in lm.items():
            if "Origin" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            print("❌ No origin location found!")
            return
        
        print(f"📍 Origin location: {origin_location.name}")
        print(f"📍 Origin conflict intensity: {getattr(origin_location, 'conflict', 'N/A')}")
        
        # Test cognitive pressure calculation over time
        print(f"\n🔬 Testing Cognitive Pressure Over Time:")
        print("-" * 50)
        
        # Create test agent
        test_agent = flee.Person(origin_location, {
            'connections': 5,
            'education_level': 0.7,
            'stress_tolerance': 0.6,
            's2_threshold': 0.5
        })
        
        print("Time | Base Pressure | Conflict Pressure | Total Pressure | S2 Capable | S2 Active")
        print("-" * 80)
        
        for time in range(0, 101, 10):
            # Calculate cognitive pressure manually to see components
            conflict_intensity = max(0.0, getattr(origin_location, 'conflict', 0.0))
            connectivity = min(1.0, test_agent.attributes.get("connections", 0) / 10.0)
            
            # Calculate recovery period
            recovery_period = 30.0  # Default
            if hasattr(origin_location, 'time_of_conflict') and origin_location.time_of_conflict >= 0:
                recovery_period = max(1.0, time - origin_location.time_of_conflict)
            
            # Base pressure components
            base_pressure = connectivity * 0.3 + (time / 20.0) * 0.2
            conflict_pressure = (conflict_intensity * connectivity) / (recovery_period / 30.0)
            total_pressure = base_pressure + conflict_pressure
            
            # Check S2 capability
            s2_capable = test_agent.get_system2_capable()
            
            # Check S2 activation
            s2_active = False
            if s2_capable:
                from flee.moving import calculate_systematic_s2_activation
                base_threshold = test_agent.attributes.get('s2_threshold', 0.5)
                s2_active = calculate_systematic_s2_activation(
                    test_agent, total_pressure, base_threshold, time
                )
            
            print(f"{time:4d} | {base_pressure:12.3f} | {conflict_pressure:15.3f} | {total_pressure:13.3f} | {s2_capable:10} | {s2_active}")
            
            # Check for issues
            if total_pressure > 1.0:
                print(f"    ⚠️  WARNING: Total pressure > 1.0 at time {time}")
            if base_pressure > 1.0:
                print(f"    ⚠️  WARNING: Base pressure > 1.0 at time {time}")
            if time > 50 and base_pressure > 0.8:
                print(f"    ⚠️  WARNING: Base pressure very high at time {time}")
        
        # Test S2 capability for new agents
        print(f"\n🔬 Testing S2 Capability for New Agents:")
        print("-" * 50)
        
        for connections in range(0, 11):
            for timesteps in range(0, 11):
                test_agent.attributes['connections'] = connections
                test_agent.timesteps_since_departure = timesteps
                
                s2_capable = test_agent.get_system2_capable()
                print(f"Connections: {connections:2d}, Timesteps: {timesteps:2d} -> S2 Capable: {s2_capable}")
        
        # Test S2 activation probability over time
        print(f"\n🔬 Testing S2 Activation Probability Over Time:")
        print("-" * 50)
        
        test_agent.attributes['connections'] = 5
        test_agent.timesteps_since_departure = 10  # Make S2 capable
        
        print("Time | Pressure | Base Prob | Education | Social | Fatigue | Learning | Final Prob | S2 Active")
        print("-" * 100)
        
        for time in range(0, 101, 20):
            # Calculate pressure
            cognitive_pressure = test_agent.calculate_cognitive_pressure(time)
            
            # Calculate S2 activation components manually
            import math
            import random
            
            base_threshold = test_agent.attributes.get('s2_threshold', 0.5)
            k = 8.0
            base_prob = 1.0 / (1.0 + math.exp(-k * (cognitive_pressure - base_threshold)))
            
            education_level = test_agent.attributes.get('education_level', 0.5)
            education_boost = education_level * 0.1
            
            stress_tolerance = test_agent.attributes.get('stress_tolerance', 0.5)
            stress_modifier = stress_tolerance * 0.05
            
            connections = test_agent.attributes.get('connections', 5)
            social_support = min(connections * 0.02, 0.1)
            
            fatigue_penalty = min(time * 0.002, 0.1)
            learning_boost = min(time * 0.001, 0.05)
            
            final_prob = base_prob + education_boost + social_support - fatigue_penalty + learning_boost + stress_modifier
            final_prob = max(0.0, min(1.0, final_prob))
            
            # Test activation
            s2_active = random.random() < final_prob
            
            print(f"{time:4d} | {cognitive_pressure:8.3f} | {base_prob:9.3f} | {education_boost:9.3f} | {social_support:6.3f} | {fatigue_penalty:7.3f} | {learning_boost:8.3f} | {final_prob:10.3f} | {s2_active}")
            
            # Check for issues
            if fatigue_penalty > 0.05:
                print(f"    ⚠️  WARNING: High fatigue penalty at time {time}")
            if learning_boost < 0.01:
                print(f"    ⚠️  WARNING: Very low learning boost at time {time}")
        
        print(f"\n🎉 Cognitive pressure analysis completed!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    test_cognitive_pressure_issues()




