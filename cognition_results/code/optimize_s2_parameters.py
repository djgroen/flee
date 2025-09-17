#!/usr/bin/env python3
"""
S2 Parameter Optimization for Real Flee

This script systematically optimizes S2 parameters to achieve the target
20-30% S2 activation rate using real Flee simulations.
"""

import sys
import os
import json
import math
import random
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def run_optimization_experiment(threshold_params, scenario_name="optimization"):
    """
    Run a single optimization experiment with given parameters.
    """
    try:
        # Import REAL Flee components
        from flee.flee import Ecosystem
        from flee.SimulationSettings import SimulationSettings
        from flee import moving, spawning
        
        # Initialize simulation settings
        SimulationSettings.ReadFromYML("flee/simsetting.yml")
        SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
        
        # Create REAL Flee ecosystem
        ecosystem = Ecosystem()
        
        # Create scenario topology
        origin = ecosystem.addLocation("Conflict_Zone", x=0, y=0, movechance=1.0, capacity=-1, pop=0)
        transit = ecosystem.addLocation("Transit_Town", x=75, y=0, movechance=0.3, capacity=-1, pop=0)
        camp = ecosystem.addLocation("Refugee_Camp", x=150, y=0, movechance=0.001, capacity=5000, pop=0)
        
        # Link locations
        ecosystem.linkUp("Conflict_Zone", "Transit_Town", 75.0)
        ecosystem.linkUp("Transit_Town", "Refugee_Camp", 75.0)
        
        # Set conflict levels
        origin.conflict = 0.8  # High conflict
        transit.conflict = 0.2  # Low conflict
        camp.conflict = 0.0    # Safe
        
        # Spawn agents with optimized cognitive profiles
        num_agents = 25  # Smaller for faster optimization
        profiles = {
            'analytical': {'s2_threshold': threshold_params['analytical'], 'connections': 8, 'population_fraction': 0.2},
            'balanced': {'s2_threshold': threshold_params['balanced'], 'connections': 5, 'population_fraction': 0.4},
            'intuitive': {'s2_threshold': threshold_params['intuitive'], 'connections': 2, 'population_fraction': 0.3},
            'social_connector': {'s2_threshold': threshold_params['social_connector'], 'connections': 10, 'population_fraction': 0.1}
        }
        
        for i in range(num_agents):
            # Select cognitive profile
            rand = random.random()
            cumulative = 0.0
            profile_name = 'balanced'
            
            for pname, pdata in profiles.items():
                cumulative += pdata['population_fraction']
                if rand <= cumulative:
                    profile_name = pname
                    break
            
            profile = profiles[profile_name]
            
            # Create agent attributes
            attributes = {
                'cognitive_profile': profile_name,
                's2_threshold': profile['s2_threshold'],
                'connections': profile['connections'],
                'education_level': 0.3 + random.random() * 0.4,  # 0.3-0.7
                'stress_tolerance': 0.3 + random.random() * 0.4,  # 0.3-0.7
            }
            
            # Add agent using REAL Flee method
            ecosystem.addAgent(origin, attributes)
        
        # Run REAL Flee simulation
        simulation_days = 15  # Shorter for faster optimization
        s2_activations = []
        
        for day in range(simulation_days):
            # Track S2 activations
            day_s2_count = 0
            for agent in ecosystem.agents:
                if hasattr(agent, 'cognitive_state') and agent.cognitive_state == "S2":
                    day_s2_count += 1
            
            s2_activations.append({
                'day': day,
                's2_count': day_s2_count,
                'total_agents': len(ecosystem.agents),
                's2_rate': day_s2_count / len(ecosystem.agents) if ecosystem.agents else 0
            })
            
            # Call REAL Flee ecosystem.evolve()
            ecosystem.evolve()
        
        # Calculate overall S2 statistics
        total_s2_decisions = sum(day['s2_count'] for day in s2_activations)
        total_decisions = sum(day['total_agents'] for day in s2_activations)
        overall_s2_rate = total_s2_decisions / total_decisions if total_decisions > 0 else 0
        
        return {
            'overall_s2_rate': overall_s2_rate,
            'total_s2_decisions': total_s2_decisions,
            'total_decisions': total_decisions,
            'simulation_days': simulation_days,
            'num_agents': num_agents,
            'threshold_params': threshold_params,
            'daily_s2_activations': s2_activations
        }
        
    except Exception as e:
        print(f"❌ Optimization experiment failed: {e}")
        return None

