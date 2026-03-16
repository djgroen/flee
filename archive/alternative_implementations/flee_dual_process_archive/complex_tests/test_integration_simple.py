"""
Simplified Integration Test for End-to-End Pipeline
"""

import unittest
import tempfile
import shutil
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flee_dual_process.topology_generator import LinearTopologyGenerator
from flee_dual_process.scenario_generator import SpikeConflictGenerator
from flee_dual_process.config_manager import ConfigurationManager, ExperimentConfig
from flee_dual_process.experiment_runner import ExperimentRunner
from flee_dual_process.analysis_pipeline import AnalysisPipeline


class TestSimpleIntegration(unittest.TestCase):
    """Simple integration test for the complete pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        
        # Create mock Flee executable
        self.mock_flee_executable = self._create_mock_flee()
        
        # Initialize components
        self.config_manager = ConfigurationManager()
        self.experiment_runner = ExperimentRunner(
            max_parallel=1,
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
    
    def _create_mock_flee(self) -> str:
        """Create a simple mock Flee executable."""
        mock_script = os.path.join(self.temp_dir, "mock_flee.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import os
import csv

def create_mock_output(output_dir):
    """Create minimal mock output."""
    os.makedirs(output_dir, exist_ok=True)
    
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

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        create_mock_output(output_dir)
        print(f"Mock simulation completed: {input_dir} -> {output_dir}")
    else:
        sys.exit(1)
'''
        
        with open(mock_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(mock_script, 0o755)
        return mock_script
    
    def test_complete_pipeline(self):
        """Test complete pipeline from topology generation to analysis."""
        # Step 1: Generate topology
        topology_generator = LinearTopologyGenerator(self.base_config)
        locations_file, routes_file = topology_generator.generate_linear(
            n_nodes=3,
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
            experiment_id='test_integration',
            topology_type='linear',
            topology_params={'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
            scenario_type='spike',
            scenario_params={'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8},
            cognitive_mode='dual_process',
            simulation_params=config,
            replications=1
        )
        
        # Step 5: Run experiment
        results = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
        
        self.assertTrue(results['success'], f"Experiment failed: {results.get('error', 'Unknown error')}")
        self.assertIn('experiment_dir', results)
        
        # Step 6: Verify output files exist
        experiment_dir = results['experiment_dir']
        output_dir = os.path.join(experiment_dir, 'output')
        
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'out.csv')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'cognitive_states.out.0')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'decision_log.out.0')))
        
        # Step 7: Analyze results
        analysis_results = self.analysis_pipeline.process_experiment(experiment_dir)
        
        self.assertIsNotNone(analysis_results)
        self.assertTrue(analysis_results.experiment_id.startswith('test_integration'))
        
        print("✓ Complete pipeline test passed")
        return True
    
    def test_multiple_cognitive_modes(self):
        """Test pipeline with different cognitive modes."""
        cognitive_modes = ['s1_only', 's2_full', 'dual_process']
        successful_runs = 0
        
        for mode in cognitive_modes:
            # Generate topology
            topology_generator = LinearTopologyGenerator(self.base_config)
            locations_file, routes_file = topology_generator.generate_linear(
                n_nodes=3, segment_distance=50.0, start_pop=1000, pop_decay=0.8
            )
            
            # Generate scenario
            scenario_generator = SpikeConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_spike_conflict(
                origin='Origin', start_day=0, peak_intensity=0.8,
                output_dir=os.path.dirname(locations_file)
            )
            
            # Create configuration
            config = self.config_manager.create_cognitive_config(mode)
            
            # Create and run experiment
            experiment_config = ExperimentConfig(
                experiment_id=f'test_{mode}',
                topology_type='linear',
                topology_params={'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                scenario_type='spike',
                scenario_params={'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8},
                cognitive_mode=mode,
                simulation_params=config,
                replications=1
            )
            
            results = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
            
            if results.get('success', False):
                successful_runs += 1
                print(f"✓ Cognitive mode {mode} test passed")
            else:
                print(f"✗ Cognitive mode {mode} test failed: {results.get('error', 'Unknown error')}")
        
        self.assertEqual(successful_runs, len(cognitive_modes), 
                        f"Only {successful_runs}/{len(cognitive_modes)} cognitive modes succeeded")
        
        return True


if __name__ == '__main__':
    unittest.main()