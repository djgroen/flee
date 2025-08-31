"""
Configuration Management Module

Manages experimental configurations and parameter sweeps for dual-process experiments.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
import os
import yaml
try:
    from .utils import ValidationUtils, LoggingUtils
except ImportError:
    from utils import ValidationUtils, LoggingUtils


class ConfigurationManager:
    """
    Manages experimental configurations and parameter sweeps.
    
    This class handles the creation of cognitive mode configurations,
    parameter sweep generation, and validation of experimental setups
    for dual-process theory testing in Flee simulations.
    """
    
    # Base template for Flee-compatible simsetting.yml
    BASE_TEMPLATE = {
        'log_levels': {
            'agent': 0,
            'link': 0,
            'camp': 0,
            'conflict': 0,
            'init': 0,
            'granularity': 'location'
        },
        'spawn_rules': {
            'take_from_population': False,
            'insert_day0': True
        },
        'move_rules': {
            'max_move_speed': 360.0,
            'max_walk_speed': 35.0,
            'foreign_weight': 1.0,
            'camp_weight': 1.0,
            'conflict_weight': 0.25,
            'conflict_movechance': 1.0,
            'camp_movechance': 0.001,
            'default_movechance': 0.3,
            'awareness_level': 1,
            'capacity_scaling': 1.0,
            'avoid_short_stints': False,
            'start_on_foot': False,
            'weight_power': 1.0,
            'TwoSystemDecisionMaking': False,
            'average_social_connectivity': 0.0,
            'weight_softening': 0.5,
            'conflict_threshold': 0.5,
            'recovery_period_max': 14
        },
        'optimisations': {
            'hasten': 1
        }
    }
    
    # Predefined cognitive mode configurations
    COGNITIVE_MODES = {
        's1_only': {
            'move_rules': {
                'TwoSystemDecisionMaking': False,
                'awareness_level': 1,
                'weight_softening': 0.8,  # More heuristic-based
                'average_social_connectivity': 0.0,
                'default_movechance': 0.5,  # Higher base move chance (faster)
                'conflict_movechance': 1.0,  # React immediately to conflict
            }
        },
        's2_disconnected': {
            'move_rules': {
                'TwoSystemDecisionMaking': True,
                'average_social_connectivity': 0.1,  # Minimal connectivity to trigger S2
                'awareness_level': 3,
                'weight_softening': 0.1,  # More analytical
                'conflict_threshold': 0.001,  # Extremely low threshold - always S2
                'default_movechance': 0.2,  # Lower base move chance (slower)
                'conflict_movechance': 0.8,  # More deliberate response
            }
        },
        's2_full': {
            'move_rules': {
                'TwoSystemDecisionMaking': True,
                'average_social_connectivity': 15.0,  # Very high connectivity
                'awareness_level': 3,
                'weight_softening': 0.1,  # More analytical
                'conflict_threshold': 0.3,  # Higher threshold but still reachable
                'default_movechance': 0.2,  # Lower base move chance (slower)
                'conflict_movechance': 0.8,  # More deliberate response
            }
        },
        'dual_process': {
            'move_rules': {
                'TwoSystemDecisionMaking': True,
                'average_social_connectivity': 8.0,  # High connectivity for pressure
                'awareness_level': 2,
                'conflict_threshold': 0.4,  # Medium threshold
                'recovery_period_max': 10,  # Very short recovery for more pressure
                'weight_softening': 0.4,  # Balanced approach
                'default_movechance': 0.3,  # Medium base move chance
                'conflict_movechance': 0.9,  # Adaptive response
            }
        }
    }
    
    # Parameter validation rules
    PARAMETER_VALIDATION = {
        'move_rules': {
            'awareness_level': {'type': int, 'min': 1, 'max': 3},
            'average_social_connectivity': {'type': (int, float), 'min': 0.0},
            'conflict_threshold': {'type': (int, float), 'min': 0.0, 'max': 1.0},
            'recovery_period_max': {'type': int, 'min': 1},
            'weight_softening': {'type': (int, float), 'min': 0.0, 'max': 1.0},
            'max_move_speed': {'type': (int, float), 'min': 0.0},
            'max_walk_speed': {'type': (int, float), 'min': 0.0},
            'foreign_weight': {'type': (int, float), 'min': 0.0},
            'camp_weight': {'type': (int, float), 'min': 0.0},
            'conflict_weight': {'type': (int, float), 'min': 0.0},
            'conflict_movechance': {'type': (int, float), 'min': 0.0, 'max': 1.0},
            'camp_movechance': {'type': (int, float), 'min': 0.0, 'max': 1.0},
            'default_movechance': {'type': (int, float), 'min': 0.0, 'max': 1.0},
            'capacity_scaling': {'type': (int, float), 'min': 0.0},
            'weight_power': {'type': (int, float), 'min': 0.0},
            'TwoSystemDecisionMaking': {'type': bool}
        },
        'optimisations': {
            'hasten': {'type': int, 'min': 1}
        }
    }
    
    def __init__(self, base_template: Dict[str, Any] = None):
        """
        Initialize configuration manager with base template.
        
        Args:
            base_template: Base configuration template dictionary (optional, uses default if None)
        """
        self.base_template = base_template if base_template is not None else self.BASE_TEMPLATE.copy()
        self.validation_utils = ValidationUtils()
        self.logging_utils = LoggingUtils()
    
    def create_cognitive_config(self, mode: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create configuration for specified cognitive mode.
        
        Args:
            mode: Cognitive mode ('s1_only', 's2_disconnected', 's2_full', 'dual_process')
            parameters: Optional additional parameters to override defaults
            
        Returns:
            Complete configuration dictionary
            
        Raises:
            ValueError: If mode is not recognized
        """
        if mode not in self.COGNITIVE_MODES:
            raise ValueError(f"Unknown cognitive mode: {mode}. "
                           f"Available modes: {list(self.COGNITIVE_MODES.keys())}")
        
        # Start with deep copy of base template
        import copy
        config = copy.deepcopy(self.base_template)
        
        # Apply cognitive mode settings by merging nested dictionaries
        mode_config = self.COGNITIVE_MODES[mode]
        for section, section_params in mode_config.items():
            if section in config and isinstance(config[section], dict):
                config[section].update(section_params)
            else:
                config[section] = section_params
        
        # Apply any additional parameters
        if parameters:
            for section, section_params in parameters.items():
                if section in config and isinstance(config[section], dict):
                    config[section].update(section_params)
                else:
                    config[section] = section_params
        
        # Validate configuration
        if not self.validate_configuration(config):
            raise ValueError("Generated configuration failed validation")
        
        return config
    
    def generate_parameter_sweep(self, base_config: Dict[str, Any], 
                                parameter: str, values: List[Any]) -> List[Dict[str, Any]]:
        """
        Generate parameter sweep configurations.
        
        Args:
            base_config: Base configuration to vary
            parameter: Parameter name to sweep (supports nested parameters with dot notation)
            values: List of values for the parameter
            
        Returns:
            List of configuration dictionaries
        """
        import copy
        configs = []
        
        for value in values:
            config = copy.deepcopy(base_config)
            
            # Handle nested parameter names (e.g., 'move_rules.awareness_level')
            if '.' in parameter:
                sections = parameter.split('.')
                current = config
                
                # Navigate to the parent section
                for section in sections[:-1]:
                    if section not in current:
                        current[section] = {}
                    current = current[section]
                
                # Set the final parameter
                current[sections[-1]] = value
            else:
                config[parameter] = value
            
            # Validate each configuration
            if self.validate_configuration(config):
                configs.append(config)
            else:
                self.logging_utils.log_warning(
                    f"Skipping invalid configuration with {parameter}={value}"
                )
        
        return configs
    
    def generate_factorial_design(self, base_config: Dict[str, Any], 
                                 factors: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """
        Generate factorial design configurations.
        
        Args:
            base_config: Base configuration to vary
            factors: Dictionary mapping parameter names to lists of values
            
        Returns:
            List of configuration dictionaries for all factor combinations
        """
        import copy
        import itertools
        
        configs = []
        
        # Get parameter names and their value lists
        parameter_names = list(factors.keys())
        value_lists = list(factors.values())
        
        # Generate all combinations using Cartesian product
        for combination in itertools.product(*value_lists):
            config = copy.deepcopy(base_config)
            
            # Apply each parameter value in the combination
            for param_name, value in zip(parameter_names, combination):
                # Handle nested parameter names (e.g., 'move_rules.awareness_level')
                if '.' in param_name:
                    sections = param_name.split('.')
                    current = config
                    
                    # Navigate to the parent section
                    for section in sections[:-1]:
                        if section not in current:
                            current[section] = {}
                        current = current[section]
                    
                    # Set the final parameter
                    current[sections[-1]] = value
                else:
                    config[param_name] = value
            
            # Validate each configuration
            if self.validate_configuration(config):
                configs.append(config)
            else:
                param_values = {param: val for param, val in zip(parameter_names, combination)}
                self.logging_utils.log_warning(
                    f"Skipping invalid configuration with parameters: {param_values}"
                )
        
        return configs
    
    def create_simsetting_yml(self, config: Dict[str, Any], output_path: str) -> None:
        """
        Create simsetting.yml file from configuration.
        
        Args:
            config: Configuration dictionary
            output_path: Path for output YAML file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write YAML file
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=True)
        
        self.logging_utils.log_info(f"Created simsetting.yml at {output_path}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration parameters with detailed error messages.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate using utility class first
            if not self.validation_utils.validate_configuration(config):
                return False
            
            # Additional detailed validation using parameter rules
            for section, section_rules in self.PARAMETER_VALIDATION.items():
                if section not in config:
                    continue
                
                section_config = config[section]
                if not isinstance(section_config, dict):
                    self.logging_utils.log_error(f"Section '{section}' must be a dictionary")
                    return False
                
                for param, rules in section_rules.items():
                    if param not in section_config:
                        continue
                    
                    value = section_config[param]
                    
                    # Type validation
                    if 'type' in rules:
                        expected_type = rules['type']
                        if not isinstance(value, expected_type):
                            self.logging_utils.log_error(
                                f"Parameter '{section}.{param}' must be of type {expected_type}, "
                                f"got {type(value)}"
                            )
                            return False
                    
                    # Range validation for numeric types
                    if isinstance(value, (int, float)):
                        if 'min' in rules and value < rules['min']:
                            self.logging_utils.log_error(
                                f"Parameter '{section}.{param}' must be >= {rules['min']}, "
                                f"got {value}"
                            )
                            return False
                        
                        if 'max' in rules and value > rules['max']:
                            self.logging_utils.log_error(
                                f"Parameter '{section}.{param}' must be <= {rules['max']}, "
                                f"got {value}"
                            )
                            return False
            
            return True
            
        except Exception as e:
            self.logging_utils.log_error(f"Configuration validation failed: {e}")
            return False
    
    def load_configuration_template(self, template_path: str) -> Dict[str, Any]:
        """
        Load configuration template from file.
        
        Args:
            template_path: Path to template YAML file
            
        Returns:
            Configuration template dictionary
        """
        try:
            with open(template_path, 'r') as f:
                template = yaml.safe_load(f)
            return template
        except Exception as e:
            self.logging_utils.log_error(f"Failed to load template from {template_path}: {e}")
            raise
    
    def save_configuration_template(self, config: Dict[str, Any], template_path: str) -> None:
        """
        Save configuration as template file.
        
        Args:
            config: Configuration dictionary
            template_path: Path for template file
        """
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        with open(template_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=True)
        
        self.logging_utils.log_info(f"Saved configuration template to {template_path}")
    
    def generate_cognitive_mode_sweep(self, base_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Generate configurations for all cognitive modes.
        
        Args:
            base_config: Base configuration to use (optional, uses default if None)
            
        Returns:
            List of configurations for all cognitive modes
        """
        if base_config is None:
            base_config = self.base_template.copy()
        
        configs = []
        for mode in self.COGNITIVE_MODES.keys():
            try:
                config = self.create_cognitive_config(mode)
                configs.append(config)
            except ValueError as e:
                self.logging_utils.log_warning(f"Failed to create config for mode {mode}: {e}")
        
        return configs
    
    def save_parameter_sweep(self, configs: List[Dict[str, Any]], output_dir: str, 
                           prefix: str = "config") -> List[str]:
        """
        Save parameter sweep configurations to individual files.
        
        Args:
            configs: List of configuration dictionaries
            output_dir: Directory to save configuration files
            prefix: Filename prefix for configuration files
            
        Returns:
            List of created file paths
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        file_paths = []
        
        for i, config in enumerate(configs):
            filename = f"{prefix}_{i:03d}.yml"
            filepath = os.path.join(output_dir, filename)
            self.create_simsetting_yml(config, filepath)
            file_paths.append(filepath)
        
        self.logging_utils.log_info(f"Saved {len(configs)} configurations to {output_dir}")
        return file_paths
    
    def validate_parameter_sweep(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a list of configurations and return summary statistics.
        
        Args:
            configs: List of configuration dictionaries
            
        Returns:
            Dictionary with validation summary statistics
        """
        total_configs = len(configs)
        valid_configs = 0
        invalid_configs = 0
        validation_errors = []
        
        for i, config in enumerate(configs):
            if self.validate_configuration(config):
                valid_configs += 1
            else:
                invalid_configs += 1
                validation_errors.append(f"Configuration {i}: validation failed")
        
        summary = {
            'total_configurations': total_configs,
            'valid_configurations': valid_configs,
            'invalid_configurations': invalid_configs,
            'validation_rate': valid_configs / total_configs if total_configs > 0 else 0.0,
            'errors': validation_errors
        }
        
        return summary


class ExperimentConfig:
    """
    Data class for experiment configuration.
    """
    
    def __init__(self, experiment_id: str, topology_type: str, topology_params: Dict[str, Any],
                 scenario_type: str, scenario_params: Dict[str, Any], cognitive_mode: str,
                 simulation_params: Dict[str, Any], replications: int = 1, 
                 metadata: Dict[str, Any] = None):
        """
        Initialize experiment configuration.
        
        Args:
            experiment_id: Unique identifier for experiment
            topology_type: Type of topology ('linear', 'star', 'tree', 'grid')
            topology_params: Parameters for topology generation
            scenario_type: Type of scenario ('spike', 'gradual', 'cascading', 'oscillating')
            scenario_params: Parameters for scenario generation
            cognitive_mode: Cognitive mode configuration
            simulation_params: Flee simulation parameters
            replications: Number of replications to run
            metadata: Additional metadata
        """
        self.experiment_id = experiment_id
        self.topology_type = topology_type
        self.topology_params = topology_params
        self.scenario_type = scenario_type
        self.scenario_params = scenario_params
        self.cognitive_mode = cognitive_mode
        self.simulation_params = simulation_params
        self.replications = replications
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'experiment_id': self.experiment_id,
            'topology_type': self.topology_type,
            'topology_params': self.topology_params,
            'scenario_type': self.scenario_type,
            'scenario_params': self.scenario_params,
            'cognitive_mode': self.cognitive_mode,
            'simulation_params': self.simulation_params,
            'replications': self.replications,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentConfig':
        """Create from dictionary representation."""
        return cls(**data)