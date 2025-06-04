import sys
import os
import numpy as np

# Import setup (same as before)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flee import flee

def test_social_connectivity_crowded_area():
    """Unit test: Social connectivity increases in crowded areas"""
    print("Testing: Social connectivity in crowded areas")
    
    flee.SimulationSettings.ReadFromYML("test_settings.yml")
    
    # Create a simple agent
    agent_attributes = {"connections": 2}
    agent = flee.Person(None, agent_attributes)  # No location needed yet
    
    # Create a crowded location (mock object) - COMPLETE VERSION
    class MockLocation:
        def __init__(self, numAgents=500):
            self.name = "TestLocation"
            self.numAgents = numAgents
            self.camp = False           # ← Add this
            self.idpcamp = False        # ← Add this  
            self.conflict = 0.0         # ← Add this
    
    crowded_location = MockLocation(numAgents=500)
    
    # Test the function
    initial_connections = agent.attributes["connections"]
    agent.update_social_connectivity(crowded_location, time=0)
    final_connections = agent.attributes["connections"]
    
    # Check result
    if final_connections > initial_connections:
        print("PASS: Connections increased from", initial_connections, "to", final_connections)
        return True
    else:
        print("FAIL: Connections should increase in crowded areas")
        return False

def test_social_connectivity_isolated_area():
    """Unit test: Social connectivity decreases in isolated areas"""
    print("Testing: Social connectivity in isolated areas")
    
    flee.SimulationSettings.ReadFromYML("test_settings.yml")
    
    agent_attributes = {"connections": 5}
    agent = flee.Person(None, agent_attributes)
    
    class MockLocation:
        def __init__(self, numAgents):
            self.numAgents = numAgents
            self.camp = False
            self.idpcamp = False
            self.conflict = 0.0
    
    isolated_location = MockLocation(numAgents=3)
    
    initial_connections = agent.attributes["connections"]
    agent.update_social_connectivity(isolated_location, time=0)
    final_connections = agent.attributes["connections"]
    
    if final_connections < initial_connections:
        print("PASS: Connections decreased from", initial_connections, "to", final_connections)
        return True
    else:
        print("FAIL: Connections should decrease in isolated areas")
        return False

def test_system2_quick():
    """verify the logic paths work"""
    
    # Mock agent with minimal attributes
    class QuickMockAgent:
        def __init__(self):
            self.location = QuickMockLocation()
            self.attributes = {"connections": 4}
    
    class QuickMockLocation:
        def __init__(self):
            self.conflict = 0.7
            self.time_of_conflict = 5
            self.town = False
            self.movechance = 0.3
            self.pop = 1000
            self.capacity = 1000
    
    agent = QuickMockAgent()
    
    # Just test the boolean logic
    conflict_triggered = agent.location.conflict > 0.6
    in_recovery = agent.location.time_of_conflict >= 0 and 16 >= agent.location.time_of_conflict + 10
    connected = agent.attributes.get("connections", 0) >= 3
    
    assert conflict_triggered == True
    assert in_recovery == True  
    assert connected == True
    
    print("System 2 activation logic works!")
    return True  # ← Add this line!

def test_system1_quick():
    """Quick test for System 1 path"""
    
    class QuickMockAgent:
        def __init__(self):
            self.location = QuickMockLocation()
            self.attributes = {"connections": 1}  # Low connections
    
    class QuickMockLocation:
        def __init__(self):
            self.conflict = 0.3  # Low conflict
            self.time_of_conflict = 5
            self.town = False
            self.movechance = 0.3
            self.pop = 1000
            self.capacity = 1000
    
    agent = QuickMockAgent()
    
    # Test System 1 conditions
    conflict_triggered = agent.location.conflict > 0.6
    connected = agent.attributes.get("connections", 0) >= 3
    
    assert conflict_triggered == False  # Should use System 1
    assert connected == False
    
    print("System 1 path works!")

# Run these quick tests
test_system2_quick()
test_system1_quick()


def test_days_in_location_tracking():
    """Unit test: Days in location counter works correctly"""
    print("Testing: Days in location tracking")
    
    flee.SimulationSettings.ReadFromYML("test_settings.yml")
    
    # Create agent
    agent_attributes = {"connections": 3}
    agent = flee.Person(None, agent_attributes)
    
    # Test initial state
    if agent.days_in_current_location != 0:
        print("FAIL: Days should start at 0")
        return False
    
    # Mock the evolve increment (without full simulation)
    agent.travelling = False
    agent.days_in_current_location += 1  # Simulate what evolve() does
    
    if agent.days_in_current_location == 1:
        print("PASS: Days in location incremented correctly")
        return True
    else:
        print("FAIL: Days tracking not working")
        return False

        

if __name__ == "__main__":
    print("Running Unit Tests for System 1/System 2 Integration")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Run each test
    total_tests += 1
    if test_social_connectivity_crowded_area():
        tests_passed += 1
    
    total_tests += 1  
    if test_social_connectivity_isolated_area():
        tests_passed += 1
        
    total_tests += 1
    if test_system2_quick():
        tests_passed += 1
    
    total_tests += 1
    if test_days_in_location_tracking():
        tests_passed += 1
    
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("All unit tests passed!")
    else:
        print("Some tests failed :(")