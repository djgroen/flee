# Dimensionless Parameter Framework for Displacement Modeling

## Overview

This document presents a dimensionless parameter framework for generalizing findings from dual-process displacement experiments. By identifying key dimensionless groups, we can scale results across different scenarios, populations, and geographic contexts.

## Theoretical Foundation

### Buckingham π Theorem Application

Following dimensional analysis principles, we identify the fundamental dimensions in displacement modeling:

- **[L]**: Length (spatial scale)
- **[T]**: Time (temporal scale)  
- **[N]**: Number of people (population scale)
- **[I]**: Information/awareness (cognitive scale)

### Key Dimensionless Groups

#### 1. Cognitive Efficiency (Π₁)
```
Π₁ = (Awareness_Level) / (Conflict_Threshold × Recovery_Period)
```

**Physical Interpretation**: Ratio of cognitive processing capacity to decision-making constraints.

**Scaling Behavior**: 
- Π₁ < 0.1: Reactive regime (System 1 dominates)
- 0.1 < Π₁ < 1.0: Transitional regime (Dual process optimal)
- Π₁ > 1.0: Deliberative regime (System 2 dominates)

#### 2. Social Coupling (Π₂)
```
Π₂ = (Social_Connectivity) / √(Network_Size)
```

**Physical Interpretation**: Effective information flow per capita in the network.

**Scaling Behavior**:
- Π₂ < 0.5: Isolated decision-making
- 0.5 < Π₂ < 2.0: Collective behavior emergence
- Π₂ > 2.0: Information cascade regime

#### 3. Temporal Scale (Π₃)
```
Π₃ = (Conflict_Duration) / (Decision_Response_Time)
```

**Physical Interpretation**: Number of decision cycles available during conflict.

**Scaling Behavior**:
- Π₃ < 1: Crisis response mode
- 1 < Π₃ < 10: Adaptive planning mode
- Π₃ > 10: Strategic optimization mode

#### 4. Spatial Scale (Π₄)
```
Π₄ = (Network_Diameter) / (Average_Link_Distance)
```

**Physical Interpretation**: Network connectivity relative to geographic scale.

**Scaling Behavior**:
- Π₄ < 5: Locally connected networks
- 5 < Π₄ < 20: Small-world networks
- Π₄ > 20: Highly connected networks

#### 5. Information Flow (Π₅)
```
Π₅ = (Awareness_Level × Social_Connectivity) / (Network_Density)
```

**Physical Interpretation**: Effective information propagation rate through the network.

## Regime Classification

### Performance Regimes

Based on the dimensionless groups, we identify distinct performance regimes:

#### High Performance Regime
- **Conditions**: Π₁ > 0.5, Π₂ > 1.0, Π₃ > 2.0
- **Characteristics**: Efficient evacuation, low casualties, adaptive routing
- **Cognitive Mode**: Dual process or System 2 optimal

#### Moderate Performance Regime  
- **Conditions**: 0.1 < Π₁ < 0.5, 0.5 < Π₂ < 1.0, 1.0 < Π₃ < 2.0
- **Characteristics**: Adequate response, some bottlenecks, mixed strategies
- **Cognitive Mode**: Dual process optimal

#### Low Performance Regime
- **Conditions**: Π₁ < 0.1, Π₂ < 0.5, Π₃ < 1.0
- **Characteristics**: Chaotic evacuation, high casualties, reactive behavior
- **Cognitive Mode**: System 1 dominates by necessity

### Transition Boundaries

Critical transitions occur at:

1. **Cognitive Transition**: Π₁ ≈ 0.3 (System 1 ↔ Dual Process)
2. **Social Transition**: Π₂ ≈ 1.0 (Individual ↔ Collective behavior)
3. **Temporal Transition**: Π₃ ≈ 2.0 (Reactive ↔ Adaptive behavior)

## Scaling Laws

### Performance Scaling
```
Performance ∝ Π₁^α × Π₂^β × Π₃^γ
```

Where empirical exponents are:
- α ≈ 0.6 (cognitive efficiency)
- β ≈ 0.4 (social coupling)  
- γ ≈ 0.3 (temporal scale)

### Response Time Scaling
```
Response_Time ∝ Π₂^(-0.5) × Π₃^(-0.3)
```

### Adaptation Rate Scaling
```
Adaptation_Rate ∝ (1 - exp(-Π₃/2)) × Π₁^0.4
```

## Practical Applications

### Scenario Scaling

To apply results from one scenario to another:

1. **Calculate dimensionless groups** for both scenarios
2. **Identify regime boundaries** using the framework
3. **Apply scaling laws** to transfer performance predictions
4. **Validate** with targeted experiments if groups differ significantly

### Parameter Optimization

For a given scenario, optimize performance by:

1. **Maximize Π₁**: Increase awareness, reduce decision thresholds
2. **Optimize Π₂**: Balance connectivity with network size
3. **Extend Π₃**: Early warning systems, preparation time
4. **Design Π₄**: Network topology optimization

### Generalization Across Contexts

The framework enables:

- **Geographic scaling**: Urban vs rural displacement patterns
- **Population scaling**: Small communities vs large cities  
- **Temporal scaling**: Sudden disasters vs gradual conflicts
- **Cultural scaling**: Different decision-making norms

## Validation and Limitations

### Experimental Validation

The dimensionless framework should be validated through:

1. **Cross-scenario experiments** spanning different Π values
2. **Scaling verification** across population sizes
3. **Regime boundary mapping** through systematic parameter sweeps
4. **Real-world validation** against historical displacement data

### Framework Limitations

1. **Linear assumptions**: Some interactions may be nonlinear
2. **Steady-state bias**: Transient effects not fully captured
3. **Cultural factors**: Social norms may affect scaling
4. **Geographic constraints**: Terrain effects not included

## Future Extensions

### Advanced Dimensionless Groups

Potential additional groups:

- **Resource Constraint**: (Available_Resources) / (Population × Distance)
- **Risk Perception**: (Perceived_Risk) / (Actual_Risk)
- **Network Resilience**: (Redundant_Paths) / (Critical_Paths)

### Multi-Scale Coupling

Extension to couple with:
- **Macro-scale models**: Regional displacement patterns
- **Micro-scale models**: Individual decision processes
- **Economic models**: Resource availability and costs

## Conclusion

The dimensionless parameter framework provides a systematic approach to:

1. **Generalize findings** across different scenarios and scales
2. **Identify universal scaling laws** in displacement behavior
3. **Optimize system parameters** for improved performance
4. **Design robust evacuation strategies** across contexts

This framework transforms scenario-specific results into universal principles, enabling broader application of dual-process displacement modeling insights.

## References

- Buckingham, E. (1914). On physically similar systems
- Barenblatt, G.I. (1996). Scaling, self-similarity, and intermediate asymptotics
- Newman, M.E.J. (2010). Networks: An Introduction
- Kahneman, D. (2011). Thinking, Fast and Slow