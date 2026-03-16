# Extended Topology Testing Guide

This guide explains how to run comprehensive topology robustness testing for dual-process hypotheses.

## Overview

The extended topology testing framework tests each hypothesis across **5 different network topologies** to assess:

1. **Robustness**: Do the effects hold across different network structures?
2. **Topology Interactions**: How do network characteristics affect cognitive decision-making?
3. **Optimal Conditions**: Which topologies maximize or minimize dual-process effects?

## Available Network Topologies

### 1. **Linear Chain**
- **Structure**: Nodes connected in a straight line
- **Characteristics**: High bottlenecks, simple paths, sequential information flow
- **Best For**: Testing corridor effects, evacuation chains

### 2. **Hub-and-Spoke (Star)**
- **Structure**: Central hub connected to multiple camps
- **Characteristics**: Centralized information, hub bottlenecks, rapid dissemination
- **Best For**: Testing centralization effects, information hubs

### 3. **Rectangular Grid**
- **Structure**: Regular 2D grid with local connections
- **Characteristics**: Distributed paths, moderate clustering, spatial exploration
- **Best For**: Testing spatial decision-making, alternative routes

### 4. **Small-World Network**
- **Structure**: High local clustering + some long-range connections
- **Characteristics**: Efficient information spread, community structure
- **Best For**: Testing realistic social networks, community effects

### 5. **Scale-Free Network**
- **Structure**: Few highly connected hubs, many low-degree nodes
- **Characteristics**: Hub vulnerability, preferential attachment
- **Best For**: Testing network resilience, hub failure scenarios

## Running Extended Topology Tests

### Basic Usage

```bash
# Test all hypotheses across all topologies
python run_hypothesis_scenarios.py --extended-topology

# Test specific hypotheses with extended topologies
python run_hypothesis_scenarios.py --extended-topology --hypotheses H1.1 H2.1

# Adjust replications and parallel processing
python run_hypothesis_scenarios.py --extended-topology --replications 5 --max-parallel 2
```

### Direct Extended Testing

```bash
# Use the dedicated extended topology script
python run_extended_topology_scenarios.py

# With specific options
python run_extended_topology_scenarios.py --hypotheses H1.1 H2.1 --replications 3
```

## Output Structure

Extended topology testing creates comprehensive results:

```
extended_topology_results/
├── topology_robustness_results.json     # Complete results data
├── topology_robustness_summary.md       # Human-readable summary
├── raw_experiments/                     # Individual experiment outputs
│   ├── H1.1_linear_dual_process_rep01/
│   ├── H1.1_star_dual_process_rep01/
│   └── ...
└── logs/                               # Execution logs
```

## Analysis Results

### Universal Topology Effects
- **Best Overall Topology**: Which topology consistently performs well across hypotheses
- **Most Consistent Topology**: Which topology shows least variation across conditions
- **Topology Rankings**: Performance ranking for each topology

### Hypothesis-Specific Effects
For each hypothesis:
- **Best/Worst Topology**: Which topologies maximize/minimize the effect
- **Robustness Score**: How consistent the effect is across topologies
- **Topology Interactions**: How network characteristics interact with cognitive effects

### Cross-Hypothesis Analysis
- **Universal Patterns**: Effects that appear across all hypotheses
- **Topology Recommendations**: Which topologies to use for different research goals

## Interpretation Guide

### High Robustness (Score > 0.8)
- Effect is **topology-independent**
- Likely reflects fundamental cognitive processes
- Results generalize across different spatial contexts

### Moderate Robustness (Score 0.4-0.8)
- Effect is **partially topology-dependent**
- Network structure moderates the cognitive effect
- Important to consider spatial context in applications

### Low Robustness (Score < 0.4)
- Effect is **highly topology-dependent**
- May reflect network properties rather than cognitive processes
- Requires careful interpretation and replication

## Research Applications

### For Hypothesis Testing
- **Use multiple topologies** to ensure effects are not artifacts of network structure
- **Compare robustness scores** to assess generalizability
- **Identify boundary conditions** where effects break down

### For Applied Research
- **Choose optimal topology** based on research goals:
  - **Maximum effects**: Use best-performing topology
  - **Realistic scenarios**: Use small-world or scale-free networks
  - **Controlled experiments**: Use linear or grid topologies

### For Theory Development
- **Topology interactions** reveal how spatial constraints affect cognition
- **Universal patterns** suggest fundamental dual-process mechanisms
- **Topology-specific effects** identify contextual factors

## Performance Considerations

### Computational Requirements
- **5x more experiments** than basic hypothesis testing
- **Longer runtime**: Plan for extended execution time
- **Storage**: Requires more disk space for comprehensive results

### Optimization Tips
```bash
# Reduce replications for initial exploration
python run_extended_topology_scenarios.py --replications 3

# Use fewer parallel processes if memory-limited
python run_extended_topology_scenarios.py --max-parallel 2

# Test subset of hypotheses first
python run_extended_topology_scenarios.py --hypotheses H1.1
```

## Example Workflow

### 1. Initial Exploration
```bash
# Quick test with reduced replications
python run_extended_topology_scenarios.py --replications 3 --hypotheses H1.1
```

### 2. Full Analysis
```bash
# Complete topology robustness testing
python run_extended_topology_scenarios.py --replications 10
```

### 3. Results Analysis
```bash
# Review summary report
cat extended_topology_results/topology_robustness_summary.md

# Analyze detailed results
python -c "
import json
with open('extended_topology_results/topology_robustness_results.json') as f:
    results = json.load(f)
    print('Best topology:', results['cross_analysis']['universal_topology_effects']['best_overall_topology'])
"
```

## Integration with Standard Testing

Extended topology testing **complements** rather than replaces standard hypothesis testing:

1. **Standard Testing**: Tests hypotheses with scenario-specific topologies
2. **Extended Testing**: Tests robustness across multiple topologies
3. **Combined Analysis**: Provides both specific and general insights

Use both approaches for comprehensive dual-process research!

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure you're in the flee_dual_process directory
cd flee_dual_process
python run_extended_topology_scenarios.py
```

**Memory Issues**:
```bash
# Reduce parallel processes and replications
python run_extended_topology_scenarios.py --max-parallel 1 --replications 2
```

**Long Runtime**:
```bash
# Test subset first, then scale up
python run_extended_topology_scenarios.py --hypotheses H1.1 --replications 3
```

### Getting Help

- Check execution logs in `extended_topology_results/logs/`
- Review individual experiment outputs in `raw_experiments/`
- Compare with standard hypothesis testing results for validation

## Next Steps

After running extended topology testing:

1. **Review robustness scores** to assess generalizability
2. **Identify optimal topologies** for your research context
3. **Analyze topology interactions** to understand spatial effects
4. **Use insights** to design better experiments and applications

The extended topology framework provides powerful tools for understanding how spatial structure affects dual-process decision-making in refugee movement scenarios!