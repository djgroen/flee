# H1.1 Multi-Destination Choice Scenario

## Overview

This scenario tests Hypothesis 1 (Speed vs Optimality) by presenting agents with multiple destination choices that involve trade-offs between distance, capacity, and safety. The scenario is designed to reveal differences between System 1 (fast, heuristic) and System 2 (slow, deliberative) decision-making processes.

## Network Structure

- **Origin**: Starting location with 10,000 population, experiences escalating conflict
- **Hub**: Intermediate waypoint (5,000 capacity) connecting to all camps
- **Camp_A**: Closest option (50km from Hub), highest safety (0.9), smallest capacity (3,000)
- **Camp_B**: Medium distance (75km), medium safety (0.8), medium capacity (5,000)  
- **Camp_C**: Farthest option (100km), lowest safety (0.7), largest capacity (8,000)

## Conflict Timeline

- **Day 0**: Initial conflict intensity 0.3 at Origin
- **Day 30**: Escalation to intensity 0.6 at Origin
- **Day 180**: Peak conflict intensity 1.0 at Origin

## Expected Cognitive Differences

### System 1 (Fast) Agents
- Quick evacuation decisions (early movement)
- Preference for closest option (Camp_A) regardless of capacity constraints
- Less consideration of long-term safety/capacity trade-offs

### System 2 (Deliberative) Agents  
- More delayed but optimized evacuation decisions
- Better evaluation of distance vs capacity vs safety trade-offs
- More likely to choose Camp_B or Camp_C for better overall outcomes

## Key Metrics

1. **Time to Move**: Speed of evacuation response
2. **Camp Efficiency**: Quality of destination choices (capacity utilization vs distance)
3. **Average Safety Achieved**: Weighted safety outcomes based on final destinations
4. **Decision Quality Index**: Composite measure combining speed, efficiency, and safety

## Usage

```python
from h1_1_metrics import analyze_h1_1_scenario

# Analyze simulation results
results = analyze_h1_1_scenario('/path/to/simulation/output')
print(f"Decision Quality Index: {results['decision_quality_index']}")
```

## Files

- `locations.csv`: Network topology with camp properties
- `routes.csv`: Distance matrix between locations  
- `conflicts.csv`: Escalating conflict timeline at Origin
- `sim_period.csv`: 200-day simulation period
- `closures.csv`: No route closures (empty)
- `h1_1_metrics.py`: Analysis tools for decision quality measurement