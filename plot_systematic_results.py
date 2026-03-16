import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# Load systematic results
df = pd.read_csv("systematic_results/summary_fixed.csv")

# 1. Scaling of Delay vs Size (N) by Topology
plt.figure(figsize=(12, 8))
topologies = df['Topology'].unique()
colors = plt.cm.tab10(range(len(topologies)))

for i, topo in enumerate(topologies):
    subset = df[df['Topology'] == topo]
    # Calculate Delay Factor: AvgTime / (Ideal Time roughly)
    # We don't have ideal time in this summary, so we use raw AvgTime normalized by N or similar?
    # Better: Just plot AvgTime vs N to show scaling scaling class (linear, log, etc)
    
    # Separate Sparse/Dense
    sparse = subset[subset['Dense'] == False]
    dense = subset[subset['Dense'] == True]
    
    plt.plot(sparse['N'], sparse['AvgTime'], 'o--', label=f"{topo} (Sparse)", color=colors[i], alpha=0.7)
    plt.plot(dense['N'], dense['AvgTime'], 's-', label=f"{topo} (Dense)", color=colors[i])

plt.xlabel("Network Size (Nodes)")
plt.ylabel("Average Travel Time (Days)")
plt.title("Scaling of Refugee Travel Time by Topology")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("systematic_results/scaling_laws.png")
plt.close()

# 2. Impact of Density on Efficiency
# Bar chart of AvgTime improvement from Dense connectivity
plt.figure(figsize=(12, 6))
improvements = []
topo_labels = []

for topo in topologies:
    subset = df[df['Topology'] == topo]
    # Compare N=100
    s_100 = subset[(subset['N'] == 100) & (subset['Dense'] == False)]['AvgTime'].values
    d_100 = subset[(subset['N'] == 100) & (subset['Dense'] == True)]['AvgTime'].values
    
    if len(s_100) > 0 and len(d_100) > 0:
        improvement = (s_100[0] - d_100[0]) / s_100[0] * 100
        improvements.append(improvement)
        topo_labels.append(topo)

plt.bar(topo_labels, improvements, color='green', alpha=0.7)
plt.axhline(0, color='black', linewidth=1)
plt.xlabel("Topology")
plt.ylabel("Efficiency Gain from High Density (%)")
plt.title("Impact of Redundant Connectivity (N=100)")
plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig("systematic_results/density_impact.png")
plt.close()

print("Systematic plots generated.")

