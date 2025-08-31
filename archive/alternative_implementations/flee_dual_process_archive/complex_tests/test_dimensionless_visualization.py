"""
Test suite for dimensionless parameter visualization framework.

Tests the visualization generator, plot creation, and publication-ready
figure generation capabilities.
"""

import unittest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock

from flee_dual_process.dimensionless_visualization import (
    DimensionlessVisualizationGenerator,
    PlotConfiguration
)
from flee_dual_process.dimensionless_analysis import ScalingRelationship


class TestDimensionlessVisualizationGenerator(unittest.TestCase):
    """Test cases for DimensionlessVisualizationGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PlotConfiguration(figsize=(8, 6), dpi=100)
        self.generator = DimensionlessVisualizationGenerator(self.config)
        
        # Create synthetic test data
        np.random.seed(42)
        n_points = 100
        
        # Generate realistic experimental data
        conflict_intensities = np.random.uniform(0.1, 1.0, n_points)
        connectivities = np.random.uniform(1.0, 8.0, n_points)
        recovery_times = np.random.uniform(5.0, 30.0, n_points)
        
        # Calculate cognitive pressure
        cognitive_pressures = (conflict_intensities * connectivities) / recovery_times
        
        # Generate responses with known scaling relationships
        system2_rates = 1.0 / (1.0 + np.exp(-3.0 * (cognitive_pressures - 0.5)))
        movement_rates = 2.0 * np.power(cognitive_pressures, 0.8) + 0.1 * np.random.randn(n_points)
        
        # Add grouping variables
        scenarios = np.random.choice(['A', 'B', 'C'], n_points)
        topologies = np.random.choice(['linear', 'star', 'grid'], n_points)
        
        self.test_data = pd.DataFrame({
            'conflict_intensity': conflict_intensities,
            'connectivity': connectivities,
            'recovery_time': recovery_times,
            'cognitive_pressure': cognitive_pressures,
            'system2_activation_rate': system2_rates,
            'movement_rate': movement_rates,
            'scenario': scenarios,
            'topology': topologies
        })
        
        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Close any open matplotlib figures
        plt.close('all')
        
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_data_collapse_plot_creation(self):
        """Test creation of data collapse plots."""
        fig = self.generator.create_data_collapse_plot(
            self.test_data,
            'cognitive_pressure',
            'system2_activation_rate',
            'scenario',
            title='Test Data Collapse'
        )
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 2)  # Should have two subplots
        
        # Check that axes have proper labels
        ax1, ax2 = fig.axes
        self.assertIn('cognitive_pressure', ax1.get_xlabel())
        self.assertIn('system2_activation_rate', ax1.get_ylabel())
        self.assertIn('cognitive_pressure', ax2.get_xlabel())
        self.assertIn('normalized', ax2.get_ylabel())
        
        plt.close(fig)
    
    def test_data_collapse_plot_with_save(self):
        """Test data collapse plot with file saving."""
        save_path = os.path.join(self.temp_dir, 'test_collapse.png')
        
        fig = self.generator.create_data_collapse_plot(
            self.test_data,
            'cognitive_pressure',
            'system2_activation_rate',
            'scenario',
            save_path=save_path
        )
        
        self.assertTrue(os.path.exists(save_path))
        plt.close(fig)
    
    def test_scaling_relationship_plot_creation(self):
        """Test creation of scaling relationship plots."""
        # Create mock scaling relationships
        relationships = [
            ScalingRelationship(
                parameter='cognitive_pressure',
                dependent_variable='system2_activation_rate',
                scaling_function='sigmoid',
                fit_parameters={'a': 1.0, 'b': 3.0, 'c': 0.5},
                r_squared=0.85,
                confidence_interval=(0.8, 0.9)
            ),
            ScalingRelationship(
                parameter='cognitive_pressure',
                dependent_variable='movement_rate',
                scaling_function='power_law',
                fit_parameters={'a': 2.0, 'b': 0.8},
                r_squared=0.75,
                confidence_interval=(0.7, 0.8)
            )
        ]
        
        fig = self.generator.create_scaling_relationship_plot(
            self.test_data,
            relationships,
            title='Test Scaling Relationships'
        )
        
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 2)  # Should have two subplots for two relationships
        
        plt.close(fig)
    
    def test_scaling_relationship_plot_empty_relationships(self):
        """Test scaling relationship plot with empty relationships list."""
        with self.assertRaises(ValueError):
            self.generator.create_scaling_relationship_plot(
                self.test_data,
                [],
                title='Empty Relationships'
            )
    
    def test_parameter_sensitivity_heatmap_creation(self):
        """Test creation of parameter sensitivity heatmaps."""
        dimensionless_params = ['cognitive_pressure']
        dependent_variables = ['system2_activation_rate', 'movement_rate']
        
        fig = self.generator.create_parameter_sensitivity_heatmap(
            self.test_data,
            dimensionless_params,
            dependent_variables,
            title='Test Sensitivity Analysis'
        )
        
        self.assertIsNotNone(fig)
        # Should have at least 2 axes (correlation and sensitivity plots)
        # Note: seaborn heatmap may create additional axes for colorbars
        self.assertGreaterEqual(len(fig.axes), 2)
        
        plt.close(fig)
    
    def test_parameter_sensitivity_insufficient_data(self):
        """Test sensitivity analysis with insufficient parameters."""
        with self.assertRaises(ValueError):
            self.generator.create_parameter_sensitivity_heatmap(
                self.test_data,
                ['nonexistent_param'],
                ['another_nonexistent_param']
            )
    
    def test_dimensionless_parameter_table_creation(self):
        """Test creation of dimensionless parameter summary table."""
        dimensionless_params = ['cognitive_pressure']
        
        table_df = self.generator.create_dimensionless_parameter_table(
            self.test_data,
            dimensionless_params
        )
        
        self.assertIsInstance(table_df, pd.DataFrame)
        self.assertGreater(len(table_df), 0)
        
        # Check required columns
        expected_columns = ['Parameter', 'Formula', 'Description', 'Min', 'Max', 'Mean', 'Std']
        for col in expected_columns:
            self.assertIn(col, table_df.columns)
    
    def test_parameter_table_with_save(self):
        """Test parameter table with file saving."""
        save_path = os.path.join(self.temp_dir, 'test_table.csv')
        dimensionless_params = ['cognitive_pressure']
        
        table_df = self.generator.create_dimensionless_parameter_table(
            self.test_data,
            dimensionless_params,
            save_path=save_path
        )
        
        self.assertTrue(os.path.exists(save_path))
        
        # Verify saved file can be read back
        loaded_df = pd.read_csv(save_path)
        self.assertEqual(len(loaded_df), len(table_df))
    
    def test_interactive_parameter_explorer_creation(self):
        """Test creation of interactive parameter explorer."""
        dimensionless_params = ['cognitive_pressure']
        dependent_variables = ['system2_activation_rate', 'movement_rate']
        
        # Mock plotly to avoid display issues in tests
        with patch('flee_dual_process.dimensionless_visualization.pyo') if hasattr(self.generator, 'pyo') else patch('builtins.print'):
            fig = self.generator.create_interactive_parameter_explorer(
                self.test_data,
                dimensionless_params,
                dependent_variables
            )
        
        # Figure might be None if plotly is not available
        if fig is not None:
            # Check that figure has data
            self.assertGreater(len(fig.data), 0)
    
    def test_interactive_explorer_empty_parameters(self):
        """Test interactive explorer with empty parameters."""
        with self.assertRaises(ValueError):
            self.generator.create_interactive_parameter_explorer(
                self.test_data,
                [],
                []
            )
    
    def test_publication_figures_generation(self):
        """Test generation of complete publication figure set."""
        # Mock plotly if available
        mock_context = patch('flee_dual_process.dimensionless_visualization.pyo') if hasattr(self.generator, 'pyo') else patch('builtins.print')
        
        with mock_context:
            generated_files = self.generator.generate_publication_figures(
                self.test_data,
                self.temp_dir,
                prefix='test'
            )
        
        self.assertIsInstance(generated_files, dict)
        
        # Check that some files were generated
        self.assertGreater(len(generated_files), 0)
        
        # Check that generated files exist
        for file_type, file_path in generated_files.items():
            if file_path and file_type != 'interactive':  # Interactive might not be generated without plotly
                self.assertTrue(os.path.exists(file_path), 
                              f"Generated file {file_type} does not exist: {file_path}")
    
    def test_plot_configuration_application(self):
        """Test that plot configuration is properly applied."""
        custom_config = PlotConfiguration(
            figsize=(12, 8),
            dpi=150,
            font_size=14,
            color_palette='viridis'
        )
        
        custom_generator = DimensionlessVisualizationGenerator(custom_config)
        
        # Check that configuration is stored
        self.assertEqual(custom_generator.config.figsize, (12, 8))
        self.assertEqual(custom_generator.config.dpi, 150)
        self.assertEqual(custom_generator.config.font_size, 14)
        
        # Test that configuration affects plot creation
        fig = custom_generator.create_data_collapse_plot(
            self.test_data,
            'cognitive_pressure',
            'system2_activation_rate',
            'scenario'
        )
        
        # Check figure size (approximately, due to matplotlib's handling)
        fig_width, fig_height = fig.get_size_inches()
        self.assertAlmostEqual(fig_width, 15, delta=1)  # Data collapse creates wider figure
        
        plt.close(fig)
    
    def test_error_handling_missing_columns(self):
        """Test error handling for missing data columns."""
        # Test with missing dimensionless parameter
        fig = self.generator.create_data_collapse_plot(
            self.test_data,
            'nonexistent_param',
            'system2_activation_rate',
            'scenario'
        )
        
        # Should still create figure but with limited content
        self.assertIsNotNone(fig)
        plt.close(fig)
    
    def test_error_handling_empty_data(self):
        """Test error handling for empty datasets."""
        empty_data = pd.DataFrame()
        
        # Should handle empty data gracefully
        try:
            fig = self.generator.create_data_collapse_plot(
                empty_data,
                'cognitive_pressure',
                'system2_activation_rate',
                'scenario'
            )
            plt.close(fig)
        except Exception as e:
            # Should raise a meaningful error
            self.assertIsInstance(e, (ValueError, KeyError))
    
    def test_scaling_function_fitting_edge_cases(self):
        """Test scaling function fitting with edge cases."""
        # Create data with extreme values
        edge_case_data = pd.DataFrame({
            'cognitive_pressure': [0.001, 0.01, 0.1, 1.0, 10.0],
            'response': [0.001, 0.01, 0.1, 1.0, 10.0]
        })
        
        relationships = [
            ScalingRelationship(
                parameter='cognitive_pressure',
                dependent_variable='response',
                scaling_function='linear',
                fit_parameters={'a': 1.0, 'b': 0.0},
                r_squared=0.99,
                confidence_interval=(0.95, 1.0)
            )
        ]
        
        fig = self.generator.create_scaling_relationship_plot(
            edge_case_data,
            relationships
        )
        
        self.assertIsNotNone(fig)
        plt.close(fig)


class TestPlotConfiguration(unittest.TestCase):
    """Test cases for PlotConfiguration dataclass."""
    
    def test_default_configuration(self):
        """Test default plot configuration values."""
        config = PlotConfiguration()
        
        self.assertEqual(config.figsize, (10, 8))
        self.assertEqual(config.dpi, 300)
        self.assertEqual(config.style, 'seaborn-v0_8-whitegrid')
        self.assertEqual(config.color_palette, 'Set2')
        self.assertEqual(config.font_size, 12)
    
    def test_custom_configuration(self):
        """Test custom plot configuration values."""
        config = PlotConfiguration(
            figsize=(15, 10),
            dpi=150,
            font_size=16,
            color_palette='viridis'
        )
        
        self.assertEqual(config.figsize, (15, 10))
        self.assertEqual(config.dpi, 150)
        self.assertEqual(config.font_size, 16)
        self.assertEqual(config.color_palette, 'viridis')


if __name__ == '__main__':
    # Set matplotlib backend to avoid display issues in tests
    import matplotlib
    matplotlib.use('Agg')
    
    unittest.main()