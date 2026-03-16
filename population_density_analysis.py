#!/usr/bin/env python3
"""
Population Density Analysis for S1/S2 Experiments
- Analyze population density across network sizes
- Propose rigorous population scaling for journal publication
- Justify experimental design choices
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import seaborn as sns

class PopulationDensityAnalysis:
    """Analyze and justify population density choices for experiments"""
    
    def __init__(self):
        self.network_sizes = [5, 7, 11]
        self.current_populations = {5: 25, 7: 35, 11: 50}
        
    def analyze_current_density(self):
        """Analyze current population density approach"""
        
        print("📊 Current Population Density Analysis")
        print("=" * 50)
        
        # Calculate density metrics
        density_metrics = []
        
        for n_nodes in self.network_sizes:
            population = self.current_populations[n_nodes]
            
            # Calculate various density metrics
            density_per_node = population / n_nodes
            density_per_connection = population / (n_nodes - 1)  # Assuming tree-like connections
            density_per_area = population / (n_nodes ** 0.5)  # Assuming 2D area scaling
            
            density_metrics.append({
                'network_size': n_nodes,
                'population': population,
                'density_per_node': density_per_node,
                'density_per_connection': density_per_connection,
                'density_per_area': density_per_area,
                'scaling_factor': population / n_nodes
            })
        
        df = pd.DataFrame(density_metrics)
        
        print("Current Population Scaling:")
        print(df.to_string(index=False))
        print()
        
        # Analyze scaling patterns
        print("Scaling Analysis:")
        print(f"- Linear scaling factor: {df['scaling_factor'].mean():.2f} agents/node")
        print(f"- Scaling factor std: {df['scaling_factor'].std():.2f}")
        print(f"- Scaling factor range: {df['scaling_factor'].min():.2f} - {df['scaling_factor'].max():.2f}")
        print()
        
        return df
    
    def propose_rigorous_scaling(self):
        """Propose rigorous population scaling for journal publication"""
        
        print("🔬 Rigorous Population Scaling Proposals")
        print("=" * 50)
        
        scaling_proposals = {
            'constant_density': {
                'description': 'Constant agents per node (5 agents/node)',
                'populations': {5: 25, 7: 35, 11: 55},
                'justification': 'Maintains constant population density across network sizes'
            },
            'constant_total': {
                'description': 'Constant total population (50 agents)',
                'populations': {5: 50, 7: 50, 11: 50},
                'justification': 'Controls for total system size effects'
            },
            'scaled_by_connections': {
                'description': 'Scaled by number of connections (4 agents/connection)',
                'populations': {5: 16, 7: 24, 11: 40},  # (n-1) * 4
                'justification': 'Scales with network connectivity'
            },
            'scaled_by_area': {
                'description': 'Scaled by network area (2.5 agents/area unit)',
                'populations': {5: 11, 7: 19, 11: 33},  # n^0.5 * 2.5
                'justification': 'Scales with 2D network area'
            },
            'logarithmic_scaling': {
                'description': 'Logarithmic scaling (20 * log(n))',
                'populations': {5: 32, 7: 39, 11: 48},
                'justification': 'Logarithmic scaling for complex systems'
            }
        }
        
        # Analyze each proposal
        for name, proposal in scaling_proposals.items():
            print(f"\n{name.upper().replace('_', ' ')}:")
            print(f"  Description: {proposal['description']}")
            print(f"  Populations: {proposal['populations']}")
            print(f"  Justification: {proposal['justification']}")
            
            # Calculate scaling metrics
            populations = list(proposal['populations'].values())
            network_sizes = list(proposal['populations'].keys())
            
            scaling_factors = [p/n for p, n in zip(populations, network_sizes)]
            print(f"  Scaling factors: {[f'{sf:.2f}' for sf in scaling_factors]}")
            print(f"  Scaling std: {np.std(scaling_factors):.2f}")
        
        return scaling_proposals
    
    def recommend_for_journal(self):
        """Recommend population scaling for high-profile journal"""
        
        print("\n🎯 RECOMMENDATION FOR HIGH-PROFILE JOURNAL")
        print("=" * 50)
        
        recommendations = {
            'primary_approach': {
                'name': 'Constant Density per Node',
                'populations': {5: 25, 7: 35, 11: 55},
                'rationale': [
                    'Maintains constant population density across network sizes',
                    'Controls for node-level effects',
                    'Easy to interpret and justify',
                    'Standard approach in network analysis literature'
                ]
            },
            'sensitivity_analysis': {
                'name': 'Multiple Scaling Approaches',
                'populations': {
                    'constant_density': {5: 25, 7: 35, 11: 55},
                    'constant_total': {5: 50, 7: 50, 11: 50},
                    'scaled_connections': {5: 16, 7: 24, 11: 40}
                },
                'rationale': [
                    'Demonstrates robustness across different scaling assumptions',
                    'Shows that results are not artifacts of population scaling',
                    'Provides comprehensive analysis for reviewers'
                ]
            },
            'justification_framework': {
                'name': 'Theoretical Justification',
                'points': [
                    'Population density affects decision-making complexity',
                    'Constant density per node maintains comparable decision environments',
                    'Scaling with network size reflects realistic population growth',
                    'Multiple scaling approaches demonstrate robustness'
                ]
            }
        }
        
        print("PRIMARY APPROACH:")
        print(f"  {recommendations['primary_approach']['name']}")
        print(f"  Populations: {recommendations['primary_approach']['populations']}")
        print("  Rationale:")
        for point in recommendations['primary_approach']['rationale']:
            print(f"    - {point}")
        
        print("\nSENSITIVITY ANALYSIS:")
        print(f"  {recommendations['sensitivity_analysis']['name']}")
        print("  Rationale:")
        for point in recommendations['sensitivity_analysis']['rationale']:
            print(f"    - {point}")
        
        print("\nTHEORETICAL JUSTIFICATION:")
        for point in recommendations['justification_framework']['points']:
            print(f"  - {point}")
        
        return recommendations
    
    def create_visualization(self):
        """Create visualization of population scaling approaches"""
        
        scaling_proposals = self.propose_rigorous_scaling()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Population vs Network Size
        network_sizes = [5, 7, 11]
        
        for name, proposal in scaling_proposals.items():
            populations = [proposal['populations'][n] for n in network_sizes]
            ax1.plot(network_sizes, populations, marker='o', label=name.replace('_', ' ').title())
        
        ax1.set_xlabel('Network Size (Number of Nodes)')
        ax1.set_ylabel('Population Size')
        ax1.set_title('Population Scaling Approaches')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Density per Node
        for name, proposal in scaling_proposals.items():
            populations = [proposal['populations'][n] for n in network_sizes]
            densities = [p/n for p, n in zip(populations, network_sizes)]
            ax2.plot(network_sizes, densities, marker='o', label=name.replace('_', ' ').title())
        
        ax2.set_xlabel('Network Size (Number of Nodes)')
        ax2.set_ylabel('Density (Agents per Node)')
        ax2.set_title('Population Density per Node')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('population_scaling_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("📊 Visualization saved: population_scaling_analysis.png")
    
    def create_journal_justification(self):
        """Create justification document for journal submission"""
        
        justification_file = Path("POPULATION_SCALING_JUSTIFICATION.md")
        
        with open(justification_file, 'w') as f:
            f.write("# Population Scaling Justification for S1/S2 Experiments\n\n")
            f.write("## Research Question\n\n")
            f.write("How does population density affect S1/S2 dual-process decision-making in refugee movement models?\n\n")
            
            f.write("## Experimental Design Rationale\n\n")
            f.write("### Primary Approach: Constant Density per Node\n\n")
            f.write("**Population Scaling**: 5 agents per node\n")
            f.write("- Network Size 5: 25 agents\n")
            f.write("- Network Size 7: 35 agents\n")
            f.write("- Network Size 11: 55 agents\n\n")
            
            f.write("**Justification**:\n")
            f.write("1. **Theoretical Consistency**: Maintains constant decision-making complexity per node\n")
            f.write("2. **Literature Standard**: Common approach in network analysis and agent-based modeling\n")
            f.write("3. **Interpretability**: Easy to understand and compare across network sizes\n")
            f.write("4. **Realistic Scaling**: Reflects how populations might grow with network size\n\n")
            
            f.write("### Sensitivity Analysis: Multiple Scaling Approaches\n\n")
            f.write("To demonstrate robustness, we test three additional scaling approaches:\n\n")
            f.write("1. **Constant Total Population** (50 agents): Controls for total system size\n")
            f.write("2. **Scaled by Connections** (4 agents/connection): Scales with network connectivity\n")
            f.write("3. **Logarithmic Scaling** (20 * log(n)): Reflects complex system scaling\n\n")
            
            f.write("## Theoretical Framework\n\n")
            f.write("### Population Density Effects on Decision-Making\n\n")
            f.write("1. **Cognitive Load**: Higher density increases decision complexity\n")
            f.write("2. **Social Influence**: More agents per node increases social pressure\n")
            f.write("3. **Resource Competition**: Higher density increases resource scarcity\n")
            f.write("4. **Information Flow**: Density affects information transmission\n\n")
            
            f.write("### S1/S2 System Implications\n\n")
            f.write("1. **System 1 (Reactive)**: May be more effective in high-density, fast-moving situations\n")
            f.write("2. **System 2 (Deliberative)**: May be more effective in low-density, complex situations\n")
            f.write("3. **Switching Threshold**: May depend on local population density\n\n")
            
            f.write("## Experimental Controls\n\n")
            f.write("### Consistent Initialization\n")
            f.write("- All agents start at the same origin location\n")
            f.write("- Same random seed for reproducibility\n")
            f.write("- Identical network topologies (only size varies)\n\n")
            
            f.write("### Parameter Control\n")
            f.write("- Only population size varies between network sizes\n")
            f.write("- All other parameters held constant\n")
            f.write("- S2 threshold parameters consistent across experiments\n\n")
            
            f.write("## Statistical Analysis Plan\n\n")
            f.write("### Primary Analysis\n")
            f.write("- Compare S1/S2 scenarios across network sizes with constant density\n")
            f.write("- Test for main effects of network size and S2 threshold\n")
            f.write("- Test for interaction effects between network size and S2 threshold\n\n")
            
            f.write("### Sensitivity Analysis\n")
            f.write("- Repeat analysis with different population scaling approaches\n")
            f.write("- Test robustness of conclusions across scaling methods\n")
            f.write("- Report effect sizes and confidence intervals\n\n")
            
            f.write("## Expected Outcomes\n\n")
            f.write("### Hypothesis 1: Population Density Effects\n")
            f.write("- **Null**: Population density has no effect on S1/S2 behavior\n")
            f.write("- **Alternative**: Higher density increases S2 activation (more complex decisions)\n\n")
            
            f.write("### Hypothesis 2: Network Size Effects\n")
            f.write("- **Null**: Network size has no effect on S1/S2 behavior\n")
            f.write("- **Alternative**: Larger networks show different S1/S2 patterns\n\n")
            
            f.write("### Hypothesis 3: Scaling Robustness\n")
            f.write("- **Null**: Results depend on population scaling method\n")
            f.write("- **Alternative**: Results are robust across different scaling approaches\n\n")
            
            f.write("## Limitations and Future Work\n\n")
            f.write("1. **Fixed Density**: Real-world density may vary spatially\n")
            f.write("2. **Homogeneous Agents**: All agents have same cognitive parameters\n")
            f.write("3. **Static Networks**: Network structure doesn't change over time\n")
            f.write("4. **Future**: Test with heterogeneous agents and dynamic networks\n\n")
            
            f.write("## Conclusion\n\n")
            f.write("The constant density per node approach provides a rigorous, interpretable, and theoretically justified method for scaling population across network sizes in S1/S2 dual-process experiments. The inclusion of sensitivity analysis with multiple scaling approaches demonstrates robustness and provides comprehensive evidence for reviewers.\n")
        
        print(f"📋 Journal justification saved: {justification_file}")

def main():
    """Main function to analyze population density"""
    
    print("🔬 Population Density Analysis for S1/S2 Experiments")
    print("=" * 60)
    
    analysis = PopulationDensityAnalysis()
    
    # Analyze current approach
    analysis.analyze_current_density()
    
    # Propose rigorous scaling
    analysis.propose_rigorous_scaling()
    
    # Make recommendations
    analysis.recommend_for_journal()
    
    # Create visualization
    analysis.create_visualization()
    
    # Create journal justification
    analysis.create_journal_justification()
    
    print("\n🎯 Population Density Analysis Complete!")

if __name__ == "__main__":
    main()




