# Experimental Design Guidelines

This document provides comprehensive guidelines for designing rigorous dual-process experiments using the Flee framework.

## Experimental Design Principles

### 1. Hypothesis-Driven Design

Every experiment should test specific hypotheses about dual-process decision-making:

**Example Hypotheses:**
- H1: System 1 processing leads to faster but less optimal movement decisions
- H2: Social connectivity improves destination selection in System 2 mode
- H3: Conflict intensity determines the activation of System 1 vs System 2 processing
- H4: Network topology moderates the effects of cognitive processing mode

### 2. Controlled Experimental Conditions

Design experiments to isolate specific factors:

```python
# Example: Testing cognitive mode effects while controlling other factors
base_conditions = {
    'topology': 'linear_5_nodes',
    'scenario': 'spike_conflict_0.8',
    'simulation_days': 100,
    'replications': 10
}

cognitive_modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']

for mode in cognitive_modes:
    experiment = base_conditions.copy()
    experiment['cognitive_mode'] = mode
    run_experiment(experiment)
```

### 3. Factorial Experimental Designs

Use factorial designs to test interactions between factors:

```python
# 2x3 factorial design: Cognitive Mode × Conflict Type
cognitive_modes = ['s1_only', 's2_full']
conflict_types = ['spike', 'gradual', 'cascading']

for mode in cognitive_modes:
    for conflict in conflict_types:
        experiment_config = {
            'cognitive_mode': mode,
            'conflict_type': conflict,
            'replications': 15  # Sufficient for statistical power
        }
        run_experiment(experiment_config)
```

## Experimental Variables

### Independent Variables (Factors)

#### 1. Cognitive Mode Configuration
- **s1_only**: Pure System 1 processing
- **s2_disconnected**: System 2 without social connectivity
- **s2_full**: System 2 with full social connectivity
- **dual_process**: Dynamic switching between systems

#### 2. Network Topology
- **Linear**: Chain topology for testing corridor effects
- **Star**: Hub-and-spoke for testing centralization effects
- **Tree**: Hierarchical for testing multi-level decision-making
- **Grid**: Regular network for testing spatial effects

#### 3. Conflict Scenario Type
- **Spike**: Sudden high-intensity conflict (tests System 1 responses)
- **Gradual**: Linear escalation (tests System 2 planning)
- **Cascading**: Network-based spread (tests social effects)
- **Oscillating**: Cyclical variations (tests adaptation)

#### 4. Parameter Values
- **Awareness Level**: 1, 2, 3 (information processing capacity)
- **Social Connectivity**: 0.0, 3.0, 6.0, 9.0 (network effects)
- **Conflict Threshold**: 0.3, 0.5, 0.7 (System 1 activation)
- **Recovery Period**: 7, 21, 45 days (cognitive recovery time)

### Dependent Variables (Outcomes)

#### 1. Movement Timing Metrics
```python
timing_metrics = {
    'first_move_day': 'Speed of initial response to conflict',
    'peak_movement_day': 'Day of maximum movement activity',
    'movement_duration': 'Total time from first to last move',
    'response_variability': 'Individual differences in timing'
}
```

#### 2. Movement Efficiency Metrics
```python
efficiency_metrics = {
    'total_distance': 'Cumulative distance traveled per agent',
    'path_optimality': 'Ratio of actual to optimal path length',
    'destination_accuracy': 'Selection of appropriate destinations',
    'route_directness': 'Straightness of movement paths'
}
```

#### 3. Destination Selection Metrics
```python
destination_metrics = {
    'destination_distribution': 'Spread across available destinations',
    'camp_utilization': 'Efficiency of camp capacity usage',
    'destination_entropy': 'Diversity of destination choices',
    'overcrowding_frequency': 'Instances of capacity violations'
}
```

#### 4. Cognitive State Metrics (Dual Process Mode)
```python
cognitive_metrics = {
    'system1_activation_frequency': 'How often System 1 is activated',
    'system1_duration': 'Average duration of System 1 episodes',
    'recovery_time': 'Time to return to System 2',
    'switching_patterns': 'Temporal patterns of system switching'
}
```

## Sample Size and Power Analysis

### 1. Determining Sample Size

Use power analysis to determine required sample sizes:

