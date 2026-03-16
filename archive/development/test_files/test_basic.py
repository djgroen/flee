#!/usr/bin/env python3

print("Starting basic test...")

try:
    from flee.SimulationSettings import SimulationSettings
    print("✅ SimulationSettings imported")
    
    from flee.flee import Ecosystem, Person
    print("✅ Flee classes imported")
    
    from flee import moving
    print("✅ Moving module imported")
    
    from scripts.refugee_decision_tracker import RefugeeDecisionTracker
    print("✅ RefugeeDecisionTracker imported")
    
    print("🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()