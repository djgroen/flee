"""
Comprehensive Scenario Generator

This module provides a unified interface for generating all types of scenarios
needed for dual-process theory testing, including hypothesis-specific scenarios
for H1, H2, H3, and H4.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional, Union
import os
import csv
import json
import math
import random
from dataclasses import dataclass
from .utils import CSVUtils, ValidationUtils, LoggingUtils
from .topology_generator import (
    LinearTopologyGenerator, 
    StarTopologyGenerator, 
    TreeTopologyGenerator, 
    GridTopologyGenerator
)
from .scenario_generator import (
    SpikeConflictGenerator, 
    GradualConflictGenerator,
    CascadingConflictGenerator,
    OscillatingConflictGenerator
)


@dataclass
class NetworkConfig:
    """Configuration for network topology generation."""
    topology_type: str  # 'linear', 'star', 'tree', 'grid', 'custom'
    parameters: Dict[str, Any]
    output_dir: str


@dataclass
class ConflictConfig:
    """Configuration for conflict scenario generation."""
    scenario_type: str  # 'spike', 'gradual', 'cascading', 'oscillating', 'custom'
    parameters: Dict[str, Any]
    timeline: Dict[int, Dict[str, float]]  # Optional pre-defined timeline


@dataclass
class PopulationConfig:
    """Configuration for population distribution."""
    total_population: int
    distribution_type: str  # 'uniform', 'concentrated', 'realistic', 'custom'
    cognitive_composition: Dict[str, float]  # {'s1_only': 0.3, 's2_connected': 0.4, ...}
    parameters: Dict[str, Any]


class ScenarioGenerator:
    """
    Comprehensive scenario generator for dual-process theory experiments.
    
    This class provides a unified interface for generating complete experimental
    scenarios including network topologies, conflict patterns, and population
    configurations for all hypothesis testing (H1, H2, H3, H4).
    """
    
    def __init__(self, base_output_dir: str = "scenarios"):
        """
        Initialize the comprehensive scenario generator.
        
        Args:
            base_output_dir: Base directory for scenario outputs
        """
        self.base_output_dir = base_output_dir
        self.csv_utils = CSVUtils()
        self.validation_utils = ValidationUtils()
        self.logger = LoggingUtils().get_logger('ScenarioGenerator')
        
        # Initialize component generators (will be created per-request with proper config)
        self.conflict_generators = {
            'spike': SpikeConflictGenerator,
            'gradual': GradualConflictGenerator,
            'cascading': CascadingConflictGenerator,
            'oscillating': OscillatingConflictGenerator
        }
        
        # Hypothesis-specific scenario templates
        self.hypothesis_templates = {
            'H1': self._get_h1_templates(),
            'H2': self._get_h2_templates(),
            'H3': self._get_h3_templates(),
            'H4': self._get_h4_templates()
        }
    
    def generate_network(self, config: NetworkConfig) -> Tuple[str, str]:
        """
        Generate network topology based on configuration.
        
        Args:
            config: Network configuration specifying topology type and parameters
            
        Returns:
            Tuple of (locations_csv_path, routes_csv_path)
            
        Raises:
            ValueError: If topology type is not supported
            RuntimeError: If network generation fails
        """
        try:
            os.makedirs(config.output_dir, exist_ok=True)
            
            locations_path = os.path.join(config.output_dir, 'locations.csv')
            routes_path = os.path.join(config.output_dir, 'routes.csv')
            
            if config.topology_type == 'linear':
                generator = LinearTopologyGenerator({'output_dir': config.output_dir})
                locations_path, routes_path = generator.generate_linear(
                    n_nodes=config.parameters.get('n_nodes', 5),
                    segment_distance=config.parameters.get('segment_distance', 50.0),
                    start_pop=config.parameters.get('start_pop', 10000),
                    pop_decay=config.parameters.get('pop_decay', 0.8)
                )
            
            elif config.topology_type == 'star':
                generator = StarTopologyGenerator({'output_dir': config.output_dir})
                locations_path, routes_path = generator.generate_star(
                    n_camps=config.parameters.get('n_camps', 4),
                    hub_pop=config.parameters.get('hub_pop', 10000),
                    camp_capacity=config.parameters.get('camp_capacity', 5000),
                    radius=config.parameters.get('radius', 100.0)
                )
            
            elif config.topology_type == 'tree':
                generator = TreeTopologyGenerator({'output_dir': config.output_dir})
                locations_path, routes_path = generator.generate_tree(
                    branching_factor=config.parameters.get('branching_factor', 2),
                    depth=config.parameters.get('depth', 3),
                    root_pop=config.parameters.get('root_pop', 10000)
                )
            
            elif config.topology_type == 'grid':
                generator = GridTopologyGenerator({'output_dir': config.output_dir})
                locations_path, routes_path = generator.generate_grid(
                    rows=config.parameters.get('rows', 3),
                    cols=config.parameters.get('cols', 3),
                    cell_distance=config.parameters.get('cell_distance', 50.0),
                    pop_distribution=config.parameters.get('pop_distribution', 'uniform')
                )
            
            elif config.topology_type == 'custom':
                # Handle custom topology generation
                self._generate_custom_network(config)
            
            else:
                raise ValueError(f"Unsupported topology type: {config.topology_type}")
            
            # Validate generated network
            if not (os.path.exists(locations_path) and os.path.exists(routes_path)):
                raise RuntimeError("Network generation failed - output files not created")
            
            self.logger.info(f"Generated {config.topology_type} network topology in {config.output_dir}")
            return locations_path, routes_path
            
        except Exception as e:
            self.logger.error(f"Network generation failed: {e}")
            raise
    
    def generate_conflict_schedule(self, config: ConflictConfig, 
                                 locations_file: str) -> str:
        """
        Generate conflict schedule based on configuration.
        
        Args:
            config: Conflict configuration specifying scenario type and parameters
            locations_file: Path to locations.csv file for topology reference
            
        Returns:
            Path to generated conflicts.csv file
            
        Raises:
            ValueError: If scenario type is not supported
            RuntimeError: If conflict generation fails
        """
        try:
            if config.scenario_type in self.conflict_generators:
                generator_class = self.conflict_generators[config.scenario_type]
                generator = generator_class(locations_file)
                
                output_dir = os.path.dirname(locations_file)
                
                if config.scenario_type == 'spike':
                    conflicts_path = generator.generate_spike_conflict(
                        origin=config.parameters.get('origin', 'Origin'),
                        start_day=config.parameters.get('start_day', 0),
                        peak_intensity=config.parameters.get('peak_intensity', 1.0),
                        output_dir=output_dir
                    )
                
                elif config.scenario_type == 'gradual':
                    conflicts_path = generator.generate_gradual_conflict(
                        origin=config.parameters.get('origin', 'Origin'),
                        start_day=config.parameters.get('start_day', 0),
                        end_day=config.parameters.get('end_day', 30),
                        max_intensity=config.parameters.get('max_intensity', 1.0),
                        output_dir=output_dir
                    )
                
                elif config.scenario_type == 'cascading':
                    conflicts_path = generator.generate_cascading_conflict(
                        origin=config.parameters.get('origin', 'Origin'),
                        start_day=config.parameters.get('start_day', 0),
                        spread_rate=config.parameters.get('spread_rate', 0.2),
                        max_intensity=config.parameters.get('max_intensity', 1.0),
                        output_dir=output_dir
                    )
                
                elif config.scenario_type == 'oscillating':
                    conflicts_path = generator.generate_oscillating_conflict(
                        origin=config.parameters.get('origin', 'Origin'),
                        start_day=config.parameters.get('start_day', 0),
                        period=config.parameters.get('period', 14),
                        amplitude=config.parameters.get('amplitude', 0.8),
                        output_dir=output_dir
                    )
            
            elif config.scenario_type == 'custom':
                # Handle custom conflict timeline
                conflicts_path = self._generate_custom_conflicts(config, locations_file)
            
            else:
                raise ValueError(f"Unsupported scenario type: {config.scenario_type}")
            
            # Validate generated conflicts
            if not os.path.exists(conflicts_path):
                raise RuntimeError("Conflict generation failed - output file not created")
            
            self.logger.info(f"Generated {config.scenario_type} conflict scenario: {conflicts_path}")
            return conflicts_path
            
        except Exception as e:
            self.logger.error(f"Conflict generation failed: {e}")
            raise
    
    def generate_population(self, config: PopulationConfig, 
                          locations_file: str) -> str:
        """
        Generate population configuration based on specification.
        
        Args:
            config: Population configuration
            locations_file: Path to locations.csv file
            
        Returns:
            Path to generated population configuration file
        """
        try:
            # Load locations to understand network structure
            locations = self.csv_utils.read_locations_csv(locations_file)
            
            output_dir = os.path.dirname(locations_file)
            population_file = os.path.join(output_dir, 'population_config.json')
            
            # Generate population distribution
            population_data = {
                'total_population': config.total_population,
                'distribution_type': config.distribution_type,
                'cognitive_composition': config.cognitive_composition,
                'location_populations': {}
            }
            
            if config.distribution_type == 'uniform':
                # Distribute population uniformly across origin locations
                origin_locations = [loc for loc in locations if loc.get('location_type') == 'town']
                if not origin_locations:
                    origin_locations = [locations[0]]  # Fallback to first location
                
                pop_per_location = config.total_population // len(origin_locations)
                for loc in origin_locations:
                    population_data['location_populations'][loc['name']] = pop_per_location
            
            elif config.distribution_type == 'concentrated':
                # Concentrate population in single origin
                origin_name = config.parameters.get('origin', locations[0]['name'])
                population_data['location_populations'][origin_name] = config.total_population
            
            elif config.distribution_type == 'realistic':
                # Use realistic population distribution based on location types
                self._generate_realistic_population(population_data, locations, config)
            
            elif config.distribution_type == 'custom':
                # Use custom population distribution
                population_data['location_populations'] = config.parameters.get('distribution', {})
            
            # Save population configuration
            with open(population_file, 'w') as f:
                json.dump(population_data, f, indent=2)
            
            self.logger.info(f"Generated population configuration: {population_file}")
            return population_file
            
        except Exception as e:
            self.logger.error(f"Population generation failed: {e}")
            raise
    
    def generate_hypothesis_scenario(self, hypothesis: str, scenario_id: str, 
                                   parameters: Dict[str, Any] = None) -> str:
        """
        Generate complete scenario for specific hypothesis testing.
        
        Args:
            hypothesis: Hypothesis identifier ('H1', 'H2', 'H3', 'H4')
            scenario_id: Specific scenario within hypothesis
            parameters: Optional parameter overrides
            
        Returns:
            Path to generated scenario directory
            
        Raises:
            ValueError: If hypothesis or scenario_id is not supported
        """
        try:
            if hypothesis not in self.hypothesis_templates:
                raise ValueError(f"Unsupported hypothesis: {hypothesis}")
            
            templates = self.hypothesis_templates[hypothesis]
            if scenario_id not in templates:
                raise ValueError(f"Unsupported scenario {scenario_id} for {hypothesis}")
            
            template = templates[scenario_id].copy()
            if parameters:
                # Merge parameter overrides
                template = self._merge_parameters(template, parameters)
            
            # Create scenario directory
            scenario_dir = os.path.join(self.base_output_dir, hypothesis.lower(), scenario_id)
            os.makedirs(scenario_dir, exist_ok=True)
            
            # Generate network topology
            network_config = NetworkConfig(
                topology_type=template['network']['topology_type'],
                parameters=template['network']['parameters'],
                output_dir=scenario_dir
            )
            locations_path, routes_path = self.generate_network(network_config)
            
            # Generate conflict schedule
            conflict_config = ConflictConfig(
                scenario_type=template['conflict']['scenario_type'],
                parameters=template['conflict']['parameters'],
                timeline=template['conflict'].get('timeline', {})
            )
            conflicts_path = self.generate_conflict_schedule(conflict_config, locations_path)
            
            # Generate population configuration
            population_config = PopulationConfig(
                total_population=template['population']['total_population'],
                distribution_type=template['population']['distribution_type'],
                cognitive_composition=template['population']['cognitive_composition'],
                parameters=template['population']['parameters']
            )
            population_path = self.generate_population(population_config, locations_path)
            
            # Generate additional scenario-specific files
            self._generate_scenario_metadata(scenario_dir, hypothesis, scenario_id, template)
            
            # Generate simulation period file
            self._generate_sim_period(scenario_dir, template.get('sim_period', {'start': 0, 'end': 180}))
            
            self.logger.info(f"Generated complete {hypothesis} scenario {scenario_id} in {scenario_dir}")
            return scenario_dir
            
        except Exception as e:
            self.logger.error(f"Hypothesis scenario generation failed: {e}")
            raise
    
    def _get_h1_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get H1 (Speed vs Optimality) scenario templates."""
        return {
            'h1_1_multi_destination': {
                'network': {
                    'topology_type': 'custom',
                    'parameters': {
                        'locations': [
                            {'name': 'Origin', 'population': 10000, 'location_type': 'town'},
                            {'name': 'Hub', 'population': 0, 'location_type': 'town'},
                            {'name': 'Camp_A', 'population': 0, 'location_type': 'camp', 'capacity': 3000},
                            {'name': 'Camp_B', 'population': 0, 'location_type': 'camp', 'capacity': 5000},
                            {'name': 'Camp_C', 'population': 0, 'location_type': 'camp', 'capacity': 8000}
                        ],
                        'routes': [
                            {'name1': 'Origin', 'name2': 'Hub', 'distance': 25},
                            {'name1': 'Hub', 'name2': 'Camp_A', 'distance': 50},
                            {'name1': 'Hub', 'name2': 'Camp_B', 'distance': 75},
                            {'name1': 'Hub', 'name2': 'Camp_C', 'distance': 100}
                        ]
                    }
                },
                'conflict': {
                    'scenario_type': 'gradual',
                    'parameters': {
                        'origin': 'Origin',
                        'start_day': 0,
                        'end_day': 30,
                        'max_intensity': 1.0
                    }
                },
                'population': {
                    'total_population': 10000,
                    'distribution_type': 'concentrated',
                    'cognitive_composition': {
                        's1_only': 0.33,
                        's2_disconnected': 0.33,
                        's2_connected': 0.34
                    },
                    'parameters': {'origin': 'Origin'}
                },
                'sim_period': {'start': 0, 'end': 180}
            },
            'h1_2_time_pressure_cascade': {
                'network': {
                    'topology_type': 'linear',
                    'parameters': {
                        'n_nodes': 5,
                        'segment_distance': 50.0,
                        'start_pop': 8000,
                        'pop_decay': 0.8
                    }
                },
                'conflict': {
                    'scenario_type': 'cascading',
                    'parameters': {
                        'origin': 'Town_A',
                        'start_day': 0,
                        'spread_rate': 0.2,
                        'max_intensity': 1.0
                    }
                },
                'population': {
                    'total_population': 20000,
                    'distribution_type': 'uniform',
                    'cognitive_composition': {
                        's1_only': 0.4,
                        's2_connected': 0.6
                    },
                    'parameters': {}
                },
                'sim_period': {'start': 0, 'end': 120}
            }
        }
    
    def _get_h2_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get H2 (Social Connectivity) scenario templates."""
        return {
            'h2_1_hidden_information': {
                'network': {
                    'topology_type': 'custom',
                    'parameters': {
                        'locations': [
                            {'name': 'Origin', 'population': 15000, 'location_type': 'town'},
                            {'name': 'Obvious_Camp', 'population': 0, 'location_type': 'camp', 
                             'capacity': 3000, 'visibility': 'high'},
                            {'name': 'Hidden_Camp', 'population': 0, 'location_type': 'camp', 
                             'capacity': 8000, 'visibility': 'low', 'requires_social_info': True}
                        ],
                        'routes': [
                            {'name1': 'Origin', 'name2': 'Obvious_Camp', 'distance': 60},
                            {'name1': 'Origin', 'name2': 'Hidden_Camp', 'distance': 80}
                        ]
                    }
                },
                'conflict': {
                    'scenario_type': 'spike',
                    'parameters': {
                        'origin': 'Origin',
                        'start_day': 0,
                        'peak_intensity': 1.0
                    }
                },
                'population': {
                    'total_population': 15000,
                    'distribution_type': 'concentrated',
                    'cognitive_composition': {
                        's1_baseline': 0.25,
                        's2_isolated': 0.25,
                        's2_connected': 0.5
                    },
                    'parameters': {'origin': 'Origin'}
                },
                'sim_period': {'start': 0, 'end': 150}
            },
            'h2_2_dynamic_information': {
                'network': {
                    'topology_type': 'star',
                    'parameters': {
                        'n_camps': 4,
                        'hub_pop': 12000,
                        'camp_capacity': 4000,
                        'radius': 100.0
                    }
                },
                'conflict': {
                    'scenario_type': 'gradual',
                    'parameters': {
                        'origin': 'Hub',
                        'start_day': 0,
                        'end_day': 45,
                        'max_intensity': 0.9
                    }
                },
                'population': {
                    'total_population': 12000,
                    'distribution_type': 'concentrated',
                    'cognitive_composition': {
                        's2_connected': 0.7,
                        's2_isolated': 0.3
                    },
                    'parameters': {'origin': 'Hub'}
                },
                'sim_period': {'start': 0, 'end': 200}
            }
        }
    
    def _get_h3_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get H3 (Dimensionless Parameters) scenario templates."""
        return {
            'h3_1_parameter_grid': {
                'network': {
                    'topology_type': 'grid',
                    'parameters': {
                        'rows': 3,
                        'cols': 3,
                        'cell_distance': 75.0,
                        'pop_distribution': 'uniform'
                    }
                },
                'conflict': {
                    'scenario_type': 'custom',
                    'parameters': {
                        'grid_search': True,
                        'conflict_intensity_range': [0.1, 1.0],
                        'recovery_period_range': [5, 60],
                        'connectivity_rate_range': [0.0, 1.0]
                    }
                },
                'population': {
                    'total_population': 25000,
                    'distribution_type': 'uniform',
                    'cognitive_composition': {
                        's1_only': 0.3,
                        's2_connected': 0.7
                    },
                    'parameters': {}
                },
                'sim_period': {'start': 0, 'end': 180}
            },
            'h3_2_phase_transition': {
                'network': {
                    'topology_type': 'tree',
                    'parameters': {
                        'branching_factor': 3,
                        'depth': 3,
                        'root_pop': 20000
                    }
                },
                'conflict': {
                    'scenario_type': 'custom',
                    'parameters': {
                        'phase_transition': True,
                        'cognitive_pressure_range': [0.0, 2.0],
                        'n_scenarios': 50
                    }
                },
                'population': {
                    'total_population': 20000,
                    'distribution_type': 'concentrated',
                    'cognitive_composition': {
                        'dual_process': 1.0
                    },
                    'parameters': {}
                },
                'sim_period': {'start': 0, 'end': 150}
            }
        }
    
    def _get_h4_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get H4 (Population Diversity) scenario templates."""
        return {
            'h4_1_adaptive_shock': {
                'network': {
                    'topology_type': 'custom',
                    'parameters': {
                        'adaptive_network': True,
                        'dynamic_events': [
                            {'type': 'conflict', 'day': 0, 'location': 'Origin'},
                            {'type': 'route_closure', 'day': 30, 'route': 'Origin-Camp_A'},
                            {'type': 'camp_full', 'day': 60, 'location': 'Camp_B'},
                            {'type': 'new_camp', 'day': 90, 'location': 'Emergency_Camp'}
                        ]
                    }
                },
                'conflict': {
                    'scenario_type': 'custom',
                    'parameters': {
                        'dynamic_timeline': True,
                        'shock_events': True
                    }
                },
                'population': {
                    'total_population': 18000,
                    'distribution_type': 'concentrated',
                    'cognitive_composition': {
                        'pure_s1': 0.2,
                        'pure_s2': 0.2,
                        'balanced': 0.3,
                        'realistic': 0.3
                    },
                    'parameters': {'origin': 'Origin'}
                },
                'sim_period': {'start': 0, 'end': 200}
            },
            'h4_2_information_cascade': {
                'network': {
                    'topology_type': 'star',
                    'parameters': {
                        'n_camps': 6,
                        'hub_pop': 16000,
                        'camp_capacity': 3500,
                        'radius': 120.0
                    }
                },
                'conflict': {
                    'scenario_type': 'oscillating',
                    'parameters': {
                        'origin': 'Hub',
                        'start_day': 0,
                        'period': 21,
                        'amplitude': 0.8
                    }
                },
                'population': {
                    'total_population': 16000,
                    'distribution_type': 'concentrated',
                    'cognitive_composition': {
                        's1_scouts': 0.3,
                        's2_followers': 0.7
                    },
                    'parameters': {'origin': 'Hub'}
                },
                'sim_period': {'start': 0, 'end': 180}
            }
        }
    
    def _generate_custom_network(self, config: NetworkConfig) -> None:
        """Generate custom network topology from configuration."""
        locations = config.parameters.get('locations', [])
        routes = config.parameters.get('routes', [])
        
        locations_path = os.path.join(config.output_dir, 'locations.csv')
        routes_path = os.path.join(config.output_dir, 'routes.csv')
        
        # Write locations CSV
        with open(locations_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name', 'region', 'country', 'lat', 'lon', 'location_type', 
                           'conflict_date', 'population/capacity'])
            
            for i, loc in enumerate(locations):
                writer.writerow([
                    loc['name'],
                    'region1',
                    'country1',
                    f"{10.0 + i * 0.1:.1f}",  # Dummy coordinates
                    f"{20.0 + i * 0.1:.1f}",
                    loc.get('location_type', 'town'),
                    loc.get('conflict_date', '2023-01-01'),
                    loc.get('population', 0) if loc.get('location_type') == 'town' else loc.get('capacity', 5000)
                ])
        
        # Write routes CSV
        with open(routes_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#name1', 'name2', 'distance [km]', 'forced_redirection'])
            
            for route in routes:
                writer.writerow([
                    route['name1'],
                    route['name2'],
                    route['distance'],
                    route.get('forced_redirection', 0)
                ])
    
    def _generate_custom_conflicts(self, config: ConflictConfig, locations_file: str) -> str:
        """Generate custom conflict timeline."""
        output_dir = os.path.dirname(locations_file)
        conflicts_path = os.path.join(output_dir, 'conflicts.csv')
        
        if config.timeline:
            # Use pre-defined timeline
            self._write_conflicts_csv(config.timeline, conflicts_path)
        else:
            # Generate based on parameters
            # This would implement custom conflict generation logic
            # For now, create a simple default
            conflicts = {0: {'Origin': 1.0}}
            self._write_conflicts_csv(conflicts, conflicts_path)
        
        return conflicts_path
    
    def _write_conflicts_csv(self, conflicts: Dict[int, Dict[str, float]], filepath: str) -> None:
        """Write conflicts data to CSV file in Flee matrix format."""
        # Get all locations mentioned in conflicts
        all_locations = set()
        for day_conflicts in conflicts.values():
            all_locations.update(day_conflicts.keys())
        
        sorted_locations = sorted(all_locations)
        days = sorted(conflicts.keys())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            header = ['#Day'] + sorted_locations
            writer.writerow(header)
            
            # Write data rows
            for day in days:
                row = [day]
                day_conflicts = conflicts.get(day, {})
                
                for location in sorted_locations:
                    intensity = day_conflicts.get(location, 0.0)
                    row.append(intensity)
                
                writer.writerow(row)
    
    def _generate_realistic_population(self, population_data: Dict[str, Any], 
                                     locations: List[Dict[str, Any]], 
                                     config: PopulationConfig) -> None:
        """Generate realistic population distribution based on location types."""
        # Separate locations by type
        towns = [loc for loc in locations if loc.get('location_type') == 'town']
        camps = [loc for loc in locations if loc.get('location_type') == 'camp']
        
        # Distribute population among towns (origin locations)
        if towns:
            # Use population weights if available, otherwise uniform
            total_weight = sum(loc.get('population', 1000) for loc in towns)
            
            for town in towns:
                weight = town.get('population', 1000) / total_weight
                town_pop = int(config.total_population * weight)
                population_data['location_populations'][town['name']] = town_pop
        else:
            # Fallback: put all population in first location
            population_data['location_populations'][locations[0]['name']] = config.total_population
    
    def _generate_scenario_metadata(self, scenario_dir: str, hypothesis: str, 
                                  scenario_id: str, template: Dict[str, Any]) -> None:
        """Generate metadata file for the scenario."""
        metadata = {
            'hypothesis': hypothesis,
            'scenario_id': scenario_id,
            'description': f"{hypothesis} scenario {scenario_id}",
            'template': template,
            'generated_files': [
                'locations.csv',
                'routes.csv', 
                'conflicts.csv',
                'population_config.json',
                'sim_period.csv'
            ]
        }
        
        metadata_path = os.path.join(scenario_dir, 'scenario_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _generate_sim_period(self, scenario_dir: str, sim_period: Dict[str, int]) -> None:
        """Generate simulation period CSV file."""
        sim_period_path = os.path.join(scenario_dir, 'sim_period.csv')
        
        with open(sim_period_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#start', 'end'])
            writer.writerow([sim_period['start'], sim_period['end']])
    
    def _merge_parameters(self, template: Dict[str, Any], 
                         overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Merge parameter overrides into template."""
        import copy
        merged = copy.deepcopy(template)
        
        def deep_merge(base: Dict, override: Dict) -> Dict:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        return deep_merge(merged, overrides)