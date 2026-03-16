#!/usr/bin/env python3
"""
Test running Flee directly to see if it works
"""

import os
import sys
import tempfile

def test_flee_direct():
    """Test running Flee directly."""
    
    # Create a simple test scenario
    temp_dir = tempfile.mkdtemp(prefix="flee_test_")
    print(f"Test directory: {temp_dir}")
    
    # Create minimal input files
    locations_content = """#name,region,country,lat,lon,location_type,conflict_date,pop/cap
Origin,region1,country1,0.0,0.0,town,,1000
Camp_A,region1,country1,1.0,0.0,camp,,500
"""
    
    routes_content = """#name1,name2,distance,forced_redirection
Origin,Camp_A,50,0
"""
    
    conflicts_content = """#Day,Origin
0,0.0
1,0.0
2,1.0
"""
    
    closures_content = """#Day,name1,name2,closure_type
"""
    
    simsetting_content = """max_days: 5
print_progress: true
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
    
    with open(os.path.join(temp_dir, "simsetting.yml"), "w") as f:
        f.write(simsetting_content)
    
    print("Input files created:")
    for file in os.listdir(temp_dir):
        print(f"  {file}")
    
    # Try to run Flee
    try:
        import flee.flee as flee_module
        
        print("\nRunning Flee simulation...")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # Run simulation
        sys.argv = ['flee.py', '.', '5']  # Simulate command line args
        
        flee_module.main()
        
        os.chdir(original_cwd)
        
        print("✓ Flee simulation completed")
        
        # Check output
        print("\nOutput files:")
        for file in os.listdir(temp_dir):
            print(f"  {file}")
            
    except Exception as e:
        print(f"✗ Flee simulation failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up: {temp_dir}")
        except:
            pass

if __name__ == "__main__":
    test_flee_direct()