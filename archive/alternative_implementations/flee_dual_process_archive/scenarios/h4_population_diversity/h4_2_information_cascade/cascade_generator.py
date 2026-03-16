"""
Information Cascade Test Scenario Generator

Creates scenarios to test S1 "scout" and S2 "follower" behavior interactions.
Tests information flow and decision correlation between agent types.
"""

import os
import csv
import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DestinationInfo:
    """Information about a destination for cascade testing"""
    name: str
    visibility: float  # How easily discovered (0.0-1.0)
    quality: float     # Actual quality/desirability (0.0-1.0)
    capacity: int
    discovery_difficulty: float  # How hard to find without information
    information_value: float     # Value of information about this destination


class InformationCascadeGenerator:
    """Generates information cascade test scenarios"""
    
    def __init__(self, base_config: Dict[str, Any]):
        """
        Initialize cascade generator
        
        Args:
            base_config: Base configuration parameters
        """
        self.base_config = base_config
        self.destinations = self._initialize_destinations()
    
    def _initialize_destinations(self) -> List[DestinationInfo]:
        """Initialize destination information for cascade testing"""
        return [
            DestinationInfo(
                name="Obvious_Camp",
                visibility=1.0,
                quality=0.6,
                capacity=3000,
                discovery_difficulty=0.1,
                information_value=0.3
            ),
            DestinationInfo(
                name="Hidden_Good_Camp",
                visibility=0.2,
                quality=0.9,
                capacity=4000,
                discovery_difficulty=0.8,
                information_value=0.9
            ),
            DestinationInfo(
                name="Moderate_Camp",
                visibility=0.6,
                quality=0.7,
                capacity=3500,
                discovery_difficulty=0.4,
                information_value=0.6
            ),
            DestinationInfo(
                name="Late_Discovery_Camp",
                visibility=0.1,
                quality=0.8,
                capacity=5000,
                discovery_difficulty=0.9,
                information_value=0.8
            )
        ]
    
    def generate_scenario(self,
                         scenario_name: str,
                         output_dir: str,
                         scout_ratio: float = 0.3,
                         information_sharing_rate: float = 0.7,
                         discovery_delay: int = 5) -> Dict[str, str]:
        """
        Generate complete information cascade scenario
        
        Args:
            scenario_name: Name for the scenario
            output_dir: Directory to save scenario files
            scout_ratio: Proportion of S1 "scout" agents
            information_sharing_rate: Rate of information sharing
            discovery_delay: Days between S1 discovery and S2 adoption
            
        Returns:
            Dictionary mapping file types to file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate network topology with information asymmetry
        locations_file = self._generate_locations(output_dir)
        routes_file = self._generate_routes(output_dir)
        
        # Generate conflict scenario
        conflicts_file = self._generate_conflicts(output_dir)
        
        # Generate information discovery timeline
        discovery_file = self._generate_discovery_timeline(output_dir, discovery_delay)
        
        # Generate agent configuration for scout-follower dynamics
        agent_config_file = self._generate_agent_config(output_dir, scout_ratio, information_sharing_rate)
        
        # Generate simulation period
        sim_period_file = self._generate_sim_period(output_dir)
        
        # Generate scenario metadata
        metadata_file = self._generate_metadata(output_dir, scenario_name, scout_ratio)
        
        return {
            'locations': locations_file,
            'routes': routes_file,
            'conflicts': conflicts_file,
            'discovery_timeline': discovery_file,
            'agent_config': agent_config_file,
            'sim_period': sim_period_file,
            'metadata': metadata_file
        }
    
    def _generate_locations(self, output_dir: str) -> str:
        """Generate locations.csv with information asymmetry"""
        locations_file = os.path.join(output_dir, "locations.csv")
        
        locations = [
            {
                'name': 'Origin',
                'region': 'conflict_zone',
                'country': 'TestCountry',
                'lat': 0.0,
                'lon': 0.0,
                'location_type': 'town',
                'conflict_date': '2023-01-01',
                'population': 40000
            },
            {
                'name': 'Information_Hub',
                'region': 'transit_zone',
                'country': 'TestCountry',
                'lat': 0.5,
                'lon': 0.5,
                'location_type': 'town',
                'conflict_date': '',
                'population': 8000
            }
        ]
        
        # Add destinations with varying visibility
        for i, dest in enumerate(self.destinations):
            locations.append({
                'name': dest.name,
                'region': 'safe_zone',
                'country': 'NeighborCountry',
                'lat': 1.0 + (i * 0.2),
                'lon': i * 0.3,
                'location_type': 'camp',
                'conflict_date': '',
                'population': 0,
                'capacity': dest.capacity,
                'visibility': dest.visibility,
                'quality': dest.quality,
                'discovery_difficulty': dest.discovery_difficulty
            })
        
        with open(locations_file, 'w', newline='') as f:
            if locations:
                # Get all possible fieldnames from all locations
                all_fieldnames = set()
                for location in locations:
                    all_fieldnames.update(location.keys())
                
                writer = csv.DictWriter(f, fieldnames=sorted(all_fieldnames))
                writer.writeheader()
                writer.writerows(locations)
        
        return locations_file
    
    def _generate_routes(self, output_dir: str) -> str:
        """Generate routes.csv with varying accessibility"""
        routes_file = os.path.join(output_dir, "routes.csv")
        
        routes = [
            # From Origin to Information Hub
            {'name1': 'Origin', 'name2': 'Information_Hub', 'distance': 40.0, 'forced_redirection': 0},
        ]
        
        # Routes from Information Hub to destinations
        base_distances = [60.0, 120.0, 90.0, 150.0]  # Varying distances
        
        for i, dest in enumerate(self.destinations):
            # Distance modified by discovery difficulty
            distance = base_distances[i] * (1.0 + dest.discovery_difficulty * 0.5)
            
            routes.append({
                'name1': 'Information_Hub',
                'name2': dest.name,
                'distance': distance,
                'forced_redirection': 0,
                'discovery_difficulty': dest.discovery_difficulty
            })
        
        # Direct routes from Origin (for scouts)
        for i, dest in enumerate(self.destinations):
            if dest.visibility > 0.5:  # Only obvious destinations have direct routes
                distance = base_distances[i] * 1.2  # Slightly longer direct routes
                routes.append({
                    'name1': 'Origin',
                    'name2': dest.name,
                    'distance': distance,
                    'forced_redirection': 0
                })
        
        with open(routes_file, 'w', newline='') as f:
            if routes:
                # Get all possible fieldnames from all routes
                all_fieldnames = set()
                for route in routes:
                    all_fieldnames.update(route.keys())
                
                writer = csv.DictWriter(f, fieldnames=sorted(all_fieldnames))
                writer.writeheader()
                writer.writerows(routes)
        
        return routes_file
    
    def _generate_conflicts(self, output_dir: str) -> str:
        """Generate conflicts.csv with gradual escalation"""
        conflicts_file = os.path.join(output_dir, "conflicts.csv")
        
        conflicts = []
        
        # Gradual conflict escalation to allow for information discovery
        for day in range(60):  # Longer scenario for cascade observation
            if day <= 40:
                # Gradual escalation
                intensity = min(0.2 + (day * 0.015), 0.8)
            else:
                # Stabilization
                intensity = 0.8
            
            conflicts.append({
                'day': day,
                'location': 'Origin',
                'intensity': intensity
            })
        
        with open(conflicts_file, 'w', newline='') as f:
            if conflicts:
                # Get all possible fieldnames from all conflicts
                all_fieldnames = set()
                for conflict in conflicts:
                    all_fieldnames.update(conflict.keys())
                
                writer = csv.DictWriter(f, fieldnames=sorted(all_fieldnames))
                writer.writeheader()
                writer.writerows(conflicts)
        
        return conflicts_file
    
    def _generate_discovery_timeline(self, output_dir: str, discovery_delay: int) -> str:
        """Generate discovery timeline for information cascade analysis"""
        discovery_file = os.path.join(output_dir, "discovery_timeline.csv")
        
        discoveries = []
        
        # S1 scouts discover destinations at different times
        discovery_days = {
            'Obvious_Camp': 3,      # Discovered early by everyone
            'Moderate_Camp': 8,     # Discovered by scouts first
            'Hidden_Good_Camp': 15, # Discovered by persistent scouts
            'Late_Discovery_Camp': 25  # Discovered late in scenario
        }
        
        for dest_name, discovery_day in discovery_days.items():
            dest_info = next(d for d in self.destinations if d.name == dest_name)
            
            discoveries.append({
                'day': discovery_day,
                'destination': dest_name,
                'discoverer_type': 'S1_scout',
                'visibility': dest_info.visibility,
                'quality': dest_info.quality,
                'information_value': dest_info.information_value,
                'expected_s2_adoption_day': discovery_day + discovery_delay
            })
        
        with open(discovery_file, 'w', newline='') as f:
            if discoveries:
                # Get all possible fieldnames from all discoveries
                all_fieldnames = set()
                for discovery in discoveries:
                    all_fieldnames.update(discovery.keys())
                
                writer = csv.DictWriter(f, fieldnames=sorted(all_fieldnames))
                writer.writeheader()
                writer.writerows(discoveries)
        
        return discovery_file
    
    def _generate_agent_config(self, output_dir: str, scout_ratio: float, sharing_rate: float) -> str:
        """Generate agent configuration for scout-follower dynamics"""
        config_file = os.path.join(output_dir, "agent_config.yml")
        
        config_content = f"""# Agent Configuration for H4.2 Information Cascade Test
