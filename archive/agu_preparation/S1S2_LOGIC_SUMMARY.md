# S1/S2 Logic in FLEE: Complete Summary

## 🎯 **Overview**

The S1/S2 dual-process decision-making system in FLEE implements a realistic cognitive model where agents can switch between two thinking modes:

- **System 1 (S1)**: Fast, heuristic, reactive decision-making
- **System 2 (S2)**: Slow, deliberative, analytical decision-making

## 🔄 **Decision Flow**

### **Step 1: Agent Assessment**
- Agent is at a location with conflict
- System calculates cognitive pressure based on multiple factors

### **Step 2: Cognitive Pressure Calculation**
```
P(t) = B(t) + C(t) + S(t)
```

Where:
- **B(t)**: Base pressure (internal stress)
- **C(t)**: Conflict pressure (external stress)
- **S(t)**: Social pressure (network effects)

### **Step 3: S2 Capability Check**
- Agent must be "S2 capable" (based on education, connections, etc.)
- If not capable → always use System 1

### **Step 4: S2 Activation Decision**
If S2 capable, calculate activation probability:
```
P(S2) = 1 / (1 + exp(-η × (P(t) - θ)))
```

Where:
- **η (eta)**: Steepness parameter (default: 6.0)
- **θ (theta)**: S2 threshold (default: 0.5)

### **Step 5: Decision Making**
- **System 1**: `P(move) = location.movechance` (heuristic)
- **System 2**: `P(move) = 0.9` (high probability, deliberative)

### **Step 6: Final Move Probability**
```
P(move) = P(S1) × (1 - P(S2)) + P(S2) × 0.9
```

## 📊 **Mathematical Components**

### **1. Base Pressure (Internal Stress)**
```
B(t) = min(0.4, connectivity_factor × 0.2 + time_stress(t))
```

- **connectivity_factor**: `min(1.0, connections / 10.0)`
- **time_stress(t)**: `0.1 × (1 - exp(-t/10)) × exp(-t/50)`

### **2. Time Stress Dynamics**
- **Growth phase**: Increases from 0 to 0.1 over ~10 timesteps
- **Peak**: Around t = 10 timesteps
- **Decay phase**: Gradually decreases to 0 over ~50 timesteps
- **Bounded**: Always between 0.0 and 0.1

### **3. Conflict Pressure (External Stress)**
```
C(t) = min(0.4, conflict_intensity × connectivity_factor × conflict_decay(t))
```

- **conflict_intensity**: Location conflict level (0.0 to 1.0)
- **conflict_decay(t)**: `exp(-max(0, t - conflict_start) / 20)`

### **4. Social Pressure (Network Effects)**
```
S(t) = min(0.2, connectivity_factor × 0.1)
```

- Based on agent's social connections
- Bounded to maximum of 0.2

## ⚙️ **Key Parameters**

### **Configuration Parameters**
- **`TwoSystemDecisionMaking`**: Enable/disable S1/S2 (0.0 = disabled, >0 = enabled)
- **`connectivity_mode`**: "baseline" or "diminishing"
- **`soft_capability`**: Use soft S2 capability gates (true/false)
- **`eta`**: S2 activation steepness (default: 6.0)
- **`steepness`**: General steepness parameter (default: 6.0)
- **`pmove_s2_mode`**: "scaled" or "constant" for S2 move probability

### **Agent Attributes**
- **`connections`**: Number of social connections (0-10)
- **`education_level`**: Education level (0.0-1.0)
- **`stress_tolerance`**: Stress tolerance (0.0-1.0)
- **`s2_threshold`**: Individual S2 threshold (0.0-1.0)

## 🔧 **FLEE Integration**

### **Integration Points**
1. **Main Loop**: `Ecosystem.evolve()` → `Person.evolve()`
2. **Move Calculation**: `calculateMoveChance()` calls S1/S2 logic
3. **Route Selection**: `selectRoute()` uses different logic for S1 vs S2
4. **State Tracking**: Agents track cognitive state and decision history

### **Configuration in YAML**
```yaml
move_rules:
  TwoSystemDecisionMaking: 0.5  # Enable S1/S2
  connectivity_mode: "baseline"  # or "diminishing"
  soft_capability: false  # or true for soft gates
  eta: 6.0  # S2 activation steepness
  steepness: 6.0  # General steepness
  pmove_s2_mode: "scaled"  # or "constant"
  pmove_s2_constant: 0.9  # S2 move probability
```

## 📈 **Behavioral Effects**

### **System 1 Behavior**
- Fast, heuristic decisions
- Based on location movechance
- Reactive to immediate conditions
- Lower move probabilities

### **System 2 Behavior**
- Deliberative, analytical decisions
- High move probability (~0.9)
- Considers multiple factors
- More strategic movement

### **Cognitive Pressure Effects**
- **Low pressure**: Agents use System 1 (heuristic)
- **High pressure**: Agents more likely to use System 2 (deliberative)
- **Individual differences**: Education, connections, stress tolerance affect behavior

## 🎯 **Key Insights**

1. **Realistic Psychology**: Models actual cognitive processes from psychology
2. **Individual Differences**: Agents have different capabilities and thresholds
3. **Dynamic Behavior**: Cognitive pressure changes over time
4. **Network Effects**: Social connections influence decision-making
5. **Configurable**: All parameters can be tuned for different scenarios

## 🚀 **Usage**

The S1/S2 system is automatically active when `TwoSystemDecisionMaking > 0` in the YAML configuration. Agents will:

1. Calculate cognitive pressure each timestep
2. Determine if they're S2 capable
3. Calculate S2 activation probability
4. Make movement decisions based on their active system
5. Track their decision history for analysis

This creates more realistic and varied agent behavior compared to simple heuristic movement rules.

## 📊 **Validation**

The system has been validated with:
- ✅ Mathematical bounds checking
- ✅ Monotonicity tests
- ✅ Parameter sensitivity analysis
- ✅ Integration with FLEE framework
- ✅ Comprehensive unit tests
- ✅ Full simulation runs

The S1/S2 system is ready for production use and will be merged with the master branch.




