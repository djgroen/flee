#!/usr/bin/env python3
"""
Create comparison figures across all 27 experiments
Focus on dimensionless numbers and cross-experiment analysis
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
import networkx as nx

def load_experiment_results():
    """Load all experiment results"""
    results_file = Path("proper_10k_agent_experiments/all_10k_agent_results.json")
    
    if not results_file.exists():
        print("❌ Results file not found. Run experiments first.")
        return None
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    if 'experiments' in results:
        print(f"📊 Loaded {len(results['experiments'])} experiment results")
    else:
        print(f"📊 Loaded {len(results)} experiment results")
    return results

def create_dimensionless_analysis(results):
    """Create dimensionless parameter analysis across experiments"""
    
    # Extract data for analysis
    data = []
    
    # Handle the new JSON structure
    if 'experiments' in results:
        experiments = results['experiments']
    else:
        experiments = results
    
    for exp_data in experiments:
        exp_name = exp_data['experiment_name']
        topology = exp_data['topology']
        size = exp_data['network_size']
        scenario = exp_data['scenario']
        population = exp_data['population_size']
        
        # Calculate dimensionless parameters
        s2_rate = exp_data['s2_rate'] * 100  # Convert to percentage
        total_distance = exp_data['total_distance']
        destinations_reached = exp_data['destinations_reached']
        
        # Network metrics
        avg_degree = 2 * (size - 1) / size  # Approximate for connected networks
        network_density = (size - 1) / (size * (size - 1) / 2) if size > 1 else 0
        
        # Dimensionless ratios
        distance_per_agent = total_distance / population
        efficiency = destinations_reached / size  # Fraction of nodes reached
        
        data.append({
            'experiment': exp_name,
            'topology': topology,
            'size': size,
            'scenario': scenario,
            's2_rate': s2_rate,
            'distance_per_agent': distance_per_agent,
            'efficiency': efficiency,
            'avg_degree': avg_degree,
            'network_density': network_density,
            'destinations_reached': destinations_reached
        })
    
    df = pd.DataFrame(data)
    return df

def create_comparison_plots(df):
    """Create comprehensive comparison plots"""
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. S2 Activation Rate vs Network Size
    ax1 = plt.subplot(3, 3, 1)
    for topology in df['topology'].unique():
        for scenario in df['scenario'].unique():
            subset = df[(df['topology'] == topology) & (df['scenario'] == scenario)]
            if not subset.empty:
                ax1.plot(subset['size'], subset['s2_rate'], 
                        marker='o', linewidth=2, markersize=8,
                        label=f'{topology}_{scenario}')
    
    ax1.set_xlabel('Network Size (nodes)')
    ax1.set_ylabel('S2 Activation Rate (%)')
    ax1.set_title('S2 Activation vs Network Size')
    ax1.grid(True, alpha=0.3)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 2. Distance per Agent vs Network Size
    ax2 = plt.subplot(3, 3, 2)
    for topology in df['topology'].unique():
        for scenario in df['scenario'].unique():
            subset = df[(df['topology'] == topology) & (df['scenario'] == scenario)]
            if not subset.empty:
                ax2.plot(subset['size'], subset['distance_per_agent'], 
                        marker='s', linewidth=2, markersize=8,
                        label=f'{topology}_{scenario}')
    
    ax2.set_xlabel('Network Size (nodes)')
    ax2.set_ylabel('Distance per Agent')
    ax2.set_title('Mobility vs Network Size')
    ax2.grid(True, alpha=0.3)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 3. Efficiency vs Network Size
    ax3 = plt.subplot(3, 3, 3)
    for topology in df['topology'].unique():
        for scenario in df['scenario'].unique():
            subset = df[(df['topology'] == topology) & (df['scenario'] == scenario)]
            if not subset.empty:
                ax3.plot(subset['size'], subset['efficiency'], 
                        marker='^', linewidth=2, markersize=8,
                        label=f'{topology}_{scenario}')
    
    ax3.set_xlabel('Network Size (nodes)')
    ax3.set_ylabel('Efficiency (destinations/size)')
    ax3.set_title('Network Efficiency vs Size')
    ax3.grid(True, alpha=0.3)
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 4. S2 Rate vs Scenario (box plot)
    ax4 = plt.subplot(3, 3, 4)
    df_pivot = df.pivot_table(values='s2_rate', index='experiment', 
                             columns='scenario', aggfunc='mean')
    df_pivot.boxplot(ax=ax4)
    ax4.set_ylabel('S2 Activation Rate (%)')
    ax4.set_title('S2 Activation by Scenario')
    ax4.grid(True, alpha=0.3)
    
    # 5. Topology comparison (heatmap)
    ax5 = plt.subplot(3, 3, 5)
    pivot_data = df.pivot_table(values='s2_rate', index='topology', 
                               columns='scenario', aggfunc='mean')
    sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='viridis', ax=ax5)
    ax5.set_title('S2 Activation: Topology vs Scenario')
    
    # 6. Network metrics correlation
    ax6 = plt.subplot(3, 3, 6)
    correlation_data = df[['s2_rate', 'distance_per_agent', 'efficiency', 
                          'avg_degree', 'network_density']].corr()
    sns.heatmap(correlation_data, annot=True, fmt='.2f', cmap='coolwarm', 
                center=0, ax=ax6)
    ax6.set_title('Parameter Correlations')
    
    # 7. Size scaling analysis
    ax7 = plt.subplot(3, 3, 7)
    for topology in df['topology'].unique():
        subset = df[df['topology'] == topology]
        avg_s2 = subset.groupby('size')['s2_rate'].mean()
        ax7.plot(avg_s2.index, avg_s2.values, marker='o', linewidth=3, 
                markersize=10, label=topology)
    
    ax7.set_xlabel('Network Size')
    ax7.set_ylabel('Average S2 Rate (%)')
    ax7.set_title('S2 Scaling with Network Size')
    ax7.grid(True, alpha=0.3)
    ax7.legend()
    
    # 8. Scenario sensitivity
    ax8 = plt.subplot(3, 3, 8)
    scenario_means = df.groupby('scenario')['s2_rate'].mean()
    scenario_stds = df.groupby('scenario')['s2_rate'].std()
    ax8.bar(scenario_means.index, scenario_means.values, 
           yerr=scenario_stds.values, capsize=5, alpha=0.7)
    ax8.set_ylabel('S2 Activation Rate (%)')
    ax8.set_title('S2 Sensitivity to Threshold')
    ax8.grid(True, alpha=0.3)
    
    # 9. Summary statistics table
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    # Create summary table
    summary_stats = df.groupby(['topology', 'scenario']).agg({
        's2_rate': ['mean', 'std'],
        'efficiency': ['mean', 'std'],
        'distance_per_agent': ['mean', 'std']
    }).round(2)
    
    # Flatten column names
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
    summary_stats = summary_stats.reset_index()
    
    # Create table
    table_data = []
    for _, row in summary_stats.iterrows():
        table_data.append([
            f"{row['topology']}_{row['scenario']}",
            f"{row['s2_rate_mean']:.1f}±{row['s2_rate_std']:.1f}",
            f"{row['efficiency_mean']:.2f}±{row['efficiency_std']:.2f}",
            f"{row['distance_per_agent_mean']:.0f}±{row['distance_per_agent_std']:.0f}"
        ])
    
    table = ax9.table(cellText=table_data,
                     colLabels=['Experiment', 'S2 Rate (%)', 'Efficiency', 'Distance/Agent'],
                     cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)
    ax9.set_title('Summary Statistics', pad=20)
    
    plt.tight_layout()
    return fig

def create_scaling_analysis(df):
    """Create scaling law analysis"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. S2 Rate vs Network Size (log-log)
    ax1 = axes[0, 0]
    for topology in df['topology'].unique():
        subset = df[df['topology'] == topology]
        avg_s2 = subset.groupby('size')['s2_rate'].mean()
        ax1.loglog(avg_s2.index, avg_s2.values, marker='o', linewidth=2, 
                  markersize=8, label=topology)
    
    ax1.set_xlabel('Network Size (log scale)')
    ax1.set_ylabel('S2 Rate % (log scale)')
    ax1.set_title('S2 Activation Scaling')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 2. Distance scaling
    ax2 = axes[0, 1]
    for topology in df['topology'].unique():
        subset = df[df['topology'] == topology]
        avg_dist = subset.groupby('size')['distance_per_agent'].mean()
        ax2.loglog(avg_dist.index, avg_dist.values, marker='s', linewidth=2, 
                  markersize=8, label=topology)
    
    ax2.set_xlabel('Network Size (log scale)')
    ax2.set_ylabel('Distance per Agent (log scale)')
    ax2.set_title('Mobility Scaling')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Efficiency scaling
    ax3 = axes[1, 0]
    for topology in df['topology'].unique():
        subset = df[df['topology'] == topology]
        avg_eff = subset.groupby('size')['efficiency'].mean()
        ax3.semilogx(avg_eff.index, avg_eff.values, marker='^', linewidth=2, 
                    markersize=8, label=topology)
    
    ax3.set_xlabel('Network Size (log scale)')
    ax3.set_ylabel('Efficiency')
    ax3.set_title('Network Efficiency Scaling')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. Dimensionless groups
    ax4 = axes[1, 1]
    # Create dimensionless groups
    df['dimensionless_group'] = (df['s2_rate'] * df['efficiency']) / (df['distance_per_agent'] / 1000)
    
    for topology in df['topology'].unique():
        subset = df[df['topology'] == topology]
        avg_dim = subset.groupby('size')['dimensionless_group'].mean()
        ax4.semilogx(avg_dim.index, avg_dim.values, marker='d', linewidth=2, 
                    markersize=8, label=topology)
    
    ax4.set_xlabel('Network Size (log scale)')
    ax4.set_ylabel('Dimensionless Group')
    ax4.set_title('Dimensionless Parameter Scaling')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    plt.tight_layout()
    return fig

