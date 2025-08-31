#!/usr/bin/env python3
"""
Direct test of cognitive modes using Flee API
Based on the steering files and test_twosystem.py patterns
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Import Flee directly
from flee import flee
from flee import InputGeography
from flee.datamanager import handle_refugee_data, read_period

def create_test_input_files(temp_dir):
    """Create test input files in the expected format."""
    
    # Create locations.csv
    locations_content = """#name,region,country,lat,lon,location_type,conflict_date,pop/cap
Origin,region1,country1,0.0,0.0,town,,5000
Camp_A,region1,country1,1.0,0.0,camp,,500
Camp_B,region1,country1,2.0,0.0,camp,,1500
Camp_C,region1,country1,4.0,0.0,camp,,3000
"""
    
    # Create routes.csv
    routes_content = """#name1,name2,distance,forced_redirection
Origin,Camp_A,30,0
Origin,Camp_B,60,0
Origin,Camp_C,120,0
"""
    
    # Create conflicts.csv
    conflicts_content = """#Day,Origin
0,0.0
1,0.0
2,1.0
3,1.0
4,1.0
5,1.0
6,1.0
7,1.0
8,1.0
9,1.0
"""
    
    # Create closures.csv (empty)
    closures_content = """#Day,name1,name2,closure_type
"""
    
    # Create sim_period.csv
    sim_period_content = """#StartDate,EndDate
2023-01-01,2023-01-10
"""
    
    # Write files
    files = {
        "locations.csv": locations_content,
        "routes.csv": routes_content,
        "conflicts.csv": conflicts_content,
        "closures.csv": closures_content,
        "sim_period.csv": sim_period_content
    }
    
    for filename, content in files.items():
        with open(os.path.join(temp_dir, filename), "w") as f:
            f.write(content)
    
    return temp_dir

def create_simsetting_yml(cognitive_mode, temp_dir):
    """Create simsetting.yml for a specific cognitive mode."""
    
    # Cognitive mode configurations (from our fixed config_manager.py)
    mode_configs = {
        's1_only': {
            'TwoSystemDecisionMaking': False,
            'awareness_level': 1,
            'weight_softening': 0.8,
            'average_social_connectivity': 0.0,
            'default_movechance': 0.5,
            'conflict_movechance': 1.0,
            'conflict_threshold': 0.5
        },
        's2_disconnected': {
            'TwoSystemDecisionMaking': True,
            'average_social_connectivity': 0.1,
            'awareness_level': 3,
            'weight_softening': 0.1,
            'conflict_threshold': 0.001,
            'default_movechance': 0.2,
            'conflict_movechance': 0.8,
        },
        's2_full': {
            'TwoSystemDecisionMaking': True,
            'average_social_connectivity': 15.0,
            'awareness_level': 3,
            'weight_softening': 0.1,
            'conflict_threshold': 0.3,
            'default_movechance': 0.2,
            'conflict_movechance': 0.8,
        },
        'dual_process': {
            'TwoSystemDecisionMaking': True,
            'average_social_connectivity': 8.0,
            'awareness_level': 2,
            'weight_softening': 0.4,
            'conflict_threshold': 0.4,
            'recovery_period_max': 10,
            'default_movechance': 0.3,
            'conflict_movechance': 0.9,
        }
    }
    
    config = mode_configs.get(cognitive_mode, mode_configs['s1_only'])
    
    # Create simsetting.yml content
    simsetting_content = f"""# H1 Test Configuration for {cognitive_mode}
log_levels:
  agent: 0

move_rules:
  two_system_decision_making: {config['TwoSystemDecisionMaking']}
  awareness_level: {config['awareness_level']}
  weight_softening: {config['weight_softening']}
  average_social_connectivity: {config['average_social_connectivity']}
  default_movechance: {config['default_movechance']}
  conflict_movechance: {config['conflict_movechance']}
  conflict_threshold: {config['conflict_threshold']}
  max_move_speed: 360.0

spawn_rules:
  take_from_population: False
