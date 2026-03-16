"""
Unit tests for Individual Agent Tracking System
"""

import unittest
import tempfile
import shutil
import os
import json
import csv
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import numpy as np
import pandas as pd

from flee_dual_process.individual_agent_tracker import (
    IndividualAgentTracker, TrackingConfig, TrackingLevel, StorageFormat,
    AgentSnapshot, AgentDecision, TrackingConfigBuilder,
    create_summary_tracking_config, create_detailed_tracking_config,
    create_full_tracking_config
)


class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, agent_id: str, location_name: str = "TestLocation"):
        self.location = Mock()
        self.location.name = location_name
        self.location.x = 0.0
        self.location.y = 0.0
        self.location.conflict = 0.1
        
        self.attributes = {
            'connections': 3,
            'network_neighbors': ['agent1', 'agent2'],
            'information_shared_count': 1,
            'information_received_count': 2
        }
        
        self.cognitive_state = 'S1'
        self.system2_activations = 0
        self.days_in_current_location = 5
        self.distance_travelled = 10.5
        self.route = ['loc1', 'loc2']
        
        self.decision_history = []
        self.last_decision_factors = {
            'movechance': 0.3,
            'conflict_level': 0.1,
            'system2_active': False
        }


class TestTrackingConfig(unittest.TestCase):
    """Test tracking configuration classes."""
    
    def test_tracking_config_defaults(self):
        """Test default tracking configuration."""
        config = TrackingConfig()
        
        self.assertEqual(config.tracking_level, TrackingLevel.DETAILED)
        self.assertEqual(config.storage_format, StorageFormat.CSV)
        self.assertEqual(config.sampling_rate, 1.0)
        self.assertEqual(config.timestep_interval, 1)
        self.assertTrue(config.compression)
        self.assertTrue(config.track_decisions)
        self.assertTrue(config.track_trajectories)
        self.assertTrue(config.validate_data)
        
    def test_tracking_config_builder(self):
        """Test tracking configuration builder."""
        config = (TrackingConfigBuilder()
                 .set_tracking_level(TrackingLevel.FULL)
                 .set_storage_format(StorageFormat.HDF5)
                 .set_sampling_rate(0.5)
                 .set_memory_limit(2000)
                 .enable_compression(False)
                 .set_timestep_interval(5)
                 .build())
        
        self.assertEqual(config.tracking_level, TrackingLevel.FULL)
        self.assertEqual(config.storage_format, StorageFormat.HDF5)
        self.assertEqual(config.sampling_rate, 0.5)
        self.assertEqual(config.max_memory_mb, 2000)
        self.assertFalse(config.compression)
        self.assertEqual(config.timestep_interval, 5)
        
    def test_invalid_sampling_rate(self):
        """Test invalid sampling rate raises error."""
        builder = TrackingConfigBuilder()
        
        with self.assertRaises(ValueError):
            builder.set_sampling_rate(-0.1)
            
        with self.assertRaises(ValueError):
            builder.set_sampling_rate(1.5)
            
    def test_convenience_config_functions(self):
        """Test convenience configuration functions."""
        summary_config = create_summary_tracking_config("/tmp")
        self.assertEqual(summary_config.tracking_level, TrackingLevel.SUMMARY)
        self.assertEqual(summary_config.sampling_rate, 0.1)
        
        detailed_config = create_detailed_tracking_config("/tmp", "parquet")
        self.assertEqual(detailed_config.tracking_level, TrackingLevel.DETAILED)
        self.assertEqual(detailed_config.storage_format, StorageFormat.PARQUET)
        
        full_config = create_full_tracking_config("/tmp", "hdf5", 0.2)
        self.assertEqual(full_config.tracking_level, TrackingLevel.FULL)
        self.assertEqual(full_config.sampling_rate, 0.2)
        
    def test_flee_compatible_config(self):
        """Test Flee-compatible configuration function."""
        from flee_dual_process.individual_agent_tracker import create_flee_compatible_config
        
        # No Flee logging - should use full tracking
        config0 = create_flee_compatible_config("/tmp", 0)
        self.assertEqual(config0.tracking_level, TrackingLevel.FULL)
        self.assertEqual(config0.sampling_rate, 1.0)
        
        # Basic Flee logging - should use detailed tracking
        config1 = create_flee_compatible_config("/tmp", 1)
        self.assertEqual(config1.tracking_level, TrackingLevel.DETAILED)
        
        # Advanced Flee logging - should use summary
        config2 = create_flee_compatible_config("/tmp", 2)
        self.assertEqual(config2.tracking_level, TrackingLevel.SUMMARY)


