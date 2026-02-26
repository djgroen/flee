# Implementation Plan

## Phase 1: Clean Up and Basic Execution

- [x] 1. Clean up flee_dual_process directory structure
  - Remove experimental files built on faulty foundations
  - Keep only essential components: config_manager.py, scenario_generator.py, topology_generator.py
  - Create clean directory structure for core integration
  - _Requirements: All requirements - need clean foundation_

- [x] 1.1 Archive existing experimental code
  - Create archive directory for existing complex experimental framework
  - Move scenarios/, publication_figures/, and complex test files to archive
  - Keep only core utilities that will be needed for basic integration
  - _Requirements: 1, 2, 3, 4, 5, 6_

- [x] 1.2 Create minimal core structure
  - Keep config_manager.py (for parameter management)
  - Keep scenario_generator.py (for basic scenario creation)
  - Keep topology_generator.py (for simple network creation)
  - Remove all complex hypothesis testing and analysis code
  - _Requirements: 1, 2, 3_

- [x] 2. Diagnose basic Flee execution issues
  - Create simple test script to run basic Flee simulation
  - Identify why simulations complete but produce no output files
  - Test with minimal scenario (origin → single camp)
  - Document specific execution problems found
  - _Requirements: 1_

- [x] 2.1 Test Flee import and basic functionality
  - Create test script to verify Flee can be imported correctly
  - Test basic Flee classes (Person, Location, Link) instantiation
  - Verify Flee can load scenario files (locations.csv, routes.csv, etc.)
  - Identify any import path or dependency issues
  - _Requirements: 1, 6_

- [x] 2.2 Create minimal working Flee scenario
  - Generate simplest possible scenario: 1 origin, 1 camp, 100 agents
  - Test that this scenario produces output files (out.csv, agents.out)
  - Verify population movement occurs (agents move from origin to camp)
  - Establish baseline working Flee execution
  - _Requirements: 1, 5_

- [ ] 3. Implement parameter loading system
  - Enhance SimulationSettings.py to include cognitive parameters
  - Add parameter validation for cognitive parameter ranges
  - Create test to verify parameters are loaded correctly in Flee
  - Add debug logging to show parameter loading process
  - _Requirements: 2_

- [ ] 3.1 Add cognitive parameters to SimulationSettings
  - Add TwoSystemDecisionMaking, conflict_threshold, average_social_connectivity
  - Add awareness_level, weight_softening parameters
  - Implement parameter validation with appropriate ranges
  - Add parameter loading debug output
  - _Requirements: 2_

- [ ] 3.2 Create parameter loading test
  - Create test scenario with cognitive parameters in simsetting.csv
  - Verify parameters are loaded into SimulationSettings.move_rules
  - Test parameter validation catches invalid values
  - Confirm parameters are accessible during simulation
  - _Requirements: 2, 6_

## Phase 2: Cognitive Decision Integration

- [ ] 4. Implement basic cognitive decision logic in Flee Person class
  - Add cognitive attributes to Person class (cognitive_state, system2_capable)
  - Implement calculate_cognitive_pressure method
  - Add update_cognitive_state method for System 2 activation
  - Create debug logging for cognitive state changes
  - _Requirements: 3, 4_

- [ ] 4.1 Add cognitive attributes to Person class
  - Add cognitive_state ("system1" or "system2")
  - Add system2_capable boolean flag
  - Add connection_count for social connectivity
  - Add last_pressure_calc for caching pressure values
  - _Requirements: 3, 4_

- [ ] 4.2 Implement cognitive pressure calculation
  - Implement formula: (conflict_intensity × connectivity) / recovery_period
  - Use base connectivity from average_social_connectivity parameter
  - Add personal connectivity based on connection_count
  - Cache pressure calculation to avoid repeated computation
  - _Requirements: 4_

- [ ] 4.3 Implement System 2 activation logic
  - Compare cognitive pressure to conflict_threshold
  - Update cognitive_state based on pressure vs threshold
  - Add debug logging for state transitions (S1→S2, S2→S1)
  - Ensure activation only occurs for system2_capable agents
  - _Requirements: 3, 4, 6_

- [ ] 5. Implement System 1 vs System 2 route selection
  - Modify Person.selectRoute to use cognitive decision-making
  - Implement _system1_route_selection (fast, heuristic)
  - Implement _system2_route_selection (slow, analytical)
  - Add decision logging for debugging
  - _Requirements: 3_

- [ ] 5.1 Implement System 1 route selection
  - Use simple heuristic: choose closest available destination
  - Add randomness based on weight_softening parameter
  - Optimize for speed over decision quality
  - Log decision factors for debugging
  - _Requirements: 3_

