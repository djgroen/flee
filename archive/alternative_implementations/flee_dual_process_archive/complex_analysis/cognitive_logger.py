"""
Cognitive State Logger for Dual Process Experiments

This module provides logging functionality for tracking cognitive states
and decision-making processes in Flee simulations.
"""

from __future__ import annotations, print_function
import os
import csv
import numpy as np
from datetime import datetime
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


class MetricsSummaryLogger:
    """
    Logger for generating hypothesis-specific metrics and summary data.
    """
    
    def __init__(self, output_dir: str = ".", rank: int = 0):
        """
        Initialize the metrics summary logger.
        
        Args:
            output_dir: Directory to write output files
            rank: MPI rank for parallel processing
        """
        self.output_dir = output_dir
        self.rank = rank
        self.metrics_data = {}
        self.hypothesis_data = {}
        
    @check_args_type
    def collect_timestep_metrics(self, agents: List, time: int) -> None:
        """
        Collect metrics for the current timestep.
        
        Args:
            agents: List of agents to analyze
            time: Current simulation time
        """
        if time not in self.metrics_data:
            self.metrics_data[time] = {}
            
        # H1: Decision quality metrics
        h1_metrics = self._calculate_h1_metrics(agents, time)
        self.metrics_data[time]['h1_decision_quality'] = h1_metrics
        
        # H2: Connectivity effects metrics
        h2_metrics = self._calculate_h2_metrics(agents, time)
        self.metrics_data[time]['h2_connectivity_effects'] = h2_metrics
        
        # H3: Cognitive pressure metrics
        h3_metrics = self._calculate_h3_metrics(agents, time)
        self.metrics_data[time]['h3_cognitive_pressure'] = h3_metrics
        
        # H4: Population diversity metrics
        h4_metrics = self._calculate_h4_metrics(agents, time)
        self.metrics_data[time]['h4_population_diversity'] = h4_metrics
        
    def _calculate_h1_metrics(self, agents: List, time: int) -> Dict[str, Any]:
        """Calculate H1: Speed vs Optimality metrics."""
        s1_agents = [a for a in agents if getattr(a, 'cognitive_state', 'S1') == 'S1']
        s2_agents = [a for a in agents if getattr(a, 'cognitive_state', 'S1') == 'S2']
        
        # Decision speed metrics
        s1_avg_decision_time = sum(len(getattr(a, 'decision_history', [])) for a in s1_agents) / max(1, len(s1_agents))
        s2_avg_decision_time = sum(len(getattr(a, 'decision_history', [])) for a in s2_agents) / max(1, len(s2_agents))
        
        # Route optimality metrics (distance efficiency)
        s1_avg_route_length = sum(len(getattr(a, 'route', [])) for a in s1_agents) / max(1, len(s1_agents))
        s2_avg_route_length = sum(len(getattr(a, 'route', [])) for a in s2_agents) / max(1, len(s2_agents))
        
        # Safety achievement metrics
        s1_in_safe_locations = sum(1 for a in s1_agents if a.location and getattr(a.location, 'conflict', 1) < 0.3)
        s2_in_safe_locations = sum(1 for a in s2_agents if a.location and getattr(a.location, 'conflict', 1) < 0.3)
        
        return {
            'time_to_move_s1': s1_avg_decision_time,
            'time_to_move_s2': s2_avg_decision_time,
            'route_efficiency_s1': 1.0 / max(1, s1_avg_route_length),
            'route_efficiency_s2': 1.0 / max(1, s2_avg_route_length),
            'safety_achievement_s1': s1_in_safe_locations / max(1, len(s1_agents)),
            'safety_achievement_s2': s2_in_safe_locations / max(1, len(s2_agents)),
            's1_agent_count': len(s1_agents),
            's2_agent_count': len(s2_agents)
        }
        
    def _calculate_h2_metrics(self, agents: List, time: int) -> Dict[str, Any]:
        """Calculate H2: Connectivity effects metrics."""
        connected_agents = [a for a in agents if a.attributes.get('connections', 0) >= 3]
        isolated_agents = [a for a in agents if a.attributes.get('connections', 0) < 3]
        
        # Information sharing metrics
        agents_with_shared_info = sum(1 for a in agents if '_safety_info' in a.attributes)
        agents_using_shared_routes = sum(1 for a in agents if '_shared_route' in a.attributes)
        
        # Destination discovery metrics
        connected_unique_destinations = len(set(a.location.name for a in connected_agents if a.location))
        isolated_unique_destinations = len(set(a.location.name for a in isolated_agents if a.location))
        
        return {
            'information_propagation_rate': agents_with_shared_info / max(1, len(agents)),
            'shared_route_usage': agents_using_shared_routes / max(1, len(agents)),
            'connected_destination_diversity': connected_unique_destinations / max(1, len(connected_agents)),
            'isolated_destination_diversity': isolated_unique_destinations / max(1, len(isolated_agents)),
            'avg_connectivity_connected': sum(a.attributes.get('connections', 0) for a in connected_agents) / max(1, len(connected_agents)),
            'avg_connectivity_isolated': sum(a.attributes.get('connections', 0) for a in isolated_agents) / max(1, len(isolated_agents)),
            'connected_agent_count': len(connected_agents),
            'isolated_agent_count': len(isolated_agents)
        }
        
    def _calculate_h3_metrics(self, agents: List, time: int) -> Dict[str, Any]:
        """Calculate H3: Cognitive pressure and phase transition metrics."""
        pressures = []
        s2_activations = []
        
        for agent in agents:
            if hasattr(agent, 'calculate_cognitive_pressure'):
                pressure = agent.calculate_cognitive_pressure(time)
                pressures.append(pressure)
                s2_activations.append(1 if getattr(agent, 'cognitive_state', 'S1') == 'S2' else 0)
        
        avg_pressure = sum(pressures) / max(1, len(pressures))
        s2_activation_rate = sum(s2_activations) / max(1, len(s2_activations))
        
        # Phase transition detection
        pressure_bins = {}
        for i, pressure in enumerate(pressures):
            bin_key = round(pressure, 1)
            if bin_key not in pressure_bins:
                pressure_bins[bin_key] = []
            pressure_bins[bin_key].append(s2_activations[i])
        
        return {
            'avg_cognitive_pressure': avg_pressure,
            's2_activation_rate': s2_activation_rate,
            'pressure_distribution': pressure_bins,
            'total_s2_activations': sum(getattr(a, 'system2_activations', 0) for a in agents),
            'agents_above_threshold': sum(1 for p in pressures if p > 0.5),
            'pressure_variance': np.var(pressures) if pressures else 0
        }
        
    def _calculate_h4_metrics(self, agents: List, time: int) -> Dict[str, Any]:
        """Calculate H4: Population diversity metrics."""
        s1_agents = [a for a in agents if getattr(a, 'cognitive_state', 'S1') == 'S1']
        s2_agents = [a for a in agents if getattr(a, 'cognitive_state', 'S1') == 'S2']
        
        # Population composition
        s1_ratio = len(s1_agents) / max(1, len(agents))
        s2_ratio = len(s2_agents) / max(1, len(agents))
        
        # Collective performance metrics
        total_distance = sum(getattr(a, 'distance_travelled', 0) for a in agents)
        avg_distance = total_distance / max(1, len(agents))
        
        # Information cascade metrics
        s1_scouts = sum(1 for a in s1_agents if len(getattr(a, 'route', [])) > 0)
        s2_followers = sum(1 for a in s2_agents if '_shared_route' in a.attributes)
        
        # Resilience metrics (agents in safe locations)
        safe_agents = sum(1 for a in agents if a.location and getattr(a.location, 'conflict', 1) < 0.3)
        resilience_score = safe_agents / max(1, len(agents))
        
        return {
            's1_population_ratio': s1_ratio,
            's2_population_ratio': s2_ratio,
            'population_diversity_index': 1 - (s1_ratio**2 + s2_ratio**2),  # Simpson's diversity index
            'collective_avg_distance': avg_distance,
            'scout_behavior_rate': s1_scouts / max(1, len(s1_agents)),
            'follower_behavior_rate': s2_followers / max(1, len(s2_agents)),
            'collective_resilience': resilience_score,
            'information_cascade_strength': s2_followers / max(1, s1_scouts) if s1_scouts > 0 else 0
        }
        
    @check_args_type
    def write_metrics_summary_json(self) -> None:
        """Write metrics summary to JSON file."""
        import json
        
        filename = os.path.join(self.output_dir, f"metrics_summary.{self.rank}.json")
        
        # Calculate aggregate metrics across all timesteps
        summary = {
            'simulation_metadata': {
                'total_timesteps': len(self.metrics_data),
                'rank': self.rank,
                'generated_at': str(datetime.now())
            },
            'h1_decision_quality_summary': self._aggregate_h1_metrics(),
            'h2_connectivity_effects_summary': self._aggregate_h2_metrics(),
            'h3_cognitive_pressure_summary': self._aggregate_h3_metrics(),
            'h4_population_diversity_summary': self._aggregate_h4_metrics(),
            'timestep_data': self.metrics_data
        }
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
    def _aggregate_h1_metrics(self) -> Dict[str, Any]:
        """Aggregate H1 metrics across timesteps."""
        if not self.metrics_data:
            return {}
            
        h1_data = [data.get('h1_decision_quality', {}) for data in self.metrics_data.values()]
        
        return {
            'avg_decision_speed_difference': np.mean([d.get('time_to_move_s2', 0) - d.get('time_to_move_s1', 0) for d in h1_data]),
            'avg_route_efficiency_difference': np.mean([d.get('route_efficiency_s2', 0) - d.get('route_efficiency_s1', 0) for d in h1_data]),
            'avg_safety_achievement_difference': np.mean([d.get('safety_achievement_s2', 0) - d.get('safety_achievement_s1', 0) for d in h1_data]),
            'final_s1_count': h1_data[-1].get('s1_agent_count', 0) if h1_data else 0,
            'final_s2_count': h1_data[-1].get('s2_agent_count', 0) if h1_data else 0
        }
        
    def _aggregate_h2_metrics(self) -> Dict[str, Any]:
        """Aggregate H2 metrics across timesteps."""
        if not self.metrics_data:
            return {}
            
        h2_data = [data.get('h2_connectivity_effects', {}) for data in self.metrics_data.values()]
        
        return {
            'peak_information_propagation': max(d.get('information_propagation_rate', 0) for d in h2_data),
            'avg_shared_route_usage': np.mean([d.get('shared_route_usage', 0) for d in h2_data]),
            'connectivity_advantage': np.mean([d.get('connected_destination_diversity', 0) - d.get('isolated_destination_diversity', 0) for d in h2_data]),
            'final_connected_count': h2_data[-1].get('connected_agent_count', 0) if h2_data else 0,
            'final_isolated_count': h2_data[-1].get('isolated_agent_count', 0) if h2_data else 0
        }
        
    def _aggregate_h3_metrics(self) -> Dict[str, Any]:
        """Aggregate H3 metrics across timesteps."""
        if not self.metrics_data:
            return {}
            
        h3_data = [data.get('h3_cognitive_pressure', {}) for data in self.metrics_data.values()]
        
        return {
            'peak_cognitive_pressure': max(d.get('avg_cognitive_pressure', 0) for d in h3_data),
            'peak_s2_activation_rate': max(d.get('s2_activation_rate', 0) for d in h3_data),
            'total_s2_activations': sum(d.get('total_s2_activations', 0) for d in h3_data),
            'pressure_threshold_crossings': sum(1 for d in h3_data if d.get('avg_cognitive_pressure', 0) > 0.5),
            'final_pressure_variance': h3_data[-1].get('pressure_variance', 0) if h3_data else 0
        }
        
    def _aggregate_h4_metrics(self) -> Dict[str, Any]:
        """Aggregate H4 metrics across timesteps."""
        if not self.metrics_data:
            return {}
            
        h4_data = [data.get('h4_population_diversity', {}) for data in self.metrics_data.values()]
        
        return {
            'avg_population_diversity': np.mean([d.get('population_diversity_index', 0) for d in h4_data]),
            'peak_collective_resilience': max(d.get('collective_resilience', 0) for d in h4_data),
            'avg_information_cascade_strength': np.mean([d.get('information_cascade_strength', 0) for d in h4_data]),
            'final_scout_rate': h4_data[-1].get('scout_behavior_rate', 0) if h4_data else 0,
            'final_follower_rate': h4_data[-1].get('follower_behavior_rate', 0) if h4_data else 0
        }
        
    @check_args_type
    def write_hypothesis_specific_analysis_pkl(self) -> None:
        """Write detailed hypothesis-specific analysis to pickle file."""
        import pickle
        
        filename = os.path.join(self.output_dir, f"hypothesis_specific_analysis.{self.rank}.pkl")
        
        analysis_data = {
            'raw_metrics_data': self.metrics_data,
            'h1_analysis': self._detailed_h1_analysis(),
            'h2_analysis': self._detailed_h2_analysis(),
            'h3_analysis': self._detailed_h3_analysis(),
            'h4_analysis': self._detailed_h4_analysis(),
            'cross_hypothesis_correlations': self._calculate_cross_hypothesis_correlations()
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(analysis_data, f)
            
    def _detailed_h1_analysis(self) -> Dict[str, Any]:
        """Detailed H1 analysis for pickle file."""
        return {
            'decision_quality_timeseries': [data.get('h1_decision_quality', {}) for data in self.metrics_data.values()],
            'speed_optimality_tradeoff': 'Detailed analysis would go here',
            'statistical_tests': 'T-tests and effect sizes would be calculated here'
        }
        
    def _detailed_h2_analysis(self) -> Dict[str, Any]:
        """Detailed H2 analysis for pickle file."""
        return {
            'connectivity_effects_timeseries': [data.get('h2_connectivity_effects', {}) for data in self.metrics_data.values()],
            'information_network_analysis': 'Network analysis would go here',
            'connectivity_thresholds': 'Threshold analysis would go here'
        }
        
    def _detailed_h3_analysis(self) -> Dict[str, Any]:
        """Detailed H3 analysis for pickle file."""
        return {
            'pressure_timeseries': [data.get('h3_cognitive_pressure', {}) for data in self.metrics_data.values()],
            'phase_transition_analysis': 'Sigmoid fitting and critical point detection would go here',
            'dimensionless_scaling': 'Scaling law analysis would go here'
        }
        
    def _detailed_h4_analysis(self) -> Dict[str, Any]:
        """Detailed H4 analysis for pickle file."""
        return {
            'diversity_timeseries': [data.get('h4_population_diversity', {}) for data in self.metrics_data.values()],
            'collective_intelligence_analysis': 'Swarm intelligence metrics would go here',
            'diversity_advantage_quantification': 'Statistical analysis of diversity benefits would go here'
        }
        
    def _calculate_cross_hypothesis_correlations(self) -> Dict[str, Any]:
        """Calculate correlations between different hypothesis metrics."""
        return {
            'h1_h2_correlation': 'Correlation between decision quality and connectivity',
            'h2_h3_correlation': 'Correlation between connectivity and cognitive pressure',
            'h3_h4_correlation': 'Correlation between pressure and diversity',
            'all_hypotheses_pca': 'Principal component analysis across all metrics'
        }


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