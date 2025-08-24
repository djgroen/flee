# Implementation Plan

- [x] 1. Set up project structure and core interfaces

  - Create directory structure for flee_dual_process framework
  - Define base classes and interfaces for topology generators, scenario generators, and configuration management
  - Create shared utilities module for common functions (CSV I/O, validation, logging)
  - _Requirements: 1.1, 1.6, 2.5, 3.5_

- [x] 2. Implement topology generation system

  - [x] 2.1 Create base topology generator class with CSV output methods

    - Write TopologyGenerator base class with abstract methods for each topology type
    - Implement \_write_locations_csv and \_write_routes_csv methods with proper Flee format
    - Add validation methods to ensure topology connectivity and parameter consistency
    - _Requirements: 1.1, 1.6_

  - [x] 2.2 Implement linear topology generator

    - Code generate_linear_topology function with parameterizable nodes, distances, and population decay
    - Create unit tests for linear chain connectivity and population distribution
    - Validate output format compatibility with Flee InputGeography module
    - _Requirements: 1.1_

  - [x] 2.3 Implement star topology generator

    - Code generate_star_topology function with hub-and-spoke network structure
    - Implement distance calculations from central hub to camps using radius parameter
    - Create unit tests for star topology structure and capacity distribution
    - _Requirements: 1.1_

  - [x] 2.4 Implement tree topology generator

    - Code generate_tree_topology function with configurable branching factor and depth
    - Implement hierarchical population distribution from root to leaves
    - Create unit tests for tree connectivity and balanced branching
    - _Requirements: 1.1_

  - [x] 2.5 Implement grid topology generator
    - Code generate_grid_topology function with rectangular grid connections
    - Support uniform and weighted population distribution patterns
    - Create unit tests for grid connectivity and neighbor relationships
    - _Requirements: 1.1_

- [x] 3. Implement conflict scenario generation system

  - [x] 3.1 Create base scenario generator class

    - Write ConflictScenarioGenerator base class with topology integration
    - Implement \_write_conflicts_csv method with proper Flee format
    - Add temporal validation to ensure scenario consistency with simulation period
    - _Requirements: 2.1, 2.5, 2.6_

  - [x] 3.2 Implement spike conflict scenario generator

    - Code generate_spike_conflict function with sudden high-intensity conflict at origin
    - Create unit tests for conflict timing and intensity validation
    - Ensure compatibility with Flee conflict input processing
    - _Requirements: 2.1_

  - [x] 3.3 Implement gradual conflict scenario generator

    - Code generate_gradual_conflict function with linear escalation over time
    - Implement configurable escalation curves and peak intensity timing
    - Create unit tests for gradual escalation patterns and boundary conditions
    - _Requirements: 2.2_

  - [x] 3.4 Implement cascading conflict scenario generator

    - Code generate_cascading_conflict function with network-based conflict spread
    - Implement spread rate calculations based on network connectivity
    - Create unit tests for cascading patterns and spread validation
    - _Requirements: 2.3_

  - [x] 3.5 Implement oscillating conflict scenario generator
    - Code generate_oscillating_conflict function with cyclical intensity variations
    - Support configurable period, amplitude, and phase parameters
    - Create unit tests for oscillation patterns and temporal consistency
    - _Requirements: 2.4_

- [x] 4. Implement configuration management system

  - [x] 4.1 Create configuration manager class

    - Write ConfigurationManager class with template-based config generation
    - Implement create_simsetting_yml method for Flee-compatible output
    - Add comprehensive parameter validation with detailed error messages
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 4.2 Implement cognitive mode configurations

    - Code predefined configurations for S1-only, S2-disconnected, S2-full, and dual-process modes
    - Implement parameter mapping between framework settings and Flee SimulationSettings
    - Create unit tests for configuration validation and parameter consistency
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 4.3 Implement parameter sweep generation
    - Code generate_parameter_sweep method for systematic parameter variation
    - Support single-parameter and factorial design experiment generation
    - Create unit tests for sweep completeness and parameter range validation
    - _Requirements: 4.1, 4.2_

