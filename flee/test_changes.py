import sys
import os
import numpy as np

# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (flee-master)
parent_dir = os.path.dirname(current_dir)

# Add to Python path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print(f"Current directory: {current_dir}")
print(f"Parent directory: {parent_dir}")
print(f"Python path: {sys.path[:3]}")  # Show first 3 entries

# Try importing
try:
    from flee import flee
    print("✓ Successfully imported flee!")
except ImportError as e:
    print(f"✗ Import error: {e}")
    # Let's see what's actually available
    try:
        import flee as flee_module
        print("✓ Found flee as direct module")
        flee = flee_module.flee
    except ImportError as e2:
        print(f"✗ Direct import also failed: {e2}")
        # Show what files are available
        print("Files in parent directory:")
        for item in os.listdir(parent_dir):
            if item.endswith('.py') or os.path.isdir(os.path.join(parent_dir, item)):
                print(f"  {item}")
        sys.exit(1)

# ADD ALL THE TEST FUNCTIONS HERE:

def test_dynamic_social_connectivity():
    """Test the dynamic social connectivity system"""
    print("=== Testing Dynamic Social Connectivity ===")
    
    # Initialize settings
    flee.SimulationSettings.ReadFromYML("simsetting.yml")
    
    e = flee.Ecosystem()
    
    # ... rest of the test function code ...

def test_system2_activation():
    """Test System 2 activation logic"""
    # ... test function code ...

def test_route_selection_differences():
    """Test that System 1 and System 2 select routes differently"""
    # ... test function code ...

def run_full_simulation_test():
    """Run a small simulation to see System 1/2 in action"""
    # ... test function code ...

if __name__ == "__main__":
    print("Starting System 1/System 2 Integration Tests...")
    print("=" * 50)
    
    try:
        test_dynamic_social_connectivity()
        test_system2_activation()
        test_route_selection_differences()
        run_full_simulation_test()
        
        print("=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()