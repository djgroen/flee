"""
Information sharing protocols for H2.2 Dynamic Information Sharing scenario.

This module implements real-time camp capacity tracking, information lag simulation,
and network-based information propagation for testing dynamic information sharing.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class CapacityUpdate:
    """Represents a capacity update event."""
    day: int
    location: str
    new_capacity: int
    change_reason: str
    source: str = "official"  # official, network, observation


@dataclass
class AgentInformation:
    """Tracks what an agent knows about camp capacities."""
    agent_id: str
    agent_type: str
    capacity_beliefs: Dict[str, int]
    last_update: Dict[str, int]  # Day of last update for each location
    information_age: Dict[str, int]  # Days since last update
    accuracy_score: float = 0.0


class DynamicCapacityManager:
    """Manages dynamic capacity changes and information propagation."""
    
    def __init__(self, capacity_timeline_file: str):
        """
        Initialize capacity manager with timeline data.
        
        Args:
            capacity_timeline_file: Path to capacity timeline CSV
        """
        self.capacity_timeline = self._load_capacity_timeline(capacity_timeline_file)
        self.current_capacities = {}
        self.official_updates = {}  # Official updates with delay
        self.network_updates = {}   # Network updates with shorter delay
        
        # Information lag parameters
        self.official_delay = 5  # Days delay for official updates
        self.network_delay = 1   # Days delay for network updates
        self.information_decay_rate = 0.05  # Daily accuracy decay
        
        # Initialize starting capacities
        self._initialize_capacities()
    
    def _load_capacity_timeline(self, filepath: str) -> pd.DataFrame:
        """Load capacity timeline from CSV file."""
        try:
            df = pd.read_csv(filepath)
            # Handle case where column might be named differently
            if 'Day' in df.columns:
                return df.sort_values('Day')
            else:
                # Create default timeline if file format is unexpected
                return self._create_default_timeline()
        except (FileNotFoundError, KeyError):
            # Create default timeline if file doesn't exist or has wrong format
            return self._create_default_timeline()
    
    def _create_default_timeline(self) -> pd.DataFrame:
        """Create default capacity timeline."""
        return pd.DataFrame({
            'Day': [0, 30, 60, 90],
            'Location': ['Camp_Alpha', 'Camp_Alpha', 'Camp_Beta', 'Camp_Alpha'],
            'Capacity': [4000, 2000, 4000, 3000],
            'Change_Reason': ['Initial', 'Resource constraints', 'Expansion', 'Recovery']
        })
    
    def _initialize_capacities(self):
        """Initialize starting capacities from timeline."""
        initial_updates = self.capacity_timeline[self.capacity_timeline['Day'] == 0]
        for _, row in initial_updates.iterrows():
            self.current_capacities[row['Location']] = row['Capacity']
    
    def update_day(self, current_day: int):
        """Update capacities and information for current day."""
        # Apply real capacity changes
        day_updates = self.capacity_timeline[self.capacity_timeline['Day'] == current_day]
        for _, row in day_updates.iterrows():
            self.current_capacities[row['Location']] = row['Capacity']
            
            # Schedule official updates (with delay)
            official_day = current_day + self.official_delay
            if official_day not in self.official_updates:
                self.official_updates[official_day] = []
            self.official_updates[official_day].append(CapacityUpdate(
                day=current_day,
                location=row['Location'],
                new_capacity=row['Capacity'],
                change_reason=row['Change_Reason'],
                source="official"
            ))
            
            # Schedule network updates (with shorter delay)
            network_day = current_day + self.network_delay
            if network_day not in self.network_updates:
                self.network_updates[network_day] = []
            self.network_updates[network_day].append(CapacityUpdate(
                day=current_day,
                location=row['Location'],
                new_capacity=row['Capacity'],
                change_reason=row['Change_Reason'],
                source="network"
            ))
    
    def get_real_capacity(self, location: str) -> int:
        """Get actual current capacity for a location."""
        return self.current_capacities.get(location, 0)
    
    def get_official_updates(self, day: int) -> List[CapacityUpdate]:
        """Get official updates available on specified day."""
        return self.official_updates.get(day, [])
    
    def get_network_updates(self, day: int) -> List[CapacityUpdate]:
        """Get network updates available on specified day."""
        return self.network_updates.get(day, [])
    
    def get_all_locations(self) -> List[str]:
        """Get list of all locations with dynamic capacity."""
        return list(self.current_capacities.keys())


class NetworkInformationProtocol:
    """Handles information sharing between connected agents."""
    
    def __init__(self, capacity_manager: DynamicCapacityManager):
        """
        Initialize network protocol.
        
        Args:
            capacity_manager: Dynamic capacity manager instance
        """
        self.capacity_manager = capacity_manager
        self.agent_information = {}  # Track agent knowledge
        self.connection_matrix = {}  # Agent connections
        self.info_sharing_events = []  # Log sharing events
        
        # Network parameters
        self.sharing_probability = 0.8  # Probability of sharing when connected
        self.information_accuracy_decay = 0.02  # Daily accuracy decay
        
    def initialize_agent(self, agent_id: str, agent_type: str, connections: List[str] = None):
        """Initialize agent information state."""
        if connections is None:
            connections = []
            
        # Initialize with basic knowledge
        initial_beliefs = {}
        for location in self.capacity_manager.get_all_locations():
            initial_beliefs[location] = self.capacity_manager.get_real_capacity(location)
        
        self.agent_information[agent_id] = AgentInformation(
            agent_id=agent_id,
            agent_type=agent_type,
            capacity_beliefs=initial_beliefs,
            last_update={loc: 0 for loc in initial_beliefs.keys()},
            information_age={loc: 0 for loc in initial_beliefs.keys()}
        )
        
        self.connection_matrix[agent_id] = connections
    
    def update_agent_information(self, agent_id: str, day: int, current_location: str = None):
        """Update agent information based on available updates and connections."""
        if agent_id not in self.agent_information:
            return
        
        agent_info = self.agent_information[agent_id]
        
        # Update information age
        for location in agent_info.information_age:
            agent_info.information_age[location] = day - agent_info.last_update[location]
        
        # Apply information decay
        self._apply_information_decay(agent_info, day)
        
        # Get available updates based on agent type
        if agent_info.agent_type == 's1_baseline':
            # Only official updates
            updates = self.capacity_manager.get_official_updates(day)
        elif agent_info.agent_type == 's2_isolated':
            # Only official updates (no network access)
            updates = self.capacity_manager.get_official_updates(day)
        elif agent_info.agent_type == 's2_connected':
            # Both official and network updates
            updates = (self.capacity_manager.get_official_updates(day) + 
                      self.capacity_manager.get_network_updates(day))
        else:
            updates = []
        
        # Apply updates
        for update in updates:
            self._apply_capacity_update(agent_info, update, day)
        
        # Information sharing at Info_Station
        if current_location == 'Info_Station' and agent_info.agent_type == 's2_connected':
            self._share_information_at_hub(agent_id, day)
        
        # Calculate accuracy score
        agent_info.accuracy_score = self._calculate_accuracy_score(agent_info)
    
    def _apply_information_decay(self, agent_info: AgentInformation, day: int):
        """Apply information decay over time."""
        for location in agent_info.capacity_beliefs:
            age = agent_info.information_age[location]
            if age > 0:
                # Decay accuracy based on age
                real_capacity = self.capacity_manager.get_real_capacity(location)
                current_belief = agent_info.capacity_beliefs[location]
                
                # Move belief toward uncertainty (average capacity)
                decay_factor = 1 - np.exp(-self.information_accuracy_decay * age)
                average_capacity = 3000  # Rough average
                
                decayed_belief = current_belief * (1 - decay_factor) + average_capacity * decay_factor
                agent_info.capacity_beliefs[location] = int(decayed_belief)
    
    def _apply_capacity_update(self, agent_info: AgentInformation, update: CapacityUpdate, day: int):
        """Apply a capacity update to agent's beliefs."""
        agent_info.capacity_beliefs[update.location] = update.new_capacity
        agent_info.last_update[update.location] = day
        agent_info.information_age[update.location] = 0
    
    def _share_information_at_hub(self, agent_id: str, day: int):
        """Handle information sharing when agent visits Info_Station."""
        if agent_id not in self.connection_matrix:
            return
        
        agent_info = self.agent_information[agent_id]
        connections = self.connection_matrix[agent_id]
        
        # Share information with connected agents
        for connected_id in connections:
            if (connected_id in self.agent_information and 
                np.random.random() < self.sharing_probability):
                
                connected_info = self.agent_information[connected_id]
                
                # Share capacity information
                for location in agent_info.capacity_beliefs:
                    # Share if agent has more recent information
                    if (agent_info.last_update[location] > connected_info.last_update[location]):
                        connected_info.capacity_beliefs[location] = agent_info.capacity_beliefs[location]
                        connected_info.last_update[location] = day
                        connected_info.information_age[location] = 0
                
                # Log sharing event
                self.info_sharing_events.append({
                    'day': day,
                    'sharer': agent_id,
                    'receiver': connected_id,
                    'location': 'Info_Station',
                    'information_shared': list(agent_info.capacity_beliefs.keys())
                })
    
    def _calculate_accuracy_score(self, agent_info: AgentInformation) -> float:
        """Calculate accuracy score for agent's capacity beliefs."""
        if not agent_info.capacity_beliefs:
            return 0.0
        
        total_error = 0
        total_capacity = 0
        
        for location, believed_capacity in agent_info.capacity_beliefs.items():
            real_capacity = self.capacity_manager.get_real_capacity(location)
            if real_capacity > 0:
                error = abs(believed_capacity - real_capacity) / real_capacity
                total_error += error
                total_capacity += 1
        
        if total_capacity == 0:
            return 0.0
        
        average_error = total_error / total_capacity
        accuracy = max(0.0, 1.0 - average_error)
        return accuracy
    
    def get_agent_beliefs(self, agent_id: str) -> Dict[str, int]:
        """Get agent's current capacity beliefs."""
        if agent_id not in self.agent_information:
            return {}
        return self.agent_information[agent_id].capacity_beliefs.copy()
    
    def get_information_accuracy(self, agent_id: str) -> float:
        """Get agent's information accuracy score."""
        if agent_id not in self.agent_information:
            return 0.0
        return self.agent_information[agent_id].accuracy_score
    
    def get_sharing_statistics(self) -> Dict[str, Any]:
        """Get statistics about information sharing events."""
        if not self.info_sharing_events:
            return {
                'total_sharing_events': 0,
                'average_sharing_per_day': 0.0,
                'unique_sharers': 0,
                'unique_receivers': 0
            }
        
        events_df = pd.DataFrame(self.info_sharing_events)
        
        return {
            'total_sharing_events': len(self.info_sharing_events),
            'average_sharing_per_day': len(self.info_sharing_events) / (events_df['day'].max() - events_df['day'].min() + 1),
            'unique_sharers': events_df['sharer'].nunique(),
            'unique_receivers': events_df['receiver'].nunique(),
            'sharing_timeline': events_df.groupby('day').size().to_dict()
        }


