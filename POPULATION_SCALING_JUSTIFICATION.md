# Population Scaling Justification for S1/S2 Experiments

## Research Question

How does population density affect S1/S2 dual-process decision-making in refugee movement models?

## Experimental Design Rationale

### Primary Approach: Constant Density per Node

**Population Scaling**: 5 agents per node
- Network Size 5: 25 agents
- Network Size 7: 35 agents
- Network Size 11: 55 agents

**Justification**:
1. **Theoretical Consistency**: Maintains constant decision-making complexity per node
2. **Literature Standard**: Common approach in network analysis and agent-based modeling
3. **Interpretability**: Easy to understand and compare across network sizes
4. **Realistic Scaling**: Reflects how populations might grow with network size

### Sensitivity Analysis: Multiple Scaling Approaches

To demonstrate robustness, we test three additional scaling approaches:

1. **Constant Total Population** (50 agents): Controls for total system size
2. **Scaled by Connections** (4 agents/connection): Scales with network connectivity
3. **Logarithmic Scaling** (20 * log(n)): Reflects complex system scaling

## Theoretical Framework

### Population Density Effects on Decision-Making

1. **Cognitive Load**: Higher density increases decision complexity
2. **Social Influence**: More agents per node increases social pressure
3. **Resource Competition**: Higher density increases resource scarcity
4. **Information Flow**: Density affects information transmission

### S1/S2 System Implications

1. **System 1 (Reactive)**: May be more effective in high-density, fast-moving situations
2. **System 2 (Deliberative)**: May be more effective in low-density, complex situations
3. **Switching Threshold**: May depend on local population density

## Experimental Controls

### Consistent Initialization
- All agents start at the same origin location
- Same random seed for reproducibility
- Identical network topologies (only size varies)

### Parameter Control
- Only population size varies between network sizes
- All other parameters held constant
- S2 threshold parameters consistent across experiments

## Statistical Analysis Plan

### Primary Analysis
- Compare S1/S2 scenarios across network sizes with constant density
- Test for main effects of network size and S2 threshold
- Test for interaction effects between network size and S2 threshold

### Sensitivity Analysis
- Repeat analysis with different population scaling approaches
- Test robustness of conclusions across scaling methods
- Report effect sizes and confidence intervals

## Expected Outcomes

### Hypothesis 1: Population Density Effects
- **Null**: Population density has no effect on S1/S2 behavior
- **Alternative**: Higher density increases S2 activation (more complex decisions)

### Hypothesis 2: Network Size Effects
- **Null**: Network size has no effect on S1/S2 behavior
- **Alternative**: Larger networks show different S1/S2 patterns

### Hypothesis 3: Scaling Robustness
- **Null**: Results depend on population scaling method
- **Alternative**: Results are robust across different scaling approaches

## Limitations and Future Work

1. **Fixed Density**: Real-world density may vary spatially
2. **Homogeneous Agents**: All agents have same cognitive parameters
3. **Static Networks**: Network structure doesn't change over time
4. **Future**: Test with heterogeneous agents and dynamic networks

## Conclusion

The constant density per node approach provides a rigorous, interpretable, and theoretically justified method for scaling population across network sizes in S1/S2 dual-process experiments. The inclusion of sensitivity analysis with multiple scaling approaches demonstrates robustness and provides comprehensive evidence for reviewers.
