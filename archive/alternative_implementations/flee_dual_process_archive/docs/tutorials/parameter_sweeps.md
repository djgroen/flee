# Parameter Sweeps and Sensitivity Analysis

This tutorial demonstrates how to conduct systematic parameter sweeps to understand the sensitivity of dual-process decision-making to key parameters.

## Overview

Parameter sweeps allow you to:
- Test sensitivity to individual parameters
- Explore parameter interactions
- Identify critical thresholds
- Validate model robustness
- Generate data for statistical analysis

## Types of Parameter Sweeps

### 1. Single Parameter Sweeps

Test how one parameter affects outcomes while keeping others constant.

```python
from flee_dual_process import ConfigurationManager, ExperimentRunner

# Initialize components
config_manager = ConfigurationManager()
runner = ExperimentRunner(max_parallel=4)

# Create base configuration
base_config = config_manager.create_cognitive_config('dual_process')

# Test different awareness levels
awareness_sweep = config_manager.generate_parameter_sweep(
    base_config=base_config,
    parameter='move_rules.awareness_level',
    values=[1, 2, 3]
)

print(f"Generated {len(awareness_sweep)} configurations for awareness sweep")
```

### 2. Multi-Parameter Sweeps

Test interactions between multiple parameters using factorial designs.

```python
# Test awareness level × social connectivity interaction
factorial_sweep = config_manager.generate_factorial_design(
    base_config=base_config,
    factors={
        'move_rules.awareness_level': [1, 2, 3],
        'move_rules.average_social_connectivity': [0.0, 3.0, 6.0, 9.0]
    }
)

print(f"Generated {len(factorial_sweep)} configurations for factorial design")
# This creates 3 × 4 = 12 configurations
```

### 3. Cognitive Mode Comparison

Compare all cognitive modes systematically.

```python
# Generate configurations for all cognitive modes
mode_sweep = config_manager.generate_cognitive_mode_sweep()

print("Cognitive modes included:")
for i, config in enumerate(mode_sweep):
    mode_name = ['s1_only', 's2_disconnected', 's2_full', 'dual_process'][i]
    print(f"  {mode_name}: two_system = {config['move_rules']['two_system_decision_making']}")
```

## Comprehensive Parameter Sweep Example

Let's conduct a comprehensive sensitivity analysis for the dual-process model:

### Step 1: Define Parameter Ranges

```python
# Define parameters to test and their ranges
parameter_ranges = {
    # Core dual-process parameters
    'move_rules.conflict_threshold': [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    'move_rules.recovery_period_max': [7, 14, 21, 30, 45, 60],
    'move_rules.average_social_connectivity': [0.0, 1.0, 2.0, 4.0, 6.0, 8.0],
    'move_rules.awareness_level': [1, 2, 3],
    
    # Movement behavior parameters
    'move_rules.weight_softening': [0.1, 0.3, 0.5, 0.7, 0.9],
    'move_rules.conflict_movechance': [0.5, 0.7, 0.9, 1.0],
    'move_rules.default_movechance': [0.1, 0.2, 0.3, 0.4, 0.5]
}

print("Parameter ranges defined:")
for param, values in parameter_ranges.items():
    print(f"  {param}: {len(values)} values")
```

### Step 2: Generate Single Parameter Sweeps

```python
# Generate individual parameter sweeps
single_param_sweeps = {}

for parameter, values in parameter_ranges.items():
    sweep_configs = config_manager.generate_parameter_sweep(
        base_config=base_config,
        parameter=parameter,
        values=values
    )
    single_param_sweeps[parameter] = sweep_configs
    print(f"Generated {len(sweep_configs)} configs for {parameter}")
```

### Step 3: Set Up Base Experiment

```python
from flee_dual_process import LinearTopologyGenerator, SpikeConflictGenerator

# Generate topology and scenario (reuse for all experiments)
topology_gen = LinearTopologyGenerator({'output_dir': 'sweeps/topology'})
locations_file, routes_file = topology_gen.generate_linear(
    n_nodes=6, segment_distance=40.0, start_pop=12000, pop_decay=0.75
)

scenario_gen = SpikeConflictGenerator(locations_file)
conflicts_file = scenario_gen.generate_spike_conflict(
    origin='Origin', start_day=0, peak_intensity=0.85,
    output_dir='sweeps/scenarios'
)

# Base experiment configuration
base_experiment = {
    'topology_files': (locations_file, routes_file),
    'conflicts_file': conflicts_file,
    'simulation_days': 120
}
```

