#!/usr/bin/env python3
"""
S1/S2 Refugee Framework Visualization Suite

Creates publication-ready plots demonstrating S1 vs S2 cognitive differences
in refugee displacement scenarios.
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any

# Set up plotting style
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 11

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import plotting functions
from s1s2_plotting_functions import (
    create_evacuation_timing_plot,
    create_bottleneck_avoidance_plot,
    create_destination_choice_plot,
    create_information_utilization_plot,
    create_cognitive_activation_plot,
    create_framework_summary_plot
)

def create_comprehensive_plots():
    """Create comprehensive S1/S2 refugee framework visualization plots"""
    print("📊 CREATING S1/S2 REFUGEE FRAMEWORK VISUALIZATION PLOTS")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("s1s2_refugee_plots")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Run scenarios and collect data for plotting
        print("🔄 Running scenarios to collect plotting data...")
        
        evacuation_data = collect_evacuation_timing_data()
        bottleneck_data = collect_bottleneck_data()
        destination_data = collect_destination_choice_data()
        information_data = collect_information_network_data()
        
        print("✅ Data collection completed")
        
        # Create individual scenario plots
        print("\n📈 Creating scenario-specific plots...")
        
        create_evacuation_timing_plot(evacuation_data, output_dir)
        create_bottleneck_avoidance_plot(bottleneck_data, output_dir)
        create_destination_choice_plot(destination_data, output_dir)
        create_information_utilization_plot(information_data, output_dir)     
   
        # Create comprehensive comparison plots
        print("\n📊 Creating comprehensive comparison plots...")
        
        create_cognitive_activation_plot(evacuation_data, bottleneck_data, destination_data, information_data, output_dir)
        create_framework_summary_plot(evacuation_data, bottleneck_data, destination_data, information_data, output_dir)
        
        print(f"\n✅ All plots saved to {output_dir}/")
        print("\n🎯 PLOT SUMMARY:")
        print("  • evacuation_timing_comparison.png - S1 vs S2 evacuation timing")
        print("  • bottleneck_avoidance_analysis.png - Route planning differences")
        print("  • destination_choice_patterns.png - Satisficing vs optimizing behavior")
        print("  • information_utilization.png - Network information effects")
        print("  • cognitive_activation_patterns.png - System 2 activation analysis")
        print("  • framework_summary_dashboard.png - Comprehensive overview")
        
        return True
        
    except Exception as e:
        print(f"❌ Plot creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def collect_evacuation_timing_data():
    """Collect evacuation timing data for plotting"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_decision_tracker import RefugeeDecisionTracker
    from scripts.refugee_person_enhancements import create_refugee_agent, enhanced_refugee_movechance
    
    # Initialize settings
    SimulationSettings.ReadFromYML("test_data/test_settings.yml")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    
    # Create scenario
    ecosystem = Ecosystem()
    origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=1000)
    town = ecosystem.addLocation("Town", x=100, y=0, movechance=0.3, capacity=-1, pop=500)
    camp = ecosystem.addLocation("Camp", x=200, y=0, movechance=0.001, capacity=2000, pop=0)
    
    ecosystem.linkUp("Origin", "Town", 100.0)
    ecosystem.linkUp("Town", "Camp", 100.0)
    
    # Create agents
    agents = []
    tracker = RefugeeDecisionTracker()
    
    # S1-prone agents
    for i in range(20):
        agent = create_refugee_agent(origin, {"connections": 1}, {"safety_threshold": 0.7})
        agents.append(agent)
    
    # S2-capable agents
    for i in range(20):
        agent = create_refugee_agent(origin, {"connections": 8}, {"safety_threshold": 0.4})
        agents.append(agent)
    
    # Run simulation
    evacuation_events = []
    cognitive_pressure_data = [] 
   
    for time in range(30):
        conflict_level = min(time * 0.05, 1.0)
        origin.conflict = conflict_level
        origin.time_of_conflict = 0
        
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            enhanced_movechance = enhanced_refugee_movechance(agent, base_movechance, system2_active, time)
            cognitive_pressure = agent.calculate_cognitive_pressure(time)
            
            # Track cognitive pressure over time
            cognitive_pressure_data.append({
                'time': time,
                'cognitive_pressure': cognitive_pressure,
                'system2_active': system2_active,
                'connections': agent.attributes['connections'],
                'conflict_level': conflict_level
            })
            
            tracker.track_refugee_decision(agent, system2_active, enhanced_movechance, time)
            
            if enhanced_movechance > 0.5 and agent not in [e['agent'] for e in evacuation_events]:
                evacuation_events.append({
                    'agent': agent,
                    'time': time,
                    'system2_active': system2_active,
                    'connections': agent.attributes['connections'],
                    'safety_threshold': agent.attributes['safety_threshold'],
                    'conflict_level': conflict_level
                })
    
    return {
        'evacuation_events': evacuation_events,
        'cognitive_pressure_data': cognitive_pressure_data,
        'tracker': tracker
    }

