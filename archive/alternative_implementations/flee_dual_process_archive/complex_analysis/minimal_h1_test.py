#!/usr/bin/env python3
"""
Minimal H1 test that directly calls Flee with different cognitive modes
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

def create_minimal_h1_input():
    """Create minimal input files for H1 test."""
    temp_dir = tempfile.mkdtemp(prefix="h1_minimal_")
    
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
"""
    
    # Create closures.csv (empty)
    closures_content = """#Day,name1,name2,closure_type
"""
    
    # Write files
    with open(os.path.join(temp_dir, "locations.csv"), "w") as f:
        f.write(locations_content)
    
    with open(os.path.join(temp_dir, "routes.csv"), "w") as f:
        f.write(routes_content)
    
    with open(os.path.join(temp_dir, "conflicts.csv"), "w") as f:
        f.write(conflicts_content)
    
    with open(os.path.join(temp_dir, "closures.csv"), "w") as f:
        f.write(closures_content)
    
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
max_days: 20
print_progress: false

move_rules:
  TwoSystemDecisionMaking: {config['TwoSystemDecisionMaking']}
  awareness_level: {config['awareness_level']}
  weight_softening: {config['weight_softening']}
  average_social_connectivity: {config['average_social_connectivity']}
  default_movechance: {config['default_movechance']}
  conflict_movechance: {config['conflict_movechance']}
  conflict_threshold: {config['conflict_threshold']}
"""
    
    if 'recovery_period_max' in config:
        simsetting_content += f"  recovery_period_max: {config['recovery_period_max']}\n"
    
    simsetting_path = os.path.join(temp_dir, "simsetting.yml")
    with open(simsetting_path, "w") as f:
        f.write(simsetting_content)
    
    return simsetting_path

def run_flee_simulation(input_dir, cognitive_mode):
    """Run Flee simulation for a specific cognitive mode."""
    print(f"Running {cognitive_mode} simulation...")
    
    # Create simsetting.yml for this mode
    simsetting_path = create_simsetting_yml(cognitive_mode, input_dir)
    
    # Create output directory
    output_dir = os.path.join(input_dir, f"output_{cognitive_mode}")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Run Flee simulation
        cmd = [
            sys.executable, "-m", "flee.flee",
            input_dir,
            "20",  # max_days
            "2>&1"  # Redirect stderr to stdout
        ]
        
        # Change to the parent directory to run Flee
        original_cwd = os.getcwd()
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        flee_dir = os.path.dirname(parent_dir)  # Go up to the main directory
        
        os.chdir(flee_dir)
        
        result = subprocess.run(
            [sys.executable, "-m", "flee.flee", input_dir, "20"],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        os.chdir(original_cwd)
        
        print(f"  Return code: {result.returncode}")
        if result.stdout:
            print(f"  Stdout: {result.stdout[:200]}...")
        if result.stderr:
            print(f"  Stderr: {result.stderr[:200]}...")
        
        if result.returncode == 0:
            print(f"✓ {cognitive_mode} completed successfully")
            
            # List all files in input directory
            print(f"  Files in {input_dir}:")
            for file in os.listdir(input_dir):
                file_path = os.path.join(input_dir, file)
                if os.path.isdir(file_path):
                    print(f"    {file}/ (directory)")
                    # List contents of output directories
                    if file.startswith('output_'):
                        try:
                            subfiles = os.listdir(file_path)
                            for subfile in subfiles:
                                print(f"      {subfile}")
                        except:
                            pass
                else:
                    print(f"    {file}")
            
            # Check for output files in the output directory
            output_subdir = os.path.join(input_dir, f"output_{cognitive_mode}")
            out_csv = os.path.join(output_subdir, "out.csv")
            
            # Also check the main directory
            if not os.path.exists(out_csv):
                out_csv = os.path.join(input_dir, "out.csv")
            if os.path.exists(out_csv):
                # Read final populations
                with open(out_csv, "r") as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        final_line = lines[-1].strip()
                        print(f"  Final line from out.csv: {final_line}")
                        values = final_line.split(",")
                        if len(values) >= 4:
                            try:
                                day = int(values[0])
                                origin = float(values[1])
                                camp_a = float(values[2]) if len(values) > 2 else 0
                                camp_b = float(values[3]) if len(values) > 3 else 0
                                camp_c = float(values[4]) if len(values) > 4 else 0
                                
                                return {
                                    'success': True,
                                    'final_day': day,
                                    'final_populations': {
                                        'Origin': origin,
                                        'Camp_A': camp_a,
                                        'Camp_B': camp_b,
                                        'Camp_C': camp_c
                                    },
                                    'total_displaced': camp_a + camp_b + camp_c
                                }
                            except (ValueError, IndexError):
                                print(f"  Could not parse values: {values}")
                                pass
                    else:
                        print(f"  out.csv has only {len(lines)} lines")
            else:
                print(f"  out.csv not found at {out_csv}")
            
            return {'success': True, 'message': 'Completed but could not parse results'}
        
        else:
            print(f"✗ {cognitive_mode} failed:")
            print(f"  Return code: {result.returncode}")
            print(f"  Stdout: {result.stdout[:500]}")
            print(f"  Stderr: {result.stderr[:500]}")
            return {'success': False, 'error': result.stderr}
    
    except subprocess.TimeoutExpired:
        print(f"✗ {cognitive_mode} timed out")
        return {'success': False, 'error': 'Timeout'}
    
    except Exception as e:
        print(f"✗ {cognitive_mode} error: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Run minimal H1 test with all cognitive modes."""
    print("=" * 50)
    print("MINIMAL H1 TEST WITH FIXED PARAMETERS")
    print("=" * 50)
    print()
    
    # Create input files
    print("Creating minimal H1 input files...")
    input_dir = create_minimal_h1_input()
    print(f"Input directory: {input_dir}")
    print()
    
    # Test cognitive modes
    modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
    results = {}
    
    try:
        for mode in modes:
            results[mode] = run_flee_simulation(input_dir, mode)
            print()
        
        # Analyze results
        print("=" * 50)
        print("RESULTS ANALYSIS")
        print("=" * 50)
        
        successful_modes = {mode: result for mode, result in results.items() if result.get('success')}
        
        if len(successful_modes) >= 2:
            print("Final populations by cognitive mode:")
            print()
            
            for mode, result in successful_modes.items():
                if 'final_populations' in result:
                    pops = result['final_populations']
                    total = result.get('total_displaced', 0)
                    print(f"{mode}:")
                    print(f"  Origin: {pops.get('Origin', 0):.0f}")
                    print(f"  Camp_A: {pops.get('Camp_A', 0):.0f}")
                    print(f"  Camp_B: {pops.get('Camp_B', 0):.0f}")
                    print(f"  Camp_C: {pops.get('Camp_C', 0):.0f}")
                    print(f"  Total displaced: {total:.0f}")
                    print()
            
            # Check for differences
            total_displaced = [result.get('total_displaced', 0) for result in successful_modes.values()]
            if len(set(total_displaced)) > 1:
                print("✓ DIFFERENT RESULTS FOUND!")
                print("The cognitive mode fixes are working.")
            else:
                print("✗ All modes produced identical results")
                print("May need further parameter tuning.")
        
        else:
            print("✗ Not enough successful simulations to compare")
            for mode, result in results.items():
                if not result.get('success'):
                    print(f"{mode}: {result.get('error', 'Unknown error')}")
    
    finally:
        # Clean up
        try:
            shutil.rmtree(input_dir)
            print(f"\nCleaned up: {input_dir}")
        except:
            pass

if __name__ == "__main__":
    main()