"""
Cognitive State Logger for Dual Process Experiments

This module provides logging functionality for tracking cognitive states
and decision-making processes in Flee simulations.
"""

from __future__ import annotations, print_function
import os
import csv
from typing import List, Dict, Any, Optional
from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


class CognitiveStateLogger:
    """
    Logger for tracking agent cognitive states over time.
    """
    
    def __init__(self, output_dir: str = ".", rank: int = 0):
        """
        Initialize the cognitive state logger.
        
        Args:
            output_dir: Directory to write output files
            rank: MPI rank for parallel processing
        """
        self.output_dir = output_dir
        self.rank = rank
        self.cognitive_states_file = None
        self.initialized = False
        
    @check_args_type
    def initialize(self, agents: List) -> None:
        """
        Initialize the cognitive states output file with headers.
        
        Args:
            agents: List of agents to determine output format
        """
        if self.initialized:
            return
            
        filename = os.path.join(self.output_dir, f"cognitive_states.out.{self.rank}")
        self.cognitive_states_file = open(filename, "w", encoding="utf-8")
        
        # Write header
        header = "#day,agent_id,cognitive_state,location,connections,system2_activations,days_in_location,conflict_level"
        print(header, file=self.cognitive_states_file)
        
        self.initialized = True
    
    @check_args_type
    def write_cognitive_states_csv(self, agents: List, time: int, timestep_interval: int = 1) -> None:
        """
        Write cognitive state data for all agents at current timestep.
        
        Args:
            agents: List of agents to log
            time: Current simulation time
            timestep_interval: Interval between writing files
        """
        if not self.initialized:
            self.initialize(agents)
            
        # Only write at specified intervals
        if time % timestep_interval != 0:
            return
            
        for i, agent in enumerate(agents):
            # Skip agents that have been removed from simulation
            if agent.location is None:
                continue
                
            # Get agent data
            agent_id = f"{self.rank}-{i}"
            cognitive_state = getattr(agent, 'cognitive_state', 'S1')
            location_name = agent.location.name if hasattr(agent.location, 'name') else 'unknown'
            connections = agent.attributes.get('connections', 0)
            system2_activations = getattr(agent, 'system2_activations', 0)
            days_in_location = getattr(agent, 'days_in_current_location', 0)
            conflict_level = getattr(agent.location, 'conflict', 0) if agent.location else 0
            
            # Write data row
            row = f"{time},{agent_id},{cognitive_state},{location_name},{connections},{system2_activations},{days_in_location},{conflict_level}"
            print(row, file=self.cognitive_states_file)
            
        # Flush to ensure data is written
        self.cognitive_states_file.flush()
    
    def close(self) -> None:
        """Close the output file."""
        if self.cognitive_states_file:
            self.cognitive_states_file.close()
            self.cognitive_states_file = None
        self.initialized = False


