#!/usr/bin/env python3
"""
Basic Dual Process Experiment Example

This script demonstrates how to set up and run a basic dual-process experiment
comparing System 1 vs System 2 decision-making in a simple linear topology.
"""

import os
import sys
import time
from pathlib import Path

# Add flee_dual_process to path if needed
sys.path.append(str(Path(__file__).parent.parent))

from flee_dual_process import (
    LinearTopologyGenerator,
    SpikeConflictGenerator,
    ConfigurationManager,
    ExperimentRunner,
    AnalysisPipeline,
    VisualizationGenerator
)


def main():
    """Run basic dual-process experiment."""
    
    print("=== Basic Dual Process Experiment ===\n")
    
    # Create output directory
    output_base = Path("examples/basic_experiment_output")
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Generate Network Topology
    print("1. Generating linear topology...")
    
    topology_gen = LinearTopologyGenerator({
        'output_dir': str(output_base / 'topology')
    })
    
    locations_file, routes_file = topology_gen.generate_linear(
        n_nodes=5,           # 5 locations: Origin -> Town_1 -> Town_2 -> Town_3 -> Camp_4
        segment_distance=40.0,  # 40km between each location
        start_pop=8000,      # 8,000 people at origin
        pop_decay=0.75       # Population decreases by 25% each step
    )
    
    print(f"   ✓ Locations: {locations_file}")
    print(f"   ✓ Routes: {routes_file}")
    
    # Step 2: Generate Conflict Scenario
    print("\n2. Generating spike conflict scenario...")
    
    scenario_gen = SpikeConflictGenerator(locations_file)
    
    conflicts_file = scenario_gen.generate_spike_conflict(
        origin='Origin',        # Conflict starts at the origin location
        start_day=0,           # Conflict begins immediately
        peak_intensity=0.85,   # High intensity conflict (85% of maximum)
        output_dir=str(output_base / 'scenario')
    )
    
    print(f"   ✓ Conflicts: {conflicts_file}")
    
    # Step 3: Create Cognitive Mode Configurations
    print("\n3. Creating cognitive mode configurations...")
    
    config_manager = ConfigurationManager()
    
    # System 1: Fast, intuitive decision-making
    s1_config = config_manager.create_cognitive_config('s1_only')
    
    # System 2: Slow, deliberate decision-making with social connectivity
    s2_config = config_manager.create_cognitive_config('s2_full')
    
    # Dual Process: Dynamic switching between System 1 and System 2
    dual_config = config_manager.create_cognitive_config('dual_process')
    
    print("   ✓ System 1 (fast, intuitive)")
    print("   ✓ System 2 (slow, deliberate)")
    print("   ✓ Dual Process (dynamic switching)")
    
    # Step 4: Set Up Experiment Runner
    print("\n4. Setting up experiment runner...")
    
    runner = ExperimentRunner(
        max_parallel=3,  # Run up to 3 experiments in parallel
        base_output_dir=str(output_base / 'results'),
        timeout=1800     # 30-minute timeout per experiment
    )
    
    print("   ✓ Runner configured for parallel execution")
    
    # Step 5: Define Base Experiment Configuration
    base_experiment = {
        'topology_files': (locations_file, routes_file),
        'conflicts_file': conflicts_file,
        'simulation_days': 80  # Run simulation for 80 days
    }
    
    # Step 6: Run Experiments
    print("\n5. Running experiments...")
    
    experiments = [
        ('System_1', s1_config),
        ('System_2', s2_config),
        ('Dual_Process', dual_config)
    ]
    
    results = []
    start_time = time.time()
    
    for exp_name, config in experiments:
        print(f"\n   Running {exp_name} experiment...")
        
        experiment_config = base_experiment.copy()
        experiment_config.update({
            'experiment_id': f'basic_{exp_name.lower()}',
            'config': config
        })
        
        result = runner.run_single_experiment(experiment_config)
        results.append((exp_name, result))
        
        if result['status'] == 'completed':
            print(f"   ✓ {exp_name} completed in {result['execution_time']:.1f}s")
        else:
            print(f"   ✗ {exp_name} failed: {result.get('error', 'Unknown error')}")
    
    total_time = time.time() - start_time
    print(f"\n   Total execution time: {total_time:.1f} seconds")
    
    # Step 7: Analyze Results
    print("\n6. Analyzing results...")
    
    analyzer = AnalysisPipeline(str(output_base / 'results'))
    
    analysis_results = {}
    successful_experiments = []
    
    for exp_name, result in results:
        if result['status'] == 'completed':
            print(f"\n   Analyzing {exp_name}...")
            
            # Load experiment data
            exp_data = analyzer.load_experiment_data(result['output_dir'])
            
            # Calculate movement metrics
            metrics = analyzer.calculate_movement_metrics(result['output_dir'])
            
            analysis_results[exp_name] = {
                'data': exp_data,
                'metrics': metrics,
                'result': result
            }
            
            successful_experiments.append(exp_name)
            
            # Print key metrics
            print(f"     First move day (avg): {metrics['first_move_day']['mean']:.1f}")
            print(f"     Total distance (avg): {metrics['total_distance']['mean']:.1f} km")
            print(f"     Destination entropy: {metrics['destination_distribution']['entropy']:.2f}")
    
    # Step 8: Compare Results
    if len(successful_experiments) >= 2:
        print(f"\n7. Comparing results across {len(successful_experiments)} experiments...")
        
        # Create comparison table
        print("\n   Comparison Summary:")
        print("   " + "="*70)
        print(f"   {'Metric':<25} {'System 1':<12} {'System 2':<12} {'Dual Process':<12}")
        print("   " + "-"*70)
        
        metrics_to_compare = [
            ('First Move Day', 'first_move_day', 'mean'),
            ('Total Distance (km)', 'total_distance', 'mean'),
            ('Movement Duration', 'movement_duration', 'mean'),
            ('Destination Entropy', 'destination_distribution', 'entropy')
        ]
        
        for metric_name, metric_key, stat_key in metrics_to_compare:
            row = f"   {metric_name:<25}"
            
            for exp_name in ['System_1', 'System_2', 'Dual_Process']:
                if exp_name in analysis_results:
                    if stat_key == 'entropy':
                        value = analysis_results[exp_name]['metrics'][metric_key][stat_key]
                    else:
                        value = analysis_results[exp_name]['metrics'][metric_key][stat_key]
                    row += f" {value:<12.1f}"
                else:
                    row += f" {'N/A':<12}"
            
            print(row)
        
        print("   " + "="*70)
    
    # Step 9: Generate Visualizations
    print("\n8. Generating visualizations...")
    
    if len(successful_experiments) >= 2:
        viz_gen = VisualizationGenerator(
            results_directory=str(output_base / 'results'),
            output_directory=str(output_base / 'visualizations')
        )
        
        # Prepare comparison data
        comparison_data = {}
        for exp_name in successful_experiments:
            comparison_data[exp_name] = analysis_results[exp_name]['data']
        
        try:
            # Create movement timing comparison
            timing_plot = viz_gen.create_movement_timing_comparison(
                comparison_data,
                title="Movement Timing Comparison: Dual Process Experiment",
                output_file=str(output_base / 'visualizations' / 'movement_timing.png')
            )
            print(f"   ✓ Movement timing plot: {timing_plot}")
            
            # Create destination distribution comparison
            dest_plot = viz_gen.create_destination_distribution_plot(
                comparison_data,
                title="Destination Distribution: Dual Process Experiment",
                output_file=str(output_base / 'visualizations' / 'destinations.png')
            )
            print(f"   ✓ Destination distribution plot: {dest_plot}")
            
            # Create cognitive state evolution plot (if dual process data available)
            if 'Dual_Process' in comparison_data:
                cognitive_plot = viz_gen.create_cognitive_state_evolution_plot(
                    comparison_data['Dual_Process'],
                    title="Cognitive State Evolution: Dual Process Mode",
                    output_file=str(output_base / 'visualizations' / 'cognitive_states.png')
                )
                print(f"   ✓ Cognitive state plot: {cognitive_plot}")
            
        except Exception as e:
            print(f"   ⚠ Visualization generation failed: {e}")
            print("   (This may be due to missing optional packages like plotly)")
    
    # Step 10: Generate Summary Report
    print("\n9. Generating summary report...")
    
    report_file = output_base / 'experiment_report.txt'
    
    with open(report_file, 'w') as f:
        f.write("Basic Dual Process Experiment Report\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Experiment Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Execution Time: {total_time:.1f} seconds\n\n")
        
        f.write("Experimental Setup:\n")
        f.write(f"- Topology: Linear chain with 5 locations\n")
        f.write(f"- Scenario: Spike conflict (intensity 0.85)\n")
        f.write(f"- Simulation Duration: 80 days\n")
        f.write(f"- Cognitive Modes Tested: {len(experiments)}\n\n")
        
        f.write("Results Summary:\n")
        f.write("-" * 20 + "\n")
        
        for exp_name, result in results:
            f.write(f"\n{exp_name}:\n")
            if result['status'] == 'completed':
                f.write(f"  Status: Completed successfully\n")
                f.write(f"  Execution Time: {result['execution_time']:.1f} seconds\n")
                
                if exp_name in analysis_results:
                    metrics = analysis_results[exp_name]['metrics']
                    f.write(f"  First Move Day: {metrics['first_move_day']['mean']:.1f}\n")
                    f.write(f"  Total Distance: {metrics['total_distance']['mean']:.1f} km\n")
                    f.write(f"  Destination Entropy: {metrics['destination_distribution']['entropy']:.2f}\n")
            else:
                f.write(f"  Status: Failed\n")
                f.write(f"  Error: {result.get('error', 'Unknown error')}\n")
        
        f.write(f"\nOutput Files:\n")
        f.write(f"- Topology: {locations_file}\n")
        f.write(f"- Scenario: {conflicts_file}\n")
        f.write(f"- Results: {output_base / 'results'}\n")
        f.write(f"- Visualizations: {output_base / 'visualizations'}\n")
    
    print(f"   ✓ Report saved: {report_file}")
    
    # Final Summary
    print(f"\n{'='*50}")
    print("EXPERIMENT COMPLETED")
    print(f"{'='*50}")
    
    successful_count = len([r for _, r in results if r['status'] == 'completed'])
    print(f"Successful experiments: {successful_count}/{len(experiments)}")
    print(f"Total execution time: {total_time:.1f} seconds")
    print(f"Output directory: {output_base}")
    
    if successful_count >= 2:
        print("\nKey Findings:")
        
        # Simple comparison of first move days
        if 'System_1' in analysis_results and 'System_2' in analysis_results:
            s1_first_move = analysis_results['System_1']['metrics']['first_move_day']['mean']
            s2_first_move = analysis_results['System_2']['metrics']['first_move_day']['mean']
            
            if s1_first_move < s2_first_move:
                print(f"- System 1 responds faster (day {s1_first_move:.1f} vs {s2_first_move:.1f})")
            else:
                print(f"- System 2 responds faster (day {s2_first_move:.1f} vs {s1_first_move:.1f})")
        
        # Distance comparison
        if 'System_1' in analysis_results and 'System_2' in analysis_results:
            s1_distance = analysis_results['System_1']['metrics']['total_distance']['mean']
            s2_distance = analysis_results['System_2']['metrics']['total_distance']['mean']
            
            if s1_distance < s2_distance:
                print(f"- System 1 travels less distance ({s1_distance:.1f} vs {s2_distance:.1f} km)")
            else:
                print(f"- System 2 travels less distance ({s2_distance:.1f} vs {s1_distance:.1f} km)")
    
    print(f"\nFor detailed analysis, see: {report_file}")
    print("For visualizations, check the visualizations directory.")
    
    return successful_count == len(experiments)


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nExperiment failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)