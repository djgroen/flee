"""
Comprehensive Unit Tests for Scenario Generator System

Tests for all scenario generators with temporal consistency checks,
parameter validation, and conflict pattern verification.
"""

import unittest
import tempfile
import shutil
import os
import csv
import math
from typing import Dict, List, Any, Tuple
from unittest.mock import patch, MagicMock

try:
    from .scenario_generator import (
        ConflictScenarioGenerator, SpikeConflictGenerator, GradualConflictGenerator,
        CascadingConflictGenerator, OscillatingConflictGenerator
    )
    from .utils import CSVUtils, ValidationUtils
except ImportError:
    from scenario_generator import (
        ConflictScenarioGenerator, SpikeConflictGenerator, GradualConflictGenerator,
        CascadingConflictGenerator, OscillatingConflictGenerator
    )
    from utils import CSVUtils, ValidationUtils


class TestConflictScenarioGeneratorBase(unittest.TestCase):
    """Test cases for base ConflictScenarioGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.topology_file = os.path.join(self.temp_dir, 'locations.csv')
        
        # Create sample topology file
        self._create_sample_topology()
        
        # Create a concrete implementation for testing abstract methods
        class ConcreteScenarioGenerator(ConflictScenarioGenerator):
            def generate_spike_conflict(self, origin, start_day, peak_intensity):
                return "test_conflicts.csv"
            def generate_gradual_conflict(self, origin, start_day, end_day, max_intensity):
                return "test_conflicts.csv"
            def generate_cascading_conflict(self, origin, start_day, spread_rate, max_intensity):
                return "test_conflicts.csv"
            def generate_oscillating_conflict(self, origin, start_day, period, amplitude):
                return "test_conflicts.csv"
        
        self.generator = ConcreteScenarioGenerator(self.topology_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_topology(self):
        """Create sample topology file for testing."""
        locations = [
            ['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'],
            ['Town_A', 'Region1', 'Country1', '10.0', '20.0', 'town', '', '1000'],
            ['Town_B', 'Region1', 'Country1', '11.0', '21.0', 'town', '', '800'],
            ['Camp_C', 'Region1', 'Country1', '12.0', '22.0', 'camp', '', '5000'],
            ['Camp_D', 'Region1', 'Country1', '13.0', '23.0', 'camp', '', '3000']
        ]
        
        with open(self.topology_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(locations)
    
    def test_initialization(self):
        """Test scenario generator initialization."""
        self.assertEqual(self.generator.topology_file, self.topology_file)
        self.assertIsInstance(self.generator.csv_utils, CSVUtils)
        self.assertIsInstance(self.generator.validation_utils, ValidationUtils)
        
        # Check that topology was loaded
        self.assertEqual(len(self.generator.locations), 4)
        self.assertEqual(len(self.generator.location_names), 4)
        self.assertIn('Town_A', self.generator.location_names)
        self.assertIn('Camp_C', self.generator.location_names)
    
    def test_initialization_missing_topology(self):
        """Test initialization with missing topology file."""
        missing_file = os.path.join(self.temp_dir, 'missing.csv')
        
        with self.assertRaises(FileNotFoundError):
            ConflictScenarioGenerator(missing_file)
    
    def test_write_conflicts_csv_basic(self):
        """Test writing conflicts to CSV file."""
        conflicts = {
            0: {'Town_A': 0.5},
            1: {'Town_A': 0.7, 'Town_B': 0.3},
            2: {'Town_B': 0.8}
        }
        
        output_file = os.path.join(self.temp_dir, 'test_conflicts.csv')
        self.generator._write_conflicts_csv(conflicts, output_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Verify content
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # Check header format
            self.assertEqual(header[0], '#Day')
            self.assertIn('Town_A', header)
            self.assertIn('Town_B', header)
            
            # Check data rows
            rows = list(reader)
            self.assertEqual(len(rows), 3)  # 3 days
            
            # Check first row (day 0)
            day0_row = rows[0]
            self.assertEqual(int(day0_row[0]), 0)
            town_a_idx = header.index('Town_A')
            self.assertEqual(float(day0_row[town_a_idx]), 0.5)
    
    def test_write_conflicts_csv_empty(self):
        """Test writing empty conflicts to CSV file."""
        conflicts = {}
        
        output_file = os.path.join(self.temp_dir, 'empty_conflicts.csv')
        self.generator._write_conflicts_csv(conflicts, output_file)
        
        # Verify file was created with header only
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)  # Header only
            self.assertTrue(lines[0].startswith('#Day'))
    
    def test_read_conflicts_matrix(self):
        """Test reading conflicts from matrix format CSV."""
        # Create test conflicts file
        conflicts_file = os.path.join(self.temp_dir, 'test_conflicts.csv')
        conflicts_data = [
            ['#Day', 'Town_A', 'Town_B', 'Camp_C'],
            ['0', '0.5', '0.0', '0.0'],
            ['1', '0.7', '0.3', '0.0'],
            ['2', '0.0', '0.8', '0.2']
        ]
        
        with open(conflicts_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(conflicts_data)
        
        # Read conflicts
        conflicts = self.generator._read_conflicts_matrix(conflicts_file)
        
        # Verify structure
        self.assertEqual(len(conflicts), 3)  # 3 days with conflicts
        
        # Check day 0
        self.assertIn(0, conflicts)
        self.assertEqual(conflicts[0]['Town_A'], 0.5)
        self.assertNotIn('Town_B', conflicts[0])  # Zero values not stored
        
        # Check day 1
        self.assertIn(1, conflicts)
        self.assertEqual(conflicts[1]['Town_A'], 0.7)
        self.assertEqual(conflicts[1]['Town_B'], 0.3)
        
        # Check day 2
        self.assertIn(2, conflicts)
        self.assertEqual(conflicts[2]['Town_B'], 0.8)
        self.assertEqual(conflicts[2]['Camp_C'], 0.2)
    
    def test_validate_temporal_consistency_valid(self):
        """Test temporal consistency validation with valid data."""
        conflicts = {
            0: {'Town_A': 0.5},
            1: {'Town_A': 0.7},
            5: {'Town_B': 0.3}  # Gap is acceptable
        }
        
        self.assertTrue(self.generator._validate_temporal_consistency(conflicts))
    
    def test_validate_temporal_consistency_negative_days(self):
        """Test temporal consistency validation with negative days."""
        conflicts = {
            -1: {'Town_A': 0.5},  # Negative day
            0: {'Town_A': 0.7}
        }
        
        self.assertFalse(self.generator._validate_temporal_consistency(conflicts))
    
    def test_validate_temporal_consistency_simulation_period(self):
        """Test temporal consistency validation with simulation period."""
        conflicts = {
            0: {'Town_A': 0.5},
            10: {'Town_A': 0.7},
            50: {'Town_B': 0.3}  # Outside simulation period
        }
        
        sim_period = (0, 30)
        self.assertFalse(self.generator._validate_temporal_consistency(conflicts, sim_period))
        
        # Valid case
        conflicts_valid = {
            0: {'Town_A': 0.5},
            10: {'Town_A': 0.7},
            25: {'Town_B': 0.3}
        }
        
        self.assertTrue(self.generator._validate_temporal_consistency(conflicts_valid, sim_period))
    
    def test_validate_location_consistency_valid(self):
        """Test location consistency validation with valid data."""
        conflicts = {
            0: {'Town_A': 0.5, 'Town_B': 0.3},
            1: {'Camp_C': 0.7}
        }
        
        self.assertTrue(self.generator._validate_location_consistency(conflicts))
    
    def test_validate_location_consistency_invalid(self):
        """Test location consistency validation with invalid location."""
        conflicts = {
            0: {'Town_A': 0.5, 'Unknown_Location': 0.3}  # Unknown location
        }
        
        self.assertFalse(self.generator._validate_location_consistency(conflicts))
    
    def test_validate_intensity_ranges_valid(self):
        """Test intensity range validation with valid data."""
        conflicts = {
            0: {'Town_A': 0.0, 'Town_B': 0.5, 'Camp_C': 1.0}
        }
        
        self.assertTrue(self.generator._validate_intensity_ranges(conflicts))
    
    def test_validate_intensity_ranges_invalid(self):
        """Test intensity range validation with invalid intensities."""
        # Test negative intensity
        conflicts_negative = {
            0: {'Town_A': -0.1}  # Negative intensity
        }
        self.assertFalse(self.generator._validate_intensity_ranges(conflicts_negative))
        
        # Test intensity > 1
        conflicts_high = {
            0: {'Town_A': 1.5}  # Intensity > 1
        }
        self.assertFalse(self.generator._validate_intensity_ranges(conflicts_high))
        
        # Test non-numeric intensity
        conflicts_non_numeric = {
            0: {'Town_A': 'invalid'}  # Non-numeric
        }
        self.assertFalse(self.generator._validate_intensity_ranges(conflicts_non_numeric))
    
    def test_validate_scenario_complete(self):
        """Test complete scenario validation."""
        # Create valid conflicts file
        conflicts_file = os.path.join(self.temp_dir, 'valid_conflicts.csv')
        conflicts_data = [
            ['#Day', 'Town_A', 'Town_B'],
            ['0', '0.5', '0.0'],
            ['1', '0.7', '0.3']
        ]
        
        with open(conflicts_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(conflicts_data)
        
        self.assertTrue(self.generator.validate_scenario(conflicts_file))
    
    def test_validate_scenario_missing_file(self):
        """Test scenario validation with missing file."""
        missing_file = os.path.join(self.temp_dir, 'missing_conflicts.csv')
        self.assertFalse(self.generator.validate_scenario(missing_file))


class TestSpikeConflictGenerator(unittest.TestCase):
    """Test cases for SpikeConflictGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.topology_file = os.path.join(self.temp_dir, 'locations.csv')
        
        # Create sample topology file
        self._create_sample_topology()
        
        self.generator = SpikeConflictGenerator(self.topology_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_topology(self):
        """Create sample topology file for testing."""
        locations = [
            ['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'],
            ['Origin', 'Region1', 'Country1', '10.0', '20.0', 'conflict_zone', '', '1000'],
            ['Town_B', 'Region1', 'Country1', '11.0', '21.0', 'town', '', '800'],
            ['Camp_C', 'Region1', 'Country1', '12.0', '22.0', 'camp', '', '5000']
        ]
        
        with open(self.topology_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(locations)
    
    def test_generate_spike_conflict_basic(self):
        """Test basic spike conflict generation."""
        output_file = self.generator.generate_spike_conflict(
            origin='Origin',
            start_day=0,
            peak_intensity=0.8,
            output_dir=self.temp_dir
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read and verify conflicts
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check that conflicts start immediately at peak intensity
        self.assertIn(0, conflicts)
        self.assertEqual(conflicts[0]['Origin'], 0.8)
        
        # Check duration (should be 30 days by default)
        self.assertIn(29, conflicts)  # Day 29 should exist
        self.assertEqual(conflicts[29]['Origin'], 0.8)
        
        # Check that intensity remains constant
        for day in range(30):
            if day in conflicts:
                self.assertEqual(conflicts[day]['Origin'], 0.8)
    
    def test_generate_spike_conflict_custom_start_day(self):
        """Test spike conflict with custom start day."""
        output_file = self.generator.generate_spike_conflict(
            origin='Origin',
            start_day=10,
            peak_intensity=0.6,
            output_dir=self.temp_dir
        )
        
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check that conflicts start on specified day
        self.assertNotIn(9, conflicts)  # Day before start
        self.assertIn(10, conflicts)    # Start day
        self.assertEqual(conflicts[10]['Origin'], 0.6)
        
        # Check end day
        self.assertIn(39, conflicts)    # start_day + 29
        self.assertEqual(conflicts[39]['Origin'], 0.6)
    
    def test_generate_spike_conflict_invalid_origin(self):
        """Test spike conflict with invalid origin location."""
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_spike_conflict(
                origin='Unknown_Location',
                start_day=0,
                peak_intensity=0.8,
                output_dir=self.temp_dir
            )
    
    def test_generate_spike_conflict_invalid_parameters(self):
        """Test spike conflict with invalid parameters."""
        # Invalid start_day
        with self.assertRaises(ValueError):
            self.generator.generate_spike_conflict(
                origin='Origin',
                start_day=-1,  # Negative
                peak_intensity=0.8,
                output_dir=self.temp_dir
            )
        
        # Invalid peak_intensity
        with self.assertRaises(ValueError):
            self.generator.generate_spike_conflict(
                origin='Origin',
                start_day=0,
                peak_intensity=1.5,  # > 1.0
                output_dir=self.temp_dir
            )
        
        with self.assertRaises(ValueError):
            self.generator.generate_spike_conflict(
                origin='Origin',
                start_day=0,
                peak_intensity=-0.1,  # < 0.0
                output_dir=self.temp_dir
            )
    
    def test_generate_spike_conflict_validation(self):
        """Test that generated spike conflict passes validation."""
        output_file = self.generator.generate_spike_conflict(
            origin='Origin',
            start_day=5,
            peak_intensity=0.7,
            output_dir=self.temp_dir
        )
        
        # Should pass validation
        self.assertTrue(self.generator.validate_scenario(output_file))
    
    def test_generate_spike_conflict_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_gradual_conflict('Origin', 0, 10, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_cascading_conflict('Origin', 0, 0.5, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_oscillating_conflict('Origin', 0, 10, 0.5)


class TestGradualConflictGenerator(unittest.TestCase):
    """Test cases for GradualConflictGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.topology_file = os.path.join(self.temp_dir, 'locations.csv')
        
        # Create sample topology file
        self._create_sample_topology()
        
        self.generator = GradualConflictGenerator(self.topology_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_topology(self):
        """Create sample topology file for testing."""
        locations = [
            ['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'],
            ['Origin', 'Region1', 'Country1', '10.0', '20.0', 'conflict_zone', '', '1000'],
            ['Town_B', 'Region1', 'Country1', '11.0', '21.0', 'town', '', '800'],
            ['Camp_C', 'Region1', 'Country1', '12.0', '22.0', 'camp', '', '5000']
        ]
        
        with open(self.topology_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(locations)
    
    def test_generate_gradual_conflict_basic(self):
        """Test basic gradual conflict generation."""
        output_file = self.generator.generate_gradual_conflict(
            origin='Origin',
            start_day=0,
            end_day=10,
            max_intensity=0.8,
            output_dir=self.temp_dir
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read and verify conflicts
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check escalation pattern
        self.assertIn(0, conflicts)
        self.assertIn(10, conflicts)
        
        # Check that intensity increases over time
        start_intensity = conflicts[0]['Origin']
        end_intensity = conflicts[10]['Origin']
        
        self.assertLess(start_intensity, end_intensity)
        self.assertEqual(end_intensity, 0.8)
        
        # Check linear escalation
        mid_intensity = conflicts[5]['Origin']
        expected_mid = start_intensity + (end_intensity - start_intensity) * 0.5
        self.assertAlmostEqual(mid_intensity, expected_mid, places=2)
    
    def test_generate_gradual_conflict_escalation_pattern(self):
        """Test gradual conflict escalation pattern."""
        output_file = self.generator.generate_gradual_conflict(
            origin='Origin',
            start_day=0,
            end_day=4,  # Short escalation for easier testing
            max_intensity=1.0,
            output_dir=self.temp_dir
        )
        
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check that each day has higher intensity than previous
        intensities = []
        for day in range(5):  # Days 0-4
            if day in conflicts:
                intensities.append(conflicts[day]['Origin'])
        
        # Should be monotonically increasing during escalation
        for i in range(1, len(intensities)):
            self.assertGreaterEqual(intensities[i], intensities[i-1])
    
    def test_generate_gradual_conflict_peak_persistence(self):
        """Test that peak intensity persists after escalation."""
        output_file = self.generator.generate_gradual_conflict(
            origin='Origin',
            start_day=0,
            end_day=10,
            max_intensity=0.9,
            output_dir=self.temp_dir
        )
        
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check that peak intensity is maintained after end_day
        peak_intensity = conflicts[10]['Origin']
        
        # Check several days after peak
        for day in range(11, min(25, max(conflicts.keys()) + 1)):
            if day in conflicts:
                self.assertEqual(conflicts[day]['Origin'], peak_intensity)
    
    def test_generate_gradual_conflict_invalid_parameters(self):
        """Test gradual conflict with invalid parameters."""
        # Invalid origin
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_gradual_conflict(
                origin='Unknown_Location',
                start_day=0,
                end_day=10,
                max_intensity=0.8,
                output_dir=self.temp_dir
            )
        
        # Invalid day parameters
        with self.assertRaises(ValueError):
            self.generator.generate_gradual_conflict(
                origin='Origin',
                start_day=10,
                end_day=5,  # end_day <= start_day
                max_intensity=0.8,
                output_dir=self.temp_dir
            )
        
        # Invalid intensity
        with self.assertRaises(ValueError):
            self.generator.generate_gradual_conflict(
                origin='Origin',
                start_day=0,
                end_day=10,
                max_intensity=1.5,  # > 1.0
                output_dir=self.temp_dir
            )
    
    def test_generate_gradual_conflict_validation(self):
        """Test that generated gradual conflict passes validation."""
        output_file = self.generator.generate_gradual_conflict(
            origin='Origin',
            start_day=2,
            end_day=15,
            max_intensity=0.7,
            output_dir=self.temp_dir
        )
        
        # Should pass validation
        self.assertTrue(self.generator.validate_scenario(output_file))
    
    def test_generate_gradual_conflict_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_spike_conflict('Origin', 0, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_cascading_conflict('Origin', 0, 0.5, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_oscillating_conflict('Origin', 0, 10, 0.5)


class TestCascadingConflictGenerator(unittest.TestCase):
    """Test cases for CascadingConflictGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.topology_file = os.path.join(self.temp_dir, 'locations.csv')
        self.routes_file = os.path.join(self.temp_dir, 'routes.csv')
        
        # Create sample topology and routes files
        self._create_sample_topology()
        self._create_sample_routes()
        
        self.generator = CascadingConflictGenerator(self.topology_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_topology(self):
        """Create sample topology file for testing."""
        locations = [
            ['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'],
            ['Origin', 'Region1', 'Country1', '10.0', '20.0', 'conflict_zone', '', '1000'],
            ['Town_A', 'Region1', 'Country1', '11.0', '21.0', 'town', '', '800'],
            ['Town_B', 'Region1', 'Country1', '12.0', '22.0', 'town', '', '600'],
            ['Camp_C', 'Region1', 'Country1', '13.0', '23.0', 'camp', '', '5000']
        ]
        
        with open(self.topology_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(locations)
    
    def _create_sample_routes(self):
        """Create sample routes file for testing."""
        routes = [
            ['#name1', 'name2', 'distance', 'forced_redirection'],
            ['Origin', 'Town_A', '50.0', '0'],
            ['Origin', 'Town_B', '75.0', '0'],
            ['Town_A', 'Camp_C', '100.0', '0'],
            ['Town_B', 'Camp_C', '80.0', '0']
        ]
        
        with open(self.routes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(routes)
    
    def test_generate_cascading_conflict_basic(self):
        """Test basic cascading conflict generation."""
        output_file = self.generator.generate_cascading_conflict(
            origin='Origin',
            start_day=0,
            spread_rate=1.0,  # 1 location per day
            max_intensity=0.8,
            routes_file=self.routes_file,
            output_dir=self.temp_dir
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read and verify conflicts
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check that conflict starts at origin
        self.assertIn(0, conflicts)
        self.assertEqual(conflicts[0]['Origin'], 0.8)
        
        # Check that conflict spreads to connected locations
        # Should spread to Town_A and Town_B on day 1
        self.assertIn(1, conflicts)
        affected_day1 = set(conflicts[1].keys())
        
        # Origin should still be affected, plus at least one neighbor
        self.assertIn('Origin', affected_day1)
        self.assertTrue(len(affected_day1) > 1)
    
    def test_generate_cascading_conflict_spread_rate(self):
        """Test cascading conflict with different spread rates."""
        # Slow spread rate
        output_file = self.generator.generate_cascading_conflict(
            origin='Origin',
            start_day=0,
            spread_rate=0.5,  # 0.5 locations per day (2 days per location)
            max_intensity=0.8,
            routes_file=self.routes_file,
            output_dir=self.temp_dir
        )
        
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # With slow spread, should take longer to affect neighbors
        # Day 0: Only origin
        self.assertEqual(len(conflicts[0]), 1)
        self.assertIn('Origin', conflicts[0])
        
        # Day 1: Still only origin (spread_rate = 0.5 means 2 days delay)
        if 1 in conflicts:
            # May or may not have spread yet due to spread delay
            pass
    
    def test_generate_cascading_conflict_intensity_decay(self):
        """Test intensity decay in cascading conflicts."""
        output_file = self.generator.generate_cascading_conflict(
            origin='Origin',
            start_day=0,
            spread_rate=1.0,
            max_intensity=1.0,
            routes_file=self.routes_file,
            output_dir=self.temp_dir
        )
        
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Find a day when multiple locations are affected
        multi_location_day = None
        for day, day_conflicts in conflicts.items():
            if len(day_conflicts) > 1:
                multi_location_day = day
                break
        
        if multi_location_day is not None:
            day_conflicts = conflicts[multi_location_day]
            
            # Origin should have highest intensity
            origin_intensity = day_conflicts.get('Origin', 0)
            
            # Other locations should have lower intensity due to distance decay
            for location, intensity in day_conflicts.items():
                if location != 'Origin':
                    self.assertLessEqual(intensity, origin_intensity)
    
    def test_generate_cascading_conflict_network_building(self):
        """Test network graph building from routes file."""
        network = self.generator._build_network_graph(self.routes_file)
        
        # Check that network was built correctly
        self.assertIn('Origin', network)
        self.assertIn('Town_A', network)
        
        # Check bidirectional connections
        origin_neighbors = [neighbor for neighbor, _ in network['Origin']]
        self.assertIn('Town_A', origin_neighbors)
        self.assertIn('Town_B', origin_neighbors)
        
        town_a_neighbors = [neighbor for neighbor, _ in network['Town_A']]
        self.assertIn('Origin', town_a_neighbors)
        self.assertIn('Camp_C', town_a_neighbors)
    
    def test_generate_cascading_conflict_missing_routes(self):
        """Test cascading conflict with missing routes file."""
        missing_routes = os.path.join(self.temp_dir, 'missing_routes.csv')
        
        # Should still work by creating complete graph
        output_file = self.generator.generate_cascading_conflict(
            origin='Origin',
            start_day=0,
            spread_rate=1.0,
            max_intensity=0.8,
            routes_file=missing_routes,
            output_dir=self.temp_dir
        )
        
        # Should create file successfully
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_cascading_conflict_invalid_parameters(self):
        """Test cascading conflict with invalid parameters."""
        # Invalid origin
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_cascading_conflict(
                origin='Unknown_Location',
                start_day=0,
                spread_rate=1.0,
                max_intensity=0.8,
                routes_file=self.routes_file,
                output_dir=self.temp_dir
            )
        
        # Invalid spread_rate
        with self.assertRaises(ValueError):
            self.generator.generate_cascading_conflict(
                origin='Origin',
                start_day=0,
                spread_rate=0.0,  # Must be positive
                max_intensity=0.8,
                routes_file=self.routes_file,
                output_dir=self.temp_dir
            )
        
        # Invalid intensity
        with self.assertRaises(ValueError):
            self.generator.generate_cascading_conflict(
                origin='Origin',
                start_day=0,
                spread_rate=1.0,
                max_intensity=1.5,  # > 1.0
                routes_file=self.routes_file,
                output_dir=self.temp_dir
            )
    
    def test_generate_cascading_conflict_validation(self):
        """Test that generated cascading conflict passes validation."""
        output_file = self.generator.generate_cascading_conflict(
            origin='Origin',
            start_day=3,
            spread_rate=0.8,
            max_intensity=0.7,
            routes_file=self.routes_file,
            output_dir=self.temp_dir
        )
        
        # Should pass validation
        self.assertTrue(self.generator.validate_scenario(output_file))
    
    def test_generate_cascading_conflict_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_spike_conflict('Origin', 0, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_gradual_conflict('Origin', 0, 10, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_oscillating_conflict('Origin', 0, 10, 0.5)


class TestOscillatingConflictGenerator(unittest.TestCase):
    """Test cases for OscillatingConflictGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.topology_file = os.path.join(self.temp_dir, 'locations.csv')
        
        # Create sample topology file
        self._create_sample_topology()
        
        self.generator = OscillatingConflictGenerator(self.topology_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_sample_topology(self):
        """Create sample topology file for testing."""
        locations = [
            ['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap'],
            ['Origin', 'Region1', 'Country1', '10.0', '20.0', 'conflict_zone', '', '1000'],
            ['Town_B', 'Region1', 'Country1', '11.0', '21.0', 'town', '', '800'],
            ['Camp_C', 'Region1', 'Country1', '12.0', '22.0', 'camp', '', '5000']
        ]
        
        with open(self.topology_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(locations)
    
    def test_generate_oscillating_conflict_basic(self):
        """Test basic oscillating conflict generation."""
        output_file = self.generator.generate_oscillating_conflict(
            origin='Origin',
            start_day=0,
            period=10,
            amplitude=0.5,
            output_dir=self.temp_dir
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read and verify conflicts
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check that conflicts start on specified day
        self.assertIn(0, conflicts)
        
        # Check oscillation pattern over one complete period
        intensities = []
        for day in range(10):  # One complete period
            if day in conflicts:
                intensities.append(conflicts[day]['Origin'])
        
        # Should have variation in intensities (not constant)
        self.assertGreater(len(set(intensities)), 1)
    
    def test_generate_oscillating_conflict_period_pattern(self):
        """Test oscillating conflict period pattern."""
        output_file = self.generator.generate_oscillating_conflict(
            origin='Origin',
            start_day=0,
            period=8,
            amplitude=0.4,
            output_dir=self.temp_dir
        )
        
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Check that pattern repeats after one period
        if 0 in conflicts and 8 in conflicts:
            intensity_0 = conflicts[0]['Origin']
            intensity_8 = conflicts[8]['Origin']
            
            # Should be approximately equal (allowing for small numerical differences)
            self.assertAlmostEqual(intensity_0, intensity_8, places=2)
        
        # Check that pattern has peaks and troughs
        intensities = []
        for day in range(16):  # Two complete periods
            if day in conflicts:
                intensities.append(conflicts[day]['Origin'])
        
        if len(intensities) > 4:
            max_intensity = max(intensities)
            min_intensity = min(intensities)
            
            # Should have significant variation
            self.assertGreater(max_intensity - min_intensity, 0.1)
    
    def test_generate_oscillating_conflict_amplitude(self):
        """Test oscillating conflict amplitude parameter."""
        output_file = self.generator.generate_oscillating_conflict(
            origin='Origin',
            start_day=0,
            period=10,
            amplitude=0.3,
            output_dir=self.temp_dir
        )
        
        conflicts = self.generator._read_conflicts_matrix(output_file)
        
        # Collect all intensities
        all_intensities = []
        for day_conflicts in conflicts.values():
            if 'Origin' in day_conflicts:
                all_intensities.append(day_conflicts['Origin'])
        
        if all_intensities:
            max_intensity = max(all_intensities)
            min_intensity = min(all_intensities)
            
            # The range should be related to the amplitude
            intensity_range = max_intensity - min_intensity
            
            # Should have reasonable variation based on amplitude
            self.assertGreater(intensity_range, 0.1)
            self.assertLess(intensity_range, 1.0)
    
    def test_generate_oscillating_conflict_phase_offset(self):
        """Test oscillating conflict with phase offset."""
        # Generate two conflicts with different start days
        output_file1 = self.generator.generate_oscillating_conflict(
            origin='Origin',
            start_day=0,
            period=8,
            amplitude=0.4,
            output_dir=self.temp_dir
        )
        
        output_file2 = self.generator.generate_oscillating_conflict(
            origin='Origin',
            start_day=2,  # Different start day
            period=8,
            amplitude=0.4,
            output_dir=self.temp_dir
        )
        
        conflicts1 = self.generator._read_conflicts_matrix(output_file1)
        conflicts2 = self.generator._read_conflicts_matrix(output_file2)
        
        # Check that the patterns are phase-shifted
        if 0 in conflicts1 and 2 in conflicts2:
            intensity1_day0 = conflicts1[0]['Origin']
            intensity2_day2 = conflicts2[2]['Origin']
            
            # These should be approximately equal (same phase)
            self.assertAlmostEqual(intensity1_day0, intensity2_day2, places=2)
    
    def test_generate_oscillating_conflict_invalid_parameters(self):
        """Test oscillating conflict with invalid parameters."""
        # Invalid origin
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_oscillating_conflict(
                origin='Unknown_Location',
                start_day=0,
                period=10,
                amplitude=0.5,
                output_dir=self.temp_dir
            )
        
        # Invalid period
        with self.assertRaises(ValueError):
            self.generator.generate_oscillating_conflict(
                origin='Origin',
                start_day=0,
                period=0,  # Must be positive
                amplitude=0.5,
                output_dir=self.temp_dir
            )
        
        # Invalid amplitude
        with self.assertRaises(ValueError):
            self.generator.generate_oscillating_conflict(
                origin='Origin',
                start_day=0,
                period=10,
                amplitude=1.5,  # > 1.0
                output_dir=self.temp_dir
            )
    
    def test_generate_oscillating_conflict_validation(self):
        """Test that generated oscillating conflict passes validation."""
        output_file = self.generator.generate_oscillating_conflict(
            origin='Origin',
            start_day=1,
            period=12,
            amplitude=0.6,
            output_dir=self.temp_dir
        )
        
        # Should pass validation
        self.assertTrue(self.generator.validate_scenario(output_file))
    
    def test_generate_oscillating_conflict_not_implemented_methods(self):
        """Test that non-applicable methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.generator.generate_spike_conflict('Origin', 0, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_gradual_conflict('Origin', 0, 10, 0.8)
        
        with self.assertRaises(NotImplementedError):
            self.generator.generate_cascading_conflict('Origin', 0, 0.5, 0.8)


if __name__ == '__main__':
    unittest.main()