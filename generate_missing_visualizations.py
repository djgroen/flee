#!/usr/bin/env python3
"""
Generate Missing Visualizations
- Individual network analysis figures
- Sensitivity analysis plots
- Complete the organized results structure
"""

import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Any
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, '.')

class MissingVisualizationGenerator:
    """Generate missing individual network and sensitivity analysis visualizations"""
    
    def __init__(self, results_dir="organized_s1s2_experiments"):
        self.results_dir = Path(results_dir)
        self.figures_dir = self.results_dir / "02_figures"
        self.individual_dir = self.figures_dir / "individual_networks"
        self.sensitivity_dir = self.figures_dir / "sensitivity_analysis"
        
        # Load experimental results
        self.results = self._load_results()
        self.df = self._create_dataframe()
        
    def _load_results(self):
        """Load experimental results from JSON"""
        results_file = self.results_dir / "experimental_results.json"
        with open(results_file, 'r') as f:
            return json.load(f)
    
    def _create_dataframe(self):
        """Create DataFrame from results"""
        data = []
        for exp_id, exp_data in self.results.items():
            result = exp_data['results']
            data.append({
                'experiment_id': exp_id,
                'topology': exp_data['topology'],
                'network_size': exp_data['network_size'],
                'scenario': exp_data['scenario'],
                'scenario_type': exp_data['scenario_type'],
                's2_threshold': exp_data['s2_threshold'],
                's2_rate': result['s2_rate'],
                'total_distance': result['total_distance'],
                'destinations_reached': result['destinations_reached'],
                'population_size': result['population_size']
            })
        return pd.DataFrame(data)
    
    def generate_all_missing_visualizations(self):
        """Generate all missing visualizations"""
        
        print("🎨 Generating Missing Visualizations")
        print("=" * 50)
        
        # Generate individual network visualizations
        self._generate_individual_network_plots()
        
        # Generate sensitivity analysis plots
        self._generate_sensitivity_analysis_plots()
        
        print(f"\n✅ All missing visualizations generated!")
        print(f"📊 Individual networks: {self.individual_dir}")
        print(f"📈 Sensitivity analysis: {self.sensitivity_dir}")
    
    def _generate_individual_network_plots(self):
        """Generate individual network analysis plots"""
        
        print("📊 Generating individual network plots...")
        
        # Create plots for each topology
        for topology in ['linear', 'star', 'tree', 'grid']:
            self._create_topology_analysis_plot(topology)
            self._create_network_size_comparison_plot(topology)
            self._create_scenario_comparison_plot(topology)
    
    def _create_topology_analysis_plot(self, topology):
        """Create comprehensive analysis plot for a specific topology"""
        
        topo_data = self.df[self.df['topology'] == topology]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{topology.title()} Network Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: S2 Rate by Network Size
        for scenario in topo_data['scenario'].unique():
            scenario_data = topo_data[topo_data['scenario'] == scenario]
            ax1.plot(scenario_data['network_size'], scenario_data['s2_rate'], 
                    marker='o', linewidth=2, label=scenario, markersize=8)
        
        ax1.set_xlabel('Network Size (Number of Nodes)')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('S2 Activation Rate vs Network Size')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)
        
        # Plot 2: Distance by Network Size
        for scenario in topo_data['scenario'].unique():
            scenario_data = topo_data[topo_data['scenario'] == scenario]
            ax2.plot(scenario_data['network_size'], scenario_data['total_distance'], 
                    marker='s', linewidth=2, label=scenario, markersize=8)
        
        ax2.set_xlabel('Network Size (Number of Nodes)')
        ax2.set_ylabel('Total Distance Traveled')
        ax2.set_title('Travel Distance vs Network Size')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: S2 Rate by Scenario (Box Plot)
        scenario_order = ['pure_s1', 'pure_s2', 'static_mixed', 'low_s2', 'medium_s2', 'high_s2']
        scenario_labels = ['Pure S1', 'Pure S2', 'Static Mixed', 'Low S2', 'Medium S2', 'High S2']
        
        s2_rates_by_scenario = []
        for scenario in scenario_order:
            scenario_data = topo_data[topo_data['scenario'] == scenario]
            s2_rates_by_scenario.append(scenario_data['s2_rate'].values)
        
        ax3.boxplot(s2_rates_by_scenario, labels=scenario_labels)
        ax3.set_ylabel('S2 Activation Rate')
        ax3.set_title('S2 Activation Rate Distribution by Scenario')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Distance vs S2 Rate (Scatter)
        for scenario_type in ['baseline', 's1s2']:
            subset = topo_data[topo_data['scenario_type'] == scenario_type]
            ax4.scatter(subset['s2_rate'], subset['total_distance'], 
                       label=scenario_type.title(), alpha=0.7, s=100)
        
        ax4.set_xlabel('S2 Activation Rate')
        ax4.set_ylabel('Total Distance Traveled')
        ax4.set_title('Travel Distance vs S2 Activation Rate')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.individual_dir / f"{topology}_network_analysis.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.individual_dir / f"{topology}_network_analysis.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {topology.title()} network analysis plot created")
    
    def _create_network_size_comparison_plot(self, topology):
        """Create network size comparison plot for a topology"""
        
        topo_data = self.df[self.df['topology'] == topology]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(f'{topology.title()} Network: Size Effects', fontsize=14, fontweight='bold')
        
        # Plot 1: S2 Rate by Size
        for size in sorted(topo_data['network_size'].unique()):
            size_data = topo_data[topo_data['network_size'] == size]
            ax1.plot(size_data['scenario'], size_data['s2_rate'], 
                    marker='o', linewidth=2, label=f'{size} nodes', markersize=8)
        
        ax1.set_xlabel('Scenario')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('S2 Activation Rate by Network Size')
        ax1.legend()
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)
        
        # Plot 2: Distance by Size
        for size in sorted(topo_data['network_size'].unique()):
            size_data = topo_data[topo_data['network_size'] == size]
            ax2.plot(size_data['scenario'], size_data['total_distance'], 
                    marker='s', linewidth=2, label=f'{size} nodes', markersize=8)
        
        ax2.set_xlabel('Scenario')
        ax2.set_ylabel('Total Distance Traveled')
        ax2.set_title('Travel Distance by Network Size')
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.individual_dir / f"{topology}_size_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.individual_dir / f"{topology}_size_comparison.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {topology.title()} size comparison plot created")
    
    def _create_scenario_comparison_plot(self, topology):
        """Create scenario comparison plot for a topology"""
        
        topo_data = self.df[self.df['topology'] == topology]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create grouped bar chart
        scenarios = ['pure_s1', 'pure_s2', 'static_mixed', 'low_s2', 'medium_s2', 'high_s2']
        scenario_labels = ['Pure S1', 'Pure S2', 'Static Mixed', 'Low S2', 'Medium S2', 'High S2']
        sizes = sorted(topo_data['network_size'].unique())
        
        x = np.arange(len(scenarios))
        width = 0.25
        
        for i, size in enumerate(sizes):
            size_data = topo_data[topo_data['network_size'] == size]
            s2_rates = []
            for scenario in scenarios:
                scenario_data = size_data[size_data['scenario'] == scenario]
                s2_rates.append(scenario_data['s2_rate'].iloc[0] if len(scenario_data) > 0 else 0)
            
            ax.bar(x + i * width, s2_rates, width, label=f'{size} nodes', alpha=0.8)
        
        ax.set_xlabel('Scenario')
        ax.set_ylabel('S2 Activation Rate')
        ax.set_title(f'{topology.title()} Network: S2 Activation by Scenario and Size')
        ax.set_xticks(x + width)
        ax.set_xticklabels(scenario_labels, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(self.individual_dir / f"{topology}_scenario_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.individual_dir / f"{topology}_scenario_comparison.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {topology.title()} scenario comparison plot created")
    
    def _generate_sensitivity_analysis_plots(self):
        """Generate sensitivity analysis plots"""
        
        print("📈 Generating sensitivity analysis plots...")
        
        # S2 threshold sensitivity
        self._create_s2_threshold_sensitivity_plot()
        
        # Network topology sensitivity
        self._create_topology_sensitivity_plot()
        
        # Network size sensitivity
        self._create_network_size_sensitivity_plot()
        
        # Combined sensitivity analysis
        self._create_combined_sensitivity_plot()
    
    def _create_s2_threshold_sensitivity_plot(self):
        """Create S2 threshold sensitivity plot"""
        
        # Filter S1/S2 scenarios only
        s1s2_data = self.df[self.df['scenario_type'] == 's1s2']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('S2 Threshold Sensitivity Analysis', fontsize=14, fontweight='bold')
        
        # Plot 1: S2 Rate vs Threshold by Topology
        for topology in s1s2_data['topology'].unique():
            topo_data = s1s2_data[s1s2_data['topology'] == topology]
            ax1.plot(topo_data['s2_threshold'], topo_data['s2_rate'], 
                    marker='o', linewidth=2, label=topology.title(), markersize=8)
        
        ax1.set_xlabel('S2 Threshold')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('S2 Activation Rate vs S2 Threshold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)
        
        # Plot 2: Distance vs Threshold by Topology
        for topology in s1s2_data['topology'].unique():
            topo_data = s1s2_data[s1s2_data['topology'] == topology]
            ax2.plot(topo_data['s2_threshold'], topo_data['total_distance'], 
                    marker='s', linewidth=2, label=topology.title(), markersize=8)
        
        ax2.set_xlabel('S2 Threshold')
        ax2.set_ylabel('Total Distance Traveled')
        ax2.set_title('Travel Distance vs S2 Threshold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.sensitivity_dir / "s2_threshold_sensitivity.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.sensitivity_dir / "s2_threshold_sensitivity.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print("  ✅ S2 threshold sensitivity plot created")
    
    def _create_topology_sensitivity_plot(self):
        """Create topology sensitivity plot"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Network Topology Sensitivity Analysis', fontsize=14, fontweight='bold')
        
        # Plot 1: S2 Rate by Topology (Box Plot)
        topologies = ['linear', 'star', 'tree', 'grid']
        topology_labels = ['Linear', 'Star', 'Tree', 'Grid']
        
        s2_rates_by_topology = []
        for topology in topologies:
            topo_data = self.df[self.df['topology'] == topology]
            s2_rates_by_topology.append(topo_data['s2_rate'].values)
        
        ax1.boxplot(s2_rates_by_topology, labels=topology_labels)
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('S2 Activation Rate Distribution by Topology')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Distance by Topology (Box Plot)
        distances_by_topology = []
        for topology in topologies:
            topo_data = self.df[self.df['topology'] == topology]
            distances_by_topology.append(topo_data['total_distance'].values)
        
        ax2.boxplot(distances_by_topology, labels=topology_labels)
        ax2.set_ylabel('Total Distance Traveled')
        ax2.set_title('Travel Distance Distribution by Topology')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.sensitivity_dir / "topology_sensitivity.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.sensitivity_dir / "topology_sensitivity.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print("  ✅ Topology sensitivity plot created")
    
    def _create_network_size_sensitivity_plot(self):
        """Create network size sensitivity plot"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Network Size Sensitivity Analysis', fontsize=14, fontweight='bold')
        
        # Plot 1: S2 Rate by Network Size
        for topology in self.df['topology'].unique():
            topo_data = self.df[self.df['topology'] == topology]
            size_effects = topo_data.groupby('network_size')['s2_rate'].mean()
            ax1.plot(size_effects.index, size_effects.values, 
                    marker='o', linewidth=2, label=topology.title(), markersize=8)
        
        ax1.set_xlabel('Network Size (Number of Nodes)')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('S2 Activation Rate vs Network Size')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Distance by Network Size
        for topology in self.df['topology'].unique():
            topo_data = self.df[self.df['topology'] == topology]
            size_effects = topo_data.groupby('network_size')['total_distance'].mean()
            ax2.plot(size_effects.index, size_effects.values, 
                    marker='s', linewidth=2, label=topology.title(), markersize=8)
        
        ax2.set_xlabel('Network Size (Number of Nodes)')
        ax2.set_ylabel('Total Distance Traveled')
        ax2.set_title('Travel Distance vs Network Size')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.sensitivity_dir / "network_size_sensitivity.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.sensitivity_dir / "network_size_sensitivity.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print("  ✅ Network size sensitivity plot created")
    
    def _create_combined_sensitivity_plot(self):
        """Create combined sensitivity analysis plot"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Combined Sensitivity Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: S2 Rate Heatmap (Topology vs Scenario)
        pivot_s2 = self.df.pivot_table(values='s2_rate', index='topology', 
                                      columns='scenario', aggfunc='mean')
        sns.heatmap(pivot_s2, annot=True, fmt='.3f', cmap='viridis', ax=ax1)
        ax1.set_title('S2 Activation Rate: Topology vs Scenario')
        
        # Plot 2: Distance Heatmap (Topology vs Scenario)
        pivot_dist = self.df.pivot_table(values='total_distance', index='topology', 
                                        columns='scenario', aggfunc='mean')
        sns.heatmap(pivot_dist, annot=True, fmt='.0f', cmap='plasma', ax=ax2)
        ax2.set_title('Travel Distance: Topology vs Scenario')
        
        # Plot 3: S2 Rate by Network Size and Topology
        for topology in self.df['topology'].unique():
            topo_data = self.df[self.df['topology'] == topology]
            size_effects = topo_data.groupby('network_size')['s2_rate'].mean()
            ax3.plot(size_effects.index, size_effects.values, 
                    marker='o', linewidth=2, label=topology.title(), markersize=8)
        
        ax3.set_xlabel('Network Size (Number of Nodes)')
        ax3.set_ylabel('S2 Activation Rate')
        ax3.set_title('S2 Activation Rate vs Network Size by Topology')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Scenario Comparison (Box Plot)
        scenario_order = ['pure_s1', 'pure_s2', 'static_mixed', 'low_s2', 'medium_s2', 'high_s2']
        scenario_labels = ['Pure S1', 'Pure S2', 'Static Mixed', 'Low S2', 'Medium S2', 'High S2']
        
        s2_rates_by_scenario = []
        for scenario in scenario_order:
            scenario_data = self.df[self.df['scenario'] == scenario]
            s2_rates_by_scenario.append(scenario_data['s2_rate'].values)
        
        ax4.boxplot(s2_rates_by_scenario, labels=scenario_labels)
        ax4.set_ylabel('S2 Activation Rate')
        ax4.set_title('S2 Activation Rate Distribution by Scenario')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.sensitivity_dir / "combined_sensitivity_analysis.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.sensitivity_dir / "combined_sensitivity_analysis.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print("  ✅ Combined sensitivity analysis plot created")

def main():
    """Main function to generate missing visualizations"""
    
    print("🎨 Missing Visualization Generator")
    print("=" * 50)
    print("Generating individual network and sensitivity analysis plots")
    print("=" * 50)
    
    # Create and run generator
    generator = MissingVisualizationGenerator()
    generator.generate_all_missing_visualizations()
    
    print(f"\n🎉 All missing visualizations generated successfully!")
    print(f"📊 Check the organized_s1s2_experiments/02_figures/ directory")

if __name__ == "__main__":
    main()






