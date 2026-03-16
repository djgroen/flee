#!/usr/bin/env python3
"""
Generate figures for colleague meeting.

Shows:
1. Topology sensitivity (S2 activation across topologies)
2. S1/S2 switching effects (baseline vs scenarios)
3. Normalized metrics for fair comparison
4. Agent movement patterns
"""

import json
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from pathlib import Path
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (20, 12)
plt.rcParams['font.size'] = 10


def load_results():
    """Load experiment results."""
    results_file = Path("results/data/colleague_meeting_results.json")
    
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        print("   Please run: python run_colleague_meeting_experiments.py first")
        return None
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    return data['experiments']


def create_topology_sensitivity_figure(results):
    """Figure 1: Topology Sensitivity to S2 Activation."""
    
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Organize data
    topologies = ['star', 'linear', 'hierarchical', 'regular_grid', 'irregular_grid']
    scenarios = ['baseline', 'low_s2', 'medium_s2', 'high_s2']
    
    # Panel 1: S2 Activation Rate by Topology and Scenario
    ax1 = fig.add_subplot(gs[0, :])
    
    data_matrix = []
    for topo in topologies:
        row = []
        for scenario in scenarios:
            exp = [r for r in results if r['topology'] == topo and r['s2_scenario'] == scenario]
            if exp and exp[0]['status'] == 'SUCCESS':
                row.append(exp[0]['s2_activation_rate'])
            else:
                row.append(0)
        data_matrix.append(row)
    
    x = np.arange(len(scenarios))
    width = 0.15
    
    for i, topo in enumerate(topologies):
        offset = (i - 2) * width
        ax1.bar(x + offset, data_matrix[i], width, label=topo.replace('_', ' ').title())
    
    ax1.set_xlabel('S2 Scenario', fontsize=12, fontweight='bold')
    ax1.set_ylabel('S2 Activation Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Topology Sensitivity: S2 Activation Across Network Structures', 
                  fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.replace('_', ' ').title() for s in scenarios])
    ax1.legend(loc='upper left', ncol=5)
    ax1.grid(axis='y', alpha=0.3)
    
    # Panel 2: Normalized Network Metrics
    ax2 = fig.add_subplot(gs[1, 0])
    
    avg_degrees = []
    for topo in topologies:
        exp = [r for r in results if r['topology'] == topo and r['s2_scenario'] == 'medium_s2']
        if exp and exp[0]['status'] == 'SUCCESS':
            avg_degrees.append(exp[0]['avg_degree'])
        else:
            avg_degrees.append(0)
    
    ax2.barh(topologies, avg_degrees, color=sns.color_palette("husl", len(topologies)))
    ax2.set_xlabel('Average Degree', fontsize=11, fontweight='bold')
    ax2.set_title('Network Connectivity', fontsize=12, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    # Panel 3: S2 Activation vs Network Connectivity
    ax3 = fig.add_subplot(gs[1, 1])
    
    for scenario in scenarios:
        x_data = []
        y_data = []
        for topo in topologies:
            exp = [r for r in results if r['topology'] == topo and r['s2_scenario'] == scenario]
            if exp and exp[0]['status'] == 'SUCCESS':
                x_data.append(exp[0]['avg_degree'])
                y_data.append(exp[0]['s2_activation_rate'])
        
        ax3.scatter(x_data, y_data, label=scenario.replace('_', ' ').title(), s=100, alpha=0.7)
    
    ax3.set_xlabel('Average Degree', fontsize=11, fontweight='bold')
    ax3.set_ylabel('S2 Activation Rate (%)', fontsize=11, fontweight='bold')
    ax3.set_title('S2 Activation vs Network Connectivity', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(alpha=0.3)
    
    # Panel 4: Baseline vs S2 Switching
    ax4 = fig.add_subplot(gs[1, 2])
    
    baseline_rates = []
    s2_rates = []
    for topo in topologies:
        baseline = [r for r in results if r['topology'] == topo and r['s2_scenario'] == 'baseline']
        s2_exp = [r for r in results if r['topology'] == topo and r['s2_scenario'] == 'medium_s2']
        
        if baseline and baseline[0]['status'] == 'SUCCESS':
            baseline_rates.append(baseline[0]['s2_activation_rate'])
        else:
            baseline_rates.append(0)
        
        if s2_exp and s2_exp[0]['status'] == 'SUCCESS':
            s2_rates.append(s2_exp[0]['s2_activation_rate'])
        else:
            s2_rates.append(0)
    
    x = np.arange(len(topologies))
    width = 0.35
    
    ax4.bar(x - width/2, baseline_rates, width, label='Baseline (No S2)', color='lightcoral')
    ax4.bar(x + width/2, s2_rates, width, label='Medium S2', color='lightblue')
    
    ax4.set_ylabel('S2 Activation Rate (%)', fontsize=11, fontweight='bold')
    ax4.set_title('Baseline vs S2 Switching', fontsize=12, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels([t.replace('_', '\n') for t in topologies], fontsize=9)
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)
    
    # Panel 5-9: S2 Activation Over Time for Each Topology
    for i, topo in enumerate(topologies):
        ax = fig.add_subplot(gs[2, i % 3] if i < 3 else fig.add_subplot(gs[2, i - 3]))
        
        for scenario in scenarios:
            exp = [r for r in results if r['topology'] == topo and r['s2_scenario'] == scenario]
            if exp and exp[0]['status'] == 'SUCCESS' and 's2_activations_over_time' in exp[0]:
                days = list(range(len(exp[0]['s2_activations_over_time'])))
                s2_over_time = exp[0]['s2_activations_over_time']
                # Normalize by population
                s2_rate_over_time = [(s / 5000) * 100 for s in s2_over_time]
                ax.plot(days, s2_rate_over_time, label=scenario.replace('_', ' ').title(), 
                       linewidth=2, alpha=0.8)
        
        ax.set_xlabel('Day', fontsize=10)
        ax.set_ylabel('S2 Rate (%)', fontsize=10)
        ax.set_title(f'{topo.replace("_", " ").title()}', fontsize=11, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    
    plt.suptitle('Topology Sensitivity Analysis: S1/S2 Dual-Process Decision-Making',
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Save
    output_file = Path("results/figures/colleague_meeting_topology_sensitivity.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.pdf'), bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    
    plt.close()


def create_s1s2_comparison_figure(results):
    """Figure 2: S1/S2 Switching Comparison."""
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    topologies = ['star', 'linear', 'hierarchical', 'regular_grid', 'irregular_grid']
    scenarios = ['baseline', 'low_s2', 'medium_s2', 'high_s2']
    
    # Panel 1: S2 Activation Rate Heatmap
    ax1 = fig.add_subplot(gs[0, :2])
    
    data_matrix = []
    for topo in topologies:
        row = []
        for scenario in scenarios:
            exp = [r for r in results if r['topology'] == topo and r['s2_scenario'] == scenario]
            if exp and exp[0]['status'] == 'SUCCESS':
                row.append(exp[0]['s2_activation_rate'])
            else:
                row.append(0)
        data_matrix.append(row)
    
    im = ax1.imshow(data_matrix, cmap='YlOrRd', aspect='auto')
    ax1.set_xticks(np.arange(len(scenarios)))
    ax1.set_yticks(np.arange(len(topologies)))
    ax1.set_xticklabels([s.replace('_', ' ').title() for s in scenarios])
    ax1.set_yticklabels([t.replace('_', ' ').title() for t in topologies])
    
    # Add text annotations
    for i in range(len(topologies)):
        for j in range(len(scenarios)):
            text = ax1.text(j, i, f'{data_matrix[i][j]:.1f}%',
                          ha="center", va="center", color="black", fontsize=10, fontweight='bold')
    
    ax1.set_title('S2 Activation Rate Heatmap', fontsize=13, fontweight='bold')
    plt.colorbar(im, ax=ax1, label='S2 Activation Rate (%)')
    
    # Panel 2: S2 Scenario Sensitivity
    ax2 = fig.add_subplot(gs[0, 2])
    
    scenario_means = []
    scenario_stds = []
    for scenario in scenarios:
        rates = [r['s2_activation_rate'] for r in results 
                if r['s2_scenario'] == scenario and r['status'] == 'SUCCESS']
        scenario_means.append(np.mean(rates) if rates else 0)
        scenario_stds.append(np.std(rates) if rates else 0)
    
    ax2.bar(range(len(scenarios)), scenario_means, yerr=scenario_stds, 
           color=sns.color_palette("husl", len(scenarios)), capsize=5)
    ax2.set_xticks(range(len(scenarios)))
    ax2.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax2.set_ylabel('Mean S2 Activation Rate (%)', fontsize=11, fontweight='bold')
    ax2.set_title('S2 Scenario Sensitivity\n(across all topologies)', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Panel 3: Topology Sensitivity
    ax3 = fig.add_subplot(gs[1, 0])
    
    topo_means = []
    topo_stds = []
    for topo in topologies:
        rates = [r['s2_activation_rate'] for r in results 
                if r['topology'] == topo and r['status'] == 'SUCCESS']
        topo_means.append(np.mean(rates) if rates else 0)
        topo_stds.append(np.std(rates) if rates else 0)
    
    ax3.barh(range(len(topologies)), topo_means, xerr=topo_stds,
            color=sns.color_palette("husl", len(topologies)), capsize=5)
    ax3.set_yticks(range(len(topologies)))
    ax3.set_yticklabels([t.replace('_', ' ').title() for t in topologies])
    ax3.set_xlabel('Mean S2 Activation Rate (%)', fontsize=11, fontweight='bold')
    ax3.set_title('Topology Sensitivity\n(across all scenarios)', fontsize=12, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)
    
    # Panel 4: S2 Threshold Effect
    ax4 = fig.add_subplot(gs[1, 1])
    
    thresholds = [0.0, 0.3, 0.5, 0.7]  # baseline, low, medium, high
    
    for topo in topologies:
        topo_rates = []
        for scenario in scenarios:
            exp = [r for r in results if r['topology'] == topo and r['s2_scenario'] == scenario]
            if exp and exp[0]['status'] == 'SUCCESS':
                topo_rates.append(exp[0]['s2_activation_rate'])
            else:
                topo_rates.append(0)
        ax4.plot(thresholds, topo_rates, marker='o', label=topo.replace('_', ' ').title(),
                linewidth=2, markersize=8)
    
    ax4.set_xlabel('S2 Threshold', fontsize=11, fontweight='bold')
    ax4.set_ylabel('S2 Activation Rate (%)', fontsize=11, fontweight='bold')
    ax4.set_title('S2 Threshold Effect', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=8)
    ax4.grid(alpha=0.3)
    
    # Panel 5: Summary Statistics
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')
    
    # Calculate summary stats
    all_rates = [r['s2_activation_rate'] for r in results if r['status'] == 'SUCCESS']
    baseline_rates = [r['s2_activation_rate'] for r in results 
                     if r['s2_scenario'] == 'baseline' and r['status'] == 'SUCCESS']
    s2_rates = [r['s2_activation_rate'] for r in results 
               if r['s2_scenario'] != 'baseline' and r['status'] == 'SUCCESS']
    
    summary_text = f"""
    📊 SUMMARY STATISTICS
    
    Overall:
    • Mean S2 Rate: {np.mean(all_rates):.1f}%
    • Std Dev: {np.std(all_rates):.1f}%
    • Range: [{np.min(all_rates):.1f}%, {np.max(all_rates):.1f}%]
    
    Baseline (No S2):
    • Mean: {np.mean(baseline_rates):.1f}%
    • Std Dev: {np.std(baseline_rates):.1f}%
    
    S2 Switching:
    • Mean: {np.mean(s2_rates):.1f}%
    • Std Dev: {np.std(s2_rates):.1f}%
    
    Effect Size:
    • Δ Mean: {np.mean(s2_rates) - np.mean(baseline_rates):.1f}%
    • Relative: {((np.mean(s2_rates) / np.mean(baseline_rates)) - 1) * 100:.1f}%
    
    Topology Sensitivity:
    • Max Variance: {np.max(topo_stds):.1f}%
    • Min Variance: {np.min(topo_stds):.1f}%
    """
    
    ax5.text(0.1, 0.5, summary_text, fontsize=10, verticalalignment='center',
            family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.suptitle('S1/S2 Switching Analysis: Parameterization and Sensitivity',
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Save
    output_file = Path("results/figures/colleague_meeting_s1s2_comparison.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(output_file.with_suffix('.pdf'), bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    
    plt.close()


def main():
    """Generate all colleague meeting figures."""
    
    print("=" * 70)
    print("📊 GENERATING COLLEAGUE MEETING FIGURES")
    print("=" * 70)
    print()
    
    # Load results
    results = load_results()
    
    if results is None:
        return
    
    print(f"Loaded {len(results)} experiment results")
    print()
    
    # Generate figures
    print("Creating figures...")
    create_topology_sensitivity_figure(results)
    create_s1s2_comparison_figure(results)
    
    print()
    print("=" * 70)
    print("✅ ALL FIGURES GENERATED")
    print("=" * 70)
    print()
    print("Figures saved to: results/figures/")
    print("  • colleague_meeting_topology_sensitivity.png/pdf")
    print("  • colleague_meeting_s1s2_comparison.png/pdf")
    print()


if __name__ == "__main__":
    main()




