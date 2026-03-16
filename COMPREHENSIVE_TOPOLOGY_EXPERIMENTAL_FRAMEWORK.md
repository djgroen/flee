# Comprehensive Topology-S1/S2 Experimental Framework

## 🎯 **EXPERIMENTAL OBJECTIVE**

Design and implement a scientifically rigorous experimental framework to systematically test how S1/S2 dual-process decision-making behavior varies across different network topologies, with proper statistical controls, comprehensive metrics, and publication-ready analysis.

## 🧪 **EXPERIMENTAL DESIGN**

### **1. Topology Specifications**

#### **Linear Topologies (Chain-like)**
- **Variants**: 4, 8, 16 locations
- **Structure**: Sequential chain (Origin → Towns → Camps)
- **Expected Properties**: High diameter, zero clustering, high centrality variance
- **Use Case**: Testing sequential bottleneck effects

#### **Star Topologies (Hub-and-spoke)**
- **Variants**: 4, 8, 16 locations (1 hub + n-1 spokes)
- **Structure**: Central hub connected to all other locations
- **Expected Properties**: Diameter = 2, zero clustering, very high centrality variance
- **Use Case**: Testing centralized coordination effects

#### **Grid Topologies (2D grids)**
- **Variants**: 4 (2×2), 9 (3×3), 16 (4×4) locations
- **Structure**: Regular 2D grid with orthogonal connections
- **Expected Properties**: Moderate diameter, moderate clustering, low centrality variance
- **Use Case**: Testing redundant pathway effects

#### **Random Topologies (Erdős-Rényi)**
- **Variants**: 8, 16 locations with p = 0.2, 0.4, 0.6
- **Structure**: Random connections with specified probability
- **Expected Properties**: Variable diameter, low clustering, moderate centrality variance
- **Use Case**: Testing random connectivity effects

#### **Scale-free Topologies (Barabási-Albert)**
- **Variants**: 8, 16 locations with m = 2, 4
- **Structure**: Preferential attachment growth model
- **Expected Properties**: Small diameter, high clustering, very high centrality variance
- **Use Case**: Testing hub-dominated network effects

#### **Ring Topologies**
- **Variants**: 8, 16 locations
- **Structure**: Circular arrangement with nearest-neighbor connections
- **Expected Properties**: High diameter, zero clustering, no centrality variance
- **Use Case**: Testing symmetric network effects

### **2. S1/S2 Configurations**

#### **Baseline Configuration**
- **Description**: Standard S1/S2 behavior with scaled move probabilities
- **Parameters**: eta = 0.5, steepness = 6.0, soft_capability = False
- **Use Case**: Reference configuration for comparison

#### **Constant S2 Configuration**
- **Description**: Fixed high move probability for S2-capable agents
- **Parameters**: pmove_s2_mode = "constant", pmove_s2_constant = 0.9
- **Use Case**: Testing maximum S2 effectiveness

#### **Soft Gate Configuration**
- **Description**: Gradual S2 activation using sigmoid functions
- **Parameters**: soft_capability = True, soft_gate_steepness = 8.0
- **Use Case**: Testing gradual activation effects

#### **Diminishing Configuration**
- **Description**: Diminishing connectivity effects over time
- **Parameters**: connectivity_mode = "diminishing"
- **Use Case**: Testing temporal dynamics

#### **High Eta Configuration**
- **Description**: High eta parameter for increased S2 activation
- **Parameters**: eta = 0.8
- **Use Case**: Testing high S2 activation scenarios

#### **Low Eta Configuration**
- **Description**: Low eta parameter for reduced S2 activation
- **Parameters**: eta = 0.2
- **Use Case**: Testing low S2 activation scenarios

### **3. Experimental Controls**

#### **Statistical Power**
- **Replicates**: 10 per topology-configuration combination
- **Total Experiments**: 6 topology types × 6 configurations × 10 replicates = 360 experiments
- **Random Seeds**: Fixed seeds (1000-1009) for reproducibility

#### **Simulation Parameters**
- **Agents**: 100 per simulation
- **Timesteps**: 100 per simulation
- **Agent Attributes**: Diverse connections, education, stress tolerance, S2 thresholds
- **Location Types**: Origin (conflict zone), Towns (transit), Camps (destinations)

#### **Network Metrics**
- **Basic**: Nodes, edges, density
- **Connectivity**: Diameter, radius, average path length
- **Centrality**: Degree, betweenness, closeness (mean and std)
- **Clustering**: Average clustering, transitivity
- **Assortativity**: Degree assortativity coefficient

## 📊 **COMPREHENSIVE METRICS**

### **1. Behavioral Metrics**
- **S2 Activation**: Final rate, peak rate, variance over time
- **Movement**: Final rate, peak rate, variance over time
- **Evacuation**: Final rate, time to 50%, time to 90%
- **Pressure**: Mean, variance, distribution statistics

### **2. Agent Attribute Metrics**
- **Connections**: Average, distribution
- **Education**: Average, distribution
- **Stress Tolerance**: Average, distribution
- **S2 Threshold**: Average, distribution

