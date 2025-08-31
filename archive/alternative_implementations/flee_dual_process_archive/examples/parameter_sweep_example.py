#!/usr/bin/env python3
"""
Parameter Sweep Example

This script demonstrates how to conduct systematic parameter sweeps to test
the sensitivity of dual-process decision-making to key parameters.
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path

# Add flee_dual_process to path if needed
sys.path.append(str(Path(__file__).parent.parent))

from flee_dual_process import (
    LinearTopologyGenerator,
    GradualConflictGenerator,
    ConfigurationManager,
    ExperimentRunner,
    AnalysisPipeline,
    VisualizationGenerator
)


def main():
    """Run parameter sweep experiment."""
    
    print("=== Parameter Sweep Experiment ===\n")
    
    # Create output directory
    output_base = Path("examples/parameter_sweep_output")
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Generate Experimental Setup
    print("1. Setting up experimental infrastructure...")
    
    # Generate topology (reused for all experiments)
    topology_gen = LinearTopologyGenerator({
        'output_dir': str(output_base / 'topology')
    })
    
    locations_file, routes_file = topology_gen.generate_linear(
        n_nodes=6,
        segment_distance=35.0,
        start_pop=12000,
        pop_decay=0.8
    )
    
    # Generate scenario (gradual conflict for testing System 2 planning)
    scenario_gen = GradualConflictGenerator(locations_file)
    
    conflicts_file = scenario_gen.generate_gradual_conflict(
        origin='Origin',
        start_day=0,
        end_day=25,  # 25-day escalation period
        max_intensity=0.75,
        output_dir=str(output_base / 'scenario')
    )
    
    print(f"   ✓ Topology: {locations_file}")
    print(f"   ✓ Scenario: {conflicts_file}")
    
    # Step 2: Define Parameter Sweeps
    print("\n2. Defining parameter sweeps...")
    
    config_manager = ConfigurationManager()
    base_config = config_manager.create_cognitive_config('dual_process')
    
    # Define parameters to sweep and their ranges
    parameter_sweeps = {
        'awareness_level': {
            'parameter': 'move_rules.awareness_level',
            'values': [1, 2, 3],
            'description': 'Agent awareness of distant locations'
        },
        'social_connectivity': {
            'parameter': 'move_rules.average_social_connectivity',
            'values': [0.0, 2.0, 4.0, 6.0, 8.0],
            'description': 'Average social connections per agent'
        },
        'conflict_threshold': {
            'parameter': 'move_rules.conflict_threshold',
            'values': [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            'description': 'Conflict level triggering System 2 activation'
        },
        'recovery_period': {
            'parameter': 'move_rules.recovery_period_max',
            'values': [7, 14, 21, 30, 45],
            'description': 'Maximum recovery period after System 2 activation'
        }
    }
    
    print(f"   Defined {len(parameter_sweeps)} parameter sweeps:")
    for name, sweep_info in parameter_sweeps.items():
        print(f"   - {name}: {len(sweep_info['values'])} values")
        print(f"     {sweep_info['description']}")
    
    # Step 3: Generate Parameter Configurations
    print("\n3. Generating parameter configurations...")
    
    sweep_configurations = {}
    total_experiments = 0
    
    for sweep_name, sweep_info in parameter_sweeps.items():
        configs = config_manager.generate_parameter_sweep(
            base_config=base_config,
            parameter=sweep_info['parameter'],
            values=sweep_info['values']
        )
        
        sweep_configurations[sweep_name] = {
            'configs': configs,
            'info': sweep_info
        }
        
        total_experiments += len(configs)
        print(f"   ✓ {sweep_name}: {len(configs)} configurations")
    
    print(f"\n   Total experiments to run: {total_experiments}")
    
    # Step 4: Set Up Experiment Runner
    print("\n4. Setting up experiment runner...")
    
    runner = ExperimentRunner(
        max_parallel=4,  # Adjust based on your system
        base_output_dir=str(output_base / 'results'),
        timeout=2400     # 40-minute timeout per experiment
    )
    
    # Base experiment configuration
    base_experiment = {
        'topology_files': (locations_file, routes_file),
        'conflicts_file': conflicts_file,
        'simulation_days': 100
    }
    
    print("   ✓ Runner configured for parallel execution")
    
    # Step 5: Execute Parameter Sweeps
    print("\n5. Executing parameter sweeps...")
    
    sweep_results = {}
    total_start_time = time.time()
    
    for sweep_name, sweep_data in sweep_configurations.items():
        print(f"\n   Running {sweep_name} sweep...")
        print(f"   Parameter: {sweep_data['info']['parameter']}")
        print(f"   Values: {sweep_data['info']['values']}")
        
        start_time = time.time()
        
        # Create sweep configuration
        sweep_config = {
            'base_experiment': base_experiment,
            'parameter_configs': sweep_data['configs'],
            'sweep_id': f'sweep_{sweep_name}'
        }
        
        # Execute parameter sweep
        results = runner.run_parameter_sweep(sweep_config)
        sweep_results[sweep_name] = results
        
        # Report progress
        completed = len([r for r in results if r['status'] == 'completed'])
        failed = len([r for r in results if r['status'] == 'failed'])
        duration = time.time() - start_time
        
        print(f"   ✓ Completed: {completed}/{len(results)} ({100*completed/len(results):.1f}%)")
        if failed > 0:
            print(f"   ✗ Failed: {failed}")
        print(f"   ⏱ Duration: {duration:.1f} seconds")
    
    total_duration = time.time() - total_start_time
    print(f"\n   Total sweep execution time: {total_duration:.1f} seconds")
    
    # Step 6: Analyze Parameter Sensitivity
    print("\n6. Analyzing parameter sensitivity...")
    
    analyzer = AnalysisPipeline(str(output_base / 'results'))
    sensitivity_results = {}
    
    for sweep_name, results in sweep_results.items():
        print(f"\n   Analyzing {sweep_name} sensitivity...")
        
        # Extract successful experiments
        successful_results = [r for r in results if r['status'] == 'completed']
        
        if len(successful_results) < 2:
            print(f"   ⚠ Insufficient successful experiments ({len(successful_results)})")
            continue
        
        # Analyze sensitivity
        sensitivity_analysis = analyze_parameter_sensitivity(
            successful_results, 
            sweep_configurations[sweep_name]['info']['parameter'],
            analyzer
        )
        
        sensitivity_results[sweep_name] = sensitivity_analysis
        
        # Print key findings
        print(f"   📊 First move correlation: {sensitivity_analysis['first_move_correlation']:.3f}")
        print(f"   📊 Distance correlation: {sensitivity_analysis['distance_correlation']:.3f}")
        print(f"   📊 Effect size: {sensitivity_analysis['effect_size']:.3f}")
        
        if abs(sensitivity_analysis['first_move_correlation']) > 0.5:
            print(f"   🔍 Strong correlation detected!")
        elif abs(sensitivity_analysis['first_move_correlation']) > 0.3:
            print(f"   🔍 Moderate correlation detected")
    
    # Step 7: Create Sensitivity Summary
    print("\n7. Creating sensitivity summary...")
    
    if sensitivity_results:
        # Create summary table
        summary_data = []
        
        for sweep_name, analysis in sensitivity_results.items():
            summary_data.append({
                'Parameter': sweep_name,
                'First Move Correlation': analysis['first_move_correlation'],
                'Distance Correlation': analysis['distance_correlation'],
                'Entropy Correlation': analysis['entropy_correlation'],
                'Effect Size': analysis['effect_size'],
                'N Experiments': analysis['n_experiments']
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Save summary
        summary_file = output_base / 'sensitivity_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        
        print(f"   ✓ Sensitivity summary saved: {summary_file}")
        
        # Print summary table
        print("\n   Sensitivity Summary:")
        print("   " + "="*80)
        print(f"   {'Parameter':<20} {'First Move':<12} {'Distance':<12} {'Entropy':<12} {'Effect Size':<12}")
        print("   " + "-"*80)
        
        for _, row in summary_df.iterrows():
            print(f"   {row['Parameter']:<20} {row['First Move Correlation']:<12.3f} "
                  f"{row['Distance Correlation']:<12.3f} {row['Entropy Correlation']:<12.3f} "
                  f"{row['Effect Size']:<12.3f}")
        
        print("   " + "="*80)
    
    # Step 8: Generate Visualizations
    print("\n8. Generating visualizations...")
    
    if sensitivity_results:
        try:
            viz_gen = VisualizationGenerator(
                results_directory=str(output_base / 'results'),
                output_directory=str(output_base / 'visualizations')
            )
            
            # Create sensitivity heatmap
            create_sensitivity_heatmap(sensitivity_results, output_base / 'visualizations')
            
            # Create parameter response curves
            for sweep_name in sensitivity_results.keys():
                create_parameter_response_curve(
                    sweep_results[sweep_name],
                    sweep_configurations[sweep_name]['info']['parameter'],
                    analyzer,
                    output_base / 'visualizations',
                    sweep_name
                )
            
            print("   ✓ Visualizations generated successfully")
            
        except Exception as e:
            print(f"   ⚠ Visualization generation failed: {e}")
    
    # Step 9: Generate Comprehensive Report
    print("\n9. Generating comprehensive report...")
    
    report_file = output_base / 'parameter_sweep_report.txt'
    
    with open(report_file, 'w') as f:
        f.write("Parameter Sweep Experiment Report\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Experiment Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Execution Time: {total_duration:.1f} seconds\n")
        f.write(f"Total Experiments: {total_experiments}\n\n")
        
        f.write("Experimental Setup:\n")
        f.write("- Topology: Linear chain with 6 locations\n")
        f.write("- Scenario: Gradual conflict (25-day escalation)\n")
        f.write("- Base Cognitive Mode: Dual Process\n")
        f.write("- Simulation Duration: 100 days\n\n")
        
        f.write("Parameter Sweeps:\n")
        f.write("-" * 20 + "\n")
        
        for sweep_name, sweep_data in sweep_configurations.items():
            f.write(f"\n{sweep_name}:\n")
            f.write(f"  Parameter: {sweep_data['info']['parameter']}\n")
            f.write(f"  Values: {sweep_data['info']['values']}\n")
            f.write(f"  Description: {sweep_data['info']['description']}\n")
            
            if sweep_name in sweep_results:
                results = sweep_results[sweep_name]
                completed = len([r for r in results if r['status'] == 'completed'])
                f.write(f"  Completed: {completed}/{len(results)}\n")
        
        if sensitivity_results:
            f.write(f"\nSensitivity Analysis:\n")
            f.write("-" * 20 + "\n")
            
            for sweep_name, analysis in sensitivity_results.items():
                f.write(f"\n{sweep_name}:\n")
                f.write(f"  First Move Correlation: {analysis['first_move_correlation']:.3f}\n")
                f.write(f"  Distance Correlation: {analysis['distance_correlation']:.3f}\n")
                f.write(f"  Entropy Correlation: {analysis['entropy_correlation']:.3f}\n")
                f.write(f"  Effect Size: {analysis['effect_size']:.3f}\n")
                f.write(f"  Statistical Significance: {analysis['first_move_p_value']:.3f}\n")
        
        f.write(f"\nOutput Files:\n")
        f.write(f"- Results Directory: {output_base / 'results'}\n")
        f.write(f"- Visualizations: {output_base / 'visualizations'}\n")
        f.write(f"- Sensitivity Summary: {summary_file}\n")
    
    print(f"   ✓ Report saved: {report_file}")
    
    # Final Summary
    print(f"\n{'='*60}")
    print("PARAMETER SWEEP COMPLETED")
    print(f"{'='*60}")
    
    total_successful = sum(len([r for r in results if r['status'] == 'completed']) 
                          for results in sweep_results.values())
    
    print(f"Total successful experiments: {total_successful}/{total_experiments}")
    print(f"Total execution time: {total_duration:.1f} seconds")
    print(f"Average time per experiment: {total_duration/total_experiments:.1f} seconds")
    
    if sensitivity_results:
        print(f"\nKey Sensitivity Findings:")
        
        # Find most sensitive parameters
        correlations = [(name, abs(analysis['first_move_correlation'])) 
                       for name, analysis in sensitivity_results.items()]
        correlations.sort(key=lambda x: x[1], reverse=True)
        
        print(f"Most sensitive parameters (by first move correlation):")
        for i, (param_name, correlation) in enumerate(correlations[:3], 1):
            print(f"{i}. {param_name}: {correlation:.3f}")
    
    print(f"\nFor detailed analysis, see: {report_file}")
    print(f"For visualizations, check: {output_base / 'visualizations'}")
    
    return total_successful > total_experiments * 0.8  # 80% success rate


def analyze_parameter_sensitivity(successful_results, parameter_name, analyzer):
    """Analyze sensitivity of outcomes to parameter changes."""
    
    from scipy.stats import pearsonr
    
    # Extract parameter values and metrics
    param_values = []
    first_move_days = []
    total_distances = []
    destination_entropy = []
    
    for result in successful_results:
        # Extract parameter value from configuration
        param_parts = parameter_name.split('.')
        param_value = result['metadata']['config']
        for part in param_parts:
            param_value = param_value[part]
        param_values.append(param_value)
        
        # Calculate metrics
        metrics = analyzer.calculate_movement_metrics(result['output_dir'])
        first_move_days.append(metrics['first_move_day']['mean'])
        total_distances.append(metrics['total_distance']['mean'])
        destination_entropy.append(metrics['destination_distribution']['entropy'])
    
    # Calculate correlations
    first_move_corr, first_move_p = pearsonr(param_values, first_move_days)
    distance_corr, distance_p = pearsonr(param_values, total_distances)
    entropy_corr, entropy_p = pearsonr(param_values, destination_entropy)
    
    # Calculate effect size (Cohen's d for extreme values)
    if len(param_values) >= 4:
        low_quartile = np.percentile(param_values, 25)
        high_quartile = np.percentile(param_values, 75)
        
        low_indices = [i for i, v in enumerate(param_values) if v <= low_quartile]
        high_indices = [i for i, v in enumerate(param_values) if v >= high_quartile]
        
        if low_indices and high_indices:
            low_moves = [first_move_days[i] for i in low_indices]
            high_moves = [first_move_days[i] for i in high_indices]
            
            # Cohen's d
            pooled_std = np.sqrt(((len(low_moves)-1)*np.var(low_moves) + 
                                 (len(high_moves)-1)*np.var(high_moves)) / 
                                (len(low_moves) + len(high_moves) - 2))
            
            if pooled_std > 0:
                effect_size = (np.mean(high_moves) - np.mean(low_moves)) / pooled_std
            else:
                effect_size = 0.0
        else:
            effect_size = 0.0
    else:
        effect_size = 0.0
    
    return {
        'parameter': parameter_name,
        'first_move_correlation': first_move_corr,
        'first_move_p_value': first_move_p,
        'distance_correlation': distance_corr,
        'distance_p_value': distance_p,
        'entropy_correlation': entropy_corr,
        'entropy_p_value': entropy_p,
        'effect_size': effect_size,
        'n_experiments': len(param_values),
        'param_values': param_values,
        'first_move_days': first_move_days,
        'total_distances': total_distances,
        'destination_entropy': destination_entropy
    }


def create_sensitivity_heatmap(sensitivity_results, output_dir):
    """Create heatmap showing parameter sensitivity across metrics."""
    
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Prepare data for heatmap
    parameters = list(sensitivity_results.keys())
    metrics = ['first_move_correlation', 'distance_correlation', 'entropy_correlation']
    metric_labels = ['First Move Day', 'Total Distance', 'Destination Entropy']
    
    heatmap_data = []
    for param in parameters:
        row = [sensitivity_results[param][metric] for metric in metrics]
        heatmap_data.append(row)
    
    # Create heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        heatmap_data,
        xticklabels=metric_labels,
        yticklabels=[p.replace('_', ' ').title() for p in parameters],
        annot=True,
        cmap='RdBu_r',
        center=0,
        vmin=-1,
        vmax=1,
        fmt='.3f'
    )
    plt.title('Parameter Sensitivity Analysis\n(Correlation with Outcome Metrics)')
    plt.tight_layout()
    
    output_file = output_dir / 'parameter_sensitivity_heatmap.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"   ✓ Sensitivity heatmap: {output_file}")


def create_parameter_response_curve(results, parameter_name, analyzer, output_dir, sweep_name):
    """Create response curve showing how metrics change with parameter values."""
    
    import matplotlib.pyplot as plt
    
    successful_results = [r for r in results if r['status'] == 'completed']
    
    if len(successful_results) < 3:
        return
    
    # Extract data
    param_values = []
    first_move_days = []
    total_distances = []
    
    for result in successful_results:
        # Extract parameter value
        param_parts = parameter_name.split('.')
        param_value = result['metadata']['config']
        for part in param_parts:
            param_value = param_value[part]
        param_values.append(param_value)
        
        # Calculate metrics
        metrics = analyzer.calculate_movement_metrics(result['output_dir'])
        first_move_days.append(metrics['first_move_day']['mean'])
        total_distances.append(metrics['total_distance']['mean'])
    
    # Create plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # First move day response
    ax1.scatter(param_values, first_move_days, alpha=0.7, s=50)
    ax1.set_xlabel(parameter_name.split('.')[-1].replace('_', ' ').title())
    ax1.set_ylabel('Average First Move Day')
    ax1.set_title('First Move Day Response')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line if enough points
    if len(param_values) >= 3:
        z = np.polyfit(param_values, first_move_days, 1)
        p = np.poly1d(z)
        sorted_params = sorted(param_values)
        ax1.plot(sorted_params, p(sorted_params), "r--", alpha=0.8, linewidth=2)
    
    # Total distance response
    ax2.scatter(param_values, total_distances, alpha=0.7, s=50, color='orange')
    ax2.set_xlabel(parameter_name.split('.')[-1].replace('_', ' ').title())
    ax2.set_ylabel('Average Total Distance (km)')
    ax2.set_title('Total Distance Response')
    ax2.grid(True, alpha=0.3)
    
    # Add trend line if enough points
    if len(param_values) >= 3:
        z = np.polyfit(param_values, total_distances, 1)
        p = np.poly1d(z)
        ax2.plot(sorted_params, p(sorted_params), "r--", alpha=0.8, linewidth=2)
    
    plt.suptitle(f'Parameter Response Curves: {sweep_name.replace("_", " ").title()}')
    plt.tight_layout()
    
    output_file = output_dir / f'{sweep_name}_response_curves.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"   ✓ Response curves: {output_file}")


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nParameter sweep interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nParameter sweep failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)