#!/usr/bin/env python3
"""
Example script demonstrating parameter sweep generation.

This script shows how to use the ConfigurationManager to generate
parameter sweeps for dual-process experiments.
"""

import os
import sys
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigurationManager


def main():
    """Demonstrate parameter sweep generation."""
    print("Dual Process Configuration Manager - Parameter Sweep Example")
    print("=" * 60)
    
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    
    # Example 1: Single parameter sweep
    print("\n1. Single Parameter Sweep - Awareness Level")
    print("-" * 40)
    
    base_config = config_manager.create_cognitive_config('dual_process')
    parameter = 'move_rules.awareness_level'
    values = [1, 2, 3]
    
    sweep_configs = config_manager.generate_parameter_sweep(base_config, parameter, values)
    
    print(f"Generated {len(sweep_configs)} configurations")
    for i, config in enumerate(sweep_configs):
        awareness = config['move_rules']['awareness_level']
        print(f"  Config {i+1}: awareness_level = {awareness}")
    
    # Example 2: Factorial design
    print("\n2. Factorial Design - Awareness x Social Connectivity")
    print("-" * 50)
    
    factors = {
        'move_rules.awareness_level': [1, 3],
        'move_rules.average_social_connectivity': [0.0, 8.0]
    }
    
    factorial_configs = config_manager.generate_factorial_design(base_config, factors)
    
    print(f"Generated {len(factorial_configs)} configurations")
    for i, config in enumerate(factorial_configs):
        awareness = config['move_rules']['awareness_level']
        connectivity = config['move_rules']['average_social_connectivity']
        print(f"  Config {i+1}: awareness={awareness}, connectivity={connectivity}")
    
    # Example 3: Cognitive mode sweep
    print("\n3. Cognitive Mode Sweep")
    print("-" * 25)
    
    mode_configs = config_manager.generate_cognitive_mode_sweep()
    
    print(f"Generated {len(mode_configs)} configurations")
    for i, config in enumerate(mode_configs):
        two_system = config['move_rules']['two_system_decision_making']
        awareness = config['move_rules']['awareness_level']
        connectivity = config['move_rules']['average_social_connectivity']
        
        if not two_system:
            mode_name = "S1-only"
        elif connectivity == 0.0:
            mode_name = "S2-disconnected"
        elif connectivity >= 8.0:
            mode_name = "S2-full"
        else:
            mode_name = "Dual-process"
        
        print(f"  Config {i+1}: {mode_name} (awareness={awareness}, connectivity={connectivity})")
    
    # Example 4: Validation summary
    print("\n4. Configuration Validation")
    print("-" * 30)
    
    all_configs = sweep_configs + factorial_configs + mode_configs
    summary = config_manager.validate_parameter_sweep(all_configs)
    
    print(f"Total configurations: {summary['total_configurations']}")
    print(f"Valid configurations: {summary['valid_configurations']}")
    print(f"Invalid configurations: {summary['invalid_configurations']}")
    print(f"Validation rate: {summary['validation_rate']:.2%}")
    
    # Example 5: Save configurations
    print("\n5. Saving Configurations")
    print("-" * 25)
    
    output_dir = "example_sweep_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save single parameter sweep
    sweep_files = config_manager.save_parameter_sweep(
        sweep_configs, 
        os.path.join(output_dir, "awareness_sweep"), 
        "awareness_config"
    )
    print(f"Saved awareness sweep: {len(sweep_files)} files")
    
    # Save factorial design
    factorial_files = config_manager.save_parameter_sweep(
        factorial_configs,
        os.path.join(output_dir, "factorial_design"),
        "factorial_config"
    )
    print(f"Saved factorial design: {len(factorial_files)} files")
    
    # Save cognitive mode sweep
    mode_files = config_manager.save_parameter_sweep(
        mode_configs,
        os.path.join(output_dir, "cognitive_modes"),
        "mode_config"
    )
    print(f"Saved cognitive modes: {len(mode_files)} files")
    
    print(f"\nAll configurations saved to: {output_dir}/")
    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()