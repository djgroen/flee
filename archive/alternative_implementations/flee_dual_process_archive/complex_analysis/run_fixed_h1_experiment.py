#!/usr/bin/env python3
"""
Run H1 experiment with all the connectivity and parameter fixes applied.
This should now show meaningful differences between cognitive modes.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_fixed_h1_experiment():
    """Run H1 experiment with fixed parameters."""
    print("=" * 60)
    print("RUNNING FIXED H1 EXPERIMENT")
    print("=" * 60)
    print()
    
    # Show what we fixed
    print("FIXES APPLIED:")
    print("✓ Made conflict_threshold configurable in Flee")
    print("✓ Fixed TwoSystemDecisionMaking parameter validation")
    print("✓ Increased cognitive pressure values")
    print("✓ Fixed s2_disconnected connectivity issue")
    print()
    
    # Show expected cognitive pressure values
    print("EXPECTED COGNITIVE PRESSURE:")
    modes = {
        's1_only': {'conn': 0.0, 'thresh': 0.5, 'expected': 'System 1 only'},
        's2_disconnected': {'conn': 0.1, 'thresh': 0.001, 'expected': 'Always System 2, no social info'},
        's2_full': {'conn': 15.0, 'thresh': 0.3, 'expected': 'Always System 2, high social connectivity'},
        'dual_process': {'conn': 8.0, 'thresh': 0.4, 'expected': 'Dynamic System 2 activation'}
    }
    
    conflict_intensity = 1.0
    recovery_period = 10
    
    for mode, params in modes.items():
        pressure = (conflict_intensity * params['conn']) / recovery_period
        activated = pressure > params['thresh']
        print(f"  {mode}: pressure={pressure:.3f} > {params['thresh']} = {activated} ({params['expected']})")
    print()
    
    try:
        # Import the hypothesis testing pipeline
        from run_hypothesis_scenarios import HypothesisTestingPipeline
        
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"h1_fixed_results_{timestamp}"
        
        print(f"Output directory: {output_dir}")
        print()
        
        # Initialize pipeline with focused settings for H1
        print("Initializing H1 testing pipeline...")
        pipeline = HypothesisTestingPipeline(
            output_dir=output_dir,
            max_parallel=2,  # Use 2 parallel processes
            replications=3   # 3 replications for statistical validity
        )
        
        print("✓ Pipeline initialized")
        print()
        
        # Run H1.1 Multi-Destination scenario
        print("Running H1.1 Multi-Destination Choice scenario...")
        print("This tests speed vs optimality trade-offs with multiple camp options")
        print()
        
        start_time = time.time()
        
        # Run only H1.1 for focused testing
        results = pipeline.run_all_hypotheses(['H1.1'])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✓ H1.1 completed in {execution_time:.1f} seconds")
        print()
        
        # Analyze results
        if 'H1.1' in results['raw_results']:
            h1_results = results['raw_results']['H1.1']
            
            if 'error' in h1_results:
                print(f"✗ H1.1 FAILED: {h1_results['error']}")
                return False
            
            print("=" * 40)
            print("H1.1 RESULTS ANALYSIS")
            print("=" * 40)
            
            # Check aggregated results
            aggregated = h1_results.get('aggregated_results', {})
            
            if not aggregated:
                print("✗ No aggregated results found")
                return False
            
            print(f"Cognitive modes tested: {list(aggregated.keys())}")
            print()
            
            # Analyze each cognitive mode
            mode_metrics = {}
            for mode, mode_results in aggregated.items():
                n_experiments = mode_results.get('n_experiments', 0)
                success_rate = mode_results.get('success_rate', 0)
                metrics = mode_results.get('metrics', {})
                
                print(f"{mode.upper()}:")
                print(f"  Experiments: {n_experiments}")
                print(f"  Success rate: {success_rate:.1%}")
                
                if metrics:
                    # Look for key metrics
                    for metric_name, values in metrics.items():
                        if values:
                            avg_value = sum(values) / len(values)
                            mode_metrics[mode] = mode_metrics.get(mode, {})
                            mode_metrics[mode][metric_name] = avg_value
                            print(f"  {metric_name}: {avg_value:.3f}")
                
                print()
            
            # Compare modes to see if we have meaningful differences
            print("=" * 40)
            print("COGNITIVE MODE COMPARISON")
            print("=" * 40)
            
            if len(mode_metrics) >= 2:
                # Check if we have different results
                modes_list = list(mode_metrics.keys())
                differences_found = False
                
                for i, mode1 in enumerate(modes_list):
                    for mode2 in modes_list[i+1:]:
                        print(f"\n{mode1} vs {mode2}:")
                        
                        mode1_metrics = mode_metrics[mode1]
                        mode2_metrics = mode_metrics[mode2]
                        
                        common_metrics = set(mode1_metrics.keys()) & set(mode2_metrics.keys())
                        
                        for metric in common_metrics:
                            val1 = mode1_metrics[metric]
                            val2 = mode2_metrics[metric]
                            diff = abs(val1 - val2)
                            
                            if diff > 0.001:  # Meaningful difference threshold
                                differences_found = True
                                percent_diff = (diff / max(val1, val2)) * 100
                                print(f"  {metric}: {val1:.3f} vs {val2:.3f} (diff: {percent_diff:.1f}%)")
                
                if differences_found:
                    print("\n✓ MEANINGFUL DIFFERENCES FOUND!")
                    print("The cognitive mode fixes are working correctly.")
                else:
                    print("\n✗ No meaningful differences found")
                    print("Results are still too similar - may need further parameter tuning")
            
            # Save detailed results
            results_file = os.path.join(output_dir, 'h1_analysis_summary.json')
            summary = {
                'timestamp': timestamp,
                'execution_time': execution_time,
                'cognitive_modes': list(aggregated.keys()),
                'mode_metrics': mode_metrics,
                'fixes_applied': [
                    'Made conflict_threshold configurable',
                    'Fixed TwoSystemDecisionMaking validation',
                    'Increased cognitive pressure values',
                    'Fixed s2_disconnected connectivity'
                ]
            }
            
            with open(results_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"\n✓ Detailed results saved to: {results_file}")
            
            return True
        
        else:
            print("✗ No H1.1 results found in pipeline output")
            return False
    
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Cannot run full H1 experiment")
        return False
    
    except Exception as e:
        print(f"✗ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the fixed H1 experiment."""
    success = run_fixed_h1_experiment()
    
    print()
    print("=" * 60)
    if success:
        print("H1 EXPERIMENT COMPLETED SUCCESSFULLY")
        print("Check the results above to see if cognitive modes show differences")
    else:
        print("H1 EXPERIMENT FAILED")
        print("Check the error messages above for debugging")
    print("=" * 60)

if __name__ == "__main__":
    main()