def collect_bottleneck_data():
    """Collect bottleneck avoidance data for plotting"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_person_enhancements import create_refugee_agent, s1_refugee_decision, s2_refugee_decision
    
    # Initialize settings
    SimulationSettings.ReadFromYML("test_data/test_settings.yml")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    
    # Create bottleneck scenario
    ecosystem = Ecosystem()
    origin = ecosystem.addLocation("Origin", x=0, y=0, movechance=1.0, capacity=-1, pop=800)
    bottleneck = ecosystem.addLocation("Bottleneck", x=150, y=0, movechance=0.5, capacity=50, pop=200)
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
    for i in range(30):
        connections = 1 if i < 15 else 8
        safety_thresh = 0.7 if i < 15 else 0.5
        agent = create_refugee_agent(origin, {"connections": connections}, {"safety_threshold": safety_thresh})
        agents.append(agent)
    
    # Run simulation
    route_choices = []
    capacity_over_time = []
    
    for time in range(15):
        # Track bottleneck capacity over time
        capacity_over_time.append({
            'time': time,
            'capacity': bottleneck.capacity,
            'occupancy': bottleneck.numAgents,
            'occupancy_rate': bottleneck.numAgents / bottleneck.capacity if bottleneck.capacity > 0 else 0
        })
        
        # Reduce capacity over time to simulate congestion
        if time > 5:
            bottleneck.capacity = max(20, bottleneck.capacity - 2)
        
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            
            if base_movechance > 0.5:
                destinations = [bottleneck, alternative]
                if system2_active:
                    choice = s2_refugee_decision(agent, destinations, time, ecosystem)
                else:
                    choice = s1_refugee_decision(agent, destinations, time)
                
                if choice:
                    route_choices.append({
                        'time': time,
                        'system2_active': system2_active,
                        'choice': choice.name,
                        'connections': agent.attributes['connections'],
                        'bottleneck_occupancy': bottleneck.numAgents / bottleneck.capacity if bottleneck.capacity > 0 else 0
                    })
                    
                    # Simulate movement
                    if choice.name == "Bottleneck" and bottleneck.numAgents < bottleneck.capacity:
                        bottleneck.numAgents += 1
                    elif choice.name == "Alternative":
                        alternative.numAgents += 1
    
    return {
        'route_choices': route_choices,
        'capacity_over_time': capacity_over_time
    }

def collect_destination_choice_data():
    """Collect destination choice data for plotting"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_person_enhancements import create_refugee_agent, s1_refugee_decision, s2_refugee_decision
    
    # Initialize settings
    SimulationSettings.ReadFromYML("test_data/test_settings.yml")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    
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
    for i in range(40):
        connections = 1 if i < 20 else 8
        safety_thresh = 0.6 if i < 20 else 0.4
        agent = create_refugee_agent(origin, {"connections": connections}, {"safety_threshold": safety_thresh})
        
        # High connectivity agents get destination knowledge
        if connections >= 5:
            agent.attributes['destination_knowledge'] = {
                'Close_Safe': {'quality_score': 0.6, 'safety_score': 0.8, 'distance_score': 1.0},
                'Medium_Balanced': {'quality_score': 0.7, 'safety_score': 0.7, 'distance_score': 0.7},
                'Far_Excellent': {'quality_score': 0.9, 'safety_score': 0.9, 'distance_score': 0.3},
                'Risky_Opportunity': {'quality_score': 0.5, 'safety_score': 0.4, 'distance_score': 0.6}
            }
        
        agents.append(agent)
    
    # Run simulation
    destination_choices = []
    
    for time in range(8):
        for agent in agents:
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            
            if base_movechance > 0.5:
                destinations = [close_safe, medium_balanced, far_excellent, risky_opportunity]
                if system2_active:
                    choice = s2_refugee_decision(agent, destinations, time, ecosystem)
                else:
                    choice = s1_refugee_decision(agent, destinations, time)
                
                if choice:
                    destination_choices.append({
                        'time': time,
                        'system2_active': system2_active,
                        'choice': choice.name,
                        'distance': choice.calculateDistance(origin),
                        'safety': 1.0 - choice.conflict,
                        'connections': agent.attributes['connections'],
                        'has_knowledge': len(agent.attributes.get('destination_knowledge', {})) > 0
                    })
    
    return {
        'destination_choices': destination_choices,
        'destinations': {
            'Close_Safe': {'distance': 50, 'safety': 0.8, 'quality': 0.6},
            'Medium_Balanced': {'distance': 120, 'safety': 0.7, 'quality': 0.7},
            'Far_Excellent': {'distance': 150, 'safety': 0.9, 'quality': 0.9},
            'Risky_Opportunity': {'distance': 80, 'safety': 0.4, 'quality': 0.5}
        }
    }