- [ ] 5.2 Implement System 2 route selection
  - Consider multiple factors: distance, capacity, safety
  - Use awareness_level to modify decision quality
  - Apply weighted scoring for optimal decisions
  - Add less randomness than System 1
  - _Requirements: 3_

- [ ] 5.3 Integrate cognitive route selection into selectRoute
  - Call update_cognitive_state before making decisions
  - Route to appropriate decision method based on cognitive_state
  - Maintain compatibility with existing Flee functionality
  - Add decision logging for analysis
  - _Requirements: 3, 6_

## Phase 3: Validation and Testing

- [ ] 6. Create output validation tools
  - Implement FleeOutputValidator class
  - Add validation for required output files (out.csv, agents.out)
  - Add basic metrics extraction (population movement, timing)
  - Create validation report generation
  - _Requirements: 1, 6_

- [ ] 6.1 Implement basic output validation
  - Check that required files exist and have content
  - Validate out.csv format and required columns
  - Extract basic metrics: total days, population change
  - Detect whether agent movement occurred
  - _Requirements: 1, 6_

- [ ] 6.2 Add cognitive output validation
  - Check for cognitive-specific output files if enabled
  - Validate cognitive tracking data format
  - Extract cognitive metrics: S2 activation rate, decision patterns
  - Report cognitive validation issues
  - _Requirements: 3, 6_

- [ ] 7. Create minimal test scenarios for cognitive validation
  - Create s1_only test scenario (TwoSystemDecisionMaking=False)
  - Create s2_full test scenario (high connectivity, low threshold)
  - Create dual_process test scenario (medium threshold)
  - Verify each scenario produces different movement patterns
  - _Requirements: 5_

- [ ] 7.1 Create System 1 only test scenario
  - Configure TwoSystemDecisionMaking=False
  - Set up simple origin→camp scenario with 100 agents
  - Run simulation and validate output
  - Establish baseline S1 behavior patterns
  - _Requirements: 5_

- [ ] 7.2 Create System 2 full test scenario
  - Configure high connectivity (0.8) and low threshold (0.1)
  - Use same network topology as S1 test
  - Run simulation and compare to S1 results
  - Verify S2 produces different movement patterns
  - _Requirements: 5_

- [ ] 7.3 Create dual-process test scenario
  - Configure medium threshold (0.5) for dynamic switching
  - Add conflict escalation to trigger S2 activation
  - Run simulation and verify both S1 and S2 modes are used
  - Validate cognitive switching occurs as expected
  - _Requirements: 5_

- [ ] 8. Implement debug and diagnostic tools
  - Create CognitiveDebugger class for integration diagnosis
  - Add scenario file validation
  - Add Flee import testing
  - Create comprehensive debug report generation
  - _Requirements: 6_

- [ ] 8.1 Create scenario validation tools
  - Check all required scenario files exist
  - Validate scenario file formats
  - Check cognitive parameters in simsetting.csv
  - Report missing or invalid scenario components
  - _Requirements: 6_

- [ ] 8.2 Create Flee integration testing tools
  - Test Flee import and basic functionality
  - Verify cognitive methods exist in Person class
  - Test minimal simulation execution
  - Generate integration status report
  - _Requirements: 6_

- [ ] 9. Validate behavioral differences between cognitive modes
  - Run all three test scenarios (s1_only, s2_full, dual_process)
  - Extract and compare key metrics: evacuation timing, route choices
  - Perform statistical analysis of differences
  - Generate behavioral comparison report
  - _Requirements: 3, 5_

- [ ] 9.1 Run comparative analysis
  - Execute all test scenarios with identical parameters except cognitive mode
  - Extract evacuation timing, destination choices, route efficiency
  - Calculate statistical significance of differences (t-tests, Cohen's d)
  - Verify S1 vs S2 differences are detectable and meaningful
  - _Requirements: 3, 5_

- [ ] 9.2 Generate validation report
  - Document behavioral differences found between cognitive modes
  - Report statistical significance of differences
  - Identify any scenarios where differences are not detected
  - Provide recommendations for parameter tuning if needed
  - _Requirements: 3, 5, 6_

- [ ] 10. Create integration documentation and usage guide
  - Document how to configure cognitive parameters
  - Provide examples of running cognitive simulations
  - Document troubleshooting common integration issues
  - Create guide for extending cognitive functionality
  - _Requirements: All requirements_

- [ ] 10.1 Create parameter configuration guide
  - Document all cognitive parameters and their effects
  - Provide recommended parameter ranges for different scenarios
  - Include examples of simsetting.csv configuration
  - Document parameter validation rules
  - _Requirements: 2, 5_

- [ ] 10.2 Create troubleshooting guide
  - Document common integration issues and solutions
  - Provide diagnostic steps for debugging problems
  - Include examples of using debug tools
  - Document performance considerations
  - _Requirements: 6_