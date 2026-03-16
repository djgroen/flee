#!/usr/bin/env python3
"""
Generate Network Topology Maps
- Create visualizations showing nodes, links, and agent flows
- Network topology diagrams with spatial layout
- Agent flow visualization on network structures
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

class NetworkTopologyMapGenerator:
    """Generate network topology maps with nodes, links, and flows"""
    
    def __init__(self, results_dir="organized_s1s2_experiments"):
        self.results_dir = Path(results_dir)
        self.figures_dir = self.results_dir / "02_figures"
        self.network_maps_dir = self.figures_dir / "network_topology_maps"
        self.network_maps_dir.mkdir(exist_ok=True)
        
        # Load experimental results
        self.results = self._load_results()
        self.df = self._create_dataframe()
        
        # Network topology definitions
        self.topology_definitions = self._define_topologies()
        
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
    
    def _define_topologies(self):
        """Define network topology structures"""
        return {
            'linear': {
                'description': 'Linear chain network',
                'layout': 'linear',
                'node_positions': lambda n: {i: (i * 2, 0) for i in range(n)},
                'edges': lambda n: [(i, i+1) for i in range(n-1)]
            },
            'star': {
                'description': 'Star network with central hub',
                'layout': 'star',
                'node_positions': lambda n: self._star_positions(n),
                'edges': lambda n: self._star_edges(n)
            },
            'tree': {
                'description': 'Binary tree network',
                'layout': 'tree',
                'node_positions': lambda n: self._tree_positions(n),
                'edges': lambda n: self._tree_edges(n)
            },
            'grid': {
                'description': 'Square grid network',
                'layout': 'grid',
                'node_positions': lambda n: self._grid_positions(n),
                'edges': lambda n: self._grid_edges(n)
            }
        }
    
    def _star_positions(self, n):
        """Generate star network positions"""
        positions = {0: (0, 0)}  # Center node
        if n > 1:
            positions[1] = (3, 0)  # Hub
            for i in range(2, n):
                angle = 2 * np.pi * (i - 2) / (n - 2)
                x = 6 * np.cos(angle)
                y = 6 * np.sin(angle)
                positions[i] = (x, y)
        return positions
    
    def _star_edges(self, n):
        """Generate star network edges"""
        edges = [(0, 1)]  # Origin to hub
        for i in range(2, n):
            edges.append((1, i))  # Hub to each camp
        return edges
    
    def _tree_positions(self, n):
        """Generate tree network positions"""
        positions = {0: (0, 0)}  # Root
        current_level = 1
        level_y = 0
        
        for i in range(1, n):
            if i >= 2 ** current_level:
                current_level += 1
                level_y += 3
            
            level_width = 2 ** (current_level - 1)
            level_pos = i - (2 ** (current_level - 1)) + 1
            x = (level_pos - level_width/2 - 0.5) * 3
            y = level_y
            
            positions[i] = (x, y)
        
        return positions
    
    def _tree_edges(self, n):
        """Generate tree network edges"""
        edges = []
        for i in range(1, n):
            parent = (i - 1) // 2
            edges.append((parent, i))
        return edges
    
    def _grid_positions(self, n):
        """Generate grid network positions"""
        grid_size = int(np.ceil(np.sqrt(n)))
        positions = {}
        
        for i in range(n):
            row = i // grid_size
            col = i % grid_size
            positions[i] = (col * 2, row * 2)
        
        return positions
    
    def _grid_edges(self, n):
        """Generate grid network edges"""
        grid_size = int(np.ceil(np.sqrt(n)))
        edges = []
        
        for i in range(n):
            row = i // grid_size
            col = i % grid_size
            
            # Right neighbor
            if col < grid_size - 1 and i + 1 < n:
                edges.append((i, i + 1))
            
            # Bottom neighbor
            if row < grid_size - 1 and i + grid_size < n:
                edges.append((i, i + grid_size))
        
        return edges
    
    def generate_all_network_maps(self):
        """Generate all network topology maps"""
        
        print("🗺️ Generating Network Topology Maps")
        print("=" * 50)
        
        # Generate topology structure maps
        self._generate_topology_structure_maps()
        
        # Generate flow visualization maps
        self._generate_flow_visualization_maps()
        
        # Generate comparative network maps
        self._generate_comparative_network_maps()
        
        print(f"\n✅ All network topology maps generated!")
        print(f"🗺️ Maps saved to: {self.network_maps_dir}")
    
    def _generate_topology_structure_maps(self):
        """Generate network structure maps for each topology"""
        
        print("📊 Generating topology structure maps...")
        
        for topology in ['linear', 'star', 'tree', 'grid']:
            for size in [5, 7, 11]:
                self._create_topology_structure_map(topology, size)
    
    def _create_topology_structure_map(self, topology, size):
        """Create a single topology structure map"""
        
        # Create network
        G = nx.Graph()
        
        # Add nodes
        for i in range(size):
            G.add_node(i)
        
        # Add edges
        edges = self.topology_definitions[topology]['edges'](size)
        G.add_edges_from(edges)
        
        # Get positions
        pos = self.topology_definitions[topology]['node_positions'](size)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw network
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                              node_size=1000, alpha=0.8, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='gray', 
                              width=2, alpha=0.6, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)
        
        # Add title and labels
        ax.set_title(f'{topology.title()} Network (n={size})\n{self.topology_definitions[topology]["description"]}', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # Add network metrics
        metrics_text = f"""Network Metrics:
