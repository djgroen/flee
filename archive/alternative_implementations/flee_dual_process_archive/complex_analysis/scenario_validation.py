"""
Scenario Validation Framework

This module provides comprehensive validation for experimental scenarios,
including hypothesis-specific checks to ensure scenarios are properly
configured for dual-process theory testing.
"""

from typing import Dict, List, Tuple, Optional, Any, Set
import os
import csv
import json
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .utils import CSVUtils, ValidationUtils, LoggingUtils


@dataclass
class ValidationResult:
    """Result of scenario validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class ScenarioValidator(ABC):
    """Base class for scenario validation."""
    
    def __init__(self):
        self.csv_utils = CSVUtils()
        self.validation_utils = ValidationUtils()
        self.logger = LoggingUtils().get_logger('ScenarioValidator')
    
    @abstractmethod
    def validate(self, scenario_dir: str) -> ValidationResult:
        """Validate a scenario directory."""
        pass


class GeneralScenarioValidator(ScenarioValidator):
    """General validation for all scenarios."""
    
    def validate(self, scenario_dir: str) -> ValidationResult:
        """
        Perform general validation checks on scenario.
        
        Args:
            scenario_dir: Path to scenario directory
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            # Check required files exist
            required_files = [
                'locations.csv',
                'routes.csv', 
                'conflicts.csv',
                'sim_period.csv'
            ]
            
            missing_files = []
            for file in required_files:
                file_path = os.path.join(scenario_dir, file)
                if not os.path.exists(file_path):
                    missing_files.append(file)
            
            if missing_files:
                errors.append(f"Missing required files: {missing_files}")
            
            # Validate file formats and content
            if not missing_files:
                # Validate locations.csv
                locations_result = self._validate_locations(scenario_dir)
                if not locations_result.is_valid:
                    errors.extend(locations_result.errors)
                    warnings.extend(locations_result.warnings)
                details['locations'] = locations_result.details
                
                # Validate routes.csv
                routes_result = self._validate_routes(scenario_dir)
                if not routes_result.is_valid:
                    errors.extend(routes_result.errors)
                    warnings.extend(routes_result.warnings)
                details['routes'] = routes_result.details
                
                # Validate conflicts.csv
                conflicts_result = self._validate_conflicts(scenario_dir)
                if not conflicts_result.is_valid:
                    errors.extend(conflicts_result.errors)
                    warnings.extend(conflicts_result.warnings)
                details['conflicts'] = conflicts_result.details
                
                # Validate sim_period.csv
                sim_period_result = self._validate_sim_period(scenario_dir)
                if not sim_period_result.is_valid:
                    errors.extend(sim_period_result.errors)
                    warnings.extend(sim_period_result.warnings)
                details['sim_period'] = sim_period_result.details
                
                # Cross-validate consistency between files
                consistency_result = self._validate_consistency(scenario_dir)
                if not consistency_result.is_valid:
                    errors.extend(consistency_result.errors)
                    warnings.extend(consistency_result.warnings)
                details['consistency'] = consistency_result.details
            
            is_valid = len(errors) == 0
            
            if is_valid:
                self.logger.info(f"Scenario validation passed: {scenario_dir}")
            else:
                self.logger.error(f"Scenario validation failed: {scenario_dir}, errors: {errors}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation exception: {str(e)}"],
                warnings=[],
                details={}
            )
    
    def _validate_locations(self, scenario_dir: str) -> ValidationResult:
        """Validate locations.csv file."""
        errors = []
        warnings = []
        details = {}
        
        try:
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            locations = self.csv_utils.read_locations_csv(locations_path)
            
            details['location_count'] = len(locations)
            details['location_names'] = [loc['name'] for loc in locations]
            
            # Check for required fields
            required_fields = ['name', 'location_type']
            for loc in locations:
                for field in required_fields:
                    if field not in loc or not loc[field]:
                        errors.append(f"Location missing required field '{field}': {loc}")
            
            # Check for duplicate names
            names = [loc['name'] for loc in locations]
            duplicates = [name for name in set(names) if names.count(name) > 1]
            if duplicates:
                errors.append(f"Duplicate location names: {duplicates}")
            
            # Check location types
            valid_types = ['town', 'camp', 'marker', 'conflict_zone']
            for loc in locations:
                if loc.get('location_type') not in valid_types:
                    warnings.append(f"Unknown location type '{loc.get('location_type')}' for {loc['name']}")
            
            # Check for at least one origin (town) and one destination (camp)
            towns = [loc for loc in locations if loc.get('location_type') == 'town']
            camps = [loc for loc in locations if loc.get('location_type') == 'camp']
            
            if not towns:
                errors.append("No origin locations (towns) found")
            if not camps:
                warnings.append("No destination locations (camps) found")
            
            details['towns'] = len(towns)
            details['camps'] = len(camps)
            
        except Exception as e:
            errors.append(f"Error validating locations.csv: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _validate_routes(self, scenario_dir: str) -> ValidationResult:
        """Validate routes.csv file."""
        errors = []
        warnings = []
        details = {}
        
        try:
            routes_path = os.path.join(scenario_dir, 'routes.csv')
            routes = self.csv_utils.read_routes_csv(routes_path)
            
            details['route_count'] = len(routes)
            
            # Load locations for reference
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            locations = self.csv_utils.read_locations_csv(locations_path)
            location_names = set(loc['name'] for loc in locations)
            
            # Check route validity
            for route in routes:
                # Check required fields
                if 'name1' not in route or 'name2' not in route:
                    errors.append(f"Route missing name1 or name2: {route}")
                    continue
                
                # Check locations exist
                if route['name1'] not in location_names:
                    errors.append(f"Route references unknown location: {route['name1']}")
                if route['name2'] not in location_names:
                    errors.append(f"Route references unknown location: {route['name2']}")
                
                # Check distance is valid
                try:
                    distance = float(route.get('distance', 0))
                    if distance <= 0:
                        warnings.append(f"Route has zero or negative distance: {route}")
                    elif distance > 1000:
                        warnings.append(f"Route has very large distance ({distance}km): {route}")
                except (ValueError, TypeError):
                    errors.append(f"Route has invalid distance: {route}")
            
            # Check network connectivity
            connectivity_result = self._check_network_connectivity(locations, routes)
            if not connectivity_result['is_connected']:
                errors.append("Network is not fully connected")
                details['isolated_locations'] = connectivity_result['isolated_locations']
            
            details['connectivity'] = connectivity_result
            
        except Exception as e:
            errors.append(f"Error validating routes.csv: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _validate_conflicts(self, scenario_dir: str) -> ValidationResult:
        """Validate conflicts.csv file."""
        errors = []
        warnings = []
        details = {}
        
        try:
            conflicts_path = os.path.join(scenario_dir, 'conflicts.csv')
            
            # Read conflicts in matrix format
            conflicts = {}
            location_names = []
            
            with open(conflicts_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                location_names = [name.strip() for name in header[1:]]  # Skip #Day column
                
                for row in reader:
                    if not row or not row[0].strip():
                        continue
                    
                    day = int(row[0])
                    day_conflicts = {}
                    
                    for i, intensity_str in enumerate(row[1:]):
                        if i < len(location_names):
                            location = location_names[i]
                            intensity = float(intensity_str.strip())
                            if intensity > 0:
                                day_conflicts[location] = intensity
                    
                    if day_conflicts:
                        conflicts[day] = day_conflicts
            
            details['conflict_days'] = len(conflicts)
            details['affected_locations'] = len(set().union(*[day_conflicts.keys() for day_conflicts in conflicts.values()]))
            
            # Load locations for reference
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            locations = self.csv_utils.read_locations_csv(locations_path)
            valid_location_names = set(loc['name'] for loc in locations)
            
            # Validate conflict data
            for day, day_conflicts in conflicts.items():
                # Check day is valid
                if day < 0:
                    errors.append(f"Negative conflict day: {day}")
                
                for location, intensity in day_conflicts.items():
                    # Check location exists
                    if location not in valid_location_names:
                        errors.append(f"Conflict references unknown location: {location}")
                    
                    # Check intensity range
                    if not (0 <= intensity <= 1):
                        errors.append(f"Invalid conflict intensity {intensity} at day {day}, location {location}")
            
            # Check for conflicts
            if not conflicts:
                warnings.append("No conflicts found in scenario")
            
            # Check temporal consistency
            if conflicts:
                days = sorted(conflicts.keys())
                details['first_conflict_day'] = days[0]
                details['last_conflict_day'] = days[-1]
                details['conflict_duration'] = days[-1] - days[0] + 1
                
                # Check for large gaps
                for i in range(1, len(days)):
                    gap = days[i] - days[i-1]
                    if gap > 30:
                        warnings.append(f"Large gap ({gap} days) between conflicts at days {days[i-1]} and {days[i]}")
            
        except Exception as e:
            errors.append(f"Error validating conflicts.csv: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _validate_sim_period(self, scenario_dir: str) -> ValidationResult:
        """Validate sim_period.csv file."""
        errors = []
        warnings = []
        details = {}
        
        try:
            sim_period_path = os.path.join(scenario_dir, 'sim_period.csv')
            
            with open(sim_period_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                data_row = next(reader)
                
                start_day = int(data_row[0])
                end_day = int(data_row[1])
                
                details['start_day'] = start_day
                details['end_day'] = end_day
                details['duration'] = end_day - start_day + 1
                
                # Validate period
                if start_day < 0:
                    errors.append(f"Negative start day: {start_day}")
                
                if end_day <= start_day:
                    errors.append(f"End day ({end_day}) must be greater than start day ({start_day})")
                
                duration = end_day - start_day + 1
                if duration < 30:
                    warnings.append(f"Very short simulation period: {duration} days")
                elif duration > 365:
                    warnings.append(f"Very long simulation period: {duration} days")
        
        except Exception as e:
            errors.append(f"Error validating sim_period.csv: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _validate_consistency(self, scenario_dir: str) -> ValidationResult:
        """Validate consistency between different files."""
        errors = []
        warnings = []
        details = {}
        
        try:
            # Load all files
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            conflicts_path = os.path.join(scenario_dir, 'conflicts.csv')
            sim_period_path = os.path.join(scenario_dir, 'sim_period.csv')
            
            locations = self.csv_utils.read_locations_csv(locations_path)
            location_names = set(loc['name'] for loc in locations)
            
            # Read sim period
            with open(sim_period_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                data_row = next(reader)
                start_day = int(data_row[0])
                end_day = int(data_row[1])
            
            # Read conflicts
            conflicts = {}
            with open(conflicts_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                conflict_locations = [name.strip() for name in header[1:]]
                
                for row in reader:
                    if not row or not row[0].strip():
                        continue
                    day = int(row[0])
                    conflicts[day] = day
            
            # Check conflicts are within simulation period
            conflict_days = list(conflicts.keys())
            if conflict_days:
                first_conflict = min(conflict_days)
                last_conflict = max(conflict_days)
                
                if first_conflict < start_day:
                    errors.append(f"Conflicts start before simulation period: {first_conflict} < {start_day}")
                
                if last_conflict > end_day:
                    warnings.append(f"Conflicts extend beyond simulation period: {last_conflict} > {end_day}")
            
            # Check conflict locations exist in topology
            unknown_locations = set(conflict_locations) - location_names
            if unknown_locations:
                errors.append(f"Conflicts reference unknown locations: {unknown_locations}")
            
            details['consistency_checks'] = {
                'locations_count': len(location_names),
                'conflict_locations_count': len(conflict_locations),
                'sim_period': (start_day, end_day),
                'conflict_period': (min(conflict_days), max(conflict_days)) if conflict_days else None
            }
            
        except Exception as e:
            errors.append(f"Error validating consistency: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _check_network_connectivity(self, locations: List[Dict], routes: List[Dict]) -> Dict[str, Any]:
        """Check if the network is fully connected."""
        location_names = [loc['name'] for loc in locations]
        
        # Build adjacency list
        graph = {name: [] for name in location_names}
        for route in routes:
            name1 = route.get('name1')
            name2 = route.get('name2')
            if name1 in graph and name2 in graph:
                graph[name1].append(name2)
                graph[name2].append(name1)
        
        # Find connected components using DFS
        visited = set()
        components = []
        
        def dfs(node, component):
            if node in visited:
                return
            visited.add(node)
            component.append(node)
            for neighbor in graph[node]:
                dfs(neighbor, component)
        
        for location in location_names:
            if location not in visited:
                component = []
                dfs(location, component)
                components.append(component)
        
        is_connected = len(components) <= 1
        isolated_locations = []
        
        if not is_connected:
            # Find isolated locations (components with size 1)
            for component in components:
                if len(component) == 1:
                    isolated_locations.extend(component)
        
        return {
            'is_connected': is_connected,
            'component_count': len(components),
            'components': components,
            'isolated_locations': isolated_locations
        }


class HypothesisSpecificValidator(ScenarioValidator):
    """Hypothesis-specific scenario validation."""
    
    def __init__(self, hypothesis: str):
        super().__init__()
        self.hypothesis = hypothesis
        
        # Map hypothesis to validation methods
        self.validation_methods = {
            'H1': self._validate_h1_scenario,
            'H2': self._validate_h2_scenario,
            'H3': self._validate_h3_scenario,
            'H4': self._validate_h4_scenario
        }
    
    def validate(self, scenario_dir: str) -> ValidationResult:
        """
        Perform hypothesis-specific validation.
        
        Args:
            scenario_dir: Path to scenario directory
            
        Returns:
            ValidationResult with validation status and details
        """
        if self.hypothesis not in self.validation_methods:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown hypothesis: {self.hypothesis}"],
                warnings=[],
                details={}
            )
        
        return self.validation_methods[self.hypothesis](scenario_dir)
    
    def _validate_h1_scenario(self, scenario_dir: str) -> ValidationResult:
        """Validate H1 (Speed vs Optimality) scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            # Check multiple destinations exist
            multiple_dest_result = self.check_multiple_destinations_exist(scenario_dir)
            if not multiple_dest_result.is_valid:
                errors.extend(multiple_dest_result.errors)
                warnings.extend(multiple_dest_result.warnings)
            details['multiple_destinations'] = multiple_dest_result.details
            
            # Check for trade-offs between destinations
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            locations = self.csv_utils.read_locations_csv(locations_path)
            
            camps = [loc for loc in locations if loc.get('location_type') == 'camp']
            if len(camps) >= 2:
                # Check for capacity/distance trade-offs
                capacities = []
                for camp in camps:
                    try:
                        capacity = int(camp.get('population/capacity', 0))
                        capacities.append(capacity)
                    except (ValueError, TypeError):
                        pass
                
                if len(set(capacities)) > 1:
                    details['capacity_variation'] = True
                else:
                    warnings.append("H1 scenarios should have camps with different capacities for trade-off testing")
            
            # Check for gradual or cascading conflicts (allows planning time)
            conflicts_path = os.path.join(scenario_dir, 'conflicts.csv')
            if os.path.exists(conflicts_path):
                # Simple check for conflict pattern
                with open(conflicts_path, 'r') as f:
                    content = f.read()
                    if 'gradual' in content.lower() or len(content.split('\n')) > 5:
                        details['allows_planning'] = True
                    else:
                        warnings.append("H1 scenarios should allow time for planning (gradual conflicts)")
            
        except Exception as e:
            errors.append(f"H1 validation error: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _validate_h2_scenario(self, scenario_dir: str) -> ValidationResult:
        """Validate H2 (Social Connectivity) scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            # Check information asymmetry exists
            info_asymmetry_result = self.check_information_asymmetry(scenario_dir)
            if not info_asymmetry_result.is_valid:
                errors.extend(info_asymmetry_result.errors)
                warnings.extend(info_asymmetry_result.warnings)
            details['information_asymmetry'] = info_asymmetry_result.details
            
            # Check for hidden/obvious destinations
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            locations = self.csv_utils.read_locations_csv(locations_path)
            
            # Look for visibility indicators
            has_visibility_info = any('visibility' in str(loc) for loc in locations)
            has_hidden_info = any('hidden' in str(loc).lower() for loc in locations)
            
            if has_visibility_info or has_hidden_info:
                details['has_visibility_mechanics'] = True
            else:
                warnings.append("H2 scenarios should have visibility/information mechanics")
            
            # Check for different agent types in population config
            pop_config_path = os.path.join(scenario_dir, 'population_config.json')
            if os.path.exists(pop_config_path):
                with open(pop_config_path, 'r') as f:
                    pop_config = json.load(f)
                
                cognitive_comp = pop_config.get('cognitive_composition', {})
                if 'connected' in str(cognitive_comp) and 'isolated' in str(cognitive_comp):
                    details['has_connectivity_variation'] = True
                else:
                    warnings.append("H2 scenarios should have connected vs isolated agent types")
            
        except Exception as e:
            errors.append(f"H2 validation error: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _validate_h3_scenario(self, scenario_dir: str) -> ValidationResult:
        """Validate H3 (Dimensionless Parameters) scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            # Check parameter range is sufficient
            param_range_result = self.check_parameter_range_sufficient(scenario_dir)
            if not param_range_result.is_valid:
                errors.extend(param_range_result.errors)
                warnings.extend(param_range_result.warnings)
            details['parameter_range'] = param_range_result.details
            
            # Check for parameter sweep configuration
            metadata_path = os.path.join(scenario_dir, 'scenario_metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                template = metadata.get('template', {})
                conflict_params = template.get('conflict', {}).get('parameters', {})
                
                # Look for parameter sweep indicators
                has_grid_search = conflict_params.get('grid_search', False)
                has_pressure_range = 'cognitive_pressure_range' in conflict_params
                
                if has_grid_search or has_pressure_range:
                    details['has_parameter_sweep'] = True
                else:
                    warnings.append("H3 scenarios should include parameter sweep configuration")
            
            # Check for dimensionless parameter calculation
            if 'cognitive_pressure' in str(details):
                details['has_dimensionless_params'] = True
            else:
                warnings.append("H3 scenarios should calculate dimensionless parameters (cognitive_pressure)")
            
        except Exception as e:
            errors.append(f"H3 validation error: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _validate_h4_scenario(self, scenario_dir: str) -> ValidationResult:
        """Validate H4 (Population Diversity) scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            # Check population diversity exists
            diversity_result = self.check_population_diversity(scenario_dir)
            if not diversity_result.is_valid:
                errors.extend(diversity_result.errors)
                warnings.extend(diversity_result.warnings)
            details['population_diversity'] = diversity_result.details
            
            # Check for dynamic events or shocks
            metadata_path = os.path.join(scenario_dir, 'scenario_metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                template = metadata.get('template', {})
                network_params = template.get('network', {}).get('parameters', {})
                
                # Look for dynamic events
                has_dynamic_events = 'dynamic_events' in network_params
                has_shock_events = template.get('conflict', {}).get('parameters', {}).get('shock_events', False)
                
                if has_dynamic_events or has_shock_events:
                    details['has_dynamic_events'] = True
                else:
                    warnings.append("H4 scenarios should include dynamic events or shocks")
            
            # Check for scout/follower behavior tracking
            pop_config_path = os.path.join(scenario_dir, 'population_config.json')
            if os.path.exists(pop_config_path):
                with open(pop_config_path, 'r') as f:
                    pop_config = json.load(f)
                
                cognitive_comp = pop_config.get('cognitive_composition', {})
                has_scouts = 'scout' in str(cognitive_comp).lower()
                has_followers = 'follower' in str(cognitive_comp).lower()
                
                if has_scouts and has_followers:
                    details['has_scout_follower'] = True
                else:
                    warnings.append("H4 scenarios should distinguish scout vs follower behavior")
            
        except Exception as e:
            errors.append(f"H4 validation error: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def check_multiple_destinations_exist(self, scenario_dir: str) -> ValidationResult:
        """Check that multiple destination options exist for H1 scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            locations = self.csv_utils.read_locations_csv(locations_path)
            
            # Count camps (destinations)
            camps = [loc for loc in locations if loc.get('location_type') == 'camp']
            camp_count = len(camps)
            
            details['camp_count'] = camp_count
            details['camp_names'] = [camp['name'] for camp in camps]
            
            if camp_count < 2:
                errors.append(f"H1 scenarios require multiple destinations, found only {camp_count}")
            elif camp_count < 3:
                warnings.append("H1 scenarios work best with 3+ destination options")
            
            # Check for different characteristics (capacity, distance)
            if camp_count >= 2:
                capacities = []
                for camp in camps:
                    try:
                        capacity = int(camp.get('population/capacity', 0))
                        capacities.append(capacity)
                    except (ValueError, TypeError):
                        capacities.append(0)
                
                if len(set(capacities)) > 1:
                    details['has_capacity_variation'] = True
                else:
                    warnings.append("Camps should have different capacities for meaningful choice")
            
        except Exception as e:
            errors.append(f"Error checking multiple destinations: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def check_information_asymmetry(self, scenario_dir: str) -> ValidationResult:
        """Check that information asymmetry exists for H2 scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            locations_path = os.path.join(scenario_dir, 'locations.csv')
            locations = self.csv_utils.read_locations_csv(locations_path)
            
            # Look for visibility or information access indicators
            has_visibility = False
            has_hidden_locations = False
            
            for loc in locations:
                loc_str = str(loc).lower()
                if 'visibility' in loc_str or 'hidden' in loc_str:
                    has_visibility = True
                if 'hidden' in loc_str or 'requires_social' in loc_str:
                    has_hidden_locations = True
            
            details['has_visibility_mechanics'] = has_visibility
            details['has_hidden_locations'] = has_hidden_locations
            
            if not (has_visibility or has_hidden_locations):
                warnings.append("H2 scenarios should have information asymmetry (hidden/visible locations)")
            
            # Check population configuration for different agent types
            pop_config_path = os.path.join(scenario_dir, 'population_config.json')
            if os.path.exists(pop_config_path):
                with open(pop_config_path, 'r') as f:
                    pop_config = json.load(f)
                
                cognitive_comp = pop_config.get('cognitive_composition', {})
                comp_str = str(cognitive_comp).lower()
                
                has_connected = 'connected' in comp_str
                has_isolated = 'isolated' in comp_str
                
                details['has_connected_agents'] = has_connected
                details['has_isolated_agents'] = has_isolated
                
                if not (has_connected and has_isolated):
                    warnings.append("H2 scenarios should have both connected and isolated agent types")
            
        except Exception as e:
            errors.append(f"Error checking information asymmetry: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def check_parameter_range_sufficient(self, scenario_dir: str) -> ValidationResult:
        """Check that parameter ranges are sufficient for H3 scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            metadata_path = os.path.join(scenario_dir, 'scenario_metadata.json')
            if not os.path.exists(metadata_path):
                warnings.append("No metadata file found for parameter range validation")
                return ValidationResult(True, [], warnings, details)
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            template = metadata.get('template', {})
            conflict_params = template.get('conflict', {}).get('parameters', {})
            
            # Check for parameter ranges
            required_ranges = [
                'conflict_intensity_range',
                'recovery_period_range', 
                'connectivity_rate_range'
            ]
            
            found_ranges = []
            for param_range in required_ranges:
                if param_range in conflict_params:
                    found_ranges.append(param_range)
                    
                    # Validate range values
                    range_values = conflict_params[param_range]
                    if isinstance(range_values, list) and len(range_values) == 2:
                        min_val, max_val = range_values
                        if min_val >= max_val:
                            errors.append(f"Invalid parameter range {param_range}: min >= max")
                        
                        # Check range coverage
                        range_span = max_val - min_val
                        if param_range == 'conflict_intensity_range' and range_span < 0.5:
                            warnings.append(f"Small conflict intensity range: {range_span}")
                        elif param_range == 'connectivity_rate_range' and range_span < 0.5:
                            warnings.append(f"Small connectivity rate range: {range_span}")
                        elif param_range == 'recovery_period_range' and range_span < 20:
                            warnings.append(f"Small recovery period range: {range_span}")
            
            details['found_parameter_ranges'] = found_ranges
            details['missing_parameter_ranges'] = [r for r in required_ranges if r not in found_ranges]
            
            if len(found_ranges) < 2:
                warnings.append("H3 scenarios should vary multiple parameters for dimensionless analysis")
            
            # Check for cognitive pressure calculation
            has_pressure_range = 'cognitive_pressure_range' in conflict_params
            details['has_cognitive_pressure'] = has_pressure_range
            
            if not has_pressure_range and len(found_ranges) >= 2:
                warnings.append("H3 scenarios should calculate cognitive_pressure from parameter combinations")
            
        except Exception as e:
            errors.append(f"Error checking parameter ranges: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def check_population_diversity(self, scenario_dir: str) -> ValidationResult:
        """Check that population diversity exists for H4 scenarios."""
        errors = []
        warnings = []
        details = {}
        
        try:
            pop_config_path = os.path.join(scenario_dir, 'population_config.json')
            if not os.path.exists(pop_config_path):
                errors.append("No population configuration found for H4 scenario")
                return ValidationResult(False, errors, warnings, details)
            
            with open(pop_config_path, 'r') as f:
                pop_config = json.load(f)
            
            cognitive_comp = pop_config.get('cognitive_composition', {})
            
            # Count different cognitive types
            cognitive_types = list(cognitive_comp.keys())
            type_count = len(cognitive_types)
            
            details['cognitive_types'] = cognitive_types
            details['type_count'] = type_count
            
            if type_count < 2:
                errors.append(f"H4 scenarios require population diversity, found only {type_count} cognitive type(s)")
            elif type_count < 3:
                warnings.append("H4 scenarios work best with 3+ cognitive types")
            
            # Check for balanced vs extreme compositions
            if cognitive_comp:
                proportions = list(cognitive_comp.values())
                max_proportion = max(proportions)
                min_proportion = min(proportions)
                
                details['max_proportion'] = max_proportion
                details['min_proportion'] = min_proportion
                
                if max_proportion > 0.8:
                    warnings.append(f"Very unbalanced population: {max_proportion:.1%} of one type")
                
                if min_proportion < 0.1 and type_count > 2:
                    warnings.append(f"Very small minority type: {min_proportion:.1%}")
            
            # Check for specific H4 types (scouts, followers, etc.)
            comp_str = str(cognitive_comp).lower()
            has_scouts = 'scout' in comp_str
            has_followers = 'follower' in comp_str
            has_pure_types = 'pure_s1' in comp_str or 'pure_s2' in comp_str
            has_mixed_types = 'balanced' in comp_str or 'realistic' in comp_str
            
            details['has_scouts'] = has_scouts
            details['has_followers'] = has_followers
            details['has_pure_types'] = has_pure_types
            details['has_mixed_types'] = has_mixed_types
            
            if not (has_scouts or has_pure_types):
                warnings.append("H4 scenarios should include distinct behavioral types (scouts, pure S1/S2)")
            
        except Exception as e:
            errors.append(f"Error checking population diversity: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )


def validate_scenario(scenario_dir: str, hypothesis: str = None) -> ValidationResult:
    """
    Validate a complete scenario directory.
    
    Args:
        scenario_dir: Path to scenario directory
        hypothesis: Optional hypothesis identifier for specific validation
        
    Returns:
        ValidationResult with combined validation results
    """
    # Perform general validation
    general_validator = GeneralScenarioValidator()
    general_result = general_validator.validate(scenario_dir)
    
    # Perform hypothesis-specific validation if specified
    hypothesis_result = None
    if hypothesis:
        hypothesis_validator = HypothesisSpecificValidator(hypothesis)
        hypothesis_result = hypothesis_validator.validate(scenario_dir)
    
    # Combine results
    combined_errors = general_result.errors.copy()
    combined_warnings = general_result.warnings.copy()
    combined_details = {'general': general_result.details}
    
    if hypothesis_result:
        combined_errors.extend(hypothesis_result.errors)
        combined_warnings.extend(hypothesis_result.warnings)
        combined_details[f'{hypothesis}_specific'] = hypothesis_result.details
    
    is_valid = len(combined_errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=combined_errors,
        warnings=combined_warnings,
        details=combined_details
    )