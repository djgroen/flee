# Move Probability Consistency Analysis

## 🔍 Issue Identified

The S1/S2 model can override location-specific `movechance` values, similar to the camp bug we fixed. Let's analyze all location types:

## 📊 Current Behavior

### Formula
```
p_move = (1 - P_S2) × movechance + P_S2 × p_s2
```
where:
- `movechance` = location-specific move probability (conflict_movechance, default_movechance, camp_movechance)
- `p_s2` = S2 move probability (fixed at 0.8)
- `P_S2` = S2 activation probability (Ψ × Ω)

### Impact Analysis

#### 1. **Camps** (`camp_movechance = 0.001`)
- **Intent**: Agents should STAY in safe zones
- **Current Status**: ✅ **FIXED** - Early return prevents S1/S2 override
- **Behavior**: Always returns `a.location.movechance` (0.001), preserving cognitive state

#### 2. **Conflict Zones** (`conflict_movechance = 1.0`)
- **Intent**: Agents should ALWAYS try to leave (high urgency, panic response)
- **Current Status**: ⚠️ **POTENTIAL ISSUE** - S1/S2 model can reduce move probability
- **Example**: 
  - If `P_S2 = 0.8`: `p_move = 0.2 × 1.0 + 0.8 × 0.8 = 0.84` (16% reduction)
  - If `P_S2 = 1.0`: `p_move = 0.0 × 1.0 + 1.0 × 0.8 = 0.80` (20% reduction)
- **Question**: Should conflict zones have a hard constraint like camps?

#### 3. **Towns** (`default_movechance = 0.3`)
- **Intent**: Moderate move probability (normal decision-making)
- **Current Status**: ⚠️ **MODIFIED** - S1/S2 model increases move probability
- **Example**:
  - If `P_S2 = 0.8`: `p_move = 0.2 × 0.3 + 0.8 × 0.8 = 0.70` (133% increase)
- **Question**: Is this intentional? (S2 agents are more strategic and move more)

## 🤔 Design Questions

### Should conflict zones have a hard constraint?

**Arguments FOR hard constraint:**
- `conflict_movechance = 1.0` is a design intent: agents should ALWAYS try to leave
- High conflict zones should trigger panic (S1) response, not deliberation
- Consistency with camp fix: if camps have hard constraint, conflict zones should too

**Arguments AGAINST hard constraint:**
- S2 agents might be more strategic: assess routes before fleeing (realistic)
- Moderate conflict zones might benefit from deliberation
- The model already accounts for conflict in Ω calculation (lower conflict → higher Ω → higher P_S2)

### Should towns allow S1/S2 modification?

**Current behavior**: S2 agents move more (0.3 → 0.70 with P_S2=0.8)
- **Rationale**: S2 agents are more strategic and make better decisions
- **This seems intentional and reasonable**

## 💡 Proposed Solution

### Option 1: Hard Constraint for Conflict Zones (Most Consistent)
```python
# In calculateMoveChance, after camp check:
if a.location.conflict and a.location.conflict > 0.5:  # High conflict
    # Preserve cognitive state, but use conflict_movechance (agents always try to leave)
    current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
    return a.location.movechance, current_s2
```

**Pros:**
- Consistent with camp fix
- Respects design intent of `conflict_movechance = 1.0`
- High conflict → panic response (S1), not deliberation

**Cons:**
- Removes S2 strategic behavior in conflict zones
- Might be less realistic (some agents might deliberate even under high conflict)

### Option 2: Soft Constraint (Minimum Move Probability)
```python
# After S1/S2 calculation:
if a.location.conflict and a.location.conflict > 0.5:
    # Ensure minimum move probability for high conflict zones
    p_move = max(p_move, a.location.movechance * 0.9)  # At least 90% of conflict_movechance
```

**Pros:**
- Allows some S2 modification but preserves urgency
- More flexible than hard constraint

**Cons:**
- Still allows reduction (10% reduction possible)
- More complex logic

### Option 3: Keep Current Behavior (Status Quo)
- Conflict zones: Allow S1/S2 to modify (current behavior)
- Towns: Allow S1/S2 to modify (current behavior)
- Camps: Hard constraint (already fixed)

**Pros:**
- Simplest solution
- S2 strategic behavior preserved everywhere

**Cons:**
- Inconsistent with camp fix
- Contradicts design intent of `conflict_movechance = 1.0`

## 🎯 Recommendation

**Option 1 (Hard Constraint for High Conflict Zones)** is most consistent with:
1. The camp fix we just implemented
2. The design intent of `conflict_movechance = 1.0`
3. Realistic behavior: extreme conflict → panic (S1), not deliberation

However, we should only apply this to **high conflict zones** (conflict > 0.5), not moderate conflict zones where deliberation might be beneficial.

## 📝 Implementation

If we implement Option 1, we would add:
```python
# After camp check, before S1/S2 calculation:
if hasattr(a.location, 'conflict') and a.location.conflict > 0.5:
    # High conflict zones: agents should always try to leave (panic response)
    # Preserve cognitive state, but use conflict_movechance
    current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
    return a.location.movechance, current_s2
```

This ensures:
- **Camps**: Hard constraint (stay)
- **High conflict zones**: Hard constraint (leave immediately)
- **Moderate conflict zones**: Allow S1/S2 modification (deliberation possible)
- **Towns**: Allow S1/S2 modification (strategic decisions)





