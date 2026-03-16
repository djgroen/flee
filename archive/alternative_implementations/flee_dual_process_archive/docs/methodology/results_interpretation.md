# Results Interpretation Guide

This document provides comprehensive guidelines for interpreting results from dual-process experiments, including statistical analysis, effect size interpretation, and theoretical implications.

## Statistical Analysis Framework

### 1. Descriptive Statistics

Always begin analysis with comprehensive descriptive statistics:

```python
def calculate_descriptive_statistics(data, group_var, outcome_vars):
    """Calculate comprehensive descriptive statistics."""
    
    descriptives = {}
    
    for outcome in outcome_vars:
        descriptives[outcome] = data.groupby(group_var)[outcome].agg([
            'count', 'mean', 'std', 'median', 'min', 'max',
            lambda x: x.quantile(0.25),  # Q1
            lambda x: x.quantile(0.75),  # Q3
            'skew', 'kurtosis'
        ]).round(3)
    
    return descriptives

# Example usage
outcomes = ['first_move_day', 'total_distance', 'destination_entropy']
descriptives = calculate_descriptive_statistics(
    data=experiment_data, 
    group_var='cognitive_mode', 
    outcome_vars=outcomes
)
```

**Key Descriptive Measures:**
- **Central Tendency**: Mean (for normal distributions) or median (for skewed distributions)
- **Variability**: Standard deviation and interquartile range
- **Distribution Shape**: Skewness and kurtosis
- **Range**: Minimum and maximum values

### 2. Inferential Statistics

#### Choosing Appropriate Tests

**Decision Tree for Test Selection:**

```python
def select_statistical_test(data_properties):
    """Guide for selecting appropriate statistical tests."""
    
    # Check normality
    if data_properties['normal_distribution']:
        if data_properties['n_groups'] == 2:
            if data_properties['paired']:
                return 'paired_t_test'
            else:
                return 'independent_t_test'
        else:
            return 'anova'
    
    else:  # Non-normal distribution
        if data_properties['n_groups'] == 2:
            if data_properties['paired']:
                return 'wilcoxon_signed_rank'
            else:
                return 'mann_whitney_u'
        else:
            return 'kruskal_wallis'

# Example implementation
from scipy import stats

def run_statistical_test(group1_data, group2_data, test_type='auto'):
    """Run appropriate statistical test."""
    
    if test_type == 'auto':
        # Test normality
        _, p_norm1 = stats.shapiro(group1_data)
        _, p_norm2 = stats.shapiro(group2_data)
        
        if p_norm1 > 0.05 and p_norm2 > 0.05:
            # Both normal - use t-test
            statistic, p_value = stats.ttest_ind(group1_data, group2_data)
            test_used = 't-test'
        else:
            # Non-normal - use Mann-Whitney U
            statistic, p_value = stats.mannwhitneyu(
                group1_data, group2_data, alternative='two-sided'
            )
            test_used = 'Mann-Whitney U'
    
    return {
        'statistic': statistic,
        'p_value': p_value,
        'test_used': test_used
    }
```

#### Effect Size Calculation

**Cohen's d for Mean Differences:**

```python
def calculate_cohens_d(group1, group2):
    """Calculate Cohen's d effect size."""
    
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    # Cohen's d
    d = (mean1 - mean2) / pooled_std
    
    return d

def interpret_cohens_d(d):
    """Interpret Cohen's d effect size."""
    
    abs_d = abs(d)
    
    if abs_d < 0.2:
        return 'negligible'
    elif abs_d < 0.5:
        return 'small'
    elif abs_d < 0.8:
        return 'medium'
    else:
        return 'large'
```

**Eta-squared for ANOVA:**

```python
def calculate_eta_squared(f_statistic, df_between, df_within):
    """Calculate eta-squared effect size for ANOVA."""
    
    eta_squared = (f_statistic * df_between) / (f_statistic * df_between + df_within)
    
    return eta_squared

def interpret_eta_squared(eta_squared):
    """Interpret eta-squared effect size."""
    
    if eta_squared < 0.01:
        return 'negligible'
    elif eta_squared < 0.06:
        return 'small'
    elif eta_squared < 0.14:
        return 'medium'
    else:
        return 'large'
```

