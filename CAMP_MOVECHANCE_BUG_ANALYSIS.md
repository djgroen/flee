# Camp Movechance Bug Analysis

## Problem

Agents are leaving safe zones (camps) too frequently, even though `camp_movechance: 0.001` (1/1000 probability per timestep).

## Root Cause

The S1/S2 model (`calculate_move_probability_s1s2`) does NOT respect `camp_movechance` when System 2 is active.

### Current Behavior

In `flee/moving.py` line 539-550:
```python
movechance = a.location.movechance  # Gets camp_movechance = 0.001 for camps
p_move, p_s2_active = calculate_move_probability_s1s2(
    experience_index, conflict, movechance,
    alpha, beta, p_s2
)
```

In `flee/s1s2_model.py` line 182:
```python
p_move = (1.0 - p_s2_active) * movechance + p_s2_active * p_s2
```

**Example calculation for agent at camp with S2 active:**
- `movechance = 0.001` (camp_movechance)
- `p_s2_active = 0.9` (high S2 activation at safe zone - low conflict, high experience)
- `p_s2 = 0.9` (S2 move probability from config)

**Result:**
```
p_move = (1.0 - 0.9) * 0.001 + 0.9 * 0.9
       = 0.1 * 0.001 + 0.81
       = 0.0001 + 0.81
       = 0.81 (81% move probability!)
```

**Expected:**
```
p_move = 0.001 (camp_movechance should override)
```

## Why This Happens

The S1/S2 model is designed to blend S1 and S2 move probabilities, but it doesn't account for location-specific constraints like camps. When S2 is active, it uses `p_s2` (0.9) which is meant for deliberative movement, but camps should have a hard constraint regardless of cognitive state.

## Solution

Add a check in `calculateMoveChance` to respect `camp_movechance` regardless of S1/S2 state:

```python
# BEFORE S1/S2 calculation, check if agent is at a camp
if a.location.camp:
    # Camps have very low movechance - respect it regardless of S1/S2
    return a.location.movechance, False  # Use camp_movechance, no S2 override
```

Or modify `calculate_move_probability_s1s2` to accept a `max_movechance` parameter that caps the result.

## Impact

- **Current**: Agents at camps with S2 active have ~81% chance to leave
- **Expected**: Agents at camps should have 0.1% chance to leave (camp_movechance)
- **Effect**: Agents are leaving safe zones too quickly, reducing final safe zone population

## Fix Location

File: `flee/moving.py`
Function: `calculateMoveChance`
Line: ~520-570 (S1/S2 model section)





