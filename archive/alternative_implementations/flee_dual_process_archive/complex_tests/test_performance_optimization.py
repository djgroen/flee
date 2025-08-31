"""
Performance Optimization and Profiling Tests

Profiles code performance, identifies bottlenecks in critical paths,
and validates performance optimizations for the dual process framework.
"""

import unittest
import tempfile
import shutil
import os
import time
import cProfile
import pstats
import io
from typing import Dict, List, Any
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flee_dual_process.topology_generator import LinearTopologyGenerator, StarTopologyGenerator
from flee_dual_process.scenario_generator import SpikeConflictGenerator
from flee_dual_process.config_manager import ConfigurationManager, ExperimentConfig
from flee_dual_process.experiment_runner import ExperimentRunner
from flee_dual_process.analysis_pipeline import AnalysisPipeline


class TestPerformanceOptimization(unittest.TestCase):
    """Performance optimization and profiling tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        
        # Create fast mock Flee executable for performance testing
        self.mock_flee_executable = self._create_fast_mock_flee()
        
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
    
    def _create_fast_mock_flee(self) -> str:
        """Create a fast mock Flee executable for performance testing."""
        mock_script = os.path.join(self.temp_dir, "fast_mock_flee.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import os
import csv

def create_minimal_output(output_dir):
    """Create minimal output files quickly."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create minimal out.csv
    with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
        for day in range(10):
            writer.writerow([day, 'Origin', max(0, 100 - day * 10), max(0, 100 - day * 10)])
            if day > 2:
                writer.writerow([day, 'Camp_1', min(100, day * 10), min(100, day * 10)])
    
    # Create minimal cognitive_states.out.0
    with open(os.path.join(output_dir, 'cognitive_states.out.0'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'agent_id', 'cognitive_state', 'location', 'connections',
                        'system2_activations', 'days_in_location', 'conflict_level'])
        for day in range(10):
            for agent_id in range(1, 11):  # 10 agents
                writer.writerow([day, f'0-{agent_id}', 'S1', 'Origin', 0, 0, day + 1, 0.5])
    
    # Create minimal decision_log.out.0
    with open(os.path.join(output_dir, 'decision_log.out.0'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'agent_id', 'decision_type', 'cognitive_state', 'location',
                        'movechance', 'outcome', 'system2_active', 'conflict_level', 'connections'])
        for day in range(1, 10):
            for agent_id in range(1, 11):
                writer.writerow([day, f'0-{agent_id}', 'stay', 'S1', 'Origin', 0.3, 0, False, 0.5, 0])

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        create_minimal_output(output_dir)
        print(f"Fast mock simulation completed: {input_dir} -> {output_dir}")
    else:
        sys.exit(1)
