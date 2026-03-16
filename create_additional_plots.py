#!/usr/bin/env python3
"""Create additional plots for colleague meeting"""

import json
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from pathlib import Path
import seaborn as sns

sns.set_style("whitegrid")

# Load archived results
with open("archive/old_results/archived_20251026_034930/proper_10k_agent_experiments/all_10k_agent_results.json", 'r') as f:
    data = json.load(f)

experiments = data['experiments']

# ============================================================================
# PLOT 1: S2 Activation Heatmap (Topology × Threshold)
# ============================================================================
fig1, ax1 = plt.subplots(figsize=(10, 6))

topologies = ['star', 'linear', 'grid']
scenarios = ['low_s2', 'medium_s2', 'high_s2']
heatmap_data = np.zeros((len(topologies), len(scenarios)))

for i, topo in enumerate(topologies):
    for j, scenario in enumerate(scenarios):
        exps = [e for e in experiments if e['topology'] == topo and e['scenario'] == scenario]
        if exps:
            heatmap_data[i, j] = np.mean([e['s2_rate'] * 100 for e in exps])

im = ax1.imshow(heatmap_data, cmap='YlOrRd', aspect='auto', vmin=25, vmax=35)
ax1.set_xticks(range(len(scenarios)))
ax1.set_yticks(range(len(topologies)))
ax1.set_xticklabels([s.replace('_s2', ' S2').title() for s in scenarios], fontsize=12)
ax1.set_yticklabels([t.capitalize() for t in topologies], fontsize=12)

# Add text annotations
for i in range(len(topologies)):
    for j in range(len(scenarios)):
        text = ax1.text(j, i, f'{heatmap_data[i, j]:.1f}%',
                       ha="center", va="center", color="black", 
                       fontsize=14, fontweight='bold')

ax1.set_title('S2 Activation Rate: Topology × Threshold', fontsize=16, fontweight='bold', pad=20)
ax1.set_xlabel('S2 Threshold Scenario', fontsize=13, fontweight='bold')
ax1.set_ylabel('Network Topology', fontsize=13, fontweight='bold')
plt.colorbar(im, ax=ax1, label='S2 Activation Rate (%)')
plt.tight_layout()

output1 = Path("results/figures/s2_heatmap.png")
plt.savefig(output1, dpi=300, bbox_inches='tight')
plt.savefig(output1.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output1}")
plt.close()

# ============================================================================
# PLOT 2: Network Scaling Analysis (Size × S2 Rate)
# ============================================================================
fig2, ax2 = plt.subplots(figsize=(10, 6))

sizes = [4, 8, 16]
scenarios = ['low_s2', 'medium_s2', 'high_s2']
colors = {'low_s2': '#e74c3c', 'medium_s2': '#3498db', 'high_s2': '#2ecc71'}

for scenario in scenarios:
    means = []
    stds = []
    for size in sizes:
        exps = [e for e in experiments if e['network_size'] == size and e['scenario'] == scenario]
        if exps:
            rates = [e['s2_rate'] * 100 for e in exps]
            means.append(np.mean(rates))
            stds.append(np.std(rates))
        else:
            means.append(0)
            stds.append(0)
    
    ax2.errorbar(sizes, means, yerr=stds, marker='o', markersize=10, 
                linewidth=2, capsize=5, label=scenario.replace('_s2', ' S2').title(),
                color=colors[scenario])

ax2.set_xlabel('Network Size (nodes)', fontsize=13, fontweight='bold')
ax2.set_ylabel('S2 Activation Rate (%)', fontsize=13, fontweight='bold')
ax2.set_title('Network Size Effect on S2 Activation', fontsize=16, fontweight='bold')
ax2.legend(fontsize=12, loc='lower right')
ax2.grid(alpha=0.3)
ax2.set_xticks(sizes)
ax2.set_xticklabels([f'{s}' for s in sizes])
plt.tight_layout()

output2 = Path("results/figures/network_scaling.png")
plt.savefig(output2, dpi=300, bbox_inches='tight')
plt.savefig(output2.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output2}")
plt.close()

# ============================================================================
# PLOT 3: Camp Distribution Patterns (End of simulation)
# ============================================================================
fig3, axes = plt.subplots(1, 3, figsize=(18, 5))

