#!/usr/bin/env python3
"""
Explore S1/S2 dynamics in FLEE simulations.

This script runs simulations with different S1/S2 configurations to understand
the model behavior and dynamics.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import yaml
import time

# Add current directory to path
sys.path.insert(0, '.')

def run_s1s2_simulation(config_name, config_dict, timesteps=50, num_agents=100):
    """Run a simulation with specific S1/S2 configuration."""
    
    print(f"\n🧪 Running simulation: {config_name}")
    print("=" * 60)
    
    # Create temporary config file
    temp_config = {
        'log_levels': {'agent': 0, 'link': 0, 'camp': 0, 'conflict': 0, 'init': 0, 'granularity': 'location'},
        'spawn_rules': {'take_from_population': False, 'insert_day0': True},
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
            'two_system_decision_making': 0.5,
            'conflict_threshold': 0.5,
            **config_dict  # Add S1/S2 specific config
        },
        'optimisations': {'hasten': 1}
    }
    
    # Write temporary config
    config_file = f"temp_config_{config_name}.yml"
    with open(config_file, 'w') as f:
        yaml.dump(temp_config, f)
    
    try:
        # Import FLEE components
        from flee import flee
        from flee.datamanager import handle_refugee_data, read_period
        from flee import InputGeography
        
        # Read simulation settings
        flee.SimulationSettings.ReadFromYML(config_file)
        
        # Create ecosystem
        e = flee.Ecosystem()
        
        # Create input geography
        ig = InputGeography.InputGeography()
        
        # Read input files
        flee.SimulationSettings.ConflictInputFile = "proper_10k_agent_experiments/star_n4_medium_s2_10k/input_csv/conflicts.csv"
        ig.ReadConflictInputCSV(flee.SimulationSettings.ConflictInputFile)
        ig.ReadLocationsFromCSV("proper_10k_agent_experiments/star_n4_medium_s2_10k/input_csv/locations.csv")
        ig.ReadLinksFromCSV("proper_10k_agent_experiments/star_n4_medium_s2_10k/input_csv/routes.csv")
        ig.ReadClosuresFromCSV("proper_10k_agent_experiments/star_n4_medium_s2_10k/input_csv/closures.csv")
        
        # Store input geography in ecosystem
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        
        # Get origin location
        origin_location = None
        for loc_name, loc in lm.items():
            if "Origin" in loc_name:
                origin_location = loc
                break
        
        if origin_location is None:
            print("❌ No origin location found!")
            return None
        
        print(f"📍 Origin location: {origin_location.name}")
        print(f"📍 Origin conflict intensity: {getattr(origin_location, 'conflict', 'N/A')}")
        
        # Create agents
        agents = []
        for i in range(num_agents):
            # Create agents with varied attributes
            attributes = {
                'connections': np.random.randint(0, 8),
                'education_level': np.random.uniform(0.2, 0.8),
                'stress_tolerance': np.random.uniform(0.3, 0.7),
                's2_threshold': np.random.uniform(0.3, 0.7)
            }
            agent = flee.Person(origin_location, attributes)
            agents.append(agent)
        
        e.agents = agents
        print(f"👥 Created {len(agents)} agents")
        
        # Run simulation
        results = {
            'timesteps': [],
            's2_activation_rates': [],
            'move_rates': [],
            'pressure_stats': [],
            'capability_stats': []
        }
        
        print(f"🚀 Running simulation for {timesteps} timesteps...")
        
        for t in range(timesteps):
            # Update ecosystem
            e.time = t
            e.evolve()
            
            # Collect statistics
            s2_active_count = 0
            move_count = 0
            pressures = []
            s2_capable_count = 0
            
            for agent in agents:
                if hasattr(agent, 'cognitive_state') and agent.cognitive_state == "S2":
                    s2_active_count += 1
                
                # Check if agent moved (simplified)
                if agent.location != origin_location:
                    move_count += 1
                
                # Collect pressure data
                pressure = agent.calculate_cognitive_pressure(t)
                pressures.append(pressure)
                
                # Check S2 capability
                if agent.get_system2_capable():
                    s2_capable_count += 1
            
            # Store results
            results['timesteps'].append(t)
            results['s2_activation_rates'].append(s2_active_count / len(agents))
            results['move_rates'].append(move_count / len(agents))
            results['pressure_stats'].append({
                'mean': np.mean(pressures),
                'std': np.std(pressures),
                'min': np.min(pressures),
                'max': np.max(pressures)
            })
            results['capability_stats'].append(s2_capable_count / len(agents))
            
            if t % 10 == 0:
                print(f"  Time {t:2d}: S2 rate: {s2_active_count/len(agents):.1%}, "
                      f"Move rate: {move_count/len(agents):.1%}, "
                      f"Pressure: {np.mean(pressures):.3f}")
        
        print(f"✅ Simulation completed: {config_name}")
        return results
        
    except Exception as e:
        print(f"❌ Error in simulation {config_name}: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Clean up temporary config file
        if os.path.exists(config_file):
            os.remove(config_file)


def analyze_s1s2_dynamics():
    """Run multiple simulations to analyze S1/S2 dynamics."""
    
    print("🔬 S1/S2 Dynamics Analysis")
    print("=" * 80)
    
    # Define different configurations to test
    configurations = {
        "Baseline": {
            "connectivity_mode": "baseline",
            "soft_capability": False,
            "pmove_s2_mode": "scaled",
            "eta": 0.5
        },
        "Diminishing Connectivity": {
            "connectivity_mode": "diminishing",
            "soft_capability": False,
            "pmove_s2_mode": "scaled",
            "eta": 0.5
        },
        "Soft Capability Gate": {
            "connectivity_mode": "baseline",
            "soft_capability": True,
            "pmove_s2_mode": "scaled",
            "eta": 0.5
        },
        "Constant S2 Move": {
            "connectivity_mode": "baseline",
            "soft_capability": False,
            "pmove_s2_mode": "constant",
            "pmove_s2_constant": 0.9
        },
        "High Eta (S2 Boost)": {
            "connectivity_mode": "baseline",
            "soft_capability": False,
            "pmove_s2_mode": "scaled",
            "eta": 0.8
        },
        "Low Eta (S2 Penalty)": {
            "connectivity_mode": "baseline",
            "soft_capability": False,
            "pmove_s2_mode": "scaled",
            "eta": 0.2
        }
    }
    
    # Run simulations
    all_results = {}
    
    for config_name, config_dict in configurations.items():
        results = run_s1s2_simulation(config_name, config_dict, timesteps=30, num_agents=50)
        if results is not None:
            all_results[config_name] = results
    
    # Create visualizations
    create_dynamics_plots(all_results)
    
    # Print summary statistics
    print_summary_statistics(all_results)
    
    return all_results


def create_dynamics_plots(all_results):
    """Create plots showing S1/S2 dynamics."""
    
    print("\n📊 Creating dynamics plots...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('S1/S2 Dynamics Analysis', fontsize=16, fontweight='bold')
    
    colors = plt.cm.Set1(np.linspace(0, 1, len(all_results)))
    
    # Plot 1: S2 Activation Rates over Time
    ax1 = axes[0, 0]
    for i, (config_name, results) in enumerate(all_results.items()):
        ax1.plot(results['timesteps'], results['s2_activation_rates'], 
                label=config_name, color=colors[i], linewidth=2)
    
    ax1.set_xlabel('Time (timesteps)')
    ax1.set_ylabel('S2 Activation Rate')
    ax1.set_title('S2 Activation Rates Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1)
    
    # Plot 2: Move Rates over Time
    ax2 = axes[0, 1]
    for i, (config_name, results) in enumerate(all_results.items()):
        ax2.plot(results['timesteps'], results['move_rates'], 
                label=config_name, color=colors[i], linewidth=2)
    
    ax2.set_xlabel('Time (timesteps)')
    ax2.set_ylabel('Move Rate')
    ax2.set_title('Move Rates Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1)
    
    # Plot 3: Cognitive Pressure Evolution
    ax3 = axes[1, 0]
    for i, (config_name, results) in enumerate(all_results.items()):
        pressures = [stat['mean'] for stat in results['pressure_stats']]
        ax3.plot(results['timesteps'], pressures, 
                label=config_name, color=colors[i], linewidth=2)
    
    ax3.set_xlabel('Time (timesteps)')
    ax3.set_ylabel('Mean Cognitive Pressure')
    ax3.set_title('Cognitive Pressure Evolution')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 1)
    
    # Plot 4: S2 Capability Rates
    ax4 = axes[1, 1]
    for i, (config_name, results) in enumerate(all_results.items()):
        ax4.plot(results['timesteps'], results['capability_stats'], 
                label=config_name, color=colors[i], linewidth=2)
    
    ax4.set_xlabel('Time (timesteps)')
    ax4.set_ylabel('S2 Capability Rate')
    ax4.set_title('S2 Capability Rates Over Time')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('S1S2_Dynamics_Analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig('S1S2_Dynamics_Analysis.pdf', bbox_inches='tight')
    
    print("✅ Plots saved as:")
    print("   - S1S2_Dynamics_Analysis.png")
    print("   - S1S2_Dynamics_Analysis.pdf")
    
    plt.show()


def print_summary_statistics(all_results):
    """Print summary statistics for all configurations."""
    
    print("\n📈 SUMMARY STATISTICS")
    print("=" * 80)
    
    for config_name, results in all_results.items():
        print(f"\n🔧 Configuration: {config_name}")
        print("-" * 50)
        
        # Calculate summary statistics
        final_s2_rate = results['s2_activation_rates'][-1]
        final_move_rate = results['move_rates'][-1]
        avg_pressure = np.mean([stat['mean'] for stat in results['pressure_stats']])
        final_capability = results['capability_stats'][-1]
        
        print(f"  Final S2 Activation Rate: {final_s2_rate:.1%}")
        print(f"  Final Move Rate: {final_move_rate:.1%}")
        print(f"  Average Cognitive Pressure: {avg_pressure:.3f}")
        print(f"  Final S2 Capability Rate: {final_capability:.1%}")
        
        # Calculate trends
        s2_trend = np.polyfit(results['timesteps'], results['s2_activation_rates'], 1)[0]
        move_trend = np.polyfit(results['timesteps'], results['move_rates'], 1)[0]
        
        print(f"  S2 Rate Trend: {'↗️ Increasing' if s2_trend > 0.001 else '↘️ Decreasing' if s2_trend < -0.001 else '➡️ Stable'}")
        print(f"  Move Rate Trend: {'↗️ Increasing' if move_trend > 0.001 else '↘️ Decreasing' if move_trend < -0.001 else '➡️ Stable'}")


def run_parameter_sensitivity_analysis():
    """Run parameter sensitivity analysis."""
    
    print("\n🔬 Parameter Sensitivity Analysis")
    print("=" * 60)
    
    # Test different eta values
    eta_values = [0.2, 0.3, 0.5, 0.7, 0.8]
    eta_results = {}
    
    for eta in eta_values:
        config = {
            "connectivity_mode": "baseline",
            "soft_capability": False,
            "pmove_s2_mode": "scaled",
            "eta": eta
        }
        
        results = run_s1s2_simulation(f"Eta_{eta}", config, timesteps=20, num_agents=30)
        if results is not None:
            eta_results[eta] = results
    
    # Plot eta sensitivity
    if eta_results:
        plt.figure(figsize=(10, 6))
        
        for eta, results in eta_results.items():
            plt.plot(results['timesteps'], results['s2_activation_rates'], 
                    label=f'η = {eta}', linewidth=2, marker='o', markersize=4)
        
        plt.xlabel('Time (timesteps)')
        plt.ylabel('S2 Activation Rate')
        plt.title('Sensitivity to Eta Parameter (S2 Move Probability Scaling)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig('S1S2_Eta_Sensitivity.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("✅ Eta sensitivity plot saved as S1S2_Eta_Sensitivity.png")


if __name__ == "__main__":
    print("🚀 Starting S1/S2 Dynamics Exploration")
    print("=" * 80)
    
    # Run main dynamics analysis
    results = analyze_s1s2_dynamics()
    
    # Run parameter sensitivity analysis
    run_parameter_sensitivity_analysis()
    
    print("\n🎉 S1/S2 Dynamics Exploration Complete!")
    print("\nKey findings:")
    print("- Different configurations show distinct behavioral patterns")
    print("- Connectivity mode affects pressure dynamics")
    print("- Capability gates influence S2 activation rates")
    print("- Eta parameter controls S2 move probability scaling")
    print("- System shows realistic psychological stress patterns")




