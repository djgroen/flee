# Dimensionless Parameter Analysis Framework

This module provides comprehensive tools for dimensionless parameter analysis in dual-process refugee movement experiments. It implements the requirements from task 19 of the dual-process experiments specification.

## Overview

The framework consists of two main components:

1. **Dimensionless Analysis** (`dimensionless_analysis.py`) - Core analysis capabilities
2. **Dimensionless Visualization** (`dimensionless_visualization.py`) - Publication-ready visualizations

## Key Features

### Dimensionless Parameter Identification
- **Cognitive Pressure Calculation**: Primary dimensionless parameter `(conflict_intensity × connectivity) / recovery_time`
- **Automatic Discovery**: Identifies other dimensionless combinations from experimental parameters
- **Dimensional Validation**: Ensures parameter combinations are truly dimensionless
- **Known Parameters**: Includes Reynolds and Peclet number analogs for refugee flow dynamics

### Universal Scaling Detection
- **Multiple Scaling Functions**: Linear, power law, exponential, sigmoid, logarithmic, double exponential
- **Statistical Validation**: R-squared analysis and significance testing
- **Data Collapse Validation**: Tests for universal scaling behavior across different experimental conditions
- **Confidence Intervals**: Provides uncertainty quantification for scaling relationships

### Visualization Framework
- **Data Collapse Plots**: Before/after collapse visualization showing universal scaling
- **Scaling Relationship Plots**: Multiple scaling functions with fit parameters and R-squared values
- **Parameter Sensitivity Heatmaps**: Correlation analysis and effect size visualization
- **Interactive Explorers**: Plotly-based interactive parameter exploration (optional)
- **Publication Figures**: Complete set of publication-ready figures with customizable styling

## Usage Example

```python
from flee_dual_process.dimensionless_analysis import DimensionlessParameterCalculator
from flee_dual_process.dimensionless_visualization import DimensionlessVisualizationGenerator

# Initialize tools
calculator = DimensionlessParameterCalculator()
visualizer = DimensionlessVisualizationGenerator()

# Calculate cognitive pressure
pressure = calculator.calculate_cognitive_pressure(
    conflict_intensity=0.5,
    connectivity=4.0,
    recovery_time=10.0
)

# Generate complete publication figure set
generated_files = visualizer.generate_publication_figures(
    data, output_dir, prefix='experiment'
)
```

## Files

- `dimensionless_analysis.py` - Core analysis classes and functions
- `dimensionless_visualization.py` - Visualization and plotting tools
- `test_dimensionless_analysis.py` - Comprehensive test suite for analysis
- `test_dimensionless_visualization.py` - Comprehensive test suite for visualization
- `example_dimensionless_analysis.py` - Complete working example

## Key Classes

### DimensionlessParameterCalculator
- `calculate_cognitive_pressure()` - Primary cognitive pressure parameter
- `calculate_dimensionless_parameter()` - Calculate any known dimensionless parameter
- `identify_dimensionless_combinations()` - Automatic discovery of dimensionless combinations
- `validate_parameter_scaling()` - Validate scaling relationships in data

### UniversalScalingDetector
- `detect_scaling_relationships()` - Find universal scaling laws in data
- `validate_data_collapse()` - Test for data collapse quality
- Multiple scaling function fitting with statistical validation

### DimensionlessVisualizationGenerator
- `create_data_collapse_plot()` - Universal scaling visualization
- `create_scaling_relationship_plot()` - Scaling function plots
- `create_parameter_sensitivity_heatmap()` - Sensitivity analysis
- `create_dimensionless_parameter_table()` - Publication-ready parameter tables
- `generate_publication_figures()` - Complete figure generation

## Requirements Satisfied

### Task 19.1: Dimensionless Parameter Identification System
✅ Cognitive pressure calculator: `(conflict_intensity × connectivity) / recovery_time`
✅ Automatic identification of dimensionless combinations
✅ Parameter scaling validation with dimensional consistency
✅ Universal scaling relationship detection algorithms

### Task 19.2: Dimensionless Visualization Framework
✅ Data collapse visualization with universal scaling curves
✅ Scaling curve fitting and validation tools
✅ Parameter sensitivity analysis and heatmaps
✅ Publication-ready tables and figures

## Testing

The framework includes comprehensive test suites:

```bash
# Run all dimensionless analysis tests
python -m pytest flee_dual_process/test_dimensionless_analysis.py -v

# Run all visualization tests  
python -m pytest flee_dual_process/test_dimensionless_visualization.py -v

# Run example demonstration
python flee_dual_process/example_dimensionless_analysis.py
```

## Dependencies

- **Core**: numpy, pandas, scipy, matplotlib, seaborn
- **Optional**: plotly (for interactive visualizations)
- **Testing**: unittest, pytest

## Integration

This framework integrates with the broader dual-process experiments system:

- Uses experimental data from parameter sweeps
- Provides analysis for hypothesis testing (H1-H4)
- Generates figures for publication and reporting
- Supports real-world case study analysis

The dimensionless analysis capabilities enable researchers to:

1. **Identify Universal Laws**: Find scaling relationships that generalize across contexts
2. **Validate Theory**: Test dual-process theory predictions with dimensionless parameters
3. **Create Generalizable Models**: Develop models that work across different scales and scenarios
4. **Generate Publications**: Create publication-ready figures and analysis tables

This completes the implementation of Task 19: Implement Dimensionless Parameter Analysis from the dual-process experiments specification.