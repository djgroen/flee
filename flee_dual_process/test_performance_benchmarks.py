"""
Performance Benchmarking Suite for Dual Process Experiments Framework

Tests performance of topology generation, experiment execution throughput,
memory usage, and scalability for large parameter sweeps.
"""

import unittest
import tempfile
import shutil
import os
import time
import psutil
import threading
import multiprocessing
from typing import Dict, List, Any, Tuple
from unittest.mock import patch, MagicMock

try:
    from .topology_generator import (
        LinearTopologyGenerator, StarTopologyGenerator, 
        TreeTopologyGenerator, GridTopologyGenerator
    )
    from .scenario_generator import (
        SpikeConflictGenerator, GradualConflictGenerator,
        CascadingConflictGenerator, OscillatingConflictGenerator
    )
    from .config_manager import ConfigurationManager, ExperimentConfig
    from .experiment_runner import ExperimentRunner, ProcessPoolManager
    from .analysis_pipeline import AnalysisPipeline
    from .utils import CSVUtils
except ImportError:
    from topology_generator import (
        LinearTopologyGenerator, StarTopologyGenerator, 
        TreeTopologyGenerator, GridTopologyGenerator
    )
    from scenario_generator import (
        SpikeConflictGenerator, GradualConflictGenerator,
        CascadingConflictGenerator, OscillatingConflictGenerator
    )
    from config_manager import ConfigurationManager, ExperimentConfig
    from experiment_runner import ExperimentRunner, ProcessPoolManager
    from analysis_pipeline import AnalysisPipeline
    from utils import CSVUtils


