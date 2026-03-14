# S1/S2 Dual-Process Experimental Design

## 🎯 **Research Objectives**

### Primary Goal
Demonstrate the **value and sensitivity** of including S1/S2 dual-process decision-making in refugee movement models.

### Specific Objectives
1. **Value Demonstration**: Show that S1/S2 switching produces more realistic agent behavior than static models
2. **Sensitivity Analysis**: Quantify how S2 threshold parameters affect simulation outcomes
3. **Topology Effects**: Understand how network structure influences S1/S2 behavior patterns
4. **Baseline Comparison**: Compare against pure S1, pure S2, and static mixed models

## 🧪 **Experimental Design**

### **Baseline Scenarios (No S1/S2 Switching)**

| Scenario | Description | S2 Threshold | Behavior |
|----------|-------------|--------------|----------|
| `pure_s1` | Pure System 1 (reactive) | 1.0 | All decisions use fast, heuristic-based System 1 |
| `pure_s2` | Pure System 2 (deliberative) | 0.0 | All decisions use slow, analytical System 2 |
| `static_mixed` | Static mixed (50/50) | 0.5 | Fixed 50% S1, 50% S2 decisions (no switching) |

### **S1/S2 Switching Scenarios**

| Scenario | Description | S2 Threshold | Behavior |
|----------|-------------|--------------|----------|
| `low_s2` | Low S2 activation | 0.3 | S2 activates only under high cognitive pressure |
| `medium_s2` | Medium S2 activation | 0.5 | Balanced S1/S2 switching |
| `high_s2` | High S2 activation | 0.7 | S2 activates under moderate cognitive pressure |

### **Experimental Matrix**

**Topologies**: Linear, Star, Tree, Grid  
**Network Sizes**: 5, 7, 11 nodes  
**Total Experiments**: 4 × 3 × 6 = **72 experiments**

```
Topology × Network Size × Scenario Matrix:
┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│         │ pure_s1 │ pure_s2 │ static_ │ low_s2  │ medium_ │ high_s2 │
│         │         │         │ mixed   │         │ s2      │         │
├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Linear  │   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│
│ Star    │   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│
│ Tree    │   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│
│ Grid    │   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│   5,7,11│
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

## 📊 **Key Metrics for Comparison**

### **Primary Metrics**
- **S2 Activation Rate**: Percentage of decisions using System 2
- **Average Travel Distance**: Total distance traveled by agents
- **Destination Diversity**: Number of unique destinations reached
- **Convergence Time**: Time to reach stable population distribution

### **Secondary Metrics**
- **Network Utilization**: How well agents use available routes
- **Cognitive Load Distribution**: Distribution of cognitive effort across agents
- **Decision Consistency**: Stability of decision patterns over time
- **Route Efficiency**: Optimal vs actual path selection

## 🔬 **Hypothesis Testing**

### **H1: S1/S2 Switching Improves Realism**
- **Null Hypothesis**: S1/S2 switching has no effect on simulation outcomes
- **Alternative Hypothesis**: S1/S2 switching produces more realistic agent behavior
- **Test**: Compare S1/S2 scenarios vs baseline scenarios
- **Expected Result**: S1/S2 scenarios should show intermediate values between pure S1 and pure S2

### **H2: S2 Threshold Sensitivity**
- **Null Hypothesis**: S2 threshold has no effect on outcomes
- **Alternative Hypothesis**: Different S2 thresholds produce different outcomes
- **Test**: Compare low_s2 vs medium_s2 vs high_s2 scenarios
- **Expected Result**: Higher S2 thresholds should lead to higher S2 activation rates

### **H3: Topology-Dependent Effects**
- **Null Hypothesis**: Network topology has no effect on S1/S2 behavior
- **Alternative Hypothesis**: Different topologies show different S1/S2 patterns
- **Test**: Compare S1/S2 effects across linear, star, tree, grid networks
- **Expected Result**: More complex topologies (grid, tree) should show different S1/S2 patterns than simple ones (linear)

## 📋 **Experimental Protocol**

### **1. Consistent Initialization**
- **Random Seed**: Same seed for all experiments to ensure reproducibility
- **Population Consistency**: Same number of agents for same network size
- **Parameter Control**: Only S2 threshold varies between scenarios

### **2. Population Management**
- **Network Size 5**: 25 agents
- **Network Size 7**: 35 agents  
- **Network Size 11**: 50 agents
- **Consistent Spawning**: All agents start at the same origin location

### **3. Simulation Parameters**
- **Duration**: 20 simulation days
- **Agent Tracking**: Full individual agent tracking enabled
- **Cognitive Pressure**: Dynamic pressure based on network complexity
- **S2 Activation**: Sigmoid function with configurable threshold

### **4. Data Collection**
- **Raw Data**: All agent tracking data preserved with timestamps
- **Metrics**: Calculated for each experiment
- **Metadata**: Complete experimental parameters documented

## 🎯 **Expected Outcomes**

### **Value Demonstration**
- S1/S2 scenarios should show **intermediate behavior** between pure S1 and pure S2
- **More realistic decision patterns** than static mixed scenarios
- **Adaptive behavior** based on cognitive pressure

### **Sensitivity Analysis**
- **Clear relationship** between S2 threshold and S2 activation rate
- **Non-linear effects** of threshold on travel distance and destination diversity
- **Threshold-dependent** convergence patterns

### **Topology Effects**
- **Linear networks**: Simple, predictable S1/S2 patterns
- **Star networks**: Hub-dependent S1/S2 behavior
- **Tree networks**: Hierarchical S1/S2 decision patterns
- **Grid networks**: Complex, multi-path S1/S2 interactions

## 📈 **Analysis Plan**

### **1. Descriptive Analysis**
- Summary statistics for all metrics across scenarios
- Visualization of S2 activation rates by topology and threshold
- Distribution analysis of travel distances and destination diversity

### **2. Comparative Analysis**
- **Baseline vs S1/S2**: Statistical tests comparing baseline scenarios to S1/S2 scenarios
- **Threshold Effects**: ANOVA analysis of S2 threshold effects
- **Topology Effects**: Multi-way ANOVA including topology as a factor

### **3. Sensitivity Analysis**
- **Parameter Sensitivity**: How much outcomes change with S2 threshold
- **Robustness Testing**: Consistency of results across different random seeds
- **Effect Size**: Magnitude of S1/S2 effects relative to baseline scenarios

## 🔒 **Data Management**

### **Preservation Strategy**
- **Raw Data**: All agent tracking files preserved with timestamps
- **Metadata**: Complete experimental parameters for each run
- **Reproducibility**: Random seeds and configuration files saved
- **Version Control**: All code and data versioned

### **Quality Assurance**
- **Consistency Checks**: Verify population sizes and initial conditions
- **Data Validation**: Check for missing or corrupted data
- **Replication**: Multiple runs with different seeds for key scenarios

## 🚀 **Implementation Timeline**

### **Phase 1: Framework Setup** ✅
- [x] Experimental design framework
- [x] Baseline scenario implementation
- [x] S1/S2 scenario implementation

### **Phase 2: Experiment Execution**
- [ ] Run all 72 experiments
- [ ] Data collection and validation
- [ ] Initial analysis and visualization

### **Phase 3: Analysis and Reporting**
- [ ] Statistical analysis
- [ ] Sensitivity analysis
- [ ] Results interpretation and reporting

This experimental design provides a comprehensive framework for demonstrating the value and sensitivity of S1/S2 dual-process decision-making in refugee movement models.