### 3. Confidence Intervals

Always report confidence intervals alongside point estimates:

```python
def calculate_confidence_interval(data, confidence_level=0.95):
    """Calculate confidence interval for mean."""
    
    n = len(data)
    mean = np.mean(data)
    sem = stats.sem(data)  # Standard error of mean
    
    # t-distribution critical value
    alpha = 1 - confidence_level
    t_critical = stats.t.ppf(1 - alpha/2, df=n-1)
    
    # Confidence interval
    margin_of_error = t_critical * sem
    ci_lower = mean - margin_of_error
    ci_upper = mean + margin_of_error
    
    return {
        'mean': mean,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'margin_of_error': margin_of_error
    }
```

## Interpreting Key Metrics

### 1. Movement Timing Metrics

#### First Move Day

**Interpretation Guidelines:**

```python
def interpret_first_move_day(results_by_mode):
    """Interpret first move day results."""
    
    interpretations = {}
    
    for mode, data in results_by_mode.items():
        mean_day = np.mean(data['first_move_day'])
        std_day = np.std(data['first_move_day'])
        
        if mean_day < 2:
            speed = 'very fast'
            implication = 'immediate crisis response'
        elif mean_day < 5:
            speed = 'fast'
            implication = 'rapid threat assessment'
        elif mean_day < 10:
            speed = 'moderate'
            implication = 'deliberate planning period'
        else:
            speed = 'slow'
            implication = 'extensive preparation time'
        
        interpretations[mode] = {
            'speed_category': speed,
            'theoretical_implication': implication,
            'variability': 'high' if std_day > mean_day * 0.5 else 'low'
        }
    
    return interpretations
```

**Expected Patterns:**
- **System 1**: Fast response (1-3 days), high variability
- **System 2**: Slower response (5-10 days), low variability
- **Dual Process**: Context-dependent (2-8 days), moderate variability

#### Peak Movement Day

**Interpretation:**
- Early peaks (days 1-5): Crisis-driven mass exodus
- Later peaks (days 10-20): Planned, coordinated movement
- Multiple peaks: Staged movement or secondary displacement

### 2. Movement Efficiency Metrics

#### Total Distance Traveled

**Interpretation Framework:**

```python
def interpret_total_distance(distance_data, topology_info):
    """Interpret total distance results."""
    
    # Calculate theoretical minimum distance
    min_distance = topology_info['shortest_path_to_safety']
    
    interpretations = {}
    
    for mode, distances in distance_data.items():
        mean_distance = np.mean(distances)
        efficiency_ratio = min_distance / mean_distance
        
        if efficiency_ratio > 0.9:
            efficiency = 'highly efficient'
        elif efficiency_ratio > 0.7:
            efficiency = 'moderately efficient'
        elif efficiency_ratio > 0.5:
            efficiency = 'somewhat inefficient'
        else:
            efficiency = 'highly inefficient'
        
        interpretations[mode] = {
            'efficiency_category': efficiency,
            'efficiency_ratio': efficiency_ratio,
            'excess_distance': mean_distance - min_distance
        }
    
    return interpretations
```

**Expected Patterns:**
- **System 1**: Shorter distances (direct routes), higher variability
- **System 2**: Longer distances (optimal routes), lower variability
- **Social Connectivity**: May increase distances due to coordination

### 3. Destination Selection Metrics

#### Destination Entropy

**Calculation and Interpretation:**

```python
def calculate_destination_entropy(destination_counts):
    """Calculate Shannon entropy for destination distribution."""
    
    total_agents = sum(destination_counts.values())
    probabilities = [count/total_agents for count in destination_counts.values()]
    
    # Shannon entropy
    entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
    
    # Maximum possible entropy (uniform distribution)
    max_entropy = np.log2(len(destination_counts))
    
    # Normalized entropy
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
    
    return {
        'entropy': entropy,
        'max_entropy': max_entropy,
        'normalized_entropy': normalized_entropy
    }

def interpret_destination_entropy(entropy_results):
    """Interpret destination entropy results."""
    
    interpretations = {}
    
    for mode, entropy_data in entropy_results.items():
        norm_entropy = entropy_data['normalized_entropy']
        
        if norm_entropy > 0.9:
            distribution = 'highly dispersed'
            implication = 'diverse destination preferences'
        elif norm_entropy > 0.7:
            distribution = 'moderately dispersed'
            implication = 'some destination clustering'
        elif norm_entropy > 0.5:
            distribution = 'somewhat concentrated'
            implication = 'preferred destinations emerging'
        else:
            distribution = 'highly concentrated'
            implication = 'strong destination preferences'
        
        interpretations[mode] = {
            'distribution_pattern': distribution,
            'theoretical_implication': implication
        }
    
    return interpretations
```