### Step 4: Execute Parameter Sweeps

```python
import time

# Execute each parameter sweep
sweep_results = {}

for parameter, configs in single_param_sweeps.items():
    print(f"\nRunning sweep for {parameter}...")
    start_time = time.time()
    
    # Create sweep configuration
    sweep_config = {
        'base_experiment': base_experiment,
        'parameter_configs': configs,
        'sweep_id': f'sweep_{parameter.replace(".", "_")}'
    }
    
    # Run parameter sweep
    results = runner.run_parameter_sweep(sweep_config)
    
    # Store results
    sweep_results[parameter] = results
    
    # Report progress
    completed = len([r for r in results if r['status'] == 'completed'])
    failed = len([r for r in results if r['status'] == 'failed'])
    duration = time.time() - start_time
    
    print(f"  Completed: {completed}/{len(results)} ({100*completed/len(results):.1f}%)")
    print(f"  Failed: {failed}")
    print(f"  Duration: {duration:.1f} seconds")
```

### Step 5: Analyze Sensitivity

```python
from flee_dual_process import AnalysisPipeline
import pandas as pd
import numpy as np

# Initialize analysis pipeline
analyzer = AnalysisPipeline('sweeps/results')

# Analyze sensitivity for each parameter
sensitivity_results = {}

for parameter, results in sweep_results.items():
    print(f"\nAnalyzing sensitivity for {parameter}:")
    
    # Extract successful experiments
    successful_results = [r for r in results if r['status'] == 'completed']
    
    if len(successful_results) < 2:
        print(f"  Insufficient successful experiments ({len(successful_results)})")
        continue
    
    # Calculate metrics for each experiment
    experiment_metrics = []
    parameter_values = []
    
    for result in successful_results:
        # Load experiment data
        exp_data = analyzer.load_experiment_data(result['output_dir'])
        
        # Calculate movement metrics
        metrics = analyzer.calculate_movement_metrics(result['output_dir'])
        
        # Extract parameter value from configuration
        param_parts = parameter.split('.')
        param_value = result['metadata']['config']
        for part in param_parts:
            param_value = param_value[part]
        
        experiment_metrics.append(metrics)
        parameter_values.append(param_value)
    
    # Analyze sensitivity
    sensitivity_analysis = analyze_parameter_sensitivity(
        parameter_values, experiment_metrics, parameter
    )
    
    sensitivity_results[parameter] = sensitivity_analysis
    
    # Print key findings
    print(f"  Correlation with first move day: {sensitivity_analysis['first_move_correlation']:.3f}")
    print(f"  Correlation with total distance: {sensitivity_analysis['distance_correlation']:.3f}")
    print(f"  Effect size: {sensitivity_analysis['effect_size']:.3f}")
```

### Step 6: Create Sensitivity Analysis Function

