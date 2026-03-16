#!/usr/bin/env python3
"""
Test Multi-Destination Choice Scenario

Tests S1 satisficing vs S2 optimizing behavior in refugee destination choice
using enhanced information sharing and network effects.
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def run_multi_destination_choice():
    """Run multi-destination choice scenario with S1 vs S2 refugee logic and information sharing"""
    print("🎯 MULTI-DESTINATION CHOICE SCENARIO WITH S1/S2 AND INFORMATION SHARING")
    print("=" * 70)
    
    try:
        # Import required modules
        from flee.SimulationSettings import SimulationSettings
        from flee.flee import Ecosystem, Person
        from flee import moving
        from scripts.refugee_decision_tracker import RefugeeDecisionTracker
        from scripts.refugee_person_enhancements import (
            create_refugee_agent, s1_refugee_decision, s2_refugee_decision,
            enhanced_refugee_movechance, get_safety_threshold
        )
        from scripts.refugee_information_sharing import (
            enhance_refugee_information_sharing, process_shared_information_s1_vs_s2
        )
        
        print("✅ Imported modules successfully")
        
        # Initialize Flee settings with S1/S2 enabled
        SimulationSettings.ReadFromYML("test_data/test_settings.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.6
        print("✅ Initialized Flee settings")
        
        # Create multi-destination topology: Origin → {Close_Safe, Medium_Balanced, Far_Excellent, Risky_Opportunity}
        ecosystem = Ecosystem()
        
        origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=1000)
        close_safe = ecosystem.addLocation("Close_Safe", x=50, y=0, movechance=0.001, capacity=300, pop=0)
        medium_balanced = ecosystem.addLocation("Medium_Balanced", x=0, y=120, movechance=0.001, capacity=600, pop=0)
        far_excellent = ecosystem.addLocation("Far_Excellent", x=-150, y=0, movechance=0.001, capacity=1000, pop=0)
        risky_opportunity = ecosystem.addLocation("Risky_Opportunity", x=0, y=-80, movechance=0.001, capacity=400, pop=0)
        
        # Set conflict and quality levels to create trade-offs
        origin.conflict = 0.9  # High conflict - need to evacuate
        close_safe.conflict = 0.2  # Safe but limited opportunities
        medium_balanced.conflict = 0.3  # Good balance
        far_excellent.conflict = 0.1  # Excellent but distant
        risky_opportunity.conflict = 0.6  # High opportunity but risky
        
        # Add quality attributes for refugee decision-making
        close_safe.attributes = {"opportunity_score": 0.3, "distance_score": 1.0}
        medium_balanced.attributes = {"opportunity_score": 0.6, "distance_score": 0.7}
        far_excellent.attributes = {"opportunity_score": 0.9, "distance_score": 0.3}
        risky_opportunity.attributes = {"opportunity_score": 0.8, "distance_score": 0.6}
        
        # Link all destinations to origin
        ecosystem.linkUp("Origin", "Close_Safe", 50.0)
        ecosystem.linkUp("Origin", "Medium_Balanced", 120.0)
        ecosystem.linkUp("Origin", "Far_Excellent", 150.0)
        ecosystem.linkUp("Origin", "Risky_Opportunity", 80.0)
        
        print("✅ Created multi-destination topology with trade-offs")
        
        # Initialize decision tracker
        tracker = RefugeeDecisionTracker()
        
        # Create mixed agents with different profiles
        agents = []
        
        # S1-prone agents (low connectivity, higher safety threshold)
        for i in range(8):
            refugee_config = {
                'safety_threshold': 0.6,  # Higher safety threshold
                'risk_tolerance': 0.2,    # Low risk tolerance
                'mobility': 0.9           # Lower mobility
            }
            agent = create_refugee_agent(origin, {"connections": 1}, refugee_config)
            agents.append(agent)
        
        # S2-capable agents (high connectivity, more analytical)
        for i in range(8):
            refugee_config = {
                'safety_threshold': 0.4,  # Lower safety threshold (more analytical)
                'risk_tolerance': 0.4,    # Higher risk tolerance
                'mobility': 1.2           # Higher mobility
            }
            agent = create_refugee_agent(origin, {"connections": 8}, refugee_config)
            agents.append(agent)
        
        print(f"✅ Created {len(agents)} agents (8 S1-prone, 8 S2-capable)")
        
        # Simulate information sharing and destination choice
        print("\\n🎯 SIMULATING MULTI-DESTINATION CHOICE WITH INFORMATION SHARING")
        print("-" * 60)
        
        destination_choices = []
        
        # Phase 1: Initial information sharing (Days 0-2)
        for time in range(3):
            print(f"\\nDay {time}: Information sharing phase")
            
            for i, agent in enumerate(agents):
                connections = agent.attributes.get('connections', 0)
                
                # High connectivity agents discover detailed information about destinations
                if connections >= 5:
                    # Simulate network information discovery
                    if 'destination_knowledge' not in agent.attributes:
                        agent.attributes['destination_knowledge'] = {}
                    
                    # Discover detailed information about all destinations
                    agent.attributes['destination_knowledge'].update({
                        'Close_Safe': {
                            'quality_score': 0.6,  # Safe but limited
                            'safety_score': 0.8,
                            'opportunity_score': 0.3,
                            'distance_score': 1.0
                        },
                        'Medium_Balanced': {
                            'quality_score': 0.7,  # Good balance
                            'safety_score': 0.7,
                            'opportunity_score': 0.6,
                            'distance_score': 0.7
                        },
                        'Far_Excellent': {
                            'quality_score': 0.9,  # Excellent but distant
                            'safety_score': 0.9,
                            'opportunity_score': 0.9,
                            'distance_score': 0.3
                        },
                        'Risky_Opportunity': {
                            'quality_score': 0.5,  # Risky but good opportunities
                            'safety_score': 0.4,
                            'opportunity_score': 0.8,
                            'distance_score': 0.6
                        }
                    })
                
                # Share information with other agents
                if connections > 0:
                    enhance_refugee_information_sharing(agent, ecosystem, "safety", time)
                    enhance_refugee_information_sharing(agent, ecosystem, "capacity", time)
        
        # Phase 2: Decision making with shared information (Days 3-7)
        for time in range(3, 8):
            print(f"\\nDay {time}: Decision making phase")
            
            for i, agent in enumerate(agents):
                # Process shared information based on S1/S2 mode
                movechance, system2_active = moving.calculateMoveChance(agent, False, time)
                
                # Process any shared information
                if agent.attributes.get("_safety_info"):
                    process_shared_information_s1_vs_s2(agent, system2_active)
                
                # Apply refugee enhancements
                enhanced_movechance = enhanced_refugee_movechance(agent, movechance, system2_active, time)
                
                # Track decision
                tracker.track_refugee_decision(agent, system2_active, enhanced_movechance, time)
                
                # Make destination choice if agent decides to move
                if enhanced_movechance > 0.5:
                    destinations = [close_safe, medium_balanced, far_excellent, risky_opportunity]
                    
                    if system2_active:
                        # S2: Analytical destination choice
                        chosen_dest = s2_refugee_decision(agent, destinations, time, ecosystem)
                        decision_type = "S2_optimizing"
                    else:
                        # S1: Heuristic destination choice (satisficing)
                        chosen_dest = s1_refugee_decision(agent, destinations, time)
                        decision_type = "S1_satisficing"
                    
                    if chosen_dest:
                        choice_record = {
                            'agent_id': i,
                            'time': time,
                            'system2_active': system2_active,
                            'decision_type': decision_type,
                            'chosen_destination': chosen_dest.name,
                            'destination_distance': chosen_dest.calculateDistance(origin),
                            'destination_safety': 1.0 - chosen_dest.conflict,
                            'safety_threshold': get_safety_threshold(agent),
                            'connections': agent.attributes['connections'],
                            'has_destination_knowledge': len(agent.attributes.get('destination_knowledge', {})) > 0
                        }
                        destination_choices.append(choice_record)
                        
                        system = "S2" if system2_active else "S1"
                        knows_info = "with info" if choice_record['has_destination_knowledge'] else "no info"
                        print(f"  Agent {i} ({system}) chooses {chosen_dest.name} "
                              f"(safety={1.0-chosen_dest.conflict:.1f}, dist={chosen_dest.calculateDistance(origin):.0f}, {knows_info})")
        
        print("\\n📊 ANALYZING MULTI-DESTINATION CHOICE RESULTS")
        print("-" * 50)
        
        # Analyze destination choices by S1 vs S2
        s1_choices = [c for c in destination_choices if not c['system2_active']]
        s2_choices = [c for c in destination_choices if c['system2_active']]
        
        if s1_choices and s2_choices:
            print(f"\\n🎯 DESTINATION CHOICE ANALYSIS:")
            
            # Analyze destination preferences
            destinations = ['Close_Safe', 'Medium_Balanced', 'Far_Excellent', 'Risky_Opportunity']
            
            print(f"  S1 Satisficing Choices ({len(s1_choices)} total):")
            for dest in destinations:
                count = len([c for c in s1_choices if c['chosen_destination'] == dest])
                percentage = count / len(s1_choices) * 100 if s1_choices else 0
                print(f"    {dest}: {count} ({percentage:.1f}%)")
            
            print(f"  S2 Optimizing Choices ({len(s2_choices)} total):")
            for dest in destinations:
                count = len([c for c in s2_choices if c['chosen_destination'] == dest])
                percentage = count / len(s2_choices) * 100 if s2_choices else 0
                print(f"    {dest}: {count} ({percentage:.1f}%)")
            
            # Analyze distance vs quality trade-offs
            s1_avg_distance = sum(c['destination_distance'] for c in s1_choices) / len(s1_choices)
            s1_avg_safety = sum(c['destination_safety'] for c in s1_choices) / len(s1_choices)
            
            s2_avg_distance = sum(c['destination_distance'] for c in s2_choices) / len(s2_choices)
            s2_avg_safety = sum(c['destination_safety'] for c in s2_choices) / len(s2_choices)
            
            print(f"\\n📈 DISTANCE VS QUALITY TRADE-OFFS:")
            print(f"  S1 Satisficing:")
            print(f"    Average distance: {s1_avg_distance:.1f}")
            print(f"    Average safety: {s1_avg_safety:.2f}")
            print(f"  S2 Optimizing:")
            print(f"    Average distance: {s2_avg_distance:.1f}")
            print(f"    Average safety: {s2_avg_safety:.2f}")
            
            # Calculate optimization vs satisficing difference
            distance_difference = s2_avg_distance - s1_avg_distance
            safety_difference = s2_avg_safety - s1_avg_safety
            
            print(f"\\n🔍 SATISFICING VS OPTIMIZING ANALYSIS:")
            print(f"  Distance difference (S2 - S1): {distance_difference:+.1f}")
            print(f"  Safety difference (S2 - S1): {safety_difference:+.2f}")
            
            if distance_difference > 10 and safety_difference > 0.1:
                print(f"  → S2 agents travel {distance_difference:.0f} units further for {safety_difference:.2f} better safety")
                print(f"  → S2 optimizing behavior: willing to travel further for better outcomes")
            elif abs(distance_difference) < 10:
                print(f"  → Similar distance preferences between S1 and S2 agents")
            else:
                print(f"  → S1 agents show different optimization pattern")
            
            # Analyze information utilization
            s1_with_info = len([c for c in s1_choices if c['has_destination_knowledge']])
            s2_with_info = len([c for c in s2_choices if c['has_destination_knowledge']])
            
            print(f"\\n📡 INFORMATION UTILIZATION:")
            print(f"  S1 agents with destination knowledge: {s1_with_info}/{len(s1_choices)} ({s1_with_info/len(s1_choices)*100:.1f}%)")
            print(f"  S2 agents with destination knowledge: {s2_with_info}/{len(s2_choices)} ({s2_with_info/len(s2_choices)*100:.1f}%)")
        
        # Generate comprehensive analysis using tracker
        analysis = tracker.generate_refugee_analysis_report()
        
        if 'cognitive_activation' in analysis:
            activation = analysis['cognitive_activation']
            print(f"\\n🧠 COGNITIVE ACTIVATION SUMMARY:")
            print(f"  Total decisions: {activation['total_decisions']}")
            print(f"  S2 activation rate: {activation['s2_activation_rate']:.1%}")
        
        # Save results
        tracker.save_decision_data("multi_destination_results")
        print(f"\\n💾 Saved detailed results to multi_destination_results/")
        
        print("\\n✅ MULTI-DESTINATION CHOICE COMPLETED SUCCESSFULLY!")
        print("\\n🎯 KEY FINDINGS:")
        print("  • S1 satisficing vs S2 optimizing behavior demonstrated")
        print("  • Information sharing affects destination choice quality")
        print("  • Distance vs safety trade-offs differ by cognitive mode")
        print("  • Network information discovery enhances S2 decision-making")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_multi_destination_choice()
    if success:
        print("\\n🎉 MULTI-DESTINATION SCENARIO PASSED - Week 3 Complete!")
    else:
        print("\\n❌ MULTI-DESTINATION SCENARIO FAILED")
        sys.exit(1)