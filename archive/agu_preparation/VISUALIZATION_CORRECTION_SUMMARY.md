# Visualization Correction Summary

## Problems Identified

1. ❌ **Conceptual Error**: Visualization showed agents as "S1 agents" vs "S2 agents" based on location, but agents make S1/S2 **decisions** at each timestep, not fixed states
2. ❌ **Individual Agents Not Visible**: Couldn't see individual agents - they were overlapping or too small
3. ❌ **Wrong S1/S2 Classification**: Used location as proxy instead of actual decision state
4. ❌ **No Flocking Visualization**: Can't see S1 flocking behavior without seeing individual agents

## Fixes Implemented

### 1. Correct S1/S2 State Tracking
- **Before**: Classified agents by location (Facility/Ring1 = S1, others = S2)
- **After**: Uses actual `agent.cognitive_state` from simulation
- **Key**: Each agent's decision state is tracked per timestep in `agent_s2_states_by_time`

### 2. Individual Agent Visibility
- **Small random offsets**: Agents at same location get small random offsets (±3 units) so all are visible
- **One marker per agent**: Each of the 100 agents gets its own marker
- **Size**: 100 pixels per agent (visible but not overwhelming)

### 3. Correct Color Coding
- **Red circles (○)**: Agents currently making S1 decisions (reactive/flocking)
- **Green squares (□)**: Agents currently making S2 decisions (deliberative/individual)
- **Dynamic**: Agent color changes based on their current decision state at each timestep

### 4. Agent State Data Structure
```python
agent_s2_states_by_time[t] = {
    'agent_0': {
        's2_active': bool,
        'x': float,  # Location x + small random offset
        'y': float,  # Location y + small random offset
        'location': str,
        'cognitive_state': 'S1' or 'S2',  # ACTUAL decision state
        'agent_index': int
    },
    ...
}
```

## Current Simulation Parameters

- **Number of agents**: 100 (default)
- **Timesteps**: 30
- **Topologies**: Ring, Star, Linear

## What You Should See Now

1. **100 individual agents**: Each agent has its own marker
2. **Dynamic S1/S2 states**: Agent colors change based on their current decision state
3. **S1 flocking potential**: Red agents (S1) should cluster together (though with 100 agents, this may be subtle)
4. **Network structure**: Topology clearly visible with routes and locations

## Recommendations for Better Flocking Visualization

### Option 1: Increase Agent Count
```python
# In nuclear_evacuation_simulations.py, line 565
simulator.run_all_topologies(num_agents=1000, num_timesteps=30)  # or 10000
```

**Pros**: More agents = clearer flocking patterns
**Cons**: Larger files, slower simulation

### Option 2: Add Flocking Metrics
- Calculate agent density/clustering for S1 agents
- Show density heatmap overlay
- Track average distance between S1 agents vs S2 agents

### Option 3: Enhanced Visualization
- Use smaller markers for many agents (size scales with agent count)
- Add transparency/alpha blending to show density
- Show agent trajectories (paths over time)

## Files Created

1. `visualize_agent_movements_corrected.py` - Corrected visualization script
2. Updated `nuclear_evacuation_simulations.py` - Tracks actual cognitive_state with offsets

## Usage

```bash
# Run simulations (100 agents default)
python3 nuclear_evacuation_simulations.py

# Create corrected animations
python3 visualize_agent_movements_corrected.py nuclear_evacuation_results

# For more agents (better flocking):
# Edit nuclear_evacuation_simulations.py line 565:
# simulator.run_all_topologies(num_agents=1000, num_timesteps=30)
```

## Next Steps

1. **Test with more agents**: Try 1000 or 10000 agents to see clearer flocking
2. **Add flocking metrics**: Calculate clustering coefficient for S1 agents
3. **Trajectory visualization**: Show agent paths over time
4. **Density visualization**: Heatmap showing where S1 vs S2 agents cluster

