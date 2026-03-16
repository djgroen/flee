# Individual Agent Tracking System

This document describes the Individual Agent Tracking system for Flee dual-process experiments, which provides comprehensive tracking and analysis of individual agent behaviors, trajectories, and decision-making patterns.

## Overview

The Individual Agent Tracking system extends Flee's existing agent logging capabilities with dual-process specific features:

- **Configurable multi-level tracking** (summary, detailed, full)
- **Efficient storage formats** (CSV, HDF5, Parquet) for large datasets
- **Cognitive state and decision tracking** for dual-process analysis
- **Integration with Flee's standard agent logs** to avoid duplication
- **Comprehensive analysis tools** for individual and population-level insights

## Key Components

### 1. Individual Agent Tracker (`individual_agent_tracker.py`)

The core tracking system that collects agent data during simulation.

**Features:**
- Multi-level tracking (summary/detailed/full)
- Configurable sampling rates for performance
- Multiple storage formats with compression
- Memory management and data validation
- Integration with Flee's existing logging system

**Usage:**
```python
from flee_dual_process.individual_agent_tracker import (
    IndividualAgentTracker, create_flee_compatible_config
)

# Create configuration based on Flee's logging level
config = create_flee_compatible_config("output", flee_agent_level=1)

# Initialize tracker
tracker = IndividualAgentTracker(config, rank=0)

# During simulation loop
tracker.track_agents(agents, time)
tracker.integrate_with_flee_agent_logs(agents, time)  # Optional

# At simulation end
tracker.close()
```

### 2. Individual Agent Analyzer (`individual_agent_analysis.py`)

Comprehensive analysis tools for agent trajectory and behavior analysis.

**Features:**
- Complete trajectory reconstruction from multiple data sources
- Movement pattern identification and clustering
- Decision-making pattern analysis
- Cognitive behavior profiling
- Individual vs aggregate comparisons
- Detailed individual agent reports

**Usage:**
```python
from flee_dual_process.individual_agent_analysis import IndividualAgentAnalyzer

# Initialize analyzer
analyzer = IndividualAgentAnalyzer("output_directory", rank=0)

# Load data
analyzer.load_flee_agent_data()
analyzer.load_dual_process_data()

# Build trajectories
trajectories = analyzer.build_agent_trajectories()

# Analyze patterns
movement_patterns = analyzer.identify_movement_patterns()
decision_clusters = analyzer.analyze_decision_making_patterns()

# Generate reports
report = analyzer.generate_individual_agent_report("agent_id")
analyzer.export_analysis_results("analysis_output")
```

## Integration with Flee's Existing System

### Flee's Standard Agent Logging

Flee 3.0 already provides comprehensive agent tracking through:
- `Diagnostics.write_agents_par()` function
- Configurable logging levels via `SimulationSettings.log_levels["agent"]`
- Standard output format: `agents.out.{rank}`

**Flee Logging Levels:**
- Level 0: No agent logging
- Level 1: Basic agent data per timestep
- Level 2: Multiple hops per timestep  
- Level 3: Detailed hop-by-hop tracking

### Dual-Process Extensions

Our system **complements** rather than replaces Flee's logging:

| Flee Standard Logs | Dual-Process Extensions |
|-------------------|------------------------|
| Location trajectories | Cognitive state transitions |
| Distance traveled | Decision-making processes |
| Agent attributes | Social network changes |
| GPS coordinates | System 2 activations |
| Movement status | Individual behavior analysis |

### Recommended Integration Strategy

1. **Enable Flee's basic logging**: Set `SimulationSettings.log_levels["agent"] = 1`
2. **Use detailed dual-process tracking**: Captures cognitive events and decisions
3. **Combine datasets for analysis**: Join on (time, agent_id) for complete picture

## Configuration Options

### Tracking Levels

**Summary Level:**
- Aggregate statistics only
- Minimal memory usage
- Recommended when Flee logging ≥ 1

**Detailed Level:**
- Key events and state changes
- Cognitive transitions and decisions
- Balanced performance/detail

**Full Level:**
- Complete individual trajectories
- All timesteps tracked
- Maximum detail for analysis

### Storage Formats

**CSV Format:**
- Human-readable
- Compatible with standard tools
- Good for small-medium datasets

**HDF5 Format:**
- Efficient for large datasets
- Hierarchical data organization
- Compression support
- Requires h5py package

**Parquet Format:**
- Columnar storage
- Excellent compression
- Fast analytical queries
- Requires pyarrow package

### Configuration Examples

```python
# Summary tracking (complements Flee logging)
config = create_summary_tracking_config("output")

# Detailed tracking with compression
config = create_detailed_tracking_config("output", "parquet")

# Full tracking for comprehensive analysis
config = create_full_tracking_config("output", "hdf5", sampling_rate=0.1)

# Automatic configuration based on Flee settings
config = create_flee_compatible_config("output", flee_agent_level)
```

## Data Structures

### Agent Trajectory
Complete trajectory data for individual agents:
```python
@dataclass
class AgentTrajectory:
    agent_id: str
    trajectory_points: List[Dict[str, Any]]    # Location/time data
    decisions: List[Dict[str, Any]]            # Decision events
    cognitive_transitions: List[Dict[str, Any]] # State changes
    social_interactions: List[Dict[str, Any]]   # Network events
    summary_stats: Dict[str, Any]              # Computed metrics
```

### Movement Pattern
Identified behavioral patterns from clustering:
```python
@dataclass
class MovementPattern:
    pattern_id: str
    agent_ids: List[str]                    # Agents in cluster
    characteristics: Dict[str, Any]         # Behavioral metrics
    cognitive_profile: Dict[str, Any]       # Cognitive tendencies
    spatial_signature: Dict[str, Any]       # Spatial behavior
```