for idx, topo in enumerate(['star', 'linear', 'grid']):
    ax = axes[idx]
    
    # Get medium_s2, size 8 example
    exp = [e for e in experiments if e['topology'] == topo and 
           e['scenario'] == 'medium_s2' and e['network_size'] == 8][0]
    
    # Get final day camp populations
    final_day = exp['daily_results'][-1]
    camps = {}
    for loc, pop in final_day['camp_populations'].items():
        if 'Camp' in loc:
            camps[loc] = pop
    
    # Sort by population
    sorted_camps = sorted(camps.items(), key=lambda x: x[1], reverse=True)
    camp_names = [c[0].replace(f'_{topo}_{exp["network_size"]}', '') for c in sorted_camps]
    camp_pops = [c[1] for c in sorted_camps]
    
    colors_list = plt.cm.viridis(np.linspace(0, 0.8, len(camp_names)))
    ax.bar(range(len(camp_names)), camp_pops, color=colors_list)
    ax.set_xticks(range(len(camp_names)))
    ax.set_xticklabels(camp_names, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('Agent Population', fontsize=12, fontweight='bold')
    ax.set_title(f'{topo.capitalize()} Network', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add total
    total = sum(camp_pops)
    ax.text(0.95, 0.95, f'Total: {total:,}', transform=ax.transAxes,
           fontsize=11, fontweight='bold', ha='right', va='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.suptitle('Final Agent Distribution Across Camps (Day 20, Medium S2)', 
             fontsize=16, fontweight='bold')
plt.tight_layout()

output3 = Path("results/figures/camp_distribution.png")
plt.savefig(output3, dpi=300, bbox_inches='tight')
plt.savefig(output3.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output3}")
plt.close()

# ============================================================================
# PLOT 4: S2 Temporal Dynamics (All experiments combined)
# ============================================================================
fig4, ax4 = plt.subplots(figsize=(12, 6))

# Combine all medium_s2 experiments
all_s2_rates = {day: [] for day in range(20)}

for exp in experiments:
    if exp['scenario'] == 'medium_s2':
        for day, s2_count in enumerate(exp['s2_activations']):
            s2_rate = (s2_count / exp['population_size']) * 100
            all_s2_rates[day].append(s2_rate)

days = list(range(20))
means = [np.mean(all_s2_rates[d]) for d in days]
stds = [np.std(all_s2_rates[d]) for d in days]
upper = [means[i] + stds[i] for i in range(20)]
lower = [means[i] - stds[i] for i in range(20)]

ax4.plot(days, means, linewidth=3, color='#3498db', label='Mean S2 Rate')
ax4.fill_between(days, lower, upper, alpha=0.3, color='#3498db', label='±1 Std Dev')

# Mark phases
ax4.axvspan(0, 2, alpha=0.1, color='red', label='Crisis Phase')
ax4.axvspan(2, 5, alpha=0.1, color='orange', label='Dispersal Phase')
ax4.axvspan(5, 20, alpha=0.1, color='green', label='Stabilization Phase')

ax4.set_xlabel('Day', fontsize=13, fontweight='bold')
ax4.set_ylabel('S2 Activation Rate (%)', fontsize=13, fontweight='bold')
ax4.set_title('S2 Activation Temporal Dynamics (All Medium S2 Experiments)', 
             fontsize=16, fontweight='bold')
ax4.legend(fontsize=11, loc='upper right')
ax4.grid(alpha=0.3)
plt.tight_layout()

output4 = Path("results/figures/s2_temporal_dynamics.png")
plt.savefig(output4, dpi=300, bbox_inches='tight')
plt.savefig(output4.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output4}")
plt.close()

# ============================================================================
# PLOT 5: Summary Dashboard
# ============================================================================
fig5 = plt.figure(figsize=(16, 10))
gs = fig5.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

# Panel 1: Overall S2 rate distribution
ax1 = fig5.add_subplot(gs[0, 0])
all_rates = [e['s2_rate'] * 100 for e in experiments]
ax1.hist(all_rates, bins=15, color='#3498db', alpha=0.7, edgecolor='black')
ax1.axvline(np.mean(all_rates), color='red', linestyle='--', linewidth=2, 
           label=f'Mean: {np.mean(all_rates):.1f}%')
ax1.set_xlabel('S2 Activation Rate (%)', fontweight='bold')
ax1.set_ylabel('Count', fontweight='bold')
ax1.set_title('Distribution of S2 Rates', fontweight='bold')
ax1.legend()
ax1.grid(alpha=0.3)

# Panel 2: Total distance by topology
ax2 = fig5.add_subplot(gs[0, 1])
topo_distances = {}
for exp in experiments:
    topo = exp['topology']
    if topo not in topo_distances:
        topo_distances[topo] = []
    topo_distances[topo].append(exp['total_distance'] / 1e6)  # Convert to millions

topo_names = list(topo_distances.keys())
topo_means = [np.mean(topo_distances[t]) for t in topo_names]
ax2.bar(range(len(topo_names)), topo_means, color=['#e74c3c', '#2ecc71', '#f39c12'])
ax2.set_xticks(range(len(topo_names)))
ax2.set_xticklabels([t.capitalize() for t in topo_names])
ax2.set_ylabel('Total Distance (Million km)', fontweight='bold')
ax2.set_title('Total Distance Traveled', fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

# Panel 3: Destinations reached
ax3 = fig5.add_subplot(gs[0, 2])
dest_reached = [e['destinations_reached'] for e in experiments]
ax3.hist(dest_reached, bins=range(1, max(dest_reached)+2), color='#2ecc71', 
        alpha=0.7, edgecolor='black')
ax3.set_xlabel('Number of Destinations', fontweight='bold')
ax3.set_ylabel('Count', fontweight='bold')
ax3.set_title('Camp Utilization', fontweight='bold')
ax3.grid(alpha=0.3)

# Panel 4: S2 by topology (box plot)
ax4 = fig5.add_subplot(gs[1, :2])
data_by_topo = [topo_distances[t] for t in ['star', 'linear', 'grid']]
s2_by_topo = [[e['s2_rate']*100 for e in experiments if e['topology'] == t] 
              for t in ['star', 'linear', 'grid']]
bp = ax4.boxplot(s2_by_topo, labels=['Star', 'Linear', 'Grid'], patch_artist=True)
for patch, color in zip(bp['boxes'], ['#e74c3c', '#2ecc71', '#f39c12']):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax4.set_ylabel('S2 Activation Rate (%)', fontweight='bold')
ax4.set_title('S2 Distribution by Topology', fontweight='bold')
ax4.grid(axis='y', alpha=0.3)

# Panel 5: Summary statistics
ax5 = fig5.add_subplot(gs[1, 2])
ax5.axis('off')

summary_text = f"""
📊 SUMMARY STATISTICS

Total Experiments: {len(experiments)}
Total Agent-Days: {len(experiments) * 10000 * 20:,}

S2 Activation:
• Mean: {np.mean(all_rates):.1f}%
• Std Dev: {np.std(all_rates):.1f}%
• Range: [{min(all_rates):.1f}%, {max(all_rates):.1f}%]

By Topology:
• Star: {np.mean([e['s2_rate']*100 for e in experiments if e['topology']=='star']):.1f}%
• Linear: {np.mean([e['s2_rate']*100 for e in experiments if e['topology']=='linear']):.1f}%
• Grid: {np.mean([e['s2_rate']*100 for e in experiments if e['topology']=='grid']):.1f}%

Total Distance:
• {sum([e['total_distance'] for e in experiments])/1e6:.0f} Million km

Camps Utilized:
• Mean: {np.mean(dest_reached):.1f} camps
• Max: {max(dest_reached)} camps
"""

ax5.text(0.1, 0.5, summary_text, fontsize=10, verticalalignment='center',
        family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# Panel 6: S2 activation over time (mean across all)
ax6 = fig5.add_subplot(gs[2, :])
days = list(range(20))
all_s2_over_time = {d: [] for d in days}
for exp in experiments:
    for day, s2_count in enumerate(exp['s2_activations']):
        all_s2_over_time[day].append((s2_count / exp['population_size']) * 100)

means = [np.mean(all_s2_over_time[d]) for d in days]
ax6.plot(days, means, linewidth=3, marker='o', markersize=8, color='#3498db')
ax6.fill_between(days, 
                 [means[i] - np.std(all_s2_over_time[i]) for i in days],
                 [means[i] + np.std(all_s2_over_time[i]) for i in days],
                 alpha=0.3, color='#3498db')
ax6.set_xlabel('Day', fontweight='bold', fontsize=12)
ax6.set_ylabel('S2 Activation Rate (%)', fontweight='bold', fontsize=12)
ax6.set_title('Mean S2 Activation Over Time (All Experiments)', fontweight='bold', fontsize=13)
ax6.grid(alpha=0.3)

plt.suptitle('S1/S2 Dual-Process Model: Comprehensive Dashboard', 
            fontsize=18, fontweight='bold')

output5 = Path("results/figures/comprehensive_dashboard.png")
plt.savefig(output5, dpi=300, bbox_inches='tight')
plt.savefig(output5.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output5}")
plt.close()

print("\n🎉 All additional plots created!")
print(f"\n📊 New figures:")
print(f"   1. results/figures/s2_heatmap.png")
print(f"   2. results/figures/network_scaling.png")
print(f"   3. results/figures/camp_distribution.png")
print(f"   4. results/figures/s2_temporal_dynamics.png")
print(f"   5. results/figures/comprehensive_dashboard.png")



