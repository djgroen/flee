"""
Unit tests for Individual Agent Analysis Tools
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

from flee_dual_process.individual_agent_analysis import (
    IndividualAgentAnalyzer, AgentTrajectory, MovementPattern
)


class TestIndividualAgentAnalyzer(unittest.TestCase):
    """Test individual agent analyzer functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = IndividualAgentAnalyzer(self.temp_dir, rank=0)
        
        # Create sample data files
        self._create_sample_flee_data()
        self._create_sample_dual_process_data()
        self._create_sample_decision_data()
        self._create_sample_social_data()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        
    def _create_sample_flee_data(self):
        """Create sample Flee agent data."""
        flee_file = Path(self.temp_dir) / "agents.out.0"
        
        with open(flee_file, 'w') as f:
            f.write("#time,agent_id,original_location,current_location,gps_x,gps_y,is_travelling,distance_travelled,places_travelled,distance_moved_this_timestep\n")
            
            # Agent 0-0 trajectory
            f.write("0,0-0,Origin,Origin,0.0,0.0,False,0.0,1,0.0\n")
            f.write("1,0-0,Origin,Town_A,10.0,5.0,True,15.0,2,15.0\n")
            f.write("2,0-0,Origin,Town_A,10.0,5.0,False,15.0,2,0.0\n")
            f.write("3,0-0,Origin,Camp_B,20.0,10.0,True,30.0,3,15.0\n")
            
            # Agent 0-1 trajectory
            f.write("0,0-1,Origin,Origin,0.0,0.0,False,0.0,1,0.0\n")
            f.write("1,0-1,Origin,Origin,0.0,0.0,False,0.0,1,0.0\n")
            f.write("2,0-1,Origin,Town_C,5.0,15.0,True,20.0,2,20.0\n")
            f.write("3,0-1,Origin,Town_C,5.0,15.0,False,20.0,2,0.0\n")
            
    def _create_sample_dual_process_data(self):
        """Create sample dual-process data."""
        dp_file = Path(self.temp_dir) / "agents_dual_process.out.0"
        
        with open(dp_file, 'w') as f:
            f.write("#time,agent_id,cognitive_state,system2_activations,decision_history_length,days_in_current_location,last_connection_update\n")
            
            # Agent 0-0 cognitive data
            f.write("0,0-0,S1,0,0,0,0\n")
            f.write("1,0-0,S2,1,1,1,1\n")
            f.write("2,0-0,S2,1,2,1,1\n")
            f.write("3,0-0,S1,1,3,1,3\n")
            
            # Agent 0-1 cognitive data
            f.write("0,0-1,S1,0,0,0,0\n")
            f.write("1,0-1,S1,0,0,1,0\n")
            f.write("2,0-1,S2,1,1,1,2\n")
            f.write("3,0-1,S2,1,1,1,2\n")
            
    def _create_sample_decision_data(self):
        """Create sample decision data."""
        decision_file = Path(self.temp_dir) / "agent_decisions.0.csv"
        
        with open(decision_file, 'w') as f:
            f.write("time,agent_id,decision_type,cognitive_state,location,destination,movechance,outcome,system2_active,conflict_level,connections,decision_factors,reasoning\n")
            
            f.write("1,0-0,move,S2,Origin,Town_A,0.8,1.0,True,0.7,2,{},High conflict\n")
            f.write("3,0-0,move,S1,Town_A,Camp_B,0.6,1.0,False,0.3,3,{},Seeking safety\n")
            f.write("2,0-1,move,S2,Origin,Town_C,0.9,1.0,True,0.5,1,{},Better opportunities\n")
            
    def _create_sample_social_data(self):
        """Create sample social network data."""
        social_file = Path(self.temp_dir) / "social_network_individual.0.csv"
        
        with open(social_file, 'w') as f:
            f.write("time,agent_id,location,connections,connection_change,network_neighbors,information_shared,information_received\n")
            
            f.write("0,0-0,Origin,0,0,[],0,0\n")
            f.write("1,0-0,Town_A,2,2,[agent1],1,0\n")
            f.write("2,0-0,Town_A,3,1,[agent1;agent2],1,1\n")
            f.write("3,0-0,Camp_B,3,0,[agent1;agent2;agent3],2,1\n")
            
            f.write("0,0-1,Origin,0,0,[],0,0\n")
            f.write("2,0-1,Town_C,1,1,[agent4],0,1\n")
            
    def test_load_flee_agent_data(self):
        """Test loading Flee agent data."""
        success = self.analyzer.load_flee_agent_data()
        
        self.assertTrue(success)
        self.assertIsNotNone(self.analyzer.flee_agent_data)
        self.assertIn('flee_agents', self.analyzer.loaded_data_sources)
        
        # Check data content
        self.assertEqual(len(self.analyzer.flee_agent_data), 8)  # 4 + 4 records
        self.assertIn('0-0', self.analyzer.flee_agent_data['agent_id'].values)
        self.assertIn('0-1', self.analyzer.flee_agent_data['agent_id'].values)
        
    def test_load_dual_process_data(self):
        """Test loading dual-process data."""
        success = self.analyzer.load_dual_process_data()
        
        self.assertTrue(success)
        self.assertIn('dual_process', self.analyzer.loaded_data_sources)
        self.assertIn('decisions', self.analyzer.loaded_data_sources)
        self.assertIn('social_network', self.analyzer.loaded_data_sources)
        
        # Check data content
        self.assertEqual(len(self.analyzer.dual_process_data), 8)
        self.assertEqual(len(self.analyzer.decision_data), 3)
        self.assertEqual(len(self.analyzer.social_network_data), 6)
        
    def test_build_agent_trajectories(self):
        """Test building agent trajectories."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        
        trajectories = self.analyzer.build_agent_trajectories()
        
        self.assertEqual(len(trajectories), 2)  # Two agents
        self.assertIn('0-0', trajectories)
        self.assertIn('0-1', trajectories)
        
        # Check trajectory structure
        agent_0_trajectory = trajectories['0-0']
        self.assertIsInstance(agent_0_trajectory, AgentTrajectory)
        self.assertEqual(len(agent_0_trajectory.trajectory_points), 4)
        self.assertEqual(len(agent_0_trajectory.decisions), 2)
        self.assertGreater(len(agent_0_trajectory.cognitive_transitions), 0)
        
    def test_agent_summary_statistics(self):
        """Test calculation of agent summary statistics."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        trajectories = self.analyzer.build_agent_trajectories()
        
        agent_0_stats = trajectories['0-0'].summary_stats
        
        # Check basic stats
        self.assertEqual(agent_0_stats['total_timesteps'], 4)
        self.assertEqual(agent_0_stats['simulation_duration'], 3)
        self.assertEqual(agent_0_stats['total_distance'], 30.0)
        self.assertEqual(agent_0_stats['unique_locations_visited'], 3)  # Origin, Town_A, Camp_B
        
        # Check cognitive stats
        self.assertGreater(agent_0_stats['s2_proportion'], 0)
        self.assertGreater(agent_0_stats['cognitive_transitions_count'], 0)
        
        # Check decision stats
        self.assertEqual(agent_0_stats['total_decisions'], 2)
        self.assertGreater(agent_0_stats['avg_decision_confidence'], 0)
        
    def test_cognitive_transition_detection(self):
        """Test detection of cognitive state transitions."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        trajectories = self.analyzer.build_agent_trajectories()
        
        agent_0_trajectory = trajectories['0-0']
        transitions = agent_0_trajectory.cognitive_transitions
        
        # Should detect S1->S2 and S2->S1 transitions
        self.assertGreater(len(transitions), 0)
        
        # Check transition structure
        for transition in transitions:
            self.assertIn('time', transition)
            self.assertIn('from_state', transition)
            self.assertIn('to_state', transition)
            self.assertIn(transition['from_state'], ['S1', 'S2'])
            self.assertIn(transition['to_state'], ['S1', 'S2'])
            
    @patch('flee_dual_process.individual_agent_analysis.SKLEARN_AVAILABLE', True)
    @patch('sklearn.cluster.KMeans')
    def test_identify_movement_patterns_with_sklearn(self, mock_kmeans):
        """Test movement pattern identification with sklearn."""
        # Mock sklearn components
        mock_kmeans_instance = Mock()
        mock_kmeans_instance.fit_predict.return_value = np.array([0, 1])
        mock_kmeans.return_value = mock_kmeans_instance
        
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        self.analyzer.build_agent_trajectories()
        
        patterns = self.analyzer.identify_movement_patterns(n_clusters=2)
        
        self.assertEqual(len(patterns), 2)
        self.assertIsInstance(patterns[0], MovementPattern)
        
        # Check pattern structure
        for pattern in patterns:
            self.assertIsNotNone(pattern.pattern_id)
            self.assertIsInstance(pattern.agent_ids, list)
            self.assertIsInstance(pattern.characteristics, dict)
            self.assertIsInstance(pattern.cognitive_profile, dict)
            
    def test_identify_movement_patterns_without_sklearn(self):
        """Test movement pattern identification without sklearn."""
        with patch('flee_dual_process.individual_agent_analysis.SKLEARN_AVAILABLE', False):
            self.analyzer.load_flee_agent_data()
            self.analyzer.load_dual_process_data()
            self.analyzer.build_agent_trajectories()
            
            patterns = self.analyzer.identify_movement_patterns()
            
            # Should use simple heuristic method
            self.assertGreaterEqual(len(patterns), 0)
            
            if patterns:
                self.assertIn(patterns[0].pattern_id, ['high_mobility', 'low_mobility'])
                
    def test_analyze_decision_making_patterns(self):
        """Test decision-making pattern analysis."""
        self.analyzer.load_dual_process_data()
        
        decision_clusters = self.analyzer.analyze_decision_making_patterns()
        
        # Check cluster structure
        expected_clusters = [
            'quick_deciders', 'deliberate_deciders', 'high_confidence_deciders',
            'low_confidence_deciders', 'frequent_movers', 'infrequent_movers'
        ]
        
        for cluster in expected_clusters:
            self.assertIn(cluster, decision_clusters)
            self.assertIsInstance(decision_clusters[cluster], list)
            
        # Should have classified some agents
        total_classified = sum(len(agents) for agents in decision_clusters.values())
        self.assertGreater(total_classified, 0)
        
    def test_compare_individual_vs_aggregate_patterns(self):
        """Test comparison of individual vs aggregate patterns."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        self.analyzer.build_agent_trajectories()
        
        comparison = self.analyzer.compare_individual_vs_aggregate_patterns()
        
        # Check comparison structure
        expected_analyses = ['distance_analysis', 'cognitive_analysis', 'spatial_analysis']
        for analysis in expected_analyses:
            self.assertIn(analysis, comparison)
            
        # Check distance analysis
        distance_analysis = comparison['distance_analysis']
        self.assertIn('individual_mean', distance_analysis)
        self.assertIn('individual_std', distance_analysis)
        self.assertIn('distance_inequality_gini', distance_analysis)
        
        # Gini coefficient should be between 0 and 1
        gini = distance_analysis['distance_inequality_gini']
        self.assertGreaterEqual(gini, 0)
        self.assertLessEqual(gini, 1)
        
    def test_gini_coefficient_calculation(self):
        """Test Gini coefficient calculation."""
        # Test with equal values (should be 0)
        equal_values = [10, 10, 10, 10]
        gini_equal = self.analyzer._calculate_gini_coefficient(equal_values)
        self.assertAlmostEqual(gini_equal, 0, places=2)
        
        # Test with maximum inequality
        max_inequality = [0, 0, 0, 100]
        gini_max = self.analyzer._calculate_gini_coefficient(max_inequality)
        self.assertGreater(gini_max, 0.5)
        
        # Test edge cases
        self.assertEqual(self.analyzer._calculate_gini_coefficient([]), 0)
        self.assertEqual(self.analyzer._calculate_gini_coefficient([5]), 0)
        
    def test_generate_individual_agent_report(self):
        """Test individual agent report generation."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        self.analyzer.build_agent_trajectories()
        
        report = self.analyzer.generate_individual_agent_report('0-0')
        
        # Check report structure
        expected_sections = [
            'agent_id', 'summary_statistics', 'trajectory_analysis',
            'decision_analysis', 'cognitive_analysis', 'social_analysis',
            'comparative_analysis'
        ]
        
        for section in expected_sections:
            self.assertIn(section, report)
            
        self.assertEqual(report['agent_id'], '0-0')
        
        # Check trajectory analysis
        trajectory_analysis = report['trajectory_analysis']
        self.assertIn('movement_velocity', trajectory_analysis)
        self.assertIn('location_patterns', trajectory_analysis)
        self.assertIn('temporal_patterns', trajectory_analysis)
        
        # Check decision analysis
        decision_analysis = report['decision_analysis']
        self.assertGreater(decision_analysis['total_decisions'], 0)
        
    def test_individual_trajectory_analysis(self):
        """Test individual trajectory analysis."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        trajectories = self.analyzer.build_agent_trajectories()
        
        trajectory = trajectories['0-0']
        analysis = self.analyzer._analyze_individual_trajectory(trajectory)
        
        # Check movement velocity analysis
        self.assertIn('movement_velocity', analysis)
        velocity = analysis['movement_velocity']
        self.assertIn('avg_daily_movement', velocity)
        self.assertIn('max_daily_movement', velocity)
        self.assertIn('movement_consistency', velocity)
        
        # Check location patterns
        self.assertIn('location_patterns', analysis)
        location_patterns = analysis['location_patterns']
        self.assertIn('total_location_changes', location_patterns)
        self.assertIn('location_sequence', location_patterns)
        
        # Movement consistency should be between 0 and 1
        consistency = velocity['movement_consistency']
        self.assertGreaterEqual(consistency, 0)
        self.assertLessEqual(consistency, 1)
        
    def test_individual_decision_analysis(self):
        """Test individual decision analysis."""
        self.analyzer.load_dual_process_data()
        trajectories = self.analyzer.build_agent_trajectories()
        
        trajectory = trajectories['0-0']
        analysis = self.analyzer._analyze_individual_decisions(trajectory)
        
        # Check decision analysis structure
        self.assertIn('total_decisions', analysis)
        self.assertIn('decision_types', analysis)
        self.assertIn('cognitive_state_decisions', analysis)
        self.assertIn('confidence_analysis', analysis)
        
        # Should have move decisions
        self.assertIn('move', analysis['decision_types'])
        
        # Should have confidence analysis
        confidence = analysis['confidence_analysis']
        self.assertIn('avg_confidence', confidence)
        self.assertGreater(confidence['avg_confidence'], 0)
        
    def test_individual_cognitive_analysis(self):
        """Test individual cognitive behavior analysis."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        trajectories = self.analyzer.build_agent_trajectories()
        
        trajectory = trajectories['0-0']
        analysis = self.analyzer._analyze_individual_cognitive_behavior(trajectory)
        
        # Check cognitive analysis structure
        self.assertIn('cognitive_transitions', analysis)
        self.assertIn('transition_patterns', analysis)
        self.assertIn('state_durations', analysis)
        
        # Should detect transitions
        self.assertGreater(analysis['cognitive_transitions'], 0)
        
        # Should have transition patterns
        patterns = analysis['transition_patterns']
        self.assertGreater(len(patterns), 0)
        
    def test_individual_social_analysis(self):
        """Test individual social behavior analysis."""
        self.analyzer.load_dual_process_data()
        trajectories = self.analyzer.build_agent_trajectories()
        
        trajectory = trajectories['0-0']
        analysis = self.analyzer._analyze_individual_social_behavior(trajectory)
        
        # Check social analysis structure
        self.assertIn('total_interactions', analysis)
        
        if analysis['total_interactions'] > 0:
            self.assertIn('connection_patterns', analysis)
            self.assertIn('information_sharing', analysis)
            
            # Check connection patterns
            connections = analysis['connection_patterns']
            self.assertIn('max_connections', connections)
            self.assertIn('avg_connections', connections)
            
    def test_agent_population_comparison(self):
        """Test comparison of agent to population."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        self.analyzer.build_agent_trajectories()
        
        comparison = self.analyzer._compare_agent_to_population('0-0')
        
        # Should have comparisons for key metrics
        expected_metrics = ['total_distance', 's2_proportion', 'unique_locations_visited']
        
        for metric in expected_metrics:
            if metric in comparison:
                metric_comparison = comparison[metric]
                self.assertIn('agent_value', metric_comparison)
                self.assertIn('population_mean', metric_comparison)
                self.assertIn('z_score', metric_comparison)
                self.assertIn('percentile', metric_comparison)
                
                # Percentile should be between 0 and 100
                percentile = metric_comparison['percentile']
                self.assertGreaterEqual(percentile, 0)
                self.assertLessEqual(percentile, 100)
                
    def test_export_analysis_results(self):
        """Test exporting analysis results."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.load_dual_process_data()
        self.analyzer.build_agent_trajectories()
        self.analyzer.identify_movement_patterns()
        self.analyzer.analyze_decision_making_patterns()
        
        export_dir = Path(self.temp_dir) / "exports"
        self.analyzer.export_analysis_results(str(export_dir))
        
        # Check that files were created
        expected_files = [
            "movement_patterns.0.json",
            "decision_clusters.0.json", 
            "agent_summaries.0.csv",
            "individual_vs_aggregate.0.json"
        ]
        
        for filename in expected_files:
            file_path = export_dir / filename
            self.assertTrue(file_path.exists(), f"File {filename} was not created")
            
        # Check content of summary CSV
        summary_file = export_dir / "agent_summaries.0.csv"
        df = pd.read_csv(summary_file)
        self.assertEqual(len(df), 2)  # Two agents
        self.assertIn('agent_id', df.columns)
        self.assertIn('total_distance', df.columns)
        
    def test_missing_data_handling(self):
        """Test handling of missing data files."""
        # Test with empty directory
        empty_dir = tempfile.mkdtemp()
        try:
            empty_analyzer = IndividualAgentAnalyzer(empty_dir, rank=0)
            
            # Should handle missing files gracefully
            flee_success = empty_analyzer.load_flee_agent_data()
            self.assertFalse(flee_success)
            
            dp_success = empty_analyzer.load_dual_process_data()
            self.assertFalse(dp_success)
            
            # Should return empty results
            trajectories = empty_analyzer.build_agent_trajectories()
            self.assertEqual(len(trajectories), 0)
            
        finally:
            shutil.rmtree(empty_dir)
            
    def test_invalid_agent_report(self):
        """Test report generation for non-existent agent."""
        self.analyzer.load_flee_agent_data()
        self.analyzer.build_agent_trajectories()
        
        # Request report for non-existent agent
        report = self.analyzer.generate_individual_agent_report('non-existent')
        
        self.assertEqual(len(report), 0)
        
    def test_insufficient_trajectory_data(self):
        """Test handling of agents with insufficient trajectory data."""
        # Create minimal data
        minimal_file = Path(self.temp_dir) / "minimal_agents.out.0"
        with open(minimal_file, 'w') as f:
            f.write("#time,agent_id,original_location,current_location,gps_x,gps_y,is_travelling,distance_travelled,places_travelled,distance_moved_this_timestep\n")
            f.write("0,0-0,Origin,Origin,0.0,0.0,False,0.0,1,0.0\n")  # Only one point
            
        # Rename to standard file
        standard_file = Path(self.temp_dir) / "agents.out.0"
        standard_file.unlink()  # Remove existing file
        minimal_file.rename(standard_file)
        
        analyzer = IndividualAgentAnalyzer(self.temp_dir, rank=0)
        analyzer.load_flee_agent_data()
        trajectories = analyzer.build_agent_trajectories()
        
        # Should still create trajectory but with limited analysis
        self.assertIn('0-0', trajectories)
        
        trajectory = trajectories['0-0']
        analysis = analyzer._analyze_individual_trajectory(trajectory)
        
        # Should handle insufficient data gracefully
        self.assertIn('error', analysis)


class TestAgentTrajectoryDataStructure(unittest.TestCase):
    """Test AgentTrajectory data structure."""
    
    def test_agent_trajectory_creation(self):
        """Test creation of AgentTrajectory objects."""
        trajectory = AgentTrajectory(
            agent_id="test-agent",
            trajectory_points=[
                {'time': 0, 'location': 'A', 'x': 0, 'y': 0},
                {'time': 1, 'location': 'B', 'x': 10, 'y': 5}
            ],
            decisions=[
                {'time': 1, 'decision_type': 'move', 'movechance': 0.8}
            ],
            cognitive_transitions=[
                {'time': 1, 'from_state': 'S1', 'to_state': 'S2'}
            ],
            social_interactions=[
                {'time': 1, 'connections': 2, 'connection_change': 1}
            ],
            summary_stats={'total_distance': 15.0, 'unique_locations': 2}
        )
        
        self.assertEqual(trajectory.agent_id, "test-agent")
        self.assertEqual(len(trajectory.trajectory_points), 2)
        self.assertEqual(len(trajectory.decisions), 1)
        self.assertEqual(len(trajectory.cognitive_transitions), 1)
        self.assertEqual(len(trajectory.social_interactions), 1)
        self.assertEqual(trajectory.summary_stats['total_distance'], 15.0)


class TestMovementPatternDataStructure(unittest.TestCase):
    """Test MovementPattern data structure."""
    
    def test_movement_pattern_creation(self):
        """Test creation of MovementPattern objects."""
        pattern = MovementPattern(
            pattern_id="test_pattern",
            agent_ids=["agent1", "agent2", "agent3"],
            characteristics={"mobility": "high", "avg_distance": 50.0},
            cognitive_profile={"dominant_mode": "S2", "avg_transitions": 3.5},
            spatial_signature={"range": "wide", "unique_locations": 8}
        )
        
        self.assertEqual(pattern.pattern_id, "test_pattern")
        self.assertEqual(len(pattern.agent_ids), 3)
        self.assertEqual(pattern.characteristics["mobility"], "high")
        self.assertEqual(pattern.cognitive_profile["dominant_mode"], "S2")
        self.assertEqual(pattern.spatial_signature["range"], "wide")


if __name__ == '__main__':
    unittest.main()