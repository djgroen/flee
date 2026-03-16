Flee Dual Process API Documentation
===================================

Welcome to the Flee Dual Process API documentation. This framework provides comprehensive tools for testing Dual Process Theory in refugee movement simulations.

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   topology_generator
   scenario_generator
   config_manager
   experiment_runner
   analysis_pipeline
   visualization_generator
   cognitive_logger
   validation_framework
   utils

Quick Start
-----------

The Flee Dual Process framework enables systematic testing of how different cognitive modes (System 1 vs System 2 thinking) affect refugee movement patterns. Here's a basic example:

.. code-block:: python

    from flee_dual_process import (
        TopologyGenerator, 
        ConflictScenarioGenerator, 
        ConfigurationManager,
        ExperimentRunner
    )
    
    # Generate a linear topology
    topology_gen = TopologyGenerator({'output_dir': 'topologies'})
    locations_file, routes_file = topology_gen.generate_linear(
        n_nodes=5, 
        segment_distance=50.0, 
        start_pop=10000, 
        pop_decay=0.8
    )
    
    # Generate a spike conflict scenario
    scenario_gen = ConflictScenarioGenerator(locations_file)
    conflicts_file = scenario_gen.generate_spike_conflict(
        origin='Origin',
        start_day=0,
        peak_intensity=0.9
    )
    
    # Create cognitive mode configuration
    config_manager = ConfigurationManager()
    config = config_manager.create_cognitive_config('dual_process')
    
    # Run experiment
    runner = ExperimentRunner()
    results = runner.run_single_experiment({
        'topology_files': (locations_file, routes_file),
        'conflicts_file': conflicts_file,
        'config': config,
        'experiment_id': 'test_experiment'
    })

Core Concepts
-------------

**Cognitive Modes**
    The framework supports four cognitive modes:
    
    - ``s1_only``: Pure System 1 (fast, intuitive) decision-making
    - ``s2_disconnected``: System 2 (slow, deliberate) without social connectivity
    - ``s2_full``: System 2 with full social connectivity
    - ``dual_process``: Dynamic switching between System 1 and System 2

**Network Topologies**
    Four topology types are supported:
    
    - ``linear``: Chain of connected locations
    - ``star``: Hub-and-spoke network structure
    - ``tree``: Hierarchical branching network
    - ``grid``: Rectangular grid of locations

**Conflict Scenarios**
    Four scenario types test different cognitive triggers:
    
    - ``spike``: Sudden high-intensity conflict (tests System 1 responses)
    - ``gradual``: Linear escalation over time (tests System 2 planning)
    - ``cascading``: Conflict spreads through network (tests social effects)
    - ``oscillating``: Cyclical intensity variations (tests adaptation)

Installation
------------

The framework requires Python 3.8+ and integrates with the existing Flee codebase:

.. code-block:: bash

    # Install dependencies
    pip install numpy pandas matplotlib seaborn scipy pyyaml
    
    # Optional: Install plotly for interactive visualizations
    pip install plotly
    
    # The framework is designed to work within the Flee project structure

Configuration
-------------

All experiments are configured through YAML files that extend Flee's standard ``simsetting.yml`` format:

.. code-block:: yaml

    move_rules:
      two_system_decision_making: true
      average_social_connectivity: 3.0
      awareness_level: 2
      conflict_threshold: 0.6
      recovery_period_max: 30
      weight_softening: 0.3

The framework provides predefined configurations for each cognitive mode and supports parameter sweeps for sensitivity analysis.

Output Files
------------

Experiments generate standard Flee outputs plus additional cognitive tracking files:

- ``cognitive_states.csv``: Agent cognitive states over time
- ``decision_log.csv``: Decision factors and reasoning processes  
- ``social_network.csv``: Social connectivity changes
- ``experiment_metadata.json``: Complete experiment configuration and timing

Analysis and Visualization
--------------------------

The framework includes comprehensive analysis and visualization tools:

- Movement timing and distance metrics by cognitive mode
- Cognitive state transition analysis
- Statistical significance testing between modes
- Publication-ready plots and interactive visualizations
- Automated report generation

For detailed API documentation, see the individual module pages.