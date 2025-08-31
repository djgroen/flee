#!/usr/bin/env python3
"""
Example script demonstrating dimensionless parameter analysis.

This script shows how to use the dimensionless parameter analysis framework
to identify scaling relationships and create publication-ready visualizations.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import tempfile

from flee_dual_process.dimensionless_analysis import (
    DimensionlessParameterCalculator,
    UniversalScalingDetector
)
from flee_dual_process.dimensionless_visualization import (
    DimensionlessVisualizationGenerator,
    PlotConfiguration
)


def generate_synthetic_experiment_data(n_experiments: int = 100) -> pd.DataFrame:
    """Generate synthetic experimental data for demonstration."""
    np.random.seed(42)
    
    # Generate parameter combinations
    conflict_intensities = np.random.uniform(0.1, 1.0, n_experiments)
    connectivities = np.random.uniform(1.0, 8.0, n_experiments)
    recovery_times = np.random.uniform(5.0, 30.0, n_experiments)
    populations = np.random.uniform(100, 1000, n_experiments)
    distances = np.random.uniform(50, 200, n_experiments)
    movement_speeds = np.random.uniform(10, 100, n_experiments)
    
    # Calculate dimensionless parameters
    calculator = DimensionlessParameterCalculator()
    
    cognitive_pressures = []
    reynolds_analogs = []
    
    for i in range(n_experiments):
        # Cognitive pressure
        cp = calculator.calculate_cognitive_pressure(
            conflict_intensities[i], connectivities[i], recovery_times[i]
        )
        cognitive_pressures.append(cp)
        
        # Reynolds number analog
        ra = calculator.calculate_dimensionless_parameter(
            'reynolds_number_analog',
            {
                'population': populations[i],
                'movement_speed': movement_speeds[i],
                'connectivity': connectivities[i],
                'distance': distances[i]
            }
        )
        reynolds_analogs.append(ra)
    
    # Generate synthetic responses with known scaling relationships
    # System 2 activation follows sigmoid relationship with cognitive pressure
    system2_rates = 1.0 / (1.0 + np.exp(-3.0 * (np.array(cognitive_pressures) - 0.5)))
    system2_rates += 0.05 * np.random.randn(n_experiments)  # Add noise
    
    # Movement rate follows power law with cognitive pressure
    movement_rates = 2.0 * np.power(cognitive_pressures, 0.8)
    movement_rates += 0.1 * np.random.randn(n_experiments)  # Add noise
    
    # Flow efficiency depends on Reynolds analog
    flow_efficiencies = 0.5 + 0.4 * np.tanh(0.1 * (np.array(reynolds_analogs) - 50))
    flow_efficiencies += 0.05 * np.random.randn(n_experiments)  # Add noise
    
    # Add grouping variables for data collapse analysis
    scenarios = np.random.choice(['conflict_spike', 'gradual_escalation', 'cascading'], n_experiments)
    topologies = np.random.choice(['linear', 'star', 'grid'], n_experiments)
    
    return pd.DataFrame({
        'conflict_intensity': conflict_intensities,
        'connectivity': connectivities,
        'recovery_time': recovery_times,
        'population': populations,
        'distance': distances,
        'movement_speed': movement_speeds,
        'cognitive_pressure': cognitive_pressures,
        'reynolds_analog': reynolds_analogs,
        'system2_activation_rate': system2_rates,
        'movement_rate': movement_rates,
        'flow_efficiency': flow_efficiencies,
        'scenario': scenarios,
        'topology': topologies
    })


def main():
    """Main demonstration function."""
    print("Dimensionless Parameter Analysis Example")
    print("=" * 50)
    
    # Generate synthetic data
    print("1. Generating synthetic experimental data...")
    data = generate_synthetic_experiment_data(150)
    print(f"   Generated {len(data)} experimental data points")
    
    # Initialize analysis tools
    calculator = DimensionlessParameterCalculator()
    detector = UniversalScalingDetector()
    
    # Configure visualization
    config = PlotConfiguration(
        figsize=(12, 8),
        dpi=150,
        font_size=12,
        color_palette='Set2'
    )
    visualizer = DimensionlessVisualizationGenerator(config)
    
    print("\n2. Analyzing dimensionless parameters...")
    
    # Identify dimensionless parameter combinations
    available_params = ['conflict_intensity', 'connectivity', 'recovery_time', 
                       'population', 'movement_speed', 'distance']
    
    discovered_combinations = calculator.identify_dimensionless_combinations(
        available_params, max_exponent=2
    )
    
    print(f"   Found {len(discovered_combinations)} dimensionless parameter combinations:")
    for combo in discovered_combinations[:3]:  # Show first 3
        print(f"   - {combo.name}: {combo.formula}")
    
    # Validate parameter scaling
    print("\n3. Validating parameter scaling relationships...")
    
    dimensionless_params = ['cognitive_pressure', 'reynolds_analog']
    dependent_variables = ['system2_activation_rate', 'movement_rate', 'flow_efficiency']
    
    for dim_param in dimensionless_params:
        for dep_var in dependent_variables:
            validation_result = calculator.validate_parameter_scaling(
                data, dim_param, dep_var
            )
            
            if validation_result['valid']:
                scaling_results = validation_result['scaling_relationships']
                best_fit = max(scaling_results.items(), 
                             key=lambda x: x[1].get('r_squared', 0) if isinstance(x[1], dict) else 0)
                
                if isinstance(best_fit[1], dict) and 'r_squared' in best_fit[1]:
                    print(f"   {dim_param} vs {dep_var}: {best_fit[0]} fit (R² = {best_fit[1]['r_squared']:.3f})")
    
    # Detect universal scaling relationships
    print("\n4. Detecting universal scaling relationships...")
    
    relationships = detector.detect_scaling_relationships(
        data, dimensionless_params, dependent_variables
    )
    
    print(f"   Found {len(relationships)} significant scaling relationships:")
    for rel in relationships:
        print(f"   - {rel.parameter} → {rel.dependent_variable}: {rel.scaling_function} (R² = {rel.r_squared:.3f})")
    
    # Create visualizations
    print("\n5. Creating visualizations...")
    
    # Create temporary directory for outputs
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"   Saving plots to: {temp_dir}")
        
        # Data collapse plot
        try:
            fig1 = visualizer.create_data_collapse_plot(
                data,
                'cognitive_pressure',
                'system2_activation_rate',
                'scenario',
                title='Universal Scaling: System 2 Activation vs Cognitive Pressure',
                save_path=os.path.join(temp_dir, 'data_collapse.png')
            )
            plt.close(fig1)
            print("   ✓ Data collapse plot created")
        except Exception as e:
            print(f"   ✗ Data collapse plot failed: {e}")
        
        # Scaling relationships plot
        if relationships:
            try:
                fig2 = visualizer.create_scaling_relationship_plot(
                    data,
                    relationships,
                    title='Universal Scaling Relationships',
                    save_path=os.path.join(temp_dir, 'scaling_relationships.png')
                )
                plt.close(fig2)
                print("   ✓ Scaling relationships plot created")
            except Exception as e:
                print(f"   ✗ Scaling relationships plot failed: {e}")
        
        # Parameter sensitivity heatmap
        try:
            fig3 = visualizer.create_parameter_sensitivity_heatmap(
                data,
                dimensionless_params,
                dependent_variables,
                title='Dimensionless Parameter Sensitivity Analysis',
                save_path=os.path.join(temp_dir, 'sensitivity_heatmap.png')
            )
            plt.close(fig3)
            print("   ✓ Parameter sensitivity heatmap created")
        except Exception as e:
            print(f"   ✗ Parameter sensitivity heatmap failed: {e}")
        
        # Parameter summary table
        try:
            table_df = visualizer.create_dimensionless_parameter_table(
                data,
                dimensionless_params,
                save_path=os.path.join(temp_dir, 'parameter_table.csv')
            )
            print("   ✓ Parameter summary table created")
            print("\n   Parameter Summary:")
            print(table_df.to_string(index=False))
        except Exception as e:
            print(f"   ✗ Parameter summary table failed: {e}")
        
        # Generate complete publication figure set
        try:
            generated_files = visualizer.generate_publication_figures(
                data,
                temp_dir,
                prefix='example'
            )
            print(f"\n   ✓ Generated {len(generated_files)} publication figures:")
            for fig_type, file_path in generated_files.items():
                if file_path and os.path.exists(file_path):
                    print(f"     - {fig_type}: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"   ✗ Publication figures generation failed: {e}")
    
    print("\n6. Data collapse validation...")
    
    # Test data collapse quality
    collapse_results = detector.validate_data_collapse(
        data,
        'cognitive_pressure',
        ['system2_activation_rate', 'movement_rate'],
        ['scenario']
    )
    
    for var, result in collapse_results.items():
        if result['valid']:
            quality = result['quality_assessment']
            print(f"   {var}: {quality} collapse quality (CV = {result['collapse_quality']:.3f})")
    
    print("\n" + "=" * 50)
    print("Analysis complete! Key findings:")
    print(f"- Identified {len(discovered_combinations)} dimensionless parameter combinations")
    print(f"- Found {len(relationships)} universal scaling relationships")
    print("- Cognitive pressure shows strong correlation with System 2 activation")
    print("- Reynolds analog affects flow efficiency in refugee movement")
    print("- Data collapse demonstrates universal scaling behavior")
    
    print("\nThis framework can be applied to real experimental data to:")
    print("- Identify fundamental scaling laws in refugee movement")
    print("- Create generalizable models across different contexts")
    print("- Generate publication-ready figures and analysis")


if __name__ == '__main__':
    main()