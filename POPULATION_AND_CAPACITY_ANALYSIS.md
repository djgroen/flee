# Population and Capacity Analysis

## Summary

Generated aggregate plots showing population distribution by location type and capacity information.

## Capacity Settings

| Topology | Camp Locations | Capacity per Camp | Total Camp Capacity | Town Capacity |
|----------|---------------|-------------------|---------------------|---------------|
| **Ring** | 3 | 10,000 | 30,000 | Unlimited |
| **Star** | 6 | 5,000 | 30,000 | Unlimited |
| **Linear** | 1 | 10,000 | 10,000 | Unlimited |

**Note**: Towns have unlimited capacity (`capacity=-1`), which means they can hold any number of agents.

## Final Population Distribution

### Ring Topology
- **Camps**: 152 agents (15.2%) - Utilization: 0.5%
- **Towns**: 845 agents (84.5%)
- **Conflict**: 3 agents (0.3%)

### Star Topology
- **Camps**: 242 agents (24.2%) - Utilization: 0.8%
- **Towns**: 682 agents (68.2%)
- **Conflict**: 76 agents (7.6%)

### Linear Topology
- **Camps**: 188 agents (18.8%) - Utilization: 1.9%
- **Towns**: 809 agents (80.9%)
- **Conflict**: 3 agents (0.3%)

## Key Observation

**Towns have HIGHER population than camps in all topologies!**

This is unexpected - we would expect more agents to accumulate in safe zones (camps) than in intermediate locations (towns).

### Possible Explanations

1. **Route distances too long**: Agents may not have enough time (30 timesteps) to complete the journey from Facility → Towns → Safe Zones
2. **Agents pausing at towns**: Towns have `movechance=0.3` (30% chance per timestep), so agents may pause there
3. **Agents getting stuck**: Some agents may be stuck at intermediate locations due to routing issues
4. **Agents oscillating**: Agents may be moving back and forth between locations rather than settling in safe zones
5. **Safe zones not attractive enough**: Even though `camp_movechance=0.001` (very low), agents may still be leaving or not reaching them

### Capacity Utilization

- **Ring**: 152 / 30,000 = 0.5% utilization (plenty of space)
- **Star**: 242 / 30,000 = 0.8% utilization (plenty of space)
- **Linear**: 188 / 10,000 = 1.9% utilization (plenty of space)

**Capacity is NOT the limiting factor** - there's plenty of space in safe zones.

## Generated Plots

1. **nuclear_evacuation_population_by_type.png**
   - Shows population in camps, towns, and conflict zones over time
   - Three subplots (one per location type)
   - Allows comparison across topologies

2. **nuclear_evacuation_capacity_and_population.png**
   - Top row: Capacity by location type for each topology
   - Bottom row: Final population by location type for each topology
   - Side-by-side comparison of capacity vs actual population

## Recommendations

1. **Increase timesteps**: Try 60-90 timesteps to give agents more time to reach safe zones
2. **Reduce route distances**: Make paths to safe zones shorter
3. **Increase town movechance**: Consider increasing `default_movechance` from 0.3 to 0.5-0.7 to reduce pausing
4. **Analyze agent trajectories**: Check agent logs to see where agents are getting stuck
5. **Check routing logic**: Verify that agents can find routes to safe zones

## Files Generated

- `nuclear_evacuation_population_by_type.png` - Temporal population by type
- `nuclear_evacuation_capacity_and_population.png` - Capacity and population comparison
- All other aggregate plots regenerated with latest data


