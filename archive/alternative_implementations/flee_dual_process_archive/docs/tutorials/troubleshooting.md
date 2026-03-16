# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using the Flee Dual Process framework.

## Common Issues and Solutions

### 1. Import and Installation Issues

#### Problem: Module Import Errors

```python
ImportError: No module named 'flee_dual_process'
```

**Solutions:**

1. **Check Python Path**:
   ```python
   import sys
   print(sys.path)
   # Add Flee directory to path if needed
   sys.path.append('/path/to/flee/directory')
   ```

2. **Verify Installation**:
   ```bash
   # Check if required packages are installed
   pip list | grep -E "(numpy|pandas|matplotlib|scipy|pyyaml)"
   
   # Install missing packages
   pip install numpy pandas matplotlib seaborn scipy pyyaml
   ```

3. **Check File Structure**:
   ```bash
   # Ensure flee_dual_process directory exists in Flee project
   ls -la flee_dual_process/
   # Should show: __init__.py and module files
   ```

#### Problem: Flee Core Import Errors

```python
ImportError: No module named 'flee'
```

**Solutions:**

1. **Install Flee Framework**:
   ```bash
   # From Flee project root directory
   python setup.py install
   # Or for development
   python setup.py develop
   ```

2. **Check Flee Installation**:
   ```python
   try:
       import flee
       print("Flee imported successfully")
   except ImportError as e:
       print(f"Flee import failed: {e}")
   ```

### 2. Configuration Issues

#### Problem: Invalid Configuration Parameters

```python
ValueError: Parameter 'move_rules.awareness_level' must be between 1 and 3, got 5
```

**Solutions:**

1. **Check Parameter Ranges**:
   ```python
   from flee_dual_process import ConfigurationManager
   
   config_manager = ConfigurationManager()
   
   # Valid ranges for key parameters:
   valid_ranges = {
       'awareness_level': [1, 2, 3],
       'average_social_connectivity': [0.0, float('inf')],
       'conflict_threshold': [0.0, 1.0],
       'weight_softening': [0.0, 1.0],
       'recovery_period_max': [1, float('inf')]
   }
   ```

2. **Validate Configuration Before Use**:
   ```python
   config = config_manager.create_cognitive_config('dual_process')
   
   if config_manager.validate_configuration(config):
       print("Configuration is valid")
   else:
       print("Configuration validation failed")
   ```

3. **Use Predefined Configurations**:
   ```python
   # Use tested predefined configurations
   safe_config = config_manager.create_cognitive_config('dual_process')
   # Then modify specific parameters carefully
   ```

#### Problem: Unknown Cognitive Mode

```python
ValueError: Unknown cognitive mode: invalid_mode. Available modes: ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
```

**Solution:**

```python
# Use only valid cognitive modes
valid_modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']

for mode in valid_modes:
    config = config_manager.create_cognitive_config(mode)
    print(f"Created config for {mode}")
```

### 3. Topology Generation Issues

#### Problem: Invalid Topology Parameters

```python
ValueError: Linear topology requires at least 2 nodes
```

**Solutions:**

1. **Check Minimum Requirements**:
   ```python
   from flee_dual_process import LinearTopologyGenerator
   
   # Minimum parameter values
   min_params = {
       'linear': {'n_nodes': 2},
       'star': {'n_camps': 1},
       'tree': {'branching_factor': 2, 'depth': 1},
       'grid': {'rows': 1, 'cols': 1}
   }
   ```

2. **Validate Parameters Before Generation**:
   ```python
   topology_gen = LinearTopologyGenerator({'output_dir': 'output'})
   
   # Check parameters
   params = {'n_nodes': 5, 'segment_distance': 50.0, 'start_pop': 10000, 'pop_decay': 0.8}
   
   if topology_gen.validate_topology_parameters(**params):
       locations, routes = topology_gen.generate_linear(**params)
   else:
       print("Invalid topology parameters")
   ```

#### Problem: Topology Validation Failures

```python
RuntimeError: Generated topology failed validation
```

**Solutions:**

1. **Check Output Files**:
   ```python
   import os
   
   # Verify files were created
   if os.path.exists(locations_file) and os.path.exists(routes_file):
       print("Files created successfully")
       
       # Check file contents
       with open(locations_file, 'r') as f:
           print("Locations file preview:")
           print(f.read()[:500])
   ```

