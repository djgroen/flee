"""
Individual Agent Tracking System for Dual Process Experiments

This module extends Flee's existing agent tracking capabilities with
dual-process specific tracking, efficient storage formats, and enhanced
analysis features. It complements the standard Flee agent logging system
by adding cognitive state tracking and decision-making analysis.
"""

from __future__ import annotations, print_function
import os
import sys
import csv
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

# Optional dependencies for efficient storage
try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


class TrackingLevel(Enum):
    """Enumeration of available tracking levels."""
    SUMMARY = "summary"      # Basic aggregate metrics only
    DETAILED = "detailed"    # Key events and state changes
    FULL = "full"           # Complete individual trajectories


class StorageFormat(Enum):
    """Enumeration of available storage formats."""
    CSV = "csv"             # Standard CSV format
    HDF5 = "hdf5"          # HDF5 for large datasets
    PARQUET = "parquet"     # Parquet for compressed columnar storage
    PICKLE = "pickle"       # Python pickle for complex objects


@dataclass
class AgentSnapshot:
    """Data structure for agent state at a single timestep."""
    time: int
    agent_id: str
    location: str
    cognitive_state: str
    connections: int
    system2_activations: int
    days_in_location: int
    conflict_level: float
    distance_travelled: float
    route_length: int
    decision_factors: Dict[str, Any]
    attributes: Dict[str, Any]


@dataclass
class AgentDecision:
    """Data structure for individual agent decisions."""
    time: int
    agent_id: str
    decision_type: str
    cognitive_state: str
    location: str
    destination: Optional[str]
    movechance: float
    outcome: float
    system2_active: bool
    conflict_level: float
    connections: int
    decision_factors: Dict[str, Any]
    reasoning: str


@dataclass
class TrackingConfig:
    """Configuration for agent tracking system."""
    tracking_level: TrackingLevel = TrackingLevel.DETAILED
    storage_format: StorageFormat = StorageFormat.CSV
    output_dir: str = "."
    sampling_rate: float = 1.0  # Fraction of agents to track (0.0-1.0)
    timestep_interval: int = 1  # Interval between data collection
    compression: bool = True    # Enable compression for supported formats
    max_memory_mb: int = 1000   # Maximum memory usage before flushing
    track_decisions: bool = True
    track_trajectories: bool = True
    track_social_network: bool = True
    validate_data: bool = True


