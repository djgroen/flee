# Presentation vs Code Implementation Comparison

## ✅ What Matches

### 1. Core Mathematical Structure
**Presentation:**
- Ψ(x; α) = 1/(1 + e^(-αx)) - Cognitive Capacity
- Ω(c; β) = 1/(1 + e^(-β(1-c))) - Structural Opportunity

**Code (`flee/s1s2_model.py`):**
- ✅ `calculate_cognitive_capacity(education, alpha)` → `sigmoid(alpha * education)`
- ✅ `calculate_structural_opportunity(conflict, beta)` → `sigmoid(beta * (1.0 - conflict))`

**Status:** ✅ **MATCHES** (except input variable - see below)

### 2. Parameter Defaults
**Presentation:**
- α = 2.0 (FREE)
- β = 2.0 (FREE)
- η = 4.0 (FIXED)
- θ = 0.5 (FIXED)
- p_s2 = 0.8 (FIXED)

**Code:**
- ✅ `alpha: float = 2.0`
- ✅ `beta: float = 2.0`
- ✅ `eta: float = 4.0`
- ✅ `theta: float = 0.5`
- ✅ `p_s2: float = 0.8`

**Status:** ✅ **MATCHES**

### 3. Multiplicative Form
**Presentation:**
- P_S2 = Ψ × Ω

**Code:**
- Has: P_S2 = Ψ × Ω × pressure_activation

**Status:** ⚠️ **PARTIAL MATCH** (see discrepancy below)

---

## ❌ Key Discrepancies

### 1. **Experience vs Education** (CRITICAL)

**Presentation Says:**
> "In survival contexts, relevant experience matters more"
> 
> "Experience-based capacity index: x = f(prior displacement, local knowledge, conflict exposure, age, ...)"
>
> "Urban educated professional: High education, **low survival capacity**"
>
> "Tribal elder: Low education, **high survival capacity**"

**Code Has:**
```python
def calculate_cognitive_capacity(education: float, alpha: float = 2.0) -> float:
    """Calculate cognitive capacity (Psi)."""
    return sigmoid(alpha * education)  # ❌ Uses education directly
```

**Problem:** Code uses `education` directly, not an experience-based index `x`.

**What Should Be:**
```python
def calculate_cognitive_capacity(experience_index: float, alpha: float = 2.0) -> float:
    """
    Calculate cognitive capacity from experience-based index.
    
    experience_index = f(
        prior_displacement,
        local_knowledge,
        conflict_exposure,
        age,
        connections,
        ...
    )
    """
    return sigmoid(alpha * experience_index)
```

**Impact:** ⚠️ **HIGH** - This contradicts the presentation's core insight about experience over education.

---

### 2. **S2 Activation Formula** (CRITICAL)

**Presentation Shows:**
```
P_S2 = Ψ × Ω
```

**Code Has:**
```python
def calculate_s2_activation(psi, omega, conflict, theta=0.5, eta=4.0):
    pressure_activation = sigmoid_with_steepness(conflict - theta, eta)
    return psi * omega * pressure_activation  # ❌ Extra term!
```

**Problem:** Code has an extra `pressure_activation` term that multiplies the result.

**What Presentation Describes:**
- Simple multiplication: P_S2 = Ψ × Ω
- The sigmoid functions in Ψ and Ω already handle the conflict/experience relationship

**What Code Does:**
- P_S2 = Ψ × Ω × σ(η(conflict - θ))
- This adds a third multiplicative term

**Impact:** ⚠️ **HIGH** - This changes the mathematical model from what's presented.

---

### 3. **Simplified vs Full Model**

**Presentation:**
- Shows simplified model: P_S2 = Ψ × Ω
- Mentions 5 parameters but says 3 are fixed (η, θ, p_s2)
- Core insight: Only 2 free parameters (α, β)

**Code:**
- Implements full 5-parameter model
- All parameters are configurable (though defaults match presentation)
- The `pressure_activation` term uses η and θ

