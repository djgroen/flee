# Authentic Flee Simulation Requirements

## Introduction

This specification ensures that all S1/S2 diagnostic tools ONLY use authentic data from real Flee simulations. Creating fake or simulated data is dangerous and misleading for scientific research.

## Requirements

### Requirement 1: Authentic Data Validation

**User Story:** As a researcher, I want to ensure that all diagnostic data comes from real Flee simulations, so that my analysis is scientifically valid and not based on fake data.

#### Acceptance Criteria

1. WHEN I run any S1/S2 diagnostic tool THEN the system SHALL verify that data comes from actual `ecosystem.evolve()` calls
2. WHEN data is not from a real Flee simulation THEN the system SHALL display a clear ERROR and refuse to proceed
3. WHEN data source is uncertain THEN the system SHALL display a WARNING and require explicit user confirmation
4. WHEN displaying any plot or analysis THEN the system SHALL include metadata showing the data source verification status

### Requirement 2: Multiple Flee Instance Management

**User Story:** As a researcher, I want to run multiple Flee simulation instances and save their outputs separately, so that I can compare different scenarios or parameter sets.

#### Acceptance Criteria

1. WHEN I run multiple Flee simulations THEN each simulation SHALL save output to a unique directory
2. WHEN simulation directories are created THEN they SHALL include timestamp and scenario identifier
3. WHEN simulation completes THEN the system SHALL save both standard Flee output (out.csv, agents.out) AND S1/S2 cognitive data
4. WHEN I analyze results THEN I SHALL be able to specify which simulation instance to analyze

### Requirement 3: Standard Flee Output Compliance

**User Story:** As a researcher, I want S1/S2 simulations to produce standard Flee output files, so that I can use existing Flee analysis tools alongside S1/S2 diagnostics.

#### Acceptance Criteria

1. WHEN I run an S1/S2 simulation THEN the system SHALL produce standard out.csv file in Flee format
2. WHEN agents are tracked THEN the system SHALL optionally produce agents.out file if logging is enabled
3. WHEN simulation uses input CSV files THEN the system SHALL follow standard Flee input format (locations.csv, routes.csv, etc.)
4. WHEN simulation completes THEN output SHALL be compatible with existing Flee postprocessing tools

### Requirement 4: Proper Flee Simulation Construction

**User Story:** As a researcher, I want to construct Flee simulations using proper input files and methods, so that my simulations follow established Flee methodology.

#### Acceptance Criteria

1. WHEN creating a simulation THEN I SHALL use proper locations.csv and routes.csv input files
2. WHEN spawning agents THEN the system SHALL use Flee's spawning mechanisms (spawning.add_initial_refugees, spawning.spawn_daily_displaced)
3. WHEN running simulation THEN the system SHALL call ecosystem.evolve() for each time step
4. WHEN simulation has conflicts THEN the system SHALL use conflicts.csv or set conflict attributes properly
5. WHEN simulation has closures THEN the system SHALL use closures.csv format

### Requirement 5: Data Provenance Tracking

**User Story:** As a researcher, I want complete provenance tracking of simulation data, so that I can verify the authenticity and reproducibility of my results.

#### Acceptance Criteria

1. WHEN simulation starts THEN the system SHALL record simulation metadata (start time, parameters, input files)
2. WHEN simulation runs THEN the system SHALL log that ecosystem.evolve() was called for each time step
3. WHEN simulation completes THEN the system SHALL create a provenance.json file with complete simulation details
4. WHEN analyzing data THEN the system SHALL verify provenance before proceeding
5. WHEN data lacks provenance THEN the system SHALL refuse to analyze and display clear error

### Requirement 6: Multi-Instance Output Management

**User Story:** As a researcher, I want to organize outputs from multiple simulation runs, so that I can systematically compare results across different scenarios.

#### Acceptance Criteria

1. WHEN running multiple simulations THEN each SHALL save to directory format: `flee_output_YYYY-MM-DD_HH-MM-SS_<scenario_name>/`
2. WHEN simulation directory is created THEN it SHALL contain subdirectories: `standard_flee/` and `s1s2_diagnostics/`
3. WHEN simulation completes THEN `standard_flee/` SHALL contain out.csv, agents.out (if enabled), and input files copy
4. WHEN S1/S2 analysis runs THEN `s1s2_diagnostics/` SHALL contain cognitive analysis plots and data
5. WHEN multiple runs exist THEN the system SHALL provide tools to list, compare, and analyze across runs

## Technical Requirements

### TR-1: Data Validation Requirements

- Authentic data verification through ecosystem.evolve() call tracking
- Provenance metadata in JSON format
- Clear error messages for fake/missing data
- Warning system for uncertain data sources

### TR-2: File Management Requirements

- Standard Flee output format compliance (out.csv, agents.out)
- Proper input file format support (locations.csv, routes.csv, conflicts.csv, closures.csv)
- Timestamped output directories for multiple runs
- Organized subdirectory structure for different data types

### TR-3: Integration Requirements

- Compatibility with existing Flee postprocessing tools
- Support for standard Flee simulation construction methods
- Integration with Flee's spawning and evolution mechanisms
- Proper handling of Flee's configuration system (simsetting.yml)