def optimize_s2_parameters():
    """
    Systematically optimize S2 parameters to achieve 20-30% S2 rate.
    """
    print("🔧 S2 PARAMETER OPTIMIZATION")
    print("=" * 50)
    print("Optimizing S2 thresholds to achieve 20-30% S2 activation rate")
    print("Using real Flee simulations for authentic results")
    print()
    
    # Define parameter search space
    # Current: analytical=0.35, balanced=0.50, intuitive=0.65, social_connector=0.40
    # Target: Lower thresholds to increase S2 activation
    
    parameter_sets = [
        # Set 1: Lower all thresholds by 0.1
        {
            'analytical': 0.25,
            'balanced': 0.40,
            'intuitive': 0.55,
            'social_connector': 0.30,
            'name': 'Lower by 0.1'
        },
        # Set 2: Lower all thresholds by 0.15
        {
            'analytical': 0.20,
            'balanced': 0.35,
            'intuitive': 0.50,
            'social_connector': 0.25,
            'name': 'Lower by 0.15'
        },
        # Set 3: Lower all thresholds by 0.2
        {
            'analytical': 0.15,
            'balanced': 0.30,
            'intuitive': 0.45,
            'social_connector': 0.20,
            'name': 'Lower by 0.2'
        },
        # Set 4: Focus on analytical and balanced (most common profiles)
        {
            'analytical': 0.20,
            'balanced': 0.30,
            'intuitive': 0.65,  # Keep high
            'social_connector': 0.25,
            'name': 'Focus on analytical/balanced'
        },
        # Set 5: Very low thresholds
        {
            'analytical': 0.10,
            'balanced': 0.20,
            'intuitive': 0.30,
            'social_connector': 0.15,
            'name': 'Very low thresholds'
        }
    ]
    
    results = []
    
    for i, params in enumerate(parameter_sets):
        print(f"🧪 Experiment {i+1}/{len(parameter_sets)}: {params['name']}")
        print(f"   Thresholds: analytical={params['analytical']}, balanced={params['balanced']}, intuitive={params['intuitive']}, social_connector={params['social_connector']}")
        
        result = run_optimization_experiment(params, f"optimization_{i+1}")
        
        if result:
            s2_rate = result['overall_s2_rate']
            print(f"   Result: {s2_rate:.1%} S2 rate")
            
            # Check if this meets our target
            if 0.20 <= s2_rate <= 0.30:
                print(f"   ✅ TARGET ACHIEVED! (20-30% range)")
            elif s2_rate < 0.20:
                print(f"   ⚠️  Still too low (need +{0.20-s2_rate:.1%})")
            else:
                print(f"   ⚠️  Too high (need -{s2_rate-0.30:.1%})")
            
            results.append(result)
        else:
            print(f"   ❌ Experiment failed")
        
        print()
    
    return results

def analyze_optimization_results(results):
    """
    Analyze the optimization results and recommend best parameters.
    """
    print("📊 OPTIMIZATION RESULTS ANALYSIS")
    print("=" * 50)
    
    if not results:
        print("❌ No results to analyze")
        return None
    
    # Find best result
    best_result = None
    best_score = float('inf')
    
    for result in results:
        s2_rate = result['overall_s2_rate']
        # Score based on distance from target range (20-30%)
        if s2_rate < 0.20:
            score = 0.20 - s2_rate  # Penalty for being too low
        elif s2_rate > 0.30:
            score = s2_rate - 0.30  # Penalty for being too high
        else:
            score = 0  # Perfect score if in target range
        
        if score < best_score:
            best_score = score
            best_result = result
    
    print(f"🎯 BEST RESULT:")
    if best_result:
        s2_rate = best_result['overall_s2_rate']
        params = best_result['threshold_params']
        
        print(f"   S2 Rate: {s2_rate:.1%}")
        print(f"   Parameters: {params['name']}")
        print(f"   Thresholds:")
        print(f"     - Analytical: {params['analytical']}")
        print(f"     - Balanced: {params['balanced']}")
        print(f"     - Intuitive: {params['intuitive']}")
        print(f"     - Social Connector: {params['social_connector']}")
        
        if 0.20 <= s2_rate <= 0.30:
            print(f"   Status: ✅ OPTIMAL (within 20-30% target range)")
        elif s2_rate < 0.20:
            print(f"   Status: ⚠️  Still too low (need +{0.20-s2_rate:.1%})")
        else:
            print(f"   Status: ⚠️  Too high (need -{s2_rate-0.30:.1%})")
    
    # Create optimization summary
    print(f"\\n📈 ALL RESULTS:")
    for i, result in enumerate(results):
        s2_rate = result['overall_s2_rate']
        params = result['threshold_params']
        print(f"   {i+1}. {params['name']}: {s2_rate:.1%} S2 rate")
    
    return best_result

