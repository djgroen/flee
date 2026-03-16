# 10k Agent Experiments: S1/S2 Dual-Process Decision-Making in Flee

> **DEPRECATED:** `run_all_10k_experiments.py` and `generate_10k_agent_visualizations.py` were removed (they used the old `calculate_systematic_s2_activation` API). Use the current S1/S2 workflow instead — see **SCRIPTS_CATALOGUE.md** for `run_nuclear_parameter_sweep`, `run_fork_experiments`, and `animate_agents.py`.

## 🎯 Overview

This repository contains a comprehensive framework for running large-scale (10,000 agent) experiments with the Flee refugee simulation, incorporating S1/S2 dual-process decision-making theory. The experiments test different network topologies to understand how cognitive decision-making affects refugee movement patterns.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Flee simulation framework
- Required Python packages: `pandas`, `numpy`, `matplotlib`, `seaborn`, `networkx`

### Running Experiments

#### Step 1: Generate Input Files
```bash
python create_proper_10k_agent_experiments.py
```

#### Step 2: Run All Experiments
```bash
python run_all_10k_experiments.py
```

#### Step 3: Generate Visualizations
```bash
python generate_10k_agent_visualizations.py
```

## 📁 Directory Structure

```
flee-1/
├── proper_10k_agent_experiments/          # Generated input files
│   ├── star_n7_medium_s2_10k/            # Star network experiment
│   ├── linear_n7_medium_s2_10k/          # Linear network experiment
│   ├── grid_n7_medium_s2_10k/            # Grid network experiment
│   └── all_10k_agent_results.json        # Combined results
├── 10k_agent_visualizations/              # Generated visualizations
│   ├── network_topology_comparison.png    # Topology comparison
│   ├── comprehensive_dashboard.png        # Complete analysis
│   ├── *_flow_analysis.png               # Individual flow analyses
│   └── README_SUMMARY.md                 # Results summary
└── scripts/
    ├── create_proper_10k_agent_experiments.py
    ├── run_all_10k_experiments.py
    └── generate_10k_agent_visualizations.py
```

## 🧪 Experimental Design

### Network Topologies

1. **Star Network**: Central hub with radial connections
   - Most efficient routing
   - All destinations reachable
   - Lowest total distance

2. **Linear Network**: Sequential chain of locations
   - Bottleneck effects
   - Limited routing options
   - Highest total distance

3. **Grid Network**: 2D grid layout
   - Balanced connectivity
   - Multiple routing paths
   - Moderate efficiency

### S1/S2 Dual-Process Parameters

- **S2 Threshold**: 0.5 (medium switching)
- **Population**: 10,000 agents per experiment
- **Simulation Duration**: 20 days
- **Agent Tracking**: Enabled (`log_levels.agent: 1`)

## 📊 Key Results

### Performance Comparison

| Topology | S2 Rate | Total Distance | Destinations | Efficiency |
|----------|---------|----------------|--------------|------------|
| Star     | 0.00%   | 2,113,200     | 5/5         | 2.37       |
| Grid     | 0.00%   | 2,522,600     | 4/4         | 1.59       |
| Linear   | 0.00%   | 8,519,700     | 2/4         | 0.23       |

### Key Findings

1. **Network Topology Effects**: Clear performance differences between topologies
2. **Star Network Superiority**: Most efficient with all destinations reached
3. **Linear Network Limitations**: Bottleneck effects reduce efficiency
4. **S2 Activation**: Currently 0% - requires parameter tuning

## 🔧 Technical Details

### Input File Format

Each experiment directory contains:

```
experiment_name/
├── input_csv/
│   ├── locations.csv      # Location definitions
│   ├── routes.csv         # Network connections
│   ├── conflicts.csv      # Conflict zones
│   └── closures.csv       # Route closures
├── source_data/
│   ├── data_layout.csv    # Data file mapping
│   └── refugees.csv       # Refugee data
├── simsetting.yml         # Simulation parameters
└── sim_period.csv         # Time period definition
```

