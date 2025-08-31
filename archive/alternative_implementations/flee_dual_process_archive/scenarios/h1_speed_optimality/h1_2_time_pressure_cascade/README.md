# H1.2 Time Pressure Cascade Scenario

## Overview

This scenario tests Hypothesis 1 (Speed vs Optimality) by creating a cascading conflict that moves sequentially through connected towns, creating temporal pressure for evacuation decisions. The scenario is designed to distinguish between System 1 (immediate response) and System 2 (anticipatory planning) decision-making under time pressure.

## Network Structure

### Towns (Sequential Conflict Path)
- **Town_A**: Western starting point (8,000 population) - First conflict at day 0
- **Town_B**: Central-West (6,000 population) - Conflict at day 5  
- **Town_C**: Central-East (4,000 population) - Conflict at day 10
- **Town_D**: Eastern endpoint (2,000 population) - Conflict at day 15

### Safe Destinations
- **Safe_Camp_North**: Northern refuge (15,000 capacity)
- **Safe_Camp_South**: Southern refuge (15,000 capacity)

## Conflict Timeline (Cascading Pattern)

### Initial Wave (Days 0-15)
- **Day 0**: Town_A conflict begins (intensity 0.8)
- **Day 5**: Town_B conflict begins (intensity 0.8) 
- **Day 10**: Town_C conflict begins (intensity 0.8)
- **Day 15**: Town_D conflict begins (intensity 0.8)

### Escalation Wave (Days 20-35)
- **Day 20**: Town_A conflict escalates (intensity 1.0)
- **Day 25**: Town_B conflict escalates (intensity 1.0)
- **Day 30**: Town_C conflict escalates (intensity 1.0)
- **Day 35**: Town_D conflict escalates (intensity 1.0)

## Expected Cognitive Differences

### System 1 (Immediate Response) Agents
- React only when conflict directly affects their current location
- Immediate evacuation upon conflict onset
- No anticipatory movement based on conflict patterns
- Focus on nearest available safe destination

### System 2 (Anticipatory Planning) Agents
- Recognize cascading conflict pattern early
- Evacuate before conflict reaches their location
- Consider future conflict spread when making decisions
- May choose optimal evacuation routes and timing

## Key Metrics

1. **Evacuation Timing**: When each town begins evacuating relative to conflict onset
2. **Anticipatory Behavior**: Evidence of forward-looking evacuation decisions
3. **Cascade Response Quality**: Effectiveness of responses to sequential threats
4. **Temporal Pressure Index**: Composite measure of time-sensitive decision quality

## Response Categories

- **Anticipatory**: Evacuation before/during initial conflict onset
- **Immediate**: Evacuation within 2 days of local conflict
- **Delayed**: Evacuation before conflict escalation
- **Crisis**: Evacuation only after conflict escalation

## Usage

```python
from h1_2_metrics import analyze_h1_2_scenario

# Analyze simulation results
results = analyze_h1_2_scenario('/path/to/simulation/output')
print(f"Temporal Pressure Index: {results['temporal_pressure_index']}")
print(f"Anticipatory Score: {results['anticipatory_score']}")
```

## Files

- `locations.csv`: Sequential town network with safe camps
- `routes.csv`: Connections between towns and evacuation routes
- `conflicts.csv`: Cascading conflict timeline across all towns
- `sim_period.csv`: 100-day simulation period
- `closures.csv`: No route closures (empty)
- `h1_2_metrics.py`: Analysis tools for temporal pressure measurement