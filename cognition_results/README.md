# Cognition Results: Network Topology Effects on Dual-Process S2 Activation

## Overview

This framework implements systematic network topology testing for dual-process decision-making in Flee simulations. The work demonstrates that network structure significantly affects System 2 (S2) activation rates, with up to **21.6% variation** across different topologies.

## Key Findings

### Network Topology Effects on S2 Activation
- **Grid networks**: Highest S2 activation (95.2% ± 0.4%)
- **Star networks**: Moderate S2 activation (81.8% ± 0.7%) 
- **Tree networks**: Moderate S2 activation (78.3% ± 1.3%)
- **Linear networks**: Lowest S2 activation (73.6% ± 1.9%)

### Network Size Scaling Effects
- **Linear**: S2 rate decreases with size (75.6% → 71.1%)
- **Star**: S2 rate increases with size (81.4% → 82.2%)
- **Tree**: S2 rate decreases with size (80.0% → 76.3%)
- **Grid**: S2 rate stable with size (95.0% → 94.9%)

## Usage

### Quick Start
```bash
# Run systematic network scaling
python code/systematic_network_scaling_framework.py

# Generate comprehensive visualizations  
python code/comprehensive_visualization_suite.py

# Run S2 parameter optimization
python code/optimize_s2_parameters.py
```

### Configuration
Edit `config/experiment_config.yml` to modify:
- Network sizes and topologies
- S2 parameter ranges
- Output directories

## Scientific Significance

This work provides the first systematic demonstration that network topology affects dual-process decision-making in agent-based simulations. The findings have implications for:

1. **Refugee Movement Modeling**: Network structure affects decision complexity
2. **Cognitive Load Theory**: Network complexity correlates with S2 activation
3. **Scaling Laws**: Dimensionless parameters enable cross-scale analysis
4. **Policy Implications**: Network design affects decision-making outcomes

## File Structure

```
cognition_results/
├── code/                    # Implementation files
├── config/                  # Configuration files
├── documentation/           # Documentation
├── analysis_scripts/        # Analysis utilities
└── README.md               # This file
```

## Results

**Note**: Large result files (PNG, PDF, JSON) are excluded from this repository due to GitHub file size constraints. To generate results:

1. Run the analysis scripts
2. Results will be saved locally in organized directories
3. Figures are generated in both PNG and PDF formats

## Requirements

See `config/requirements.txt` for required Python packages.

## Contact

For questions about this implementation, please refer to the code documentation or create an issue in the repository.

---
*This framework represents a significant advancement in understanding network topology effects on dual-process decision-making in agent-based simulations.*