```python
from scipy.stats import pearsonr, spearmanr
from scipy import stats

def analyze_parameter_sensitivity(param_values, metrics_list, parameter_name):
    """Analyze sensitivity of outcomes to parameter changes."""
    
    # Extract key metrics
    first_move_days = [m['first_move_day']['mean'] for m in metrics_list]
    total_distances = [m['total_distance']['mean'] for m in metrics_list]
    destination_entropy = [m['destination_distribution']['entropy'] for m in metrics_list]
    
    # Calculate correlations
    first_move_corr, first_move_p = pearsonr(param_values, first_move_days)
    distance_corr, distance_p = pearsonr(param_values, total_distances)
    entropy_corr, entropy_p = pearsonr(param_values, destination_entropy)
    
    # Calculate effect sizes (Cohen's d for extreme values)
    if len(param_values) >= 4:
        low_quartile = np.percentile(param_values, 25)
        high_quartile = np.percentile(param_values, 75)
        
        low_indices = [i for i, v in enumerate(param_values) if v <= low_quartile]
        high_indices = [i for i, v in enumerate(param_values) if v >= high_quartile]
        
        if low_indices and high_indices:
            low_moves = [first_move_days[i] for i in low_indices]
            high_moves = [first_move_days[i] for i in high_indices]
            
            # Cohen's d
            pooled_std = np.sqrt(((len(low_moves)-1)*np.var(low_moves) + 
                                 (len(high_moves)-1)*np.var(high_moves)) / 
                                (len(low_moves) + len(high_moves) - 2))
            effect_size = (np.mean(high_moves) - np.mean(low_moves)) / pooled_std
        else:
            effect_size = 0.0
    else:
        effect_size = 0.0
    
    return {
        'parameter': parameter_name,
        'first_move_correlation': first_move_corr,
        'first_move_p_value': first_move_p,
        'distance_correlation': distance_corr,
        'distance_p_value': distance_p,
        'entropy_correlation': entropy_corr,
        'entropy_p_value': entropy_p,
        'effect_size': effect_size,
        'n_experiments': len(param_values)
    }
```

## Advanced Parameter Sweep Techniques

### 1. Latin Hypercube Sampling

For high-dimensional parameter spaces, use Latin Hypercube Sampling:

```python
from scipy.stats import qmc
import numpy as np

def generate_lhs_sweep(parameter_ranges, n_samples=50):
    """Generate Latin Hypercube Sample for parameter sweep."""
    
    # Get parameter names and bounds
    param_names = list(parameter_ranges.keys())
    param_bounds = [parameter_ranges[name] for name in param_names]
    
    # Create sampler
    sampler = qmc.LatinHypercube(d=len(param_names))
    
    # Generate samples
    samples = sampler.random(n=n_samples)
    
    # Scale samples to parameter ranges
    configs = []
    for sample in samples:
        config = config_manager.create_cognitive_config('dual_process')
        
        for i, (param_name, bounds) in enumerate(zip(param_names, param_bounds)):
            # Scale sample to parameter range
            if isinstance(bounds[0], int):
                # Integer parameter
                value = int(bounds[0] + sample[i] * (bounds[-1] - bounds[0]))
            else:
                # Float parameter
                value = bounds[0] + sample[i] * (bounds[-1] - bounds[0])
            
            # Set parameter value
            param_parts = param_name.split('.')
            current = config
            for part in param_parts[:-1]:
                current = current[part]
            current[param_parts[-1]] = value
        
        configs.append(config)
    
    return configs

# Generate LHS sweep
lhs_configs = generate_lhs_sweep(parameter_ranges, n_samples=100)
print(f"Generated {len(lhs_configs)} LHS configurations")
```

### 2. Adaptive Parameter Sweeps

Focus computational resources on interesting parameter regions:

```python
def adaptive_parameter_sweep(base_config, parameter, initial_values, 
                           refinement_criterion='variance', max_iterations=3):
    """Adaptively refine parameter sweep based on results."""
    
    current_values = initial_values
    all_results = []
    
    for iteration in range(max_iterations):
        print(f"Iteration {iteration + 1}: Testing {len(current_values)} values")
        
        # Generate configurations
        configs = config_manager.generate_parameter_sweep(
            base_config=base_config,
            parameter=parameter,
            values=current_values
        )
        
        # Run experiments
        sweep_config = {
            'base_experiment': base_experiment,
            'parameter_configs': configs,
            'sweep_id': f'adaptive_{parameter}_{iteration}'
        }
        
        results = runner.run_parameter_sweep(sweep_config)
        all_results.extend(results)
        
        # Analyze results to identify regions of interest
        if iteration < max_iterations - 1:
            current_values = identify_refinement_regions(
                results, parameter, refinement_criterion
            )
    
    return all_results

def identify_refinement_regions(results, parameter, criterion='variance'):
    """Identify parameter regions that need more detailed exploration."""
    
    # Extract parameter values and metrics
    successful_results = [r for r in results if r['status'] == 'completed']
    
    param_values = []
    metrics = []
    
    for result in successful_results:
        # Extract parameter value
        param_parts = parameter.split('.')
        param_value = result['metadata']['config']
        for part in param_parts:
            param_value = param_value[part]
        param_values.append(param_value)
        
        # Calculate key metric (e.g., first move day variance)
        exp_metrics = analyzer.calculate_movement_metrics(result['output_dir'])
        metrics.append(exp_metrics['first_move_day']['std'])
    
    # Sort by parameter value
    sorted_pairs = sorted(zip(param_values, metrics))
    sorted_values, sorted_metrics = zip(*sorted_pairs)
    
    # Identify regions with high variance or steep gradients
    refinement_values = []
    
    for i in range(len(sorted_values) - 1):
        # Check for high variance or large changes
        if (sorted_metrics[i] > np.mean(sorted_metrics) or 
            abs(sorted_metrics[i+1] - sorted_metrics[i]) > np.std(sorted_metrics)):
            
            # Add intermediate values for refinement
            v1, v2 = sorted_values[i], sorted_values[i+1]
            if isinstance(v1, int):
                if v2 - v1 > 1:
                    refinement_values.extend(range(v1, v2 + 1))
            else:
                refinement_values.extend([
                    v1 + 0.25 * (v2 - v1),
                    v1 + 0.5 * (v2 - v1),
                    v1 + 0.75 * (v2 - v1)
                ])
    
    return list(set(refinement_values))
```

