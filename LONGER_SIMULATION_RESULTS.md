# Longer Simulation Results (60 Timesteps)

## Summary

Ran simulations with 60 timesteps (doubled from 30) to see if more agents would reach safe zones.

## Results Comparison: 30 vs 60 Timesteps

| Topology | Timesteps | Final S2 Rate | Agents at Safe | Safe Zone % |
|----------|-----------|---------------|----------------|-------------|
| **Ring** | 30 | 90.0% | 158 | 15.8% |
| **Ring** | 60 | 99.1% | 164 | 16.4% |
| **Star** | 30 | 92.0% | 273 | 27.3% |
| **Star** | 60 | 91.2% | 224 | 22.4% |
| **Linear** | 30 | 95.9% | 181 | 18.1% |
| **Linear** | 60 | 99.2% | 172 | 17.2% |

## Key Findings

### 1. S2 Activation Rates Improved
- **Ring**: 90.0% → 99.1% (+9.1 percentage points)
- **Linear**: 95.9% → 99.2% (+3.3 percentage points)
- **Star**: Slight decrease (92.0% → 91.2%), but still high

**Interpretation**: With more time, agents gain more experience and activate S2 more frequently. This aligns with the model: experience increases over time → higher cognitive capacity (Ψ) → higher S2 activation.

### 2. Safe Zone Occupancy
- **Ring**: Slight increase (15.8% → 16.4%)
- **Star**: Decrease (27.3% → 22.4%)
- **Linear**: Slight decrease (18.1% → 17.2%)

**Observation**: Longer simulations did NOT significantly increase safe zone occupancy. In fact, Star and Linear showed decreases.

### 3. Possible Explanations

**Why safe zones aren't filling more:**
1. **Agents can leave safe zones**: Even though `camp_movechance=0.001` (0.1% chance), over 60 timesteps, some agents may leave
2. **Agents stuck at intermediate locations**: Some agents may be getting stuck at locations between Facility and safe zones
3. **Route distances**: Long route distances (100-200 units) may require more than 60 timesteps to traverse
4. **Population dynamics**: Agents may be oscillating between locations rather than settling in safe zones

**Why S2 rates increased:**
- Experience increases over time (`timesteps_since_departure` increments)
- Higher experience → higher cognitive capacity (Ψ) → higher S2 activation probability
- This is expected behavior from the model

## Recommendations

1. **Check agent distribution**: Analyze where agents are at the end of simulations
2. **Reduce route distances**: Make paths to safe zones shorter
3. **Increase safe zone movechance penalty**: Consider making safe zones even more attractive (though 0.001 is already very low)
4. **Monitor agent trajectories**: Use agent logs to see if agents are oscillating or getting stuck

## Files Generated

- **Results**: `nuclear_evacuation_detailed_20251126_112939.json` (60 timesteps)
- **Visualizations**: All 8 aggregate figures updated with latest results
- **Input files**: Saved in `run_*` directories for reproducibility

## Command to Run Longer Simulations

```bash
python3 nuclear_evacuation_simulations.py --decision-rich --longer
```

This runs simulations with 60 timesteps instead of the default 30.

