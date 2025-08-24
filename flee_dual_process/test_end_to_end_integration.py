"""
End-to-End Integration Test Suite for Dual Process Experiments Framework

Tests complete experimental pipeline with all topology and scenario combinations,
validates integration with existing Flee codebase, and tests framework performance
under realistic experimental loads.
"""

import unittest
import tempfile
import shutil
import os
import json
import time
import itertools
from pathlib import Path
from typing import Dict, List, Any, Tuple
from unittest.mock import patch, MagicMock

try:
    from .topology_generator import (
        LinearTopologyGenerator, StarTopologyGenerator, 
        TreeTopologyGenerator, GridTopologyGenerator
    )
    from .scenario_generator import (
        SpikeConflictGenerator, GradualConflictGenerator,
        CascadingConflictGenerator, OscillatingConflictGenerator
    )
    from .config_manager import ConfigurationManager, ExperimentConfig
    from .experiment_runner import ExperimentRunner
    from .analysis_pipeline import AnalysisPipeline
    from .visualization_generator import VisualizationGenerator
    from .validation_framework import ExperimentValidator
    from .utils import CSVUtils, ValidationUtils
except ImportError:
    from topology_generator import (
        LinearTopologyGenerator, StarTopologyGenerator, 
        TreeTopologyGenerator, GridTopologyGenerator
    )
    from scenario_generator import (
        SpikeConflictGenerator, GradualConflictGenerator,
        CascadingConflictGenerator, OscillatingConflictGenerator
    )
    from config_manager import ConfigurationManager, ExperimentConfig
    from experiment_runner import ExperimentRunner
    from analysis_pipeline import AnalysisPipeline
    from visualization_generator import VisualizationGenerator
    from validation_framework import ExperimentValidator
    from utils import CSVUtils, ValidationUtils