### 3. Parallel Sweep Execution

Optimize execution for large parameter sweeps:

```python
def execute_large_parameter_sweep(parameter_configs, batch_size=20):
    """Execute large parameter sweeps in batches with progress tracking."""
    
    total_configs = len(parameter_configs)
    all_results = []
    
    # Process in batches
    for batch_start in range(0, total_configs, batch_size):
        batch_end = min(batch_start + batch_size, total_configs)
        batch_configs = parameter_configs[batch_start:batch_end]
        
        print(f"Processing batch {batch_start//batch_size + 1}: "
              f"experiments {batch_start+1}-{batch_end} of {total_configs}")
        
        # Create batch sweep configuration
        batch_sweep_config = {
            'base_experiment': base_experiment,
            'parameter_configs': batch_configs,
            'sweep_id': f'large_sweep_batch_{batch_start//batch_size + 1}'
        }
        
        # Execute batch
        batch_results = runner.run_parameter_sweep(batch_sweep_config)
        all_results.extend(batch_results)
        
        # Progress report
        completed = len([r for r in batch_results if r['status'] == 'completed'])
        print(f"  Batch completed: {completed}/{len(batch_configs)} successful")
        
        # Optional: Clean up intermediate files to save disk space
        cleanup_batch_intermediates(batch_results)
    
    return all_results

def cleanup_batch_intermediates(batch_results):
    """Clean up intermediate files to save disk space."""
    import shutil
    
    for result in batch_results:
        if result['status'] == 'completed':
            # Keep only essential output files
            output_dir = result['output_dir']
            
            # Remove large intermediate files but keep key outputs
            files_to_keep = [
                'out.csv', 'cognitive_states.csv', 'decision_log.csv',
                'metadata.json', 'experiment.log'
            ]
            
            # Implementation depends on specific file structure
            pass
```

## Visualization of Parameter Sensitivity

### 1. Sensitivity Heatmaps

```python
from flee_dual_process import VisualizationGenerator
import matplotlib.pyplot as plt
import seaborn as sns

# Create sensitivity heatmap
def create_sensitivity_heatmap(sensitivity_results):
    """Create heatmap showing parameter sensitivity across metrics."""
    
    # Prepare data for heatmap
    parameters = list(sensitivity_results.keys())
    metrics = ['first_move_correlation', 'distance_correlation', 'entropy_correlation']
    
    heatmap_data = []
    for param in parameters:
        row = [sensitivity_results[param][metric] for metric in metrics]
        heatmap_data.append(row)
    
    # Create heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        heatmap_data,
        xticklabels=['First Move Day', 'Total Distance', 'Destination Entropy'],
        yticklabels=[p.replace('move_rules.', '') for p in parameters],
        annot=True,
        cmap='RdBu_r',
        center=0,
        vmin=-1,
        vmax=1
    )
    plt.title('Parameter Sensitivity Analysis')
    plt.tight_layout()
    plt.savefig('parameter_sensitivity_heatmap.png', dpi=300)
    plt.show()

# Generate heatmap
create_sensitivity_heatmap(sensitivity_results)
```

