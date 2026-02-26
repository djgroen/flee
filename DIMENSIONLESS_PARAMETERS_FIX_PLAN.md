# 🔧 DIMENSIONLESS PARAMETERS FIX PLAN

## 🚨 **PROBLEMS IDENTIFIED**

### **1. Lack of Variation - The Core Issue**
Looking at the figures, the dimensionless parameters show **constant values across scenarios**:
- **Quality Improvement (ΔQ*)**: Exactly 0.200 for all scenarios (flat green bars)
- **Temporal Separation (Δτ*)**: Exactly 0.518 for all scenarios (identical red bars)  
- **Connectivity Threshold**: Sharp binary cutoff at 0.700 (no variation)
- **Cognitive Threshold**: Single peak distribution (no scaling)

### **2. Root Causes**:
1. **Insufficient scenario diversity**: Only 3 scenario types, similar parameters
2. **Fixed agent profiles**: All agents have same cognitive parameters within type
3. **Binary S1/S2 activation**: No continuous variation in cognitive effort
4. **Artificial parameter choices**: Hardcoded thresholds not derived from data
5. **Small sample sizes**: 2.5% S2 usage = insufficient data for scaling laws

### **3. Mathematical Issues**:
- **No true scaling**: Parameters don't vary with system size or conditions
- **Artificial normalization**: Dividing by arbitrary constants
- **Missing physical meaning**: Parameters don't represent real dimensionless groups
- **No universality**: Laws don't generalize across different conditions

---

## 🎯 **COMPREHENSIVE FIX PLAN**

### **Phase 1: Immediate Fixes (This Week)**

#### **1.1 Increase Scenario Diversity**
```python
# Create 10+ distinct scenarios with varying:
scenarios = [
    # Network topology variations
    {"type": "linear", "length": 3, "conflict": 0.9},
    {"type": "linear", "length": 5, "conflict": 0.7}, 
    {"type": "star", "branches": 4, "conflict": 0.8},
    {"type": "star", "branches": 8, "conflict": 0.6},
    {"type": "grid", "size": "3x3", "conflict": 0.5},
    
    # Population size variations  
    {"agents": 25, "type": "evacuation"},
    {"agents": 50, "type": "evacuation"},
    {"agents": 100, "type": "evacuation"},
    {"agents": 200, "type": "evacuation"},
    
    # Stress level variations
    {"conflict_intensity": 0.3, "type": "choice"},
    {"conflict_intensity": 0.6, "type": "choice"},
    {"conflict_intensity": 0.9, "type": "choice"},
    
    # Time pressure variations
    {"duration": 10, "escalation": True},
    {"duration": 20, "escalation": False},
    {"duration": 30, "escalation": True},
]
```

#### **1.2 Fix S2 Activation Rates**
```python
# Test multiple S2 thresholds to get 10-30% S2 activation
s2_thresholds = [0.2, 0.3, 0.4, 0.5]  # Instead of fixed 0.6

# Implement continuous S2 probability
def s2_activation_probability(pressure, connections, day):
    base_prob = sigmoid(pressure - 0.4)  # Smooth curve
    social_boost = min(connections * 0.05, 0.2)
    fatigue_penalty = min(day * 0.01, 0.3)
    return base_prob + social_boost - fatigue_penalty
```

#### **1.3 Add Agent Diversity**
```python
# Create 5 cognitive profiles instead of 2
cognitive_profiles = [
    {"s2_threshold": 0.2, "connections": 8, "name": "analytical"},
    {"s2_threshold": 0.3, "connections": 6, "name": "balanced_high"},  
    {"s2_threshold": 0.5, "connections": 4, "name": "balanced_mid"},
    {"s2_threshold": 0.7, "connections": 3, "name": "intuitive_social"},
    {"s2_threshold": 0.8, "connections": 1, "name": "pure_intuitive"}
]
```

### **Phase 2: Proper Dimensionless Analysis (Next Week)**

#### **2.1 Define Meaningful Dimensionless Groups**
Based on refugee decision-making physics:

```python
# 1. Stress-to-Capacity Ratio (Π₁)
Pi_1 = (conflict_intensity * population_density) / (social_support * resources)

# 2. Time-to-Decision Ratio (Π₂)  
Pi_2 = decision_time / evacuation_window

# 3. Network Efficiency Parameter (Π₃)
Pi_3 = (shortest_path_length * congestion) / (network_connectivity * capacity)

# 4. Cognitive Load Parameter (Π₄)
Pi_4 = (information_complexity * time_pressure) / (cognitive_capacity * experience)
```

#### **2.2 Implement Proper Scaling Analysis**
```python
def analyze_scaling_laws(scenarios_data):
    """Find true scaling relationships"""
    
    # Group scenarios by dimensionless parameter ranges
    for pi_1_range in [(0, 0.3), (0.3, 0.7), (0.7, 1.0)]:
        for pi_2_range in [(0, 0.5), (0.5, 1.0)]:
            
            # Find scenarios in this parameter space
            matching_scenarios = filter_scenarios(pi_1_range, pi_2_range)
            
            # Compute response variables
            s2_usage_rate = compute_s2_rate(matching_scenarios)
            evacuation_efficiency = compute_efficiency(matching_scenarios)
            decision_quality = compute_quality(matching_scenarios)
            
            # Test for scaling relationships
            test_power_law(pi_1, s2_usage_rate)
            test_exponential(pi_2, evacuation_efficiency)
```

