"""
Individual Agent Analysis Tools for Dual Process Experiments

This module provides analysis tools for individual agent trajectories,
decision-making patterns, and behavioral clustering. It works with data
from both Flee's standard agent logs and the dual-process tracker.
"""

from __future__ import annotations, print_function
import os
import sys
import csv
import json
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

# Optional dependencies for advanced analysis
try:
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


@dataclass
class AgentTrajectory:
    """Complete trajectory data for a single agent."""
    agent_id: str
    trajectory_points: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    cognitive_transitions: List[Dict[str, Any]]
    social_interactions: List[Dict[str, Any]]
    summary_stats: Dict[str, Any]


@dataclass
class MovementPattern:
    """Identified movement pattern for clustering."""
    pattern_id: str
    agent_ids: List[str]
    characteristics: Dict[str, Any]
    cognitive_profile: Dict[str, Any]
    spatial_signature: Dict[str, Any]


class IndividualAgentAnalyzer:
    """
    Analyzer for individual agent trajectories and decision-making patterns.
    
    This class provides comprehensive analysis of individual agent behavior,
    integrating data from Flee's standard logs and dual-process tracking.
    """
    
    def __init__(self, data_directory: str, rank: int = 0):
        """
        Initialize the individual agent analyzer.
        
        Args:
            data_directory: Directory containing agent tracking data
            rank: MPI rank for parallel processing (default: 0)
        """
        self.data_directory = Path(data_directory)
        self.rank = rank
        
        # Data storage
        self.agent_trajectories: Dict[str, AgentTrajectory] = {}
        self.flee_agent_data: Optional[pd.DataFrame] = None
        self.dual_process_data: Optional[pd.DataFrame] = None
        self.decision_data: Optional[pd.DataFrame] = None
        self.social_network_data: Optional[pd.DataFrame] = None
        
        # Analysis results
        self.movement_patterns: List[MovementPattern] = []
        self.decision_clusters: Dict[str, List[str]] = {}
        self.cognitive_profiles: Dict[str, Dict] = {}
        
        # Configuration
        self.loaded_data_sources: Set[str] = set()
        
    @check_args_type
    def load_flee_agent_data(self) -> bool:
        """
        Load Flee's standard agent log data.
        
        Returns:
            True if data was loaded successfully, False otherwise
        """
        flee_file = self.data_directory / f"agents.out.{self.rank}"
        
        if not flee_file.exists():
            print(f"Warning: Flee agent file {flee_file} not found", file=sys.stderr)
            return False
            
        try:
            # Read Flee's agent data format
            self.flee_agent_data = pd.read_csv(
                flee_file,
                comment='#',
                names=[
                    'time', 'agent_id', 'original_location', 'current_location',
                    'gps_x', 'gps_y', 'is_travelling', 'distance_travelled',
                    'places_travelled', 'distance_moved_this_timestep'
                ] + [f'attr_{i}' for i in range(10)]  # Handle variable attributes
            )
            
            # Clean up agent_id format for consistency
            self.flee_agent_data['agent_id'] = self.flee_agent_data['agent_id'].astype(str)
            
            self.loaded_data_sources.add('flee_agents')
            print(f"Loaded {len(self.flee_agent_data)} Flee agent records", file=sys.stderr)
            return True
            
        except Exception as e:
            print(f"Error loading Flee agent data: {e}", file=sys.stderr)
            return False
            
    @check_args_type
    def load_dual_process_data(self) -> bool:
        """
        Load dual-process tracking data.
        
        Returns:
            True if data was loaded successfully, False otherwise
        """
        # Load main dual-process data
        dp_file = self.data_directory / f"agents_dual_process.out.{self.rank}"
        
        if dp_file.exists():
            try:
                self.dual_process_data = pd.read_csv(dp_file, comment='#')
                self.loaded_data_sources.add('dual_process')
                print(f"Loaded {len(self.dual_process_data)} dual-process records", file=sys.stderr)
            except Exception as e:
                print(f"Error loading dual-process data: {e}", file=sys.stderr)
                
        # Load decision data
        decision_file = self.data_directory / f"agent_decisions.{self.rank}.csv"
        
        if decision_file.exists():
            try:
                self.decision_data = pd.read_csv(decision_file)
                self.loaded_data_sources.add('decisions')
                print(f"Loaded {len(self.decision_data)} decision records", file=sys.stderr)
            except Exception as e:
                print(f"Error loading decision data: {e}", file=sys.stderr)
                
        # Load social network data
        social_file = self.data_directory / f"social_network_individual.{self.rank}.csv"
        
        if social_file.exists():
            try:
                self.social_network_data = pd.read_csv(social_file)
                self.loaded_data_sources.add('social_network')
                print(f"Loaded {len(self.social_network_data)} social network records", file=sys.stderr)
            except Exception as e:
                print(f"Error loading social network data: {e}", file=sys.stderr)
                
        return len(self.loaded_data_sources) > 1
        
    @check_args_type
    def build_agent_trajectories(self) -> Dict[str, AgentTrajectory]:
        """
        Build complete trajectory objects for each agent.
        
        Returns:
            Dictionary mapping agent_id to AgentTrajectory objects
        """
        if 'flee_agents' not in self.loaded_data_sources:
            print("Warning: Flee agent data not loaded. Loading basic trajectories only.", file=sys.stderr)
            
        # Get all unique agent IDs
        agent_ids = set()
        
        if self.flee_agent_data is not None:
            agent_ids.update(self.flee_agent_data['agent_id'].unique())
            
        if self.dual_process_data is not None:
            agent_ids.update(self.dual_process_data['agent_id'].unique())
            
        # Build trajectory for each agent
        for agent_id in agent_ids:
            trajectory = self._build_single_agent_trajectory(agent_id)
            if trajectory:
                self.agent_trajectories[agent_id] = trajectory
                
        print(f"Built trajectories for {len(self.agent_trajectories)} agents", file=sys.stderr)
        return self.agent_trajectories
        
    def _build_single_agent_trajectory(self, agent_id: str) -> Optional[AgentTrajectory]:
        """Build trajectory for a single agent."""
        trajectory_points = []
        decisions = []
        cognitive_transitions = []
        social_interactions = []
        
        # Extract trajectory points from Flee data
        if self.flee_agent_data is not None:
            agent_flee_data = self.flee_agent_data[
                self.flee_agent_data['agent_id'] == agent_id
            ].sort_values('time')
            
            for _, row in agent_flee_data.iterrows():
                trajectory_points.append({
                    'time': row['time'],
                    'location': row['current_location'],
                    'x': row['gps_x'],
                    'y': row['gps_y'],
                    'distance_travelled': row['distance_travelled'],
                    'places_travelled': row['places_travelled'],
                    'is_travelling': row['is_travelling'],
                    'distance_moved_this_timestep': row['distance_moved_this_timestep']
                })
                
        # Add dual-process data
        if self.dual_process_data is not None:
            agent_dp_data = self.dual_process_data[
                self.dual_process_data['agent_id'] == agent_id
            ].sort_values('time')
            
            # Merge with trajectory points or create new ones
            for _, row in agent_dp_data.iterrows():
                time = row['time']
                
                # Find matching trajectory point or create new one
                matching_point = next(
                    (p for p in trajectory_points if p['time'] == time), None
                )
                
                if matching_point:
                    # Add dual-process data to existing point
                    matching_point.update({
                        'cognitive_state': row['cognitive_state'],
                        'system2_activations': row['system2_activations'],
                        'days_in_current_location': row['days_in_current_location']
                    })
                else:
                    # Create new trajectory point
                    trajectory_points.append({
                        'time': time,
                        'cognitive_state': row['cognitive_state'],
                        'system2_activations': row['system2_activations'],
                        'days_in_current_location': row['days_in_current_location']
                    })
                    
                # Track cognitive transitions
                if len(trajectory_points) > 1:
                    prev_state = trajectory_points[-2].get('cognitive_state', 'S1')
                    curr_state = row['cognitive_state']
                    
                    if prev_state != curr_state:
                        cognitive_transitions.append({
                            'time': time,
                            'from_state': prev_state,
                            'to_state': curr_state,
                            'trigger': 'unknown'  # Could be enhanced with decision data
                        })
                        
        # Extract decisions
        if self.decision_data is not None:
            agent_decisions = self.decision_data[
                self.decision_data['agent_id'] == agent_id
            ].sort_values('time')
            
            decisions = agent_decisions.to_dict('records')
            
        # Extract social interactions
        if self.social_network_data is not None:
            agent_social = self.social_network_data[
                self.social_network_data['agent_id'] == agent_id
            ].sort_values('time')
            
            social_interactions = agent_social.to_dict('records')
            
        # Calculate summary statistics
        summary_stats = self._calculate_agent_summary_stats(
            trajectory_points, decisions, cognitive_transitions, social_interactions
        )
        
        if not trajectory_points:
            return None
            
        return AgentTrajectory(
            agent_id=agent_id,
            trajectory_points=sorted(trajectory_points, key=lambda x: x['time']),
            decisions=decisions,
            cognitive_transitions=cognitive_transitions,
            social_interactions=social_interactions,
            summary_stats=summary_stats
        )
        
    def _calculate_agent_summary_stats(self, trajectory_points: List[Dict], 
                                     decisions: List[Dict],
                                     cognitive_transitions: List[Dict],
                                     social_interactions: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for an agent."""
        if not trajectory_points:
            return {}
            
        stats = {}
        
        # Basic trajectory stats
        stats['total_timesteps'] = len(trajectory_points)
        stats['simulation_duration'] = (
            max(p['time'] for p in trajectory_points) - 
            min(p['time'] for p in trajectory_points)
        ) if len(trajectory_points) > 1 else 0
        
        # Distance and movement stats
        distances = [p.get('distance_travelled', 0) for p in trajectory_points]
        if distances:
            stats['total_distance'] = max(distances)
            stats['avg_daily_distance'] = stats['total_distance'] / max(1, stats['simulation_duration'])
            
        # Location diversity
        locations = [p.get('location', 'unknown') for p in trajectory_points]
        unique_locations = set(loc for loc in locations if loc != 'unknown')
        stats['unique_locations_visited'] = len(unique_locations)
        stats['location_diversity_index'] = len(unique_locations) / max(1, len(locations))
        
        # Cognitive behavior stats
        cognitive_states = [p.get('cognitive_state', 'S1') for p in trajectory_points]
        s1_count = cognitive_states.count('S1')
        s2_count = cognitive_states.count('S2')
        
        stats['s1_proportion'] = s1_count / len(cognitive_states) if cognitive_states else 0
        stats['s2_proportion'] = s2_count / len(cognitive_states) if cognitive_states else 0
        stats['cognitive_transitions_count'] = len(cognitive_transitions)
        
        # Decision-making stats
        stats['total_decisions'] = len(decisions)
        stats['decisions_per_day'] = len(decisions) / max(1, stats['simulation_duration'])
        
        if decisions:
            move_decisions = [d for d in decisions if d.get('decision_type') == 'move']
            stats['move_decisions_count'] = len(move_decisions)
            stats['move_decision_rate'] = len(move_decisions) / len(decisions)
            
            # Average decision confidence (movechance)
            movechances = [d.get('movechance', 0) for d in decisions if 'movechance' in d]
            if movechances:
                stats['avg_decision_confidence'] = np.mean(movechances)
                stats['decision_confidence_variance'] = np.var(movechances)
                
        # Social interaction stats
        stats['social_interactions_count'] = len(social_interactions)
        
        if social_interactions:
            connections = [s.get('connections', 0) for s in social_interactions]
            stats['max_connections'] = max(connections)
            stats['avg_connections'] = np.mean(connections)
            stats['connection_volatility'] = np.var(connections)
            
        return stats
        
    @check_args_type
    def identify_movement_patterns(self, n_clusters: int = 5) -> List[MovementPattern]:
        """
        Identify common movement patterns using clustering analysis.
        
        Args:
            n_clusters: Number of clusters to identify
            
        Returns:
            List of identified movement patterns
        """
        if not SKLEARN_AVAILABLE:
            print("Warning: scikit-learn not available. Using simple heuristic clustering.", file=sys.stderr)
            return self._simple_pattern_identification()
            
        if not self.agent_trajectories:
            print("Warning: No agent trajectories loaded. Call build_agent_trajectories() first.", file=sys.stderr)
            return []
            
        # Extract features for clustering
        features, agent_ids = self._extract_movement_features()
        
        if len(features) < n_clusters:
            print(f"Warning: Only {len(features)} agents available, reducing clusters to {len(features)}", file=sys.stderr)
            n_clusters = len(features)
            
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # Calculate silhouette score
        if len(set(cluster_labels)) > 1:
            silhouette_avg = silhouette_score(features_scaled, cluster_labels)
            print(f"Clustering silhouette score: {silhouette_avg:.3f}", file=sys.stderr)
            
        # Build movement patterns
        patterns = []
        for cluster_id in range(n_clusters):
            cluster_agent_ids = [agent_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
            
            if not cluster_agent_ids:
                continue
                
            # Analyze cluster characteristics
            characteristics = self._analyze_cluster_characteristics(cluster_agent_ids, features, cluster_id)
            cognitive_profile = self._analyze_cluster_cognitive_profile(cluster_agent_ids)
            spatial_signature = self._analyze_cluster_spatial_signature(cluster_agent_ids)
            
            pattern = MovementPattern(
                pattern_id=f"pattern_{cluster_id}",
                agent_ids=cluster_agent_ids,
                characteristics=characteristics,
                cognitive_profile=cognitive_profile,
                spatial_signature=spatial_signature
            )
            patterns.append(pattern)
            
        self.movement_patterns = patterns
        print(f"Identified {len(patterns)} movement patterns", file=sys.stderr)
        return patterns
        
    def _extract_movement_features(self) -> Tuple[np.ndarray, List[str]]:
        """Extract numerical features for movement pattern clustering."""
        features = []
        agent_ids = []
        
        for agent_id, trajectory in self.agent_trajectories.items():
            stats = trajectory.summary_stats
            
            # Extract key features for clustering
            feature_vector = [
                stats.get('total_distance', 0),
                stats.get('unique_locations_visited', 0),
                stats.get('location_diversity_index', 0),
                stats.get('s2_proportion', 0),
                stats.get('cognitive_transitions_count', 0),
                stats.get('move_decision_rate', 0),
                stats.get('avg_decision_confidence', 0),
                stats.get('max_connections', 0),
                stats.get('avg_connections', 0),
                stats.get('simulation_duration', 0)
            ]
            
            # Only include agents with valid features
            if any(f > 0 for f in feature_vector):
                features.append(feature_vector)
                agent_ids.append(agent_id)
                
        return np.array(features), agent_ids
        
    def _simple_pattern_identification(self) -> List[MovementPattern]:
        """Simple heuristic-based pattern identification when sklearn is not available."""
        patterns = []
        
        # Group agents by basic characteristics
        high_mobility = []
        low_mobility = []
        high_cognitive = []
        low_cognitive = []
        
        for agent_id, trajectory in self.agent_trajectories.items():
            stats = trajectory.summary_stats
            
            # Mobility classification
            total_distance = stats.get('total_distance', 0)
            if total_distance > 100:  # Threshold for high mobility
                high_mobility.append(agent_id)
            else:
                low_mobility.append(agent_id)
                
            # Cognitive classification
            s2_proportion = stats.get('s2_proportion', 0)
            if s2_proportion > 0.3:  # Threshold for high System 2 usage
                high_cognitive.append(agent_id)
            else:
                low_cognitive.append(agent_id)
                
        # Create simple patterns
        if high_mobility:
            patterns.append(MovementPattern(
                pattern_id="high_mobility",
                agent_ids=high_mobility,
                characteristics={"mobility": "high", "avg_distance": "high"},
                cognitive_profile={"type": "mixed"},
                spatial_signature={"range": "wide"}
            ))
            
        if low_mobility:
            patterns.append(MovementPattern(
                pattern_id="low_mobility", 
                agent_ids=low_mobility,
                characteristics={"mobility": "low", "avg_distance": "low"},
                cognitive_profile={"type": "mixed"},
                spatial_signature={"range": "narrow"}
            ))
            
        return patterns
        
    def _analyze_cluster_characteristics(self, agent_ids: List[str], 
                                       features: np.ndarray, 
                                       cluster_id: int) -> Dict[str, Any]:
        """Analyze characteristics of a movement pattern cluster."""
        cluster_indices = [i for i, aid in enumerate(self.agent_trajectories.keys()) if aid in agent_ids]
        
        if not cluster_indices:
            return {}
            
        cluster_features = features[cluster_indices]
        
        feature_names = [
            'total_distance', 'unique_locations', 'location_diversity',
            's2_proportion', 'cognitive_transitions', 'move_decision_rate',
            'avg_decision_confidence', 'max_connections', 'avg_connections',
            'simulation_duration'
        ]
        
        characteristics = {}
        for i, name in enumerate(feature_names):
            characteristics[f'avg_{name}'] = np.mean(cluster_features[:, i])
            characteristics[f'std_{name}'] = np.std(cluster_features[:, i])
            
        characteristics['cluster_size'] = len(agent_ids)
        
        return characteristics
        
    def _analyze_cluster_cognitive_profile(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Analyze cognitive profile of a cluster."""
        s1_proportions = []
        s2_proportions = []
        transition_counts = []
        
        for agent_id in agent_ids:
            if agent_id in self.agent_trajectories:
                stats = self.agent_trajectories[agent_id].summary_stats
                s1_proportions.append(stats.get('s1_proportion', 0))
                s2_proportions.append(stats.get('s2_proportion', 0))
                transition_counts.append(stats.get('cognitive_transitions_count', 0))
                
        profile = {}
        if s1_proportions:
            profile['avg_s1_proportion'] = np.mean(s1_proportions)
            profile['avg_s2_proportion'] = np.mean(s2_proportions)
            profile['avg_transitions'] = np.mean(transition_counts)
            
            # Classify cognitive type
            if profile['avg_s2_proportion'] > 0.5:
                profile['dominant_mode'] = 'S2'
            elif profile['avg_s1_proportion'] > 0.8:
                profile['dominant_mode'] = 'S1'
            else:
                profile['dominant_mode'] = 'Mixed'
                
        return profile
        
    def _analyze_cluster_spatial_signature(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Analyze spatial movement signature of a cluster."""
        all_locations = set()
        total_distances = []
        location_diversities = []
        
        for agent_id in agent_ids:
            if agent_id in self.agent_trajectories:
                trajectory = self.agent_trajectories[agent_id]
                
                # Collect locations
                locations = [p.get('location', 'unknown') for p in trajectory.trajectory_points]
                all_locations.update(loc for loc in locations if loc != 'unknown')
                
                # Collect stats
                stats = trajectory.summary_stats
                total_distances.append(stats.get('total_distance', 0))
                location_diversities.append(stats.get('location_diversity_index', 0))
                
        signature = {
            'unique_locations_in_cluster': len(all_locations),
            'common_locations': list(all_locations),
            'avg_total_distance': np.mean(total_distances) if total_distances else 0,
            'avg_location_diversity': np.mean(location_diversities) if location_diversities else 0
        }
        
        return signature
        
    @check_args_type
    def analyze_decision_making_patterns(self) -> Dict[str, List[str]]:
        """
        Analyze decision-making patterns and cluster agents by decision behavior.
        
        Returns:
            Dictionary mapping decision pattern names to lists of agent IDs
        """
        if not self.decision_data is not None:
            print("Warning: No decision data available", file=sys.stderr)
            return {}
            
        decision_clusters = {
            'quick_deciders': [],
            'deliberate_deciders': [],
            'high_confidence_deciders': [],
            'low_confidence_deciders': [],
            'frequent_movers': [],
            'infrequent_movers': []
        }
        
        # Analyze each agent's decision patterns
        for agent_id in self.decision_data['agent_id'].unique():
            agent_decisions = self.decision_data[self.decision_data['agent_id'] == agent_id]
            
            if len(agent_decisions) == 0:
                continue
                
            # Calculate decision metrics
            avg_movechance = agent_decisions['movechance'].mean()
            decision_count = len(agent_decisions)
            move_decisions = agent_decisions[agent_decisions['decision_type'] == 'move']
            move_rate = len(move_decisions) / len(agent_decisions)
            
            # Classify based on decision confidence
            if avg_movechance > 0.7:
                decision_clusters['high_confidence_deciders'].append(agent_id)
            elif avg_movechance < 0.3:
                decision_clusters['low_confidence_deciders'].append(agent_id)
                
            # Classify based on movement frequency
            if move_rate > 0.5:
                decision_clusters['frequent_movers'].append(agent_id)
            elif move_rate < 0.2:
                decision_clusters['infrequent_movers'].append(agent_id)
                
            # Classify based on cognitive state during decisions
            s2_decisions = agent_decisions[agent_decisions['cognitive_state'] == 'S2']
            if len(s2_decisions) / len(agent_decisions) > 0.5:
                decision_clusters['deliberate_deciders'].append(agent_id)
            else:
                decision_clusters['quick_deciders'].append(agent_id)
                
        self.decision_clusters = decision_clusters
        
        # Print summary
        for pattern, agents in decision_clusters.items():
            print(f"{pattern}: {len(agents)} agents", file=sys.stderr)
            
        return decision_clusters
        
    @check_args_type
    def compare_individual_vs_aggregate_patterns(self) -> Dict[str, Any]:
        """
        Compare individual agent patterns with aggregate population behavior.
        
        Returns:
            Dictionary with comparison results
        """
        if not self.agent_trajectories:
            return {}
            
        comparison = {}
        
        # Individual vs aggregate distance traveled
        individual_distances = [t.summary_stats.get('total_distance', 0) 
                              for t in self.agent_trajectories.values()]
        
        comparison['distance_analysis'] = {
            'individual_mean': np.mean(individual_distances),
            'individual_std': np.std(individual_distances),
            'individual_median': np.median(individual_distances),
            'individual_range': (min(individual_distances), max(individual_distances)),
            'distance_inequality_gini': self._calculate_gini_coefficient(individual_distances)
        }
        
        # Individual vs aggregate cognitive behavior
        s2_proportions = [t.summary_stats.get('s2_proportion', 0) 
                         for t in self.agent_trajectories.values()]
        
        comparison['cognitive_analysis'] = {
            'individual_s2_mean': np.mean(s2_proportions),
            'individual_s2_std': np.std(s2_proportions),
            'cognitive_diversity': len(set(np.round(s2_proportions, 1))),
            's2_usage_inequality': self._calculate_gini_coefficient(s2_proportions)
        }
        
        # Location diversity analysis
        location_diversities = [t.summary_stats.get('location_diversity_index', 0) 
                              for t in self.agent_trajectories.values()]
        
        comparison['spatial_analysis'] = {
            'individual_diversity_mean': np.mean(location_diversities),
            'individual_diversity_std': np.std(location_diversities),
            'spatial_exploration_inequality': self._calculate_gini_coefficient(location_diversities)
        }
        
        # Decision-making analysis
        if self.decision_data is not None:
            agent_decision_counts = self.decision_data.groupby('agent_id').size()
            
            comparison['decision_analysis'] = {
                'individual_decisions_mean': agent_decision_counts.mean(),
                'individual_decisions_std': agent_decision_counts.std(),
                'decision_activity_inequality': self._calculate_gini_coefficient(agent_decision_counts.values)
            }
            
        return comparison
        
    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient for inequality measurement."""
        if not values or len(values) < 2:
            return 0.0
            
        values = np.array(values)
        values = values[values >= 0]  # Remove negative values
        
        if len(values) == 0 or np.sum(values) == 0:
            return 0.0
            
        # Sort values
        sorted_values = np.sort(values)
        n = len(sorted_values)
        
        # Calculate Gini coefficient
        cumsum = np.cumsum(sorted_values)
        gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * np.sum(sorted_values)) - (n + 1) / n
        
        return gini
        
    @check_args_type
    def generate_individual_agent_report(self, agent_id: str, 
                                       output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive report for a specific agent.
        
        Args:
            agent_id: ID of agent to analyze
            output_file: Optional file to write report to
            
        Returns:
            Dictionary with complete agent analysis
        """
        if agent_id not in self.agent_trajectories:
            print(f"Warning: Agent {agent_id} not found in trajectories", file=sys.stderr)
            return {}
            
        trajectory = self.agent_trajectories[agent_id]
        
        report = {
            'agent_id': agent_id,
            'summary_statistics': trajectory.summary_stats,
            'trajectory_analysis': self._analyze_individual_trajectory(trajectory),
            'decision_analysis': self._analyze_individual_decisions(trajectory),
            'cognitive_analysis': self._analyze_individual_cognitive_behavior(trajectory),
            'social_analysis': self._analyze_individual_social_behavior(trajectory),
            'comparative_analysis': self._compare_agent_to_population(agent_id)
        }
        
        # Write to file if requested
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Individual agent report written to {output_path}", file=sys.stderr)
            
        return report
        
    def _analyze_individual_trajectory(self, trajectory: AgentTrajectory) -> Dict[str, Any]:
        """Analyze individual agent trajectory patterns."""
        points = trajectory.trajectory_points
        
        if len(points) < 2:
            return {'error': 'Insufficient trajectory data'}
            
        analysis = {}
        
        # Movement velocity analysis
        distances = [p.get('distance_moved_this_timestep', 0) for p in points]
        analysis['movement_velocity'] = {
            'avg_daily_movement': np.mean(distances),
            'max_daily_movement': max(distances),
            'movement_consistency': 1 - (np.std(distances) / max(1, np.mean(distances)))
        }
        
        # Location sequence analysis
        locations = [p.get('location', 'unknown') for p in points]
        location_changes = sum(1 for i in range(1, len(locations)) if locations[i] != locations[i-1])
        
        analysis['location_patterns'] = {
            'total_location_changes': location_changes,
            'avg_stay_duration': len(points) / max(1, location_changes),
            'location_sequence': locations[:10],  # First 10 locations
            'final_location': locations[-1] if locations else 'unknown'
        }
        
        # Temporal patterns
        times = [p['time'] for p in points]
        analysis['temporal_patterns'] = {
            'simulation_start': min(times),
            'simulation_end': max(times),
            'active_timesteps': len(set(times)),
            'data_completeness': len(set(times)) / (max(times) - min(times) + 1) if times else 0
        }
        
        return analysis
        
    def _analyze_individual_decisions(self, trajectory: AgentTrajectory) -> Dict[str, Any]:
        """Analyze individual agent decision-making patterns."""
        decisions = trajectory.decisions
        
        if not decisions:
            return {'total_decisions': 0}
            
        analysis = {
            'total_decisions': len(decisions),
            'decision_types': {},
            'cognitive_state_decisions': {},
            'confidence_analysis': {},
            'temporal_patterns': {}
        }
        
        # Decision type distribution
        for decision in decisions:
            decision_type = decision.get('decision_type', 'unknown')
            analysis['decision_types'][decision_type] = analysis['decision_types'].get(decision_type, 0) + 1
            
        # Decisions by cognitive state
        for decision in decisions:
            cognitive_state = decision.get('cognitive_state', 'S1')
            analysis['cognitive_state_decisions'][cognitive_state] = analysis['cognitive_state_decisions'].get(cognitive_state, 0) + 1
            
        # Confidence analysis
        movechances = [d.get('movechance', 0) for d in decisions if 'movechance' in d]
        if movechances:
            analysis['confidence_analysis'] = {
                'avg_confidence': np.mean(movechances),
                'confidence_std': np.std(movechances),
                'high_confidence_decisions': sum(1 for m in movechances if m > 0.7),
                'low_confidence_decisions': sum(1 for m in movechances if m < 0.3)
            }
            
        # Temporal decision patterns
        decision_times = [d.get('time', 0) for d in decisions]
        if decision_times:
            time_diffs = [decision_times[i] - decision_times[i-1] for i in range(1, len(decision_times))]
            analysis['temporal_patterns'] = {
                'avg_time_between_decisions': np.mean(time_diffs) if time_diffs else 0,
                'decision_frequency_variance': np.var(time_diffs) if time_diffs else 0,
                'early_decisions': sum(1 for t in decision_times if t < 30),
                'late_decisions': sum(1 for t in decision_times if t > 100)
            }
            
        return analysis
        
    def _analyze_individual_cognitive_behavior(self, trajectory: AgentTrajectory) -> Dict[str, Any]:
        """Analyze individual agent cognitive behavior patterns."""
        transitions = trajectory.cognitive_transitions
        points = trajectory.trajectory_points
        
        analysis = {
            'cognitive_transitions': len(transitions),
            'transition_patterns': {},
            'state_durations': {},
            'triggers': {}
        }
        
        # Analyze transition patterns
        if transitions:
            for transition in transitions:
                pattern = f"{transition['from_state']}_to_{transition['to_state']}"
                analysis['transition_patterns'][pattern] = analysis['transition_patterns'].get(pattern, 0) + 1
                
            # Analyze triggers
            for transition in transitions:
                trigger = transition.get('trigger', 'unknown')
                analysis['triggers'][trigger] = analysis['triggers'].get(trigger, 0) + 1
                
        # Analyze state durations
        if points:
            current_state = None
            state_start = None
            
            for point in points:
                state = point.get('cognitive_state', 'S1')
                time = point['time']
                
                if state != current_state:
                    if current_state is not None and state_start is not None:
                        duration = time - state_start
                        if current_state not in analysis['state_durations']:
                            analysis['state_durations'][current_state] = []
                        analysis['state_durations'][current_state].append(duration)
                        
                    current_state = state
                    state_start = time
                    
            # Calculate average durations
            for state, durations in analysis['state_durations'].items():
                analysis['state_durations'][state] = {
                    'avg_duration': np.mean(durations),
                    'total_episodes': len(durations),
                    'max_duration': max(durations),
                    'min_duration': min(durations)
                }
                
        return analysis
        
    def _analyze_individual_social_behavior(self, trajectory: AgentTrajectory) -> Dict[str, Any]:
        """Analyze individual agent social behavior patterns."""
        social_interactions = trajectory.social_interactions
        
        if not social_interactions:
            return {'social_interactions': 0}
            
        analysis = {
            'total_interactions': len(social_interactions),
            'connection_patterns': {},
            'information_sharing': {}
        }
        
        # Connection patterns
        connections = [s.get('connections', 0) for s in social_interactions]
        if connections:
            analysis['connection_patterns'] = {
                'max_connections': max(connections),
                'avg_connections': np.mean(connections),
                'connection_volatility': np.std(connections),
                'connection_growth': connections[-1] - connections[0] if len(connections) > 1 else 0
            }
            
        # Information sharing patterns
        info_shared = [s.get('information_shared', 0) for s in social_interactions]
        info_received = [s.get('information_received', 0) for s in social_interactions]
        
        if info_shared or info_received:
            analysis['information_sharing'] = {
                'total_shared': sum(info_shared),
                'total_received': sum(info_received),
                'sharing_ratio': sum(info_shared) / max(1, sum(info_received)),
                'net_information_flow': sum(info_received) - sum(info_shared)
            }
            
        return analysis
        
    def _compare_agent_to_population(self, agent_id: str) -> Dict[str, Any]:
        """Compare individual agent to population averages."""
        if agent_id not in self.agent_trajectories:
            return {}
            
        agent_stats = self.agent_trajectories[agent_id].summary_stats
        
        # Calculate population statistics
        all_stats = [t.summary_stats for t in self.agent_trajectories.values()]
        
        comparison = {}
        
        for stat_name in ['total_distance', 's2_proportion', 'unique_locations_visited', 
                         'cognitive_transitions_count', 'avg_connections']:
            agent_value = agent_stats.get(stat_name, 0)
            population_values = [s.get(stat_name, 0) for s in all_stats]
            
            if population_values:
                pop_mean = np.mean(population_values)
                pop_std = np.std(population_values)
                
                comparison[stat_name] = {
                    'agent_value': agent_value,
                    'population_mean': pop_mean,
                    'population_std': pop_std,
                    'z_score': (agent_value - pop_mean) / max(0.001, pop_std),
                    'percentile': sum(1 for v in population_values if v <= agent_value) / len(population_values) * 100
                }
                
        return comparison
        
    @check_args_type
    def export_analysis_results(self, output_directory: str) -> None:
        """
        Export all analysis results to files.
        
        Args:
            output_directory: Directory to write analysis files
        """
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export movement patterns
        if self.movement_patterns:
            patterns_file = output_dir / f"movement_patterns.{self.rank}.json"
            patterns_data = [
                {
                    'pattern_id': p.pattern_id,
                    'agent_count': len(p.agent_ids),
                    'characteristics': p.characteristics,
                    'cognitive_profile': p.cognitive_profile,
                    'spatial_signature': p.spatial_signature
                }
                for p in self.movement_patterns
            ]
            
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2, default=str)
                
        # Export decision clusters
        if self.decision_clusters:
            clusters_file = output_dir / f"decision_clusters.{self.rank}.json"
            with open(clusters_file, 'w') as f:
                json.dump(self.decision_clusters, f, indent=2)
                
        # Export individual trajectory summaries
        if self.agent_trajectories:
            summaries_file = output_dir / f"agent_summaries.{self.rank}.csv"
            
            summary_data = []
            for agent_id, trajectory in self.agent_trajectories.items():
                summary = {'agent_id': agent_id}
                summary.update(trajectory.summary_stats)
                summary_data.append(summary)
                
            df = pd.DataFrame(summary_data)
            df.to_csv(summaries_file, index=False)
            
        # Export comparative analysis
        comparison = self.compare_individual_vs_aggregate_patterns()
        if comparison:
            comparison_file = output_dir / f"individual_vs_aggregate.{self.rank}.json"
            with open(comparison_file, 'w') as f:
                json.dump(comparison, f, indent=2, default=str)
                
        print(f"Analysis results exported to {output_dir}", file=sys.stderr)