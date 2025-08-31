"""
Spatial Movement Visualization System for Dual Process Experiments

This module provides comprehensive spatial visualization capabilities for dual-process experiments,
including network layout algorithms, agent movement flow visualization, and spatial pattern analysis.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
from matplotlib.collections import LineCollection
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import warnings
from collections import defaultdict
import networkx as nx
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import DBSCAN, KMeans

# Optional plotly imports
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from .utils import LoggingUtils, ValidationUtils, FileUtils
    from .analysis_pipeline import AnalysisPipeline, ExperimentResults
    from .visualization_generator import PlotConfig
except ImportError:
    from utils import LoggingUtils, ValidationUtils, FileUtils
    from analysis_pipeline import AnalysisPipeline, ExperimentResults
    from visualization_generator import PlotConfig


@dataclass
class SpatialLayoutConfig:
    """Configuration for spatial network layout algorithms."""
    layout_algorithm: str = 'spring'  # 'spring', 'circular', 'kamada_kawai', 'spectral'
    node_size_scale: float = 1000.0
    edge_width_scale: float = 2.0
    node_spacing: float = 1.0
    iterations: int = 50
    k_spring: Optional[float] = None  # Spring constant for spring layout
    seed: int = 42


@dataclass
class AnimationConfig:
    """Configuration for temporal animation settings."""
    fps: int = 10
    interval: int = 200  # milliseconds between frames
    duration_seconds: Optional[int] = None
    save_format: str = 'mp4'  # 'mp4', 'gif'
    dpi: int = 100
    bitrate: int = 1800


class SpatialVisualizationGenerator:
    """
    Spatial visualization generator for dual-process experiments.
    
    This class creates spatial network layouts, agent movement flow visualizations,
    temporal animations, and spatial pattern analysis tools.
    """
    
    def __init__(self, results_directory: str, output_directory: str = None, 
                 backend: str = 'matplotlib', plot_config: PlotConfig = None,
                 spatial_config: SpatialLayoutConfig = None,
                 animation_config: AnimationConfig = None):
        """
        Initialize spatial visualization generator.
        
        Args:
            results_directory: Directory containing experiment results
            output_directory: Directory for visualization outputs
            backend: Visualization backend ('matplotlib' or 'plotly')
            plot_config: Configuration for plot styling
            spatial_config: Configuration for spatial layout algorithms
            animation_config: Configuration for temporal animations
        """
        self.results_directory = Path(results_directory)
        self.output_directory = Path(output_directory) if output_directory else self.results_directory / "spatial_visualizations"
        self.backend = backend.lower()
        self.plot_config = plot_config or PlotConfig()
        self.spatial_config = spatial_config or SpatialLayoutConfig()
        self.animation_config = animation_config or AnimationConfig()
        
        # Initialize utilities
        self.logging_utils = LoggingUtils()
        self.validation_utils = ValidationUtils()
        self.file_utils = FileUtils()
        
        # Setup logger
        self.logger = self.logging_utils.get_logger('SpatialVisualizationGenerator')
        
        # Ensure output directory exists
        self.file_utils.ensure_directory(str(self.output_directory))
        
        # Initialize analysis pipeline for data loading
        self.analysis_pipeline = AnalysisPipeline(str(self.results_directory))
        
        # Validate backend
        if self.backend == 'plotly' and not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available, falling back to matplotlib")
            self.backend = 'matplotlib'
        
        # Setup matplotlib style
        if self.backend == 'matplotlib':
            self._setup_matplotlib_style()
        
        # Cache for network layouts
        self._layout_cache = {}
        
        self.logger.info(f"SpatialVisualizationGenerator initialized with backend: {self.backend}")
        self.logger.info(f"Spatial visualizations will be saved to: {self.output_directory}")
    
    def _setup_matplotlib_style(self):
        """Setup matplotlib styling for spatial plots."""
        plt.rcParams.update({
            'font.size': self.plot_config.font_size,
            'axes.titlesize': self.plot_config.title_size,
            'axes.labelsize': self.plot_config.label_size,
            'xtick.labelsize': self.plot_config.label_size,
            'ytick.labelsize': self.plot_config.label_size,
            'legend.fontsize': self.plot_config.legend_size,
            'figure.titlesize': self.plot_config.title_size,
            'lines.linewidth': self.plot_config.line_width,
            'lines.markersize': self.plot_config.marker_size,
            'figure.dpi': self.plot_config.dpi,
            'savefig.dpi': self.plot_config.save_dpi,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1
        })
    
    def create_network_spatial_layout(self, experiment_dir: str, 
                                    layout_algorithm: str = None) -> Optional[Dict[str, Any]]:
        """
        Create automatic network layout for spatial visualization.
        
        Args:
            experiment_dir: Path to experiment directory
            layout_algorithm: Layout algorithm to use (overrides config)
            
        Returns:
            Dictionary containing network layout information
        """
        try:
            # Load experiment data
            results = self.analysis_pipeline.load_experiment_data(experiment_dir)
            
            # Load network topology from input files
            network_data = self._load_network_topology(experiment_dir)
            if not network_data:
                self.logger.error(f"Failed to load network topology for {experiment_dir}")
                return None
            
            # Use specified algorithm or default from config
            algorithm = layout_algorithm or self.spatial_config.layout_algorithm
            
            # Check cache
            cache_key = f"{experiment_dir}_{algorithm}"
            if cache_key in self._layout_cache:
                self.logger.debug(f"Using cached layout for {cache_key}")
                return self._layout_cache[cache_key]
            
            # Create NetworkX graph
            G = self._create_networkx_graph(network_data)
            
            # Generate layout
            layout_info = self._generate_network_layout(G, network_data, algorithm)
            
            # Cache the layout
            self._layout_cache[cache_key] = layout_info
            
            self.logger.info(f"Created network spatial layout using {algorithm} algorithm")
            return layout_info
            
        except Exception as e:
            self.logger.error(f"Failed to create network spatial layout: {e}")
            return None
    
    def _load_network_topology(self, experiment_dir: str) -> Optional[Dict[str, Any]]:
        """
        Load network topology from experiment input files.
        
        Args:
            experiment_dir: Path to experiment directory
            
        Returns:
            Dictionary containing locations and routes data
        """
        try:
            exp_path = Path(experiment_dir)
            
            # Look for locations.csv and routes.csv
            locations_file = exp_path / "locations.csv"
            routes_file = exp_path / "routes.csv"
            
            if not locations_file.exists() or not routes_file.exists():
                self.logger.warning(f"Network topology files not found in {experiment_dir}")
                return None
            
            # Load locations
            locations_df = pd.read_csv(locations_file)
            routes_df = pd.read_csv(routes_file)
            
            # Validate required columns
            required_location_cols = ['name']
            required_route_cols = ['name1', 'name2']
            
            if not all(col in locations_df.columns for col in required_location_cols):
                self.logger.error(f"Missing required columns in locations.csv: {required_location_cols}")
                return None
            
            if not all(col in routes_df.columns for col in required_route_cols):
                self.logger.error(f"Missing required columns in routes.csv: {required_route_cols}")
                return None
            
            return {
                'locations': locations_df,
                'routes': routes_df
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load network topology: {e}")
            return None
    
    def _create_networkx_graph(self, network_data: Dict[str, Any]) -> nx.Graph:
        """
        Create NetworkX graph from network topology data.
        
        Args:
            network_data: Dictionary containing locations and routes data
            
        Returns:
            NetworkX graph object
        """
        G = nx.Graph()
        
        locations_df = network_data['locations']
        routes_df = network_data['routes']
        
        # Add nodes with attributes
        for _, location in locations_df.iterrows():
            node_attrs = {
                'name': location['name'],
                'population': location.get('population', 0),
                'capacity': location.get('capacity', 0),
                'location_type': location.get('location_type', 'unknown')
            }
            
            # Add coordinates if available
            if 'x' in location and 'y' in location:
                node_attrs['x'] = location['x']
                node_attrs['y'] = location['y']
            
            G.add_node(location['name'], **node_attrs)
        
        # Add edges with attributes
        for _, route in routes_df.iterrows():
            edge_attrs = {
                'distance': route.get('distance', 1.0),
                'forced_redirection': route.get('forced_redirection', 0)
            }
            
            G.add_edge(route['name1'], route['name2'], **edge_attrs)
        
        return G
    
    def _generate_network_layout(self, G: nx.Graph, network_data: Dict[str, Any], 
                                algorithm: str) -> Dict[str, Any]:
        """
        Generate network layout using specified algorithm.
        
        Args:
            G: NetworkX graph
            network_data: Original network data
            algorithm: Layout algorithm name
            
        Returns:
            Dictionary containing layout information
        """
        # Check if coordinates are already provided
        has_coordinates = all('x' in G.nodes[node] and 'y' in G.nodes[node] for node in G.nodes())
        
        if has_coordinates and algorithm != 'force_recalculate':
            # Use existing coordinates
            pos = {node: (G.nodes[node]['x'], G.nodes[node]['y']) for node in G.nodes()}
            self.logger.info("Using existing node coordinates")
        else:
            # Generate layout using specified algorithm
            np.random.seed(self.spatial_config.seed)
            
            if algorithm == 'spring':
                pos = nx.spring_layout(
                    G, 
                    k=self.spatial_config.k_spring,
                    iterations=self.spatial_config.iterations,
                    seed=self.spatial_config.seed
                )
            elif algorithm == 'circular':
                pos = nx.circular_layout(G)
            elif algorithm == 'kamada_kawai':
                pos = nx.kamada_kawai_layout(G)
            elif algorithm == 'spectral':
                pos = nx.spectral_layout(G, seed=self.spatial_config.seed)
            elif algorithm == 'random':
                pos = nx.random_layout(G, seed=self.spatial_config.seed)
            else:
                self.logger.warning(f"Unknown layout algorithm: {algorithm}, using spring")
                pos = nx.spring_layout(G, seed=self.spatial_config.seed)
        
        # Calculate node sizes based on population/capacity
        node_sizes = {}
        for node in G.nodes():
            population = G.nodes[node].get('population', 0)
            capacity = G.nodes[node].get('capacity', 0)
            # Use max of population and capacity, with minimum size
            size = max(population, capacity, 100) * self.spatial_config.node_size_scale / 1000
            node_sizes[node] = size
        
        # Calculate edge widths based on distance (inverse relationship)
        edge_widths = {}
        for edge in G.edges():
            distance = G.edges[edge].get('distance', 1.0)
            # Inverse relationship: shorter distances = thicker lines
            width = self.spatial_config.edge_width_scale / max(distance, 0.1)
            edge_widths[edge] = width
        
        # Determine node colors based on location type
        node_colors = {}
        color_map = {
            'town': '#FF6B6B',      # Red for towns/origins
            'camp': '#4ECDC4',      # Teal for camps
            'conflict_zone': '#FF4757',  # Bright red for conflict zones
            'safe_zone': '#2ED573',      # Green for safe zones
            'unknown': '#A4B0BE'         # Gray for unknown
        }
        
        for node in G.nodes():
            location_type = G.nodes[node].get('location_type', 'unknown')
            node_colors[node] = color_map.get(location_type, color_map['unknown'])
        
        layout_info = {
            'graph': G,
            'positions': pos,
            'node_sizes': node_sizes,
            'edge_widths': edge_widths,
            'node_colors': node_colors,
            'algorithm': algorithm,
            'network_data': network_data
        }
        
        return layout_info
    
    def create_agent_movement_flow_visualization(self, experiment_dir: str, 
                                               cognitive_mode_colors: Dict[str, str] = None,
                                               time_range: Tuple[int, int] = None) -> Optional[str]:
        """
        Create agent movement flow visualization with cognitive mode color coding.
        
        Args:
            experiment_dir: Path to experiment directory
            cognitive_mode_colors: Color mapping for cognitive modes
            time_range: Tuple of (start_day, end_day) to filter data
            
        Returns:
            Path to generated visualization file
        """
        try:
            # Load experiment data
            results = self.analysis_pipeline.load_experiment_data(experiment_dir)
            
            if results.movement_data is None or results.movement_data.empty:
                self.logger.warning(f"No movement data available for {experiment_dir}")
                return None
            
            # Get network layout
            layout_info = self.create_network_spatial_layout(experiment_dir)
            if not layout_info:
                self.logger.error(f"Failed to create network layout for {experiment_dir}")
                return None
            
            # Default cognitive mode colors
            if cognitive_mode_colors is None:
                cognitive_mode_colors = {
                    'S1': '#FF6B6B',  # Red for System 1
                    'S2': '#4ECDC4',  # Teal for System 2
                    'unknown': '#A4B0BE'  # Gray for unknown
                }
            
            # Filter movement data by time range if specified
            movement_data = results.movement_data.copy()
            if time_range:
                start_day, end_day = time_range
                movement_data = movement_data[
                    (movement_data['day'] >= start_day) & 
                    (movement_data['day'] <= end_day)
                ]
            
            if self.backend == 'matplotlib':
                plot_file = self._create_matplotlib_movement_flow(
                    movement_data, results.cognitive_states, layout_info, 
                    cognitive_mode_colors, results.experiment_id
                )
            else:
                plot_file = self._create_plotly_movement_flow(
                    movement_data, results.cognitive_states, layout_info, 
                    cognitive_mode_colors, results.experiment_id
                )
            
            return plot_file
            
        except Exception as e:
            self.logger.error(f"Failed to create movement flow visualization: {e}")
            return None
    
    def _create_matplotlib_movement_flow(self, movement_data: pd.DataFrame, 
                                       cognitive_states: pd.DataFrame,
                                       layout_info: Dict[str, Any],
                                       cognitive_mode_colors: Dict[str, str],
                                       experiment_id: str) -> Optional[str]:
        """
        Create movement flow visualization using matplotlib.
        
        Args:
            movement_data: DataFrame with agent movement data
            cognitive_states: DataFrame with cognitive states data
            layout_info: Network layout information
            cognitive_mode_colors: Color mapping for cognitive modes
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, ax = plt.subplots(figsize=(15, 12))
            
            G = layout_info['graph']
            pos = layout_info['positions']
            node_sizes = layout_info['node_sizes']
            edge_widths = layout_info['edge_widths']
            node_colors = layout_info['node_colors']
            
            # Draw network structure
            nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, 
                                 width=[edge_widths[edge] for edge in G.edges()])
            
            # Draw nodes
            for node in G.nodes():
                x, y = pos[node]
                ax.scatter(x, y, s=node_sizes[node], c=node_colors[node], 
                          alpha=0.7, edgecolors='black', linewidth=1)
                ax.annotate(node, (x, y), xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.8)
            
            # Create movement flow lines
            if 'agent_id' in movement_data.columns and 'location' in movement_data.columns:
                # Group movements by agent and create trajectories
                agent_trajectories = {}
                
                for agent_id in movement_data['agent_id'].unique():
                    agent_moves = movement_data[movement_data['agent_id'] == agent_id].sort_values('day')
                    if len(agent_moves) > 1:
                        trajectory = []
                        for i in range(len(agent_moves) - 1):
                            from_loc = agent_moves.iloc[i]['location']
                            to_loc = agent_moves.iloc[i + 1]['location']
                            day = agent_moves.iloc[i + 1]['day']
                            
                            if from_loc in pos and to_loc in pos and from_loc != to_loc:
                                trajectory.append({
                                    'from': from_loc,
                                    'to': to_loc,
                                    'day': day,
                                    'from_pos': pos[from_loc],
                                    'to_pos': pos[to_loc]
                                })
                        
                        if trajectory:
                            agent_trajectories[agent_id] = trajectory
                
                # Draw movement flows with cognitive mode colors
                for agent_id, trajectory in agent_trajectories.items():
                    for move in trajectory:
                        # Get cognitive state for this agent at this time
                        cognitive_state = 'unknown'
                        if cognitive_states is not None and not cognitive_states.empty:
                            agent_cognitive = cognitive_states[
                                (cognitive_states['agent_id'] == agent_id) & 
                                (cognitive_states['day'] == move['day'])
                            ]
                            if not agent_cognitive.empty:
                                cognitive_state = agent_cognitive.iloc[0]['cognitive_state']
                        
                        color = cognitive_mode_colors.get(cognitive_state, cognitive_mode_colors['unknown'])
                        
                        # Draw arrow for movement
                        ax.annotate('', xy=move['to_pos'], xytext=move['from_pos'],
                                   arrowprops=dict(arrowstyle='->', color=color, alpha=0.6, lw=1))
            
            # Create legend for cognitive modes
            legend_elements = []
            for mode, color in cognitive_mode_colors.items():
                legend_elements.append(plt.Line2D([0], [0], color=color, lw=3, label=mode))
            
            ax.legend(handles=legend_elements, title='Cognitive Mode', loc='upper right')
            
            ax.set_title(f'Agent Movement Flow Visualization - {experiment_id}', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            ax.set_xlabel('Spatial X Coordinate')
            ax.set_ylabel('Spatial Y Coordinate')
            ax.grid(True, alpha=0.3)
            
            # Save plot
            output_file = self.output_directory / f"movement_flow_{experiment_id}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created movement flow visualization: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib movement flow visualization: {e}")
            return None
    
    def _create_plotly_movement_flow(self, movement_data: pd.DataFrame, 
                                   cognitive_states: pd.DataFrame,
                                   layout_info: Dict[str, Any],
                                   cognitive_mode_colors: Dict[str, str],
                                   experiment_id: str) -> Optional[str]:
        """
        Create movement flow visualization using plotly.
        
        Args:
            movement_data: DataFrame with agent movement data
            cognitive_states: DataFrame with cognitive states data
            layout_info: Network layout information
            cognitive_mode_colors: Color mapping for cognitive modes
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated plot file
        """
        try:
            G = layout_info['graph']
            pos = layout_info['positions']
            node_sizes = layout_info['node_sizes']
            node_colors = layout_info['node_colors']
            
            fig = go.Figure()
            
            # Draw network edges
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            fig.add_trace(go.Scatter(x=edge_x, y=edge_y,
                                   line=dict(width=1, color='#888'),
                                   hoverinfo='none',
                                   mode='lines',
                                   name='Network'))
            
            # Draw nodes
            node_x = []
            node_y = []
            node_text = []
            node_color_list = []
            node_size_list = []
            
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(node)
                node_color_list.append(node_colors[node])
                node_size_list.append(node_sizes[node] / 50)  # Scale for plotly
            
            fig.add_trace(go.Scatter(x=node_x, y=node_y,
                                   mode='markers+text',
                                   marker=dict(size=node_size_list,
                                             color=node_color_list,
                                             line=dict(width=2, color='black')),
                                   text=node_text,
                                   textposition="middle center",
                                   name='Locations'))
            
            # Add movement flows
            if 'agent_id' in movement_data.columns and 'location' in movement_data.columns:
                for cognitive_mode, color in cognitive_mode_colors.items():
                    flow_x = []
                    flow_y = []
                    
                    for agent_id in movement_data['agent_id'].unique():
                        agent_moves = movement_data[movement_data['agent_id'] == agent_id].sort_values('day')
                        
                        if len(agent_moves) > 1:
                            for i in range(len(agent_moves) - 1):
                                from_loc = agent_moves.iloc[i]['location']
                                to_loc = agent_moves.iloc[i + 1]['location']
                                day = agent_moves.iloc[i + 1]['day']
                                
                                # Get cognitive state
                                agent_cognitive_state = 'unknown'
                                if cognitive_states is not None and not cognitive_states.empty:
                                    agent_cognitive = cognitive_states[
                                        (cognitive_states['agent_id'] == agent_id) & 
                                        (cognitive_states['day'] == day)
                                    ]
                                    if not agent_cognitive.empty:
                                        agent_cognitive_state = agent_cognitive.iloc[0]['cognitive_state']
                                
                                if (agent_cognitive_state == cognitive_mode and 
                                    from_loc in pos and to_loc in pos and from_loc != to_loc):
                                    x0, y0 = pos[from_loc]
                                    x1, y1 = pos[to_loc]
                                    flow_x.extend([x0, x1, None])
                                    flow_y.extend([y0, y1, None])
                    
                    if flow_x:  # Only add trace if there are flows for this mode
                        fig.add_trace(go.Scatter(x=flow_x, y=flow_y,
                                               line=dict(width=2, color=color),
                                               mode='lines',
                                               name=f'{cognitive_mode} Flows',
                                               opacity=0.6))
            
            fig.update_layout(
                title=f'Agent Movement Flow Visualization - {experiment_id}',
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Movement flows colored by cognitive mode",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(size=12)
                )],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            
            # Save plot
            output_file = self.output_directory / f"movement_flow_{experiment_id}.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created movement flow visualization: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly movement flow visualization: {e}")
            return None
    
    def create_temporal_animation(self, experiment_dir: str, 
                                time_step: int = 1,
                                max_frames: int = 100) -> Optional[str]:
        """
        Create temporal animation of agent movement evolution over time.
        
        Args:
            experiment_dir: Path to experiment directory
            time_step: Time step between animation frames
            max_frames: Maximum number of animation frames
            
        Returns:
            Path to generated animation file
        """
        try:
            # Load experiment data
            results = self.analysis_pipeline.load_experiment_data(experiment_dir)
            
            if results.movement_data is None or results.movement_data.empty:
                self.logger.warning(f"No movement data available for {experiment_dir}")
                return None
            
            # Get network layout
            layout_info = self.create_network_spatial_layout(experiment_dir)
            if not layout_info:
                self.logger.error(f"Failed to create network layout for {experiment_dir}")
                return None
            
            movement_data = results.movement_data
            cognitive_states = results.cognitive_states
            
            # Determine time range
            min_day = movement_data['day'].min()
            max_day = movement_data['day'].max()
            time_points = list(range(min_day, min(max_day + 1, min_day + max_frames * time_step), time_step))
            
            if self.backend == 'matplotlib':
                animation_file = self._create_matplotlib_animation(
                    movement_data, cognitive_states, layout_info, 
                    time_points, results.experiment_id
                )
            else:
                animation_file = self._create_plotly_animation(
                    movement_data, cognitive_states, layout_info, 
                    time_points, results.experiment_id
                )
            
            return animation_file
            
        except Exception as e:
            self.logger.error(f"Failed to create temporal animation: {e}")
            return None
    
    def _create_matplotlib_animation(self, movement_data: pd.DataFrame,
                                   cognitive_states: pd.DataFrame,
                                   layout_info: Dict[str, Any],
                                   time_points: List[int],
                                   experiment_id: str) -> Optional[str]:
        """
        Create temporal animation using matplotlib.
        
        Args:
            movement_data: DataFrame with agent movement data
            cognitive_states: DataFrame with cognitive states data
            layout_info: Network layout information
            time_points: List of time points for animation frames
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated animation file
        """
        try:
            G = layout_info['graph']
            pos = layout_info['positions']
            node_sizes = layout_info['node_sizes']
            node_colors = layout_info['node_colors']
            
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Cognitive mode colors
            cognitive_mode_colors = {
                'S1': '#FF6B6B',  # Red for System 1
                'S2': '#4ECDC4',  # Teal for System 2
                'unknown': '#A4B0BE'  # Gray for unknown
            }
            
            def animate(frame):
                ax.clear()
                current_day = time_points[frame]
                
                # Draw network structure
                nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, width=1)
                
                # Draw nodes
                for node in G.nodes():
                    x, y = pos[node]
                    ax.scatter(x, y, s=node_sizes[node]/10, c=node_colors[node], 
                              alpha=0.7, edgecolors='black', linewidth=1)
                    ax.annotate(node, (x, y), xytext=(5, 5), textcoords='offset points',
                               fontsize=8, alpha=0.8)
                
                # Get current agent positions
                current_positions = movement_data[movement_data['day'] == current_day]
                
                if not current_positions.empty:
                    # Draw agents at their current locations
                    for _, agent_row in current_positions.iterrows():
                        agent_id = agent_row['agent_id']
                        location = agent_row['location']
                        
                        if location in pos:
                            # Get cognitive state
                            cognitive_state = 'unknown'
                            if cognitive_states is not None and not cognitive_states.empty:
                                agent_cognitive = cognitive_states[
                                    (cognitive_states['agent_id'] == agent_id) & 
                                    (cognitive_states['day'] == current_day)
                                ]
                                if not agent_cognitive.empty:
                                    cognitive_state = agent_cognitive.iloc[0]['cognitive_state']
                            
                            color = cognitive_mode_colors.get(cognitive_state, cognitive_mode_colors['unknown'])
                            x, y = pos[location]
                            
                            # Add small offset to avoid overlap
                            offset = np.random.normal(0, 0.02, 2)
                            ax.scatter(x + offset[0], y + offset[1], s=20, c=color, 
                                      alpha=0.8, edgecolors='white', linewidth=0.5)
                
                ax.set_title(f'Agent Movement Animation - Day {current_day}\n{experiment_id}', 
                            fontsize=self.plot_config.title_size)
                ax.set_xlabel('Spatial X Coordinate')
                ax.set_ylabel('Spatial Y Coordinate')
                ax.grid(True, alpha=0.3)
                
                # Create legend
                legend_elements = []
                for mode, color in cognitive_mode_colors.items():
                    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                     markerfacecolor=color, markersize=8, label=mode))
                ax.legend(handles=legend_elements, title='Cognitive Mode', loc='upper right')
            
            # Create animation
            anim = animation.FuncAnimation(fig, animate, frames=len(time_points), 
                                         interval=self.animation_config.interval, 
                                         blit=False, repeat=True)
            
            # Save animation
            output_file = self.output_directory / f"movement_animation_{experiment_id}.{self.animation_config.save_format}"
            
            if self.animation_config.save_format == 'mp4':
                Writer = animation.writers['ffmpeg']
                writer = Writer(fps=self.animation_config.fps, 
                               metadata=dict(artist='SpatialVisualizationGenerator'), 
                               bitrate=self.animation_config.bitrate)
                anim.save(str(output_file), writer=writer, dpi=self.animation_config.dpi)
            elif self.animation_config.save_format == 'gif':
                anim.save(str(output_file), writer='pillow', fps=self.animation_config.fps, 
                         dpi=self.animation_config.dpi)
            
            plt.close()
            
            self.logger.debug(f"Created temporal animation: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib animation: {e}")
            return None
    
    def create_interactive_spatial_exploration(self, experiment_dir: str) -> Optional[str]:
        """
        Create interactive spatial exploration with zoom and filtering capabilities.
        
        Args:
            experiment_dir: Path to experiment directory
            
        Returns:
            Path to generated interactive visualization file
        """
        try:
            if self.backend != 'plotly':
                self.logger.warning("Interactive exploration requires plotly backend")
                return None
            
            # Load experiment data
            results = self.analysis_pipeline.load_experiment_data(experiment_dir)
            
            if results.movement_data is None or results.movement_data.empty:
                self.logger.warning(f"No movement data available for {experiment_dir}")
                return None
            
            # Get network layout
            layout_info = self.create_network_spatial_layout(experiment_dir)
            if not layout_info:
                self.logger.error(f"Failed to create network layout for {experiment_dir}")
                return None
            
            return self._create_plotly_interactive_exploration(
                results.movement_data, results.cognitive_states, 
                layout_info, results.experiment_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create interactive spatial exploration: {e}")
            return None
    
    def _create_plotly_interactive_exploration(self, movement_data: pd.DataFrame,
                                             cognitive_states: pd.DataFrame,
                                             layout_info: Dict[str, Any],
                                             experiment_id: str) -> Optional[str]:
        """
        Create interactive spatial exploration using plotly.
        
        Args:
            movement_data: DataFrame with agent movement data
            cognitive_states: DataFrame with cognitive states data
            layout_info: Network layout information
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated interactive visualization file
        """
        try:
            G = layout_info['graph']
            pos = layout_info['positions']
            node_sizes = layout_info['node_sizes']
            node_colors = layout_info['node_colors']
            
            # Create subplots for different views
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Network Overview', 'Agent Trajectories', 
                               'Cognitive State Distribution', 'Movement Heatmap'),
                specs=[[{"type": "scatter"}, {"type": "scatter"}],
                       [{"type": "bar"}, {"type": "scatter"}]]
            )
            
            # Plot 1: Network Overview
            # Add edges
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            fig.add_trace(go.Scatter(x=edge_x, y=edge_y,
                                   line=dict(width=1, color='#888'),
                                   hoverinfo='none',
                                   mode='lines',
                                   showlegend=False),
                         row=1, col=1)
            
            # Add nodes with hover information
            node_x = []
            node_y = []
            node_text = []
            node_hover = []
            node_color_list = []
            node_size_list = []
            
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(node)
                
                # Calculate statistics for this location
                location_visits = movement_data[movement_data['location'] == node]
                unique_agents = location_visits['agent_id'].nunique() if not location_visits.empty else 0
                total_visits = len(location_visits)
                
                hover_text = f"Location: {node}<br>Unique Agents: {unique_agents}<br>Total Visits: {total_visits}"
                node_hover.append(hover_text)
                
                node_color_list.append(node_colors[node])
                node_size_list.append(max(10, node_sizes[node] / 100))
            
            fig.add_trace(go.Scatter(x=node_x, y=node_y,
                                   mode='markers+text',
                                   marker=dict(size=node_size_list,
                                             color=node_color_list,
                                             line=dict(width=2, color='black')),
                                   text=node_text,
                                   hovertext=node_hover,
                                   hoverinfo='text',
                                   textposition="middle center",
                                   showlegend=False),
                         row=1, col=1)
            
            # Plot 2: Sample Agent Trajectories
            sample_agents = movement_data['agent_id'].unique()[:10]  # Sample 10 agents
            colors = px.colors.qualitative.Set3
            
            for i, agent_id in enumerate(sample_agents):
                agent_moves = movement_data[movement_data['agent_id'] == agent_id].sort_values('day')
                
                if len(agent_moves) > 1:
                    traj_x = []
                    traj_y = []
                    
                    for _, move in agent_moves.iterrows():
                        location = move['location']
                        if location in pos:
                            x, y = pos[location]
                            traj_x.append(x)
                            traj_y.append(y)
                    
                    if len(traj_x) > 1:
                        fig.add_trace(go.Scatter(x=traj_x, y=traj_y,
                                               mode='lines+markers',
                                               line=dict(color=colors[i % len(colors)], width=2),
                                               marker=dict(size=5),
                                               name=f'Agent {agent_id}',
                                               showlegend=False),
                                     row=1, col=2)
            
            # Plot 3: Cognitive State Distribution
            if cognitive_states is not None and not cognitive_states.empty:
                state_counts = cognitive_states['cognitive_state'].value_counts()
                
                fig.add_trace(go.Bar(x=state_counts.index, y=state_counts.values,
                                   marker_color=['#FF6B6B', '#4ECDC4'],
                                   showlegend=False),
                             row=2, col=1)
            
            # Plot 4: Movement Heatmap (location popularity)
            location_popularity = movement_data['location'].value_counts()
            
            heatmap_x = []
            heatmap_y = []
            heatmap_z = []
            
            for location, count in location_popularity.items():
                if location in pos:
                    x, y = pos[location]
                    heatmap_x.append(x)
                    heatmap_y.append(y)
                    heatmap_z.append(count)
            
            fig.add_trace(go.Scatter(x=heatmap_x, y=heatmap_y,
                                   mode='markers',
                                   marker=dict(size=[z/10 for z in heatmap_z],
                                             color=heatmap_z,
                                             colorscale='Viridis',
                                             showscale=True,
                                             colorbar=dict(title="Visit Count")),
                                   text=[f"Visits: {z}" for z in heatmap_z],
                                   hoverinfo='text',
                                   showlegend=False),
                         row=2, col=2)
            
            # Update layout
            fig.update_layout(
                title_text=f'Interactive Spatial Exploration - {experiment_id}',
                height=800,
                showlegend=False
            )
            
            # Update axes
            for i in range(1, 3):
                for j in range(1, 3):
                    if (i, j) in [(1, 1), (1, 2), (2, 2)]:  # Spatial plots
                        fig.update_xaxes(title_text="X Coordinate", row=i, col=j)
                        fig.update_yaxes(title_text="Y Coordinate", row=i, col=j)
                    elif (i, j) == (2, 1):  # Bar plot
                        fig.update_xaxes(title_text="Cognitive State", row=i, col=j)
                        fig.update_yaxes(title_text="Count", row=i, col=j)
            
            # Save interactive plot
            output_file = self.output_directory / f"interactive_exploration_{experiment_id}.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created interactive spatial exploration: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create interactive spatial exploration: {e}")
            return None


