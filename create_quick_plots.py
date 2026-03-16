#!/usr/bin/env python3
"""Quick plots for colleague meeting from archived data"""

import json
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from pathlib import Path
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams['font.size'] = 11

# Load archived results
with open("archive/old_results/archived_20251026_034930/proper_10k_agent_experiments/all_10k_agent_results.json", 'r') as f:
    data = json.load(f)

experiments = data['experiments']

# Create figure with 4 key plots
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Plot 1: S2 Activation by Topology
ax1 = fig.add_subplot(gs[0, 0])
topologies = {}
for exp in experiments:
    topo = exp['topology']
    if topo not in topologies:
        topologies[topo] = []
    topologies[topo].append(exp['s2_rate'] * 100)

topo_names = list(topologies.keys())
topo_means = [np.mean(topologies[t]) for t in topo_names]
topo_stds = [np.std(topologies[t]) for t in topo_names]

ax1.bar(range(len(topo_names)), topo_means, yerr=topo_stds, capsize=5, 
        color=['#3498db', '#e74c3c', '#2ecc71'])
ax1.set_xticks(range(len(topo_names)))
ax1.set_xticklabels([t.capitalize() for t in topo_names])
ax1.set_ylabel('S2 Activation Rate (%)', fontweight='bold')
ax1.set_title('S2 Activation by Network Topology', fontsize=13, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

# Plot 2: S2 Activation by Network Size
ax2 = fig.add_subplot(gs[0, 1])
sizes = {}
for exp in experiments:
    size = exp['network_size']
    if size not in sizes:
        sizes[size] = []
    sizes[size].append(exp['s2_rate'] * 100)

size_nums = sorted(sizes.keys())
size_means = [np.mean(sizes[s]) for s in size_nums]
size_stds = [np.std(sizes[s]) for s in size_nums]

ax2.bar(range(len(size_nums)), size_means, yerr=size_stds, capsize=5,
        color=['#9b59b6', '#f39c12', '#1abc9c'])
ax2.set_xticks(range(len(size_nums)))
ax2.set_xticklabels([f'{s} nodes' for s in size_nums])
ax2.set_ylabel('S2 Activation Rate (%)', fontweight='bold')
ax2.set_title('S2 Activation by Network Size', fontsize=13, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

# Plot 3: S2 Activation Over Time (example)
ax3 = fig.add_subplot(gs[1, :])
# Get one example from each topology
examples = {}
for exp in experiments:
    if exp['scenario'] == 'medium_s2' and exp['network_size'] == 8:
        examples[exp['topology']] = exp

days = list(range(20))
for topo, exp in examples.items():
    s2_acts = exp['s2_activations']
    s2_rates = [(s / exp['population_size']) * 100 for s in s2_acts]
    ax3.plot(days, s2_rates, marker='o', label=topo.capitalize(), linewidth=2, markersize=6)

ax3.set_xlabel('Day', fontweight='bold')
ax3.set_ylabel('S2 Activation Rate (%)', fontweight='bold')
ax3.set_title('S2 Activation Over Time (Medium S2, 8 nodes)', fontsize=13, fontweight='bold')
ax3.legend(loc='upper right')
ax3.grid(alpha=0.3)

# Plot 4: Agent Distribution Over Time (Grid example)
ax4 = fig.add_subplot(gs[2, :])
grid_exp = [e for e in experiments if e['topology'] == 'grid' and e['scenario'] == 'medium_s2' and e['network_size'] == 8][0]

# Stack plot of camp populations
days = []
camp_pops = {}

for day_result in grid_exp['daily_results']:
    days.append(day_result['day'])
    for camp, pop in day_result['camp_populations'].items():
        if camp not in camp_pops:
            camp_pops[camp] = []
        camp_pops[camp].append(pop)

# Plot origin and top 3 camps
origin_key = [k for k in camp_pops.keys() if 'Origin' in k][0]
camp_keys = [k for k in camp_pops.keys() if 'Camp' in k][:3]

ax4.plot(days, camp_pops[origin_key], label='Origin', linewidth=3, color='red')
colors = ['blue', 'green', 'orange']
for i, camp in enumerate(camp_keys):
    ax4.plot(days, camp_pops[camp], label=camp, linewidth=2, color=colors[i])

ax4.set_xlabel('Day', fontweight='bold')
ax4.set_ylabel('Agent Population', fontweight='bold')
ax4.set_title('Agent Movement Over Time (Grid, Medium S2, 8 nodes)', fontsize=13, fontweight='bold')
ax4.legend(loc='right')
ax4.grid(alpha=0.3)

plt.suptitle('S1/S2 Dual-Process Model: Key Results', fontsize=16, fontweight='bold', y=0.995)

# Save
output_file = Path("results/figures/quick_colleague_plots.png")
output_file.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.savefig(output_file.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output_file}")

plt.close()

# Create topology comparison figure
fig2, axes = plt.subplots(1, 3, figsize=(18, 5))

for i, (topo_name, ax) in enumerate(zip(['star', 'linear', 'grid'], axes)):
    # Get example experiment
    exp = [e for e in experiments if e['topology'] == topo_name and e['scenario'] == 'medium_s2' and e['network_size'] == 8][0]
    
    # Plot S2 activation over time
    days = list(range(20))
    s2_rates = [(s / exp['population_size']) * 100 for s in exp['s2_activations']]
    
    ax.plot(days, s2_rates, marker='o', linewidth=2, markersize=6, color='#3498db')
    ax.fill_between(days, s2_rates, alpha=0.3, color='#3498db')
    ax.set_xlabel('Day', fontweight='bold', fontsize=12)
    ax.set_ylabel('S2 Activation Rate (%)', fontweight='bold', fontsize=12)
    ax.set_title(f'{topo_name.capitalize()} Network', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 40)
    
    # Add mean line
    mean_s2 = np.mean(s2_rates)
    ax.axhline(mean_s2, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_s2:.1f}%')
    ax.legend()

plt.suptitle('S2 Activation Over Time by Topology (Medium S2, 8 nodes)', fontsize=16, fontweight='bold')
plt.tight_layout()

output_file2 = Path("results/figures/topology_comparison.png")
plt.savefig(output_file2, dpi=300, bbox_inches='tight')
plt.savefig(output_file2.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output_file2}")

print("\n📊 Quick plots created!")
print(f"   • results/figures/quick_colleague_plots.png")
print(f"   • results/figures/topology_comparison.png")



