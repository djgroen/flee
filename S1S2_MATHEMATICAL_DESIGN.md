# S1/S2 Mathematical Design

## Core Principles

### 1. **Bounded Cognitive Pressure**
- Pressure should be bounded between 0.0 and 1.0
- Should have realistic dynamics (increase, plateau, decay)
- Should reflect real psychological stress patterns

### 2. **Realistic S2 Activation**
- Should be probabilistic, not deterministic
- Should vary meaningfully across agents and time
- Should reflect individual differences

### 3. **Meaningful S1/S2 Differences**
- S1: Fast, heuristic, reactive
- S2: Slow, deliberative, analytical
- Should produce different behavioral outcomes

## Mathematical Framework

### 1. **Cognitive Pressure Calculation**

```
cognitive_pressure(t) = base_pressure(t) + conflict_pressure(t) + social_pressure(t)
```

Where each component is bounded and has realistic dynamics:

#### **Base Pressure (Internal Stress)**
```
base_pressure(t) = min(0.4, connectivity_factor * 0.2 + time_stress(t))
```

- **connectivity_factor**: `min(1.0, connections / 10.0)` (0.0 to 1.0)
- **time_stress(t)**: Bounded time-based stress with decay

#### **Time Stress with Decay**
```
time_stress(t) = 0.1 * (1 - exp(-t/10)) * exp(-t/50)
```

This creates:
- Initial increase (0 to 0.1)
- Peak around t=10
- Gradual decay to 0
- Bounded between 0.0 and 0.1

#### **Conflict Pressure (External Stress)**
```
conflict_pressure(t) = conflict_intensity * connectivity_factor * conflict_decay(t)
```

- **conflict_intensity**: Location conflict level (0.0 to 1.0)
- **conflict_decay(t)**: Decay factor based on time since conflict

#### **Conflict Decay**
```
conflict_decay(t) = exp(-max(0, t - conflict_start_time) / recovery_time)
```

- **recovery_time**: 20 timesteps (realistic recovery period)
- Creates exponential decay after conflict starts

#### **Social Pressure (Network Effects)**
```
social_pressure(t) = min(0.2, social_network_stress(t))
```

- **social_network_stress**: Based on connected agents' stress levels
- Bounded to prevent runaway effects

### 2. **S2 Activation Probability**

```
P(S2_activation) = sigmoid(pressure - threshold) + individual_modifiers
```

#### **Sigmoid Function**
```
sigmoid(x) = 1 / (1 + exp(-k * x))
```

- **k = 6.0**: Steepness parameter (sharper than current k=8.0)
- **x = pressure - threshold**: Difference from individual threshold

#### **Individual Modifiers**
```
individual_modifiers = education_boost + stress_tolerance_modifier + social_support - fatigue_penalty
```

- **education_boost**: `education_level * 0.05` (max 5% boost)
- **stress_tolerance_modifier**: `stress_tolerance * 0.03` (max 3% boost)
- **social_support**: `min(connections * 0.01, 0.05)` (max 5% boost)
- **fatigue_penalty**: `min(time * 0.001, 0.03)` (max 3% penalty, bounded)

### 3. **S2 Capability**

```
S2_capable = (connections >= 1) OR (timesteps_since_departure >= 3) OR (education_level >= 0.3)
```

More realistic than current requirement of 2+ connections OR 5+ timesteps.

### 4. **Move Chance Calculation**

#### **S1 Move Chance**
```
S1_move_chance = location.movechance * population_factor * conflict_factor
```

- **population_factor**: Based on location population density
- **conflict_factor**: Reduced move chance in high conflict

#### **S2 Move Chance**
```
S2_move_chance = min(1.0, S1_move_chance + deliberation_boost)
```

- **deliberation_boost**: `0.2 + (pressure - 0.5) * 0.3`
- S2 agents get higher move chance due to better planning

### 5. **Route Selection Differences**

#### **S1 Route Selection**
- Uses standard awareness level
- Higher randomness (weight_softening > 0)
- Shorter planning horizon

#### **S2 Route Selection**
- Increased awareness level (+1)
- Lower randomness (weight_softening = 0)
- Longer planning horizon
- More distance-sensitive

## Implementation Plan

### Phase 1: Fix Cognitive Pressure
1. Implement bounded time stress with decay
2. Add conflict decay mechanism
3. Add social pressure calculation
4. Ensure total pressure is bounded [0.0, 1.0]

### Phase 2: Fix S2 Activation
1. Implement proper sigmoid function
2. Add bounded individual modifiers
3. Ensure probabilistic activation
4. Test activation rates over time

### Phase 3: Fix S2 Capability
1. Lower connection requirements
2. Add education-based capability
3. Make capability more realistic

### Phase 4: Fix Move Chance
1. Implement S1/S2 move chance differences
2. Add deliberation boost for S2
3. Ensure meaningful behavioral differences

### Phase 5: Fix Route Selection
1. Implement agent-specific parameter modification
2. Avoid global parameter changes
3. Ensure proper parameter restoration

## Expected Behavior

### **Short-term (0-20 timesteps)**
- Pressure increases from 0.0 to ~0.6
- S2 activation rate: 20-60%
- Clear S1/S2 behavioral differences

### **Medium-term (20-50 timesteps)**
- Pressure stabilizes around 0.4-0.7
- S2 activation rate: 40-80%
- Sustained behavioral differences

### **Long-term (50+ timesteps)**
- Pressure remains bounded
- S2 activation rate: 30-70%
- No runaway effects

## Validation Criteria

1. **Pressure Bounds**: Always 0.0 ≤ pressure ≤ 1.0
2. **Activation Probability**: Always 0.0 ≤ P(S2) ≤ 1.0
3. **Behavioral Differences**: S1 ≠ S2 in move rates and route selection
4. **Stability**: No runaway effects over long simulations
5. **Realism**: Matches psychological stress patterns

## Mathematical Properties

### **Monotonicity**
- Pressure increases with conflict intensity
- Pressure increases with connectivity
- Pressure decreases with recovery time

### **Boundedness**
- All components are bounded
- Total pressure is bounded
- Activation probability is bounded

### **Continuity**
- Smooth transitions between S1 and S2
- No sudden jumps in behavior
- Realistic psychological dynamics

This design ensures mathematically sound, behaviorally realistic, and computationally stable S1/S2 system.




