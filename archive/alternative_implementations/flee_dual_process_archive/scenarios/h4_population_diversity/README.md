# H4: Population Diversity Scenarios

## Overview

This directory contains scenarios designed to test Hypothesis 4 of dual-process theory in refugee movement: **Mixed S1/S2 populations achieve better collective outcomes than homogeneous populations through complementary cognitive strategies**.

## Scenarios

### H4.1: Adaptive Shock Response
**Directory**: `h4_1_adaptive_shock/`

Tests population resilience to unexpected changes through dynamic event timeline:
- **Initial Conflict**: Standard conflict at Origin (day 0-30)
- **Route Closure**: Main evacuation route blocked (day 15)
- **Camp Full**: Primary destination reaches capacity (day 25)
- **New Camp**: Alternative destination opens (day 30)

**Population Compositions**:
- **pure_s1**: 100% System 1 agents (fast, reactive)
- **pure_s2**: 100% System 2 agents (slow, deliberative)
- **balanced**: 50% S1, 50% S2 agents
- **realistic**: 70% S1, 30% S2 agents (based on cognitive psychology research)

**Key Question**: Do mixed populations show better adaptation to unexpected changes than homogeneous populations?

### H4.2: Information Cascade Test
**Directory**: `h4_2_information_cascade/`

Tests information flow and decision correlation between agent types:
- **S1 "Scouts"**: Fast-moving agents who discover new destinations first
- **S2 "Followers"**: Deliberative agents who benefit from scout information
- **Information Flow**: Tracking how S1 discoveries influence S2 choices
- **Time Lag Analysis**: Measuring delay between S1 discovery and S2 adoption

**Key Question**: Do S1 agents serve as "scouts" whose discoveries benefit S2 "followers" in mixed populations?

## Expected Findings

### Pure S1 Population Characteristics
- Fast initial response to conflict
- Poor adaptation to unexpected changes
- Limited information sharing and learning
- Suboptimal collective outcomes

### Pure S2 Population Characteristics
- Slow initial response but better planning
- Good adaptation once information is processed
- Effective information sharing within connected networks
- Better individual decisions but slower collective response

### Mixed Population Advantages
- **Complementary Strengths**: S1 speed + S2 optimization
- **Information Cascades**: S1 scouts discover, S2 followers optimize
- **Adaptive Resilience**: Better response to unexpected shocks
- **Collective Intelligence**: Population-level learning and adaptation

## Analysis Tools

Each scenario includes specialized metrics:
- **H4.1**: Resilience index (adaptation speed + recovery rate + collective efficiency)
- **H4.2**: Information cascade metrics (discovery rate + adoption lag + correlation analysis)

## Usage

```python
# Analyze H4.1 results
from h4_1_adaptive_shock.h4_1_metrics import analyze_adaptive_shock
results_h4_1 = analyze_adaptive_shock('/path/to/h4_1/output')

# Analyze H4.2 results
from h4_2_information_cascade.h4_2_metrics import analyze_information_cascade
results_h4_2 = analyze_information_cascade('/path/to/h4_2/output')
```

## Integration with Dual-Process Framework

These scenarios are designed to work with the flee_dual_process cognitive modeling framework:
- Configure different population compositions (pure_s1, pure_s2, balanced, realistic)
- Run parameter sweeps across population diversity levels
- Compare collective performance metrics between population types
- Validate theoretical predictions about diversity advantages in complex adaptive systems