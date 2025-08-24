# Requirements Document

## Introduction

This feature implements a complete experimental framework for testing Dual Process Theory in the Flee refugee movement model. The framework will enable researchers to systematically study how different cognitive modes (System 1 vs System 2 thinking) affect refugee movement patterns across various network topologies and conflict scenarios. The system will generate standardized experimental inputs, execute parameter sweeps, track cognitive states, and provide comprehensive analysis of results.

## Requirements

### Requirement 1

**User Story:** As a researcher, I want to generate different network topologies for experiments, so that I can test how network structure affects cognitive decision-making in refugee movements.

#### Acceptance Criteria

1. WHEN I specify a linear topology with parameters THEN the system SHALL generate locations.csv and routes.csv files with nodes connected in a chain
2. WHEN I specify a star topology with parameters THEN the system SHALL generate a hub-and-spoke network with one central location connected to multiple camps
3. WHEN I specify a tree topology with branching factor and depth THEN the system SHALL generate a hierarchical branching network structure
4. WHEN I specify a grid topology with dimensions THEN the system SHALL generate a rectangular grid of connected locations
5. IF topology parameters are invalid THEN the system SHALL raise appropriate validation errors
6. WHEN generating any topology THEN the system SHALL ensure all output files are compatible with standard Flee input format

### Requirement 2

**User Story:** As a researcher, I want to generate different conflict scenarios, so that I can test how various conflict patterns trigger different cognitive responses.

#### Acceptance Criteria

1. WHEN I specify a spike conflict scenario THEN the system SHALL generate sudden high-intensity conflict at the origin location
2. WHEN I specify a gradual conflict scenario THEN the system SHALL generate linearly escalating conflict intensity over time
3. WHEN I specify a cascading conflict scenario THEN the system SHALL generate conflict that spreads through the network based on connectivity
4. WHEN I specify an oscillating conflict scenario THEN the system SHALL generate cyclically varying conflict intensity
5. WHEN generating any conflict scenario THEN the system SHALL output a properly formatted conflicts.csv file
6. IF scenario parameters are inconsistent with topology THEN the system SHALL validate and report errors

### Requirement 3

**User Story:** As a researcher, I want to configure different cognitive modes for experiments, so that I can compare System 1, System 2, and dual-process decision-making behaviors.

#### Acceptance Criteria

1. WHEN I select S1-only mode THEN the system SHALL configure simulations with system2_active=False
2. WHEN I select S2-disconnected mode THEN the system SHALL configure system2_active=True with social_connectivity_rate=0.0
3. WHEN I select S2-full mode THEN the system SHALL configure system2_active=True with social_connectivity_rate=1.0
4. WHEN I select dual-process mode THEN the system SHALL configure both systems active with configurable thresholds
5. WHEN generating configuration files THEN the system SHALL create valid simsetting.csv files for Flee
6. IF configuration parameters conflict THEN the system SHALL validate and prevent invalid combinations

### Requirement 4

**User Story:** As a researcher, I want to run systematic parameter sweeps, so that I can understand sensitivity of cognitive behaviors to key parameters.

#### Acceptance Criteria

1. WHEN I specify a parameter sweep THEN the system SHALL generate all combinations of parameter values
2. WHEN running experiments in parallel THEN the system SHALL manage concurrent execution without conflicts
3. WHEN an experiment fails THEN the system SHALL log errors and continue with remaining experiments
4. WHEN experiments complete THEN the system SHALL organize results in standardized directory structure
5. IF system resources are insufficient THEN the system SHALL queue experiments and provide progress updates
6. WHEN resuming interrupted sweeps THEN the system SHALL detect completed experiments and skip them

### Requirement 5

**User Story:** As a researcher, I want to track cognitive states during simulations, so that I can analyze when and why agents switch between System 1 and System 2 thinking.

#### Acceptance Criteria

