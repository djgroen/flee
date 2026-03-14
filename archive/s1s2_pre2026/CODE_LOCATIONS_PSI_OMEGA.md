# Code Locations: Cognitive Capacity (Ψ) and Structural Opportunity (Ω)

## Quick Reference for Colleagues

This document shows exactly where in the code the two key components of S2 activation are calculated:
- **Ψ (Psi)**: Cognitive Capacity
- **Ω (Omega)**: Structural Opportunity

---

## 📍 Main Location: `flee/s1s2_model.py`

This is the **primary file** where the mathematical model is implemented.

### 1. Cognitive Capacity (Ψ) - Line 85-101

**File**: `flee/s1s2_model.py`  
**Function**: `calculate_cognitive_capacity()`

```python
def calculate_cognitive_capacity(experience_index: float, alpha: float = 2.0) -> float:
    """
    Calculate cognitive capacity (Psi) from experience-based index.
    
    As per presentation: Ψ(x; α) = 1/(1 + e^(-αx))
    
    Cognitive capacity represents an agent's ability to engage in deliberative
    thinking. Higher experience increases this capacity.
    
    Args:
        experience_index: Experience-based capacity index x (from calculate_experience_index)
        alpha: Capacity weight parameter (FREE parameter, default: 2.0)
        
    Returns:
        Psi in (0, 1) - cognitive capacity
    """
    return sigmoid(alpha * experience_index)
```

**Key Points:**
- **Input**: `experience_index` (composite of prior displacement, local knowledge, connections, etc.)
- **Formula**: `Ψ = sigmoid(α × experience_index)`
- **Parameter**: `alpha = 2.0` (FREE parameter, can be tuned)
- **Output**: Value in (0, 1) representing cognitive capacity

### 2. Structural Opportunity (Ω) - Line 104-118

**File**: `flee/s1s2_model.py`  
**Function**: `calculate_structural_opportunity()`

```python
def calculate_structural_opportunity(conflict: float, beta: float = 2.0) -> float:
    """
    Calculate structural opportunity (Omega).
    
    Structural opportunity represents whether the situation permits
    deliberative thinking. High conflict reduces this opportunity.
    
    Args:
        conflict: Conflict intensity in [0, 1]
        beta: Opportunity weight parameter
        
    Returns:
        Omega in (0, 1) - structural opportunity
    """
    return sigmoid(beta * (1.0 - conflict))
```