```python
from scipy import stats
import numpy as np

def calculate_sample_size(effect_size, alpha=0.05, power=0.8):
    """
    Calculate required sample size for detecting effect.
    
    Args:
        effect_size: Expected Cohen's d
        alpha: Type I error rate
        power: Statistical power (1 - Type II error rate)
    
    Returns:
        Required sample size per group
    """
    # Using t-test approximation
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n))

# Example: Detect medium effect size (d=0.5)
n_required = calculate_sample_size(effect_size=0.5)
print(f"Required sample size per group: {n_required}")
```

### 2. Recommended Sample Sizes

**Minimum Recommendations:**
- **Pilot Studies**: 5-10 replications per condition
- **Main Studies**: 15-30 replications per condition
- **Parameter Sweeps**: 10-20 replications per parameter value
- **Factorial Designs**: 20-50 replications per cell

**Considerations:**
- Increase sample size for smaller expected effects
- Account for potential experiment failures
- Consider computational resources and time constraints

## Randomization and Controls

### 1. Randomization Strategies

**Complete Randomization:**
```python
import random

# Randomize experiment order
experiment_list = generate_all_experiments()
random.shuffle(experiment_list)

for experiment in experiment_list:
    run_experiment(experiment)
```

**Block Randomization:**
```python
# Randomize within blocks to control for time effects
experiments_by_block = group_experiments_by_factor(experiment_list)

for block in experiments_by_block:
    random.shuffle(block)
    for experiment in block:
        run_experiment(experiment)
```

**Stratified Randomization:**
```python
# Ensure balanced allocation across important factors
stratified_experiments = stratify_by_factors(
    experiment_list, 
    factors=['cognitive_mode', 'topology_type']
)

for stratum in stratified_experiments:
    random.shuffle(stratum)
    run_experiments(stratum)
```

### 2. Control Conditions

**Baseline Controls:**
- Include standard Flee simulation (no dual-process) as baseline
- Use identical random seeds across cognitive mode comparisons
- Control for topology and scenario effects

**Negative Controls:**
- Test with minimal parameter differences to verify sensitivity
- Include conditions expected to show no effect

**Positive Controls:**
- Include conditions with known strong effects
- Verify that expected differences are detected

## Replication Strategies

### 1. Technical Replication

Multiple runs with different random seeds:

```python
def run_replicated_experiment(base_config, n_replications=20):
    """Run experiment with multiple random seeds."""
    results = []
    
    for rep in range(n_replications):
        config = base_config.copy()
        config['random_seed'] = rep + 1000  # Ensure unique seeds
        config['replication_id'] = rep
        
        result = run_single_experiment(config)
        results.append(result)
    
    return results
```

### 2. Systematic Replication

Vary non-essential parameters to test generalizability:

```python
def run_systematic_replication(base_config):
    """Test robustness across parameter variations."""
    
    # Vary population sizes
    population_sizes = [5000, 10000, 15000]
    
    # Vary topology sizes
    topology_sizes = [4, 5, 6]  # nodes in linear topology
    
    results = []
    for pop_size in population_sizes:
        for topo_size in topology_sizes:
            config = base_config.copy()
            config['population_size'] = pop_size
            config['topology_nodes'] = topo_size
            
            result = run_replicated_experiment(config, n_replications=10)
            results.extend(result)
    
    return results
```

### 3. Conceptual Replication

Test same hypotheses with different experimental setups:

```python
def run_conceptual_replication():
    """Test same hypothesis with different scenarios."""
    
    # Test System 1 vs System 2 speed hypothesis
    # Replication 1: Spike conflict in linear topology
    # Replication 2: Cascading conflict in star topology
    # Replication 3: Gradual conflict in grid topology
    
    replications = [
        {'topology': 'linear', 'scenario': 'spike'},
        {'topology': 'star', 'scenario': 'cascading'},
        {'topology': 'grid', 'scenario': 'gradual'}
    ]
    
    for rep_config in replications:
        test_speed_hypothesis(rep_config)
```

## Experimental Protocols

### 1. Pre-Experiment Checklist

**System Validation:**
- [ ] Verify Flee installation and dependencies
- [ ] Test framework components with minimal examples
- [ ] Validate topology and scenario generation
- [ ] Check available computational resources

**Experimental Setup:**
- [ ] Define clear hypotheses and predictions
- [ ] Specify all experimental conditions
- [ ] Calculate required sample sizes
- [ ] Prepare randomization scheme
- [ ] Set up output directory structure