# Scout Ratio: {scout_ratio}
# Information Sharing Rate: {sharing_rate}

population:
  total_agents: 8000
  scout_ratio: {scout_ratio}  # S1 agents acting as scouts
  follower_ratio: {1.0 - scout_ratio}  # S2 agents acting as followers

scout_profile:
  cognitive_type: "S1"
  decision_speed: 0.9
  exploration_tendency: 0.8
  information_sharing: {sharing_rate}
  discovery_capability: 0.9
  risk_tolerance: 0.7
  
follower_profile:
  cognitive_type: "S2"
  decision_speed: 0.3
  exploration_tendency: 0.3
  information_receptivity: 0.9
  deliberation_depth: 0.8
  social_connectivity: 6.0
  
information_dynamics:
  sharing_rate: {sharing_rate}
  adoption_delay: 3  # Days for S2 to adopt S1 discoveries
  information_decay: 0.05  # Daily decay of information value
  network_effects: 0.6  # Strength of network information sharing
  
cascade_parameters:
  discovery_threshold: 0.1  # Minimum agents needed to "discover" destination
  adoption_threshold: 0.05  # Minimum information needed for S2 adoption
  cascade_amplification: 1.5  # Multiplier for cascade effects
  saturation_point: 0.8  # Point where information becomes common knowledge
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        return config_file
    
    def _generate_sim_period(self, output_dir: str) -> str:
        """Generate sim_period.csv"""
        sim_period_file = os.path.join(output_dir, "sim_period.csv")
        
        with open(sim_period_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['StartDate', 'EndDate'])
            writer.writerow(['2023-01-01', '2023-03-01'])  # 60 days for cascade observation
        
        return sim_period_file
    
    def _generate_metadata(self, output_dir: str, scenario_name: str, scout_ratio: float) -> str:
        """Generate scenario metadata"""
        metadata_file = os.path.join(output_dir, "scenario_metadata.yml")
        
        metadata_content = f"""# H4.2 Information Cascade Test Scenario Metadata
scenario_name: {scenario_name}
hypothesis: H4 - Population Diversity
sub_scenario: H4.2 - Information Cascade Test
scout_ratio: {scout_ratio}

description: |
  Tests information flow and decision correlation between S1 "scouts" and S2 "followers".
  Measures how S1 discoveries influence S2 choices and the dynamics of information cascades.

destinations:
"""
        
        for dest in self.destinations:
            metadata_content += f"""  - name: {dest.name}
    visibility: {dest.visibility}
    quality: {dest.quality}
    capacity: {dest.capacity}
    discovery_difficulty: {dest.discovery_difficulty}
    information_value: {dest.information_value}
"""
        
        metadata_content += f"""
expected_cascade_patterns:
  s1_scouts:
    - Rapid exploration and destination discovery
    - High mobility and risk-taking behavior
    - Early adoption of new destinations
    - Information sharing with connected S2 agents
    
  s2_followers:
    - Delayed but informed decision-making
    - Benefit from S1 scout information
    - More optimal destination choices
    - Network-based information processing
    
  cascade_dynamics:
    - S1 discovers hidden high-quality destinations
    - Information flows from S1 to S2 through social networks
    - S2 adoption follows S1 discovery with time lag
    - Mixed populations achieve better collective outcomes

metrics:
  - discovery_rate: Speed of destination discovery by S1 scouts
  - adoption_lag: Time delay between S1 discovery and S2 adoption
  - information_correlation: Correlation between S1 and S2 destination choices
  - cascade_efficiency: Overall information cascade effectiveness
  - collective_optimality: Population-level destination choice quality

generated: {datetime.now().isoformat()}
"""
        
        with open(metadata_file, 'w') as f:
            f.write(metadata_content)
        
        return metadata_file


class InformationCascadeScenario:
    """Main interface for H4.2 Information Cascade Test scenarios"""
    
    def __init__(self):
        self.generator = InformationCascadeGenerator({})
    
    def create_scenario(self,
                       output_dir: str,
                       scout_ratio: float = 0.3,
                       information_sharing_rate: float = 0.7) -> Dict[str, str]:
        """
        Create a complete information cascade scenario
        
        Args:
            output_dir: Directory to save scenario files
            scout_ratio: Proportion of S1 scout agents
            information_sharing_rate: Rate of information sharing
            
        Returns:
            Dictionary of generated file paths
        """
        scenario_name = f"h4_2_information_cascade_scouts_{scout_ratio:.1f}"
        
        return self.generator.generate_scenario(
            scenario_name=scenario_name,
            output_dir=output_dir,
            scout_ratio=scout_ratio,
            information_sharing_rate=information_sharing_rate
        )