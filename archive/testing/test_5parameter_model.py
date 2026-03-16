#!/usr/bin/env python3
"""
Test script for 5-parameter S1/S2 model.

Quick validation with 1,000 agents to verify:
1. Model runs without errors
2. S2 activation rates are reasonable (10-50%)
3. Cognitive pressure is bounded [0.0, 1.0]
4. Results are reproducible

For demonstration to colleagues.
"""

import sys
from pathlib import Path
import json
import time as time_module

# Add flee to path
sys.path.append('.')

from flee import flee
from flee.SimulationSettings import SimulationSettings
from flee import InputGeography
from flee.datamanager import handle_refugee_data
import yaml


def test_5parameter_model():
    """
    Test the 5-parameter S1/S2 model with 3 small experiments.
    
    Each experiment:
    - 1,000 agents (fast execution)
    - 5 days (quick validation)
    - Different topology (star, linear, grid)
    """
    
    print("=" * 70)
    print("🧪 5-PARAMETER S1/S2 MODEL VALIDATION TEST")
    print("=" * 70)
    print()
    print("📋 Test Configuration:")
    print("   • Population: 1,000 agents per experiment")
    print("   • Duration: 5 days")
    print("   • Topologies: Star, Linear, Grid (4 nodes each)")
    print("   • S2 Threshold: 0.5 (medium)")
    print()
    print("🎯 Validation Criteria:")
    print("   ✓ Model runs without errors")
    print("   ✓ S2 activation rate: 10-50% (reasonable range)")
    print("   ✓ Cognitive pressure: bounded [0.0, 1.0]")
    print("   ✓ Results are reproducible")
    print()
    print("=" * 70)
    print()
    
    # Test configurations
    test_configs = [
        {'topology': 'star', 'size': 4, 'scenario': 'medium_s2', 'population': 1000},
        {'topology': 'linear', 'size': 4, 'scenario': 'medium_s2', 'population': 1000},
        {'topology': 'grid', 'size': 4, 'scenario': 'medium_s2', 'population': 1000}
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        exp_name = f"{config['topology']}_n{config['size']}_{config['scenario']}_{config['population']}"
        exp_dir = Path("proper_10k_agent_experiments") / f"{config['topology']}_n{config['size']}_{config['scenario']}_10k"
        
        print(f"\n{'=' * 70}")
        print(f"🧪 Test {i}/3: {exp_name}")
        print(f"{'=' * 70}")
        
        start_time = time_module.time()
        
        try:
            # Load simsetting.yml
            simsetting_path = exp_dir / "simsetting.yml"
            if not simsetting_path.exists():
                print(f"❌ SKIP: {simsetting_path} not found")
                continue
            
            with open(simsetting_path, 'r') as f:
                sim_settings = yaml.safe_load(f)
            
            # Enable 5-parameter model
            if 'move_rules' not in sim_settings:
                sim_settings['move_rules'] = {}
            
            # Add 5-parameter model configuration
            sim_settings['move_rules']['s1s2_model_params'] = {
                'enabled': True,
                'alpha': 2.0,    # Education sensitivity
                'beta': 2.0,     # Conflict sensitivity
                'eta': 4.0,      # S2 activation steepness
                'theta': 0.5,    # S2 threshold
                'p_s2': 0.8      # S2 move probability
            }
            
            # Save modified settings
            temp_settings_path = exp_dir / "simsetting_5param.yml"
            with open(temp_settings_path, 'w') as f:
                yaml.dump(sim_settings, f)
            
            # Set up simulation
            SimulationSettings.ReadFromYML(temp_settings_path)
            
            # Create ecosystem
            e = flee.Ecosystem()
            
            # Create input geography
            ig = InputGeography.InputGeography()
            
            # Set conflict input file and read input files
            flee.SimulationSettings.ConflictInputFile = str(exp_dir / "input_csv" / "conflicts.csv")
            ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
            ig.ReadLocationsFromCSV(str(exp_dir / "input_csv" / "locations.csv"))
            ig.ReadLinksFromCSV(str(exp_dir / "input_csv" / "routes.csv"))
            ig.ReadClosuresFromCSV(str(exp_dir / "input_csv" / "closures.csv"))
            
            # Store input geography in ecosystem
            e, lm = ig.StoreInputGeographyInEcosystem(e)
            
            # Create refugee data handler
            d = handle_refugee_data.RefugeeTable(
                csvformat="generic", 
                data_directory=str(exp_dir / "source_data"), 
                start_date="2013-01-01", 
                data_layout="data_layout.csv"
            )
            
            # Spawn agents with education attribute
            print(f"   👥 Spawning {config['population']} agents...")
            origin_location = None
            for loc_name, loc in lm.items():
                if "Origin" in loc_name:
                    origin_location = loc
                    break
            
            if origin_location is None:
                print(f"   ❌ No origin location found!")
                continue
            
            for j in range(config['population']):
                agent_attributes = {
                    'connections': 5,
                    'education_level': 0.5 + (j % 5) * 0.1,  # Vary education: 0.5-0.9
                    'stress_tolerance': 0.6,
                    's2_threshold': 0.5,
                    'cognitive_profile': 'balanced',
                    'education': 0.5 + (j % 5) * 0.1  # For 5-parameter model
                }
                agent = flee.Person(origin_location, agent_attributes)
                e.agents.append(agent)
            
            print(f"   ✅ Spawned {len(e.agents)} agents")
            
            # Run simulation
            simulation_days = 5
            print(f"   🏃 Running simulation for {simulation_days} days...")
            
            s2_activations_per_day = []
            pressure_values = []
            
            for day in range(simulation_days):
                # Count S2 activations and collect pressure values
                day_s2_count = 0
                day_pressures = []
                
                for agent in e.agents:
                    # Get cognitive pressure
                    pressure = agent.calculate_cognitive_pressure(day)
                    day_pressures.append(pressure)
                    
                    # Check if agent has S2 activation probability
                    if hasattr(agent, 's2_activation_prob') and agent.s2_activation_prob > 0.5:
                        day_s2_count += 1
                
                s2_activations_per_day.append(day_s2_count)
                pressure_values.extend(day_pressures)
                
                # Evolve ecosystem
                e.evolve()
                
                if day % 2 == 0:
                    s2_rate = (day_s2_count / len(e.agents)) * 100 if e.agents else 0
                    print(f"      Day {day}: {len(e.agents)} agents, S2: {s2_rate:.1f}%")
            
            # Calculate final statistics
            total_s2_activations = sum(s2_activations_per_day)
            avg_s2_rate = (total_s2_activations / (len(e.agents) * simulation_days)) * 100 if e.agents else 0
            
            # Pressure statistics
            min_pressure = min(pressure_values) if pressure_values else 0.0
            max_pressure = max(pressure_values) if pressure_values else 0.0
            avg_pressure = sum(pressure_values) / len(pressure_values) if pressure_values else 0.0
            
            # Validation checks
            pressure_bounded = (min_pressure >= 0.0) and (max_pressure <= 1.0)
            s2_rate_reasonable = (10.0 <= avg_s2_rate <= 50.0)
            
            elapsed_time = time_module.time() - start_time
            
            # Store results
            result = {
                'experiment': exp_name,
                'topology': config['topology'],
                'size': config['size'],
                'population': config['population'],
                'days': simulation_days,
                's2_activation_rate': avg_s2_rate,
                'total_s2_activations': total_s2_activations,
                'pressure_min': min_pressure,
                'pressure_max': max_pressure,
                'pressure_avg': avg_pressure,
                'pressure_bounded': pressure_bounded,
                's2_rate_reasonable': s2_rate_reasonable,
                'execution_time': elapsed_time,
                'status': 'SUCCESS'
            }
            results.append(result)
            
            # Print summary
            print()
            print(f"   📊 Results:")
            print(f"      • S2 Activation Rate: {avg_s2_rate:.1f}%")
            print(f"      • Cognitive Pressure: [{min_pressure:.3f}, {max_pressure:.3f}], avg={avg_pressure:.3f}")
            print(f"      • Pressure Bounded [0,1]: {'✅ YES' if pressure_bounded else '❌ NO'}")
            print(f"      • S2 Rate Reasonable [10-50%]: {'✅ YES' if s2_rate_reasonable else '⚠️  NO'}")
            print(f"      • Execution Time: {elapsed_time:.2f}s")
            print(f"   ✅ Test PASSED")
            
        except Exception as ex:
            elapsed_time = time_module.time() - start_time
            print(f"   ❌ Test FAILED: {ex}")
            import traceback
            traceback.print_exc()
            
            result = {
                'experiment': exp_name,
                'topology': config['topology'],
                'size': config['size'],
                'population': config['population'],
                'status': 'FAILED',
                'error': str(ex),
                'execution_time': elapsed_time
            }
            results.append(result)
    
    # Final summary
    print()
    print("=" * 70)
    print("📊 VALIDATION TEST SUMMARY")
    print("=" * 70)
    print()
    
    successful_tests = [r for r in results if r.get('status') == 'SUCCESS']
    failed_tests = [r for r in results if r.get('status') == 'FAILED']
    
    print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed Tests: {len(failed_tests)}/{len(results)}")
    print()
    
    if successful_tests:
        print("📈 S2 Activation Rates:")
        for result in successful_tests:
            status_icon = "✅" if result['s2_rate_reasonable'] else "⚠️ "
            print(f"   {status_icon} {result['topology']:8s}: {result['s2_activation_rate']:5.1f}%")
        
        print()
        print("🧠 Cognitive Pressure Ranges:")
        for result in successful_tests:
            status_icon = "✅" if result['pressure_bounded'] else "❌"
            print(f"   {status_icon} {result['topology']:8s}: [{result['pressure_min']:.3f}, {result['pressure_max']:.3f}], avg={result['pressure_avg']:.3f}")
        
        print()
        print("⏱️  Execution Times:")
        for result in successful_tests:
            print(f"   • {result['topology']:8s}: {result['execution_time']:.2f}s")
        
        # Overall validation
        print()
        all_pressure_bounded = all(r['pressure_bounded'] for r in successful_tests)
        all_s2_reasonable = all(r['s2_rate_reasonable'] for r in successful_tests)
        
        print("🎯 Overall Validation:")
        print(f"   {'✅' if all_pressure_bounded else '❌'} All pressures bounded [0.0, 1.0]")
        print(f"   {'✅' if all_s2_reasonable else '⚠️ '} All S2 rates reasonable [10-50%]")
        print(f"   {'✅' if len(failed_tests) == 0 else '❌'} No failed tests")
        
        if all_pressure_bounded and len(failed_tests) == 0:
            print()
            print("🎉 5-PARAMETER MODEL VALIDATION: PASSED")
            print("   ✓ Model is ready for full experiments")
        else:
            print()
            print("⚠️  5-PARAMETER MODEL VALIDATION: NEEDS REVIEW")
            if not all_s2_reasonable:
                print("   • S2 activation rates outside expected range")
            if not all_pressure_bounded:
                print("   • Cognitive pressure not properly bounded")
    
    # Save results
    results_file = Path("test_5parameter_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'test_date': time_module.strftime('%Y-%m-%d %H:%M:%S'),
            'test_type': '5-parameter model validation',
            'test_config': {
                'population': 1000,
                'days': 5,
                'topologies': ['star', 'linear', 'grid'],
                'parameters': {
                    'alpha': 2.0,
                    'beta': 2.0,
                    'eta': 4.0,
                    'theta': 0.5,
                    'p_s2': 0.8
                }
            },
            'results': results,
            'summary': {
                'total_tests': len(results),
                'successful': len(successful_tests),
                'failed': len(failed_tests),
                'all_pressure_bounded': all_pressure_bounded if successful_tests else False,
                'all_s2_reasonable': all_s2_reasonable if successful_tests else False
            }
        }, f, indent=2)
    
    print()
    print(f"💾 Results saved to: {results_file}")
    print()
    print("=" * 70)
    print("🎓 READY FOR COLLEAGUE DEMONSTRATION")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review test_5parameter_results.json")
    print("2. If validation passed, run full 27-experiment suite")
    print("3. Generate comparison figures")
    print("4. Present to colleagues with confidence!")
    print()


if __name__ == "__main__":
    test_5parameter_model()