def collect_information_network_data():
    """Collect information network data for plotting"""
    from flee.SimulationSettings import SimulationSettings
    from flee.flee import Ecosystem
    from flee import moving
    from scripts.refugee_person_enhancements import create_refugee_agent
    from scripts.refugee_information_sharing import enhance_refugee_information_sharing, process_shared_information_s1_vs_s2
    
    # Initialize settings
    SimulationSettings.ReadFromYML("test_data/test_settings.yml")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    
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
    for i in range(20):
        connections = 1 if i < 10 else 8
        agent = create_refugee_agent(hub, {"connections": connections}, {"safety_threshold": 0.4})
        agents.append(agent)
    
    # Run information sharing simulation
    information_discoveries = []
    information_sharing_events = []
    
    for time in range(12):
        for agent in agents:
            connections = agent.attributes.get('connections', 0)
            
            # High connectivity agents discover hidden information
            if connections >= 5 and time >= 2:
                if 'destination_knowledge' not in agent.attributes:
                    agent.attributes['destination_knowledge'] = {}
                
                # Simulate gradual information discovery
                if time >= 3 and 'HiddenGood' not in agent.attributes['destination_knowledge']:
                    agent.attributes['destination_knowledge']['HiddenGood'] = {
                        'quality_score': 0.9,
                        'discovered_time': time,
                        'discovery_method': 'network'
                    }
                    
                    information_discoveries.append({
                        'time': time,
                        'agent_id': len([a for a in agents if a == agent]),
                        'connections': connections,
                        'discovery_type': 'HiddenGood'
                    })   
         
            # Share information
            if connections > 0:
                enhance_refugee_information_sharing(agent, ecosystem, "safety", time)
                information_sharing_events.append({
                    'time': time,
                    'agent_connections': connections,
                    'shared_info': len(agent.attributes.get('_safety_info', {}))
                })
            
            # Process shared information
            base_movechance, system2_active = moving.calculateMoveChance(agent, False, time)
            
            if agent.attributes.get("_safety_info"):
                processed_count = process_shared_information_s1_vs_s2(agent, system2_active)
    
    return {
        'information_discoveries': information_discoveries,
        'information_sharing_events': information_sharing_events
    }

if __name__ == "__main__":
    success = create_comprehensive_plots()
    if success:
        print("\n🎉 S1/S2 refugee framework visualization plots created successfully!")
    else:
        print("\n❌ Failed to create visualization plots")
        sys.exit(1)