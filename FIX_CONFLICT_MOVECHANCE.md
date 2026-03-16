# Fix: Agents Stuck at Origin (Conflict Movechance)

## Problem Identified

**Issue**: Most agents (86-87%) were staying at the origin (Facility) and not reaching safe zones.

**Root Cause**: 
- Facility is designated as `type: 'conflict'` (correct - it's a dangerous location)
- When a location has `type: 'conflict'`, Flee sets its `movechance = SimulationSettings.move_rules["ConflictMoveChance"]`
- `conflict_movechance` was set to `0.0` in the configuration
- **Result**: Agents at conflict zones CANNOT LEAVE (0% move probability per timestep)

## Fix Applied

Changed `conflict_movechance` from `0.0` to `1.0` in `nuclear_evacuation_simulations.py`:

```python
# Before:
'conflict_movechance': 0.0,

# After:
'conflict_movechance': 1.0,  # HIGH movechance to escape danger zones
```

## Rationale

**Semantic Correctness**: 
- Conflict zones are dangerous - agents should **ESCAPE** them, not stay in them
- `conflict_movechance` should represent the **urgency to leave** a conflict zone
- Setting it to `1.0` means agents have 100% chance per timestep to attempt to leave

**Expected Behavior**:
- Agents spawn at Facility (conflict zone)
- With `conflict_movechance=1.0`, they immediately attempt to leave
- They move through intermediate locations toward safe zones
- Safe zones have `camp_movechance=0.001` (0.1% chance to leave), so agents stay there

## Capacity Analysis

**Safe Zone Capacities**:
- Ring: 3 safe zones × 10,000 = 30,000 total capacity
- Star: 6 safe zones × 5,000 = 30,000 total capacity  
- Linear: 1 safe zone × 10,000 = 10,000 total capacity

**Agent Count**: 1,000 agents per topology

**Conclusion**: Capacity is NOT the issue. The problem was agents being trapped at the origin.

## Expected Impact

After this fix:
- ✅ Agents will leave Facility immediately (100% movechance)
- ✅ More agents will reach safe zones
- ✅ Evacuation rates should increase from ~13-18% to much higher
- ✅ Safe zones should fill up more (though still limited by 30 timesteps)

## Files Modified

- `nuclear_evacuation_simulations.py` line 353: Changed `conflict_movechance` from `0.0` to `1.0`

## Next Steps

1. Re-run simulations with the fix
2. Verify agents leave Facility and reach safe zones
3. Check if evacuation rates increase significantly
4. If safe zones still don't fill, consider:
   - Increasing number of timesteps
   - Adjusting route distances
   - Checking if there are bottlenecks in the network

