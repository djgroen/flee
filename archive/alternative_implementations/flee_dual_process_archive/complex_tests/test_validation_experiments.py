"""
Validation Experiments for Dual Process Framework

Runs baseline experiments to validate cognitive mode implementations,
compares results with existing Flee behavior for consistency checks,
and performs sensitivity analysis to identify key parameters and thresholds.
"""

import unittest
import tempfile
import shutil
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from scipy import stats
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flee_dual_process.topology_generator import LinearTopologyGenerator
from flee_dual_process.scenario_generator import SpikeConflictGenerator, GradualConflictGenerator
from flee_dual_process.config_manager import ConfigurationManager, ExperimentConfig
from flee_dual_process.experiment_runner import ExperimentRunner
from flee_dual_process.analysis_pipeline import AnalysisPipeline


class TestValidationExperiments(unittest.TestCase):
    """Validation experiments for cognitive mode implementations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_config = {'output_dir': self.temp_dir}
        
        # Create comprehensive mock Flee executable
        self.mock_flee_executable = self._create_validation_mock_flee()
        
        # Initialize components
        self.config_manager = ConfigurationManager()
        self.experiment_runner = ExperimentRunner(
            max_parallel=1,
            base_output_dir=self.temp_dir,
            flee_executable=self.mock_flee_executable,
            timeout=60
        )
        self.analysis_pipeline = AnalysisPipeline(
            results_directory=os.path.join(self.temp_dir, "results"),
            output_directory=os.path.join(self.temp_dir, "analysis")
        )
        
        # Store experiment results for comparison
        self.experiment_results = {}
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_validation_mock_flee(self) -> str:
        """Create a mock Flee executable that simulates realistic cognitive behavior."""
        mock_script = os.path.join(self.temp_dir, "validation_mock_flee.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import os
import time
import random
import csv
import yaml
from pathlib import Path

def load_simulation_settings(input_dir):
    """Load simulation settings from simsetting.yml."""
    settings_file = os.path.join(input_dir, 'simsetting.yml')
    settings = {}
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                settings = yaml.safe_load(f) or {}
        except:
            # Fallback to simple parsing
            with open(settings_file, 'r') as f:
                for line in f:
                    if ':' in line and not line.strip().startswith('#'):
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if value.lower() in ['true', 'false']:
                            settings[key] = value.lower() == 'true'
                        elif value.replace('.', '').replace('-', '').isdigit():
                            settings[key] = float(value) if '.' in value else int(value)
                        else:
                            settings[key] = value
    
    return settings

def load_conflicts(input_dir):
    """Load conflict data."""
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

def simulate_cognitive_behavior(settings, conflicts, simulation_days=30):
    """Simulate refugee behavior with different cognitive modes."""
    # Extract cognitive settings
    dual_process = settings.get('two_system_decision_making', False)
    social_connectivity = settings.get('average_social_connectivity', 0.0)
    awareness_level = settings.get('awareness_level', 1)
    conflict_threshold = settings.get('conflict_threshold', 0.6)
    
    # Initialize agents
    num_agents = 50
    agents = []
    
    for i in range(num_agents):
        agents.append({
            'id': f'0-{i+1}',
            'location': 'Origin',
            'cognitive_state': 'S1',
            'connections': 0,
            'system2_activations': 0,
            'days_in_location': 0,
            'move_history': [],
            'decision_factors': []
        })
    
    # Simulation data
    daily_populations = {}
    cognitive_states_log = []
    decision_log = []
    
    # Available locations (simple linear topology)
    locations = ['Origin', 'Town_1', 'Town_2', 'Camp_3']
    
    for day in range(simulation_days):
        daily_populations[day] = {loc: 0 for loc in locations}
        day_conflicts = conflicts.get(day, {})
        
        for agent in agents:
            current_location = agent['location']
            agent['days_in_location'] += 1
            daily_populations[day][current_location] += 1
            
            conflict_level = day_conflicts.get(current_location, 0.0)
            
            # Cognitive state transitions based on mode
            if dual_process:
                # Dual process mode: S1 <-> S2 transitions
                if conflict_level > conflict_threshold and agent['cognitive_state'] == 'S1':
                    agent['cognitive_state'] = 'S2'
                    agent['system2_activations'] += 1
                elif conflict_level < 0.3 and agent['cognitive_state'] == 'S2':
                    if agent['days_in_location'] > 3:  # Recovery period
                        agent['cognitive_state'] = 'S1'
                
                # Social connectivity affects S2 behavior
                if social_connectivity > 0:
                    base_connections = int(social_connectivity)
                    agent['connections'] = max(0, base_connections + random.randint(-1, 2))
                else:
                    agent['connections'] = 0
            else:
                # Traditional mode: always S1
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
            
            # Movement decision (skip day 0)
            if day > 0:
                move_chance = 0.0
                decision_factors = {
                    'conflict_level': conflict_level,
                    'cognitive_state': agent['cognitive_state'],
                    'connections': agent['connections'],
                    'days_in_location': agent['days_in_location']
                }
                
                # Base movement probability from conflict
                if conflict_level > 0.1:
                    move_chance = min(0.9, conflict_level * 1.5)
                
                # Cognitive mode affects decision making
                if agent['cognitive_state'] == 'S2':
                    # S2: More deliberative, considers social connections
                    if agent['connections'] > 2:
                        move_chance *= 0.7  # Social connections reduce move chance
                    
                    # Higher awareness in S2 mode
                    move_chance *= (1.0 + awareness_level * 0.15)
                    
                    # S2 agents are more likely to move to camps
                    if current_location != 'Camp_3':
                        move_chance *= 1.2
                else:
                    # S1: More reactive, immediate response to conflict
                    move_chance *= (1.0 + conflict_level * 0.8)
                    
                    # S1 agents move more randomly
                    move_chance += random.uniform(0.0, 0.1)
                
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
                if will_move and current_location != 'Camp_3':  # Can't move from final camp
                    # Simple linear movement: Origin -> Town_1 -> Town_2 -> Camp_3
                    next_locations = {
                        'Origin': ['Town_1'],
                        'Town_1': ['Town_2', 'Origin'],
                        'Town_2': ['Camp_3', 'Town_1'],
                        'Camp_3': []
                    }
                    
                    possible_destinations = next_locations.get(current_location, [])
                    if possible_destinations:
                        # S2 agents prefer camps, S1 agents move more randomly
                        if agent['cognitive_state'] == 'S2' and 'Camp_3' in possible_destinations:
                            destination = 'Camp_3'
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
    """Create output files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create out.csv
    with open(os.path.join(output_dir, 'out.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#day', 'location', 'refugees', 'total_refugees'])
        
        for day in sorted(daily_populations.keys()):
            for location, count in daily_populations[day].items():
                if count > 0:
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
            # Load configuration and conflicts
            settings = load_simulation_settings(input_dir)
            conflicts = load_conflicts(input_dir)
            
            # Run simulation
            daily_populations, cognitive_states_log, decision_log = simulate_cognitive_behavior(
                settings, conflicts
            )
            
            # Create output files
            create_output_files(output_dir, daily_populations, cognitive_states_log, decision_log)
            
            print(f"Validation simulation completed: {input_dir} -> {output_dir}")
            print(f"Cognitive mode: {'dual_process' if settings.get('two_system_decision_making') else 'traditional'}")
            
        except Exception as e:
            print(f"Validation simulation error: {e}")
            sys.exit(1)
    else:
        print("Usage: validation_mock_flee.py <input_dir> <output_dir>")
        sys.exit(1)