**Expected Patterns:**
- **System 1**: Lower entropy (herding behavior)
- **System 2**: Higher entropy (individual optimization)
- **Social Connectivity**: May increase or decrease entropy depending on information quality

### 4. Cognitive State Metrics (Dual Process Mode)

#### System 1 Activation Patterns

**Analysis Framework:**

```python
def analyze_system1_activation(cognitive_state_data):
    """Analyze System 1 activation patterns."""
    
    # Extract System 1 episodes
    system1_episodes = identify_system1_episodes(cognitive_state_data)
    
    analysis = {
        'activation_frequency': len(system1_episodes) / len(cognitive_state_data),
        'average_duration': np.mean([ep['duration'] for ep in system1_episodes]),
        'total_time_in_system1': sum(ep['duration'] for ep in system1_episodes),
        'triggers': analyze_activation_triggers(system1_episodes, cognitive_state_data)
    }
    
    return analysis

def interpret_system1_patterns(activation_analysis):
    """Interpret System 1 activation patterns."""
    
    freq = activation_analysis['activation_frequency']
    duration = activation_analysis['average_duration']
    
    if freq > 0.3:  # >30% of time in System 1
        pattern = 'high stress response'
        implication = 'frequent threat perception'
    elif freq > 0.1:  # 10-30% of time
        pattern = 'moderate stress response'
        implication = 'situational threat responses'
    else:  # <10% of time
        pattern = 'low stress response'
        implication = 'predominantly deliberate processing'
    
    return {
        'activation_pattern': pattern,
        'theoretical_implication': implication,
        'recovery_efficiency': 'good' if duration < 7 else 'poor'
    }
```

## Comparative Analysis

### 1. Between-Group Comparisons

#### Cognitive Mode Comparisons

**Analysis Template:**

```python
def compare_cognitive_modes(experiment_results):
    """Comprehensive comparison of cognitive modes."""
    
    modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
    metrics = ['first_move_day', 'total_distance', 'destination_entropy']
    
    comparisons = {}
    
    for metric in metrics:
        comparisons[metric] = {}
        
        # Pairwise comparisons
        for i, mode1 in enumerate(modes):
            for mode2 in modes[i+1:]:
                
                data1 = experiment_results[mode1][metric]
                data2 = experiment_results[mode2][metric]
                
                # Statistical test
                test_result = run_statistical_test(data1, data2)
                
                # Effect size
                effect_size = calculate_cohens_d(data1, data2)
                
                comparisons[metric][f'{mode1}_vs_{mode2}'] = {
                    'p_value': test_result['p_value'],
                    'effect_size': effect_size,
                    'effect_interpretation': interpret_cohens_d(effect_size),
                    'practical_significance': abs(effect_size) > 0.3
                }
    
    return comparisons
```

#### Expected Comparison Patterns

**System 1 vs System 2:**
- First Move Day: S1 < S2 (faster response)
- Total Distance: S1 < S2 (more direct routes)
- Destination Entropy: S1 < S2 (more clustering)

**Disconnected vs Connected System 2:**
- First Move Day: Similar (both deliberate)
- Total Distance: Connected > Disconnected (coordination costs)
- Destination Entropy: Connected < Disconnected (coordination effects)

### 2. Parameter Sensitivity Analysis

#### Interpreting Parameter Effects

