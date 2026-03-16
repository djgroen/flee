# Individual Movement Visualization Ideas

## Problem
With 1000 agents, showing individual movements can become cluttered and hard to interpret. We need ways to visualize individual agent trajectories without overwhelming the visualization.

## Current Approach
- All agents shown as individual markers
- Small random offsets to prevent overlap
- Color coding by S1/S2 state or experience level
- Population counters at safe zones

## Proposed Solutions

### Option 1: Agent Trails (Recommended)
**Concept**: Show recent path history for each agent as a fading trail.

**Implementation**:
- Store last N positions (e.g., 5-10 timesteps) for each agent
- Draw lines connecting recent positions
- Fade trail opacity: most recent = 1.0, older = 0.2
- Use agent's current color for trail

**Pros**:
- Shows direction of movement
- Indicates speed (longer trails = faster movement)
- Can see flocking vs individual paths
- Not too cluttered if limited to recent history

**Cons**:
- Can still be cluttered with 1000 agents
- Requires storing position history

**Code Example**:
```python
# Store agent trails
agent_trails = {}  # agent_id -> list of (x, y, t) tuples

# In animate function:
for agent_id, state in t_states.items():
    x, y = state.get('x', 0.0), state.get('y', 0.0)
    
    # Add to trail
    if agent_id not in agent_trails:
        agent_trails[agent_id] = []
    agent_trails[agent_id].append((x, y, t))
    
    # Keep only last 5 positions
    if len(agent_trails[agent_id]) > 5:
        agent_trails[agent_id].pop(0)
    
    # Draw trail with fading opacity
    trail = agent_trails[agent_id]
    for i, (tx, ty, tt) in enumerate(trail[:-1]):
        alpha = 0.2 + 0.8 * (i / len(trail))
        ax.plot([tx, trail[i+1][0]], [ty, trail[i+1][1]], 
               color=agent_color, alpha=alpha, linewidth=1, zorder=5)
```

---

### Option 2: Movement Arrows
**Concept**: Show direction of movement with small arrows.

**Implementation**:
- Calculate velocity vector from previous position
- Draw arrow in direction of movement
- Arrow size proportional to speed
- Only show arrows for agents that moved recently

**Pros**:
- Clear indication of movement direction
- Can see flow patterns
- Less cluttered than full trails

**Cons**:
- Requires velocity calculation
- Arrows can overlap
- Doesn't show path history

**Code Example**:
```python
# Store previous positions
prev_positions = {}  # agent_id -> (x, y)

# In animate function:
for agent_id, state in t_states.items():
    x, y = state.get('x', 0.0), state.get('y', 0.0)
    
    if agent_id in prev_positions:
        px, py = prev_positions[agent_id]
        dx, dy = x - px, y - py
        speed = np.sqrt(dx**2 + dy**2)
        
        # Only show arrow if agent moved significantly
        if speed > 1.0:
            ax.arrow(px, py, dx, dy, head_width=3, head_length=2,
                    fc=agent_color, ec=agent_color, alpha=0.6, zorder=6)
    
    prev_positions[agent_id] = (x, y)
```

---

### Option 3: Selective Visualization
**Concept**: Only show agents that moved recently or are in interesting states.

**Implementation**:
- Track which agents moved in last N timesteps
- Only visualize agents that:
  - Moved recently (active agents)
  - Are at safe zones (destination reached)
  - Are in S2 state (deliberative decisions)
  - Are at conflict zones (danger)

**Pros**:
- Reduces clutter significantly
- Focuses on interesting behaviors
- Can toggle different filters

**Cons**:
- Doesn't show all agents
- May miss important patterns
- Requires filtering logic

**Code Example**:
```python
# Track movement history
agent_moved = {}  # agent_id -> last_move_timestep

# In animate function:
active_agents = []
for agent_id, state in t_states.items():
    # Filter: only show agents that moved in last 3 timesteps
    last_move = agent_moved.get(agent_id, -1)
    if t - last_move <= 3:
        active_agents.append((agent_id, state))
    
    # Or filter by state
    if state.get('cognitive_state') == 'S2':
        active_agents.append((agent_id, state))
    
    # Or filter by location
    if 'SafeZone' in state.get('location', ''):
        active_agents.append((agent_id, state))

# Only visualize active_agents
```

---

### Option 4: Heatmap Overlay
**Concept**: Show agent density as a heatmap, with individual markers for selected agents.

**Implementation**:
- Create 2D histogram of agent positions
- Display as heatmap (density map)
- Overlay individual markers for:
  - Agents in S2 state
  - Agents at safe zones
  - Random sample (e.g., 10% of agents)

