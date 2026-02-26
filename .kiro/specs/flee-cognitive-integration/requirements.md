# Flee Cognitive Integration Requirements

## Introduction

This feature implements the core integration between Flee's agent-based refugee simulation and dual-process cognitive decision-making. The primary goal is to ensure that System 1 (fast, heuristic) and System 2 (slow, analytical) cognitive modes actually work in Flee simulations and produce measurably different refugee movement behaviors.

## Problem Statement

Currently, our dual-process cognitive framework has fundamental integration issues:
1. **Flee execution problems** - Simulations complete but produce no output files
2. **Parameter passing failures** - Cognitive parameters aren't reaching Flee properly  
3. **S1/S2 modes not working** - No behavioral differences detected between cognitive modes
4. **Import/module issues** - Framework has import problems preventing execution

## Requirements

### Requirement 1: Basic Flee Execution

**User Story:** As a researcher, I want Flee simulations to execute successfully and produce output files, so that I can validate cognitive behavior differences.

#### Acceptance Criteria

1. WHEN I run a basic Flee simulation THEN the system SHALL produce out.csv and agents.out files
2. WHEN simulation completes THEN output files SHALL contain population movement data
3. WHEN using cognitive parameters THEN Flee SHALL load parameters without errors
4. WHEN simulation fails THEN the system SHALL provide clear error messages
5. IF output directory is empty THEN the system SHALL diagnose and report the cause

### Requirement 2: Cognitive Parameter Integration

**User Story:** As a researcher, I want cognitive parameters to be correctly passed to Flee, so that different cognitive modes affect agent behavior.

#### Acceptance Criteria

1. WHEN I configure TwoSystemDecisionMaking=True THEN Flee SHALL enable cognitive switching logic
2. WHEN I set conflict_threshold=0.5 THEN agents SHALL activate System 2 when cognitive pressure > 0.5
3. WHEN I configure average_social_connectivity THEN it SHALL affect cognitive pressure calculations
4. WHEN parameters are invalid THEN the system SHALL validate and reject with clear errors
5. IF parameter loading fails THEN the system SHALL log specific parameter names and values

### Requirement 3: System 1 vs System 2 Behavioral Differences

**User Story:** As a researcher, I want System 1 and System 2 modes to produce clearly different movement behaviors, so that I can validate dual-process theory.

#### Acceptance Criteria

1. WHEN agents use System 1 THEN they SHALL make faster, more heuristic movement decisions
2. WHEN agents use System 2 THEN they SHALL make slower, more analytical movement decisions  
3. WHEN comparing S1 vs S2 modes THEN evacuation timing SHALL be statistically different
4. WHEN measuring destination choices THEN S1 and S2 SHALL show different optimality patterns
5. IF no behavioral differences detected THEN the system SHALL diagnose cognitive switching logic

### Requirement 4: Cognitive Pressure Calculation

**User Story:** As a researcher, I want cognitive pressure to be calculated correctly, so that System 2 activation occurs when theoretically predicted.

#### Acceptance Criteria

1. WHEN calculating cognitive pressure THEN formula SHALL be (conflict_intensity × connectivity) / recovery_period
2. WHEN pressure exceeds threshold THEN System 2 SHALL activate for that agent
3. WHEN pressure is below threshold THEN agents SHALL use System 1 decision-making
4. WHEN connectivity changes THEN pressure calculations SHALL update accordingly
5. IF pressure calculations are wrong THEN the system SHALL log pressure values for debugging

### Requirement 5: Minimal Working Scenarios

**User Story:** As a researcher, I want simple test scenarios that validate cognitive differences, so that I can confirm the framework works before building complex experiments.

#### Acceptance Criteria

1. WHEN I run s1_only scenario THEN all agents SHALL use System 1 throughout simulation
2. WHEN I run s2_full scenario THEN all agents SHALL use System 2 throughout simulation  
3. WHEN I run dual_process scenario THEN agents SHALL switch between S1 and S2 based on pressure
4. WHEN comparing scenarios THEN movement patterns SHALL be measurably different
5. IF scenarios produce identical results THEN the system SHALL identify configuration errors

### Requirement 6: Debug and Validation Tools

