# Analysis Guide

## Running the Framework

### 1. Systematic Network Scaling
```bash
python code/systematic_network_scaling_framework.py
```
- Tests 4 topology types × 4 network sizes = 16 experiments
- Uses geometric progression [5, 7, 11, 16] nodes
- Generates network metrics and S2 activation rates

### 2. Comprehensive Visualizations
```bash
python code/comprehensive_visualization_suite.py
```
- Creates network topology diagrams
- Generates metrics analysis plots
- Produces dimensionless parameter analysis
- Creates publication-ready figures

### 3. S2 Parameter Optimization
```bash
python code/optimize_s2_parameters.py
```
- Optimizes S2 thresholds for target activation rates
- Tests different cognitive profiles
- Generates parameter sensitivity analysis

## Output Structure

Results are organized in the following structure:
```
cognition_results/
├── results/
│   ├── raw_data/           # JSON results
│   ├── figures/            # PNG/PDF visualizations
│   ├── analysis/           # Statistical analysis
│   └── reports/            # Markdown summaries
```

## Key Metrics

### Network Metrics
- **Average Degree**: Connections per node
- **Clustering Coefficient**: Local connectivity patterns
- **Average Path Length**: Network efficiency
- **Network Density**: Overall connectivity
- **Betweenness Centrality**: Node importance

### Dimensionless Parameters
- **Complexity**: (Degree × Density) / (1 + Path Length)
- **Efficiency**: Density / Path Length
- **Connectivity**: Degree / (1 + Clustering)

## Interpretation

### S2 Activation Rates
- **Target Range**: 20-30% (based on psychological research)
- **Current Results**: 73.6% - 95.2% (needs calibration)
- **Topology Effects**: 21.6% variation across topologies

### Network Complexity
- **Linear**: Lowest complexity, lowest S2 activation
- **Grid**: Highest complexity, highest S2 activation
- **Star/Tree**: Moderate complexity, moderate S2 activation
