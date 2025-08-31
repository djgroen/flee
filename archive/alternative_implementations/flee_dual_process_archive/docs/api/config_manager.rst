Configuration Manager API
=========================

.. currentmodule:: flee_dual_process.config_manager

The configuration manager handles experimental configurations and parameter sweeps for dual-process experiments.

Classes
-------

.. autoclass:: ConfigurationManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages experimental configurations and parameter sweeps.
   
   This class handles the creation of cognitive mode configurations,
   parameter sweep generation, and validation of experimental setups
   for dual-process theory testing in Flee simulations.

   **Example Usage:**
   
   .. code-block:: python
   
       from flee_dual_process.config_manager import ConfigurationManager
       
       # Initialize manager
       config_manager = ConfigurationManager()
       
       # Create dual-process configuration
       config = config_manager.create_cognitive_config('dual_process')
       
       # Generate parameter sweep
       sweep_configs = config_manager.generate_parameter_sweep(
           base_config=config,
           parameter='move_rules.awareness_level',
           values=[1, 2, 3]
       )

.. autoclass:: ExperimentConfig
   :members:
   :undoc-members:
   :show-inheritance:

   Data class for experiment configuration.
   
   Encapsulates all parameters needed to define and execute a complete
   dual-process experiment, including topology, scenario, and simulation settings.

   **Example Usage:**
   
   .. code-block:: python
   
       from flee_dual_process.config_manager import ExperimentConfig
       
       # Create experiment configuration
       exp_config = ExperimentConfig(
           experiment_id='test_dual_process',
           topology_type='linear',
           topology_params={'n_nodes': 5, 'segment_distance': 50.0},
           scenario_type='spike',
           scenario_params={'peak_intensity': 0.9},
           cognitive_mode='dual_process',
           simulation_params={'max_days': 100},
           replications=3
       )

Cognitive Modes
---------------

The framework supports four predefined cognitive modes:

**s1_only**
   Pure System 1 (fast, intuitive) decision-making:
   
   .. code-block:: python
   
       config = config_manager.create_cognitive_config('s1_only')
       # Results in:
       # - two_system_decision_making: False
       # - awareness_level: 1
       # - weight_softening: 0.5
       # - average_social_connectivity: 0.0

**s2_disconnected**
   System 2 (slow, deliberate) without social connectivity:
   
   .. code-block:: python
   
       config = config_manager.create_cognitive_config('s2_disconnected')
       # Results in:
       # - two_system_decision_making: True
       # - average_social_connectivity: 0.0
       # - awareness_level: 3
       # - weight_softening: 0.1

**s2_full**
   System 2 with full social connectivity:
   
   .. code-block:: python
   
       config = config_manager.create_cognitive_config('s2_full')
       # Results in:
       # - two_system_decision_making: True
       # - average_social_connectivity: 8.0
       # - awareness_level: 3
       # - weight_softening: 0.1

**dual_process**
   Dynamic switching between System 1 and System 2:
   
   .. code-block:: python
   
       config = config_manager.create_cognitive_config('dual_process')
       # Results in:
       # - two_system_decision_making: True
       # - average_social_connectivity: 3.0
       # - awareness_level: 2
       # - conflict_threshold: 0.6
       # - recovery_period_max: 30
       # - weight_softening: 0.3

Methods
-------

.. automethod:: ConfigurationManager.create_cognitive_config

   Create configuration for specified cognitive mode.
   
   **Parameters:**
   
   - ``mode`` (str): Cognitive mode ('s1_only', 's2_disconnected', 's2_full', 'dual_process')
   - ``parameters`` (dict, optional): Additional parameters to override defaults
   
   **Returns:**
   
   - ``dict``: Complete configuration dictionary
   
   **Example:**
   
   .. code-block:: python
   
       # Create dual-process config with custom parameters
       config = config_manager.create_cognitive_config(
           mode='dual_process',
           parameters={
               'move_rules': {
                   'conflict_threshold': 0.7,
                   'recovery_period_max': 45
               }
           }
       )

.. automethod:: ConfigurationManager.generate_parameter_sweep

   Generate parameter sweep configurations.
   
   **Parameters:**
   
   - ``base_config`` (dict): Base configuration to vary
   - ``parameter`` (str): Parameter name to sweep (supports dot notation)
   - ``values`` (list): List of values for the parameter
   
   **Returns:**
   
   - ``list``: List of configuration dictionaries
   
   **Example:**
   
   .. code-block:: python
   
       # Sweep awareness levels
       configs = config_manager.generate_parameter_sweep(
           base_config=base_config,
           parameter='move_rules.awareness_level',
           values=[1, 2, 3]
       )
       
       # Sweep social connectivity
       configs = config_manager.generate_parameter_sweep(
           base_config=base_config,
           parameter='move_rules.average_social_connectivity',
           values=[0.0, 2.0, 4.0, 6.0, 8.0]
       )

.. automethod:: ConfigurationManager.generate_factorial_design

   Generate factorial design configurations.
   
   **Parameters:**
   
   - ``base_config`` (dict): Base configuration to vary
   - ``factors`` (dict): Dictionary mapping parameter names to value lists
   
   **Returns:**
   
   - ``list``: List of configuration dictionaries for all combinations
   
   **Example:**
   
   .. code-block:: python
   
       # 2x3 factorial design
       configs = config_manager.generate_factorial_design(
           base_config=base_config,
           factors={
               'move_rules.awareness_level': [1, 3],
               'move_rules.average_social_connectivity': [0.0, 3.0, 8.0]
           }
       )
       # Generates 6 configurations (2 × 3 combinations)

