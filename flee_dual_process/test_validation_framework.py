"""
Unit Tests for Validation Framework

Tests for experiment configuration validation, output validation,
and statistical validation components.
"""

import unittest
import tempfile
import shutil
import os
import csv
import json
import numpy as np
from typing import Dict, List, Any

try:
    from .validation_framework import (
        ValidationResult, ExperimentConfigValidator, FileFormatValidator,
        StatisticalValidator, ExperimentValidator
    )
except ImportError:
    from validation_framework import (
        ValidationResult, ExperimentConfigValidator, FileFormatValidator,
        StatisticalValidator, ExperimentValidator
    )


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult class."""
    
    def test_initialization_default(self):
        """Test default initialization."""
        result = ValidationResult()
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.details, {})
    
    def test_initialization_with_parameters(self):
        """Test initialization with parameters."""
        errors = ["Error 1", "Error 2"]
        warnings = ["Warning 1"]
        details = {"key": "value"}
        
        result = ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            details=details
        )
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors, errors)
        self.assertEqual(result.warnings, warnings)
        self.assertEqual(result.details, details)
    
    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult()
        
        result.add_error("Test error")
        
        self.assertFalse(result.is_valid)
        self.assertIn("Test error", result.errors)
    
    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult()
        
        result.add_warning("Test warning")
        
        self.assertTrue(result.is_valid)  # Warnings don't affect validity
        self.assertIn("Test warning", result.warnings)
    
    def test_add_detail(self):
        """Test adding details."""
        result = ValidationResult()
        
        result.add_detail("test_key", "test_value")
        
        self.assertEqual(result.details["test_key"], "test_value")
    
    def test_merge(self):
        """Test merging validation results."""
        result1 = ValidationResult()
        result1.add_error("Error 1")
        result1.add_warning("Warning 1")
        result1.add_detail("key1", "value1")
        
        result2 = ValidationResult()
        result2.add_error("Error 2")
        result2.add_warning("Warning 2")
        result2.add_detail("key2", "value2")
        
        result1.merge(result2)
        
        self.assertFalse(result1.is_valid)
        self.assertEqual(len(result1.errors), 2)
        self.assertEqual(len(result1.warnings), 2)
        self.assertEqual(len(result1.details), 2)
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ValidationResult()
        result.add_error("Test error")
        result.add_warning("Test warning")
        result.add_detail("test_key", "test_value")
        
        result_dict = result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertFalse(result_dict['is_valid'])
        self.assertIn("Test error", result_dict['errors'])
        self.assertIn("Test warning", result_dict['warnings'])
        self.assertEqual(result_dict['details']['test_key'], "test_value")


class TestExperimentConfigValidator(unittest.TestCase):
    """Test cases for ExperimentConfigValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ExperimentConfigValidator()
    
    def test_valid_linear_config(self):
        """Test validation of valid linear topology configuration."""
        config = {
            'experiment_id': 'test_linear_001',
            'topology_type': 'linear',
            'topology_params': {
                'n_nodes': 5,
                'segment_distance': 50.0,
                'start_pop': 1000,
                'pop_decay': 0.8
            },
            'scenario_type': 'spike',
            'scenario_params': {
                'origin': 'Origin',
                'start_day': 0,
                'peak_intensity': 0.8
            },
            'cognitive_mode': 'dual_process',
            'simulation_params': {
                'move_rules': {
                    'awareness_level': 2,
                    'weight_softening': 0.3
                }
            }
        }
        
        result = self.validator.validate_experiment_config(config)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        config = {
            'experiment_id': 'test_missing',
            # Missing topology_type, scenario_type, cognitive_mode
        }
        
        result = self.validator.validate_experiment_config(config)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_invalid_experiment_id(self):
        """Test validation of invalid experiment IDs."""
        # Empty ID
        config = {'experiment_id': '', 'topology_type': 'linear', 'scenario_type': 'spike', 'cognitive_mode': 's1_only'}
        result = self.validator.validate_experiment_config(config)
        self.assertFalse(result.is_valid)
        
        # Invalid characters
        config['experiment_id'] = 'test@invalid#id'
        result = self.validator.validate_experiment_config(config)
        self.assertFalse(result.is_valid)
        
        # Too long
        config['experiment_id'] = 'a' * 101
        result = self.validator.validate_experiment_config(config)
        self.assertFalse(result.is_valid)
    
    def test_invalid_topology_type(self):
        """Test validation with invalid topology type."""
        config = {
            'experiment_id': 'test_invalid_topology',
            'topology_type': 'invalid_topology',
            'scenario_type': 'spike',
            'cognitive_mode': 's1_only'
        }
        
        result = self.validator.validate_experiment_config(config)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('Invalid topology type' in error for error in result.errors))
    
    def test_linear_topology_validation(self):
        """Test linear topology parameter validation."""
        base_config = {
            'experiment_id': 'test_linear',
            'topology_type': 'linear',
            'scenario_type': 'spike',
            'cognitive_mode': 's1_only'
        }
        
        # Valid parameters
        base_config['topology_params'] = {
            'n_nodes': 5,
            'segment_distance': 50.0,
            'start_pop': 1000,
            'pop_decay': 0.8
        }
        result = self.validator.validate_experiment_config(base_config)
        self.assertTrue(result.is_valid)
        
        # Invalid n_nodes
        base_config['topology_params']['n_nodes'] = 1
        result = self.validator.validate_experiment_config(base_config)
        self.assertFalse(result.is_valid)
        
        # Invalid pop_decay
        base_config['topology_params']['n_nodes'] = 5
        base_config['topology_params']['pop_decay'] = 1.5
        result = self.validator.validate_experiment_config(base_config)
        self.assertFalse(result.is_valid)
    
    def test_star_topology_validation(self):
        """Test star topology parameter validation."""
        config = {
            'experiment_id': 'test_star',
            'topology_type': 'star',
            'topology_params': {
                'n_camps': 4,
                'hub_pop': 2000,
                'camp_capacity': 5000,
                'radius': 100.0
            },
            'scenario_type': 'spike',
            'cognitive_mode': 's1_only'
        }
        
        result = self.validator.validate_experiment_config(config)
        self.assertTrue(result.is_valid)
        
        # Invalid n_camps
        config['topology_params']['n_camps'] = 0
        result = self.validator.validate_experiment_config(config)
        self.assertFalse(result.is_valid)
    
    def test_scenario_validation(self):
        """Test scenario parameter validation."""
        base_config = {
            'experiment_id': 'test_scenario',
            'topology_type': 'linear',
            'topology_params': {'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
            'cognitive_mode': 's1_only'
        }
        
        # Valid spike scenario
        base_config['scenario_type'] = 'spike'
        base_config['scenario_params'] = {
            'origin': 'Origin',
            'start_day': 0,
            'peak_intensity': 0.8
        }
        result = self.validator.validate_experiment_config(base_config)
        self.assertTrue(result.is_valid)
        
        # Invalid peak_intensity
        base_config['scenario_params']['peak_intensity'] = 1.5
        result = self.validator.validate_experiment_config(base_config)
        self.assertFalse(result.is_valid)
        
        # Valid gradual scenario
        base_config['scenario_type'] = 'gradual'
        base_config['scenario_params'] = {
            'origin': 'Origin',
            'start_day': 0,
            'end_day': 10,
            'max_intensity': 0.8
        }
        result = self.validator.validate_experiment_config(base_config)
        self.assertTrue(result.is_valid)
        
        # Invalid day order
        base_config['scenario_params']['end_day'] = -1
        result = self.validator.validate_experiment_config(base_config)
        self.assertFalse(result.is_valid)
    
    def test_cognitive_mode_validation(self):
        """Test cognitive mode validation."""
        config = {
            'experiment_id': 'test_cognitive',
            'topology_type': 'linear',
            'topology_params': {'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
            'scenario_type': 'spike',
            'scenario_params': {'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8}
        }
        
        # Valid cognitive modes
        for mode in ['s1_only', 's2_disconnected', 's2_full', 'dual_process']:
            config['cognitive_mode'] = mode
            result = self.validator.validate_experiment_config(config)
            self.assertTrue(result.is_valid, f"Valid mode {mode} failed validation")
        
        # Invalid cognitive mode
        config['cognitive_mode'] = 'invalid_mode'
        result = self.validator.validate_experiment_config(config)
        self.assertFalse(result.is_valid)
    
    def test_simulation_params_validation(self):
        """Test simulation parameters validation."""
        config = {
            'experiment_id': 'test_sim_params',
            'topology_type': 'linear',
            'topology_params': {'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
            'scenario_type': 'spike',
            'scenario_params': {'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8},
            'cognitive_mode': 'dual_process'
        }
        
        # Valid simulation params
        config['simulation_params'] = {
            'move_rules': {
                'awareness_level': 2,
                'weight_softening': 0.3,
                'average_social_connectivity': 3.0,
                'two_system_decision_making': True
            }
        }
        result = self.validator.validate_experiment_config(config)
        self.assertTrue(result.is_valid)
        
        # Invalid awareness_level
        config['simulation_params']['move_rules']['awareness_level'] = 5
        result = self.validator.validate_experiment_config(config)
        self.assertFalse(result.is_valid)
        
        # Invalid weight_softening
        config['simulation_params']['move_rules']['awareness_level'] = 2
        config['simulation_params']['move_rules']['weight_softening'] = 1.5
        result = self.validator.validate_experiment_config(config)
        self.assertFalse(result.is_valid)


class TestFileFormatValidator(unittest.TestCase):
    """Test cases for FileFormatValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = FileFormatValidator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_valid_locations_csv(self):
        """Test validation of valid locations CSV."""
        locations_file = os.path.join(self.temp_dir, 'locations.csv')
        
        with open(locations_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'])
            writer.writerow(['Origin', 'Region1', 'Country1', '10.0', '20.0', 'conflict_zone', '', '1000'])
            writer.writerow(['Town_A', 'Region1', 'Country1', '11.0', '21.0', 'town', '', '800'])
            writer.writerow(['Camp_B', 'Region1', 'Country1', '12.0', '22.0', 'camp', '', '5000'])
        
        result = self.validator.validate_locations_csv_format(locations_file)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
        self.assertEqual(result.details['row_count'], 3)
    
    def test_invalid_locations_csv_header(self):
        """Test validation with invalid locations CSV header."""
        locations_file = os.path.join(self.temp_dir, 'invalid_locations.csv')
        
        with open(locations_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'lat', 'lon'])  # Wrong header
            writer.writerow(['Origin', '10.0', '20.0'])
        
        result = self.validator.validate_locations_csv_format(locations_file)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('Invalid locations CSV header' in error for error in result.errors))
    
    def test_invalid_locations_csv_data(self):
        """Test validation with invalid locations CSV data."""
        locations_file = os.path.join(self.temp_dir, 'invalid_data_locations.csv')
        
        with open(locations_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'])
            writer.writerow(['', 'Region1', 'Country1', '10.0', '20.0', 'town', '', '1000'])  # Empty name
            writer.writerow(['Town_A', 'Region1', 'Country1', '100.0', '20.0', 'town', '', '1000'])  # Invalid lat
            writer.writerow(['Town_B', 'Region1', 'Country1', '10.0', '20.0', 'invalid_type', '', '1000'])  # Invalid type
            writer.writerow(['Town_C', 'Region1', 'Country1', '10.0', '20.0', 'town', '', '-100'])  # Negative pop
        
        result = self.validator.validate_locations_csv_format(locations_file)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 3)  # Should have multiple errors
    
    def test_valid_routes_csv(self):
        """Test validation of valid routes CSV."""
        routes_file = os.path.join(self.temp_dir, 'routes.csv')
        
        with open(routes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name1', 'name2', 'distance', 'forced_redirection'])
            writer.writerow(['Origin', 'Town_A', '50.0', '0'])
            writer.writerow(['Town_A', 'Camp_B', '75.0', '0'])
        
        result = self.validator.validate_routes_csv_format(routes_file)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
        self.assertEqual(result.details['row_count'], 2)
    
    def test_invalid_routes_csv_data(self):
        """Test validation with invalid routes CSV data."""
        routes_file = os.path.join(self.temp_dir, 'invalid_routes.csv')
        
        with open(routes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name1', 'name2', 'distance', 'forced_redirection'])
            writer.writerow(['Origin', 'Origin', '50.0', '0'])  # Self-loop
            writer.writerow(['Town_A', 'Town_B', '-10.0', '0'])  # Negative distance
            writer.writerow(['Town_C', 'Town_D', '50.0', '2'])  # Invalid redirection
        
        result = self.validator.validate_routes_csv_format(routes_file)
        
        self.assertFalse(result.is_valid)
        self.assertGreaterEqual(len(result.errors), 3)
    
    def test_valid_conflicts_csv(self):
        """Test validation of valid conflicts CSV."""
        conflicts_file = os.path.join(self.temp_dir, 'conflicts.csv')
        
        with open(conflicts_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#Day', 'Origin', 'Town_A', 'Camp_B'])
            writer.writerow(['0', '0.8', '0.0', '0.0'])
            writer.writerow(['1', '0.9', '0.2', '0.0'])
            writer.writerow(['2', '0.7', '0.5', '0.1'])
        
        result = self.validator.validate_conflicts_csv_format(conflicts_file)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
        self.assertEqual(result.details['row_count'], 3)
        self.assertEqual(result.details['location_count'], 3)
    
    def test_invalid_conflicts_csv_data(self):
        """Test validation with invalid conflicts CSV data."""
        conflicts_file = os.path.join(self.temp_dir, 'invalid_conflicts.csv')
        
        with open(conflicts_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#Day', 'Origin', 'Town_A'])
            writer.writerow(['-1', '0.8', '0.0'])  # Negative day
            writer.writerow(['1', '1.5', '0.0'])  # Intensity > 1
            writer.writerow(['2', '0.5', '-0.1'])  # Negative intensity
        
        result = self.validator.validate_conflicts_csv_format(conflicts_file)
        
        self.assertFalse(result.is_valid)
        self.assertGreaterEqual(len(result.errors), 3)
    
    def test_valid_flee_output(self):
        """Test validation of valid Flee output."""
        output_file = os.path.join(self.temp_dir, 'out.csv')
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
            writer.writerow(['0', 'Origin', '1000', '1000'])
            writer.writerow(['1', 'Origin', '800', '800'])
            writer.writerow(['1', 'Town_A', '200', '200'])
        
        result = self.validator.validate_flee_output_format(output_file)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
    
    def test_missing_file_validation(self):
        """Test validation of missing files."""
        missing_file = os.path.join(self.temp_dir, 'missing.csv')
        
        result = self.validator.validate_locations_csv_format(missing_file)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('not found' in error for error in result.errors))


class TestStatisticalValidator(unittest.TestCase):
    """Test cases for StatisticalValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = StatisticalValidator()
    
    def test_valid_statistical_test_results(self):
        """Test validation of valid statistical test results."""
        test_results = {
            'p_value': 0.05,
            'test_statistic': 2.5,
            'degrees_of_freedom': 10,
            'effect_size': 0.8,
            'confidence_interval': [0.1, 0.9]
        }
        
        result = self.validator.validate_statistical_test_results(test_results)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
    
    def test_invalid_p_value(self):
        """Test validation with invalid p-values."""
        # p-value > 1
        test_results = {'p_value': 1.5}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
        
        # Negative p-value
        test_results = {'p_value': -0.1}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
        
        # NaN p-value
        test_results = {'p_value': float('nan')}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
    
    def test_invalid_test_statistic(self):
        """Test validation with invalid test statistics."""
        # NaN test statistic
        test_results = {'test_statistic': float('nan')}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
        
        # Infinite test statistic
        test_results = {'test_statistic': float('inf')}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
    
    def test_invalid_confidence_interval(self):
        """Test validation with invalid confidence intervals."""
        # Wrong length
        test_results = {'confidence_interval': [0.1]}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
        
        # Lower > upper
        test_results = {'confidence_interval': [0.9, 0.1]}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
        
        # NaN values
        test_results = {'confidence_interval': [float('nan'), 0.5]}
        result = self.validator.validate_statistical_test_results(test_results)
        self.assertFalse(result.is_valid)
    
    def test_valid_effect_sizes(self):
        """Test validation of valid effect sizes."""
        effect_sizes = {
            'cohens_d': 0.8,
            'eta_squared': 0.25,
            'pearson_r': 0.6
        }
        
        result = self.validator.validate_effect_size_calculations(effect_sizes)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
    
    def test_invalid_effect_sizes(self):
        """Test validation with invalid effect sizes."""
        # Invalid eta squared (> 1)
        effect_sizes = {'eta_squared': 1.5}
        result = self.validator.validate_effect_size_calculations(effect_sizes)
        self.assertFalse(result.is_valid)
        
        # Invalid Pearson r (> 1)
        effect_sizes = {'pearson_r': 1.5}
        result = self.validator.validate_effect_size_calculations(effect_sizes)
        self.assertFalse(result.is_valid)
        
        # Very large Cohen's d (warning)
        effect_sizes = {'cohens_d': 15.0}
        result = self.validator.validate_effect_size_calculations(effect_sizes)
        self.assertTrue(result.is_valid)  # Should be valid but with warning
        self.assertGreater(len(result.warnings), 0)
    
    def test_sample_size_adequacy(self):
        """Test sample size adequacy validation."""
        # Adequate sample sizes
        sample_sizes = {'group1': 100, 'group2': 120}
        result = self.validator.validate_sample_size_adequacy(sample_sizes)
        self.assertTrue(result.is_valid)
        
        # Small sample sizes (warning)
        sample_sizes = {'group1': 20, 'group2': 25}
        result = self.validator.validate_sample_size_adequacy(sample_sizes)
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
        
        # Very small sample sizes (error)
        sample_sizes = {'group1': 5, 'group2': 3}
        result = self.validator.validate_sample_size_adequacy(sample_sizes)
        self.assertFalse(result.is_valid)
    
    def test_normality_assumptions(self):
        """Test normality assumptions validation."""
        # Normal-ish data
        np.random.seed(42)
        data = {
            'group1': np.random.normal(0, 1, 50).tolist(),
            'group2': np.random.normal(1, 1, 50).tolist()
        }
        
        result = self.validator.validate_normality_assumptions(data)
        self.assertTrue(result.is_valid)
        
        # Data with extreme outliers
        data_with_outliers = {
            'group1': [1, 2, 3, 4, 5, 100],  # 100 is an extreme outlier
            'group2': [2, 3, 4, 5, 6, 7]
        }
        
        result = self.validator.validate_normality_assumptions(data_with_outliers)
        self.assertTrue(result.is_valid)  # Should be valid but with warnings
        self.assertGreater(len(result.warnings), 0)
        
        # Insufficient data
        insufficient_data = {
            'group1': [1, 2],  # Too few points
            'group2': [3, 4, 5]
        }
        
        result = self.validator.validate_normality_assumptions(insufficient_data)
        self.assertFalse(result.is_valid)


class TestExperimentValidator(unittest.TestCase):
    """Test cases for ExperimentValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = ExperimentValidator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_validate_complete_experiment_setup(self):
        """Test complete experiment setup validation."""
        # Create valid input files
        locations_file = os.path.join(self.temp_dir, 'locations.csv')
        routes_file = os.path.join(self.temp_dir, 'routes.csv')
        conflicts_file = os.path.join(self.temp_dir, 'conflicts.csv')
        
        # Create locations file
        with open(locations_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'])
            writer.writerow(['Origin', 'Region1', 'Country1', '10.0', '20.0', 'conflict_zone', '', '1000'])
            writer.writerow(['Camp_A', 'Region1', 'Country1', '11.0', '21.0', 'camp', '', '5000'])
        
        # Create routes file
        with open(routes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name1', 'name2', 'distance', 'forced_redirection'])
            writer.writerow(['Origin', 'Camp_A', '50.0', '0'])
        
        # Create conflicts file
        with open(conflicts_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#Day', 'Origin', 'Camp_A'])
            writer.writerow(['0', '0.8', '0.0'])
            writer.writerow(['1', '0.9', '0.0'])
        
        # Valid configuration
        config = {
            'experiment_id': 'test_complete_validation',
            'topology_type': 'linear',
            'topology_params': {
                'n_nodes': 2,
                'segment_distance': 50.0,
                'start_pop': 1000,
                'pop_decay': 0.8
            },
            'scenario_type': 'spike',
            'scenario_params': {
                'origin': 'Origin',
                'start_day': 0,
                'peak_intensity': 0.8
            },
            'cognitive_mode': 'dual_process',
            'simulation_params': {
                'move_rules': {
                    'awareness_level': 2,
                    'two_system_decision_making': True
                }
            }
        }
        
        input_files = {
            'locations': locations_file,
            'routes': routes_file,
            'conflicts': conflicts_file
        }
        
        result = self.validator.validate_experiment_setup(config, input_files)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
    
    def test_validate_experiment_output(self):
        """Test experiment output validation."""
        # Create output directory with valid files
        output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(output_dir)
        
        # Create required out.csv
        with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
            writer.writerow(['0', 'Origin', '1000', '1000'])
            writer.writerow(['1', 'Camp_A', '500', '500'])
        
        # Create optional cognitive states file
        with open(os.path.join(output_dir, 'cognitive_states.out.0'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'agent_id', 'cognitive_state', 'location'])
            writer.writerow(['0', '0-1', 'S1', 'Origin'])
            writer.writerow(['1', '0-1', 'S2', 'Camp_A'])
        
        result = self.validator.validate_experiment_output(output_dir)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
    
    def test_validate_analysis_results(self):
        """Test analysis results validation."""
        analysis_results = {
            'statistical_tests': {
                'ttest': {
                    'p_value': 0.03,
                    'test_statistic': 2.1,
                    'degrees_of_freedom': 20
                }
            },
            'effect_sizes': {
                'cohens_d': 0.6,
                'eta_squared': 0.15
            },
            'multiple_comparisons': {
                'bonferroni': {
                    'corrected_alpha': 0.025
                }
            }
        }
        
        result = self.validator.validate_analysis_results(analysis_results)
        
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")
    
    def test_generate_validation_report(self):
        """Test validation report generation."""
        # Create some validation results
        result1 = ValidationResult()
        result1.add_error("Test error 1")
        result1.add_warning("Test warning 1")
        result1.add_detail("test_key", "test_value")
        
        result2 = ValidationResult()
        result2.add_warning("Test warning 2")
        
        results = [result1, result2]
        
        # Generate report
        report = self.validator.generate_validation_report(results)
        
        # Check report content
        self.assertIn("Experiment Validation Report", report)
        self.assertIn("FAIL", report)  # Should fail due to error in result1
        self.assertIn("Total Errors: 1", report)
        self.assertIn("Total Warnings: 2", report)
        self.assertIn("Test error 1", report)
        self.assertIn("Test warning 1", report)
        self.assertIn("Test warning 2", report)
        
        # Test saving report to file
        report_file = os.path.join(self.temp_dir, 'validation_report.md')
        saved_report = self.validator.generate_validation_report(results, report_file)
        
        self.assertTrue(os.path.exists(report_file))
        self.assertEqual(report, saved_report)


if __name__ == '__main__':
    unittest.main(verbosity=2)