2. **Manual Validation**:
   ```python
   # Validate topology manually
   is_valid = topology_gen.validate_topology(locations_file, routes_file)
   if not is_valid:
       print("Topology validation failed - check file formats")
   ```

### 4. Scenario Generation Issues

#### Problem: Origin Location Not Found

```python
FileNotFoundError: Origin location 'InvalidLocation' not found in topology
```

**Solutions:**

1. **Check Available Locations**:
   ```python
   from flee_dual_process import SpikeConflictGenerator
   
   scenario_gen = SpikeConflictGenerator(locations_file)
   print("Available locations:")
   for location in scenario_gen.location_names:
       print(f"  {location}")
   ```

2. **Use Correct Location Names**:
   ```python
   # For linear topology, typical names are:
   # 'Origin', 'Town_1', 'Town_2', ..., 'Camp_N'
   
   conflicts_file = scenario_gen.generate_spike_conflict(
       origin='Origin',  # Use exact name from locations file
       start_day=0,
       peak_intensity=0.9
   )
   ```

#### Problem: Invalid Scenario Parameters

```python
ValueError: peak_intensity must be between 0 and 1, got 1.5
```

**Solutions:**

1. **Check Parameter Ranges**:
   ```python
   # Valid parameter ranges for scenarios
   scenario_ranges = {
       'peak_intensity': [0.0, 1.0],
       'max_intensity': [0.0, 1.0],
       'start_day': [0, float('inf')],
       'spread_rate': [0.0, float('inf')],
       'period': [1, float('inf')]
   }
   ```

2. **Validate Before Generation**:
   ```python
   # Check parameters before using
   peak_intensity = 0.9
   if 0.0 <= peak_intensity <= 1.0:
       conflicts_file = scenario_gen.generate_spike_conflict(
           origin='Origin',
           start_day=0,
           peak_intensity=peak_intensity
       )
   ```

### 5. Experiment Execution Issues

#### Problem: Experiment Timeouts

```python
ExperimentTimeoutError: Experiment timed out after 3600 seconds
```

**Solutions:**

1. **Increase Timeout**:
   ```python
   from flee_dual_process import ExperimentRunner
   
   # Increase timeout for complex experiments
   runner = ExperimentRunner(
       max_parallel=2,
       timeout=7200  # 2 hours
   )
   ```

2. **Reduce Experiment Complexity**:
   ```python
   # Reduce simulation days or topology size
   experiment_config = {
       'simulation_days': 50,  # Reduced from 100
       'topology_files': (small_locations_file, small_routes_file)
   }
   ```

3. **Monitor Resource Usage**:
   ```python
   import psutil
   
   # Check system resources before starting
   print(f"CPU usage: {psutil.cpu_percent()}%")
   print(f"Memory usage: {psutil.virtual_memory().percent}%")
   print(f"Available memory: {psutil.virtual_memory().available / 1e9:.1f} GB")
   ```

#### Problem: Memory Errors

```python
MemoryError: Unable to allocate memory for experiment
```

**Solutions:**

1. **Reduce Parallelism**:
   ```python
   # Reduce number of parallel experiments
   runner = ExperimentRunner(max_parallel=1)
   ```

2. **Process in Batches**:
   ```python
   # For large parameter sweeps, process in smaller batches
   def run_sweep_in_batches(configs, batch_size=5):
       all_results = []
       for i in range(0, len(configs), batch_size):
           batch = configs[i:i+batch_size]
           batch_results = runner.run_parameter_sweep({
               'parameter_configs': batch,
               'base_experiment': base_experiment,
               'sweep_id': f'batch_{i//batch_size}'
           })
           all_results.extend(batch_results)
       return all_results
   ```

3. **Clean Up Between Experiments**:
   ```python
   import gc
   
   # Force garbage collection between experiments
   gc.collect()
   ```

#### Problem: Flee Executable Not Found

```python
RuntimeError: Could not find Flee executable
```

**Solutions:**

1. **Specify Executable Path**:
   ```python
   runner = ExperimentRunner(
       flee_executable='/path/to/flee/runscripts/run.py'
   )
   ```

