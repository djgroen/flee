#!/usr/bin/env python3
"""
Example Usage of the Visualization Generator System

This script demonstrates how to use the visualization generator for dual-process experiments.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visualization_generator import VisualizationGenerator, PlotConfig


def main():
    """
    Example usage of the visualization generator.
    """
    
    # Example 1: Basic usage with matplotlib backend
    print("Example 1: Basic Visualization Generation")
    print("=" * 50)
    
    # Specify your results directory
    results_directory = "path/to/your/experiment/results"
    
    # Create visualization generator with matplotlib backend
    viz_gen = VisualizationGenerator(
        results_directory=results_directory,
        backend='matplotlib',
        plot_config=PlotConfig(
            figsize=(12, 8),
            dpi=300,
            style='seaborn-v0_8',
            color_palette='Set2'
        )
    )
    
    # List of experiment directories to analyze
    experiment_dirs = [
        "path/to/experiment1",
        "path/to/experiment2", 
        "path/to/experiment3"
    ]
    
    # Generate cognitive state plots
    print("Generating cognitive state plots...")
    cognitive_plots = viz_gen.create_cognitive_state_plots(
        experiment_dirs,
        plot_types=['evolution', 'distribution', 'transitions']
    )
    print(f"Generated {len(cognitive_plots)} cognitive state plots")
    
    # Generate movement comparison charts
    print("Generating movement comparison charts...")
    movement_plots = viz_gen.create_movement_comparison_charts(experiment_dirs)
    print(f"Generated {len(movement_plots)} movement comparison charts")
    
    # Generate experiment report
    print("Generating experiment report...")
    report_file = viz_gen.generate_experiment_report(
        experiment_dirs,
        report_title="My Dual Process Experiment Analysis",
        output_format="html"
    )
    print(f"Generated report: {report_file}")
    
    print("\nExample 2: Parameter Sensitivity Analysis")
    print("=" * 50)
    
    # For parameter sweep analysis
    sweep_results_directory = "path/to/parameter/sweep/results"
    
    # Generate parameter sensitivity plots
    print("Generating parameter sensitivity plots...")
    sensitivity_plots = viz_gen.create_parameter_sensitivity_plots(
        sweep_results_directory,
        parameters=['awareness_level', 'social_connectivity', 'conflict_threshold'],
        metrics=['first_movement_day', 'destination_entropy', 'cognitive_transitions']
    )
    print(f"Generated {len(sensitivity_plots)} parameter sensitivity plots")
    
    print("\nExample 3: Using Plotly Backend")
    print("=" * 50)
    
    try:
        # Create visualization generator with plotly backend
        viz_gen_plotly = VisualizationGenerator(
            results_directory=results_directory,
            backend='plotly'
        )
        
        # Generate interactive plots
        print("Generating interactive cognitive state plots...")
        interactive_plots = viz_gen_plotly.create_cognitive_state_plots(
            experiment_dirs[:2],  # Use fewer experiments for demo
            plot_types=['evolution']
        )
        print(f"Generated {len(interactive_plots)} interactive plots")
        
    except ImportError:
        print("Plotly not available - install with: pip install plotly")
    
    print("\nExample 4: Custom Plot Configuration")
    print("=" * 50)
    
    # Custom plot configuration
    custom_config = PlotConfig(
        figsize=(15, 10),
        dpi=150,
        style='default',
        color_palette='viridis',
        font_size=14,
        title_size=16,
        save_format='pdf'  # Save as PDF instead of PNG
    )
    
    viz_gen_custom = VisualizationGenerator(
        results_directory=results_directory,
        backend='matplotlib',
        plot_config=custom_config
    )
    
    print("Using custom configuration for high-quality PDF outputs...")
    
    print("\nExample 5: Grouped Comparisons")
    print("=" * 50)
    
    # Define comparison groups
    comparison_groups = {
        'System1_Only': ['exp_s1_linear', 'exp_s1_star', 'exp_s1_grid'],
        'System2_Full': ['exp_s2_linear', 'exp_s2_star', 'exp_s2_grid'],
        'Dual_Process': ['exp_dual_linear', 'exp_dual_star', 'exp_dual_grid']
    }
    
    # Generate grouped comparison charts
    print("Generating grouped comparison charts...")
    grouped_plots = viz_gen.create_movement_comparison_charts(
        experiment_dirs,
        comparison_groups=comparison_groups
    )
    print(f"Generated {len(grouped_plots)} grouped comparison charts")
    
    print("\nVisualization Examples Complete!")
    print("Check the output directory for generated plots and reports.")


if __name__ == "__main__":
    main()