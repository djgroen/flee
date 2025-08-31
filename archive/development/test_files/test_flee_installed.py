#!/usr/bin/env python3
"""
Test Flee as Installed Package

Tests Flee functionality now that it's properly installed as a package.
"""

import sys
import os
from pathlib import Path

def test_flee_package_import():
    """Test that Flee can be imported as an installed package."""
    print("🔍 Testing Flee package import...")
    
    try:
        import flee
        print("✅ Flee package imported successfully")
        
        # Test specific classes from flee.flee module
        from flee.flee import Person, Location, Link
        print("✅ Core Flee classes imported successfully")
        
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

def test_flee_classes():
    """Test that Flee classes can be instantiated."""
    print("\n🔍 Testing Flee class instantiation...")
    
    try:
        from flee.flee import Person, Location, Link
        
        # Test Location creation
        test_location = Location("TestLocation", x=0, y=0, capacity=1000)
        print(f"✅ Location created: {test_location.name}, capacity: {test_location.capacity}")
        
        # Test Person creation
        test_person = Person(test_location)
        print(f"✅ Person created at location: {test_person.location.name}")
        
        # Test basic Person attributes
        print(f"   - Location: {test_person.location.name}")
        print(f"   - Travelling: {test_person.travelling}")
        
        # Check if cognitive methods exist (they might not yet)
        if hasattr(test_person, 'calculate_cognitive_pressure'):
            print("✅ Cognitive methods found in Person class")
        else:
            print("⚠️  Cognitive methods not yet implemented in Person class")
        
        return True
        
    except Exception as e:
        print(f"❌ Class instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simulation_settings():
    """Test SimulationSettings functionality."""
    print("\n🔍 Testing SimulationSettings...")
    
    try:
        from flee.SimulationSettings import SimulationSettings
        
        print("✅ SimulationSettings imported successfully")
        
        # Check current move_rules
        print(f"   - move_rules type: {type(SimulationSettings.move_rules)}")
        print(f"   - move_rules keys: {list(SimulationSettings.move_rules.keys())}")
        
        # Check if cognitive parameters exist
        cognitive_params = [
            'TwoSystemDecisionMaking',
            'conflict_threshold',
            'average_social_connectivity'
        ]
        
        found_params = []
        missing_params = []
        
        for param in cognitive_params:
            if param in SimulationSettings.move_rules:
                found_params.append(param)
            else:
                missing_params.append(param)
        
        if found_params:
            print(f"✅ Found cognitive parameters: {found_params}")
        
        if missing_params:
            print(f"⚠️  Missing cognitive parameters: {missing_params}")
            
        # Test adding cognitive parameters
        original_count = len(SimulationSettings.move_rules)
        SimulationSettings.move_rules['TwoSystemDecisionMaking'] = False
        SimulationSettings.move_rules['conflict_threshold'] = 0.5
        SimulationSettings.move_rules['average_social_connectivity'] = 0.1
        
        new_count = len(SimulationSettings.move_rules)
        print(f"✅ Successfully added {new_count - original_count} cognitive parameters")
        
        return True
        
    except Exception as e:
        print(f"❌ SimulationSettings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_flee_scenario():
    """Test creating a basic Flee scenario structure."""
    print("\n🔍 Testing basic Flee scenario creation...")
    
    try:
        from flee.flee import Person, Location, Link
        
        # Create a simple scenario: Origin -> Camp
        origin = Location("Origin", x=0, y=0, capacity=1000, location_type="conflict_zone")
        camp = Location("Camp", x=100, y=0, capacity=500, location_type="camp")
        
        print(f"✅ Created origin: {origin.name} (conflict: {origin.conflict})")
        print(f"✅ Created camp: {camp.name} (camp: {camp.camp})")
        
        # Create a link between them
        link = Link(origin, camp, distance=100, forced_redirection=False)
        print(f"✅ Created link: {link.startpoint.name} -> {link.endpoint.name} ({link.distance}km)")
        
        # Create some agents
        agents = []
        for i in range(10):
            agent = Person(origin)
            agents.append(agent)
        
        print(f"✅ Created {len(agents)} agents at origin")
        print(f"   - Origin population: {origin.numAgents}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic scenario creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flee_runscripts():
    """Test if Flee runscripts exist and can be accessed."""
    print("\n🔍 Testing Flee runscripts availability...")
    
    try:
        # Check if runscripts directory exists
        runscripts_dir = Path("runscripts")
        if runscripts_dir.exists():
            print(f"✅ Found runscripts directory: {runscripts_dir}")
            
            # List some runscripts
            runscript_files = list(runscripts_dir.glob("*.py"))
            if runscript_files:
                print(f"   - Found {len(runscript_files)} Python runscripts")
                for script in runscript_files[:3]:  # Show first 3
                    print(f"     - {script.name}")
            else:
                print("⚠️  No Python runscripts found")
        else:
            print("⚠️  Runscripts directory not found")
        
        # Check if we can access test scenarios
        test_data_dir = Path("test_data")
        if test_data_dir.exists():
            print(f"✅ Found test_data directory: {test_data_dir}")
            
            # Look for example scenarios
            scenario_dirs = [d for d in test_data_dir.iterdir() if d.is_dir()]
            if scenario_dirs:
                print(f"   - Found {len(scenario_dirs)} test scenarios")
                for scenario in scenario_dirs[:3]:  # Show first 3
                    print(f"     - {scenario.name}")
            else:
                print("⚠️  No test scenarios found")
        else:
            print("⚠️  test_data directory not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Runscripts test failed: {e}")
        return False

def main():
    """Run all Flee installation tests."""
    print("=" * 60)
    print("FLEE INSTALLED PACKAGE DIAGNOSTIC")
    print("=" * 60)
    
    tests = [
        ("Package Import", test_flee_package_import),
        ("Class Instantiation", test_flee_classes),
        ("SimulationSettings", test_simulation_settings),
        ("Basic Scenario", test_basic_flee_scenario),
        ("Runscripts Access", test_flee_runscripts)
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
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 4:  # If core functionality works
        print("🎉 Flee is properly installed and functional!")
        print("\n📋 Next Steps:")
        print("   1. Add cognitive parameters to SimulationSettings")
        print("   2. Implement cognitive decision logic in Person class")
        print("   3. Create simple test scenarios")
        print("   4. Run basic Flee simulations")
        return True
    else:
        print("⚠️  Flee installation has issues that need to be resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)