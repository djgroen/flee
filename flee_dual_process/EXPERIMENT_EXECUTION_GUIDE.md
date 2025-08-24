# Experiment Execution System Guide

This guide explains how to use the experiment execution system implemented for dual-process experiments in the Flee framework.

## Overview

The experiment execution system provides comprehensive infrastructure for running systematic experiments to test dual-process theory in refugee movement simulations. It includes:

- **ExperimentRunner**: Core class for executing single experiments and parameter sweeps
- **ProcessPoolManager**: Advanced parallel execution with resource monitoring and retry logic
- **ExperimentMetadataCollector**: Comprehensive metadata collection for reproducibility
- **ExperimentStateManager**: State persistence for resumability after failures

## Key Features

### 1. Single Experiment Execution
- Automated input file generation (topology, scenarios, configurations)
- Flee simulation execution with timeout handling
- Comprehensive error handling and logging
- Output validation and metadata collection

### 2. Parameter Sweep Execution
- Systematic variation of single parameters
- Parallel execution with configurable worker pools
- Progress tracking and status reporting
- Automatic result aggregation and CSV export

### 3. Factorial Design Experiments
- Multi-factor experimental designs
- All combinations of factor levels
- Statistical analysis support

### 4. Resource Management
- Memory and CPU usage monitoring
- Automatic throttling to prevent system overload
- Retry logic with exponential backoff
- Resource usage reporting

### 5. Metadata Collection
- System information (hardware, software versions)
- Configuration parameters and checksums
- File metadata (sizes, timestamps, checksums)
- Git repository information
- Validation results

## Usage Examples

### Basic Single Experiment

```python
from experiment_runner import ExperimentRunner
from config_manager import ExperimentConfig

# Create experiment configuration
config = ExperimentConfig(
    experiment_id="test_001",
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
        "average_social_connectivity": 3.0
    }
)

# Create runner and execute
runner = ExperimentRunner(
    max_parallel=4,
    base_output_dir="results",
    flee_executable="path/to/flee/run.py",
    timeout=1800
)

result = runner.run_single_experiment(config)
print(f"Experiment {result['experiment_id']}: {result['status']}")
```

### Parameter Sweep

```python
# Define parameter sweep
sweep_config = {
    'base_config': {
        'topology_type': 'linear',
        'topology_params': {'n_nodes': 8, 'segment_distance': 50.0},
        'scenario_type': 'gradual',
        'scenario_params': {'start_day': 5, 'duration': 120},
        'cognitive_mode': 'dual_process'
    },
    'parameter': 'simulation_params.average_social_connectivity',
    'values': [0.0, 1.0, 3.0, 5.0, 8.0],
    'replications': 3
}

# Run parameter sweep
results = runner.run_parameter_sweep(sweep_config)

# Analyze results
successful = len([r for r in results if r['status'] == 'success'])
print(f"Completed {successful}/{len(results)} experiments successfully")
```

### Factorial Design

```python
# Define factorial factors
factors = {
    'topology_params.n_nodes': [5, 10, 15],
    'scenario_params.peak_intensity': [0.6, 0.8, 1.0],
    'simulation_params.awareness_level': [1, 2, 3]
}

# Run factorial design (3 × 3 × 3 = 27 combinations)
results = runner.run_factorial_design(factors)
```

### Advanced Resource Management

```python
from experiment_runner import ProcessPoolManager

# Create process pool manager with custom settings
manager = ProcessPoolManager(
    max_workers=8,
    memory_threshold=0.8,  # Throttle at 80% memory usage
    cpu_threshold=0.9,     # Throttle at 90% CPU usage
    retry_attempts=3       # Retry failed experiments up to 3 times
)

# Execute experiments with advanced management
results = manager.execute_experiments(experiment_configs, runner)

# Monitor resource usage
status = manager.get_resource_status()
print(f"Memory usage: {status['memory_usage_percent']:.1f}%")
print(f"Throttling active: {status['throttling_active']}")
```

### Metadata Collection

```python
from experiment_runner import ExperimentMetadataCollector

collector = ExperimentMetadataCollector()

# Collect comprehensive metadata
metadata = collector.collect_experiment_metadata(
    experiment_config, experiment_dir, start_time
)

# Validate metadata integrity
validation = collector.validate_metadata_integrity(metadata)
print(f"Metadata completeness: {validation['completeness_score']:.2f}")
```