class H2_2_SimulationController:
    """Main controller for H2.2 Dynamic Information Sharing scenario."""
    
    def __init__(self, scenario_directory: str):
        """
        Initialize simulation controller.
        
        Args:
            scenario_directory: Path to scenario directory
        """
        self.scenario_dir = Path(scenario_directory)
        
        # Initialize components
        capacity_file = self.scenario_dir / 'capacity_timeline.csv'
        self.capacity_manager = DynamicCapacityManager(str(capacity_file))
        self.network_protocol = NetworkInformationProtocol(self.capacity_manager)
        
        # Simulation state
        self.current_day = 0
        self.simulation_log = []
    
    def initialize_simulation(self, agent_configs: List[Dict[str, Any]]):
        """Initialize simulation with agent configurations."""
        for config in agent_configs:
            agent_id = config['agent_id']
            agent_type = config['agent_type']
            connections = config.get('connections', [])
            
            self.network_protocol.initialize_agent(agent_id, agent_type, connections)
    
    def step_simulation(self, day: int, agent_locations: Dict[str, str] = None):
        """Step simulation forward one day."""
        self.current_day = day
        
        # Update capacity manager
        self.capacity_manager.update_day(day)
        
        # Update agent information
        if agent_locations is None:
            agent_locations = {}
        
        for agent_id in self.network_protocol.agent_information:
            current_location = agent_locations.get(agent_id, None)
            self.network_protocol.update_agent_information(agent_id, day, current_location)
        
        # Log simulation state
        self._log_simulation_state(day)
    
    def _log_simulation_state(self, day: int):
        """Log current simulation state."""
        state = {
            'day': day,
            'real_capacities': self.capacity_manager.current_capacities.copy(),
            'agent_accuracies': {},
            'information_sharing_events': len(self.network_protocol.info_sharing_events)
        }
        
        for agent_id, agent_info in self.network_protocol.agent_information.items():
            state['agent_accuracies'][agent_id] = agent_info.accuracy_score
        
        self.simulation_log.append(state)
    
    def get_simulation_results(self) -> Dict[str, Any]:
        """Get comprehensive simulation results."""
        return {
            'simulation_log': self.simulation_log,
            'final_capacities': self.capacity_manager.current_capacities,
            'sharing_statistics': self.network_protocol.get_sharing_statistics(),
            'agent_final_states': {
                agent_id: {
                    'beliefs': info.capacity_beliefs,
                    'accuracy': info.accuracy_score,
                    'information_age': info.information_age
                }
                for agent_id, info in self.network_protocol.agent_information.items()
            }
        }


