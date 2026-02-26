# Project Structure

## Core Package (`flee/`)

- **flee.py**: Main simulation engine with Person, Location, and Link classes
- **pflee.py**: Parallel version of the simulation engine using MPI
- **pmicro_flee.py**: Microscale parallel simulation for multiscale coupling
- **InputGeography.py**: Handles loading and parsing of geographical input data
- **SimulationSettings.py**: Configuration management for simulation parameters
- **Diagnostics.py**: Output generation and data collection utilities

### Specialized Modules
- **datamanager/**: CSV data handling, date calculations, refugee data processing
- **postprocessing/**: Analysis tools, plotting utilities, diagnostic calculations
- **preprocessing/**: Data preparation tools (e.g., ACLED conflict data conversion)
- **runscripts/**: Standard execution scripts for different simulation modes

## Input Data Structure

### Conflict Scenarios (`conflict_input/`)
Each scenario (burundi, car, ethiopia, mali, ssudan, syria) contains:
- **locations.csv**: Geographical locations and their properties
- **routes.csv**: Connections between locations with travel costs
- **conflicts.csv**: Conflict events with dates and intensities
- **closures.csv**: Border/route closures over time
- **sim_period.csv**: Simulation time period definition
- **registration_corrections.csv**: Data corrections for validation

### Validation Data (`conflict_validation/`)
Real-world refugee data for model validation:
- **refugees.csv**: Actual refugee numbers by location and date
- **data_layout.csv**: Metadata describing data structure
- **[country]-[camp].csv**: Camp-specific refugee arrival data

## Test Structure

- **tests/**: Unit tests for core functionality
- **tests_mpi/**: MPI-specific parallel tests
- **test_data/**: Sample datasets for testing
- **flee_benchmark_tests/**: Performance benchmarking tests

## Multiscale Simulations (`multiscale/`)

- **run_mscale.py**: Main multiscale simulation runner
- **coupling.py**: MUSCLE3 integration for macro-micro coupling
- **[scenario]-mscale/**: Multiscale-specific input configurations

## Documentation (`docs/`)

- **index.md**: Main documentation entry point
- **Installation_and_Testing.md**: Setup and testing instructions
- **Simulation_*.md**: Various simulation guides and tutorials
- **code_reference/**: Auto-generated API documentation
- **images/**: Documentation assets and diagrams

## Configuration Files

- **.linter_cfg/**: All code quality tool configurations
- **mkdocs.yml**: Documentation site configuration
- **setup.py**: Package installation and metadata
- **requirements.txt**: Python dependencies
- **Makefile**: Development workflow automation

## Experimental Features (`flee_dual_process/`)

New dual-process cognitive modeling extension with:
- **config_manager.py**: Configuration management
- **scenario_generator.py**: Automated scenario creation
- **topology_generator.py**: Network topology generation
- **configs/**: Cognitive mode and parameter sweep configurations
- **scenarios/**: Pre-built simulation scenarios
- **topologies/**: Network topology definitions