## Output Structure

Each experiment creates a structured output directory:

```
experiment_id_timestamp/
├── input/                  # Generated input files
│   ├── locations.csv
│   ├── routes.csv
│   ├── conflicts.csv
│   ├── simsetting.yml
│   └── sim_period.csv
├── output/                 # Flee simulation outputs
│   ├── out.csv
│   ├── agents.out
│   └── ...
├── logs/                   # Execution logs
│   ├── flee_stdout.log
│   └── flee_stderr.log
└── metadata/               # Experiment metadata
    ├── experiment_metadata.json
    └── experiment_summary.txt
```

## Configuration Options

### ExperimentRunner Parameters

- `max_parallel`: Maximum number of parallel experiments (default: 4)
- `base_output_dir`: Base directory for experiment outputs (default: "results")
- `flee_executable`: Path to Flee executable (auto-detected if None)
- `timeout`: Timeout for individual experiments in seconds (default: 3600)

### ProcessPoolManager Parameters

- `max_workers`: Maximum number of worker processes (default: 4)
- `memory_threshold`: Memory usage threshold for throttling (default: 0.8)
- `cpu_threshold`: CPU usage threshold for throttling (default: 0.9)
- `retry_attempts`: Maximum retry attempts for failed experiments (default: 3)

## Error Handling

The system provides comprehensive error handling:

1. **Configuration Validation**: Validates experiment parameters before execution
2. **Resource Monitoring**: Prevents system overload through throttling
3. **Timeout Handling**: Terminates hung simulations after specified timeout
4. **Retry Logic**: Automatically retries failed experiments with exponential backoff
5. **State Persistence**: Saves experiment state for resumability after failures

## Best Practices

### 1. Resource Planning
- Monitor system resources during large parameter sweeps
- Adjust `max_parallel` based on available CPU cores and memory
- Use appropriate timeouts for different experiment types

### 2. Experiment Design
- Start with small parameter sweeps to validate setup
- Use factorial designs for systematic multi-factor analysis
- Include multiple replications for statistical validity

### 3. Result Management
- Regularly backup experiment results
- Use descriptive experiment IDs for easy identification
- Clean up intermediate files to save disk space

### 4. Reproducibility
- Always save complete metadata for each experiment
- Use version control for experiment configurations
- Document experimental procedures and rationale

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed (psutil, pyyaml, etc.)
2. **Flee Executable Not Found**: Specify the correct path to Flee's run.py
3. **Memory Issues**: Reduce `max_parallel` or increase `memory_threshold`
4. **Timeout Errors**: Increase timeout for complex experiments
5. **Permission Errors**: Ensure write permissions for output directories

### Performance Optimization

1. **Parallel Execution**: Use multiple workers but don't exceed CPU core count
2. **Resource Monitoring**: Enable throttling to prevent system overload
3. **Disk I/O**: Use fast storage for experiment outputs
4. **Memory Management**: Monitor memory usage during large sweeps

## Integration with Analysis Pipeline

The experiment execution system is designed to integrate with the analysis pipeline (Task 7). Experiment outputs include:

- Standardized CSV files for movement data
- Cognitive state logs for dual-process analysis
- Comprehensive metadata for reproducibility
- Structured directory organization for batch processing

## Testing

Run the test suite to verify installation:

```bash
python flee_dual_process/test_experiment_runner_simple.py
```

Run the demonstration script to see examples:

```bash
python flee_dual_process/example_experiment_execution.py
```

## Requirements

### System Requirements
- Python 3.8+
- 4+ GB RAM (8+ GB recommended for large sweeps)
- Multi-core CPU (4+ cores recommended)
- Sufficient disk space for experiment outputs

### Python Dependencies
- psutil (resource monitoring)
- pyyaml (configuration files)
- pandas (data handling)
- numpy (numerical operations)
- multiprocessing (parallel execution)

### Flee Dependencies
- Working Flee installation
- All Flee dependencies satisfied
- Flee executable accessible

This experiment execution system provides a robust foundation for systematic dual-process experiments in the Flee framework, enabling researchers to conduct comprehensive studies of cognitive decision-making in refugee movement simulations.