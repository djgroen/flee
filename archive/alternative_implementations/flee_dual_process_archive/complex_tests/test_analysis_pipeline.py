"""
Unit Tests for Analysis Pipeline System

Tests for movement metrics calculation, cognitive state analysis,
and comparative analysis methods.
"""

import unittest
import tempfile
import shutil
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from .analysis_pipeline import AnalysisPipeline, ExperimentResults
    from .utils import CSVUtils
except ImportError:
    from analysis_pipeline import AnalysisPipeline, ExperimentResults
    from utils import CSVUtils


class TestAnalysisPipeline(unittest.TestCase):
    """Test cases for AnalysisPipeline class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = os.path.join(self.temp_dir, "results")
        self.analysis_dir = os.path.join(self.temp_dir, "analysis")
        
        os.makedirs(self.results_dir)
        
        # Create test pipeline
        self.pipeline = AnalysisPipeline(self.results_dir, self.analysis_dir)
        
        # Create sample experiment directory structure
        self.exp_dir = os.path.join(self.results_dir, "test_experiment_001")
        self.create_sample_experiment_data()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def create_sample_experiment_data(self):
        """Create sample experiment data for testing."""
        # Create directory structure
        os.makedirs(os.path.join(self.exp_dir, "output"))
        os.makedirs(os.path.join(self.exp_dir, "input"))
        os.makedirs(os.path.join(self.exp_dir, "metadata"))
        
        # Create sample movement data (out.csv) with header comment
        movement_data = pd.DataFrame({
            'day': [0, 1, 2, 3, 4, 5] * 3,
            'location': ['Town_A'] * 6 + ['Camp_B'] * 6 + ['Camp_C'] * 6,
            'refugees': [100, 80, 60, 40, 20, 10, 0, 20, 40, 60, 80, 90, 0, 0, 0, 0, 0, 10],
            'total_refugees': [100] * 18
        })
        # Write with header comment for Flee compatibility
        with open(os.path.join(self.exp_dir, "output", "out.csv"), 'w') as f:
            f.write('#day,location,refugees,total_refugees\n')
            movement_data.to_csv(f, index=False, header=False)
        
        # Create sample cognitive states data with header comment
        cognitive_data = pd.DataFrame({
            'day': [0, 1, 2, 3, 4, 5] * 4,
            'agent_id': ['0-1'] * 6 + ['0-2'] * 6 + ['0-3'] * 6 + ['0-4'] * 6,
            'cognitive_state': ['S1', 'S1', 'S2', 'S2', 'S1', 'S1'] * 4,
            'location': ['Town_A', 'Town_A', 'Town_A', 'Camp_B', 'Camp_B', 'Camp_B'] * 4,
            'connections': [0, 1, 2, 3, 2, 1] * 4,
            'system2_activations': [0, 0, 1, 1, 1, 1] * 4,
            'days_in_location': [1, 2, 3, 1, 2, 3] * 4,
            'conflict_level': [0.1, 0.3, 0.7, 0.8, 0.5, 0.2] * 4
        })
        # Write with header comment
        with open(os.path.join(self.exp_dir, "output", "cognitive_states.out.0"), 'w') as f:
            f.write('#day,agent_id,cognitive_state,location,connections,system2_activations,days_in_location,conflict_level\n')
            cognitive_data.to_csv(f, index=False, header=False)
        
        # Create sample decision log data with header comment
        decision_data = pd.DataFrame({
            'day': [1, 2, 3, 4] * 2,
            'agent_id': ['0-1'] * 4 + ['0-2'] * 4,
            'decision_type': ['move', 'stay', 'move', 'stay'] * 2,
            'cognitive_state': ['S1', 'S2', 'S2', 'S1'] * 2,
            'location': ['Town_A', 'Town_A', 'Camp_B', 'Camp_B'] * 2,
            'movechance': [0.8, 0.2, 0.9, 0.1] * 2,
            'outcome': [1, 0, 1, 0] * 2,
            'system2_active': [False, True, True, False] * 2,
            'conflict_level': [0.3, 0.7, 0.8, 0.5] * 2,
            'connections': [1, 2, 3, 2] * 2
        })
        # Write with header comment
        with open(os.path.join(self.exp_dir, "output", "decision_log.out.0"), 'w') as f:
            f.write('#day,agent_id,decision_type,cognitive_state,location,movechance,outcome,system2_active,conflict_level,connections\n')
            decision_data.to_csv(f, index=False, header=False)
        
        # Create sample locations data for distance calculations
        locations_data = [
            {'name': 'Town_A', 'region': 'Region1', 'country': 'Country1', 
             'lat': 10.0, 'lon': 20.0, 'location_type': 'town', 'conflict_date': '', 'pop/cap': 1000},
            {'name': 'Camp_B', 'region': 'Region1', 'country': 'Country1', 
             'lat': 11.0, 'lon': 21.0, 'location_type': 'camp', 'conflict_date': '', 'pop/cap': 5000},
            {'name': 'Camp_C', 'region': 'Region1', 'country': 'Country1', 
             'lat': 12.0, 'lon': 22.0, 'location_type': 'camp', 'conflict_date': '', 'pop/cap': 3000}
        ]
        CSVUtils.write_locations_csv(locations_data, os.path.join(self.exp_dir, "input", "locations.csv"))
        
        # Create sample metadata
        metadata = {
            'experiment_id': 'test_experiment_001',
            'timestamp': '2024-01-01T00:00:00',
            'configuration': {
                'cognitive_mode': 'dual_process',
                'topology_type': 'linear',
                'scenario_type': 'spike',
                'simulation_params': {
                    'move_rules': {
                        'two_system_decision_making': True,
                        'average_social_connectivity': 3.0,
                        'awareness_level': 2
                    }
                }
            }
        }
        with open(os.path.join(self.exp_dir, "metadata", "experiment_metadata.json"), 'w') as f:
            json.dump(metadata, f)
    
    def test_initialization(self):
        """Test pipeline initialization."""
        self.assertEqual(str(self.pipeline.results_directory), self.results_dir)
        self.assertEqual(str(self.pipeline.output_directory), self.analysis_dir)
        self.assertTrue(os.path.exists(self.analysis_dir))
    
    def test_load_experiment_data(self):
        """Test loading experiment data."""
        results = self.pipeline.load_experiment_data(self.exp_dir)
        
        self.assertIsInstance(results, ExperimentResults)
        self.assertEqual(results.experiment_id, "test_experiment_001")
        self.assertIsNotNone(results.movement_data)
        self.assertIsNotNone(results.cognitive_states)
        self.assertIsNotNone(results.decision_log)
        
        # Check data shapes
        self.assertEqual(len(results.movement_data), 18)
        self.assertEqual(len(results.cognitive_states), 24)
        self.assertEqual(len(results.decision_log), 8)
    
    def test_calculate_movement_metrics(self):
        """Test movement metrics calculation."""
        metrics = self.pipeline.calculate_movement_metrics(self.exp_dir)
        
        self.assertIn('movement_metrics', metrics)
        movement_metrics = metrics['movement_metrics']
        
        # Check timing metrics
        self.assertIn('timing', movement_metrics)
        timing = movement_metrics['timing']
        self.assertIn('simulation_duration', timing)
        self.assertEqual(timing['simulation_duration']['total_days'], 6)
        
        # Check destination metrics
        self.assertIn('destinations', movement_metrics)
        destinations = movement_metrics['destinations']
        self.assertIn('distribution', destinations)
        self.assertIn('concentration', destinations)
        self.assertIn('entropy', destinations)
        
        # Check flow metrics
        self.assertIn('flows', movement_metrics)
        
        # Check temporal patterns
        self.assertIn('temporal_patterns', movement_metrics)
    
    def test_analyze_cognitive_transitions(self):
        """Test cognitive state analysis."""
        metrics = self.pipeline.analyze_cognitive_transitions(self.exp_dir)
        
        self.assertIn('cognitive_analysis', metrics)
        cognitive_analysis = metrics['cognitive_analysis']
        
        # Check state distribution
        self.assertIn('state_distribution', cognitive_analysis)
        state_dist = cognitive_analysis['state_distribution']
        self.assertIn('overall', state_dist)
        self.assertIn('state_counts', state_dist['overall'])
        
        # Check transitions
        self.assertIn('transitions', cognitive_analysis)
        transitions = cognitive_analysis['transitions']
        self.assertIn('overall', transitions)
        
        # Check durations
        self.assertIn('durations', cognitive_analysis)
        
        # Check triggers
        self.assertIn('triggers', cognitive_analysis)
        
        # Check social connectivity
        self.assertIn('social_connectivity', cognitive_analysis)
    
    def test_compare_cognitive_modes(self):
        """Test cognitive mode comparison."""
        # Create a second experiment for comparison
        exp_dir2 = os.path.join(self.results_dir, "test_experiment_002")
        shutil.copytree(self.exp_dir, exp_dir2)
        
        # Modify metadata for different cognitive mode
        metadata_file = os.path.join(exp_dir2, "metadata", "experiment_metadata.json")
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        metadata['experiment_id'] = 'test_experiment_002'
        metadata['configuration']['cognitive_mode'] = 's1_only'
        metadata['configuration']['simulation_params']['move_rules']['two_system_decision_making'] = False
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Compare experiments
        comparison = self.pipeline.compare_cognitive_modes([self.exp_dir, exp_dir2])
        
        self.assertIn('cognitive_modes', comparison)
        self.assertIn('movement_comparison', comparison)
        self.assertIn('cognitive_comparison', comparison)
        self.assertIn('statistical_tests', comparison)
        self.assertIn('effect_sizes', comparison)
        
        # Check cognitive modes were extracted correctly
        cognitive_modes = comparison['cognitive_modes']
        self.assertEqual(len(cognitive_modes), 2)
        self.assertIn('dual_process', cognitive_modes.values())
        self.assertIn('s1_only', cognitive_modes.values())
    
    def test_get_experiment_list(self):
        """Test getting list of experiments."""
        exp_list = self.pipeline.get_experiment_list()
        
        self.assertEqual(len(exp_list), 1)
        self.assertIn(self.exp_dir, exp_list)
    
    def test_process_experiment(self):
        """Test complete experiment processing."""
        results = self.pipeline.process_experiment(self.exp_dir)
        
        self.assertIsInstance(results, ExperimentResults)
        self.assertIn('movement_metrics', results.metrics)
        self.assertIn('cognitive_analysis', results.metrics)
        self.assertIsNotNone(results.summary_statistics)
        
        # Check that results were saved
        exp_output_dir = os.path.join(self.analysis_dir, "test_experiment_001")
        self.assertTrue(os.path.exists(exp_output_dir))
        self.assertTrue(os.path.exists(os.path.join(exp_output_dir, "metrics.json")))
        self.assertTrue(os.path.exists(os.path.join(exp_output_dir, "summary_statistics.json")))
    
    def test_missing_data_handling(self):
        """Test handling of missing data files."""
        # Create experiment directory without cognitive states
        exp_dir_minimal = os.path.join(self.results_dir, "minimal_experiment")
        os.makedirs(os.path.join(exp_dir_minimal, "output"))
        
        # Only create movement data with header comment
        movement_data = pd.DataFrame({
            'day': [0, 1, 2],
            'location': ['Town_A', 'Camp_B', 'Camp_C'],
            'refugees': [100, 50, 25]
        })
        with open(os.path.join(exp_dir_minimal, "output", "out.csv"), 'w') as f:
            f.write('#day,location,refugees\n')
            movement_data.to_csv(f, index=False, header=False)
        
        # Should load successfully with warnings
        results = self.pipeline.load_experiment_data(exp_dir_minimal)
        
        self.assertIsNotNone(results.movement_data)
        self.assertIsNone(results.cognitive_states)
        self.assertIsNone(results.decision_log)
    
    def test_cache_functionality(self):
        """Test data caching functionality."""
        # Load data twice
        results1 = self.pipeline.load_experiment_data(self.exp_dir)
        results2 = self.pipeline.load_experiment_data(self.exp_dir)
        
        # Should be the same object (cached)
        self.assertIs(results1, results2)
        
        # Clear cache and load again
        self.pipeline.clear_cache()
        results3 = self.pipeline.load_experiment_data(self.exp_dir)
        
        # Should be different object (not cached)
        self.assertIsNot(results1, results3)
    
    def test_statistical_calculations(self):
        """Test statistical calculation methods."""
        # Test concentration metrics
        proportions = pd.Series([0.5, 0.3, 0.2])
        concentration = self.pipeline._calculate_concentration_metrics(proportions)
        
        self.assertIn('gini_coefficient', concentration)
        self.assertIn('herfindahl_hirschman_index', concentration)
        self.assertIn('concentration_ratio_1', concentration)
        
        # Test Cohen's d calculation
        group1 = [1, 2, 3, 4, 5]
        group2 = [3, 4, 5, 6, 7]
        cohens_d = self.pipeline._calculate_cohens_d(group1, group2)
        
        self.assertIsInstance(cohens_d, float)
        self.assertAlmostEqual(abs(cohens_d), 1.26, places=1)  # Expected value for this data
    
    def test_haversine_distance(self):
        """Test haversine distance calculation."""
        coord1 = (10.0, 20.0)
        coord2 = (11.0, 21.0)
        
        distance = self.pipeline._calculate_haversine_distance(coord1, coord2)
        
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
        self.assertLess(distance, 200)  # Should be reasonable distance in km
    
    def test_nested_metric_extraction(self):
        """Test nested metric extraction."""
        metrics = {
            'level1': {
                'level2': {
                    'value': 42
                }
            }
        }
        
        # Valid path
        value = self.pipeline._get_nested_metric(metrics, 'level1.level2.value')
        self.assertEqual(value, 42)
        
        # Invalid path
        value = self.pipeline._get_nested_metric(metrics, 'level1.nonexistent.value')
        self.assertIsNone(value)
    
    def test_multiple_comparison_corrections(self):
        """Test multiple comparison corrections."""
        # Create mock comparison results with p-values
        comparison_results = {
            'statistical_tests': {
                'test1': {
                    'subtest1': {'p_value': 0.01},
                    'subtest2': {'p_value': 0.03}
                },
                'test2': {
                    'subtest3': {'p_value': 0.04}
                }
            }
        }
        
        corrected = self.pipeline._apply_multiple_comparison_corrections(comparison_results)
        
        self.assertIn('bonferroni', corrected)
        self.assertIn('fdr_bh', corrected)
        self.assertIn('original_p_values', corrected)
        
        # Check that corrections were applied
        bonferroni = corrected['bonferroni']
        self.assertIn('corrected_alpha', bonferroni)
        self.assertIn('significant_tests', bonferroni)


class TestMovementMetricsCalculation(unittest.TestCase):
    """Test cases specifically for movement metrics calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pipeline = AnalysisPipeline(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_timing_metrics_calculation(self):
        """Test timing metrics calculation with edge cases."""
        # Test with normal data
        movement_data = pd.DataFrame({
            'day': [0, 1, 2, 3, 4],
            'refugees': [0, 10, 20, 15, 5],
            'location': ['A', 'B', 'C', 'D', 'E']
        })
        
        timing_metrics = self.pipeline._calculate_timing_metrics(movement_data)
        
        self.assertIn('simulation_duration', timing_metrics)
        self.assertIn('first_movement_day', timing_metrics)
        self.assertIn('peak_movement', timing_metrics)
        
        # Check values
        self.assertEqual(timing_metrics['simulation_duration']['total_days'], 5)
        self.assertEqual(timing_metrics['first_movement_day'], 1)
        self.assertEqual(timing_metrics['peak_movement']['day'], 2)
        self.assertEqual(timing_metrics['peak_movement']['refugees'], 20)
    
    def test_destination_metrics_calculation(self):
        """Test destination metrics calculation."""
        movement_data = pd.DataFrame({
            'day': [5, 5, 5],  # Final day
            'location': ['Camp_A', 'Camp_B', 'Camp_C'],
            'refugees': [100, 50, 25]
        })
        
        destination_metrics = self.pipeline._calculate_destination_metrics(movement_data)
        
        self.assertIn('distribution', destination_metrics)
        self.assertIn('concentration', destination_metrics)
        self.assertIn('entropy', destination_metrics)
        
        # Check distribution
        distribution = destination_metrics['distribution']
        self.assertEqual(distribution['total_refugees'], 175)
        self.assertEqual(distribution['total_locations'], 3)
        
        # Check entropy
        entropy = destination_metrics['entropy']
        self.assertGreater(entropy['entropy'], 0)
        self.assertLessEqual(entropy['normalized_entropy'], 1)
    
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data."""
        # Empty DataFrame
        empty_data = pd.DataFrame()
        
        timing_metrics = self.pipeline._calculate_timing_metrics(empty_data)
        self.assertEqual(timing_metrics, {})
        
        destination_metrics = self.pipeline._calculate_destination_metrics(empty_data)
        self.assertEqual(destination_metrics, {})
        
        # DataFrame with missing columns
        invalid_data = pd.DataFrame({'invalid_col': [1, 2, 3]})
        
        timing_metrics = self.pipeline._calculate_timing_metrics(invalid_data)
        self.assertEqual(timing_metrics, {})


class TestCognitiveStateAnalysis(unittest.TestCase):
    """Test cases specifically for cognitive state analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pipeline = AnalysisPipeline(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_state_distribution_calculation(self):
        """Test cognitive state distribution calculation."""
        cognitive_data = pd.DataFrame({
            'cognitive_state': ['S1', 'S1', 'S2', 'S2', 'S1'],
            'agent_id': ['1', '1', '1', '2', '2'],
            'day': [0, 1, 2, 3, 4]
        })
        
        state_metrics = self.pipeline._calculate_state_distribution(cognitive_data)
        
        self.assertIn('overall', state_metrics)
        overall = state_metrics['overall']
        
        self.assertEqual(overall['state_counts']['S1'], 3)
        self.assertEqual(overall['state_counts']['S2'], 2)
        self.assertEqual(overall['total_observations'], 5)
        
        # Check proportions
        self.assertAlmostEqual(overall['state_proportions']['S1'], 0.6)
        self.assertAlmostEqual(overall['state_proportions']['S2'], 0.4)
    
    def test_transition_patterns_calculation(self):
        """Test cognitive state transition patterns."""
        cognitive_data = pd.DataFrame({
            'agent_id': ['1', '1', '1', '1'],
            'day': [0, 1, 2, 3],
            'cognitive_state': ['S1', 'S1', 'S2', 'S1']
        })
        
        transition_metrics = self.pipeline._calculate_transition_patterns(cognitive_data)
        
        self.assertIn('overall', transition_metrics)
        overall = transition_metrics['overall']
        
        self.assertEqual(overall['total_transitions'], 2)
        self.assertIn('S1->S2', overall['transition_counts'])
        self.assertIn('S2->S1', overall['transition_counts'])
    
    def test_state_durations_calculation(self):
        """Test cognitive state duration calculation."""
        cognitive_data = pd.DataFrame({
            'agent_id': ['1', '1', '1', '1', '1'],
            'day': [0, 1, 2, 3, 4],
            'cognitive_state': ['S1', 'S1', 'S2', 'S2', 'S1']
        })
        
        duration_metrics = self.pipeline._calculate_state_durations(cognitive_data)
        
        # Should have durations for both S1 and S2
        self.assertIn('S1_durations', duration_metrics)
        self.assertIn('S2_durations', duration_metrics)
        
        # Check S1 durations (should have two periods: days 0-1 and day 4)
        s1_durations = duration_metrics['S1_durations']
        self.assertEqual(s1_durations['count'], 2)
        
        # Check S2 durations (should have one period: days 2-3)
        s2_durations = duration_metrics['S2_durations']
        self.assertEqual(s2_durations['count'], 1)


if __name__ == '__main__':
    unittest.main()