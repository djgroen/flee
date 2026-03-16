# S1/S2 Parameter Justification Analysis

## 🎯 **Executive Summary**

**Status**: The S1/S2 dual-process framework is conceptually sound and well-grounded in cognitive psychology, but the specific functional forms and parameters require better empirical justification.

**Recommendation**: Implement a **parameter sensitivity analysis framework** and **empirical calibration system** before production use.

## ✅ **Well-Justified Components**

### **1. Dual-Process Framework**
- **Grounded in**: Kahneman & Tversky (1979), Stanovich & West (2000)
- **Evidence**: Extensive cognitive psychology literature on System 1/System 2
- **Status**: ✅ **Strong theoretical foundation**

### **2. Sigmoid Activation Function**
```
P(S2) = 1 / (1 + exp(-η × (P(t) - θ)))
```
- **Justification**: Neural activation patterns, decision-making thresholds
- **Evidence**: Sigmoidal functions common in cognitive modeling
- **Status**: ✅ **Well-supported functional form**

### **3. Additive Pressure Model**
```
P(t) = B(t) + C(t) + S(t)
```
- **Rationale**: Simple, interpretable combination
- **Status**: ⚠️ **Reasonable but needs validation**

## ⚠️ **Questionable/Arbitrary Components**

### **1. Time Stress Function**
```
time_stress(t) = 0.1 × (1 - exp(-t/10)) × exp(-t/50)
```

**Issues:**
- Time constants (10, 50) appear arbitrary
- No empirical basis for this specific form
- Growth-then-decay pattern is intuitive but uncalibrated

**Recommendations:**
- Calibrate to displacement stress studies
- Test alternative forms (linear, polynomial, hyperbolic)
- Use parameter estimation from refugee mental health data

### **2. Hard-Coded Bounds**
```
B(t) = min(0.4, ...)  # Base pressure cap
C(t) = min(0.4, ...)  # Conflict pressure cap  
S(t) = min(0.2, ...)  # Social pressure cap
```

**Issues:**
- Why 0.4 for base/conflict but 0.2 for social?
- No theoretical justification for relative weightings
- Arbitrary caps may not reflect real psychological limits

**Recommendations:**
- Calibrate bounds to psychological stress literature
- Test different relative weightings
- Consider dynamic bounds based on individual traits

### **3. Connectivity Factor**
```
connectivity_factor = min(1.0, connections / 10.0)
```

**Issues:**
- Linear scaling up to 10 connections is simplistic
- Social network effects often show diminishing returns
- No basis for the "10 connections" threshold

**Recommendations:**
- Use social network research (Dunbar's number, network effects)
- Test non-linear forms: `connections^α` or `log(1 + connections)`
- Calibrate to actual refugee social network data

### **4. Conflict Decay**
```
conflict_decay(t) = exp(-max(0, t - conflict_start) / 20)
```

**Issues:**
- Time constant (20) appears arbitrary
- Exponential decay is reasonable but uncalibrated

**Recommendations:**
- Calibrate to post-traumatic stress recovery literature
- Test different decay functions
- Use individual variation in recovery rates

### **5. S2 Move Probability = 0.9**
```
P(move|S2) = 0.9
```

**Major Issues:**
- **Too high**: Even deliberative decisions shouldn't be near-certain
- **No empirical basis**: No data supporting this specific value
- **Unrealistic**: Real displacement decisions are complex and uncertain

**Recommendations:**
- Calibrate to actual refugee decision-making data
- Use more realistic values (0.6-0.8)
- Make it parameter-dependent on individual traits

## 🔍 **Critical Missing Elements**

### **1. Empirical Calibration**
- No fit to actual displacement datasets
- No comparison with refugee decision-making patterns
- Parameters not grounded in real data

### **2. Sensitivity Analysis**
- No systematic testing of parameter sensitivity
- No confidence intervals for predictions
- No robustness testing

### **3. Model Validation**
- No cross-validation on held-out scenarios
- No comparison with alternative models
- No predictive accuracy assessment

### **4. Non-linear Interactions**
- Assumes independent, additive pressure effects
- May miss important stress × conflict interactions
- Cognitive load research suggests non-linear effects

## 💡 **Recommended Improvements**

### **Phase 1: Parameter Sensitivity Analysis**
```python
# Implement systematic parameter testing
parameter_ranges = {
    'eta': [2, 4, 6, 8, 10],
    'threshold': [0.3, 0.4, 0.5, 0.6, 0.7],
    'time_constants': [(5,25), (10,50), (15,75)],
    'pressure_caps': [(0.3,0.3,0.15), (0.4,0.4,0.2), (0.5,0.5,0.25)],
    's2_move_prob': [0.6, 0.7, 0.8, 0.9]
}
```

### **Phase 2: Empirical Calibration**
- Fit to UNHCR displacement data
- Use IDMC internal displacement datasets
- Calibrate to refugee mental health studies
- Validate against actual decision-making patterns

### **Phase 3: Alternative Functional Forms**
```python
# Test alternative pressure combinations
def multiplicative_pressure(B, C, S):
    return B * C * S

def weighted_pressure(B, C, S, weights):
    return weights[0]*B + weights[1]*C + weights[2]*S

def non_linear_pressure(B, C, S, alpha):
    return (B**alpha + C**alpha + S**alpha)**(1/alpha)
```

### **Phase 4: Individual Differences**
- Make parameters depend on agent traits
- Use realistic distributions for individual variation
- Calibrate trait effects to psychological literature

## 🎯 **Implementation Strategy**

### **Immediate Actions (Before Production)**
1. **Parameter Sensitivity Analysis**: Test how results change with different parameter values
2. **Literature Review**: Ground parameters in cognitive psychology and displacement research
3. **Alternative Models**: Implement and test different functional forms
4. **Transparency**: Document which choices are theoretical vs. empirical

### **Medium-term Actions (Post-Production)**
1. **Empirical Calibration**: Fit to real displacement datasets
2. **Cross-validation**: Test on held-out scenarios
3. **Model Comparison**: Compare with simpler and more complex alternatives
4. **Publication**: Document parameter choices and validation results

## 📊 **Validation Framework**

### **Parameter Justification Checklist**
- [ ] **Theoretical**: Based on established psychological theory
- [ ] **Empirical**: Calibrated to real data
- [ ] **Sensitivity**: Tested across reasonable ranges
- [ ] **Robustness**: Validated on multiple scenarios
- [ ] **Transparency**: Clearly documented rationale

### **Model Validation Metrics**
- [ ] **Predictive Accuracy**: How well does it predict actual displacement patterns?
- [ ] **Behavioral Realism**: Do agent behaviors match real refugee decisions?
- [ ] **Parameter Stability**: Are results robust to parameter changes?
- [ ] **Cross-validation**: Does it generalize to new scenarios?

## 🏆 **Conclusion**

The S1/S2 framework is **conceptually sound** and represents a significant improvement over simple heuristic models. However, the **specific functional forms and parameters need better justification** before production use.

**Recommendation**: Implement the parameter sensitivity analysis framework and conduct empirical calibration. The system will work mechanically, but its predictive validity depends on better parameter justification.

**Status**: ✅ **Ready for sensitivity analysis and empirical calibration**  
**Next Step**: Implement parameter testing framework and begin empirical validation