- [x] 5. Enhance Flee integration for cognitive state tracking

  - [x] 5.1 Extend Person class with cognitive tracking attributes

    - Add cognitive_state, decision_history, and system2_activations attributes to Person class
    - Implement log_decision method for recording decision-making processes
    - Modify existing evolve method to call cognitive tracking functions
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 5.2 Implement cognitive state output generation

    - Create CognitiveStateLogger class to track agent states over time
    - Implement write_cognitive_states_csv method with proper formatting
    - Add integration hooks in Ecosystem.evolve to call logging functions
    - _Requirements: 5.4, 5.5_

  - [x] 5.3 Implement decision logging system

    - Create DecisionLogger class to record decision factors and reasoning
    - Implement write_decision_log_csv method with structured decision data
    - Integrate decision logging with existing selectRoute and calculateMoveChance functions
    - _Requirements: 5.3, 5.4_

  - [x] 5.4 Add social connectivity tracking
    - Enhance update_social_connectivity method with detailed logging
    - Create SocialNetworkLogger class for connectivity change tracking
    - Implement write_social_network_csv method for network evolution data
    - _Requirements: 5.1, 5.2_

- [x] 6. Implement experiment execution system

  - [x] 6.1 Create experiment runner class

    - Write ExperimentRunner class with parallel execution capabilities
    - Implement run_single_experiment method with proper error handling and logging
    - Add experiment directory setup and cleanup functionality
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 6.2 Implement parameter sweep execution

    - Code run_parameter_sweep method with multiprocessing support
    - Add progress tracking and status reporting for long-running sweeps
    - Implement experiment state persistence for resumability after failures
    - _Requirements: 4.1, 4.2, 4.5_

  - [x] 6.3 Implement parallel execution management

    - Create ProcessPoolManager class for worker process coordination
    - Add resource monitoring and throttling to prevent system overload
    - Implement retry logic with exponential backoff for failed experiments
    - _Requirements: 4.2, 4.5_

  - [x] 6.4 Add experiment metadata collection
    - Implement collect_experiment_metadata method for reproducibility tracking
    - Create standardized metadata format including parameters, timing, and system info
    - Add metadata validation and integrity checking
    - _Requirements: 4.4, 8.2_

- [x] 7. Implement analysis pipeline system

  - [x] 7.1 Create base analysis pipeline class

    - Write AnalysisPipeline class with modular metric calculation methods
    - Implement data loading and preprocessing for experiment outputs
    - Add error handling for missing or corrupted output files
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 7.2 Implement movement metrics calculation

    - Code calculate_movement_metrics method for timing, distance, and destination analysis
    - Implement statistical measures including means, medians, and confidence intervals
    - Create unit tests for metric accuracy and edge case handling
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 7.3 Implement cognitive state analysis

    - Code analyze_cognitive_transitions method for S1/S2 transition patterns
    - Calculate cognitive state duration statistics and activation triggers
    - Implement social connectivity impact analysis on cognitive transitions
    - _Requirements: 6.4, 5.1, 5.2_

  - [x] 7.4 Implement comparative analysis methods
    - Code compare_cognitive_modes method for statistical significance testing
    - Implement effect size calculations and confidence interval comparisons
    - Add support for multiple comparison corrections (Bonferroni, FDR)
    - _Requirements: 6.4, 8.4_

- [x] 8. Implement visualization and reporting system

  - [x] 8.1 Create visualization generator class

    - Write VisualizationGenerator class with matplotlib and plotly backends
    - Implement create_cognitive_state_plots method for temporal state evolution
    - Add publication-ready formatting with proper labels, legends, and styling
    - _Requirements: 7.1, 7.2, 7.5_

  - [x] 8.2 Implement movement pattern visualizations

    - Code create_movement_comparison_charts method for cognitive mode comparisons
    - Implement network flow diagrams showing agent movement patterns
    - Add interactive visualizations for parameter sweep exploration
    - _Requirements: 7.2, 7.3, 7.4_

  - [x] 8.3 Implement parameter sensitivity visualizations

    - Code create_parameter_sensitivity_plots method for sweep result analysis
    - Implement heatmaps and contour plots for multi-parameter relationships
    - Add statistical significance indicators and confidence bands
    - _Requirements: 7.3, 7.4_

  - [x] 8.4 Create automated report generation
    - Implement generate_experiment_report method with standardized templates
    - Create summary tables with key metrics and statistical comparisons
    - Add LaTeX and HTML output formats for different presentation needs
    - _Requirements: 7.5, 6.4_

