#!/usr/bin/env python3
"""
Quick Validation of Topology-S1/S2 Experiments

This script performs a quick validation to ensure the experimental framework
is working correctly before running the full staged experiments.
"""

import sys
import os
import numpy as np
import time

# Add current directory to path
sys.path.insert(0, '.')

def validate_imports():
    """Validate that all required modules can be imported."""
    
    print("🔍 Validating imports...")
    
    try:
        import matplotlib.pyplot as plt
        print("  ✅ matplotlib")
    except ImportError as e:
        print(f"  ❌ matplotlib: {e}")
        return False
    
    try:
        import pandas as pd
        print("  ✅ pandas")
    except ImportError as e:
        print(f"  ❌ pandas: {e}")
        return False
    
    try:
        import seaborn as sns
        print("  ✅ seaborn")
    except ImportError as e:
        print(f"  ❌ seaborn: {e}")
        return False
    
    try:
        import networkx as nx
        print("  ✅ networkx")
    except ImportError as e:
        print(f"  ❌ networkx: {e}")
        return False
    
    try:
        from scipy import stats
        print("  ✅ scipy")
    except ImportError as e:
        print(f"  ❌ scipy: {e}")
        return False
    
    try:
        import yaml
        print("  ✅ yaml")
    except ImportError as e:
        print(f"  ❌ yaml: {e}")
        return False
    
    try:
        from flee import flee
        print("  ✅ flee")
    except ImportError as e:
        print(f"  ❌ flee: {e}")
        return False
    
    return True

def validate_topology_creation():
    """Validate that topology creation works."""
    
    print("\n🔍 Validating topology creation...")
    
    try:
        from comprehensive_topology_s1s2_experiments import ComprehensiveTopologyExperiment
        experiment = ComprehensiveTopologyExperiment()
        
        # Test creating a simple topology
        spec = experiment.topology_specs[0]  # Get first topology spec
        print(f"  Testing topology: {spec.name}")
        
        G = experiment.create_topology_network(spec)
        print(f"  ✅ Created network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Test network metrics calculation
        metrics = experiment.calculate_network_metrics(G)
        print(f"  ✅ Calculated {len(metrics)} network metrics")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Topology creation failed: {e}")
        return False

def validate_s1s2_configs():
    """Validate that S1/S2 configurations are properly defined."""
    
    print("\n🔍 Validating S1/S2 configurations...")
    
    try:
        from comprehensive_topology_s1s2_experiments import ComprehensiveTopologyExperiment
        experiment = ComprehensiveTopologyExperiment()
        
        print(f"  Found {len(experiment.topology_specs)} topology specifications")
        print(f"  Found {len(experiment.s1s2_configs)} S1/S2 configurations")
        
        # Test each S1/S2 config
        for config in experiment.s1s2_configs:
            print(f"  ✅ {config.name}: {config.description}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ S1/S2 config validation failed: {e}")
        return False

def validate_single_experiment():
    """Validate that a single experiment can run."""
    
    print("\n🔍 Validating single experiment...")
    
    try:
        from comprehensive_topology_s1s2_experiments import ComprehensiveTopologyExperiment
        experiment = ComprehensiveTopologyExperiment()
        
        # Use minimal parameters for quick test
        spec = experiment.topology_specs[0]  # First topology
        s1s2_config = experiment.s1s2_configs[0]  # First config
        
        print(f"  Testing: {spec.name} + {s1s2_config.name}")
        
        # Create output directory
        output_dir = "temp_validation"
        os.makedirs(output_dir, exist_ok=True)
        
        # Run single experiment with minimal parameters
        start_time = time.time()
        result = experiment.run_single_experiment(
            spec=spec,
            s1s2_config=s1s2_config,
            replicate_id=0,
            output_dir=output_dir
        )
        end_time = time.time()
        
        if result is not None:
            print(f"  ✅ Experiment completed in {end_time - start_time:.1f} seconds")
            print(f"  ✅ Collected {len(result['timesteps'])} timesteps of data")
            print(f"  ✅ Final evacuation rate: {result['evacuation_rates'][-1]:.3f}")
            print(f"  ✅ Final S2 activation rate: {result['s2_activation_rates'][-1]:.3f}")
            
            # Don't clean up for debugging
            # import shutil
            # shutil.rmtree(output_dir, ignore_errors=True)
            
            return True
        else:
            print("  ❌ Experiment returned None")
            return False
            
    except Exception as e:
        print(f"  ❌ Single experiment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_staged_runner():
    """Validate that the staged runner works."""
    
    print("\n🔍 Validating staged runner...")
    
    try:
        from run_staged_topology_experiments import StagedTopologyExperimentRunner
        runner = StagedTopologyExperimentRunner()
        
        print(f"  ✅ Created staged runner with {len(runner.stages)} stages")
        
        # Test stage calculations
        for i, stage in enumerate(runner.stages):
            n_experiments = runner.calculate_stage_experiments(i)
            print(f"  ✅ Stage {i+1}: {n_experiments} experiments")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Staged runner validation failed: {e}")
        return False

def main():
    """Main validation function."""
    
    print("🔍 TOPOLOGY EXPERIMENT VALIDATION")
    print("=" * 60)
    print("This validates that the experimental framework is working correctly.")
    print()
    
    validation_results = []
    
    # Run all validations
    validation_results.append(("Imports", validate_imports()))
    validation_results.append(("Topology Creation", validate_topology_creation()))
    validation_results.append(("S1/S2 Configs", validate_s1s2_configs()))
    validation_results.append(("Staged Runner", validate_staged_runner()))
    validation_results.append(("Single Experiment", validate_single_experiment()))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in validation_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ The experimental framework is ready to run.")
        print("\n🚀 Next steps:")
        print("1. Run staged experiments: python run_staged_topology_experiments.py")
        print("2. Start with Stage 1 validation")
        print("3. Proceed through stages as results look good")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("🔧 Please fix the issues before running experiments.")
    
    print("="*60)

if __name__ == "__main__":
    main()
