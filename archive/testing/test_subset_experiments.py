#!/usr/bin/env python3
"""
Test script to run a subset of the 10k agent experiments
"""

import os
import sys
from pathlib import Path

# Add flee to path
sys.path.append('.')

from flee import flee
from flee.SimulationSettings import SimulationSettings
from flee import InputGeography
from flee.datamanager import handle_refugee_data
import yaml

def test_subset_experiments():
    """Test a subset of experiments to verify the setup works"""
    
    # Test configurations - just a few to verify setup
    test_configs = [
        'star_n4_medium_s2_10k',
        'linear_n4_medium_s2_10k', 
        'grid_n4_medium_s2_10k'
    ]
    
    results = []
    
    for exp_name in test_configs:
        print(f"\n🚀 Testing experiment: {exp_name}")
        
        exp_dir = Path(f"proper_10k_agent_experiments/{exp_name}")
        if not exp_dir.exists():
            print(f"❌ Experiment directory not found: {exp_dir}")
            continue
            
        try:
            # Load simulation settings
            with open(exp_dir / "simsetting.yml", 'r') as f:
                sim_settings = yaml.safe_load(f)
            
            # Set up simulation
            SimulationSettings.ReadFromYML(exp_dir / "simsetting.yml")
            
            # Create ecosystem
            e = flee.Ecosystem()
            
            # Create input geography
            ig = InputGeography.InputGeography()
            
            # Set conflict input file and read input files
            flee.SimulationSettings.ConflictInputFile = str(exp_dir / "input_csv" / "conflicts.csv")
            ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
            ig.ReadLocationsFromCSV(str(exp_dir / "input_csv" / "locations.csv"))
            ig.ReadLinksFromCSV(str(exp_dir / "input_csv" / "routes.csv"))
            ig.ReadClosuresFromCSV(str(exp_dir / "input_csv" / "closures.csv"))
            
            # Store input geography in ecosystem
            e, lm = ig.StoreInputGeographyInEcosystem(e)
            
            # Create refugee data handler
            d = handle_refugee_data.RefugeeTable(
                csvformat="generic", 
                data_directory=str(exp_dir / "source_data"), 
                start_date="2013-01-01", 
                data_layout="data_layout.csv"
            )
            
            # Spawn agents
            print(f"  👥 Spawning 10,000 agents...")
            # Find origin location object
            origin_location = None
            for loc_name, loc in lm.items():
                if "Origin" in loc_name:
                    origin_location = loc
                    break
            
            if origin_location is None:
                print(f"  ❌ No origin location found!")
                continue
            
            for i in range(10000):
                agent_attributes = {
                    'connections': 5,  # Enable S2 capability (needs >= 2)
                    'education_level': 0.7,  # Boost S2 activation
                    'stress_tolerance': 0.6,  # Moderate stress tolerance
                    's2_threshold': 0.5,  # S2 activation threshold
                    'cognitive_profile': 'balanced'
                }
                agent = flee.Person(origin_location, agent_attributes)
                e.agents.append(agent)
            
            # Run simulation for a few days
            print(f"  🏃 Running simulation for 5 days...")
            for day in range(5):
                e.evolve()
                if day % 2 == 0:
                    print(f"    Day {day}: {e.numAgents()} agents")
            
            # Collect results - count S2 activations from decision history
            total_s2_decisions = 0
            for agent in e.agents:
                if hasattr(agent, 'decision_history'):
                    s2_decisions = sum(1 for decision in agent.decision_history 
                                     if decision.get('decision_type') == 'S2')
                    total_s2_decisions += s2_decisions
            
            s2_rate = (total_s2_decisions / (len(e.agents) * 5)) * 100 if e.agents else 0  # 5 days simulation
            
            results.append({
                'experiment': exp_name,
                'total_agents': len(e.agents),
                's2_activations': total_s2_decisions,
                's2_rate': s2_rate,
                'status': 'success'
            })
            
            print(f"  ✅ Success: {total_s2_decisions} S2 decisions made ({s2_rate:.1f}% of total decisions)")
            
        except Exception as ex:
            print(f"  ❌ Failed: {ex}")
            results.append({
                'experiment': exp_name,
                'status': 'failed',
                'error': str(ex)
            })
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 50)
    for result in results:
        if result['status'] == 'success':
            print(f"✅ {result['experiment']}: {result['s2_rate']:.1f}% S2 activation")
        else:
            print(f"❌ {result['experiment']}: {result['error']}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n🎯 {success_count}/{len(results)} experiments successful")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = test_subset_experiments()
    sys.exit(0 if success else 1)