class TestAgentDataStructures(unittest.TestCase):
    """Test agent data structures."""
    
    def test_agent_snapshot_creation(self):
        """Test agent snapshot data structure."""
        snapshot = AgentSnapshot(
            time=10,
            agent_id="test-agent-1",
            location="TestLocation",
            cognitive_state="S2",
            connections=5,
            system2_activations=2,
            days_in_location=3,
            conflict_level=0.7,
            distance_travelled=25.5,
            route_length=4,
            decision_factors={'test': 'value'},
            attributes={'attr': 'value'}
        )
        
        self.assertEqual(snapshot.time, 10)
        self.assertEqual(snapshot.agent_id, "test-agent-1")
        self.assertEqual(snapshot.cognitive_state, "S2")
        self.assertEqual(snapshot.connections, 5)
        
    def test_agent_decision_creation(self):
        """Test agent decision data structure."""
        decision = AgentDecision(
            time=5,
            agent_id="test-agent-1",
            decision_type="move",
            cognitive_state="S1",
            location="Origin",
            destination="Camp",
            movechance=0.8,
            outcome=1.0,
            system2_active=False,
            conflict_level=0.9,
            connections=2,
            decision_factors={'urgency': 'high'},
            reasoning="High conflict level"
        )
        
        self.assertEqual(decision.time, 5)
        self.assertEqual(decision.decision_type, "move")
        self.assertEqual(decision.movechance, 0.8)
        self.assertEqual(decision.reasoning, "High conflict level")


