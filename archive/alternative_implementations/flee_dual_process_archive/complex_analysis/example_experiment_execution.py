#!/usr/bin/env python3
"""
Example script demonstrating the experiment execution system.

This script shows how to use the ExperimentRunner, ProcessPoolManager,
and metadata collection system for dual-process experiments.
"""

import os
import sys
import json
from pathlib import Path

# Add the flee_dual_process directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config_manager import ConfigurationManager, ExperimentConfig
    from experiment_runner import ExperimentRunner, ProcessPoolManager, ExperimentMetadataCollector
    from utils import LoggingUtils
except ImportError as e:
    print(f"Import error: {e}")
    print("This example requires the full flee_dual_process module to be properly installed.")
    print("Running in demonstration mode with mock functionality...")
    
    # Mock classes for demonstration
    class MockExperimentConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def to_dict(self):
            return {key: value for key, value in self.__dict__.items()}
    
    class MockExperimentRunner:
        def __init__(self, **kwargs):
            self.config = kwargs
            print(f"MockExperimentRunner initialized with: {kwargs}")
        
        def run_single_experiment(self, config):
            print(f"Running experiment: {config.experiment_id}")
            return {
                'experiment_id': config.experiment_id,
                'status': 'success',
                'execution_time': 10.5,
                'directory': f'/mock/path/{config.experiment_id}'
            }
        
        def run_parameter_sweep(self, sweep_config):
            print(f"Running parameter sweep with {len(sweep_config.get('values', []))} configurations")
            results = []
            for i, value in enumerate(sweep_config.get('values', [])):
                results.append({
                    'experiment_id': f"sweep_{i}",
                    'status': 'success',
                    'execution_time': 8.2,
                    'parameter_value': value
                })
            return results
    
    ExperimentConfig = MockExperimentConfig
    ExperimentRunner = MockExperimentRunner


def create_example_experiment_config():
    """Create an example experiment configuration."""
    return ExperimentConfig(
        experiment_id="example_dual_process_001",
        topology_type="linear",
        topology_params={
            "n_nodes": 10,
            "segment_distance": 50.0,
            "start_pop": 2000,
            "pop_decay": 0.9
        },
        scenario_type="spike",
        scenario_params={
            "start_day": 10,
            "peak_intensity": 0.8,
            "duration": 150
        },
        cognitive_mode="dual_process",
        simulation_params={
            "awareness_level": 2,
            "average_social_connectivity": 3.0,
            "conflict_threshold": 0.6,
            "recovery_period_max": 30
        },
        replications=1,
        metadata={
            "description": "Example dual-process experiment with linear topology",
            "researcher": "example_user",
            "project": "dual_process_validation"
        }
    )


def demonstrate_single_experiment():
    """Demonstrate running a single experiment."""
    print("=" * 60)
    print("DEMONSTRATING SINGLE EXPERIMENT EXECUTION")
    print("=" * 60)
    
    # Create experiment configuration
    config = create_example_experiment_config()
    
    print("Experiment Configuration:")
    print(f"  ID: {config.experiment_id}")
    print(f"  Topology: {config.topology_type} ({config.topology_params['n_nodes']} nodes)")
    print(f"  Scenario: {config.scenario_type} (intensity: {config.scenario_params['peak_intensity']})")
    print(f"  Cognitive Mode: {config.cognitive_mode}")
    print(f"  Simulation Duration: {config.scenario_params['duration']} days")
    print()
    
    # Create experiment runner
    runner = ExperimentRunner(
        max_parallel=2,
        base_output_dir="example_results",
        timeout=1800  # 30 minutes
    )
    
    # Run single experiment
    print("Running single experiment...")
    result = runner.run_single_experiment(config)
    
    print("Experiment Result:")
    print(f"  Status: {result['status']}")
    print(f"  Execution Time: {result.get('execution_time', 0):.2f} seconds")
    if 'directory' in result:
        print(f"  Output Directory: {result['directory']}")
    if 'error' in result:
        print(f"  Error: {result['error']}")
    print()


