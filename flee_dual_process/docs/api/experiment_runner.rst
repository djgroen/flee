Experiment Runner API
====================

.. currentmodule:: flee_dual_process.experiment_runner

The experiment runner orchestrates experiment execution with parallel processing, error handling, and comprehensive metadata collection.

Classes
-------

.. autoclass:: ExperimentRunner
   :members:
   :undoc-members:
   :show-inheritance:

   Orchestrates experiment execution with parallel processing and error handling.
   
   This class manages the complete lifecycle of dual-process experiments,
   from input generation through simulation execution and result collection.

   **Example Usage:**
   
   .. code-block:: python
   
       from flee_dual_process.experiment_runner import ExperimentRunner
       
       # Initialize runner
       runner = ExperimentRunner(
           max_parallel=4,
           base_output_dir='results',
           timeout=3600
       )
       
       # Run single experiment
       results = runner.run_single_experiment({
           'experiment_id': 'test_001',
           'topology_files': ('locations.csv', 'routes.csv'),
           'conflicts_file': 'conflicts.csv',
           'config': config_dict,
           'simulation_days': 100
       })

.. autoclass:: ResourceMonitor
   :members:
   :undoc-members:
   :show-inheritance:

   Monitors system resources during experiment execution.
   
   Tracks CPU usage, memory consumption, and disk space to prevent
   system overload during parallel experiment execution.

.. autoclass:: ProcessPoolManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages worker processes for parallel experiment execution.
   
   Coordinates multiple experiment processes with resource monitoring,
   error handling, and automatic retry logic.

Methods
-------

.. automethod:: ExperimentRunner.run_single_experiment

   Execute a single dual-process experiment.
   
   **Parameters:**
   
   - ``experiment_config`` (dict): Experiment configuration containing:
     
     - ``experiment_id`` (str): Unique experiment identifier
     - ``topology_files`` (tuple): Paths to (locations.csv, routes.csv)
     - ``conflicts_file`` (str): Path to conflicts.csv
     - ``config`` (dict): Simulation configuration
     - ``simulation_days`` (int, optional): Number of simulation days
     - ``output_dir`` (str, optional): Custom output directory
   
   **Returns:**
   
   - ``dict``: Experiment results containing:
     
     - ``experiment_id`` (str): Experiment identifier
     - ``status`` (str): 'completed', 'failed', or 'timeout'
     - ``output_dir`` (str): Path to experiment outputs
     - ``execution_time`` (float): Runtime in seconds
     - ``metadata`` (dict): Complete experiment metadata
     - ``error`` (str, optional): Error message if failed
   
   **Example:**
   
   .. code-block:: python
   
       experiment_config = {
           'experiment_id': 'linear_spike_s1',
           'topology_files': ('linear_locations.csv', 'linear_routes.csv'),
           'conflicts_file': 'spike_conflicts.csv',
           'config': s1_config,
           'simulation_days': 100
       }
       
       results = runner.run_single_experiment(experiment_config)
       
       if results['status'] == 'completed':
           print(f"Experiment completed in {results['execution_time']:.2f}s")
           print(f"Results saved to: {results['output_dir']}")
       else:
           print(f"Experiment failed: {results.get('error', 'Unknown error')}")

.. automethod:: ExperimentRunner.run_parameter_sweep

   Execute parameter sweep with multiprocessing support.
   
   **Parameters:**
   
   - ``sweep_config`` (dict): Parameter sweep configuration containing:
     
     - ``base_experiment`` (dict): Base experiment configuration
     - ``parameter_configs`` (list): List of parameter configurations
     - ``sweep_id`` (str): Unique sweep identifier
     - ``max_parallel`` (int, optional): Override default parallelism
   
   **Returns:**
   
   - ``list``: List of experiment results dictionaries
   
   **Example:**
   
   .. code-block:: python
   
       # Generate parameter sweep configurations
       base_config = config_manager.create_cognitive_config('dual_process')
       param_configs = config_manager.generate_parameter_sweep(
           base_config=base_config,
           parameter='move_rules.awareness_level',
           values=[1, 2, 3]
       )
       
       # Run parameter sweep
       sweep_config = {
           'base_experiment': {
               'topology_files': ('locations.csv', 'routes.csv'),
               'conflicts_file': 'conflicts.csv',
               'simulation_days': 100
           },
           'parameter_configs': param_configs,
           'sweep_id': 'awareness_sweep_001'
       }
       
       results = runner.run_parameter_sweep(sweep_config)
       
       # Analyze results
       completed = [r for r in results if r['status'] == 'completed']
       failed = [r for r in results if r['status'] == 'failed']
       
       print(f"Completed: {len(completed)}, Failed: {len(failed)}")

