#!/usr/bin/env python3
"""
Test script for cognitive tracking functionality.

This script tests the cognitive state tracking, decision logging, and social
connectivity tracking features added to the Flee simulation.
"""

import sys
import os
import tempfile
import shutil

# Add the parent directory to the path so we can import flee
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flee.flee import Person, Location, Ecosystem
from flee.SimulationSettings import SimulationSettings
from flee_dual_process.cognitive_logger import CognitiveStateLogger, DecisionLogger, SocialNetworkLogger


def test_person_cognitive_attributes():
    """Test that Person class has the new cognitive tracking attributes."""
    print("Testing Person cognitive attributes...")
    
    # Create a simple location for testing
    location = Location("TestLocation", x=0.0, y=0.0)
    
    # Create a person
    person = Person(location, {"connections": 0})
    
    # Check that cognitive attributes exist
    assert hasattr(person, 'cognitive_state'), "Person should have cognitive_state attribute"
    assert hasattr(person, 'decision_history'), "Person should have decision_history attribute"
    assert hasattr(person, 'system2_activations'), "Person should have system2_activations attribute"
    
    # Check initial values
    assert person.cognitive_state == "S1", "Initial cognitive state should be S1"
    assert person.decision_history == [], "Initial decision history should be empty"
    assert person.system2_activations == 0, "Initial system2_activations should be 0"
    
    print("✓ Person cognitive attributes test passed")


def test_decision_logging():
    """Test the decision logging functionality."""
    print("Testing decision logging...")
    
    # Create a simple location for testing
    location = Location("TestLocation", x=0.0, y=0.0)
    
    # Create a person
    person = Person(location, {"connections": 0})
    
    # Test logging a decision
    factors = {
        'movechance': 0.5,
        'outcome': 0.3,
        'system2_active': False,
        'conflict_level': 0.2
    }
    
    person.log_decision('move', factors, 10)
    
    # Check that decision was logged
    assert len(person.decision_history) == 1, "Decision should be logged"
    
    decision = person.decision_history[0]
    assert decision['time'] == 10, "Decision time should be recorded"
    assert decision['type'] == 'move', "Decision type should be recorded"
    assert decision['cognitive_state'] == 'S1', "Cognitive state should be recorded"
    assert decision['factors']['movechance'] == 0.5, "Decision factors should be recorded"
    
    print("✓ Decision logging test passed")


def test_cognitive_loggers():
    """Test the cognitive logger classes."""
    print("Testing cognitive loggers...")
    
    # Create temporary directory for test output
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create loggers
        state_logger = CognitiveStateLogger(temp_dir, rank=0)
        decision_logger = DecisionLogger(temp_dir, rank=0)
        social_logger = SocialNetworkLogger(temp_dir, rank=0)
        
        # Create test agents
        location = Location("TestLocation", x=0.0, y=0.0)
        agents = [Person(location, {"connections": i}) for i in range(3)]
        
        # Add some decision history to agents
        for i, agent in enumerate(agents):
            agent.log_decision('test', {'factor': i}, 0)
        
        # Test writing logs
        state_logger.write_cognitive_states_csv(agents, 0)
        decision_logger.write_decision_log_csv(agents, 0)
        social_logger.write_social_network_csv(agents, 0)
        
        # Close loggers
        state_logger.close()
        decision_logger.close()
        social_logger.close()
        
        # Check that files were created
        expected_files = [
            'cognitive_states.out.0',
            'decision_log.out.0',
            'social_network.out.0'
        ]
        
        for filename in expected_files:
            filepath = os.path.join(temp_dir, filename)
            assert os.path.exists(filepath), f"Output file {filename} should exist"
            
            # Check that file has content
            with open(filepath, 'r') as f:
                content = f.read()
                assert len(content) > 0, f"Output file {filename} should have content"
                assert content.startswith('#'), f"Output file {filename} should have header"
        
        print("✓ Cognitive loggers test passed")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


def test_social_connectivity_tracking():
    """Test the social connectivity tracking functionality."""
    print("Testing social connectivity tracking...")
    
    # Create locations with different characteristics
    camp_location = Location("Camp", x=0.0, y=0.0, location_type="camp")
    town_location = Location("Town", x=1.0, y=1.0, location_type="town")
    conflict_location = Location("Conflict", x=2.0, y=2.0, location_type="conflict")
    
    # Set up conflict location
    conflict_location.conflict = 0.8
    
    # Create a person
    person = Person(town_location, {"connections": 5})
    
    # Test social connectivity updates
    initial_connections = person.attributes["connections"]
    
    # Move to camp (should potentially increase connections over time)
    person.update_social_connectivity(camp_location, 10)
    
    # Move to conflict zone (should decrease connections)
    person.update_social_connectivity(conflict_location, 20)
    conflict_connections = person.attributes["connections"]
    
    assert conflict_connections < initial_connections, "Conflict should reduce connections"
    
    print("✓ Social connectivity tracking test passed")


def main():
    """Run all tests."""
    print("Running cognitive tracking tests...\n")
    
    # Initialize simulation settings for testing
    SimulationSettings.log_levels = {"cognitive": 1, "agent": 1, "link": 0, "camp": 0, "conflict": 0, "init": 0}
    
    # Initialize required move_rules settings with correct key names
    SimulationSettings.move_rules = {
        "CampWeight": 2.0,
        "ConflictWeight": 0.25,
        "DefaultMoveChance": 0.001,
        "CampMoveChance": 0.001,
        "ConflictMoveChance": 1.0,
        "IDPCampMoveChance": 0.001,
        "MaxMoveSpeed": 35.0,
        "MaxWalkSpeed": 5.0,
        "MovechancePopBase": 1000,
        "MovechancePopScaleFactor": 0.1,
        "TwoSystemDecisionMaking": True,
        "AwarenessLevel": 1,
        "WeightSoftening": 0.5,
        "DistancePower": 1.0,
        "PruningThreshold": 0.1,
        "FixedRoutes": False,
        "StartOnFoot": False,
        "AvoidShortStints": False,
        "HarvestMonths": []
    }
    
    # Initialize spawn_rules
    SimulationSettings.spawn_rules = {
        "camps_are_sinks": False,
        "take_from_population": False,
        "insert_day0": True,
        "conflict_spawn_decay_interval": 30,
        "conflict_spawn_decay_factor": 0.9,
        "conflict_spawn_decay": [1.0, 0.9, 0.8, 0.7, 0.6]
    }
    
    # Initialize optimisations
    SimulationSettings.optimisations = {
        "hasten": 1
    }
    
    # Initialize farming setting
    SimulationSettings.farming = False
    
    try:
        test_person_cognitive_attributes()
        test_decision_logging()
        test_cognitive_loggers()
        test_social_connectivity_tracking()
        
        print("\n✅ All cognitive tracking tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())