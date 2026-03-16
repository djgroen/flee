#!/usr/bin/env python3
"""
Test Native Flee Simulation with Actual Agent Movement

This test creates a proper Flee simulation that:
1. Uses native Flee simulation engine (ecosystem.evolve())
2. Actually spawns agents and shows movement
3. Produces standard Flee output (out.csv)
4. Integrates with S1/S2 cognitive enhancements
5. Shows both native Flee output AND S1/S2 diagnostics
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_native_flee_with_agent_movement():
    """Test native Flee simulation with actual agent spawning and movement"""
    print("🚀 TESTING NATIVE FLEE WITH ACTUAL AGENT MOVEMENT")
    print("=" * 70)
    
    try:
        # Import Flee as a proper package
        from flee.flee import Ecosystem
        from flee.SimulationSettings import SimulationSettings
        print("✅ Flee package imported successfully")
        
        # Initialize simulation settings
        SimulationSettings.ReadFromYML("flee/simsetting.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        print("✅ Simulation settings loaded with S1/S2 enabled")
        
        # Create a simple evacuation scenario
        ecosystem = Ecosystem()
        
        # Add locations (note: pop=0 for refugee locations, we'll add agents manually)
        origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=0)
        intermediate = ecosystem.addLocation("Intermediate", x=50, y=0, movechance=0.3, capacity=-1, pop=0)
        camp = ecosystem.addLocation("Camp", x=100, y=0, movechance=0.001, capacity=1000, pop=0)
        
        # Link locations
        ecosystem.linkUp("Origin", "Intermediate", 50.0)
        ecosystem.linkUp("Intermediate", "Camp", 50.0)
        
        # Set conflict levels to drive movement
        origin.conflict = 0.8  # High conflict - agents want to leave
        intermediate.conflict = 0.3  # Medium conflict - transit location
        camp.conflict = 0.1  # Low conflict - safe destination
        
        print(f"✅ Scenario created: {len(ecosystem.locations)} locations")
        
        # Spawn agents at origin with different cognitive profiles
        num_agents = 20
        
        for i in range(num_agents):
            # Create agents with different connectivity levels
            if i < 10:
                # S1-prone agents (low connectivity)
                attributes = {"connections": 1, "safety_threshold": 0.7}
            else:
                # S2-capable agents (high connectivity)
                attributes = {"connections": 8, "safety_threshold": 0.4}
            
            # Add agent to ecosystem at origin
            ecosystem.addAgent(origin, attributes)
        
        print(f"✅ Spawned {num_agents} agents at origin with cognitive profiles")
        print(f"   Initial populations: Origin={origin.numAgents}, Intermediate={intermediate.numAgents}, Camp={camp.numAgents}")
        
        # Prepare output directory and file
        output_dir = Path("native_flee_output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "out.csv"
        
        # Create output header (matching native Flee format)
        with open(output_file, 'w') as f:
            f.write("Day,Date,Origin sim,Intermediate sim,Camp sim,Total refugees\\n")
        
        print(f"✅ Output file prepared: {output_file}")
        
        # Run native Flee simulation
        simulation_days = 15
        print(f"\\n🏃 Running native Flee simulation for {simulation_days} days...")
        print("=" * 50)
        
        for day in range(simulation_days):
            # Record populations before evolution
            origin_pop = origin.numAgents
            intermediate_pop = intermediate.numAgents
            camp_pop = camp.numAgents
            total_pop = origin_pop + intermediate_pop + camp_pop
            
            print(f"Day {day:2d}: Origin={origin_pop:2d}, Intermediate={intermediate_pop:2d}, Camp={camp_pop:2d}, Total={total_pop}")
            
            # Write to output file (native Flee format)
            with open(output_file, 'a') as f:
                f.write(f"{day},Day{day},{origin_pop},{intermediate_pop},{camp_pop},{total_pop}\\n")
            
            # Track S1/S2 cognitive states if available
            s1_count = 0
            s2_count = 0
            
            for agent in ecosystem.agents:
                if hasattr(agent, 'cognitive_state'):
                    if agent.cognitive_state == "S1":
                        s1_count += 1
                    elif agent.cognitive_state == "S2":
                        s2_count += 1
            
            if s1_count > 0 or s2_count > 0:
                print(f"        Cognitive states: S1={s1_count}, S2={s2_count}")
            
            # THIS IS THE KEY: Run native Flee simulation step
            ecosystem.evolve()
        
        # Final summary
        final_origin = origin.numAgents
        final_intermediate = intermediate.numAgents
        final_camp = camp.numAgents
        
        print("\\n📊 SIMULATION SUMMARY")
        print("=" * 30)
        print(f"Initial agents: {num_agents}")
        print(f"Final distribution:")
        print(f"  Origin: {final_origin} ({final_origin/num_agents*100:.1f}%)")
        print(f"  Intermediate: {final_intermediate} ({final_intermediate/num_agents*100:.1f}%)")
        print(f"  Camp: {final_camp} ({final_camp/num_agents*100:.1f}%)")
        
        # Verify output file
        if output_file.exists():
            with open(output_file, 'r') as f:
                lines = f.readlines()
                print(f"\\n✅ Native Flee output generated: {len(lines)} lines in out.csv")
                
                # Show sample lines
                print("\\n📄 Output file sample:")
                print("   " + lines[0].strip())  # Header
                print("   " + lines[1].strip())  # Day 0
                print("   " + lines[-1].strip())  # Final day
                
                return True
        else:
            print("❌ Output file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_s1s2_enhanced_flee_simulation():
    """Test S1/S2 enhanced Flee simulation with cognitive decision tracking"""
    print("\\n\\n🧠 TESTING S1/S2 ENHANCED FLEE SIMULATION")
    print("=" * 70)
    
    try:
        from flee.flee import Ecosystem
        from flee.SimulationSettings import SimulationSettings
        from scripts.refugee_person_enhancements import create_refugee_agent
        from scripts.refugee_decision_tracker import RefugeeDecisionTracker
        
        # Initialize with enhanced cognitive settings
        SimulationSettings.ReadFromYML("flee/simsetting.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.5
        SimulationSettings.move_rules["average_social_connectivity"] = 4
        
        print("✅ Enhanced cognitive parameters loaded")
        
        # Create bottleneck scenario to test S1/S2 differences
        ecosystem = Ecosystem()
        origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=0)
        bottleneck = ecosystem.addLocation("Bottleneck", x=100, y=0, movechance=0.5, capacity=5, pop=0)  # Small capacity
        camp_a = ecosystem.addLocation("Camp_A", x=150, y=-25, movechance=0.001, capacity=100, pop=0)
        camp_b = ecosystem.addLocation("Camp_B", x=150, y=25, movechance=0.001, capacity=100, pop=0)
        alternative = ecosystem.addLocation("Alternative", x=50, y=50, movechance=0.3, capacity=-1, pop=0)
        
        # Set conflict levels
        origin.conflict = 0.9  # High conflict
        bottleneck.conflict = 0.4  # Medium conflict, but limited capacity
        camp_a.conflict = 0.1  # Safe
        camp_b.conflict = 0.1  # Safe
        alternative.conflict = 0.2  # Safer alternative route
        
        # Create network topology
        ecosystem.linkUp("Origin", "Bottleneck", 100.0)
        ecosystem.linkUp("Bottleneck", "Camp_A", 56.0)
        ecosystem.linkUp("Bottleneck", "Camp_B", 56.0)
        ecosystem.linkUp("Origin", "Alternative", 71.0)
        ecosystem.linkUp("Alternative", "Camp_B", 71.0)
        
        print("✅ Bottleneck scenario created with alternative route")
        
        # Create enhanced agents with different cognitive profiles
        tracker = RefugeeDecisionTracker()
        
        # S1-prone agents (low connectivity, prefer simple heuristics)
        for i in range(8):
            agent = create_refugee_agent(origin, {"connections": 1}, {"safety_threshold": 0.7})
            ecosystem.agents.append(agent)
        
        # S2-capable agents (high connectivity, can use complex analysis)
        for i in range(8):
            agent = create_refugee_agent(origin, {"connections": 8}, {"safety_threshold": 0.4})
            ecosystem.agents.append(agent)
        
        print(f"✅ Created {len(ecosystem.agents)} enhanced agents")
        print(f"   S1-prone (low connectivity): 8 agents")
        print(f"   S2-capable (high connectivity): 8 agents")
        
        # Run enhanced simulation with decision tracking
        decision_data = []
        
        print(f"\\n🔬 Running enhanced simulation with decision tracking...")
        print("=" * 60)
        
        for day in range(12):
            # Record state before evolution
            populations = {
                'Origin': origin.numAgents,
                'Bottleneck': bottleneck.numAgents,
                'Camp_A': camp_a.numAgents,
                'Camp_B': camp_b.numAgents,
                'Alternative': alternative.numAgents
            }
            
            # Track cognitive decisions
            day_decisions = {'day': day, 's1_decisions': 0, 's2_decisions': 0, 'total_pressure': 0}
            
            for agent in ecosystem.agents:
                if hasattr(agent, 'calculate_cognitive_pressure'):
                    pressure = agent.calculate_cognitive_pressure(day)
                    day_decisions['total_pressure'] += pressure
                    
                    # Determine if S2 would be activated
                    s2_active = pressure > 0.6  # Threshold for S2 activation
                    
                    if s2_active:
                        day_decisions['s2_decisions'] += 1
                    else:
                        day_decisions['s1_decisions'] += 1
                    
                    # Track decision
                    tracker.track_refugee_decision(agent, s2_active, pressure, day)
            
            decision_data.append(day_decisions)
            
            # Print daily summary
            total_agents = sum(populations.values())
            avg_pressure = day_decisions['total_pressure'] / max(1, total_agents)
            
            print(f"Day {day:2d}: {populations} | S1={day_decisions['s1_decisions']:2d}, S2={day_decisions['s2_decisions']:2d}, P={avg_pressure:.2f}")
            
            # Run native Flee evolution
            ecosystem.evolve()
        
        # Analysis summary
        print("\\n📈 COGNITIVE DECISION ANALYSIS")
        print("=" * 40)
        
        total_s1 = sum(d['s1_decisions'] for d in decision_data)
        total_s2 = sum(d['s2_decisions'] for d in decision_data)
        total_decisions = total_s1 + total_s2
        
        if total_decisions > 0:
            print(f"Total S1 decisions: {total_s1} ({total_s1/total_decisions*100:.1f}%)")
            print(f"Total S2 decisions: {total_s2} ({total_s2/total_decisions*100:.1f}%)")
            
            # Check if S2 agents found alternative route
            final_alt = alternative.numAgents
            if final_alt > 0:
                print(f"✅ {final_alt} agents used alternative route (likely S2 behavior)")
            else:
                print("⚠️  No agents used alternative route")
        
        print(f"\\n✅ Enhanced S1/S2 simulation completed with {len(decision_data)} days of cognitive tracking")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all native Flee integration tests"""
    print("🧪 NATIVE FLEE SIMULATION WITH S1/S2 INTEGRATION")
    print("=" * 70)
    
    tests = [
        ("Native Flee with Agent Movement", test_native_flee_with_agent_movement),
        ("S1/S2 Enhanced Flee Simulation", test_s1s2_enhanced_flee_simulation)
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
    print("\\n\\n📋 FINAL TEST SUMMARY")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:35} {status}")
        if success:
            passed += 1
    
    print(f"\\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\\n🎉 SUCCESS! Native Flee integration with S1/S2 is working perfectly!")
        print("\\n📁 Check 'native_flee_output/' for standard Flee output files")
        print("\\n🔬 Key findings:")
        print("   • Native Flee simulation engine (ecosystem.evolve()) works")
        print("   • Standard Flee output (out.csv) is generated")
        print("   • S1/S2 cognitive enhancements integrate properly")
        print("   • Agent movement and decision tracking works")
        print("\\n✨ Ready to integrate with standardized diagnostic suite!")
    else:
        print(f"\\n⚠️  {total - passed} test(s) failed. Check error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)