```python
def interpret_parameter_sensitivity(sensitivity_results):
    """Interpret parameter sensitivity analysis results."""
    
    interpretations = {}
    
    for parameter, analysis in sensitivity_results.items():
        correlation = analysis['correlation_coefficient']
        p_value = analysis['p_value']
        effect_size = analysis['effect_size']
        
        # Strength of relationship
        if abs(correlation) > 0.7:
            strength = 'strong'
        elif abs(correlation) > 0.5:
            strength = 'moderate'
        elif abs(correlation) > 0.3:
            strength = 'weak'
        else:
            strength = 'negligible'
        
        # Direction of relationship
        direction = 'positive' if correlation > 0 else 'negative'
        
        # Statistical significance
        significant = p_value < 0.05
        
        interpretations[parameter] = {
            'relationship_strength': strength,
            'relationship_direction': direction,
            'statistically_significant': significant,
            'practical_importance': abs(effect_size) > 0.3,
            'interpretation': generate_parameter_interpretation(
                parameter, correlation, strength, direction
            )
        }
    
    return interpretations

def generate_parameter_interpretation(parameter, correlation, strength, direction):
    """Generate interpretation text for parameter effects."""
    
    interpretations = {
        'awareness_level': {
            'positive': 'Higher awareness leads to better destination selection',
            'negative': 'Higher awareness may cause decision paralysis'
        },
        'social_connectivity': {
            'positive': 'Social connections improve collective decision-making',
            'negative': 'Social connections may lead to herding behavior'
        },
        'conflict_threshold': {
            'positive': 'Higher thresholds delay System 1 activation',
            'negative': 'Higher thresholds enable faster System 1 responses'
        }
    }
    
    return interpretations.get(parameter, {}).get(direction, 'No standard interpretation available')
```

## Theoretical Interpretation

### 1. Dual Process Theory Validation

#### Expected Theoretical Patterns

**System 1 Characteristics:**
- Fast response times
- Higher decision variability
- Proximity-based destination selection
- Limited information integration

**System 2 Characteristics:**
- Slower response times
- Lower decision variability
- Optimization-based destination selection
- Comprehensive information integration

**Validation Checklist:**

```python
def validate_dual_process_theory(experimental_results):
    """Validate results against dual process theory predictions."""
    
    validations = {}
    
    # Speed hypothesis: S1 faster than S2
    s1_speed = np.mean(experimental_results['s1_only']['first_move_day'])
    s2_speed = np.mean(experimental_results['s2_full']['first_move_day'])
    
    validations['speed_hypothesis'] = {
        'prediction': 'S1 < S2',
        'observed': f'S1: {s1_speed:.1f}, S2: {s2_speed:.1f}',
        'supported': s1_speed < s2_speed
    }
    
    # Variability hypothesis: S1 more variable than S2
    s1_var = np.std(experimental_results['s1_only']['first_move_day'])
    s2_var = np.std(experimental_results['s2_full']['first_move_day'])
    
    validations['variability_hypothesis'] = {
        'prediction': 'S1_var > S2_var',
        'observed': f'S1_var: {s1_var:.1f}, S2_var: {s2_var:.1f}',
        'supported': s1_var > s2_var
    }
    
    # Efficiency hypothesis: S2 more efficient than S1
    s1_distance = np.mean(experimental_results['s1_only']['total_distance'])
    s2_distance = np.mean(experimental_results['s2_full']['total_distance'])
    
    validations['efficiency_hypothesis'] = {
        'prediction': 'S2 more optimal routes',
        'observed': f'S1: {s1_distance:.1f}km, S2: {s2_distance:.1f}km',
        'supported': s2_distance > s1_distance  # Assuming longer = more optimal
    }
    
    return validations
```

### 2. Contextual Factors

#### Scenario-Mode Interactions

**Expected Interaction Patterns:**

```python
def interpret_scenario_mode_interactions(interaction_results):
    """Interpret scenario-cognitive mode interactions."""
    
    interpretations = {}
    
    for scenario_type, mode_results in interaction_results.items():
        
        if scenario_type == 'spike':
            # Spike conflicts should favor System 1
            expected_pattern = 'S1 advantage in speed, S2 disadvantage'
            
        elif scenario_type == 'gradual':
            # Gradual conflicts should favor System 2
            expected_pattern = 'S2 advantage in optimization, S1 disadvantage'
            
        elif scenario_type == 'cascading':
            # Cascading conflicts should favor social connectivity
            expected_pattern = 'Connected modes show coordination benefits'
            
        elif scenario_type == 'oscillating':
            # Oscillating conflicts should favor dual process
            expected_pattern = 'Dual process shows adaptation advantages'
        
        interpretations[scenario_type] = {
            'expected_pattern': expected_pattern,
            'observed_results': mode_results,
            'pattern_match': evaluate_pattern_match(expected_pattern, mode_results)
        }
    
    return interpretations
```

