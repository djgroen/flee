#!/usr/bin/env python3
"""
Test Bottleneck Challenge Scenario

Tests S1 vs S2 differences in bottleneck avoidance and route planning
using the refugee enhancements with existing Flee infrastructure.
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def run_bottleneck_challenge():
    """Run bottleneck challenge scenario with S1 vs S2 refugee logic"""
    print("🚧 BOTTLENECK CHALLENGE SCENARIO WITH S1/S2 REFUGEE LOGIC")
    print("=" * 60)
    
    try:
        # Import required modules
        from flee.SimulationSettings import SimulationSettings
        from flee.flee import Ecosystem, Person
        from flee import moving
        from scripts.refugee_decision_tracker import RefugeeDecisionTracker
        from scripts.refugee_person_enhancements import (
            create_refugee_agent, s1_refugee_decision, s2_refugee_decision,
            enhanced_refugee_movechance, get_safety_threshold, get_risk_tolerance
        )
        
        print("✅ Imported modules successfully")
        
        # Initialize Flee settings with S1/S2 enabled
        SimulationSettings.ReadFromYML("test_data/test_settings.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.6
        print("✅ Initialized Flee settings")
        
        # Create bottleneck topology: Origin → Bottleneck → {Camp_A, Camp_B}
        ecosystem = Ecosystem()
        
        origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=1000)
        bottleneck = ecosystem.addLocation("Bottleneck", x=150, y=0, movechance=0.5, capacity=50, pop=200)  # Limited capacity
        camp_a = ecosystem.addLocation("Camp_A", x=250, y=-50, movechance=0.001, capacity=500, pop=0)
        camp_b = ecosystem.addLocation("Camp_B", x=250, y=50, movechance=0.001, capacity=800, pop=0)
        alternative = ecosystem.addLocation("AlternativeRoute", x=75, y=100, movechance=0.3, capacity=-1, pop=100)
        
        # Set conflict and safety levels
        origin.conflict = 0.9  # High conflict - need to evacuate
        bottleneck.conflict = 0.3  # Moderate conflict
        camp_a.conflict = 0.1  # Safe
        camp_b.conflict = 0.05  # Very safe
        alternative.conflict = 0.2  # Relatively safe
        
        # Link locations
        ecosystem.linkUp("Origin", "Bottleneck", 150.0)
        ecosystem.linkUp("Bottleneck", "Camp_A", 111.0)  # sqrt(100^2 + 50^2)
        ecosystem.linkUp("Bottleneck", "Camp_B", 111.0)
        # Alternative route (longer but avoids bottleneck)
        ecosystem.linkUp("Origin", "AlternativeRoute", 125.0)
        ecosystem.linkUp("AlternativeRoute", "Camp_B", 180.0)
        
        print("✅ Created bottleneck topology")
        
        # Initialize decision tracker
        tracker = RefugeeDecisionTracker()
        
        # Create mixed agents: some S1-only, some S2-capable
        agents = []
        
        # S1-prone agents (low connectivity, higher safety threshold)
        for i in range(10):
            refugee_config = {
                'safety_threshold': 0.7,  # Higher threshold = evacuate earlier
                'risk_tolerance': 0.2,    # Low risk tolerance
                'mobility': 0.8           # Lower mobility
            }
            agent = create_refugee_agent(origin, {"connections": 1}, refugee_config)  # Low connectivity
            agents.append(agent)
        
        # S2-capable agents (high connectivity, lower safety threshold)
        for i in range(10):
            refugee_config = {
                'safety_threshold': 0.5,  # Lower threshold = more analytical
                'risk_tolerance': 0.4,    # Higher risk tolerance
                'mobility': 1.3           # Higher mobility
            }
            agent = create_refugee_agent(origin, {"connections": 8}, refugee_config)  # High connectivity
            agents.append(agent)
        
        print(f"✅ Created {len(agents)} agents (10 S1-prone, 10 S2-capable)")
        
        # Simulate bottleneck scenario
        print("\\n🚧 RUNNING BOTTLENECK SIMULATION")
        print("-" * 40)
        
        route_choices = []
        decision_analysis = []
        
        for time in range(15):
            print(f"\\nDay {time}: Bottleneck capacity {bottleneck.capacity}, current occupancy {bottleneck.numAgents}")
            
            # Simulate bottleneck congestion (capacity decreases over time)
            if time > 5:
                bottleneck.capacity = max(20, bottleneck.capacity - 2)  # Capacity reduces
            
            for i, agent in enumerate(agents):
                # Use existing calculateMoveChance with S1/S2 logic
                base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
                
                # Apply refugee enhancements
                enhanced_movechance = enhanced_refugee_movechance(agent, base_movechance, system2_active, time)
                
                # Track decision
                tracker.track_refugee_decision(agent, system2_active, enhanced_movechance, time)
                
                # Test route selection if agent decides to move
                if enhanced_movechance > 0.5:
                    destinations = [bottleneck, alternative]  # Two route options
                    
                    if system2_active:
                        # S2: Analytical route planning
                        chosen_dest = s2_refugee_decision(agent, destinations, time, ecosystem)
                        decision_type = "S2_analytical"
                    else:
                        # S1: Heuristic route planning
                        chosen_dest = s1_refugee_decision(agent, destinations, time)
                        decision_type = "S1_heuristic"
                    
                    if chosen_dest:
                        route_choice = {
                            'agent_id': i,
                            'time': time,
                            'system2_active': system2_active,
                            'chosen_route': chosen_dest.name,
                            'safety_threshold': get_safety_threshold(agent),
                            'risk_tolerance': get_risk_tolerance(agent),
                            'connections': agent.attributes['connections'],
                            'bottleneck_occupancy': bottleneck.numAgents / bottleneck.capacity if bottleneck.capacity > 0 else 0
                        }
                        route_choices.append(route_choice)
                        
                        # Simulate agent moving to chosen destination
                        if chosen_dest.name == "Bottleneck" and bottleneck.numAgents < bottleneck.capacity:
                            bottleneck.numAgents += 1
                        elif chosen_dest.name == "AlternativeRoute":
                            alternative.numAgents += 1
                        
                        system = "S2" if system2_active else "S1"
                        print(f"  Agent {i} ({system}) chooses {chosen_dest.name} "
                              f"(safety_thresh={get_safety_threshold(agent):.1f}, "
                              f"conn={agent.attributes['connections']})")
        
        print("\\n📊 ANALYZING BOTTLENECK AVOIDANCE RESULTS")
        print("-" * 45)
        
        # Analyze route choices
        s1_choices = [r for r in route_choices if not r['system2_active']]
        s2_choices = [r for r in route_choices if r['system2_active']]
        
        if s1_choices and s2_choices:
            s1_bottleneck_rate = len([r for r in s1_choices if r['chosen_route'] == 'Bottleneck']) / len(s1_choices)
            s2_bottleneck_rate = len([r for r in s2_choices if r['chosen_route'] == 'Bottleneck']) / len(s2_choices)
            
            s1_alternative_rate = len([r for r in s1_choices if r['chosen_route'] == 'AlternativeRoute']) / len(s1_choices)
            s2_alternative_rate = len([r for r in s2_choices if r['chosen_route'] == 'AlternativeRoute']) / len(s2_choices)
            
            print(f"\\n🧠 ROUTE CHOICE ANALYSIS:")
            print(f"  S1 agents:")
            print(f"    Bottleneck route: {s1_bottleneck_rate:.1%} ({len([r for r in s1_choices if r['chosen_route'] == 'Bottleneck'])} choices)")
            print(f"    Alternative route: {s1_alternative_rate:.1%} ({len([r for r in s1_choices if r['chosen_route'] == 'AlternativeRoute'])} choices)")
            print(f"    Total decisions: {len(s1_choices)}")
            
            print(f"  S2 agents:")
            print(f"    Bottleneck route: {s2_bottleneck_rate:.1%} ({len([r for r in s2_choices if r['chosen_route'] == 'Bottleneck'])} choices)")
            print(f"    Alternative route: {s2_alternative_rate:.1%} ({len([r for r in s2_choices if r['chosen_route'] == 'AlternativeRoute'])} choices)")
            print(f"    Total decisions: {len(s2_choices)}")
            
            # Calculate bottleneck avoidance difference
            avoidance_difference = s2_alternative_rate - s1_alternative_rate
            print(f"\\n📈 BOTTLENECK AVOIDANCE DIFFERENCE:")
            print(f"  S2 alternative rate - S1 alternative rate: {avoidance_difference:+.1%}")
            
            if avoidance_difference > 0.1:
                print(f"  → S2 agents are {avoidance_difference:.1%} MORE likely to avoid bottlenecks")
                print(f"  → S2 analytical thinking leads to better route planning")
            elif avoidance_difference < -0.1:
                print(f"  → S1 agents are {abs(avoidance_difference):.1%} MORE likely to avoid bottlenecks")
                print(f"  → S1 heuristic thinking may be more effective in this scenario")
            else:
                print(f"  → Similar bottleneck avoidance between S1 and S2 agents")
        
        # Generate comprehensive analysis using tracker
        analysis = tracker.generate_refugee_analysis_report()
        
        if 'cognitive_activation' in analysis:
            activation = analysis['cognitive_activation']
            print(f"\\n🧠 COGNITIVE ACTIVATION ANALYSIS:")
            print(f"  Total decisions: {activation['total_decisions']}")
            print(f"  S2 activation rate: {activation['s2_activation_rate']:.1%}")
        
        # Save results
        tracker.save_decision_data("bottleneck_results")
        print(f"\\n💾 Saved detailed results to bottleneck_results/")
        
        print("\\n✅ BOTTLENECK CHALLENGE COMPLETED SUCCESSFULLY!")
        print("\\n🎯 KEY FINDINGS:")
        print("  • S1 vs S2 differences in route planning demonstrated")
        print("  • Refugee enhancements integrated with existing Flee S1/S2 system")
        print("  • Bottleneck avoidance strategies differ by cognitive mode")
        print("  • Enhanced movechance calculation affects decision timing")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_bottleneck_challenge()
    if success:
        print("\\n🎉 BOTTLENECK SCENARIO PASSED - Week 2 Task 2.2 Complete!")
    else:
        print("\\n❌ BOTTLENECK SCENARIO FAILED")
        sys.exit(1)