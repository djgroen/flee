# S1/S2 Dual Process Decision-Making: Development Plan

## 🎯 **Project Goal**
Implement and validate a scientifically rigorous dual-process (System 1 / System 2) decision-making framework in Flee, with three implementations for comparison and validation.

---

## 📊 **Current Status**

### ✅ **Completed**
1. Fixed cognitive pressure calculation bug (was showing 0.00)
2. Enhanced cognitive pressure with:
   - Base pressure (internal stress) - bounded to 0.4
   - Conflict pressure (external stress) - bounded to 0.4
   - Social pressure (network effects) - bounded to 0.2
   - Total pressure bounded [0.0, 1.0]
3. Created refactored S1/S2 system (`flee/s1s2_refactored.py`)
4. Implemented 5-parameter S1/S2 model (`flee/s1s2_model.py`)
5. Enhanced S2 capability requirements (connections=1, experience=3, education=0.3)
6. Implemented fallback mechanisms for backward compatibility

### 🔄 **In Progress**
- Testing new S1/S2 implementations
- Running 27 experiments with fixed cognitive pressure

### ⏳ **Pending**
- Validation of all three S1/S2 implementations
- Sensitivity analysis of 5-parameter model
- Comparison figures across implementations
- Scientific documentation

---

## 🗺️ **Development Roadmap**

### **Phase 1: Validation & Testing (Days 1-2)**

#### 1.1 Verify Implementation Files
- [ ] Read and validate `flee/s1s2_refactored.py`
- [ ] Read and validate `flee/s1s2_model.py`
- [ ] Check for any import errors or missing dependencies
- [ ] Verify parameter definitions and bounds

#### 1.2 Test Small-Scale Experiments
- [ ] Create test script for 5-parameter model (100 agents, 5 days)
- [ ] Test with different parameter combinations:
  - **Baseline**: α=2.0, β=2.0, η=4.0, θ=0.5, p_s2=0.8
  - **High Education Sensitivity**: α=4.0
  - **High Conflict Sensitivity**: β=4.0
  - **High S2 Preference**: p_s2=0.95
- [ ] Verify S2 activation rates are reasonable (10-50%)
- [ ] Check cognitive pressure bounds [0.0, 1.0]

#### 1.3 Validate Fallback Mechanisms
- [ ] Test with `s1s2_model.py` disabled
- [ ] Test with `s1s2_refactored.py` disabled
- [ ] Verify original S1/S2 logic still works

---

### **Phase 2: Comparison Experiments (Days 3-4)**

#### 2.1 Design Comparison Matrix
Run experiments with **3 implementations × 3 topologies × 3 sizes × 3 scenarios = 81 experiments**

**Implementations:**
1. **Original S1/S2**: Current system with fixed cognitive pressure
2. **Refactored S1/S2**: Modular system with improved pressure calculation
3. **5-Parameter Model**: New mathematical model

**Experimental Matrix:**
- Topologies: Star, Linear, Grid
- Sizes: 4, 8, 16 nodes
- Scenarios: low_s2 (θ=0.3), medium_s2 (θ=0.5), high_s2 (θ=0.7)
- Population: 10,000 agents each
- Duration: 20 days

#### 2.2 Run Experiments
- [ ] Configure experiments for all three implementations
- [ ] Run original S1/S2 experiments (27 experiments)
- [ ] Run refactored S1/S2 experiments (27 experiments)
- [ ] Run 5-parameter model experiments (27 experiments)
- [ ] Save results with clear naming: `{implementation}_{topology}_{size}_{scenario}`

#### 2.3 Data Collection
For each experiment, collect:
- S2 activation rate (%)
- Cognitive pressure distribution
- Agent movement patterns
- Final camp populations
- Distance traveled per agent
- S2 activation over time

---

### **Phase 3: Analysis & Visualization (Days 5-6)**

#### 3.1 Comparison Metrics
Calculate for each implementation:
- **S2 Activation Rate**: Mean ± std across scenarios
- **Pressure Sensitivity**: Correlation between pressure and S2 activation
- **Topology Sensitivity**: S2 rate variance across topologies
- **Threshold Sensitivity**: S2 rate change across low/medium/high scenarios
- **Temporal Dynamics**: S2 activation pattern over time

#### 3.2 Create Comparison Figures
1. **Implementation Comparison Dashboard**:
   - S2 activation rates (box plots)
   - Cognitive pressure distributions (histograms)
   - Topology sensitivity (heatmaps)
   - Threshold response curves

2. **Parameter Sensitivity Analysis** (5-parameter model):
   - α (education sensitivity) sweep
   - β (conflict sensitivity) sweep
   - η (S2 decision quality) sweep
   - θ (S2 threshold) sweep
   - p_s2 (S2 preference) sweep

3. **Temporal Dynamics**:
   - S2 activation over time (line plots)
   - Cognitive pressure evolution (area plots)
   - Agent movement patterns (flow diagrams)

4. **Network Effects**:
   - S2 activation vs network size (scaling plots)
   - S2 activation vs topology (comparison plots)
   - S2 activation vs connectivity (scatter plots)

