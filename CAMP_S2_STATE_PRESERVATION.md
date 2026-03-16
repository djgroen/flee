# Should Agents Maintain S2 State at Camps?

## Current Behavior

When agents are at camps, the code returns `False` for `system2_active` (line 524):
```python
if a.location.camp or a.location.idpcamp:
    return a.location.movechance, False  # Forces S1
```

This causes `cognitive_state` to be set to "S1" in `flee/flee.py` line 508, even if the agent was in S2 when they arrived.

## Question: Should S2 State Be Preserved?

### Option 1: Preserve S2 State (Recommended)
**Rationale:**
- S2 is a cognitive state, not just about movement decisions
- Agents might still be deliberating even at safe zones (e.g., planning next steps, assessing resources)
- More realistic: people don't instantly switch cognitive modes
- Maintains continuity in agent behavior

**Implementation:**
```python
if a.location.camp or a.location.idpcamp:
    # Preserve current cognitive state, but use camp_movechance
    current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
    return a.location.movechance, current_s2
```

### Option 2: Force S1 at Camps (Current)
**Rationale:**
- At safe zones, agents aren't making movement decisions
- S2 is primarily for deliberative movement planning
- Simpler: camps = S1 (reactive/resting state)

**Current Implementation:**
```python
if a.location.camp or a.location.idpcamp:
    return a.location.movechance, False  # Forces S1
```

## Recommendation

**Preserve S2 state** - agents who were deliberating (S2) when they reached a safe zone should maintain that cognitive state, even though they're not actively moving. This is more realistic and maintains behavioral continuity.

## Fix

Modify `flee/moving.py` line 522-524 to preserve current cognitive state:

```python
if a.location.camp or a.location.idpcamp:
    # Preserve current cognitive state, but respect camp_movechance
    current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
    return a.location.movechance, current_s2
```

This way:
- `camp_movechance = 0.001` is still respected (agents don't move)
- But agents maintain their cognitive state (S1 or S2)
- More realistic behavior





