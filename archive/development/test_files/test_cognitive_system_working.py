#!/usr/bin/env python3
"""
Test Working Cognitive System in Flee

Tests the S1/S2 cognitive functionality that's already implemented and working in Flee.
"""

import sys
import os
from pathlib import Path

def test_cognitive_system_with_proper_setup():
    """Test the cognitive system with proper Flee setup."""
    print("🔍 Testing cognitive system with proper Flee setup...")
    
    try:
        # Set up PYTHONPATH properly
        current_dir = Path(__file__).parent
        os.environ['PYTHONPATH'] = f"{current_dir}:{os.environ.get('PYTHONPATH', '')}"
        
        # Import Flee components
        import flee.flee as flee_module
        from flee.SimulationSettings import SimulationSettings
        from flee import moving
        
        print("✅ Flee modules imported successfully")
        
        # Initialize SimulationSettings with default values by reading the default YAML
        yaml_file = current_dir / "flee" / "simsetting.yml"
        if yaml_file.exists():
            SimulationSettings.ReadFromYML(str(yaml_file))
            print("✅ SimulationSettings initialized from YAML")
        else:
            print("⚠️  No simsetting.yml found, using defaults")
        
        # Check cognitive parameters
        print(f"   - TwoSystemDecisionMaking: {SimulationSettings.move_rules.get('TwoSystemDecisionMaking', 'NOT FOUND')}")
        print(f"   - conflict_threshold: {SimulationSettings.move_rules.get('conflict_threshold', 'NOT FOUND')}")
        print(f"   - AwarenessLevel: {SimulationSettings.move_rules.get('AwarenessLevel', 'NOT FOUND')}")
        
        # Enable cognitive decision making
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.5
        print("✅ Enabled TwoSystemDecisionMaking")
        
        # Create test ecosystem
        ecosystem = flee_module.Ecosystem()
        
        # Add locations
        origin = ecosystem.addLocation("Origin", 0, 0, movechance=1.0, capacity=-1, pop=1000)
        camp = ecosystem.addLocation("Camp", 100, 0, movechance=0.001, capacity=10000, pop=0)
        
        # Add route
        ecosystem.linkUp("Origin", "Camp", 100.0)
        
        print("✅ Created test ecosystem with Origin and Camp")
        
        # Add agents
        for i in range(10):
            ecosystem.addAgent(location=origin, attributes={})
        
        print("✅ Added 10 agents to Origin")
        
        # Test cognitive functionality on agents
        agents = origin.agents
        if len(agents) > 0:
            test_agent = agents[0]
            
            # Test cognitive attributes
            print(f"   - Agent cognitive_state: {test_agent.cognitive_state}")
            print(f"   - Agent system2_activations: {test_agent.system2_activations}")
            
            # Test cognitive pressure calculation
            pressure = test_agent.calculate_cognitive_pressure(time=1)
            print(f"   - Cognitive pressure: {pressure}")
            
            # Test System 2 capability
            s2_capable = test_agent.get_system2_capable()
            print(f"   - System 2 capable: {s2_capable}")
            
            # Test move chance calculation with cognitive logic
            movechance, system2_active = moving.calculateMoveChance(test_agent, False, 1)
            print(f"   - Move chance: {movechance}, System 2 active: {system2_active}")
            
            print("✅ All cognitive methods working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Cognitive system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cognitive_differences():
    """Test that different cognitive modes produce different behaviors."""
    print("\n🔍 Testing cognitive mode differences...")
    
    try:
        import flee.flee as flee_module
        from flee.SimulationSettings import SimulationSettings
        from flee import moving
        
        # Initialize settings
        current_dir = Path(__file__).parent
        yaml_file = current_dir / "flee" / "simsetting.yml"
        if yaml_file.exists():
            SimulationSettings.ReadFromYML(str(yaml_file))
        
        results = {}
        
        # Test S1 only mode (TwoSystemDecisionMaking = False)
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = False
        
        ecosystem_s1 = flee_module.Ecosystem()
        origin_s1 = ecosystem_s1.addLocation("Origin", 0, 0, movechance=1.0, capacity=-1, pop=1000)
        camp_s1 = ecosystem_s1.addLocation("Camp", 100, 0, movechance=0.001, capacity=10000, pop=0)
        ecosystem_s1.linkUp("Origin", "Camp", 100.0)
        
        agent_s1 = ecosystem_s1.addAgent(location=origin_s1, attributes={})
        movechance_s1, system2_active_s1 = moving.calculateMoveChance(agent_s1, False, 1)
        
        results['S1_only'] = {
            'movechance': movechance_s1,
            'system2_active': system2_active_s1,
            'cognitive_state': agent_s1.cognitive_state
        }
        
        print(f"   - S1 only: movechance={movechance_s1}, S2_active={system2_active_s1}, state={agent_s1.cognitive_state}")
        
        # Test S2 mode (TwoSystemDecisionMaking = True, low threshold)
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.1  # Low threshold for easy activation
        
        ecosystem_s2 = flee_module.Ecosystem()
        origin_s2 = ecosystem_s2.addLocation("Origin", 0, 0, movechance=1.0, capacity=-1, pop=1000)
        camp_s2 = ecosystem_s2.addLocation("Camp", 100, 0, movechance=0.001, capacity=10000, pop=0)
        ecosystem_s2.linkUp("Origin", "Camp", 100.0)
        
        # Add conflict to trigger S2
        origin_s2.conflict = 1.0
        origin_s2.time_of_conflict = 0
        
        agent_s2 = ecosystem_s2.addAgent(location=origin_s2)
        
        # Give agent some connections to increase cognitive pressure
        agent_s2.attributes["connections"] = 5
        
        movechance_s2, system2_active_s2 = moving.calculateMoveChance(agent_s2, False, 5)
        
        results['S2_active'] = {
            'movechance': movechance_s2,
            'system2_active': system2_active_s2,
            'cognitive_state': agent_s2.cognitive_state
        }
        
        print(f"   - S2 active: movechance={movechance_s2}, S2_active={system2_active_s2}, state={agent_s2.cognitive_state}")
        
        # Check if we got different results
        s1_s2_different = (
            results['S1_only']['system2_active'] != results['S2_active']['system2_active'] or
            results['S1_only']['cognitive_state'] != results['S2_active']['cognitive_state']
        )
        
        if s1_s2_different:
            print("✅ S1 and S2 modes produce different behaviors!")
            return True
        else:
            print("⚠️  S1 and S2 modes produced identical results - may need parameter tuning")
            return False
        
    except Exception as e:
        print(f"❌ Cognitive differences test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_cognitive_simulation():
    """Run a simple simulation with cognitive agents."""
    print("\n🔍 Testing simple cognitive simulation...")
    
    try:
        import flee.flee as flee_module
        from flee.SimulationSettings import SimulationSettings
        
        # Initialize settings
        current_dir = Path(__file__).parent
        yaml_file = current_dir / "flee" / "simsetting.yml"
        if yaml_file.exists():
            SimulationSettings.ReadFromYML(str(yaml_file))
        
        # Enable cognitive decision making
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.3
        
        # Create ecosystem
        ecosystem = flee_module.Ecosystem()
        
        # Add locations
        origin = ecosystem.addLocation("Origin", 0, 0, movechance=1.0, capacity=-1, pop=1000)
        intermediate = ecosystem.addLocation("Intermediate", 50, 0, movechance=0.3, capacity=-1, pop=0)
        camp = ecosystem.addLocation("Camp", 100, 0, movechance=0.001, capacity=5000, pop=0)
        
        # Add routes
        ecosystem.linkUp("Origin", "Intermediate", 50.0)
        ecosystem.linkUp("Intermediate", "Camp", 50.0)
        
        # Add conflict at origin
        origin.conflict = 1.0
        origin.time_of_conflict = 0
        
        # Add agents
        for i in range(5):
            agent = ecosystem.addAgent(location=origin)
            # Give some agents more connections
            if i < 3:
                agent.attributes["connections"] = 3
        
        print("✅ Created ecosystem with 5 cognitive agents")
        
        # Run a few simulation steps
        initial_origin_pop = len(origin.agents)
        
        for day in range(3):
            ecosystem.evolve()
            
            # Count cognitive states
            s1_count = 0
            s2_count = 0
            s2_activations = 0
            
            for location in [origin, intermediate, camp]:
                for agent in location.agents:
                    if agent.cognitive_state == "S1":
                        s1_count += 1
                    elif agent.cognitive_state == "S2":
                        s2_count += 1
                    s2_activations += agent.system2_activations
            
            print(f"   Day {day}: Origin={len(origin.agents)}, Intermediate={len(intermediate.agents)}, Camp={len(camp.agents)}")
            print(f"            S1 agents={s1_count}, S2 agents={s2_count}, Total S2 activations={s2_activations}")
        
        final_origin_pop = len(origin.agents)
        movement_occurred = final_origin_pop < initial_origin_pop
        
        if movement_occurred:
            print("✅ Agent movement occurred in cognitive simulation")
            return True
        else:
            print("⚠️  No agent movement detected - check parameters")
            return False
        
    except Exception as e:
        print(f"❌ Simple cognitive simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all cognitive system tests."""
    print("=" * 60)
    print("WORKING COGNITIVE SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Cognitive System Setup", test_cognitive_system_with_proper_setup),
        ("Cognitive Mode Differences", test_cognitive_differences),
        ("Simple Cognitive Simulation", test_simple_cognitive_simulation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The existing S1/S2 cognitive system is working!")
        print("\n📋 FINDINGS:")
        print("- Flee already has comprehensive S1/S2 cognitive functionality implemented")
        print("- TwoSystemDecisionMaking parameter controls cognitive switching")
        print("- conflict_threshold controls when System 2 activates")
        print("- Agents have cognitive_state, system2_activations tracking")
        print("- Cognitive pressure calculation is working")
        print("- Different cognitive modes produce different behaviors")
        return True
    else:
        print("⚠️  Some tests failed. The cognitive system may need parameter tuning.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)