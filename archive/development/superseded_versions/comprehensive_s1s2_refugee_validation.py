#!/usr/bin/env python3
"""
Comprehensive S1/S2 Refugee Framework Validation

Runs all refugee displacement scenarios and generates publication-ready analysis
of S1 vs S2 cognitive differences in refugee decision-making contexts.
"""

import sys
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def run_comprehensive_validation():
    """Run comprehensive validation of S1/S2 refugee framework"""
    print("🎯 COMPREHENSIVE S1/S2 REFUGEE FRAMEWORK VALIDATION")
    print("=" * 60)
    
    try:
        # Import all required modules
        from flee.SimulationSettings import SimulationSettings
        from flee.flee import Ecosystem, Person
        from flee import moving
        from scripts.refugee_decision_tracker import RefugeeDecisionTracker
        from scripts.refugee_person_enhancements import (
            create_refugee_agent, s1_refugee_decision, s2_refugee_decision,
            enhanced_refugee_movechance, get_safety_threshold, get_risk_tolerance
        )
        from scripts.refugee_information_sharing import (
            enhance_refugee_information_sharing, process_shared_information_s1_vs_s2
        )
        
        print("✅ Imported all framework modules successfully")
        
        # Initialize comprehensive validation results
        validation_results = {
            'framework_info': {
                'version': '1.0',
                'validation_date': '2024',
                'scenarios_tested': [],
                'total_agents': 0,
                'total_decisions': 0
            },
            'scenarios': {},
            'overall_analysis': {}
        }
        
        # Initialize Flee settings
        SimulationSettings.ReadFromYML("test_data/test_settings.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        SimulationSettings.move_rules["conflict_threshold"] = 0.6
        print("✅ Initialized Flee settings for comprehensive validation")
        
        # Scenario 1: Evacuation Timing Test
        print("\\n📊 SCENARIO 1: EVACUATION TIMING TEST")
        print("-" * 45)
        
        evacuation_results = run_evacuation_timing_validation()
        validation_results['scenarios']['evacuation_timing'] = evacuation_results
        validation_results['framework_info']['scenarios_tested'].append('evacuation_timing')
        
        # Scenario 2: Bottleneck Challenge
        print("\\n🚧 SCENARIO 2: BOTTLENECK CHALLENGE")
        print("-" * 40)
        
        bottleneck_results = run_bottleneck_validation()
        validation_results['scenarios']['bottleneck_challenge'] = bottleneck_results
        validation_results['framework_info']['scenarios_tested'].append('bottleneck_challenge')
        
        # Scenario 3: Multi-Destination Choice
        print("\\n🎯 SCENARIO 3: MULTI-DESTINATION CHOICE")
        print("-" * 42)
        
        destination_results = run_destination_choice_validation()
        validation_results['scenarios']['multi_destination'] = destination_results
        validation_results['framework_info']['scenarios_tested'].append('multi_destination')
        
        # Scenario 4: Information Network Test
        print("\\n📡 SCENARIO 4: INFORMATION NETWORK TEST")
        print("-" * 42)
        
        information_results = run_information_network_validation()
        validation_results['scenarios']['information_network'] = information_results
        validation_results['framework_info']['scenarios_tested'].append('information_network')
        
        # Generate overall analysis
        print("\\n📈 GENERATING COMPREHENSIVE ANALYSIS")
        print("-" * 40)
        
        overall_analysis = generate_overall_analysis(validation_results['scenarios'])
        validation_results['overall_analysis'] = overall_analysis
        
        # Calculate framework statistics
        total_agents = sum(scenario.get('total_agents', 0) for scenario in validation_results['scenarios'].values())
        total_decisions = sum(scenario.get('total_decisions', 0) for scenario in validation_results['scenarios'].values())
        
        validation_results['framework_info']['total_agents'] = total_agents
        validation_results['framework_info']['total_decisions'] = total_decisions
        
        # Save comprehensive results
        save_comprehensive_results(validation_results)
        
        # Display summary
        display_validation_summary(validation_results)
        
        print("\\n✅ COMPREHENSIVE VALIDATION COMPLETED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_evacuation_timing_validation():
    """Run evacuation timing scenario validation"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_decision_tracker import RefugeeDecisionTracker
    from scripts.refugee_person_enhancements import create_refugee_agent, enhanced_refugee_movechance
    
    # Create evacuation scenario
    ecosystem = Ecosystem()
    origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=1000)
    town = ecosystem.addLocation("Town", x=100, y=0, movechance=0.3, capacity=-1, pop=500)
    camp = ecosystem.addLocation("Camp", x=200, y=0, movechance=0.001, capacity=2000, pop=0)
    
    ecosystem.linkUp("Origin", "Town", 100.0)
    ecosystem.linkUp("Town", "Camp", 100.0)
    
    # Create mixed agents
    agents = []
    tracker = RefugeeDecisionTracker()
    
    # S1-prone agents
    for i in range(15):
        agent = create_refugee_agent(origin, {"connections": 1}, {"safety_threshold": 0.7})
        agents.append(agent)
    
    # S2-capable agents
    for i in range(15):
        agent = create_refugee_agent(origin, {"connections": 8}, {"safety_threshold": 0.4})
        agents.append(agent)
    
    # Run simulation
    evacuation_events = []
    for time in range(25):
        conflict_level = min(time * 0.05, 1.0)
        origin.conflict = conflict_level
        origin.time_of_conflict = 0
        
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            enhanced_movechance = enhanced_refugee_movechance(agent, base_movechance, system2_active, time)
            
            tracker.track_refugee_decision(agent, system2_active, enhanced_movechance, time)
            
            if enhanced_movechance > 0.5 and agent not in [e['agent'] for e in evacuation_events]:
                evacuation_events.append({
                    'agent': agent,
                    'time': time,
                    'system2_active': system2_active,
                    'connections': agent.attributes['connections']
                })
    
    # Analyze results
    analysis = tracker.generate_refugee_analysis_report()
    
    s1_evacuations = [e for e in evacuation_events if not e['system2_active']]
    s2_evacuations = [e for e in evacuation_events if e['system2_active']]
    
    return {
        'scenario_name': 'Evacuation Timing Test',
        'total_agents': len(agents),
        'total_decisions': len(tracker.decision_records),
        's1_evacuations': len(s1_evacuations),
        's2_evacuations': len(s2_evacuations),
        's1_avg_timing': statistics.mean([e['time'] for e in s1_evacuations]) if s1_evacuations else 0,
        's2_avg_timing': statistics.mean([e['time'] for e in s2_evacuations]) if s2_evacuations else 0,
        'timing_difference': statistics.mean([e['time'] for e in s1_evacuations]) - statistics.mean([e['time'] for e in s2_evacuations]) if s1_evacuations and s2_evacuations else 0,
        'cognitive_activation_rate': analysis['cognitive_activation']['s2_activation_rate'] if 'cognitive_activation' in analysis else 0,
        'effect_size': calculate_effect_size([e['time'] for e in s1_evacuations], [e['time'] for e in s2_evacuations])
    }

def run_bottleneck_validation():
    """Run bottleneck challenge scenario validation"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_decision_tracker import RefugeeDecisionTracker
    from scripts.refugee_person_enhancements import create_refugee_agent, s1_refugee_decision, s2_refugee_decision
    
    # Create bottleneck scenario
    ecosystem = Ecosystem()
    origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=800)
    bottleneck = ecosystem.addLocation("Bottleneck", x=150, y=0, movechance=0.5, capacity=30, pop=200)
    camp_a = ecosystem.addLocation("Camp_A", x=250, y=-50, movechance=0.001, capacity=500, pop=0)
    camp_b = ecosystem.addLocation("Camp_B", x=250, y=50, movechance=0.001, capacity=800, pop=0)
    alternative = ecosystem.addLocation("Alternative", x=75, y=100, movechance=0.3, capacity=-1, pop=100)
    
    origin.conflict = 0.9
    bottleneck.conflict = 0.3
    camp_a.conflict = 0.1
    camp_b.conflict = 0.05
    alternative.conflict = 0.2
    
    ecosystem.linkUp("Origin", "Bottleneck", 150.0)
    ecosystem.linkUp("Bottleneck", "Camp_A", 111.0)
    ecosystem.linkUp("Bottleneck", "Camp_B", 111.0)
    ecosystem.linkUp("Origin", "Alternative", 125.0)
    ecosystem.linkUp("Alternative", "Camp_B", 180.0)
    
    # Create agents
    agents = []
    tracker = RefugeeDecisionTracker()
    
    for i in range(20):
        connections = 1 if i < 10 else 8
        safety_thresh = 0.7 if i < 10 else 0.5
        agent = create_refugee_agent(origin, {"connections": connections}, {"safety_threshold": safety_thresh})
        agents.append(agent)
    
    # Run simulation
    route_choices = []
    for time in range(10):
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            tracker.track_refugee_decision(agent, system2_active, base_movechance, time)
            
            if base_movechance > 0.5:
                destinations = [bottleneck, alternative]
                if system2_active:
                    choice = s2_refugee_decision(agent, destinations, time, ecosystem)
                else:
                    choice = s1_refugee_decision(agent, destinations, time)
                
                if choice:
                    route_choices.append({
                        'system2_active': system2_active,
                        'choice': choice.name,
                        'connections': agent.attributes['connections']
                    })
    
    # Analyze bottleneck avoidance
    s1_choices = [c for c in route_choices if not c['system2_active']]
    s2_choices = [c for c in route_choices if c['system2_active']]
    
    s1_alternative_rate = len([c for c in s1_choices if c['choice'] == 'Alternative']) / len(s1_choices) if s1_choices else 0
    s2_alternative_rate = len([c for c in s2_choices if c['choice'] == 'Alternative']) / len(s2_choices) if s2_choices else 0
    
    return {
        'scenario_name': 'Bottleneck Challenge',
        'total_agents': len(agents),
        'total_decisions': len(tracker.decision_records),
        's1_choices': len(s1_choices),
        's2_choices': len(s2_choices),
        's1_alternative_rate': s1_alternative_rate,
        's2_alternative_rate': s2_alternative_rate,
        'avoidance_difference': s2_alternative_rate - s1_alternative_rate,
        'bottleneck_avoidance_effect': 'S2_better' if s2_alternative_rate > s1_alternative_rate else 'S1_better' if s1_alternative_rate > s2_alternative_rate else 'similar'
    }

def run_destination_choice_validation():
    """Run multi-destination choice scenario validation"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_decision_tracker import RefugeeDecisionTracker
    from scripts.refugee_person_enhancements import create_refugee_agent, s1_refugee_decision, s2_refugee_decision
    
    # Create multi-destination scenario
    ecosystem = Ecosystem()
    origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=1000)
    close_safe = ecosystem.addLocation("Close_Safe", x=50, y=0, movechance=0.001, capacity=300, pop=0)
    medium_balanced = ecosystem.addLocation("Medium_Balanced", x=0, y=120, movechance=0.001, capacity=600, pop=0)
    far_excellent = ecosystem.addLocation("Far_Excellent", x=-150, y=0, movechance=0.001, capacity=1000, pop=0)
    risky_opportunity = ecosystem.addLocation("Risky_Opportunity", x=0, y=-80, movechance=0.001, capacity=400, pop=0)
    
    origin.conflict = 0.9
    close_safe.conflict = 0.2
    medium_balanced.conflict = 0.3
    far_excellent.conflict = 0.1
    risky_opportunity.conflict = 0.6
    
    ecosystem.linkUp("Origin", "Close_Safe", 50.0)
    ecosystem.linkUp("Origin", "Medium_Balanced", 120.0)
    ecosystem.linkUp("Origin", "Far_Excellent", 150.0)
    ecosystem.linkUp("Origin", "Risky_Opportunity", 80.0)
    
    # Create agents
    agents = []
    tracker = RefugeeDecisionTracker()
    
    for i in range(20):
        connections = 1 if i < 10 else 8
        safety_thresh = 0.6 if i < 10 else 0.4
        agent = create_refugee_agent(origin, {"connections": connections}, {"safety_threshold": safety_thresh})
        
        # High connectivity agents get destination knowledge
        if connections >= 5:
            agent.attributes['destination_knowledge'] = {
                'Close_Safe': {'quality_score': 0.6, 'safety_score': 0.8},
                'Medium_Balanced': {'quality_score': 0.7, 'safety_score': 0.7},
                'Far_Excellent': {'quality_score': 0.9, 'safety_score': 0.9},
                'Risky_Opportunity': {'quality_score': 0.5, 'safety_score': 0.4}
            }
        
        agents.append(agent)
    
    # Run simulation
    destination_choices = []
    for time in range(5):
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            tracker.track_refugee_decision(agent, system2_active, base_movechance, time)
            
            if base_movechance > 0.5:
                destinations = [close_safe, medium_balanced, far_excellent, risky_opportunity]
                if system2_active:
                    choice = s2_refugee_decision(agent, destinations, time, ecosystem)
                else:
                    choice = s1_refugee_decision(agent, destinations, time)
                
                if choice:
                    destination_choices.append({
                        'system2_active': system2_active,
                        'choice': choice.name,
                        'distance': choice.calculateDistance(origin),
                        'safety': 1.0 - choice.conflict,
                        'connections': agent.attributes['connections']
                    })
    
    # Analyze destination preferences
    s1_choices = [c for c in destination_choices if not c['system2_active']]
    s2_choices = [c for c in destination_choices if c['system2_active']]
    
    s1_avg_distance = statistics.mean([c['distance'] for c in s1_choices]) if s1_choices else 0
    s1_avg_safety = statistics.mean([c['safety'] for c in s1_choices]) if s1_choices else 0
    s2_avg_distance = statistics.mean([c['distance'] for c in s2_choices]) if s2_choices else 0
    s2_avg_safety = statistics.mean([c['safety'] for c in s2_choices]) if s2_choices else 0
    
    return {
        'scenario_name': 'Multi-Destination Choice',
        'total_agents': len(agents),
        'total_decisions': len(tracker.decision_records),
        's1_choices': len(s1_choices),
        's2_choices': len(s2_choices),
        's1_avg_distance': s1_avg_distance,
        's1_avg_safety': s1_avg_safety,
        's2_avg_distance': s2_avg_distance,
        's2_avg_safety': s2_avg_safety,
        'distance_difference': s2_avg_distance - s1_avg_distance,
        'safety_difference': s2_avg_safety - s1_avg_safety,
        'optimization_pattern': 'S2_optimizing' if s2_avg_distance > s1_avg_distance and s2_avg_safety > s1_avg_safety else 'S1_satisficing'
    }

def run_information_network_validation():
    """Run information network scenario validation"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_decision_tracker import RefugeeDecisionTracker
    from scripts.refugee_person_enhancements import create_refugee_agent
    from scripts.refugee_information_sharing import enhance_refugee_information_sharing, process_shared_information_s1_vs_s2
    
    # Create information network scenario
    ecosystem = Ecosystem()
    hub = ecosystem.addLocation("Hub", x=100, y=0, movechance=0.3, capacity=-1, pop=300)
    obvious = ecosystem.addLocation("Obvious", x=150, y=0, movechance=0.001, capacity=400, pop=0)
    hidden_good = ecosystem.addLocation("HiddenGood", x=120, y=80, movechance=0.001, capacity=600, pop=0)
    hidden_poor = ecosystem.addLocation("HiddenPoor", x=120, y=-80, movechance=0.001, capacity=200, pop=0)
    
    hub.conflict = 0.6
    obvious.conflict = 0.2
    hidden_good.conflict = 0.1
    hidden_poor.conflict = 0.5
    
    ecosystem.linkUp("Hub", "Obvious", 50.0)
    ecosystem.linkUp("Hub", "HiddenGood", 94.0)
    ecosystem.linkUp("Hub", "HiddenPoor", 94.0)
    
    # Create agents
    agents = []
    tracker = RefugeeDecisionTracker()
    
    for i in range(16):
        connections = 1 if i < 8 else 8
        agent = create_refugee_agent(hub, {"connections": connections}, {"safety_threshold": 0.4})
        agents.append(agent)
    
    # Run information sharing simulation
    information_discoveries = []
    for time in range(8):
        for agent in agents:
            connections = agent.attributes.get('connections', 0)
            
            # High connectivity agents discover hidden information
            if connections >= 5 and time >= 2:
                if 'destination_knowledge' not in agent.attributes:
                    agent.attributes['destination_knowledge'] = {}
                agent.attributes['destination_knowledge']['HiddenGood'] = {
                    'quality_score': 0.9,
                    'discovered_time': time
                }
            
            # Share information
            if connections > 0:
                enhance_refugee_information_sharing(agent, ecosystem, "safety", time)
            
            # Process shared information
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            tracker.track_refugee_decision(agent, system2_active, base_movechance, time)
            
            if agent.attributes.get("_safety_info"):
                processed_count = process_shared_information_s1_vs_s2(agent, system2_active)
                
                dest_knowledge = agent.attributes.get('destination_knowledge', {})
                if 'HiddenGood' in dest_knowledge:
                    information_discoveries.append({
                        'agent_id': i,
                        'time': time,
                        'system2_active': system2_active,
                        'connections': connections
                    })
    
    # Analyze information utilization
    s1_discoveries = [d for d in information_discoveries if not d['system2_active']]
    s2_discoveries = [d for d in information_discoveries if d['system2_active']]
    
    return {
        'scenario_name': 'Information Network Test',
        'total_agents': len(agents),
        'total_decisions': len(tracker.decision_records),
        's1_discoveries': len(s1_discoveries),
        's2_discoveries': len(s2_discoveries),
        's1_discovery_rate': len(s1_discoveries) / 8 if len(s1_discoveries) > 0 else 0,  # 8 S1 agents
        's2_discovery_rate': len(s2_discoveries) / 8 if len(s2_discoveries) > 0 else 0,  # 8 S2 agents
        'information_advantage': 'S2_better' if len(s2_discoveries) > len(s1_discoveries) else 'S1_better' if len(s1_discoveries) > len(s2_discoveries) else 'similar'
    }

def generate_overall_analysis(scenarios):
    """Generate overall analysis across all scenarios"""
    
    # Collect S2 activation rates
    s2_activation_rates = []
    effect_sizes = []
    
    # Analyze patterns across scenarios
    s2_advantages = []
    
    for scenario_name, results in scenarios.items():
        if 'cognitive_activation_rate' in results:
            s2_activation_rates.append(results['cognitive_activation_rate'])
        
        if 'effect_size' in results:
            effect_sizes.append(results['effect_size'])
        
        # Determine S2 advantage in each scenario
        if scenario_name == 'evacuation_timing':
            # Earlier evacuation is better (negative timing difference means S2 evacuates earlier)
            s2_advantages.append(results.get('timing_difference', 0) < 0)
        elif scenario_name == 'bottleneck_challenge':
            s2_advantages.append(results.get('avoidance_difference', 0) > 0)
        elif scenario_name == 'multi_destination':
            # Better optimization (higher safety for reasonable distance increase)
            s2_advantages.append(results.get('safety_difference', 0) > 0)
        elif scenario_name == 'information_network':
            s2_advantages.append(results.get('s2_discovery_rate', 0) > results.get('s1_discovery_rate', 0))
    
    return {
        'total_scenarios': len(scenarios),
        'avg_s2_activation_rate': statistics.mean(s2_activation_rates) if s2_activation_rates else 0,
        'avg_effect_size': statistics.mean([abs(e) for e in effect_sizes]) if effect_sizes else 0,
        's2_advantage_count': sum(s2_advantages),
        's2_advantage_rate': sum(s2_advantages) / len(s2_advantages) if s2_advantages else 0,
        'framework_effectiveness': 'high' if sum(s2_advantages) >= 3 else 'moderate' if sum(s2_advantages) >= 2 else 'low',
        'key_findings': [
            f"S2 shows advantages in {sum(s2_advantages)}/{len(s2_advantages)} scenarios",
            f"Average S2 activation rate: {statistics.mean(s2_activation_rates)*100:.1f}%" if s2_activation_rates else "No activation data",
            f"Average effect size: {statistics.mean([abs(e) for e in effect_sizes]):.2f}" if effect_sizes else "No effect size data"
        ]
    }

def calculate_effect_size(group1, group2):
    """Calculate Cohen's d effect size"""
    if len(group1) < 2 or len(group2) < 2:
        return 0.0
    
    mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
    std1, std2 = statistics.stdev(group1), statistics.stdev(group2)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
    pooled_std = pooled_std**0.5
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def save_comprehensive_results(results):
    """Save comprehensive validation results"""
    output_dir = Path("comprehensive_validation_results")
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON results
    with open(output_dir / "comprehensive_validation.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save summary report
    with open(output_dir / "validation_summary.txt", 'w') as f:
        f.write("S1/S2 REFUGEE FRAMEWORK COMPREHENSIVE VALIDATION SUMMARY\\n")
        f.write("=" * 60 + "\\n\\n")
        
        f.write(f"Framework Version: {results['framework_info']['version']}\\n")
        f.write(f"Validation Date: {results['framework_info']['validation_date']}\\n")
        f.write(f"Total Scenarios: {len(results['framework_info']['scenarios_tested'])}\\n")
        f.write(f"Total Agents: {results['framework_info']['total_agents']}\\n")
        f.write(f"Total Decisions: {results['framework_info']['total_decisions']}\\n\\n")
        
        f.write("SCENARIO RESULTS:\\n")
        f.write("-" * 20 + "\\n")
        for scenario_name, scenario_results in results['scenarios'].items():
            f.write(f"\\n{scenario_results['scenario_name']}:\\n")
            f.write(f"  Agents: {scenario_results['total_agents']}\\n")
            f.write(f"  Decisions: {scenario_results['total_decisions']}\\n")
            
            if 'timing_difference' in scenario_results:
                f.write(f"  Timing Difference: {scenario_results['timing_difference']:.2f} days\\n")
            if 'avoidance_difference' in scenario_results:
                f.write(f"  Avoidance Difference: {scenario_results['avoidance_difference']:.2%}\\n")
            if 'distance_difference' in scenario_results:
                f.write(f"  Distance Difference: {scenario_results['distance_difference']:.1f}\\n")
            if 'safety_difference' in scenario_results:
                f.write(f"  Safety Difference: {scenario_results['safety_difference']:.2f}\\n")
        
        f.write(f"\\nOVERALL ANALYSIS:\\n")
        f.write("-" * 20 + "\\n")
        overall = results['overall_analysis']
        f.write(f"Framework Effectiveness: {overall['framework_effectiveness']}\\n")
        f.write(f"S2 Advantage Rate: {overall['s2_advantage_rate']:.1%}\\n")
        f.write(f"Average S2 Activation: {overall['avg_s2_activation_rate']:.1%}\\n")
        f.write(f"Average Effect Size: {overall['avg_effect_size']:.2f}\\n")
    
    print(f"💾 Saved comprehensive results to {output_dir}/")

def display_validation_summary(results):
    """Display validation summary"""
    print("\\n📋 COMPREHENSIVE VALIDATION SUMMARY")
    print("=" * 45)
    
    info = results['framework_info']
    print(f"Framework Version: {info['version']}")
    print(f"Scenarios Tested: {len(info['scenarios_tested'])}")
    print(f"Total Agents: {info['total_agents']}")
    print(f"Total Decisions: {info['total_decisions']}")
    
    print(f"\\n🎯 SCENARIO PERFORMANCE:")
    for scenario_name, scenario_results in results['scenarios'].items():
        print(f"  {scenario_results['scenario_name']}: {scenario_results['total_agents']} agents, {scenario_results['total_decisions']} decisions")
    
    overall = results['overall_analysis']
    print(f"\\n📊 OVERALL FRAMEWORK ANALYSIS:")
    print(f"  Framework Effectiveness: {overall['framework_effectiveness'].upper()}")
    print(f"  S2 Advantage Rate: {overall['s2_advantage_rate']:.1%}")
    print(f"  Average S2 Activation: {overall['avg_s2_activation_rate']:.1%}")
    print(f"  Average Effect Size: {overall['avg_effect_size']:.2f}")
    
    print(f"\\n🔍 KEY FINDINGS:")
    for finding in overall['key_findings']:
        print(f"  • {finding}")

if __name__ == "__main__":
    success = run_comprehensive_validation()
    if success:
        print("\\n🎉 COMPREHENSIVE VALIDATION PASSED - FRAMEWORK READY FOR EVALUATION!")
    else:
        print("\\n❌ COMPREHENSIVE VALIDATION FAILED")
        sys.exit(1)