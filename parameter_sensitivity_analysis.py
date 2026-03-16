#!/usr/bin/env python3
"""
Parameter Sensitivity Analysis for S1/S2 System

This script implements a parsimonious approach to parameter justification:
1. Test only the most critical parameters
2. Use simple, interpretable alternatives
3. Focus on parameters that most affect outcomes
4. Provide clear recommendations for production use
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from itertools import product
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

class ParsimoniousParameterAnalysis:
    """Focused parameter sensitivity analysis prioritizing simplicity."""
    
    def __init__(self):
        # Focus on the most critical parameters only
        self.critical_parameters = {
            'eta': [3, 6, 9],  # S2 activation steepness (3 values)
            'threshold': [0.4, 0.5, 0.6],  # S2 threshold (3 values)
            's2_move_prob': [0.7, 0.8, 0.9],  # S2 move probability (3 values)
            'pressure_cap': [0.3, 0.4, 0.5],  # Single cap for all pressures (3 values)
        }
        
        # Keep other parameters fixed at reasonable defaults
        self.fixed_parameters = {
            'time_growth': 10,  # Time constant for growth
            'time_decay': 50,   # Time constant for decay
            'conflict_decay': 20,  # Conflict decay constant
            'connectivity_max': 10,  # Max connections for normalization
        }
    
    def test_parameter_combinations(self):
        """Test all combinations of critical parameters."""
        
        print("🔍 Testing Parameter Combinations...")
        
        results = []
        
        # Generate all combinations
        param_combinations = list(product(*self.critical_parameters.values()))
        param_names = list(self.critical_parameters.keys())
        
        print(f"Testing {len(param_combinations)} parameter combinations...")
        
        for i, combination in enumerate(param_combinations):
            params = dict(zip(param_names, combination))
            
            # Test this parameter set
            result = self.test_parameter_set(params)
            result.update(params)
            results.append(result)
            
            if (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{len(param_combinations)} combinations")
        
        return pd.DataFrame(results)
    
    def test_parameter_set(self, params):
        """Test a specific parameter set."""
        
        # Simulate cognitive pressure over time
        t = np.linspace(0, 50, 100)
        
        # Calculate pressure components with current parameters
        base_pressure = self.calculate_base_pressure(t, params['pressure_cap'])
        conflict_pressure = self.calculate_conflict_pressure(t, params['pressure_cap'])
        social_pressure = self.calculate_social_pressure(params['pressure_cap'])
        
        total_pressure = base_pressure + conflict_pressure + social_pressure
        
        # Calculate S2 activation probability
        s2_prob = self.calculate_s2_activation(total_pressure, params['eta'], params['threshold'])
        
        # Calculate final move probability
        s1_move_prob = 0.3  # Fixed S1 move probability
        final_move_prob = (s1_move_prob * (1 - s2_prob) + 
                          params['s2_move_prob'] * s2_prob)
        
        # Calculate summary statistics
        return {
            'max_pressure': np.max(total_pressure),
            'mean_pressure': np.mean(total_pressure),
            'max_s2_prob': np.max(s2_prob),
            'mean_s2_prob': np.mean(s2_prob),
            'max_move_prob': np.max(final_move_prob),
            'mean_move_prob': np.mean(final_move_prob),
            'pressure_variance': np.var(total_pressure),
            's2_variance': np.var(s2_prob),
        }
    
    def calculate_base_pressure(self, t, pressure_cap):
        """Calculate base pressure with parsimonious form."""
        connectivity = 0.5  # Fixed for simplicity
        time_stress = 0.1 * (1 - np.exp(-t/self.fixed_parameters['time_growth'])) * np.exp(-t/self.fixed_parameters['time_decay'])
        base = connectivity * 0.2 + time_stress
        return np.minimum(pressure_cap, base)
    
    def calculate_conflict_pressure(self, t, pressure_cap):
        """Calculate conflict pressure with parsimonious form."""
        connectivity = 0.5  # Fixed for simplicity
        conflict_intensity = 0.8  # Fixed for simplicity
        conflict_decay = np.exp(-np.maximum(0, t-5) / self.fixed_parameters['conflict_decay'])
        conflict = conflict_intensity * connectivity * conflict_decay
        return np.minimum(pressure_cap, conflict)
    
    def calculate_social_pressure(self, pressure_cap):
        """Calculate social pressure with parsimonious form."""
        connectivity = 0.5  # Fixed for simplicity
        social = connectivity * 0.1
        return np.minimum(pressure_cap * 0.5, social)  # Social pressure is half the cap
    
    def calculate_s2_activation(self, pressure, eta, threshold):
        """Calculate S2 activation probability."""
        return 1 / (1 + np.exp(-eta * (pressure - threshold)))
    
    def analyze_results(self, results_df):
        """Analyze parameter sensitivity results."""
        
        print("\n📊 Parameter Sensitivity Analysis Results")
        print("=" * 60)
        
        # Calculate parameter importance
        param_importance = {}
        
        for param in self.critical_parameters.keys():
            # Calculate variance in outcomes explained by this parameter
            param_values = results_df[param].unique()
            
            # Group by parameter value and calculate mean outcomes
            grouped = results_df.groupby(param).agg({
                'mean_move_prob': 'std',
                'mean_s2_prob': 'std',
                'max_pressure': 'std'
            }).mean(axis=1)
            
            param_importance[param] = grouped.mean()
        
        # Sort by importance
        sorted_importance = sorted(param_importance.items(), key=lambda x: x[1], reverse=True)
        
        print("Parameter Importance (higher = more sensitive):")
        for param, importance in sorted_importance:
            print(f"  {param}: {importance:.4f}")
        
        # Find optimal parameter set
        optimal_idx = results_df['mean_move_prob'].idxmax()
        optimal_params = results_df.loc[optimal_idx]
        
        print(f"\nOptimal Parameter Set:")
        for param in self.critical_parameters.keys():
            print(f"  {param}: {optimal_params[param]}")
        
        return sorted_importance, optimal_params
    
    def create_sensitivity_plots(self, results_df):
        """Create sensitivity analysis plots."""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('S1/S2 Parameter Sensitivity Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Eta effect
        ax1 = axes[0, 0]
        for eta in self.critical_parameters['eta']:
            subset = results_df[results_df['eta'] == eta]
            ax1.plot(subset['threshold'], subset['mean_move_prob'], 
                    marker='o', label=f'η = {eta}', linewidth=2)
        ax1.set_xlabel('S2 Threshold')
        ax1.set_ylabel('Mean Move Probability')
        ax1.set_title('Effect of Eta (Steepness)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Threshold effect
        ax2 = axes[0, 1]
        for threshold in self.critical_parameters['threshold']:
            subset = results_df[results_df['threshold'] == threshold]
            ax2.plot(subset['eta'], subset['mean_s2_prob'], 
                    marker='s', label=f'θ = {threshold}', linewidth=2)
        ax2.set_xlabel('Eta (Steepness)')
        ax2.set_ylabel('Mean S2 Activation Probability')
        ax2.set_title('Effect of Threshold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: S2 move probability effect
        ax3 = axes[1, 0]
        for s2_prob in self.critical_parameters['s2_move_prob']:
            subset = results_df[results_df['s2_move_prob'] == s2_prob]
            ax3.plot(subset['pressure_cap'], subset['mean_move_prob'], 
                    marker='^', label=f'P(S2) = {s2_prob}', linewidth=2)
        ax3.set_xlabel('Pressure Cap')
        ax3.set_ylabel('Mean Move Probability')
        ax3.set_title('Effect of S2 Move Probability')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Parameter correlation heatmap
        ax4 = axes[1, 1]
        corr_data = results_df[list(self.critical_parameters.keys()) + ['mean_move_prob', 'mean_s2_prob']]
        correlation_matrix = corr_data.corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, ax=ax4)
        ax4.set_title('Parameter Correlations')
        
        plt.tight_layout()
        return fig
    
    def generate_recommendations(self, sorted_importance, optimal_params):
        """Generate parsimonious parameter recommendations."""
        
        print("\n💡 Parsimonious Parameter Recommendations")
        print("=" * 60)
        
        recommendations = {}
        
        # For each parameter, recommend the most robust value
        for param, importance in sorted_importance:
            param_values = self.critical_parameters[param]
            
            if importance > 0.1:  # High sensitivity
                print(f"🔴 {param}: HIGH SENSITIVITY - Use optimal value {optimal_params[param]}")
                recommendations[param] = optimal_params[param]
            elif importance > 0.05:  # Medium sensitivity
                print(f"🟡 {param}: MEDIUM SENSITIVITY - Use optimal value {optimal_params[param]}")
                recommendations[param] = optimal_params[param]
            else:  # Low sensitivity
                print(f"🟢 {param}: LOW SENSITIVITY - Use default value {param_values[1]}")
                recommendations[param] = param_values[1]  # Use middle value
        
        print(f"\n📋 Recommended Parameter Set:")
        for param, value in recommendations.items():
            print(f"  {param}: {value}")
        
        return recommendations

def main():
    """Run the parsimonious parameter sensitivity analysis."""
    
    print("🎯 Parsimonious S1/S2 Parameter Sensitivity Analysis")
    print("=" * 60)
    print("Focus: Test only critical parameters with simple, interpretable alternatives")
    print()
    
    # Create analyzer
    analyzer = ParsimoniousParameterAnalysis()
    
    # Test parameter combinations
    results_df = analyzer.test_parameter_combinations()
    
    # Analyze results
    sorted_importance, optimal_params = analyzer.analyze_results(results_df)
    
    # Create plots
    fig = analyzer.create_sensitivity_plots(results_df)
    
    # Generate recommendations
    recommendations = analyzer.generate_recommendations(sorted_importance, optimal_params)
    
    # Save results
    results_df.to_csv('parameter_sensitivity_results.csv', index=False)
    fig.savefig('parameter_sensitivity_analysis.png', dpi=300, bbox_inches='tight')
    fig.savefig('parameter_sensitivity_analysis.pdf', bbox_inches='tight')
    
    print(f"\n✅ Results saved:")
    print(f"   📊 parameter_sensitivity_analysis.png/pdf")
    print(f"   📄 parameter_sensitivity_results.csv")
    
    # Show plots
    plt.show()
    
    return results_df, recommendations

if __name__ == "__main__":
    results_df, recommendations = main()




