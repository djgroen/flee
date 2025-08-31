#!/usr/bin/env python3
"""
Quick H1 test with fixed parameters
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_quick_h1_test():
    """Run a quick H1 test with the fixed parameters."""
    print("=== QUICK H1 TEST WITH FIXES ===\n")
    
    try:
        from run_hypothesis_scenarios import HypothesisTestingPipeline
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="h1_quick_test_")
        print(f"Using temp directory: {temp_dir}")
        
        # Initialize pipeline with minimal settings
        pipeline = HypothesisTestingPipeline(
            output_dir=temp_dir,
            max_parallel=1,
            replications=1  # Just 1 replication for quick test
        )
        
        # Run only H1.1 scenario
        print("Running H1.1 Multi-Destination scenario...")
        results = pipeline.run_all_hypotheses(['H1.1'])
        
        # Check results
        if 'H1.1' in results['raw_results']:
            h1_results = results['raw_results']['H1.1']
            
            if 'error' in h1_results:
                print(f"✗ H1.1 failed: {h1_results['error']}")
            else:
                print("✓ H1.1 completed successfully!")
                
                # Check aggregated results
                aggregated = h1_results.get('aggregated_results', {})
                print(f"\nCognitive modes tested: {list(aggregated.keys())}")
                
                # Show some metrics if available
                for mode, mode_results in aggregated.items():
                    metrics = mode_results.get('metrics', {})
                    n_experiments = mode_results.get('n_experiments', 0)
                    success_rate = mode_results.get('success_rate', 0)
                    
                    print(f"\n{mode}:")
                    print(f"  Experiments: {n_experiments}")
                    print(f"  Success rate: {success_rate:.1%}")
                    
                    if metrics:
                        print(f"  Metrics available: {list(metrics.keys())}")
        else:
            print("✗ No H1.1 results found")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Cannot run full test - checking configuration only")
        
        # Just test configuration
        try:
            from config_manager import ConfigurationManager
            
            config_manager = ConfigurationManager()
            
            print("Testing cognitive mode configurations...")
            for mode in ['s1_only', 's2_disconnected', 's2_full', 'dual_process']:
                try:
                    config = config_manager.create_cognitive_config(mode)
                    is_valid = config_manager.validate_configuration(config)
                    print(f"  {mode}: {'✓ VALID' if is_valid else '✗ INVALID'}")
                except Exception as e:
                    print(f"  {mode}: ✗ ERROR - {e}")
        
        except ImportError:
            print("Cannot test configurations either")
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)
                print(f"\nCleaned up temp directory: {temp_dir}")
        except:
            pass

if __name__ == "__main__":
    run_quick_h1_test()