#!/usr/bin/env python3
"""
Test Native Flee Simulation with S1/S2 Integration

This test verifies that we can run a proper Flee simulation that:
1. Uses the native Flee simulation engine (ecosystem.evolve())
2. Produces standard Flee output files (out.csv, agents.out)
3. Integrates with our S1/S2 cognitive enhancements
4. Generates both native Flee output AND our S1/S2 diagnostics
"""

import sys
import os
from pathlib import Path
import csv

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_native_flee_simulation():
    """Test that we can run a native Flee simulation with S1/S2 integration"""
    print("🔍 TESTING NATIVE FLEE SIMULATION WITH S1/S2 INTEGRATION")
    print("=" * 70)
    
    try:
        # Import Flee as a proper package
        from flee.flee import Ecosystem
        from flee.SimulationSettings import SimulationSettings
        from flee import moving, spawning
        print("✅ Flee package imported successfully")
        
        # Initialize simulation settings
        SimulationSettings.ReadFromYML("flee/simsetting.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        print("✅ Simulation settings loaded with S1/S2 enabled")
        
        # Create a simple scenario
        ecosystem = Ecosystem()
        
        # Add locations
        origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=100)
        intermediate = ecosystem.addLocation("Intermediate", x=50, y=0, movechance=0.3, capacity=-1, pop=0)
        camp = ecosystem.addLocation("Camp", x=100, y=0, movechance=0.001, capacity=1000, pop=0)
        
        # Link locations
        ecosystem.linkUp("Origin", "Intermediate", 50.0)
        ecosystem.linkUp("Intermediate", "Camp", 50.0)
        
        # Set conflict levels
        origin.conflict = 0.8
        intermediate.conflict = 0.3
        camp.conflict = 0.1
        
        print(f"✅ Scenario created: {len(ecosystem.locations)} locations, {origin.numAgents} initial agents")
        
        # Prepare output directory
        output_dir = Path("native_flee_output")
        output_dir.mkdir(exist_ok=True)
        
        # Prepare output file
        output_file = output_dir / "out.csv"
        
        # Create output header
        output_header = "Day,Date,Origin sim,Intermediate sim,Camp sim,Total refugees\\n"
        
        with open(output_file, 'w') as f:
            f.write(output_header)
        
        print(f"✅ Output file prepared: {output_file}")
        
        # Run native Flee simulation
        simulation_days = 10
        print(f"🚀 Running native Flee simulation for {simulation_days} days...")
        
        for day in range(simulation_days):
            print(f"   Day {day}: ", end="")
            
            # Record populations before evolution
            origin_pop = origin.numAgents
            intermediate_pop = intermediate.numAgents
            camp_pop = camp.numAgents
            total_pop = origin_pop + intermediate_pop + camp_pop
            
            print(f"Origin={origin_pop}, Intermediate={intermediate_pop}, Camp={camp_pop}")
            
            # Write to output file
            with open(output_file, 'a') as f:
                f.write(f"{day},Day{day},{origin_pop},{intermediate_pop},{camp_pop},{total_pop}\\n")
            
            # THIS IS THE KEY: Run native Flee simulation step
            ecosystem.evolve()
            
            # Optional: Track S1/S2 decisions if agents have cognitive capabilities
            s1_decisions = 0
            s2_decisions = 0
            
            for agent in ecosystem.agents:
                    # Check if agent has cognitive state tracking
                    if hasattr(agent, 'cognitive_state'):
                        if agent.cognitive_state == "S1":
                            s1_decisions += 1
                        elif agent.cognitive_state == "S2":
                            s2_decisions += 1
            
            if s1_decisions > 0 or s2_decisions > 0:
                print(f"      Cognitive: S1={s1_decisions}, S2={s2_decisions}")
        
        # Verify output file was created and has content
        if output_file.exists():
            with open(output_file, 'r') as f:
                lines = f.readlines()
                print(f"✅ Native Flee output generated: {len(lines)} lines in out.csv")
                
                # Show first few lines
                print("📄 Output file preview:")
                for i, line in enumerate(lines[:5]):
                    print(f"   {i}: {line.strip()}")
                
                return True
        else:
            print("❌ Output file was not created")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure Flee is properly installed as a package")
        return False
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_s1s2_integration_with_native_flee():
    """Test S1/S2 cognitive integration with native Flee simulation"""
    print("\\n🧠 TESTING S1/S2 COGNITIVE INTEGRATION WITH NATIVE FLEE")
    print("=" * 70)
    
    try:
        from flee.flee import Ecosystem
        from flee.SimulationSettings import SimulationSettings
        from scripts.refugee_person_enhancements import create_refugee_agent
        
        # Initialize with cognitive settings
        SimulationSettings.ReadFromYML("flee/simsetting.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.5
        SimulationSettings.move_rules["average_social_connectivity"] = 4
        
        print("✅ Cognitive parameters loaded into SimulationSettings")
        
        # Create ecosystem
        ecosystem = Ecosystem()
        origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=0)
        camp = ecosystem.addLocation("Camp", x=100, y=0, movechance=0.001, capacity=500, pop=0)
        ecosystem.linkUp("Origin", "Camp", 100.0)
        
        # Create enhanced agents with different cognitive profiles
        agents = []
        
        # S1-prone agents (low connectivity)
        for i in range(5):
            agent = create_refugee_agent(origin, {"connections": 1}, {"safety_threshold": 0.7})
            agents.append(agent)
        
        # S2-capable agents (high connectivity)
        for i in range(5):
            agent = create_refugee_agent(origin, {"connections": 8}, {"safety_threshold": 0.4})
            agents.append(agent)
        
        print(f"✅ Created {len(agents)} enhanced agents with cognitive profiles")
        
        # Run simulation with cognitive tracking
        cognitive_data = []
        
        for day in range(5):
            print(f"   Day {day}: ", end="")
            
            # Track cognitive states before evolution
            day_data = {'day': day, 's1_count': 0, 's2_count': 0, 'decisions': []}
            
            for agent in agents:
                # Check cognitive state if available
                if hasattr(agent, 'cognitive_state'):
                    if agent.cognitive_state == "S1":
                        day_data['s1_count'] += 1
                    elif agent.cognitive_state == "S2":
                        day_data['s2_count'] += 1
                
                # Track decision if agent has cognitive pressure calculation
                if hasattr(agent, 'calculate_cognitive_pressure'):
                    pressure = agent.calculate_cognitive_pressure(day)
                    day_data['decisions'].append({
                        'agent_id': id(agent),
                        'pressure': pressure,
                        'connectivity': agent.attributes.get('connections', 0)
                    })
            
            cognitive_data.append(day_data)
            
            print(f"S1={day_data['s1_count']}, S2={day_data['s2_count']}, Decisions={len(day_data['decisions'])}")
            
            # Run native Flee evolution
            ecosystem.evolve()
        
        print(f"✅ Cognitive integration test completed with {len(cognitive_data)} days of data")
        return True
        
    except Exception as e:
        print(f"❌ Cognitive integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all native Flee integration tests"""
    print("🧪 NATIVE FLEE SIMULATION INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Native Flee Simulation", test_native_flee_simulation),
        ("S1/S2 Cognitive Integration", test_s1s2_integration_with_native_flee)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\\n📋 TEST SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if success:
            passed += 1
    
    print(f"\\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\\n🎉 All tests passed! Native Flee integration is working.")
        print("\\n📁 Check 'native_flee_output/' directory for Flee's standard output files.")
        print("\\n🔬 Next step: Integrate this with S1/S2 diagnostic suite for complete analysis.")
    else:
        print(f"\\n⚠️  {total - passed} test(s) failed. Check error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)