def create_optimization_figures(results):
    """
    Create figures showing the optimization results.
    """
    if not results:
        return
    
    print("\\n📊 CREATING OPTIMIZATION FIGURES...")
    
    # Extract data
    experiment_names = [r['threshold_params']['name'] for r in results]
    s2_rates = [r['overall_s2_rate'] for r in results]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Figure 1: S2 rates by experiment
    bars = ax1.bar(range(len(experiment_names)), s2_rates, color=['green' if 0.20 <= rate <= 0.30 else 'orange' for rate in s2_rates])
    ax1.axhline(y=0.20, color='red', linestyle='--', alpha=0.7, label='Target Min (20%)')
    ax1.axhline(y=0.30, color='red', linestyle='--', alpha=0.7, label='Target Max (30%)')
    ax1.set_xlabel('Experiment')
    ax1.set_ylabel('S2 Activation Rate')
    ax1.set_title('S2 Parameter Optimization Results')
    ax1.set_xticks(range(len(experiment_names)))
    ax1.set_xticklabels(experiment_names, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, rate) in enumerate(zip(bars, s2_rates)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{rate:.1%}', ha='center', va='bottom')
    
    # Figure 2: Parameter comparison
    param_names = ['analytical', 'balanced', 'intuitive', 'social_connector']
    x = np.arange(len(param_names))
    width = 0.15
    
    for i, result in enumerate(results[:3]):  # Show top 3 results
        params = result['threshold_params']
        thresholds = [params[name] for name in param_names]
        ax2.bar(x + i*width, thresholds, width, label=f"{params['name']} ({result['overall_s2_rate']:.1%})")
    
    ax2.set_xlabel('Cognitive Profile')
    ax2.set_ylabel('S2 Threshold')
    ax2.set_title('S2 Thresholds by Profile and Experiment')
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(param_names)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    figure_file = Path("s2_optimization_results.png")
    plt.savefig(figure_file, dpi=300, bbox_inches='tight')
    print(f"✅ Optimization figure saved: {figure_file}")
    
    plt.show()

def main():
    """Run the S2 parameter optimization."""
    print("🧠 S2 PARAMETER OPTIMIZATION FOR REAL FLEE")
    print("=" * 60)
    print("Systematically optimizing S2 thresholds to achieve 20-30% S2 rate")
    print("Using real Flee simulations for authentic results")
    print()
    
    try:
        # Run optimization experiments
        results = optimize_s2_parameters()
        
        if results:
            # Analyze results
            best_result = analyze_optimization_results(results)
            
            # Create figures
            create_optimization_figures(results)
            
            # Save results
            output_file = Path("s2_optimization_results.json")
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\\n✅ Results saved to: {output_file}")
            
            if best_result:
                print(f"\\n🎉 OPTIMIZATION COMPLETE!")
                print(f"📊 Best S2 rate: {best_result['overall_s2_rate']:.1%}")
                print(f"🎯 Target achieved: {'✅ YES' if 0.20 <= best_result['overall_s2_rate'] <= 0.30 else '❌ NO'}")
                print(f"📁 Results: {output_file}")
                print(f"📊 Figure: s2_optimization_results.png")
            
            return best_result
        else:
            print("❌ No optimization results obtained")
            return None
            
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    best_result = main()
    sys.exit(0 if best_result else 1)
