# Dual Process Theory Implementation

This document explains the theoretical foundation and implementation of dual-process decision-making in the Flee Dual Process framework.

## Theoretical Background

### Dual Process Theory Overview

Dual Process Theory proposes that human cognition operates through two distinct systems:

**System 1 (Automatic Processing)**
- Fast, intuitive, and automatic
- Requires minimal cognitive resources
- Based on heuristics and learned associations
- Operates under time pressure and stress
- Prone to biases but enables rapid responses

**System 2 (Controlled Processing)**
- Slow, deliberate, and effortful
- Requires significant cognitive resources
- Based on logical reasoning and analysis
- Operates when time and resources permit
- More accurate but slower decision-making

### Application to Refugee Movement

In refugee movement scenarios, dual-process theory helps explain:

1. **Crisis Response Patterns**: How people make movement decisions under different levels of threat and time pressure
2. **Information Processing**: How agents use available information about destinations and routes
3. **Social Influence**: How social connections affect decision-making processes
4. **Adaptation Over Time**: How decision-making strategies change as situations evolve

## Framework Implementation

### Cognitive Mode Configurations

The framework implements four distinct cognitive modes:

#### 1. System 1 Only (`s1_only`)

Pure System 1 processing with minimal deliberation:

```yaml
move_rules:
  two_system_decision_making: false
  awareness_level: 1              # Limited awareness of distant locations
  weight_softening: 0.5           # Moderate weight softening
  average_social_connectivity: 0.0 # No social connectivity
```

**Behavioral Characteristics:**
- Immediate response to conflict
- Limited consideration of distant destinations
- Decisions based on immediate proximity and capacity
- High variability in individual decisions
- Fast movement initiation

#### 2. System 2 Disconnected (`s2_disconnected`)

Pure System 2 processing without social connectivity:

```yaml
move_rules:
  two_system_decision_making: true
  awareness_level: 3              # Full awareness of all locations
  weight_softening: 0.1           # Minimal weight softening (sharp preferences)
  average_social_connectivity: 0.0 # No social connectivity
```

**Behavioral Characteristics:**
- Delayed response (planning time)
- Comprehensive evaluation of all destinations
- Optimal route selection based on individual analysis
- Consistent decision-making patterns
- Lower movement variability

#### 3. System 2 Full (`s2_full`)

System 2 processing with full social connectivity:

```yaml
move_rules:
  two_system_decision_making: true
  awareness_level: 3              # Full awareness of all locations
  weight_softening: 0.1           # Minimal weight softening
  average_social_connectivity: 8.0 # High social connectivity
```

**Behavioral Characteristics:**
- Delayed response with social consultation
- Information sharing about destinations
- Coordinated movement patterns
- Reduced individual variability
- Collective decision-making effects

#### 4. Dual Process (`dual_process`)

Dynamic switching between System 1 and System 2:

```yaml
move_rules:
  two_system_decision_making: true
  awareness_level: 2              # Moderate awareness
  weight_softening: 0.3           # Balanced weight softening
  average_social_connectivity: 3.0 # Moderate social connectivity
  conflict_threshold: 0.6         # Threshold for System 1 activation
  recovery_period_max: 30         # Recovery time after System 1 activation
```

**Behavioral Characteristics:**
- Context-dependent processing mode
- System 1 activation under high conflict
- System 2 operation during low conflict periods
- Adaptive decision-making strategies
- Realistic cognitive load management

### Key Parameters and Their Effects

#### Awareness Level
Controls how many locations agents consider in their decision-making:

- **Level 1**: Only immediate neighbors and current location
- **Level 2**: Locations within 2 steps of current position
- **Level 3**: All locations in the network

**Theoretical Basis**: Represents cognitive capacity limitations and information availability under different processing modes.

#### Social Connectivity
Average number of social connections per agent:

- **0.0**: No social information sharing
- **3.0**: Moderate social network (family/close friends)
- **8.0**: High social connectivity (community networks)

**Theoretical Basis**: Social networks provide information channels and influence decision-making through social proof and collective intelligence.

#### Conflict Threshold
Conflict intensity level that triggers System 1 activation:

- **Low (0.3)**: System 1 activated by minor threats
- **Medium (0.6)**: Balanced threshold for realistic responses
- **High (0.8)**: System 1 only for severe threats