**Quality Assurance:**
- [ ] Run pilot experiments to test setup
- [ ] Verify output file formats and contents
- [ ] Test analysis pipeline with pilot data
- [ ] Document all parameter choices and rationale

### 2. Experiment Execution Protocol

**Batch Processing:**
```python
def execute_experiment_batch(experiment_configs, batch_size=10):
    """Execute experiments in manageable batches."""
    
    total_experiments = len(experiment_configs)
    completed = 0
    
    for i in range(0, total_experiments, batch_size):
        batch = experiment_configs[i:i+batch_size]
        
        print(f"Processing batch {i//batch_size + 1}: "
              f"experiments {i+1}-{min(i+batch_size, total_experiments)}")
        
        batch_results = run_experiment_batch(batch)
        
        # Validate batch results
        validate_batch_results(batch_results)
        
        # Save intermediate results
        save_batch_results(batch_results, batch_id=i//batch_size)
        
        completed += len(batch_results)
        print(f"Progress: {completed}/{total_experiments} completed")
```

**Progress Monitoring:**
```python
def monitor_experiment_progress(experiment_id):
    """Monitor long-running experiments."""
    
    while not experiment_completed(experiment_id):
        status = get_experiment_status(experiment_id)
        
        print(f"Experiment {experiment_id}: {status['progress']:.1%} complete")
        print(f"Estimated time remaining: {status['eta']} minutes")
        
        # Check for errors or resource issues
        if status['errors']:
            handle_experiment_errors(experiment_id, status['errors'])
        
        time.sleep(60)  # Check every minute
```

### 3. Post-Experiment Validation

**Data Quality Checks:**
```python
def validate_experiment_results(results_directory):
    """Validate experiment outputs for quality and completeness."""
    
    validation_results = {
        'missing_files': [],
        'corrupted_files': [],
        'parameter_mismatches': [],
        'statistical_anomalies': []
    }
    
    for experiment_dir in get_experiment_directories(results_directory):
        # Check required files exist
        required_files = ['out.csv', 'metadata.json', 'simsetting.yml']
        for file in required_files:
            if not os.path.exists(os.path.join(experiment_dir, file)):
                validation_results['missing_files'].append(
                    f"{experiment_dir}/{file}"
                )
        
        # Validate file contents
        try:
            validate_output_files(experiment_dir)
        except Exception as e:
            validation_results['corrupted_files'].append(
                f"{experiment_dir}: {e}"
            )
        
        # Check parameter consistency
        if not validate_parameter_consistency(experiment_dir):
            validation_results['parameter_mismatches'].append(experiment_dir)
    
    return validation_results
```

## Statistical Analysis Planning

### 1. Analysis Plan Template

**Pre-Registration:**
Document analysis plan before data collection:

```python
analysis_plan = {
    'primary_hypotheses': [
        'System 1 leads to faster movement initiation than System 2',
        'Social connectivity improves destination selection efficiency'
    ],
    
    'primary_analyses': [
        'Mann-Whitney U test comparing first move day between S1 and S2',
        'ANOVA testing social connectivity effects on destination entropy'
    ],
    
    'secondary_analyses': [
        'Correlation analysis between conflict threshold and System 1 activation',
        'Regression analysis of topology effects on movement patterns'
    ],
    
    'multiple_comparisons': 'Bonferroni correction for family-wise error rate',
    
    'effect_size_measures': ['Cohen\'s d', 'eta-squared', 'Pearson\'s r'],
    
    'significance_level': 0.05,
    
    'exclusion_criteria': [
        'Experiments with >20% agent initialization failures',
        'Simulations terminating before day 50'
    ]
}
```

### 2. Statistical Test Selection

**Choosing Appropriate Tests:**

```python
def select_statistical_test(data_characteristics):
    """Guide for selecting appropriate statistical tests."""
    
    if data_characteristics['distribution'] == 'normal':
        if data_characteristics['groups'] == 2:
            return 't-test (independent or paired)'
        else:
            return 'ANOVA (one-way or factorial)'
    
    else:  # Non-normal distribution
        if data_characteristics['groups'] == 2:
            return 'Mann-Whitney U test (independent) or Wilcoxon signed-rank (paired)'
        else:
            return 'Kruskal-Wallis test'
    
    # For categorical outcomes
    if data_characteristics['outcome_type'] == 'categorical':
        return 'Chi-square test or Fisher\'s exact test'
    
    # For correlation analysis
    if data_characteristics['analysis_type'] == 'correlation':
        if data_characteristics['distribution'] == 'normal':
            return 'Pearson correlation'
        else:
            return 'Spearman rank correlation'
```