- [x] 9. Implement validation and testing framework

  - [x] 9.1 Create comprehensive unit test suite

    - Write unit tests for all topology generators with connectivity validation
    - Implement unit tests for scenario generators with temporal consistency checks
    - Add unit tests for configuration management with parameter validation
    - _Requirements: 8.1, 8.3, 8.4_

  - [x] 9.2 Implement integration test suite

    - Code end-to-end pipeline tests from generation through analysis
    - Implement parallel execution stability tests with resource monitoring
    - Add data integrity tests for experiment output validation
    - _Requirements: 8.2, 8.3_

  - [x] 9.3 Create performance benchmarking suite

    - Implement performance tests for topology generation speed
    - Add benchmarks for experiment execution throughput and memory usage
    - Create scalability tests for large parameter sweeps
    - _Requirements: 8.1, 8.2_

  - [x] 9.4 Add validation framework for experimental setup
    - Code pre-flight validation checks for experiment configurations
    - Implement output validation with format and completeness checking
    - Add statistical validation for analysis results and significance tests
    - _Requirements: 8.1, 8.4, 8.5, 8.6_

- [x] 10. Create documentation and examples

  - [x] 10.1 Write comprehensive API documentation

    - Create docstrings for all public classes and methods
    - Generate API documentation using Sphinx with code examples
    - Add type hints and parameter descriptions for all functions
    - _Requirements: 8.6_

  - [x] 10.2 Create tutorial and usage examples

    - Write step-by-step tutorial for basic experiment setup and execution
    - Create example scripts for common experimental designs
    - Add troubleshooting guide for common issues and error messages
    - _Requirements: 8.6_

  - [x] 10.3 Document experimental methodology
    - Create methodology documentation explaining dual-process theory implementation
    - Document cognitive mode configurations and their theoretical basis
    - Add guidelines for interpreting results and statistical significance
    - _Requirements: 8.6_

- [x] 11. Integration and final testing

  - [x] 11.1 Perform end-to-end system integration

    - Execute complete experimental pipeline with all topology and scenario combinations
    - Validate integration with existing Flee codebase and backward compatibility
    - Test framework performance under realistic experimental loads
    - _Requirements: 8.2, 8.3_

  - [x] 11.2 Conduct validation experiments

    - Run baseline experiments to validate cognitive mode implementations
    - Compare results with existing Flee behavior for consistency checks
    - Perform sensitivity analysis to identify key parameters and thresholds
    - _Requirements: 8.4, 8.5_

  - [x] 11.3 Optimize performance and finalize
    - Profile code performance and optimize bottlenecks in critical paths
    - Finalize configuration templates and default parameter values
    - Create deployment package with installation instructions and dependencies
    - _Requirements: 8.1, 8.2, 8.6_

## Phase 2: Real FLEE Scenario Implementation

- [ ] 12. Implement H1: Speed vs Optimality Testing Scenarios

  - [ ] 12.1 Create H1.1: Multi-Destination Choice scenario

    - Create flee_dual_process/scenarios/h1_speed_optimality/h1_1_multi_destination/ directory structure
    - Implement locations.csv with Origin-Hub-Camp_A/B/C network (different safety/capacity trade-offs)
    - Create routes.csv with 50km/75km/100km distances to test route optimization
    - Implement conflict.csv with escalating conflict at Origin (day 0→30→180)
    - Add h1_1_metrics.py with decision quality measurements (time_to_move, camp_efficiency, avg_safety_achieved)
    - _Requirements: New H1 scenario testing requirements_

  - [ ] 12.2 Create H1.2: Time Pressure Cascade scenario

    - Implement cascading conflict schedule across Town_A→B→C→D with 5-day intervals
    - Create network topology with sequential towns and evacuation routes
    - Add temporal pressure measurements for S1 (immediate) vs S2 (anticipatory) responses
    - Implement metrics for evacuation timing and destination choice quality
    - _Requirements: New H1 temporal pressure testing requirements_

- [ ] 13. Implement H2: Social Connectivity Impact Scenarios

  - [ ] 13.1 Create H2.1: Hidden Information scenario

    - Implement Origin→Obvious_Camp (visible, limited) vs Origin→Hidden_Camp (better, requires social knowledge)
    - Create agent_config.py with s2_connected, s2_isolated, s1_baseline agent types
    - Add visibility and information access parameters to location definitions
    - Implement information sharing mechanics for connected vs isolated agents
    - Add metrics for destination discovery and information propagation
    - _Requirements: New H2 connectivity testing requirements_

  - [ ] 13.2 Create H2.2: Dynamic Information Sharing scenario

    - Implement real-time camp capacity updates with information lag
    - Create connected agent networks with information sharing protocols
    - Add dynamic capacity tracking and information propagation simulation
    - Implement metrics for information accuracy and decision timing
    - _Requirements: New H2 dynamic information requirements_