class DecisionLogger:
    """
    Logger for tracking decision-making processes and factors.
    """
    
    def __init__(self, output_dir: str = ".", rank: int = 0):
        """
        Initialize the decision logger.
        
        Args:
            output_dir: Directory to write output files
            rank: MPI rank for parallel processing
        """
        self.output_dir = output_dir
        self.rank = rank
        self.decision_log_file = None
        self.initialized = False
        
    @check_args_type
    def initialize(self) -> None:
        """Initialize the decision log output file with headers."""
        if self.initialized:
            return
            
        filename = os.path.join(self.output_dir, f"decision_log.out.{self.rank}")
        self.decision_log_file = open(filename, "w", encoding="utf-8")
        
        # Write header
        header = "#day,agent_id,decision_type,cognitive_state,location,movechance,outcome,system2_active,conflict_level,connections"
        print(header, file=self.decision_log_file)
        
        self.initialized = True
    
    @check_args_type
    def write_decision_log_csv(self, agents: List, time: int, timestep_interval: int = 1) -> None:
        """
        Write decision log data for agents with recent decisions.
        
        Args:
            agents: List of agents to check for decisions
            time: Current simulation time
            timestep_interval: Interval between writing files
        """
        if not self.initialized:
            self.initialize()
            
        # Only write at specified intervals
        if time % timestep_interval != 0:
            return
            
        for i, agent in enumerate(agents):
            # Skip agents that have been removed from simulation
            if agent.location is None:
                continue
                
            # Check if agent has decision history
            decision_history = getattr(agent, 'decision_history', [])
            if not decision_history:
                continue
                
            # Write recent decisions (from current timestep)
            agent_id = f"{self.rank}-{i}"
            for decision in decision_history:
                if decision['time'] == time:
                    # Extract decision data
                    decision_type = decision.get('type', 'unknown')
                    cognitive_state = decision.get('cognitive_state', 'S1')
                    location = decision.get('location', 'unknown')
                    factors = decision.get('factors', {})
                    
                    movechance = factors.get('movechance', 0.0)
                    outcome = factors.get('outcome', 0.0)
                    system2_active = factors.get('system2_active', False)
                    conflict_level = factors.get('conflict_level', 0.0)
                    connections = decision.get('connections', 0)
                    
                    # Write data row
                    row = f"{time},{agent_id},{decision_type},{cognitive_state},{location},{movechance},{outcome},{system2_active},{conflict_level},{connections}"
                    print(row, file=self.decision_log_file)
            
        # Flush to ensure data is written
        self.decision_log_file.flush()
    
    def close(self) -> None:
        """Close the output file."""
        if self.decision_log_file:
            self.decision_log_file.close()
            self.decision_log_file = None
        self.initialized = False


class SocialNetworkLogger:
    """
    Logger for tracking social connectivity changes over time.
    """
    
    def __init__(self, output_dir: str = ".", rank: int = 0):
        """
        Initialize the social network logger.
        
        Args:
            output_dir: Directory to write output files
            rank: MPI rank for parallel processing
        """
        self.output_dir = output_dir
        self.rank = rank
        self.social_network_file = None
        self.initialized = False
        self.previous_connections = {}  # Track previous connection levels
        
    @check_args_type
    def initialize(self) -> None:
        """Initialize the social network output file with headers."""
        if self.initialized:
            return
            
        filename = os.path.join(self.output_dir, f"social_network.out.{self.rank}")
        self.social_network_file = open(filename, "w", encoding="utf-8")
        
        # Write header
        header = "#day,agent_id,location,connections,connection_change,location_population,camp_status"
        print(header, file=self.social_network_file)
        
        self.initialized = True
    
    @check_args_type
    def write_social_network_csv(self, agents: List, time: int, timestep_interval: int = 1) -> None:
        """
        Write social network data for agents with connection changes.
        
        Args:
            agents: List of agents to track
            time: Current simulation time
            timestep_interval: Interval between writing files
        """
        if not self.initialized:
            self.initialize()
            
        # Only write at specified intervals
        if time % timestep_interval != 0:
            return
            
        for i, agent in enumerate(agents):
            # Skip agents that have been removed from simulation
            if agent.location is None:
                continue
                
            agent_id = f"{self.rank}-{i}"
            current_connections = agent.attributes.get('connections', 0)
            previous_connections = self.previous_connections.get(agent_id, 0)
            
            # Only log if connections changed or it's the first timestep
            if current_connections != previous_connections or time == 0:
                location_name = agent.location.name if hasattr(agent.location, 'name') else 'unknown'
                connection_change = current_connections - previous_connections
                location_population = getattr(agent.location, 'numAgents', 0)
                camp_status = getattr(agent.location, 'camp', False) or getattr(agent.location, 'idpcamp', False)
                
                # Write data row
                row = f"{time},{agent_id},{location_name},{current_connections},{connection_change},{location_population},{camp_status}"
                print(row, file=self.social_network_file)
                
                # Update previous connections
                self.previous_connections[agent_id] = current_connections
            
        # Flush to ensure data is written
        self.social_network_file.flush()
    
    def close(self) -> None:
        """Close the output file."""
        if self.social_network_file:
            self.social_network_file.close()
            self.social_network_file = None
        self.initialized = False