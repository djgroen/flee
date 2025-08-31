"""
Experiment Execution System

Orchestrates experiment execution with parallel processing, error handling,
and comprehensive metadata collection for dual-process experiments.
"""

import os
import sys
import time
import json
import shutil
import subprocess
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import traceback
import psutil
import threading
from pathlib import Path

try:
    from .config_manager import ConfigurationManager, ExperimentConfig
    from .topology_generator import TopologyGenerator
    from .scenario_generator import ConflictScenarioGenerator
    from .utils import LoggingUtils, ValidationUtils, FileUtils
except ImportError:
    from config_manager import ConfigurationManager, ExperimentConfig
    from topology_generator import TopologyGenerator
    from scenario_generator import ConflictScenarioGenerator
    from utils import LoggingUtils, ValidationUtils, FileUtils


class ExperimentRunner:
    """
    Orchestrates experiment execution with parallel processing and error handling.
    
    This class manages the complete lifecycle of dual-process experiments,
    from input generation through simulation execution and result collection.
    """
    
    def __init__(self, max_parallel: int = 4, base_output_dir: str = "results",
                 flee_executable: str = None, timeout: int = 3600):
        """
        Initialize experiment runner.
        
        Args:
            max_parallel: Maximum number of parallel experiments
            base_output_dir: Base directory for experiment outputs
            flee_executable: Path to Flee executable (auto-detected if None)
            timeout: Timeout for individual experiments in seconds
        """
        self.max_parallel = max_parallel
        self.base_output_dir = base_output_dir
        self.timeout = timeout
        
        # Initialize utilities
        self.logging_utils = LoggingUtils()
        self.validation_utils = ValidationUtils()
        self.file_utils = FileUtils()
        self.config_manager = ConfigurationManager()
        
        # Setup logger
        self.logger = self.logging_utils.get_logger('ExperimentRunner')
        
        # Find Flee executable
        self.flee_executable = flee_executable or self._find_flee_executable()
        if not self.flee_executable:
            raise RuntimeError("Could not find Flee executable. Please specify flee_executable parameter.")
        
        # Initialize resource monitoring
        self.resource_monitor = ResourceMonitor()
        
        # Experiment state tracking
        self.experiment_states = {}
        self.failed_experiments = []
        self.completed_experiments = []
        
        # Ensure base output directory exists
        self.file_utils.ensure_directory(self.base_output_dir)
        
        self.logger.info(f"ExperimentRunner initialized with max_parallel={max_parallel}")
        self.logger.info(f"Using Flee executable: {self.flee_executable}")
    
    def _find_flee_executable(self) -> Optional[str]:
        """
        Auto-detect Flee executable location.
        
        Returns:
            Path to Flee executable or None if not found
        """
        # Common locations to check
        possible_paths = [
            "runscripts/run.py",
            "flee/runscripts/run.py",
            "../runscripts/run.py",
            "../flee/runscripts/run.py",
            "run.py"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # Check if run.py is in PATH
        try:
            result = subprocess.run(['which', 'run.py'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def run_single_experiment(self, experiment_config: Union[ExperimentConfig, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run a single experiment with proper error handling and logging.
        
        Args:
            experiment_config: Experiment configuration (ExperimentConfig object or dictionary)
            
        Returns:
            Dictionary with experiment results and metadata
        """
        # Handle both ExperimentConfig objects and dictionaries
        if isinstance(experiment_config, dict):
            experiment_id = experiment_config.get('experiment_id', 'unknown')
            config_dict = experiment_config
        else:
            experiment_id = experiment_config.experiment_id
            config_dict = experiment_config.to_dict()
        self.logger.info(f"Starting experiment: {experiment_id}")
        
        start_time = time.time()
        experiment_dir = None
        
        try:
            # Setup experiment directory
            experiment_dir = self._setup_experiment_directory(experiment_id)
            
            # Update experiment state
            self.experiment_states[experiment_id] = {
                'status': 'running',
                'start_time': start_time,
                'directory': experiment_dir
            }
            
            # Generate input files
            self._generate_experiment_inputs(config_dict, experiment_dir)
            
            # Execute Flee simulation
            simulation_success = self._execute_flee_simulation(experiment_dir)
            
            if not simulation_success:
                raise RuntimeError("Flee simulation failed")
            
            # Collect experiment metadata
            metadata = self._collect_experiment_metadata(config_dict, experiment_dir, start_time)
            
            # Validate outputs
            if not self._validate_experiment_outputs(experiment_dir):
                raise RuntimeError("Output validation failed")
            
            # Mark as completed
            self.experiment_states[experiment_id]['status'] = 'completed'
            self.experiment_states[experiment_id]['end_time'] = time.time()
            self.completed_experiments.append(experiment_id)
            
            self.logger.info(f"Experiment {experiment_id} completed successfully")
            
            return {
                'experiment_id': experiment_id,
                'success': True,
                'experiment_dir': experiment_dir,
                'metadata': metadata,
                'execution_time': time.time() - start_time
            }
            
        except Exception as e:
            # Mark as failed
            self.experiment_states[experiment_id] = {
                'status': 'failed',
                'error': str(e),
                'start_time': start_time,
                'end_time': time.time(),
                'directory': experiment_dir
            }
            self.failed_experiments.append(experiment_id)
            
            self.logger.error(f"Experiment {experiment_id} failed: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            
            return {
                'experiment_id': experiment_id,
                'success': False,
                'error': str(e),
                'experiment_dir': experiment_dir,
                'execution_time': time.time() - start_time
            }
    
    def _setup_experiment_directory(self, experiment_id: str) -> str:
        """
        Setup directory structure for experiment.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            Path to experiment directory
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        experiment_dir = os.path.join(self.base_output_dir, f"{experiment_id}_{timestamp}")
        
        # Create directory structure
        directories = [
            experiment_dir,
            os.path.join(experiment_dir, 'input'),
            os.path.join(experiment_dir, 'output'),
            os.path.join(experiment_dir, 'logs'),
            os.path.join(experiment_dir, 'metadata')
        ]
        
        for directory in directories:
            self.file_utils.ensure_directory(directory)
        
        self.logger.debug(f"Created experiment directory: {experiment_dir}")
        return experiment_dir
    
    def _generate_experiment_inputs(self, experiment_config: Dict[str, Any], experiment_dir: str) -> None:
        """
        Generate all input files for experiment.
        
        Args:
            experiment_config: Experiment configuration dictionary
            experiment_dir: Experiment directory path
        """
        input_dir = os.path.join(experiment_dir, 'input')
        os.makedirs(input_dir, exist_ok=True)
        
        # Get topology generator based on type
        topology_type = experiment_config.get('topology_type', 'linear')
        topology_params = experiment_config.get('topology_params', {})
        
        base_config = {'output_dir': input_dir}
        
        if topology_type == 'linear':
            from .topology_generator import LinearTopologyGenerator
            topology_generator = LinearTopologyGenerator(base_config)
            locations_file, routes_file = topology_generator.generate_linear(**topology_params)
        elif topology_type == 'star':
            from .topology_generator import StarTopologyGenerator
            topology_generator = StarTopologyGenerator(base_config)
            locations_file, routes_file = topology_generator.generate_star(**topology_params)
        elif topology_type == 'tree':
            from .topology_generator import TreeTopologyGenerator
            topology_generator = TreeTopologyGenerator(base_config)
            locations_file, routes_file = topology_generator.generate_tree(**topology_params)
        elif topology_type == 'grid':
            from .topology_generator import GridTopologyGenerator
            topology_generator = GridTopologyGenerator(base_config)
            locations_file, routes_file = topology_generator.generate_grid(**topology_params)
        else:
            raise ValueError(f"Unknown topology type: {topology_type}")
        
        # Generate scenario files
        scenario_type = experiment_config.get('scenario_type', 'spike')
        scenario_params = experiment_config.get('scenario_params', {})
        
        if scenario_type == 'spike':
            from .scenario_generator import SpikeConflictGenerator
            scenario_generator = SpikeConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_spike_conflict(
                output_dir=input_dir, **scenario_params
            )
        elif scenario_type == 'gradual':
            from .scenario_generator import GradualConflictGenerator
            scenario_generator = GradualConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_gradual_conflict(
                output_dir=input_dir, **scenario_params
            )
        elif scenario_type == 'cascading':
            from .scenario_generator import CascadingConflictGenerator
            scenario_generator = CascadingConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_cascading_conflict(
                output_dir=input_dir, **scenario_params
            )
        elif scenario_type == 'oscillating':
            from .scenario_generator import OscillatingConflictGenerator
            scenario_generator = OscillatingConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_oscillating_conflict(
                output_dir=input_dir, **scenario_params
            )
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
        
        # Generate configuration files
        cognitive_mode = experiment_config.get('cognitive_mode', 'dual_process')
        simulation_params = experiment_config.get('simulation_params', {})
        
        if not hasattr(self, 'config_manager'):
            from .config_manager import ConfigurationManager
            self.config_manager = ConfigurationManager()
        
        config = self.config_manager.create_cognitive_config(cognitive_mode)
        config.update(simulation_params)
        
        simsetting_file = os.path.join(input_dir, 'simsetting.yml')
        self.config_manager.create_simsetting_yml(config, simsetting_file)
        
        # Create sim_period.csv (required by Flee)
        self._create_sim_period_file(input_dir, scenario_params)
        
        # Create empty files that Flee expects
        self._create_empty_flee_files(input_dir)
        
        experiment_id = experiment_config.get('experiment_id', 'unknown')
        self.logger.debug(f"Generated input files for experiment {experiment_id}")
    
    def _create_sim_period_file(self, input_dir: str, scenario_params: Dict[str, Any]) -> None:
        """
        Create sim_period.csv file required by Flee.
        
        Args:
            input_dir: Input directory path
            scenario_params: Scenario parameters containing simulation period
        """
        # Extract simulation period from scenario parameters
        start_day = scenario_params.get('start_day', 0)
        duration = scenario_params.get('duration', 100)
        end_day = start_day + duration
        
        sim_period_file = os.path.join(input_dir, 'sim_period.csv')
        with open(sim_period_file, 'w') as f:
            f.write('#StartDate,EndDate\n')
            f.write(f'{start_day},{end_day}\n')
    
    def _create_empty_flee_files(self, input_dir: str) -> None:
        """
        Create empty files that Flee expects but may not be needed for experiments.
        
        Args:
            input_dir: Input directory path
        """
        empty_files = [
            'closures.csv',
            'registration_corrections.csv'
        ]
        
        for filename in empty_files:
            filepath = os.path.join(input_dir, filename)
            with open(filepath, 'w') as f:
                if filename == 'closures.csv':
                    f.write('#closure_type,name1,name2,closure_start,closure_end\n')
                elif filename == 'registration_corrections.csv':
                    f.write('#name,day,correction\n')
    
    def _execute_flee_simulation(self, experiment_dir: str) -> bool:
        """
        Execute Flee simulation for experiment.
        
        Args:
            experiment_dir: Experiment directory path
            
        Returns:
            True if simulation succeeded, False otherwise
        """
        input_dir = os.path.join(experiment_dir, 'input')
        output_dir = os.path.join(experiment_dir, 'output')
        log_dir = os.path.join(experiment_dir, 'logs')
        
        # Prepare command
        cmd = [
            sys.executable,
            self.flee_executable,
            input_dir,
            output_dir
        ]
        
        # Setup logging
        stdout_log = os.path.join(log_dir, 'flee_stdout.log')
        stderr_log = os.path.join(log_dir, 'flee_stderr.log')
        
        try:
            with open(stdout_log, 'w') as stdout_file, open(stderr_log, 'w') as stderr_file:
                process = subprocess.run(
                    cmd,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    timeout=self.timeout,
                    cwd=input_dir
                )
            
            if process.returncode == 0:
                self.logger.debug(f"Flee simulation completed successfully")
                return True
            else:
                self.logger.error(f"Flee simulation failed with return code {process.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Flee simulation timed out after {self.timeout} seconds")
            return False
        except Exception as e:
            self.logger.error(f"Error executing Flee simulation: {e}")
            return False
    
    def _validate_experiment_outputs(self, experiment_dir: str) -> bool:
        """
        Validate experiment outputs for completeness and format.
        
        Args:
            experiment_dir: Experiment directory path
            
        Returns:
            True if outputs are valid, False otherwise
        """
        output_dir = os.path.join(experiment_dir, 'output')
        
        # Check if output directory exists and has files
        if not os.path.exists(output_dir):
            self.logger.error("Output directory does not exist")
            return False
        
        output_files = os.listdir(output_dir)
        if not output_files:
            self.logger.error("No output files generated")
            return False
        
        # Check for expected output files (basic validation)
        expected_patterns = ['out.csv', 'agents.out']
        found_patterns = []
        
        for pattern in expected_patterns:
            for filename in output_files:
                if pattern in filename:
                    found_patterns.append(pattern)
                    break
        
        if len(found_patterns) < len(expected_patterns):
            missing = set(expected_patterns) - set(found_patterns)
            self.logger.warning(f"Some expected output files missing: {missing}")
            # Don't fail validation for missing files, just warn
        
        return True
    
    def _collect_experiment_metadata(self, experiment_config: Dict[str, Any], 
                                   experiment_dir: str, start_time: float) -> Dict[str, Any]:
        """
        Collect comprehensive experiment metadata for reproducibility.
        
        Args:
            experiment_config: Experiment configuration
            experiment_dir: Experiment directory path
            start_time: Experiment start time
            
        Returns:
            Dictionary with experiment metadata
        """
        end_time = time.time()
        
        metadata = {
            'experiment_id': experiment_config.get('experiment_id', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'execution_time': end_time - start_time,
            'configuration': experiment_config,
            'system_info': self._collect_system_info(),
            'flee_version': self._get_flee_version(),
            'input_files': self._collect_input_file_info(experiment_dir),
            'output_files': self._collect_output_file_info(experiment_dir),
            'resource_usage': self.resource_monitor.get_peak_usage() if hasattr(self, 'resource_monitor') else {}
        }
        
        # Save metadata to file
        metadata_file = os.path.join(experiment_dir, 'metadata', 'experiment_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return metadata
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information."""
        return {
            'platform': sys.platform,
            'python_version': sys.version,
            'cpu_count': mp.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        }
    
    def _get_flee_version(self) -> str:
        """Get Flee version information."""
        try:
            # Try to get version from Flee module
            import flee
            if hasattr(flee, '__version__'):
                return flee.__version__
            elif hasattr(flee, '_version'):
                return flee._version.__version__
        except:
            pass
        
        return 'unknown'
    
    def _collect_input_file_info(self, experiment_dir: str) -> Dict[str, Any]:
        """Collect information about input files."""
        input_dir = os.path.join(experiment_dir, 'input')
        file_info = {}
        
        if os.path.exists(input_dir):
            for filename in os.listdir(input_dir):
                filepath = os.path.join(input_dir, filename)
                if os.path.isfile(filepath):
                    file_info[filename] = {
                        'size': self.file_utils.get_file_size(filepath),
                        'timestamp': self.file_utils.get_file_timestamp(filepath).isoformat()
                    }
        
        return file_info
    
    def _collect_output_file_info(self, experiment_dir: str) -> Dict[str, Any]:
        """Collect information about output files."""
        output_dir = os.path.join(experiment_dir, 'output')
        file_info = {}
        
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                filepath = os.path.join(output_dir, filename)
                if os.path.isfile(filepath):
                    file_info[filename] = {
                        'size': self.file_utils.get_file_size(filepath),
                        'timestamp': self.file_utils.get_file_timestamp(filepath).isoformat()
                    }
        
        return file_info


class ResourceMonitor:
    """
    Monitor system resource usage during experiment execution.
    """
    
    def __init__(self):
        """Initialize resource monitor."""
        self.monitoring = False
        self.peak_memory = 0
        self.peak_cpu = 0
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start resource monitoring in background thread."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_resources(self):
        """Monitor resources in background thread."""
        while self.monitoring:
            try:
                # Monitor memory usage
                memory = psutil.virtual_memory()
                self.peak_memory = max(self.peak_memory, memory.used)
                
                # Monitor CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.peak_cpu = max(self.peak_cpu, cpu_percent)
                
                time.sleep(1)
            except:
                break
    
    def get_peak_usage(self) -> Dict[str, Any]:
        """Get peak resource usage."""
        return {
            'peak_memory_bytes': self.peak_memory,
            'peak_cpu_percent': self.peak_cpu,
            'current_memory_bytes': psutil.virtual_memory().used,
            'current_cpu_percent': psutil.cpu_percent()
        }

    def run_parameter_sweep(self, sweep_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute parameter sweep with multiprocessing support.
        
        Args:
            sweep_config: Parameter sweep configuration containing:
                - base_config: Base experiment configuration
                - parameter: Parameter name to sweep
                - values: List of parameter values
                - replications: Number of replications per configuration
                
        Returns:
            List of experiment results
        """
        self.logger.info("Starting parameter sweep execution")
        
        # Generate experiment configurations
        experiment_configs = self._generate_sweep_experiments(sweep_config)
        
        self.logger.info(f"Generated {len(experiment_configs)} experiment configurations")
        
        # Execute experiments with progress tracking
        results = self._execute_experiments_parallel(experiment_configs)
        
        # Save sweep summary
        self._save_sweep_summary(sweep_config, results)
        
        self.logger.info(f"Parameter sweep completed. {len(self.completed_experiments)} successful, "
                        f"{len(self.failed_experiments)} failed")
        
        return results
    
    def _generate_sweep_experiments(self, sweep_config: Dict[str, Any]) -> List[ExperimentConfig]:
        """
        Generate experiment configurations for parameter sweep.
        
        Args:
            sweep_config: Parameter sweep configuration
            
        Returns:
            List of experiment configurations
        """
        base_config = sweep_config['base_config']
        parameter = sweep_config['parameter']
        values = sweep_config['values']
        replications = sweep_config.get('replications', 1)
        
        experiment_configs = []
        
        for i, value in enumerate(values):
            for rep in range(replications):
                # Create unique experiment ID
                experiment_id = f"sweep_{parameter}_{value}_rep{rep}_{i:03d}"
                
                # Create experiment configuration
                config = ExperimentConfig(
                    experiment_id=experiment_id,
                    topology_type=base_config['topology_type'],
                    topology_params=base_config['topology_params'],
                    scenario_type=base_config['scenario_type'],
                    scenario_params=base_config['scenario_params'],
                    cognitive_mode=base_config['cognitive_mode'],
                    simulation_params=base_config.get('simulation_params', {}),
                    replications=1,
                    metadata={
                        'sweep_parameter': parameter,
                        'sweep_value': value,
                        'replication': rep,
                        'sweep_index': i
                    }
                )
                
                # Apply parameter value to appropriate section
                if parameter.startswith('topology_params.'):
                    param_name = parameter.replace('topology_params.', '')
                    config.topology_params[param_name] = value
                elif parameter.startswith('scenario_params.'):
                    param_name = parameter.replace('scenario_params.', '')
                    config.scenario_params[param_name] = value
                elif parameter.startswith('simulation_params.'):
                    param_name = parameter.replace('simulation_params.', '')
                    config.simulation_params[param_name] = value
                else:
                    # Direct parameter
                    setattr(config, parameter, value)
                
                experiment_configs.append(config)
        
        return experiment_configs
    
    def _execute_experiments_parallel(self, experiment_configs: List[ExperimentConfig]) -> List[Dict[str, Any]]:
        """
        Execute experiments in parallel with progress tracking.
        
        Args:
            experiment_configs: List of experiment configurations
            
        Returns:
            List of experiment results
        """
        results = []
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        try:
            with ProcessPoolExecutor(max_workers=self.max_parallel) as executor:
                # Submit all experiments
                future_to_config = {
                    executor.submit(self._run_experiment_worker, config): config
                    for config in experiment_configs
                }
                
                # Process completed experiments with progress tracking
                completed = 0
                total = len(experiment_configs)
                
                for future in as_completed(future_to_config):
                    config = future_to_config[future]
                    completed += 1
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Log progress
                        progress = (completed / total) * 100
                        self.logger.info(f"Progress: {completed}/{total} ({progress:.1f}%) - "
                                       f"Experiment {config.experiment_id}: {result['status']}")
                        
                    except Exception as e:
                        self.logger.error(f"Experiment {config.experiment_id} failed with exception: {e}")
                        results.append({
                            'experiment_id': config.experiment_id,
                            'status': 'failed',
                            'error': str(e),
                            'execution_time': 0
                        })
        
        finally:
            # Stop resource monitoring
            self.resource_monitor.stop_monitoring()
        
        return results
    
    def _run_experiment_worker(self, experiment_config: ExperimentConfig) -> Dict[str, Any]:
        """
        Worker function for parallel experiment execution.
        
        Args:
            experiment_config: Experiment configuration
            
        Returns:
            Experiment result dictionary
        """
        # Create new runner instance for worker process
        worker_runner = ExperimentRunner(
            max_parallel=1,
            base_output_dir=self.base_output_dir,
            flee_executable=self.flee_executable,
            timeout=self.timeout
        )
        
        return worker_runner.run_single_experiment(experiment_config)
    
    def _save_sweep_summary(self, sweep_config: Dict[str, Any], results: List[Dict[str, Any]]) -> None:
        """
        Save parameter sweep summary and results.
        
        Args:
            sweep_config: Parameter sweep configuration
            results: List of experiment results
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_dir = os.path.join(self.base_output_dir, f"sweep_summary_{timestamp}")
        self.file_utils.ensure_directory(summary_dir)
        
        # Create summary data
        summary = {
            'sweep_config': sweep_config,
            'timestamp': datetime.now().isoformat(),
            'total_experiments': len(results),
            'successful_experiments': len([r for r in results if r['status'] == 'success']),
            'failed_experiments': len([r for r in results if r['status'] == 'failed']),
            'total_execution_time': sum(r.get('execution_time', 0) for r in results),
            'results': results
        }
        
        # Save summary as JSON
        summary_file = os.path.join(summary_dir, 'sweep_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save results as CSV for easy analysis
        self._save_results_csv(results, os.path.join(summary_dir, 'sweep_results.csv'))
        
        self.logger.info(f"Saved parameter sweep summary to {summary_dir}")
    
    def _save_results_csv(self, results: List[Dict[str, Any]], csv_file: str) -> None:
        """
        Save experiment results as CSV file.
        
        Args:
            results: List of experiment results
            csv_file: Output CSV file path
        """
        if not results:
            return
        
        import csv
        
        # Extract all possible fields from results
        fieldnames = set()
        for result in results:
            fieldnames.update(result.keys())
            if 'metadata' in result and isinstance(result['metadata'], dict):
                for key in result['metadata'].keys():
                    fieldnames.add(f"metadata_{key}")
        
        fieldnames = sorted(fieldnames)
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                row = result.copy()
                
                # Flatten metadata
                if 'metadata' in row and isinstance(row['metadata'], dict):
                    metadata = row.pop('metadata')
                    for key, value in metadata.items():
                        row[f"metadata_{key}"] = value
                
                # Convert complex objects to strings
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value)
                
                writer.writerow(row)
    
    def run_factorial_design(self, factors: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """
        Execute factorial design experiment.
        
        Args:
            factors: Dictionary mapping parameter names to lists of values
            
        Returns:
            List of experiment results
        """
        self.logger.info("Starting factorial design execution")
        
        # Generate all factor combinations
        experiment_configs = self._generate_factorial_experiments(factors)
        
        self.logger.info(f"Generated {len(experiment_configs)} factorial combinations")
        
        # Execute experiments
        results = self._execute_experiments_parallel(experiment_configs)
        
        # Save factorial summary
        self._save_factorial_summary(factors, results)
        
        self.logger.info(f"Factorial design completed. {len(self.completed_experiments)} successful, "
                        f"{len(self.failed_experiments)} failed")
        
        return results
    
    def _generate_factorial_experiments(self, factors: Dict[str, List[Any]]) -> List[ExperimentConfig]:
        """
        Generate experiment configurations for factorial design.
        
        Args:
            factors: Dictionary mapping parameter names to lists of values
            
        Returns:
            List of experiment configurations
        """
        import itertools
        
        experiment_configs = []
        
        # Get parameter names and their value lists
        parameter_names = list(factors.keys())
        value_lists = list(factors.values())
        
        # Generate all combinations using Cartesian product
        for i, combination in enumerate(itertools.product(*value_lists)):
            # Create unique experiment ID
            param_values = {param: val for param, val in zip(parameter_names, combination)}
            experiment_id = f"factorial_{i:03d}_" + "_".join(f"{k}_{v}" for k, v in param_values.items())
            
            # Create base configuration (you may want to make this configurable)
            config = ExperimentConfig(
                experiment_id=experiment_id,
                topology_type='linear',  # Default topology
                topology_params={'n_nodes': 5, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                scenario_type='spike',   # Default scenario
                scenario_params={'start_day': 0, 'peak_intensity': 0.8, 'duration': 100},
                cognitive_mode='dual_process',  # Default cognitive mode
                simulation_params={},
                replications=1,
                metadata={
                    'factorial_design': True,
                    'factor_combination': param_values,
                    'combination_index': i
                }
            )
            
            # Apply factor values to appropriate sections
            for param_name, value in param_values.items():
                if param_name.startswith('topology_params.'):
                    param_key = param_name.replace('topology_params.', '')
                    config.topology_params[param_key] = value
                elif param_name.startswith('scenario_params.'):
                    param_key = param_name.replace('scenario_params.', '')
                    config.scenario_params[param_key] = value
                elif param_name.startswith('simulation_params.'):
                    param_key = param_name.replace('simulation_params.', '')
                    config.simulation_params[param_key] = value
                elif param_name == 'topology_type':
                    config.topology_type = value
                elif param_name == 'scenario_type':
                    config.scenario_type = value
                elif param_name == 'cognitive_mode':
                    config.cognitive_mode = value
                else:
                    # Store in metadata if not recognized
                    config.metadata[param_name] = value
            
            experiment_configs.append(config)
        
        return experiment_configs
    
    def _save_factorial_summary(self, factors: Dict[str, List[Any]], results: List[Dict[str, Any]]) -> None:
        """
        Save factorial design summary and results.
        
        Args:
            factors: Factorial design factors
            results: List of experiment results
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_dir = os.path.join(self.base_output_dir, f"factorial_summary_{timestamp}")
        self.file_utils.ensure_directory(summary_dir)
        
        # Create summary data
        summary = {
            'factors': factors,
            'timestamp': datetime.now().isoformat(),
            'total_combinations': len(results),
            'successful_experiments': len([r for r in results if r['status'] == 'success']),
            'failed_experiments': len([r for r in results if r['status'] == 'failed']),
            'total_execution_time': sum(r.get('execution_time', 0) for r in results),
            'results': results
        }
        
        # Save summary as JSON
        summary_file = os.path.join(summary_dir, 'factorial_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save results as CSV
        self._save_results_csv(results, os.path.join(summary_dir, 'factorial_results.csv'))
        
        self.logger.info(f"Saved factorial design summary to {summary_dir}")
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get status of specific experiment.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            Dictionary with experiment status information
        """
        return self.experiment_states.get(experiment_id, {'status': 'not_found'})
    
    def get_all_experiment_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all experiments.
        
        Returns:
            Dictionary mapping experiment IDs to status information
        """
        return self.experiment_states.copy()
    
    def cleanup_experiment_directory(self, experiment_id: str, keep_outputs: bool = True) -> bool:
        """
        Clean up experiment directory, optionally keeping outputs.
        
        Args:
            experiment_id: Experiment identifier
            keep_outputs: Whether to keep output files
            
        Returns:
            True if cleanup succeeded, False otherwise
        """
        if experiment_id not in self.experiment_states:
            self.logger.warning(f"Experiment {experiment_id} not found for cleanup")
            return False
        
        experiment_dir = self.experiment_states[experiment_id].get('directory')
        if not experiment_dir or not os.path.exists(experiment_dir):
            self.logger.warning(f"Experiment directory not found: {experiment_dir}")
            return False
        
        try:
            if keep_outputs:
                # Remove only input and log directories
                for subdir in ['input', 'logs']:
                    subdir_path = os.path.join(experiment_dir, subdir)
                    if os.path.exists(subdir_path):
                        shutil.rmtree(subdir_path)
            else:
                # Remove entire experiment directory
                shutil.rmtree(experiment_dir)
            
            self.logger.info(f"Cleaned up experiment directory: {experiment_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup experiment directory {experiment_dir}: {e}")
            return False
    
    def save_experiment_state(self, state_file: str) -> None:
        """
        Save experiment state for resumability.
        
        Args:
            state_file: Path to state file
        """
        state_data = {
            'experiment_states': self.experiment_states,
            'completed_experiments': self.completed_experiments,
            'failed_experiments': self.failed_experiments,
            'timestamp': datetime.now().isoformat()
        }
        
        self.file_utils.ensure_directory(os.path.dirname(state_file))
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2, default=str)
        
        self.logger.info(f"Saved experiment state to {state_file}")
    
    def load_experiment_state(self, state_file: str) -> bool:
        """
        Load experiment state for resumability.
        
        Args:
            state_file: Path to state file
            
        Returns:
            True if state loaded successfully, False otherwise
        """
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            self.experiment_states = state_data.get('experiment_states', {})
            self.completed_experiments = state_data.get('completed_experiments', [])
            self.failed_experiments = state_data.get('failed_experiments', [])
            
            self.logger.info(f"Loaded experiment state from {state_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load experiment state from {state_file}: {e}")
            return False

class ProcessPoolManager:
    """
    Manages worker process coordination with resource monitoring and throttling.
    
    This class provides advanced process pool management with resource monitoring,
    automatic throttling, and retry logic with exponential backoff.
    """
    
    def __init__(self, max_workers: int = 4, memory_threshold: float = 0.8, 
                 cpu_threshold: float = 0.9, retry_attempts: int = 3):
        """
        Initialize process pool manager.
        
        Args:
            max_workers: Maximum number of worker processes
            memory_threshold: Memory usage threshold for throttling (0.0-1.0)
            cpu_threshold: CPU usage threshold for throttling (0.0-1.0)
            retry_attempts: Maximum number of retry attempts for failed experiments
        """
        self.max_workers = max_workers
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.retry_attempts = retry_attempts
        
        # Resource monitoring
        self.resource_monitor = ResourceMonitor()
        self.throttling_active = False
        self.current_workers = 0
        
        # Retry tracking
        self.retry_counts = {}
        self.failed_experiments = []
        
        # Logging
        self.logger = LoggingUtils().get_logger('ProcessPoolManager')
        
        self.logger.info(f"ProcessPoolManager initialized with max_workers={max_workers}")
    
    def execute_experiments(self, experiment_configs: List[ExperimentConfig], 
                          experiment_runner: 'ExperimentRunner') -> List[Dict[str, Any]]:
        """
        Execute experiments with resource monitoring and retry logic.
        
        Args:
            experiment_configs: List of experiment configurations
            experiment_runner: ExperimentRunner instance
            
        Returns:
            List of experiment results
        """
        self.logger.info(f"Starting execution of {len(experiment_configs)} experiments")
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        results = []
        pending_experiments = experiment_configs.copy()
        
        try:
            while pending_experiments:
                # Check resource usage and adjust worker count
                current_workers = self._adjust_worker_count()
                
                # Execute batch of experiments
                batch_size = min(current_workers * 2, len(pending_experiments))
                current_batch = pending_experiments[:batch_size]
                pending_experiments = pending_experiments[batch_size:]
                
                batch_results = self._execute_batch(current_batch, experiment_runner)
                
                # Process results and handle retries
                for result in batch_results:
                    if result['status'] == 'failed':
                        retry_result = self._handle_failed_experiment(
                            result, experiment_runner
                        )
                        if retry_result:
                            results.append(retry_result)
                        else:
                            results.append(result)
                    else:
                        results.append(result)
                
                # Log progress
                completed = len(results)
                total = len(experiment_configs)
                progress = (completed / total) * 100
                self.logger.info(f"Progress: {completed}/{total} ({progress:.1f}%)")
                
                # Brief pause to allow system recovery if throttling
                if self.throttling_active:
                    time.sleep(2)
        
        finally:
            # Stop resource monitoring
            self.resource_monitor.stop_monitoring()
        
        self.logger.info(f"Completed execution of {len(results)} experiments")
        return results
    
    def _adjust_worker_count(self) -> int:
        """
        Adjust worker count based on resource usage.
        
        Returns:
            Current optimal worker count
        """
        # Get current resource usage
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        memory_usage = memory.used / memory.total
        cpu_usage = cpu_percent / 100.0
        
        # Determine if throttling is needed
        memory_throttle = memory_usage > self.memory_threshold
        cpu_throttle = cpu_usage > self.cpu_threshold
        
        if memory_throttle or cpu_throttle:
            if not self.throttling_active:
                self.logger.warning(f"Resource throttling activated - Memory: {memory_usage:.1%}, "
                                  f"CPU: {cpu_usage:.1%}")
                self.throttling_active = True
            
            # Reduce worker count
            optimal_workers = max(1, self.max_workers // 2)
        else:
            if self.throttling_active:
                self.logger.info("Resource throttling deactivated")
                self.throttling_active = False
            
            # Use full worker count
            optimal_workers = self.max_workers
        
        self.current_workers = optimal_workers
        return optimal_workers
    
    def _execute_batch(self, experiment_configs: List[ExperimentConfig], 
                      experiment_runner: 'ExperimentRunner') -> List[Dict[str, Any]]:
        """
        Execute a batch of experiments in parallel.
        
        Args:
            experiment_configs: List of experiment configurations for this batch
            experiment_runner: ExperimentRunner instance
            
        Returns:
            List of experiment results
        """
        results = []
        
        with ProcessPoolExecutor(max_workers=self.current_workers) as executor:
            # Submit experiments
            future_to_config = {
                executor.submit(self._execute_single_experiment, config, experiment_runner): config
                for config in experiment_configs
            }
            
            # Collect results with timeout handling
            for future in as_completed(future_to_config, timeout=experiment_runner.timeout + 60):
                config = future_to_config[future]
                
                try:
                    result = future.result(timeout=30)  # Additional timeout for result retrieval
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Experiment {config.experiment_id} failed with exception: {e}")
                    results.append({
                        'experiment_id': config.experiment_id,
                        'status': 'failed',
                        'error': str(e),
                        'execution_time': 0,
                        'retry_eligible': True
                    })
        
        return results
    
    def _execute_single_experiment(self, experiment_config: ExperimentConfig, 
                                 experiment_runner: 'ExperimentRunner') -> Dict[str, Any]:
        """
        Execute a single experiment in worker process.
        
        Args:
            experiment_config: Experiment configuration
            experiment_runner: ExperimentRunner instance
            
        Returns:
            Experiment result dictionary
        """
        try:
            # Create isolated runner for worker process
            worker_runner = ExperimentRunner(
                max_parallel=1,
                base_output_dir=experiment_runner.base_output_dir,
                flee_executable=experiment_runner.flee_executable,
                timeout=experiment_runner.timeout
            )
            
            return worker_runner.run_single_experiment(experiment_config)
            
        except Exception as e:
            return {
                'experiment_id': experiment_config.experiment_id,
                'status': 'failed',
                'error': str(e),
                'execution_time': 0,
                'retry_eligible': True
            }
    
    def _handle_failed_experiment(self, failed_result: Dict[str, Any], 
                                experiment_runner: 'ExperimentRunner') -> Optional[Dict[str, Any]]:
        """
        Handle failed experiment with retry logic and exponential backoff.
        
        Args:
            failed_result: Failed experiment result
            experiment_runner: ExperimentRunner instance
            
        Returns:
            Retry result if successful, None if all retries exhausted
        """
        experiment_id = failed_result['experiment_id']
        
        # Check if experiment is eligible for retry
        if not failed_result.get('retry_eligible', True):
            self.logger.info(f"Experiment {experiment_id} not eligible for retry")
            return None
        
        # Initialize retry count if not exists
        if experiment_id not in self.retry_counts:
            self.retry_counts[experiment_id] = 0
        
        # Check if retry attempts exhausted
        if self.retry_counts[experiment_id] >= self.retry_attempts:
            self.logger.error(f"Experiment {experiment_id} failed after {self.retry_attempts} attempts")
            self.failed_experiments.append(experiment_id)
            return None
        
        # Increment retry count
        self.retry_counts[experiment_id] += 1
        retry_count = self.retry_counts[experiment_id]
        
        self.logger.info(f"Retrying experiment {experiment_id} (attempt {retry_count}/{self.retry_attempts})")
        
        # Exponential backoff delay
        delay = min(2 ** retry_count, 60)  # Cap at 60 seconds
        time.sleep(delay)
        
        # Recreate experiment configuration from failed result
        # This is a simplified approach - in practice, you might want to store
        # the original configuration more systematically
        try:
            # For now, we'll skip the retry and just return None
            # In a full implementation, you would reconstruct the ExperimentConfig
            # and retry the experiment
            self.logger.warning(f"Retry logic not fully implemented for {experiment_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Retry failed for experiment {experiment_id}: {e}")
            return None
    
    def get_resource_status(self) -> Dict[str, Any]:
        """
        Get current resource status and throttling information.
        
        Returns:
            Dictionary with resource status information
        """
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        return {
            'memory_usage_percent': (memory.used / memory.total) * 100,
            'memory_available_gb': memory.available / (1024**3),
            'cpu_usage_percent': cpu_percent,
            'throttling_active': self.throttling_active,
            'current_workers': self.current_workers,
            'max_workers': self.max_workers,
            'memory_threshold_percent': self.memory_threshold * 100,
            'cpu_threshold_percent': self.cpu_threshold * 100
        }
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        Get retry statistics for failed experiments.
        
        Returns:
            Dictionary with retry statistics
        """
        total_retries = sum(self.retry_counts.values())
        experiments_with_retries = len(self.retry_counts)
        
        return {
            'total_retry_attempts': total_retries,
            'experiments_with_retries': experiments_with_retries,
            'permanently_failed_experiments': len(self.failed_experiments),
            'retry_counts': self.retry_counts.copy(),
            'failed_experiment_ids': self.failed_experiments.copy()
        }


class ExperimentStateManager:
    """
    Manages experiment state persistence for resumability after failures.
    """
    
    def __init__(self, state_dir: str = "experiment_state"):
        """
        Initialize experiment state manager.
        
        Args:
            state_dir: Directory for storing state files
        """
        self.state_dir = state_dir
        self.logger = LoggingUtils().get_logger('ExperimentStateManager')
        
        # Ensure state directory exists
        FileUtils.ensure_directory(state_dir)
    
    def save_experiment_state(self, experiment_id: str, state: Dict[str, Any]) -> str:
        """
        Save experiment state to file.
        
        Args:
            experiment_id: Experiment identifier
            state: State dictionary to save
            
        Returns:
            Path to saved state file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        state_file = os.path.join(self.state_dir, f"{experiment_id}_{timestamp}.json")
        
        # Add timestamp to state
        state['saved_timestamp'] = datetime.now().isoformat()
        state['experiment_id'] = experiment_id
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        self.logger.debug(f"Saved experiment state for {experiment_id} to {state_file}")
        return state_file
    
    def load_experiment_state(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Load most recent experiment state.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            State dictionary if found, None otherwise
        """
        # Find most recent state file for experiment
        pattern = f"{experiment_id}_*.json"
        state_files = FileUtils.list_files(self.state_dir, pattern)
        
        if not state_files:
            return None
        
        # Sort by timestamp and get most recent
        state_files.sort(reverse=True)
        latest_state_file = state_files[0]
        
        try:
            with open(latest_state_file, 'r') as f:
                state = json.load(f)
            
            self.logger.debug(f"Loaded experiment state for {experiment_id} from {latest_state_file}")
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to load experiment state from {latest_state_file}: {e}")
            return None
    
    def list_experiment_states(self) -> List[Dict[str, Any]]:
        """
        List all available experiment states.
        
        Returns:
            List of state information dictionaries
        """
        state_files = FileUtils.list_files(self.state_dir, "*.json")
        states = []
        
        for state_file in state_files:
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                states.append({
                    'experiment_id': state.get('experiment_id', 'unknown'),
                    'saved_timestamp': state.get('saved_timestamp', 'unknown'),
                    'file_path': state_file,
                    'file_size': FileUtils.get_file_size(state_file)
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to read state file {state_file}: {e}")
        
        return sorted(states, key=lambda x: x['saved_timestamp'], reverse=True)
    
    def cleanup_old_states(self, max_age_days: int = 30) -> int:
        """
        Clean up old state files.
        
        Args:
            max_age_days: Maximum age of state files to keep
            
        Returns:
            Number of files cleaned up
        """
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        state_files = FileUtils.list_files(self.state_dir, "*.json")
        
        cleaned_count = 0
        for state_file in state_files:
            try:
                file_time = os.path.getmtime(state_file)
                if file_time < cutoff_time:
                    os.remove(state_file)
                    cleaned_count += 1
                    self.logger.debug(f"Removed old state file: {state_file}")
            except Exception as e:
                self.logger.warning(f"Failed to remove state file {state_file}: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old state files")
        
        return cleaned_count


class ExperimentMetadataCollector:
    """
    Comprehensive metadata collection for reproducibility tracking.
    
    This class collects detailed metadata about experiments including
    system information, configuration parameters, timing data, and
    resource usage for full reproducibility.
    """
    
    def __init__(self):
        """Initialize metadata collector."""
        self.logger = LoggingUtils().get_logger('ExperimentMetadataCollector')
    
    def collect_experiment_metadata(self, experiment_config: ExperimentConfig, 
                                  experiment_dir: str, start_time: float,
                                  end_time: float = None) -> Dict[str, Any]:
        """
        Collect comprehensive experiment metadata.
        
        Args:
            experiment_config: Experiment configuration
            experiment_dir: Experiment directory path
            start_time: Experiment start time (timestamp)
            end_time: Experiment end time (timestamp, current time if None)
            
        Returns:
            Dictionary with comprehensive metadata
        """
        if end_time is None:
            end_time = time.time()
        
        metadata = {
            # Basic experiment information
            'experiment_id': experiment_config.experiment_id,
            'timestamp': datetime.now().isoformat(),
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'execution_time_seconds': end_time - start_time,
            
            # Configuration information
            'configuration': self._collect_configuration_metadata(experiment_config),
            
            # System information
            'system_info': self._collect_system_info(),
            
            # Environment information
            'environment': self._collect_environment_info(),
            
            # Software versions
            'software_versions': self._collect_software_versions(),
            
            # File information
            'input_files': self._collect_input_file_metadata(experiment_dir),
            'output_files': self._collect_output_file_metadata(experiment_dir),
            
            # Resource usage
            'resource_usage': self._collect_resource_usage_metadata(),
            
            # Git information (if available)
            'git_info': self._collect_git_info(),
            
            # Validation results
            'validation': self._collect_validation_metadata(experiment_dir)
        }
        
        # Save metadata to file
        self._save_metadata_file(metadata, experiment_dir)
        
        return metadata
    
    def _collect_configuration_metadata(self, experiment_config: ExperimentConfig) -> Dict[str, Any]:
        """Collect configuration metadata."""
        return {
            'experiment_config': experiment_config.to_dict(),
            'config_hash': self._calculate_config_hash(experiment_config),
            'parameter_count': self._count_parameters(experiment_config),
            'topology_summary': self._summarize_topology_params(experiment_config.topology_params),
            'scenario_summary': self._summarize_scenario_params(experiment_config.scenario_params)
        }
    
    def _calculate_config_hash(self, experiment_config: ExperimentConfig) -> str:
        """Calculate hash of configuration for uniqueness checking."""
        import hashlib
        
        config_str = json.dumps(experiment_config.to_dict(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _count_parameters(self, experiment_config: ExperimentConfig) -> Dict[str, int]:
        """Count parameters in different sections."""
        return {
            'topology_params': len(experiment_config.topology_params),
            'scenario_params': len(experiment_config.scenario_params),
            'simulation_params': len(experiment_config.simulation_params),
            'metadata_params': len(experiment_config.metadata)
        }
    
    def _summarize_topology_params(self, topology_params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize topology parameters."""
        summary = {}
        
        # Extract key topology characteristics
        if 'n_nodes' in topology_params:
            summary['node_count'] = topology_params['n_nodes']
        if 'rows' in topology_params and 'cols' in topology_params:
            summary['grid_size'] = topology_params['rows'] * topology_params['cols']
        if 'start_pop' in topology_params:
            summary['initial_population'] = topology_params['start_pop']
        
        return summary
    
    def _summarize_scenario_params(self, scenario_params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize scenario parameters."""
        summary = {}
        
        # Extract key scenario characteristics
        if 'duration' in scenario_params:
            summary['simulation_duration'] = scenario_params['duration']
        if 'peak_intensity' in scenario_params:
            summary['max_conflict_intensity'] = scenario_params['peak_intensity']
        if 'start_day' in scenario_params:
            summary['conflict_start_day'] = scenario_params['start_day']
        
        return summary
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect detailed system information."""
        system_info = {
            'platform': sys.platform,
            'architecture': os.uname().machine if hasattr(os, 'uname') else 'unknown',
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
            'python_version': sys.version,
            'python_executable': sys.executable,
            'cpu_count': mp.cpu_count(),
            'cpu_info': self._get_cpu_info(),
            'memory_info': self._get_memory_info(),
            'disk_info': self._get_disk_info()
        }
        
        return system_info
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information."""
        try:
            cpu_freq = psutil.cpu_freq()
            return {
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'max_frequency_mhz': cpu_freq.max if cpu_freq else None,
                'current_frequency_mhz': cpu_freq.current if cpu_freq else None,
                'cpu_percent': psutil.cpu_percent(interval=1)
            }
        except Exception as e:
            self.logger.warning(f"Failed to collect CPU info: {e}")
            return {'error': str(e)}
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_bytes': memory.total,
                'available_bytes': memory.available,
                'used_bytes': memory.used,
                'used_percent': memory.percent,
                'swap_total_bytes': swap.total,
                'swap_used_bytes': swap.used,
                'swap_percent': swap.percent
            }
        except Exception as e:
            self.logger.warning(f"Failed to collect memory info: {e}")
            return {'error': str(e)}
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk information."""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                'total_bytes': disk_usage.total,
                'used_bytes': disk_usage.used,
                'free_bytes': disk_usage.free,
                'used_percent': (disk_usage.used / disk_usage.total) * 100
            }
        except Exception as e:
            self.logger.warning(f"Failed to collect disk info: {e}")
            return {'error': str(e)}
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information."""
        env_info = {
            'working_directory': os.getcwd(),
            'python_path': sys.path,
            'environment_variables': self._get_relevant_env_vars(),
            'locale': self._get_locale_info()
        }
        
        return env_info
    
    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Get relevant environment variables."""
        relevant_vars = [
            'PATH', 'PYTHONPATH', 'HOME', 'USER', 'SHELL',
            'FLEE_TYPE_CHECK', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'
        ]
        
        env_vars = {}
        for var in relevant_vars:
            if var in os.environ:
                env_vars[var] = os.environ[var]
        
        return env_vars
    
    def _get_locale_info(self) -> Dict[str, str]:
        """Get locale information."""
        try:
            import locale
            return {
                'default_locale': locale.getdefaultlocale()[0] or 'unknown',
                'preferred_encoding': locale.getpreferredencoding()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _collect_software_versions(self) -> Dict[str, str]:
        """Collect software version information."""
        versions = {}
        
        # Core Python packages
        packages_to_check = [
            'numpy', 'pandas', 'matplotlib', 'scipy', 'psutil',
            'pyyaml', 'mpi4py', 'networkx'
        ]
        
        for package in packages_to_check:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                versions[package] = version
            except ImportError:
                versions[package] = 'not_installed'
            except Exception as e:
                versions[package] = f'error: {e}'
        
        # Flee version
        try:
            import flee
            if hasattr(flee, '__version__'):
                versions['flee'] = flee.__version__
            elif hasattr(flee, '_version'):
                versions['flee'] = flee._version.__version__
            else:
                versions['flee'] = 'unknown'
        except ImportError:
            versions['flee'] = 'not_installed'
        except Exception as e:
            versions['flee'] = f'error: {e}'
        
        return versions
    
    def _collect_input_file_metadata(self, experiment_dir: str) -> Dict[str, Any]:
        """Collect metadata about input files."""
        input_dir = os.path.join(experiment_dir, 'input')
        file_metadata = {}
        
        if os.path.exists(input_dir):
            for filename in os.listdir(input_dir):
                filepath = os.path.join(input_dir, filename)
                if os.path.isfile(filepath):
                    file_metadata[filename] = self._get_file_metadata(filepath)
        
        return file_metadata
    
    def _collect_output_file_metadata(self, experiment_dir: str) -> Dict[str, Any]:
        """Collect metadata about output files."""
        output_dir = os.path.join(experiment_dir, 'output')
        file_metadata = {}
        
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                filepath = os.path.join(output_dir, filename)
                if os.path.isfile(filepath):
                    file_metadata[filename] = self._get_file_metadata(filepath)
        
        return file_metadata
    
    def _get_file_metadata(self, filepath: str) -> Dict[str, Any]:
        """Get metadata for a single file."""
        try:
            stat = os.stat(filepath)
            
            metadata = {
                'size_bytes': stat.st_size,
                'created_timestamp': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:],
                'checksum': self._calculate_file_checksum(filepath)
            }
            
            # Add line count for text files
            if filepath.endswith(('.csv', '.txt', '.yml', '.yaml', '.log')):
                metadata['line_count'] = self._count_file_lines(filepath)
            
            return metadata
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_file_checksum(self, filepath: str) -> str:
        """Calculate MD5 checksum of file."""
        import hashlib
        
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return f'error: {e}'
    
    def _count_file_lines(self, filepath: str) -> int:
        """Count lines in text file."""
        try:
            with open(filepath, 'r') as f:
                return sum(1 for _ in f)
        except Exception:
            return -1
    
    def _collect_resource_usage_metadata(self) -> Dict[str, Any]:
        """Collect resource usage metadata."""
        try:
            process = psutil.Process()
            
            return {
                'current_memory_bytes': process.memory_info().rss,
                'current_cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'num_file_descriptors': process.num_fds() if hasattr(process, 'num_fds') else None,
                'system_memory_percent': psutil.virtual_memory().percent,
                'system_cpu_percent': psutil.cpu_percent()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _collect_git_info(self) -> Dict[str, Any]:
        """Collect Git repository information if available."""
        try:
            # Try to get git information
            git_info = {}
            
            # Get current commit hash
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                git_info['commit_hash'] = result.stdout.strip()
            
            # Get current branch
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                git_info['branch'] = result.stdout.strip()
            
            # Check for uncommitted changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                git_info['has_uncommitted_changes'] = bool(result.stdout.strip())
                git_info['uncommitted_files'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Get remote URL
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                git_info['remote_url'] = result.stdout.strip()
            
            return git_info
            
        except Exception as e:
            return {'error': str(e), 'available': False}
    
    def _collect_validation_metadata(self, experiment_dir: str) -> Dict[str, Any]:
        """Collect validation metadata."""
        validation_info = {
            'input_validation': self._validate_input_files(experiment_dir),
            'output_validation': self._validate_output_files(experiment_dir),
            'directory_structure': self._validate_directory_structure(experiment_dir)
        }
        
        return validation_info
    
    def _validate_input_files(self, experiment_dir: str) -> Dict[str, Any]:
        """Validate input files."""
        input_dir = os.path.join(experiment_dir, 'input')
        validation = {
            'directory_exists': os.path.exists(input_dir),
            'required_files': {},
            'file_count': 0
        }
        
        if validation['directory_exists']:
            required_files = ['locations.csv', 'routes.csv', 'conflicts.csv', 'simsetting.yml']
            
            for filename in required_files:
                filepath = os.path.join(input_dir, filename)
                validation['required_files'][filename] = {
                    'exists': os.path.exists(filepath),
                    'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
                }
            
            validation['file_count'] = len([f for f in os.listdir(input_dir) 
                                          if os.path.isfile(os.path.join(input_dir, f))])
        
        return validation
    
    def _validate_output_files(self, experiment_dir: str) -> Dict[str, Any]:
        """Validate output files."""
        output_dir = os.path.join(experiment_dir, 'output')
        validation = {
            'directory_exists': os.path.exists(output_dir),
            'file_count': 0,
            'total_size_bytes': 0
        }
        
        if validation['directory_exists']:
            files = [f for f in os.listdir(output_dir) 
                    if os.path.isfile(os.path.join(output_dir, f))]
            validation['file_count'] = len(files)
            
            total_size = 0
            for filename in files:
                filepath = os.path.join(output_dir, filename)
                total_size += os.path.getsize(filepath)
            validation['total_size_bytes'] = total_size
        
        return validation
    
    def _validate_directory_structure(self, experiment_dir: str) -> Dict[str, bool]:
        """Validate experiment directory structure."""
        expected_dirs = ['input', 'output', 'logs', 'metadata']
        
        structure_validation = {}
        for dirname in expected_dirs:
            dirpath = os.path.join(experiment_dir, dirname)
            structure_validation[dirname] = os.path.exists(dirpath)
        
        return structure_validation
    
    def _save_metadata_file(self, metadata: Dict[str, Any], experiment_dir: str) -> str:
        """Save metadata to file."""
        metadata_dir = os.path.join(experiment_dir, 'metadata')
        FileUtils.ensure_directory(metadata_dir)
        
        metadata_file = os.path.join(metadata_dir, 'experiment_metadata.json')
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Also save a human-readable summary
        summary_file = os.path.join(metadata_dir, 'experiment_summary.txt')
        self._save_metadata_summary(metadata, summary_file)
        
        return metadata_file
    
    def _save_metadata_summary(self, metadata: Dict[str, Any], summary_file: str) -> None:
        """Save human-readable metadata summary."""
        with open(summary_file, 'w') as f:
            f.write("Experiment Metadata Summary\n")
            f.write("=" * 50 + "\n\n")
            
            # Basic information
            f.write(f"Experiment ID: {metadata['experiment_id']}\n")
            f.write(f"Timestamp: {metadata['timestamp']}\n")
            f.write(f"Execution Time: {metadata['execution_time_seconds']:.2f} seconds\n\n")
            
            # Configuration summary
            config = metadata.get('configuration', {})
            f.write("Configuration:\n")
            f.write(f"  Topology: {config.get('experiment_config', {}).get('topology_type', 'unknown')}\n")
            f.write(f"  Scenario: {config.get('experiment_config', {}).get('scenario_type', 'unknown')}\n")
            f.write(f"  Cognitive Mode: {config.get('experiment_config', {}).get('cognitive_mode', 'unknown')}\n\n")
            
            # System information
            system = metadata.get('system_info', {})
            f.write("System Information:\n")
            f.write(f"  Platform: {system.get('platform', 'unknown')}\n")
            f.write(f"  CPU Cores: {system.get('cpu_count', 'unknown')}\n")
            f.write(f"  Memory: {system.get('memory_info', {}).get('total_bytes', 0) / (1024**3):.1f} GB\n\n")
            
            # File information
            input_files = metadata.get('input_files', {})
            output_files = metadata.get('output_files', {})
            f.write(f"Files:\n")
            f.write(f"  Input files: {len(input_files)}\n")
            f.write(f"  Output files: {len(output_files)}\n\n")
            
            # Validation results
            validation = metadata.get('validation', {})
            f.write("Validation:\n")
            input_val = validation.get('input_validation', {})
            output_val = validation.get('output_validation', {})
            f.write(f"  Input directory exists: {input_val.get('directory_exists', False)}\n")
            f.write(f"  Output directory exists: {output_val.get('directory_exists', False)}\n")
            f.write(f"  Output files generated: {output_val.get('file_count', 0)}\n")
    
    def validate_metadata_integrity(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata integrity and completeness.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'completeness_score': 0.0
        }
        
        # Required fields
        required_fields = [
            'experiment_id', 'timestamp', 'execution_time_seconds',
            'configuration', 'system_info', 'software_versions'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in metadata:
                missing_fields.append(field)
        
        if missing_fields:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Missing required fields: {missing_fields}")
        
        # Check for empty or invalid values
        if metadata.get('execution_time_seconds', 0) <= 0:
            validation_results['warnings'].append("Execution time is zero or negative")
        
        if not metadata.get('experiment_id'):
            validation_results['errors'].append("Experiment ID is empty")
            validation_results['is_valid'] = False
        
        # Calculate completeness score
        total_sections = 10  # Expected number of metadata sections
        present_sections = sum(1 for section in [
            'experiment_id', 'configuration', 'system_info', 'environment',
            'software_versions', 'input_files', 'output_files', 'resource_usage',
            'git_info', 'validation'
        ] if section in metadata and metadata[section])
        
        validation_results['completeness_score'] = present_sections / total_sections
        
        return validation_results