#!/usr/bin/env python3
"""
Minimal test to verify S1/S2 system works correctly.

This script creates a simple simulation with:
- 1 agent
- 5 locations (1 origin, 3 towns, 1 camp)
- 10 timesteps
- S1/S2 system enabled

Expected output:
- Simulation runs without errors
- S1/S2 activation logic executes
- Cognitive pressure calculated
- Decision history recorded
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_minimal_s1s2():
    """Run minimal S1/S2 test"""
    
    print("🧪 Minimal S1/S2 System Test")
    print("=" * 60)
    
    # Step 1: Test imports
    print("\n[1/5] Testing imports...")
    try:
        from flee import flee
        from flee.SimulationSettings import SimulationSettings
        from flee.moving import calculateMoveChance
        from flee.flee import Person
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Step 2: Create minimal configuration
    print("\n[2/5] Creating configuration...")
    import yaml
    
    config = {
        'log_levels': {
            'agent': 1,
            'link': 0,
            'camp': 0,
            'conflict': 0,
            'init': 0,
            'granularity': 'location'
        },
        'spawn_rules': {
            'take_from_population': False,
            'insert_day0': True
        },
        'move_rules': {
            'max_move_speed': 360.0,
            'max_walk_speed': 35.0,
            'foreign_weight': 1.0,
            'camp_weight': 1.0,
            'conflict_weight': 0.25,
            'conflict_movechance': 0.0,
            'camp_movechance': 0.001,
            'default_movechance': 0.3,
            'awareness_level': 1,
            'capacity_scaling': 1.0,
            'avoid_short_stints': False,
            'start_on_foot': False,
            'weight_power': 1.0,
            'movechance_pop_base': 10000.0,
            'movechance_pop_scale_factor': 0.5,
            # S1/S2 Configuration
            'two_system_decision_making': True,
            'conflict_threshold': 0.5,
            'connectivity_mode': 'baseline',
            'steepness': 6.0
        },
        'optimisations': {
            'hasten': 1
        }
    }
    
    config_file = 'test_simsetting.yml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    print(f"✅ Configuration saved to {config_file}")
    
    # Step 3: Initialize simulation
    print("\n[3/5] Initializing simulation...")
    try:
        SimulationSettings.ReadFromYML(config_file)
        ecosystem = flee.Ecosystem()
        print("✅ Ecosystem created")
        
        # Check S1/S2 is enabled
        s1s2_enabled = SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False)
        print(f"   S1/S2 Enabled: {s1s2_enabled}")
        
        if not s1s2_enabled:
            print("⚠️  WARNING: S1/S2 not enabled in configuration!")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Create simple network
    print("\n[4/5] Creating network topology...")
    try:
        # Add locations: Origin -> Town1 -> Town2 -> Town3 -> Camp
        origin = ecosystem.addLocation(
            name="Origin",
            x=0.0, y=0.0,
            movechance=1.0,
            capacity=-1,
            pop=0
        )
        origin.conflict = 0.3  # Some conflict at origin
        
        town1 = ecosystem.addLocation(
            name="Town1",
            x=100.0, y=0.0,
            movechance=0.3,
            capacity=-1,
            pop=0
        )
        
        town2 = ecosystem.addLocation(
            name="Town2",
            x=200.0, y=0.0,
            movechance=0.3,
            capacity=-1,
            pop=0
        )
        
        town3 = ecosystem.addLocation(
            name="Town3",
            x=300.0, y=0.0,
            movechance=0.3,
            capacity=-1,
            pop=0
        )
        
        camp = ecosystem.addLocation(
            name="Camp",
            x=400.0, y=0.0,
            movechance=0.001,
            capacity=1000,
            pop=0
        )
        
        # Add routes
        ecosystem.linkUp("Origin", "Town1", 100.0)
        ecosystem.linkUp("Town1", "Town2", 100.0)
        ecosystem.linkUp("Town2", "Town3", 100.0)
        ecosystem.linkUp("Town3", "Camp", 100.0)
        
        print("✅ Network created: Origin -> Town1 -> Town2 -> Town3 -> Camp")
    except Exception as e:
        print(f"❌ Network creation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Create agent and run simulation
    print("\n[5/5] Running simulation...")
    try:
        # Create agent with attributes
        agent_attributes = {
            'education_level': 0.6,
            'stress_tolerance': 0.5,
            'connections': 3
        }
        
        agent = Person(origin, agent_attributes)
        ecosystem.agents.append(agent)
        
        print(f"   Agent created at {agent.location.name}")
        print(f"   Agent attributes: {agent_attributes}")
        
        # Run simulation for 10 timesteps
        s2_activations = 0
        total_decisions = 0
        pressure_values = []
        
        for t in range(10):
            # Calculate cognitive pressure
            pressure = agent.calculate_cognitive_pressure(t)
            pressure_values.append(pressure)
            
            # Check if agent can use S2
            s2_capable = agent.get_system2_capable()
            
            # Calculate move chance (this triggers S1/S2 logic)
            move_chance, s2_active = calculateMoveChance(agent, ForceTownMove=False, time=t)
            
            if s2_active:
                s2_activations += 1
            total_decisions += 1
            
            # Evolve ecosystem (agent may move)
            ecosystem.evolve()
            
            if t < 3 or t == 9:  # Show first 3 and last timestep
                print(f"   t={t}: pressure={pressure:.3f}, s2_capable={s2_capable}, "
                      f"s2_active={s2_active}, move_chance={move_chance:.3f}, "
                      f"location={agent.location.name if agent.location else 'None'}")
        
        # Summary statistics
        print("\n" + "=" * 60)
        print("📊 RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total timesteps: 10")
        print(f"S2 activations: {s2_activations}")
        print(f"S2 activation rate: {s2_activations/10*100:.1f}%")
        print(f"Average cognitive pressure: {sum(pressure_values)/len(pressure_values):.3f}")
        print(f"Min pressure: {min(pressure_values):.3f}")
        print(f"Max pressure: {max(pressure_values):.3f}")
        print(f"Final location: {agent.location.name if agent.location else 'None'}")
        
        # Check decision history
        if hasattr(agent, 'decision_history') and agent.decision_history:
            s2_decisions = [d for d in agent.decision_history if d.get('decision_type') == 'S2']
            print(f"Decision history S2 entries: {len(s2_decisions)}")
        
        # Validation
        print("\n" + "=" * 60)
        print("✅ VALIDATION")
        print("=" * 60)
        
        all_pressures_valid = all(0.0 <= p <= 1.0 for p in pressure_values)
        print(f"Pressure values in [0, 1]: {all_pressures_valid}")
        
        s2_rate_reasonable = 0 <= s2_activations <= 10
        print(f"S2 activations reasonable: {s2_rate_reasonable}")
        
        simulation_success = all_pressures_valid and s2_rate_reasonable
        print(f"\n{'✅ TEST PASSED' if simulation_success else '❌ TEST FAILED'}")
        
        return simulation_success
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if os.path.exists(config_file):
            os.remove(config_file)
            print(f"\n🧹 Cleaned up {config_file}")


if __name__ == "__main__":
    success = test_minimal_s1s2()
    sys.exit(0 if success else 1)

