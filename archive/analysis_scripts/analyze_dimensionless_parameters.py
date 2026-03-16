#!/usr/bin/env python3
"""
Analyze Dimensionless Parameters and Their Evolution

This script calculates and visualizes key dimensionless parameters for the S1/S2
evacuation model, tracking how they evolve over time and comparing across topologies.

Key Dimensionless Parameters:
1. P_S2: S2 activation probability [0, 1]
2. Ψ (Psi): Cognitive capacity [0, 1]
3. Ω (Omega): Structural opportunity [0, 1]
4. Experience Index: Normalized experience [0, ∞)
5. Cognitive Pressure: Normalized pressure [0, 1]
6. Normalized Time: t/T_max [0, 1]
7. Evacuation Efficiency: agents_safe / agents_total [0, 1]
8. Experience-to-Pressure Ratio: experience / pressure
9. S2 Efficiency: S2_rate × evacuation_success
10. Network Utilization: routes_used / routes_available
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 12)


def load_results(json_file):
    """Load results from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)


def calculate_dimensionless_parameters(result):
    """Calculate all dimensionless parameters for a single topology result."""
    
    topology = result['topology']
    num_agents = result['num_agents']
    num_timesteps = result['num_timesteps']
    num_routes = result['num_routes']
    agent_states = result.get('agent_s2_states_by_time', {})
    
    timesteps = sorted([int(t) for t in agent_states.keys()])
    
    # Initialize arrays
    params = {
        'topology': topology,
        'timesteps': timesteps,
        'normalized_time': [],
        'p_s2': [],  # S2 activation probability
        'avg_psi': [],  # Average cognitive capacity (Psi)
        'avg_omega': [],  # Average structural opportunity (Omega)
        'avg_experience': [],  # Average experience index
        'avg_pressure': [],  # Average cognitive pressure
        'evacuation_efficiency': [],  # agents_safe / agents_total
        'experience_pressure_ratio': [],  # experience / pressure
        's2_efficiency': [],  # S2_rate × evacuation_efficiency
        'experience_heterogeneity': [],  # Std dev of experience
        'psi_omega_product': [],  # Ψ × Ω (should match P_S2)
    }
    
    # Import model functions
    from flee.s1s2_model import (
        calculate_experience_index,
        calculate_cognitive_capacity,
        calculate_structural_opportunity,
        calculate_s2_activation
    )
    
    for t in timesteps:
        states = agent_states.get(str(t), {})
        if not states:
            continue
        
        # Normalized time
        normalized_t = t / num_timesteps if num_timesteps > 0 else 0.0
        params['normalized_time'].append(normalized_t)
        
        # Calculate per-agent metrics
        psi_values = []
        omega_values = []
        experience_values = []
        pressure_values = []
        s2_active_count = 0
        
        for agent_id, state in states.items():
            experience_index = state.get('experience_index', 0.0)
            conflict = state.get('conflict', 0.0)  # Will need to get from location
            s2_active = state.get('s2_active', False)
            cognitive_state = state.get('cognitive_state', 'S1')
            
            # Get conflict from location data if available
            location_name = state.get('location', '')
            conflict = 0.5  # Default
            
            # Try to get conflict from result's location data
            if 'locations' in result:
                for loc in result['locations']:
                    if loc.get('name') == location_name:
                        conflict = loc.get('conflict', 0.5)
                        break
            
            # Fallback: estimate from location name
            if conflict == 0.5:  # Still default
                if 'Facility' in location_name:
                    conflict = 0.95
                elif 'SafeZone' in location_name:
                    conflict = 0.0
                elif 'Ring1' in location_name:
                    conflict = 0.8
                elif 'Ring2' in location_name:
                    conflict = 0.4
                elif 'Ring3' in location_name:
                    conflict = 0.2
                else:
                    # Estimate based on topology and time
                    conflict = max(0.0, 0.95 - (t / num_timesteps) * 0.5)
            
            # Calculate Psi and Omega
            psi = calculate_cognitive_capacity(experience_index, alpha=2.0)
            omega = calculate_structural_opportunity(conflict, beta=2.0)
            p_s2_calc = calculate_s2_activation(psi, omega)
            
            psi_values.append(psi)
            omega_values.append(omega)
            experience_values.append(experience_index)
            
            # Try to get pressure from state, or estimate
            pressure = state.get('pressure', 0.0)
            if pressure == 0.0:
                # Estimate pressure from conflict and time
                pressure = min(1.0, conflict + (t / num_timesteps) * 0.2)
            pressure_values.append(pressure)
            
            if s2_active or cognitive_state == 'S2':
                s2_active_count += 1
        
        # Aggregate metrics
        if psi_values:
            params['avg_psi'].append(np.mean(psi_values))
            params['avg_omega'].append(np.mean(omega_values))
            params['avg_experience'].append(np.mean(experience_values))
            params['avg_pressure'].append(np.mean(pressure_values))
            params['experience_heterogeneity'].append(np.std(experience_values))
            params['psi_omega_product'].append(np.mean([p * o for p, o in zip(psi_values, omega_values)]))
        else:
            params['avg_psi'].append(0.0)
            params['avg_omega'].append(0.0)
            params['avg_experience'].append(0.0)
            params['avg_pressure'].append(0.0)
            params['experience_heterogeneity'].append(0.0)
            params['psi_omega_product'].append(0.0)
        
        # S2 activation rate
        p_s2_rate = (s2_active_count / len(states) * 100) if states else 0.0
        params['p_s2'].append(p_s2_rate / 100.0)  # Convert to [0, 1]
        
        # Evacuation efficiency
        agents_at_safe = result.get('agents_at_safe_by_time', [])
        if t < len(agents_at_safe):
            evacuation_eff = agents_at_safe[t] / num_agents if num_agents > 0 else 0.0
        else:
            evacuation_eff = 0.0
        params['evacuation_efficiency'].append(evacuation_eff)
        
        # Experience-to-pressure ratio
        if params['avg_pressure'][-1] > 0:
            exp_press_ratio = params['avg_experience'][-1] / params['avg_pressure'][-1]
        else:
            exp_press_ratio = 0.0
        params['experience_pressure_ratio'].append(exp_press_ratio)
        
        # S2 efficiency (S2 activation × evacuation success)
        params['s2_efficiency'].append(params['p_s2'][-1] * evacuation_eff)
    
    return params