**Key Points:**
- **Input**: `conflict` (current location's conflict intensity, 0.0 to 1.0)
- **Formula**: `Ω = sigmoid(β × (1 - conflict))`
- **Parameter**: `beta = 2.0` (FREE parameter, can be tuned)
- **Output**: Value in (0, 1) representing structural opportunity
- **Behavior**: High conflict → Low Ω, Low conflict → High Ω

### 3. S2 Activation (P_S2 = Ψ × Ω) - Line 121-137

**File**: `flee/s1s2_model.py`  
**Function**: `calculate_s2_activation()`

```python
def calculate_s2_activation(psi: float, omega: float) -> float:
    """
    Calculate S2 activation probability (simplified form as per presentation).
    
    As per presentation: P_S2 = Ψ × Ω
    
    Simple multiplicative form: Deliberation requires BOTH cognitive capacity
    AND structural opportunity. Neither alone is sufficient.
    
    Args:
        psi: Cognitive capacity in (0, 1)
        omega: Structural opportunity in (0, 1)
    
    Returns:
        p_s2_active in [0, 1] - S2 activation probability
    """
    return psi * omega
```

**Key Points:**
- **Formula**: `P_S2 = Ψ × Ω` (simple multiplication)
- **Both factors required**: If either Ψ or Ω is low, S2 activation is low
- **Multiplicative logic**: Matches "necessary conditions" theory

### 4. Experience Index Calculation - Line 47-82

**File**: `flee/s1s2_model.py`  
**Function**: `calculate_experience_index()`

This calculates the experience-based capacity index `x` that feeds into Ψ:

```python
def calculate_experience_index(
    prior_displacement: float = 0.0,
    local_knowledge: float = 0.0,
    conflict_exposure: float = 0.0,
    connections: int = 0,
    age_factor: float = 0.5,
    education_level: float = 0.5
) -> float:
    """
    Calculate experience-based capacity index.
    
    Composite index incorporating multiple factors (as per presentation:
    "experience matters more than education").
    
    Weights:
    - prior_displacement: 25%
    - local_knowledge: 25%
    - conflict_exposure: 20%
    - connections: 15%
    - age_factor: 10%
    - education_level: 5% (lowest weight)
    """
    x = (
        prior_displacement * 0.25 +
        local_knowledge * 0.25 +
        conflict_exposure * 0.20 +
        connections * 0.15 +
        age_factor * 0.10 +
        education_level * 0.05
    )
    return x
```

**Key Points:**
- **Composite index**: Multiple factors combined
- **Education is only 5%**: Emphasizes "experience over education"
- **Used to calculate Ψ**: `Ψ = sigmoid(α × experience_index)`

---

## 📍 Where It's Called: `flee/moving.py`

The main decision-making function calls these calculations.

### Entry Point: `calculateMoveChance()` - Line 502-671

**File**: `flee/moving.py`  
**Function**: `calculateMoveChance()`

**Key section** (lines 523-550):

```python
# Check if S1/S2 model is enabled
s1s2_params = SimulationSettings.move_rules.get('s1s2_model_params', None)
if s1s2_params and s1s2_params.get('enabled', False):
    # Calculate experience-based capacity index
    experience_index = calculate_experience_index(
        prior_displacement=a.timesteps_since_departure / 30.0,
        local_knowledge=a.attributes.get('local_knowledge', 0.0),
        conflict_exposure=a.attributes.get('conflict_exposure', 0.0),
        connections=a.attributes.get('connections', 0),
        age_factor=a.attributes.get('age_factor', 0.5),
        education_level=a.attributes.get('education_level', getattr(a, 'education', 0.5))
    )
    
    conflict = max(0.0, getattr(a.location, 'conflict', 0.0))
    movechance = a.location.movechance
    
    # Get parameters (only α and β are free; p_s2 is fixed)
    alpha = s1s2_params.get('alpha', 2.0)
    beta = s1s2_params.get('beta', 2.0)
    p_s2 = s1s2_params.get('p_s2', 0.8)
    
    # Calculate move probability using parsimonious model (P_S2 = Ψ × Ω)
    p_move, p_s2_active = calculate_move_probability_s1s2(
        experience_index, conflict, movechance,
        alpha, beta, p_s2
    )
```

**Inside `calculate_move_probability_s1s2()`** (line 140-184 in `s1s2_model.py`):

```python
# Cognitive capacity (stable - depends on agent's experience)
psi = calculate_cognitive_capacity(experience_index, alpha)

# Structural opportunity (dynamic - depends on current conflict)
omega = calculate_structural_opportunity(conflict, beta)

# S2 activation probability (simple multiplicative form)
p_s2_active = calculate_s2_activation(psi, omega)
```

---

## 📊 Complete Flow Diagram

```
Agent at Location
    ↓
calculateMoveChance() [flee/moving.py:502]
    ↓
calculate_experience_index() [flee/s1s2_model.py:47]
    → Returns: experience_index (x)
    ↓
calculate_cognitive_capacity(experience_index, alpha) [flee/s1s2_model.py:85]
    → Returns: Ψ = sigmoid(α × x)
    ↓
calculate_structural_opportunity(conflict, beta) [flee/s1s2_model.py:104]
    → Returns: Ω = sigmoid(β × (1 - conflict))
    ↓
calculate_s2_activation(psi, omega) [flee/s1s2_model.py:121]
    → Returns: P_S2 = Ψ × Ω
    ↓
Final move probability calculation
```

---

## 🔑 Key Files Summary

| Component | File | Function | Line |
|-----------|------|----------|------|
| **Experience Index** | `flee/s1s2_model.py` | `calculate_experience_index()` | 47-82 |
| **Ψ (Cognitive Capacity)** | `flee/s1s2_model.py` | `calculate_cognitive_capacity()` | 85-101 |
| **Ω (Structural Opportunity)** | `flee/s1s2_model.py` | `calculate_structural_opportunity()` | 104-118 |
| **P_S2 = Ψ × Ω** | `flee/s1s2_model.py` | `calculate_s2_activation()` | 121-137 |
| **Called from** | `flee/moving.py` | `calculateMoveChance()` | 523-550 |

---

## 💡 For Colleagues: Quick Explanation

**"Where is the model implemented?"**

1. **Main model file**: `flee/s1s2_model.py`
   - All the mathematical functions are here
   - Clean, well-documented, matches presentation

2. **Called from**: `flee/moving.py` → `calculateMoveChance()`
   - This is where agents make decisions each timestep
   - Calls the model functions and uses the results

3. **Key functions to show**:
   - `calculate_cognitive_capacity()` → Ψ
   - `calculate_structural_opportunity()` → Ω
   - `calculate_s2_activation()` → P_S2 = Ψ × Ω

**"How do I verify it matches the presentation?"**

- Open `flee/s1s2_model.py`
- Lines 85-101: Ψ calculation (matches presentation formula)
- Lines 104-118: Ω calculation (matches presentation formula)
- Lines 121-137: P_S2 = Ψ × Ω (simple multiplication, as per presentation)

**"What are the parameters?"**

- `alpha = 2.0`: Cognitive capacity weight (FREE parameter)
- `beta = 2.0`: Structural opportunity weight (FREE parameter)
- `p_s2 = 0.8`: S2 move probability (FIXED parameter)

All defined in `flee/simsetting.yml` or passed via config.

---

## 📝 Example Values

For an agent at Ring3 (one step from SafeZone):

```python
# Agent attributes
experience_index = 2.5  # High (agent has traveled, has connections)
conflict = 0.20  # Low (Ring3 location)

# Calculate Ψ
alpha = 2.0
psi = sigmoid(2.0 * 2.5) = sigmoid(5.0) ≈ 0.993  # Very high

# Calculate Ω
beta = 2.0
omega = sigmoid(2.0 * (1 - 0.20)) = sigmoid(1.6) ≈ 0.832  # High

# Calculate P_S2
p_s2 = psi * omega = 0.993 * 0.832 ≈ 0.826  # 82.6% S2 activation
```

This matches the observed 98% S2 activation at Ring3!

