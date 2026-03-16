# Why Agents Stay in Towns Instead of Safe Zones

## Problem Summary

Despite routes existing from towns to safe zones (camps), agents are accumulating in towns rather than reaching camps:
- **Ring**: 845 agents in towns vs 152 in camps (84.5% vs 15.2%)
- **Star**: 682 agents in towns vs 242 in camps (68.2% vs 24.2%)
- **Linear**: 809 agents in towns vs 188 in camps (80.9% vs 18.8%)

## Verified Facts

✅ **Routes exist**: All topologies have routes from towns to camps
- Star: 6 routes (Route1_Mid → SafeZone1, etc.)
- Ring: 12 routes (Ring3_Loc* → SafeZone*)
- Linear: 1 route (Location6 → SafeZone)

✅ **Camp designation**: Safe zones are correctly marked as `type: 'camp'` in locations.csv

✅ **Camp movechance**: `camp_movechance: 0.001` (very low, prevents agents from leaving camps)

✅ **Capacity**: Camps have plenty of space (0.5-1.9% utilization)

## Root Cause Analysis

### 1. **Camp Weight Too Low**

**Current setting**: `camp_weight: 1.0`

**Issue**: Camps have the same base score (1.0) as towns. While towns with conflict get penalized by `conflict_weight: 0.25`, this might not be enough to make camps significantly more attractive.

**Scoring logic** (from `flee/scoring.py`):
```python
score = 1.0  # default
if loc.camp:
    score *= camp_weight  # Currently 1.0
if loc.conflict > 0.0:
    score *= conflict_weight^(decay * conflict)  # 0.25^(decay * 0.4) for towns
```

**For a town with conflict=0.4**:
- Score ≈ 1.0 × 0.25^(1.0 × 0.4) ≈ 0.76

**For a camp (conflict=0.0)**:
- Score = 1.0 × 1.0 = 1.0

Camps ARE more attractive, but the difference might not be large enough, especially when combined with distance penalties.

### 2. **Distance Penalty in Route Selection**

Route weights are calculated as:
```python
weight = (score + weight_softening) / (distance_softening + distance)^distance_power
```

Even if camps have a slightly higher score, longer distances can reduce their route weight significantly.

**Example** (Star topology):
- Route1_Mid → SafeZone1: distance = 100.0
- If a town has a route to another town at distance 50.0, that route might be preferred

### 3. **Low Move Probability at Towns**

**Current setting**: `default_movechance: 0.3` (30% chance per timestep)

Agents at towns only have a 30% chance to move each timestep. Over 30 timesteps:
- Expected moves: 30 × 0.3 = 9 moves
- But agents need to move from Facility → Town → Camp, which might take 2-3 moves
- If agents pause at towns, they might not reach camps in time

### 4. **Time Constraint**

**Current setting**: `num_timesteps: 30`

With `movechance=0.3`, agents might not have enough time to:
1. Leave Facility (t=0-5)
2. Reach Town (t=5-10)
3. Leave Town (t=10-20, multiple attempts needed)
4. Reach Camp (t=20-30)

## Proposed Fixes

### Fix 1: Increase Camp Weight (RECOMMENDED)

**Change**: `camp_weight: 1.0` → `camp_weight: 2.0` or `3.0`

**Rationale**: Makes camps significantly more attractive than towns, encouraging agents to prioritize reaching safe zones.

**Implementation**: Update `nuclear_evacuation_simulations.py` line 351:
```python
'camp_weight': 2.0,  # Increased from 1.0 to make camps more attractive
```

### Fix 2: Increase Town Movechance

**Change**: `default_movechance: 0.3` → `default_movechance: 0.5` or `0.6`

**Rationale**: Reduces pausing at intermediate locations, allowing agents to reach camps faster.

**Trade-off**: Agents might also leave camps more easily, but `camp_movechance=0.001` should prevent this.

### Fix 3: Increase Simulation Length

**Change**: `num_timesteps: 30` → `num_timesteps: 60` or `90`

**Rationale**: Gives agents more time to complete the journey to camps.

**Trade-off**: Longer simulations take more time to run.

### Fix 4: Reduce Route Distances

**Change**: Make routes to camps shorter (e.g., place camps closer to towns)

**Rationale**: Reduces distance penalty in route selection.

**Trade-off**: Changes topology structure (might not be desired for realism).

## Recommended Solution

**Combine Fixes 1 and 2**:
1. Increase `camp_weight` to `2.0` or `3.0`
2. Increase `default_movechance` to `0.5`

This should:
- Make camps significantly more attractive (Fix 1)
- Reduce pausing at towns (Fix 2)
- Allow agents to reach camps within 30 timesteps

## Testing Plan

1. Apply Fix 1 (increase camp_weight to 2.0)
2. Run simulation with 30 timesteps
3. Check if camp population increases
4. If still insufficient, apply Fix 2 (increase default_movechance to 0.5)
5. Re-run and verify results

## Expected Outcome

After fixes:
- **Camps**: Should have 40-60% of agents (vs current 15-24%)
- **Towns**: Should have 30-50% of agents (vs current 68-85%)
- **Conflict**: Should have <5% of agents (similar to current)





