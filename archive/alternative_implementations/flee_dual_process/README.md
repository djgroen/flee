# Flee Cognitive Integration - Core Components

This directory contains the essential components for integrating dual-process cognitive decision-making with Flee refugee simulations.

## Core Components

### Essential Files (Kept)
- `config_manager.py` - Manages cognitive parameter configurations
- `scenario_generator.py` - Creates basic conflict scenarios for testing
- `topology_generator.py` - Generates simple network topologies
- `utils.py` - Utility functions for CSV handling and validation

### Directories
- `configs/` - Configuration templates and cognitive mode definitions
- `topologies/` - Generated network topology files
- `results/` - Output directory for simulation results

## Archived Components

Complex experimental framework has been moved to `../flee_dual_process_archive/`:
- `scenarios/` - Complex hypothesis testing scenarios (H1-H4)
- `publication_figures/` - Advanced visualization and analysis tools
- `docs/` - Comprehensive documentation
- `complex_tests/` - Advanced testing framework
- `complex_analysis/` - Hypothesis analysis and experimental tools

## Current Focus

This cleaned structure focuses on:
1. **Basic Flee Integration** - Getting cognitive parameters to work in Flee
2. **Simple Cognitive Modes** - System 1 vs System 2 decision-making
3. **Minimal Testing** - Validating that cognitive differences are detectable
4. **Core Functionality** - Essential tools without complex experimental overhead

## Next Steps

1. Fix basic Flee execution issues
2. Implement cognitive decision logic in Flee Person class
3. Validate behavioral differences between S1 and S2 modes
4. Build simple test scenarios

Once the core integration is working, we can gradually reintroduce more complex experimental features from the archive as needed.