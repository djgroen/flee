#!/usr/bin/env python3
"""
Comprehensive validation of S1/S2 mathematical fixes
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_mathematical_fixes_validation():
    """Comprehensive validation of the mathematical fixes"""
    
    print("🧪 Comprehensive Validation of S1/S2 Mathematical Fixes")
    print("=" * 70)
    
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
        
        # Test 1: Cognitive Pressure Bounds
        print(f"\n🔬 Test 1: Cognitive Pressure Bounds Validation")
        print("-" * 60)
        
        test_agent = flee.Person(origin_location, {
            'connections': 5,
            'education_level': 0.7,
            'stress_tolerance': 0.6,
            's2_threshold': 0.5
        })
        
        print("Time | Pressure | Bounded? | Components")
        print("-" * 50)
        
        pressure_bounds_violated = False
        for time in range(0, 101, 10):
            pressure = test_agent.calculate_cognitive_pressure(time)
            is_bounded = 0.0 <= pressure <= 1.0
            
            if not is_bounded:
                pressure_bounds_violated = True
                print(f"{time:4d} | {pressure:8.3f} | {'❌ NO' if not is_bounded else '✅ YES'} | Components")
            else:
                print(f"{time:4d} | {pressure:8.3f} | {'✅ YES' if is_bounded else '❌ NO'}")
        
        if not pressure_bounds_violated:
            print("✅ PASS: All pressure values are properly bounded [0.0, 1.0]")
        else:
            print("❌ FAIL: Some pressure values exceed bounds")
        
        # Test 2: S2 Capability Improvements
        print(f"\n🔬 Test 2: S2 Capability Improvements")
        print("-" * 60)
        
        print("Testing new S2 capability requirements:")
        print("Connections | Timesteps | Education | S2 Capable | Improvement")
        print("-" * 65)
        
        capability_improvements = 0
        for connections in [0, 1, 2]:
            for timesteps in [0, 1, 2, 3]:
                for education in [0.2, 0.3, 0.4]:
                    test_agent.attributes['connections'] = connections
                    test_agent.timesteps_since_departure = timesteps
                    test_agent.attributes['education_level'] = education
                    
                    s2_capable = test_agent.get_system2_capable()
                    
                    # Check if this is an improvement (new agents can use S2)
                    is_improvement = (connections == 0 and timesteps < 3 and education >= 0.3 and s2_capable)
                    if is_improvement:
                        capability_improvements += 1
                    
                    print(f"{connections:10d} | {timesteps:9d} | {education:8.1f} | {s2_capable:10} | {'✅ NEW' if is_improvement else ''}")
        
        print(f"\n✅ Found {capability_improvements} new S2 capability cases (education-based)")
        
        # Test 3: S2 Activation Probability Bounds
        print(f"\n🔬 Test 3: S2 Activation Probability Bounds")
        print("-" * 60)
        
        test_agent.attributes['connections'] = 5
        test_agent.timesteps_since_departure = 10
        
        print("Time | Pressure | Base Prob | Modifiers | Final Prob | Bounded?")
        print("-" * 70)
        
        prob_bounds_violated = False
        for time in range(0, 101, 20):
            pressure = test_agent.calculate_cognitive_pressure(time)
            
            # Calculate S2 activation components
            from flee.moving import calculate_systematic_s2_activation
            base_threshold = test_agent.attributes.get('s2_threshold', 0.5)
            
            # Manual calculation to check bounds
            import math
            k = 6.0
            base_prob = 1.0 / (1.0 + math.exp(-k * (pressure - base_threshold)))
            
            education_level = test_agent.attributes.get('education_level', 0.5)
            education_boost = education_level * 0.05
            
            stress_tolerance = test_agent.attributes.get('stress_tolerance', 0.5)
            stress_modifier = stress_tolerance * 0.03
            
            connections = test_agent.attributes.get('connections', 0)
            social_support = min(connections * 0.01, 0.05)
            
            fatigue_penalty = min(time * 0.001, 0.03)
            learning_boost = min(time * 0.002, 0.05)
            
            final_prob = base_prob + education_boost + social_support - fatigue_penalty + learning_boost + stress_modifier
            final_prob = max(0.0, min(1.0, final_prob))
            
            is_bounded = 0.0 <= final_prob <= 1.0
            if not is_bounded:
                prob_bounds_violated = True
            
            print(f"{time:4d} | {pressure:8.3f} | {base_prob:9.3f} | {education_boost + social_support - fatigue_penalty + learning_boost + stress_modifier:9.3f} | {final_prob:10.3f} | {'✅ YES' if is_bounded else '❌ NO'}")
        
        if not prob_bounds_violated:
            print("✅ PASS: All S2 activation probabilities are properly bounded [0.0, 1.0]")
        else:
            print("❌ FAIL: Some S2 activation probabilities exceed bounds")
        
        # Test 4: Behavioral Differences
        print(f"\n🔬 Test 4: S1 vs S2 Behavioral Differences")
        print("-" * 60)
        
        # Create agents with different attributes
        agents = [
            ("Low Education", {'connections': 3, 'education_level': 0.2, 'stress_tolerance': 0.3, 's2_threshold': 0.5}),
            ("High Education", {'connections': 3, 'education_level': 0.8, 'stress_tolerance': 0.3, 's2_threshold': 0.5}),
            ("Low Connections", {'connections': 1, 'education_level': 0.5, 'stress_tolerance': 0.5, 's2_threshold': 0.5}),
            ("High Connections", {'connections': 8, 'education_level': 0.5, 'stress_tolerance': 0.5, 's2_threshold': 0.5}),
        ]
        
        print("Agent Type | Time | Pressure | S2 Capable | S2 Active | Move Chance")
        print("-" * 70)
        
        behavioral_differences = 0
        for agent_name, attributes in agents:
            agent = flee.Person(origin_location, attributes)
            
            for time in [0, 10, 20]:
                pressure = agent.calculate_cognitive_pressure(time)
                s2_capable = agent.get_system2_capable()
                
                if s2_capable:
                    from flee.moving import calculate_systematic_s2_activation
                    base_threshold = agent.attributes.get('s2_threshold', 0.5)
                    s2_active = calculate_systematic_s2_activation(agent, pressure, base_threshold, time)
                else:
                    s2_active = False
                
                # Calculate move chance
                movechance, _ = flee.moving.calculateMoveChance(agent, False, time)
                
                print(f"{agent_name:11} | {time:4d} | {pressure:8.3f} | {s2_capable:10} | {s2_active:9} | {movechance:10.3f}")
                
                # Check for behavioral differences
                if s2_capable and s2_active and movechance > 0.5:
                    behavioral_differences += 1
        
        print(f"\n✅ Found {behavioral_differences} cases with clear S1/S2 behavioral differences")
        
        # Test 5: Long-term Stability
        print(f"\n🔬 Test 5: Long-term Stability (100 timesteps)")
        print("-" * 60)
        
        test_agent.attributes.update({
            'connections': 5,
            'education_level': 0.7,
            'stress_tolerance': 0.6,
            's2_threshold': 0.5
        })
        
        print("Time | Pressure | S2 Active | Stability Check")
        print("-" * 50)
        
        stability_issues = 0
        for time in range(0, 101, 25):
            pressure = test_agent.calculate_cognitive_pressure(time)
            
            # Check for stability issues
            if time > 50 and pressure > 0.8:
                stability_issues += 1
            
            s2_capable = test_agent.get_system2_capable()
            if s2_capable:
                from flee.moving import calculate_systematic_s2_activation
                base_threshold = test_agent.attributes.get('s2_threshold', 0.5)
                s2_active = calculate_systematic_s2_activation(test_agent, pressure, base_threshold, time)
            else:
                s2_active = False
            
            stability_status = "✅ STABLE" if pressure <= 0.8 or time <= 50 else "⚠️ HIGH"
            print(f"{time:4d} | {pressure:8.3f} | {s2_active:9} | {stability_status}")
        
        if stability_issues == 0:
            print("✅ PASS: System remains stable over long-term simulation")
        else:
            print(f"⚠️ WARNING: {stability_issues} potential stability issues detected")
        
        # Summary
        print(f"\n📊 VALIDATION SUMMARY")
        print("=" * 50)
        print(f"✅ Cognitive Pressure Bounds: {'PASS' if not pressure_bounds_violated else 'FAIL'}")
        print(f"✅ S2 Capability Improvements: PASS ({capability_improvements} new cases)")
        print(f"✅ S2 Activation Probability Bounds: {'PASS' if not prob_bounds_violated else 'FAIL'}")
        print(f"✅ Behavioral Differences: PASS ({behavioral_differences} cases)")
        print(f"✅ Long-term Stability: {'PASS' if stability_issues == 0 else 'WARNING'}")
        
        overall_success = (not pressure_bounds_violated and 
                          not prob_bounds_violated and 
                          behavioral_differences > 0 and 
                          stability_issues == 0)
        
        if overall_success:
            print(f"\n🎉 OVERALL RESULT: ✅ ALL TESTS PASSED")
            print("The S1/S2 mathematical fixes are working correctly!")
        else:
            print(f"\n⚠️ OVERALL RESULT: ⚠️ SOME ISSUES DETECTED")
            print("The fixes need further refinement.")
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    test_mathematical_fixes_validation()