**Theoretical Basis**: Stress and threat levels determine when automatic processing overrides deliberate planning.

#### Weight Softening
Controls how sharply agents prefer better destinations:

- **0.1**: Sharp preferences (clear best choice)
- **0.5**: Moderate preferences (some randomness)
- **0.9**: Soft preferences (high randomness)

**Theoretical Basis**: System 1 processing introduces more noise and heuristic-based decisions compared to System 2's optimization.

#### Recovery Period
Time required to return to System 2 after System 1 activation:

- **7 days**: Quick recovery (resilient populations)
- **30 days**: Moderate recovery (typical stress response)
- **60 days**: Slow recovery (traumatized populations)

**Theoretical Basis**: Cognitive resources need time to recover after stress-induced System 1 activation.

## Experimental Design Principles

### 1. Controlled Comparisons

Design experiments to isolate specific cognitive mechanisms:

```python
# Compare pure modes to understand baseline differences
modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']

# Use identical topology and scenario across modes
for mode in modes:
    config = config_manager.create_cognitive_config(mode)
    run_experiment(topology, scenario, config)
```

### 2. Parameter Sensitivity Analysis

Test sensitivity to key dual-process parameters:

```python
# Test conflict threshold sensitivity
thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
for threshold in thresholds:
    config = create_dual_process_config(conflict_threshold=threshold)
    run_experiment(topology, scenario, config)
```

### 3. Scenario-Mode Interactions

Test how different conflict patterns interact with cognitive modes:

```python
scenarios = ['spike', 'gradual', 'cascading', 'oscillating']
modes = ['s1_only', 's2_full', 'dual_process']

# Full factorial design
for scenario_type in scenarios:
    for mode in modes:
        scenario = generate_scenario(scenario_type)
        config = create_config(mode)
        run_experiment(topology, scenario, config)
```

### 4. Network Topology Effects

Examine how network structure affects cognitive processing:

```python
topologies = ['linear', 'star', 'tree', 'grid']
for topology_type in topologies:
    topology = generate_topology(topology_type)
    # Test with dual-process mode to see topology-cognition interactions
    config = create_dual_process_config()
    run_experiment(topology, scenario, config)
```

## Validation Approaches

### 1. Face Validity

Ensure model behaviors align with theoretical expectations:

- **System 1**: Faster responses, more variable decisions
- **System 2**: Slower responses, more optimal decisions
- **Dual Process**: Context-dependent switching between modes

### 2. Construct Validity

Verify that parameters affect behavior as theoretically predicted:

- **Awareness Level**: Higher levels → better destination selection
- **Social Connectivity**: Higher connectivity → more coordinated movement
- **Conflict Threshold**: Lower thresholds → more System 1 activation

### 3. Predictive Validity

Compare model predictions with empirical refugee movement data:

- Movement timing patterns
- Destination selection preferences
- Response to different conflict types
- Social network effects on movement

### 4. Sensitivity Analysis

Test model robustness to parameter variations:

```python
# Test parameter sensitivity
base_config = create_dual_process_config()
parameters = {
    'conflict_threshold': [0.4, 0.5, 0.6, 0.7],
    'recovery_period_max': [14, 21, 30, 45],
    'average_social_connectivity': [1.0, 3.0, 5.0, 7.0]
}

for param, values in parameters.items():
    test_parameter_sensitivity(base_config, param, values)
```

## Statistical Analysis Guidelines

### 1. Appropriate Statistical Tests