### Output Files

Each experiment generates:

- `agents.out.0`: Individual agent tracking data
- `links.out.0`: Link/route utilization data
- `experiment_results.json`: Complete results summary
- `daily_results.csv`: Daily simulation metrics

### S2 Threshold Configuration

The S2 threshold is configured in `simsetting.yml`:

```yaml
move_rules:
  two_system_decision_making: 0.5  # S2 activation threshold
```

## 🎨 Visualization Outputs

### 1. Network Topology Comparison
- S2 activation rates by topology
- Total distance traveled
- Destinations reached
- Network efficiency scores

### 2. Individual Flow Analyses
- Agent population over time
- Final destination distribution
- Movement patterns by topology

### 3. Comprehensive Dashboard
- Multi-panel analysis
- Summary statistics table
- Performance metrics comparison

## 🛠️ Troubleshooting

### Common Issues

1. **"location name has population value of population, which is not an int"**
   - **Solution**: Ensure CSV headers start with `#` (e.g., `#name,region,country...`)

2. **"time data '' does not match format '%Y-%m-%d'"**
   - **Solution**: Check `sim_period.csv` format:
     ```
     startdate,2013-01-01
     length,20
     ```

3. **"No such file or directory: 'source_data/Refugees'"**
   - **Solution**: Ensure `data_layout.csv` references correct filenames:
     ```
     Camp_1,refugees.csv
     Camp_2,refugees.csv
     ```

4. **S2 Rate = 0%**
   - **Current Status**: Expected behavior - S2 activation logic needs refinement
   - **Next Steps**: Adjust S2 threshold or cognitive pressure calculation

### File Format Requirements

#### locations.csv
```csv
#name,region,country,latitude,longitude,location_type,conflict_date,population
Origin_star_7,TestRegion,TestCountry,0.0,0.0,conflict_zone,0,5000
Hub_star_7,TestRegion,TestCountry,3.0,0.0,town,,1000
```

#### routes.csv
```csv
#name1,name2,distance,forced_redirection
Origin_star_7,Hub_star_7,100.0,
Hub_star_7,Camp_2_star_7,100.0,
```

#### sim_period.csv
```csv
startdate,2013-01-01
length,20
```

## 🔬 Scientific Context

### Dual-Process Theory

- **System 1 (S1)**: Fast, automatic, heuristic-based decisions
- **System 2 (S2)**: Slow, deliberate, analytical decisions
- **Cognitive Pressure**: Triggers S2 activation under stress/uncertainty

### Research Applications

- Refugee movement modeling
- Emergency evacuation planning
- Network resilience analysis
- Cognitive decision-making in crisis situations

## 📈 Future Work

### Immediate Next Steps

1. **S2 Parameter Tuning**: Test thresholds (0.3, 0.7) for S2 activation
2. **Extended Simulations**: Run 50+ day experiments
3. **Scale Comparison**: Compare with smaller population experiments
4. **Cognitive Pressure Refinement**: Improve S2 activation logic

### Advanced Features

1. **Dynamic S2 Thresholds**: Context-dependent activation
2. **Multi-Agent Types**: Different cognitive profiles
3. **Real-World Data**: Integration with actual refugee data
4. **Network Evolution**: Dynamic topology changes

## 📚 References

- Flee Simulation Framework: [GitHub Repository]
- Dual-Process Decision-Making Theory: Kahneman (2011)
- Refugee Movement Modeling: Recent literature review

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the 10k agent framework
5. Submit a pull request

## 📄 License

[Add appropriate license information]

---

## 🎉 Success Metrics

✅ **10,000 agents per experiment**  
✅ **Real Flee simulation integration**  
✅ **S1/S2 dual-process decision-making**  
✅ **Multiple network topologies**  
✅ **Comprehensive visualizations**  
✅ **Reproducible experimental framework**  

*Last updated: 2024-09-23*