#### Network Topology Effects

**Topology-Cognition Interactions:**

```python
def interpret_topology_effects(topology_results):
    """Interpret network topology effects on cognitive processing."""
    
    interpretations = {}
    
    topology_characteristics = {
        'linear': {
            'structure': 'sequential choices',
            'cognitive_demand': 'low',
            'expected_mode_effects': 'minimal differences between S1/S2'
        },
        'star': {
            'structure': 'centralized hub',
            'cognitive_demand': 'moderate',
            'expected_mode_effects': 'S2 advantage in hub utilization'
        },
        'tree': {
            'structure': 'hierarchical choices',
            'cognitive_demand': 'high',
            'expected_mode_effects': 'S2 strong advantage in navigation'
        },
        'grid': {
            'structure': 'multiple pathways',
            'cognitive_demand': 'very high',
            'expected_mode_effects': 'S2 very strong advantage'
        }
    }
    
    for topology, results in topology_results.items():
        characteristics = topology_characteristics[topology]
        
        interpretations[topology] = {
            'structural_characteristics': characteristics,
            'observed_mode_differences': calculate_mode_differences(results),
            'cognitive_load_evidence': assess_cognitive_load_evidence(results),
            'theoretical_consistency': evaluate_theoretical_consistency(
                characteristics, results
            )
        }
    
    return interpretations
```

## Practical Significance Assessment

### 1. Effect Size Interpretation

#### Contextualizing Effect Sizes

```python
def assess_practical_significance(statistical_results, context_info):
    """Assess practical significance of statistical results."""
    
    assessments = {}
    
    for comparison, results in statistical_results.items():
        effect_size = results['effect_size']
        p_value = results['p_value']
        
        # Statistical significance
        statistically_significant = p_value < 0.05
        
        # Practical significance thresholds (context-dependent)
        if context_info['domain'] == 'humanitarian_response':
            # Lower threshold for humanitarian applications
            practically_significant = abs(effect_size) > 0.2
        else:
            # Standard threshold for research
            practically_significant = abs(effect_size) > 0.3
        
        # Real-world impact assessment
        if 'first_move_day' in comparison:
            # Days difference in response time
            days_difference = effect_size * context_info['pooled_std_days']
            impact_description = f"{days_difference:.1f} days difference in response time"
            
        elif 'total_distance' in comparison:
            # Distance difference
            distance_difference = effect_size * context_info['pooled_std_distance']
            impact_description = f"{distance_difference:.1f} km difference in travel distance"
        
        assessments[comparison] = {
            'statistically_significant': statistically_significant,
            'practically_significant': practically_significant,
            'real_world_impact': impact_description,
            'recommendation': generate_practical_recommendation(
                statistically_significant, practically_significant, effect_size
            )
        }
    
    return assessments

def generate_practical_recommendation(stat_sig, pract_sig, effect_size):
    """Generate practical recommendations based on significance."""
    
    if stat_sig and pract_sig:
        if abs(effect_size) > 0.8:
            return "Strong evidence for practical application"
        else:
            return "Moderate evidence for practical consideration"
    
    elif stat_sig and not pract_sig:
        return "Statistically reliable but limited practical impact"
    
    elif not stat_sig and pract_sig:
        return "Potentially important effect requiring larger sample"
    
    else:
        return "No evidence for practical significance"
```

### 2. Policy and Humanitarian Implications

#### Translating Results to Practice

