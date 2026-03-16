#!/usr/bin/env python3
"""
Plot Comprehensive Heuristics Analysis
Generates figures for the Scientific Reports paper.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# Load results
with open("data/comprehensive/summary.json", "r") as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame.from_dict(data, orient='index')
df['topology'] = df.index

# Constants
MAX_MOVE_SPEED = 20.0 # km/day

# Calculate Ideal Travel Time (Heuristic / Speed)
df['ideal_travel_time'] = df['heuristic_distance'] / MAX_MOVE_SPEED

# Calculate Delay Factor (Actual / Ideal)
df['delay_factor'] = df['avg_travel_time'] / df['ideal_travel_time']

print("Analyzed Data:")
print(df[['topology', 'avg_travel_time', 'ideal_travel_time', 'delay_factor']])

# =============================================================================
# Plot 1: Heuristic vs Actual Travel Time
# =============================================================================
plt.figure(figsize=(10, 8))
plt.style.use('default')

# Scatter plot
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
markers = ['o', 's', '^', 'D']

for i, (idx, row) in enumerate(df.iterrows()):
    plt.scatter(row['ideal_travel_time'], row['avg_travel_time'], 
                s=300, c=colors[i], marker=markers[i], label=idx, zorder=3,
                edgecolors='black', linewidth=1.5)

# Ideal line (y=x)
max_val = max(df['avg_travel_time'].max(), df['ideal_travel_time'].max()) * 1.1
plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label='Ideal (No Delay)')

# Add delay factor labels
for i, (idx, row) in enumerate(df.iterrows()):
    plt.text(row['ideal_travel_time'], row['avg_travel_time'] + 0.5, 
             f"{row['delay_factor']:.1f}x Delay", 
             ha='center', va='bottom', fontweight='bold', fontsize=10)

plt.xlabel('Heuristic Travel Time (Distance / Speed) [Days]', fontsize=12, fontweight='bold')
plt.ylabel('Actual Agent Travel Time [Days]', fontsize=12, fontweight='bold')
plt.title('Topology Predictability:\nWhen do simple heuristics fail?', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.tight_layout()

plt.savefig('data/comprehensive/heuristic_vs_actual.png', dpi=300)
print("✅ Saved plot: heuristic_vs_actual.png")

# =============================================================================
# Plot 2: Delay Factor by Topology
# =============================================================================
plt.figure(figsize=(10, 6))

bars = plt.bar(df['topology'], df['delay_factor'], color=colors, edgecolor='black', alpha=0.8)

plt.axhline(y=1.0, color='k', linestyle='--', linewidth=2, label='Ideal')

# Labels
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
             f'{height:.1f}x',
             ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.ylabel('Delay Factor (Actual / Heuristic)', fontsize=12, fontweight='bold')
plt.title('Network Inefficiency by Topology', fontsize=14, fontweight='bold')
plt.ylim(0, max(df['delay_factor']) * 1.2)
plt.grid(axis='y', alpha=0.3)

# Add descriptions below x-axis
descriptions = {
    "Hierarchical": "Bottlenecks at\nintermediate nodes",
    "Lattice": "Resilient:\nMultiple paths",
    "Bottleneck": "Congestion at\nborder crossing",
    "HubAndSpoke": "Efficient transit\nvia central hub"
}

# Add text boxes below bars
# This is tricky with standard matplot, simplified to print logic for now.

plt.tight_layout()
plt.savefig('data/comprehensive/delay_factor.png', dpi=300)
print("✅ Saved plot: delay_factor.png")


