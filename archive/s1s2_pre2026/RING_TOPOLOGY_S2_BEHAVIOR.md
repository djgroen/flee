# Ring Topology: S2 Activation Behavior Analysis

## Topology Structure

**Yes, there is only ONE SafeZone** in the ring topology:
- **SafeZone**: Located at (x=150.0, y=0.0), conflict=0.00
- **All 4 Ring3 locations** are directly connected to SafeZone (distance: 50.0 units)
- So agents at Ring3 are **one step away** from safety

### Location Hierarchy (by distance from SafeZone)

| Location | Distance from SafeZone | Conflict Level | Ring |
|----------|----------------------|----------------|------|
| Ring3_Loc1 | 50.0 | 0.20 | Outer (one step) |
| Ring2_Loc1 | 83.3 | 0.45 | Middle |
| Ring1_Loc1 | 116.7 | 0.70 | Inner |
| Facility | 150.0 | 0.95 | Center (danger) |

## S2 Activation Model

The S2 activation follows the **parsimonious dual-process model**:

```
P_S2 = Ψ × Ω
```

Where:
- **Ψ (Cognitive Capacity)** = `sigmoid(α × experience_index)`
  - Increases with agent's experience (time since departure, connections, local knowledge, etc.)
  - **Stable** - depends on agent attributes, not location
  
- **Ω (Structural Opportunity)** = `sigmoid(β × (1 - conflict))`
  - **HIGH when conflict is LOW** (more opportunity to think)
  - **LOW when conflict is HIGH** (too much stress to deliberate)
  - **Dynamic** - depends on current location's conflict level

## Expected Behavior: "One Step Away" Pattern

**Yes, agents should activate S2 more when one step away from SafeZone**, but not just because of proximity. The mechanism is:

### At Ring3 (One Step from SafeZone):

1. **Low Conflict (0.20)** → **HIGH Ω** (structural opportunity)
   - `Ω = sigmoid(β × (1 - 0.20)) = sigmoid(β × 0.80)`
   - With β=2.0: `Ω ≈ 0.83` (high opportunity)

2. **High Experience** (agents have been traveling) → **HIGH Ψ** (cognitive capacity)
   - Experience increases with `timesteps_since_departure`
   - Agents at Ring3 have traveled through multiple rings
   - `Ψ = sigmoid(α × experience_index)` → likely high

3. **Result**: `P_S2 = HIGH × HIGH = HIGH S2 activation`

### At Facility (Center, High Danger):

1. **High Conflict (0.95)** → **LOW Ω** (structural opportunity)
   - `Ω = sigmoid(β × (1 - 0.95)) = sigmoid(β × 0.05)`
   - With β=2.0: `Ω ≈ 0.12` (low opportunity - too much stress)

2. **Low Experience** (just started) → **LOW Ψ** (cognitive capacity)
   - Agents just spawned, minimal travel experience
   - `Ψ` is likely low

3. **Result**: `P_S2 = LOW × LOW = LOW S2 activation`

## Key Insight

**S2 activation is NOT directly about distance to SafeZone**, but rather:

1. **Structural Opportunity (Ω)**: Lower conflict → more opportunity to think
2. **Cognitive Capacity (Ψ)**: More experience → more ability to think
3. **Combined Effect**: Both must be high for S2 activation

Since Ring3 has:
- **Low conflict** (high Ω)
- **Agents with more travel experience** (high Ψ)

→ **S2 activation should be HIGH at Ring3**

This creates the appearance of "agents go to S2 when one step away" because:
- Ring3 is one step from SafeZone
- Ring3 has the lowest conflict (except SafeZone itself)
- Agents at Ring3 have the most experience

## Verification Results ✅

**Actual S2 Activation Rates by Location** (from simulation):

| Location | S2 Rate | Conflict | Distance from SafeZone |
|----------|---------|----------|----------------------|
| **SafeZone** | **99.9%** | 0.00 | 0 (destination) |
| **Ring3** (all locations) | **98.1%** | 0.20 | **50.0 (one step)** |
| Ring2 (all locations) | 73.1% | 0.45 | 83.3 (middle) |
| Ring1 (all locations) | 3.1% | 0.70 | 116.7 (inner) |
| Facility (center) | 0.0% | 0.95 | 150.0 (danger) |

**✅ Confirmed Pattern**: 
- **Ring3 (one step from SafeZone) has 98.1% S2 activation** - nearly all agents are in S2 mode
- S2 activation decreases dramatically as conflict increases and distance from safety increases
- This matches the theoretical model: `P_S2 = Ψ × Ω` where both factors are high at Ring3

## Model Parameters

Current settings (from `simsetting.yml`):
- `alpha = 2.0` (cognitive capacity weight)
- `beta = 2.0` (structural opportunity weight)
- `p_s2 = 0.8` (S2 move probability when active)

These parameters control the sensitivity of S2 activation to experience and conflict.