def demonstrate_parameter_sweep():
    """Demonstrate running a parameter sweep."""
    print("=" * 60)
    print("DEMONSTRATING PARAMETER SWEEP EXECUTION")
    print("=" * 60)
    
    # Create base configuration
    base_config = {
        'topology_type': 'linear',
        'topology_params': {
            'n_nodes': 8,
            'segment_distance': 50.0,
            'start_pop': 1500,
            'pop_decay': 0.8
        },
        'scenario_type': 'gradual',
        'scenario_params': {
            'start_day': 5,
            'end_day': 50,
            'max_intensity': 0.9,
            'duration': 120
        },
        'cognitive_mode': 'dual_process',
        'simulation_params': {
            'awareness_level': 2,
            'conflict_threshold': 0.5
        }
    }
    
    # Define parameter sweep
    sweep_config = {
        'base_config': base_config,
        'parameter': 'simulation_params.average_social_connectivity',
        'values': [0.0, 1.0, 3.0, 5.0, 8.0],  # Test different connectivity levels
        'replications': 2
    }
    
    print("Parameter Sweep Configuration:")
    print(f"  Parameter: {sweep_config['parameter']}")
    print(f"  Values: {sweep_config['values']}")
    print(f"  Replications: {sweep_config['replications']}")
    print(f"  Total Experiments: {len(sweep_config['values']) * sweep_config['replications']}")
    print()
    
    # Create experiment runner
    runner = ExperimentRunner(
        max_parallel=4,
        base_output_dir="example_sweep_results",
        timeout=1200  # 20 minutes per experiment
    )
    
    # Run parameter sweep
    print("Running parameter sweep...")
    results = runner.run_parameter_sweep(sweep_config)
    
    print("Parameter Sweep Results:")
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])
    total_time = sum(r.get('execution_time', 0) for r in results)
    
    print(f"  Total Experiments: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total Execution Time: {total_time:.2f} seconds")
    print(f"  Average Time per Experiment: {total_time/len(results):.2f} seconds")
    print()
    
    # Show results by parameter value
    print("Results by Parameter Value:")
    for value in sweep_config['values']:
        value_results = [r for r in results if r.get('parameter_value') == value]
        success_count = len([r for r in value_results if r['status'] == 'success'])
        print(f"  Connectivity {value}: {success_count}/{len(value_results)} successful")
    print()


def demonstrate_factorial_design():
    """Demonstrate running a factorial design experiment."""
    print("=" * 60)
    print("DEMONSTRATING FACTORIAL DESIGN EXECUTION")
    print("=" * 60)
    
    # Define factorial design factors
    factors = {
        'topology_params.n_nodes': [5, 10, 15],
        'scenario_params.peak_intensity': [0.6, 0.8, 1.0],
        'simulation_params.awareness_level': [1, 2, 3]
    }
    
    total_combinations = 1
    for factor, values in factors.items():
        total_combinations *= len(values)
    
    print("Factorial Design Configuration:")
    for factor, values in factors.items():
        print(f"  {factor}: {values}")
    print(f"  Total Combinations: {total_combinations}")
    print()
    
    # Create experiment runner
    runner = ExperimentRunner(
        max_parallel=3,
        base_output_dir="example_factorial_results",
        timeout=900  # 15 minutes per experiment
    )
    
    # Run factorial design
    print("Running factorial design...")
    results = runner.run_factorial_design(factors)
    
    print("Factorial Design Results:")
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])
    total_time = sum(r.get('execution_time', 0) for r in results)
    
    print(f"  Total Combinations: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total Execution Time: {total_time:.2f} seconds")
    print()