1. WHEN running dual-process simulations THEN the system SHALL log cognitive state for each agent at each time step
2. WHEN agents transition between cognitive states THEN the system SHALL record transition triggers and timing
3. WHEN agents make movement decisions THEN the system SHALL log decision factors and reasoning mode
4. WHEN simulations complete THEN the system SHALL output cognitive_states.csv and decision_log.csv files
5. IF cognitive tracking impacts performance significantly THEN the system SHALL provide options to reduce logging frequency
6. WHEN analyzing cognitive data THEN the system SHALL ensure data format is compatible with analysis scripts

### Requirement 6

**User Story:** As a researcher, I want automated analysis of experimental results, so that I can quickly identify patterns and generate insights from large experimental datasets.

#### Acceptance Criteria

1. WHEN experiments complete THEN the system SHALL automatically calculate movement timing metrics
2. WHEN analyzing results THEN the system SHALL compute distance traveled statistics by cognitive mode
3. WHEN processing outputs THEN the system SHALL calculate destination distribution entropy and concentration
4. WHEN comparing cognitive modes THEN the system SHALL perform statistical significance tests
5. WHEN generating reports THEN the system SHALL create standardized plots and summary tables
6. IF analysis fails due to missing data THEN the system SHALL report specific data requirements and continue with available metrics

### Requirement 7

**User Story:** As a researcher, I want to visualize experimental results, so that I can communicate findings effectively and identify patterns across experiments.

#### Acceptance Criteria

1. WHEN generating visualizations THEN the system SHALL create cognitive state evolution plots over time
2. WHEN comparing experiments THEN the system SHALL generate movement pattern comparison charts
3. WHEN analyzing parameter sweeps THEN the system SHALL create parameter sensitivity plots
4. WHEN displaying network effects THEN the system SHALL generate network flow diagrams
5. WHEN creating reports THEN the system SHALL ensure all plots are publication-ready with proper labels and legends
6. IF visualization data is too large THEN the system SHALL provide sampling and aggregation options

### Requirement 8

**User Story:** As a researcher, I want to validate experimental setup and results, so that I can ensure scientific rigor and reproducibility.

#### Acceptance Criteria

1. WHEN setting up experiments THEN the system SHALL validate all input parameters and file formats
2. WHEN running experiments THEN the system SHALL record complete metadata including parameters, timing, and system configuration
3. WHEN experiments complete THEN the system SHALL verify output file integrity and completeness
4. WHEN analyzing results THEN the system SHALL check for statistical validity and report confidence intervals
5. IF validation fails THEN the system SHALL provide specific error messages and suggested corrections
6. WHEN archiving results THEN the system SHALL ensure full reproducibility with saved configurations and random seeds

## Phase 2: Real FLEE Scenario Implementation Requirements

### Requirement 9

**User Story:** As a researcher, I want to implement H1 speed vs optimality testing scenarios, so that I can measure decision quality differences between cognitive modes in realistic FLEE simulations.

#### Acceptance Criteria

1. WHEN implementing H1.1 Multi-Destination Choice THEN the system SHALL create Origin-Hub-Camp_A/B/C network with different safety/capacity trade-offs
2. WHEN running H1.1 scenarios THEN the system SHALL measure time_to_move, camp_efficiency, and avg_safety_achieved metrics
3. WHEN implementing H1.2 Time Pressure Cascade THEN the system SHALL create cascading conflict across Town_A→B→C→D with 5-day intervals
4. WHEN analyzing H1 results THEN the system SHALL compare S1 immediate vs S2 anticipatory evacuation responses
5. IF H1 scenarios detect no cognitive differences THEN the system SHALL validate scenario parameters and suggest adjustments
6. WHEN H1 experiments complete THEN the system SHALL generate decision quality comparison reports

### Requirement 10

**User Story:** As a researcher, I want to implement H2 social connectivity impact scenarios, so that I can test how information sharing affects destination discovery and decision-making.

#### Acceptance Criteria

1. WHEN implementing H2.1 Hidden Information THEN the system SHALL create Obvious_Camp (visible, limited) vs Hidden_Camp (better, requires social knowledge)
2. WHEN configuring H2 agents THEN the system SHALL implement s2_connected, s2_isolated, and s1_baseline agent types with different information access
3. WHEN implementing H2.2 Dynamic Information Sharing THEN the system SHALL simulate real-time camp capacity updates with information lag
4. WHEN analyzing H2 results THEN the system SHALL measure destination discovery rates and information propagation speed
5. IF connectivity effects are not detected THEN the system SHALL validate information asymmetry and network parameters
6. WHEN H2 experiments complete THEN the system SHALL generate connectivity impact analysis reports