**User Story:** As a researcher, I want debugging tools to diagnose cognitive integration issues, so that I can identify and fix problems quickly.

#### Acceptance Criteria

1. WHEN debugging cognitive switching THEN the system SHALL log System 2 activation events
2. WHEN validating parameters THEN the system SHALL show parameter loading in Flee
3. WHEN tracking decisions THEN the system SHALL log decision factors for each agent
4. WHEN simulation fails THEN the system SHALL provide diagnostic information
5. IF integration is broken THEN debug tools SHALL identify specific failure points

## Technical Requirements

### TR-1: Flee Integration Points
- Cognitive parameters must be loaded via SimulationSettings.py
- Decision logic must be integrated into Person.selectRoute() method
- Cognitive pressure calculation must be accessible to agents
- System 2 activation must be trackable and loggable

### TR-2: Parameter Validation
- TwoSystemDecisionMaking boolean flag validation
- conflict_threshold numeric range validation (0.0 to 2.0)
- average_social_connectivity range validation (0.0 to 1.0)
- Parameter type checking and conversion

### TR-3: Output Requirements
- Standard Flee output files (out.csv, agents.out)
- Optional cognitive tracking files (cognitive_states.csv)
- Debug logging for parameter loading and decision-making
- Error reporting for failed simulations

### TR-4: Performance Requirements
- Single simulation must complete within 2 minutes
- Cognitive calculations must not significantly slow Flee
- Memory usage must remain reasonable for 1000+ agents
- Error handling must not corrupt simulation state

## Success Metrics

### Quantitative Metrics
1. **Execution Success Rate**: >95% of simulations complete successfully
2. **Behavioral Differentiation**: Cohen's d > 0.5 between S1 and S2 modes
3. **Parameter Loading**: 100% of cognitive parameters loaded correctly
4. **Performance Impact**: <20% slowdown compared to standard Flee

### Qualitative Metrics
1. **Scientific Validity**: Results align with dual-process theory predictions
2. **Reproducibility**: Same parameters produce consistent results
3. **Debuggability**: Clear diagnostic information when issues occur
4. **Integration Quality**: Cognitive logic integrates cleanly with Flee

## Risk Assessment

### High Risk
- **Deep Flee Integration**: Modifying core Flee decision-making logic
- **Parameter Passing Complexity**: Multiple integration points between framework and Flee
- **Behavioral Validation**: Difficult to verify cognitive differences are meaningful

### Medium Risk
- **Performance Impact**: Cognitive calculations may slow simulations
- **Import Dependencies**: Module import issues between framework and Flee
- **Configuration Complexity**: Multiple cognitive parameters must work together

### Low Risk
- **Basic Flee Functionality**: Standard Flee features are well-established
- **Parameter Validation**: Standard validation patterns available
- **Debug Logging**: Straightforward to implement diagnostic tools

## Dependencies

### Internal Dependencies
- Flee simulation engine (flee.py, Person class)
- SimulationSettings.py for parameter loading
- Cognitive parameter configuration system

### External Dependencies
- Python scientific computing stack (NumPy, SciPy)
- Standard Flee dependencies (NetworkX, etc.)
- Testing frameworks for validation

## Definition of Done

✅ **Complete** when:
1. Basic Flee simulations execute successfully and produce output files
2. Cognitive parameters are correctly loaded and used by Flee
3. System 1 and System 2 modes produce statistically different behaviors
4. Cognitive pressure calculations work as theoretically predicted
5. Simple test scenarios validate cognitive switching logic
6. Debug tools can diagnose integration issues
7. All acceptance criteria are met and tested
8. Performance meets specified requirements
9. Integration is documented and ready for hypothesis testing

## Phase Approach

### Phase 1: Fix Basic Execution (1 week)
- Diagnose and fix Flee output file generation
- Ensure parameter loading works correctly
- Get one cognitive mode working reliably

### Phase 2: Validate Cognitive Differences (1 week)  
- Implement System 1 vs System 2 decision logic
- Verify behavioral differences are detectable
- Add cognitive pressure calculation and activation

### Phase 3: Complete Integration (1 week)
- Implement dual-process switching mode
- Add debug and validation tools
- Create simple test scenarios for validation

This focused approach ensures we have a working foundation before building complex experimental frameworks.