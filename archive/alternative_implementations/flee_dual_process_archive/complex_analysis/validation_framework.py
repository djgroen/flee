"""
Validation Framework for Experimental Setup

Provides comprehensive validation for experiment configurations, output validation,
and statistical validation for analysis results and significance tests.
"""

import os
import csv
import json
import yaml
import re
import math
from typing import Dict, List, Any, Tuple, Optional, Union
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

try:
    from .utils import CSVUtils, LoggingUtils
except ImportError:
    from utils import CSVUtils, LoggingUtils


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None, 
                 warnings: List[str] = None, details: Dict[str, Any] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.details = details or {}
    
    def add_error(self, error: str):
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the validation result."""
        self.warnings.append(warning)
    
    def add_detail(self, key: str, value: Any):
        """Add a detail to the validation result."""
        self.details[key] = value
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.details.update(other.details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'details': self.details
        }


class ExperimentConfigValidator:
    """Validator for experiment configurations."""
    
    def __init__(self):
        self.logger = LoggingUtils().get_logger('ExperimentConfigValidator')
        
        # Define valid values for configuration parameters
        self.valid_topology_types = ['linear', 'star', 'tree', 'grid']
        self.valid_scenario_types = ['spike', 'gradual', 'cascading', 'oscillating']
        self.valid_cognitive_modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
        self.valid_location_types = ['town', 'camp', 'conflict_zone']
    
    def validate_experiment_config(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete experiment configuration.
        
        Args:
            config: Experiment configuration dictionary
            
        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult()
        
        # Validate required fields
        required_fields = ['experiment_id', 'topology_type', 'scenario_type', 'cognitive_mode']
        for field in required_fields:
            if field not in config:
                result.add_error(f"Missing required field: {field}")
        
        if not result.is_valid:
            return result
        
        # Validate individual components
        result.merge(self._validate_experiment_id(config.get('experiment_id')))
        result.merge(self._validate_topology_config(config))
        result.merge(self._validate_scenario_config(config))
        result.merge(self._validate_cognitive_mode_config(config))
        result.merge(self._validate_simulation_params(config.get('simulation_params', {})))
        
        # Cross-validate components
        result.merge(self._cross_validate_config(config))
        
        return result
    
    def _validate_experiment_id(self, experiment_id: str) -> ValidationResult:
        """Validate experiment ID format and uniqueness."""
        result = ValidationResult()
        
        if not experiment_id:
            result.add_error("Experiment ID cannot be empty")
            return result
        
        # Check format (alphanumeric, underscores, hyphens)
        if not re.match(r'^[a-zA-Z0-9_-]+$', experiment_id):
            result.add_error("Experiment ID must contain only alphanumeric characters, underscores, and hyphens")
        
        # Check length
        if len(experiment_id) > 100:
            result.add_error("Experiment ID must be 100 characters or less")
        
        if len(experiment_id) < 3:
            result.add_warning("Experiment ID is very short, consider using a more descriptive name")
        
        return result
    
    def _validate_topology_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate topology configuration."""
        result = ValidationResult()
        
        topology_type = config.get('topology_type')
        topology_params = config.get('topology_params', {})
        
        if topology_type not in self.valid_topology_types:
            result.add_error(f"Invalid topology type: {topology_type}. Must be one of: {self.valid_topology_types}")
            return result
        
        # Validate topology-specific parameters
        if topology_type == 'linear':
            result.merge(self._validate_linear_topology_params(topology_params))
        elif topology_type == 'star':
            result.merge(self._validate_star_topology_params(topology_params))
        elif topology_type == 'tree':
            result.merge(self._validate_tree_topology_params(topology_params))
        elif topology_type == 'grid':
            result.merge(self._validate_grid_topology_params(topology_params))
        
        return result
    
    def _validate_linear_topology_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate linear topology parameters."""
        result = ValidationResult()
        
        # Required parameters
        required_params = ['n_nodes', 'segment_distance', 'start_pop', 'pop_decay']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required linear topology parameter: {param}")
        
        if not result.is_valid:
            return result
        
        # Validate parameter values
        n_nodes = params.get('n_nodes')
        if not isinstance(n_nodes, int) or n_nodes < 2:
            result.add_error("n_nodes must be an integer >= 2")
        elif n_nodes > 1000:
            result.add_warning("n_nodes is very large, may impact performance")
        
        segment_distance = params.get('segment_distance')
        if not isinstance(segment_distance, (int, float)) or segment_distance <= 0:
            result.add_error("segment_distance must be a positive number")
        
        start_pop = params.get('start_pop')
        if not isinstance(start_pop, int) or start_pop <= 0:
            result.add_error("start_pop must be a positive integer")
        
        pop_decay = params.get('pop_decay')
        if not isinstance(pop_decay, (int, float)) or not (0 <= pop_decay <= 1):
            result.add_error("pop_decay must be a number between 0 and 1")
        
        return result
    
    def _validate_star_topology_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate star topology parameters."""
        result = ValidationResult()
        
        required_params = ['n_camps', 'hub_pop', 'camp_capacity', 'radius']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required star topology parameter: {param}")
        
        if not result.is_valid:
            return result
        
        n_camps = params.get('n_camps')
        if not isinstance(n_camps, int) or n_camps < 1:
            result.add_error("n_camps must be an integer >= 1")
        elif n_camps > 100:
            result.add_warning("n_camps is very large, may impact performance")
        
        hub_pop = params.get('hub_pop')
        if not isinstance(hub_pop, int) or hub_pop <= 0:
            result.add_error("hub_pop must be a positive integer")
        
        camp_capacity = params.get('camp_capacity')
        if not isinstance(camp_capacity, int) or camp_capacity <= 0:
            result.add_error("camp_capacity must be a positive integer")
        
        radius = params.get('radius')
        if not isinstance(radius, (int, float)) or radius <= 0:
            result.add_error("radius must be a positive number")
        
        return result
    
    def _validate_tree_topology_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate tree topology parameters."""
        result = ValidationResult()
        
        required_params = ['branching_factor', 'depth', 'root_pop']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required tree topology parameter: {param}")
        
        if not result.is_valid:
            return result
        
        branching_factor = params.get('branching_factor')
        if not isinstance(branching_factor, int) or branching_factor < 2:
            result.add_error("branching_factor must be an integer >= 2")
        elif branching_factor > 10:
            result.add_warning("branching_factor is very large, may create too many nodes")
        
        depth = params.get('depth')
        if not isinstance(depth, int) or depth < 1:
            result.add_error("depth must be an integer >= 1")
        elif depth > 6:
            result.add_warning("depth is very large, may create too many nodes")
        
        # Check total nodes estimate
        if isinstance(branching_factor, int) and isinstance(depth, int):
            total_nodes = sum(branching_factor ** i for i in range(depth + 1))
            if total_nodes > 1000:
                result.add_warning(f"Tree topology will create {total_nodes} nodes, may impact performance")
        
        root_pop = params.get('root_pop')
        if not isinstance(root_pop, int) or root_pop <= 0:
            result.add_error("root_pop must be a positive integer")
        
        return result
    
    def _validate_grid_topology_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate grid topology parameters."""
        result = ValidationResult()
        
        required_params = ['rows', 'cols', 'cell_distance', 'pop_distribution']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required grid topology parameter: {param}")
        
        if not result.is_valid:
            return result
        
        rows = params.get('rows')
        if not isinstance(rows, int) or rows < 1:
            result.add_error("rows must be an integer >= 1")
        
        cols = params.get('cols')
        if not isinstance(cols, int) or cols < 1:
            result.add_error("cols must be an integer >= 1")
        
        # Check total nodes
        if isinstance(rows, int) and isinstance(cols, int):
            total_nodes = rows * cols
            if total_nodes > 1000:
                result.add_warning(f"Grid topology will create {total_nodes} nodes, may impact performance")
        
        cell_distance = params.get('cell_distance')
        if not isinstance(cell_distance, (int, float)) or cell_distance <= 0:
            result.add_error("cell_distance must be a positive number")
        
        pop_distribution = params.get('pop_distribution')
        valid_distributions = ['uniform', 'weighted', 'center_heavy', 'edge_heavy']
        if pop_distribution not in valid_distributions:
            result.add_error(f"pop_distribution must be one of: {valid_distributions}")
        
        return result
    
    def _validate_scenario_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate scenario configuration."""
        result = ValidationResult()
        
        scenario_type = config.get('scenario_type')
        scenario_params = config.get('scenario_params', {})
        
        if scenario_type not in self.valid_scenario_types:
            result.add_error(f"Invalid scenario type: {scenario_type}. Must be one of: {self.valid_scenario_types}")
            return result
        
        # Validate scenario-specific parameters
        if scenario_type == 'spike':
            result.merge(self._validate_spike_scenario_params(scenario_params))
        elif scenario_type == 'gradual':
            result.merge(self._validate_gradual_scenario_params(scenario_params))
        elif scenario_type == 'cascading':
            result.merge(self._validate_cascading_scenario_params(scenario_params))
        elif scenario_type == 'oscillating':
            result.merge(self._validate_oscillating_scenario_params(scenario_params))
        
        return result
    
    def _validate_spike_scenario_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate spike scenario parameters."""
        result = ValidationResult()
        
        required_params = ['origin', 'start_day', 'peak_intensity']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required spike scenario parameter: {param}")
        
        if not result.is_valid:
            return result
        
        start_day = params.get('start_day')
        if not isinstance(start_day, int) or start_day < 0:
            result.add_error("start_day must be a non-negative integer")
        
        peak_intensity = params.get('peak_intensity')
        if not isinstance(peak_intensity, (int, float)) or not (0 <= peak_intensity <= 1):
            result.add_error("peak_intensity must be a number between 0 and 1")
        
        return result
    
    def _validate_gradual_scenario_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate gradual scenario parameters."""
        result = ValidationResult()
        
        required_params = ['origin', 'start_day', 'end_day', 'max_intensity']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required gradual scenario parameter: {param}")
        
        if not result.is_valid:
            return result
        
        start_day = params.get('start_day')
        end_day = params.get('end_day')
        
        if not isinstance(start_day, int) or start_day < 0:
            result.add_error("start_day must be a non-negative integer")
        
        if not isinstance(end_day, int) or end_day < 0:
            result.add_error("end_day must be a non-negative integer")
        
        if isinstance(start_day, int) and isinstance(end_day, int) and end_day <= start_day:
            result.add_error("end_day must be greater than start_day")
        
        max_intensity = params.get('max_intensity')
        if not isinstance(max_intensity, (int, float)) or not (0 <= max_intensity <= 1):
            result.add_error("max_intensity must be a number between 0 and 1")
        
        return result
    
    def _validate_cascading_scenario_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate cascading scenario parameters."""
        result = ValidationResult()
        
        required_params = ['origin', 'start_day', 'spread_rate', 'max_intensity']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required cascading scenario parameter: {param}")
        
        if not result.is_valid:
            return result
        
        start_day = params.get('start_day')
        if not isinstance(start_day, int) or start_day < 0:
            result.add_error("start_day must be a non-negative integer")
        
        spread_rate = params.get('spread_rate')
        if not isinstance(spread_rate, (int, float)) or spread_rate <= 0:
            result.add_error("spread_rate must be a positive number")
        
        max_intensity = params.get('max_intensity')
        if not isinstance(max_intensity, (int, float)) or not (0 <= max_intensity <= 1):
            result.add_error("max_intensity must be a number between 0 and 1")
        
        return result
    
    def _validate_oscillating_scenario_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate oscillating scenario parameters."""
        result = ValidationResult()
        
        required_params = ['origin', 'start_day', 'period', 'amplitude']
        for param in required_params:
            if param not in params:
                result.add_error(f"Missing required oscillating scenario parameter: {param}")
        
        if not result.is_valid:
            return result
        
        start_day = params.get('start_day')
        if not isinstance(start_day, int) or start_day < 0:
            result.add_error("start_day must be a non-negative integer")
        
        period = params.get('period')
        if not isinstance(period, int) or period <= 0:
            result.add_error("period must be a positive integer")
        
        amplitude = params.get('amplitude')
        if not isinstance(amplitude, (int, float)) or not (0 <= amplitude <= 1):
            result.add_error("amplitude must be a number between 0 and 1")
        
        return result
    
    def _validate_cognitive_mode_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate cognitive mode configuration."""
        result = ValidationResult()
        
        cognitive_mode = config.get('cognitive_mode')
        if cognitive_mode not in self.valid_cognitive_modes:
            result.add_error(f"Invalid cognitive mode: {cognitive_mode}. Must be one of: {self.valid_cognitive_modes}")
        
        return result
    
    def _validate_simulation_params(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate simulation parameters."""
        result = ValidationResult()
        
        if not isinstance(params, dict):
            result.add_error("simulation_params must be a dictionary")
            return result
        
        # Validate move_rules if present
        if 'move_rules' in params:
            result.merge(self._validate_move_rules(params['move_rules']))
        
        # Validate log_levels if present
        if 'log_levels' in params:
            result.merge(self._validate_log_levels(params['log_levels']))
        
        # Validate spawn_rules if present
        if 'spawn_rules' in params:
            result.merge(self._validate_spawn_rules(params['spawn_rules']))
        
        return result
    
    def _validate_move_rules(self, move_rules: Dict[str, Any]) -> ValidationResult:
        """Validate move rules parameters."""
        result = ValidationResult()
        
        if not isinstance(move_rules, dict):
            result.add_error("move_rules must be a dictionary")
            return result
        
        # Validate specific parameters
        if 'awareness_level' in move_rules:
            awareness = move_rules['awareness_level']
            if not isinstance(awareness, int) or awareness not in [1, 2, 3]:
                result.add_error("awareness_level must be 1, 2, or 3")
        
        if 'weight_softening' in move_rules:
            weight = move_rules['weight_softening']
            if not isinstance(weight, (int, float)) or not (0 <= weight <= 1):
                result.add_error("weight_softening must be a number between 0 and 1")
        
        if 'average_social_connectivity' in move_rules:
            connectivity = move_rules['average_social_connectivity']
            if not isinstance(connectivity, (int, float)) or connectivity < 0:
                result.add_error("average_social_connectivity must be a non-negative number")
        
        if 'conflict_threshold' in move_rules:
            threshold = move_rules['conflict_threshold']
            if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                result.add_error("conflict_threshold must be a number between 0 and 1")
        
        if 'recovery_period_max' in move_rules:
            recovery = move_rules['recovery_period_max']
            if not isinstance(recovery, int) or recovery <= 0:
                result.add_error("recovery_period_max must be a positive integer")
        
        if 'two_system_decision_making' in move_rules:
            two_system = move_rules['two_system_decision_making']
            if not isinstance(two_system, bool):
                result.add_error("two_system_decision_making must be a boolean")
        
        return result
    
    def _validate_log_levels(self, log_levels: Dict[str, Any]) -> ValidationResult:
        """Validate log levels parameters."""
        result = ValidationResult()
        
        if not isinstance(log_levels, dict):
            result.add_error("log_levels must be a dictionary")
            return result
        
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for key, value in log_levels.items():
            if not isinstance(value, str) or value.upper() not in valid_log_levels:
                result.add_error(f"Invalid log level '{value}' for '{key}'. Must be one of: {valid_log_levels}")
        
        return result
    
    def _validate_spawn_rules(self, spawn_rules: Dict[str, Any]) -> ValidationResult:
        """Validate spawn rules parameters."""
        result = ValidationResult()
        
        if not isinstance(spawn_rules, dict):
            result.add_error("spawn_rules must be a dictionary")
            return result
        
        # Add specific spawn rules validation as needed
        # This is a placeholder for future spawn rules validation
        
        return result
    
    def _cross_validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Cross-validate configuration components for consistency."""
        result = ValidationResult()
        
        # Validate origin location exists in topology (if we have topology info)
        scenario_params = config.get('scenario_params', {})
        origin = scenario_params.get('origin')
        
        if origin:
            # This would require topology file to be generated first
            # For now, just validate that origin is a reasonable name
            if not isinstance(origin, str) or not origin.strip():
                result.add_error("Origin location must be a non-empty string")
        
        # Validate cognitive mode and simulation params consistency
        cognitive_mode = config.get('cognitive_mode')
        simulation_params = config.get('simulation_params', {})
        move_rules = simulation_params.get('move_rules', {})
        
        if cognitive_mode == 's1_only':
            if move_rules.get('two_system_decision_making', False):
                result.add_warning("S1-only mode should have two_system_decision_making=False")
        
        elif cognitive_mode in ['s2_disconnected', 's2_full', 'dual_process']:
            if not move_rules.get('two_system_decision_making', True):
                result.add_warning(f"{cognitive_mode} mode should have two_system_decision_making=True")
        
        return result


class FileFormatValidator:
    """Validator for file formats and content."""
    
    def __init__(self):
        self.logger = LoggingUtils().get_logger('FileFormatValidator')
        self.csv_utils = CSVUtils()
    
    def validate_locations_csv_format(self, filepath: str) -> ValidationResult:
        """Validate locations CSV file format."""
        result = ValidationResult()
        
        if not os.path.exists(filepath):
            result.add_error(f"Locations file not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Check header format
                expected_header = ['#name', 'region', 'country', 'lat', 'lon', 'location_type', 'conflict_date', 'pop/cap']
                if header != expected_header:
                    result.add_error(f"Invalid locations CSV header. Expected: {expected_header}, Got: {header}")
                    return result
                
                # Validate data rows
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    if len(row) != len(expected_header):
                        result.add_error(f"Row {row_num}: Expected {len(expected_header)} columns, got {len(row)}")
                        continue
                    
                    # Validate specific fields
                    name, region, country, lat, lon, location_type, conflict_date, pop_cap = row
                    
                    if not name.strip():
                        result.add_error(f"Row {row_num}: Location name cannot be empty")
                    
                    try:
                        lat_val = float(lat)
                        if not (-90 <= lat_val <= 90):
                            result.add_error(f"Row {row_num}: Invalid latitude {lat_val}")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid latitude format '{lat}'")
                    
                    try:
                        lon_val = float(lon)
                        if not (-180 <= lon_val <= 180):
                            result.add_error(f"Row {row_num}: Invalid longitude {lon_val}")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid longitude format '{lon}'")
                    
                    if location_type not in ['town', 'camp', 'conflict_zone']:
                        result.add_error(f"Row {row_num}: Invalid location_type '{location_type}'")
                    
                    try:
                        pop_cap_val = float(pop_cap)
                        if pop_cap_val < 0:
                            result.add_error(f"Row {row_num}: Population/capacity cannot be negative")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid population/capacity format '{pop_cap}'")
                    
                    row_count += 1
                
                result.add_detail('row_count', row_count)
                
        except Exception as e:
            result.add_error(f"Error reading locations CSV: {str(e)}")
        
        return result
    
    def validate_routes_csv_format(self, filepath: str) -> ValidationResult:
        """Validate routes CSV file format."""
        result = ValidationResult()
        
        if not os.path.exists(filepath):
            result.add_error(f"Routes file not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Check header format
                expected_header = ['#name1', 'name2', 'distance', 'forced_redirection']
                if header != expected_header:
                    result.add_error(f"Invalid routes CSV header. Expected: {expected_header}, Got: {header}")
                    return result
                
                # Validate data rows
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    if len(row) != len(expected_header):
                        result.add_error(f"Row {row_num}: Expected {len(expected_header)} columns, got {len(row)}")
                        continue
                    
                    name1, name2, distance, forced_redirection = row
                    
                    if not name1.strip():
                        result.add_error(f"Row {row_num}: name1 cannot be empty")
                    
                    if not name2.strip():
                        result.add_error(f"Row {row_num}: name2 cannot be empty")
                    
                    if name1 == name2:
                        result.add_error(f"Row {row_num}: Self-loop detected ({name1} -> {name2})")
                    
                    try:
                        distance_val = float(distance)
                        if distance_val <= 0:
                            result.add_error(f"Row {row_num}: Distance must be positive, got {distance_val}")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid distance format '{distance}'")
                    
                    try:
                        redirection_val = int(forced_redirection)
                        if redirection_val not in [0, 1]:
                            result.add_error(f"Row {row_num}: forced_redirection must be 0 or 1, got {redirection_val}")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid forced_redirection format '{forced_redirection}'")
                    
                    row_count += 1
                
                result.add_detail('row_count', row_count)
                
        except Exception as e:
            result.add_error(f"Error reading routes CSV: {str(e)}")
        
        return result
    
    def validate_conflicts_csv_format(self, filepath: str) -> ValidationResult:
        """Validate conflicts CSV file format."""
        result = ValidationResult()
        
        if not os.path.exists(filepath):
            result.add_error(f"Conflicts file not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Check header format
                if not header or not header[0].startswith('#Day'):
                    result.add_error("Conflicts CSV must start with '#Day' column")
                    return result
                
                location_names = header[1:]  # All columns after #Day are location names
                
                # Validate data rows
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    if len(row) != len(header):
                        result.add_error(f"Row {row_num}: Expected {len(header)} columns, got {len(row)}")
                        continue
                    
                    # Validate day
                    try:
                        day = int(row[0])
                        if day < 0:
                            result.add_error(f"Row {row_num}: Day cannot be negative")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid day format '{row[0]}'")
                        continue
                    
                    # Validate conflict intensities
                    for i, intensity_str in enumerate(row[1:], start=1):
                        try:
                            intensity = float(intensity_str)
                            if not (0 <= intensity <= 1):
                                result.add_error(f"Row {row_num}, Column {i}: Conflict intensity must be between 0 and 1, got {intensity}")
                        except ValueError:
                            result.add_error(f"Row {row_num}, Column {i}: Invalid intensity format '{intensity_str}'")
                    
                    row_count += 1
                
                result.add_detail('row_count', row_count)
                result.add_detail('location_count', len(location_names))
                
        except Exception as e:
            result.add_error(f"Error reading conflicts CSV: {str(e)}")
        
        return result
    
    def validate_flee_output_format(self, filepath: str) -> ValidationResult:
        """Validate Flee output file format."""
        result = ValidationResult()
        
        if not os.path.exists(filepath):
            result.add_error(f"Flee output file not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r') as f:
                first_line = f.readline().strip()
                
                # Check header format
                if not first_line.startswith('#day'):
                    result.add_error("Flee output must start with '#day' column")
                    return result
                
                # Read as CSV and validate structure
                f.seek(0)
                reader = csv.reader(f)
                header = next(reader)
                
                expected_columns = ['#day', 'location', 'refugees']
                for col in expected_columns:
                    if col not in header:
                        result.add_error(f"Missing required column: {col}")
                
                # Validate data rows (sample first few)
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    if row_num > 100:  # Only check first 100 rows for performance
                        break
                    
                    if len(row) < len(expected_columns):
                        result.add_error(f"Row {row_num}: Insufficient columns")
                        continue
                    
                    # Validate day
                    try:
                        day = int(row[0])
                        if day < 0:
                            result.add_error(f"Row {row_num}: Day cannot be negative")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid day format")
                    
                    # Validate refugees count
                    try:
                        refugees = int(row[2])
                        if refugees < 0:
                            result.add_error(f"Row {row_num}: Refugees count cannot be negative")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid refugees count format")
                    
                    row_count += 1
                
                result.add_detail('row_count', row_count)
                
        except Exception as e:
            result.add_error(f"Error reading Flee output: {str(e)}")
        
        return result
    
    def validate_cognitive_states_format(self, filepath: str) -> ValidationResult:
        """Validate cognitive states output file format."""
        result = ValidationResult()
        
        if not os.path.exists(filepath):
            result.add_error(f"Cognitive states file not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                expected_columns = ['#day', 'agent_id', 'cognitive_state', 'location']
                for col in expected_columns:
                    if col not in header:
                        result.add_error(f"Missing required column: {col}")
                
                # Validate data rows (sample)
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    if row_num > 100:  # Only check first 100 rows
                        break
                    
                    if len(row) < len(expected_columns):
                        result.add_error(f"Row {row_num}: Insufficient columns")
                        continue
                    
                    # Find column indices
                    day_idx = header.index('#day')
                    agent_idx = header.index('agent_id')
                    state_idx = header.index('cognitive_state')
                    
                    # Validate day
                    try:
                        day = int(row[day_idx])
                        if day < 0:
                            result.add_error(f"Row {row_num}: Day cannot be negative")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid day format")
                    
                    # Validate cognitive state
                    cognitive_state = row[state_idx]
                    if cognitive_state not in ['S1', 'S2']:
                        result.add_error(f"Row {row_num}: Invalid cognitive state '{cognitive_state}'")
                    
                    row_count += 1
                
                result.add_detail('row_count', row_count)
                
        except Exception as e:
            result.add_error(f"Error reading cognitive states file: {str(e)}")
        
        return result
    
    def validate_decision_log_format(self, filepath: str) -> ValidationResult:
        """Validate decision log output file format."""
        result = ValidationResult()
        
        if not os.path.exists(filepath):
            result.add_error(f"Decision log file not found: {filepath}")
            return result
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                expected_columns = ['#day', 'agent_id', 'decision_type', 'cognitive_state']
                for col in expected_columns:
                    if col not in header:
                        result.add_error(f"Missing required column: {col}")
                
                # Validate data rows (sample)
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    if row_num > 100:  # Only check first 100 rows
                        break
                    
                    if len(row) < len(expected_columns):
                        result.add_error(f"Row {row_num}: Insufficient columns")
                        continue
                    
                    # Find column indices
                    day_idx = header.index('#day')
                    decision_idx = header.index('decision_type')
                    state_idx = header.index('cognitive_state')
                    
                    # Validate day
                    try:
                        day = int(row[day_idx])
                        if day < 0:
                            result.add_error(f"Row {row_num}: Day cannot be negative")
                    except ValueError:
                        result.add_error(f"Row {row_num}: Invalid day format")
                    
                    # Validate decision type
                    decision_type = row[decision_idx]
                    if decision_type not in ['move', 'stay']:
                        result.add_error(f"Row {row_num}: Invalid decision type '{decision_type}'")
                    
                    # Validate cognitive state
                    cognitive_state = row[state_idx]
                    if cognitive_state not in ['S1', 'S2']:
                        result.add_error(f"Row {row_num}: Invalid cognitive state '{cognitive_state}'")
                    
                    row_count += 1
                
                result.add_detail('row_count', row_count)
                
        except Exception as e:
            result.add_error(f"Error reading decision log file: {str(e)}")
        
        return result


class StatisticalValidator:
    """Validator for statistical analysis results and significance tests."""
    
    def __init__(self):
        self.logger = LoggingUtils().get_logger('StatisticalValidator')
    
    def validate_statistical_test_results(self, test_results: Dict[str, Any]) -> ValidationResult:
        """Validate statistical test results."""
        result = ValidationResult()
        
        if not isinstance(test_results, dict):
            result.add_error("Statistical test results must be a dictionary")
            return result
        
        # Validate p-values
        if 'p_value' in test_results:
            p_value = test_results['p_value']
            if not isinstance(p_value, (int, float)):
                result.add_error("p_value must be a number")
            elif not (0 <= p_value <= 1):
                result.add_error(f"p_value must be between 0 and 1, got {p_value}")
            elif math.isnan(p_value):
                result.add_error("p_value cannot be NaN")
        
        # Validate test statistics
        if 'test_statistic' in test_results:
            test_stat = test_results['test_statistic']
            if not isinstance(test_stat, (int, float)):
                result.add_error("test_statistic must be a number")
            elif math.isnan(test_stat) or math.isinf(test_stat):
                result.add_error("test_statistic cannot be NaN or infinite")
        
        # Validate degrees of freedom
        if 'degrees_of_freedom' in test_results:
            df = test_results['degrees_of_freedom']
            if not isinstance(df, int) or df <= 0:
                result.add_error("degrees_of_freedom must be a positive integer")
        
        # Validate effect sizes
        if 'effect_size' in test_results:
            effect_size = test_results['effect_size']
            if not isinstance(effect_size, (int, float)):
                result.add_error("effect_size must be a number")
            elif math.isnan(effect_size) or math.isinf(effect_size):
                result.add_error("effect_size cannot be NaN or infinite")
        
        # Validate confidence intervals
        if 'confidence_interval' in test_results:
            ci = test_results['confidence_interval']
            if not isinstance(ci, (list, tuple)) or len(ci) != 2:
                result.add_error("confidence_interval must be a list/tuple of length 2")
            else:
                lower, upper = ci
                if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)):
                    result.add_error("confidence_interval bounds must be numbers")
                elif lower > upper:
                    result.add_error("confidence_interval lower bound must be <= upper bound")
                elif math.isnan(lower) or math.isnan(upper):
                    result.add_error("confidence_interval bounds cannot be NaN")
        
        return result
    
    def validate_multiple_comparison_corrections(self, corrections: Dict[str, Any]) -> ValidationResult:
        """Validate multiple comparison corrections."""
        result = ValidationResult()
        
        if not isinstance(corrections, dict):
            result.add_error("Multiple comparison corrections must be a dictionary")
            return result
        
        # Validate Bonferroni correction
        if 'bonferroni' in corrections:
            bonf = corrections['bonferroni']
            if 'corrected_alpha' in bonf:
                alpha = bonf['corrected_alpha']
                if not isinstance(alpha, (int, float)) or not (0 < alpha < 1):
                    result.add_error("Bonferroni corrected_alpha must be between 0 and 1")
        
        # Validate FDR correction
        if 'fdr_bh' in corrections:
            fdr = corrections['fdr_bh']
            if 'corrected_p_values' in fdr:
                p_values = fdr['corrected_p_values']
                if not isinstance(p_values, list):
                    result.add_error("FDR corrected_p_values must be a list")
                else:
                    for i, p in enumerate(p_values):
                        if not isinstance(p, (int, float)) or not (0 <= p <= 1):
                            result.add_error(f"FDR corrected p-value {i} must be between 0 and 1")
        
        return result
    
    def validate_effect_size_calculations(self, effect_sizes: Dict[str, Any]) -> ValidationResult:
        """Validate effect size calculations."""
        result = ValidationResult()
        
        if not isinstance(effect_sizes, dict):
            result.add_error("Effect sizes must be a dictionary")
            return result
        
        # Validate Cohen's d
        if 'cohens_d' in effect_sizes:
            cohens_d = effect_sizes['cohens_d']
            if not isinstance(cohens_d, (int, float)):
                result.add_error("Cohen's d must be a number")
            elif math.isnan(cohens_d) or math.isinf(cohens_d):
                result.add_error("Cohen's d cannot be NaN or infinite")
            elif abs(cohens_d) > 10:  # Sanity check
                result.add_warning(f"Cohen's d is very large: {cohens_d}")
        
        # Validate eta squared
        if 'eta_squared' in effect_sizes:
            eta_sq = effect_sizes['eta_squared']
            if not isinstance(eta_sq, (int, float)):
                result.add_error("Eta squared must be a number")
            elif not (0 <= eta_sq <= 1):
                result.add_error(f"Eta squared must be between 0 and 1, got {eta_sq}")
        
        # Validate Pearson correlation
        if 'pearson_r' in effect_sizes:
            r = effect_sizes['pearson_r']
            if not isinstance(r, (int, float)):
                result.add_error("Pearson r must be a number")
            elif not (-1 <= r <= 1):
                result.add_error(f"Pearson r must be between -1 and 1, got {r}")
        
        return result
    
    def validate_sample_size_adequacy(self, sample_sizes: Dict[str, int], 
                                    effect_size: float = 0.5, alpha: float = 0.05, 
                                    power: float = 0.8) -> ValidationResult:
        """Validate sample size adequacy for statistical tests."""
        result = ValidationResult()
        
        if not isinstance(sample_sizes, dict):
            result.add_error("Sample sizes must be a dictionary")
            return result
        
        for group_name, n in sample_sizes.items():
            if not isinstance(n, int) or n <= 0:
                result.add_error(f"Sample size for {group_name} must be a positive integer")
                continue
            
            # Basic power analysis for t-test (rough approximation)
            # For Cohen's d = 0.5, alpha = 0.05, power = 0.8, need ~64 per group
            min_n_rough = int(16 / (effect_size ** 2))  # Very rough approximation
            
            if n < min_n_rough:
                result.add_warning(f"Sample size for {group_name} ({n}) may be too small for adequate power")
            
            if n < 10:
                result.add_error(f"Sample size for {group_name} ({n}) is too small for reliable statistical tests")
        
        return result
    
    def validate_normality_assumptions(self, data: Dict[str, List[float]]) -> ValidationResult:
        """Validate normality assumptions for statistical tests."""
        result = ValidationResult()
        
        if not isinstance(data, dict):
            result.add_error("Data must be a dictionary")
            return result
        
        for group_name, values in data.items():
            if not isinstance(values, list) or len(values) == 0:
                result.add_error(f"Data for {group_name} must be a non-empty list")
                continue
            
            # Check for sufficient data points
            if len(values) < 3:
                result.add_error(f"Insufficient data points for {group_name} (need at least 3)")
                continue
            
            # Basic normality checks
            try:
                values_array = np.array(values)
                
                # Check for NaN or infinite values
                if np.any(np.isnan(values_array)) or np.any(np.isinf(values_array)):
                    result.add_error(f"Data for {group_name} contains NaN or infinite values")
                    continue
                
                # Shapiro-Wilk test for normality (if sample size is appropriate)
                if 3 <= len(values) <= 5000:
                    stat, p_value = stats.shapiro(values_array)
                    if p_value < 0.05:
                        result.add_warning(f"Data for {group_name} may not be normally distributed (Shapiro-Wilk p={p_value:.4f})")
                
                # Check for extreme outliers (beyond 3 standard deviations)
                if len(values) > 3:
                    mean_val = np.mean(values_array)
                    std_val = np.std(values_array)
                    if std_val > 0:
                        z_scores = np.abs((values_array - mean_val) / std_val)
                        extreme_outliers = np.sum(z_scores > 3)
                        if extreme_outliers > 0:
                            result.add_warning(f"Data for {group_name} has {extreme_outliers} extreme outliers")
                
            except Exception as e:
                result.add_error(f"Error validating normality for {group_name}: {str(e)}")
        
        return result


class ExperimentValidator:
    """Main validator that orchestrates all validation components."""
    
    def __init__(self):
        self.config_validator = ExperimentConfigValidator()
        self.file_validator = FileFormatValidator()
        self.stats_validator = StatisticalValidator()
        self.logger = LoggingUtils().get_logger('ExperimentValidator')
    
    def validate_experiment_setup(self, config: Dict[str, Any], 
                                input_files: Dict[str, str] = None) -> ValidationResult:
        """
        Comprehensive validation of experiment setup.
        
        Args:
            config: Experiment configuration dictionary
            input_files: Dictionary of input file paths (optional)
            
        Returns:
            ValidationResult with comprehensive validation status
        """
        result = ValidationResult()
        
        # Validate configuration
        config_result = self.config_validator.validate_experiment_config(config)
        result.merge(config_result)
        
        # Validate input files if provided
        if input_files:
            if 'locations' in input_files:
                locations_result = self.file_validator.validate_locations_csv_format(input_files['locations'])
                result.merge(locations_result)
            
            if 'routes' in input_files:
                routes_result = self.file_validator.validate_routes_csv_format(input_files['routes'])
                result.merge(routes_result)
            
            if 'conflicts' in input_files:
                conflicts_result = self.file_validator.validate_conflicts_csv_format(input_files['conflicts'])
                result.merge(conflicts_result)
        
        return result
    
    def validate_experiment_output(self, output_dir: str) -> ValidationResult:
        """
        Validate experiment output files and completeness.
        
        Args:
            output_dir: Directory containing experiment output files
            
        Returns:
            ValidationResult with output validation status
        """
        result = ValidationResult()
        
        if not os.path.exists(output_dir):
            result.add_error(f"Output directory not found: {output_dir}")
            return result
        
        # Check for required output files
        required_files = ['out.csv']
        optional_files = ['cognitive_states.out.0', 'decision_log.out.0']
        
        for filename in required_files:
            filepath = os.path.join(output_dir, filename)
            if not os.path.exists(filepath):
                result.add_error(f"Required output file missing: {filename}")
            else:
                # Validate file format
                if filename == 'out.csv':
                    file_result = self.file_validator.validate_flee_output_format(filepath)
                    result.merge(file_result)
        
        for filename in optional_files:
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                # Validate file format
                if filename.startswith('cognitive_states'):
                    file_result = self.file_validator.validate_cognitive_states_format(filepath)
                    result.merge(file_result)
                elif filename.startswith('decision_log'):
                    file_result = self.file_validator.validate_decision_log_format(filepath)
                    result.merge(file_result)
        
        return result
    
    def validate_analysis_results(self, analysis_results: Dict[str, Any]) -> ValidationResult:
        """
        Validate analysis results and statistical computations.
        
        Args:
            analysis_results: Dictionary containing analysis results
            
        Returns:
            ValidationResult with analysis validation status
        """
        result = ValidationResult()
        
        if not isinstance(analysis_results, dict):
            result.add_error("Analysis results must be a dictionary")
            return result
        
        # Validate statistical test results if present
        if 'statistical_tests' in analysis_results:
            stats_tests = analysis_results['statistical_tests']
            if isinstance(stats_tests, dict):
                for test_name, test_result in stats_tests.items():
                    test_validation = self.stats_validator.validate_statistical_test_results(test_result)
                    if not test_validation.is_valid:
                        result.add_error(f"Invalid statistical test result for {test_name}")
                        result.merge(test_validation)
        
        # Validate effect sizes if present
        if 'effect_sizes' in analysis_results:
            effect_sizes = analysis_results['effect_sizes']
            effect_validation = self.stats_validator.validate_effect_size_calculations(effect_sizes)
            result.merge(effect_validation)
        
        # Validate multiple comparison corrections if present
        if 'multiple_comparisons' in analysis_results:
            corrections = analysis_results['multiple_comparisons']
            correction_validation = self.stats_validator.validate_multiple_comparison_corrections(corrections)
            result.merge(correction_validation)
        
        return result
    
    def generate_validation_report(self, validation_results: List[ValidationResult], 
                                 output_path: str = None) -> str:
        """
        Generate a comprehensive validation report.
        
        Args:
            validation_results: List of validation results
            output_path: Optional path to save the report
            
        Returns:
            String containing the validation report
        """
        report_lines = []
        report_lines.append("# Experiment Validation Report")
        report_lines.append("=" * 50)
        report_lines.append("")
        
        # Summary
        total_errors = sum(len(result.errors) for result in validation_results)
        total_warnings = sum(len(result.warnings) for result in validation_results)
        all_valid = all(result.is_valid for result in validation_results)
        
        report_lines.append("## Summary")
        report_lines.append(f"Overall Status: {'PASS' if all_valid else 'FAIL'}")
        report_lines.append(f"Total Errors: {total_errors}")
        report_lines.append(f"Total Warnings: {total_warnings}")
        report_lines.append("")
        
        # Detailed results
        for i, result in enumerate(validation_results):
            report_lines.append(f"## Validation {i+1}")
            report_lines.append(f"Status: {'PASS' if result.is_valid else 'FAIL'}")
            
            if result.errors:
                report_lines.append("### Errors:")
                for error in result.errors:
                    report_lines.append(f"- {error}")
            
            if result.warnings:
                report_lines.append("### Warnings:")
                for warning in result.warnings:
                    report_lines.append(f"- {warning}")
            
            if result.details:
                report_lines.append("### Details:")
                for key, value in result.details.items():
                    report_lines.append(f"- {key}: {value}")
            
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # Save report if path provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)
            self.logger.info(f"Validation report saved to: {output_path}")
        
        return report