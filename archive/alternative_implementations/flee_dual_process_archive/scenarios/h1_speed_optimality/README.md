# H1: Speed vs Optimality Testing Scenarios

## Overview

This directory contains scenarios designed to test Hypothesis 1 of dual-process theory in refugee movement: **System 1 (fast, heuristic) vs System 2 (slow, deliberative) decision-making trade-offs between speed and optimality**.

## Scenarios

### H1.1: Multi-Destination Choice
**Directory**: `h1_1_multi_destination/`

Tests decision quality when agents must choose between multiple destinations with different trade-offs:
- **Camp_A**: Closest (50km), highest safety (0.9), smallest capacity (3,000)
- **Camp_B**: Medium distance (75km), medium safety (0.8), medium capacity (5,000)
- **Camp_C**: Farthest (100km), lowest safety (0.7), largest capacity (8,000)

**Key Question**: Do S1 agents prioritize speed (choose closest camp) while S2 agents optimize for better long-term outcomes?

### H1.2: Time Pressure Cascade  
**Directory**: `h1_2_time_pressure_cascade/`

Tests temporal decision-making under cascading conflict pressure:
- Sequential conflicts across Town_A → Town_B → Town_C → Town_D (5-day intervals)
- Tests anticipatory vs reactive evacuation behavior
- Measures response to predictable threat patterns

**Key Question**: Do S2 agents show anticipatory evacuation while S1 agents react only to immediate threats?

## Expected Findings

### System 1 (Fast) Characteristics
- Quick evacuation decisions
- Preference for closest/most obvious options
- Reactive responses to immediate threats
- Less consideration of long-term trade-offs

### System 2 (Deliberative) Characteristics  
- More delayed but optimized decisions
- Better evaluation of complex trade-offs
- Anticipatory responses to future threats
- Higher overall decision quality

## Analysis Tools

Each scenario includes specialized metrics:
- **H1.1**: Decision quality index (speed + efficiency + safety)
- **H1.2**: Temporal pressure index (anticipation + cascade response + evacuation rate)

## Usage

```python
# Analyze H1.1 results
from h1_1_multi_destination.h1_1_metrics import analyze_h1_1_scenario
results_h1_1 = analyze_h1_1_scenario('/path/to/h1_1/output')

# Analyze H1.2 results  
from h1_2_time_pressure_cascade.h1_2_metrics import analyze_h1_2_scenario
results_h1_2 = analyze_h1_2_scenario('/path/to/h1_2/output')
```

## Integration with Dual-Process Framework

These scenarios are designed to work with the flee_dual_process cognitive modeling framework:
- Configure different cognitive modes (S1-only, S2-disconnected, S2-full, dual-process)
- Run parameter sweeps across cognitive configurations
- Compare decision quality metrics between cognitive modes
- Validate theoretical predictions about speed vs optimality trade-offs