class PerformanceBenchmark:
    """Base class for performance benchmarking utilities."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.results = {}
    
    def measure_time(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    def measure_memory(self, func, *args, **kwargs) -> Tuple[Any, Dict[str, float]]:
        """Measure memory usage of a function."""
        # Get initial memory
        initial_memory = self.process.memory_info().rss
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Get final memory
        final_memory = self.process.memory_info().rss
        
        memory_stats = {
            'initial_memory_mb': initial_memory / (1024 * 1024),
            'final_memory_mb': final_memory / (1024 * 1024),
            'memory_delta_mb': (final_memory - initial_memory) / (1024 * 1024)
        }
        
        return result, memory_stats
    
    def measure_cpu_usage(self, func, duration=1.0, *args, **kwargs) -> Tuple[Any, float]:
        """Measure CPU usage during function execution."""
        # Start CPU monitoring
        cpu_percent_start = self.process.cpu_percent()
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Wait a bit and get CPU usage
        time.sleep(0.1)
        cpu_percent_end = self.process.cpu_percent()
        
        return result, cpu_percent_end
    
    def benchmark_function(self, func, iterations=1, *args, **kwargs) -> Dict[str, Any]:
        """Comprehensive benchmark of a function."""
        times = []
        memory_deltas = []
        
        for i in range(iterations):
            # Measure time and memory
            start_time = time.time()
            initial_memory = self.process.memory_info().rss
            
            result = func(*args, **kwargs)
            
            end_time = time.time()
            final_memory = self.process.memory_info().rss
            
            execution_time = end_time - start_time
            memory_delta = (final_memory - initial_memory) / (1024 * 1024)
            
            times.append(execution_time)
            memory_deltas.append(memory_delta)
        
        return {
            'iterations': iterations,
            'avg_time_seconds': sum(times) / len(times),
            'min_time_seconds': min(times),
            'max_time_seconds': max(times),
            'avg_memory_delta_mb': sum(memory_deltas) / len(memory_deltas),
            'max_memory_delta_mb': max(memory_deltas),
            'total_time_seconds': sum(times)
        }


class TestTopologyGenerationPerformance(unittest.TestCase):
    """Test performance of topology generation algorithms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        self.benchmark = PerformanceBenchmark()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_linear_topology_generation_speed(self):
        """Test linear topology generation speed for different sizes."""
        generator = LinearTopologyGenerator(self.base_config)
        
        test_sizes = [10, 50, 100, 500]
        results = {}
        
        for size in test_sizes:
            benchmark_result = self.benchmark.benchmark_function(
                generator.generate_linear,
                iterations=3,
                n_nodes=size,
                segment_distance=50.0,
                start_pop=1000,
                pop_decay=0.8
            )
            
            results[size] = benchmark_result
            
            # Performance requirements
            self.assertLess(benchmark_result['avg_time_seconds'], 2.0, 
                          f"Linear topology generation for {size} nodes took too long")
            self.assertLess(benchmark_result['avg_memory_delta_mb'], 50.0,
                          f"Linear topology generation for {size} nodes used too much memory")
        
        # Check scalability - time should scale reasonably with size
        if len(results) >= 2:
            small_time = results[test_sizes[0]]['avg_time_seconds']
            large_time = results[test_sizes[-1]]['avg_time_seconds']
            
            # Should not be more than quadratic scaling
            size_ratio = test_sizes[-1] / test_sizes[0]
            time_ratio = large_time / small_time if small_time > 0 else 1
            
            self.assertLess(time_ratio, size_ratio ** 2,
                          "Linear topology generation scaling is worse than quadratic")
        
        print(f"Linear topology generation performance: {results}")
    
    def test_star_topology_generation_speed(self):
        """Test star topology generation speed for different sizes."""
        generator = StarTopologyGenerator(self.base_config)
        
        test_sizes = [5, 25, 50, 100]
        results = {}
        
        for size in test_sizes:
            benchmark_result = self.benchmark.benchmark_function(
                generator.generate_star,
                iterations=3,
                n_camps=size,
                hub_pop=2000,
                camp_capacity=5000,
                radius=100.0
            )
            
            results[size] = benchmark_result
            
            # Performance requirements
            self.assertLess(benchmark_result['avg_time_seconds'], 1.0,
                          f"Star topology generation for {size} camps took too long")
        
        print(f"Star topology generation performance: {results}")
    
    def test_tree_topology_generation_speed(self):
        """Test tree topology generation speed for different sizes."""
        generator = TreeTopologyGenerator(self.base_config)
        
        test_configs = [
            (2, 3),  # Small tree: 2^3 = 8 nodes
            (3, 3),  # Medium tree: 3^3 = 27 nodes
            (2, 5),  # Deep tree: 2^5 = 32 nodes
            (4, 3),  # Wide tree: 4^3 = 64 nodes
        ]
        
        results = {}
        
        for branching_factor, depth in test_configs:
            config_name = f"bf{branching_factor}_d{depth}"
            
            benchmark_result = self.benchmark.benchmark_function(
                generator.generate_tree,
                iterations=3,
                branching_factor=branching_factor,
                depth=depth,
                root_pop=1000
            )
            
            results[config_name] = benchmark_result
            
            # Performance requirements
            self.assertLess(benchmark_result['avg_time_seconds'], 2.0,
                          f"Tree topology generation for {config_name} took too long")
        
        print(f"Tree topology generation performance: {results}")
    
    def test_grid_topology_generation_speed(self):
        """Test grid topology generation speed for different sizes."""
        generator = GridTopologyGenerator(self.base_config)
        
        test_sizes = [
            (5, 5),    # 25 nodes
            (10, 10),  # 100 nodes
            (20, 20),  # 400 nodes
            (30, 30),  # 900 nodes
        ]
        
        results = {}
        
        for rows, cols in test_sizes:
            size_name = f"{rows}x{cols}"
            
            benchmark_result = self.benchmark.benchmark_function(
                generator.generate_grid,
                iterations=3,
                rows=rows,
                cols=cols,
                cell_distance=50.0,
                pop_distribution='uniform'
            )
            
            results[size_name] = benchmark_result
            
            # Performance requirements
            self.assertLess(benchmark_result['avg_time_seconds'], 3.0,
                          f"Grid topology generation for {size_name} took too long")
        
        print(f"Grid topology generation performance: {results}")
    
    def test_topology_file_io_performance(self):
        """Test file I/O performance for topology generation."""
        generator = LinearTopologyGenerator(self.base_config)
        csv_utils = CSVUtils()
        
        # Generate a large topology
        locations_file, routes_file = generator.generate_linear(
            n_nodes=1000,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        # Benchmark file reading
        read_benchmark = self.benchmark.benchmark_function(
            csv_utils.read_locations_csv,
            iterations=5,
            filepath=locations_file
        )
        
        self.assertLess(read_benchmark['avg_time_seconds'], 0.5,
                       "Reading large topology file took too long")
        
        print(f"Topology file I/O performance: {read_benchmark}")


class TestScenarioGenerationPerformance(unittest.TestCase):
    """Test performance of scenario generation algorithms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        self.benchmark = PerformanceBenchmark()
        
        # Create a large topology for testing
        generator = LinearTopologyGenerator(self.base_config)
        self.locations_file, self.routes_file = generator.generate_linear(
            n_nodes=100,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_spike_conflict_generation_speed(self):
        """Test spike conflict generation speed."""
        generator = SpikeConflictGenerator(self.locations_file)
        
        benchmark_result = self.benchmark.benchmark_function(
            generator.generate_spike_conflict,
            iterations=5,
            origin='Origin',
            start_day=0,
            peak_intensity=0.8,
            output_dir=self.temp_dir
        )
        
        self.assertLess(benchmark_result['avg_time_seconds'], 1.0,
                       "Spike conflict generation took too long")
        
        print(f"Spike conflict generation performance: {benchmark_result}")
    
    def test_gradual_conflict_generation_speed(self):
        """Test gradual conflict generation speed."""
        generator = GradualConflictGenerator(self.locations_file)
        
        # Test with different escalation periods
        test_periods = [10, 50, 100, 200]
        results = {}
        
        for period in test_periods:
            benchmark_result = self.benchmark.benchmark_function(
                generator.generate_gradual_conflict,
                iterations=3,
                origin='Origin',
                start_day=0,
                end_day=period,
                max_intensity=0.8,
                output_dir=self.temp_dir
            )
            
            results[period] = benchmark_result
            
            self.assertLess(benchmark_result['avg_time_seconds'], 2.0,
                          f"Gradual conflict generation for {period} days took too long")
        
        print(f"Gradual conflict generation performance: {results}")
    
    def test_cascading_conflict_generation_speed(self):
        """Test cascading conflict generation speed."""
        generator = CascadingConflictGenerator(self.locations_file)
        
        benchmark_result = self.benchmark.benchmark_function(
            generator.generate_cascading_conflict,
            iterations=3,
            origin='Origin',
            start_day=0,
            spread_rate=1.0,
            max_intensity=0.8,
            routes_file=self.routes_file,
            output_dir=self.temp_dir
        )
        
        self.assertLess(benchmark_result['avg_time_seconds'], 3.0,
                       "Cascading conflict generation took too long")
        
        print(f"Cascading conflict generation performance: {benchmark_result}")
    
    def test_oscillating_conflict_generation_speed(self):
        """Test oscillating conflict generation speed."""
        generator = OscillatingConflictGenerator(self.locations_file)
        
        # Test with different periods and durations
        test_configs = [
            (10, 100),   # 10-day period, 100 days total
            (20, 200),   # 20-day period, 200 days total
            (30, 300),   # 30-day period, 300 days total
        ]
        
        results = {}
        
        for period, duration in test_configs:
            config_name = f"p{period}_d{duration}"
            
            benchmark_result = self.benchmark.benchmark_function(
                generator.generate_oscillating_conflict,
                iterations=3,
                origin='Origin',
                start_day=0,
                period=period,
                amplitude=0.5,
                output_dir=self.temp_dir
            )
            
            results[config_name] = benchmark_result
            
            self.assertLess(benchmark_result['avg_time_seconds'], 2.0,
                          f"Oscillating conflict generation for {config_name} took too long")
        
        print(f"Oscillating conflict generation performance: {results}")
    
    def test_scenario_file_io_performance(self):
        """Test scenario file I/O performance."""
        generator = SpikeConflictGenerator(self.locations_file)
        
        # Generate a scenario with many days
        conflicts_file = generator.generate_spike_conflict(
            origin='Origin',
            start_day=0,
            peak_intensity=0.8,
            output_dir=self.temp_dir
        )
        
        # Benchmark reading the conflicts file
        read_benchmark = self.benchmark.benchmark_function(
            generator._read_conflicts_matrix,
            iterations=5,
            filepath=conflicts_file
        )
        
        self.assertLess(read_benchmark['avg_time_seconds'], 0.5,
                       "Reading conflicts file took too long")
        
        print(f"Scenario file I/O performance: {read_benchmark}")


class TestExperimentExecutionThroughput(unittest.TestCase):
    """Test experiment execution throughput and memory usage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark = PerformanceBenchmark()
        
        # Create mock Flee executable
        self.mock_flee_executable = self._create_mock_flee_executable()
        
        self.experiment_runner = ExperimentRunner(
            max_parallel=4,
            base_output_dir=self.temp_dir,
            flee_executable=self.mock_flee_executable,
            timeout=30
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_mock_flee_executable(self) -> str:
        """Create a fast mock Flee executable for throughput testing."""
        mock_script = os.path.join(self.temp_dir, "fast_mock_flee.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import os
import time
import csv

def create_minimal_output(output_dir):
    """Create minimal mock output quickly."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create minimal out.csv
    with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'location', 'refugees'])
        writer.writerow([0, 'Origin', 100])
        writer.writerow([1, 'Camp', 100])

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
        
        # Very fast execution
        time.sleep(0.01)
        
        create_minimal_output(output_dir)
    else:
        sys.exit(1)
'''
        
        with open(mock_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(mock_script, 0o755)
        return mock_script
    
    def test_single_experiment_throughput(self):
        """Test throughput of single experiment execution."""
        config = {
            'experiment_id': 'throughput_test',
            'topology_type': 'linear',
            'topology_params': {'n_nodes': 5},
            'scenario_type': 'spike',
            'scenario_params': {'origin': 'Origin'},
            'cognitive_mode': 's1_only',
            'simulation_params': {'move_rules': {'awareness_level': 1}},
            'replications': 1
        }
        
        benchmark_result = self.benchmark.benchmark_function(
            self.experiment_runner.run_single_experiment,
            iterations=10,
            experiment_config=config
        )
        
        # Should complete quickly with mock executable
        self.assertLess(benchmark_result['avg_time_seconds'], 2.0,
                       "Single experiment execution took too long")
        
        # Memory usage should be reasonable
        self.assertLess(benchmark_result['avg_memory_delta_mb'], 100.0,
                       "Single experiment used too much memory")
        
        print(f"Single experiment throughput: {benchmark_result}")
    
    def test_parallel_experiment_throughput(self):
        """Test throughput of parallel experiment execution."""
        # Create multiple experiment configurations
        configs = []
        for i in range(20):
            config = {
                'experiment_id': f'parallel_throughput_test_{i}',
                'topology_type': 'linear',
                'topology_params': {'n_nodes': 3},
                'scenario_type': 'spike',
                'scenario_params': {'origin': 'Origin'},
                'cognitive_mode': 's1_only',
                'simulation_params': {'move_rules': {'awareness_level': 1}},
                'replications': 1
            }
            configs.append(config)
        
        # Measure parallel execution time
        start_time = time.time()
        results = []
        
        for config in configs:
            result = self.experiment_runner.run_single_experiment(config)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        successful_experiments = [r for r in results if r.get('success', False)]
        throughput = len(successful_experiments) / total_time
        
        # Should achieve reasonable throughput
        self.assertGreater(throughput, 5.0,  # At least 5 experiments per second
                          f"Parallel experiment throughput too low: {throughput:.2f} exp/sec")
        
        print(f"Parallel experiment throughput: {throughput:.2f} experiments/second")
    
    def test_memory_usage_during_execution(self):
        """Test memory usage during experiment execution."""
        initial_memory = self.benchmark.process.memory_info().rss
        
        # Run multiple experiments and monitor memory
        memory_samples = []
        
        for i in range(10):
            config = {
                'experiment_id': f'memory_test_{i}',
                'topology_type': 'linear',
                'cognitive_mode': 's1_only',
                'simulation_params': {}
            }
            
            self.experiment_runner.run_single_experiment(config)
            
            current_memory = self.benchmark.process.memory_info().rss
            memory_samples.append(current_memory)
        
        # Calculate memory statistics
        max_memory = max(memory_samples)
        memory_growth = (max_memory - initial_memory) / (1024 * 1024)
        
        # Memory growth should be reasonable
        self.assertLess(memory_growth, 200.0,  # Less than 200MB growth
                       f"Memory growth too high: {memory_growth:.2f} MB")
        
        print(f"Memory usage during execution: {memory_growth:.2f} MB growth")
    
    def test_resource_monitoring_overhead(self):
        """Test overhead of resource monitoring."""
        process_manager = ProcessPoolManager(max_workers=2)
        
        # Measure time to get resource status
        status_benchmark = self.benchmark.benchmark_function(
            process_manager.get_resource_status,
            iterations=100
        )
        
        # Resource monitoring should be fast
        self.assertLess(status_benchmark['avg_time_seconds'], 0.01,
                       "Resource monitoring took too long")
        
        print(f"Resource monitoring overhead: {status_benchmark}")


class TestAnalysisPipelinePerformance(unittest.TestCase):
    """Test analysis pipeline performance and scalability."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark = PerformanceBenchmark()
        
        # Create analysis pipeline
        self.analysis_pipeline = AnalysisPipeline(
            results_directory=self.temp_dir,
            output_directory=os.path.join(self.temp_dir, "analysis")
        )
        
        # Create mock experiment data
        self._create_mock_experiment_data()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_mock_experiment_data(self):
        """Create mock experiment data for performance testing."""
        import csv
        import json
        
        experiment_dir = os.path.join(self.temp_dir, "large_experiment")
        output_dir = os.path.join(experiment_dir, "output")
        metadata_dir = os.path.join(experiment_dir, "metadata")
        
        os.makedirs(output_dir)
        os.makedirs(metadata_dir)
        
        # Create large movement data file
        with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
            
            locations = ['Origin', 'Town_1', 'Town_2', 'Town_3', 'Camp_1', 'Camp_2']
            for day in range(100):  # 100 days
                for location in locations:
                    refugees = max(0, 1000 - day * 10 + hash(location) % 100)
                    writer.writerow([day, location, refugees, refugees])
        
        # Create large cognitive states file
        with open(os.path.join(output_dir, 'cognitive_states.out.0'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'agent_id', 'cognitive_state', 'location', 'connections',
                           'system2_activations', 'days_in_location', 'conflict_level'])
            
            for day in range(100):
                for agent_id in range(1, 101):  # 100 agents
                    state = 'S1' if (day + agent_id) % 3 == 0 else 'S2'
                    location = locations[agent_id % len(locations)]
                    connections = (day + agent_id) % 6
                    activations = (day + agent_id) % 4
                    days_in_loc = (day % 10) + 1
                    conflict = ((day + agent_id) % 100) / 100.0
                    
                    writer.writerow([day, f'0-{agent_id}', state, location, connections,
                                   activations, days_in_loc, conflict])
        
        # Create decision log file
        with open(os.path.join(output_dir, 'decision_log.out.0'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#day', 'agent_id', 'decision_type', 'cognitive_state', 'location',
                           'movechance', 'outcome', 'system2_active', 'conflict_level', 'connections'])
            
            for day in range(1, 100):
                for agent_id in range(1, 101):
                    decision = 'move' if (day + agent_id) % 4 == 0 else 'stay'
                    state = 'S1' if (day + agent_id) % 3 == 0 else 'S2'
                    location = locations[agent_id % len(locations)]
                    movechance = ((day + agent_id) % 100) / 100.0
                    outcome = 1 if decision == 'move' else 0
                    s2_active = state == 'S2'
                    conflict = ((day + agent_id) % 100) / 100.0
                    connections = (day + agent_id) % 6
                    
                    writer.writerow([day, f'0-{agent_id}', decision, state, location,
                                   movechance, outcome, s2_active, conflict, connections])
        
        # Create metadata
        metadata = {
            'experiment_id': 'large_experiment',
            'configuration': {
                'cognitive_mode': 'dual_process',
                'topology_type': 'linear'
            }
        }
        
        with open(os.path.join(metadata_dir, 'experiment_metadata.json'), 'w') as f:
            json.dump(metadata, f)
    
    def test_data_loading_performance(self):
        """Test performance of loading large experiment data."""
        experiment_dir = os.path.join(self.temp_dir, "large_experiment")
        
        benchmark_result = self.benchmark.benchmark_function(
            self.analysis_pipeline.load_experiment_data,
            iterations=3,
            experiment_dir=experiment_dir
        )
        
        # Should load large dataset reasonably quickly
        self.assertLess(benchmark_result['avg_time_seconds'], 5.0,
                       "Loading large experiment data took too long")
        
        # Memory usage should be reasonable
        self.assertLess(benchmark_result['avg_memory_delta_mb'], 500.0,
                       "Loading experiment data used too much memory")
        
        print(f"Data loading performance: {benchmark_result}")
    
    def test_movement_metrics_calculation_performance(self):
        """Test performance of movement metrics calculation."""
        experiment_dir = os.path.join(self.temp_dir, "large_experiment")
        
        benchmark_result = self.benchmark.benchmark_function(
            self.analysis_pipeline.calculate_movement_metrics,
            iterations=3,
            experiment_dir=experiment_dir
        )
        
        # Should calculate metrics reasonably quickly
        self.assertLess(benchmark_result['avg_time_seconds'], 3.0,
                       "Movement metrics calculation took too long")
        
        print(f"Movement metrics calculation performance: {benchmark_result}")
    
    def test_cognitive_analysis_performance(self):
        """Test performance of cognitive state analysis."""
        experiment_dir = os.path.join(self.temp_dir, "large_experiment")
        
        benchmark_result = self.benchmark.benchmark_function(
            self.analysis_pipeline.analyze_cognitive_transitions,
            iterations=3,
            experiment_dir=experiment_dir
        )
        
        # Should analyze cognitive states reasonably quickly
        self.assertLess(benchmark_result['avg_time_seconds'], 4.0,
                       "Cognitive analysis took too long")
        
        print(f"Cognitive analysis performance: {benchmark_result}")
    
    def test_complete_analysis_pipeline_performance(self):
        """Test performance of complete analysis pipeline."""
        experiment_dir = os.path.join(self.temp_dir, "large_experiment")
        
        benchmark_result = self.benchmark.benchmark_function(
            self.analysis_pipeline.process_experiment,
            iterations=2,
            experiment_dir=experiment_dir
        )
        
        # Complete analysis should finish in reasonable time
        self.assertLess(benchmark_result['avg_time_seconds'], 10.0,
                       "Complete analysis pipeline took too long")
        
        print(f"Complete analysis pipeline performance: {benchmark_result}")


class TestParameterSweepScalability(unittest.TestCase):
    """Test scalability for large parameter sweeps."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.benchmark = PerformanceBenchmark()
        self.config_manager = ConfigurationManager()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_parameter_sweep_generation_scalability(self):
        """Test scalability of parameter sweep generation."""
        base_config = self.config_manager.create_cognitive_config('dual_process')
        
        # Test different sweep sizes
        sweep_sizes = [10, 50, 100, 500]
        results = {}
        
        for size in sweep_sizes:
            values = [i * 0.01 for i in range(size)]  # Generate many values
            
            benchmark_result = self.benchmark.benchmark_function(
                self.config_manager.generate_parameter_sweep,
                iterations=3,
                base_config=base_config,
                parameter='move_rules.weight_softening',
                values=values
            )
            
            results[size] = benchmark_result
            
            # Should generate sweeps quickly
            self.assertLess(benchmark_result['avg_time_seconds'], 1.0,
                          f"Parameter sweep generation for {size} values took too long")
        
        print(f"Parameter sweep generation scalability: {results}")
    
    def test_factorial_design_scalability(self):
        """Test scalability of factorial design generation."""
        base_config = self.config_manager.create_cognitive_config('dual_process')
        
        # Test different factorial sizes
        factorial_configs = [
            {'param1': [1, 2], 'param2': [0.1, 0.2]},  # 2x2 = 4 configs
            {'param1': [1, 2, 3], 'param2': [0.1, 0.2, 0.3]},  # 3x3 = 9 configs
            {'param1': [1, 2, 3, 4], 'param2': [0.1, 0.2, 0.3, 0.4]},  # 4x4 = 16 configs
            {'param1': [1, 2, 3, 4, 5], 'param2': [0.1, 0.2, 0.3, 0.4, 0.5]},  # 5x5 = 25 configs
        ]
        
        results = {}
        
        for i, factors in enumerate(factorial_configs):
            config_count = len(factors['param1']) * len(factors['param2'])
            
            # Map to actual parameter names
            mapped_factors = {
                'move_rules.awareness_level': factors['param1'],
                'move_rules.weight_softening': factors['param2']
            }
            
            benchmark_result = self.benchmark.benchmark_function(
                self.config_manager.generate_factorial_design,
                iterations=3,
                base_config=base_config,
                factors=mapped_factors
            )
            
            results[config_count] = benchmark_result
            
            # Should generate factorial designs quickly
            self.assertLess(benchmark_result['avg_time_seconds'], 2.0,
                          f"Factorial design generation for {config_count} configs took too long")
        
        print(f"Factorial design generation scalability: {results}")
    
    def test_configuration_validation_scalability(self):
        """Test scalability of configuration validation."""
        # Generate many configurations
        base_config = self.config_manager.create_cognitive_config('s1_only')
        values = [i * 0.01 for i in range(100)]
        
        configs = self.config_manager.generate_parameter_sweep(
            base_config, 'move_rules.weight_softening', values
        )
        
        # Benchmark validation of all configurations
        benchmark_result = self.benchmark.benchmark_function(
            self.config_manager.validate_parameter_sweep,
            iterations=3,
            configurations=configs
        )
        
        # Should validate many configurations quickly
        self.assertLess(benchmark_result['avg_time_seconds'], 2.0,
                       "Configuration validation took too long")
        
        print(f"Configuration validation scalability: {benchmark_result}")
    
    def test_memory_usage_for_large_sweeps(self):
        """Test memory usage for large parameter sweeps."""
        base_config = self.config_manager.create_cognitive_config('dual_process')
        
        # Generate a large parameter sweep
        large_values = [i * 0.001 for i in range(1000)]  # 1000 values
        
        initial_memory = self.benchmark.process.memory_info().rss
        
        large_sweep = self.config_manager.generate_parameter_sweep(
            base_config, 'move_rules.weight_softening', large_values
        )
        
        final_memory = self.benchmark.process.memory_info().rss
        memory_usage = (final_memory - initial_memory) / (1024 * 1024)
        
        # Memory usage should be reasonable for large sweeps
        self.assertLess(memory_usage, 100.0,
                       f"Large parameter sweep used too much memory: {memory_usage:.2f} MB")
        
        # Verify we got the expected number of configurations
        self.assertEqual(len(large_sweep), 1000)
        
        print(f"Large parameter sweep memory usage: {memory_usage:.2f} MB for 1000 configs")


if __name__ == '__main__':
    # Run performance benchmarks with detailed output
    unittest.main(verbosity=2)