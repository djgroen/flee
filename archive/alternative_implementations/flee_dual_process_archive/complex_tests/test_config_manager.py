"""
Unit tests for ConfigurationManager class.

Tests configuration validation, parameter consistency, and cognitive mode configurations.
"""

import unittest
import tempfile
import os
import yaml
from typing import Dict, Any

from .config_manager import ConfigurationManager, ExperimentConfig


class TestConfigurationManager(unittest.TestCase):
    """Test cases for ConfigurationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigurationManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_with_default_template(self):
        """Test initialization with default base template."""
        cm = ConfigurationManager()
        self.assertIsNotNone(cm.base_template)
        self.assertIn('move_rules', cm.base_template)
        self.assertIn('log_levels', cm.base_template)
        self.assertIn('spawn_rules', cm.base_template)
        self.assertIn('optimisations', cm.base_template)
    
    def test_initialization_with_custom_template(self):
        """Test initialization with custom base template."""
        custom_template = {'custom_section': {'param': 'value'}}
        cm = ConfigurationManager(custom_template)
        self.assertEqual(cm.base_template, custom_template)
    
    def test_cognitive_mode_s1_only(self):
        """Test S1-only cognitive mode configuration."""
        config = self.config_manager.create_cognitive_config('s1_only')
        
        # Check S1-specific settings
        self.assertFalse(config['move_rules']['two_system_decision_making'])
        self.assertEqual(config['move_rules']['awareness_level'], 1)
        self.assertEqual(config['move_rules']['weight_softening'], 0.5)
        self.assertEqual(config['move_rules']['average_social_connectivity'], 0.0)
        
        # Validate configuration
        self.assertTrue(self.config_manager.validate_configuration(config))
    
    def test_cognitive_mode_s2_disconnected(self):
        """Test S2-disconnected cognitive mode configuration."""
        config = self.config_manager.create_cognitive_config('s2_disconnected')
        
        # Check S2-disconnected specific settings
        self.assertTrue(config['move_rules']['two_system_decision_making'])
        self.assertEqual(config['move_rules']['awareness_level'], 3)
        self.assertEqual(config['move_rules']['weight_softening'], 0.1)
        self.assertEqual(config['move_rules']['average_social_connectivity'], 0.0)
        
        # Validate configuration
        self.assertTrue(self.config_manager.validate_configuration(config))
    
    def test_cognitive_mode_s2_full(self):
        """Test S2-full cognitive mode configuration."""
        config = self.config_manager.create_cognitive_config('s2_full')
        
        # Check S2-full specific settings
        self.assertTrue(config['move_rules']['two_system_decision_making'])
        self.assertEqual(config['move_rules']['awareness_level'], 3)
        self.assertEqual(config['move_rules']['weight_softening'], 0.1)
        self.assertEqual(config['move_rules']['average_social_connectivity'], 8.0)
        
        # Validate configuration
        self.assertTrue(self.config_manager.validate_configuration(config))
    
    def test_cognitive_mode_dual_process(self):
        """Test dual-process cognitive mode configuration."""
        config = self.config_manager.create_cognitive_config('dual_process')
        
        # Check dual-process specific settings
        self.assertTrue(config['move_rules']['two_system_decision_making'])
        self.assertEqual(config['move_rules']['awareness_level'], 2)
        self.assertEqual(config['move_rules']['weight_softening'], 0.3)
        self.assertEqual(config['move_rules']['average_social_connectivity'], 3.0)
        self.assertEqual(config['move_rules']['conflict_threshold'], 0.6)
        self.assertEqual(config['move_rules']['recovery_period_max'], 30)
        
        # Validate configuration
        self.assertTrue(self.config_manager.validate_configuration(config))
    
    def test_invalid_cognitive_mode(self):
        """Test error handling for invalid cognitive mode."""
        with self.assertRaises(ValueError) as context:
            self.config_manager.create_cognitive_config('invalid_mode')
        
        self.assertIn("Unknown cognitive mode", str(context.exception))
        self.assertIn("invalid_mode", str(context.exception))
    
    def test_cognitive_mode_with_custom_parameters(self):
        """Test cognitive mode configuration with custom parameter overrides."""
        custom_params = {
            'move_rules': {
                'max_move_speed': 500.0,
                'conflict_weight': 0.5
            },
            'optimisations': {
                'hasten': 5
            }
        }
        
        config = self.config_manager.create_cognitive_config('s1_only', custom_params)
        
        # Check that custom parameters were applied
        self.assertEqual(config['move_rules']['max_move_speed'], 500.0)
        self.assertEqual(config['move_rules']['conflict_weight'], 0.5)
        self.assertEqual(config['optimisations']['hasten'], 5)
        
        # Check that cognitive mode settings are still applied
        self.assertFalse(config['move_rules']['two_system_decision_making'])
        self.assertEqual(config['move_rules']['awareness_level'], 1)
        
        # Validate configuration
        self.assertTrue(self.config_manager.validate_configuration(config))
    
    def test_parameter_validation_awareness_level(self):
        """Test parameter validation for awareness_level."""
        # Valid awareness levels
        for level in [1, 2, 3]:
            config = self.config_manager.create_cognitive_config('s1_only')
            config['move_rules']['awareness_level'] = level
            self.assertTrue(self.config_manager.validate_configuration(config))
        
        # Invalid awareness levels
        invalid_configs = []
        for invalid_level in [0, 4, -1, 1.5, 'invalid']:
            config = self.config_manager.create_cognitive_config('s1_only')
            config['move_rules']['awareness_level'] = invalid_level
            invalid_configs.append(config)
        
        for config in invalid_configs:
            self.assertFalse(self.config_manager.validate_configuration(config))
    
    def test_parameter_validation_social_connectivity(self):
        """Test parameter validation for average_social_connectivity."""
        # Valid social connectivity values
        for connectivity in [0.0, 1.0, 5.0, 10.0]:
            config = self.config_manager.create_cognitive_config('dual_process')
            config['move_rules']['average_social_connectivity'] = connectivity
            self.assertTrue(self.config_manager.validate_configuration(config))
        
        # Invalid social connectivity values
        invalid_configs = []
        for invalid_connectivity in [-1.0, -5.0, 'invalid']:
            config = self.config_manager.create_cognitive_config('dual_process')
            config['move_rules']['average_social_connectivity'] = invalid_connectivity
            invalid_configs.append(config)
        
        for config in invalid_configs:
            self.assertFalse(self.config_manager.validate_configuration(config))
    
    def test_parameter_validation_conflict_threshold(self):
        """Test parameter validation for conflict_threshold."""
        # Valid conflict threshold values
        for threshold in [0.0, 0.5, 1.0]:
            config = self.config_manager.create_cognitive_config('dual_process')
            config['move_rules']['conflict_threshold'] = threshold
            self.assertTrue(self.config_manager.validate_configuration(config))
        
        # Invalid conflict threshold values
        invalid_configs = []
        for invalid_threshold in [-0.1, 1.1, 2.0, 'invalid']:
            config = self.config_manager.create_cognitive_config('dual_process')
            config['move_rules']['conflict_threshold'] = invalid_threshold
            invalid_configs.append(config)
        
        for config in invalid_configs:
            self.assertFalse(self.config_manager.validate_configuration(config))
    
    def test_parameter_validation_recovery_period(self):
        """Test parameter validation for recovery_period_max."""
        # Valid recovery period values
        for period in [1, 10, 30, 100]:
            config = self.config_manager.create_cognitive_config('dual_process')
            config['move_rules']['recovery_period_max'] = period
            self.assertTrue(self.config_manager.validate_configuration(config))
        
        # Invalid recovery period values
        invalid_configs = []
        for invalid_period in [0, -1, 1.5, 'invalid']:
            config = self.config_manager.create_cognitive_config('dual_process')
            config['move_rules']['recovery_period_max'] = invalid_period
            invalid_configs.append(config)
        
        for config in invalid_configs:
            self.assertFalse(self.config_manager.validate_configuration(config))
    
    def test_parameter_validation_weight_softening(self):
        """Test parameter validation for weight_softening."""
        # Valid weight softening values
        for weight in [0.0, 0.5, 1.0]:
            config = self.config_manager.create_cognitive_config('s1_only')
            config['move_rules']['weight_softening'] = weight
            self.assertTrue(self.config_manager.validate_configuration(config))
        
        # Invalid weight softening values
        invalid_configs = []
        for invalid_weight in [-0.1, 1.1, 2.0, 'invalid']:
            config = self.config_manager.create_cognitive_config('s1_only')
            config['move_rules']['weight_softening'] = invalid_weight
            invalid_configs.append(config)
        
        for config in invalid_configs:
            self.assertFalse(self.config_manager.validate_configuration(config))
    
    def test_parameter_validation_boolean_parameters(self):
        """Test parameter validation for boolean parameters."""
        config = self.config_manager.create_cognitive_config('s1_only')
        
        # Valid boolean values
        for bool_val in [True, False]:
            config['move_rules']['two_system_decision_making'] = bool_val
            self.assertTrue(self.config_manager.validate_configuration(config))
        
        # Invalid boolean values
        for invalid_bool in [1, 0, 'true', 'false', 'invalid']:
            config['move_rules']['two_system_decision_making'] = invalid_bool
            self.assertFalse(self.config_manager.validate_configuration(config))
    
    def test_create_simsetting_yml(self):
        """Test creation of simsetting.yml file."""
        config = self.config_manager.create_cognitive_config('dual_process')
        output_path = os.path.join(self.temp_dir, 'simsetting.yml')
        
        self.config_manager.create_simsetting_yml(config, output_path)
        
        # Check that file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Check that file content is valid YAML and matches config
        with open(output_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        self.assertEqual(loaded_config, config)
    
    def test_load_configuration_template(self):
        """Test loading configuration template from file."""
        # Create a test template file
        test_template = {
            'test_section': {
                'param1': 'value1',
                'param2': 42
            }
        }
        
        template_path = os.path.join(self.temp_dir, 'test_template.yml')
        with open(template_path, 'w') as f:
            yaml.dump(test_template, f)
        
        # Load template
        loaded_template = self.config_manager.load_configuration_template(template_path)
        self.assertEqual(loaded_template, test_template)
    
    def test_save_configuration_template(self):
        """Test saving configuration as template file."""
        config = self.config_manager.create_cognitive_config('s2_full')
        template_path = os.path.join(self.temp_dir, 'saved_template.yml')
        
        self.config_manager.save_configuration_template(config, template_path)
        
        # Check that file was created
        self.assertTrue(os.path.exists(template_path))
        
        # Check that saved content matches original config
        with open(template_path, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        self.assertEqual(saved_config, config)
    
    def test_parameter_sweep_generation(self):
        """Test parameter sweep generation."""
        base_config = self.config_manager.create_cognitive_config('s1_only')
        parameter = 'move_rules.awareness_level'
        values = [1, 2, 3]
        
        sweep_configs = self.config_manager.generate_parameter_sweep(base_config, parameter, values)
        
        self.assertEqual(len(sweep_configs), len(values))
        for i, config in enumerate(sweep_configs):
            # Check that the parameter was set correctly
            self.assertEqual(config['move_rules']['awareness_level'], values[i])
            # Check that other parameters remain unchanged
            self.assertFalse(config['move_rules']['two_system_decision_making'])
    
    def test_parameter_sweep_nested_parameter(self):
        """Test parameter sweep with nested parameter names."""
        base_config = self.config_manager.create_cognitive_config('dual_process')
        parameter = 'move_rules.average_social_connectivity'
        values = [0.0, 3.0, 8.0]
        
        sweep_configs = self.config_manager.generate_parameter_sweep(base_config, parameter, values)
        
        self.assertEqual(len(sweep_configs), len(values))
        for i, config in enumerate(sweep_configs):
            self.assertEqual(config['move_rules']['average_social_connectivity'], values[i])
    
    def test_factorial_design_generation(self):
        """Test factorial design generation."""
        base_config = self.config_manager.create_cognitive_config('dual_process')
        factors = {
            'move_rules.awareness_level': [1, 2],
            'move_rules.average_social_connectivity': [0.0, 3.0]
        }
        
        factorial_configs = self.config_manager.generate_factorial_design(base_config, factors)
        
        # Should generate 2 x 2 = 4 configurations
        self.assertEqual(len(factorial_configs), 4)
        
        # Check that all combinations are present
        combinations = [
            (1, 0.0), (1, 3.0), (2, 0.0), (2, 3.0)
        ]
        
        actual_combinations = []
        for config in factorial_configs:
            awareness = config['move_rules']['awareness_level']
            connectivity = config['move_rules']['average_social_connectivity']
            actual_combinations.append((awareness, connectivity))
        
        for combo in combinations:
            self.assertIn(combo, actual_combinations)
    
    def test_cognitive_mode_sweep(self):
        """Test cognitive mode sweep generation."""
        configs = self.config_manager.generate_cognitive_mode_sweep()
        
        # Should generate one config for each cognitive mode
        self.assertEqual(len(configs), len(self.config_manager.COGNITIVE_MODES))
        
        # Check that each config is valid
        for config in configs:
            self.assertTrue(self.config_manager.validate_configuration(config))
    
    def test_save_parameter_sweep(self):
        """Test saving parameter sweep configurations."""
        base_config = self.config_manager.create_cognitive_config('s1_only')
        parameter = 'move_rules.awareness_level'
        values = [1, 2, 3]
        
        sweep_configs = self.config_manager.generate_parameter_sweep(base_config, parameter, values)
        
        output_dir = os.path.join(self.temp_dir, 'sweep_configs')
        file_paths = self.config_manager.save_parameter_sweep(sweep_configs, output_dir, 'test_config')
        
        # Check that files were created
        self.assertEqual(len(file_paths), len(sweep_configs))
        for filepath in file_paths:
            self.assertTrue(os.path.exists(filepath))
    
    def test_validate_parameter_sweep(self):
        """Test parameter sweep validation."""
        # Create some valid configs
        valid_configs = []
        for mode in ['s1_only', 's2_full']:
            config = self.config_manager.create_cognitive_config(mode)
            valid_configs.append(config)
        
        # Create some invalid configs
        invalid_config = self.config_manager.create_cognitive_config('s1_only')
        invalid_config['move_rules']['awareness_level'] = 5  # Invalid value
        
        all_configs = valid_configs + [invalid_config]
        
        summary = self.config_manager.validate_parameter_sweep(all_configs)
        
        self.assertEqual(summary['total_configurations'], 3)
        self.assertEqual(summary['valid_configurations'], 2)
        self.assertEqual(summary['invalid_configurations'], 1)
        self.assertAlmostEqual(summary['validation_rate'], 2/3, places=2)


class TestExperimentConfig(unittest.TestCase):
    """Test cases for ExperimentConfig class."""
    
    def test_experiment_config_creation(self):
        """Test ExperimentConfig creation and serialization."""
        config = ExperimentConfig(
            experiment_id='test_exp_001',
            topology_type='linear',
            topology_params={'n_nodes': 5, 'segment_distance': 10.0},
            scenario_type='spike',
            scenario_params={'origin': 'Town_A', 'start_day': 0, 'peak_intensity': 0.8},
            cognitive_mode='dual_process',
            simulation_params={'max_days': 100},
            replications=3,
            metadata={'description': 'Test experiment'}
        )
        
        # Test basic attributes
        self.assertEqual(config.experiment_id, 'test_exp_001')
        self.assertEqual(config.topology_type, 'linear')
        self.assertEqual(config.scenario_type, 'spike')
        self.assertEqual(config.cognitive_mode, 'dual_process')
        self.assertEqual(config.replications, 3)
    
    def test_experiment_config_to_dict(self):
        """Test ExperimentConfig to_dict method."""
        config = ExperimentConfig(
            experiment_id='test_exp_002',
            topology_type='star',
            topology_params={'n_camps': 4},
            scenario_type='gradual',
            scenario_params={'origin': 'Town_B'},
            cognitive_mode='s2_full',
            simulation_params={'max_days': 50}
        )
        
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['experiment_id'], 'test_exp_002')
        self.assertEqual(config_dict['topology_type'], 'star')
        self.assertEqual(config_dict['cognitive_mode'], 's2_full')
    
    def test_experiment_config_from_dict(self):
        """Test ExperimentConfig from_dict method."""
        config_dict = {
            'experiment_id': 'test_exp_003',
            'topology_type': 'grid',
            'topology_params': {'rows': 3, 'cols': 3},
            'scenario_type': 'cascading',
            'scenario_params': {'origin': 'Town_C'},
            'cognitive_mode': 's1_only',
            'simulation_params': {'max_days': 75},
            'replications': 1,
            'metadata': {}
        }
        
        config = ExperimentConfig.from_dict(config_dict)
        
        self.assertEqual(config.experiment_id, 'test_exp_003')
        self.assertEqual(config.topology_type, 'grid')
        self.assertEqual(config.scenario_type, 'cascading')
        self.assertEqual(config.cognitive_mode, 's1_only')


if __name__ == '__main__':
    unittest.main()