# H3: Dimensionless Parameter Testing Scenarios

This directory contains scenarios for testing Hypothesis 3: Dimensionless parameter scaling laws govern cognitive mode transitions.

## Scenarios

### H3.1: Parameter Grid Search
- Systematic exploration of conflict_intensity × recovery_period × connectivity_rate parameter space
- 175 parameter combinations testing cognitive_pressure scaling
- Phase transition detection for S2 activation threshold

### H3.2: Phase Transition Identification  
- 50 scenarios with cognitive_pressure values from 0 to 2
- Critical point detection with sigmoid fitting
- Phase diagram visualization and analysis

## Key Concepts

**Cognitive Pressure**: The dimensionless parameter that governs S1/S2 transitions:
```
cognitive_pressure = (conflict_intensity × connectivity_rate) / (recovery_period / 30.0)
```

**Phase Transition**: The critical cognitive_pressure value where agents transition from predominantly S1 to S2 decision-making.