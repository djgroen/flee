#!/usr/bin/env python3
"""
Run the properly generated experiments.
Uses the working input files from create_proper_10k_agent_experiments.py
"""

import sys
from pathlib import Path
import json
import time as time_module

sys.path.append('.')

from flee import flee
from flee.SimulationSettings import SimulationSettings
from flee import InputGeography
from flee.datamanager import handle_refugee_data


def run_experiment(exp_dir):
    """Run a single Flee experiment."""
    
    exp_name = exp_dir.name
    print(f"\n{'='*70}")
    print(f"🚀 Running: {exp_name}")
    print(f"{'='*70}")
    
    try:
        # Load settings
        SimulationSettings.ReadFromYML(exp_dir / "simsetting.yml")
        
        # Create ecosystem
        e = flee.Ecosystem()
        
        # Create input geography
        ig = InputGeography.InputGeography()
        
        # Read input files
        flee.SimulationSettings.ConflictInputFile = str(exp_dir / "input_csv" / "conflicts.csv")
        ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
        ig.ReadLocationsFromCSV(str(exp_dir / "input_csv" / "locations.csv"))
        ig.ReadLinksFromCSV(str(exp_dir / "input_csv" / "routes.csv"))
        ig.ReadClosuresFromCSV(str(exp_dir / "input_csv" / "closures.csv"))
        
        # Store in ecosystem
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        
        # Create refugee data handler
        d = handle_refugee_data.RefugeeTable(
            csvformat="generic",
            data_directory=str(exp_dir / "source_data"),
            start_date="2013-01-01",
            data_layout="data_layout.csv"
        )
        
        # Find origin
        origin_location = None
        for loc_name, loc in lm.items():
            if "Origin" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            raise ValueError("No origin location found!")
        
        # Get population from metadata
        with open(exp_dir / "experiment_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        population = metadata['population']
        
        # Spawn agents at origin ONLY
        print(f"   👥 Spawning {population} agents at {origin_location.name}...")
        for i in range(population):
            agent_attributes = {
                'connections': 5,
                'education_level': 0.5 + (i % 5) * 0.1,
                'stress_tolerance': 0.6,
                's2_threshold': SimulationSettings.move_rules.get("TwoSystemDecisionMaking", 0.5),
                'cognitive_profile': 'balanced',
                'education': 0.5 + (i % 5) * 0.1
            }
            agent = flee.Person(origin_location, agent_attributes)
            e.agents.append(agent)
        
        print(f"   ✅ Spawned {len(e.agents)} agents at origin")
        
        # Run simulation
        simulation_days = 20
        print(f"   🏃 Running Flee simulation for {simulation_days} days...")
        
        s2_activations = []
        
        for day in range(simulation_days):
            # Count S2 activations
            day_s2 = sum(1 for a in e.agents if hasattr(a, 'decision_history') and 
                        any(d.get('decision_type') == 'S2' for d in a.decision_history))
            s2_activations.append(day_s2)
            
            # Evolve
            e.evolve()
            
            if day % 5 == 0:
                s2_rate = (day_s2 / len(e.agents)) * 100 if e.agents else 0
                print(f"      Day {day}: {len(e.agents)} agents, S2: {s2_rate:.1f}%")
        
        # Calculate metrics
        total_s2 = sum(s2_activations)
        s2_rate = (total_s2 / (len(e.agents) * simulation_days)) * 100 if e.agents else 0
        
        # Camp populations
        final_camps = {}
        for loc_name, loc in lm.items():
            if loc.location_type == "camp":
                final_camps[loc_name] = loc.numAgents
        
        results = {
            'experiment': exp_name,
            'population': population,
            'days': simulation_days,
            's2_activation_rate': s2_rate,
            'total_s2_activations': total_s2,
            'final_camp_populations': final_camps,
            'status': 'SUCCESS'
        }
        
        # Save results
        with open(exp_dir / "experiment_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"   ✅ SUCCESS: S2 rate = {s2_rate:.1f}%")
        return results
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {
            'experiment': exp_name,
            'status': 'FAILED',
            'error': str(e)
        }


def main():
    """Run all experiments."""
    
    print("=" * 70)
    print("🎓 RUNNING COLLEAGUE MEETING EXPERIMENTS")
    print("=" * 70)
    print()
    print("Using properly generated input files from create_proper_10k_agent_experiments.py")
    print()
    
    # Find all experiment directories
    experiments_dir = Path("proper_10k_agent_experiments")
    exp_dirs = sorted([d for d in experiments_dir.iterdir() if d.is_dir() and '_5000' in d.name])
    
    print(f"Found {len(exp_dirs)} experiments to run")
    print()
    
    all_results = []
    
    for exp_dir in exp_dirs:
        result = run_experiment(exp_dir)
        all_results.append(result)
    
    # Save summary
    summary_file = Path("results/data/colleague_meeting_results.json")
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': time_module.strftime('%Y-%m-%d %H:%M:%S'),
            'total_experiments': len(all_results),
            'successful': len([r for r in all_results if r['status'] == 'SUCCESS']),
            'failed': len([r for r in all_results if r['status'] == 'FAILED']),
            'experiments': all_results
        }, f, indent=2)
    
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total experiments: {len(all_results)}")
    print(f"Successful: {len([r for r in all_results if r['status'] == 'SUCCESS'])}")
    print(f"Failed: {len([r for r in all_results if r['status'] == 'FAILED'])}")
    print()
    print(f"Results saved to: {summary_file}")
    print()


if __name__ == "__main__":
    main()