### **3. Network Analysis Metrics**
- **Topology Properties**: All network metrics calculated for each topology
- **Structural Analysis**: Centrality distributions, clustering patterns
- **Connectivity Analysis**: Path length distributions, bottleneck identification

### **4. Temporal Dynamics**
- **Evolution**: S2 activation, movement, evacuation over time
- **Convergence**: Time to steady state
- **Variability**: Behavioral diversity measures

## 🔬 **STATISTICAL ANALYSIS**

### **1. Primary Analysis**
- **ANOVA**: Topology effects on evacuation success
- **ANOVA**: S1/S2 configuration effects on evacuation success
- **ANOVA**: Network size effects on evacuation success
- **ANOVA**: Interaction effects (Topology × S1/S2 Config)

### **2. Correlation Analysis**
- **Network Metrics**: Correlation with evacuation success
- **Agent Attributes**: Correlation with evacuation success
- **Behavioral Metrics**: Cross-correlations

### **3. Post-hoc Analysis**
- **Tukey HSD**: Pairwise comparisons between groups
- **Effect Sizes**: Cohen's d for significant differences
- **Power Analysis**: Statistical power calculations

## 📈 **VISUALIZATION SUITE**

### **1. Behavioral Analysis**
- Box plots: Evacuation success by topology type and S1/S2 config
- Time series: S2 activation, movement, evacuation over time
- Scatter plots: Network metrics vs evacuation success

### **2. Network Analysis**
- Network visualizations: Topology structures
- Centrality heatmaps: Node importance across topologies
- Clustering analysis: Community structure identification

### **3. Statistical Analysis**
- Correlation matrices: All metric correlations
- Heatmaps: Topology-S1/S2 performance
- Effect size plots: Significant differences

## 🎯 **EXPECTED OUTCOMES**

### **1. Topology Effects**
- **Hypothesis**: Different topologies will show varying evacuation success rates
- **Expected**: Star topologies > Grid topologies > Linear topologies
- **Rationale**: Centralized coordination vs. redundant pathways vs. bottlenecks

### **2. S1/S2 Configuration Effects**
- **Hypothesis**: S1/S2 configuration will significantly affect evacuation success
- **Expected**: Constant S2 > High Eta > Baseline > Low Eta
- **Rationale**: Higher S2 activation leads to better decision-making

### **3. Network Metric Correlations**
- **Hypothesis**: Network metrics will correlate with evacuation success
- **Expected**: Negative correlation with diameter, positive with clustering
- **Rationale**: Shorter paths and better connectivity improve evacuation

### **4. Agent Attribute Effects**
- **Hypothesis**: Agent attributes will affect evacuation success
- **Expected**: Higher education and connections improve evacuation
- **Rationale**: Better-informed agents make better decisions

## 📁 **DELIVERABLES**

### **1. Data Files**
- `comprehensive_results.json`: Complete experimental results
- `comprehensive_summary_statistics.csv`: Summary statistics
- `comprehensive_detailed_results.csv`: Detailed analysis data
- `statistical_analysis_results.json`: Statistical test results

### **2. Visualizations**
- `Comprehensive_Topology_Analysis.png/pdf`: Complete analysis plots
- Network topology diagrams
- Statistical analysis plots

### **3. Reports**
- `Comprehensive_Analysis_Report.md`: Complete analysis report
- Statistical validation results
- Policy recommendations

## 🚀 **IMPLEMENTATION**

### **1. Experiment Execution**
```bash
python comprehensive_topology_s1s2_experiments.py
```

### **2. Analysis Execution**
```bash
python analyze_comprehensive_topology_results.py
```

### **3. Results Organization**
- All results organized in `results/comprehensive_topology_experiments/`
- Structured directory hierarchy for easy navigation
- Publication-ready figures and data

## 🎉 **SCIENTIFIC RIGOR**

### **1. Experimental Controls**
- Fixed random seeds for reproducibility
- Consistent agent attribute distributions
- Standardized simulation parameters
- Comprehensive network metrics

### **2. Statistical Power**
- 10 replicates per condition
- Multiple comparison corrections
- Effect size calculations
- Power analysis

### **3. Comprehensive Metrics**
- Behavioral, network, and agent metrics
- Temporal dynamics analysis
- Cross-correlation analysis
- Interaction effects

### **4. Publication Standards**
- Publication-ready figures
- Comprehensive statistical analysis
- Detailed methodology documentation
- Reproducible results

## 🎯 **CONCLUSION**

This comprehensive experimental framework provides:

1. **Scientific Rigor**: Proper controls, statistical power, and comprehensive metrics
2. **Topology Diversity**: 6 different topology types with multiple variants
3. **S1/S2 Variety**: 6 different S1/S2 configurations
4. **Statistical Validation**: Comprehensive statistical analysis with proper controls
5. **Publication Readiness**: Publication-ready figures, data, and reports

**The framework is designed to provide definitive answers about how network topology affects S1/S2 decision-making behavior in refugee evacuation scenarios, with the statistical rigor required for academic publication.** 🎯