class IndividualAgentTracker:
    """
    Configurable system for tracking individual agent behaviors and trajectories.
    
    This class extends Flee's existing agent tracking (Diagnostics.write_agents_par)
    with dual-process specific features:
    - Cognitive state transitions and decision-making processes
    - Enhanced storage formats (HDF5, Parquet) for large datasets
    - Configurable sampling and compression for performance
    - Integration with existing Flee logging levels and output formats
    
    Note: This complements rather than replaces Flee's standard agent logging.
    Use SimulationSettings.log_levels["agent"] for basic trajectory tracking.
    """
    
    def __init__(self, config: TrackingConfig, rank: int = 0):
        """
        Initialize the individual agent tracker.
        
        Args:
            config: Tracking configuration
            rank: MPI rank for parallel processing
        """
        self.config = config
        self.rank = rank
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Import Flee's SimulationSettings to check existing logging configuration
        try:
            from flee.SimulationSettings import SimulationSettings
            self.flee_agent_logging_level = SimulationSettings.log_levels.get("agent", 0)
            self.flee_logging_available = True
        except (ImportError, AttributeError):
            self.flee_agent_logging_level = 0
            self.flee_logging_available = False
            
        # Data storage
        self.agent_snapshots: List[AgentSnapshot] = []
        self.agent_decisions: List[AgentDecision] = []
        self.trajectory_data: Dict[str, List[Dict]] = {}
        self.social_network_data: List[Dict] = []
        
        # Tracking state
        self.initialized = False
        self.tracked_agents: set = set()
        self.memory_usage_mb = 0
        self.last_flush_time = 0
        
        # File handles for streaming formats
        self.csv_files: Dict[str, Any] = {}
        self.hdf5_file: Optional[Any] = None
        
        # Validation
        self.validation_errors: List[str] = []
        
        # Integration with Flee's existing logging
        if self.flee_logging_available and self.flee_agent_logging_level > 0:
            print(f"INFO: Flee agent logging level {self.flee_agent_logging_level} detected. "
                  f"Dual-process tracker will complement existing agent logs.", file=sys.stderr)
        
    @check_args_type
    def initialize(self, agents: List) -> None:
        """
        Initialize the tracking system and select agents to track.
        
        Args:
            agents: List of all agents in simulation
        """
        if self.initialized:
            return
            
        # Select agents to track based on sampling rate
        if self.config.sampling_rate < 1.0:
            n_agents_to_track = max(1, int(len(agents) * self.config.sampling_rate))
            agent_indices = np.random.choice(len(agents), n_agents_to_track, replace=False)
            self.tracked_agents = {f"{self.rank}-{i}" for i in agent_indices}
        else:
            self.tracked_agents = {f"{self.rank}-{i}" for i in range(len(agents))}
            
        # Initialize storage based on format
        if self.config.storage_format == StorageFormat.CSV:
            self._initialize_csv_storage()
        elif self.config.storage_format == StorageFormat.HDF5:
            self._initialize_hdf5_storage()
        elif self.config.storage_format == StorageFormat.PARQUET:
            self._initialize_parquet_storage()
            
        self.initialized = True
        
    def _initialize_csv_storage(self) -> None:
        """Initialize CSV file storage."""
        if self.config.track_trajectories:
            filename = self.output_dir / f"agent_trajectories.{self.rank}.csv"
            self.csv_files['trajectories'] = open(filename, 'w', newline='')
            writer = csv.writer(self.csv_files['trajectories'])
            writer.writerow([
                'time', 'agent_id', 'location', 'cognitive_state', 'connections',
                'system2_activations', 'days_in_location', 'conflict_level',
                'distance_travelled', 'route_length', 'decision_factors', 'attributes'
            ])
            
        if self.config.track_decisions:
            filename = self.output_dir / f"agent_decisions.{self.rank}.csv"
            self.csv_files['decisions'] = open(filename, 'w', newline='')
            writer = csv.writer(self.csv_files['decisions'])
            writer.writerow([
                'time', 'agent_id', 'decision_type', 'cognitive_state', 'location',
                'destination', 'movechance', 'outcome', 'system2_active',
                'conflict_level', 'connections', 'decision_factors', 'reasoning'
            ])
            
        if self.config.track_social_network:
            filename = self.output_dir / f"social_network_individual.{self.rank}.csv"
            self.csv_files['social'] = open(filename, 'w', newline='')
            writer = csv.writer(self.csv_files['social'])
            writer.writerow([
                'time', 'agent_id', 'location', 'connections', 'connection_change',
                'network_neighbors', 'information_shared', 'information_received'
            ])
            
    def _initialize_hdf5_storage(self) -> None:
        """Initialize HDF5 file storage."""
        if not HDF5_AVAILABLE:
            raise ImportError("HDF5 storage requires h5py package")
            
        filename = self.output_dir / f"agent_tracking.{self.rank}.h5"
        self.hdf5_file = h5py.File(filename, 'w')
        
        # Create groups for different data types
        if self.config.track_trajectories:
            self.hdf5_file.create_group('trajectories')
        if self.config.track_decisions:
            self.hdf5_file.create_group('decisions')
        if self.config.track_social_network:
            self.hdf5_file.create_group('social_network')
            
    def _initialize_parquet_storage(self) -> None:
        """Initialize Parquet file storage."""
        if not PARQUET_AVAILABLE:
            raise ImportError("Parquet storage requires pyarrow package")
            
        # Parquet files will be written in batches during flush operations
        pass
        
    @check_args_type
    def track_agents(self, agents: List, time: int) -> None:
        """
        Track agent states at current timestep.
        
        Args:
            agents: List of agents to track
            time: Current simulation time
        """
        if not self.initialized:
            self.initialize(agents)
            
        # Only track at specified intervals
        if time % self.config.timestep_interval != 0:
            return
            
        # Track based on level
        if self.config.tracking_level == TrackingLevel.SUMMARY:
            self._track_summary_data(agents, time)
        elif self.config.tracking_level == TrackingLevel.DETAILED:
            self._track_detailed_data(agents, time)
        elif self.config.tracking_level == TrackingLevel.FULL:
            self._track_full_data(agents, time)
            
        # Check memory usage and flush if needed
        self._check_memory_usage(time)
        
    def _track_summary_data(self, agents: List, time: int) -> None:
        """Track summary-level data (aggregate metrics only)."""
        # For summary level, we only collect basic statistics
        tracked_agents = [a for i, a in enumerate(agents) 
                         if f"{self.rank}-{i}" in self.tracked_agents]
        
        if not tracked_agents:
            return
            
        # Calculate summary statistics
        summary_data = {
            'time': time,
            'total_tracked_agents': len(tracked_agents),
            'avg_connections': np.mean([a.attributes.get('connections', 0) for a in tracked_agents]),
            'cognitive_state_distribution': self._get_cognitive_state_distribution(tracked_agents),
            'location_distribution': self._get_location_distribution(tracked_agents),
            'avg_distance_travelled': np.mean([getattr(a, 'distance_travelled', 0) for a in tracked_agents])
        }
        
        # Store summary data
        if not hasattr(self, 'summary_data'):
            self.summary_data = []
        self.summary_data.append(summary_data)
        
    def _track_detailed_data(self, agents: List, time: int) -> None:
        """Track detailed-level data (key events and state changes)."""
        for i, agent in enumerate(agents):
            agent_id = f"{self.rank}-{i}"
            
            if agent_id not in self.tracked_agents:
                continue
                
            if agent.location is None:
                continue
                
            # Track state changes and key events
            if self._should_track_agent_state(agent, time):
                snapshot = self._create_agent_snapshot(agent, agent_id, time)
                self.agent_snapshots.append(snapshot)
                
            # Track decisions
            if self.config.track_decisions:
                decisions = self._extract_agent_decisions(agent, agent_id, time)
                self.agent_decisions.extend(decisions)
                
            # Track social network changes
            if self.config.track_social_network:
                social_data = self._extract_social_network_data(agent, agent_id, time)
                if social_data:
                    self.social_network_data.append(social_data)
                    
    def _track_full_data(self, agents: List, time: int) -> None:
        """Track full-level data (complete individual trajectories)."""
        for i, agent in enumerate(agents):
            agent_id = f"{self.rank}-{i}"
            
            if agent_id not in self.tracked_agents:
                continue
                
            if agent.location is None:
                continue
                
            # Always track full state for full tracking level
            snapshot = self._create_agent_snapshot(agent, agent_id, time)
            self.agent_snapshots.append(snapshot)
            
            # Track all decisions
            if self.config.track_decisions:
                decisions = self._extract_agent_decisions(agent, agent_id, time)
                self.agent_decisions.extend(decisions)
                
            # Track complete trajectory
            if self.config.track_trajectories:
                if agent_id not in self.trajectory_data:
                    self.trajectory_data[agent_id] = []
                    
                trajectory_point = {
                    'time': time,
                    'location': agent.location.name if hasattr(agent.location, 'name') else 'unknown',
                    'x': getattr(agent.location, 'x', 0),
                    'y': getattr(agent.location, 'y', 0),
                    'cognitive_state': getattr(agent, 'cognitive_state', 'S1'),
                    'route_progress': len(getattr(agent, 'route', [])),
                    'movement_vector': self._calculate_movement_vector(agent, time)
                }
                self.trajectory_data[agent_id].append(trajectory_point)
                
            # Track social network
            if self.config.track_social_network:
                social_data = self._extract_social_network_data(agent, agent_id, time)
                if social_data:
                    self.social_network_data.append(social_data)
                    
    def _should_track_agent_state(self, agent, time: int) -> bool:
        """Determine if agent state should be tracked (for detailed level)."""
        # Track on first timestep
        if time == 0:
            return True
            
        # Track if cognitive state changed
        if hasattr(agent, '_previous_cognitive_state'):
            if getattr(agent, 'cognitive_state', 'S1') != agent._previous_cognitive_state:
                return True
                
        # Track if location changed
        if hasattr(agent, '_previous_location'):
            current_location = agent.location.name if hasattr(agent.location, 'name') else 'unknown'
            if current_location != agent._previous_location:
                return True
                
        # Track if connections changed significantly
        if hasattr(agent, '_previous_connections'):
            current_connections = agent.attributes.get('connections', 0)
            if abs(current_connections - agent._previous_connections) >= 2:
                return True
                
        return False
        
    def _create_agent_snapshot(self, agent, agent_id: str, time: int) -> AgentSnapshot:
        """Create a snapshot of agent state."""
        location_name = agent.location.name if hasattr(agent.location, 'name') else 'unknown'
        
        # Extract decision factors if available
        decision_factors = {}
        if hasattr(agent, 'last_decision_factors'):
            decision_factors = agent.last_decision_factors.copy()
            
        # Extract attributes
        attributes = agent.attributes.copy() if hasattr(agent, 'attributes') else {}
        
        snapshot = AgentSnapshot(
            time=time,
            agent_id=agent_id,
            location=location_name,
            cognitive_state=getattr(agent, 'cognitive_state', 'S1'),
            connections=agent.attributes.get('connections', 0),
            system2_activations=getattr(agent, 'system2_activations', 0),
            days_in_location=getattr(agent, 'days_in_current_location', 0),
            conflict_level=getattr(agent.location, 'conflict', 0) if agent.location else 0,
            distance_travelled=getattr(agent, 'distance_travelled', 0),
            route_length=len(getattr(agent, 'route', [])),
            decision_factors=decision_factors,
            attributes=attributes
        )
        
        # Update previous state tracking
        agent._previous_cognitive_state = snapshot.cognitive_state
        agent._previous_location = snapshot.location
        agent._previous_connections = snapshot.connections
        
        return snapshot
        
    def _extract_agent_decisions(self, agent, agent_id: str, time: int) -> List[AgentDecision]:
        """Extract decisions made by agent at current timestep."""
        decisions = []
        
        # Check if agent has decision history
        decision_history = getattr(agent, 'decision_history', [])
        
        for decision in decision_history:
            if decision.get('time') == time:
                agent_decision = AgentDecision(
                    time=time,
                    agent_id=agent_id,
                    decision_type=decision.get('type', 'unknown'),
                    cognitive_state=decision.get('cognitive_state', 'S1'),
                    location=decision.get('location', 'unknown'),
                    destination=decision.get('destination'),
                    movechance=decision.get('factors', {}).get('movechance', 0.0),
                    outcome=decision.get('factors', {}).get('outcome', 0.0),
                    system2_active=decision.get('factors', {}).get('system2_active', False),
                    conflict_level=decision.get('factors', {}).get('conflict_level', 0.0),
                    connections=decision.get('connections', 0),
                    decision_factors=decision.get('factors', {}),
                    reasoning=decision.get('reasoning', '')
                )
                decisions.append(agent_decision)
                
        return decisions
        
    def _extract_social_network_data(self, agent, agent_id: str, time: int) -> Optional[Dict]:
        """Extract social network data for agent."""
        current_connections = agent.attributes.get('connections', 0)
        
        # Get previous connections for change calculation
        if not hasattr(agent, '_previous_connections_social'):
            agent._previous_connections_social = 0
            
        connection_change = current_connections - agent._previous_connections_social
        
        # Only record if there's a change or it's the first timestep
        if connection_change != 0 or time == 0:
            social_data = {
                'time': time,
                'agent_id': agent_id,
                'location': agent.location.name if hasattr(agent.location, 'name') else 'unknown',
                'connections': current_connections,
                'connection_change': connection_change,
                'network_neighbors': list(agent.attributes.get('network_neighbors', [])),
                'information_shared': agent.attributes.get('information_shared_count', 0),
                'information_received': agent.attributes.get('information_received_count', 0)
            }
            
            agent._previous_connections_social = current_connections
            return social_data
            
        return None
        
    def _calculate_movement_vector(self, agent, time: int) -> Tuple[float, float]:
        """Calculate movement vector for agent."""
        if not hasattr(agent, '_previous_x') or not hasattr(agent, '_previous_y'):
            agent._previous_x = getattr(agent.location, 'x', 0)
            agent._previous_y = getattr(agent.location, 'y', 0)
            return (0.0, 0.0)
            
        current_x = getattr(agent.location, 'x', 0)
        current_y = getattr(agent.location, 'y', 0)
        
        dx = current_x - agent._previous_x
        dy = current_y - agent._previous_y
        
        agent._previous_x = current_x
        agent._previous_y = current_y
        
        return (dx, dy)
        
    def _get_cognitive_state_distribution(self, agents: List) -> Dict[str, int]:
        """Get distribution of cognitive states."""
        distribution = {}
        for agent in agents:
            state = getattr(agent, 'cognitive_state', 'S1')
            distribution[state] = distribution.get(state, 0) + 1
        return distribution
        
    def _get_location_distribution(self, agents: List) -> Dict[str, int]:
        """Get distribution of agent locations."""
        distribution = {}
        for agent in agents:
            location = agent.location.name if hasattr(agent.location, 'name') else 'unknown'
            distribution[location] = distribution.get(location, 0) + 1
        return distribution
        
    def _check_memory_usage(self, time: int) -> None:
        """Check memory usage and flush if needed."""
        # Estimate memory usage
        estimated_mb = (
            len(self.agent_snapshots) * 0.001 +  # Rough estimate
            len(self.agent_decisions) * 0.001 +
            len(self.social_network_data) * 0.0005
        )
        
        self.memory_usage_mb = estimated_mb
        
        # Flush if memory limit exceeded or at regular intervals
        if (self.memory_usage_mb > self.config.max_memory_mb or 
            time - self.last_flush_time > 100):
            self.flush_data()
            self.last_flush_time = time
            
    @check_args_type
    def flush_data(self) -> None:
        """Flush accumulated data to storage."""
        if self.config.storage_format == StorageFormat.CSV:
            self._flush_to_csv()
        elif self.config.storage_format == StorageFormat.HDF5:
            self._flush_to_hdf5()
        elif self.config.storage_format == StorageFormat.PARQUET:
            self._flush_to_parquet()
            
        # Clear memory
        self.agent_snapshots.clear()
        self.agent_decisions.clear()
        self.social_network_data.clear()
        self.memory_usage_mb = 0
        
    def _flush_to_csv(self) -> None:
        """Flush data to CSV files."""
        if self.config.track_trajectories and 'trajectories' in self.csv_files:
            writer = csv.writer(self.csv_files['trajectories'])
            for snapshot in self.agent_snapshots:
                writer.writerow([
                    snapshot.time, snapshot.agent_id, snapshot.location,
                    snapshot.cognitive_state, snapshot.connections,
                    snapshot.system2_activations, snapshot.days_in_location,
                    snapshot.conflict_level, snapshot.distance_travelled,
                    snapshot.route_length, json.dumps(snapshot.decision_factors),
                    json.dumps(snapshot.attributes)
                ])
            self.csv_files['trajectories'].flush()
            
        if self.config.track_decisions and 'decisions' in self.csv_files:
            writer = csv.writer(self.csv_files['decisions'])
            for decision in self.agent_decisions:
                writer.writerow([
                    decision.time, decision.agent_id, decision.decision_type,
                    decision.cognitive_state, decision.location, decision.destination,
                    decision.movechance, decision.outcome, decision.system2_active,
                    decision.conflict_level, decision.connections,
                    json.dumps(decision.decision_factors), decision.reasoning
                ])
            self.csv_files['decisions'].flush()
            
        if self.config.track_social_network and 'social' in self.csv_files:
            writer = csv.writer(self.csv_files['social'])
            for social_data in self.social_network_data:
                writer.writerow([
                    social_data['time'], social_data['agent_id'], social_data['location'],
                    social_data['connections'], social_data['connection_change'],
                    json.dumps(social_data['network_neighbors']),
                    social_data['information_shared'], social_data['information_received']
                ])
            self.csv_files['social'].flush()
            
    def _flush_to_hdf5(self) -> None:
        """Flush data to HDF5 file."""
        if not self.hdf5_file:
            return
            
        if self.config.track_trajectories and self.agent_snapshots:
            # Convert snapshots to structured array
            snapshot_data = []
            for snapshot in self.agent_snapshots:
                snapshot_data.append((
                    snapshot.time, snapshot.agent_id.encode(), snapshot.location.encode(),
                    snapshot.cognitive_state.encode(), snapshot.connections,
                    snapshot.system2_activations, snapshot.days_in_location,
                    snapshot.conflict_level, snapshot.distance_travelled, snapshot.route_length
                ))
                
            if snapshot_data:
                dt = np.dtype([
                    ('time', 'i4'), ('agent_id', 'S20'), ('location', 'S50'),
                    ('cognitive_state', 'S10'), ('connections', 'i4'),
                    ('system2_activations', 'i4'), ('days_in_location', 'i4'),
                    ('conflict_level', 'f4'), ('distance_travelled', 'f4'),
                    ('route_length', 'i4')
                ])
                
                arr = np.array(snapshot_data, dtype=dt)
                
                # Create or extend dataset
                if 'trajectory_data' not in self.hdf5_file['trajectories']:
                    self.hdf5_file['trajectories'].create_dataset(
                        'trajectory_data', data=arr, maxshape=(None,),
                        compression='gzip' if self.config.compression else None
                    )
                else:
                    # Extend existing dataset
                    dataset = self.hdf5_file['trajectories']['trajectory_data']
                    old_size = dataset.shape[0]
                    dataset.resize((old_size + len(arr),))
                    dataset[old_size:] = arr
                    
        self.hdf5_file.flush()
        
    def _flush_to_parquet(self) -> None:
        """Flush data to Parquet files."""
        if self.config.track_trajectories and self.agent_snapshots:
            # Convert to DataFrame
            snapshot_dicts = [asdict(snapshot) for snapshot in self.agent_snapshots]
            df = pd.DataFrame(snapshot_dicts)
            
            # Write to Parquet
            filename = self.output_dir / f"agent_trajectories.{self.rank}.{self.last_flush_time}.parquet"
            df.to_parquet(filename, compression='snappy' if self.config.compression else None)
            
        if self.config.track_decisions and self.agent_decisions:
            # Convert to DataFrame
            decision_dicts = [asdict(decision) for decision in self.agent_decisions]
            df = pd.DataFrame(decision_dicts)
            
            # Write to Parquet
            filename = self.output_dir / f"agent_decisions.{self.rank}.{self.last_flush_time}.parquet"
            df.to_parquet(filename, compression='snappy' if self.config.compression else None)
            
    @check_args_type
    def validate_data_integrity(self) -> List[str]:
        """
        Validate data integrity and return list of validation errors.
        
        Returns:
            List of validation error messages
        """
        if not self.config.validate_data:
            return []
            
        errors = []
        
        # Validate agent snapshots
        for snapshot in self.agent_snapshots:
            if snapshot.time < 0:
                errors.append(f"Invalid time {snapshot.time} for agent {snapshot.agent_id}")
            if snapshot.connections < 0:
                errors.append(f"Invalid connections {snapshot.connections} for agent {snapshot.agent_id}")
            if not snapshot.location:
                errors.append(f"Missing location for agent {snapshot.agent_id} at time {snapshot.time}")
                
        # Validate agent decisions
        for decision in self.agent_decisions:
            if decision.time < 0:
                errors.append(f"Invalid decision time {decision.time} for agent {decision.agent_id}")
            if not (0 <= decision.movechance <= 1):
                errors.append(f"Invalid movechance {decision.movechance} for agent {decision.agent_id}")
                
        # Validate trajectory continuity
        for agent_id, trajectory in self.trajectory_data.items():
            times = [point['time'] for point in trajectory]
            if times != sorted(times):
                errors.append(f"Non-sequential trajectory times for agent {agent_id}")
                
        self.validation_errors.extend(errors)
        return errors
        
    @check_args_type
    def integrate_with_flee_agent_logs(self, agents: List, time: int) -> None:
        """
        Integrate with Flee's existing agent logging system.
        
        This method can be called alongside Flee's write_agents_par() to ensure
        consistency between standard Flee logs and dual-process tracking.
        
        Args:
            agents: List of agents (same as passed to write_agents_par)
            time: Current simulation time
        """
        if not self.flee_logging_available:
            return
            
        # Extract data that complements Flee's standard agent logs
        for i, agent in enumerate(agents):
            agent_id = f"{self.rank}-{i}"
            
            if agent_id not in self.tracked_agents:
                continue
                
            if agent.location is None:
                continue
                
            # Add dual-process specific data that Flee doesn't track
            dual_process_data = {
                'time': time,
                'agent_id': agent_id,
                'cognitive_state': getattr(agent, 'cognitive_state', 'S1'),
                'system2_activations': getattr(agent, 'system2_activations', 0),
                'decision_history_length': len(getattr(agent, 'decision_history', [])),
                'days_in_current_location': getattr(agent, 'days_in_current_location', 0),
                'last_connection_update': getattr(agent, 'last_connection_update', 0),
                # Flee already tracks: location, distance_travelled, places_travelled, 
                # travelling, attributes, home_location
            }
            
            # Store complementary data
            if not hasattr(self, 'flee_integration_data'):
                self.flee_integration_data = []
            self.flee_integration_data.append(dual_process_data)
            
    @check_args_type
    def write_flee_integration_csv(self) -> None:
        """Write CSV file that complements Flee's agents.out files."""
        if not hasattr(self, 'flee_integration_data') or not self.flee_integration_data:
            return
            
        filename = self.output_dir / f"agents_dual_process.out.{self.rank}"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header compatible with Flee's format
            writer.writerow([
                '#time', 'agent_id', 'cognitive_state', 'system2_activations',
                'decision_history_length', 'days_in_current_location', 'last_connection_update'
            ])
            
            for data in self.flee_integration_data:
                writer.writerow([
                    data['time'], data['agent_id'], data['cognitive_state'],
                    data['system2_activations'], data['decision_history_length'],
                    data['days_in_current_location'], data['last_connection_update']
                ])
                
    @check_args_type
    def get_tracking_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the tracking system.
        
        Returns:
            Dictionary with tracking statistics
        """
        return {
            'tracking_level': self.config.tracking_level.value,
            'storage_format': self.config.storage_format.value,
            'tracked_agents_count': len(self.tracked_agents),
            'sampling_rate': self.config.sampling_rate,
            'memory_usage_mb': self.memory_usage_mb,
            'snapshots_collected': len(self.agent_snapshots),
            'decisions_collected': len(self.agent_decisions),
            'social_network_events': len(self.social_network_data),
            'validation_errors': len(self.validation_errors),
            'last_flush_time': self.last_flush_time
        }
        
    def close(self) -> None:
        """Close all file handles and finalize data."""
        # Final flush
        self.flush_data()
        
        # Write Flee integration data
        self.write_flee_integration_csv()
        
        # Close CSV files
        for file_handle in self.csv_files.values():
            if file_handle:
                file_handle.close()
                
        # Close HDF5 file
        if self.hdf5_file:
            self.hdf5_file.close()
            
        # Write summary data for summary tracking level
        if (self.config.tracking_level == TrackingLevel.SUMMARY and 
            hasattr(self, 'summary_data')):
            filename = self.output_dir / f"tracking_summary.{self.rank}.json"
            with open(filename, 'w') as f:
                json.dump(self.summary_data, f, indent=2, default=str)
                
        # Write tracking statistics
        stats_filename = self.output_dir / f"tracking_statistics.{self.rank}.json"
        with open(stats_filename, 'w') as f:
            json.dump(self.get_tracking_statistics(), f, indent=2)
            
        # Write validation report if there were errors
        if self.validation_errors:
            errors_filename = self.output_dir / f"validation_errors.{self.rank}.txt"
            with open(errors_filename, 'w') as f:
                for error in self.validation_errors:
                    f.write(f"{error}\n")
                    
        # Write integration guide
        self._write_integration_guide()
        
    def _write_integration_guide(self) -> None:
        """Write guide for integrating with Flee's existing agent logs."""
        guide_filename = self.output_dir / f"flee_integration_guide.{self.rank}.md"
        
        with open(guide_filename, 'w') as f:
            f.write("# Flee Agent Tracking Integration Guide\n\n")
            f.write("This dual-process tracker complements Flee's existing agent logging system.\n\n")
            
            f.write("## Flee's Standard Agent Logs\n")
            f.write(f"- Flee agent logging level: {self.flee_agent_logging_level}\n")
            f.write("- Standard output file: `agents.out.{rank}`\n")
            f.write("- Contains: agent_id, locations, GPS coordinates, distance_travelled, attributes\n\n")
            
            f.write("## Dual-Process Extensions\n")
            f.write("- Cognitive state tracking: `agents_dual_process.out.{rank}`\n")
            f.write("- Decision logging: `agent_decisions.{rank}.csv`\n")
            f.write("- Social network changes: `social_network_individual.{rank}.csv`\n\n")
            
            f.write("## Usage Recommendations\n")
            f.write("1. Set `SimulationSettings.log_levels['agent'] = 1` for basic Flee tracking\n")
            f.write("2. Use this dual-process tracker for cognitive analysis\n")
            f.write("3. Combine both datasets for complete agent behavior analysis\n\n")
            
            f.write("## File Compatibility\n")
            f.write("- All files use same agent_id format: `{rank}-{agent_index}`\n")
            f.write("- Time columns are synchronized\n")
            f.write("- Can be joined on (time, agent_id) for analysis\n")


