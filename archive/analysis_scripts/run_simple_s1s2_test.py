#!/usr/bin/env python3
"""
Simple S1/S2 experiment runner.

Runs experiments with different S2 threshold values and collects results.
"""

import sys
import os
import csv
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

def run_s1s2_experiment(s2_threshold=0.5, num_agents=10, num_timesteps=20, experiment_id="test"):
    """
    Run a single S1/S2 experiment.
    
    Args:
        s2_threshold: S2 activation threshold
        num_agents: Number of agents
        num_timesteps: Number of simulation timesteps
        experiment_id: Unique experiment identifier
    
    Returns:
        dict with results
    """
    
    print(f"\n🧪 Experiment: {experiment_id}")
    print(f"   S2 Threshold: {s2_threshold}")
    print(f"   Agents: {num_agents}, Timesteps: {num_timesteps}")
    
    try:
        from flee import flee
        from flee.SimulationSettings import SimulationSettings
        from flee.moving import calculateMoveChance
        from flee.flee import Person
        import yaml
        
        # Create configuration
        config = {
            'log_levels': {
                'agent': 0,
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
                'conflict_threshold': s2_threshold,
                'connectivity_mode': 'baseline',
                'steepness': 6.0
            },
            'optimisations': {
                'hasten': 1
            }
        }
        
        # Write config
        config_file = f'temp_config_{experiment_id}.yml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Initialize simulation
        SimulationSettings.ReadFromYML(config_file)
        ecosystem = flee.Ecosystem()
        
        # Create simple network: Origin -> Town1 -> Town2 -> Camp
        origin = ecosystem.addLocation(
            name="Origin",
            x=0.0, y=0.0,
            movechance=1.0,
            capacity=-1,
            pop=0
        )
        origin.conflict = 0.4  # Moderate conflict
        
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
        
        camp = ecosystem.addLocation(
            name="Camp",
            x=300.0, y=0.0,
            movechance=0.001,
            capacity=1000,
            pop=0
        )
        
        # Add routes
        ecosystem.linkUp("Origin", "Town1", 100.0)
        ecosystem.linkUp("Town1", "Town2", 100.0)
        ecosystem.linkUp("Town2", "Camp", 100.0)
        
        # Create agents with varied attributes
        agents = []
        for i in range(num_agents):
            attributes = {
                'education_level': 0.3 + (i % 5) * 0.15,  # 0.3 to 0.9
                'stress_tolerance': 0.2 + (i % 4) * 0.2,   # 0.2 to 0.8
                'connections': (i % 6)  # 0 to 5
            }
            agent = Person(origin, attributes)
            ecosystem.agents.append(agent)
            agents.append(agent)
        
        # Run simulation
        total_s2_activations = 0
        total_decisions = 0
        all_pressures = []
        s2_pressures = []
        
        for t in range(num_timesteps):
            for agent in agents:
                if agent.location is None:
                    continue
                
                # Calculate cognitive pressure
                pressure = agent.calculate_cognitive_pressure(t)
                all_pressures.append(pressure)
                
                # Calculate move chance (triggers S1/S2)
                move_chance, s2_active = calculateMoveChance(agent, ForceTownMove=False, time=t)
                
                if s2_active:
                    total_s2_activations += 1
                    s2_pressures.append(pressure)
                total_decisions += 1
            
            # Evolve ecosystem
            ecosystem.evolve()
        
        # Calculate statistics
        s2_rate = (total_s2_activations / total_decisions * 100) if total_decisions > 0 else 0.0
        avg_pressure = sum(all_pressures) / len(all_pressures) if all_pressures else 0.0
        avg_s2_pressure = sum(s2_pressures) / len(s2_pressures) if s2_pressures else 0.0
        
        # Count agents at camp
        agents_at_camp = sum(1 for a in agents if a.location and a.location.name == "Camp")
        
        results = {
            'experiment_id': experiment_id,
            's2_threshold': s2_threshold,
            'num_agents': num_agents,
            'num_timesteps': num_timesteps,
            's2_activations': total_s2_activations,
            'total_decisions': total_decisions,
            's2_activation_rate': s2_rate,
            'avg_cognitive_pressure': avg_pressure,
            'avg_s2_pressure': avg_s2_pressure,
            'agents_at_camp': agents_at_camp,
            'agents_at_camp_pct': (agents_at_camp / num_agents * 100) if num_agents > 0 else 0.0
        }
        
        print(f"   ✅ Complete: S2 rate = {s2_rate:.1f}%, Avg pressure = {avg_pressure:.3f}")
        
        # Cleanup
        if os.path.exists(config_file):
            os.remove(config_file)
        
        return results
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run multiple experiments with different S2 thresholds"""
    
    print("=" * 60)
    print("S1/S2 Simple Experiment Runner")
    print("=" * 60)
    
    # Experiment configurations
    experiments = [
        {'s2_threshold': 0.0, 'id': 'baseline_low'},
        {'s2_threshold': 0.3, 'id': 'medium_low'},
        {'s2_threshold': 0.5, 'id': 'medium'},
        {'s2_threshold': 0.7, 'id': 'medium_high'},
        {'s2_threshold': 1.0, 'id': 'high'},
    ]
    
    results = []
    
    for exp_config in experiments:
        result = run_s1s2_experiment(
            s2_threshold=exp_config['s2_threshold'],
            num_agents=10,
            num_timesteps=20,
            experiment_id=exp_config['id']
        )
        
        if result:
            results.append(result)
    
    # Save results
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as CSV
        csv_file = f's1s2_results_{timestamp}.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\n📊 Results saved to: {csv_file}")
        
        # Save as JSON
        json_file = f's1s2_results_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📊 Results saved to: {json_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📈 SUMMARY")
        print("=" * 60)
        print(f"{'S2 Threshold':<15} {'S2 Rate %':<12} {'Avg Pressure':<15} {'At Camp %':<12}")
        print("-" * 60)
        for r in results:
            print(f"{r['s2_threshold']:<15.1f} {r['s2_activation_rate']:<12.1f} "
                  f"{r['avg_cognitive_pressure']:<15.3f} {r['agents_at_camp_pct']:<12.1f}")
    
    print("\n✅ All experiments complete!")


if __name__ == "__main__":
    main()

