# Flee Dual Process Experiments Framework

A comprehensive experimental framework for testing Dual Process Theory in the Flee refugee movement model.

## Overview

This framework enables researchers to systematically study how different cognitive modes (System 1 vs System 2 thinking) affect refugee movement patterns across various network topologies and conflict scenarios.

## Directory Structure

```
flee_dual_process/
├── __init__.py                 # Main package initialization
├── topology_generator.py       # Network topology generation
├── scenario_generator.py       # Conflict scenario generation  
├── config_manager.py          # Configuration management
├── utils.py                   # Shared utilities
├── README.md                  # This file
├── topologies/                # Generated network structures
│   ├── linear/               # Chain topologies
│   ├── star/                 # Hub-and-spoke networks
│   ├── tree/                 # Hierarchical branching
│   └── grid/                 # Rectangular grids
├── scenarios/                # Conflict pattern definitions
│   ├── baseline/             # Standard scenarios
│   ├── spike_conflict/       # Sudden onset conflicts
│   ├── gradual_conflict/     # Escalating conflicts
│   └── cascading_conflict/   # Spreading conflicts
├── configs/                  # Experimental configurations
│   ├── cognitive_modes/      # S1/S2/Dual settings
│   └── parameter_sweeps/     # Systematic variations
└── results/                  # Auto-generated outputs
```

## Core Components

### 1. Topology Generator
- **LinearTopologyGenerator**: Creates chain topologies
- **StarTopologyGenerator**: Creates hub-and-spoke networks  
- **TreeTopologyGenerator**: Creates hierarchical branching structures
- **GridTopologyGenerator**: Creates rectangular grid networks

### 2. Scenario Generator
- **SpikeConflictGenerator**: Sudden high-intensity conflicts
- **GradualConflictGenerator**: Linearly escalating conflicts
- **CascadingConflictGenerator**: Network-spreading conflicts
- **OscillatingConflictGenerator**: Cyclically varying conflicts

### 3. Configuration Manager
- Manages cognitive mode configurations (S1-only, S2-disconnected, S2-full, dual-process)
- Generates parameter sweeps and factorial designs
- Creates Flee-compatible simsetting.yml files

### 4. Utilities
- **CSVUtils**: Flee-format CSV I/O operations
- **ValidationUtils**: Configuration and data validation
- **LoggingUtils**: Experiment logging and progress tracking
- **FileUtils**: File and directory operations

## Cognitive Modes

The framework supports four cognitive modes:

1. **S1-only**: Pure System 1 (fast, intuitive) decision-making
2. **S2-disconnected**: System 2 active but no social connectivity
3. **S2-full**: System 2 with full social connectivity
4. **Dual-process**: Both systems active with configurable thresholds

## Usage

```python
from flee_dual_process import TopologyGenerator, ConflictScenarioGenerator, ConfigurationManager

# Create topology
topo_gen = LinearTopologyGenerator(base_config)
locations_file, routes_file = topo_gen.generate_linear(
    n_nodes=5, segment_distance=50.0, start_pop=10000, pop_decay=0.8
)

# Create conflict scenario  
scenario_gen = SpikeConflictGenerator(locations_file)
conflicts_file = scenario_gen.generate_spike_conflict(
    origin="Town_A", start_day=30, peak_intensity=0.9
)

# Create configuration
config_mgr = ConfigurationManager(base_template)
config = config_mgr.create_cognitive_config("dual_process")
config_mgr.create_simsetting_yml(config, "experiment/simsetting.yml")
```

## Requirements

This framework integrates with the existing Flee codebase and requires:
- Python 3.7+
- PyYAML for configuration management
- pandas for data processing
- Standard library modules (csv, logging, os, etc.)

## Implementation Status

This is the initial framework structure. Individual components will be implemented in subsequent tasks:
- Task 2: Topology generation system
- Task 3: Conflict scenario generation system  
- Task 4: Configuration management system
- Tasks 5-11: Additional framework components

## Integration with Flee

The framework generates standard Flee input files:
- `locations.csv`: Network node definitions
- `routes.csv`: Network edge definitions
- `conflicts.csv`: Temporal conflict patterns
- `simsetting.yml`: Simulation configuration

All outputs are compatible with the existing Flee simulation engine.