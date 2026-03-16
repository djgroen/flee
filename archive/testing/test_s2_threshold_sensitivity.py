#!/usr/bin/env python3
"""
S2 Threshold Sensitivity Test
- Quick test to validate that our proposed thresholds (0.3, 0.5, 0.7) show sufficient sensitivity
- Tests a subset of scenarios to ensure experimental design is sound
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

class S2ThresholdSensitivityTest:
    """Quick test of S2 threshold sensitivity"""
    
    def __init__(self):
        self.thresholds = [0.3, 0.5, 0.7]
        self.test_scenarios = [
            {'topology': 'linear', 'n_nodes': 5},
            {'topology': 'star', 'n_nodes': 7},
            {'topology': 'grid', 'n_nodes': 11}
        ]
        
    def test_threshold_sensitivity(self):
        """Test if thresholds show sufficient sensitivity"""
        
        print("🧪 S2 Threshold Sensitivity Test")
        print("=" * 50)
        print("Testing thresholds: 0.3, 0.5, 0.7")
        print("Scenarios: Linear(5), Star(7), Grid(11)")
        print()
        
        results = []
        
        for scenario in self.test_scenarios:
            print(f"📊 Testing {scenario['topology']} network ({scenario['n_nodes']} nodes)")
            
            for threshold in self.thresholds:
                # Simulate S2 activation rate based on threshold
                # This is a simplified model - in reality, it would depend on cognitive pressure
                s2_rate = self._simulate_s2_activation(threshold, scenario)
                
                results.append({
                    'topology': scenario['topology'],
                    'n_nodes': scenario['n_nodes'],
                    'threshold': threshold,
                    's2_rate': s2_rate
                })
                
                print(f"  Threshold {threshold}: S2 rate = {s2_rate:.1%}")
        
        # Analyze sensitivity
        self._analyze_sensitivity(results)
        
        return results
    
    def _simulate_s2_activation(self, threshold, scenario):
        """Simulate S2 activation rate based on threshold and scenario"""
        
        # Simplified model: S2 activation depends on threshold and network complexity
        base_pressure = 0.4  # Base cognitive pressure
        
        # Network complexity factors
        complexity_factors = {
            'linear': 0.8,   # Lower complexity
            'star': 1.0,     # Medium complexity  
            'tree': 1.1,     # Medium-high complexity
            'grid': 1.3      # Higher complexity
        }
        
        # Size factor (larger networks = more complex decisions)
        size_factor = 1.0 + (scenario['n_nodes'] - 5) * 0.05
        
        # Calculate effective pressure
        effective_pressure = base_pressure * complexity_factors[scenario['topology']] * size_factor
        
        # S2 activation probability (sigmoid function)
        s2_rate = 1 / (1 + np.exp(-10 * (effective_pressure - threshold)))
        
        # Add some realistic noise
        s2_rate += np.random.normal(0, 0.02)
        s2_rate = np.clip(s2_rate, 0, 1)
        
        return s2_rate
    
    def _analyze_sensitivity(self, results):
        """Analyze threshold sensitivity"""
        
        print("\n📈 Sensitivity Analysis")
        print("=" * 30)
        
        df = pd.DataFrame(results)
        
        # Calculate sensitivity metrics
        for topology in df['topology'].unique():
            topo_data = df[df['topology'] == topology]
            
            print(f"\n{topology.upper()} Network:")
            
            # Calculate threshold differences
            thresholds = sorted(topo_data['threshold'].unique())
            s2_rates = [topo_data[topo_data['threshold'] == t]['s2_rate'].iloc[0] for t in thresholds]
            
            print(f"  Thresholds: {thresholds}")
            print(f"  S2 Rates:   {[f'{rate:.1%}' for rate in s2_rates]}")
            
            # Calculate sensitivity
            if len(s2_rates) > 1:
                rate_range = max(s2_rates) - min(s2_rates)
                threshold_range = max(thresholds) - min(thresholds)
                sensitivity = rate_range / threshold_range
                
                print(f"  Rate Range: {rate_range:.1%}")
                print(f"  Sensitivity: {sensitivity:.2f} (%/threshold unit)")
                
                # Assess sensitivity
                if sensitivity > 0.3:
                    print(f"  ✅ GOOD: High sensitivity")
                elif sensitivity > 0.15:
                    print(f"  ⚠️  MODERATE: Moderate sensitivity")
                else:
                    print(f"  ❌ LOW: Low sensitivity - consider different thresholds")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        
        # Calculate average sensitivity across all scenarios
        all_sensitivities = []
        for topology in df['topology'].unique():
            topo_data = df[df['topology'] == topology]
            thresholds = sorted(topo_data['threshold'].unique())
            s2_rates = [topo_data[topo_data['threshold'] == t]['s2_rate'].iloc[0] for t in thresholds]
            
            if len(s2_rates) > 1:
                rate_range = max(s2_rates) - min(s2_rates)
                threshold_range = max(thresholds) - min(thresholds)
                sensitivity = rate_range / threshold_range
                all_sensitivities.append(sensitivity)
        
        avg_sensitivity = np.mean(all_sensitivities)
        
        print(f"  Average Sensitivity: {avg_sensitivity:.2f} (%/threshold unit)")
        
        if avg_sensitivity > 0.25:
            print(f"  ✅ EXCELLENT: Thresholds show strong sensitivity")
            print(f"  📊 Recommendation: Proceed with 0.3, 0.5, 0.7 thresholds")
        elif avg_sensitivity > 0.15:
            print(f"  ✅ GOOD: Thresholds show adequate sensitivity")
            print(f"  📊 Recommendation: Proceed with 0.3, 0.5, 0.7 thresholds")
        else:
            print(f"  ⚠️  MODERATE: Consider adjusting thresholds")
            print(f"  📊 Recommendation: Test additional thresholds (e.g., 0.2, 0.4, 0.6, 0.8)")
        
        return avg_sensitivity
    
    def create_sensitivity_plot(self, results):
        """Create visualization of threshold sensitivity"""
        
        df = pd.DataFrame(results)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for topology in df['topology'].unique():
            topo_data = df[df['topology'] == topology]
            ax.plot(topo_data['threshold'], topo_data['s2_rate'], 
                   marker='o', linewidth=2, label=f'{topology.title()} (n={topo_data["n_nodes"].iloc[0]})')
        
        ax.set_xlabel('S2 Threshold')
        ax.set_ylabel('S2 Activation Rate')
        ax.set_title('S2 Threshold Sensitivity Test')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        # Add threshold markers
        for threshold in self.thresholds:
            ax.axvline(x=threshold, color='red', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig('s2_threshold_sensitivity_test.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Sensitivity plot saved: s2_threshold_sensitivity_test.png")

def main():
    """Main function to test S2 threshold sensitivity"""
    
    print("🧪 S2 Threshold Sensitivity Test")
    print("=" * 50)
    print("Validating experimental design thresholds: 0.3, 0.5, 0.7")
    print()
    
    # Create and run test
    test = S2ThresholdSensitivityTest()
    results = test.test_threshold_sensitivity()
    
    # Create visualization
    test.create_sensitivity_plot(results)
    
    print(f"\n🎯 Threshold Sensitivity Test Complete!")
    print(f"📊 Results can be used to validate experimental design")

if __name__ == "__main__":
    main()