class TrackingConfigBuilder:
    """Builder class for creating tracking configurations."""
    
    def __init__(self):
        self.config = TrackingConfig()
        
    def set_tracking_level(self, level: Union[TrackingLevel, str]) -> 'TrackingConfigBuilder':
        """Set tracking level."""
        if isinstance(level, str):
            level = TrackingLevel(level)
        self.config.tracking_level = level
        return self
        
    def set_storage_format(self, format: Union[StorageFormat, str]) -> 'TrackingConfigBuilder':
        """Set storage format."""
        if isinstance(format, str):
            format = StorageFormat(format)
        self.config.storage_format = format
        return self
        
    def set_sampling_rate(self, rate: float) -> 'TrackingConfigBuilder':
        """Set agent sampling rate."""
        if not 0 <= rate <= 1:
            raise ValueError("Sampling rate must be between 0 and 1")
        self.config.sampling_rate = rate
        return self
        
    def set_output_dir(self, output_dir: str) -> 'TrackingConfigBuilder':
        """Set output directory."""
        self.config.output_dir = output_dir
        return self
        
    def set_memory_limit(self, limit_mb: int) -> 'TrackingConfigBuilder':
        """Set memory limit in MB."""
        self.config.max_memory_mb = limit_mb
        return self
        
    def enable_compression(self, enable: bool = True) -> 'TrackingConfigBuilder':
        """Enable or disable compression."""
        self.config.compression = enable
        return self
        
    def set_timestep_interval(self, interval: int) -> 'TrackingConfigBuilder':
        """Set timestep interval for data collection."""
        self.config.timestep_interval = interval
        return self
        
    def enable_validation(self, enable: bool = True) -> 'TrackingConfigBuilder':
        """Enable or disable data validation."""
        self.config.validate_data = enable
        return self
        
    def build(self) -> TrackingConfig:
        """Build the tracking configuration."""
        return self.config