.. automethod:: ExperimentRunner.run_factorial_design

   Execute factorial design experiments.
   
   **Parameters:**
   
   - ``factorial_config`` (dict): Factorial design configuration
   
   **Returns:**
   
   - ``list``: List of experiment results
   
   **Example:**
   
   .. code-block:: python
   
       # 2x3 factorial design
       factors = {
           'move_rules.awareness_level': [1, 3],
           'move_rules.average_social_connectivity': [0.0, 3.0, 8.0]
       }
       
       factorial_configs = config_manager.generate_factorial_design(
           base_config=base_config,
           factors=factors
       )
       
       factorial_config = {
           'base_experiment': base_experiment,
           'factorial_configs': factorial_configs,
           'design_id': 'awareness_connectivity_factorial'
       }
       
       results = runner.run_factorial_design(factorial_config)

.. automethod:: ExperimentRunner.collect_experiment_metadata

   Collect comprehensive metadata for reproducibility tracking.
   
   **Parameters:**
   
   - ``experiment_config`` (dict): Experiment configuration
   
   **Returns:**
   
   - ``dict``: Complete metadata including:
     
     - ``experiment_info``: Configuration and parameters
     - ``system_info``: Hardware and software environment
     - ``timing_info``: Execution timestamps and duration
     - ``file_info``: Input and output file details
     - ``git_info``: Version control information (if available)
   
   **Example:**
   
   .. code-block:: python
   
       metadata = runner.collect_experiment_metadata(experiment_config)
       
       # Metadata includes:
       # - Python version and packages
       # - System hardware specifications
       # - Git commit hash and branch
       # - Input file checksums
       # - Complete parameter settings

Parallel Execution
------------------

The experiment runner supports parallel execution with automatic resource management:

**Configuration**

.. code-block:: python

    # Configure parallel execution
    runner = ExperimentRunner(
        max_parallel=8,  # Maximum concurrent experiments
        timeout=7200,    # 2-hour timeout per experiment
        base_output_dir='large_scale_results'
    )

**Resource Monitoring**

The runner automatically monitors system resources:

- **CPU Usage**: Throttles new experiments if CPU usage > 90%
- **Memory Usage**: Prevents new experiments if memory usage > 85%
- **Disk Space**: Checks available disk space before starting experiments
- **Process Limits**: Respects system process limits

**Error Handling and Retry**

Automatic retry logic with exponential backoff:

.. code-block:: python

    # Configure retry behavior
    runner.configure_retry_policy(
        max_retries=3,
        initial_delay=60,    # 1 minute initial delay
        backoff_factor=2.0,  # Double delay each retry
        max_delay=600        # Maximum 10 minute delay
    )

**Progress Tracking**

Real-time progress monitoring:

.. code-block:: python

    # Enable progress tracking
    results = runner.run_parameter_sweep(
        sweep_config,
        progress_callback=lambda completed, total: 
            print(f"Progress: {completed}/{total} ({100*completed/total:.1f}%)")
    )

Experiment State Management
---------------------------

**State Persistence**

Experiment states are automatically saved for resumability:

.. code-block:: python

    # Resume interrupted parameter sweep
    results = runner.resume_parameter_sweep('sweep_001')
    
    # Check experiment status
    status = runner.get_experiment_status('experiment_001')
    print(f"Status: {status['state']}, Progress: {status['progress']}")

