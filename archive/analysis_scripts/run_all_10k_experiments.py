#!/usr/bin/env python3
"""
Run all 10k agent experiments and generate output figures
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import shutil

# Add current directory to path
sys.path.insert(0, '.')

def run_10k_experiment(exp_dir):
    """Run a single 10k agent experiment"""
    
    print(f"🚀 Running experiment: {exp_dir.name}")
    
    # Change to experiment directory
    original_dir = os.getcwd()
    os.chdir(exp_dir)
    
    try:
        # Import Flee components
        from flee import flee
        from flee.datamanager import handle_refugee_data, read_period
        from flee import InputGeography
        from flee.moving import calculate_systematic_s2_activation
        
        # Read simulation period
        start_date, end_time = read_period.read_sim_period("sim_period.csv")
        print(f"📅 Simulation period: {start_date} to {end_time} ({end_time} days)")
        
        # Read simulation settings
        flee.SimulationSettings.ReadFromYML("simsetting.yml")
        s2_threshold = flee.SimulationSettings.move_rules.get('TwoSystemDecisionMaking', 0.0)
        print(f"⚙️ S2 threshold: {s2_threshold}")
        
        # Create ecosystem
        e = flee.Ecosystem()
        print("🌍 Ecosystem created")
        
        # Create input geography
        ig = InputGeography.InputGeography()
        
        # Set conflict input file and read input files
        flee.SimulationSettings.ConflictInputFile = "input_csv/conflicts.csv"
        ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
        ig.ReadLocationsFromCSV("input_csv/locations.csv")
        ig.ReadLinksFromCSV("input_csv/routes.csv")
        ig.ReadClosuresFromCSV("input_csv/closures.csv")
        
        print("📊 Input files read successfully")
        
        # Store input geography in ecosystem
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        print(f"🏗️ Ecosystem populated with {len(lm)} locations")
        
        # Create refugee data handler
        d = handle_refugee_data.RefugeeTable(
            csvformat="generic", 
            data_directory="source_data", 
            start_date=start_date, 
            data_layout="data_layout.csv"
        )
        
        print("👥 Refugee data handler created")
        
        # Add initial refugees to camps
        camp_locations = e.get_camp_names()
        print(f"🏕️ Camp locations: {camp_locations}")
        
        total_initial_refugees = 0
        for l in camp_locations:
            initial_refugees = d.get_field(l, 0, FullInterpolation=True)
            if initial_refugees > 0:
                print(f"  📍 {l}: {initial_refugees} initial refugees")
                total_initial_refugees += initial_refugees
        
        print(f"👥 Total initial refugees: {total_initial_refugees}")
        
        # Spawn 10,000 agents at the origin
        origin_location = None
        for loc_name, loc in lm.items():
            if "Origin" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            print("❌ No origin location found!")
            return None
        
        print(f"📍 Spawning 10,000 agents at {origin_location.name}")
        
        # Spawn 10,000 agents with proper attributes for S2 activation
        for i in range(10000):
            # Create agent with attributes that enable S2 activation
            agent_attributes = {
                'connections': 5,  # Enable S2 capability (needs >= 2)
                'education_level': 0.7,  # Boost S2 activation
                'stress_tolerance': 0.6,  # Moderate stress tolerance
                's2_threshold': 0.5,  # S2 activation threshold
                'cognitive_profile': 'balanced'
            }
            agent = flee.Person(origin_location, agent_attributes)
            e.agents.append(agent)
        
        print(f"👥 Spawned {len(e.agents)} agents")
        
        # Run full simulation
        simulation_days = 20
        print(f"🚀 Running full simulation for {simulation_days} days...")
        
        s2_activations = []
        daily_results = []
        
        for day in range(simulation_days):
            day_s2_count = 0
            
            # Count S2 activations
            for agent in e.agents:
                if hasattr(agent, 'cognitive_state') and agent.cognitive_state == "S2":
                    day_s2_count += 1
            
            s2_activations.append(day_s2_count)
            
            # Record daily results
            daily_result = {
                'day': day,
                'total_agents': len(e.agents),
                's2_activations': day_s2_count,
                'camp_populations': {}
            }
            
            for camp in camp_locations:
                if camp in lm:
                    daily_result['camp_populations'][camp] = lm[camp].numAgents
            
            daily_results.append(daily_result)
            
            # Evolve ecosystem
            e.evolve()
            
            if day % 5 == 0:  # Print every 5 days
                print(f"  📅 Day {day}: {len(e.agents)} agents, {day_s2_count} S2 activations")
        
        # Calculate final results
        total_s2_decisions = sum(s2_activations)
        total_possible_decisions = len(e.agents) * simulation_days
        s2_rate = total_s2_decisions / total_possible_decisions if total_possible_decisions > 0 else 0
        
        # Calculate total distance traveled
        total_distance = 0
        for agent in e.agents:
            if hasattr(agent, 'distance_travelled'):
                total_distance += agent.distance_travelled
        
        # Count destinations reached
        destinations_reached = 0
        for camp in camp_locations:
            if camp in lm and lm[camp].numAgents > 0:
                destinations_reached += 1
        
        print(f"\n📊 Final Results:")
        print(f"  👥 Total agents: {len(e.agents)}")
        print(f"  🧠 S2 activations: {total_s2_decisions}")
        print(f"  📈 S2 rate: {s2_rate:.1%}")
        print(f"  🛣️ Total distance: {total_distance:.0f}")
        print(f"  🏕️ Destinations reached: {destinations_reached}/{len(camp_locations)}")
        print(f"  🏕️ Final camp populations:")
        
        for camp in camp_locations:
            if camp in lm:
                camp_pop = lm[camp].numAgents
                print(f"    📍 {camp}: {camp_pop} agents")
        
        # Save results
        results = {
            'experiment_name': exp_dir.name,
            'topology': exp_dir.name.split('_')[0],
            'network_size': int(exp_dir.name.split('_')[1][1:]),
            'scenario': exp_dir.name.split('_')[2] + '_' + exp_dir.name.split('_')[3],
            'population_size': len(e.agents),
            'simulation_days': simulation_days,
            's2_threshold': s2_threshold,
            's2_rate': s2_rate,
            'total_s2_decisions': total_s2_decisions,
            'total_distance': total_distance,
            'destinations_reached': destinations_reached,
            's2_activations': s2_activations,
            'daily_results': daily_results,
            'final_camp_populations': {camp: lm[camp].numAgents for camp in camp_locations if camp in lm},
            'completed_at': datetime.now().isoformat()
        }
        
        # Save results to JSON
        with open("experiment_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save daily results to CSV
        daily_df = pd.DataFrame(daily_results)
        daily_df.to_csv("daily_results.csv", index=False)
        
        print(f"  💾 Results saved: experiment_results.json, daily_results.csv")
        
        # Check for output files
        output_files = []
        for file in ['agents.out.0', 'links.out.0', 'out.csv']:
            if os.path.exists(file):
                output_files.append(file)
                print(f"  📄 Output file created: {file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during experiment: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

def main():
    """Main function to run all 10k agent experiments"""
    
    print("🚀 Running All 10k Agent Experiments")
    print("=" * 60)
    
    # Find all experiment directories
    experiments_dir = Path("proper_10k_agent_experiments")
    if not experiments_dir.exists():
        print(f"❌ Experiments directory not found: {experiments_dir}")
        return
    
    experiment_dirs = [d for d in experiments_dir.iterdir() if d.is_dir() and d.name != "EXPERIMENTS_SUMMARY.md"]
    
    if not experiment_dirs:
        print(f"❌ No experiment directories found in {experiments_dir}")
        return
    
    print(f"📁 Found {len(experiment_dirs)} experiments to run")
    
    all_results = []
    
    for exp_dir in experiment_dirs:
        print(f"\n{'='*60}")
        result = run_10k_experiment(exp_dir)
        
        if result:
            all_results.append(result)
            print(f"✅ {exp_dir.name} completed successfully")
        else:
            print(f"❌ {exp_dir.name} failed")
    
    # Create summary
    if all_results:
        print(f"\n{'='*60}")
        print("📊 SUMMARY OF ALL 10K AGENT EXPERIMENTS")
        print("=" * 60)
        
        for result in all_results:
            print(f"\n🧪 {result['experiment_name']}:")
            print(f"  📈 S2 rate: {result['s2_rate']:.1%}")
            print(f"  👥 Agents: {result['population_size']:,}")
            print(f"  🛣️ Distance: {result['total_distance']:.0f}")
            print(f"  🏕️ Destinations: {result['destinations_reached']}")
        
        # Save combined results
        summary = {
            'total_experiments': len(all_results),
            'experiments': all_results,
            'summary_created_at': datetime.now().isoformat()
        }
        
        with open(experiments_dir / "all_10k_agent_results.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n💾 All results saved to: {experiments_dir}/all_10k_agent_results.json")
        print(f"🎉 {len(all_results)} experiments completed successfully!")
    
    else:
        print(f"\n❌ No experiments completed successfully")

if __name__ == "__main__":
    main()
