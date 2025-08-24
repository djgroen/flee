"""
Comprehensive Unit Tests for Topology Generator System

Tests for all topology generators with connectivity validation,
parameter validation, and output format verification.
"""

import unittest
import tempfile
import shutil
import os
import csv
import math
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

try:
    from .topology_generator import (
        TopologyGenerator, LinearTopologyGenerator, StarTopologyGenerator,
        TreeTopologyGenerator, GridTopologyGenerator
    )
    from .utils import CSVUtils, ValidationUtils
except ImportError:
    from topology_generator import (
        TopologyGenerator, LinearTopologyGenerator, StarTopologyGenerator,
        TreeTopologyGenerator, GridTopologyGenerator
    )
    from utils import CSVUtils, ValidationUtils


class TestTopologyGeneratorBase(unittest.TestCase):
    """Test cases for base TopologyGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        
        # Create a concrete implementation for testing abstract methods
        class ConcreteTopologyGenerator(TopologyGenerator):
            def generate_linear(self, n_nodes, segment_distance, start_pop, pop_decay):
                return ("test_locations.csv", "test_routes.csv")
            def generate_star(self, n_camps, hub_pop, camp_capacity, radius):
                return ("test_locations.csv", "test_routes.csv")
            def generate_tree(self, branching_factor, depth, root_pop):
                return ("test_locations.csv", "test_routes.csv")
            def generate_grid(self, rows, cols, cell_distance, pop_distribution):
                return ("test_locations.csv", "test_routes.csv")
        
        self.generator = ConcreteTopologyGenerator(self.base_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test topology generator initialization."""
        self.assertEqual(self.generator.base_config, self.base_config)
        self.assertIsInstance(self.generator.csv_utils, CSVUtils)
        self.assertIsInstance(self.generator.validation_utils, ValidationUtils)
    
    def test_validate_locations_data_valid(self):
        """Test validation of valid locations data."""
        valid_locations = [
            {
                'name': 'Town_A',
                'lat': 10.0,
                'lon': 20.0,
                'location_type': 'town',
                'pop/cap': 1000
            },
            {
                'name': 'Camp_B',
                'lat': 11.0,
                'lon': 21.0,
                'location_type': 'camp',
                'pop/cap': 5000
            }
        ]
        
        self.assertTrue(self.generator._validate_locations_data(valid_locations))
    
    def test_validate_locations_data_missing_fields(self):
        """Test validation with missing required fields."""
        invalid_locations = [
            {
                'name': 'Town_A',
                'lat': 10.0,
                # Missing 'lon', 'location_type', 'pop/cap'
            }
        ]
        
        self.assertFalse(self.generator._validate_locations_data(invalid_locations))
    
    def test_validate_locations_data_duplicate_names(self):
        """Test validation with duplicate location names."""
        invalid_locations = [
            {
                'name': 'Town_A',
                'lat': 10.0,
                'lon': 20.0,
                'location_type': 'town',
                'pop/cap': 1000
            },
            {
                'name': 'Town_A',  # Duplicate name
                'lat': 11.0,
                'lon': 21.0,
                'location_type': 'camp',
                'pop/cap': 5000
            }
        ]
        
        self.assertFalse(self.generator._validate_locations_data(invalid_locations))
    
    def test_validate_locations_data_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        invalid_locations = [
            {
                'name': 'Town_A',
                'lat': 100.0,  # Invalid latitude (> 90)
                'lon': 20.0,
                'location_type': 'town',
                'pop/cap': 1000
            }
        ]
        
        self.assertFalse(self.generator._validate_locations_data(invalid_locations))
    
    def test_validate_locations_data_invalid_location_type(self):
        """Test validation with invalid location type."""
        invalid_locations = [
            {
                'name': 'Town_A',
                'lat': 10.0,
                'lon': 20.0,
                'location_type': 'invalid_type',
                'pop/cap': 1000
            }
        ]
        
        self.assertFalse(self.generator._validate_locations_data(invalid_locations))
    
    def test_validate_locations_data_negative_population(self):
        """Test validation with negative population."""
        invalid_locations = [
            {
                'name': 'Town_A',
                'lat': 10.0,
                'lon': 20.0,
                'location_type': 'town',
                'pop/cap': -100  # Negative population
            }
        ]
        
        self.assertFalse(self.generator._validate_locations_data(invalid_locations))
    
    def test_validate_routes_data_valid(self):
        """Test validation of valid routes data."""
        valid_routes = [
            {
                'name1': 'Town_A',
                'name2': 'Town_B',
                'distance': 50.0
            },
            {
                'name1': 'Town_B',
                'name2': 'Camp_C',
                'distance': 75.0,
                'forced_redirection': 0
            }
        ]
        
        self.assertTrue(self.generator._validate_routes_data(valid_routes))
    
    def test_validate_routes_data_empty(self):
        """Test validation of empty routes data."""
        self.assertTrue(self.generator._validate_routes_data([]))
    
    def test_validate_routes_data_missing_fields(self):
        """Test validation with missing required fields."""
        invalid_routes = [
            {
                'name1': 'Town_A',
                # Missing 'name2' and 'distance'
            }
        ]
        
        self.assertFalse(self.generator._validate_routes_data(invalid_routes))
    
    def test_validate_routes_data_self_loop(self):
        """Test validation with self-loop routes."""
        invalid_routes = [
            {
                'name1': 'Town_A',
                'name2': 'Town_A',  # Self-loop
                'distance': 50.0
            }
        ]
        
        self.assertFalse(self.generator._validate_routes_data(invalid_routes))
    
    def test_validate_routes_data_negative_distance(self):
        """Test validation with negative distance."""
        invalid_routes = [
            {
                'name1': 'Town_A',
                'name2': 'Town_B',
                'distance': -50.0  # Negative distance
            }
        ]
        
        self.assertFalse(self.generator._validate_routes_data(invalid_routes))
    
    def test_validate_routes_data_invalid_redirection(self):
        """Test validation with invalid forced_redirection value."""
        invalid_routes = [
            {
                'name1': 'Town_A',
                'name2': 'Town_B',
                'distance': 50.0,
                'forced_redirection': 2  # Invalid value (must be 0 or 1)
            }
        ]
        
        self.assertFalse(self.generator._validate_routes_data(invalid_routes))
    
    def test_write_locations_csv(self):
        """Test writing locations to CSV file."""
        locations = [
            {
                'name': 'Town_A',
                'lat': 10.0,
                'lon': 20.0,
                'location_type': 'town',
                'pop/cap': 1000
            }
        ]
        
        filepath = os.path.join(self.temp_dir, 'test_locations.csv')
        self.generator._write_locations_csv(locations, filepath)
        
        # Verify file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Verify content
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertIn('Town_A', content)
            self.assertIn('10.0', content)
            self.assertIn('20.0', content)
    
    def test_write_routes_csv(self):
        """Test writing routes to CSV file."""
        routes = [
            {
                'name1': 'Town_A',
                'name2': 'Town_B',
                'distance': 50.0
            }
        ]
        
        filepath = os.path.join(self.temp_dir, 'test_routes.csv')
        self.generator._write_routes_csv(routes, filepath)
        
        # Verify file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Verify content
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertIn('Town_A', content)
            self.assertIn('Town_B', content)
            self.assertIn('50.0', content)
    
    def test_validate_topology_parameters_basic(self):
        """Test basic parameter validation."""
        # Valid parameters
        self.assertTrue(self.generator.validate_topology_parameters(
            n_nodes=5, distance=50.0, population=1000
        ))
        
        # Invalid parameters (negative values)
        self.assertFalse(self.generator.validate_topology_parameters(
            n_nodes=-1, distance=50.0, population=1000
        ))


