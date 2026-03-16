#!/usr/bin/env python3
"""
Quick test to verify H1 parameter fixes work
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config_manager import ConfigurationManager
    from experiment_runner import ExperimentRunner, ExperimentConfig
    
    def test_cognitive_mode_configs():
        """Test that cognitive mode configurations are valid and different."""
        print("=== TESTING COGNITIVE MODE CONFIGURATIONS ===\n")
        
        config_manager = ConfigurationManager()
        
        modes = ['s1_only', 's2_full', 'dual_process']
        configs = {}
        
        for mode in modes:
            try:
                config = config_manager.create_cognitive_config(mode)
                configs[mode] = config
                
                # Validate configuration
                is_valid = config_manager.validate_configuration(config)
                print(f"Mode {mode}: {'✓ VALID' if is_valid else '✗ INVALID'}")
                
                # Show key parameters
                move_rules = config.get('move_rules', {})
                two_system = move_rules.get('TwoSystemDecisionMaking', 'NOT SET')
                connectivity = move_rules.get('average_social_connectivity', 'NOT SET')
                threshold = move_rules.get('conflict_threshold', 'NOT SET')
                
                print(f"  TwoSystemDecisionMaking: {two_system}")
                print(f"  Social Connectivity: {connectivity}")
                print(f"  Conflict Threshold: {threshold}")
                print()
                
            except Exception as e:
                print(f"Mode {mode}: ✗ ERROR - {e}")
                print()
        
        # Check for meaningful differences
        if len(configs) >= 2:
            print("=== PARAMETER DIFFERENCES ===")
            s1_connectivity = configs['s1_only']['move_rules'].get('average_social_connectivity', 0)
            s2_connectivity = configs['s2_full']['move_rules'].get('average_social_connectivity', 0)
            dual_connectivity = configs['dual_process']['move_rules'].get('average_social_connectivity', 0)
            
            print(f"Connectivity differences:")
            print(f"  s1_only: {s1_connectivity}")
            print(f"  s2_full: {s2_connectivity}")
            print(f"  dual_process: {dual_connectivity}")
            
            if s1_connectivity != s2_connectivity or s2_connectivity != dual_connectivity:
                print("✓ Meaningful connectivity differences found")
            else:
                print("✗ No connectivity differences - results will be identical")
            print()
    
    def test_simple_experiment():
        """Test running a very simple experiment with different cognitive modes."""
        print("=== TESTING SIMPLE EXPERIMENT ===\n")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="h1_test_")
        print(f"Using temp directory: {temp_dir}")
        
        try:
            # Create simple experiment configs
            base_config = ExperimentConfig(
                experiment_id="test_s1",
                topology_type="linear",
                topology_params={"n_nodes": 3, "segment_distance": 50.0, "start_pop": 1000},
                scenario_type="spike",
                scenario_params={"origin": "Town_A", "start_day": 0, "peak_intensity": 1.0},
                cognitive_mode="s1_only",
                simulation_params={"max_days": 10, "print_progress": False},
                replications=1
            )
            
            s2_config = ExperimentConfig(
                experiment_id="test_s2",
                topology_type="linear", 
                topology_params={"n_nodes": 3, "segment_distance": 50.0, "start_pop": 1000},
                scenario_type="spike",
                scenario_params={"origin": "Town_A", "start_day": 0, "peak_intensity": 1.0},
                cognitive_mode="s2_full",
                simulation_params={"max_days": 10, "print_progress": False},
                replications=1
            )
            
            # Run experiments
            runner = ExperimentRunner(max_parallel=1, base_output_dir=temp_dir)
            
            print("Running S1 experiment...")
            s1_result = runner.run_single_experiment(base_config)
            print(f"S1 result: {'✓ SUCCESS' if s1_result.get('success') else '✗ FAILED'}")
            
            print("Running S2 experiment...")
            s2_result = runner.run_single_experiment(s2_config)
            print(f"S2 result: {'✓ SUCCESS' if s2_result.get('success') else '✗ FAILED'}")
            
            # Compare results if both succeeded
            if s1_result.get('success') and s2_result.get('success'):
                print("\n=== COMPARING RESULTS ===")
                
                s1_metrics = s1_result.get('metrics', {})
                s2_metrics = s2_result.get('metrics', {})
                
                print(f"S1 execution time: {s1_metrics.get('execution_time', 'N/A')}")
                print(f"S2 execution time: {s2_metrics.get('execution_time', 'N/A')}")
                
                # Check if results are different
                if s1_metrics != s2_metrics:
                    print("✓ Results are different between cognitive modes")
                else:
                    print("✗ Results are identical - cognitive modes not working")
            
        except Exception as e:
            print(f"✗ Experiment failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temp directory: {temp_dir}")
            except:
                pass
    
    def main():
        print("H1 PARAMETER FIX VERIFICATION")
        print("=" * 50)
        print()
        
        test_cognitive_mode_configs()
        test_simple_experiment()
        
        print("=" * 50)
        print("TEST COMPLETE")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Cannot run experiment tests without proper imports")