### Requirement 11

**User Story:** As a researcher, I want to implement H3 dimensionless parameter testing scenarios, so that I can identify phase transitions in cognitive mode activation.

#### Acceptance Criteria

1. WHEN implementing H3.1 Parameter Grid Search THEN the system SHALL test 175 combinations of conflict_intensity × recovery_period × connectivity_rate
2. WHEN calculating cognitive pressure THEN the system SHALL use formula: (conflict × connectivity) / (recovery/30.0)
3. WHEN implementing H3.2 Phase Transition Identification THEN the system SHALL generate 50 scenarios with cognitive_pressure from 0 to 2
4. WHEN analyzing H3 results THEN the system SHALL detect S2 activation threshold and fit sigmoid transition curves
5. IF phase transitions are not detected THEN the system SHALL expand parameter ranges and increase resolution
6. WHEN H3 experiments complete THEN the system SHALL generate phase diagram visualizations and critical point analysis

### Requirement 12

**User Story:** As a researcher, I want to implement H4 population diversity scenarios, so that I can test whether mixed S1/S2 populations outperform homogeneous populations.

#### Acceptance Criteria

1. WHEN implementing H4.1 Adaptive Shock Response THEN the system SHALL create dynamic event timeline: conflict→route_closure→camp_full→new_camp
2. WHEN configuring H4 populations THEN the system SHALL implement pure_s1, pure_s2, balanced, and realistic population compositions
3. WHEN implementing H4.2 Information Cascade Test THEN the system SHALL track S1 "scout" and S2 "follower" behavior interactions
4. WHEN analyzing H4 results THEN the system SHALL measure resilience, adaptation speed, and collective performance
5. IF diversity advantages are not detected THEN the system SHALL validate population compositions and shock parameters
6. WHEN H4 experiments complete THEN the system SHALL generate diversity advantage analysis and information cascade reports

### Requirement 13

**User Story:** As a researcher, I want real FLEE integration with cognitive modeling, so that I can run authentic agent-based simulations with dual-process decision-making.

#### Acceptance Criteria

1. WHEN enhancing FLEE Person class THEN the system SHALL add cognitive_state, system2_capable, and connection_count attributes
2. WHEN agents make route decisions THEN the system SHALL implement cognitive decision-making logic in selectRoute method
3. WHEN agents share information THEN the system SHALL implement information sharing mechanics for connected agents
4. WHEN tracking cognitive behavior THEN the system SHALL output cognitive_tracking.csv, decision_log.csv, and metrics_summary.json
5. IF cognitive integration breaks existing FLEE functionality THEN the system SHALL maintain backward compatibility
6. WHEN cognitive simulations complete THEN the system SHALL validate output format compatibility with analysis tools

### Requirement 14

**User Story:** As a researcher, I want automated hypothesis testing pipeline, so that I can systematically validate dual-process theory predictions across all scenarios.

#### Acceptance Criteria

1. WHEN running hypothesis scenarios THEN the system SHALL execute all H1, H2, H3, H4 scenarios systematically
2. WHEN processing results THEN the system SHALL perform hypothesis-specific statistical analysis
3. WHEN comparing cognitive modes THEN the system SHALL test for significant differences in key metrics
4. WHEN generating reports THEN the system SHALL create hypothesis validation summaries with effect sizes
5. IF hypothesis predictions are not supported THEN the system SHALL provide detailed analysis of discrepancies
6. WHEN hypothesis testing completes THEN the system SHALL generate publication-ready results and visualizations

### Requirement 15

**User Story:** As a researcher, I want dimensionless parameter analysis and visualization, so that I can make results generalizable across different scales and contexts.

#### Acceptance Criteria