class TestIndividualAgentTracker(unittest.TestCase):
    """Test individual agent tracker functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            sampling_rate=1.0,
            timestep_interval=1
        )
        self.tracker = IndividualAgentTracker(self.config, rank=0)
        
    def tearDown(self):
        """Clean up test environment."""
        self.tracker.close()
        shutil.rmtree(self.temp_dir)
        
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        agents = [MockAgent(f"agent-{i}") for i in range(5)]
        
        self.tracker.initialize(agents)
        
        self.assertTrue(self.tracker.initialized)
        self.assertEqual(len(self.tracker.tracked_agents), 5)
        
    def test_agent_sampling(self):
        """Test agent sampling functionality."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            sampling_rate=0.5
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent(f"agent-{i}") for i in range(10)]
        
        # Set random seed for reproducible sampling
        np.random.seed(42)
        tracker.initialize(agents)
        
        # Should track approximately half the agents
        self.assertGreater(len(tracker.tracked_agents), 0)
        self.assertLessEqual(len(tracker.tracked_agents), 10)
        
        tracker.close()
        
    def test_summary_level_tracking(self):
        """Test summary level tracking."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.SUMMARY,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent(f"agent-{i}") for i in range(3)]
        agents[1].cognitive_state = 'S2'
        
        tracker.track_agents(agents, time=0)
        tracker.track_agents(agents, time=1)
        
        # Check summary data was collected
        self.assertTrue(hasattr(tracker, 'summary_data'))
        self.assertEqual(len(tracker.summary_data), 2)
        
        summary = tracker.summary_data[0]
        self.assertEqual(summary['total_tracked_agents'], 3)
        self.assertIn('cognitive_state_distribution', summary)
        
        tracker.close()
        
    def test_detailed_level_tracking(self):
        """Test detailed level tracking."""
        agents = [MockAgent(f"agent-{i}") for i in range(2)]
        
        # Add decision history
        agents[0].decision_history = [{
            'time': 0,
            'type': 'move',
            'cognitive_state': 'S1',
            'location': 'TestLocation',
            'factors': {'movechance': 0.5},
            'connections': 3
        }]
        
        self.tracker.track_agents(agents, time=0)
        
        # Should have collected snapshots and decisions
        self.assertGreater(len(self.tracker.agent_snapshots), 0)
        self.assertGreater(len(self.tracker.agent_decisions), 0)
        
    def test_full_level_tracking(self):
        """Test full level tracking."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.FULL,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            track_trajectories=True
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent("agent-0")]
        
        tracker.track_agents(agents, time=0)
        tracker.track_agents(agents, time=1)
        
        # Should have trajectory data
        self.assertIn("0-0", tracker.trajectory_data)
        self.assertEqual(len(tracker.trajectory_data["0-0"]), 2)
        
        tracker.close()
        
    def test_timestep_interval_filtering(self):
        """Test timestep interval filtering."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            timestep_interval=5
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent("agent-0")]
        
        # Track at various timesteps
        for time in range(10):
            tracker.track_agents(agents, time)
            
        # Should only have data for timesteps 0 and 5
        expected_times = {0, 5}
        actual_times = {snapshot.time for snapshot in tracker.agent_snapshots}
        self.assertEqual(actual_times, expected_times)
        
        tracker.close()
        
    def test_csv_output_generation(self):
        """Test CSV output file generation."""
        agents = [MockAgent("agent-0")]
        agents[0].decision_history = [{
            'time': 0,
            'type': 'move',
            'cognitive_state': 'S1',
            'location': 'TestLocation',
            'factors': {'movechance': 0.3},
            'connections': 3
        }]
        
        self.tracker.track_agents(agents, time=0)
        self.tracker.close()
        
        # Check CSV files were created
        trajectory_file = Path(self.temp_dir) / "agent_trajectories.0.csv"
        decision_file = Path(self.temp_dir) / "agent_decisions.0.csv"
        social_file = Path(self.temp_dir) / "social_network_individual.0.csv"
        
        self.assertTrue(trajectory_file.exists())
        self.assertTrue(decision_file.exists())
        self.assertTrue(social_file.exists())
        
        # Check CSV content
        with open(trajectory_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertIn('time', header)
            self.assertIn('agent_id', header)
            self.assertIn('cognitive_state', header)
            
    @patch('flee_dual_process.individual_agent_tracker.h5py')
    def test_hdf5_storage_format(self, mock_h5py):
        """Test HDF5 storage format."""
        # Mock HDF5 availability
        mock_file = MagicMock()
        mock_h5py.File.return_value = mock_file
        
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.HDF5,
            output_dir=self.temp_dir
        )
        
        with patch('flee_dual_process.individual_agent_tracker.HDF5_AVAILABLE', True):
            tracker = IndividualAgentTracker(config, rank=0)
            
            agents = [MockAgent("agent-0")]
            tracker.track_agents(agents, time=0)
            tracker.close()
            
            # Verify HDF5 file operations were called
            mock_h5py.File.assert_called_once()
            
    def test_memory_management(self):
        """Test memory management and flushing."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.FULL,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            max_memory_mb=0.001  # Very low limit to trigger flushing
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent(f"agent-{i}") for i in range(5)]
        
        # Track multiple timesteps to trigger memory limit
        for time in range(10):
            tracker.track_agents(agents, time)
            
        # Should have triggered flushes
        self.assertGreater(tracker.last_flush_time, 0)
        
        tracker.close()
        
    def test_data_validation(self):
        """Test data validation functionality."""
        agents = [MockAgent("agent-0")]
        
        # Create invalid data
        self.tracker.agent_snapshots.append(AgentSnapshot(
            time=-1,  # Invalid time
            agent_id="test",
            location="",  # Empty location
            cognitive_state="S1",
            connections=-5,  # Invalid connections
            system2_activations=0,
            days_in_location=0,
            conflict_level=0.0,
            distance_travelled=0.0,
            route_length=0,
            decision_factors={},
            attributes={}
        ))
        
        errors = self.tracker.validate_data_integrity()
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Invalid time" in error for error in errors))
        self.assertTrue(any("Invalid connections" in error for error in errors))
        
    def test_tracking_statistics(self):
        """Test tracking statistics generation."""
        agents = [MockAgent(f"agent-{i}") for i in range(3)]
        
        self.tracker.track_agents(agents, time=0)
        
        stats = self.tracker.get_tracking_statistics()
        
        self.assertEqual(stats['tracking_level'], 'detailed')
        self.assertEqual(stats['storage_format'], 'csv')
        self.assertEqual(stats['tracked_agents_count'], 3)
        self.assertEqual(stats['sampling_rate'], 1.0)
        self.assertGreaterEqual(stats['snapshots_collected'], 0)
        
    def test_social_network_tracking(self):
        """Test social network change tracking."""
        agents = [MockAgent("agent-0")]
        
        # Track initial state
        self.tracker.track_agents(agents, time=0)
        
        # Change connections
        agents[0].attributes['connections'] = 5
        self.tracker.track_agents(agents, time=1)
        
        # Should have recorded the connection change
        social_events = [event for event in self.tracker.social_network_data 
                        if event['connection_change'] != 0]
        self.assertGreater(len(social_events), 0)
        
    def test_trajectory_continuity_validation(self):
        """Test trajectory continuity validation."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.FULL,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            track_trajectories=True
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        # Create non-sequential trajectory data
        tracker.trajectory_data["test-agent"] = [
            {'time': 5, 'location': 'A'},
            {'time': 2, 'location': 'B'},  # Out of order
            {'time': 8, 'location': 'C'}
        ]
        
        errors = tracker.validate_data_integrity()
        
        self.assertTrue(any("Non-sequential trajectory" in error for error in errors))
        
        tracker.close()
        
    def test_agent_state_change_detection(self):
        """Test detection of agent state changes."""
        agents = [MockAgent("agent-0")]
        
        # Track initial state
        self.tracker.track_agents(agents, time=0)
        
        # Change cognitive state
        agents[0].cognitive_state = 'S2'
        self.tracker.track_agents(agents, time=1)
        
        # Should detect state change and create snapshot
        s2_snapshots = [s for s in self.tracker.agent_snapshots 
                       if s.cognitive_state == 'S2']
        self.assertGreater(len(s2_snapshots), 0)
        
    def test_decision_extraction(self):
        """Test decision extraction from agent history."""
        agents = [MockAgent("agent-0")]
        
        # Add multiple decisions
        agents[0].decision_history = [
            {
                'time': 0,
                'type': 'move',
                'cognitive_state': 'S1',
                'location': 'Origin',
                'destination': 'Camp',
                'factors': {'movechance': 0.8, 'system2_active': False},
                'connections': 2,
                'reasoning': 'High conflict'
            },
            {
                'time': 0,
                'type': 'stay',
                'cognitive_state': 'S1',
                'location': 'Origin',
                'factors': {'movechance': 0.2},
                'connections': 2
            }
        ]
        
        self.tracker.track_agents(agents, time=0)
        
        # Should extract both decisions
        self.assertEqual(len(self.tracker.agent_decisions), 2)
        
        move_decision = next(d for d in self.tracker.agent_decisions 
                           if d.decision_type == 'move')
        self.assertEqual(move_decision.destination, 'Camp')
        self.assertEqual(move_decision.reasoning, 'High conflict')
        
    def test_movement_vector_calculation(self):
        """Test movement vector calculation."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.FULL,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            track_trajectories=True
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent("agent-0")]
        agents[0].location.x = 0.0
        agents[0].location.y = 0.0
        
        # Track initial position
        tracker.track_agents(agents, time=0)
        
        # Move agent
        agents[0].location.x = 5.0
        agents[0].location.y = 3.0
        tracker.track_agents(agents, time=1)
        
        # Check movement vector
        trajectory = tracker.trajectory_data["0-0"]
        self.assertEqual(len(trajectory), 2)
        
        # First point should have zero movement
        self.assertEqual(trajectory[0]['movement_vector'], (0.0, 0.0))
        
        # Second point should have movement vector
        self.assertEqual(trajectory[1]['movement_vector'], (5.0, 3.0))
        
        tracker.close()
        
    def test_flee_integration(self):
        """Test integration with Flee's existing agent logging."""
        agents = [MockAgent("agent-0")]
        
        # Add dual-process specific attributes
        agents[0].cognitive_state = 'S2'
        agents[0].system2_activations = 3
        agents[0].decision_history = [{'time': 0, 'type': 'move'}]
        agents[0].days_in_current_location = 5
        agents[0].last_connection_update = 2
        
        self.tracker.track_agents(agents, time=0)
        self.tracker.integrate_with_flee_agent_logs(agents, time=0)
        self.tracker.close()
        
        # Check that Flee integration file was created
        integration_file = Path(self.temp_dir) / "agents_dual_process.out.0"
        self.assertTrue(integration_file.exists())
        
        # Check integration guide was created
        guide_file = Path(self.temp_dir) / "flee_integration_guide.0.md"
        self.assertTrue(guide_file.exists())
        
        # Verify integration file content
        with open(integration_file, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 1)  # Header + data
            self.assertIn('cognitive_state', lines[0])
            self.assertIn('S2', lines[1])