**Cleanup and Recovery**

Automatic cleanup of failed experiments:

.. code-block:: python

    # Clean up failed experiments
    runner.cleanup_failed_experiments(
        older_than_hours=24,
        preserve_logs=True
    )
    
    # Recover from system crash
    recovered_experiments = runner.recover_interrupted_experiments()

Output Organization
-------------------

Experiments are organized in a standardized directory structure:

.. code-block:: text

    results/
    ├── experiment_001/
    │   ├── input/
    │   │   ├── locations.csv
    │   │   ├── routes.csv
    │   │   ├── conflicts.csv
    │   │   └── simsetting.yml
    │   ├── output/
    │   │   ├── out.csv
    │   │   ├── cognitive_states.csv
    │   │   ├── decision_log.csv
    │   │   └── social_network.csv
    │   ├── logs/
    │   │   ├── experiment.log
    │   │   └── flee_output.log
    │   └── metadata.json
    └── parameter_sweep_001/
        ├── sweep_metadata.json
        ├── experiment_001/
        ├── experiment_002/
        └── ...

**Metadata Format**

Complete experiment metadata is saved as JSON:

.. code-block:: json

    {
        "experiment_info": {
            "experiment_id": "test_001",
            "topology_type": "linear",
            "scenario_type": "spike",
            "cognitive_mode": "dual_process",
            "parameters": {...}
        },
        "system_info": {
            "python_version": "3.9.7",
            "platform": "Linux-5.4.0",
            "cpu_count": 8,
            "memory_gb": 32.0,
            "packages": {...}
        },
        "timing_info": {
            "start_time": "2024-01-15T10:30:00Z",
            "end_time": "2024-01-15T10:45:30Z",
            "duration_seconds": 930.5
        },
        "file_info": {
            "input_files": {...},
            "output_files": {...},
            "checksums": {...}
        }
    }

Performance Optimization
------------------------

**Batch Processing**

Process multiple experiments efficiently:

.. code-block:: python

    # Batch similar experiments
    batched_results = runner.run_experiment_batch(
        experiments=experiment_list,
        batch_size=10,
        shared_inputs=True  # Reuse common input files
    )

**Memory Management**

Optimize memory usage for large parameter sweeps:

.. code-block:: python

    # Configure memory limits
    runner.configure_memory_limits(
        max_memory_per_process=4.0,  # GB
        memory_cleanup_threshold=0.8,
        garbage_collection_frequency=10
    )

**Disk I/O Optimization**

Minimize disk I/O overhead:

.. code-block:: python

    # Use temporary directories for intermediate files
    runner.configure_io_optimization(
        use_tmpfs=True,
        compress_outputs=True,
        async_file_operations=True
    )

Error Handling
--------------

Comprehensive error handling and reporting:

.. code-block:: python

    try:
        results = runner.run_parameter_sweep(sweep_config)
    except ExperimentTimeoutError as e:
        print(f"Experiments timed out: {e}")
    except ResourceExhaustionError as e:
        print(f"System resources exhausted: {e}")
    except ValidationError as e:
        print(f"Configuration validation failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Detailed error information available in logs

**Error Recovery**

Automatic error recovery strategies:

- **Timeout Recovery**: Restart timed-out experiments with extended timeout
- **Memory Recovery**: Reduce parallelism if memory errors occur
- **Disk Recovery**: Clean up disk space and retry
- **Configuration Recovery**: Validate and fix configuration issues

Best Practices
--------------

1. **Resource Planning**: Monitor system resources before large parameter sweeps
2. **Timeout Setting**: Set appropriate timeouts based on experiment complexity
3. **Error Monitoring**: Check experiment logs for warnings and errors
4. **State Management**: Use state persistence for long-running experiments
5. **Reproducibility**: Save complete metadata for all experiments
6. **Cleanup**: Regularly clean up failed and temporary experiments
7. **Validation**: Validate configurations before starting experiments
8. **Monitoring**: Use progress callbacks for long-running parameter sweeps