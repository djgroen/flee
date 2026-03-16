# S1/S2 Logical Flow Analysis

## Complete Flow Diagram

```
SIMULATION TIMESTEP
        ↓
    Ecosystem.evolve()
        ↓
    For each agent: agent.evolve()
        ↓
    agent.update_social_connectivity()  # Update connections based on location
        ↓
    moving.calculateMoveChance(agent, ForceTownMove, time)
        ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 1. Check if TwoSystemDecisionMaking is enabled         │
    │    if SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False) │
    └─────────────────────────────────────────────────────────┘
        ↓ (if True)
    ┌─────────────────────────────────────────────────────────┐
    │ 2. Calculate cognitive pressure                        │
    │    cognitive_pressure = agent.calculate_cognitive_pressure(time) │
    └─────────────────────────────────────────────────────────┘
        ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 3. Check if agent is S2 capable                        │
    │    system2_capable = agent.get_system2_capable()       │
    │    Returns: connections >= 2 OR timesteps_since_departure >= 5 │
    └─────────────────────────────────────────────────────────┘
        ↓ (if True)
    ┌─────────────────────────────────────────────────────────┐
    │ 4. Calculate S2 activation probability                 │
    │    system2_active = calculate_systematic_s2_activation() │
    └─────────────────────────────────────────────────────────┘
        ↓ (if system2_active)
    ┌─────────────────────────────────────────────────────────┐
    │ 5. Pre-calculate route for S2                          │
    │    provisional_route = selectRoute(agent, time, system2_active=True) │
    │    - Modifies parameters: AwarenessLevel++, WeightSoftening=0, etc. │
    │    - Restores parameters after route calculation       │
    └─────────────────────────────────────────────────────────┘
        ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 6. Return move chance                                  │
    │    S2: return 1.0, system2_active                     │
    │    S1: return location.movechance, system2_active      │
    └─────────────────────────────────────────────────────────┘
        ↓
    agent.evolve() continues...
        ↓
    Update agent.cognitive_state based on system2_active
        ↓
    Handle movement if movechance > random()
```

## Detailed Component Analysis

### 1. Cognitive Pressure Calculation
```python
def calculate_cognitive_pressure(self, time: int) -> float:
    # Get conflict intensity (0.0 to 1.0)
    conflict_intensity = max(0.0, getattr(self.location, 'conflict', 0.0))
    
    # Get connectivity (0 to 10, normalized to 0.0 to 1.0)
    connectivity = min(1.0, self.attributes.get("connections", 0) / 10.0)
    
    # Calculate recovery period (days since last major conflict)
    recovery_period = 30.0  # Default recovery period
    if hasattr(self.location, 'time_of_conflict') and self.location.time_of_conflict >= 0:
        recovery_period = max(1.0, time - self.location.time_of_conflict)
    
    # Enhanced cognitive pressure formula with base pressure
    # Base pressure from connectivity and time (agents get more stressed over time)
    base_pressure = connectivity * 0.3 + (time / 20.0) * 0.2  # Time-based stress
    
    # Conflict-induced pressure
    conflict_pressure = (conflict_intensity * connectivity) / (recovery_period / 30.0)
    
    # Total cognitive pressure
    cognitive_pressure = base_pressure + conflict_pressure
    
    return cognitive_pressure
```

**Issues Found:**
- ❌ **Time-based stress increases indefinitely**: `(time / 20.0) * 0.2` means pressure keeps growing
- ❌ **Recovery period logic is flawed**: Uses `time_of_conflict` which may not be set properly
- ❌ **Base pressure can exceed 1.0**: `connectivity * 0.3 + (time / 20.0) * 0.2` can be > 1.0

### 2. S2 Capability Check
```python
def get_system2_capable(self) -> bool:
    # System 2 capability based on connections and experience
    min_connections = 2
    min_travel_experience = 5  # days since departure
    
    has_connections = self.attributes.get("connections", 0) >= min_connections
    has_experience = self.timesteps_since_departure >= min_travel_experience
    
    return has_connections or has_experience
```

**Issues Found:**
- ❌ **New agents can't use S2**: `timesteps_since_departure` starts at 0, so new agents need 5+ connections
- ❌ **Logic may be too restrictive**: Most agents will be S2 capable very quickly