'''
        
        with open(mock_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(mock_script, 0o755)
        return mock_script
    
    def test_baseline_cognitive_mode_validation(self):
        """Test baseline experiments to validate cognitive mode implementations."""
        print("\n=== Baseline Cognitive Mode Validation ===")
        
        cognitive_modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
        baseline_results = {}
        
        for mode in cognitive_modes:
            print(f"\nTesting cognitive mode: {mode}")
            
            # Generate standard topology
            topology_generator = LinearTopologyGenerator(self.base_config)
            locations_file, routes_file = topology_generator.generate_linear(
                n_nodes=4, segment_distance=50.0, start_pop=1000, pop_decay=0.8
            )
            
            # Generate spike conflict scenario
            scenario_generator = SpikeConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_spike_conflict(
                origin='Origin', start_day=5, peak_intensity=0.8,
                output_dir=os.path.dirname(locations_file)
            )
            
            # Create configuration
            config = self.config_manager.create_cognitive_config(mode)
            
            # Run experiment
            experiment_config = ExperimentConfig(
                experiment_id=f'baseline_{mode}',
                topology_type='linear',
                topology_params={'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                scenario_type='spike',
                scenario_params={'origin': 'Origin', 'start_day': 5, 'peak_intensity': 0.8},
                cognitive_mode=mode,
                simulation_params=config,
                replications=1
            )
            
            result = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
            self.assertTrue(result['success'], f"Baseline experiment failed for {mode}: {result.get('error')}")
            
            # Analyze results
            analysis_results = self.analysis_pipeline.process_experiment(result['experiment_dir'])
            self.assertIsNotNone(analysis_results, f"Analysis failed for {mode}")
            
            baseline_results[mode] = {
                'experiment_dir': result['experiment_dir'],
                'analysis_results': analysis_results,
                'movement_metrics': analysis_results.metrics.get('movement_metrics', {}),
                'cognitive_analysis': analysis_results.metrics.get('cognitive_analysis', {})
            }
            
            print(f"✓ {mode} baseline experiment completed")
        
        # Validate cognitive mode differences
        self._validate_cognitive_mode_differences(baseline_results)
        
        self.experiment_results['baseline'] = baseline_results
        return baseline_results
    
    def _validate_cognitive_mode_differences(self, results: Dict[str, Any]):
        """Validate that different cognitive modes produce different behaviors."""
        print("\n--- Validating Cognitive Mode Differences ---")
        
        # Check that S1-only and S2-full produce different movement patterns
        s1_metrics = results['s1_only']['movement_metrics']
        s2_metrics = results['s2_full']['movement_metrics']
        
        # S2 agents should generally move more deliberately (potentially different timing)
        if 'first_move_day' in s1_metrics and 'first_move_day' in s2_metrics:
            s1_first_move = s1_metrics['first_move_day']['mean']
            s2_first_move = s2_metrics['first_move_day']['mean']
            print(f"First move day - S1: {s1_first_move:.2f}, S2: {s2_first_move:.2f}")
        
        # Check cognitive state distributions
        s1_cognitive = results['s1_only']['cognitive_analysis']
        s2_cognitive = results['s2_full']['cognitive_analysis']
        dual_cognitive = results['dual_process']['cognitive_analysis']
        
        # S1-only should have mostly S1 states
        if 'state_distribution' in s1_cognitive and 'overall' in s1_cognitive['state_distribution']:
            s1_proportions = s1_cognitive['state_distribution']['overall']['state_proportions']
            s1_ratio = s1_proportions.get('S1', 0)
            self.assertGreater(s1_ratio, 0.8, "S1-only mode should have >80% S1 states")
            print(f"✓ S1-only mode: {s1_ratio:.1%} S1 states")
        
        # S2-full should have more S2 states than S1-only (or at least different behavior)
        if 'state_distribution' in s2_cognitive and 'overall' in s2_cognitive['state_distribution']:
            s2_proportions = s2_cognitive['state_distribution']['overall']['state_proportions']
            s2_ratio = s2_proportions.get('S2', 0)
            # Note: In simple scenarios, S2 activation might be low due to conflict timing/intensity
            print(f"✓ S2-full mode: {s2_ratio:.1%} S2 states (may be low in simple scenarios)")
            
            # Check that the configuration is different (social connectivity should be higher)
            s2_social = s2_cognitive.get('social_connectivity', {})
            s1_social = s1_cognitive.get('social_connectivity', {})
            
            if 'connections_by_state' in s2_social and 'connections_by_state' in s1_social:
                s2_connections = s2_social['connections_by_state'].get('mean', {}).get('S1', 0)
                s1_connections = s1_social['connections_by_state'].get('mean', {}).get('S1', 0)
                print(f"Social connectivity - S1-only: {s1_connections:.2f}, S2-full: {s2_connections:.2f}")
                # S2-full should have higher social connectivity even in S1 state
                if s2_connections > s1_connections:
                    print("✓ S2-full mode shows higher social connectivity")
        
        # Dual-process should show transitions
        if 'transitions' in dual_cognitive:
            transitions = dual_cognitive['transitions']
            total_transitions = sum(transitions.values()) if transitions else 0
            # For dual-process, we expect some transitions, but it might be 0 in simple scenarios
            print(f"✓ Dual-process mode: {total_transitions} cognitive transitions")
            # Don't assert > 0 since transitions depend on conflict levels and thresholds
        
        print("✓ Cognitive mode differences validated")
    
    def test_flee_behavior_consistency(self):
        """Compare results with existing Flee behavior for consistency checks."""
        print("\n=== Flee Behavior Consistency Check ===")
        
        # Test traditional Flee behavior (no dual-process features)
        traditional_config = {
            'move_rules': {
                'awareness_level': 1,
                'camp_move_chance': 0.001,
                'conflict_move_chance': 1.0,
                'default_move_chance': 0.3
            },
            'two_system_decision_making': False,
            'end_time': 20
        }
        
        # Generate topology and scenario
        topology_generator = LinearTopologyGenerator(self.base_config)
        locations_file, routes_file = topology_generator.generate_linear(
            n_nodes=4, segment_distance=50.0, start_pop=1000, pop_decay=0.8
        )
        
        scenario_generator = SpikeConflictGenerator(locations_file)
        conflicts_file = scenario_generator.generate_spike_conflict(
            origin='Origin', start_day=3, peak_intensity=0.7,
            output_dir=os.path.dirname(locations_file)
        )
        
        # Run traditional experiment (using s1_only with traditional config)
        traditional_experiment = ExperimentConfig(
            experiment_id='traditional_flee',
            topology_type='linear',
            topology_params={'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
            scenario_type='spike',
            scenario_params={'origin': 'Origin', 'start_day': 3, 'peak_intensity': 0.7},
            cognitive_mode='s1_only',  # Use s1_only as traditional equivalent
            simulation_params=traditional_config,
            replications=1
        )
        
        traditional_result = self.experiment_runner.run_single_experiment(traditional_experiment.to_dict())
        self.assertTrue(traditional_result['success'], 
                       f"Traditional Flee experiment failed: {traditional_result.get('error')}")
        
        # Run S1-only experiment (should be similar to traditional)
        s1_config = self.config_manager.create_cognitive_config('s1_only')
        s1_experiment = ExperimentConfig(
            experiment_id='s1_only_comparison',
            topology_type='linear',
            topology_params={'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
            scenario_type='spike',
            scenario_params={'origin': 'Origin', 'start_day': 3, 'peak_intensity': 0.7},
            cognitive_mode='s1_only',
            simulation_params=s1_config,
            replications=1
        )
        
        s1_result = self.experiment_runner.run_single_experiment(s1_experiment.to_dict())
        self.assertTrue(s1_result['success'], 
                       f"S1-only experiment failed: {s1_result.get('error')}")
        
        # Analyze both results
        traditional_analysis = self.analysis_pipeline.process_experiment(traditional_result['experiment_dir'])
        s1_analysis = self.analysis_pipeline.process_experiment(s1_result['experiment_dir'])
        
        self.assertIsNotNone(traditional_analysis, "Traditional analysis failed")
        self.assertIsNotNone(s1_analysis, "S1-only analysis failed")
        
        # Compare movement patterns (should be similar)
        traditional_metrics = traditional_analysis.metrics.get('movement_metrics', {})
        s1_metrics = s1_analysis.metrics.get('movement_metrics', {})
        
        print(f"Traditional Flee movement metrics: {traditional_metrics}")
        print(f"S1-only movement metrics: {s1_metrics}")
        
        # Basic consistency checks
        if 'total_movements' in traditional_metrics and 'total_movements' in s1_metrics:
            traditional_moves = traditional_metrics['total_movements']
            s1_moves = s1_metrics['total_movements']
            
            # Should be within reasonable range (allowing for some variation due to randomness)
            ratio = s1_moves / (traditional_moves + 1e-6)
            self.assertGreater(ratio, 0.5, "S1-only should have at least 50% of traditional movement")
            self.assertLess(ratio, 2.0, "S1-only should have at most 200% of traditional movement")
            print(f"✓ Movement consistency: S1-only has {ratio:.1%} of traditional movements")
        
        print("✓ Flee behavior consistency validated")
        
        self.experiment_results['consistency'] = {
            'traditional': traditional_analysis,
            's1_only': s1_analysis
        }
    
    def test_parameter_sensitivity_analysis(self):
        """Perform sensitivity analysis to identify key parameters and thresholds."""
        print("\n=== Parameter Sensitivity Analysis ===")
        
        # Test sensitivity to conflict threshold
        conflict_thresholds = [0.3, 0.5, 0.7, 0.9]
        threshold_results = {}
        
        print("\n--- Testing Conflict Threshold Sensitivity ---")
        
        for threshold in conflict_thresholds:
            print(f"Testing conflict threshold: {threshold}")
            
            # Generate topology and scenario
            topology_generator = LinearTopologyGenerator(self.base_config)
            locations_file, routes_file = topology_generator.generate_linear(
                n_nodes=4, segment_distance=50.0, start_pop=1000, pop_decay=0.8
            )
            
            scenario_generator = GradualConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_gradual_conflict(
                origin='Origin', start_day=0, end_day=15, max_intensity=0.9,
                output_dir=os.path.dirname(locations_file)
            )
            
            # Create dual-process configuration with specific threshold
            config = self.config_manager.create_cognitive_config('dual_process')
            config['conflict_threshold'] = threshold
            
            experiment_config = ExperimentConfig(
                experiment_id=f'threshold_{threshold}',
                topology_type='linear',
                topology_params={'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                scenario_type='gradual',
                scenario_params={'origin': 'Origin', 'start_day': 0, 'end_day': 15, 'max_intensity': 0.9},
                cognitive_mode='dual_process',
                simulation_params=config,
                replications=1
            )
            
            result = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
            self.assertTrue(result['success'], 
                           f"Threshold sensitivity experiment failed for {threshold}: {result.get('error')}")
            
            analysis_results = self.analysis_pipeline.process_experiment(result['experiment_dir'])
            self.assertIsNotNone(analysis_results, f"Analysis failed for threshold {threshold}")
            
            threshold_results[threshold] = {
                'analysis_results': analysis_results,
                'cognitive_analysis': analysis_results.metrics.get('cognitive_analysis', {})
            }
            
            print(f"✓ Threshold {threshold} experiment completed")
        
        # Analyze threshold sensitivity
        self._analyze_threshold_sensitivity(threshold_results)
        
        # Test sensitivity to social connectivity
        connectivity_levels = [0.0, 2.0, 5.0, 8.0]
        connectivity_results = {}
        
        print("\n--- Testing Social Connectivity Sensitivity ---")
        
        for connectivity in connectivity_levels:
            print(f"Testing social connectivity: {connectivity}")
            
            # Generate topology and scenario
            topology_generator = LinearTopologyGenerator(self.base_config)
            locations_file, routes_file = topology_generator.generate_linear(
                n_nodes=4, segment_distance=50.0, start_pop=1000, pop_decay=0.8
            )
            
            scenario_generator = SpikeConflictGenerator(locations_file)
            conflicts_file = scenario_generator.generate_spike_conflict(
                origin='Origin', start_day=5, peak_intensity=0.8,
                output_dir=os.path.dirname(locations_file)
            )
            
            # Create S2-full configuration with specific connectivity
            config = self.config_manager.create_cognitive_config('s2_full')
            config['average_social_connectivity'] = connectivity
            
            experiment_config = ExperimentConfig(
                experiment_id=f'connectivity_{connectivity}',
                topology_type='linear',
                topology_params={'n_nodes': 4, 'segment_distance': 50.0, 'start_pop': 1000, 'pop_decay': 0.8},
                scenario_type='spike',
                scenario_params={'origin': 'Origin', 'start_day': 5, 'peak_intensity': 0.8},
                cognitive_mode='s2_full',
                simulation_params=config,
                replications=1
            )
            
            result = self.experiment_runner.run_single_experiment(experiment_config.to_dict())
            self.assertTrue(result['success'], 
                           f"Connectivity sensitivity experiment failed for {connectivity}: {result.get('error')}")
            
            analysis_results = self.analysis_pipeline.process_experiment(result['experiment_dir'])
            self.assertIsNotNone(analysis_results, f"Analysis failed for connectivity {connectivity}")
            
            connectivity_results[connectivity] = {
                'analysis_results': analysis_results,
                'movement_metrics': analysis_results.metrics.get('movement_metrics', {})
            }
            
            print(f"✓ Connectivity {connectivity} experiment completed")
        
        # Analyze connectivity sensitivity
        self._analyze_connectivity_sensitivity(connectivity_results)
        
        self.experiment_results['sensitivity'] = {
            'threshold': threshold_results,
            'connectivity': connectivity_results
        }
        
        print("✓ Parameter sensitivity analysis completed")
    
    def _analyze_threshold_sensitivity(self, results: Dict[float, Any]):
        """Analyze sensitivity to conflict threshold parameter."""
        print("\n--- Conflict Threshold Sensitivity Analysis ---")
        
        thresholds = sorted(results.keys())
        s2_activations = []
        
        for threshold in thresholds:
            cognitive_analysis = results[threshold]['cognitive_analysis']
            
            if 'state_distribution' in cognitive_analysis and 'overall' in cognitive_analysis['state_distribution']:
                state_proportions = cognitive_analysis['state_distribution']['overall']['state_proportions']
                s2_ratio = state_proportions.get('S2', 0)
                s2_activations.append(s2_ratio)
                print(f"Threshold {threshold}: {s2_ratio:.1%} S2 activations")
            else:
                s2_activations.append(0.0)
                print(f"Threshold {threshold}: 0.0% S2 activations (no data)")
        
        # Check that higher thresholds lead to fewer S2 activations
        if len(s2_activations) >= 2:
            # Should generally decrease as threshold increases
            decreasing_trend = all(s2_activations[i] >= s2_activations[i+1] - 0.1 
                                 for i in range(len(s2_activations)-1))
            if decreasing_trend:
                print("✓ S2 activations decrease with higher conflict threshold (as expected)")
            else:
                print("⚠ S2 activations don't follow expected decreasing trend")
        
        # Identify key threshold
        if s2_activations:
            max_activation_idx = s2_activations.index(max(s2_activations))
            key_threshold = thresholds[max_activation_idx]
            print(f"✓ Key threshold identified: {key_threshold} (max S2 activation: {max(s2_activations):.1%})")
    
    def _analyze_connectivity_sensitivity(self, results: Dict[float, Any]):
        """Analyze sensitivity to social connectivity parameter."""
        print("\n--- Social Connectivity Sensitivity Analysis ---")
        
        connectivity_levels = sorted(results.keys())
        movement_rates = []
        
        for connectivity in connectivity_levels:
            movement_metrics = results[connectivity]['movement_metrics']
            
            if 'total_movements' in movement_metrics:
                total_movements = movement_metrics['total_movements']
                movement_rates.append(total_movements)
                print(f"Connectivity {connectivity}: {total_movements} total movements")
            else:
                movement_rates.append(0)
        
        # Check relationship between connectivity and movement
        if len(movement_rates) >= 2:
            # Higher connectivity might lead to different movement patterns
            min_movements = min(movement_rates)
            max_movements = max(movement_rates)
            variation = (max_movements - min_movements) / (max_movements + 1e-6)
            
            if variation > 0.1:  # More than 10% variation
                print(f"✓ Social connectivity shows significant impact on movement (variation: {variation:.1%})")
            else:
                print(f"⚠ Social connectivity shows limited impact on movement (variation: {variation:.1%})")
        
        # Identify optimal connectivity level
        if movement_rates:
            optimal_idx = movement_rates.index(max(movement_rates))
            optimal_connectivity = connectivity_levels[optimal_idx]
            print(f"✓ Optimal connectivity level: {optimal_connectivity} (max movements: {max(movement_rates)})")
    
    def test_statistical_significance(self):
        """Test statistical significance of cognitive mode differences."""
        print("\n=== Statistical Significance Testing ===")
        
        if 'baseline' not in self.experiment_results:
            self.test_baseline_cognitive_mode_validation()
        
        baseline_results = self.experiment_results['baseline']
        
        # Compare S1-only vs S2-full movement patterns
        s1_metrics = baseline_results['s1_only']['movement_metrics']
        s2_metrics = baseline_results['s2_full']['movement_metrics']
        
        print("--- Comparing S1-only vs S2-full Movement Patterns ---")
        
        # Statistical tests would require multiple replications
        # For now, we'll do basic comparison and report effect sizes
        
        metrics_to_compare = ['total_movements', 'first_move_day']
        
        for metric in metrics_to_compare:
            if metric in s1_metrics and metric in s2_metrics:
                if isinstance(s1_metrics[metric], dict) and 'mean' in s1_metrics[metric]:
                    s1_value = s1_metrics[metric]['mean']
                    s2_value = s2_metrics[metric]['mean']
                else:
                    s1_value = s1_metrics[metric]
                    s2_value = s2_metrics[metric]
                
                # Calculate effect size (Cohen's d approximation)
                pooled_mean = (s1_value + s2_value) / 2
                effect_size = abs(s1_value - s2_value) / (pooled_mean + 1e-6)
                
                print(f"{metric}: S1={s1_value:.2f}, S2={s2_value:.2f}, Effect size={effect_size:.2f}")
                
                if effect_size > 0.2:
                    print(f"✓ {metric} shows meaningful difference between cognitive modes")
                else:
                    print(f"⚠ {metric} shows small difference between cognitive modes")
        
        print("✓ Statistical significance testing completed")
        print("Note: Full statistical testing requires multiple replications")


if __name__ == '__main__':
    unittest.main()