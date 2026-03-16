#!/usr/bin/env python3
"""
Comprehensive Analysis of Topology-S1/S2 Experiment Results

This script performs deep statistical analysis of the comprehensive topology
experiments, including network analysis, behavioral patterns, and statistical
validation of topology effects on S1/S2 decision-making.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.stats import f_oneway, kruskal, mannwhitneyu
import networkx as nx
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, '.')

class ComprehensiveTopologyAnalyzer:
    """Comprehensive analysis of topology experiment results."""
    
    def __init__(self, results_dir="results/comprehensive_topology_experiments"):
        self.results_dir = results_dir
        self.results = {}
        self.analysis_data = []
        self.network_metrics = {}
        
    def load_results(self):
        """Load comprehensive experiment results."""
        
        print("📊 Loading Comprehensive Experiment Results...")
        
        results_file = os.path.join(self.results_dir, "comprehensive_results.json")
        if not os.path.exists(results_file):
            print(f"❌ Results file not found: {results_file}")
            return False
        
        with open(results_file, 'r') as f:
            self.results = json.load(f)
        
        print(f"✅ Loaded results for {len(self.results)} topologies")
        return True
    
    def extract_analysis_data(self):
        """Extract data for comprehensive analysis."""
        
        print("🔍 Extracting Analysis Data...")
        
        for topology_name, s1s2_results in self.results.items():
            for s1s2_config_name, replicates in s1s2_results.items():
                for replicate in replicates:
                    # Extract key metrics
                    final_s2_rate = replicate['s2_activation_rates'][-1]
                    final_move_rate = replicate['move_rates'][-1]
                    final_evacuation = replicate['evacuation_rates'][-1]
                    
                    # Pressure statistics
                    pressure_stats = replicate['pressure_stats']
                    avg_pressure = np.mean([stat['mean'] for stat in pressure_stats])
                    pressure_variance = np.var([stat['mean'] for stat in pressure_stats])
                    
                    # Peak metrics
                    peak_s2_rate = max(replicate['s2_activation_rates'])
                    peak_move_rate = max(replicate['move_rates'])
                    
                    # Evacuation timing
                    evacuation_timeline = replicate['evacuation_rates']
                    time_to_50 = next((i for i, rate in enumerate(evacuation_timeline) if rate >= 0.5), len(evacuation_timeline))
                    time_to_90 = next((i for i, rate in enumerate(evacuation_timeline) if rate >= 0.9), len(evacuation_timeline))
                    
                    # Network metrics
                    network_metrics = replicate['network_metrics']
                    
                    # Topology specifications
                    topology_spec = replicate['topology_spec']
                    
                    # S1/S2 configuration
                    s1s2_config = replicate['s1s2_config']
                    
                    # Agent attribute analysis
                    agent_attrs = replicate['agent_attributes']
                    final_agent_attrs = agent_attrs[-1] if agent_attrs else []
                    
                    avg_connections = np.mean([attr['connections'] for attr in final_agent_attrs])
                    avg_education = np.mean([attr['education'] for attr in final_agent_attrs])
                    avg_stress_tolerance = np.mean([attr['stress_tolerance'] for attr in final_agent_attrs])
                    avg_s2_threshold = np.mean([attr['s2_threshold'] for attr in final_agent_attrs])
                    
                    # Behavioral diversity metrics
                    s2_activation_variance = np.var(replicate['s2_activation_rates'])
                    move_rate_variance = np.var(replicate['move_rates'])
                    evacuation_variance = np.var(replicate['evacuation_rates'])
                    
                    # Create analysis record
                    analysis_record = {
                        'topology_name': topology_name,
                        'topology_type': topology_spec['network_type'],
                        'topology_size': topology_spec['n_locations'],
                        's1s2_config': s1s2_config_name,
                        's1s2_description': s1s2_config['description'],
                        
                        # Behavioral metrics
                        'final_s2_rate': final_s2_rate,
                        'final_move_rate': final_move_rate,
                        'final_evacuation': final_evacuation,
                        'peak_s2_rate': peak_s2_rate,
                        'peak_move_rate': peak_move_rate,
                        'time_to_50_evacuation': time_to_50,
                        'time_to_90_evacuation': time_to_90,
                        
                        # Pressure metrics
                        'avg_pressure': avg_pressure,
                        'pressure_variance': pressure_variance,
                        
                        # Agent attributes
                        'avg_connections': avg_connections,
                        'avg_education': avg_education,
                        'avg_stress_tolerance': avg_stress_tolerance,
                        'avg_s2_threshold': avg_s2_threshold,
                        
                        # Behavioral diversity
                        's2_activation_variance': s2_activation_variance,
                        'move_rate_variance': move_rate_variance,
                        'evacuation_variance': evacuation_variance,
                        
                        # Network metrics
                        'n_nodes': network_metrics['n_nodes'],
                        'n_edges': network_metrics['n_edges'],
                        'density': network_metrics['density'],
                        'diameter': network_metrics['diameter'],
                        'average_path_length': network_metrics['average_path_length'],
                        'average_clustering': network_metrics['average_clustering'],
                        'transitivity': network_metrics['transitivity'],
                        'degree_centrality_mean': network_metrics['degree_centrality_mean'],
                        'degree_centrality_std': network_metrics['degree_centrality_std'],
                        'betweenness_centrality_mean': network_metrics['betweenness_centrality_mean'],
                        'betweenness_centrality_std': network_metrics['betweenness_centrality_std'],
                        'closeness_centrality_mean': network_metrics['closeness_centrality_mean'],
                        'closeness_centrality_std': network_metrics['closeness_centrality_std'],
                        'degree_assortativity': network_metrics['degree_assortativity']
                    }
                    
                    self.analysis_data.append(analysis_record)
        
        self.analysis_df = pd.DataFrame(self.analysis_data)
        print(f"✅ Extracted {len(self.analysis_data)} analysis records")
        
        return self.analysis_df
    
    def perform_statistical_analysis(self):
        """Perform comprehensive statistical analysis."""
        
        print("📈 Performing Statistical Analysis...")
        
        statistical_results = {}
        
        # 1. Topology effects on evacuation success
        topology_groups = [group['final_evacuation'].values for name, group in self.analysis_df.groupby('topology_type')]
        f_stat, p_value = f_oneway(*topology_groups)
        statistical_results['topology_evacuation_anova'] = {
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        # 2. S1/S2 configuration effects on evacuation success
        s1s2_groups = [group['final_evacuation'].values for name, group in self.analysis_df.groupby('s1s2_config')]
        f_stat, p_value = f_oneway(*s1s2_groups)
        statistical_results['s1s2_evacuation_anova'] = {
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        # 3. Network size effects
        size_groups = [group['final_evacuation'].values for name, group in self.analysis_df.groupby('topology_size')]
        f_stat, p_value = f_oneway(*size_groups)
        statistical_results['size_evacuation_anova'] = {
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        # 4. Network metrics correlation with evacuation success
        network_metrics = ['density', 'diameter', 'average_path_length', 'average_clustering', 
                          'degree_centrality_mean', 'betweenness_centrality_mean', 'closeness_centrality_mean']
        
        correlations = {}
        for metric in network_metrics:
            if metric in self.analysis_df.columns:
                corr, p_value = stats.pearsonr(self.analysis_df[metric], self.analysis_df['final_evacuation'])
                correlations[metric] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }
        
        statistical_results['network_metric_correlations'] = correlations
        
        # 5. Agent attribute effects
        agent_metrics = ['avg_connections', 'avg_education', 'avg_stress_tolerance', 'avg_s2_threshold']
        agent_correlations = {}
        for metric in agent_metrics:
            if metric in self.analysis_df.columns:
                corr, p_value = stats.pearsonr(self.analysis_df[metric], self.analysis_df['final_evacuation'])
                agent_correlations[metric] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }
        
        statistical_results['agent_attribute_correlations'] = agent_correlations
        
        # 6. Interaction effects (Topology × S1/S2 Config)
        interaction_groups = []
        for (topology, config), group in self.analysis_df.groupby(['topology_type', 's1s2_config']):
            interaction_groups.append(group['final_evacuation'].values)
        
        f_stat, p_value = f_oneway(*interaction_groups)
        statistical_results['interaction_anova'] = {
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        self.statistical_results = statistical_results
        return statistical_results
    
    def create_comprehensive_plots(self):
        """Create comprehensive visualization suite."""
        
        print("📊 Creating Comprehensive Plots...")
        
        # Set up plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create comprehensive figure
        fig, axes = plt.subplots(4, 4, figsize=(24, 20))
        fig.suptitle('Comprehensive Topology-S1/S2 Analysis', fontsize=20, fontweight='bold')
        
        # Plot 1: Evacuation Success by Topology Type
        ax1 = axes[0, 0]
        sns.boxplot(data=self.analysis_df, x='topology_type', y='final_evacuation', ax=ax1)
        ax1.set_title('Evacuation Success by Topology Type')
        ax1.set_ylabel('Final Evacuation Rate')
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Evacuation Success by S1/S2 Configuration
        ax2 = axes[0, 1]
        sns.boxplot(data=self.analysis_df, x='s1s2_config', y='final_evacuation', ax=ax2)
        ax2.set_title('Evacuation Success by S1/S2 Configuration')
        ax2.set_ylabel('Final Evacuation Rate')
        ax2.tick_params(axis='x', rotation=45)
        
        # Plot 3: S2 Activation Rates by Topology
        ax3 = axes[0, 2]
        sns.boxplot(data=self.analysis_df, x='topology_type', y='peak_s2_rate', ax=ax3)
        ax3.set_title('Peak S2 Activation by Topology Type')
        ax3.set_ylabel('Peak S2 Activation Rate')
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: Time to 50% Evacuation
        ax4 = axes[0, 3]
        sns.boxplot(data=self.analysis_df, x='topology_type', y='time_to_50_evacuation', ax=ax4)
        ax4.set_title('Time to 50% Evacuation by Topology')
        ax4.set_ylabel('Time (timesteps)')
        ax4.tick_params(axis='x', rotation=45)
        
        # Plot 5: Network Density vs Evacuation Success
        ax5 = axes[1, 0]
        sns.scatterplot(data=self.analysis_df, x='density', y='final_evacuation', 
                       hue='topology_type', ax=ax5)
        ax5.set_title('Network Density vs Evacuation Success')
        ax5.set_xlabel('Network Density')
        ax5.set_ylabel('Final Evacuation Rate')
        
        # Plot 6: Average Path Length vs Evacuation Success
        ax6 = axes[1, 1]
        sns.scatterplot(data=self.analysis_df, x='average_path_length', y='final_evacuation', 
                       hue='topology_type', ax=ax6)
        ax6.set_title('Average Path Length vs Evacuation Success')
        ax6.set_xlabel('Average Path Length')
        ax6.set_ylabel('Final Evacuation Rate')
        
        # Plot 7: Clustering vs Evacuation Success
        ax7 = axes[1, 2]
        sns.scatterplot(data=self.analysis_df, x='average_clustering', y='final_evacuation', 
                       hue='topology_type', ax=ax7)
        ax7.set_title('Clustering vs Evacuation Success')
        ax7.set_xlabel('Average Clustering')
        ax7.set_ylabel('Final Evacuation Rate')
        
        # Plot 8: Degree Centrality vs Evacuation Success
        ax8 = axes[1, 3]
        sns.scatterplot(data=self.analysis_df, x='degree_centrality_mean', y='final_evacuation', 
                       hue='topology_type', ax=ax8)
        ax8.set_title('Degree Centrality vs Evacuation Success')
        ax8.set_xlabel('Mean Degree Centrality')
        ax8.set_ylabel('Final Evacuation Rate')
        
        # Plot 9: Agent Connections vs Evacuation Success
        ax9 = axes[2, 0]
        sns.scatterplot(data=self.analysis_df, x='avg_connections', y='final_evacuation', 
                       hue='s1s2_config', ax=ax9)
        ax9.set_title('Agent Connections vs Evacuation Success')
        ax9.set_xlabel('Average Connections')
        ax9.set_ylabel('Final Evacuation Rate')
        
        # Plot 10: Education Level vs Evacuation Success
        ax10 = axes[2, 1]
        sns.scatterplot(data=self.analysis_df, x='avg_education', y='final_evacuation', 
                       hue='s1s2_config', ax=ax10)
        ax10.set_title('Education Level vs Evacuation Success')
        ax10.set_xlabel('Average Education Level')
        ax10.set_ylabel('Final Evacuation Rate')
        
        # Plot 11: Stress Tolerance vs Evacuation Success
        ax11 = axes[2, 2]
        sns.scatterplot(data=self.analysis_df, x='avg_stress_tolerance', y='final_evacuation', 
                       hue='s1s2_config', ax=ax11)
        ax11.set_title('Stress Tolerance vs Evacuation Success')
        ax11.set_xlabel('Average Stress Tolerance')
        ax11.set_ylabel('Final Evacuation Rate')
        
        # Plot 12: S2 Threshold vs Evacuation Success
        ax12 = axes[2, 3]
        sns.scatterplot(data=self.analysis_df, x='avg_s2_threshold', y='final_evacuation', 
                       hue='s1s2_config', ax=ax12)
        ax12.set_title('S2 Threshold vs Evacuation Success')
        ax12.set_xlabel('Average S2 Threshold')
        ax12.set_ylabel('Final Evacuation Rate')
        
        # Plot 13: Topology Size vs Evacuation Success
        ax13 = axes[3, 0]
        sns.boxplot(data=self.analysis_df, x='topology_size', y='final_evacuation', ax=ax13)
        ax13.set_title('Topology Size vs Evacuation Success')
        ax13.set_xlabel('Number of Locations')
        ax13.set_ylabel('Final Evacuation Rate')
        
        # Plot 14: Pressure Variance vs Evacuation Success
        ax14 = axes[3, 1]
        sns.scatterplot(data=self.analysis_df, x='pressure_variance', y='final_evacuation', 
                       hue='topology_type', ax=ax14)
        ax14.set_title('Pressure Variance vs Evacuation Success')
        ax14.set_xlabel('Pressure Variance')
        ax14.set_ylabel('Final Evacuation Rate')
        
        # Plot 15: Behavioral Diversity vs Evacuation Success
        ax15 = axes[3, 2]
        sns.scatterplot(data=self.analysis_df, x='s2_activation_variance', y='final_evacuation', 
                       hue='s1s2_config', ax=ax15)
        ax15.set_title('S2 Activation Variance vs Evacuation Success')
        ax15.set_xlabel('S2 Activation Variance')
        ax15.set_ylabel('Final Evacuation Rate')
        
        # Plot 16: Heatmap of Topology-S1/S2 Performance
        ax16 = axes[3, 3]
        pivot_data = self.analysis_df.groupby(['topology_type', 's1s2_config'])['final_evacuation'].mean().unstack()
        sns.heatmap(pivot_data, annot=True, fmt='.3f', cmap='YlOrRd', ax=ax16)
        ax16.set_title('Topology-S1/S2 Performance Heatmap')
        ax16.set_xlabel('S1/S2 Configuration')
        ax16.set_ylabel('Topology Type')
        
        plt.tight_layout()
        plt.savefig('results/comprehensive_topology_experiments/Comprehensive_Topology_Analysis.png', 
                    dpi=300, bbox_inches='tight')
        plt.savefig('results/comprehensive_topology_experiments/Comprehensive_Topology_Analysis.pdf', 
                    bbox_inches='tight')
        
        print("✅ Comprehensive plots saved")
        plt.show()
    
    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report."""
        
        print("📄 Generating Comprehensive Report...")
        
        # Create summary statistics
        summary_stats = self.analysis_df.groupby(['topology_type', 's1s2_config']).agg({
            'final_evacuation': ['mean', 'std', 'min', 'max'],
            'peak_s2_rate': ['mean', 'std'],
            'time_to_50_evacuation': ['mean', 'std'],
            'avg_pressure': ['mean', 'std'],
            'avg_connections': ['mean', 'std'],
            'avg_education': ['mean', 'std']
        }).round(3)
        
        # Save summary statistics
        summary_stats.to_csv('results/comprehensive_topology_experiments/comprehensive_summary_statistics.csv')
        
        # Save detailed results
        self.analysis_df.to_csv('results/comprehensive_topology_experiments/comprehensive_detailed_results.csv', index=False)
        
        # Save statistical results
        with open('results/comprehensive_topology_experiments/statistical_analysis_results.json', 'w') as f:
            json.dump(self.statistical_results, f, indent=2)
        
        # Generate comprehensive report
        report = f"""
# Comprehensive Topology-S1/S2 Experiment Analysis Report

## Executive Summary

This report presents a comprehensive analysis of {len(self.analysis_data)} experiments across {len(self.analysis_df['topology_type'].unique())} topology types and {len(self.analysis_df['s1s2_config'].unique())} S1/S2 configurations.

## Key Findings

### 1. Topology Effects on Evacuation Success
**Statistical Test**: ANOVA
**Result**: F = {self.statistical_results['topology_evacuation_anova']['f_statistic']:.3f}, p = {self.statistical_results['topology_evacuation_anova']['p_value']:.6f}
**Significance**: {'Significant' if self.statistical_results['topology_evacuation_anova']['significant'] else 'Not Significant'}

### 2. S1/S2 Configuration Effects on Evacuation Success
**Statistical Test**: ANOVA
**Result**: F = {self.statistical_results['s1s2_evacuation_anova']['f_statistic']:.3f}, p = {self.statistical_results['s1s2_evacuation_anova']['p_value']:.6f}
**Significance**: {'Significant' if self.statistical_results['s1s2_evacuation_anova']['significant'] else 'Not Significant'}

### 3. Network Size Effects
**Statistical Test**: ANOVA
**Result**: F = {self.statistical_results['size_evacuation_anova']['f_statistic']:.3f}, p = {self.statistical_results['size_evacuation_anova']['p_value']:.6f}
**Significance**: {'Significant' if self.statistical_results['size_evacuation_anova']['significant'] else 'Not Significant'}

### 4. Network Metric Correlations with Evacuation Success
"""
        
        for metric, result in self.statistical_results['network_metric_correlations'].items():
            report += f"- **{metric}**: r = {result['correlation']:.3f}, p = {result['p_value']:.6f} ({'Significant' if result['significant'] else 'Not Significant'})\n"
        
        report += f"""
### 5. Agent Attribute Correlations with Evacuation Success
"""
        
        for metric, result in self.statistical_results['agent_attribute_correlations'].items():
            report += f"- **{metric}**: r = {result['correlation']:.3f}, p = {result['p_value']:.6f} ({'Significant' if result['significant'] else 'Not Significant'})\n"
        
        report += f"""
### 6. Interaction Effects (Topology × S1/S2 Config)
**Statistical Test**: ANOVA
**Result**: F = {self.statistical_results['interaction_anova']['f_statistic']:.3f}, p = {self.statistical_results['interaction_anova']['p_value']:.6f}
**Significance**: {'Significant' if self.statistical_results['interaction_anova']['significant'] else 'Not Significant'}

## Topology Performance Rankings

### By Evacuation Success (Mean ± Std)
"""
        
        topology_means = self.analysis_df.groupby('topology_type')['final_evacuation'].agg(['mean', 'std']).round(3)
        for topology, (mean, std) in topology_means.iterrows():
            report += f"- **{topology}**: {mean:.3f} ± {std:.3f}\n"
        
        report += f"""
### By S1/S2 Configuration (Mean ± Std)
"""
        
        config_means = self.analysis_df.groupby('s1s2_config')['final_evacuation'].agg(['mean', 'std']).round(3)
        for config, (mean, std) in config_means.iterrows():
            report += f"- **{config}**: {mean:.3f} ± {std:.3f}\n"
        
        report += f"""
## Implications for Refugee Evacuation Planning

1. **Topology Selection**: Based on statistical analysis, topology type {'does' if self.statistical_results['topology_evacuation_anova']['significant'] else 'does not'} significantly affect evacuation success.

2. **S1/S2 Configuration**: S1/S2 configuration {'does' if self.statistical_results['s1s2_evacuation_anova']['significant'] else 'does not'} significantly affect evacuation success.

3. **Network Design**: Key network metrics that correlate with evacuation success should be considered in evacuation planning.

4. **Agent Characteristics**: Agent attributes that correlate with evacuation success should be incorporated into evacuation models.

## Data Files Generated

- `comprehensive_summary_statistics.csv`: Summary statistics by topology and S1/S2 config
- `comprehensive_detailed_results.csv`: Detailed results for all experiments
- `statistical_analysis_results.json`: Statistical test results
- `Comprehensive_Topology_Analysis.png/pdf`: Comprehensive analysis plots

## Conclusion

This comprehensive analysis provides rigorous statistical validation of topology effects on S1/S2 decision-making behavior in refugee evacuation scenarios. The results inform evidence-based policy recommendations for evacuation planning and network design.
"""
        
        with open('results/comprehensive_topology_experiments/Comprehensive_Analysis_Report.md', 'w') as f:
            f.write(report)
        
        print("✅ Comprehensive report generated")
        print("📁 Files saved in results/comprehensive_topology_experiments/")
        
        return report


def main():
    """Main function to analyze comprehensive topology results."""
    
    print("📊 COMPREHENSIVE TOPOLOGY ANALYSIS")
    print("=" * 80)
    print("This performs deep statistical analysis of comprehensive topology experiments.")
    print()
    
    # Create analyzer instance
    analyzer = ComprehensiveTopologyAnalyzer()
    
    # Load results
    if not analyzer.load_results():
        print("❌ Failed to load results. Please run comprehensive experiments first.")
        return
    
    # Extract analysis data
    analysis_df = analyzer.extract_analysis_data()
    
    # Perform statistical analysis
    statistical_results = analyzer.perform_statistical_analysis()
    
    # Create comprehensive plots
    analyzer.create_comprehensive_plots()
    
    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()
    
    print("\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
    print("\nKey deliverables:")
    print("• Comprehensive statistical analysis with proper controls")
    print("• Network metrics correlation analysis")
    print("• Agent attribute effects analysis")
    print("• Interaction effects analysis")
    print("• Publication-ready visualizations and reports")
    print("\nResults ready for academic publication!")


if __name__ == "__main__":
    main()




