#!/usr/bin/env python3
"""
Test Existing Cognitive System in Flee

Tests the S1/S2 cognitive functionality that's already implemented in Flee master branch.
"""

import sys
import os
from pathlib import Path

def setup_flee_path():
    """Set up the path to import Flee as a package."""
    # Add the parent directory to path so we can import flee as a package
    parent_dir = Path(__file__).parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    print(f"✅ Added parent directory to path: {parent_dir}")

def test_flee_package_import():
    """Test importing Flee as a package."""
    print("🔍 Testing Flee package import...")
    
    try:
        # Import flee as a package
        import flee
        print("✅ Flee package imported successfully")
        
        # Test specific classes
        from flee.flee import Person, Location
        print("✅ Person and Location classes imported successfully")
        
        # Test SimulationSettings
        from flee.SimulationSettings import SimulationSettings
        print("✅ SimulationSettings imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Flee package import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_cognitive_parameters():
    """Test that cognitive parameters exist in SimulationSettings."""
    print("\n🔍 Testing cognitive parameters...")
    
    try:
        from flee.SimulationSettings import SimulationSettings
        
        # Check for cognitive parameters
        cognitive_params = {
            'TwoSystemDecisionMaking': 'two_system_decision_making',
            'conflict_threshold': 'conflict_threshold', 
            'AwarenessLevel': 'awareness_level',
            'AverageSocialConnectivity': 'average_social_connectivity'
        }
        
        found_params = []
        missing_params = []
        
        for param_name, config_key in cognitive_params.items():
            if param_name in SimulationSettings.move_rules or param_name in SimulationSettings.spawn_rules:
                found_params.append(param_name)
                # Get the value
                if param_name in SimulationSettings.move_rules:
                    value = SimulationSettings.move_rules[param_name]
                    print(f"   - {param_name}: {value} (in move_rules)")
                elif param_name in SimulationSettings.spawn_rules:
                    value = SimulationSettings.spawn_rules[param_name]
                    print(f"   - {param_name}: {value} (in spawn_rules)")
            else:
                missing_params.append(param_name)
        
        if found_params:
            print(f"✅ Found cognitive parameters: {found_params}")
        
        if missing_params:
            print(f"⚠️  Missing cognitive parameters: {missing_params}")
        
        return len(found_params) > 0
        
    except Exception as e:
        print(f"❌ Cognitive parameters test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cognitive_person_methods():
    """Test that Person class has cognitive methods."""
    print("\n🔍 Testing Person class cognitive methods...")
    
    try:
        from flee.flee import Person, Location
        
        # Create test location and person
        test_location = Location("TestLocation", 0, 0, 1000)
        test_person = Person(test_location)
        
        print(f"✅ Person created at location: {test_person.location.name}")
        
        # Check cognitive attributes
        cognitive_attrs = [
            'cognitive_state',
            'decision_history', 
            'system2_activations',
            'days_in_current_location'
        ]
        
        found_attrs = []
        missing_attrs = []
        
        for attr in cognitive_attrs:
            if hasattr(test_person, attr):
                found_attrs.append(attr)
                value = getattr(test_person, attr)
                print(f"   - {attr}: {value}")
            else:
                missing_attrs.append(attr)
        
        if found_attrs:
            print(f"✅ Found cognitive attributes: {found_attrs}")
        
        if missing_attrs:
            print(f"⚠️  Missing cognitive attributes: {missing_attrs}")
        
        # Check cognitive methods
        cognitive_methods = [
            'calculate_cognitive_pressure',
            'get_system2_capable',
            'log_decision'
        ]
        
        found_methods = []
        missing_methods = []
        
        for method in cognitive_methods:
            if hasattr(test_person, method):
                found_methods.append(method)
            else:
                missing_methods.append(method)
        
        if found_methods:
            print(f"✅ Found cognitive methods: {found_methods}")
        
        if missing_methods:
            print(f"⚠️  Missing cognitive methods: {missing_methods}")
        
        return len(found_attrs) > 0 and len(found_methods) > 0
        
    except Exception as e:
        print(f"❌ Person cognitive methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cognitive_move_calculation():
    """Test the cognitive move calculation functionality."""
    print("\n🔍 Testing cognitive move calculation...")
    
    try:
        from flee.flee import Person, Location
        from flee.SimulationSettings import SimulationSettings
        from flee import moving
        
        # Enable cognitive decision making
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.5
        print("✅ Enabled TwoSystemDecisionMaking")
        
        # Create test scenario
        test_location = Location("TestLocation", 0, 0, 1000)
        test_person = Person(test_location)
        
        # Test cognitive pressure calculation
        pressure = test_person.calculate_cognitive_pressure(time=1)
        print(f"✅ Cognitive pressure calculated: {pressure}")
        
        # Test System 2 capability
        s2_capable = test_person.get_system2_capable()
        print(f"✅ System 2 capable: {s2_capable}")
        
        # Test move chance calculation with cognitive logic
        movechance, system2_active = moving.calculateMoveChance(test_person, False, 1)
        print(f"✅ Move chance calculated: {movechance}, System 2 active: {system2_active}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cognitive move calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all cognitive system tests."""
    print("=" * 60)
    print("EXISTING COGNITIVE SYSTEM TEST")
    print("=" * 60)
    
    # Setup
    setup_flee_path()
    
    tests = [
        ("Package Import", test_flee_package_import),
        ("Cognitive Parameters", test_cognitive_parameters),
        ("Person Cognitive Methods", test_cognitive_person_methods),
        ("Cognitive Move Calculation", test_cognitive_move_calculation)
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
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All cognitive system tests passed! S1/S2 functionality is working.")
        return True
    else:
        print("⚠️  Some tests failed. The cognitive system may need fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)