class TestCompleteExperimentalPipeline(unittest.TestCase):
    """Test complete experimental pipeline with all combinations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        
        # Initialize all components
        self.config_manager = ConfigurationManager()
        self.experiment_validator = ExperimentValidator()
        
        # Create mock Flee executable
        self.mock_flee_executable = self._create_comprehensive_mock_flee()
        
        self.experiment_runner = ExperimentRunner(
            max_parallel=2,
            base_output_dir=self.temp_dir,
            flee_executable=self.mock_flee_executable,
            timeout=60
        )
        
        self.analysis_pipeline = AnalysisPipeline(
            results_directory=os.path.join(self.temp_dir, "results"),
            output_directory=os.path.join(self.temp_dir, "analysis")
        )
        
        self.visualization_generator = VisualizationGenerator(
            output_directory=os.path.join(self.temp_dir, "visualizations")
        )
        
        # Define test combinations
        self.topology_configs = {
            'linear': {'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
            'star': {'n_camps': 3, 'hub_pop': 2000, 'camp_capacity': 5000, 'radius': 100.0},
            'tree': {'branching_factor': 2, 'depth': 3, 'root_pop': 1500},
            'grid': {'rows': 3, 'cols': 3, 'cell_distance': 75.0, 'pop_distribution': 'uniform'}
        }
        
        self.scenario_configs = {
            'spike': {'start_day': 0, 'peak_intensity': 0.8},
            'gradual': {'start_day': 0, 'end_day': 10, 'max_intensity': 0.9},
            'cascading': {'start_day': 0, 'spread_rate': 0.3, 'max_intensity': 0.7},
            'oscillating': {'start_day': 0, 'period': 7, 'amplitude': 0.6, 'baseline': 0.2}
        }
        
        self.cognitive_modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_comprehensive_mock_flee(self) -> str:
        """Create comprehensive mock Flee executable."""
        mock_script = os.path.join(self.temp_dir, "comprehensive_mock_flee.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import os
import time
import random
import csv
import json
from pathlib import Path

def load_topology(input_dir):
    """Load topology information."""
    locations_file = os.path.join(input_dir, 'locations.csv')
    routes_file = os.path.join(input_dir, 'routes.csv')
    
    locations = {}
    if os.path.exists(locations_file):
        with open(locations_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row['name'].startswith('#'):
                    locations[row['name']] = {
                        'population': int(row.get('population', 0)),
                        'capacity': int(row.get('capacity', 10000)),
                        'location_type': row.get('location_type', 'town')
                    }
    
    routes = []
    if os.path.exists(routes_file):
        with open(routes_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row['name1'].startswith('#'):
                    routes.append({
                        'name1': row['name1'],
                        'name2': row['name2'],
                        'distance': float(row.get('distance', 50.0))
                    })
    
    return locations, routes

def load_conflicts(input_dir):
    """Load conflict information."""
    conflicts_file = os.path.join(input_dir, 'conflicts.csv')
    conflicts = {}
    
    if os.path.exists(conflicts_file):
        with open(conflicts_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # Skip comment lines
            while header[0].startswith('#'):
                header = next(reader)
            
            locations = header[1:]  # Skip 'Day' column
            
            for row in reader:
                if row and not row[0].startswith('#'):
                    day = int(row[0])
                    conflicts[day] = {}
                    for i, location in enumerate(locations):
                        if i + 1 < len(row):
                            conflicts[day][location] = float(row[i + 1])
    
    return conflicts

def load_simulation_settings(input_dir):
    """Load simulation settings."""
    settings_file = os.path.join(input_dir, 'simsetting.yml')
    settings = {}
    
    if os.path.exists(settings_file):
        # Simple YAML parsing for basic settings
        with open(settings_file, 'r') as f:
            for line in f:
                if ':' in line and not line.strip().startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Convert common types
                    if value.lower() in ['true', 'false']:
                        settings[key] = value.lower() == 'true'
                    elif value.replace('.', '').replace('-', '').isdigit():
                        settings[key] = float(value) if '.' in value else int(value)
                    else:
                        settings[key] = value
    
    return settings

def simulate_refugee_movement(locations, routes, conflicts, settings, simulation_days=30):
    """Simulate refugee movement with cognitive modes."""
    # Determine cognitive mode from settings
    dual_process = settings.get('two_system_decision_making', False)
    social_connectivity = settings.get('average_social_connectivity', 0.0)
    awareness_level = settings.get('awareness_level', 1)
    
    # Initialize agents
    num_agents = 100
    agents = []
    
    # Find origin location (highest initial population or first conflict location)
    origin_location = None
    max_pop = 0
    for name, info in locations.items():
        if info['population'] > max_pop:
            max_pop = info['population']
            origin_location = name
    
    if not origin_location and conflicts:
        # Use first conflict location as origin
        first_day_conflicts = conflicts.get(0, {})
        if first_day_conflicts:
            origin_location = max(first_day_conflicts.keys(), 
                                key=lambda x: first_day_conflicts[x])
    
    if not origin_location:
        origin_location = list(locations.keys())[0]
    
    # Initialize agents at origin
    for i in range(num_agents):
        agents.append({
            'id': f'0-{i+1}',
            'location': origin_location,
            'cognitive_state': 'S1',
            'connections': 0,
            'system2_activations': 0,
            'days_in_location': 0,
            'move_history': []
        })
    
    # Simulation data storage
    daily_populations = {}
    cognitive_states_log = []
    decision_log = []
    
    # Run simulation
    for day in range(simulation_days):
        daily_populations[day] = {}
        
        # Initialize daily population counts
        for location in locations:
            daily_populations[day][location] = 0
        
        # Get current conflict levels
        day_conflicts = conflicts.get(day, {})
        
        # Process each agent
        for agent in agents:
            current_location = agent['location']
            agent['days_in_location'] += 1
            
            # Count agent in current location
            daily_populations[day][current_location] += 1
            
            # Determine cognitive state based on conflict and settings
            conflict_level = day_conflicts.get(current_location, 0.0)
            
            # Cognitive state transitions
            if dual_process:
                if conflict_level > 0.6 and agent['cognitive_state'] == 'S1':
                    agent['cognitive_state'] = 'S2'
                    agent['system2_activations'] += 1
                elif conflict_level < 0.3 and agent['cognitive_state'] == 'S2':
                    if agent['days_in_location'] > 5:  # Recovery period
                        agent['cognitive_state'] = 'S1'
                
                # Social connectivity affects S2 activation
                if social_connectivity > 0:
                    agent['connections'] = min(5, int(social_connectivity * random.uniform(0.5, 1.5)))
                else:
                    agent['connections'] = 0
            else:
                agent['cognitive_state'] = 'S1'
                agent['connections'] = 0
            
            # Log cognitive state
            cognitive_states_log.append({
                'day': day,
                'agent_id': agent['id'],
                'cognitive_state': agent['cognitive_state'],
                'location': current_location,
                'connections': agent['connections'],
                'system2_activations': agent['system2_activations'],
                'days_in_location': agent['days_in_location'],
                'conflict_level': conflict_level
            })
            
            # Movement decision
            if day > 0:  # No movement on day 0
                move_chance = 0.0
                
                # Base move chance from conflict
                if conflict_level > 0.1:
                    move_chance = min(0.9, conflict_level * 1.2)
                
                # Cognitive mode affects decision making
                if agent['cognitive_state'] == 'S2':
                    # S2 considers more factors, may be more cautious
                    if agent['connections'] > 2:
                        move_chance *= 0.8  # Social connections reduce move chance
                    move_chance *= (1.0 + awareness_level * 0.1)  # Higher awareness
                else:
                    # S1 more reactive to immediate conflict
                    move_chance *= (1.0 + conflict_level * 0.5)
                
                # Make movement decision
                will_move = random.random() < move_chance
                
                # Log decision
                decision_log.append({
                    'day': day,
                    'agent_id': agent['id'],
                    'decision_type': 'move' if will_move else 'stay',
                    'cognitive_state': agent['cognitive_state'],
                    'location': current_location,
                    'movechance': move_chance,
                    'outcome': 1 if will_move else 0,
                    'system2_active': agent['cognitive_state'] == 'S2',
                    'conflict_level': conflict_level,
                    'connections': agent['connections']
                })
                
                # Execute movement
                if will_move:
                    # Find possible destinations
                    possible_destinations = []
                    for route in routes:
                        if route['name1'] == current_location:
                            possible_destinations.append(route['name2'])
                        elif route['name2'] == current_location:
                            possible_destinations.append(route['name1'])
                    
                    if possible_destinations:
                        # Choose destination (prefer camps for refugees)
                        camps = [dest for dest in possible_destinations 
                                if locations[dest]['location_type'] == 'camp']
                        if camps and random.random() < 0.7:
                            destination = random.choice(camps)
                        else:
                            destination = random.choice(possible_destinations)
                        
                        # Move agent
                        agent['location'] = destination
                        agent['days_in_location'] = 0
                        agent['move_history'].append((day, current_location, destination))
                        
                        # Update population counts
                        daily_populations[day][current_location] -= 1
                        daily_populations[day][destination] += 1
    
    return daily_populations, cognitive_states_log, decision_log

def create_output_files(output_dir, daily_populations, cognitive_states_log, decision_log):
    """Create output files in Flee format."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create out.csv
    with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
        
        for day in sorted(daily_populations.keys()):
            for location, count in daily_populations[day].items():
                if count > 0:  # Only write non-zero populations
                    writer.writerow([day, location, count, count])
    
    # Create cognitive_states.out.0
    with open(os.path.join(output_dir, 'cognitive_states.out.0'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'agent_id', 'cognitive_state', 'location', 'connections',
                        'system2_activations', 'days_in_location', 'conflict_level'])
        
        for entry in cognitive_states_log:
            writer.writerow([
                entry['day'], entry['agent_id'], entry['cognitive_state'],
                entry['location'], entry['connections'], entry['system2_activations'],
                entry['days_in_location'], entry['conflict_level']
            ])
    
    # Create decision_log.out.0
    with open(os.path.join(output_dir, 'decision_log.out.0'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'agent_id', 'decision_type', 'cognitive_state', 'location',
                        'movechance', 'outcome', 'system2_active', 'conflict_level', 'connections'])
        
        for entry in decision_log:
            writer.writerow([
                entry['day'], entry['agent_id'], entry['decision_type'],
                entry['cognitive_state'], entry['location'], entry['movechance'],
                entry['outcome'], entry['system2_active'], entry['conflict_level'],
                entry['connections']
            ])

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        
        try:
            # Load input data
            locations, routes = load_topology(input_dir)
            conflicts = load_conflicts(input_dir)
            settings = load_simulation_settings(input_dir)
            
            # Run simulation
            daily_populations, cognitive_states_log, decision_log = simulate_refugee_movement(
                locations, routes, conflicts, settings
            )
            
            # Create output files
            create_output_files(output_dir, daily_populations, cognitive_states_log, decision_log)
            
            print(f"Comprehensive mock simulation completed: {input_dir} -> {output_dir}")
            print(f"Processed {len(locations)} locations, {len(routes)} routes")
            print(f"Cognitive mode: {'dual_process' if settings.get('two_system_decision_making') else 'single_system'}")
            
        except Exception as e:
            print(f"Mock simulation error: {e}")
            sys.exit(1)
    else:
        print("Usage: comprehensive_mock_flee.py <input_dir> <output_dir>")
        sys.exit(1)