**Question:** Is the presentation showing a simplified version, or is the code implementing something different?

---

## 🔍 Detailed Analysis

### Current Code Implementation

```python
# Step 1: Cognitive Capacity
psi = sigmoid(alpha * education)  # ❌ Should be experience_index

# Step 2: Structural Opportunity  
omega = sigmoid(beta * (1.0 - conflict))  # ✅ Correct

# Step 3: S2 Activation
pressure_activation = sigmoid(eta * (conflict - theta))  # ❌ Extra term
p_s2_active = psi * omega * pressure_activation  # ❌ Should be psi * omega

# Step 4: Final Move Probability
p_move = (1.0 - p_s2_active) * movechance + p_s2_active * p_s2  # ✅ Correct
```

### What Presentation Describes

```python
# Step 1: Cognitive Capacity (from experience)
x = experience_index(prior_displacement, local_knowledge, ...)
psi = sigmoid(alpha * x)  # ✅ Experience-based

# Step 2: Structural Opportunity
omega = sigmoid(beta * (1.0 - conflict))  # ✅ Correct

# Step 3: S2 Activation (simple multiplication)
p_s2_active = psi * omega  # ✅ Simple form

# Step 4: Final Move Probability
p_move = (1.0 - p_s2_active) * movechance + p_s2_active * p_s2  # ✅ Correct
```

---

## 📋 Recommendations

### Option 1: Align Code with Presentation (Recommended)

1. **Replace education with experience index:**
   ```python
   def calculate_experience_index(agent):
       """Calculate experience-based capacity index."""
       prior_displacement = agent.timesteps_since_departure
       local_knowledge = agent.attributes.get('local_knowledge', 0.0)
       conflict_exposure = agent.attributes.get('conflict_exposure', 0.0)
       connections = agent.attributes.get('connections', 0)
       age_factor = agent.attributes.get('age_factor', 0.5)
       
       # Combine into experience index
       x = (prior_displacement * 0.2 + 
            local_knowledge * 0.3 + 
            conflict_exposure * 0.2 + 
            connections * 0.1 + 
            age_factor * 0.2)
       return x
   ```

2. **Simplify S2 activation:**
   ```python
   def calculate_s2_activation(psi: float, omega: float) -> float:
       """Simple multiplicative form as in presentation."""
       return psi * omega  # No pressure_activation term
   ```

### Option 2: Update Presentation to Match Code

If the code's extra `pressure_activation` term is intentional and scientifically justified, update the presentation to show:

```
P_S2 = Ψ × Ω × σ(η(c - θ))
```

Where:
- σ(η(c - θ)) is the pressure activation term
- This adds conflict intensity as a direct modulator

---

## 🎯 Action Items

1. **Decide on experience vs education:**
   - [ ] Keep education (simpler, but contradicts presentation)
   - [ ] Switch to experience index (matches presentation, more complex)

2. **Decide on S2 activation formula:**
   - [ ] Simplify to P_S2 = Ψ × Ω (matches presentation)
   - [ ] Keep P_S2 = Ψ × Ω × pressure_activation (more complex, needs justification)

3. **Document the decision:**
   - [ ] Update code comments to explain chosen approach
   - [ ] Update presentation if code is correct
   - [ ] Create migration guide if changing code

---

## 📊 Summary

| Aspect | Presentation | Code | Status |
|--------|--------------|------|--------|
| Ψ formula | sigmoid(αx) | sigmoid(α·education) | ⚠️ Input differs |
| Ω formula | sigmoid(β(1-c)) | sigmoid(β(1-c)) | ✅ Matches |
| P_S2 formula | Ψ × Ω | Ψ × Ω × pressure | ❌ Extra term |
| Parameters | 2 free (α,β) | 5 configurable | ⚠️ All configurable |
| Experience | Required | Not used | ❌ Missing |

**Overall:** Code implements a **more complex version** than the presentation describes. Need to decide which is correct.

