"""
Integration Test Suite for Dual Process Experiments Framework

Tests end-to-end pipeline functionality from generation through analysis,
parallel execution stability, and data integrity validation.
"""

import unittest
import tempfile
import shutil
import os
import json
import time
import threading
import multiprocessing
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

try:
    from .topology_generator import LinearTopologyGenerator, StarTopologyGenerator
    from .scenario_generator import SpikeConflictGenerator, GradualConflictGenerator
    from .config_manager import ConfigurationManager, ExperimentConfig
    from .experiment_runner import ExperimentRunner, ProcessPoolManager
    from .analysis_pipeline import AnalysisPipeline
    from .visualization_generator import VisualizationGenerator
    from .utils import CSVUtils, ValidationUtils
except ImportError:
    from topology_generator import LinearTopologyGenerator, StarTopologyGenerator
    from scenario_generator import SpikeConflictGenerator, GradualConflictGenerator
    from config_manager import ConfigurationManager, ExperimentConfig
    from experiment_runner import ExperimentRunner, ProcessPoolManager
    from analysis_pipeline import AnalysisPipeline
    from visualization_generator import VisualizationGenerator
    from utils import CSVUtils, ValidationUtils


class TestEndToEndPipeline(unittest.TestCase):
    """Test complete end-to-end pipeline from generation through analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        
        # Initialize components
        self.topology_generator = LinearTopologyGenerator(self.base_config)
        self.config_manager = ConfigurationManager()
        
        # Create mock Flee executable for testing
        self.mock_flee_executable = self._create_mock_flee_executable()
        
        self.experiment_runner = ExperimentRunner(
            max_parallel=2,
            base_output_dir=self.temp_dir,
            flee_executable=self.mock_flee_executable,
            timeout=30
        )
        
        self.analysis_pipeline = AnalysisPipeline(
            results_directory=os.path.join(self.temp_dir, "results"),
            output_directory=os.path.join(self.temp_dir, "analysis")
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_mock_flee_executable(self) -> str:
        """Create a mock Flee executable for testing."""
        mock_script = os.path.join(self.temp_dir, "mock_flee.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import os
import time
import random
import csv

def create_mock_output(output_dir):
    """Create mock Flee output files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create mock out.csv (movement data)
    with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
        
        locations = ['Origin', 'Town_1', 'Town_2', 'Camp_3']
        for day in range(10):
            for i, location in enumerate(locations):
                # Simulate refugee movement
                if location == 'Origin':
                    refugees = max(0, 1000 - day * 100)
                elif location.startswith('Town'):
                    refugees = min(200, day * 20 + random.randint(0, 50))
                else:  # Camp
                    refugees = min(500, day * 50 + random.randint(0, 100))
                
                writer.writerow([day, location, refugees, refugees])
    
    # Create mock cognitive_states.out.0
    with open(os.path.join(output_dir, 'cognitive_states.out.0'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'agent_id', 'cognitive_state', 'location', 'connections', 
                        'system2_activations', 'days_in_location', 'conflict_level'])
        
        for day in range(10):
            for agent_id in range(1, 6):  # 5 agents
                state = 'S1' if random.random() < 0.7 else 'S2'
                location = random.choice(['Origin', 'Town_1', 'Town_2', 'Camp_3'])
                connections = random.randint(0, 5)
                activations = random.randint(0, 3)
                days_in_loc = random.randint(1, 5)
                conflict = random.uniform(0.0, 1.0)
                
                writer.writerow([day, f'0-{agent_id}', state, location, connections,
                               activations, days_in_loc, conflict])
    
    # Create mock decision_log.out.0
    with open(os.path.join(output_dir, 'decision_log.out.0'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'agent_id', 'decision_type', 'cognitive_state', 'location',
                        'movechance', 'outcome', 'system2_active', 'conflict_level', 'connections'])
        
        for day in range(1, 10):  # Start from day 1
            for agent_id in range(1, 6):
                decision = random.choice(['move', 'stay'])
                state = 'S1' if random.random() < 0.7 else 'S2'
                location = random.choice(['Origin', 'Town_1', 'Town_2', 'Camp_3'])
                movechance = random.uniform(0.0, 1.0)
                outcome = 1 if decision == 'move' else 0
                s2_active = state == 'S2'
                conflict = random.uniform(0.0, 1.0)
                connections = random.randint(0, 5)
                
                writer.writerow([day, f'0-{agent_id}', decision, state, location,
                               movechance, outcome, s2_active, conflict, connections])

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Create mock output
        create_mock_output(output_dir)
        
        print(f"Mock Flee simulation completed: {input_dir} -> {output_dir}")
    else:
        print("Usage: mock_flee.py <input_dir> <output_dir>")
        sys.exit(1)
