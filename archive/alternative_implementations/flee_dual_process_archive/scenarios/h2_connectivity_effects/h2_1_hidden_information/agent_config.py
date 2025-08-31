"""
Agent configuration for H2.1 Hidden Information scenario.

This module defines different agent types with varying social connectivity
and information access capabilities for testing Hypothesis 2.
"""

import numpy as np
from typing import Dict, List, Any


class AgentTypeConfig:
    """Configuration for different agent types in H2.1 scenario."""
    
    # Agent type definitions
    AGENT_TYPES = {
        's1_baseline': {
            'name': 'S1 Baseline',
            'description': 'System 1 agents with no social connectivity',
            'system2_active': False,
            'social_connectivity': 0.0,
            'information_sharing': False,
            'visibility_threshold': 1.0,  # Can only see fully visible locations
            'discovery_probability': 0.0,  # Cannot discover hidden locations
            'decision_speed': 'fast',
            'population_fraction': 0.33
        },
        
        's2_isolated': {
            'name': 'S2 Isolated', 
            'description': 'System 2 agents without social connections',
            'system2_active': True,
            'social_connectivity': 0.0,
            'information_sharing': False,
            'visibility_threshold': 1.0,  # Can only see fully visible locations
            'discovery_probability': 0.0,  # Cannot discover hidden locations
            'decision_speed': 'deliberative',
            'population_fraction': 0.33
        },
        
        's2_connected': {
            'name': 'S2 Connected',
            'description': 'System 2 agents with social network connections',
            'system2_active': True,
            'social_connectivity': 5.0,  # Average connections per agent
            'information_sharing': True,
            'visibility_threshold': 0.5,  # Can discover partially visible locations
            'discovery_probability': 0.8,  # High probability of discovering hidden locations
            'decision_speed': 'deliberative',
            'population_fraction': 0.34
        }
    }
    
    @classmethod
    def get_agent_config(cls, agent_type: str) -> Dict[str, Any]:
        """Get configuration for specified agent type."""
        if agent_type not in cls.AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls.AGENT_TYPES[agent_type].copy()
    
    @classmethod
    def get_all_agent_types(cls) -> List[str]:
        """Get list of all available agent types."""
        return list(cls.AGENT_TYPES.keys())
    
    @classmethod
    def validate_population_fractions(cls) -> bool:
        """Validate that population fractions sum to 1.0."""
        total = sum(config['population_fraction'] for config in cls.AGENT_TYPES.values())
        return abs(total - 1.0) < 1e-6


class InformationSharingMechanics:
    """Mechanics for information sharing between connected agents."""
    
    def __init__(self, decay_rate: float = 0.02, propagation_rate: float = 0.1):
        """
        Initialize information sharing mechanics.
        
        Args:
            decay_rate: Rate at which information decays over time
            propagation_rate: Rate at which information spreads through network
        """
        self.decay_rate = decay_rate
        self.propagation_rate = propagation_rate
        self.information_state = {}  # Track what each agent knows
        
    def update_agent_knowledge(self, agent_id: str, location: str, 
                             discovered_locations: List[str], day: int):
        """Update agent's knowledge based on current location and connections."""
        if agent_id not in self.information_state:
            self.information_state[agent_id] = {
                'known_locations': set(['Origin', 'Obvious_Camp']),  # Always known
                'discovery_day': {},
                'last_update': day
            }
        
        agent_info = self.information_state[agent_id]
        
        # Information decay
        days_since_update = day - agent_info['last_update']
        if days_since_update > 0:
            self._apply_information_decay(agent_info, days_since_update)
        
        # Location-based discovery
        if location == 'Information_Hub':
            if 'Hidden_Camp' not in agent_info['known_locations']:
                agent_info['known_locations'].add('Hidden_Camp')
                agent_info['discovery_day']['Hidden_Camp'] = day
        
        # Add any externally discovered locations
        for loc in discovered_locations:
            if loc not in agent_info['known_locations']:
                agent_info['known_locations'].add(loc)
                agent_info['discovery_day'][loc] = day
        
        agent_info['last_update'] = day
    
    def share_information(self, agent_id: str, connected_agents: List[str], day: int):
        """Share information between connected agents."""
        if agent_id not in self.information_state:
            return
        
        agent_info = self.information_state[agent_id]
        
        for connected_id in connected_agents:
            if connected_id not in self.information_state:
                continue
                
            connected_info = self.information_state[connected_id]
            
            # Share knowledge with probability based on propagation rate
            for location in agent_info['known_locations']:
                if (location not in connected_info['known_locations'] and 
                    np.random.random() < self.propagation_rate):
                    connected_info['known_locations'].add(location)
                    connected_info['discovery_day'][location] = day
    
    def _apply_information_decay(self, agent_info: Dict, days_elapsed: int):
        """Apply information decay over time."""
        # Some locations never decay (Origin, Obvious_Camp)
        permanent_locations = {'Origin', 'Obvious_Camp'}
        
        locations_to_remove = []
        for location in agent_info['known_locations']:
            if location not in permanent_locations:
                # Probability of forgetting increases with time
                forget_probability = 1 - np.exp(-self.decay_rate * days_elapsed)
                if np.random.random() < forget_probability:
                    locations_to_remove.append(location)
        
        for location in locations_to_remove:
            agent_info['known_locations'].discard(location)
            if location in agent_info['discovery_day']:
                del agent_info['discovery_day'][location]
    
    def get_agent_knowledge(self, agent_id: str) -> Dict[str, Any]:
        """Get current knowledge state for an agent."""
        if agent_id not in self.information_state:
            return {
                'known_locations': {'Origin', 'Obvious_Camp'},
                'discovery_day': {},
                'last_update': 0
            }
        return self.information_state[agent_id].copy()
    
    def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get statistics about information discovery and propagation."""
        if not self.information_state:
            return {}
        
        stats = {
            'total_agents': len(self.information_state),
            'hidden_camp_discoverers': 0,
            'average_discovery_day': 0,
            'information_spread_rate': 0
        }
        
        discovery_days = []
        for agent_info in self.information_state.values():
            if 'Hidden_Camp' in agent_info['known_locations']:
                stats['hidden_camp_discoverers'] += 1
                if 'Hidden_Camp' in agent_info['discovery_day']:
                    discovery_days.append(agent_info['discovery_day']['Hidden_Camp'])
        
        if discovery_days:
            stats['average_discovery_day'] = np.mean(discovery_days)
            stats['information_spread_rate'] = len(discovery_days) / len(self.information_state)
        
        return stats


# Configuration validation
if __name__ == "__main__":
    # Validate configuration
    assert AgentTypeConfig.validate_population_fractions(), "Population fractions must sum to 1.0"
    
    print("Agent Type Configurations:")
    for agent_type in AgentTypeConfig.get_all_agent_types():
        config = AgentTypeConfig.get_agent_config(agent_type)
        print(f"\n{config['name']}:")
        print(f"  - System 2 Active: {config['system2_active']}")
        print(f"  - Social Connectivity: {config['social_connectivity']}")
        print(f"  - Information Sharing: {config['information_sharing']}")
        print(f"  - Population Fraction: {config['population_fraction']}")
    
    print("\nConfiguration validation passed!")