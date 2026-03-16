"""
Test suite for dimensionless parameter analysis module.

Tests the dimensionless parameter calculator, universal scaling detector,
and validation framework for dimensional consistency.
"""

import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import tempfile
import os

from flee_dual_process.dimensionless_analysis import (
    DimensionlessParameterCalculator,
    UniversalScalingDetector,
    DimensionlessParameter,
    ScalingRelationship
)


class TestDimensionlessParameterCalculator(unittest.TestCase):
    """Test cases for DimensionlessParameterCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = DimensionlessParameterCalculator()
    
    def test_cognitive_pressure_calculation(self):
        """Test basic cognitive pressure calculation."""
        # Test normal case
        pressure = self.calculator.calculate_cognitive_pressure(
            conflict_intensity=0.5,
            connectivity=4.0,
            recovery_time=10.0
        )
        expected = (0.5 * 4.0) / 10.0
        self.assertAlmostEqual(pressure, expected, places=6)
        
        # Test edge cases
        pressure_zero_conflict = self.calculator.calculate_cognitive_pressure(
            conflict_intensity=0.0,
            connectivity=4.0,
            recovery_time=10.0
        )
        self.assertEqual(pressure_zero_conflict, 0.0)
        
        # Test error case
        with self.assertRaises(ValueError):
            self.calculator.calculate_cognitive_pressure(
                conflict_intensity=0.5,
                connectivity=4.0,
                recovery_time=0.0
            )
    
    def test_dimensionless_parameter_calculation(self):
        """Test calculation of known dimensionless parameters."""
        values = {
            'conflict_intensity': 0.5,
            'connectivity': 4.0,
            'recovery_time': 10.0
        }
        
        # Test cognitive pressure
        pressure = self.calculator.calculate_dimensionless_parameter(
            'cognitive_pressure', values
        )
        expected = (0.5 * 4.0) / 10.0
        self.assertAlmostEqual(pressure, expected, places=6)
        
        # Test missing variables
        incomplete_values = {'conflict_intensity': 0.5}
        with self.assertRaises(ValueError):
            self.calculator.calculate_dimensionless_parameter(
                'cognitive_pressure', incomplete_values
            )
        
        # Test unknown parameter
        with self.assertRaises(ValueError):
            self.calculator.calculate_dimensionless_parameter(
                'unknown_parameter', values
            )
    
    def test_reynolds_analog_calculation(self):
        """Test Reynolds number analog calculation."""
        values = {
            'population': 1000,
            'movement_speed': 50.0,  # km/day
            'connectivity': 4.0,
            'distance': 100.0  # km
        }
        
        reynolds = self.calculator.calculate_dimensionless_parameter(
            'reynolds_number_analog', values
        )
        expected = (1000 * 50.0) / (4.0 * 100.0)
        self.assertAlmostEqual(reynolds, expected, places=6)
    
    def test_dimensionless_combination_identification(self):
        """Test automatic identification of dimensionless combinations."""
        parameters = ['conflict_intensity', 'connectivity', 'recovery_time', 'population']
        
        combinations = self.calculator.identify_dimensionless_combinations(
            parameters, max_exponent=2
        )
        
        # Should find at least the cognitive pressure combination
        self.assertGreater(len(combinations), 0)
        
        # Check that all combinations are actually dimensionless
        for combo in combinations:
            self.assertTrue(
                self.calculator._is_dimensionless_combination(
                    tuple(combo.variables), tuple(combo.exponents)
                )
            )
    
    def test_dimensional_consistency_check(self):
        """Test dimensional consistency checking."""
        # Test known dimensionless combination
        params = ('conflict_intensity', 'connectivity', 'recovery_time')
        exponents = (1.0, 1.0, -1.0)
        
        is_dimensionless = self.calculator._is_dimensionless_combination(
            params, exponents
        )
        self.assertTrue(is_dimensionless)
        
        # Test dimensional combination (should not be dimensionless)
        params = ('distance', 'recovery_time')
        exponents = (1.0, 1.0)  # This has dimensions of length × time
        
        is_dimensionless = self.calculator._is_dimensionless_combination(
            params, exponents
        )
        self.assertFalse(is_dimensionless)
    
    def test_parameter_scaling_validation(self):
        """Test parameter scaling validation."""
        # Create synthetic data with known scaling relationship
        np.random.seed(42)
        n_points = 50
        
        # Generate data with power law relationship: y = 2 * x^1.5 + noise
        x_values = np.linspace(0.1, 2.0, n_points)
        y_values = 2.0 * np.power(x_values, 1.5) + 0.1 * np.random.randn(n_points)
        
        data = pd.DataFrame({
            'cognitive_pressure': x_values,
            'movement_rate': y_values
        })
        
        validation_result = self.calculator.validate_parameter_scaling(
            data, 'cognitive_pressure', 'movement_rate'
        )
        
        self.assertTrue(validation_result['valid'])
        self.assertEqual(validation_result['n_points'], n_points)
        self.assertIn('scaling_relationships', validation_result)
        
        # Check that power law fit has reasonable R-squared
        power_law_result = validation_result['scaling_relationships']['power_law']
        if 'r_squared' in power_law_result:
            self.assertGreater(power_law_result['r_squared'], 0.8)
    
    def test_validation_with_invalid_data(self):
        """Test validation with insufficient or invalid data."""
        # Test with insufficient data
        data = pd.DataFrame({
            'cognitive_pressure': [1.0, 2.0],
            'movement_rate': [1.0, 2.0]
        })
        
        result = self.calculator.validate_parameter_scaling(
            data, 'cognitive_pressure', 'movement_rate'
        )
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        
        # Test with missing columns
        with self.assertRaises(ValueError):
            self.calculator.validate_parameter_scaling(
                data, 'missing_column', 'movement_rate'
            )


class TestUniversalScalingDetector(unittest.TestCase):
    """Test cases for UniversalScalingDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = UniversalScalingDetector(significance_threshold=0.05)
    
    def test_scaling_relationship_detection(self):
        """Test detection of scaling relationships."""
        # Create synthetic data with known relationships
        np.random.seed(42)
        n_points = 100
        
        # Linear relationship: y1 = 3*x + 1
        # Power law relationship: y2 = 2*x^1.5
        x_values = np.linspace(0.1, 5.0, n_points)
        y1_values = 3.0 * x_values + 1.0 + 0.1 * np.random.randn(n_points)
        y2_values = 2.0 * np.power(x_values, 1.5) + 0.1 * np.random.randn(n_points)
        
        data = pd.DataFrame({
            'cognitive_pressure': x_values,
            'linear_response': y1_values,
            'power_response': y2_values
        })
        
        relationships = self.detector.detect_scaling_relationships(
            data, 
            ['cognitive_pressure'], 
            ['linear_response', 'power_response']
        )
        
        self.assertGreater(len(relationships), 0)
        
        # Check that we found good fits
        for rel in relationships:
            self.assertGreater(rel.r_squared, 0.8)
            self.assertIn(rel.scaling_function, self.detector.scaling_functions.keys())
    
    def test_scaling_function_fitting(self):
        """Test individual scaling function fitting."""
        # Test linear function fitting
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect linear relationship
        
        linear_func = self.detector.scaling_functions['linear']
        result = self.detector._fit_scaling_function(x, y, linear_func, 'linear')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['function_name'], 'linear')
        self.assertAlmostEqual(result['parameters']['a'], 2.0, places=1)
        self.assertAlmostEqual(result['parameters']['b'], 0.0, places=1)
        self.assertGreater(result['r_squared'], 0.99)
    
    def test_power_law_fitting(self):
        """Test power law function fitting."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])  # y = x^2
        
        power_func = self.detector.scaling_functions['power_law']
        result = self.detector._fit_scaling_function(x, y, power_func, 'power_law')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['function_name'], 'power_law')
        self.assertAlmostEqual(result['parameters']['b'], 2.0, places=1)
        self.assertGreater(result['r_squared'], 0.99)
    
    def test_data_collapse_validation(self):
        """Test data collapse validation."""
        # Create synthetic data that should collapse
        np.random.seed(42)
        
        # Generate data for different groups that follow same scaling law
        groups_data = []
        for group_id in range(3):
            x_vals = np.linspace(0.1, 2.0, 20)
            # Same scaling law: y = x^1.5, but different absolute scales
            scale_factor = 1.0 + 0.1 * group_id
            y_vals = scale_factor * np.power(x_vals, 1.5) + 0.05 * np.random.randn(20)
            
            group_df = pd.DataFrame({
                'cognitive_pressure': x_vals,
                'normalized_response': y_vals / scale_factor,  # Normalize to collapse
                'group_id': group_id,
                'scenario': f'scenario_{group_id}'
            })
            groups_data.append(group_df)
        
        data = pd.concat(groups_data, ignore_index=True)
        
        collapse_results = self.detector.validate_data_collapse(
            data,
            'cognitive_pressure',
            ['normalized_response'],
            ['group_id']
        )
        
        self.assertIn('normalized_response', collapse_results)
        result = collapse_results['normalized_response']
        self.assertTrue(result['valid'])
        self.assertEqual(result['n_groups'], 3)
        self.assertIn('collapse_quality', result)
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data."""
        # Create minimal dataset
        data = pd.DataFrame({
            'cognitive_pressure': [1.0, 2.0],
            'response': [1.0, 2.0],
            'group': ['A', 'B']
        })
        
        relationships = self.detector.detect_scaling_relationships(
            data, ['cognitive_pressure'], ['response']
        )
        
        # Should return empty list due to insufficient data
        self.assertEqual(len(relationships), 0)


