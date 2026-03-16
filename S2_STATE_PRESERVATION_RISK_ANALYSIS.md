# Risk Analysis: Preserving S2 State at Camps

## Change Made

Modified `flee/moving.py` to preserve `cognitive_state` when agents are at camps, instead of forcing them to S1.

**Before:**
```python
if a.location.camp or a.location.idpcamp:
    return a.location.movechance, False  # Forces S1
```

**After:**
```python
if a.location.camp or a.location.idpcamp:
    current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
    return a.location.movechance, current_s2  # Preserves state
```

## Potential Issues

### ✅ Issue 1: Route Pre-calculation (NOT A PROBLEM)

**Concern**: If agents are in S2 at camps, might they pre-calculate routes unnecessarily?

**Analysis**: 
- Route pre-calculation happens at line 573: `if s2_active: provisional_route = selectRoute(...)`
- But at camps, we return early (line 526) BEFORE reaching this code
- So routes are NOT pre-calculated at camps
- **No issue**

### ✅ Issue 2: Information Sharing (NOT A PROBLEM)

**Concern**: If agents are in S2 at camps, might they try to share route information?

**Analysis**:
- Information sharing happens at line 511: `if system2_active and self.attributes.get("_share_route_info", False)`
- But `_share_route_info` is only set when routes are pre-calculated (line 581)
- Since routes aren't pre-calculated at camps, `_share_route_info` won't be set
- **No issue**

### ⚠️ Issue 3: Stale S2 State (MINOR CONCERN)

**Concern**: If an agent arrives at a camp in S2 state (based on previous location's conditions), the state might be "stale" - the conditions that triggered S2 no longer apply.

**Example**:
- Agent at high-conflict location → S2 activated (high pressure)
- Agent moves to camp (low conflict, safe)
- We preserve S2 state, but the agent is now in a safe environment

**Analysis**:
- This is actually **realistic**: cognitive states don't instantly switch
- People who were deliberating don't instantly become reactive when they reach safety
- The state will naturally update if the agent moves to a new location
- **Minor concern, but acceptable behavior**

### ✅ Issue 4: Route Selection if Agent Moves (NOT A PROBLEM)

**Concern**: If an agent at a camp (in S2 state) somehow moves (0.1% chance), would route selection be affected?

**Analysis**:
- If agent moves from camp, they're no longer at a camp
- Next timestep, `calculateMoveChance` will run normally (not the camp check)
- S2 state will be recalculated based on new location
- **No issue**

### ✅ Issue 5: State Consistency (NOT A PROBLEM)

**Concern**: Could preserving state lead to inconsistent `cognitive_state` vs actual behavior?

**Analysis**:
- `cognitive_state` is updated in `flee/flee.py` line 503-508 based on `system2_active`
- We're returning the preserved state as `system2_active`
- So `cognitive_state` will match what we return
- **No inconsistency**

## Edge Cases

### Edge Case 1: Agent Spawns at Camp

**Scenario**: Agent is created/spawned at a camp location.

**Behavior**:
- `cognitive_state` defaults to "S1" (line 113 in flee.py)
- We preserve "S1" state
- **Expected behavior**

### Edge Case 2: Agent Transitions Camp → Town → Camp

**Scenario**: Agent moves from camp to town (S1), then back to camp.

**Behavior**:
- At town: S2 might activate (normal logic)
- Back at camp: We preserve whatever state they're in
- **Expected behavior**

### Edge Case 3: Agent Has Route When Arriving at Camp

**Scenario**: Agent has a pre-calculated route (`_temp_route`) when they arrive at camp.

**Behavior**:
- Route is stored in `a.attributes["_temp_route"]`
- At camp, we return early, so route isn't used
- Route will be cleared when agent moves (if they ever do)
- **No issue** - route is just unused, not harmful

## Conclusion

**No significant issues identified.** The change is safe because:

1. ✅ Route pre-calculation doesn't happen at camps (early return)
2. ✅ Information sharing doesn't happen at camps (no routes to share)
3. ✅ State is consistent (what we return matches what's stored)
4. ✅ If agents move, state recalculates normally
5. ⚠️ "Stale" S2 state is acceptable (realistic behavior)

## Recommendation

**Keep the change.** The preservation of S2 state at camps is:
- More realistic (cognitive states don't instantly switch)
- Behaviorally consistent (maintains agent identity)
- Safe (no algorithmic issues identified)
- Minor edge case (stale state) is acceptable

## Testing Recommendation

Run a simulation and verify:
1. Agents who reach camps in S2 state maintain S2 state
2. Agents who reach camps in S1 state maintain S1 state
3. No unexpected route pre-calculation or information sharing
4. State updates correctly when agents move to new locations