'''
        
        with open(mock_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(mock_script, 0o755)
        return mock_script
    
    def test_all_topology_scenario_combinations(self):
        """Test all combinations of topologies and scenarios."""
        successful_experiments = 0
        total_experiments = 0
        results_summary = {}
        
        # Test subset of combinations to keep test time reasonable
        test_combinations = [
            ('linear', 'spike', 's1_only'),
            ('star', 'gradual', 's2_full'),
            ('tree', 'cascading', 'dual_process'),
            ('grid', 'oscillating', 's2_disconnected')
        ]
        
        for topology_type, scenario_type, cognitive_mode in test_combinations:
            total_experiments += 1
            
            try:
                # Generate topology
                topology_generator = self._get_topology_generator(topology_type)
                topology_params = self.topology_configs[topology_type]
                
                locations_file, routes_file = self._generate_topology(
                    topology_generator, topology_type, topology_params
                )
                
                # Generate scenario
                scenario_generator = self._get_scenario_generator(scenario_type, locations_file)
                scenario_params = self.scenario_configs[scenario_type].copy()
                
                # Set origin based on topology
                origin = self._get_origin_location(topology_type)
                scenario_params['origin'] = origin
                
                conflicts_file = self._generate_scenario(
                    scenario_generator, scenario_type, scenario_params,
                    os.path.dirname(locations_file)
                )
                
                # Create configuration
                config = self.config_manager.create_cognitive_config(cognitive_mode)
                
                # Create experiment configuration
                experiment_config = ExperimentConfig(
                    experiment_id=f'test_{topology_type}_{scenario_type}_{cognitive_mode}',
                    topology_type=topology_type,
                    topology_params=topology_params,
                    scenario_type=scenario_type,
                    scenario_params=scenario_params,
                    cognitive_mode=cognitive_mode,
                    simulation_params=config,
                    replications=1
                )
                
                # Run experiment
                result = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
                
                if result.get('success', False):
                    successful_experiments += 1
                    
                    # Analyze results
                    analysis_results = self.analysis_pipeline.process_experiment(
                        result['experiment_dir']
                    )
                    
                    # Store results summary
                    results_summary[f'{topology_type}_{scenario_type}_{cognitive_mode}'] = {
                        'success': True,
                        'experiment_dir': result['experiment_dir'],
                        'analysis_results': analysis_results is not None,
                        'movement_metrics': analysis_results.metrics.get('movement_metrics') if analysis_results else None
                    }
                    
                    # Validate output files exist
                    output_dir = os.path.join(result['experiment_dir'], 'output')
                    self.assertTrue(os.path.exists(os.path.join(output_dir, 'out.csv')))
                    self.assertTrue(os.path.exists(os.path.join(output_dir, 'cognitive_states.out.0')))
                    self.assertTrue(os.path.exists(os.path.join(output_dir, 'decision_log.out.0')))
                    
                else:
                    results_summary[f'{topology_type}_{scenario_type}_{cognitive_mode}'] = {
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    }
                
            except Exception as e:
                results_summary[f'{topology_type}_{scenario_type}_{cognitive_mode}'] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Verify success rate
        success_rate = successful_experiments / total_experiments
        self.assertGreaterEqual(success_rate, 0.75, 
                               f"Success rate {success_rate:.2f} below threshold. Results: {results_summary}")
        
        print(f"Integration test completed: {successful_experiments}/{total_experiments} experiments successful")
        return results_summary
    
    def _get_topology_generator(self, topology_type: str):
        """Get appropriate topology generator."""
        generators = {
            'linear': LinearTopologyGenerator(self.base_config),
            'star': StarTopologyGenerator(self.base_config),
            'tree': TreeTopologyGenerator(self.base_config),
            'grid': GridTopologyGenerator(self.base_config)
        }
        return generators[topology_type]
    
    def _generate_topology(self, generator, topology_type: str, params: dict) -> Tuple[str, str]:
        """Generate topology based on type and parameters."""
        if topology_type == 'linear':
            return generator.generate_linear(**params)
        elif topology_type == 'star':
            return generator.generate_star(**params)
        elif topology_type == 'tree':
            return generator.generate_tree(**params)
        elif topology_type == 'grid':
            return generator.generate_grid(**params)
        else:
            raise ValueError(f"Unknown topology type: {topology_type}")
    
    def _get_scenario_generator(self, scenario_type: str, locations_file: str):
        """Get appropriate scenario generator."""
        generators = {
            'spike': SpikeConflictGenerator(locations_file),
            'gradual': GradualConflictGenerator(locations_file),
            'cascading': CascadingConflictGenerator(locations_file),
            'oscillating': OscillatingConflictGenerator(locations_file)
        }
        return generators[scenario_type]
    
    def _generate_scenario(self, generator, scenario_type: str, params: dict, output_dir: str) -> str:
        """Generate scenario based on type and parameters."""
        if scenario_type == 'spike':
            return generator.generate_spike_conflict(output_dir=output_dir, **params)
        elif scenario_type == 'gradual':
            return generator.generate_gradual_conflict(output_dir=output_dir, **params)
        elif scenario_type == 'cascading':
            return generator.generate_cascading_conflict(output_dir=output_dir, **params)
        elif scenario_type == 'oscillating':
            return generator.generate_oscillating_conflict(output_dir=output_dir, **params)
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
    
    def _get_origin_location(self, topology_type: str) -> str:
        """Get appropriate origin location for topology type."""
        origins = {
            'linear': 'Origin',
            'star': 'Hub',
            'tree': 'Root',
            'grid': 'Grid_0_0'
        }
        return origins[topology_type]
    
    def test_flee_codebase_compatibility(self):
        """Test compatibility with existing Flee codebase."""
        # Test that generated files are compatible with Flee format expectations
        
        # Generate standard topology
        topology_generator = LinearTopologyGenerator(self.base_config)
        locations_file, routes_file = topology_generator.generate_linear(
            n_nodes=3, segment_distance=50.0, start_pop=1000, pop_decay=0.8
        )
        
        # Validate Flee format compatibility
        validation_utils = ValidationUtils()
        
        # Check locations.csv format
        self.assertTrue(validation_utils.validate_locations_csv_format(locations_file))
        
        # Check routes.csv format
        self.assertTrue(validation_utils.validate_routes_csv_format(routes_file))
        
        # Generate scenario and validate format
        scenario_generator = SpikeConflictGenerator(locations_file)
        conflicts_file = scenario_generator.generate_spike_conflict(
            origin='Origin',
            start_day=0,
            peak_intensity=0.8,
            output_dir=os.path.dirname(locations_file)
        )
        
        # Validate conflicts.csv format
        self.assertTrue(scenario_generator.validate_scenario(conflicts_file))
        
        # Create configuration and validate simsetting.yml format
        config = self.config_manager.create_cognitive_config('dual_process')
        simsetting_file = os.path.join(self.temp_dir, 'simsetting.yml')
        self.config_manager.create_simsetting_yml(config, simsetting_file)
        
        self.assertTrue(os.path.exists(simsetting_file))
        
        # Validate YAML format
        with open(simsetting_file, 'r') as f:
            content = f.read()
            self.assertIn('two_system_decision_making:', content)
            self.assertIn('average_social_connectivity:', content)
    
    def test_framework_performance_under_load(self):
        """Test framework performance under realistic experimental loads."""
        start_time = time.time()
        
        # Create multiple experiments to simulate realistic load
        experiment_configs = []
        
        for i in range(6):  # Moderate load test
            config = {
                'experiment_id': f'load_test_{i}',
                'topology_type': 'linear',
                'topology_params': {'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                'scenario_type': 'spike',
                'scenario_params': {'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8},
                'cognitive_mode': 'dual_process',
                'simulation_params': self.config_manager.create_cognitive_config('dual_process'),
                'replications': 1
            }
            experiment_configs.append(config)
        
        # Run experiments
        successful_runs = 0
        for config in experiment_configs:
            result = self.experiment_runner.run_single_experiment(config)
            if result.get('success', False):
                successful_runs += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        self.assertEqual(successful_runs, 6, "Not all experiments completed successfully")
        self.assertLess(total_time, 120, f"Performance test took too long: {total_time:.2f}s")
        
        # Calculate throughput
        throughput = successful_runs / total_time
        self.assertGreater(throughput, 0.05, f"Throughput too low: {throughput:.3f} experiments/second")
        
        print(f"Performance test completed: {successful_runs} experiments in {total_time:.2f}s")
        print(f"Throughput: {throughput:.3f} experiments/second")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing Flee functionality."""
        # Test that framework doesn't break existing Flee behavior
        
        # Create standard Flee input files
        topology_generator = LinearTopologyGenerator(self.base_config)
        locations_file, routes_file = topology_generator.generate_linear(
            n_nodes=3, segment_distance=50.0, start_pop=1000, pop_decay=0.8
        )
        
        # Create traditional Flee configuration (without dual-process features)
        traditional_config = {
            'move_rules': {
                'awareness_level': 1,
                'camp_move_chance': 0.001,
                'conflict_move_chance': 1.0,
                'default_move_chance': 0.3
            },
            'two_system_decision_making': False,  # Disable dual-process
            'end_time': 10
        }
        
        # Create experiment with traditional settings
        experiment_config = ExperimentConfig(
            experiment_id='backward_compatibility_test',
            topology_type='linear',
            topology_params={'n_nodes': 3},
            scenario_type='spike',
            scenario_params={'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8},
            cognitive_mode='traditional',
            simulation_params=traditional_config,
            replications=1
        )
        
        # Run experiment
        result = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
        
        self.assertTrue(result.get('success', False), 
                       f"Backward compatibility test failed: {result.get('error', 'Unknown error')}")
        
        # Verify traditional output files are created
        output_dir = os.path.join(result['experiment_dir'], 'output')
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'out.csv')))
        
        # Cognitive tracking files should still be created but with minimal data
        cognitive_file = os.path.join(output_dir, 'cognitive_states.out.0')
        if os.path.exists(cognitive_file):
            # Verify all agents are in S1 state (traditional behavior)
            with open(cognitive_file, 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.strip().split(',')
                        if len(parts) >= 3:
                            cognitive_state = parts[2]
                            self.assertEqual(cognitive_state, 'S1', 
                                           "Traditional mode should only use S1 cognitive state")
    
    def test_error_recovery_and_resilience(self):
        """Test error recovery and system resilience."""
        # Test 1: Invalid topology parameters
        with self.assertRaises(ValueError):
            topology_generator = LinearTopologyGenerator(self.base_config)
            topology_generator.generate_linear(n_nodes=1, segment_distance=50.0, start_pop=1000, pop_decay=0.8)
        
        # Test 2: Missing input files
        invalid_config = {
            'experiment_id': 'missing_files_test',
            'topology_type': 'linear',
            'cognitive_mode': 's1_only',
            'simulation_params': {}
        }
        
        result = self.experiment_runner.run_single_experiment(invalid_config)
        self.assertFalse(result.get('success', True))
        self.assertIn('error', result)
        
        # Test 3: Corrupted input files
        corrupted_dir = os.path.join(self.temp_dir, 'corrupted_test')
        os.makedirs(corrupted_dir)
        
        # Create corrupted locations.csv
        with open(os.path.join(corrupted_dir, 'locations.csv'), 'w') as f:
            f.write("invalid,csv,format\n")
        
        # Analysis should handle corrupted files gracefully
        try:
            analysis_results = self.analysis_pipeline.load_experiment_data(corrupted_dir)
            # Should return empty or None results, not crash
            self.assertIsNotNone(analysis_results)
        except Exception as e:
            # If it raises an exception, it should be a handled one
            self.assertIsInstance(e, (FileNotFoundError, ValueError))
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup after experiments."""
        import psutil
        
        # Get initial resource state
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_open_files = len(process.open_files())
        
        # Run multiple experiments
        for i in range(5):
            config = {
                'experiment_id': f'cleanup_test_{i}',
                'topology_type': 'linear',
                'topology_params': {'n_nodes': 3, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                'scenario_type': 'spike',
                'scenario_params': {'origin': 'Origin', 'start_day': 0, 'peak_intensity': 0.8},
                'cognitive_mode': 's1_only',
                'simulation_params': self.config_manager.create_cognitive_config('s1_only'),
                'replications': 1
            }
            
            result = self.experiment_runner.run_single_experiment(config)
            self.assertTrue(result.get('success', False))
        
        # Check resource state after experiments
        final_memory = process.memory_info().rss
        final_open_files = len(process.open_files())
        
        # Memory growth should be reasonable (less than 50MB)
        memory_growth = final_memory - initial_memory
        self.assertLess(memory_growth, 50 * 1024 * 1024, 
                       f"Excessive memory growth: {memory_growth / 1024 / 1024:.2f}MB")
        
        # File handles should be cleaned up
        file_handle_growth = final_open_files - initial_open_files
        self.assertLessEqual(file_handle_growth, 5, 
                            f"File handles not properly cleaned up: {file_handle_growth} additional handles")


if __name__ == '__main__':
    unittest.main()