## Output Files

### Standard Output Files

| File | Description | Format |
|------|-------------|---------|
| `agents_dual_process.out.{rank}` | Cognitive state data | CSV |
| `agent_decisions.{rank}.csv` | Decision events | CSV |
| `social_network_individual.{rank}.csv` | Social interactions | CSV |
| `agent_trajectories.{rank}.csv` | Full trajectories | CSV/HDF5/Parquet |

### Analysis Output Files

| File | Description |
|------|-------------|
| `movement_patterns.{rank}.json` | Identified movement patterns |
| `decision_clusters.{rank}.json` | Decision-making clusters |
| `agent_summaries.{rank}.csv` | Individual agent statistics |
| `individual_vs_aggregate.{rank}.json` | Population comparisons |
| `agent_report_{agent_id}.json` | Detailed individual reports |

### Integration Files

| File | Description |
|------|-------------|
| `flee_integration_guide.{rank}.md` | Integration instructions |
| `tracking_statistics.{rank}.json` | System performance metrics |
| `validation_errors.{rank}.txt` | Data validation results |

## Analysis Capabilities

### Trajectory Analysis
- Complete movement histories with GPS coordinates
- Location sequence and stay duration patterns  
- Movement velocity and consistency metrics
- Spatial exploration diversity indices

### Decision Analysis
- Decision type classification and frequency
- Confidence levels and temporal patterns
- Cognitive state during decision-making
- Decision outcome tracking and success rates

### Cognitive Behavior Analysis
- System 1/System 2 usage patterns
- Cognitive state transition analysis
- Trigger identification for state changes
- Individual cognitive profiles and clustering

### Social Network Analysis
- Connection formation and dissolution
- Information sharing and receiving patterns
- Network position and influence metrics
- Social interaction temporal dynamics

### Comparative Analysis
- Individual vs population comparisons
- Behavioral clustering and pattern identification
- Inequality metrics (Gini coefficients)
- Emergent behavior detection

## Performance Considerations

### Memory Management
- Configurable memory limits with automatic flushing
- Sampling rates to reduce data volume
- Efficient storage formats for large datasets

### Scalability
- MPI-aware design for parallel simulations
- Rank-specific output files
- Configurable timestep intervals

### Storage Optimization
- Compression options for all formats
- Incremental data writing
- Validation and integrity checking

## Example Workflows

### Basic Usage
```python
# 1. Configure tracking
config = create_detailed_tracking_config("output")
tracker = IndividualAgentTracker(config, rank=0)

# 2. Track during simulation
for time in range(simulation_steps):
    # ... simulation step ...
    tracker.track_agents(agents, time)

# 3. Finalize
tracker.close()

# 4. Analyze results
analyzer = IndividualAgentAnalyzer("output", rank=0)
analyzer.load_flee_agent_data()
analyzer.load_dual_process_data()
trajectories = analyzer.build_agent_trajectories()
patterns = analyzer.identify_movement_patterns()
analyzer.export_analysis_results("analysis")
```

### Integration with Flee Logging
```python
# Enable Flee's standard logging
SimulationSettings.log_levels["agent"] = 1

# Configure compatible dual-process tracking
config = create_flee_compatible_config("output", flee_agent_level=1)
tracker = IndividualAgentTracker(config, rank=0)

# During simulation
for time in range(simulation_steps):
    # Standard Flee logging
    write_agents_par(rank, agents, time)
    
    # Dual-process extensions
    tracker.track_agents(agents, time)
    tracker.integrate_with_flee_agent_logs(agents, time)

# Analysis combines both datasets
analyzer = IndividualAgentAnalyzer("output", rank=0)
analyzer.load_flee_agent_data()      # Standard Flee data
analyzer.load_dual_process_data()    # Dual-process extensions
```

### Large-Scale Analysis
```python
# Efficient configuration for large simulations
config = TrackingConfigBuilder() \
    .set_tracking_level(TrackingLevel.DETAILED) \
    .set_storage_format(StorageFormat.HDF5) \
    .set_sampling_rate(0.1) \
    .set_memory_limit(500) \
    .enable_compression(True) \
    .build()

tracker = IndividualAgentTracker(config, rank=0)
```

## Requirements

### Core Dependencies
- numpy
- pandas
- pathlib (Python 3.4+)

### Optional Dependencies
- **h5py**: For HDF5 storage format
- **pyarrow**: For Parquet storage format
- **scikit-learn**: For advanced clustering analysis
- **matplotlib/seaborn**: For visualization (in analysis tools)
- **networkx**: For social network analysis

### Installation
```bash
# Core functionality
pip install numpy pandas

# Enhanced storage formats
pip install h5py pyarrow

# Advanced analysis
pip install scikit-learn matplotlib seaborn networkx
```

## Testing

Run the test suite:
```bash
python -m pytest flee_dual_process/test_individual_agent_tracker.py -v
python -m pytest flee_dual_process/test_individual_agent_analysis.py -v
```

## Example Usage

See `example_individual_agent_analysis.py` for a complete demonstration of the system's capabilities.

## Integration with Existing Flee Workflows

This system is designed to integrate seamlessly with existing Flee simulations:

1. **No changes required** to existing simulation code
2. **Optional enhancement** - can be added to any Flee simulation
3. **Configurable impact** - from minimal overhead to comprehensive tracking
4. **Compatible output** - works with existing analysis pipelines

The system respects Flee's design principles while adding powerful new capabilities for dual-process research.