#### **2.3 Statistical Validation**
```python
# Add proper statistical analysis
from scipy import stats
import numpy as np

def validate_scaling_law(x_data, y_data, law_type="power"):
    """Validate scaling law with statistics"""
    
    if law_type == "power":
        # Test y = A * x^B
        log_x, log_y = np.log(x_data), np.log(y_data)
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
        
    elif law_type == "exponential":
        # Test y = A * exp(B*x)
        log_y = np.log(y_data)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, log_y)
    
    return {
        'r_squared': r_value**2,
        'p_value': p_value,
        'confidence_interval': compute_ci(slope, std_err),
        'is_significant': p_value < 0.05
    }
```

### **Phase 3: Advanced Scaling Analysis (Following Week)**

#### **3.1 Multi-Scale Experiments**
```python
# Test scaling across different system sizes
system_sizes = [25, 50, 100, 200, 500]  # agents
network_sizes = [3, 5, 10, 20, 50]      # locations
time_scales = [10, 20, 50, 100]         # days

# Look for finite-size scaling
def finite_size_scaling(L, observable):
    """Test if observable ~ L^(-β/ν) * f(t*L^(1/ν))"""
    pass
```

#### **3.2 Universal Scaling Functions**
```python
def universal_scaling_collapse(scenarios):
    """Test for data collapse onto universal curve"""
    
    # Scale variables by characteristic scales
    for scenario in scenarios:
        x_scaled = scenario.stress / scenario.stress_characteristic
        y_scaled = scenario.s2_rate / scenario.s2_rate_characteristic
        
        # Plot all scenarios on same curve
        plot_collapse(x_scaled, y_scaled)
```

#### **3.3 Critical Point Analysis**
```python
def find_critical_points(parameter_space):
    """Find phase transitions in S1/S2 behavior"""
    
    # Look for sharp transitions
    stress_critical = find_transition_point(stress_range, s2_activation_rate)
    network_critical = find_transition_point(connectivity_range, decision_quality)
    
    # Test for critical scaling near transitions
    test_critical_scaling(stress_critical)
```

---

## 🛠️ **IMPLEMENTATION STRATEGY**

### **Week 1: Data Generation**
```bash
# Day 1-2: Create diverse scenario generator
python create_diverse_scenarios.py --count 20 --vary-all

# Day 3-4: Run scenarios with different S2 thresholds  
python run_s2_sensitivity_analysis.py --thresholds 0.2,0.3,0.4,0.5

# Day 5: Collect and validate all data
python validate_scenario_diversity.py
```

### **Week 2: Analysis Framework**
```bash
# Day 1-2: Implement proper dimensionless groups
python implement_physics_based_parameters.py

# Day 3-4: Statistical validation framework
python add_statistical_testing.py

# Day 5: Generate new scaling law plots
python generate_validated_scaling_laws.py
```

### **Week 3: Advanced Analysis**
```bash
# Day 1-2: Multi-scale experiments
python run_finite_size_scaling.py

# Day 3-4: Universal scaling collapse
python test_universal_functions.py

# Day 5: Critical point analysis
python find_phase_transitions.py
```

---

## 📊 **EXPECTED OUTCOMES**

### **After Week 1**:
- **20+ diverse scenarios** with varying network topology, population, stress
- **10-30% S2 activation** across scenarios (instead of 2.5%)
- **Meaningful parameter variation** instead of constants

### **After Week 2**:
- **True scaling laws** with statistical validation
- **Physics-based dimensionless groups** with clear meaning
- **Confidence intervals** and significance tests

### **After Week 3**:
- **Universal scaling functions** that work across scenarios
- **Critical points** where behavior changes qualitatively
- **Finite-size scaling** relationships

---

## 🎯 **SUCCESS CRITERIA**

### **Minimum Viable Product**:
1. **Parameter variation**: Dimensionless parameters vary by >50% across scenarios
2. **Statistical significance**: p < 0.05 for at least 2 scaling laws
3. **Physical meaning**: Can explain what each parameter represents

### **Full Success**:
1. **Universal scaling**: Data collapse onto single curve
2. **Predictive power**: Can predict new scenario outcomes
3. **Critical phenomena**: Identify phase transitions in behavior

### **Stretch Goals**:
1. **Empirical validation**: Compare to real refugee movement data
2. **Policy applications**: Use scaling laws to design interventions
3. **Theoretical framework**: Connect to established scaling theory

---

## 🚨 **IMMEDIATE ACTION ITEMS**

### **Today**:
1. **Create scenario diversity generator**
2. **Lower S2 threshold to 0.3-0.4** 
3. **Run 5 test scenarios** with different parameters

### **This Week**:
1. **Generate 20 diverse scenarios**
2. **Implement statistical validation**
3. **Create new dimensionless parameter definitions**

### **Next Week**:
1. **Run full scaling analysis**
2. **Generate publication-quality figures**
3. **Write interpretation framework**

**The current dimensionless analysis is essentially showing constants because we don't have enough parameter variation. This plan will create true scaling laws with statistical validation and physical meaning.**