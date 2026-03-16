"""
Test suite for scenario infrastructure components.
"""

import unittest
import tempfile
import os
import shutil
import json
from .comprehensive_scenario_generator import ScenarioGenerator, NetworkConfig, ConflictConfig, PopulationConfig
from .scenario_validation import validate_scenario, GeneralScenarioValidator, HypothesisSpecificValidator


class TestScenarioGenerator(unittest.TestCase):
    """Test the comprehensive scenario generator."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.generator = ScenarioGenerator(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_generate_linear_network(self):
        """Test linear network generation."""
        config = NetworkConfig(
            topology_type='linear',
            parameters={
                'n_nodes': 4,
                'segment_distance': 50.0,
                'start_pop': 10000,
                'pop_decay': 0.8
            },
            output_dir=os.path.join(self.test_dir, 'linear_test')
        )
        
        locations_path, routes_path = self.generator.generate_network(config)
        
        # Check files were created
        self.assertTrue(os.path.exists(locations_path))
        self.assertTrue(os.path.exists(routes_path))
        
        # Check file content
        with open(locations_path, 'r') as f:
            content = f.read()
            self.assertIn('#name', content)
            self.assertIn('location_type', content)
    
    def test_generate_spike_conflict(self):
        """Test spike conflict generation."""
        # First create a simple network
        network_config = NetworkConfig(
            topology_type='linear',
            parameters={'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 5000, 'pop_decay': 0.8},
            output_dir=os.path.join(self.test_dir, 'conflict_test')
        )
        locations_path, _ = self.generator.generate_network(network_config)
        
        # Generate conflict
        conflict_config = ConflictConfig(
            scenario_type='spike',
            parameters={
                'origin': 'Node_0',
                'start_day': 0,
                'peak_intensity': 1.0
            },
            timeline={}
        )
        
        conflicts_path = self.generator.generate_conflict_schedule(conflict_config, locations_path)
        
        # Check conflict file was created
        self.assertTrue(os.path.exists(conflicts_path))
        
        # Check file content
        with open(conflicts_path, 'r') as f:
            content = f.read()
            self.assertIn('#Day', content)
            self.assertIn('Node_0', content)
    
    def test_generate_population_config(self):
        """Test population configuration generation."""
        # First create a simple network
        network_config = NetworkConfig(
            topology_type='linear',
            parameters={'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 5000, 'pop_decay': 0.8},
            output_dir=os.path.join(self.test_dir, 'population_test')
        )
        locations_path, _ = self.generator.generate_network(network_config)
        
        # Generate population config
        pop_config = PopulationConfig(
            total_population=10000,
            distribution_type='uniform',
            cognitive_composition={'s1_only': 0.5, 's2_connected': 0.5},
            parameters={}
        )
        
        pop_path = self.generator.generate_population(pop_config, locations_path)
        
        # Check population file was created
        self.assertTrue(os.path.exists(pop_path))
        
        # Check file content
        with open(pop_path, 'r') as f:
            pop_data = json.load(f)
            self.assertEqual(pop_data['total_population'], 10000)
            self.assertIn('cognitive_composition', pop_data)
    
    def test_generate_h1_scenario(self):
        """Test H1 hypothesis scenario generation."""
        scenario_dir = self.generator.generate_hypothesis_scenario('H1', 'h1_1_multi_destination')
        
        # Check scenario directory was created
        self.assertTrue(os.path.exists(scenario_dir))
        
        # Check required files exist
        required_files = ['locations.csv', 'routes.csv', 'conflicts.csv', 'sim_period.csv']
        for file in required_files:
            file_path = os.path.join(scenario_dir, file)
            self.assertTrue(os.path.exists(file_path), f"Missing file: {file}")


class TestScenarioValidation(unittest.TestCase):
    """Test the scenario validation framework."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.generator = ScenarioGenerator(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_validate_complete_scenario(self):
        """Test validation of a complete scenario."""
        # Generate a complete H1 scenario
        scenario_dir = self.generator.generate_hypothesis_scenario('H1', 'h1_1_multi_destination')
        
        # Validate the scenario
        result = validate_scenario(scenario_dir, 'H1')
        
        # Check validation passed
        if not result.is_valid:
            print(f"Validation errors: {result.errors}")
            print(f"Validation warnings: {result.warnings}")
        
        # Should be valid (warnings are OK)
        self.assertTrue(result.is_valid or len(result.errors) == 0)
    
    def test_general_validator(self):
        """Test general scenario validation."""
        # Generate a basic scenario
        scenario_dir = self.generator.generate_hypothesis_scenario('H1', 'h1_1_multi_destination')
        
        validator = GeneralScenarioValidator()
        result = validator.validate(scenario_dir)
        
        # Should pass general validation
        self.assertTrue(result.is_valid or len(result.errors) == 0)
        self.assertIn('locations', result.details)
        self.assertIn('routes', result.details)
    
    def test_h1_specific_validator(self):
        """Test H1-specific validation."""
        # Generate H1 scenario
        scenario_dir = self.generator.generate_hypothesis_scenario('H1', 'h1_1_multi_destination')
        
        validator = HypothesisSpecificValidator('H1')
        result = validator.validate(scenario_dir)
        
        # Should pass H1-specific validation
        self.assertTrue(result.is_valid or len(result.errors) == 0)
        self.assertIn('multiple_destinations', result.details)
    
    def test_check_multiple_destinations(self):
        """Test multiple destinations check for H1."""
        # Generate H1 scenario (should have multiple camps)
        scenario_dir = self.generator.generate_hypothesis_scenario('H1', 'h1_1_multi_destination')
        
        validator = HypothesisSpecificValidator('H1')
        result = validator.check_multiple_destinations_exist(scenario_dir)
        
        # Should find multiple destinations
        self.assertTrue(result.is_valid)
        self.assertGreaterEqual(result.details['camp_count'], 2)
    
    def test_invalid_scenario_detection(self):
        """Test detection of invalid scenarios."""
        # Create an invalid scenario (missing files)
        invalid_dir = os.path.join(self.test_dir, 'invalid_scenario')
        os.makedirs(invalid_dir, exist_ok=True)
        
        # Only create locations.csv, missing other required files
        locations_path = os.path.join(invalid_dir, 'locations.csv')
        with open(locations_path, 'w') as f:
            f.write('#name,region,country,lat,lon,location_type,conflict_date,population/capacity\n')
            f.write('Origin,region1,country1,10.0,20.0,town,2023-01-01,10000\n')
        
        # Validate should fail
        result = validate_scenario(invalid_dir)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)


if __name__ == '__main__':
    unittest.main()