### 2. Parameter Response Curves

```python
def plot_parameter_response_curves(sweep_results, parameter):
    """Plot response curves showing how metrics change with parameter values."""
    
    results = sweep_results[parameter]
    successful_results = [r for r in results if r['status'] == 'completed']
    
    # Extract data
    param_values = []
    first_move_days = []
    total_distances = []
    
    for result in successful_results:
        # Extract parameter value
        param_parts = parameter.split('.')
        param_value = result['metadata']['config']
        for part in param_parts:
            param_value = param_value[part]
        param_values.append(param_value)
        
        # Calculate metrics
        metrics = analyzer.calculate_movement_metrics(result['output_dir'])
        first_move_days.append(metrics['first_move_day']['mean'])
        total_distances.append(metrics['total_distance']['mean'])
    
    # Create plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # First move day response
    ax1.scatter(param_values, first_move_days, alpha=0.7)
    ax1.set_xlabel(parameter.replace('move_rules.', ''))
    ax1.set_ylabel('Average First Move Day')
    ax1.set_title('First Move Day Response')
    
    # Add trend line
    z = np.polyfit(param_values, first_move_days, 1)
    p = np.poly1d(z)
    ax1.plot(sorted(param_values), p(sorted(param_values)), "r--", alpha=0.8)
    
    # Total distance response
    ax2.scatter(param_values, total_distances, alpha=0.7, color='orange')
    ax2.set_xlabel(parameter.replace('move_rules.', ''))
    ax2.set_ylabel('Average Total Distance (km)')
    ax2.set_title('Total Distance Response')
    
    # Add trend line
    z = np.polyfit(param_values, total_distances, 1)
    p = np.poly1d(z)
    ax2.plot(sorted(param_values), p(sorted(param_values)), "r--", alpha=0.8)
    
    plt.tight_layout()
    plt.savefig(f'{parameter}_response_curves.png', dpi=300)
    plt.show()

# Generate response curves for key parameters
key_parameters = [
    'move_rules.conflict_threshold',
    'move_rules.average_social_connectivity',
    'move_rules.awareness_level'
]

for param in key_parameters:
    if param in sweep_results:
        plot_parameter_response_curves(sweep_results, param)
```

## Best Practices for Parameter Sweeps

### 1. Planning Your Sweep

- **Start Small**: Begin with coarse parameter grids, then refine
- **Focus on Key Parameters**: Prioritize parameters with theoretical importance
- **Consider Interactions**: Test parameter combinations, not just individual effects
- **Plan Resources**: Estimate computational requirements before starting

### 2. Execution Strategy

- **Batch Processing**: Process large sweeps in manageable batches
- **Checkpointing**: Save intermediate results to enable resumption
- **Resource Monitoring**: Monitor system resources during execution
- **Error Handling**: Plan for experiment failures and retries

### 3. Analysis Approach

- **Multiple Metrics**: Analyze multiple outcome measures
- **Statistical Testing**: Use appropriate statistical tests for comparisons
- **Effect Sizes**: Report effect sizes, not just statistical significance
- **Visualization**: Create clear visualizations of parameter effects

### 4. Documentation

- **Parameter Rationale**: Document why specific parameters were chosen
- **Range Justification**: Explain parameter range selections
- **Results Interpretation**: Provide clear interpretation of findings
- **Reproducibility**: Save all configurations and random seeds

## Summary

Parameter sweeps are essential for understanding dual-process model behavior:

1. **Single Parameter Sweeps**: Test individual parameter sensitivity
2. **Factorial Designs**: Explore parameter interactions
3. **Advanced Techniques**: Use LHS sampling and adaptive refinement
4. **Comprehensive Analysis**: Analyze multiple metrics and visualize results
5. **Best Practices**: Plan carefully, execute systematically, analyze thoroughly

This systematic approach enables robust conclusions about dual-process decision-making in refugee movement scenarios.