# Convenience functions for common configurations
def create_summary_tracking_config(output_dir: str = ".") -> TrackingConfig:
    """
    Create configuration for summary-level tracking.
    
    Recommended when Flee's agent logging level >= 1 is already enabled.
    Provides aggregate statistics without duplicating individual trajectories.
    """
    return (TrackingConfigBuilder()
            .set_tracking_level(TrackingLevel.SUMMARY)
            .set_storage_format(StorageFormat.CSV)
            .set_sampling_rate(0.1)
            .set_output_dir(output_dir)
            .build())


def create_detailed_tracking_config(output_dir: str = ".", 
                                  storage_format: str = "csv") -> TrackingConfig:
    """
    Create configuration for detailed-level tracking.
    
    Complements Flee's basic agent logging with cognitive state changes
    and decision-making events. Use when you need dual-process analysis
    but want to avoid full trajectory duplication.
    """
    return (TrackingConfigBuilder()
            .set_tracking_level(TrackingLevel.DETAILED)
            .set_storage_format(storage_format)
            .set_sampling_rate(0.5)
            .set_output_dir(output_dir)
            .enable_compression(True)
            .build())


def create_full_tracking_config(output_dir: str = ".", 
                               storage_format: str = "hdf5",
                               sampling_rate: float = 0.1) -> TrackingConfig:
    """
    Create configuration for full-level tracking.
    
    Provides complete individual trajectories with dual-process extensions.
    Use when Flee's agent logging is disabled or when you need enhanced
    storage formats (HDF5, Parquet) for large-scale analysis.
    """
    return (TrackingConfigBuilder()
            .set_tracking_level(TrackingLevel.FULL)
            .set_storage_format(storage_format)
            .set_sampling_rate(sampling_rate)
            .set_output_dir(output_dir)
            .enable_compression(True)
            .set_memory_limit(500)  # Lower memory limit for full tracking
            .build())


def create_flee_compatible_config(output_dir: str = ".", 
                                 flee_agent_level: int = 1) -> TrackingConfig:
    """
    Create configuration that complements Flee's existing agent logging.
    
    Args:
        output_dir: Output directory
        flee_agent_level: Flee's SimulationSettings.log_levels["agent"] value
        
    Returns:
        Optimized configuration based on Flee's logging level
    """
    if flee_agent_level == 0:
        # No Flee logging, use full tracking
        return create_full_tracking_config(output_dir, "csv", 1.0)
    elif flee_agent_level == 1:
        # Basic Flee logging, use detailed dual-process tracking
        return create_detailed_tracking_config(output_dir, "csv")
    else:
        # Advanced Flee logging, use summary for efficiency
        return create_summary_tracking_config(output_dir)