def demonstrate_metadata_collection():
    """Demonstrate metadata collection functionality."""
    print("=" * 60)
    print("DEMONSTRATING METADATA COLLECTION")
    print("=" * 60)
    
    try:
        from experiment_runner import ExperimentMetadataCollector
        
        collector = ExperimentMetadataCollector()
        config = create_example_experiment_config()
        
        print("Collecting experiment metadata...")
        
        # Simulate experiment execution
        import time
        import tempfile
        
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock experiment directory
            experiment_dir = os.path.join(temp_dir, "mock_experiment")
            os.makedirs(experiment_dir)
            
            for subdir in ['input', 'output', 'logs', 'metadata']:
                os.makedirs(os.path.join(experiment_dir, subdir))
            
            # Create mock files
            with open(os.path.join(experiment_dir, 'input', 'locations.csv'), 'w') as f:
                f.write("#name,region,country,lat,lon,location_type,conflict_date,pop/cap\n")
                f.write("origin,region1,country1,0.0,0.0,town,0,2000\n")
            
            with open(os.path.join(experiment_dir, 'output', 'out.csv'), 'w') as f:
                f.write("day,location,population\n")
                f.write("0,origin,2000\n")
                f.write("1,origin,1800\n")
            
            time.sleep(0.1)  # Simulate execution time
            
            # Collect metadata
            metadata = collector.collect_experiment_metadata(
                config, experiment_dir, start_time
            )
            
            print("Metadata Collection Results:")
            print(f"  Experiment ID: {metadata['experiment_id']}")
            print(f"  Execution Time: {metadata['execution_time_seconds']:.3f} seconds")
            print(f"  System Platform: {metadata['system_info']['platform']}")
            print(f"  CPU Cores: {metadata['system_info']['cpu_count']}")
            print(f"  Input Files: {len(metadata['input_files'])}")
            print(f"  Output Files: {len(metadata['output_files'])}")
            
            # Validate metadata
            validation = collector.validate_metadata_integrity(metadata)
            print(f"  Metadata Valid: {validation['is_valid']}")
            print(f"  Completeness Score: {validation['completeness_score']:.2f}")
            
            if validation['errors']:
                print(f"  Validation Errors: {validation['errors']}")
            if validation['warnings']:
                print(f"  Validation Warnings: {validation['warnings']}")
            
            print()
    
    except ImportError:
        print("Metadata collection not available in mock mode")
        print()


def demonstrate_resource_monitoring():
    """Demonstrate resource monitoring functionality."""
    print("=" * 60)
    print("DEMONSTRATING RESOURCE MONITORING")
    print("=" * 60)
    
    try:
        from experiment_runner import ProcessPoolManager
        
        manager = ProcessPoolManager(
            max_workers=4,
            memory_threshold=0.8,
            cpu_threshold=0.9,
            retry_attempts=3
        )
        
        print("Process Pool Manager Configuration:")
        print(f"  Max Workers: {manager.max_workers}")
        print(f"  Memory Threshold: {manager.memory_threshold * 100:.0f}%")
        print(f"  CPU Threshold: {manager.cpu_threshold * 100:.0f}%")
        print(f"  Retry Attempts: {manager.retry_attempts}")
        print()
        
        # Get current resource status
        status = manager.get_resource_status()
        
        print("Current Resource Status:")
        print(f"  Memory Usage: {status['memory_usage_percent']:.1f}%")
        print(f"  Available Memory: {status['memory_available_gb']:.1f} GB")
        print(f"  CPU Usage: {status['cpu_usage_percent']:.1f}%")
        print(f"  Throttling Active: {status['throttling_active']}")
        print(f"  Current Workers: {status['current_workers']}")
        print()
        
        # Get retry statistics
        retry_stats = manager.get_retry_statistics()
        
        print("Retry Statistics:")
        print(f"  Total Retry Attempts: {retry_stats['total_retry_attempts']}")
        print(f"  Experiments with Retries: {retry_stats['experiments_with_retries']}")
        print(f"  Permanently Failed: {retry_stats['permanently_failed_experiments']}")
        print()
    
    except ImportError:
        print("Resource monitoring not available in mock mode")
        print()


def main():
    """Run all demonstrations."""
    print("DUAL-PROCESS EXPERIMENT EXECUTION SYSTEM DEMONSTRATION")
    print("=" * 60)
    print()
    
    demonstrations = [
        demonstrate_single_experiment,
        demonstrate_parameter_sweep,
        demonstrate_factorial_design,
        demonstrate_metadata_collection,
        demonstrate_resource_monitoring
    ]
    
    for demo in demonstrations:
        try:
            demo()
        except Exception as e:
            print(f"Error in {demo.__name__}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print()
    print("This demonstration showed the key features of the experiment execution system:")
    print("• Single experiment execution with comprehensive metadata collection")
    print("• Parameter sweep execution with parallel processing")
    print("• Factorial design experiments for multi-factor analysis")
    print("• Resource monitoring and throttling for system stability")
    print("• Experiment state persistence for resumability")
    print()
    print("To use this system in practice:")
    print("1. Ensure all dependencies are installed (psutil, pyyaml, etc.)")
    print("2. Configure the Flee executable path")
    print("3. Set up your experiment configurations")
    print("4. Run experiments using the ExperimentRunner class")
    print("5. Analyze results using the generated metadata and output files")


if __name__ == "__main__":
    main()