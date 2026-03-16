#!/usr/bin/env python3
"""
Generate publication-quality figures from nuclear evacuation simulation results.
Uses only matplotlib and pandas for maximum compatibility.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def figure_inverted_u(output_dir):
    """
    Figure: Inverted-U relationship between conflict and deliberation.
    """
    print("Generating Inverted-U figure...")
    results_dir = Path("data/results")
    all_agent_data = []
    
    for topology in ['ring', 'star', 'linear']:
        topo_dir = results_dir / topology
        sample_file = topo_dir / "results_a2.0_b2.0_s0.csv"
        if sample_file.exists():
            df = pd.read_csv(sample_file)
            df['topology'] = topology
            all_agent_data.append(df)
            
    if not all_agent_data:
        print("  ⚠️ No detailed data found for Inverted-U figure.")
        return
        
    df = pd.concat(all_agent_data)
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Group by experience quartile
    df['experience_quartile'] = pd.qcut(df['experience'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])
    
    for label in ['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)']:
        subset = df[df['experience_quartile'] == label]
        # Aggregate by conflict
        agg = subset.groupby('conflict')['p_s2'].agg(['mean', 'std']).reset_index()
        agg = agg.sort_values('conflict')
        
        ax.plot(agg['conflict'], agg['mean'], marker='o', label=label, linewidth=2)
        ax.fill_between(agg['conflict'], agg['mean'] - agg['std'], agg['mean'] + agg['std'], alpha=0.1)
    
    ax.set_xlabel('Conflict Intensity (Threat)', fontsize=14)
    ax.set_ylabel('Deliberation Probability (P_S2)', fontsize=14)
    ax.set_title('Inverted-U: Deliberation Peaks at Moderate Threat', fontsize=16, fontweight='bold')
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(title='Experience Level')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'inverted_u_pattern.png', dpi=300)
    print(f"  ✅ Saved {output_dir / 'inverted_u_pattern.png'}")

def figure_topology_comparison(summary_df, output_dir):
    """
    Figure: Compare average P_S2 across topologies.
    """
    print("Generating Topology Comparison figure...")
    fig, ax = plt.subplots(figsize=(10, 7))
    
    default_data = summary_df[(summary_df['alpha'] == 2.0) & (summary_df['beta'] == 2.0)]
    
    topos = default_data['topology'].unique()
    means = [default_data[default_data['topology'] == t]['avg_p_s2'].mean() for t in topos]
    stds = [default_data[default_data['topology'] == t]['avg_p_s2'].std() for t in topos]
    
    ax.bar(topos, means, yerr=stds, color=['#440154', '#21918c', '#fde725'], alpha=0.7, capsize=10)
    
    ax.set_ylabel('Average Deliberation Probability (P_S2)', fontsize=14)
    ax.set_xlabel('Network Topology', fontsize=14)
    ax.set_title('Deliberation Levels Across Topologies (α=2.0, β=2.0)', fontsize=16, fontweight='bold')
    ax.set_ylim(0, 1.0)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'topology_comparison.png', dpi=300)
    print(f"  ✅ Saved {output_dir / 'topology_comparison.png'}")

def figure_parameter_sensitivity(summary_df, output_dir):
    """
    Figure: Heatmap of final evacuation rate vs (alpha, beta).
    """
    print("Generating Parameter Sensitivity heatmaps...")
    topologies = summary_df['topology'].unique()
    fig, axes = plt.subplots(1, len(topologies), figsize=(6 * len(topologies), 5))
    
    if len(topologies) == 1:
        axes = [axes]
        
    for idx, topology in enumerate(topologies):
        data = summary_df[summary_df['topology'] == topology]
        pivot = data.pivot_table(
            values='final_evacuation_rate',
            index='alpha',
            columns='beta',
            aggfunc='mean'
        )
        
        im = axes[idx].imshow(pivot, cmap='RdYlGn', vmin=0, vmax=1, origin='lower',
                             extent=[pivot.columns.min(), pivot.columns.max(), 
                                     pivot.index.min(), pivot.index.max()],
                             aspect='auto')
        
        axes[idx].set_title(f'{topology.capitalize()} Topology', fontsize=14, fontweight='bold')
        axes[idx].set_xlabel('β (Opportunity Sensitivity)', fontsize=12)
        axes[idx].set_ylabel('α (Capacity Sensitivity)', fontsize=12)
        
        # Add text annotations
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                axes[idx].text(pivot.columns[j], pivot.index[i], f'{pivot.iloc[i, j]:.2f}',
                             ha='center', va='center', color='black')
        
        fig.colorbar(im, ax=axes[idx])
    
    plt.tight_layout()
    plt.savefig(output_dir / 'parameter_sensitivity.png', dpi=300)
    print(f"  ✅ Saved {output_dir / 'parameter_sensitivity.png'}")

def generate_all_figures():
    output_dir = Path("figures")
    output_dir.mkdir(exist_ok=True)
    
    summary_file = Path("data/results/parameter_sweep_summary.csv")
    if not summary_file.exists():
        print(f"❌ Error: Summary file {summary_file} not found. Run parameter sweep first.")
        return
        
    summary_df = pd.read_csv(summary_file)
    
    figure_inverted_u(output_dir)
    figure_topology_comparison(summary_df, output_dir)
    figure_parameter_sensitivity(summary_df, output_dir)
    
    print("\n✨ All paper figures generated in figures/ ✨")

if __name__ == "__main__":
    generate_all_figures()
