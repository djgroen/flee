# High-Conflict Zone Hard Constraint Implementation

## ✅ Implementation Complete

Added hard constraint for high-conflict zones to ensure `conflict_movechance = 1.0` is respected, similar to the camp fix.

## 📝 Changes Made

### 1. TwoSystemDecisionMaking Block (Line ~530)
```python
# CRITICAL: High-conflict zones have high movechance (1.0) - respect it regardless of S1/S2
# This ensures agents always try to leave extreme danger zones (panic response)
conflict = max(0.0, getattr(a.location, 'conflict', 0.0))
if conflict > 0.5:  # High conflict threshold
    # Preserve current cognitive state, but use conflict_movechance (agents always try to leave)
    # This maintains behavioral continuity while respecting urgency
    current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
    return a.location.movechance, current_s2
```

### 2. Fallback S1 Logic (Line ~690)
```python
# CRITICAL: High-conflict zones have high movechance (1.0) - respect it even if agent has a route
# This ensures agents always try to leave extreme danger zones (panic response)
conflict = max(0.0, getattr(a.location, 'conflict', 0.0))
if conflict > 0.5:  # High conflict threshold
    # Preserve current cognitive state, but use conflict_movechance (agents always try to leave)
    current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
    return a.location.movechance, current_s2
```

## 🎯 Logic Summary

### Location Type Handling

1. **Camps** (`camp_movechance = 0.001`)
   - ✅ Hard constraint: Always return `movechance = 0.001`
   - Agents stay in safe zones
   - Cognitive state preserved

2. **High-Conflict Zones** (`conflict > 0.5`, `conflict_movechance = 1.0`)
   - ✅ Hard constraint: Always return `movechance = 1.0`
   - Agents always try to leave (panic response)
   - Cognitive state preserved
   - **NEW**: Prevents S1/S2 model from reducing move probability

3. **Moderate-Conflict Zones** (`conflict ≤ 0.5`)
   - ✅ Allow S1/S2 modification
   - Agents can deliberate (S2) or react (S1)
   - Move probability can be modified by S1/S2 model

4. **Towns** (`default_movechance = 0.3`)
   - ✅ Allow S1/S2 modification
   - S2 agents move more (strategic decisions)
   - Move probability can be increased by S1/S2 model

## 📊 Impact Analysis

### Before Fix
- **Conflict zones** (`conflict = 0.95`, `movechance = 1.0`):
  - With `P_S2 = 0.8`: `p_move = 0.2 × 1.0 + 0.8 × 0.8 = 0.84` ❌ (16% reduction)
  - Contradicted design intent of `conflict_movechance = 1.0`

### After Fix
- **High-conflict zones** (`conflict > 0.5`, `movechance = 1.0`):
  - Always return `p_move = 1.0` ✅
  - Respects design intent
  - Preserves cognitive state

### Moderate-Conflict Zones (Unchanged)
- **Moderate conflict** (`conflict = 0.4`, `movechance = 0.3`):
  - With `P_S2 = 0.8`: `p_move = 0.2 × 0.3 + 0.8 × 0.8 = 0.70` ✅
  - Allows deliberation (S2 increases move probability)

## 🔍 Consistency Check

| Location Type | Movechance | S1/S2 Override | Hard Constraint | Rationale |
|--------------|------------|----------------|-----------------|-----------|
| Camps | 0.001 | ❌ No | ✅ Yes | Agents should stay |
| High Conflict | 1.0 | ❌ No | ✅ Yes | Agents should always try to leave |
| Moderate Conflict | 0.3 | ✅ Yes | ❌ No | Allow deliberation |
| Towns | 0.3 | ✅ Yes | ❌ No | Allow strategic decisions |

## ✅ Benefits

1. **Consistency**: High-conflict zones now have the same hard constraint as camps
2. **Design Intent**: `conflict_movechance = 1.0` is now respected
3. **Realistic Behavior**: Extreme conflict → panic response (S1), not deliberation
4. **Flexibility**: Moderate conflict zones still allow S1/S2 modification
5. **State Preservation**: Cognitive state is preserved (S2 agents stay S2, S1 agents stay S1)

## 🧪 Testing Recommendations

1. **High-conflict zone test**: Verify agents at `conflict = 0.95` always have `p_move = 1.0`
2. **Moderate-conflict zone test**: Verify agents at `conflict = 0.4` can have modified move probability
3. **Camp test**: Verify agents at camps still have `p_move = 0.001`
4. **Cognitive state test**: Verify S2 agents maintain S2 state when entering high-conflict zones

## 📄 Files Modified

- `flee/moving.py`: Added high-conflict zone checks in two locations (lines ~530 and ~690)





