#!/usr/bin/env python3
"""Create network topology diagrams"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from pathlib import Path

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Star network
ax = axes[0]
G_star = nx.Graph()
nodes = ['Origin'] + [f'Camp_{i}' for i in range(1, 8)]
G_star.add_node('Origin')
for i in range(1, 8):
    G_star.add_edge('Origin', f'Camp_{i}')

pos_star = {'Origin': (0, 0)}
for i in range(1, 8):
    angle = 2 * np.pi * (i-1) / 7
    pos_star[f'Camp_{i}'] = (np.cos(angle), np.sin(angle))

nx.draw_networkx_nodes(G_star, pos_star, node_color=['red'] + ['lightblue']*7, 
                       node_size=[1500] + [800]*7, ax=ax)
nx.draw_networkx_edges(G_star, pos_star, width=2, ax=ax)
nx.draw_networkx_labels(G_star, pos_star, font_size=8, ax=ax)
ax.set_title('Star Network (Hub-and-Spoke)', fontsize=14, fontweight='bold')
ax.axis('off')

# Linear network
ax = axes[1]
G_linear = nx.Graph()
nodes = ['Origin'] + [f'Node_{i}' for i in range(1, 8)]
for i in range(len(nodes)-1):
    G_linear.add_edge(nodes[i], nodes[i+1])

pos_linear = {nodes[i]: (i, 0) for i in range(len(nodes))}

nx.draw_networkx_nodes(G_linear, pos_linear, node_color=['red'] + ['lightblue']*7,
                       node_size=[1500] + [800]*7, ax=ax)
nx.draw_networkx_edges(G_linear, pos_linear, width=2, ax=ax)
nx.draw_networkx_labels(G_linear, pos_linear, font_size=8, ax=ax)
ax.set_title('Linear Network (Chain)', fontsize=14, fontweight='bold')
ax.axis('off')

# Grid network
ax = axes[2]
G_grid = nx.grid_2d_graph(3, 3)
pos_grid = {node: node for node in G_grid.nodes()}

# Relabel nodes
node_mapping = {}
idx = 0
for node in sorted(G_grid.nodes()):
    if idx == 0:
        node_mapping[node] = 'Origin'
    else:
        node_mapping[node] = f'Node_{idx}'
    idx += 1

G_grid = nx.relabel_nodes(G_grid, node_mapping)
pos_grid_new = {node_mapping[k]: v for k, v in pos_grid.items()}

node_colors = ['red'] + ['lightblue']* (len(G_grid.nodes())-1)
node_sizes = [1500] + [800]* (len(G_grid.nodes())-1)

nx.draw_networkx_nodes(G_grid, pos_grid_new, node_color=node_colors,
                       node_size=node_sizes, ax=ax)
nx.draw_networkx_edges(G_grid, pos_grid_new, width=2, ax=ax)
nx.draw_networkx_labels(G_grid, pos_grid_new, font_size=7, ax=ax)
ax.set_title('Grid Network (2D Lattice)', fontsize=14, fontweight='bold')
ax.axis('off')

plt.suptitle('Network Topologies for S1/S2 Testing', fontsize=16, fontweight='bold')
plt.tight_layout()

output_file = Path("results/figures/network_topologies.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.savefig(output_file.with_suffix('.pdf'), bbox_inches='tight')
print(f"✅ Saved: {output_file}")



