# H3.1: Parameter Grid Search Scenario

## Overview

This scenario implements a systematic parameter grid search to test the dimensionless parameter scaling hypothesis. It explores the three-dimensional parameter space of conflict_intensity × recovery_period × connectivity_rate to identify phase transitions in cognitive mode activation.

## Parameter Grid

- **Conflict Intensity**: [0.1, 0.3, 0.5, 0.7, 0.9] (5 values)
- **Recovery Period**: [10, 20, 30, 40, 50] days (5 values) 
- **Connectivity Rate**: [0.0, 2.0, 4.0, 6.0, 8.0] (5 values)
- **Total Combinations**: 5³ = 125 base combinations
- **Additional Edge Cases**: 50 combinations near predicted phase boundaries
- **Total Experiments**: 175 parameter combinations

## Cognitive Pressure Calculation

```python
cognitive_pressure = (conflict_intensity × connectivity_rate) / (recovery_period / 30.0)
```

This dimensionless parameter is hypothesized to govern the S1→S2 transition threshold.

## Expected Outcomes

- **Low cognitive_pressure (< 0.5)**: Predominantly S1 decision-making
- **Medium cognitive_pressure (0.5-1.5)**: Mixed S1/S2 with gradual transition
- **High cognitive_pressure (> 1.5)**: Predominantly S2 decision-making

## Network Topology

Simple linear topology: Origin → Hub → Camp_A/B/C
- Tests parameter effects without confounding network complexity
- Allows clear measurement of decision quality vs speed trade-offs

## Metrics

- S2 activation rate vs cognitive_pressure
- Decision timing (speed) vs decision quality (optimality)
- Phase transition detection and critical point identification