- [ ] 14. Implement H3: Dimensionless Parameter Testing

  - [ ] 14.1 Create H3.1: Parameter Grid Search scenario

    - Implement systematic parameter grid: conflict_intensity × recovery_period × connectivity_rate
    - Create cognitive_pressure calculation: (conflict × connectivity) / (recovery/30.0)
    - Generate experiment matrix with 175 parameter combinations
    - Add phase transition detection algorithms for S2 activation threshold
    - Implement statistical analysis for critical point identification
    - _Requirements: New H3 scaling law testing requirements_

  - [ ] 14.2 Create H3.2: Phase Transition Identification scenario

    - Generate 50 scenarios with cognitive_pressure from 0 to 2
    - Implement parameter combination generator for fixed pressure values
    - Add critical point detection with sigmoid fitting
    - Create phase diagram visualization and analysis tools
    - _Requirements: New H3 phase transition requirements_

- [ ] 15. Implement H4: Population Diversity Scenarios

  - [ ] 15.1 Create H4.1: Adaptive Shock Response scenario

    - Implement dynamic event timeline: conflict→route_closure→camp_full→new_camp
    - Create population composition configurations: pure_s1, pure_s2, balanced, realistic
    - Add adaptive response measurement for unexpected changes
    - Implement resilience metrics for different population compositions
    - _Requirements: New H4 diversity testing requirements_

  - [ ] 15.2 Create H4.2: Information Cascade Test scenario

    - Implement S1 "scout" and S2 "follower" behavior tracking
    - Create information flow measurement between agent types
    - Add destination correlation analysis between S1 and S2 choices
    - Implement time lag analysis for information cascade effects
    - _Requirements: New H4 information cascade requirements_

- [ ] 16. Create Scenario Infrastructure

  - [ ] 16.1 Implement ScenarioGenerator class

    - Create base class with generate_network, generate_conflict_schedule, generate_population methods
    - Add hypothesis-specific scenario generation for H1, H2, H3, H4
    - Implement validation methods for scenario completeness and consistency
    - Add CSV output generation for all FLEE input files
    - _Requirements: Scenario generation infrastructure_

  - [ ] 16.2 Create scenario validation framework

    - Implement validate_scenario function with hypothesis-specific checks
    - Add check_multiple_destinations_exist for H1 scenarios
    - Add check_information_asymmetry for H2 scenarios
    - Add check_parameter_range_sufficient for H3 scenarios
    - Add check_population_diversity for H4 scenarios
    - _Requirements: Scenario validation requirements_

- [ ] 17. Implement Real FLEE Integration

  - [ ] 17.1 Enhance FLEE Person class for cognitive modeling

    - Add cognitive_state, system2_capable, connection_count attributes
    - Implement cognitive decision-making logic in selectRoute method
    - Add information sharing mechanics for connected agents
    - Integrate cognitive pressure calculation with conflict intensity
    - _Requirements: Real cognitive agent implementation_

  - [ ] 17.2 Create cognitive tracking and output system

    - Implement cognitive_tracking.csv output with agent states over time
    - Create decision_log.csv with decision factors and reasoning
    - Add metrics_summary.json with hypothesis-specific measurements
    - Implement hypothesis_specific_analysis.pkl for detailed results
    - _Requirements: Comprehensive cognitive tracking_

- [ ] 18. Create Hypothesis Testing Pipeline

  - [ ] 18.1 Implement automated scenario execution

    - Create run_hypothesis_scenarios script for systematic testing
    - Add parallel execution for multiple scenario runs
    - Implement result aggregation across multiple runs
    - Add statistical significance testing for hypothesis validation
    - _Requirements: Automated hypothesis testing_

  - [ ] 18.2 Create hypothesis-specific analysis tools

    - Implement H1 decision quality analysis (speed vs optimality trade-offs)
    - Create H2 connectivity impact analysis (information sharing effects)
    - Add H3 phase transition analysis (critical point identification)
    - Implement H4 diversity advantage analysis (mixed population benefits)
    - _Requirements: Hypothesis-specific analysis capabilities_

- [ ] 19. Implement Dimensionless Parameter Analysis

  - [ ] 19.1 Create dimensionless parameter identification system

    - Implement dimensionless parameter calculator for cognitive_pressure = (conflict_intensity × connectivity) / recovery_time
    - Add automatic identification of other dimensionless combinations from experimental parameters
    - Create parameter scaling validation to ensure dimensional consistency
    - Implement universal scaling relationship detection algorithms
    - _Requirements: 15.1, 15.2, 15.3_

  - [ ] 19.2 Create dimensionless visualization framework

    - Implement dimensionless parameter space plots with data collapse visualization
    - Create universal scaling curve fitting and validation tools
    - Add dimensionless parameter sensitivity analysis
    - Implement publication-ready dimensionless parameter tables and figures
    - _Requirements: 15.3, 15.4, 15.6_