class TestDimensionlessParameterIntegration(unittest.TestCase):
    """Integration tests for dimensionless parameter analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = DimensionlessParameterCalculator()
        self.detector = UniversalScalingDetector()
    
    def test_end_to_end_analysis(self):
        """Test complete dimensionless parameter analysis workflow."""
        # Create realistic experimental data
        np.random.seed(42)
        n_experiments = 50
        
        # Generate parameter combinations
        conflict_intensities = np.random.uniform(0.1, 1.0, n_experiments)
        connectivities = np.random.uniform(1.0, 8.0, n_experiments)
        recovery_times = np.random.uniform(5.0, 30.0, n_experiments)
        
        # Calculate cognitive pressure
        cognitive_pressures = []
        for ci, conn, rt in zip(conflict_intensities, connectivities, recovery_times):
            pressure = self.calculator.calculate_cognitive_pressure(ci, conn, rt)
            cognitive_pressures.append(pressure)
        
        # Generate synthetic response that depends on cognitive pressure
        # Use sigmoid relationship: response = 1 / (1 + exp(-5*(pressure - 0.5)))
        responses = 1.0 / (1.0 + np.exp(-5.0 * (np.array(cognitive_pressures) - 0.5)))
        responses += 0.05 * np.random.randn(n_experiments)  # Add noise
        
        # Create DataFrame
        data = pd.DataFrame({
            'conflict_intensity': conflict_intensities,
            'connectivity': connectivities,
            'recovery_time': recovery_times,
            'cognitive_pressure': cognitive_pressures,
            'system2_activation_rate': responses,
            'scenario_type': np.random.choice(['A', 'B', 'C'], n_experiments)
        })
        
        # Test parameter validation
        validation_result = self.calculator.validate_parameter_scaling(
            data, 'cognitive_pressure', 'system2_activation_rate'
        )
        
        self.assertTrue(validation_result['valid'])
        self.assertGreater(validation_result['n_points'], 40)
        
        # Test scaling relationship detection
        relationships = self.detector.detect_scaling_relationships(
            data, 
            ['cognitive_pressure'], 
            ['system2_activation_rate']
        )
        
        # Should find at least one good relationship
        self.assertGreater(len(relationships), 0)
        best_relationship = max(relationships, key=lambda r: r.r_squared)
        self.assertGreater(best_relationship.r_squared, 0.7)
    
    def test_multiple_dimensionless_parameters(self):
        """Test analysis with multiple dimensionless parameters."""
        # Create data with multiple dimensionless parameters
        np.random.seed(42)
        n_points = 30
        
        data = pd.DataFrame({
            'conflict_intensity': np.random.uniform(0.1, 1.0, n_points),
            'connectivity': np.random.uniform(1.0, 8.0, n_points),
            'recovery_time': np.random.uniform(5.0, 30.0, n_points),
            'population': np.random.uniform(100, 1000, n_points),
            'movement_speed': np.random.uniform(10, 100, n_points),
            'distance': np.random.uniform(50, 200, n_points)
        })
        
        # Calculate multiple dimensionless parameters
        cognitive_pressures = []
        reynolds_analogs = []
        
        for _, row in data.iterrows():
            cp = self.calculator.calculate_cognitive_pressure(
                row['conflict_intensity'], row['connectivity'], row['recovery_time']
            )
            cognitive_pressures.append(cp)
            
            ra = self.calculator.calculate_dimensionless_parameter(
                'reynolds_number_analog',
                {
                    'population': row['population'],
                    'movement_speed': row['movement_speed'],
                    'connectivity': row['connectivity'],
                    'distance': row['distance']
                }
            )
            reynolds_analogs.append(ra)
        
        data['cognitive_pressure'] = cognitive_pressures
        data['reynolds_analog'] = reynolds_analogs
        
        # Generate synthetic responses
        data['response1'] = 2.0 * np.array(cognitive_pressures) + 0.1 * np.random.randn(n_points)
        data['response2'] = np.sqrt(reynolds_analogs) + 0.1 * np.random.randn(n_points)
        
        # Test detection of multiple relationships
        relationships = self.detector.detect_scaling_relationships(
            data,
            ['cognitive_pressure', 'reynolds_analog'],
            ['response1', 'response2']
        )
        
        # Should find relationships for both dimensionless parameters
        param_names = {rel.parameter for rel in relationships}
        self.assertIn('cognitive_pressure', param_names)
        self.assertIn('reynolds_analog', param_names)


if __name__ == '__main__':
    unittest.main()