#!/usr/bin/env python3
"""
Basic Flee Integration Test

Tests that Flee can be imported and basic functionality works.
This is the first step in diagnosing integration issues.
"""

import sys
import os
from pathlib import Path

def test_flee_import():
    """Test that Flee can be imported correctly."""
    print("🔍 Testing Flee import...")
    
    try:
        # Add flee directory to path
        flee_dir = Path(__file__).parent / 'flee'
        if flee_dir.exists():
            sys.path.insert(0, str(flee_dir))
            print(f"✅ Added Flee directory to path: {flee_dir}")
        else:
            print(f"❌ Flee directory not found: {flee_dir}")
            return False
        
        # Test importing flee.py directly (not as package)
        import flee
        print("✅ Flee module imported successfully")
        
        # Test specific classes - they should be in the flee module
        if hasattr(flee, 'Person'):
            print("✅ Person class found in flee module")
        else:
            print("❌ Person class not found in flee module")
            return False
            
        if hasattr(flee, 'Location'):
            print("✅ Location class found in flee module")
        else:
            print("❌ Location class not found in flee module")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Flee import failed: {e}")
        print("   This might be due to missing dependencies or import structure issues")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_basic_flee_classes():
    """Test that basic Flee classes can be instantiated."""
    print("\n🔍 Testing basic Flee class instantiation...")
    
    try:
        # Import flee module
        sys.path.insert(0, str(Path(__file__).parent / 'flee'))
        import flee
        
        # Get classes from flee module
        Person = flee.Person
        Location = flee.Location
        
        # Test Location creation
        test_location = Location("TestLocation", 0, 0, 1000)
        print(f"✅ Location created: {test_location.name}, capacity: {test_location.capacity}")
        
        # Test Person creation
        test_person = Person(test_location)
        print(f"✅ Person created at location: {test_person.location.name}")
        
        # Test basic Person attributes
        print(f"   - Age: {test_person.age}")
        print(f"   - Gender: {test_person.gender}")
        
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

def test_flee_simulation_settings():
    """Test that SimulationSettings can be imported and used."""
    print("\n🔍 Testing Flee SimulationSettings...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'flee'))
        import SimulationSettings
        
        print("✅ SimulationSettings imported successfully")
        
        # Check current move_rules
        print(f"   - Current move_rules keys: {list(SimulationSettings.SimulationSettings.move_rules.keys())}")
        
        # Check if cognitive parameters exist
        cognitive_params = [
            'TwoSystemDecisionMaking',
            'conflict_threshold',
            'average_social_connectivity'
        ]
        
        found_params = []
        missing_params = []
        
        for param in cognitive_params:
            if param in SimulationSettings.SimulationSettings.move_rules:
                found_params.append(param)
            else:
                missing_params.append(param)
        
        if found_params:
            print(f"✅ Found cognitive parameters: {found_params}")
        
        if missing_params:
            print(f"⚠️  Missing cognitive parameters: {missing_params}")
        
        return True
        
    except Exception as e:
        print(f"❌ SimulationSettings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flee_directory_structure():
    """Test that Flee directory has expected structure."""
    print("\n🔍 Testing Flee directory structure...")
    
    flee_dir = Path(__file__).parent / 'flee'
    
    if not flee_dir.exists():
        print(f"❌ Flee directory not found: {flee_dir}")
        return False
    
    expected_files = [
        'flee.py',
        'SimulationSettings.py',
        'InputGeography.py'
    ]
    
    found_files = []
    missing_files = []
    
    for filename in expected_files:
        filepath = flee_dir / filename
        if filepath.exists():
            found_files.append(filename)
        else:
            missing_files.append(filename)
    
    print(f"✅ Found Flee files: {found_files}")
    
    if missing_files:
        print(f"❌ Missing Flee files: {missing_files}")
        return False
    
    return True

def main():
    """Run all basic Flee tests."""
    print("=" * 60)
    print("BASIC FLEE INTEGRATION DIAGNOSTIC")
    print("=" * 60)
    
    tests = [
        ("Directory Structure", test_flee_directory_structure),
        ("Flee Import", test_flee_import),
        ("Basic Classes", test_basic_flee_classes),
        ("SimulationSettings", test_flee_simulation_settings)
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
    
    if passed == total:
        print("🎉 All basic tests passed! Flee integration looks good.")
        return True
    else:
        print("⚠️  Some tests failed. Check output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)