- [ ] 20. Implement Spatial Movement Visualization

  - [ ] 20.1 Create network spatial layout system

    - Implement automatic network layout algorithms for clear spatial visualization
    - Create agent movement flow visualization with cognitive mode color coding
    - Add temporal animation capabilities for movement evolution over time
    - Implement interactive spatial exploration with zoom and filtering
    - _Requirements: 16.1, 16.2, 16.3, 16.5_

  - [ ] 20.2 Create spatial pattern analysis tools

    - Implement location occupancy heatmaps and transition frequency analysis
    - Create spatial clustering algorithms for movement pattern identification
    - Add cognitive mode spatial comparison visualizations
    - Implement spatial statistics for movement pattern quantification
    - _Requirements: 16.4, 16.6_

- [ ] 21. Implement Individual Agent Tracking

  - [ ] 21.1 Create configurable agent tracking system

    - Implement multi-level tracking: summary, detailed, full individual tracking
    - Create efficient storage formats (HDF5, Parquet) for large agent datasets
    - Add configurable sampling and compression options for output management
    - Implement agent trajectory data validation and integrity checking
    - _Requirements: 17.1, 17.3, 17.4, 17.5_

  - [ ] 21.2 Create individual agent analysis tools

    - Implement complete movement history tracking and decision factor logging
    - Create agent-level trajectory analysis and clustering methods
    - Add individual decision-making pattern identification algorithms
    - Implement comparative analysis between individual and aggregate patterns
    - _Requirements: 17.2, 17.6_

## Phase 3: Real-World Case Study and Model Evaluation

- [ ] 22. Implement South Sudan Conflict Case Study

  - [ ] 22.1 Create South Sudan scenario from UNHCR data

    - Obtain and process real UNHCR refugee data for South Sudan → Northern Uganda displacement
    - Create authentic network topology based on actual displacement routes and camp locations
    - Implement real conflict timeline using ACLED or similar conflict event data
    - Add actual camp capacities, distances, and geographic constraints from UNHCR reports
    - _Requirements: Real-world case study requirements_

  - [ ] 22.2 Calibrate cognitive model parameters using real data

    - Fit dual-process model parameters to match observed displacement patterns
    - Assess cognitive pressure scaling using real conflict intensity and displacement timing
    - Calibrate social connectivity parameters based on actual refugee network data
    - Implement parameter uncertainty quantification and sensitivity analysis
    - _Requirements: Model calibration and assessment_

- [ ] 23. Evaluate Dual-Process Theory Predictions

  - [ ] 23.1 Compare model predictions with observed refugee behavior

    - Assess H1 predictions: Do faster vs more deliberate decision-makers show different destination choices?
    - Evaluate H2 predictions: Do connected refugees discover better destinations than isolated ones?
    - Test H3 predictions: Does cognitive pressure scaling predict S1/S2 activation patterns?
    - Examine H4 predictions: Do mixed populations achieve better collective outcomes?
    - _Requirements: Theory evaluation against real-world data_

  - [ ] 23.2 Create real-world case study analysis

    - Implement statistical comparison between model predictions and UNHCR observations
    - Create assessment metrics for displacement timing, route choice, and destination selection
    - Add model performance evaluation and goodness-of-fit measures
    - Generate case study report with model limitations and future research directions
    - _Requirements: Comprehensive real-world case study analysis_

- [ ] 24. Create Publication-Ready Case Study

  - [ ] 24.1 Generate South Sudan case study results

    - Create comprehensive analysis of South Sudan displacement using dual-process framework
    - Generate publication-quality figures comparing model vs observed displacement patterns
    - Implement policy-relevant analysis of intervention scenarios (information campaigns, camp capacity)
    - Add discussion of model insights for humanitarian response planning
    - _Requirements: Publication-ready case study_

  - [ ] 24.2 Create reproducible research package

    - Package complete South Sudan case study with data, code, and analysis scripts
    - Create detailed methodology documentation for real-world application
    - Add replication instructions and data sources for other conflict scenarios
    - Generate final publication manuscript with stylized scenarios + real-world validation
    - _Requirements: Reproducible research and publication_