Nodes: {G.number_of_nodes()}
Edges: {G.number_of_edges()}
Density: {nx.density(G):.3f}
Average Degree: {np.mean([d for n, d in G.degree()]):.2f}"""
        
        ax.text(0.02, 0.98, metrics_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(self.network_maps_dir / f"{topology}_structure_n{size}.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.network_maps_dir / f"{topology}_structure_n{size}.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {topology.title()} structure map (n={size}) created")
    
    def _generate_flow_visualization_maps(self):
        """Generate flow visualization maps"""
        
        print("🌊 Generating flow visualization maps...")
        
        # Create flow maps for each topology and scenario
        for topology in ['linear', 'star', 'tree', 'grid']:
            for size in [5, 7, 11]:
                for scenario in ['low_s2', 'medium_s2', 'high_s2']:
                    self._create_flow_visualization_map(topology, size, scenario)
    
    def _create_flow_visualization_map(self, topology, size, scenario):
        """Create flow visualization map"""
        
        # Get experiment data
        exp_id = f"{topology}_{size}_{scenario}"
        if exp_id not in self.results:
            return
        
        exp_data = self.results[exp_id]
        s2_rate = exp_data['results']['s2_rate']
        
        # Create network
        G = nx.Graph()
        
        # Add nodes
        for i in range(size):
            G.add_node(i)
        
        # Add edges
        edges = self.topology_definitions[topology]['edges'](size)
        G.add_edges_from(edges)
        
        # Get positions
        pos = self.topology_definitions[topology]['node_positions'](size)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Plot 1: Network with S2 activation rates
        node_colors = [s2_rate] * size  # All nodes have same S2 rate for this scenario
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                              node_size=1000, alpha=0.8, cmap='RdYlBu_r', 
                              vmin=0, vmax=1, ax=ax1)
        nx.draw_networkx_edges(G, pos, edge_color='gray', 
                              width=2, alpha=0.6, ax=ax1)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax1)
        
        ax1.set_title(f'{topology.title()} Network - {scenario.replace("_", " ").title()}\nS2 Rate: {s2_rate:.1%}', 
                     fontsize=12, fontweight='bold')
        ax1.set_xlabel('X Coordinate')
        ax1.set_ylabel('Y Coordinate')
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax1)
        cbar.set_label('S2 Activation Rate', rotation=270, labelpad=20)
        
        # Plot 2: Flow strength visualization
        # Simulate flow strength based on network structure and S2 rate
        flow_strengths = self._calculate_flow_strengths(G, s2_rate, topology)
        
        # Draw network with edge thickness representing flow
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                              node_size=1000, alpha=0.8, ax=ax2)
        
        # Draw edges with thickness based on flow strength
        for edge in G.edges():
            flow_strength = flow_strengths.get(edge, 0.1)
            nx.draw_networkx_edges(G, pos, edgelist=[edge], 
                                  width=flow_strength * 5, alpha=0.7, 
                                  edge_color='red', ax=ax2)
        
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax2)
        
        ax2.set_title(f'Flow Strength Visualization\n{topology.title()} Network (n={size})', 
                     fontsize=12, fontweight='bold')
        ax2.set_xlabel('X Coordinate')
        ax2.set_ylabel('Y Coordinate')
        ax2.grid(True, alpha=0.3)
        ax2.set_aspect('equal')
        
        # Add flow legend
        ax2.text(0.02, 0.02, 'Edge thickness = Flow strength', 
                transform=ax2.transAxes, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(self.network_maps_dir / f"{topology}_flow_{scenario}_n{size}.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.network_maps_dir / f"{topology}_flow_{scenario}_n{size}.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ {topology.title()} flow map ({scenario}, n={size}) created")
    
    def _calculate_flow_strengths(self, G, s2_rate, topology):
        """Calculate flow strengths for edges"""
        flow_strengths = {}
        
        for edge in G.edges():
            # Base flow strength depends on topology and S2 rate
            if topology == 'linear':
                # Linear networks have sequential flow
                flow_strengths[edge] = 0.5 + 0.5 * s2_rate
            elif topology == 'star':
                # Star networks have hub-based flow
                if 0 in edge or 1 in edge:  # Hub connections
                    flow_strengths[edge] = 0.8 + 0.2 * s2_rate
                else:
                    flow_strengths[edge] = 0.3 + 0.3 * s2_rate
            elif topology == 'tree':
                # Tree networks have hierarchical flow
                flow_strengths[edge] = 0.4 + 0.4 * s2_rate
            elif topology == 'grid':
                # Grid networks have distributed flow
                flow_strengths[edge] = 0.6 + 0.3 * s2_rate
        
        return flow_strengths
    
    def _generate_comparative_network_maps(self):
        """Generate comparative network maps"""
        
        print("📊 Generating comparative network maps...")
        
        # Create topology comparison map
        self._create_topology_comparison_map()
        
        # Create size comparison map
        self._create_size_comparison_map()
        
        # Create scenario comparison map
        self._create_scenario_comparison_map()
    
    def _create_topology_comparison_map(self):
        """Create topology comparison map"""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Network Topology Comparison (n=7)', fontsize=16, fontweight='bold')
        
        topologies = ['linear', 'star', 'tree', 'grid']
        axes = axes.flatten()
        
        for i, topology in enumerate(topologies):
            ax = axes[i]
            
            # Create network
            G = nx.Graph()
            size = 7
            
            # Add nodes and edges
            for j in range(size):
                G.add_node(j)
            
            edges = self.topology_definitions[topology]['edges'](size)
            G.add_edges_from(edges)
            
            # Get positions
            pos = self.topology_definitions[topology]['node_positions'](size)
            
            # Draw network
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                  node_size=800, alpha=0.8, ax=ax)
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                  width=2, alpha=0.6, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax)
            
            ax.set_title(f'{topology.title()} Network\n{nx.density(G):.3f} density', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
        
        plt.tight_layout()
        plt.savefig(self.network_maps_dir / "topology_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.network_maps_dir / "topology_comparison.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print("  ✅ Topology comparison map created")
    
    def _create_size_comparison_map(self):
        """Create network size comparison map"""
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Network Size Comparison (Linear Topology)', fontsize=16, fontweight='bold')
        
        sizes = [5, 7, 11]
        
        for i, size in enumerate(sizes):
            ax = axes[i]
            
            # Create linear network
            G = nx.Graph()
            
            # Add nodes and edges
            for j in range(size):
                G.add_node(j)
            
            edges = [(j, j+1) for j in range(size-1)]
            G.add_edges_from(edges)
            
            # Get positions
            pos = {j: (j * 2, 0) for j in range(size)}
            
            # Draw network
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                  node_size=800, alpha=0.8, ax=ax)
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                  width=2, alpha=0.6, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax)
            
            ax.set_title(f'Linear Network (n={size})\n{nx.density(G):.3f} density', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
        
        plt.tight_layout()
        plt.savefig(self.network_maps_dir / "size_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.network_maps_dir / "size_comparison.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print("  ✅ Size comparison map created")
    
    def _create_scenario_comparison_map(self):
        """Create scenario comparison map"""
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('S1/S2 Scenario Comparison (Star Network, n=7)', fontsize=16, fontweight='bold')
        
        scenarios = ['low_s2', 'medium_s2', 'high_s2']
        scenario_labels = ['Low S2', 'Medium S2', 'High S2']
        
        for i, scenario in enumerate(scenarios):
            ax = axes[i]
            
            # Create star network
            G = nx.Graph()
            size = 7
            
            # Add nodes and edges
            for j in range(size):
                G.add_node(j)
            
            edges = [(0, 1)]  # Origin to hub
            for j in range(2, size):
                edges.append((1, j))  # Hub to camps
            G.add_edges_from(edges)
            
            # Get positions
            pos = {0: (0, 0), 1: (3, 0)}  # Origin and hub
            for j in range(2, size):
                angle = 2 * np.pi * (j - 2) / (size - 2)
                x = 6 * np.cos(angle)
                y = 6 * np.sin(angle)
                pos[j] = (x, y)
            
            # Get S2 rate for this scenario
            exp_id = f"star_7_{scenario}"
            s2_rate = self.results[exp_id]['results']['s2_rate'] if exp_id in self.results else 0.5
            
            # Draw network with S2 rate coloring
            nx.draw_networkx_nodes(G, pos, node_color=[s2_rate] * size, 
                                  node_size=800, alpha=0.8, cmap='RdYlBu_r', 
                                  vmin=0, vmax=1, ax=ax)
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                  width=2, alpha=0.6, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax)
            
            ax.set_title(f'{scenario_labels[i]}\nS2 Rate: {s2_rate:.1%}', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=axes, shrink=0.8)
        cbar.set_label('S2 Activation Rate', rotation=270, labelpad=20)
        
        plt.tight_layout()
        plt.savefig(self.network_maps_dir / "scenario_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.savefig(self.network_maps_dir / "scenario_comparison.pdf", 
                   bbox_inches='tight')
        plt.close()
        
        print("  ✅ Scenario comparison map created")

def main():
    """Main function to generate network topology maps"""
    
    print("🗺️ Network Topology Map Generator")
    print("=" * 50)
    print("Generating network structure and flow visualization maps")
    print("=" * 50)
    
    # Create and run generator
    generator = NetworkTopologyMapGenerator()
    generator.generate_all_network_maps()
    
    print(f"\n🎉 All network topology maps generated successfully!")
    print(f"🗺️ Check the organized_s1s2_experiments/02_figures/network_topology_maps/ directory")

if __name__ == "__main__":
    main()






