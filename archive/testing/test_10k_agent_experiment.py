#!/usr/bin/env python3
"""
Test 10k Agent Experiment
- Run one of the 10k agent experiments to verify it works
- Use proper Flee framework with input files
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

def test_10k_agent_experiment():
    """Test one of the 10k agent experiments"""
    
    print("🧪 Testing 10k Agent Experiment")
    print("=" * 50)
    
    # Choose the star network experiment
    exp_dir = Path("proper_10k_agent_experiments/star_n7_medium_s2_10k")
    
    if not exp_dir.exists():
        print(f"❌ Experiment directory not found: {exp_dir}")
        return
    
    print(f"📁 Testing experiment: {exp_dir}")
    
    # Change to experiment directory
    original_dir = os.getcwd()
    os.chdir(exp_dir)
    
    try:
        # Import Flee components
        from flee import flee
        from flee.datamanager import handle_refugee_data, read_period
        from flee import InputGeography
        from flee.moving import calculate_systematic_s2_activation
        
        print("✅ Flee components imported successfully")
        
        # Read simulation period
        start_date, end_time = read_period.read_sim_period("sim_period.csv")
        print(f"📅 Simulation period: {start_date} to {end_time} ({end_time} days)")
        
        # Read simulation settings
        flee.SimulationSettings.ReadFromYML("simsetting.yml")
        print(f"⚙️ S2 threshold: {flee.SimulationSettings.move_rules['TwoSystemDecisionMaking']}")
        
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
            initial_refugees = d.get_field(l, start_date, FullInterpolation=True)
            if initial_refugees > 0:
                print(f"  📍 {l}: {initial_refugees} initial refugees")
                total_initial_refugees += initial_refugees
        
        print(f"👥 Total initial refugees: {total_initial_refugees}")
        
        # Run simulation for a few days to test
        test_days = 5
        print(f"🚀 Running simulation for {test_days} days...")
        
        s2_activations = []
        
        for day in range(test_days):
            day_s2_count = 0
            
            # Count S2 activations
            for agent in e.agents:
                if hasattr(agent, 'cognitive_state') and agent.cognitive_state == "S2":
                    day_s2_count += 1
            
            s2_activations.append(day_s2_count)
            
            # Evolve ecosystem
            e.evolve()
            
            if day % 2 == 0:  # Print every 2 days
                print(f"  📅 Day {day}: {len(e.agents)} agents, {day_s2_count} S2 activations")
        
        # Calculate S2 rate
        total_s2_decisions = sum(s2_activations)
        total_possible_decisions = len(e.agents) * test_days
        s2_rate = total_s2_decisions / total_possible_decisions if total_possible_decisions > 0 else 0
        
        print(f"\n📊 Test Results:")
        print(f"  👥 Total agents: {len(e.agents)}")
        print(f"  🧠 S2 activations: {total_s2_decisions}")
        print(f"  📈 S2 rate: {s2_rate:.1%}")
        print(f"  🏕️ Final camp populations:")
        
        for camp in camp_locations:
            if camp in lm:
                camp_pop = lm[camp].numAgents
                print(f"    📍 {camp}: {camp_pop} agents")
        
        print(f"\n✅ Test completed successfully!")
        print(f"🎯 Ready to run full 20-day simulation with 10k agents")
        
        return {
            'success': True,
            'total_agents': len(e.agents),
            's2_rate': s2_rate,
            'test_days': test_days,
            'camp_populations': {camp: lm[camp].numAgents for camp in camp_locations if camp in lm}
        }
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

def main():
    """Main function"""
    
    result = test_10k_agent_experiment()
    
    if result['success']:
        print(f"\n🎉 10k Agent Experiment Test PASSED!")
        print(f"📊 S2 rate: {result['s2_rate']:.1%}")
        print(f"👥 Agents: {result['total_agents']}")
    else:
        print(f"\n❌ 10k Agent Experiment Test FAILED!")
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