def main():
    """Main function"""
    print("🎨 Creating Experiment Comparison Figures")
    print("=" * 50)
    
    # Load results
    results = load_experiment_results()
    if results is None:
        return
    
    # Create analysis dataframe
    df = create_dimensionless_analysis(results)
    print(f"📊 Created analysis dataframe with {len(df)} experiments")
    
    # Create output directory
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    # Create comparison plots
    print("🎨 Creating comprehensive comparison plots...")
    fig1 = create_comparison_plots(df)
    fig1.savefig(output_dir / "experiment_comparison_analysis.png", dpi=300, bbox_inches='tight')
    fig1.savefig(output_dir / "experiment_comparison_analysis.pdf", bbox_inches='tight')
    print("✅ Comparison analysis saved")
    
    # Create scaling analysis
    print("🎨 Creating scaling law analysis...")
    fig2 = create_scaling_analysis(df)
    fig2.savefig(output_dir / "scaling_law_analysis.png", dpi=300, bbox_inches='tight')
    fig2.savefig(output_dir / "scaling_law_analysis.pdf", bbox_inches='tight')
    print("✅ Scaling analysis saved")
    
    # Save data summary
    df.to_csv(output_dir / "experiment_analysis_data.csv", index=False)
    print("✅ Analysis data saved to CSV")
    
    # Print summary
    print("\n📊 EXPERIMENT COMPARISON SUMMARY")
    print("=" * 50)
    print(f"Total experiments: {len(df)}")
    print(f"S2 rate range: {df['s2_rate'].min():.1f}% - {df['s2_rate'].max():.1f}%")
    print(f"Distance per agent range: {df['distance_per_agent'].min():.0f} - {df['distance_per_agent'].max():.0f}")
    print(f"Efficiency range: {df['efficiency'].min():.2f} - {df['efficiency'].max():.2f}")
    
    print("\n🎯 Key Findings:")
    print(f"• Average S2 rate: {df['s2_rate'].mean():.1f}% ± {df['s2_rate'].std():.1f}%")
    print(f"• Most efficient topology: {df.groupby('topology')['efficiency'].mean().idxmax()}")
    print(f"• Highest S2 activation: {df.groupby('scenario')['s2_rate'].mean().idxmax()}")
    
    print(f"\n✅ All comparison figures saved to: {output_dir}/")
    print("   - experiment_comparison_analysis.png/pdf")
    print("   - scaling_law_analysis.png/pdf")
    print("   - experiment_analysis_data.csv")

if __name__ == "__main__":
    main()