def plot_dimensionless_evolution(results, output_dir):
    """Plot evolution of dimensionless parameters over normalized time."""
    
    # Calculate parameters for all topologies
    all_params = []
    for result in results:
        params = calculate_dimensionless_parameters(result)
        all_params.append(params)
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 3, figsize=(18, 14))
    axes = axes.flatten()
    
    plot_idx = 0
    
    # 1. P_S2 (S2 Activation Probability)
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['p_s2'], 
               label=params['topology'], marker='o', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('P_S2 (S2 Activation)', fontsize=11)
    ax.set_title('S2 Activation Probability Evolution', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    plot_idx += 1
    
    # 2. Ψ (Cognitive Capacity)
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['avg_psi'], 
               label=params['topology'], marker='s', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('Ψ (Cognitive Capacity)', fontsize=11)
    ax.set_title('Cognitive Capacity (Psi) Evolution', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    plot_idx += 1
    
    # 3. Ω (Structural Opportunity)
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['avg_omega'], 
               label=params['topology'], marker='^', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('Ω (Structural Opportunity)', fontsize=11)
    ax.set_title('Structural Opportunity (Omega) Evolution', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    plot_idx += 1
    
    # 4. Experience Index
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['avg_experience'], 
               label=params['topology'], marker='d', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('Average Experience Index', fontsize=11)
    ax.set_title('Experience Index Evolution', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plot_idx += 1
    
    # 5. Cognitive Pressure
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['avg_pressure'], 
               label=params['topology'], marker='v', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('Average Cognitive Pressure', fontsize=11)
    ax.set_title('Cognitive Pressure Evolution', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    plot_idx += 1
    
    # 6. Evacuation Efficiency
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['evacuation_efficiency'], 
               label=params['topology'], marker='p', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('Evacuation Efficiency', fontsize=11)
    ax.set_title('Evacuation Efficiency (Agents Safe / Total)', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    plot_idx += 1
    
    # 7. Experience-to-Pressure Ratio
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['experience_pressure_ratio'], 
               label=params['topology'], marker='*', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('Experience / Pressure Ratio', fontsize=11)
    ax.set_title('Experience-to-Pressure Ratio', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plot_idx += 1
    
    # 8. S2 Efficiency
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['s2_efficiency'], 
               label=params['topology'], marker='h', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('S2 Efficiency (P_S2 × Evac. Eff.)', fontsize=11)
    ax.set_title('S2 Efficiency Metric', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    plot_idx += 1
    
    # 9. Experience Heterogeneity
    ax = axes[plot_idx]
    for params in all_params:
        ax.plot(params['normalized_time'], params['experience_heterogeneity'], 
               label=params['topology'], marker='x', markersize=3, linewidth=2)
    ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
    ax.set_ylabel('Experience Std Dev', fontsize=11)
    ax.set_title('Experience Heterogeneity Over Time', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plot_idx += 1
    
    plt.tight_layout()
    output_file = output_dir / 'dimensionless_parameters_evolution.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_psi_omega_validation(results, output_dir):
    """Validate that P_S2 = Ψ × Ω (model consistency check)."""
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for idx, result in enumerate(results):
        params = calculate_dimensionless_parameters(result)
        topology = params['topology']
        
        ax = axes[idx]
        
        # Plot P_S2 vs Ψ × Ω
        normalized_time = params['normalized_time']
        p_s2 = params['p_s2']
        psi_omega = params['psi_omega_product']
        
        ax.plot(normalized_time, p_s2, 'b-', label='P_S2 (observed)', linewidth=2)
        ax.plot(normalized_time, psi_omega, 'r--', label='Ψ × Ω (calculated)', linewidth=2)
        
        # Calculate correlation
        if len(p_s2) > 1 and len(psi_omega) > 1:
            correlation = np.corrcoef(p_s2, psi_omega)[0, 1]
            ax.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                   transform=ax.transAxes, fontsize=11,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xlabel('Normalized Time (t/T)', fontsize=11)
        ax.set_ylabel('Probability', fontsize=11)
        ax.set_title(f'{topology} Topology\nModel Validation: P_S2 = Ψ × Ω', 
                    fontsize=12, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
    
    plt.tight_layout()
    output_file = output_dir / 'dimensionless_psi_omega_validation.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def plot_dimensionless_comparison(results, output_dir):
    """Compare final dimensionless parameter values across topologies."""
    
    # Calculate parameters
    all_params = []
    for result in results:
        params = calculate_dimensionless_parameters(result)
        all_params.append(params)
    
    # Extract final values
    topologies = [p['topology'] for p in all_params]
    
    final_values = {
        'P_S2': [p['p_s2'][-1] if p['p_s2'] else 0.0 for p in all_params],
        'Psi (Ψ)': [p['avg_psi'][-1] if p['avg_psi'] else 0.0 for p in all_params],
        'Omega (Ω)': [p['avg_omega'][-1] if p['avg_omega'] else 0.0 for p in all_params],
        'Experience': [p['avg_experience'][-1] if p['avg_experience'] else 0.0 for p in all_params],
        'Pressure': [p['avg_pressure'][-1] if p['avg_pressure'] else 0.0 for p in all_params],
        'Evac. Efficiency': [p['evacuation_efficiency'][-1] if p['evacuation_efficiency'] else 0.0 for p in all_params],
        'S2 Efficiency': [p['s2_efficiency'][-1] if p['s2_efficiency'] else 0.0 for p in all_params],
    }
    
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    axes = axes.flatten()
    
    colors = ['#e74c3c', '#3498db', '#2ecc71']
    
    for idx, (metric, values) in enumerate(final_values.items()):
        ax = axes[idx]
        bars = ax.bar(topologies, values, color=colors[:len(topologies)], alpha=0.7)
        ax.set_ylabel(metric, fontsize=11)
        ax.set_title(f'Final {metric}', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=9)
        
        if metric in ['P_S2', 'Psi (Ψ)', 'Omega (Ω)', 'Pressure', 'Evac. Efficiency', 'S2 Efficiency']:
            ax.set_ylim([0, 1])
    
    plt.tight_layout()
    output_file = output_dir / 'dimensionless_parameters_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_file}")
    plt.close()


def main():
    """Main analysis function."""
    
    output_dir = Path("nuclear_evacuation_results")
    output_dir.mkdir(exist_ok=True)
    
    # Find most recent JSON results file
    json_files = list(output_dir.glob("nuclear_evacuation_detailed_*.json"))
    if not json_files:
        print("❌ No results files found. Run nuclear_evacuation_simulations.py first.")
        return
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading results from: {latest_file}")
    
    results = load_results(latest_file)
    
    print(f"\n📊 Analyzing dimensionless parameters...")
    plot_dimensionless_evolution(results, output_dir)
    plot_psi_omega_validation(results, output_dir)
    plot_dimensionless_comparison(results, output_dir)
    
    print(f"\n✅ All dimensionless parameter analyses saved to: {output_dir}")


if __name__ == "__main__":
    main()

