# Getting Started with Flee Dual Process Experiments

This tutorial will guide you through setting up and running your first dual-process experiment using the Flee Dual Process framework.

## Prerequisites

Before starting, ensure you have:

- Python 3.8 or higher
- The Flee simulation framework installed
- Required Python packages: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `pyyaml`

```bash
# Install required packages
pip install numpy pandas matplotlib seaborn scipy pyyaml

# Optional: Install plotly for interactive visualizations
pip install plotly
```

## Framework Overview

The Flee Dual Process framework consists of several key components:

1. **Topology Generators**: Create network structures (linear, star, tree, grid)
2. **Scenario Generators**: Generate conflict patterns (spike, gradual, cascading, oscillating)
3. **Configuration Manager**: Handle cognitive mode settings and parameter sweeps
4. **Experiment Runner**: Execute experiments with parallel processing
5. **Analysis Pipeline**: Process results and calculate metrics
6. **Visualization Generator**: Create plots and reports

## Your First Experiment

Let's create a simple experiment to compare System 1 vs System 2 decision-making in a linear topology with a spike conflict.

### Step 1: Import Required Modules

```python
import os
from flee_dual_process import (
    LinearTopologyGenerator,
    SpikeConflictGenerator,
    ConfigurationManager,
    ExperimentRunner,
    AnalysisPipeline,
    VisualizationGenerator
)
```

### Step 2: Generate Network Topology

Create a linear chain of 5 locations:

```python
# Initialize topology generator
topology_gen = LinearTopologyGenerator({
    'output_dir': 'experiments/tutorial/topologies'
})

# Generate linear topology
locations_file, routes_file = topology_gen.generate_linear(
    n_nodes=5,           # 5 locations in chain
    segment_distance=50.0,  # 50km between locations
    start_pop=10000,     # 10,000 people at origin
    pop_decay=0.8        # Population decreases by 20% each step
)

print(f"Generated topology:")
print(f"  Locations: {locations_file}")
print(f"  Routes: {routes_file}")
```

### Step 3: Generate Conflict Scenario

Create a spike conflict that starts immediately:

```python
# Initialize scenario generator
scenario_gen = SpikeConflictGenerator(locations_file)

# Generate spike conflict
conflicts_file = scenario_gen.generate_spike_conflict(
    origin='Origin',        # Conflict starts at origin
    start_day=0,           # Starts on day 0
    peak_intensity=0.9,    # High intensity (0.9 out of 1.0)
    output_dir='experiments/tutorial/scenarios'
)

print(f"Generated conflict scenario: {conflicts_file}")
```

### Step 4: Create Cognitive Mode Configurations

Compare System 1 (fast, intuitive) vs System 2 (slow, deliberate) decision-making:

```python
# Initialize configuration manager
config_manager = ConfigurationManager()

# Create System 1 configuration
s1_config = config_manager.create_cognitive_config('s1_only')

# Create System 2 configuration  
s2_config = config_manager.create_cognitive_config('s2_full')

print("Created cognitive mode configurations:")
print(f"  System 1: {s1_config['move_rules']['two_system_decision_making']}")
print(f"  System 2: {s2_config['move_rules']['two_system_decision_making']}")
```

### Step 5: Run Experiments

Execute both experiments:

```python
# Initialize experiment runner
runner = ExperimentRunner(
    max_parallel=2,  # Run 2 experiments in parallel
    base_output_dir='experiments/tutorial/results'
)

# Define base experiment configuration
base_experiment = {
    'topology_files': (locations_file, routes_file),
    'conflicts_file': conflicts_file,
    'simulation_days': 100
}

# Run System 1 experiment
s1_experiment = base_experiment.copy()
s1_experiment.update({
    'experiment_id': 'tutorial_s1_only',
    'config': s1_config
})

s1_results = runner.run_single_experiment(s1_experiment)

# Run System 2 experiment
s2_experiment = base_experiment.copy()
s2_experiment.update({
    'experiment_id': 'tutorial_s2_full',
    'config': s2_config
})

s2_results = runner.run_single_experiment(s2_experiment)

# Check results
for results in [s1_results, s2_results]:
    if results['status'] == 'completed':
        print(f"✓ {results['experiment_id']} completed in {results['execution_time']:.1f}s")
    else:
        print(f"✗ {results['experiment_id']} failed: {results.get('error', 'Unknown error')}")
```

### Step 6: Analyze Results

Compare the movement patterns between cognitive modes:

```python
# Initialize analysis pipeline
analyzer = AnalysisPipeline('experiments/tutorial/results')

# Load experiment data
s1_data = analyzer.load_experiment_data(s1_results['output_dir'])
s2_data = analyzer.load_experiment_data(s2_results['output_dir'])

# Calculate movement metrics
s1_metrics = analyzer.calculate_movement_metrics(s1_results['output_dir'])
s2_metrics = analyzer.calculate_movement_metrics(s2_results['output_dir'])

# Compare key metrics
print("\nMovement Metrics Comparison:")
print(f"System 1 - Average first move day: {s1_metrics['first_move_day']['mean']:.1f}")
print(f"System 2 - Average first move day: {s2_metrics['first_move_day']['mean']:.1f}")

print(f"System 1 - Total distance traveled: {s1_metrics['total_distance']['mean']:.1f} km")
print(f"System 2 - Total distance traveled: {s2_metrics['total_distance']['mean']:.1f} km")
```