#### 3.3 Statistical Validation
- [ ] ANOVA: Test if implementations differ significantly
- [ ] Correlation analysis: Pressure vs S2 activation
- [ ] Regression: Predict S2 rate from parameters
- [ ] Goodness-of-fit: Compare to theoretical expectations

---

### **Phase 4: Documentation & Publication (Days 7-8)**

#### 4.1 Scientific Documentation
Create comprehensive documentation:
1. **Mathematical Formulation**:
   - Original S1/S2 equations
   - Refactored S1/S2 equations
   - 5-parameter model equations
   - Cognitive pressure components

2. **Parameter Definitions**:
   - α: Education sensitivity (default: 2.0)
   - β: Conflict sensitivity (default: 2.0)
   - η: S2 decision quality (default: 4.0)
   - θ: S2 activation threshold (default: 0.5)
   - p_s2: S2 preference probability (default: 0.8)

3. **Validation Results**:
   - S2 activation rates across implementations
   - Sensitivity analysis results
   - Statistical comparisons
   - Recommendations

#### 4.2 Create README Files
- [ ] `S1S2_IMPLEMENTATION_GUIDE.md`: How to use each implementation
- [ ] `S1S2_PARAMETER_GUIDE.md`: Parameter definitions and tuning
- [ ] `S1S2_VALIDATION_REPORT.md`: Validation results and comparisons
- [ ] `S1S2_API_REFERENCE.md`: Function signatures and usage

#### 4.3 Prepare for Publication
- [ ] Create publication-ready figures (high DPI, vector formats)
- [ ] Write methods section for paper
- [ ] Create supplementary materials
- [ ] Prepare data repository (Zenodo/Figshare)

---

## 🔬 **Key Research Questions**

1. **Does the 5-parameter model produce more realistic S2 activation patterns?**
2. **How sensitive is S2 activation to each parameter (α, β, η, θ, p_s2)?**
3. **Do the three implementations converge to similar results?**
4. **What is the optimal parameter configuration for refugee scenarios?**
5. **How does cognitive pressure evolve over time in different topologies?**
6. **What is the relationship between network structure and S2 activation?**

---

## 📝 **Immediate Action Items**

### **Today (Priority 1)**
1. ✅ Create this development plan
2. ⏳ Verify `flee/s1s2_refactored.py` implementation
3. ⏳ Verify `flee/s1s2_model.py` implementation
4. ⏳ Create test script for 5-parameter model
5. ⏳ Run small-scale validation test (100 agents)

### **Tomorrow (Priority 2)**
6. Run comparison experiments (81 total)
7. Generate comparison figures
8. Perform sensitivity analysis
9. Create statistical validation report

### **This Week (Priority 3)**
10. Write comprehensive documentation
11. Create publication-ready figures
12. Prepare supplementary materials
13. Submit for review/publication

---

## 🎓 **Expected Outcomes**

### **Scientific Contributions**
1. **Novel 5-parameter S1/S2 model** for agent-based refugee modeling
2. **Validated cognitive pressure framework** with bounded components
3. **Comparison of three S1/S2 implementations** with statistical validation
4. **Sensitivity analysis** of S1/S2 parameters in refugee contexts
5. **Network topology effects** on cognitive decision-making

### **Technical Contributions**
1. **Modular S1/S2 framework** with fallback mechanisms
2. **Comprehensive test suite** for S1/S2 validation
3. **Visualization toolkit** for S1/S2 analysis
4. **Parameter optimization tools** for S1/S2 tuning

### **Publications**
1. **Main paper**: "Dual-Process Decision-Making in Agent-Based Refugee Models"
2. **Methods paper**: "A 5-Parameter Framework for System 1/System 2 Cognition"
3. **Software paper**: "Flee-S1S2: A Modular Cognitive Framework for ABM"

---

## 📊 **Success Criteria**

### **Technical Success**
- ✅ All three implementations run without errors
- ✅ S2 activation rates are in realistic range (10-50%)
- ✅ Cognitive pressure is properly bounded [0.0, 1.0]
- ✅ Fallback mechanisms work correctly
- ✅ Results are reproducible

### **Scientific Success**
- ✅ Implementations show statistically significant differences
- ✅ Parameter sensitivity is well-characterized
- ✅ Results align with cognitive science literature
- ✅ Network effects are clearly demonstrated
- ✅ Temporal dynamics are realistic

### **Publication Success**
- ✅ Methods are clearly documented
- ✅ Figures are publication-ready
- ✅ Code is well-documented and reproducible
- ✅ Data is archived and accessible
- ✅ Reviewers find work scientifically sound

---

## 🚀 **Let's Get Started!**

**Next immediate step**: Verify the implementation files and create a test script.

Would you like me to:
1. **Read and validate the implementation files** (`s1s2_refactored.py`, `s1s2_model.py`)?
2. **Create a test script** for the 5-parameter model?
3. **Run a small validation experiment** (100 agents, 5 days)?
4. **Something else**?