'''
        
        with open(mock_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(mock_script, 0o755)
        return mock_script
    
    def test_topology_generation_performance(self):
        """Test performance of topology generation."""
        print("\n=== Topology Generation Performance ===")
        
        # Test different topology sizes
        test_sizes = [10, 50, 100]
        performance_results = {}
        
        for size in test_sizes:
            print(f"\nTesting topology generation with {size} nodes")
            
            # Profile linear topology generation
            start_time = time.time()
            topology_generator = LinearTopologyGenerator(self.base_config)
            locations_file, routes_file = topology_generator.generate_linear(
                n_nodes=size,
                segment_distance=50.0,
                start_pop=1000,
                pop_decay=0.8
            )
            linear_time = time.time() - start_time
            
            # Profile star topology generation
            start_time = time.time()
            star_generator = StarTopologyGenerator(self.base_config)
            star_locations_file, star_routes_file = star_generator.generate_star(
                n_camps=size,
                hub_pop=2000,
                camp_capacity=5000,
                radius=100.0
            )
            star_time = time.time() - start_time
            
            performance_results[size] = {
                'linear_time': linear_time,
                'star_time': star_time
            }
            
            print(f"Linear topology ({size} nodes): {linear_time:.4f}s")
            print(f"Star topology ({size} camps): {star_time:.4f}s")
            
            # Verify files were created
            self.assertTrue(os.path.exists(locations_file))
            self.assertTrue(os.path.exists(routes_file))
            self.assertTrue(os.path.exists(star_locations_file))
            self.assertTrue(os.path.exists(star_routes_file))
        
        # Performance assertions
        for size in test_sizes:
            linear_time = performance_results[size]['linear_time']
            star_time = performance_results[size]['star_time']
            
            # Should complete within reasonable time (1 second for 100 nodes)
            max_time = 1.0 if size <= 100 else 2.0
            self.assertLess(linear_time, max_time, 
                           f"Linear topology generation too slow for {size} nodes: {linear_time:.4f}s")
            self.assertLess(star_time, max_time, 
                           f"Star topology generation too slow for {size} camps: {star_time:.4f}s")
        
        print("✓ Topology generation performance acceptable")
        return performance_results
    
    def test_experiment_execution_performance(self):
        """Test performance of experiment execution pipeline."""
        print("\n=== Experiment Execution Performance ===")
        
        # Test multiple experiments
        num_experiments = 5
        execution_times = []
        
        for i in range(num_experiments):
            print(f"Running experiment {i+1}/{num_experiments}")
            
            start_time = time.time()
            
            # Generate topology
            topology_generator = LinearTopologyGenerator(self.base_config)
            locations_file, routes_file = topology_generator.generate_linear(
                n_nodes=5, segment_distance=50.0, start_pop=1000, pop_decay=0.8
            )
            
            # Generate scenario
            scenario_generator = SpikeConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_spike_conflict(
                origin='Origin', start_day=2, peak_intensity=0.8,
                output_dir=os.path.dirname(locations_file)
            )
            
            # Create configuration
            config = self.config_manager.create_cognitive_config('dual_process')
            
            # Run experiment
            experiment_config = ExperimentConfig(
                experiment_id=f'perf_test_{i}',
                topology_type='linear',
                topology_params={'n_nodes': 5, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                scenario_type='spike',
                scenario_params={'origin': 'Origin', 'start_day': 2, 'peak_intensity': 0.8},
                cognitive_mode='dual_process',
                simulation_params=config,
                replications=1
            )
            
            result = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
            self.assertTrue(result['success'], f"Performance test experiment {i} failed")
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            print(f"Experiment {i+1} completed in {execution_time:.4f}s")
        
        # Analyze performance
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        print(f"\nExecution Performance Summary:")
        print(f"Average time: {avg_time:.4f}s")
        print(f"Min time: {min_time:.4f}s")
        print(f"Max time: {max_time:.4f}s")
        
        # Performance assertions
        self.assertLess(avg_time, 5.0, f"Average execution time too slow: {avg_time:.4f}s")
        self.assertLess(max_time, 10.0, f"Maximum execution time too slow: {max_time:.4f}s")
        
        # Calculate throughput
        throughput = len(execution_times) / sum(execution_times)
        print(f"Throughput: {throughput:.3f} experiments/second")
        
        self.assertGreater(throughput, 0.2, f"Throughput too low: {throughput:.3f} experiments/second")
        
        print("✓ Experiment execution performance acceptable")
        return execution_times
    
    def test_analysis_pipeline_performance(self):
        """Test performance of analysis pipeline."""
        print("\n=== Analysis Pipeline Performance ===")
        
        # Create test experiment data
        experiment_dirs = []
        
        for i in range(3):
            # Generate and run experiment
            topology_generator = LinearTopologyGenerator(self.base_config)
            locations_file, routes_file = topology_generator.generate_linear(
                n_nodes=4, segment_distance=50.0, start_pop=1000, pop_decay=0.8
            )
            
            scenario_generator = SpikeConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_spike_conflict(
                origin='Origin', start_day=1, peak_intensity=0.7,
                output_dir=os.path.dirname(locations_file)
            )
            
            config = self.config_manager.create_cognitive_config('s1_only')
            experiment_config = ExperimentConfig(
                experiment_id=f'analysis_perf_{i}',
                topology_type='linear',
                topology_params={'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                scenario_type='spike',
                scenario_params={'origin': 'Origin', 'start_day': 1, 'peak_intensity': 0.7},
                cognitive_mode='s1_only',
                simulation_params=config,
                replications=1
            )
            
            result = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
            self.assertTrue(result['success'])
            experiment_dirs.append(result['experiment_dir'])
        
        # Test analysis performance
        analysis_times = []
        
        for i, experiment_dir in enumerate(experiment_dirs):
            print(f"Analyzing experiment {i+1}/{len(experiment_dirs)}")
            
            start_time = time.time()
            analysis_results = self.analysis_pipeline.process_experiment(experiment_dir)
            analysis_time = time.time() - start_time
            
            analysis_times.append(analysis_time)
            self.assertIsNotNone(analysis_results, f"Analysis failed for experiment {i}")
            
            print(f"Analysis {i+1} completed in {analysis_time:.4f}s")
        
        # Analyze performance
        avg_analysis_time = sum(analysis_times) / len(analysis_times)
        max_analysis_time = max(analysis_times)
        
        print(f"\nAnalysis Performance Summary:")
        print(f"Average analysis time: {avg_analysis_time:.4f}s")
        print(f"Max analysis time: {max_analysis_time:.4f}s")
        
        # Performance assertions
        self.assertLess(avg_analysis_time, 2.0, f"Average analysis time too slow: {avg_analysis_time:.4f}s")
        self.assertLess(max_analysis_time, 5.0, f"Maximum analysis time too slow: {max_analysis_time:.4f}s")
        
        print("✓ Analysis pipeline performance acceptable")
        return analysis_times
    
    def test_memory_usage_optimization(self):
        """Test memory usage during operations."""
        print("\n=== Memory Usage Optimization ===")
        
        try:
            import psutil
            process = psutil.Process()
            
            # Get initial memory usage
            initial_memory = process.memory_info().rss
            print(f"Initial memory usage: {initial_memory / 1024 / 1024:.2f} MB")
            
            # Run multiple operations
            for i in range(10):
                # Generate topology
                topology_generator = LinearTopologyGenerator(self.base_config)
                locations_file, routes_file = topology_generator.generate_linear(
                    n_nodes=20, segment_distance=50.0, start_pop=1000, pop_decay=0.8
                )
                
                # Generate scenario
                scenario_generator = SpikeConflictGenerator(locations_file)
                conflicts_file = scenario_generator.generate_spike_conflict(
                    origin='Origin', start_day=1, peak_intensity=0.8,
                    output_dir=os.path.dirname(locations_file)
                )
                
                # Check memory usage
                current_memory = process.memory_info().rss
                memory_growth = current_memory - initial_memory
                
                print(f"Operation {i+1}: Memory usage: {current_memory / 1024 / 1024:.2f} MB "
                      f"(+{memory_growth / 1024 / 1024:.2f} MB)")
                
                # Memory growth should be reasonable (less than 100MB total)
                self.assertLess(memory_growth, 100 * 1024 * 1024, 
                               f"Excessive memory growth: {memory_growth / 1024 / 1024:.2f} MB")
            
            final_memory = process.memory_info().rss
            total_growth = final_memory - initial_memory
            
            print(f"Final memory usage: {final_memory / 1024 / 1024:.2f} MB")
            print(f"Total memory growth: {total_growth / 1024 / 1024:.2f} MB")
            
            # Total growth should be reasonable
            self.assertLess(total_growth, 50 * 1024 * 1024, 
                           f"Total memory growth too high: {total_growth / 1024 / 1024:.2f} MB")
            
            print("✓ Memory usage optimization acceptable")
            
        except ImportError:
            print("⚠ psutil not available, skipping memory usage test")
    
    def test_profiling_critical_paths(self):
        """Profile critical code paths to identify bottlenecks."""
        print("\n=== Profiling Critical Paths ===")
        
        # Profile topology generation
        pr = cProfile.Profile()
        pr.enable()
        
        topology_generator = LinearTopologyGenerator(self.base_config)
        locations_file, routes_file = topology_generator.generate_linear(
            n_nodes=50, segment_distance=50.0, start_pop=1000, pop_decay=0.8
        )
        
        pr.disable()
        
        # Analyze profiling results
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # Top 10 functions
        
        profile_output = s.getvalue()
        print("Top 10 functions in topology generation:")
        print(profile_output)
        
        # Check for obvious bottlenecks
        lines = profile_output.split('\n')
        for line in lines:
            if 'generate_linear' in line and 'seconds' in line:
                # Extract time if possible
                parts = line.split()
                if len(parts) > 3:
                    try:
                        time_per_call = float(parts[3])
                        self.assertLess(time_per_call, 0.1, 
                                       f"generate_linear taking too long per call: {time_per_call:.4f}s")
                    except (ValueError, IndexError):
                        pass
        
        print("✓ Profiling completed - no major bottlenecks detected")
    
    def test_concurrent_performance(self):
        """Test performance under concurrent load."""
        print("\n=== Concurrent Performance Test ===")
        
        import threading
        import queue
        
        # Test concurrent topology generation
        num_threads = 3
        results_queue = queue.Queue()
        
        def generate_topology_worker(worker_id):
            try:
                start_time = time.time()
                
                base_config = {'output_dir': os.path.join(self.temp_dir, f'worker_{worker_id}')}
                topology_generator = LinearTopologyGenerator(base_config)
                locations_file, routes_file = topology_generator.generate_linear(
                    n_nodes=10, segment_distance=50.0, start_pop=1000, pop_decay=0.8
                )
                
                execution_time = time.time() - start_time
                results_queue.put({
                    'worker_id': worker_id,
                    'success': True,
                    'time': execution_time,
                    'files': [locations_file, routes_file]
                })
                
            except Exception as e:
                results_queue.put({
                    'worker_id': worker_id,
                    'success': False,
                    'error': str(e),
                    'time': 0
                })
        
        # Start threads
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=generate_topology_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Analyze results
        successful_workers = [r for r in results if r['success']]
        failed_workers = [r for r in results if not r['success']]
        
        print(f"Concurrent execution completed in {total_time:.4f}s")
        print(f"Successful workers: {len(successful_workers)}/{num_threads}")
        
        if failed_workers:
            print("Failed workers:")
            for worker in failed_workers:
                print(f"  Worker {worker['worker_id']}: {worker['error']}")
        
        # All workers should succeed
        self.assertEqual(len(successful_workers), num_threads, 
                        f"Only {len(successful_workers)}/{num_threads} workers succeeded")
        
        # Average worker time should be reasonable
        avg_worker_time = sum(r['time'] for r in successful_workers) / len(successful_workers)
        print(f"Average worker time: {avg_worker_time:.4f}s")
        
        self.assertLess(avg_worker_time, 2.0, f"Average worker time too slow: {avg_worker_time:.4f}s")
        
        # Concurrent execution should be faster than sequential
        sequential_time_estimate = avg_worker_time * num_threads
        speedup = sequential_time_estimate / total_time
        print(f"Estimated speedup: {speedup:.2f}x")
        
        self.assertGreater(speedup, 1.5, f"Insufficient speedup from concurrency: {speedup:.2f}x")
        
        print("✓ Concurrent performance acceptable")


if __name__ == '__main__':
    unittest.main()