class TestLinearTopologyGenerator(unittest.TestCase):
    """Test cases for LinearTopologyGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        self.generator = LinearTopologyGenerator(self.base_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_linear_basic(self):
        """Test basic linear topology generation."""
        locations_file, routes_file = self.generator.generate_linear(
            n_nodes=5,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        # Verify files were created
        self.assertTrue(os.path.exists(locations_file))
        self.assertTrue(os.path.exists(routes_file))
        
        # Verify locations content
        locations = self._read_locations_csv(locations_file)
        self.assertEqual(len(locations), 5)
        
        # Check origin location
        origin = next(loc for loc in locations if loc['name'] == 'Origin')
        self.assertEqual(origin['location_type'], 'conflict_zone')
        self.assertEqual(int(origin['pop/cap']), 1000)
        
        # Check final location is a camp
        final_location = locations[-1]
        self.assertEqual(final_location['location_type'], 'camp')
        
        # Verify routes content
        routes = self._read_routes_csv(routes_file)
        self.assertEqual(len(routes), 4)  # n_nodes - 1 routes
        
        # Check route connectivity
        for i, route in enumerate(routes):
            expected_name1 = 'Origin' if i == 0 else f'Town_{i}'
            expected_name2 = f'Town_{i+1}' if i < len(routes)-1 else f'Camp_{i+1}'
            
            self.assertEqual(route['name1'], expected_name1)
            self.assertEqual(route['name2'], expected_name2)
            self.assertEqual(float(route['distance']), 50.0)
    
    def test_generate_linear_population_decay(self):
        """Test population decay in linear topology."""
        locations_file, _ = self.generator.generate_linear(
            n_nodes=4,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.5
        )
        
        locations = self._read_locations_csv(locations_file)
        
        # Check population decay pattern
        origin_pop = int(locations[0]['pop/cap'])
        town1_pop = int(locations[1]['pop/cap'])
        town2_pop = int(locations[2]['pop/cap'])
        
        self.assertEqual(origin_pop, 1000)
        self.assertEqual(town1_pop, int(1000 * 0.5))
        self.assertEqual(town2_pop, int(1000 * 0.25))
    
    def test_generate_linear_minimum_nodes(self):
        """Test linear topology with minimum number of nodes."""
        locations_file, routes_file = self.generator.generate_linear(
            n_nodes=2,
            segment_distance=50.0,
            start_pop=1000,
            pop_decay=0.8
        )
        
        locations = self._read_locations_csv(locations_file)
        routes = self._read_routes_csv(routes_file)
        
        self.assertEqual(len(locations), 2)
        self.assertEqual(len(routes), 1)
        
        # Check that we have origin and camp
        location_types = [loc['location_type'] for loc in locations]
        self.assertIn('conflict_zone', location_types)
        self.assertIn('camp', location_types)
    
    def test_generate_linear_invalid_parameters(self):
        """Test linear topology with invalid parameters."""
        # Too few nodes
        with self.assertRaises(ValueError):
            self.generator.generate_linear(
                n_nodes=1,
                segment_distance=50.0,
                start_pop=1000,
                pop_decay=0.8
            )
        
        # Invalid decay factor
        with self.assertRaises(ValueError):
            self.generator.generate_linear(
                n_nodes=5,
                segment_distance=50.0,
                start_pop=1000,
                pop_decay=1.5  # > 1.0
            )
        
        # Negative parameters
        with self.assertRaises(ValueError):
            self.generator.generate_linear(
                n_nodes=5,
                segment_distance=-50.0,  # Negative distance
                start_pop=1000,
                pop_decay=0.8
            )
    
    def test_generate_linear_coordinate_calculation(self):
        """Test coordinate calculation in linear topology."""
        locations_file, _ = self.generator.generate_linear(
            n_nodes=3,
            segment_distance=111.0,  # 1 degree in km
            start_pop=1000,
            pop_decay=0.8
        )
        
        locations = self._read_locations_csv(locations_file)
        
        # Check coordinate progression
        self.assertAlmostEqual(float(locations[0]['lon']), 0.0, places=5)
        self.assertAlmostEqual(float(locations[1]['lon']), 1.0, places=5)
        self.assertAlmostEqual(float(locations[2]['lon']), 2.0, places=5)
        
        # All should be on same latitude
        for location in locations:
            self.assertAlmostEqual(float(location['lat']), 0.0, places=5)
    
    def test_generate_linear_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_star(4, 1000, 5000, 100.0)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_tree(3, 2, 1000)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_grid(3, 3, 50.0, 'uniform')
    
    def _read_locations_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read locations CSV file."""
        locations = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                locations.append(row)
        return locations
    
    def _read_routes_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read routes CSV file."""
        routes = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                routes.append(row)
        return routes


class TestStarTopologyGenerator(unittest.TestCase):
    """Test cases for StarTopologyGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        self.generator = StarTopologyGenerator(self.base_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_star_basic(self):
        """Test basic star topology generation."""
        locations_file, routes_file = self.generator.generate_star(
            n_camps=4,
            hub_pop=2000,
            camp_capacity=5000,
            radius=100.0
        )
        
        # Verify files were created
        self.assertTrue(os.path.exists(locations_file))
        self.assertTrue(os.path.exists(routes_file))
        
        # Verify locations content
        locations = self._read_locations_csv(locations_file)
        self.assertEqual(len(locations), 5)  # 1 hub + 4 camps
        
        # Check hub location
        hub = next(loc for loc in locations if loc['name'] == 'Hub')
        self.assertEqual(hub['location_type'], 'conflict_zone')
        self.assertEqual(int(hub['pop/cap']), 2000)
        self.assertEqual(float(hub['lat']), 0.0)
        self.assertEqual(float(hub['lon']), 0.0)
        
        # Check camp locations
        camps = [loc for loc in locations if loc['name'].startswith('Camp_')]
        self.assertEqual(len(camps), 4)
        
        for camp in camps:
            self.assertEqual(camp['location_type'], 'camp')
            self.assertEqual(int(camp['pop/cap']), 5000)
        
        # Verify routes content
        routes = self._read_routes_csv(routes_file)
        self.assertEqual(len(routes), 4)  # Hub to each camp
        
        # Check all routes connect hub to camps
        for route in routes:
            self.assertEqual(route['name1'], 'Hub')
            self.assertTrue(route['name2'].startswith('Camp_'))
            self.assertEqual(float(route['distance']), 100.0)
    
    def test_generate_star_single_camp(self):
        """Test star topology with single camp."""
        locations_file, routes_file = self.generator.generate_star(
            n_camps=1,
            hub_pop=1000,
            camp_capacity=3000,
            radius=50.0
        )
        
        locations = self._read_locations_csv(locations_file)
        routes = self._read_routes_csv(routes_file)
        
        self.assertEqual(len(locations), 2)  # Hub + 1 camp
        self.assertEqual(len(routes), 1)    # 1 route
        
        # Check camp naming
        camp = next(loc for loc in locations if loc['name'] != 'Hub')
        self.assertEqual(camp['name'], 'Camp_1')
    
    def test_generate_star_coordinate_calculation(self):
        """Test coordinate calculation in star topology."""
        locations_file, _ = self.generator.generate_star(
            n_camps=4,
            hub_pop=1000,
            camp_capacity=3000,
            radius=111.0  # 1 degree in km
        )
        
        locations = self._read_locations_csv(locations_file)
        camps = [loc for loc in locations if loc['name'].startswith('Camp_')]
        
        # Check that camps are arranged in a circle
        for i, camp in enumerate(camps):
            expected_angle = 2 * math.pi * i / 4
            expected_lat = 1.0 * math.sin(expected_angle)
            expected_lon = 1.0 * math.cos(expected_angle)
            
            self.assertAlmostEqual(float(camp['lat']), expected_lat, places=5)
            self.assertAlmostEqual(float(camp['lon']), expected_lon, places=5)
    
    def test_generate_star_distance_calculation(self):
        """Test distance calculation from hub to camps."""
        locations_file, _ = self.generator.generate_star(
            n_camps=3,
            hub_pop=1000,
            camp_capacity=3000,
            radius=100.0
        )
        
        locations = self._read_locations_csv(locations_file)
        hub = next(loc for loc in locations if loc['name'] == 'Hub')
        camps = [loc for loc in locations if loc['name'].startswith('Camp_')]
        
        # Calculate actual distances from hub to camps
        for camp in camps:
            hub_lat, hub_lon = float(hub['lat']), float(hub['lon'])
            camp_lat, camp_lon = float(camp['lat']), float(camp['lon'])
            
            # Calculate distance using coordinate difference
            distance_deg = math.sqrt((camp_lat - hub_lat)**2 + (camp_lon - hub_lon)**2)
            distance_km = distance_deg * 111.0  # Convert to km
            
            self.assertAlmostEqual(distance_km, 100.0, places=1)
    
    def test_generate_star_invalid_parameters(self):
        """Test star topology with invalid parameters."""
        # Zero camps
        with self.assertRaises(ValueError):
            self.generator.generate_star(
                n_camps=0,
                hub_pop=1000,
                camp_capacity=3000,
                radius=100.0
            )
        
        # Negative parameters
        with self.assertRaises(ValueError):
            self.generator.generate_star(
                n_camps=4,
                hub_pop=-1000,  # Negative population
                camp_capacity=3000,
                radius=100.0
            )
    
    def test_generate_star_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_linear(5, 50.0, 1000, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_tree(3, 2, 1000)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_grid(3, 3, 50.0, 'uniform')
    
    def _read_locations_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read locations CSV file."""
        locations = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                locations.append(row)
        return locations
    
    def _read_routes_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read routes CSV file."""
        routes = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                routes.append(row)
        return routes


class TestTreeTopologyGenerator(unittest.TestCase):
    """Test cases for TreeTopologyGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        self.generator = TreeTopologyGenerator(self.base_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_tree_basic(self):
        """Test basic tree topology generation."""
        locations_file, routes_file = self.generator.generate_tree(
            branching_factor=2,
            depth=2,
            root_pop=1000
        )
        
        # Verify files were created
        self.assertTrue(os.path.exists(locations_file))
        self.assertTrue(os.path.exists(routes_file))
        
        # Verify locations content
        locations = self._read_locations_csv(locations_file)
        expected_nodes = 1 + 2 + 4  # Root + level 1 + level 2
        self.assertEqual(len(locations), expected_nodes)
        
        # Check root location
        root = next(loc for loc in locations if loc['name'] == 'Root')
        self.assertEqual(root['location_type'], 'conflict_zone')
        self.assertEqual(int(root['pop/cap']), 1000)
        
        # Check leaf locations are camps
        camps = [loc for loc in locations if loc['location_type'] == 'camp']
        self.assertEqual(len(camps), 4)  # 2^2 leaf nodes
        
        # Verify routes content
        routes = self._read_routes_csv(routes_file)
        expected_routes = 2 + 4  # Level 0->1 + Level 1->2
        self.assertEqual(len(routes), expected_routes)
    
    def test_generate_tree_single_level(self):
        """Test tree topology with single level (root only)."""
        locations_file, routes_file = self.generator.generate_tree(
            branching_factor=3,
            depth=1,
            root_pop=1000
        )
        
        locations = self._read_locations_csv(locations_file)
        routes = self._read_routes_csv(routes_file)
        
        expected_nodes = 1 + 3  # Root + 3 children
        self.assertEqual(len(locations), expected_nodes)
        self.assertEqual(len(routes), 3)  # Root to each child
        
        # All children should be camps (leaf nodes)
        camps = [loc for loc in locations if loc['location_type'] == 'camp']
        self.assertEqual(len(camps), 3)
    
    def test_generate_tree_population_distribution(self):
        """Test population distribution in tree topology."""
        locations_file, _ = self.generator.generate_tree(
            branching_factor=2,
            depth=2,
            root_pop=1000
        )
        
        locations = self._read_locations_csv(locations_file)
        
        # Check population decay by level
        root = next(loc for loc in locations if loc['name'] == 'Root')
        level1_towns = [loc for loc in locations if loc['name'].startswith('Town_1_')]
        level2_camps = [loc for loc in locations if loc['name'].startswith('Camp_2_')]
        
        root_pop = int(root['pop/cap'])
        self.assertEqual(root_pop, 1000)
        
        # Level 1 should have reduced population
        for town in level1_towns:
            town_pop = int(town['pop/cap'])
            expected_pop = int(1000 * (0.8 ** 1))
            self.assertEqual(town_pop, expected_pop)
        
        # Level 2 (camps) should have higher capacity
        for camp in level2_camps:
            camp_pop = int(camp['pop/cap'])
            expected_pop = int(1000 * 0.5 * (0.8 ** 2) * 3)
            self.assertEqual(camp_pop, expected_pop)
    
    def test_generate_tree_connectivity(self):
        """Test tree connectivity structure."""
        locations_file, routes_file = self.generator.generate_tree(
            branching_factor=2,
            depth=2,
            root_pop=1000
        )
        
        routes = self._read_routes_csv(routes_file)
        
        # Build adjacency list from routes
        adjacency = {}
        for route in routes:
            name1, name2 = route['name1'], route['name2']
            if name1 not in adjacency:
                adjacency[name1] = []
            adjacency[name1].append(name2)
        
        # Check root has correct number of children
        self.assertEqual(len(adjacency['Root']), 2)
        
        # Check level 1 nodes have correct children
        for child in adjacency['Root']:
            self.assertEqual(len(adjacency.get(child, [])), 2)
    
    def test_generate_tree_coordinate_spacing(self):
        """Test coordinate spacing in tree topology."""
        locations_file, _ = self.generator.generate_tree(
            branching_factor=2,
            depth=2,
            root_pop=1000
        )
        
        locations = self._read_locations_csv(locations_file)
        
        # Check that nodes at same level have different coordinates
        level1_nodes = [loc for loc in locations if loc['name'].startswith('Town_1_')]
        level2_nodes = [loc for loc in locations if loc['name'].startswith('Camp_2_')]
        
        # Level 1 coordinates should be different
        level1_coords = [(float(loc['lat']), float(loc['lon'])) for loc in level1_nodes]
        self.assertEqual(len(set(level1_coords)), len(level1_coords))
        
        # Level 2 coordinates should be different
        level2_coords = [(float(loc['lat']), float(loc['lon'])) for loc in level2_nodes]
        self.assertEqual(len(set(level2_coords)), len(level2_coords))
    
    def test_generate_tree_invalid_parameters(self):
        """Test tree topology with invalid parameters."""
        # Invalid branching factor
        with self.assertRaises(ValueError):
            self.generator.generate_tree(
                branching_factor=1,  # < 2
                depth=2,
                root_pop=1000
            )
        
        # Invalid depth
        with self.assertRaises(ValueError):
            self.generator.generate_tree(
                branching_factor=2,
                depth=0,  # < 1
                root_pop=1000
            )
        
        # Negative parameters
        with self.assertRaises(ValueError):
            self.generator.generate_tree(
                branching_factor=2,
                depth=2,
                root_pop=-1000  # Negative population
            )
    
    def test_generate_tree_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_linear(5, 50.0, 1000, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_star(4, 1000, 5000, 100.0)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_grid(3, 3, 50.0, 'uniform')
    
    def _read_locations_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read locations CSV file."""
        locations = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                locations.append(row)
        return locations
    
    def _read_routes_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read routes CSV file."""
        routes = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                routes.append(row)
        return routes


class TestGridTopologyGenerator(unittest.TestCase):
    """Test cases for GridTopologyGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        self.generator = GridTopologyGenerator(self.base_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_grid_basic(self):
        """Test basic grid topology generation."""
        locations_file, routes_file = self.generator.generate_grid(
            rows=3,
            cols=3,
            cell_distance=50.0,
            pop_distribution='uniform'
        )
        
        # Verify files were created
        self.assertTrue(os.path.exists(locations_file))
        self.assertTrue(os.path.exists(routes_file))
        
        # Verify locations content
        locations = self._read_locations_csv(locations_file)
        self.assertEqual(len(locations), 9)  # 3x3 grid
        
        # Check location naming
        location_names = [loc['name'] for loc in locations]
        expected_names = [f'Grid_{r}_{c}' for r in range(3) for c in range(3)]
        self.assertEqual(set(location_names), set(expected_names))
        
        # Check coordinate calculation
        for r in range(3):
            for c in range(3):
                location = next(loc for loc in locations if loc['name'] == f'Grid_{r}_{c}')
                expected_lat = r * 50.0 / 111.0
                expected_lon = c * 50.0 / 111.0
                
                self.assertAlmostEqual(float(location['lat']), expected_lat, places=5)
                self.assertAlmostEqual(float(location['lon']), expected_lon, places=5)
    
    def test_generate_grid_single_cell(self):
        """Test grid topology with single cell."""
        locations_file, routes_file = self.generator.generate_grid(
            rows=1,
            cols=1,
            cell_distance=50.0,
            pop_distribution='uniform'
        )
        
        locations = self._read_locations_csv(locations_file)
        routes = self._read_routes_csv(routes_file)
        
        self.assertEqual(len(locations), 1)
        self.assertEqual(len(routes), 0)  # No routes in single cell
        
        # Check single location
        location = locations[0]
        self.assertEqual(location['name'], 'Grid_0_0')
        self.assertEqual(float(location['lat']), 0.0)
        self.assertEqual(float(location['lon']), 0.0)
    
    def test_generate_grid_connectivity(self):
        """Test grid connectivity structure."""
        locations_file, routes_file = self.generator.generate_grid(
            rows=2,
            cols=2,
            cell_distance=50.0,
            pop_distribution='uniform'
        )
        
        routes = self._read_routes_csv(routes_file)
        
        # Build adjacency list
        adjacency = {}
        for route in routes:
            name1, name2 = route['name1'], route['name2']
            if name1 not in adjacency:
                adjacency[name1] = []
            if name2 not in adjacency:
                adjacency[name2] = []
            adjacency[name1].append(name2)
            adjacency[name2].append(name1)
        
        # Check corner nodes have 2 neighbors
        corner_nodes = ['Grid_0_0', 'Grid_0_1', 'Grid_1_0', 'Grid_1_1']
        for node in corner_nodes:
            self.assertEqual(len(adjacency[node]), 2)
    
    def test_generate_grid_population_distributions(self):
        """Test different population distribution patterns."""
        # Test uniform distribution
        locations_file, _ = self.generator.generate_grid(
            rows=2,
            cols=2,
            cell_distance=50.0,
            pop_distribution='uniform'
        )
        
        locations = self._read_locations_csv(locations_file)
        populations = [int(loc['pop/cap']) for loc in locations]
        
        # All populations should be the same for uniform distribution
        self.assertEqual(len(set(populations)), 1)
        
        # Test weighted distribution
        locations_file, _ = self.generator.generate_grid(
            rows=3,
            cols=3,
            cell_distance=50.0,
            pop_distribution='weighted'
        )
        
        locations = self._read_locations_csv(locations_file)
        populations = [int(loc['pop/cap']) for loc in locations]
        
        # Should have different populations for weighted distribution
        self.assertGreater(len(set(populations)), 1)
    
    def test_generate_grid_origin_location(self):
        """Test that origin location is properly set."""
        locations_file, _ = self.generator.generate_grid(
            rows=2,
            cols=2,
            cell_distance=50.0,
            pop_distribution='uniform'
        )
        
        locations = self._read_locations_csv(locations_file)
        
        # Origin should be at (0,0)
        origin = next(loc for loc in locations if loc['name'] == 'Grid_0_0')
        self.assertEqual(origin['location_type'], 'conflict_zone')
    
    def test_generate_grid_invalid_parameters(self):
        """Test grid topology with invalid parameters."""
        # Invalid dimensions
        with self.assertRaises(ValueError):
            self.generator.generate_grid(
                rows=0,  # Invalid
                cols=3,
                cell_distance=50.0,
                pop_distribution='uniform'
            )
        
        # Invalid distribution
        with self.assertRaises(ValueError):
            self.generator.generate_grid(
                rows=3,
                cols=3,
                cell_distance=50.0,
                pop_distribution='invalid_distribution'
            )
        
        # Negative parameters
        with self.assertRaises(ValueError):
            self.generator.generate_grid(
                rows=3,
                cols=3,
                cell_distance=-50.0,  # Negative distance
                pop_distribution='uniform'
            )
    
    def test_generate_grid_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_linear(5, 50.0, 1000, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_star(4, 1000, 5000, 100.0)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_tree(3, 2, 1000)
    
    def _read_locations_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read locations CSV file."""
        locations = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                locations.append(row)
        return locations
    
    def _read_routes_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Helper method to read routes CSV file."""
        routes = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                routes.append(row)
        return routes


if __name__ == '__main__':
    unittest.main()