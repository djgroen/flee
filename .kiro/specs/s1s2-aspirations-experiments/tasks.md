# Implementation Plan: S1/S2 Refugee Displacement Experiments

## Augmenting Existing Flee Cognitive System

## Week 1: Integrate with Existing S1/S2 System

- [x] 1. Create refugee decision tracker that hooks into existing calculateMoveChance()

  - Augment existing flee/moving.py calculateMoveChance() function
  - Use existing system2_active return value to track S1 vs S2 decisions
  - Hook into existing Person.log_decision() method for refugee-specific logging
  - Leverage existing Person.calculate_cognitive_pressure() for activation logic

- [x] 1.1 Test existing S1/S2 system with refugee scenarios

  - Use existing TwoSystemDecisionMaking flag in SimulationSettings
  - Test existing conflict_threshold and cognitive pressure calculations
  - Validate existing System 2 route planning enhancements work
  - Confirm existing Person.get_system2_capable() logic is appropriate

- [x] 1.2 Create refugee scenario runner using existing Flee infrastructure

  - Use existing Ecosystem, Location, Person, and Link classes
  - Leverage existing selectRoute() and calculateLinkWeight() functions
  - Test with existing AwarenessLevel and route planning parameters
  - Ensure compatibility with existing move_rules and SimulationSettings

- [x] 1.3 Implement evacuation timing test with existing system
  - Create scenario using existing Location.conflict and time_of_conflict
  - Use existing Person.timesteps_since_departure for timing analysis
  - Test existing cognitive_pressure calculation with gradual conflict escalation
  - Measure S1 vs S2 differences using existing decision logging

## Week 2: Minimal Refugee-Specific Enhancements

- [x] 2. Add minimal refugee attributes to existing Person class

  - Extend existing Person.**init**() with refugee-specific attributes
  - Add safety_threshold, risk_tolerance, mobility to existing attributes dict
  - Ensure backward compatibility with existing Flee simulations
  - Use existing attribute system without breaking current functionality

- [x] 2.1 Enhance existing route selection with refugee logic

  - Modify existing selectRoute() to include refugee decision factors
  - Augment existing getEndPointScore() with safety vs distance trade-offs
  - Use existing System 2 parameter modifications for analytical thinking
  - Maintain existing route pruning and weight calculation logic

- [x] 2.2 Implement bottleneck scenario using existing capacity system

  - Use existing Location.capacity and getCapMultiplier() for bottlenecks
  - Test existing route planning with capacity constraints
  - Leverage existing System 2 awareness level increases for planning
  - Measure route efficiency using existing distance calculations

- [x] 2.3 Test refugee enhancements with existing validation methods
  - Run scenarios using existing Flee simulation loop
  - Use existing agent movement and location update methods
  - Validate using existing diagnostic and logging capabilities
  - Ensure existing test suite continues to pass

## Week 3: Information Sharing with Existing Network System

- [x] 3. Enhance existing information sharing for refugee contexts

  - Extend existing Person.share_information_with_connected_agents()
  - Use existing social connectivity and connection update methods
  - Augment existing \_safety_info sharing with refugee-relevant data
  - Build on existing Person.update_social_connectivity() logic

- [x] 3.1 Create information network scenario using existing infrastructure

  - Use existing agent connectivity and information sharing mechanisms
  - Test existing network information propagation with refugee scenarios
  - Leverage existing \_shared_route and \_temp_route attributes
  - Measure information utilization using existing decision history

- [x] 3.2 Test S1 vs S2 information processing differences
  - Use existing System 2 analytical processing vs S1 heuristics
  - Test existing route information sharing between connected agents
  - Validate existing information integration in route selection
  - Measure network effects using existing connectivity tracking

## Week 4: Comprehensive Validation and Analysis

- [x] 4. Run comprehensive validation using existing Flee analysis tools

  - Execute all scenarios using existing simulation infrastructure
  - Use existing diagnostic output and agent tracking capabilities
  - Leverage existing CSV output formats for data analysis
  - Generate results compatible with existing Flee analysis pipelines

- [x] 4.1 Create analysis pipeline using existing data structures

  - Use existing Person.decision_history for S1 vs S2 analysis
  - Leverage existing agent attributes and location data
  - Build on existing diagnostic and logging infrastructure
  - Create visualizations using existing data output formats

- [x] 4.2 Validate backward compatibility with existing Flee

  - Ensure all existing Flee functionality remains unchanged
  - Test with existing conflict scenarios (burundi, syria, etc.)
  - Validate existing test suite passes with new enhancements
  - Confirm existing analysis tools work with enhanced system

- [x] 4.3 Prepare South Sudan integration using existing data formats
  - Use existing conflict_input data structure and CSV formats
  - Leverage existing UNHCR validation data integration capabilities
  - Build on existing location, route, and conflict data processing
  - Ensure compatibility with existing multiscale simulation framework

## Technical Integration Principles

### 🔧 **Augmentation, Not Replacement**

- Hook into existing calculateMoveChance() and selectRoute() functions
- Extend existing Person class attributes and methods
- Use existing SimulationSettings and move_rules infrastructure
- Maintain existing CSV input/output formats

### 🔄 **Backward Compatibility**

- All existing Flee simulations must continue to work unchanged
- New features activated only when refugee-specific flags are enabled
- Existing test suite must pass with enhancements
- Existing analysis tools must work with enhanced data

### 📊 **Leverage Existing Infrastructure**

- Use existing cognitive_pressure and system2_capable methods
- Build on existing information sharing and social connectivity
- Leverage existing route planning and awareness level logic
- Extend existing decision logging and diagnostic capabilities

### 🎯 **Minimal, Focused Changes**

- Add only essential refugee-specific attributes and logic
- Focus on S1 vs S2 differences that matter for displacement
- Keep implementation simple and well-integrated
- Avoid complex new frameworks that duplicate existing functionality

## Success Criteria

- ✅ **Integration**: Seamlessly works with existing Flee system
- ✅ **Compatibility**: All existing functionality preserved
- ✅ **Enhancement**: Clear S1 vs S2 differences in refugee contexts
- ✅ **Validation**: Statistical significance in behavioral differences
- ✅ **Usability**: Easy to enable/disable refugee-specific features

This approach ensures we build on the solid foundation of the existing Flee S1/S2 system while adding focused enhancements for refugee displacement research.