2. **Check Common Locations**:
   ```python
   import os
   
   possible_paths = [
       'runscripts/run.py',
       'flee/runscripts/run.py',
       '../runscripts/run.py'
   ]
   
   for path in possible_paths:
       if os.path.exists(path):
           print(f"Found Flee executable at: {path}")
           break
   ```

### 6. Analysis and Visualization Issues

#### Problem: Missing Output Files

```python
FileNotFoundError: Required output file not found: cognitive_states.csv
```

**Solutions:**

1. **Check Experiment Success**:
   ```python
   if results['status'] == 'completed':
       # Check what files were actually generated
       output_dir = results['output_dir']
       output_files = os.listdir(output_dir)
       print(f"Generated files: {output_files}")
   ```

2. **Handle Missing Files Gracefully**:
   ```python
   from flee_dual_process import AnalysisPipeline
   
   analyzer = AnalysisPipeline('results')
   
   try:
       exp_data = analyzer.load_experiment_data(experiment_dir)
   except FileNotFoundError as e:
       print(f"Missing file: {e}")
       print("Experiment may have failed or used different configuration")
   ```

3. **Verify Cognitive Tracking is Enabled**:
   ```python
   # Ensure dual-process tracking is enabled in configuration
   config = config_manager.create_cognitive_config('dual_process')
   
   # Check that two_system_decision_making is True
   if config['move_rules']['two_system_decision_making']:
       print("Cognitive tracking enabled")
   else:
       print("Cognitive tracking disabled - no cognitive_states.csv will be generated")
   ```

#### Problem: Visualization Errors

```python
ImportError: No module named 'plotly'
```

**Solutions:**

1. **Install Missing Packages**:
   ```bash
   # Install optional visualization packages
   pip install plotly
   pip install seaborn
   ```

2. **Use Alternative Backend**:
   ```python
   from flee_dual_process import VisualizationGenerator
   
   # Use matplotlib if plotly is not available
   viz_gen = VisualizationGenerator(
       results_directory='results',
       backend='matplotlib'  # Instead of 'plotly'
   )
   ```

3. **Check Backend Availability**:
   ```python
   try:
       import plotly
       backend = 'plotly'
   except ImportError:
       backend = 'matplotlib'
   
   viz_gen = VisualizationGenerator(
       results_directory='results',
       backend=backend
   )
   ```

### 7. File System Issues

#### Problem: Permission Errors

```python
PermissionError: [Errno 13] Permission denied: 'results/experiment_001'
```

**Solutions:**

1. **Check Directory Permissions**:
   ```bash
   # Check permissions
   ls -la results/
   
   # Fix permissions if needed
   chmod 755 results/
   chmod -R 644 results/*
   ```

2. **Use Alternative Output Directory**:
   ```python
   import tempfile
   import os
   
   # Use temporary directory if permission issues
   temp_dir = tempfile.mkdtemp()
   runner = ExperimentRunner(base_output_dir=temp_dir)
   ```

#### Problem: Disk Space Issues

```python
OSError: [Errno 28] No space left on device
```

**Solutions:**

1. **Check Disk Space**:
   ```python
   import shutil
   
   # Check available disk space
   total, used, free = shutil.disk_usage('.')
   print(f"Free space: {free / 1e9:.1f} GB")
   ```

2. **Clean Up Old Results**:
   ```python
   # Remove old experiment results
   import glob
   import os
   from datetime import datetime, timedelta
   
   # Remove results older than 7 days
   cutoff_time = datetime.now() - timedelta(days=7)
   
   for result_dir in glob.glob('results/experiment_*'):
       if os.path.getctime(result_dir) < cutoff_time.timestamp():
           shutil.rmtree(result_dir)
           print(f"Removed old result: {result_dir}")
   ```

3. **Compress Results**:
   ```python
   import zipfile
   
   # Compress completed experiments
   def compress_experiment_results(experiment_dir):
       zip_path = f"{experiment_dir}.zip"
       with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
           for root, dirs, files in os.walk(experiment_dir):
               for file in files:
                   file_path = os.path.join(root, file)
                   arcname = os.path.relpath(file_path, experiment_dir)
                   zipf.write(file_path, arcname)
       
       # Remove original directory after compression
       shutil.rmtree(experiment_dir)
       return zip_path
   ```

## Debugging Strategies

