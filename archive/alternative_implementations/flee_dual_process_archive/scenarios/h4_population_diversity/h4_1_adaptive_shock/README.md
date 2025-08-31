# H4.1: Adaptive Shock Response Scenario

## Overview

This scenario tests **Hypothesis 4.1**: Mixed S1/S2 populations show better adaptation to unexpected changes than homogeneous populations through complementary cognitive strategies.

## Scenario Design

### Dynamic Event Timeline

The scenario implements a series of unexpected shocks to test population resilience:

1. **Day 0-30**: Initial conflict escalation at Origin
2. **Day 15-35**: Main evacuation route unexpectedly blocked
3. **Day 25-45**: Primary destination reaches capacity
4. **Day 30-45**: New alternative destination opens
5. **Day 35-45**: Original route reopens with improved capacity

### Network Topology

```
Origin (50k pop) → Hub (10k pop) → Primary_Camp (8k capacity)
     ↓                    ↓
Backup_Town (15k pop) → Alternative_Camp (5k capacity)
```

### Population Compositions

- **pure_s1**: 100% System 1 agents (fast, reactive)
- **pure_s2**: 100% System 2 agents (slow, deliberative)  
- **balanced**: 50% S1, 50% S2 agents
- **realistic**: 70% S1, 30% S2 agents (research-based)

## Expected Outcomes

### Pure S1 Population
- **Strengths**: Fast initial evacuation response
- **Weaknesses**: Poor adaptation to route closure, overcrowding at blocked routes
- **Shock Response**: Reactive, may create bottlenecks

### Pure S2 Population  
- **Strengths**: Good adaptation once information is processed
- **Weaknesses**: Slow initial response, may miss early evacuation window
- **Shock Response**: Systematic but delayed

### Mixed Populations (Balanced/Realistic)
- **Strengths**: S1 provides rapid scouting, S2 provides optimization
- **Advantages**: Information cascades, complementary decision-making
- **Shock Response**: Adaptive and resilient

## Key Metrics

### Resilience Index Components
1. **Adaptation Speed**: Time to respond to unexpected changes
2. **Recovery Rate**: Speed of population recovery after shocks  
3. **Collective Efficiency**: Overall movement efficiency
4. **Information Flow Rate**: Rate of information sharing

### Shock-Specific Metrics
- **Route Closure Response**: Time to find alternative routes
- **Capacity Crisis Response**: Efficiency of redirection to alternatives
- **Recovery Utilization**: Adoption rate of new opportunities

## Usage

### Generate Scenario
```python
from h4_1_adaptive_shock import AdaptiveShockScenario

scenario = AdaptiveShockScenario()
files = scenario.create_scenario(
    output_dir="./h4_1_output",
    population_composition="balanced",
    shock_intensity=0.8
)
```

### Analyze Results
```python
from h4_1_adaptive_shock.resilience_metrics import analyze_h4_1_scenario

results = analyze_h4_1_scenario(
    output_dir="./h4_1_output",
    population_composition="balanced"
)

print(f"Resilience Index: {results.resilience_index:.3f}")
print(f"Adaptation Speed: {results.adaptation_speed:.3f}")
print(f"Recovery Rate: {results.recovery_rate:.3f}")
```

### Compare Populations
```python
from h4_1_adaptive_shock.resilience_metrics import compare_population_resilience

# Run scenarios for all population types
results = {}
for pop_type in ["pure_s1", "pure_s2", "balanced", "realistic"]:
    results[pop_type] = analyze_h4_1_scenario(f"./h4_1_{pop_type}", pop_type)

comparison = compare_population_resilience(results)
print(comparison['insights'])
```

## Files Generated

- **locations.csv**: Network topology with Origin, Hub, camps, and backup town
- **routes.csv**: Connections between locations with distances
- **conflicts.csv**: Escalating conflict intensity at Origin
- **closures.csv**: Dynamic route closures and reopenings
- **population_config.yml**: Population composition configuration
- **sim_period.csv**: 45-day simulation period
- **scenario_metadata.yml**: Complete scenario documentation

## Integration with FLEE

This scenario integrates with the flee_dual_process framework:

1. **Cognitive Modeling**: Uses enhanced Person class with cognitive state tracking
2. **Population Configuration**: Configures agent ratios and cognitive parameters
3. **Event Processing**: Handles dynamic events through FLEE's event system
4. **Output Analysis**: Generates cognitive tracking and decision logs

## Validation

The scenario validates H4 predictions:

- **H4.1a**: Mixed populations show faster adaptation to shocks than pure populations
- **H4.1b**: Balanced populations achieve higher collective efficiency
- **H4.1c**: Information cascades in mixed populations improve overall outcomes
- **H4.1d**: Realistic populations (70% S1, 30% S2) show optimal resilience

## Research Applications

This scenario enables research into:

- Population diversity effects in crisis response
- Complementary cognitive strategies in adaptive systems
- Information cascade dynamics in mixed populations
- Resilience engineering for humanitarian systems