# Dual Process Experiments Framework - Deployment Guide

This guide provides comprehensive instructions for deploying and using the Dual Process Experiments Framework for Flee refugee movement simulations.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Quick Start](#quick-start)
5. [Production Deployment](#production-deployment)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

## System Requirements

### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: 3.8 or higher
- **Memory**: 4 GB RAM
- **Storage**: 2 GB free space
- **CPU**: 2 cores (4+ recommended for parallel execution)

### Recommended Requirements
- **Operating System**: Linux (Ubuntu 20.04+ or CentOS 8+)
- **Python**: 3.9 or 3.10
- **Memory**: 16 GB RAM
- **Storage**: 10 GB free space (SSD recommended)
- **CPU**: 8+ cores for optimal parallel performance

### Dependencies

#### Core Dependencies
```
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
seaborn>=0.11.0
pyyaml>=5.4.0
networkx>=2.6.0
```

#### Optional Dependencies
```
plotly>=5.0.0          # Interactive visualizations
psutil>=5.8.0          # System monitoring
jupyter>=1.0.0         # Notebook interface
pytest>=6.2.0         # Testing framework
```

## Installation

### Option 1: Standard Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd flee
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_dev.txt  # For development
   ```

3. **Install the Flee package**:
   ```bash
   python setup.py install
   ```

4. **Verify installation**:
   ```bash
   python -c "from flee_dual_process import topology_generator; print('Installation successful')"
   ```

### Option 2: Development Installation

1. **Clone and setup development environment**:
   ```bash
   git clone <repository-url>
   cd flee
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   pip install -r requirements_dev.txt
   ```

2. **Run tests to verify setup**:
   ```bash
   python -m pytest flee_dual_process/test_integration_simple.py -v
   ```

### Option 3: Docker Installation

1. **Build Docker image**:
   ```bash
   docker build -t flee-dual-process .
   ```

2. **Run container**:
   ```bash
   docker run -it -v $(pwd)/results:/app/results flee-dual-process
   ```

## Configuration

### Basic Configuration

The framework uses YAML configuration files for experiment setup. Default templates are provided in `flee_dual_process/configs/production_templates.yml`.

#### Cognitive Mode Configuration

```python
from flee_dual_process.config_manager import ConfigurationManager

config_manager = ConfigurationManager()

# Create configuration for different cognitive modes
s1_config = config_manager.create_cognitive_config('s1_only')
s2_config = config_manager.create_cognitive_config('s2_full')
dual_config = config_manager.create_cognitive_config('dual_process')
```

#### Topology Configuration

```python
from flee_dual_process.topology_generator import LinearTopologyGenerator

# Configure topology generation
base_config = {'output_dir': './experiment_data'}
topology_generator = LinearTopologyGenerator(base_config)

# Generate linear topology
locations_file, routes_file = topology_generator.generate_linear(
    n_nodes=10,
    segment_distance=75.0,
    start_pop=2000,
    pop_decay=0.7
)
```

### Advanced Configuration

#### Custom Parameter Sweeps

```python
from flee_dual_process.experiment_runner import ExperimentRunner

# Configure parameter sweep
sweep_config = {
    'parameter': 'conflict_threshold',
    'values': [0.3, 0.5, 0.7, 0.9],
    'base_experiment': {
        'topology_type': 'linear',
        'scenario_type': 'gradual',
        'cognitive_mode': 'dual_process'
    }
}

experiment_runner = ExperimentRunner(max_parallel=4)
results = experiment_runner.run_parameter_sweep(sweep_config)
```

## Quick Start

### Running Your First Experiment

```python
#!/usr/bin/env python3
"""
Quick start example for dual process experiments.
"""

from flee_dual_process.topology_generator import LinearTopologyGenerator
from flee_dual_process.scenario_generator import SpikeConflictGenerator
from flee_dual_process.config_manager import ConfigurationManager, ExperimentConfig
from flee_dual_process.experiment_runner import ExperimentRunner
from flee_dual_process.analysis_pipeline import AnalysisPipeline

# 1. Setup
base_config = {'output_dir': './my_experiment'}
config_manager = ConfigurationManager()

# 2. Generate topology
topology_generator = LinearTopologyGenerator(base_config)
locations_file, routes_file = topology_generator.generate_linear(
    n_nodes=5,
    segment_distance=50.0,
    start_pop=1000,
    pop_decay=0.8
)

# 3. Generate scenario
scenario_generator = SpikeConflictGenerator(locations_file)
conflicts_file = scenario_generator.generate_spike_conflict(
    origin='Origin',
    start_day=5,
    peak_intensity=0.8,
    output_dir='./my_experiment'
)

# 4. Create experiment configuration
config = config_manager.create_cognitive_config('dual_process')
experiment_config = ExperimentConfig(
    experiment_id='my_first_experiment',
    topology_type='linear',
    topology_params={'n_nodes': 5, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
    scenario_type='spike',
    scenario_params={'origin': 'Origin', 'start_day': 5, 'peak_intensity': 0.8},
    cognitive_mode='dual_process',
    simulation_params=config,
    replications=1
)

# 5. Run experiment
experiment_runner = ExperimentRunner(max_parallel=1)
result = experiment_runner.run_single_experiment(experiment_config.to_dict())

if result['success']:
    print(f"Experiment completed successfully!")
    print(f"Results saved to: {result['experiment_dir']}")
    
    # 6. Analyze results
    analysis_pipeline = AnalysisPipeline()
    analysis_results = analysis_pipeline.process_experiment(result['experiment_dir'])
    
    print(f"Analysis completed. Metrics: {list(analysis_results.metrics.keys())}")
else:
    print(f"Experiment failed: {result.get('error', 'Unknown error')}")
```

### Running Parameter Sweeps

```python
#!/usr/bin/env python3
"""
Parameter sweep example.
"""

from flee_dual_process.experiment_runner import ExperimentRunner
from flee_dual_process.config_manager import ConfigurationManager

# Setup parameter sweep
config_manager = ConfigurationManager()
experiment_runner = ExperimentRunner(max_parallel=4)

# Define base experiment
base_experiment = {
    'topology_type': 'linear',
    'topology_params': {'n_nodes': 8, 'segment_distance': 75.0, 'start_pop': 2000, 'pop_decay': 0.7},
    'scenario_type': 'gradual',
    'scenario_params': {'origin': 'Origin', 'start_day': 0, 'end_day': 20, 'max_intensity': 0.8},
    'cognitive_mode': 'dual_process',
    'replications': 3
}

# Run threshold sensitivity sweep
threshold_values = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
sweep_results = []

for threshold in threshold_values:
    experiment = base_experiment.copy()
    experiment['experiment_id'] = f'threshold_sweep_{threshold}'
    
    # Modify configuration
    config = config_manager.create_cognitive_config('dual_process')
    config['conflict_threshold'] = threshold
    experiment['simulation_params'] = config
    
    result = experiment_runner.run_single_experiment(experiment)
    sweep_results.append(result)

print(f"Parameter sweep completed: {len(sweep_results)} experiments")
```

## Production Deployment

### High-Performance Setup

#### 1. System Optimization

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize Python for performance
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Set optimal number of workers
export FLEE_MAX_WORKERS=$(nproc)
```

#### 2. Cluster Deployment

For large-scale experiments, deploy on a compute cluster:

```bash
# Example SLURM job script
#!/bin/bash
#SBATCH --job-name=flee-dual-process
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=8
#SBATCH --time=24:00:00
#SBATCH --mem=32G

module load python/3.9
source venv/bin/activate

python run_large_scale_experiments.py \
    --config production_config.yml \
    --output-dir $SCRATCH/flee_results \
    --max-parallel 32
```

#### 3. Monitoring and Logging

```python
import logging
from flee_dual_process.utils import setup_logging

# Configure comprehensive logging
setup_logging(
    level=logging.INFO,
    log_file='flee_experiments.log',
    include_performance_metrics=True
)
```

### Database Integration

For large-scale studies, integrate with databases:

```python
from flee_dual_process.database import ExperimentDatabase

# Setup database connection
db = ExperimentDatabase(
    host='localhost',
    database='flee_experiments',
    user='flee_user',
    password='secure_password'
)

# Store experiment results
db.store_experiment_results(experiment_id, results)

# Query historical data
historical_results = db.query_experiments(
    cognitive_mode='dual_process',
    date_range=('2024-01-01', '2024-12-31')
)
```

## Performance Optimization

### Memory Optimization

```python
# Configure memory-efficient processing
from flee_dual_process.config_manager import ConfigurationManager

config = ConfigurationManager()
config.set_memory_optimization({
    'chunk_size': 10000,
    'cache_size': 50,
    'gc_frequency': 5
})
```

### CPU Optimization

```python
# Optimize for multi-core systems
from flee_dual_process.experiment_runner import ExperimentRunner

experiment_runner = ExperimentRunner(
    max_parallel='auto',  # Auto-detect cores
    worker_timeout=300,
    batch_size=10
)
```

### I/O Optimization

```python
# Enable I/O optimizations
config = {
    'io_optimization': {
        'buffer_size': 16384,
        'compression': True,
        'async_writes': True
    }
}
```

## Troubleshooting

### Common Issues

#### 1. Memory Errors
```
Error: MemoryError during experiment execution
```

**Solution**:
- Reduce `max_parallel` workers
- Increase system memory
- Enable memory optimization settings

#### 2. Timeout Errors
```
Error: Experiment timeout after 300 seconds
```

**Solution**:
- Increase timeout in experiment runner
- Optimize Flee executable performance
- Reduce experiment complexity

#### 3. File Permission Errors
```
Error: Permission denied writing to output directory
```

**Solution**:
```bash
chmod -R 755 experiment_output/
chown -R $USER:$USER experiment_output/
```

#### 4. Import Errors
```
Error: ModuleNotFoundError: No module named 'flee_dual_process'
```

**Solution**:
```bash
# Ensure proper installation
pip install -e .
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Performance Issues

#### Slow Experiment Execution

1. **Profile the code**:
   ```python
   import cProfile
   cProfile.run('experiment_runner.run_single_experiment(config)')
   ```

2. **Check system resources**:
   ```bash
   htop  # Monitor CPU and memory usage
   iotop # Monitor I/O usage
   ```

3. **Optimize configuration**:
   - Reduce simulation duration
   - Simplify topology
   - Use faster mock executables for testing

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run experiment with detailed logging
result = experiment_runner.run_single_experiment(config)
```

#### Validate Experiment Setup

```python
from flee_dual_process.validation_framework import ExperimentValidator

validator = ExperimentValidator()
validation_result = validator.validate_experiment_config(config)

if not validation_result.is_valid:
    print("Validation errors:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

## API Reference

### Core Classes

#### ConfigurationManager
```python
class ConfigurationManager:
    def create_cognitive_config(self, mode: str) -> Dict[str, Any]
    def create_simsetting_yml(self, config: Dict, output_path: str)
    def validate_configuration(self, config: Dict) -> bool
```

#### ExperimentRunner
```python
class ExperimentRunner:
    def __init__(self, max_parallel: int = 4, base_output_dir: str = './results')
    def run_single_experiment(self, config: Dict) -> Dict[str, Any]
    def run_parameter_sweep(self, sweep_config: Dict) -> List[Dict]
```

#### AnalysisPipeline
```python
class AnalysisPipeline:
    def __init__(self, results_directory: str, output_directory: str)
    def process_experiment(self, experiment_dir: str) -> ExperimentResults
    def compare_experiments(self, experiment_dirs: List[str]) -> Dict
```

### Topology Generators

#### LinearTopologyGenerator
```python
def generate_linear(self, n_nodes: int, segment_distance: float, 
                   start_pop: int, pop_decay: float) -> Tuple[str, str]
```

#### StarTopologyGenerator
```python
def generate_star(self, n_camps: int, hub_pop: int, 
                 camp_capacity: int, radius: float) -> Tuple[str, str]
```

### Scenario Generators

#### SpikeConflictGenerator
```python
def generate_spike_conflict(self, origin: str, start_day: int, 
                           peak_intensity: float, output_dir: str) -> str
```

#### GradualConflictGenerator
```python
def generate_gradual_conflict(self, origin: str, start_day: int, end_day: int,
                             max_intensity: float, output_dir: str) -> str
```

## Support and Contributing

### Getting Help

1. **Documentation**: Check the comprehensive documentation in `docs/`
2. **Examples**: Review example scripts in `examples/`
3. **Issues**: Report bugs and request features on the project repository
4. **Community**: Join the Flee user community for discussions

### Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make changes and add tests**
4. **Run the test suite**: `python -m pytest`
5. **Submit a pull request**

### Development Setup

```bash
# Clone and setup development environment
git clone <repository-url>
cd flee
python -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements_dev.txt

# Run tests
python -m pytest flee_dual_process/ -v

# Run linting
make lint

# Generate documentation
make docs
```

---

For more detailed information, please refer to the comprehensive documentation in the `docs/` directory or visit the project website.