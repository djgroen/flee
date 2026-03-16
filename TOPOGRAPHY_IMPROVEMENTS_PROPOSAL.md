# Topology Improvements for More Interesting Movies

## Problem Identified

Current topologies are too simple:
- **Ring**: Only one path outward, then all go to SafeZone
- **Star**: Each spoke is independent, no choices
- **Linear**: Only one path forward

**Result**: Agents don't have meaningful choices, so S1 vs S2 decisions don't create visible differences.

## Proposed Improvements

### 1. Decision-Rich Ring Topology

**Changes:**
- Multiple paths between rings (not just nearest neighbor)
- Multiple safe zones at different angles (destination choice)
- Each outer ring location connects to 2 nearest safe zones (routing choice)
- Circular paths within rings (go around or go outward?)

**Visual Impact:**
- Agents will split between different safe zones
- Some agents take longer routes (S2 planning)
- Some agents take shorter routes (S1 reactive)

### 2. Decision-Rich Star Topology

**Changes:**
- Multiple intermediate towns per spoke (route choices)
- Cross-connections between adjacent spokes (can switch routes)
- Some spokes have shortcuts vs detours

**Visual Impact:**
- Agents can switch between spokes
- Different agents take different paths to safety
- S2 agents may choose longer but safer routes

### 3. Decision-Rich Linear Topology

**Changes:**
- Branching paths at decision points
- Parallel routes (some faster, some safer)
- Routes merge back (convergence points)
- Dead-end branches (tests S2 route planning)

**Visual Impact:**
- Agents split at branches
- Some take main route, others take branches
- Clear visual difference between S1 (main route) and S2 (branch routes)

### 4. Grid/Maze Topology (New)

**Structure:**
- 4x4 grid of locations
- Multiple paths to safe zones
- Diagonal shortcuts (faster but might be riskier)
- Multiple safe zones at edges

**Visual Impact:**
- Most complex routing decisions
- Clear clustering of S1 agents (following others)
- S2 agents spread out (individual planning)

## Parameter Adjustments

### To Make Decisions More Visible:

1. **Increase agent heterogeneity:**
   ```python
   # More variation in experience
   experience_index = np.random.beta(2, 5)  # Most low, some high
   connections = np.random.poisson(3)  # More variation
   ```

2. **Adjust S2 move probability:**
   ```python
   'p_s2': 0.9  # Higher S2 move probability (was 0.8)
   # Makes S2 agents more likely to move when activated
   ```

3. **Increase awareness level for S2:**
   ```python
   'awareness_level': 2  # Higher awareness (was 1)
   # S2 agents see more routes ahead
   ```

4. **Add route distance variation:**
   - Some routes shorter but through higher conflict
   - Some routes longer but through lower conflict
   - S2 agents should prefer safer routes

## Implementation Plan

1. **Create improved topology functions** ✅ (done in `improved_topologies_for_movies.py`)
2. **Integrate into main simulation script**
3. **Run test simulations** with new topologies
4. **Generate new movies** and compare
5. **Adjust parameters** based on visual results

## Expected Visual Improvements

### Before (Current):
- All agents follow same path
- Hard to see S1 vs S2 differences
- Predictable movement patterns

### After (Improved):
- Agents split at decision points
- S1 agents: Clustered, follow main routes
- S2 agents: Spread out, take alternative routes
- Clear visual distinction between decision types
- More dynamic, interesting animations

## Next Steps

1. Test improved topologies with small agent count (100 agents)
2. Verify S1/S2 differences are visible
3. Adjust parameters if needed
4. Run full simulation (1000 agents)
5. Generate new movies
6. Compare with original movies

