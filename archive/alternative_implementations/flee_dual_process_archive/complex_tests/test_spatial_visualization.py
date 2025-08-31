"""
Test suite for spatial visualization system.

This module tests the spatial visualization capabilities including network layout,
movement flow visualization, temporal animations, and spatial pattern analysis.
"""

import unittest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from flee_dual_process.spatial_visualization import (
        SpatialVisualizationGenerator, SpatialPatternAnalyzer,
        SpatialLayoutConfig, AnimationConfig
    )
    from flee_dual_process.visualization_generator import PlotConfig
    from flee_dual_process.analysis_pipeline import ExperimentResults
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class TestSpatialVisualizationGenerator(unittest.TestCase):
    """Test cases for SpatialVisualizationGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.test_dir) / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Create test experiment directory
        self.experiment_dir = self.results_dir / "test_experiment"
        self.experiment_dir.mkdir(exist_ok=True)
        
        # Create test data files
        self._create_test_data_files()
        
        # Initialize visualization generator
        self.viz_generator = SpatialVisualizationGenerator(
            results_directory=str(self.results_dir),
            backend='matplotlib'
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def _create_test_data_files(self):
        """Create test data files for experiments."""
        # Create locations.csv
        locations_data = {
            'name': ['Location_A', 'Location_B', 'Location_C', 'Location_D'],
            'population': [1000, 500, 2000, 800],
            'capacity': [1500, 600, 2500, 1000],
            'location_type': ['town', 'camp', 'town', 'camp'],
            'x': [0.0, 1.0, 2.0, 1.5],
            'y': [0.0, 1.0, 0.5, 2.0]
        }
        locations_df = pd.DataFrame(locations_data)
        locations_df.to_csv(self.experiment_dir / "locations.csv", index=False)
        
        # Create routes.csv
        routes_data = {
            'name1': ['Location_A', 'Location_A', 'Location_B', 'Location_C'],
            'name2': ['Location_B', 'Location_C', 'Location_D', 'Location_D'],
            'distance': [1.0, 2.0, 1.5, 1.2],
            'forced_redirection': [0, 0, 0, 0]
        }
        routes_df = pd.DataFrame(routes_data)
        routes_df.to_csv(self.experiment_dir / "routes.csv", index=False)
        
        # Create test movement data
        movement_data = []
        for agent_id in range(1, 11):  # 10 agents
            for day in range(1, 21):  # 20 days
                # Simple movement pattern
                if day <= 5:
                    location = 'Location_A'
                elif day <= 10:
                    location = 'Location_B' if agent_id % 2 == 0 else 'Location_C'
                elif day <= 15:
                    location = 'Location_C'
                else:
                    location = 'Location_D'
                
                movement_data.append({
                    'agent_id': agent_id,
                    'day': day,
                    'location': location
                })
        
        movement_df = pd.DataFrame(movement_data)
        movement_df.to_csv(self.experiment_dir / "movement_data.csv", index=False)
        
        # Create test cognitive states data
        cognitive_data = []
        for agent_id in range(1, 11):
            for day in range(1, 21):
                # Alternate between S1 and S2 based on agent_id and day
                cognitive_state = 'S1' if (agent_id + day) % 2 == 0 else 'S2'
                cognitive_data.append({
                    'agent_id': agent_id,
                    'day': day,
                    'cognitive_state': cognitive_state
                })
        
        cognitive_df = pd.DataFrame(cognitive_data)
        cognitive_df.to_csv(self.experiment_dir / "cognitive_states.csv", index=False)
    
    @patch('flee_dual_process.spatial_visualization.AnalysisPipeline')
    def test_initialization(self, mock_pipeline):
        """Test SpatialVisualizationGenerator initialization."""
        # Test default initialization
        viz_gen = SpatialVisualizationGenerator(str(self.results_dir))
        
        self.assertEqual(viz_gen.results_directory, Path(self.results_dir))
        self.assertEqual(viz_gen.backend, 'matplotlib')
        self.assertIsInstance(viz_gen.plot_config, PlotConfig)
        self.assertIsInstance(viz_gen.spatial_config, SpatialLayoutConfig)
        self.assertIsInstance(viz_gen.animation_config, AnimationConfig)
        
        # Test custom configuration
        custom_spatial_config = SpatialLayoutConfig(layout_algorithm='circular')
        custom_animation_config = AnimationConfig(fps=15)
        
        viz_gen_custom = SpatialVisualizationGenerator(
            str(self.results_dir),
            backend='plotly',
            spatial_config=custom_spatial_config,
            animation_config=custom_animation_config
        )
        
        self.assertEqual(viz_gen_custom.spatial_config.layout_algorithm, 'circular')
        self.assertEqual(viz_gen_custom.animation_config.fps, 15)
    
    def test_load_network_topology(self):
        """Test loading network topology from files."""
        network_data = self.viz_generator._load_network_topology(str(self.experiment_dir))
        
        self.assertIsNotNone(network_data)
        self.assertIn('locations', network_data)
        self.assertIn('routes', network_data)
        
        locations_df = network_data['locations']
        routes_df = network_data['routes']
        
        self.assertEqual(len(locations_df), 4)
        self.assertEqual(len(routes_df), 4)
        self.assertIn('name', locations_df.columns)
        self.assertIn('name1', routes_df.columns)
        self.assertIn('name2', routes_df.columns)
    
    def test_create_networkx_graph(self):
        """Test creating NetworkX graph from topology data."""
        network_data = self.viz_generator._load_network_topology(str(self.experiment_dir))
        G = self.viz_generator._create_networkx_graph(network_data)
        
        self.assertEqual(len(G.nodes()), 4)
        self.assertEqual(len(G.edges()), 4)
        
        # Check node attributes
        for node in G.nodes():
            self.assertIn('name', G.nodes[node])
            self.assertIn('population', G.nodes[node])
            self.assertIn('capacity', G.nodes[node])
            self.assertIn('location_type', G.nodes[node])
        
        # Check edge attributes
        for edge in G.edges():
            self.assertIn('distance', G.edges[edge])
    
    def test_generate_network_layout(self):
        """Test network layout generation with different algorithms."""
        network_data = self.viz_generator._load_network_topology(str(self.experiment_dir))
        G = self.viz_generator._create_networkx_graph(network_data)
        
        # Test different layout algorithms
        algorithms = ['spring', 'circular', 'kamada_kawai', 'spectral']
        
        for algorithm in algorithms:
            layout_info = self.viz_generator._generate_network_layout(G, network_data, algorithm)
            
            self.assertIsNotNone(layout_info)
            self.assertIn('graph', layout_info)
            self.assertIn('positions', layout_info)
            self.assertIn('node_sizes', layout_info)
            self.assertIn('edge_widths', layout_info)
            self.assertIn('node_colors', layout_info)
            self.assertEqual(layout_info['algorithm'], algorithm)
            
            # Check that all nodes have positions
            self.assertEqual(len(layout_info['positions']), len(G.nodes()))
    
    def test_create_network_spatial_layout(self):
        """Test creating complete network spatial layout."""
        layout_info = self.viz_generator.create_network_spatial_layout(str(self.experiment_dir))
        
        self.assertIsNotNone(layout_info)
        self.assertIn('graph', layout_info)
        self.assertIn('positions', layout_info)
        self.assertIn('node_sizes', layout_info)
        self.assertIn('edge_widths', layout_info)
        self.assertIn('node_colors', layout_info)
        
        # Test caching
        layout_info_2 = self.viz_generator.create_network_spatial_layout(str(self.experiment_dir))
        self.assertEqual(layout_info, layout_info_2)
    
    @patch('flee_dual_process.spatial_visualization.AnalysisPipeline')
    def test_create_agent_movement_flow_visualization(self, mock_pipeline):
        """Test creating agent movement flow visualization."""
        # Mock experiment results
        mock_results = Mock(spec=ExperimentResults)
        mock_results.experiment_id = "test_experiment"
        mock_results.movement_data = pd.DataFrame({
            'agent_id': [1, 1, 2, 2],
            'day': [1, 2, 1, 2],
            'location': ['Location_A', 'Location_B', 'Location_A', 'Location_C']
        })
        mock_results.cognitive_states = pd.DataFrame({
            'agent_id': [1, 1, 2, 2],
            'day': [1, 2, 1, 2],
            'cognitive_state': ['S1', 'S1', 'S2', 'S2']
        })
        
        mock_pipeline_instance = mock_pipeline.return_value
        mock_pipeline_instance.load_experiment_data.return_value = mock_results
        
        # Mock the layout creation
        with patch.object(self.viz_generator, 'create_network_spatial_layout') as mock_layout:
            mock_layout.return_value = {
                'graph': Mock(),
                'positions': {'Location_A': (0, 0), 'Location_B': (1, 1), 'Location_C': (2, 2)},
                'node_sizes': {'Location_A': 100, 'Location_B': 100, 'Location_C': 100},
                'edge_widths': {},
                'node_colors': {'Location_A': '#FF6B6B', 'Location_B': '#4ECDC4', 'Location_C': '#A4B0BE'}
            }
            
            # Mock matplotlib to avoid actual plotting
            with patch('matplotlib.pyplot.subplots'), \
                 patch('matplotlib.pyplot.savefig'), \
                 patch('matplotlib.pyplot.close'):
                
                result = self.viz_generator.create_agent_movement_flow_visualization(
                    str(self.experiment_dir)
                )
                
                self.assertIsNotNone(result)
                self.assertTrue(result.endswith('.png'))
    
    @patch('flee_dual_process.spatial_visualization.AnalysisPipeline')
    def test_create_temporal_animation(self, mock_pipeline):
        """Test creating temporal animation."""
        # Mock experiment results
        mock_results = Mock(spec=ExperimentResults)
        mock_results.experiment_id = "test_experiment"
        mock_results.movement_data = pd.DataFrame({
            'agent_id': [1, 1, 2, 2],
            'day': [1, 2, 1, 2],
            'location': ['Location_A', 'Location_B', 'Location_A', 'Location_C']
        })
        mock_results.cognitive_states = pd.DataFrame({
            'agent_id': [1, 1, 2, 2],
            'day': [1, 2, 1, 2],
            'cognitive_state': ['S1', 'S1', 'S2', 'S2']
        })
        
        mock_pipeline_instance = mock_pipeline.return_value
        mock_pipeline_instance.load_experiment_data.return_value = mock_results
        
        # Mock the layout creation
        with patch.object(self.viz_generator, 'create_network_spatial_layout') as mock_layout:
            mock_layout.return_value = {
                'graph': Mock(),
                'positions': {'Location_A': (0, 0), 'Location_B': (1, 1), 'Location_C': (2, 2)},
                'node_sizes': {'Location_A': 100, 'Location_B': 100, 'Location_C': 100},
                'edge_widths': {},
                'node_colors': {'Location_A': '#FF6B6B', 'Location_B': '#4ECDC4', 'Location_C': '#A4B0BE'}
            }
            
            # Mock animation components
            with patch('matplotlib.pyplot.subplots'), \
                 patch('matplotlib.animation.FuncAnimation') as mock_anim, \
                 patch('matplotlib.pyplot.close'):
                
                mock_anim_instance = Mock()
                mock_anim_instance.save = Mock()
                mock_anim.return_value = mock_anim_instance
                
                result = self.viz_generator.create_temporal_animation(
                    str(self.experiment_dir), max_frames=5
                )
                
                self.assertIsNotNone(result)
                self.assertTrue(result.endswith('.mp4'))


class TestSpatialPatternAnalyzer(unittest.TestCase):
    """Test cases for SpatialPatternAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.test_dir) / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize pattern analyzer
        self.pattern_analyzer = SpatialPatternAnalyzer(
            results_directory=str(self.results_dir)
        )
        
        # Create test movement data
        self.test_movement_data = pd.DataFrame({
            'agent_id': [1, 1, 1, 2, 2, 2, 3, 3, 3],
            'day': [1, 2, 3, 1, 2, 3, 1, 2, 3],
            'location': ['A', 'B', 'C', 'A', 'A', 'B', 'B', 'C', 'A']
        })
        
        self.test_cognitive_states = pd.DataFrame({
            'agent_id': [1, 1, 1, 2, 2, 2, 3, 3, 3],
            'day': [1, 2, 3, 1, 2, 3, 1, 2, 3],
            'cognitive_state': ['S1', 'S1', 'S2', 'S2', 'S2', 'S1', 'S1', 'S2', 'S2']
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test SpatialPatternAnalyzer initialization."""
        analyzer = SpatialPatternAnalyzer(str(self.results_dir))
        
        self.assertEqual(analyzer.results_directory, Path(self.results_dir))
        self.assertIsInstance(analyzer.plot_config, PlotConfig)
        self.assertTrue(analyzer.output_directory.exists())
    
    def test_create_occupancy_heatmap(self):
        """Test creating location occupancy heatmap."""
        with patch('matplotlib.pyplot.subplots') as mock_subplots, \
             patch('seaborn.heatmap'), \
             patch('matplotlib.pyplot.savefig'), \
             patch('matplotlib.pyplot.close'):
            
            # Mock subplots to return fig, ax tuple
            mock_fig = Mock()
            mock_ax = Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = self.pattern_analyzer._create_occupancy_heatmap(
                self.test_movement_data, "test_experiment"
            )
            
            self.assertIsNotNone(result)
            self.assertTrue(result.endswith('.png'))
    
    def test_calculate_location_transitions(self):
        """Test calculating location transitions."""
        transitions = self.pattern_analyzer._calculate_location_transitions(self.test_movement_data)
        
        self.assertIsInstance(transitions, list)
        self.assertGreater(len(transitions), 0)
        
        # Check transition structure
        for transition in transitions:
            self.assertIn('agent_id', transition)
            self.assertIn('from_location', transition)
            self.assertIn('to_location', transition)
            self.assertIn('day', transition)
            self.assertIn('transition', transition)
    
    def test_aggregate_transitions(self):
        """Test aggregating transition counts."""
        transitions = [
            {'transition': 'A -> B'},
            {'transition': 'A -> B'},
            {'transition': 'B -> C'},
            {'transition': 'A -> B'}
        ]
        
        aggregated = self.pattern_analyzer._aggregate_transitions(transitions)
        
        self.assertEqual(aggregated['A -> B'], 3)
        self.assertEqual(aggregated['B -> C'], 1)
    
    def test_calculate_transition_statistics(self):
        """Test calculating transition statistics."""
        transitions = [
            {'agent_id': 1, 'transition': 'A -> B', 'day': 1},
            {'agent_id': 1, 'transition': 'B -> C', 'day': 2},
            {'agent_id': 2, 'transition': 'A -> B', 'day': 1}
        ]
        
        stats = self.pattern_analyzer._calculate_transition_statistics(transitions)
        
        self.assertIn('total_transitions', stats)
        self.assertIn('unique_transitions', stats)
        self.assertIn('most_common_transitions', stats)
        self.assertIn('transitions_per_agent', stats)
        self.assertIn('temporal_distribution', stats)
        
        self.assertEqual(stats['total_transitions'], 3)
        self.assertEqual(stats['unique_transitions'], 2)
    
    def test_perform_spatial_clustering(self):
        """Test performing spatial clustering."""
        # Mock sklearn components
        with patch('sklearn.preprocessing.StandardScaler') as mock_scaler, \
             patch('sklearn.cluster.DBSCAN') as mock_dbscan:
            
            mock_scaler_instance = Mock()
            mock_scaler_instance.fit_transform.return_value = np.array([[0, 1], [1, 0], [0.5, 0.5]])
            mock_scaler.return_value = mock_scaler_instance
            
            mock_dbscan_instance = Mock()
            mock_dbscan_instance.fit_predict.return_value = np.array([0, 1, 0])
            mock_dbscan.return_value = mock_dbscan_instance
            
            result = self.pattern_analyzer._perform_spatial_clustering(
                self.test_movement_data, 'dbscan', eps=0.5, min_samples=2
            )
            
            self.assertIsNotNone(result)
            self.assertIn('agent_ids', result)
            self.assertIn('features', result)
            self.assertIn('cluster_labels', result)
            self.assertIn('n_clusters', result)
            self.assertIn('clustering_method', result)
    
    def test_analyze_patterns_by_cognitive_mode(self):
        """Test analyzing patterns by cognitive mode."""
        patterns = self.pattern_analyzer._analyze_patterns_by_cognitive_mode(
            self.test_movement_data, self.test_cognitive_states
        )
        
        self.assertIsInstance(patterns, dict)
        self.assertIn('S1', patterns)
        self.assertIn('S2', patterns)
        
        for mode, mode_patterns in patterns.items():
            self.assertIn('total_movements', mode_patterns)
            self.assertIn('unique_agents', mode_patterns)
            self.assertIn('unique_locations', mode_patterns)
            self.assertIn('location_distribution', mode_patterns)
            self.assertIn('transitions', mode_patterns)
    
    def test_calculate_comprehensive_spatial_stats(self):
        """Test calculating comprehensive spatial statistics."""
        stats = self.pattern_analyzer._calculate_comprehensive_spatial_stats(self.test_movement_data)
        
        self.assertIn('total_movements', stats)
        self.assertIn('unique_agents', stats)
        self.assertIn('unique_locations', stats)
        self.assertIn('time_span', stats)
        self.assertIn('location_popularity', stats)
        self.assertIn('agent_movement_patterns', stats)
        self.assertIn('temporal_patterns', stats)
        
        self.assertEqual(stats['total_movements'], 9)
        self.assertEqual(stats['unique_agents'], 3)
        self.assertEqual(stats['unique_locations'], 3)
    
    def test_calculate_gini_coefficient(self):
        """Test Gini coefficient calculation."""
        # Test perfect equality
        equal_values = np.array([1, 1, 1, 1])
        gini_equal = self.pattern_analyzer._calculate_gini_coefficient(equal_values)
        self.assertAlmostEqual(gini_equal, 0.0, places=2)
        
        # Test perfect inequality
        unequal_values = np.array([0, 0, 0, 10])
        gini_unequal = self.pattern_analyzer._calculate_gini_coefficient(unequal_values)
        self.assertGreater(gini_unequal, 0.5)
        
        # Test empty array
        empty_values = np.array([])
        gini_empty = self.pattern_analyzer._calculate_gini_coefficient(empty_values)
        self.assertEqual(gini_empty, 0.0)


class TestSpatialLayoutConfig(unittest.TestCase):
    """Test cases for SpatialLayoutConfig dataclass."""
    
    def test_default_configuration(self):
        """Test default spatial layout configuration."""
        config = SpatialLayoutConfig()
        
        self.assertEqual(config.layout_algorithm, 'spring')
        self.assertEqual(config.node_size_scale, 1000.0)
        self.assertEqual(config.edge_width_scale, 2.0)
        self.assertEqual(config.node_spacing, 1.0)
        self.assertEqual(config.iterations, 50)
        self.assertIsNone(config.k_spring)
        self.assertEqual(config.seed, 42)
    
    def test_custom_configuration(self):
        """Test custom spatial layout configuration."""
        config = SpatialLayoutConfig(
            layout_algorithm='circular',
            node_size_scale=500.0,
            iterations=100,
            k_spring=0.5
        )
        
        self.assertEqual(config.layout_algorithm, 'circular')
        self.assertEqual(config.node_size_scale, 500.0)
        self.assertEqual(config.iterations, 100)
        self.assertEqual(config.k_spring, 0.5)


class TestAnimationConfig(unittest.TestCase):
    """Test cases for AnimationConfig dataclass."""
    
    def test_default_configuration(self):
        """Test default animation configuration."""
        config = AnimationConfig()
        
        self.assertEqual(config.fps, 10)
        self.assertEqual(config.interval, 200)
        self.assertIsNone(config.duration_seconds)
        self.assertEqual(config.save_format, 'mp4')
        self.assertEqual(config.dpi, 100)
        self.assertEqual(config.bitrate, 1800)
    
    def test_custom_configuration(self):
        """Test custom animation configuration."""
        config = AnimationConfig(
            fps=15,
            interval=100,
            duration_seconds=30,
            save_format='gif',
            dpi=150
        )
        
        self.assertEqual(config.fps, 15)
        self.assertEqual(config.interval, 100)
        self.assertEqual(config.duration_seconds, 30)
        self.assertEqual(config.save_format, 'gif')
        self.assertEqual(config.dpi, 150)


if __name__ == '__main__':
    unittest.main()