if __name__ == "__main__":
    # Example usage and testing
    scenario_dir = Path(__file__).parent
    controller = H2_2_SimulationController(str(scenario_dir))
    
    # Test agent configurations
    test_agents = [
        {'agent_id': 'agent_1', 'agent_type': 's1_baseline', 'connections': []},
        {'agent_id': 'agent_2', 'agent_type': 's2_isolated', 'connections': []},
        {'agent_id': 'agent_3', 'agent_type': 's2_connected', 'connections': ['agent_4', 'agent_5']},
        {'agent_id': 'agent_4', 'agent_type': 's2_connected', 'connections': ['agent_3']},
        {'agent_id': 'agent_5', 'agent_type': 's2_connected', 'connections': ['agent_3']}
    ]
    
    controller.initialize_simulation(test_agents)
    
    # Simulate several days
    for day in range(0, 100, 10):
        # Simulate some agents visiting Info_Station
        agent_locations = {}
        if day % 20 == 0:  # Every 20 days, some agents visit Info_Station
            agent_locations = {
                'agent_3': 'Info_Station',
                'agent_4': 'Info_Station'
            }
        
        controller.step_simulation(day, agent_locations)
    
    # Get results
    results = controller.get_simulation_results()
    
    print("H2.2 Dynamic Information Sharing Test Results")
    print("=" * 50)
    print(f"Total sharing events: {results['sharing_statistics']['total_sharing_events']}")
    print(f"Unique sharers: {results['sharing_statistics']['unique_sharers']}")
    
    print("\nFinal agent accuracies:")
    for agent_id, state in results['agent_final_states'].items():
        print(f"  {agent_id}: {state['accuracy']:.3f}")
    
    print("\nCapacity timeline test completed successfully!")