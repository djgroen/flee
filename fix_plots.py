import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# Load results
df = pd.read_csv("data/sweep/sweep_summary.csv")

# Fix Topology labels
def fix_topology(run_id):
    if "Lat" in run_id:
        return "Lattice"
    elif "Hier" in run_id:
        return "Hierarchical"
    else:
        return "Unknown"

df['Topology'] = df['RunID'].apply(fix_topology)

# Save fixed CSV
df.to_csv("data/sweep/sweep_summary_fixed.csv", index=False)

# Regenerate Plots
output_dir = Path("data/sweep")

# 1. Delay Factor vs Saturation
plt.figure(figsize=(10, 6))
for topo in df['Topology'].unique():
    subset = df[df['Topology'] == topo]
    plt.scatter(subset['Saturation'], subset['DelayFactor'], label=topo, s=100)
plt.xlabel("Agent Saturation (Agents / Capacity)")
plt.ylabel("Delay Factor (Actual / Ideal Time)")
plt.title("Impact of Congestion on Travel Delay")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(output_dir / "delay_vs_saturation_fixed.png")
plt.close()

# 2. Delay vs Network Size (Nodes)
plt.figure(figsize=(10, 6))
for topo in df['Topology'].unique():
    subset = df[df['Topology'] == topo]
    plt.scatter(subset['Nodes'], subset['DelayFactor'], label=topo, s=100)
plt.xlabel("Network Size (Nodes)")
plt.ylabel("Delay Factor")
plt.title("Scaling of Delay with Network Size")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(output_dir / "delay_vs_size_fixed.png")
plt.close()

# 3. Delay vs Connectivity (Avg Degree) - New Plot
plt.figure(figsize=(10, 6))
for topo in df['Topology'].unique():
    subset = df[df['Topology'] == topo]
    plt.scatter(subset['AvgDegree'], subset['DelayFactor'], label=topo, s=100)
plt.xlabel("Connectivity (Average Degree)")
plt.ylabel("Delay Factor")
plt.title("Impact of Connectivity on Delay")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(output_dir / "delay_vs_connectivity.png")
plt.close()

print("Plots regenerated.")