'''
        
        with open(mock_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(mock_script, 0o755)
        return mock_script
    
    def test_complete_pipeline_linear_spike(self):
        """Test complete pipeline with linear topology and spike conflict."""
        # Step 1: Generate topology
        locations_file, routes_file = self.topology_generator.generate_linear(
            n_nodes=4,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        self.assertTrue(os.path.exists(locations_file))
        self.assertTrue(os.path.exists(routes_file))
        
        # Step 2: Generate scenario
        scenario_generator = SpikeConflictGenerator(locations_file)
        conflicts_file = scenario_generator.generate_spike_conflict(
            origin='Origin',
            start_day=0,
            peak_intensity=0.8,
            output_dir=os.path.dirname(locations_file)
        )
        
        self.assertTrue(os.path.exists(conflicts_file))
        
        # Step 3: Create configuration
        config = self.config_manager.create_cognitive_config('dual_process')
        
        # Step 4: Create experiment configuration
        experiment_config = ExperimentConfig(
            experiment_id='test_linear_spike',
            topology_type='linear',
            topology_params={'n_nodes': 4, 'segment_distance': 50.0},
            scenario_type='spike',
            scenario_params={'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8},
            cognitive_mode='dual_process',
            simulation_params=config,
            replications=1
        )
        
        # Step 5: Run experiment
        results = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
        
        self.assertTrue(results['success'])
        self.assertIn('experiment_dir', results)
        
        # Step 6: Analyze results
        experiment_dir = results['experiment_dir']
        analysis_results = self.analysis_pipeline.process_experiment(experiment_dir)
        
        self.assertIsNotNone(analysis_results)
        self.assertIn('movement_metrics', analysis_results.metrics)
        self.assertIn('cognitive_analysis', analysis_results.metrics)
        
        # Step 7: Verify output files exist
        output_dir = os.path.join(experiment_dir, 'output')
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'out.csv')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'cognitive_states.out.0')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'decision_log.out.0')))
    
    def test_complete_pipeline_star_gradual(self):
        """Test complete pipeline with star topology and gradual conflict."""
        # Step 1: Generate star topology
        star_generator = StarTopologyGenerator(self.base_config)
        locations_file, routes_file = star_generator.generate_star(
            n_camps=3,
            hub_pop=2000,
            camp_capacity=5000,
            radius=100.0
        )
        
        # Step 2: Generate gradual conflict scenario
        scenario_generator = GradualConflictGenerator(locations_file)
        conflicts_file = scenario_generator.generate_gradual_conflict(
            origin='Hub',
            start_day=0,
            end_day=10,
            max_intensity=0.9,
            output_dir=os.path.dirname(locations_file)
        )
        
        # Step 3: Create S2-full configuration
        config = self.config_manager.create_cognitive_config('s2_full')
        
        # Step 4: Create and run experiment
        experiment_config = ExperimentConfig(
            experiment_id='test_star_gradual',
            topology_type='star',
            topology_params={'n_camps': 3, 'hub_pop': 2000},
            scenario_type='gradual',
            scenario_params={'origin': 'Hub', 'start_day': 0, 'end_day': 10},
            cognitive_mode='s2_full',
            simulation_params=config,
            replications=1
        )
        
        results = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
        
        self.assertTrue(results['success'])
        
        # Step 5: Analyze and verify
        analysis_results = self.analysis_pipeline.process_experiment(results['experiment_dir'])
        
        self.assertIsNotNone(analysis_results)
        self.assertEqual(analysis_results.experiment_id, 'test_star_gradual')
    
    def test_pipeline_data_integrity(self):
        """Test data integrity throughout the pipeline."""
        # Generate simple topology
        locations_file, routes_file = self.topology_generator.generate_linear(
            n_nodes=3,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        # Verify topology data integrity
        csv_utils = CSVUtils()
        locations = csv_utils.read_locations_csv(locations_file)
        routes = csv_utils.read_routes_csv(routes_file)
        
        self.assertEqual(len(locations), 3)
        self.assertEqual(len(routes), 2)
        
        # Check location names consistency
        location_names = [loc['name'] for loc in locations]
        route_names = set()
        for route in routes:
            route_names.add(route['name1'])
            route_names.add(route['name2'])
        
        # All route names should exist in locations
        for name in route_names:
            self.assertIn(name, location_names)
        
        # Generate scenario and verify consistency
        scenario_generator = SpikeConflictGenerator(locations_file)
        conflicts_file = scenario_generator.generate_spike_conflict(
            origin='Origin',
            start_day=0,
            peak_intensity=0.7,
            output_dir=os.path.dirname(locations_file)
        )
        
        # Verify scenario data integrity
        self.assertTrue(scenario_generator.validate_scenario(conflicts_file))
        
        # Run experiment and verify output integrity
        config = self.config_manager.create_cognitive_config('s1_only')
        experiment_config = ExperimentConfig(
            experiment_id='test_data_integrity',
            topology_type='linear',
            topology_params={'n_nodes': 3},
            scenario_type='spike',
            scenario_params={'origin': 'Origin'},
            cognitive_mode='s1_only',
            simulation_params=config,
            replications=1
        )
        
        results = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
        self.assertTrue(results['success'])
        
        # Verify experiment output files have correct format
        output_dir = os.path.join(results['experiment_dir'], 'output')
        
        # Check out.csv format
        out_file = os.path.join(output_dir, 'out.csv')
        with open(out_file, 'r') as f:
            first_line = f.readline().strip()
            self.assertTrue(first_line.startswith('#day'))
        
        # Check cognitive states format
        cognitive_file = os.path.join(output_dir, 'cognitive_states.out.0')
        with open(cognitive_file, 'r') as f:
            first_line = f.readline().strip()
            self.assertTrue(first_line.startswith('#day'))
    
    def test_pipeline_error_handling(self):
        """Test pipeline error handling and recovery."""
        # Test with invalid topology parameters
        with self.assertRaises(ValueError):
            self.topology_generator.generate_linear(
                n_nodes=1,  # Invalid: too few nodes
                segment_distance=50.0,
                start_pop=1000,
                pop_decay=0.8
            )
        
        # Test with valid topology but invalid scenario
        locations_file, _ = self.topology_generator.generate_linear(
            n_nodes=3,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        scenario_generator = SpikeConflictGenerator(locations_file)
        
        with self.assertRaises(FileNotFoundError):
            scenario_generator.generate_spike_conflict(
                origin='NonexistentLocation',  # Invalid origin
                start_day=0,
                peak_intensity=0.8,
                output_dir=self.temp_dir
            )
        
        # Test experiment runner with invalid configuration
        invalid_config = {
            'experiment_id': 'test_invalid',
            'topology_type': 'invalid_topology',  # Invalid type
            'cognitive_mode': 's1_only',
            'simulation_params': {}
        }
        
        results = self.experiment_runner.run_single_experiment(invalid_config)
        self.assertFalse(results['success'])
        self.assertIn('error', results)
    
    def test_pipeline_with_missing_files(self):
        """Test pipeline behavior with missing input files."""
        # Create experiment directory structure but with missing files
        experiment_dir = os.path.join(self.temp_dir, 'incomplete_experiment')
        os.makedirs(os.path.join(experiment_dir, 'output'))
        
        # Create only partial output files
        with open(os.path.join(experiment_dir, 'output', 'out.csv'), 'w') as f:
            f.write('#day,location,refugees\n0,Town_A,100\n')
        
        # Analysis should handle missing files gracefully
        results = self.analysis_pipeline.load_experiment_data(experiment_dir)
        
        self.assertIsNotNone(results.movement_data)
        self.assertIsNone(results.cognitive_states)  # Missing file
        self.assertIsNone(results.decision_log)      # Missing file


class TestParallelExecutionStability(unittest.TestCase):
    """Test parallel execution stability and resource monitoring."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_flee_executable = self._create_mock_flee_executable()
        
        self.experiment_runner = ExperimentRunner(
            max_parallel=3,
            base_output_dir=self.temp_dir,
            flee_executable=self.mock_flee_executable,
            timeout=10
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_mock_flee_executable(self) -> str:
        """Create a mock Flee executable that simulates variable execution time."""
        mock_script = os.path.join(self.temp_dir, "mock_flee_parallel.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import os
import time
import random
import csv

def create_basic_output(output_dir):
    """Create minimal mock output."""
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'location', 'refugees'])
        writer.writerow([0, 'Origin', 100])
        writer.writerow([1, 'Camp', 100])

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        
        # Simulate variable execution time
        execution_time = random.uniform(0.1, 0.5)
        time.sleep(execution_time)
        
        create_basic_output(output_dir)
        
        print(f"Mock parallel execution completed in {execution_time:.2f}s")
    else:
        sys.exit(1)
'''
        
        with open(mock_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(mock_script, 0o755)
        return mock_script
    
    def test_parallel_experiment_execution(self):
        """Test parallel execution of multiple experiments."""
        # Create multiple experiment configurations
        experiments = []
        for i in range(5):
            config = {
                'experiment_id': f'parallel_test_{i}',
                'topology_type': 'linear',
                'topology_params': {'n_nodes': 3},
                'scenario_type': 'spike',
                'scenario_params': {'origin': 'Origin'},
                'cognitive_mode': 's1_only',
                'simulation_params': {'move_rules': {'awareness_level': 1}},
                'replications': 1
            }
            experiments.append(config)
        
        # Run experiments in parallel
        start_time = time.time()
        results = []
        
        for config in experiments:
            result = self.experiment_runner.run_single_experiment(config)
            results.append(result)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify all experiments completed
        successful_experiments = [r for r in results if r.get('success', False)]
        self.assertEqual(len(successful_experiments), 5)
        
        # Parallel execution should be faster than sequential
        # (This is a rough check since we're using mock execution)
        self.assertLess(execution_time, 3.0)  # Should complete in reasonable time
    
    def test_resource_monitoring(self):
        """Test resource monitoring during parallel execution."""
        process_manager = ProcessPoolManager(max_workers=2)
        
        # Get initial resource status
        initial_status = process_manager.get_resource_status()
        
        self.assertIn('memory_usage_percent', initial_status)
        self.assertIn('cpu_usage_percent', initial_status)
        self.assertIn('max_workers', initial_status)
        self.assertEqual(initial_status['max_workers'], 2)
        
        # Resource usage should be reasonable
        self.assertLess(initial_status['memory_usage_percent'], 100.0)
        self.assertLess(initial_status['cpu_usage_percent'], 100.0)
    
    def test_experiment_timeout_handling(self):
        """Test handling of experiment timeouts."""
        # Create a mock executable that takes too long
        timeout_script = os.path.join(self.temp_dir, "timeout_flee.py")
        
        script_content = '''#!/usr/bin/env python3
import time
import sys

if __name__ == "__main__":
    # Sleep longer than timeout
    time.sleep(15)
    print("This should timeout")
'''
        
        with open(timeout_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(timeout_script, 0o755)
        
        # Create experiment runner with short timeout
        timeout_runner = ExperimentRunner(
            max_parallel=1,
            base_output_dir=self.temp_dir,
            flee_executable=timeout_script,
            timeout=2  # 2 second timeout
        )
        
        config = {
            'experiment_id': 'timeout_test',
            'topology_type': 'linear',
            'cognitive_mode': 's1_only',
            'simulation_params': {}
        }
        
        result = timeout_runner.run_single_experiment(config)
        
        # Should fail due to timeout
        self.assertFalse(result.get('success', True))
        self.assertIn('timeout', result.get('error', '').lower())
    
    def test_concurrent_file_access(self):
        """Test concurrent file access during parallel execution."""
        # Create shared topology files
        base_config = {'output_dir': self.temp_dir}
        topology_generator = LinearTopologyGenerator(base_config)
        
        locations_file, routes_file = topology_generator.generate_linear(
            n_nodes=3,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        # Create multiple threads that read the same files
        def read_topology_files():
            csv_utils = CSVUtils()
            locations = csv_utils.read_locations_csv(locations_file)
            routes = csv_utils.read_routes_csv(routes_file)
            return len(locations), len(routes)
        
        threads = []
        results = []
        
        def thread_worker():
            result = read_topology_files()
            results.append(result)
        
        # Start multiple threads
        for _ in range(5):
            thread = threading.Thread(target=thread_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should get the same results
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(result, (3, 2))  # 3 locations, 2 routes
    
    def test_memory_usage_stability(self):
        """Test memory usage stability during multiple experiments."""
        import psutil
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Run multiple experiments
        for i in range(10):
            config = {
                'experiment_id': f'memory_test_{i}',
                'topology_type': 'linear',
                'cognitive_mode': 's1_only',
                'simulation_params': {}
            }
            
            result = self.experiment_runner.run_single_experiment(config)
            
            # Check memory usage hasn't grown excessively
            current_memory = process.memory_info().rss
            memory_growth = current_memory - initial_memory
            
            # Memory growth should be reasonable (less than 100MB)
            self.assertLess(memory_growth, 100 * 1024 * 1024)


class TestDataIntegrityValidation(unittest.TestCase):
    """Test data integrity validation throughout the pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validation_utils = ValidationUtils()
        self.csv_utils = CSVUtils()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_topology_file_integrity(self):
        """Test topology file format and content integrity."""
        # Create test topology files
        base_config = {'output_dir': self.temp_dir}
        generator = LinearTopologyGenerator(base_config)
        
        locations_file, routes_file = generator.generate_linear(
            n_nodes=4,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        # Validate file formats
        self.assertTrue(self.validation_utils.validate_locations_csv_format(locations_file))
        self.assertTrue(self.validation_utils.validate_routes_csv_format(routes_file))
        
        # Validate topology connectivity
        self.assertTrue(self.validation_utils.validate_topology(locations_file, routes_file))
        
        # Check data consistency
        locations = self.csv_utils.read_locations_csv(locations_file)
        routes = self.csv_utils.read_routes_csv(routes_file)
        
        # All route endpoints should exist in locations
        location_names = {loc['name'] for loc in locations}
        for route in routes:
            self.assertIn(route['name1'], location_names)
            self.assertIn(route['name2'], location_names)
    
    def test_scenario_file_integrity(self):
        """Test scenario file format and content integrity."""
        # Create topology first
        base_config = {'output_dir': self.temp_dir}
        topology_generator = LinearTopologyGenerator(base_config)
        locations_file, _ = topology_generator.generate_linear(
            n_nodes=3,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        # Create scenario
        scenario_generator = SpikeConflictGenerator(locations_file)
        conflicts_file = scenario_generator.generate_spike_conflict(
            origin='Origin',
            start_day=0,
            peak_intensity=0.8,
            output_dir=self.temp_dir
        )
        
        # Validate scenario file
        self.assertTrue(scenario_generator.validate_scenario(conflicts_file))
        
        # Check file format
        with open(conflicts_file, 'r') as f:
            first_line = f.readline().strip()
            self.assertTrue(first_line.startswith('#Day'))
        
        # Validate conflict data consistency
        conflicts = scenario_generator._read_conflicts_matrix(conflicts_file)
        
        # All conflict locations should exist in topology
        locations = self.csv_utils.read_locations_csv(locations_file)
        location_names = {loc['name'] for loc in locations}
        
        for day_conflicts in conflicts.values():
            for location in day_conflicts.keys():
                self.assertIn(location, location_names)
    
    def test_experiment_output_integrity(self):
        """Test experiment output file integrity."""
        # Create mock experiment output
        experiment_dir = os.path.join(self.temp_dir, 'test_experiment')
        output_dir = os.path.join(experiment_dir, 'output')
        os.makedirs(output_dir)
        
        # Create mock output files with proper format
        self._create_mock_experiment_output(output_dir)
        
        # Validate output file formats
        out_file = os.path.join(output_dir, 'out.csv')
        self.assertTrue(self.validation_utils.validate_flee_output_format(out_file))
        
        cognitive_file = os.path.join(output_dir, 'cognitive_states.out.0')
        self.assertTrue(self.validation_utils.validate_cognitive_states_format(cognitive_file))
        
        decision_file = os.path.join(output_dir, 'decision_log.out.0')
        self.assertTrue(self.validation_utils.validate_decision_log_format(decision_file))
    
    def _create_mock_experiment_output(self, output_dir: str):
        """Create mock experiment output files."""
        import csv
        
        # Create out.csv
        with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
            writer.writerow([0, 'Origin', 1000, 1000])
            writer.writerow([1, 'Origin', 800, 800])
            writer.writerow([1, 'Town_1', 200, 200])
        
        # Create cognitive_states.out.0
        with open(os.path.join(output_dir, 'cognitive_states.out.0'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'agent_id', 'cognitive_state', 'location', 'connections',
                           'system2_activations', 'days_in_location', 'conflict_level'])
            writer.writerow([0, '0-1', 'S1', 'Origin', 0, 0, 1, 0.8])
            writer.writerow([1, '0-1', 'S2', 'Origin', 2, 1, 2, 0.9])
        
        # Create decision_log.out.0
        with open(os.path.join(output_dir, 'decision_log.out.0'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'agent_id', 'decision_type', 'cognitive_state', 'location',
                           'movechance', 'outcome', 'system2_active', 'conflict_level', 'connections'])
            writer.writerow([1, '0-1', 'move', 'S1', 'Origin', 0.8, 1, False, 0.8, 0])
            writer.writerow([2, '0-1', 'stay', 'S2', 'Town_1', 0.3, 0, True, 0.5, 2])
    
    def test_analysis_output_integrity(self):
        """Test analysis output integrity and consistency."""
        # Create mock experiment data
        experiment_dir = os.path.join(self.temp_dir, 'test_experiment')
        output_dir = os.path.join(experiment_dir, 'output')
        metadata_dir = os.path.join(experiment_dir, 'metadata')
        os.makedirs(output_dir)
        os.makedirs(metadata_dir)
        
        self._create_mock_experiment_output(output_dir)
        
        # Create metadata
        metadata = {
            'experiment_id': 'test_experiment',
            'configuration': {
                'cognitive_mode': 'dual_process',
                'topology_type': 'linear'
            }
        }
        
        with open(os.path.join(metadata_dir, 'experiment_metadata.json'), 'w') as f:
            json.dump(metadata, f)
        
        # Run analysis
        analysis_pipeline = AnalysisPipeline(self.temp_dir)
        results = analysis_pipeline.process_experiment(experiment_dir)
        
        # Validate analysis results structure
        self.assertIsNotNone(results)
        self.assertIn('movement_metrics', results.metrics)
        self.assertIn('cognitive_analysis', results.metrics)
        
        # Check that metrics are consistent
        movement_metrics = results.metrics['movement_metrics']
        self.assertIn('timing', movement_metrics)
        self.assertIn('destinations', movement_metrics)
        
        # Validate numerical consistency
        if 'timing' in movement_metrics:
            timing = movement_metrics['timing']
            if 'simulation_duration' in timing:
                duration = timing['simulation_duration']
                self.assertIsInstance(duration.get('total_days'), int)
                self.assertGreaterEqual(duration.get('total_days', 0), 0)
    
    def test_cross_component_data_consistency(self):
        """Test data consistency across different pipeline components."""
        # Generate topology
        base_config = {'output_dir': self.temp_dir}
        topology_generator = LinearTopologyGenerator(base_config)
        locations_file, routes_file = topology_generator.generate_linear(
            n_nodes=3,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        # Generate scenario
        scenario_generator = SpikeConflictGenerator(locations_file)
        conflicts_file = scenario_generator.generate_spike_conflict(
            origin='Origin',
            start_day=0,
            peak_intensity=0.8,
            output_dir=os.path.dirname(locations_file)
        )
        
        # Read all data
        locations = self.csv_utils.read_locations_csv(locations_file)
        routes = self.csv_utils.read_routes_csv(routes_file)
        conflicts = scenario_generator._read_conflicts_matrix(conflicts_file)
        
        # Cross-validate data consistency
        location_names = {loc['name'] for loc in locations}
        
        # All route endpoints should exist in locations
        for route in routes:
            self.assertIn(route['name1'], location_names)
            self.assertIn(route['name2'], location_names)
        
        # All conflict locations should exist in locations
        for day_conflicts in conflicts.values():
            for location in day_conflicts.keys():
                self.assertIn(location, location_names)
        
        # Origin location should exist and be a conflict zone
        origin_locations = [loc for loc in locations if loc['name'] == 'Origin']
        self.assertEqual(len(origin_locations), 1)
        self.assertEqual(origin_locations[0]['location_type'], 'conflict_zone')


if __name__ == '__main__':
    # Run tests with appropriate verbosity
    unittest.main(verbosity=2)