**Pros**:
- Shows overall flow patterns
- Reduces marker clutter
- Can highlight specific agent types

**Cons**:
- Loses individual agent identity
- Heatmap can obscure network topology
- Requires additional computation

**Code Example**:
```python
# Create density map
from scipy.stats import gaussian_kde

all_x = [state.get('x', 0.0) for state in t_states.values()]
all_y = [state.get('y', 0.0) for state in t_states.values()]

if len(all_x) > 0:
    # Create 2D histogram
    H, xedges, yedges = np.histogram2d(all_x, all_y, bins=20)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    
    # Display as heatmap
    ax.imshow(H.T, origin='lower', extent=extent, 
              cmap='YlOrRd', alpha=0.3, zorder=2)
    
    # Overlay selected agents
    selected_agents = [a for a in t_states.items() 
                      if a[1].get('cognitive_state') == 'S2']
    # ... draw selected agents
```

---

### Option 5: Particle Trails (Advanced)
**Concept**: Similar to trails, but with particle effects showing movement.

**Implementation**:
- Draw agents as particles with tails
- Tail length proportional to speed
- Fade tail opacity
- Use different tail styles for S1 vs S2

**Pros**:
- Visually appealing
- Clear movement indication
- Can distinguish S1 (smooth) vs S2 (jagged) paths

**Cons**:
- More complex to implement
- Can be computationally expensive
- May still be cluttered

---

### Option 6: Animated Subset
**Concept**: Show all agents, but animate a subset with trails/arrows.

**Implementation**:
- Show all agents as static markers
- Select subset (e.g., 50-100 agents) to track with trails
- Rotate which agents are tracked each timestep
- Or track agents based on interesting criteria (S2, moving, etc.)

**Pros**:
- Shows full population
- Highlights interesting movements
- Reduces clutter

**Cons**:
- May miss important patterns
- Requires selection logic

---

## Recommended Approach: Hybrid

**Combine Options 1 + 3**:
1. **Show all agents** as individual markers (current approach)
2. **Add trails** for agents in S2 state (deliberative movement)
3. **Add population counters** at safe zones (already implemented)
4. **Optional**: Add arrows for agents that moved significantly

**Rationale**:
- All agents visible (no information loss)
- Trails highlight S2 behavior (key research question)
- Counters show accumulation (clear metric)
- Arrows optional (can be toggled)

**Implementation Priority**:
1. ✅ Population counters (DONE)
2. 🔄 Trails for S2 agents (NEXT)
3. ⏳ Arrows for significant movement (OPTIONAL)
4. ⏳ Selective visualization toggle (FUTURE)

---

## Code Structure

```python
# In visualize_agent_movements_corrected.py

# Add to initialization:
agent_trails = {}  # agent_id -> list of (x, y, t) tuples
show_trails = True  # Toggle trails on/off
trail_length = 5   # Number of positions to keep

# In animate function:
if show_trails:
    # Update trails for S2 agents only
    for agent_id, state in t_states.items():
        if state.get('cognitive_state') == 'S2':
            x, y = state.get('x', 0.0), state.get('y', 0.0)
            
            if agent_id not in agent_trails:
                agent_trails[agent_id] = []
            agent_trails[agent_id].append((x, y, t))
            
            # Keep only recent positions
            if len(agent_trails[agent_id]) > trail_length:
                agent_trails[agent_id].pop(0)
            
            # Draw trail
            trail = agent_trails[agent_id]
            if len(trail) > 1:
                for i in range(len(trail) - 1):
                    alpha = 0.2 + 0.8 * (i / len(trail))
                    ax.plot([trail[i][0], trail[i+1][0]], 
                           [trail[i][1], trail[i+1][1]],
                           color='green', alpha=alpha, linewidth=1.5, zorder=5)
```

---

## Testing Recommendations

1. **Start with trails for S2 agents only** (reduces clutter)
2. **Test with different trail lengths** (3, 5, 10 positions)
3. **Test with different opacity schemes** (linear vs exponential fade)
4. **Compare with/without trails** to see if it adds value
5. **Consider making trails optional** via command-line flag

---

## Future Enhancements

- **Interactive mode**: Click to highlight specific agent's full trajectory
- **Animation controls**: Pause, step forward/backward, speed control
- **Export frames**: Save individual frames for analysis
- **3D visualization**: Add time as z-axis (shows full trajectories)
- **Network flow**: Show flow between locations as animated streams