### 3. Multiple Comparisons Handling

**Correction Methods:**

```python
from scipy.stats import false_discovery_control
import numpy as np

def apply_multiple_comparisons_correction(p_values, method='bonferroni'):
    """Apply multiple comparisons correction."""
    
    if method == 'bonferroni':
        corrected_alpha = 0.05 / len(p_values)
        significant = p_values < corrected_alpha
    
    elif method == 'fdr':
        # False Discovery Rate (Benjamini-Hochberg)
        significant = false_discovery_control(p_values, alpha=0.05)
    
    elif method == 'holm':
        # Holm-Bonferroni method
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        
        significant = np.zeros(len(p_values), dtype=bool)
        for i, p in enumerate(sorted_p):
            corrected_alpha = 0.05 / (len(p_values) - i)
            if p < corrected_alpha:
                significant[sorted_indices[i]] = True
            else:
                break
    
    return significant
```

## Quality Assurance

### 1. Experimental Validity Checks

**Internal Validity:**
- Randomization verification
- Control condition validation
- Confounding variable assessment
- Measurement reliability checks

**External Validity:**
- Parameter range justification
- Scenario realism assessment
- Generalizability considerations
- Boundary condition testing

### 2. Reproducibility Measures

**Documentation Requirements:**
```python
experiment_documentation = {
    'framework_version': get_framework_version(),
    'flee_version': get_flee_version(),
    'python_version': sys.version,
    'random_seeds': experiment_seeds,
    'parameter_values': all_parameter_settings,
    'system_specifications': get_system_info(),
    'execution_timestamp': datetime.now().isoformat(),
    'git_commit_hash': get_git_commit_hash()
}
```

**Code and Data Archival:**
- Version control all analysis code
- Archive raw experimental outputs
- Document data processing steps
- Provide replication instructions

### 3. Error Detection and Handling

**Automated Quality Checks:**
```python
def run_quality_checks(experiment_results):
    """Automated quality assurance checks."""
    
    checks = {
        'completion_rate': check_completion_rate(experiment_results),
        'output_consistency': check_output_consistency(experiment_results),
        'parameter_validation': validate_all_parameters(experiment_results),
        'statistical_sanity': check_statistical_sanity(experiment_results)
    }
    
    # Flag potential issues
    issues = []
    if checks['completion_rate'] < 0.9:
        issues.append('Low experiment completion rate')
    
    if not checks['output_consistency']:
        issues.append('Inconsistent output formats detected')
    
    return checks, issues
```

## Reporting Standards

### 1. Results Reporting Template

**Experimental Description:**
- Hypothesis and predictions
- Experimental design (factorial, etc.)
- Sample sizes and power analysis
- Randomization and control procedures

**Statistical Results:**
- Descriptive statistics (means, SDs, medians, IQRs)
- Test statistics and p-values
- Effect sizes with confidence intervals
- Multiple comparisons corrections applied

**Interpretation:**
- Practical significance assessment
- Limitations and boundary conditions
- Implications for dual-process theory
- Recommendations for future research

### 2. Visualization Standards

**Required Plots:**
- Distribution plots for key outcome variables
- Effect size plots with confidence intervals
- Interaction plots for factorial designs
- Diagnostic plots for assumption checking

**Plot Quality Standards:**
- Clear axis labels and units
- Appropriate scale and aspect ratios
- Error bars representing appropriate uncertainty measures
- Colorblind-friendly color schemes

## Summary

Rigorous experimental design is crucial for generating reliable insights about dual-process decision-making in refugee movement. Key principles include:

1. **Hypothesis-Driven Design**: Clear, testable predictions
2. **Controlled Conditions**: Systematic factor manipulation
3. **Adequate Sample Sizes**: Power analysis-based planning
4. **Proper Randomization**: Bias prevention strategies
5. **Quality Assurance**: Validation and reproducibility measures
6. **Statistical Rigor**: Appropriate tests and corrections
7. **Transparent Reporting**: Complete documentation and interpretation

Following these guidelines ensures that experimental results contribute meaningfully to our understanding of cognitive processes in crisis decision-making while maintaining scientific rigor and reproducibility.