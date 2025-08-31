#!/usr/bin/env python3
"""
Debug H1 Parameter Values and Cognitive Switching

This script checks if the H1 scenario parameters are creating meaningful
differences between cognitive modes and if cognitive switching is working.
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config_manager import ConfigurationManager
    from topology_generator import TopologyGenerator
    from scenario_generator import SpikeConflictGenerator
    from experiment_runner import ExperimentRunner
except ImportError as e:
    print(f"Import error: {e}")
    print("Running basic parameter analysis only...")
    ConfigurationManager = None

def check_cognitive_mode_differences():
    """Check if cognitive modes have meaningful parameter differences."""
    print("=== COGNITIVE MODE PARAMETER ANALYSIS ===\n")
    
    if ConfigurationManager is None:
        print("ConfigurationManager not available - showing hardcoded values")
        
        # Hardcoded cognitive mode parameters from config_manager.py
        modes_config = {
            's1_only': {
                'TwoSystemDecisionMaking': False,
                'awareness_level': 1,
                'weight_softening': 0.8,
                'average_social_connectivity': 0.0,
                'default_movechance': 0.5,
                'conflict_movechance': 1.0,
            },
            's2_disconnected': {
                'TwoSystemDecisionMaking': True,
                'average_social_connectivity': 0.0,
                'awareness_level': 3,
                'weight_softening': 0.1,
                'default_movechance': 0.2,
                'conflict_movechance': 0.8,
                'conflict_threshold': 0.01,
            },
            's2_full': {
                'TwoSystemDecisionMaking': True,
                'average_social_connectivity': 8.0,
                'awareness_level': 3,
                'weight_softening': 0.1,
                'default_movechance': 0.2,
                'conflict_movechance': 0.8,
                'conflict_threshold': 0.1,
            },
            'dual_process': {
                'TwoSystemDecisionMaking': True,
                'average_social_connectivity': 5.0,
                'awareness_level': 2,
                'weight_softening': 0.4,
                'default_movechance': 0.3,
                'conflict_movechance': 0.9,
                'conflict_threshold': 0.05,
            }
        }
        
        for mode, move_rules in modes_config.items():
            print(f"Mode: {mode}")
            for param, value in move_rules.items():
                print(f"  {param}: {value}")
            print()
        return
    
    config_manager = ConfigurationManager()
    
    modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
    
    for mode in modes:
        print(f"Mode: {mode}")
        config = config_manager.create_cognitive_config(mode)
        move_rules = config.get('move_rules', {})
        
        key_params = [
            'TwoSystemDecisionMaking',
            'awareness_level', 
            'average_social_connectivity',
            'weight_softening',
            'default_movechance',
            'conflict_movechance'
        ]
        
        for param in key_params:
            value = move_rules.get(param, 'NOT SET')
            print(f"  {param}: {value}")
        print()

def check_h1_scenario_parameters():
    """Check H1 scenario parameter magnitudes."""
    print("=== H1 SCENARIO PARAMETER ANALYSIS ===\n")
    
    # H1.1 Multi-destination parameters
    h1_1_params = {
        'distances': [30, 60, 120],  # km
        'capacities': [500, 1500, 3000],  # people
        'safety_levels': [0.6, 0.8, 0.95],  # 0-1 scale
        'peak_intensity': 0.95,  # 0-1 scale
        'duration': 100  # days
    }
    
    print("H1.1 Multi-Destination Parameters:")
    for param, value in h1_1_params.items():
        print(f"  {param}: {value}")
    
    # Calculate some derived metrics
    distance_ratio = max(h1_1_params['distances']) / min(h1_1_params['distances'])
    capacity_ratio = max(h1_1_params['capacities']) / min(h1_1_params['capacities'])
    safety_range = max(h1_1_params['safety_levels']) - min(h1_1_params['safety_levels'])
    
    print(f"\nDerived Metrics:")
    print(f"  Distance ratio (max/min): {distance_ratio:.1f}x")
    print(f"  Capacity ratio (max/min): {capacity_ratio:.1f}x") 
    print(f"  Safety range: {safety_range:.2f}")
    print()

def check_cognitive_pressure_calculation():
    """Check cognitive pressure calculation with H1 parameters."""
    print("=== COGNITIVE PRESSURE ANALYSIS ===\n")
    
    # Parameters from different cognitive modes (UPDATED)
    mode_params = {
        's1_only': {'connectivity': 0.0, 'conflict_threshold': 0.5},
        's2_disconnected': {'connectivity': 0.0, 'conflict_threshold': 0.01},
        's2_full': {'connectivity': 8.0, 'conflict_threshold': 0.1},
        'dual_process': {'connectivity': 5.0, 'conflict_threshold': 0.05}
    }
    
    # H1 scenario parameters (UPDATED)
    conflict_intensity = 1.0  # Maximum intensity
    recovery_period = 15  # Shorter recovery period
    
    print(f"Scenario: conflict_intensity={conflict_intensity}, recovery_period={recovery_period}")
    print()
    
    for mode, params in mode_params.items():
        connectivity = params['connectivity']
        threshold = params['conflict_threshold']
        
        # Calculate cognitive pressure (simplified)
        cognitive_pressure = (conflict_intensity * connectivity) / recovery_period
        
        print(f"Mode: {mode}")
        print(f"  Connectivity: {connectivity}")
        print(f"  Conflict threshold: {threshold}")
        print(f"  Cognitive pressure: {cognitive_pressure:.3f}")
        print(f"  Above threshold: {'YES' if cognitive_pressure > threshold else 'NO'}")
        print()

def check_input_file_generation():
    """Test input file generation for H1 scenario."""
    print("=== INPUT FILE GENERATION TEST ===\n")
    
    if TopologyGenerator is None:
        print("TopologyGenerator not available - skipping input file test")
        return
    
    try:
        # Create temporary directory
        temp_dir = Path("temp_h1_test")
        temp_dir.mkdir(exist_ok=True)
        
        # Generate topology
        topo_gen = TopologyGenerator()
        
        # H1.1 topology parameters
        topology_params = {
            'network_type': 'origin_hub_camps',
            'n_camps': 3,
            'distances': [30, 60, 120],
            'capacities': [500, 1500, 3000],
            'safety_levels': [0.6, 0.8, 0.95]
        }
        
        print("Generating H1.1 topology...")
        locations_file = topo_gen.generate_custom_topology(
            topology_params, str(temp_dir)
        )
        
        print(f"Generated: {locations_file}")
        
        # Check locations file content
        if os.path.exists(locations_file):
            with open(locations_file, 'r') as f:
                content = f.read()
                print("Locations file content:")
                print(content[:500] + "..." if len(content) > 500 else content)
        
        # Generate conflict scenario
        scenario_gen = SpikeConflictGenerator(locations_file)
        
        print("\nGenerating spike conflict...")
        conflicts_file = scenario_gen.generate_spike_conflict(
            origin='Origin',
            start_day=5,
            peak_intensity=0.95,
            output_dir=str(temp_dir)
        )
        
        print(f"Generated: {conflicts_file}")
        
        # Check conflicts file content
        if os.path.exists(conflicts_file):
            with open(conflicts_file, 'r') as f:
                content = f.read()
                print("Conflicts file content:")
                print(content[:300] + "..." if len(content) > 300 else content)
        
        print(f"\n✓ Input files generated successfully in {temp_dir}")
        
    except Exception as e:
        print(f"✗ Error generating input files: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all diagnostic checks."""
    print("H1 PARAMETER DIAGNOSTIC TOOL")
    print("=" * 50)
    print()
    
    check_cognitive_mode_differences()
    check_h1_scenario_parameters()
    check_cognitive_pressure_calculation()
    check_input_file_generation()
    
    print("=" * 50)
    print("DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()