"""
    
    if 'recovery_period_max' in config:
        simsetting_content += f"  recovery_period_max: {config['recovery_period_max']}\n"
    
    simsetting_path = os.path.join(temp_dir, "simsetting.yml")
    with open(simsetting_path, "w") as f:
        f.write(simsetting_content)
    
    return simsetting_path

def run_cognitive_mode_simulation(cognitive_mode, max_days=10):
    """Run a simulation with a specific cognitive mode using Flee API directly."""
    
    print(f"\n=== Running {cognitive_mode} simulation ===")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix=f"flee_{cognitive_mode}_")
    
    try:
        # Create input files
        create_test_input_files(temp_dir)
        simsetting_path = create_simsetting_yml(cognitive_mode, temp_dir)
        
        print(f"Input directory: {temp_dir}")
        
        # Load simulation settings
        flee.SimulationSettings.ReadFromYML(simsetting_path)
        
        # Verify our settings were loaded
        two_system = flee.SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False)
        connectivity = flee.SimulationSettings.move_rules.get("average_social_connectivity", 0)
        threshold = flee.SimulationSettings.move_rules.get("conflict_threshold", 0.5)
        
        print(f"  TwoSystemDecisionMaking: {two_system}")
        print(f"  Social Connectivity: {connectivity}")
        print(f"  Conflict Threshold: {threshold}")
        
        # Set conflict input file
        flee.SimulationSettings.ConflictInputFile = os.path.join(temp_dir, "conflicts.csv")
        
        # Create ecosystem
        e = flee.Ecosystem()
        
        # Load geography
        ig = InputGeography.InputGeography()
        
        # Read input files
        ig.ReadLocationsFromCSV(os.path.join(temp_dir, "locations.csv"))
        ig.ReadLinksFromCSV(os.path.join(temp_dir, "routes.csv"))
        ig.ReadClosuresFromCSV(os.path.join(temp_dir, "closures.csv"))
        
        # Store geography in ecosystem
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        
        print(f"  Locations loaded: {list(lm.keys())}")
        
        # Run simulation
        results = {}
        
        for t in range(max_days):
            # Add conflict zones
            ig.AddNewConflictZones(e, t)
            
            # Spawn agents (simplified - just add some agents at origin)
            if t == 0:
                origin_loc = lm.get('Origin')
                if origin_loc:
                    # Add some agents to origin
                    for i in range(100):  # Add 100 agents
                        agent_attributes = {"connections": connectivity}
                        agent = flee.Person(origin_loc, agent_attributes)
                        e.addAgent(agent)
            
            # Evolve ecosystem
            e.evolve()
            
            # Record populations
            day_results = {'day': t}
            for loc_name, loc in lm.items():
                day_results[loc_name] = loc.numAgents
            
            results[t] = day_results
            
            print(f"  Day {t}: Origin={lm['Origin'].numAgents}, Camp_A={lm['Camp_A'].numAgents}, Camp_B={lm['Camp_B'].numAgents}, Camp_C={lm['Camp_C'].numAgents}")
        
        return {
            'success': True,
            'cognitive_mode': cognitive_mode,
            'results': results,
            'final_populations': {
                'Origin': lm['Origin'].numAgents,
                'Camp_A': lm['Camp_A'].numAgents,
                'Camp_B': lm['Camp_B'].numAgents,
                'Camp_C': lm['Camp_C'].numAgents
            },
            'total_displaced': lm['Camp_A'].numAgents + lm['Camp_B'].numAgents + lm['Camp_C'].numAgents
        }
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'cognitive_mode': cognitive_mode,
            'error': str(e)
        }
    
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def main():
    """Test all cognitive modes and compare results."""
    
    print("=" * 60)
    print("DIRECT COGNITIVE MODE TEST USING FLEE API")
    print("=" * 60)
    
    # Test cognitive modes
    modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
    results = {}
    
    for mode in modes:
        results[mode] = run_cognitive_mode_simulation(mode, max_days=10)
    
    # Analyze results
    print("\n" + "=" * 60)
    print("RESULTS ANALYSIS")
    print("=" * 60)
    
    successful_results = {mode: result for mode, result in results.items() if result.get('success')}
    
    if len(successful_results) >= 2:
        print("\nFinal populations by cognitive mode:")
        
        for mode, result in successful_results.items():
            if 'final_populations' in result:
                pops = result['final_populations']
                total = result.get('total_displaced', 0)
                print(f"\n{mode}:")
                print(f"  Origin: {pops.get('Origin', 0)}")
                print(f"  Camp_A: {pops.get('Camp_A', 0)}")
                print(f"  Camp_B: {pops.get('Camp_B', 0)}")
                print(f"  Camp_C: {pops.get('Camp_C', 0)}")
                print(f"  Total displaced: {total}")
        
        # Check for differences
        total_displaced = [result.get('total_displaced', 0) for result in successful_results.values()]
        camp_a_pops = [result['final_populations'].get('Camp_A', 0) for result in successful_results.values()]
        
        print(f"\nTotal displaced across modes: {total_displaced}")
        print(f"Camp_A populations across modes: {camp_a_pops}")
        
        if len(set(total_displaced)) > 1 or len(set(camp_a_pops)) > 1:
            print("\n✓ DIFFERENT RESULTS FOUND!")
            print("The cognitive mode fixes are working correctly.")
            
            # Show differences
            for i, mode1 in enumerate(successful_results.keys()):
                for mode2 in list(successful_results.keys())[i+1:]:
                    result1 = successful_results[mode1]
                    result2 = successful_results[mode2]
                    
                    diff_total = abs(result1.get('total_displaced', 0) - result2.get('total_displaced', 0))
                    diff_camp_a = abs(result1['final_populations'].get('Camp_A', 0) - result2['final_populations'].get('Camp_A', 0))
                    
                    if diff_total > 0 or diff_camp_a > 0:
                        print(f"  {mode1} vs {mode2}: Total diff={diff_total}, Camp_A diff={diff_camp_a}")
        else:
            print("\n✗ All modes produced identical results")
            print("The cognitive switching may still not be working properly.")
    
    else:
        print("\n✗ Not enough successful simulations to compare")
        for mode, result in results.items():
            if not result.get('success'):
                print(f"  {mode}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()