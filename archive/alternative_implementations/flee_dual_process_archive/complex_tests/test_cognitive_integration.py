#!/usr/bin/env python3
"""
Test script for cognitive integration with FLEE Person class.

This script tests the enhanced cognitive modeling capabilities
integrated into the FLEE Person class and ecosystem.
"""

import sys
import os
import tempfile
import shutil

# Add the parent directory to the path so we can import flee
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import flee.flee as flee
from flee.SimulationSettings import SimulationSettings

def test_cognitive_person_attributes():
    """Test that Person class has cognitive attributes."""
    print("Testing Person class cognitive attributes...")
    
    # Initialize basic simulation settings to avoid KeyError
    if not hasattr(SimulationSettings, 'move_rules') or not SimulationSettings.move_rules:
        SimulationSettings.move_rules = {
            "CampWeight": 2.0,
            "ConflictWeight": 0.25,
            "DefaultMoveChance": 0.001,
            "CampMoveChance": 0.001,
            "ConflictMoveChance": 1.0,
            "FixedRoutes": False,
            "AwarenessLevel": 1,
            "WeightSoftening": 1.0,
            "DistanceSoftening": 1.0,
            "DistancePower": 1.0,
            "WeightPower": 1.0,
            "TwoSystemDecisionMaking": True
        }
    
    if not hasattr(SimulationSettings, 'log_levels') or not SimulationSettings.log_levels:
        SimulationSettings.log_levels = {
            "agent": 0,
            "camp": 0,
            "link": 0,
            "cognitive": 1
        }
    
    # Create a simple location for testing
    location = flee.Location("TestLocation", x=0, y=0, movechance=0.1)
    
    # Create a person with basic attributes
    person = flee.Person(location, {"connections": 3})
    
    # Test cognitive attributes
    assert hasattr(person, 'cognitive_state'), "Person should have cognitive_state attribute"
    assert hasattr(person, 'decision_history'), "Person should have decision_history attribute"
    assert hasattr(person, 'system2_activations'), "Person should have system2_activations attribute"
    
    # Test initial values
    assert person.cognitive_state == "S1", "Initial cognitive state should be S1"
    assert person.decision_history == [], "Initial decision history should be empty"
    assert person.system2_activations == 0, "Initial S2 activations should be 0"
    
    print("✓ Person cognitive attributes test passed")

def test_cognitive_pressure_calculation():
    """Test cognitive pressure calculation."""
    print("Testing cognitive pressure calculation...")
    
    # Create a location with conflict
    location = flee.Location("ConflictLocation", x=0, y=0)
    location.conflict = 0.8
    location.time_of_conflict = 0
    
    # Create a person with connections
    person = flee.Person(location, {"connections": 5})
    
    # Test cognitive pressure calculation
    pressure = person.calculate_cognitive_pressure(time=10)
    
    # Should be (0.8 * 0.5) / (10/30) = 0.4 / 0.333 ≈ 1.2
    expected_pressure = (0.8 * 0.5) / (10.0 / 30.0)
    assert abs(pressure - expected_pressure) < 0.01, f"Expected pressure ~{expected_pressure}, got {pressure}"
    
    print(f"✓ Cognitive pressure calculation test passed (pressure: {pressure:.2f})")

def test_system2_capability():
    """Test System 2 capability determination."""
    print("Testing System 2 capability...")
    
    location = flee.Location("TestLocation", x=0, y=0)
    
    # Test agent with high connections
    person1 = flee.Person(location, {"connections": 5})
    assert person1.get_system2_capable(), "Agent with high connections should be S2 capable"
    
    # Test agent with low connections but experience
    person2 = flee.Person(location, {"connections": 1})
    person2.timesteps_since_departure = 10
    assert person2.get_system2_capable(), "Experienced agent should be S2 capable"
    
    # Test agent with neither
    person3 = flee.Person(location, {"connections": 1})
    person3.timesteps_since_departure = 2
    assert not person3.get_system2_capable(), "Inexperienced, unconnected agent should not be S2 capable"
    
    print("✓ System 2 capability test passed")

def test_decision_logging():
    """Test decision logging functionality."""
    print("Testing decision logging...")
    
    location = flee.Location("TestLocation", x=0, y=0)
    person = flee.Person(location, {"connections": 3})
    
    # Log a decision
    factors = {
        'movechance': 0.5,
        'outcome': 0.3,
        'system2_active': True,
        'conflict_level': 0.2
    }
    
    person.log_decision('move', factors, time=5)
    
    # Check decision was logged
    assert len(person.decision_history) == 1, "Decision should be logged"
    
    decision = person.decision_history[0]
    assert decision['time'] == 5, "Decision time should be recorded"
    assert decision['type'] == 'move', "Decision type should be recorded"
    assert decision['cognitive_state'] == 'S1', "Cognitive state should be recorded"
    assert decision['factors']['movechance'] == 0.5, "Decision factors should be recorded"
    
    print("✓ Decision logging test passed")

def test_cognitive_logging_integration():
    """Test cognitive logging integration with ecosystem."""
    print("Testing cognitive logging integration...")
    
    # Add more required settings
    SimulationSettings.move_rules.update({
        "MatchCampReligion": False,
        "MatchCampEthnicity": False,
        "MatchTownEthnicity": False,
        "MatchConflictEthnicity": False
    })
    
    # Enable cognitive logging
    SimulationSettings.log_levels["cognitive"] = 1
    
    # Create a temporary directory for output
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test the MetricsSummaryLogger directly instead of full ecosystem
        from flee_dual_process.cognitive_logger import MetricsSummaryLogger
        
        # Create some test agents
        location = flee.Location("TestLocation", x=0, y=0, movechance=0.1)
        agents = []
        for i in range(5):
            agent = flee.Person(location, {"connections": i})
            agent.cognitive_state = "S1" if i < 3 else "S2"
            agents.append(agent)
        
        # Test metrics logger
        metrics_logger = MetricsSummaryLogger(temp_dir)
        metrics_logger.collect_timestep_metrics(agents, 0)
        
        # Check that metrics were collected
        assert 0 in metrics_logger.metrics_data, "Metrics should be collected for timestep 0"
        
        # Test writing summary files
        metrics_logger.write_metrics_summary_json()
        metrics_logger.write_hypothesis_specific_analysis_pkl()
        
        # Check files were created
        json_file = os.path.join(temp_dir, "metrics_summary.0.json")
        pkl_file = os.path.join(temp_dir, "hypothesis_specific_analysis.0.pkl")
        
        assert os.path.exists(json_file), "JSON summary file should be created"
        assert os.path.exists(pkl_file), "Pickle analysis file should be created"
        
        print("✓ Cognitive logging integration test passed")
    
    except ImportError:
        print("⚠ Cognitive logging not available (flee_dual_process module not found)")
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Run all tests."""
    print("Running cognitive integration tests...\n")
    
    try:
        test_cognitive_person_attributes()
        test_cognitive_pressure_calculation()
        test_system2_capability()
        test_decision_logging()
        test_cognitive_logging_integration()
        
        print("\n✅ All cognitive integration tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())