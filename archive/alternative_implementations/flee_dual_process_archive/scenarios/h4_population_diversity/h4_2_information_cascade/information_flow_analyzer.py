"""
Information Flow Analyzer for H4.2 Information Cascade Test

Analyzes information flow patterns and network effects in scout-follower dynamics.
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import entropy
import os


@dataclass
class InformationFlowMetrics:
    """Metrics for information flow analysis"""
    flow_velocity: float
    network_density: float
    information_entropy: float
    cascade_reach: float
    diffusion_efficiency: float
    temporal_patterns: Dict[str, List[float]]


@dataclass
class NetworkNode:
    """Represents a node in the information network"""
    agent_id: int
    agent_type: str  # 'scout' or 'follower'
    information_received: List[Tuple[int, str, int]]  # (day, info, source)
    information_shared: List[Tuple[int, str, List[int]]]  # (day, info, targets)
    centrality_measures: Dict[str, float]


class InformationFlowAnalyzer:
    """Analyzes information flow patterns in cascade scenarios"""
    
    def __init__(self, output_dir: str):
        """
        Initialize information flow analyzer
        
        Args:
            output_dir: Directory containing simulation output files
        """
        self.output_dir = output_dir
        self.network = nx.DiGraph()
        self.nodes: Dict[int, NetworkNode] = {}
        self.information_events: List[Dict[str, Any]] = []
        
    def build_information_network(self, 
                                scout_data: pd.DataFrame,
                                follower_data: pd.DataFrame,
                                interaction_data: Optional[pd.DataFrame] = None):
        """
        Build information network from tracking data
        
        Args:
            scout_data: Scout discovery data
            follower_data: Follower adoption data
            interaction_data: Agent interaction data (optional)
        """
        # Initialize nodes
        all_agents = set(scout_data['agent_id'].unique()) | set(follower_data['agent_id'].unique())
        
        for agent_id in all_agents:
            agent_type = 'scout' if agent_id in scout_data['agent_id'].values else 'follower'
            self.nodes[agent_id] = NetworkNode(
                agent_id=agent_id,
                agent_type=agent_type,
                information_received=[],
                information_shared=[],
                centrality_measures={}
            )
            self.network.add_node(agent_id, type=agent_type)
        
        # Build edges based on information flow
        self._infer_information_flows(scout_data, follower_data)
        
        # Calculate centrality measures
        self._calculate_centrality_measures()
    
    def _infer_information_flows(self, scout_data: pd.DataFrame, follower_data: pd.DataFrame):
        """Infer information flows from discovery and adoption patterns"""
        # Group by destination to track information flow
        for destination in scout_data['destination'].unique():
            scout_discoveries = scout_data[scout_data['destination'] == destination].sort_values('day')
            follower_adoptions = follower_data[follower_data['destination'] == destination].sort_values('day')
            
            if len(scout_discoveries) == 0 or len(follower_adoptions) == 0:
                continue
            
            # Find earliest scout discovery
            first_discovery = scout_discoveries.iloc[0]
            discovery_day = first_discovery['day']
            discoverer_id = first_discovery['agent_id']
            
            # Connect discoverer to followers who adopted within reasonable time window
            for _, adoption in follower_adoptions.iterrows():
                adoption_day = adoption['day']
                adopter_id = adoption['agent_id']
                
                # If adoption is within reasonable time window, infer information flow
                if discovery_day < adoption_day <= discovery_day + 10:
                    # Add edge from scout to follower
                    self.network.add_edge(discoverer_id, adopter_id, 
                                        destination=destination,
                                        discovery_day=discovery_day,
                                        adoption_day=adoption_day,
                                        lag=adoption_day - discovery_day)
                    
                    # Update node information
                    self.nodes[discoverer_id].information_shared.append(
                        (discovery_day, destination, [adopter_id])
                    )
                    self.nodes[adopter_id].information_received.append(
                        (adoption_day, destination, discoverer_id)
                    )
                    
                    # Record information event
                    self.information_events.append({
                        'day': discovery_day,
                        'event_type': 'information_flow',
                        'source': discoverer_id,
                        'target': adopter_id,
                        'information': destination,
                        'lag': adoption_day - discovery_day
                    })
    
    def _calculate_centrality_measures(self):
        """Calculate network centrality measures for all nodes"""
        if len(self.network.nodes()) == 0:
            return
        
        # Calculate various centrality measures
        try:
            degree_centrality = nx.degree_centrality(self.network)
            betweenness_centrality = nx.betweenness_centrality(self.network)
            closeness_centrality = nx.closeness_centrality(self.network)
            
            # For directed graph
            in_degree_centrality = nx.in_degree_centrality(self.network)
            out_degree_centrality = nx.out_degree_centrality(self.network)
            
            for agent_id in self.nodes:
                self.nodes[agent_id].centrality_measures = {
                    'degree': degree_centrality.get(agent_id, 0.0),
                    'betweenness': betweenness_centrality.get(agent_id, 0.0),
                    'closeness': closeness_centrality.get(agent_id, 0.0),
                    'in_degree': in_degree_centrality.get(agent_id, 0.0),
                    'out_degree': out_degree_centrality.get(agent_id, 0.0)
                }
        except:
            # Handle empty or disconnected networks
            for agent_id in self.nodes:
                self.nodes[agent_id].centrality_measures = {
                    'degree': 0.0, 'betweenness': 0.0, 'closeness': 0.0,
                    'in_degree': 0.0, 'out_degree': 0.0
                }
    
    def analyze_information_flow(self) -> InformationFlowMetrics:
        """Analyze information flow patterns and return metrics"""
        
        # Calculate flow velocity (average information propagation speed)
        flow_velocity = self._calculate_flow_velocity()
        
        # Calculate network density
        network_density = self._calculate_network_density()
        
        # Calculate information entropy
        information_entropy = self._calculate_information_entropy()
        
        # Calculate cascade reach
        cascade_reach = self._calculate_cascade_reach()
        
        # Calculate diffusion efficiency
        diffusion_efficiency = self._calculate_diffusion_efficiency()
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns()
        
        return InformationFlowMetrics(
            flow_velocity=flow_velocity,
            network_density=network_density,
            information_entropy=information_entropy,
            cascade_reach=cascade_reach,
            diffusion_efficiency=diffusion_efficiency,
            temporal_patterns=temporal_patterns
        )
    
    def _calculate_flow_velocity(self) -> float:
        """Calculate average information flow velocity"""
        if not self.information_events:
            return 0.0
        
        lags = [event['lag'] for event in self.information_events if event['lag'] > 0]
        return 1.0 / np.mean(lags) if lags else 0.0
    
    def _calculate_network_density(self) -> float:
        """Calculate information network density"""
        if len(self.network.nodes()) <= 1:
            return 0.0
        
        return nx.density(self.network)
    
    def _calculate_information_entropy(self) -> float:
        """Calculate entropy of information distribution"""
        if not self.information_events:
            return 0.0
        
        # Calculate distribution of information types
        info_counts = defaultdict(int)
        for event in self.information_events:
            info_counts[event['information']] += 1
        
        if len(info_counts) <= 1:
            return 0.0
        
        # Calculate entropy
        total_events = sum(info_counts.values())
        probabilities = [count / total_events for count in info_counts.values()]
        return entropy(probabilities)
    
    def _calculate_cascade_reach(self) -> float:
        """Calculate average cascade reach (how many agents receive each piece of information)"""
        if not self.information_events:
            return 0.0
        
        # Group events by information type
        info_reaches = defaultdict(set)
        for event in self.information_events:
            info_reaches[event['information']].add(event['target'])
        
        # Calculate average reach
        reaches = [len(targets) for targets in info_reaches.values()]
        return np.mean(reaches) if reaches else 0.0
    
    def _calculate_diffusion_efficiency(self) -> float:
        """Calculate information diffusion efficiency"""
        if len(self.nodes) == 0:
            return 0.0
        
        # Calculate ratio of information receivers to total agents
        receivers = set()
        for event in self.information_events:
            receivers.add(event['target'])
        
        return len(receivers) / len(self.nodes)
    
    def _analyze_temporal_patterns(self) -> Dict[str, List[float]]:
        """Analyze temporal patterns in information flow"""
        patterns = {
            'daily_flow_volume': [],
            'cumulative_reach': [],
            'flow_acceleration': []
        }
        
        if not self.information_events:
            return patterns
        
        # Group events by day
        daily_events = defaultdict(list)
        for event in self.information_events:
            daily_events[event['day']].append(event)
        
        # Calculate daily patterns
        max_day = max(daily_events.keys()) if daily_events else 0
        cumulative_agents = set()
        
        for day in range(1, max_day + 1):
            # Daily flow volume
            daily_volume = len(daily_events.get(day, []))
            patterns['daily_flow_volume'].append(daily_volume)
            
            # Cumulative reach
            for event in daily_events.get(day, []):
                cumulative_agents.add(event['target'])
            patterns['cumulative_reach'].append(len(cumulative_agents))
        
        # Calculate flow acceleration (change in daily volume)
        if len(patterns['daily_flow_volume']) > 1:
            volumes = patterns['daily_flow_volume']
            patterns['flow_acceleration'] = [volumes[i] - volumes[i-1] 
                                           for i in range(1, len(volumes))]
        
        return patterns
    
    def identify_information_brokers(self) -> List[Tuple[int, str, float]]:
        """Identify key information brokers in the network"""
        brokers = []
        
        for agent_id, node in self.nodes.items():
            # Brokers have high betweenness centrality
            betweenness = node.centrality_measures.get('betweenness', 0.0)
            
            if betweenness > 0.1:  # Threshold for broker identification
                brokers.append((agent_id, node.agent_type, betweenness))
        
        # Sort by betweenness centrality
        return sorted(brokers, key=lambda x: x[2], reverse=True)
    
    def analyze_scout_follower_dynamics(self) -> Dict[str, Any]:
        """Analyze specific scout-follower interaction patterns"""
        dynamics = {
            'scout_influence': {},
            'follower_receptivity': {},
            'interaction_patterns': {},
            'role_effectiveness': {}
        }
        
        # Analyze scout influence
        scout_nodes = {aid: node for aid, node in self.nodes.items() if node.agent_type == 'scout'}
        follower_nodes = {aid: node for aid, node in self.nodes.items() if node.agent_type == 'follower'}
        
        if scout_nodes:
            scout_out_degrees = [node.centrality_measures.get('out_degree', 0.0) for node in scout_nodes.values()]
            dynamics['scout_influence'] = {
                'avg_out_degree': np.mean(scout_out_degrees),
                'max_influence': max(scout_out_degrees) if scout_out_degrees else 0.0,
                'influence_distribution': scout_out_degrees
            }
        
        if follower_nodes:
            follower_in_degrees = [node.centrality_measures.get('in_degree', 0.0) for node in follower_nodes.values()]
            dynamics['follower_receptivity'] = {
                'avg_in_degree': np.mean(follower_in_degrees),
                'max_receptivity': max(follower_in_degrees) if follower_in_degrees else 0.0,
                'receptivity_distribution': follower_in_degrees
            }
        
        # Analyze interaction patterns
        scout_to_follower_edges = [(u, v) for u, v in self.network.edges() 
                                  if self.nodes[u].agent_type == 'scout' and 
                                     self.nodes[v].agent_type == 'follower']
        
        dynamics['interaction_patterns'] = {
            'total_scout_follower_connections': len(scout_to_follower_edges),
            'connection_density': len(scout_to_follower_edges) / (len(scout_nodes) * len(follower_nodes)) 
                                if scout_nodes and follower_nodes else 0.0
        }
        
        # Role effectiveness
        dynamics['role_effectiveness'] = {
            'scouts_as_discoverers': len([node for node in scout_nodes.values() 
                                        if len(node.information_shared) > 0]) / len(scout_nodes) if scout_nodes else 0.0,
            'followers_as_adopters': len([node for node in follower_nodes.values() 
                                        if len(node.information_received) > 0]) / len(follower_nodes) if follower_nodes else 0.0
        }
        
        return dynamics
    
    def visualize_information_network(self, output_file: str, figsize: Tuple[int, int] = (12, 8)):
        """Visualize the information network"""
        if len(self.network.nodes()) == 0:
            return
        
        plt.figure(figsize=figsize)
        
        # Create layout
        pos = nx.spring_layout(self.network, k=1, iterations=50)
        
        # Separate scouts and followers
        scout_nodes = [n for n in self.network.nodes() if self.nodes[n].agent_type == 'scout']
        follower_nodes = [n for n in self.network.nodes() if self.nodes[n].agent_type == 'follower']
        
        # Draw nodes
        nx.draw_networkx_nodes(self.network, pos, nodelist=scout_nodes, 
                              node_color='red', node_size=300, alpha=0.7, label='Scouts')
        nx.draw_networkx_nodes(self.network, pos, nodelist=follower_nodes, 
                              node_color='blue', node_size=200, alpha=0.7, label='Followers')
        
        # Draw edges
        nx.draw_networkx_edges(self.network, pos, alpha=0.5, arrows=True, 
                              arrowsize=20, edge_color='gray')
        
        # Draw labels
        nx.draw_networkx_labels(self.network, pos, font_size=8)
        
        plt.title('Information Flow Network\n(Red: Scouts, Blue: Followers)')
        plt.legend()
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    def visualize_temporal_flow(self, output_file: str, figsize: Tuple[int, int] = (12, 6)):
        """Visualize temporal information flow patterns"""
        metrics = self.analyze_information_flow()
        patterns = metrics.temporal_patterns
        
        if not patterns['daily_flow_volume']:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        
        days = range(1, len(patterns['daily_flow_volume']) + 1)
        
        # Daily flow volume
        axes[0, 0].plot(days, patterns['daily_flow_volume'], 'b-', marker='o')
        axes[0, 0].set_title('Daily Information Flow Volume')
        axes[0, 0].set_xlabel('Day')
        axes[0, 0].set_ylabel('Number of Information Events')
        
        # Cumulative reach
        axes[0, 1].plot(days, patterns['cumulative_reach'], 'g-', marker='s')
        axes[0, 1].set_title('Cumulative Information Reach')
        axes[0, 1].set_xlabel('Day')
        axes[0, 1].set_ylabel('Number of Agents Reached')
        
        # Flow acceleration
        if patterns['flow_acceleration']:
            accel_days = range(2, len(patterns['flow_acceleration']) + 2)
            axes[1, 0].plot(accel_days, patterns['flow_acceleration'], 'r-', marker='^')
            axes[1, 0].axhline(y=0, color='k', linestyle='--', alpha=0.5)
            axes[1, 0].set_title('Information Flow Acceleration')
            axes[1, 0].set_xlabel('Day')
            axes[1, 0].set_ylabel('Change in Daily Volume')
        
        # Network metrics over time (simplified)
        axes[1, 1].text(0.1, 0.8, f'Flow Velocity: {metrics.flow_velocity:.3f}', transform=axes[1, 1].transAxes)
        axes[1, 1].text(0.1, 0.6, f'Network Density: {metrics.network_density:.3f}', transform=axes[1, 1].transAxes)
        axes[1, 1].text(0.1, 0.4, f'Cascade Reach: {metrics.cascade_reach:.1f}', transform=axes[1, 1].transAxes)
        axes[1, 1].text(0.1, 0.2, f'Diffusion Efficiency: {metrics.diffusion_efficiency:.3f}', transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('Network Metrics Summary')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    def export_network_analysis(self, output_dir: str):
        """Export comprehensive network analysis"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export network metrics
        metrics = self.analyze_information_flow()
        metrics_dict = {
            'flow_velocity': metrics.flow_velocity,
            'network_density': metrics.network_density,
            'information_entropy': metrics.information_entropy,
            'cascade_reach': metrics.cascade_reach,
            'diffusion_efficiency': metrics.diffusion_efficiency,
            'temporal_patterns': metrics.temporal_patterns
        }
        
        metrics_df = pd.DataFrame([metrics_dict])
        metrics_df.to_csv(os.path.join(output_dir, 'information_flow_metrics.csv'), index=False)
        
        # Export node centralities
        centrality_data = []
        for agent_id, node in self.nodes.items():
            centrality_data.append({
                'agent_id': agent_id,
                'agent_type': node.agent_type,
                **node.centrality_measures
            })
        
        if centrality_data:
            centrality_df = pd.DataFrame(centrality_data)
            centrality_df.to_csv(os.path.join(output_dir, 'node_centralities.csv'), index=False)
        
        # Export information events
        if self.information_events:
            events_df = pd.DataFrame(self.information_events)
            events_df.to_csv(os.path.join(output_dir, 'information_events.csv'), index=False)
        
        # Export scout-follower dynamics
        dynamics = self.analyze_scout_follower_dynamics()
        with open(os.path.join(output_dir, 'scout_follower_dynamics.json'), 'w') as f:
            import json
            json.dump(dynamics, f, indent=2)
        
        # Generate visualizations
        self.visualize_information_network(os.path.join(output_dir, 'information_network.png'))
        self.visualize_temporal_flow(os.path.join(output_dir, 'temporal_flow_patterns.png'))