.. automethod:: ConfigurationManager.create_simsetting_yml

   Create simsetting.yml file from configuration.
   
   **Parameters:**
   
   - ``config`` (dict): Configuration dictionary
   - ``output_path`` (str): Path for output YAML file
   
   **Example:**
   
   .. code-block:: python
   
       config_manager.create_simsetting_yml(
           config=config,
           output_path='experiments/exp_001/simsetting.yml'
       )

.. automethod:: ConfigurationManager.validate_configuration

   Validate configuration parameters with detailed error messages.
   
   **Parameters:**
   
   - ``config`` (dict): Configuration dictionary to validate
   
   **Returns:**
   
   - ``bool``: True if configuration is valid, False otherwise
   
   **Example:**
   
   .. code-block:: python
   
       is_valid = config_manager.validate_configuration(config)
       if not is_valid:
           print("Configuration validation failed")

Parameter Validation
--------------------

The configuration manager validates parameters according to these rules:

**move_rules section:**

- ``awareness_level``: int, range [1, 3]
- ``average_social_connectivity``: float, minimum 0.0
- ``conflict_threshold``: float, range [0.0, 1.0]
- ``recovery_period_max``: int, minimum 1
- ``weight_softening``: float, range [0.0, 1.0]
- ``max_move_speed``: float, minimum 0.0
- ``max_walk_speed``: float, minimum 0.0
- ``conflict_movechance``: float, range [0.0, 1.0]
- ``camp_movechance``: float, range [0.0, 1.0]
- ``default_movechance``: float, range [0.0, 1.0]
- ``two_system_decision_making``: bool

**optimisations section:**

- ``hasten``: int, minimum 1

Parameter Sweeps
----------------

**Single Parameter Sweeps**

Test sensitivity to individual parameters:

.. code-block:: python

    # Test different conflict thresholds
    threshold_sweep = config_manager.generate_parameter_sweep(
        base_config=dual_process_config,
        parameter='move_rules.conflict_threshold',
        values=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    )

**Multi-Parameter Sweeps**

Test interactions between parameters:

.. code-block:: python

    # Test awareness level × social connectivity interaction
    interaction_sweep = config_manager.generate_factorial_design(
        base_config=base_config,
        factors={
            'move_rules.awareness_level': [1, 2, 3],
            'move_rules.average_social_connectivity': [0.0, 4.0, 8.0]
        }
    )

**Cognitive Mode Comparison**

Compare all cognitive modes:

.. code-block:: python

    # Generate configs for all modes
    mode_configs = config_manager.generate_cognitive_mode_sweep()
    
    # Or manually create comparison
    modes = ['s1_only', 's2_disconnected', 's2_full', 'dual_process']
    comparison_configs = [
        config_manager.create_cognitive_config(mode) 
        for mode in modes
    ]

Configuration Templates
-----------------------

**Base Template Structure**

The framework uses a hierarchical configuration structure:

.. code-block:: yaml

    log_levels:
      agent: 0
      link: 0
      camp: 0
      conflict: 0
      init: 0
      granularity: 'location'
    
    spawn_rules:
      take_from_population: false
      insert_day0: true
    
    move_rules:
      max_move_speed: 360.0
      max_walk_speed: 35.0
      foreign_weight: 1.0
      camp_weight: 1.0
      conflict_weight: 0.25
      conflict_movechance: 1.0
      camp_movechance: 0.001
      default_movechance: 0.3
      awareness_level: 1
      capacity_scaling: 1.0
      avoid_short_stints: false
      start_on_foot: false
      weight_power: 1.0
      two_system_decision_making: false
      average_social_connectivity: 0.0
      weight_softening: 0.5
      conflict_threshold: 0.5
      recovery_period_max: 14
    
    optimisations:
      hasten: 1

**Custom Templates**

Load and save custom templates:

.. code-block:: python

    # Load custom template
    custom_template = config_manager.load_configuration_template(
        'templates/custom_template.yml'
    )
    
    # Use custom template as base
    config_manager = ConfigurationManager(base_template=custom_template)
    
    # Save configuration as template
    config_manager.save_configuration_template(
        config=my_config,
        template_path='templates/my_template.yml'
    )

Error Handling
--------------

Comprehensive error handling for configuration issues:

.. code-block:: python

    try:
        config = config_manager.create_cognitive_config('invalid_mode')
    except ValueError as e:
        print(f"Invalid cognitive mode: {e}")
    
    try:
        config = config_manager.create_cognitive_config(
            'dual_process',
            parameters={'move_rules': {'awareness_level': 5}}  # Invalid range
        )
    except ValueError as e:
        print(f"Parameter validation failed: {e}")

Common validation errors include:

- Unknown cognitive mode names
- Parameter values outside valid ranges
- Invalid parameter types (string instead of number)
- Missing required configuration sections
- Conflicting parameter combinations

Best Practices
--------------

1. **Mode Selection**: Choose cognitive modes that match research hypotheses
2. **Parameter Ranges**: Use realistic parameter ranges based on literature
3. **Validation**: Always validate configurations before experiments
4. **Documentation**: Document parameter choices and rationale
5. **Reproducibility**: Save configurations for experiment reproducibility
6. **Systematic Testing**: Use parameter sweeps to explore parameter space
7. **Statistical Power**: Ensure sufficient parameter combinations for analysis