**Between-Group Comparisons**:
- Use non-parametric tests (Mann-Whitney U, Kruskal-Wallis) for non-normal distributions
- Report effect sizes (Cohen's d) alongside p-values
- Apply multiple comparison corrections when testing multiple parameters

**Within-Group Comparisons**:
- Use paired tests when comparing same agents across conditions
- Account for temporal autocorrelation in time series data

### 2. Key Metrics for Analysis

**Movement Timing**:
- First move day (response speed)
- Peak movement day (coordination)
- Movement duration (decision persistence)

**Destination Selection**:
- Distance traveled (efficiency)
- Destination distribution entropy (diversity)
- Camp utilization patterns (optimization)

**Cognitive State Transitions** (Dual Process mode):
- System 1 activation frequency
- System 1 duration
- Recovery time patterns

### 3. Effect Size Interpretation

**Cohen's d Guidelines**:
- Small effect: d = 0.2
- Medium effect: d = 0.5
- Large effect: d = 0.8

**Practical Significance**:
- Consider real-world implications of statistical differences
- Focus on effect sizes that would matter for policy decisions

## Interpretation Guidelines

### 1. System 1 vs System 2 Differences

**Expected Patterns**:
- System 1: Faster response, shorter distances, higher variability
- System 2: Slower response, longer distances, lower variability
- Dual Process: Intermediate values with context-dependent variation

**Interpretation Considerations**:
- Faster isn't always better (may indicate panic vs. planning)
- Higher variability may reflect realistic individual differences
- Context matters: System 1 may be adaptive in crisis situations

### 2. Social Connectivity Effects

**Expected Patterns**:
- Higher connectivity → more coordinated movement
- Information sharing → better destination selection
- Social influence → reduced individual variability

**Interpretation Considerations**:
- Social effects may be positive (information sharing) or negative (herding)
- Network structure affects information flow patterns
- Cultural factors influence social connectivity importance

### 3. Conflict Scenario Interactions

**Spike Conflicts**:
- Should favor System 1 responses
- Test immediate threat response mechanisms

**Gradual Conflicts**:
- Should favor System 2 responses
- Test planning and preparation behaviors

**Cascading Conflicts**:
- Test social information transmission
- Examine network-based decision-making

**Oscillating Conflicts**:
- Test adaptation and learning mechanisms
- Examine long-term cognitive strategies

## Limitations and Considerations

### 1. Model Limitations

**Simplifications**:
- Binary cognitive systems (reality is more continuous)
- Fixed parameter values (may vary across individuals)
- Limited emotional and psychological factors

**Scope Limitations**:
- Focus on movement decisions (not other refugee experiences)
- Simplified social network structures
- Abstract representation of conflict and threat

### 2. Validation Challenges

**Empirical Data Limitations**:
- Limited data on cognitive processes during displacement
- Ethical constraints on experimental studies with refugees
- Cultural and contextual variations in decision-making

**Model Validation**:
- Difficulty separating cognitive effects from other factors
- Parameter estimation challenges
- Generalizability across different contexts

### 3. Interpretation Cautions

**Avoid Over-Interpretation**:
- Model results are theoretical predictions, not empirical facts
- Statistical significance doesn't guarantee practical importance
- Individual variation may be more important than group averages

**Consider Context**:
- Results may be specific to modeled scenarios
- Real-world factors not captured in the model may be crucial
- Cultural and individual differences affect cognitive processing

## Future Directions

### 1. Model Extensions

**Enhanced Cognitive Modeling**:
- Continuous rather than binary cognitive systems
- Individual differences in cognitive parameters
- Learning and adaptation mechanisms

**Expanded Social Modeling**:
- Dynamic social network formation
- Information quality and reliability
- Cultural factors in decision-making

### 2. Empirical Validation

**Field Studies**:
- Collaborate with humanitarian organizations
- Collect movement timing and decision-making data
- Validate model predictions against real displacement patterns

**Laboratory Studies**:
- Controlled experiments on decision-making under stress
- Social influence studies in crisis scenarios
- Cross-cultural validation of cognitive mechanisms

### 3. Policy Applications

**Humanitarian Response**:
- Optimize camp placement based on cognitive decision-making patterns
- Design information campaigns that account for cognitive processing modes
- Predict movement patterns for resource allocation

**Early Warning Systems**:
- Incorporate cognitive factors into displacement prediction models
- Account for different response patterns across populations
- Improve timing of humanitarian interventions

## Summary

The Flee Dual Process framework provides a theoretically grounded approach to modeling refugee movement decisions. By implementing dual-process theory principles, it enables systematic investigation of how cognitive mechanisms affect displacement patterns. The framework's experimental design capabilities support rigorous hypothesis testing while its validation tools ensure theoretical consistency and empirical relevance.

Key strengths include:
- Solid theoretical foundation in cognitive science
- Flexible experimental design capabilities
- Comprehensive validation and analysis tools
- Clear interpretation guidelines

Researchers using this framework should carefully consider the theoretical assumptions, validate results against empirical data where possible, and interpret findings within the context of the model's limitations and scope.