### 3. S2 Activation Probability
```python
def calculate_systematic_s2_activation(agent, pressure, base_threshold, time):
    # Base sigmoid activation curve
    k = 8.0  # Steepness parameter
    base_prob = 1.0 / (1.0 + math.exp(-k * (pressure - base_threshold)))
    
    # Individual difference modifiers
    education_level = agent.attributes.get('education_level', 0.5)
    education_boost = education_level * 0.1
    
    stress_tolerance = agent.attributes.get('stress_tolerance', 0.5)
    stress_modifier = stress_tolerance * 0.05
    
    # Social support modifier
    connections = agent.attributes.get('connections', 5)
    social_support = min(connections * 0.02, 0.1)
    
    # Time-based modifiers
    fatigue_penalty = min(time * 0.002, 0.1)
    learning_boost = min(time * 0.001, 0.05)
    
    # Combine all modifiers
    final_prob = base_prob + education_boost + social_support - fatigue_penalty + learning_boost + stress_modifier
    
    # Ensure probability stays in valid range
    final_prob = max(0.0, min(1.0, final_prob))
    
    # Random activation based on probability
    return random.random() < final_prob
```

**Issues Found:**
- ❌ **Fatigue penalty increases indefinitely**: `time * 0.002` means agents get more tired over time
- ❌ **Learning boost is minimal**: `time * 0.001` is very small
- ❌ **Default connections = 5**: This gives all agents social support by default

### 4. Route Selection Differences
```python
# S2 route selection modifies parameters:
if SimulationSettings.move_rules["TwoSystemDecisionMaking"] and system2_active:
    # Store original values
    original_params['awareness_level'] = SimulationSettings.move_rules["AwarenessLevel"]
    original_params['weight_softening'] = SimulationSettings.move_rules["WeightSoftening"]
    original_params['distance_power'] = SimulationSettings.move_rules["DistancePower"]
    original_params['pruning_threshold'] = SimulationSettings.move_rules["PruningThreshold"]
    
    # Set System 2 parameters (more deliberative thinking)
    SimulationSettings.move_rules["AwarenessLevel"] = min(3, original_params['awareness_level'] + 1)
    SimulationSettings.move_rules["WeightSoftening"] = 0.0  # Less randomness
    SimulationSettings.move_rules["DistancePower"] = 1.2  # More distance-sensitive
    SimulationSettings.move_rules["PruningThreshold"] = 1.0  # Disable pruning
    
    # ... route calculation ...
    
    # Restore original parameters
    SimulationSettings.move_rules["AwarenessLevel"] = original_params['awareness_level']
    SimulationSettings.move_rules["WeightSoftening"] = original_params['weight_softening']
    SimulationSettings.move_rules["DistancePower"] = original_params['distance_power']
    SimulationSettings.move_rules["PruningThreshold"] = original_params['pruning_threshold']
```

**Issues Found:**
- ❌ **Global parameter modification**: Changes affect ALL agents, not just the current one
- ❌ **Race condition potential**: Multiple agents could modify parameters simultaneously

## Critical Issues Summary

1. **Cognitive Pressure Issues:**
   - Time-based stress increases indefinitely
   - Recovery period logic is flawed
   - Base pressure can exceed 1.0

2. **S2 Capability Issues:**
   - New agents can't use S2 initially
   - Logic may be too restrictive

3. **S2 Activation Issues:**
   - Fatigue penalty increases indefinitely
   - Learning boost is minimal
   - Default connections = 5 gives all agents social support

4. **Route Selection Issues:**
   - Global parameter modification affects all agents
   - Potential race conditions

5. **Move Chance Issues:**
   - S2 agents always get 100% move chance
   - S1 agents get location.movechance (often 0.0 in high conflict)
   - No gradual transition between S1 and S2

## Recommendations

1. **Fix cognitive pressure calculation:**
   - Cap time-based stress
   - Fix recovery period logic
   - Ensure pressure stays in valid range

2. **Fix S2 capability:**
   - Allow new agents to use S2
   - Make capability more realistic

3. **Fix S2 activation:**
   - Cap fatigue penalty
   - Increase learning boost
   - Fix default connections

4. **Fix route selection:**
   - Use agent-specific parameters
   - Avoid global modifications

5. **Fix move chance:**
   - Add gradual transition between S1 and S2
   - Make S1 move chance more realistic




