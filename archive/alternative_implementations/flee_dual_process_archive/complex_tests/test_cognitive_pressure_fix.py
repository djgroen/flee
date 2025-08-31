#!/usr/bin/env python3
"""
Test the cognitive pressure fix
"""

def test_cognitive_pressure():
    """Test cognitive pressure with new parameters."""
    print("=== TESTING COGNITIVE PRESSURE FIX ===\n")
    
    # Updated parameters (FINAL FIX)
    mode_params = {
        's1_only': {'connectivity': 0.0, 'threshold': 0.5},
        's2_disconnected': {'connectivity': 0.1, 'threshold': 0.001},
        's2_full': {'connectivity': 15.0, 'threshold': 0.3},
        'dual_process': {'connectivity': 8.0, 'threshold': 0.4}
    }
    
    # H1 scenario parameters
    conflict_intensity = 1.0
    recovery_period = 10  # Very short recovery
    
    print(f"Scenario: conflict_intensity={conflict_intensity}, recovery_period={recovery_period}")
    print()
    
    for mode, params in mode_params.items():
        connectivity = params['connectivity']
        threshold = params['threshold']
        
        # Calculate cognitive pressure
        cognitive_pressure = (conflict_intensity * connectivity) / recovery_period
        
        print(f"Mode: {mode}")
        print(f"  Connectivity: {connectivity}")
        print(f"  Threshold: {threshold}")
        print(f"  Cognitive pressure: {cognitive_pressure:.3f}")
        print(f"  Above threshold: {'YES' if cognitive_pressure > threshold else 'NO'}")
        
        # Calculate pressure ratio for analysis
        if threshold > 0:
            pressure_ratio = cognitive_pressure / threshold
            print(f"  Pressure/Threshold ratio: {pressure_ratio:.2f}x")
        
        print()

if __name__ == "__main__":
    test_cognitive_pressure()