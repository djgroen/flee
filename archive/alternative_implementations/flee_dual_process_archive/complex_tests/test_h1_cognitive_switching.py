#!/usr/bin/env python3
"""
Test H1 Cognitive Switching

This script tests whether the cognitive switching is working properly for H1 scenarios.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigurationManager
from experiment_runner import ExperimentRunner, ExperimentConfig


def test_cognitive_mode_configs():
    """Test that cognitive mode configurations are different."""
    print("Testing Cognitive Mode Configurations")
    print("=" * 50)
    
    config_mgr = ConfigurationManager({})
    
    for mode_name, mode_config in config_mgr.COGNITIVE_MODES.items():
        print(f"\n{mode_name}:")
        move_rules = mode_config['move_rules']
        
        print(f"  TwoSystemDecisionMaking: {move_rules.get('TwoSystemDecisionMaking', 'NOT SET')}")
        print(f"  average_social_connectivity: {move_rules.get('average_social_connectivity', 'NOT SET')}")
        print(f"  awareness_level: {move_rules.get('awareness_level', 'NOT SET')}")
        print(f"  weight_softening: {move_rules.get('weight_softening', 'NOT SET')}")
        print(f"  conflict_threshold: {move_rules.get('conflict_threshold', 'NOT SET')}")
        print(f"  default_movechance: {move_rules.get('default_movechance', 'NOT SET')}")
        print(f"  conflict_movechance: {move_rules.get('conflict_movechance', 'NOT SET')}")


def test_h1_scenario_config():
    """Test H1 scenario configuration."""
    print("\n\nTesting H1 Scenario Configuration")
    print("=" * 50)
    
    # Import the hypothesis configs
    from run_hypothesis_scenarios import HypothesisTestingPipeline
    
    pipeline = HypothesisTestingPipeline("test_output", max_parallel=1, replications=1)
    
    h1_config = pipeline.hypothesis_configs.get('H1.1')
    if h1_config:
        print("H1.1 Configuration:")
        print(f"  Name: {h1_config['name']}")
        print(f"  Topology: {h1_config['topology_type']}")
        print(f"  Cognitive modes: {h1_config['cognitive_modes']}")
        print(f"  Scenario type: {h1_config['scenario_type']}")
        
        topo_params = h1_config['topology_params']
        print(f"  Distances: {topo_params.get('distances', 'NOT SET')}")
        print(f"  Capacities: {topo_params.get('capacities', 'NOT SET')}")
        print(f"  Safety levels: {topo_params.get('safety_levels', 'NOT SET')}")
        
        scenario_params = h1_config['scenario_params']
        print(f"  Start day: {scenario_params.get('start_day', 'NOT SET')}")
        print(f"  Peak intensity: {scenario_params.get('peak_intensity', 'NOT SET')}")
        print(f"  Duration: {scenario_params.get('duration', 'NOT SET')}")
    else:
        print("ERROR: H1.1 configuration not found!")


def create_minimal_h1_test():
    """Create a minimal H1 test to verify cognitive switching."""
    print("\n\nCreating Minimal H1 Test")
    print("=" * 50)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Test directory: {temp_dir}")
    
    try:
        # Create minimal experiment configs for each cognitive mode
        config_mgr = ConfigurationManager({})
        
        for mode in ['s1_only', 's2_full', 'dual_process']:
            print(f"\nTesting {mode} mode...")
            
            # Create experiment config
            exp_config = ExperimentConfig(
                experiment_id=f"h1_test_{mode}",
                topology_type='custom',
                topology_params={
                    'network_type': 'origin_hub_camps',
                    'n_camps': 3,
                    'distances': [30, 60, 120],
                    'capacities': [500, 1500, 3000],
                    'safety_levels': [0.6, 0.8, 0.95]
                },
                scenario_type='escalating_conflict',
                scenario_params={
                    'origin': 'Origin',
                    'start_day': 5,
                    'escalation_days': [10, 25],
                    'peak_intensity': 0.95,
                    'duration': 50  # Short test
                },
                cognitive_mode=mode,
                simulation_params={
                    'max_agents': 1000,  # Small test
                    'print_progress': True
                },
                replications=1,
                metadata={'test': True}
            )
            
            # Create simsetting.yml for this mode
            mode_config = config_mgr.create_cognitive_config(mode, {})
            output_path = os.path.join(temp_dir, f"simsetting_{mode}.yml")
            config_mgr.create_simsetting_yml(mode_config, output_path)
            
            print(f"  Created config: {output_path}")
            
            # Check key differences in the config
            with open(output_path, 'r') as f:
                content = f.read()
                if 'TwoSystemDecisionMaking: true' in content:
                    print(f"  ✓ {mode} has TwoSystemDecisionMaking enabled")
                elif 'TwoSystemDecisionMaking: false' in content:
                    print(f"  ✓ {mode} has TwoSystemDecisionMaking disabled")
                else:
                    print(f"  ✗ {mode} TwoSystemDecisionMaking setting not found!")
                
                if 'average_social_connectivity:' in content:
                    import re
                    match = re.search(r'average_social_connectivity:\s*([0-9.]+)', content)
                    if match:
                        connectivity = float(match.group(1))
                        print(f"  ✓ {mode} social connectivity: {connectivity}")
                    else:
                        print(f"  ✗ {mode} social connectivity value not found!")
                
                if 'conflict_threshold:' in content:
                    import re
                    match = re.search(r'conflict_threshold:\s*([0-9.]+)', content)
                    if match:
                        threshold = float(match.group(1))
                        print(f"  ✓ {mode} conflict threshold: {threshold}")
                
                if 'default_movechance:' in content:
                    import re
                    match = re.search(r'default_movechance:\s*([0-9.]+)', content)
                    if match:
                        movechance = float(match.group(1))
                        print(f"  ✓ {mode} default movechance: {movechance}")
        
        print(f"\n✓ Test configurations created successfully!")
        print(f"Check the configs in: {temp_dir}")
        
        # Don't clean up so user can inspect
        print(f"\nTo inspect configs manually:")
        print(f"ls -la {temp_dir}")
        print(f"cat {temp_dir}/simsetting_*.yml")
        
        return temp_dir
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        shutil.rmtree(temp_dir)
        return None


def main():
    """Main test function."""
    print("🧠 Testing H1 Cognitive Switching Configuration")
    print("=" * 60)
    
    # Test 1: Check cognitive mode configurations
    test_cognitive_mode_configs()
    
    # Test 2: Check H1 scenario configuration
    test_h1_scenario_config()
    
    # Test 3: Create minimal test
    test_dir = create_minimal_h1_test()
    
    print("\n" + "=" * 60)
    print("🎯 Diagnosis Summary:")
    print("1. Check that TwoSystemDecisionMaking is properly set for each mode")
    print("2. Verify that social connectivity differs between modes")
    print("3. Confirm that movechance parameters create speed differences")
    print("4. Ensure conflict thresholds create different switching behaviors")
    
    if test_dir:
        print(f"\n📁 Test configs saved to: {test_dir}")
        print("You can manually inspect these to verify the differences")
    
    print("\n🔧 Next steps:")
    print("1. Run a quick test with these configs")
    print("2. Check the Flee logs for 'System 2 activated' messages")
    print("3. Compare movement timing between s1_only and s2_full modes")


if __name__ == "__main__":
    main()