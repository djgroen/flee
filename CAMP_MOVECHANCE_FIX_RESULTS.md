# Camp Movechance Fix: Results

## Problem Identified

Agents were leaving safe zones (camps) too frequently, even though `camp_movechance: 0.001` (0.1% per timestep).

**Root Cause**: The S1/S2 model was overriding `camp_movechance` when System 2 was active:
- At camp with S2 active: `p_move = 0.1 × 0.001 + 0.9 × 0.9 = 0.81` (81%!)
- Expected: `p_move = 0.001` (0.1%)

## Fix Applied

Added two checks in `flee/moving.py` to respect `camp_movechance` regardless of S1/S2 state:

1. **Before S1/S2 model calculation** (line ~522):
   ```python
   if a.location.camp or a.location.idpcamp:
       return a.location.movechance, False
   ```

2. **Before route continuation check** (line ~684):
   ```python
   if a.location.camp or a.location.idpcamp:
       return a.location.movechance, system2_active
   ```

## Results: Dramatic Improvement

### Before Fix (camp_movechance bug)
- **Ring**: 315/1000 (31.5%) at safe zones
- **Star**: 294/1000 (29.4%) at safe zones
- **Linear**: 283/1000 (28.3%) at safe zones

### After Fix (camp_movechance respected)
- **Ring**: 998/1000 (99.8%) at safe zones ⬆️ **+68.3%**
- **Star**: 1000/1000 (100.0%) at safe zones ⬆️ **+70.6%**
- **Linear**: 990/1000 (99.0%) at safe zones ⬆️ **+70.7%**

## Key Observations

1. **Evacuation Success**: 
   - Star topology achieved **100% evacuation success**!
   - Ring and Linear topologies achieved **99%+ evacuation success**

2. **S2 Activation Drop**:
   - S2 activation rates dropped dramatically (from ~80-95% to ~0-1%)
   - This is expected: agents at safe zones aren't making movement decisions
   - S2 is only needed when agents are deciding whether/where to move

3. **Agent Behavior**:
   - Agents now properly accumulate in safe zones
   - Very few agents leave safe zones (0.1% per timestep, as intended)
   - The remaining 0-2% are likely still in transit at t=29

## Theoretical Justification

**No S1/S2 differentiation at camps**: 
- Safe zones are designated as safe (conflict=0.0)
- The purpose of a safe zone is safety, regardless of cognitive state
- Both S1 (reactive) and S2 (deliberative) agents should feel safe and stay
- `camp_movechance = 0.001` reflects that agents rarely leave safe zones

## Files Modified

- `flee/moving.py` (2 locations: lines ~522 and ~684)
- `CAMP_MOVECHANCE_BUG_ANALYSIS.md` (analysis document)

## Conclusion

The fix successfully ensures that `camp_movechance = 0.001` is respected in all cases, regardless of:
- S1/S2 cognitive state
- Route continuation status
- Other movement logic

This results in realistic behavior where agents properly accumulate in safe zones and rarely leave them.





