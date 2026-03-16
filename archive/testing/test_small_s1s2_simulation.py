#!/usr/bin/env python3
"""
Test S1/S2 system with a small simulation
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_small_s1s2_simulation():
    """Run a small simulation to test S1/S2 behavior"""
    
    print("🧪 Small S1/S2 Simulation Test")
    print("=" * 50)
    
    # Change to experiment directory
    exp_dir = Path("proper_10k_agent_experiments/star_n4_medium_s2_10k")
    original_dir = os.getcwd()
    os.chdir(exp_dir)
    
    try:
        # Import Flee components
        from flee import flee
        from flee.datamanager import handle_refugee_data, read_period
        from flee import InputGeography
        
        # Read simulation settings
        flee.SimulationSettings.ReadFromYML("simsetting.yml")
        print(f"⚙️ S2 threshold: {flee.SimulationSettings.move_rules.get('TwoSystemDecisionMaking', 0.0)}")
        
        # Create ecosystem
        e = flee.Ecosystem()
        
        # Create input geography
        ig = InputGeography.InputGeography()
        
        # Read input files
        flee.SimulationSettings.ConflictInputFile = "input_csv/conflicts.csv"
        ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
        ig.ReadLocationsFromCSV("input_csv/locations.csv")
        ig.ReadLinksFromCSV("input_csv/routes.csv")
        ig.ReadClosuresFromCSV("input_csv/closures.csv")
        
        # Store input geography in ecosystem
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        
        # Create a small number of agents for testing
        origin_location = None
        for loc_name, loc in lm.items():
            if "Origin" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            print("❌ No origin location found!")
            return
        
        print(f"📍 Origin location: {origin_location.name}")
        print(f"📍 Origin conflict intensity: {getattr(origin_location, 'conflict', 'N/A')}")
        
        # Create 10 test agents with different attributes
        test_agents = []
        for i in range(10):
            # Vary agent attributes
            attributes = {
                'connections': 3 + (i % 5),  # 3-7 connections
                'education_level': 0.3 + (i * 0.1),  # 0.3-1.2 education
                'stress_tolerance': 0.2 + (i * 0.08),  # 0.2-0.9 stress tolerance
                's2_threshold': 0.5
            }
            agent = flee.Person(origin_location, attributes)
            test_agents.append(agent)
        
        print(f"👥 Created {len(test_agents)} test agents")
        
        # Run simulation for 5 timesteps
        print(f"\n🚀 Running simulation for 5 timesteps...")
        print("-" * 40)
        
        s2_activations_by_time = {}
        move_decisions_by_time = {}
        
        for time in range(5):
            print(f"\n⏰ Time {time}:")
            
            s2_activations = 0
            move_decisions = 0
            
            for i, agent in enumerate(test_agents):
                # Calculate move chance and S2 activation
                movechance, system2_active = flee.moving.calculateMoveChance(agent, False, time)
                
                if system2_active:
                    s2_activations += 1
                
                if movechance > 0.5:  # Agent decides to move
                    move_decisions += 1
                    # Simulate route selection
                    try:
                        route = flee.moving.selectRoute(agent, time=time, system2_active=system2_active)
                        if len(route) > 0:
                            # Simulate movement (simplified)
                            agent.timesteps_since_departure += 1
                            agent.places_travelled += 1
                    except Exception as e:
                        print(f"    Agent {i}: Route selection error: {e}")
                
                # Log agent state
                cognitive_pressure = agent.calculate_cognitive_pressure(time)
                print(f"  Agent {i}: Pressure={cognitive_pressure:.3f}, S2={system2_active}, MoveChance={movechance:.3f}")
            
            s2_activations_by_time[time] = s2_activations
            move_decisions_by_time[time] = move_decisions
            
            print(f"  📊 S2 activations: {s2_activations}/{len(test_agents)} ({s2_activations/len(test_agents):.1%})")
            print(f"  📊 Move decisions: {move_decisions}/{len(test_agents)} ({move_decisions/len(test_agents):.1%})")
        
        # Summary
        print(f"\n📈 Simulation Summary:")
        print("-" * 30)
        print("Time | S2 Rate | Move Rate")
        print("-" * 30)
        for time in range(5):
            s2_rate = s2_activations_by_time[time] / len(test_agents)
            move_rate = move_decisions_by_time[time] / len(test_agents)
            print(f"{time:4d} | {s2_rate:7.1%} | {move_rate:8.1%}")
        
        # Check if S2 activation is working
        total_s2_activations = sum(s2_activations_by_time.values())
        if total_s2_activations > 0:
            print(f"\n✅ S2 system is working! Total S2 activations: {total_s2_activations}")
        else:
            print(f"\n⚠️ No S2 activations detected - may need investigation")
        
        # Check if movement is happening
        total_moves = sum(move_decisions_by_time.values())
        if total_moves > 0:
            print(f"✅ Movement system is working! Total move decisions: {total_moves}")
        else:
            print(f"⚠️ No movement decisions detected - may need investigation")
        
        print(f"\n🎉 Small simulation test completed!")
        
    except Exception as e:
        print(f"❌ Error during simulation test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    test_small_s1s2_simulation()