class TestStorageFormats(unittest.TestCase):
    """Test different storage formats."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        
    def test_csv_storage_format(self):
        """Test CSV storage format."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent("agent-0")]
        tracker.track_agents(agents, time=0)
        tracker.close()
        
        # Verify CSV files exist and have content
        csv_files = list(Path(self.temp_dir).glob("*.csv"))
        self.assertGreater(len(csv_files), 0)
        
    @patch('flee_dual_process.individual_agent_tracker.PARQUET_AVAILABLE', True)
    @patch('pandas.DataFrame.to_parquet')
    def test_parquet_storage_format(self, mock_to_parquet):
        """Test Parquet storage format."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.PARQUET,
            output_dir=self.temp_dir,
            compression=True
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent("agent-0")]
        tracker.track_agents(agents, time=0)
        tracker.flush_data()  # Force flush to trigger Parquet write
        
        # Verify Parquet write was called
        mock_to_parquet.assert_called()
        
        tracker.close()
        
    def test_unsupported_storage_format(self):
        """Test handling of unsupported storage formats."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.HDF5,
            output_dir=self.temp_dir
        )
        
        # Mock HDF5 as unavailable
        with patch('flee_dual_process.individual_agent_tracker.HDF5_AVAILABLE', False):
            tracker = IndividualAgentTracker(config, rank=0)
            
            agents = [MockAgent("agent-0")]
            
            # Should raise ImportError for unavailable HDF5
            with self.assertRaises(ImportError):
                tracker.track_agents(agents, time=0)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        
    def test_large_agent_population(self):
        """Test tracking with large agent population."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.SUMMARY,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir,
            sampling_rate=0.01  # Sample 1% of agents
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        # Create large population
        agents = [MockAgent(f"agent-{i}") for i in range(1000)]
        
        tracker.track_agents(agents, time=0)
        tracker.close()
        
        # Should have sampled approximately 10 agents
        self.assertLessEqual(len(tracker.tracked_agents), 50)  # Allow some variance
        
    def test_agents_with_missing_attributes(self):
        """Test handling of agents with missing attributes."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        # Create agent with minimal attributes
        agent = Mock()
        agent.location = Mock()
        agent.location.name = "TestLocation"
        agent.attributes = {}  # Empty attributes
        
        agents = [agent]
        
        # Should handle missing attributes gracefully
        tracker.track_agents(agents, time=0)
        
        self.assertGreater(len(tracker.agent_snapshots), 0)
        
        tracker.close()
        
    def test_agents_removed_from_simulation(self):
        """Test handling of agents removed from simulation."""
        config = TrackingConfig(
            tracking_level=TrackingLevel.DETAILED,
            storage_format=StorageFormat.CSV,
            output_dir=self.temp_dir
        )
        tracker = IndividualAgentTracker(config, rank=0)
        
        agents = [MockAgent("agent-0")]
        
        # Track initially
        tracker.track_agents(agents, time=0)
        
        # Remove agent from simulation
        agents[0].location = None
        tracker.track_agents(agents, time=1)
        
        # Should handle removed agents gracefully
        # Only initial snapshot should exist
        self.assertEqual(len(tracker.agent_snapshots), 1)
        
        tracker.close()
        
    def test_concurrent_tracking_multiple_ranks(self):
        """Test concurrent tracking with multiple MPI ranks."""
        configs = [
            TrackingConfig(
                tracking_level=TrackingLevel.DETAILED,
                storage_format=StorageFormat.CSV,
                output_dir=self.temp_dir
            ) for _ in range(3)
        ]
        
        trackers = [IndividualAgentTracker(config, rank=i) 
                   for i, config in enumerate(configs)]
        
        # Each rank tracks different agents
        for i, tracker in enumerate(trackers):
            agents = [MockAgent(f"agent-{j}") for j in range(2)]
            tracker.track_agents(agents, time=0)
            tracker.close()
            
        # Should create separate files for each rank
        csv_files = list(Path(self.temp_dir).glob("*.csv"))
        rank_files = {int(f.name.split('.')[1]) for f in csv_files}
        
        self.assertEqual(rank_files, {0, 1, 2})


if __name__ == '__main__':
    unittest.main()