### 1. Enable Detailed Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('flee_dual_process')
logger.setLevel(logging.DEBUG)
```

### 2. Run Single Experiments First

```python
# Test with minimal configuration before running parameter sweeps
test_config = {
    'experiment_id': 'debug_test',
    'topology_files': (locations_file, routes_file),
    'conflicts_file': conflicts_file,
    'config': simple_config,
    'simulation_days': 10  # Short simulation for testing
}

result = runner.run_single_experiment(test_config)
print(f"Test result: {result['status']}")
```

### 3. Check Intermediate Files

```python
# Examine intermediate files for debugging
experiment_dir = result['output_dir']

# Check input files
input_dir = os.path.join(experiment_dir, 'input')
for file in os.listdir(input_dir):
    print(f"Input file: {file}")
    
# Check logs
log_dir = os.path.join(experiment_dir, 'logs')
if os.path.exists(log_dir):
    for log_file in os.listdir(log_dir):
        print(f"Log file: {log_file}")
        with open(os.path.join(log_dir, log_file), 'r') as f:
            print(f.read()[-1000:])  # Last 1000 characters
```

### 4. Validate Data at Each Step

```python
# Validate topology
assert os.path.exists(locations_file), "Locations file missing"
assert os.path.exists(routes_file), "Routes file missing"

# Validate scenario
assert os.path.exists(conflicts_file), "Conflicts file missing"

# Validate configuration
assert config_manager.validate_configuration(config), "Invalid configuration"

# Validate experiment setup
assert 'experiment_id' in experiment_config, "Missing experiment ID"
```

## Getting Additional Help

### 1. Check Log Files

Always check the experiment log files for detailed error information:

```python
log_file = os.path.join(experiment_dir, 'logs', 'experiment.log')
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        print("Experiment log:")
        print(f.read())
```

### 2. Use Minimal Examples

Start with the simplest possible configuration and gradually add complexity:

```python
# Minimal working example
from flee_dual_process import *

# Simplest topology
topology_gen = LinearTopologyGenerator({'output_dir': 'debug'})
locations, routes = topology_gen.generate_linear(2, 50.0, 1000, 0.8)

# Simplest scenario
scenario_gen = SpikeConflictGenerator(locations)
conflicts = scenario_gen.generate_spike_conflict('Origin', 0, 0.5)

# Simplest config
config_manager = ConfigurationManager()
config = config_manager.create_cognitive_config('s1_only')

# Simplest experiment
runner = ExperimentRunner(max_parallel=1)
result = runner.run_single_experiment({
    'experiment_id': 'minimal_test',
    'topology_files': (locations, routes),
    'conflicts_file': conflicts,
    'config': config,
    'simulation_days': 5
})

print(f"Minimal test result: {result['status']}")
```

### 3. Community Resources

- Check the Flee project documentation for core simulation issues
- Review example scripts in `flee_dual_process/examples/`
- Look for similar issues in project issue trackers
- Consult the dual-process theory literature for parameter guidance

### 4. Reporting Issues

When reporting issues, include:

1. **Complete Error Message**: Full traceback and error details
2. **Configuration**: Complete experiment configuration
3. **Environment**: Python version, package versions, operating system
4. **Minimal Example**: Smallest code that reproduces the issue
5. **Log Files**: Relevant log file contents

```python
# Generate diagnostic information
import sys
import platform

print("Diagnostic Information:")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Working directory: {os.getcwd()}")

# Package versions
try:
    import numpy, pandas, matplotlib, scipy
    print(f"NumPy: {numpy.__version__}")
    print(f"Pandas: {pandas.__version__}")
    print(f"Matplotlib: {matplotlib.__version__}")
    print(f"SciPy: {scipy.__version__}")
except ImportError as e:
    print(f"Package import error: {e}")
```

## Summary

Most issues can be resolved by:

1. **Checking Prerequisites**: Ensure all packages are installed correctly
2. **Validating Inputs**: Verify all parameters are within valid ranges
3. **Starting Simple**: Begin with minimal examples before complex experiments
4. **Reading Logs**: Check log files for detailed error information
5. **Managing Resources**: Monitor system resources and adjust parallelism
6. **Following Examples**: Use provided examples as templates

Remember that the framework is designed to be robust, but complex experiments with many parameters can encounter various issues. Systematic debugging and validation at each step will help identify and resolve problems quickly.