```python
def generate_policy_implications(experimental_results, context):
    """Generate policy implications from experimental results."""
    
    implications = {}
    
    # Response timing implications
    if experimental_results['system1_faster_response']['practically_significant']:
        implications['early_warning'] = {
            'finding': 'System 1 processing leads to faster evacuation',
            'implication': 'Early warning systems should account for immediate responses',
            'recommendation': 'Position resources for rapid deployment'
        }
    
    # Destination selection implications
    if experimental_results['system2_better_distribution']['practically_significant']:
        implications['camp_planning'] = {
            'finding': 'System 2 processing improves destination distribution',
            'implication': 'Information campaigns can improve camp utilization',
            'recommendation': 'Invest in information dissemination systems'
        }
    
    # Social connectivity implications
    if experimental_results['social_connectivity_benefits']['practically_significant']:
        implications['community_networks'] = {
            'finding': 'Social connectivity improves collective decision-making',
            'implication': 'Community networks are valuable resources',
            'recommendation': 'Support and leverage existing social structures'
        }
    
    return implications
```

## Reporting Guidelines

### 1. Results Presentation Structure

**Recommended Reporting Order:**

1. **Descriptive Statistics**
   - Sample sizes and completion rates
   - Central tendencies and variability measures
   - Distribution characteristics

2. **Primary Hypothesis Tests**
   - Statistical test results with effect sizes
   - Confidence intervals
   - Multiple comparisons corrections

3. **Secondary Analyses**
   - Parameter sensitivity results
   - Interaction effects
   - Exploratory findings

4. **Practical Significance Assessment**
   - Effect size interpretations
   - Real-world impact estimates
   - Policy implications

### 2. Visualization Standards

**Required Visualizations:**

```python
def create_results_visualizations(experimental_results):
    """Create standard results visualizations."""
    
    visualizations = {}
    
    # 1. Distribution plots
    visualizations['distributions'] = create_distribution_plots(
        experimental_results, 
        metrics=['first_move_day', 'total_distance', 'destination_entropy']
    )
    
    # 2. Effect size plots
    visualizations['effect_sizes'] = create_effect_size_plots(
        experimental_results,
        comparisons=['s1_vs_s2', 's2_disconnected_vs_s2_full']
    )
    
    # 3. Parameter sensitivity plots
    visualizations['sensitivity'] = create_sensitivity_plots(
        experimental_results,
        parameters=['awareness_level', 'social_connectivity', 'conflict_threshold']
    )
    
    # 4. Interaction plots
    visualizations['interactions'] = create_interaction_plots(
        experimental_results,
        factors=['cognitive_mode', 'scenario_type', 'topology_type']
    )
    
    return visualizations
```

### 3. Limitations and Caveats

**Standard Limitations to Address:**

```python
def document_study_limitations(experimental_design, results):
    """Document study limitations and caveats."""
    
    limitations = {
        'methodological': [
            'Simplified cognitive model (binary systems)',
            'Limited parameter ranges tested',
            'Artificial experimental scenarios'
        ],
        
        'statistical': [
            'Multiple comparisons increase Type I error risk',
            'Effect sizes may not generalize to other contexts',
            'Non-normal distributions limit parametric test validity'
        ],
        
        'theoretical': [
            'Dual process theory is one of many cognitive frameworks',
            'Individual differences not fully captured',
            'Cultural factors not explicitly modeled'
        ],
        
        'practical': [
            'Simulation results may not reflect real-world complexity',
            'Parameter values based on theoretical assumptions',
            'Limited validation against empirical refugee data'
        ]
    }
    
    return limitations
```

## Summary

Proper interpretation of dual-process experiment results requires:

1. **Statistical Rigor**: Appropriate tests, effect sizes, and confidence intervals
2. **Theoretical Grounding**: Results interpreted within dual-process theory framework
3. **Practical Relevance**: Assessment of real-world significance and implications
4. **Methodological Awareness**: Recognition of limitations and boundary conditions
5. **Clear Communication**: Accessible presentation for diverse audiences

Key principles for interpretation:

- **Effect sizes matter more than p-values** for practical significance
- **Theoretical consistency** validates model assumptions
- **Contextual factors** moderate cognitive processing effects
- **Practical implications** guide policy and humanitarian applications
- **Limitations acknowledgment** maintains scientific integrity

Following these guidelines ensures that experimental results contribute meaningfully to both theoretical understanding and practical applications in refugee movement modeling.