### Step 7: Create Visualizations

Generate plots to visualize the differences:

```python
# Initialize visualization generator
viz_gen = VisualizationGenerator(
    results_directory='experiments/tutorial/results',
    backend='matplotlib'
)

# Create movement comparison plots
comparison_data = {
    'System 1': s1_data,
    'System 2': s2_data
}

# Generate movement timing comparison
timing_plot = viz_gen.create_movement_timing_comparison(
    comparison_data,
    output_file='experiments/tutorial/plots/movement_timing.png'
)

# Generate destination distribution plot
destination_plot = viz_gen.create_destination_distribution_plot(
    comparison_data,
    output_file='experiments/tutorial/plots/destinations.png'
)

print(f"\nGenerated visualizations:")
print(f"  Movement timing: {timing_plot}")
print(f"  Destinations: {destination_plot}")
```

## Understanding the Results

### Expected Differences

**System 1 (Fast, Intuitive)**:
- Faster initial response to conflict
- More direct movement patterns
- Less consideration of camp capacities
- Higher variability in decisions

**System 2 (Slow, Deliberate)**:
- Slower initial response (more planning time)
- More efficient route selection
- Better consideration of camp capacities
- More consistent decision-making

### Key Metrics to Examine

1. **First Move Day**: How quickly agents respond to conflict
2. **Total Distance**: Efficiency of route selection
3. **Destination Distribution**: How agents distribute across camps
4. **Movement Timing**: When peak movements occur

## Next Steps

Now that you've run your first experiment, try these variations:

### 1. Test Different Topologies

```python
# Try a star topology
from flee_dual_process import StarTopologyGenerator

star_gen = StarTopologyGenerator({'output_dir': 'topologies'})
star_locations, star_routes = star_gen.generate_star(
    n_camps=4,
    hub_pop=15000,
    camp_capacity=5000,
    radius=60.0
)
```

### 2. Test Different Conflict Scenarios

```python
# Try a gradual conflict
from flee_dual_process import GradualConflictGenerator

gradual_gen = GradualConflictGenerator(locations_file)
gradual_conflicts = gradual_gen.generate_gradual_conflict(
    origin='Origin',
    start_day=0,
    end_day=30,
    max_intensity=0.8
)
```

### 3. Run Parameter Sweeps

```python
# Test different awareness levels
awareness_configs = config_manager.generate_parameter_sweep(
    base_config=s2_config,
    parameter='move_rules.awareness_level',
    values=[1, 2, 3]
)

# Run parameter sweep
sweep_config = {
    'base_experiment': base_experiment,
    'parameter_configs': awareness_configs,
    'sweep_id': 'awareness_sweep'
}

sweep_results = runner.run_parameter_sweep(sweep_config)
```

### 4. Compare All Cognitive Modes

```python
# Test all four cognitive modes
modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
mode_configs = [config_manager.create_cognitive_config(mode) for mode in modes]

# Run comparison experiments
mode_results = []
for i, (mode, config) in enumerate(zip(modes, mode_configs)):
    experiment = base_experiment.copy()
    experiment.update({
        'experiment_id': f'mode_comparison_{mode}',
        'config': config
    })
    result = runner.run_single_experiment(experiment)
    mode_results.append(result)
```

## Troubleshooting

### Common Issues

**1. Import Errors**
```python
# If you get import errors, check your Python path
import sys
sys.path.append('/path/to/flee/directory')
```

**2. File Not Found Errors**
```python
# Ensure output directories exist
import os
os.makedirs('experiments/tutorial', exist_ok=True)
```

**3. Experiment Failures**
```python
# Check experiment logs for detailed error information
if results['status'] == 'failed':
    log_file = os.path.join(results['output_dir'], 'logs', 'experiment.log')
    with open(log_file, 'r') as f:
        print(f.read())
```

**4. Memory Issues**
```python
# Reduce parallelism for large experiments
runner = ExperimentRunner(max_parallel=1)
```

### Getting Help

- Check the API documentation for detailed parameter descriptions
- Look at the example scripts in `flee_dual_process/examples/`
- Review the troubleshooting guide for common issues
- Check experiment logs for detailed error messages

## Summary

You've successfully:

1. ✓ Generated a network topology
2. ✓ Created a conflict scenario  
3. ✓ Configured cognitive modes
4. ✓ Run comparative experiments
5. ✓ Analyzed the results
6. ✓ Created visualizations

This basic workflow can be extended to test more complex hypotheses about dual-process decision-making in refugee movement scenarios. The framework provides the tools to systematically explore how cognitive modes, network structures, and conflict patterns interact to influence movement behaviors.