class SpatialPatternAnalyzer:
    """
    Spatial pattern analysis tools for movement pattern identification and quantification.
    
    This class provides location occupancy heatmaps, transition frequency analysis,
    spatial clustering algorithms, and cognitive mode spatial comparison visualizations.
    """
    
    def __init__(self, results_directory: str, output_directory: str = None,
                 plot_config: PlotConfig = None):
        """
        Initialize spatial pattern analyzer.
        
        Args:
            results_directory: Directory containing experiment results
            output_directory: Directory for analysis outputs
            plot_config: Configuration for plot styling
        """
        self.results_directory = Path(results_directory)
        self.output_directory = Path(output_directory) if output_directory else self.results_directory / "spatial_analysis"
        self.plot_config = plot_config or PlotConfig()
        
        # Initialize utilities
        self.logging_utils = LoggingUtils()
        self.validation_utils = ValidationUtils()
        self.file_utils = FileUtils()
        
        # Setup logger
        self.logger = self.logging_utils.get_logger('SpatialPatternAnalyzer')
        
        # Ensure output directory exists
        self.file_utils.ensure_directory(str(self.output_directory))
        
        # Initialize analysis pipeline
        self.analysis_pipeline = AnalysisPipeline(str(self.results_directory))
        
        self.logger.info(f"SpatialPatternAnalyzer initialized")
        self.logger.info(f"Analysis outputs will be saved to: {self.output_directory}")
    
    def create_location_occupancy_heatmaps(self, experiment_dirs: List[str],
                                         time_windows: List[Tuple[int, int]] = None) -> List[str]:
        """
        Create location occupancy heatmaps showing agent density over time.
        
        Args:
            experiment_dirs: List of experiment directory paths
            time_windows: List of (start_day, end_day) tuples for temporal analysis
            
        Returns:
            List of generated heatmap file paths
        """
        try:
            generated_plots = []
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    self.logger.warning(f"No movement data for {experiment_dir}")
                    continue
                
                # Create heatmaps for different time windows
                if time_windows is None:
                    # Create overall heatmap
                    plot_file = self._create_occupancy_heatmap(
                        results.movement_data, results.experiment_id, None
                    )
                    if plot_file:
                        generated_plots.append(plot_file)
                else:
                    # Create heatmaps for each time window
                    for i, (start_day, end_day) in enumerate(time_windows):
                        filtered_data = results.movement_data[
                            (results.movement_data['day'] >= start_day) & 
                            (results.movement_data['day'] <= end_day)
                        ]
                        
                        if not filtered_data.empty:
                            plot_file = self._create_occupancy_heatmap(
                                filtered_data, results.experiment_id, 
                                f"days_{start_day}_{end_day}"
                            )
                            if plot_file:
                                generated_plots.append(plot_file)
            
            self.logger.info(f"Generated {len(generated_plots)} occupancy heatmaps")
            return generated_plots
            
        except Exception as e:
            self.logger.error(f"Failed to create occupancy heatmaps: {e}")
            return []
    
    def _create_occupancy_heatmap(self, movement_data: pd.DataFrame, 
                                experiment_id: str, time_suffix: str = None) -> Optional[str]:
        """
        Create a single occupancy heatmap.
        
        Args:
            movement_data: DataFrame with movement data
            experiment_id: Experiment identifier
            time_suffix: Optional suffix for time window
            
        Returns:
            Path to generated heatmap file
        """
        try:
            # Calculate location occupancy
            location_occupancy = movement_data.groupby(['location', 'day']).size().reset_index(name='agent_count')
            
            # Create pivot table for heatmap
            occupancy_matrix = location_occupancy.pivot(index='location', columns='day', values='agent_count')
            occupancy_matrix = occupancy_matrix.fillna(0)
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(15, 8))
            
            sns.heatmap(occupancy_matrix, ax=ax, cmap='YlOrRd', 
                       cbar_kws={'label': 'Number of Agents'},
                       linewidths=0.1, linecolor='white')
            
            title = f'Location Occupancy Heatmap - {experiment_id}'
            if time_suffix:
                title += f' ({time_suffix})'
            
            ax.set_title(title, fontsize=self.plot_config.title_size, fontweight='bold')
            ax.set_xlabel('Day')
            ax.set_ylabel('Location')
            
            plt.tight_layout()
            
            # Save plot
            filename = f"occupancy_heatmap_{experiment_id}"
            if time_suffix:
                filename += f"_{time_suffix}"
            filename += f".{self.plot_config.save_format}"
            
            output_file = self.output_directory / filename
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created occupancy heatmap: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create occupancy heatmap: {e}")
            return None
    
    def _calculate_occupancy_statistics(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate occupancy statistics from movement data.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary containing occupancy statistics
        """
        try:
            # Calculate basic occupancy metrics
            location_counts = movement_data['location'].value_counts()
            daily_counts = movement_data.groupby('day').size()
            
            stats = {
                'total_observations': len(movement_data),
                'unique_locations': movement_data['location'].nunique(),
                'time_span': movement_data['day'].max() - movement_data['day'].min(),
                'location_popularity': {
                    'most_popular': location_counts.index[0] if not location_counts.empty else None,
                    'max_occupancy': location_counts.iloc[0] if not location_counts.empty else 0,
                    'occupancy_distribution': location_counts.to_dict()
                },
                'temporal_patterns': {
                    'mean_daily_occupancy': daily_counts.mean(),
                    'std_daily_occupancy': daily_counts.std(),
                    'peak_occupancy_day': daily_counts.idxmax(),
                    'peak_occupancy_count': daily_counts.max()
                },
                'occupancy_concentration': self._calculate_gini_coefficient(location_counts.values)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate occupancy statistics: {e}")
            return {}
    
    def analyze_transition_frequencies(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Analyze transition frequency patterns between locations.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary containing transition analysis results
        """
        try:
            all_transitions = []
            experiment_results = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Calculate transitions for this experiment
                transitions = self._calculate_location_transitions(results.movement_data)
                experiment_results[results.experiment_id] = transitions
                all_transitions.extend(transitions)
            
            # Aggregate analysis
            analysis_results = {
                'experiment_results': experiment_results,
                'aggregated_transitions': self._aggregate_transitions(all_transitions),
                'transition_statistics': self._calculate_transition_statistics(all_transitions)
            }
            
            # Create visualization
            plot_file = self._visualize_transition_frequencies(analysis_results)
            if plot_file:
                analysis_results['visualization_file'] = plot_file
            
            self.logger.info(f"Analyzed transition frequencies for {len(experiment_dirs)} experiments")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Failed to analyze transition frequencies: {e}")
            return {}
    
    def _calculate_location_transitions(self, movement_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Calculate location transitions for a single experiment.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            List of transition dictionaries
        """
        transitions = []
        
        for agent_id in movement_data['agent_id'].unique():
            agent_moves = movement_data[movement_data['agent_id'] == agent_id].sort_values('day')
            
            if len(agent_moves) > 1:
                for i in range(len(agent_moves) - 1):
                    from_location = agent_moves.iloc[i]['location']
                    to_location = agent_moves.iloc[i + 1]['location']
                    day = agent_moves.iloc[i + 1]['day']
                    
                    if from_location != to_location:  # Only count actual moves
                        transitions.append({
                            'agent_id': agent_id,
                            'from_location': from_location,
                            'to_location': to_location,
                            'day': day,
                            'transition': f"{from_location} -> {to_location}"
                        })
        
        return transitions
    
    def _aggregate_transitions(self, all_transitions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Aggregate transition counts across all experiments.
        
        Args:
            all_transitions: List of all transition dictionaries
            
        Returns:
            Dictionary mapping transitions to counts
        """
        transition_counts = defaultdict(int)
        
        for transition in all_transitions:
            transition_counts[transition['transition']] += 1
        
        return dict(transition_counts)
    
    def _calculate_transition_statistics(self, all_transitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistical measures for transitions.
        
        Args:
            all_transitions: List of all transition dictionaries
            
        Returns:
            Dictionary containing transition statistics
        """
        if not all_transitions:
            return {}
        
        transitions_df = pd.DataFrame(all_transitions)
        
        stats = {
            'total_transitions': len(all_transitions),
            'unique_transitions': transitions_df['transition'].nunique(),
            'most_common_transitions': transitions_df['transition'].value_counts().head(10).to_dict(),
            'transitions_per_agent': transitions_df.groupby('agent_id').size().describe().to_dict(),
            'temporal_distribution': transitions_df['day'].describe().to_dict()
        }
        
        return stats
    
    def _visualize_transition_frequencies(self, analysis_results: Dict[str, Any]) -> Optional[str]:
        """
        Create visualization of transition frequencies.
        
        Args:
            analysis_results: Dictionary containing transition analysis results
            
        Returns:
            Path to generated visualization file
        """
        try:
            aggregated_transitions = analysis_results['aggregated_transitions']
            
            if not aggregated_transitions:
                return None
            
            # Get top transitions for visualization
            sorted_transitions = sorted(aggregated_transitions.items(), key=lambda x: x[1], reverse=True)
            top_transitions = sorted_transitions[:20]  # Top 20 transitions
            
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Location Transition Frequency Analysis', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Plot 1: Top transitions bar chart
            ax1 = axes[0, 0]
            transitions, counts = zip(*top_transitions)
            y_pos = np.arange(len(transitions))
            
            bars = ax1.barh(y_pos, counts, alpha=self.plot_config.alpha)
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels([t.replace(' -> ', '\n→\n') for t in transitions], fontsize=8)
            ax1.set_xlabel('Frequency')
            ax1.set_title('Top Location Transitions')
            ax1.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for i, (bar, count) in enumerate(zip(bars, counts)):
                ax1.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height()/2, 
                        str(count), ha='left', va='center', fontsize=8)
            
            # Plot 2: Transition frequency distribution
            ax2 = axes[0, 1]
            frequency_counts = list(aggregated_transitions.values())
            ax2.hist(frequency_counts, bins=min(20, len(set(frequency_counts))), 
                    alpha=self.plot_config.alpha, edgecolor='black')
            ax2.set_xlabel('Transition Frequency')
            ax2.set_ylabel('Number of Transition Types')
            ax2.set_title('Distribution of Transition Frequencies')
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Network graph of transitions (top transitions only)
            ax3 = axes[1, 0]
            
            # Create network graph
            G = nx.DiGraph()
            for transition, count in top_transitions[:10]:  # Top 10 for clarity
                from_loc, to_loc = transition.split(' -> ')
                G.add_edge(from_loc, to_loc, weight=count)
            
            if G.nodes():
                pos = nx.spring_layout(G, seed=42)
                
                # Draw edges with thickness proportional to frequency
                edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
                max_weight = max(edge_weights) if edge_weights else 1
                edge_widths = [w / max_weight * 5 for w in edge_weights]
                
                nx.draw_networkx_edges(G, pos, ax=ax3, width=edge_widths, 
                                     alpha=0.6, edge_color='gray', arrows=True, arrowsize=20)
                nx.draw_networkx_nodes(G, pos, ax=ax3, node_color='lightblue', 
                                     node_size=1000, alpha=0.8)
                nx.draw_networkx_labels(G, pos, ax=ax3, font_size=8)
                
                ax3.set_title('Top Transition Network')
                ax3.axis('off')
            
            # Plot 4: Temporal transition patterns
            ax4 = axes[1, 1]
            
            if 'temporal_distribution' in analysis_results['transition_statistics']:
                temporal_stats = analysis_results['transition_statistics']['temporal_distribution']
                
                # Create a simple temporal visualization
                all_transitions = []
                for exp_results in analysis_results['experiment_results'].values():
                    all_transitions.extend(exp_results)
                
                if all_transitions:
                    transitions_df = pd.DataFrame(all_transitions)
                    daily_transitions = transitions_df.groupby('day').size()
                    
                    ax4.plot(daily_transitions.index, daily_transitions.values, 
                            linewidth=self.plot_config.line_width, alpha=self.plot_config.alpha)
                    ax4.set_xlabel('Day')
                    ax4.set_ylabel('Number of Transitions')
                    ax4.set_title('Temporal Pattern of Transitions')
                    ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"transition_frequency_analysis.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created transition frequency visualization: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create transition frequency visualization: {e}")
            return None
    
    def identify_spatial_clusters(self, experiment_dirs: List[str], 
                                clustering_method: str = 'dbscan',
                                **clustering_params) -> Dict[str, Any]:
        """
        Identify spatial clustering patterns in agent movements.
        
        Args:
            experiment_dirs: List of experiment directory paths
            clustering_method: Clustering algorithm ('dbscan', 'kmeans', 'hierarchical')
            **clustering_params: Parameters for clustering algorithm
            
        Returns:
            Dictionary containing clustering results
        """
        try:
            clustering_results = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Perform clustering analysis
                clusters = self._perform_spatial_clustering(
                    results.movement_data, clustering_method, **clustering_params
                )
                
                if clusters:
                    clustering_results[results.experiment_id] = clusters
            
            # Create visualization
            if clustering_results:
                plot_file = self._visualize_spatial_clusters(clustering_results)
                if plot_file:
                    clustering_results['visualization_file'] = plot_file
            
            self.logger.info(f"Identified spatial clusters for {len(clustering_results)} experiments")
            return clustering_results
            
        except Exception as e:
            self.logger.error(f"Failed to identify spatial clusters: {e}")
            return {}
    
    def _perform_spatial_clustering(self, movement_data: pd.DataFrame, 
                                  clustering_method: str, **params) -> Optional[Dict[str, Any]]:
        """
        Perform spatial clustering on movement data.
        
        Args:
            movement_data: DataFrame with movement data
            clustering_method: Clustering algorithm name
            **params: Clustering parameters
            
        Returns:
            Dictionary containing clustering results
        """
        try:
            # Create agent trajectory features
            agent_features = []
            agent_ids = []
            
            for agent_id in movement_data['agent_id'].unique():
                agent_moves = movement_data[movement_data['agent_id'] == agent_id]
                
                # Calculate trajectory features
                unique_locations = agent_moves['location'].nunique()
                total_moves = len(agent_moves)
                movement_span = agent_moves['day'].max() - agent_moves['day'].min() if len(agent_moves) > 1 else 0
                
                # Location frequency features
                location_counts = agent_moves['location'].value_counts()
                most_visited = location_counts.iloc[0] if not location_counts.empty else 0
                location_diversity = len(location_counts)
                
                features = [unique_locations, total_moves, movement_span, most_visited, location_diversity]
                agent_features.append(features)
                agent_ids.append(agent_id)
            
            if not agent_features:
                return None
            
            # Convert to numpy array
            X = np.array(agent_features)
            
            # Normalize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform clustering
            if clustering_method == 'dbscan':
                eps = params.get('eps', 0.5)
                min_samples = params.get('min_samples', 5)
                clusterer = DBSCAN(eps=eps, min_samples=min_samples)
            elif clustering_method == 'kmeans':
                n_clusters = params.get('n_clusters', 3)
                clusterer = KMeans(n_clusters=n_clusters, random_state=42)
            else:
                self.logger.warning(f"Unknown clustering method: {clustering_method}")
                return None
            
            cluster_labels = clusterer.fit_predict(X_scaled)
            
            # Organize results
            results = {
                'agent_ids': agent_ids,
                'features': X,
                'scaled_features': X_scaled,
                'cluster_labels': cluster_labels,
                'n_clusters': len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0),
                'clustering_method': clustering_method,
                'parameters': params,
                'feature_names': ['unique_locations', 'total_moves', 'movement_span', 
                                'most_visited', 'location_diversity']
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to perform spatial clustering: {e}")
            return None
    
    def _visualize_spatial_clusters(self, clustering_results: Dict[str, Any]) -> Optional[str]:
        """
        Create visualization of spatial clustering results.
        
        Args:
            clustering_results: Dictionary containing clustering results
            
        Returns:
            Path to generated visualization file
        """
        try:
            n_experiments = len([k for k in clustering_results.keys() if k != 'visualization_file'])
            
            if n_experiments == 0:
                return None
            
            # Create subplots
            cols = min(3, n_experiments)
            rows = (n_experiments + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
            if n_experiments == 1:
                axes = [axes]
            elif rows == 1:
                axes = [axes]
            else:
                axes = axes.flatten()
            
            fig.suptitle('Spatial Movement Pattern Clusters', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            plot_idx = 0
            for exp_id, results in clustering_results.items():
                if exp_id == 'visualization_file':
                    continue
                
                if plot_idx >= len(axes):
                    break
                
                ax = axes[plot_idx]
                
                # Plot clusters in feature space (first 2 features)
                X = results['scaled_features']
                labels = results['cluster_labels']
                
                # Use first two features for 2D visualization
                scatter = ax.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', alpha=0.7)
                
                ax.set_xlabel(results['feature_names'][0])
                ax.set_ylabel(results['feature_names'][1])
                ax.set_title(f'{exp_id}\n{results["n_clusters"]} clusters')
                ax.grid(True, alpha=0.3)
                
                # Add colorbar
                plt.colorbar(scatter, ax=ax, label='Cluster')
                
                plot_idx += 1
            
            # Hide unused subplots
            for i in range(plot_idx, len(axes)):
                axes[i].set_visible(False)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"spatial_clusters.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created spatial clustering visualization: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create spatial clustering visualization: {e}")
            return None
    
    def compare_cognitive_mode_spatial_patterns(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Compare spatial patterns between different cognitive modes.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary containing cognitive mode comparison results
        """
        try:
            comparison_results = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if (results.movement_data is None or results.movement_data.empty or
                    results.cognitive_states is None or results.cognitive_states.empty):
                    continue
                
                # Analyze patterns by cognitive mode
                mode_patterns = self._analyze_patterns_by_cognitive_mode(
                    results.movement_data, results.cognitive_states
                )
                
                if mode_patterns:
                    comparison_results[results.experiment_id] = mode_patterns
            
            # Create comparison visualization
            if comparison_results:
                plot_file = self._visualize_cognitive_mode_comparison(comparison_results)
                if plot_file:
                    comparison_results['visualization_file'] = plot_file
            
            self.logger.info(f"Compared cognitive mode patterns for {len(comparison_results)} experiments")
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"Failed to compare cognitive mode spatial patterns: {e}")
            return {}
    
    def _analyze_patterns_by_cognitive_mode(self, movement_data: pd.DataFrame, 
                                          cognitive_states: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze spatial patterns separately for each cognitive mode.
        
        Args:
            movement_data: DataFrame with movement data
            cognitive_states: DataFrame with cognitive states data
            
        Returns:
            Dictionary containing pattern analysis by cognitive mode
        """
        try:
            # Merge movement data with cognitive states
            merged_data = movement_data.merge(
                cognitive_states, on=['agent_id', 'day'], how='left'
            )
            
            mode_patterns = {}
            
            for cognitive_mode in merged_data['cognitive_state'].dropna().unique():
                mode_data = merged_data[merged_data['cognitive_state'] == cognitive_mode]
                
                if mode_data.empty:
                    continue
                
                # Calculate basic movement statistics for this mode
                mode_stats = {
                    'total_movements': len(mode_data),
                    'unique_agents': mode_data['agent_id'].nunique(),
                    'unique_locations': mode_data['location'].nunique(),
                    'time_span': mode_data['day'].max() - mode_data['day'].min() if len(mode_data) > 1 else 0
                }
                
                # Location distribution analysis
                location_counts = mode_data['location'].value_counts()
                mode_stats['location_distribution'] = {
                    'most_popular_location': location_counts.index[0] if not location_counts.empty else None,
                    'location_concentration': location_counts.iloc[0] / len(mode_data) if not location_counts.empty else 0,
                    'location_diversity': len(location_counts),
                    'location_gini': self._calculate_gini_coefficient(location_counts.values)
                }
                
                # Calculate transitions for this mode
                       
                if mode_data.empty:
                    continue
                
                # Calculate spatial statistics for this mode
                patterns = {
                    'total_movements': len(mode_data),
                    'unique_agents': mode_data['agent_id'].nunique(),
                    'unique_locations': mode_data['location'].nunique(),
                    'location_distribution': mode_data['location'].value_counts().to_dict(),
                    'movement_frequency': mode_data.groupby('agent_id').size().describe().to_dict(),
                    'temporal_distribution': mode_data['day'].describe().to_dict()
                }
                
                # Calculate transitions for this mode
                transitions = self._calculate_location_transitions(mode_data)
                patterns['transitions'] = {
                    'total_transitions': len(transitions),
                    'unique_transitions': len(set(t['transition'] for t in transitions)),
                    'top_transitions': pd.DataFrame(transitions)['transition'].value_counts().head(5).to_dict() if transitions else {}
                }
                
                mode_patterns[cognitive_mode] = patterns
            
            return mode_patterns
            
        except Exception as e:
            self.logger.error(f"Failed to analyze patterns by cognitive mode: {e}")
            return {}
    
    def _visualize_cognitive_mode_comparison(self, comparison_results: Dict[str, Any]) -> Optional[str]:
        """
        Create visualization comparing cognitive mode spatial patterns.
        
        Args:
            comparison_results: Dictionary containing comparison results
            
        Returns:
            Path to generated visualization file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Cognitive Mode Spatial Pattern Comparison', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Aggregate data across experiments
            all_mode_data = defaultdict(lambda: defaultdict(list))
            
            for exp_id, exp_results in comparison_results.items():
                if exp_id == 'visualization_file':
                    continue
                
                for mode, patterns in exp_results.items():
                    all_mode_data[mode]['total_movements'].append(patterns['total_movements'])
                    all_mode_data[mode]['unique_locations'].append(patterns['unique_locations'])
                    all_mode_data[mode]['movement_frequency_mean'].append(patterns['movement_frequency']['mean'])
                    all_mode_data[mode]['total_transitions'].append(patterns['transitions']['total_transitions'])
            
            # Plot 1: Total movements by cognitive mode
            ax1 = axes[0, 0]
            modes = list(all_mode_data.keys())
            movement_means = [np.mean(all_mode_data[mode]['total_movements']) for mode in modes]
            movement_stds = [np.std(all_mode_data[mode]['total_movements']) for mode in modes]
            
            bars = ax1.bar(modes, movement_means, yerr=movement_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax1.set_ylabel('Total Movements')
            ax1.set_title('Average Total Movements by Cognitive Mode')
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Unique locations by cognitive mode
            ax2 = axes[0, 1]
            location_means = [np.mean(all_mode_data[mode]['unique_locations']) for mode in modes]
            location_stds = [np.std(all_mode_data[mode]['unique_locations']) for mode in modes]
            
            bars = ax2.bar(modes, location_means, yerr=location_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax2.set_ylabel('Unique Locations Visited')
            ax2.set_title('Average Unique Locations by Cognitive Mode')
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Movement frequency by cognitive mode
            ax3 = axes[1, 0]
            freq_means = [np.mean(all_mode_data[mode]['movement_frequency_mean']) for mode in modes]
            freq_stds = [np.std(all_mode_data[mode]['movement_frequency_mean']) for mode in modes]
            
            bars = ax3.bar(modes, freq_means, yerr=freq_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax3.set_ylabel('Average Movements per Agent')
            ax3.set_title('Movement Frequency by Cognitive Mode')
            ax3.grid(True, alpha=0.3)
            
            # Plot 4: Transitions by cognitive mode
            ax4 = axes[1, 1]
            transition_means = [np.mean(all_mode_data[mode]['total_transitions']) for mode in modes]
            transition_stds = [np.std(all_mode_data[mode]['total_transitions']) for mode in modes]
            
            bars = ax4.bar(modes, transition_means, yerr=transition_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax4.set_ylabel('Total Transitions')
            ax4.set_title('Location Transitions by Cognitive Mode')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"cognitive_mode_spatial_comparison.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created cognitive mode comparison visualization: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create cognitive mode comparison visualization: {e}")
            return None
    
    def calculate_spatial_statistics(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Calculate comprehensive spatial statistics for movement pattern quantification.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary containing spatial statistics
        """
        try:
            spatial_stats = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Calculate comprehensive spatial statistics
                stats = self._calculate_comprehensive_spatial_stats(results.movement_data)
                
                if stats:
                    spatial_stats[results.experiment_id] = stats
            
            # Calculate aggregate statistics
            if spatial_stats:
                spatial_stats['aggregate_statistics'] = self._calculate_aggregate_spatial_stats(spatial_stats)
            
            self.logger.info(f"Calculated spatial statistics for {len(spatial_stats)} experiments")
            return spatial_stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate spatial statistics: {e}")
            return {}
    
    def _calculate_comprehensive_spatial_stats(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive spatial statistics for a single experiment.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary containing spatial statistics
        """
        try:
            stats = {}
            
            # Basic movement statistics
            stats['total_movements'] = len(movement_data)
            stats['unique_agents'] = movement_data['agent_id'].nunique()
            stats['unique_locations'] = movement_data['location'].nunique()
            stats['time_span'] = movement_data['day'].max() - movement_data['day'].min()
            
            # Location popularity statistics
            location_counts = movement_data['location'].value_counts()
            stats['location_popularity'] = {
                'most_popular': location_counts.index[0] if not location_counts.empty else None,
                'max_visits': location_counts.iloc[0] if not location_counts.empty else 0,
                'location_gini_coefficient': self._calculate_gini_coefficient(location_counts.values)
            }
            
            # Agent movement statistics
            agent_movement_counts = movement_data.groupby('agent_id').size()
            stats['agent_movement_patterns'] = {
                'mean_movements_per_agent': agent_movement_counts.mean(),
                'std_movements_per_agent': agent_movement_counts.std(),
                'max_movements_per_agent': agent_movement_counts.max(),
                'min_movements_per_agent': agent_movement_counts.min()
            }
            
            # Temporal movement patterns
            daily_movements = movement_data.groupby('day').size()
            stats['temporal_patterns'] = {
                'mean_daily_movements': daily_movements.mean(),
                'std_daily_movements': daily_movements.std(),
                'peak_movement_day': daily_movements.idxmax(),
                'peak_movement_count': daily_movements.max()
            }
            
            # Transition statistics
            transitions = self._calculate_location_transitions(movement_data)
            if transitions:
                transition_counts = pd.DataFrame(transitions)['transition'].value_counts()
                stats['transition_patterns'] = {
                    'total_transitions': len(transitions),
                    'unique_transition_types': len(transition_counts),
                    'most_common_transition': transition_counts.index[0] if not transition_counts.empty else None,
                    'transition_diversity': len(transition_counts) / len(transitions) if transitions else 0
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate comprehensive spatial stats: {e}")
            return {}
    
    def _calculate_gini_coefficient(self, values: np.ndarray) -> float:
        """
        Calculate Gini coefficient for measuring inequality in distribution.
        
        Args:
            values: Array of values
            
        Returns:
            Gini coefficient (0 = perfect equality, 1 = perfect inequality)
        """
        if len(values) == 0:
            return 0.0
        
        # Sort values
        sorted_values = np.sort(values)
        n = len(sorted_values)
        
        # Calculate Gini coefficient
        cumsum = np.cumsum(sorted_values)
        gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * cumsum[-1]) - (n + 1) / n
        
        return gini
    
    def _calculate_aggregate_spatial_stats(self, spatial_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate aggregate statistics across all experiments.
        
        Args:
            spatial_stats: Dictionary containing individual experiment statistics
            
        Returns:
            Dictionary containing aggregate statistics
        """
        try:
            # Exclude aggregate_statistics key if it exists
            experiment_stats = {k: v for k, v in spatial_stats.items() if k != 'aggregate_statistics'}
            
            if not experiment_stats:
                return {}
            
            aggregate = {}
            
            # Aggregate basic statistics
            total_movements = [stats['total_movements'] for stats in experiment_stats.values()]
            unique_agents = [stats['unique_agents'] for stats in experiment_stats.values()]
            unique_locations = [stats['unique_locations'] for stats in experiment_stats.values()]
            
            aggregate['movement_statistics'] = {
                'mean_total_movements': np.mean(total_movements),
                'std_total_movements': np.std(total_movements),
                'mean_unique_agents': np.mean(unique_agents),
                'mean_unique_locations': np.mean(unique_locations)
            }
            
            # Aggregate agent movement patterns
            mean_movements = [stats['agent_movement_patterns']['mean_movements_per_agent'] 
                            for stats in experiment_stats.values()]
            aggregate['agent_patterns'] = {
                'overall_mean_movements_per_agent': np.mean(mean_movements),
                'std_mean_movements_per_agent': np.std(mean_movements)
            }
            
            return aggregate
            
        except Exception as e:
            self.logger.error(f"Failed to calculate aggregate spatial stats: {e}")
            return {}


class SpatialPatternAnalyzer:
    """
    Spatial pattern analysis tools for dual-process experiments.
    
    This class provides comprehensive spatial pattern analysis including occupancy heatmaps,
    transition frequency analysis, spatial clustering, and cognitive mode comparisons.
    """
    
    def __init__(self, results_directory: str, output_directory: str = None,
                 plot_config: PlotConfig = None):
        """
        Initialize spatial pattern analyzer.
        
        Args:
            results_directory: Directory containing experiment results
            output_directory: Directory for analysis outputs
            plot_config: Configuration for plot styling
        """
        self.results_directory = Path(results_directory)
        self.output_directory = Path(output_directory) if output_directory else self.results_directory / "spatial_analysis"
        self.plot_config = plot_config or PlotConfig()
        
        # Initialize utilities
        self.logging_utils = LoggingUtils()
        self.validation_utils = ValidationUtils()
        self.file_utils = FileUtils()
        
        # Setup logger
        self.logger = self.logging_utils.get_logger('SpatialPatternAnalyzer')
        
        # Ensure output directory exists
        self.file_utils.ensure_directory(str(self.output_directory))
        
        # Initialize analysis pipeline for data loading
        self.analysis_pipeline = AnalysisPipeline(str(self.results_directory))
        
        self.logger.info(f"SpatialPatternAnalyzer initialized")
        self.logger.info(f"Analysis outputs will be saved to: {self.output_directory}")
    
    def create_location_occupancy_heatmaps(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Create location occupancy heatmaps for movement pattern analysis.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary containing heatmap analysis results
        """
        try:
            heatmap_results = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Create occupancy heatmap
                heatmap_file = self._create_occupancy_heatmap(
                    results.movement_data, results.experiment_id
                )
                
                # Calculate occupancy statistics
                occupancy_stats = self._calculate_occupancy_statistics(results.movement_data)
                
                if heatmap_file and occupancy_stats:
                    heatmap_results[results.experiment_id] = {
                        'heatmap_file': heatmap_file,
                        'occupancy_statistics': occupancy_stats
                    }
            
            self.logger.info(f"Created occupancy heatmaps for {len(heatmap_results)} experiments")
            return heatmap_results
            
        except Exception as e:
            self.logger.error(f"Failed to create location occupancy heatmaps: {e}")
            return {}
    
    def _create_occupancy_heatmap(self, movement_data: pd.DataFrame, experiment_id: str) -> Optional[str]:
        """
        Create occupancy heatmap for a single experiment.
        
        Args:
            movement_data: DataFrame with movement data
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated heatmap file
        """
        try:
            # Create occupancy matrix (location x time)
            occupancy_pivot = movement_data.pivot_table(
                index='location', 
                columns='day', 
                values='agent_id', 
                aggfunc='count', 
                fill_value=0
            )
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(15, 8))
            
            sns.heatmap(
                occupancy_pivot, 
                annot=True, 
                fmt='d', 
                cmap='YlOrRd',
                cbar_kws={'label': 'Number of Agents'},
                ax=ax
            )
            
            ax.set_title(f'Location Occupancy Heatmap - {experiment_id}', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            ax.set_xlabel('Day')
            ax.set_ylabel('Location')
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"occupancy_heatmap_{experiment_id}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created occupancy heatmap: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create occupancy heatmap: {e}")
            return None
    
    def _calculate_occupancy_statistics(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate occupancy statistics from movement data.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary containing occupancy statistics
        """
        try:
            # Calculate basic occupancy metrics
            location_counts = movement_data['location'].value_counts()
            daily_counts = movement_data.groupby('day').size()
            
            stats = {
                'total_observations': len(movement_data),
                'unique_locations': movement_data['location'].nunique(),
                'time_span': movement_data['day'].max() - movement_data['day'].min(),
                'location_popularity': {
                    'most_popular': location_counts.index[0] if not location_counts.empty else None,
                    'max_occupancy': location_counts.iloc[0] if not location_counts.empty else 0,
                    'occupancy_distribution': location_counts.to_dict()
                },
                'temporal_patterns': {
                    'mean_daily_occupancy': daily_counts.mean(),
                    'std_daily_occupancy': daily_counts.std(),
                    'peak_occupancy_day': daily_counts.idxmax(),
                    'peak_occupancy_count': daily_counts.max()
                },
                'occupancy_concentration': self._calculate_gini_coefficient(location_counts.values)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate occupancy statistics: {e}")
            return {}
    
    def analyze_transition_frequencies(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Analyze location transition frequencies across experiments.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary containing transition frequency analysis results
        """
        try:
            transition_results = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Calculate transitions
                transitions = self._calculate_location_transitions(results.movement_data)
                
                if transitions:
                    # Aggregate and analyze transitions
                    transition_counts = self._aggregate_transitions(transitions)
                    transition_stats = self._calculate_transition_statistics(transitions)
                    
                    # Create transition visualization
                    transition_plot = self._create_transition_frequency_plot(
                        transition_counts, results.experiment_id
                    )
                    
                    transition_results[results.experiment_id] = {
                        'transitions': transitions,
                        'transition_counts': transition_counts,
                        'transition_statistics': transition_stats,
                        'visualization_file': transition_plot
                    }
            
            # Create comparative analysis
            if len(transition_results) > 1:
                comparative_plot = self._create_comparative_transition_analysis(transition_results)
                if comparative_plot:
                    transition_results['comparative_analysis'] = comparative_plot
            
            self.logger.info(f"Analyzed transition frequencies for {len(transition_results)} experiments")
            return transition_results
            
        except Exception as e:
            self.logger.error(f"Failed to analyze transition frequencies: {e}")
            return {}
    
    def _calculate_location_transitions(self, movement_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Calculate location transitions from movement data.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            List of transition dictionaries
        """
        try:
            transitions = []
            
            # Group by agent and calculate transitions
            for agent_id in movement_data['agent_id'].unique():
                agent_moves = movement_data[movement_data['agent_id'] == agent_id].sort_values('day')
                
                for i in range(len(agent_moves) - 1):
                    from_location = agent_moves.iloc[i]['location']
                    to_location = agent_moves.iloc[i + 1]['location']
                    from_day = agent_moves.iloc[i]['day']
                    to_day = agent_moves.iloc[i + 1]['day']
                    
                    # Only record actual transitions (different locations)
                    if from_location != to_location:
                        transitions.append({
                            'agent_id': agent_id,
                            'from_location': from_location,
                            'to_location': to_location,
                            'from_day': from_day,
                            'to_day': to_day,
                            'day': to_day,  # Day when transition occurred
                            'transition': f"{from_location} -> {to_location}"
                        })
            
            return transitions
            
        except Exception as e:
            self.logger.error(f"Failed to calculate location transitions: {e}")
            return []
    
    def _aggregate_transitions(self, transitions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Aggregate transition counts.
        
        Args:
            transitions: List of transition dictionaries
            
        Returns:
            Dictionary mapping transition strings to counts
        """
        transition_counts = {}
        
        for transition in transitions:
            transition_str = transition['transition']
            transition_counts[transition_str] = transition_counts.get(transition_str, 0) + 1
        
        return transition_counts
    
    def _calculate_transition_statistics(self, transitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive transition statistics.
        
        Args:
            transitions: List of transition dictionaries
            
        Returns:
            Dictionary containing transition statistics
        """
        try:
            if not transitions:
                return {}
            
            transition_df = pd.DataFrame(transitions)
            
            stats = {
                'total_transitions': len(transitions),
                'unique_transitions': transition_df['transition'].nunique(),
                'unique_agents_with_transitions': transition_df['agent_id'].nunique(),
                'most_common_transitions': transition_df['transition'].value_counts().head(5).to_dict(),
                'transitions_per_agent': {
                    'mean': transition_df.groupby('agent_id').size().mean(),
                    'std': transition_df.groupby('agent_id').size().std(),
                    'max': transition_df.groupby('agent_id').size().max(),
                    'min': transition_df.groupby('agent_id').size().min()
                },
                'temporal_distribution': {
                    'mean_transition_day': transition_df['day'].mean(),
                    'std_transition_day': transition_df['day'].std(),
                    'earliest_transition': transition_df['day'].min(),
                    'latest_transition': transition_df['day'].max()
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate transition statistics: {e}")
            return {}
    
    def _create_transition_frequency_plot(self, transition_counts: Dict[str, int], 
                                        experiment_id: str) -> Optional[str]:
        """
        Create transition frequency visualization.
        
        Args:
            transition_counts: Dictionary mapping transitions to counts
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated plot file
        """
        try:
            if not transition_counts:
                return None
            
            # Sort transitions by frequency
            sorted_transitions = sorted(transition_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Take top 15 transitions for readability
            top_transitions = sorted_transitions[:15]
            
            transitions, counts = zip(*top_transitions)
            
            # Create bar plot
            fig, ax = plt.subplots(figsize=(12, 8))
            
            bars = ax.bar(range(len(transitions)), counts, alpha=self.plot_config.alpha)
            
            ax.set_xlabel('Location Transitions')
            ax.set_ylabel('Frequency')
            ax.set_title(f'Location Transition Frequencies - {experiment_id}', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Set x-axis labels
            ax.set_xticks(range(len(transitions)))
            ax.set_xticklabels(transitions, rotation=45, ha='right')
            
            # Add value labels on bars
            for i, (bar, count) in enumerate(zip(bars, counts)):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                       str(count), ha='center', va='bottom')
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"transition_frequencies_{experiment_id}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created transition frequency plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create transition frequency plot: {e}")
            return None
    
    def _create_comparative_transition_analysis(self, transition_results: Dict[str, Any]) -> Optional[str]:
        """
        Create comparative analysis of transitions across experiments.
        
        Args:
            transition_results: Dictionary containing transition results for multiple experiments
            
        Returns:
            Path to generated comparative plot file
        """
        try:
            # Exclude non-experiment keys
            experiment_results = {k: v for k, v in transition_results.items() 
                                if k not in ['comparative_analysis', 'visualization_file']}
            
            if len(experiment_results) < 2:
                return None
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Comparative Transition Analysis', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Plot 1: Total transitions per experiment
            ax1 = axes[0, 0]
            exp_names = list(experiment_results.keys())
            total_transitions = [results['transition_statistics']['total_transitions'] 
                               for results in experiment_results.values()]
            
            ax1.bar(exp_names, total_transitions, alpha=self.plot_config.alpha)
            ax1.set_ylabel('Total Transitions')
            ax1.set_title('Total Transitions by Experiment')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Unique transitions per experiment
            ax2 = axes[0, 1]
            unique_transitions = [results['transition_statistics']['unique_transitions'] 
                                for results in experiment_results.values()]
            
            ax2.bar(exp_names, unique_transitions, alpha=self.plot_config.alpha)
            ax2.set_ylabel('Unique Transitions')
            ax2.set_title('Unique Transitions by Experiment')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Mean transitions per agent
            ax3 = axes[1, 0]
            mean_per_agent = [results['transition_statistics']['transitions_per_agent']['mean'] 
                            for results in experiment_results.values()]
            
            ax3.bar(exp_names, mean_per_agent, alpha=self.plot_config.alpha)
            ax3.set_ylabel('Mean Transitions per Agent')
            ax3.set_title('Average Transitions per Agent')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3)
            
            # Plot 4: Transition diversity (unique/total ratio)
            ax4 = axes[1, 1]
            diversity_ratios = [results['transition_statistics']['unique_transitions'] / 
                              max(results['transition_statistics']['total_transitions'], 1)
                              for results in experiment_results.values()]
            
            ax4.bar(exp_names, diversity_ratios, alpha=self.plot_config.alpha)
            ax4.set_ylabel('Transition Diversity Ratio')
            ax4.set_title('Transition Diversity (Unique/Total)')
            ax4.tick_params(axis='x', rotation=45)
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"comparative_transition_analysis.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created comparative transition analysis: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create comparative transition analysis: {e}")
            return None
    
    def perform_spatial_clustering_analysis(self, experiment_dirs: List[str],
                                          clustering_method: str = 'dbscan',
                                          **clustering_params) -> Dict[str, Any]:
        """
        Perform spatial clustering analysis for movement pattern identification.
        
        Args:
            experiment_dirs: List of experiment directory paths
            clustering_method: Clustering algorithm ('dbscan', 'kmeans')
            **clustering_params: Parameters for clustering algorithm
            
        Returns:
            Dictionary containing clustering analysis results
        """
        try:
            clustering_results = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Perform clustering analysis
                cluster_results = self._perform_spatial_clustering(
                    results.movement_data, clustering_method, **clustering_params
                )
                
                if cluster_results:
                    clustering_results[results.experiment_id] = cluster_results
            
            # Create clustering visualization
            if clustering_results:
                visualization_file = self._visualize_spatial_clusters(clustering_results)
                if visualization_file:
                    clustering_results['visualization_file'] = visualization_file
            
            self.logger.info(f"Performed spatial clustering for {len(clustering_results)} experiments")
            return clustering_results
            
        except Exception as e:
            self.logger.error(f"Failed to perform spatial clustering analysis: {e}")
            return {}
    
    def _perform_spatial_clustering(self, movement_data: pd.DataFrame, 
                                  clustering_method: str = 'dbscan',
                                  **params) -> Optional[Dict[str, Any]]:
        """
        Perform spatial clustering on agent movement patterns.
        
        Args:
            movement_data: DataFrame with movement data
            clustering_method: Clustering algorithm to use
            **params: Clustering parameters
            
        Returns:
            Dictionary containing clustering results
        """
        try:
            # Extract features for each agent
            agent_features = []
            agent_ids = []
            
            for agent_id in movement_data['agent_id'].unique():
                agent_moves = movement_data[movement_data['agent_id'] == agent_id]
                
                # Calculate trajectory features
                unique_locations = agent_moves['location'].nunique()
                total_moves = len(agent_moves)
                movement_span = agent_moves['day'].max() - agent_moves['day'].min() if len(agent_moves) > 1 else 0
                
                # Location frequency features
                location_counts = agent_moves['location'].value_counts()
                most_visited = location_counts.iloc[0] if not location_counts.empty else 0
                location_diversity = len(location_counts)
                
                features = [unique_locations, total_moves, movement_span, most_visited, location_diversity]
                agent_features.append(features)
                agent_ids.append(agent_id)
            
            if not agent_features:
                return None
            
            # Convert to numpy array
            X = np.array(agent_features)
            
            # Normalize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform clustering
            if clustering_method == 'dbscan':
                eps = params.get('eps', 0.5)
                min_samples = params.get('min_samples', 5)
                clusterer = DBSCAN(eps=eps, min_samples=min_samples)
            elif clustering_method == 'kmeans':
                n_clusters = params.get('n_clusters', 3)
                clusterer = KMeans(n_clusters=n_clusters, random_state=42)
            else:
                self.logger.warning(f"Unknown clustering method: {clustering_method}")
                return None
            
            cluster_labels = clusterer.fit_predict(X_scaled)
            
            # Organize results
            results = {
                'agent_ids': agent_ids,
                'features': X,
                'scaled_features': X_scaled,
                'cluster_labels': cluster_labels,
                'n_clusters': len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0),
                'clustering_method': clustering_method,
                'parameters': params,
                'feature_names': ['unique_locations', 'total_moves', 'movement_span', 
                                'most_visited', 'location_diversity']
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to perform spatial clustering: {e}")
            return None
    
    def _visualize_spatial_clusters(self, clustering_results: Dict[str, Any]) -> Optional[str]:
        """
        Create visualization of spatial clustering results.
        
        Args:
            clustering_results: Dictionary containing clustering results
            
        Returns:
            Path to generated visualization file
        """
        try:
            n_experiments = len([k for k in clustering_results.keys() if k != 'visualization_file'])
            
            if n_experiments == 0:
                return None
            
            # Create subplots
            cols = min(3, n_experiments)
            rows = (n_experiments + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
            if n_experiments == 1:
                axes = [axes]
            elif rows == 1:
                axes = [axes]
            else:
                axes = axes.flatten()
            
            fig.suptitle('Spatial Movement Pattern Clusters', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            plot_idx = 0
            for exp_id, results in clustering_results.items():
                if exp_id == 'visualization_file':
                    continue
                
                if plot_idx >= len(axes):
                    break
                
                ax = axes[plot_idx]
                
                # Plot clusters in feature space (first 2 features)
                X = results['scaled_features']
                labels = results['cluster_labels']
                
                # Use first two features for 2D visualization
                scatter = ax.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', alpha=0.7)
                
                ax.set_xlabel(results['feature_names'][0])
                ax.set_ylabel(results['feature_names'][1])
                ax.set_title(f'{exp_id}\n{results["n_clusters"]} clusters')
                ax.grid(True, alpha=0.3)
                
                # Add colorbar
                plt.colorbar(scatter, ax=ax, label='Cluster')
                
                plot_idx += 1
            
            # Hide unused subplots
            for i in range(plot_idx, len(axes)):
                axes[i].set_visible(False)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"spatial_clusters.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created spatial clustering visualization: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create spatial clustering visualization: {e}")
            return None
    
    def compare_cognitive_mode_spatial_patterns(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Compare spatial patterns between different cognitive modes.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary containing cognitive mode comparison results
        """
        try:
            comparison_results = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if (results.movement_data is None or results.movement_data.empty or
                    results.cognitive_states is None or results.cognitive_states.empty):
                    continue
                
                # Analyze patterns by cognitive mode
                mode_patterns = self._analyze_patterns_by_cognitive_mode(
                    results.movement_data, results.cognitive_states
                )
                
                if mode_patterns:
                    comparison_results[results.experiment_id] = mode_patterns
            
            # Create comparison visualization
            if comparison_results:
                plot_file = self._visualize_cognitive_mode_comparison(comparison_results)
                if plot_file:
                    comparison_results['visualization_file'] = plot_file
            
            self.logger.info(f"Compared cognitive mode patterns for {len(comparison_results)} experiments")
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"Failed to compare cognitive mode spatial patterns: {e}")
            return {}
    
    def _analyze_patterns_by_cognitive_mode(self, movement_data: pd.DataFrame, 
                                          cognitive_states: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze spatial patterns separately for each cognitive mode.
        
        Args:
            movement_data: DataFrame with movement data
            cognitive_states: DataFrame with cognitive states data
            
        Returns:
            Dictionary containing pattern analysis by cognitive mode
        """
        try:
            # Merge movement data with cognitive states
            merged_data = movement_data.merge(
                cognitive_states, on=['agent_id', 'day'], how='left'
            )
            
            mode_patterns = {}
            
            for cognitive_mode in merged_data['cognitive_state'].dropna().unique():
                mode_data = merged_data[merged_data['cognitive_state'] == cognitive_mode]
                
                if mode_data.empty:
                    continue
                
                # Calculate spatial statistics for this mode
                patterns = {
                    'total_movements': len(mode_data),
                    'unique_agents': mode_data['agent_id'].nunique(),
                    'unique_locations': mode_data['location'].nunique(),
                    'location_distribution': mode_data['location'].value_counts().to_dict(),
                    'movement_frequency': mode_data.groupby('agent_id').size().describe().to_dict(),
                    'temporal_distribution': mode_data['day'].describe().to_dict()
                }
                
                # Calculate transitions for this mode
                transitions = self._calculate_location_transitions(mode_data)
                patterns['transitions'] = {
                    'total_transitions': len(transitions),
                    'unique_transitions': len(set(t['transition'] for t in transitions)),
                    'top_transitions': pd.DataFrame(transitions)['transition'].value_counts().head(5).to_dict() if transitions else {}
                }
                
                mode_patterns[cognitive_mode] = patterns
            
            return mode_patterns
            
        except Exception as e:
            self.logger.error(f"Failed to analyze patterns by cognitive mode: {e}")
            return {}
    
    def _visualize_cognitive_mode_comparison(self, comparison_results: Dict[str, Any]) -> Optional[str]:
        """
        Create visualization comparing cognitive mode spatial patterns.
        
        Args:
            comparison_results: Dictionary containing comparison results
            
        Returns:
            Path to generated visualization file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Cognitive Mode Spatial Pattern Comparison', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Aggregate data across experiments
            all_mode_data = defaultdict(lambda: defaultdict(list))
            
            for exp_id, exp_results in comparison_results.items():
                if exp_id == 'visualization_file':
                    continue
                
                for mode, patterns in exp_results.items():
                    all_mode_data[mode]['total_movements'].append(patterns['total_movements'])
                    all_mode_data[mode]['unique_locations'].append(patterns['unique_locations'])
                    all_mode_data[mode]['movement_frequency_mean'].append(patterns['movement_frequency']['mean'])
                    all_mode_data[mode]['total_transitions'].append(patterns['transitions']['total_transitions'])
            
            # Plot 1: Total movements by cognitive mode
            ax1 = axes[0, 0]
            modes = list(all_mode_data.keys())
            movement_means = [np.mean(all_mode_data[mode]['total_movements']) for mode in modes]
            movement_stds = [np.std(all_mode_data[mode]['total_movements']) for mode in modes]
            
            bars = ax1.bar(modes, movement_means, yerr=movement_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax1.set_ylabel('Total Movements')
            ax1.set_title('Average Total Movements by Cognitive Mode')
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Unique locations by cognitive mode
            ax2 = axes[0, 1]
            location_means = [np.mean(all_mode_data[mode]['unique_locations']) for mode in modes]
            location_stds = [np.std(all_mode_data[mode]['unique_locations']) for mode in modes]
            
            bars = ax2.bar(modes, location_means, yerr=location_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax2.set_ylabel('Unique Locations Visited')
            ax2.set_title('Average Unique Locations by Cognitive Mode')
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Movement frequency by cognitive mode
            ax3 = axes[1, 0]
            freq_means = [np.mean(all_mode_data[mode]['movement_frequency_mean']) for mode in modes]
            freq_stds = [np.std(all_mode_data[mode]['movement_frequency_mean']) for mode in modes]
            
            bars = ax3.bar(modes, freq_means, yerr=freq_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax3.set_ylabel('Average Movements per Agent')
            ax3.set_title('Movement Frequency by Cognitive Mode')
            ax3.grid(True, alpha=0.3)
            
            # Plot 4: Transitions by cognitive mode
            ax4 = axes[1, 1]
            transition_means = [np.mean(all_mode_data[mode]['total_transitions']) for mode in modes]
            transition_stds = [np.std(all_mode_data[mode]['total_transitions']) for mode in modes]
            
            bars = ax4.bar(modes, transition_means, yerr=transition_stds, 
                          alpha=self.plot_config.alpha, capsize=5)
            ax4.set_ylabel('Total Transitions')
            ax4.set_title('Location Transitions by Cognitive Mode')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"cognitive_mode_spatial_comparison.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created cognitive mode comparison visualization: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create cognitive mode comparison visualization: {e}")
            return None
    
    def calculate_spatial_statistics(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Calculate comprehensive spatial statistics for movement pattern quantification.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary containing spatial statistics
        """
        try:
            spatial_stats = {}
            
            for experiment_dir in experiment_dirs:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Calculate comprehensive spatial statistics
                stats = self._calculate_comprehensive_spatial_stats(results.movement_data)
                
                if stats:
                    spatial_stats[results.experiment_id] = stats
            
            # Calculate aggregate statistics
            if spatial_stats:
                spatial_stats['aggregate_statistics'] = self._calculate_aggregate_spatial_stats(spatial_stats)
            
            self.logger.info(f"Calculated spatial statistics for {len(spatial_stats)} experiments")
            return spatial_stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate spatial statistics: {e}")
            return {}
    
    def _calculate_comprehensive_spatial_stats(self, movement_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive spatial statistics for a single experiment.
        
        Args:
            movement_data: DataFrame with movement data
            
        Returns:
            Dictionary containing spatial statistics
        """
        try:
            stats = {}
            
            # Basic movement statistics
            stats['total_movements'] = len(movement_data)
            stats['unique_agents'] = movement_data['agent_id'].nunique()
            stats['unique_locations'] = movement_data['location'].nunique()
            stats['time_span'] = movement_data['day'].max() - movement_data['day'].min()
            
            # Location popularity statistics
            location_counts = movement_data['location'].value_counts()
            stats['location_popularity'] = {
                'most_popular': location_counts.index[0] if not location_counts.empty else None,
                'max_visits': location_counts.iloc[0] if not location_counts.empty else 0,
                'location_gini_coefficient': self._calculate_gini_coefficient(location_counts.values)
            }
            
            # Agent movement statistics
            agent_movement_counts = movement_data.groupby('agent_id').size()
            stats['agent_movement_patterns'] = {
                'mean_movements_per_agent': agent_movement_counts.mean(),
                'std_movements_per_agent': agent_movement_counts.std(),
                'max_movements_per_agent': agent_movement_counts.max(),
                'min_movements_per_agent': agent_movement_counts.min()
            }
            
            # Temporal movement patterns
            daily_movements = movement_data.groupby('day').size()
            stats['temporal_patterns'] = {
                'mean_daily_movements': daily_movements.mean(),
                'std_daily_movements': daily_movements.std(),
                'peak_movement_day': daily_movements.idxmax(),
                'peak_movement_count': daily_movements.max()
            }
            
            # Transition statistics
            transitions = self._calculate_location_transitions(movement_data)
            if transitions:
                transition_counts = pd.DataFrame(transitions)['transition'].value_counts()
                stats['transition_patterns'] = {
                    'total_transitions': len(transitions),
                    'unique_transition_types': len(transition_counts),
                    'most_common_transition': transition_counts.index[0] if not transition_counts.empty else None,
                    'transition_diversity': len(transition_counts) / len(transitions) if transitions else 0
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate comprehensive spatial stats: {e}")
            return {}
    
    def _calculate_gini_coefficient(self, values: np.ndarray) -> float:
        """
        Calculate Gini coefficient for measuring inequality in distribution.
        
        Args:
            values: Array of values
            
        Returns:
            Gini coefficient (0 = perfect equality, 1 = perfect inequality)
        """
        if len(values) == 0:
            return 0.0
        
        # Sort values
        sorted_values = np.sort(values)
        n = len(sorted_values)
        
        # Calculate Gini coefficient
        cumsum = np.cumsum(sorted_values)
        gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * cumsum[-1]) - (n + 1) / n
        
        return gini
    
    def _calculate_aggregate_spatial_stats(self, spatial_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate aggregate statistics across all experiments.
        
        Args:
            spatial_stats: Dictionary containing individual experiment statistics
            
        Returns:
            Dictionary containing aggregate statistics
        """
        try:
            # Exclude aggregate_statistics key if it exists
            experiment_stats = {k: v for k, v in spatial_stats.items() if k != 'aggregate_statistics'}
            
            if not experiment_stats:
                return {}
            
            aggregate = {}
            
            # Aggregate basic statistics
            total_movements = [stats['total_movements'] for stats in experiment_stats.values()]
            unique_agents = [stats['unique_agents'] for stats in experiment_stats.values()]
            unique_locations = [stats['unique_locations'] for stats in experiment_stats.values()]
            
            aggregate['movement_statistics'] = {
                'mean_total_movements': np.mean(total_movements),
                'std_total_movements': np.std(total_movements),
                'mean_unique_agents': np.mean(unique_agents),
                'mean_unique_locations': np.mean(unique_locations)
            }
            
            # Aggregate agent movement patterns
            mean_movements = [stats['agent_movement_patterns']['mean_movements_per_agent'] 
                            for stats in experiment_stats.values()]
            aggregate['agent_patterns'] = {
                'overall_mean_movements_per_agent': np.mean(mean_movements),
                'std_mean_movements_per_agent': np.std(mean_movements)
            }
            
            return aggregate
            
        except Exception as e:
            self.logger.error(f"Failed to calculate aggregate spatial stats: {e}")
            return {}