1. WHEN analyzing parameters THEN the system SHALL identify and compute dimensionless parameter combinations
2. WHEN creating dimensionless parameters THEN the system SHALL use cognitive_pressure = (conflict_intensity × connectivity) / recovery_time as primary scaling variable
3. WHEN visualizing results THEN the system SHALL create dimensionless parameter space plots showing universal scaling relationships
4. WHEN comparing scenarios THEN the system SHALL demonstrate data collapse when plotted against dimensionless parameters
5. IF dimensionless scaling is not achieved THEN the system SHALL identify missing scaling variables and suggest parameter modifications
6. WHEN publishing results THEN the system SHALL provide dimensionless parameter tables for reproducibility across different contexts

### Requirement 16

**User Story:** As a researcher, I want spatial movement visualizations, so that I can understand how agents move through the network and identify spatial patterns in cognitive decision-making.

#### Acceptance Criteria

1. WHEN generating spatial visualizations THEN the system SHALL create network layout plots showing agent movement flows
2. WHEN displaying movement patterns THEN the system SHALL use different colors/styles for S1 vs S2 agent trajectories
3. WHEN showing temporal evolution THEN the system SHALL create animated visualizations of agent movement over time
4. WHEN analyzing spatial patterns THEN the system SHALL generate heatmaps of location occupancy and transition frequencies
5. IF spatial patterns are unclear THEN the system SHALL provide interactive visualizations with zoom and filtering capabilities
6. WHEN comparing cognitive modes THEN the system SHALL create side-by-side spatial comparison visualizations

### Requirement 17

**User Story:** As a researcher, I want individual agent tracking capabilities, so that I can achieve refined understanding of agent movement patterns and decision-making processes, while managing large output file sizes.

#### Acceptance Criteria

1. WHEN enabling individual agent tracking THEN the system SHALL record complete movement history for each agent
2. WHEN tracking individual decisions THEN the system SHALL log decision factors, timing, and cognitive state for each agent choice
3. WHEN managing large output files THEN the system SHALL provide configurable tracking levels (summary, detailed, full)
4. WHEN storing individual data THEN the system SHALL use efficient file formats (HDF5, Parquet) to minimize storage requirements
5. IF output files become too large THEN the system SHALL provide sampling options and data compression
6. WHEN analyzing individual trajectories THEN the system SHALL create agent-level analysis tools and trajectory clustering methods

## Phase 3: Real-World Case Study Requirements

### Requirement 18

**User Story:** As a researcher, I want to evaluate dual-process theory using real UNHCR displacement data, so that I can assess the practical relevance and explanatory power of the cognitive modeling framework.

#### Acceptance Criteria

1. WHEN implementing real-world scenarios THEN the system SHALL use authentic UNHCR refugee data and conflict event databases
2. WHEN creating South Sudan case study THEN the system SHALL implement actual displacement routes, camp locations, and capacity constraints
3. WHEN calibrating model parameters THEN the system SHALL fit dual-process parameters to observed displacement patterns with uncertainty quantification
4. WHEN evaluating predictions THEN the system SHALL assess all four hypotheses (H1-H4) against real refugee behavior data
5. IF model predictions deviate from observations THEN the system SHALL provide detailed analysis of discrepancies, model limitations, and alternative explanations
6. WHEN generating case study results THEN the system SHALL create publication-ready analysis with appropriate caveats and policy insights

### Requirement 19

**User Story:** As a researcher, I want to create a reproducible research package, so that other researchers can apply the dual-process framework to different conflict scenarios and validate results independently.

#### Acceptance Criteria

1. WHEN packaging research outputs THEN the system SHALL include complete data, code, analysis scripts, and documentation
2. WHEN documenting methodology THEN the system SHALL provide detailed instructions for applying framework to new conflict scenarios
3. WHEN creating replication materials THEN the system SHALL ensure all results can be reproduced with provided code and data
4. WHEN generating final publication THEN the system SHALL combine stylized scenarios (Phase 2) with real-world validation (Phase 3)
5. IF replication fails THEN the system SHALL provide troubleshooting guide and technical support documentation
6. WHEN distributing research package THEN the system SHALL ensure compliance with data privacy and ethical research standards