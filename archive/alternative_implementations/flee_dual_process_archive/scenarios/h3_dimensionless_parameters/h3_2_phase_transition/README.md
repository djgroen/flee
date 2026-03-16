# H3.2: Phase Transition Identification Scenario

## Overview

This scenario implements focused phase transition identification by generating 50 scenarios with cognitive_pressure values systematically distributed from 0 to 2. The goal is to precisely identify the critical point where agents transition from predominantly S1 to S2 decision-making.

## Approach

Unlike H3.1's broad parameter grid, H3.2 uses a targeted approach:

1. **Fixed Cognitive Pressure Range**: 50 scenarios with cognitive_pressure from 0 to 2
2. **Parameter Combination Generation**: For each target pressure, generate valid parameter combinations
3. **Critical Point Detection**: Use sigmoid fitting to identify the precise transition point
4. **Phase Diagram Creation**: Visualize the phase transition with high resolution

## Cognitive Pressure Distribution

- **Range**: 0.0 to 2.0 (50 evenly spaced values)
- **Step Size**: 0.04 cognitive pressure units
- **Focus Areas**: 
  - Low pressure (0.0-0.5): Predominantly S1 behavior
  - Transition zone (0.5-1.5): Mixed S1/S2 with critical point
  - High pressure (1.5-2.0): Predominantly S2 behavior

## Parameter Generation Strategy

For each target cognitive_pressure value, generate parameter combinations using:

```python
cognitive_pressure = (conflict_intensity × connectivity_rate) / (recovery_period / 30.0)
```

**Strategy**:
1. Select base conflict_intensity and connectivity_rate values
2. Calculate required recovery_period for target cognitive_pressure
3. Ensure parameters are within realistic ranges
4. Generate multiple combinations per pressure value for robustness

## Expected Phase Transition

Based on dual-process theory, we expect:
- **Critical Point**: Around cognitive_pressure = 1.0-1.2
- **Transition Width**: Sharp transition over ~0.2-0.4 pressure units
- **Sigmoid Shape**: S-curve with clear inflection point

## Analysis Methods

1. **Sigmoid Fitting**: Fit sigmoid curve to identify critical point
2. **Derivative Analysis**: Find steepest slope point
3. **Statistical Significance**: Test for significant difference across critical point
4. **Confidence Intervals**: Quantify uncertainty in critical point estimate

## Validation Criteria

- **R² > 0.8**: Good sigmoid fit quality
- **Effect Size > 0.8**: Large effect size across critical point
- **p < 0.001**: Highly significant transition
- **Narrow CI**: Critical point confidence interval < 0.2 pressure units