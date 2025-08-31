"""
Adaptive Shock Response Scenario Generator

Creates dynamic event timeline scenarios to test population resilience:
- Initial conflict at origin
- Route closure (unexpected)
- Camp capacity reached (unexpected)
- New camp opening (recovery opportunity)
"""

import os
import csv
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ShockEvent:
    """Represents a shock event in the timeline"""
    day: int
    event_type: str
    location: str
    parameters: Dict[str, Any]
    description: str


class AdaptiveShockGenerator:
    """Generates adaptive shock response scenarios with dynamic event timelines"""
    
    def __init__(self, base_config: Dict[str, Any]):
        """
        Initialize the adaptive shock generator
        
        Args:
            base_config: Base configuration parameters
        """
        self.base_config = base_config
        self.events = []
        
    def generate_scenario(self, 
                         scenario_name: str,
                         output_dir: str,
                         population_composition: str = "balanced",
                         shock_intensity: float = 0.8,
                         adaptation_window: int = 10) -> Dict[str, str]:
        """
        Generate complete adaptive shock scenario
        
        Args:
            scenario_name: Name for the scenario
            output_dir: Directory to save scenario files
            population_composition: Type of population (pure_s1, pure_s2, balanced, realistic)
            shock_intensity: Intensity of shock events (0.0-1.0)
            adaptation_window: Days available for adaptation after each shock
            
        Returns:
            Dictionary mapping file types to file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate event timeline
        self._create_event_timeline(shock_intensity, adaptation_window)
        
        # Generate network topology
        locations_file = self._generate_locations(output_dir)
        routes_file = self._generate_routes(output_dir)
        
        # Generate dynamic events
        conflicts_file = self._generate_conflicts(output_dir)
        closures_file = self._generate_closures(output_dir)
        
        # Generate population configuration
        population_file = self._generate_population_config(output_dir, population_composition)
        
        # Generate simulation period
        sim_period_file = self._generate_sim_period(output_dir)
        
        # Generate scenario metadata
        metadata_file = self._generate_metadata(output_dir, scenario_name, population_composition)
        
        return {
            'locations': locations_file,
            'routes': routes_file,
            'conflicts': conflicts_file,
            'closures': closures_file,
            'population': population_file,
            'sim_period': sim_period_file,
            'metadata': metadata_file
        }
    
    def _create_event_timeline(self, shock_intensity: float, adaptation_window: int):
        """Create the dynamic event timeline"""
        self.events = [
            ShockEvent(
                day=0,
                event_type="conflict_start",
                location="Origin",
                parameters={"intensity": 0.3, "escalation_rate": 0.02},
                description="Initial conflict begins at origin"
            ),
            ShockEvent(
                day=15,
                event_type="route_closure",
                location="Main_Route",
                parameters={"closure_probability": 1.0, "duration": adaptation_window},
                description="Main evacuation route unexpectedly blocked"
            ),
            ShockEvent(
                day=25,
                event_type="camp_full",
                location="Primary_Camp",
                parameters={"capacity_reduction": 0.0, "overflow_handling": "reject"},
                description="Primary destination reaches capacity"
            ),
            ShockEvent(
                day=30,
                event_type="new_camp_opens",
                location="Alternative_Camp",
                parameters={"capacity": 5000, "safety_level": 0.85},
                description="New alternative destination becomes available"
            ),
            ShockEvent(
                day=35,
                event_type="route_reopens",
                location="Main_Route",
                parameters={"closure_probability": 0.0},
                description="Main route reopens after repairs"
            )
        ]
    
    def _generate_locations(self, output_dir: str) -> str:
        """Generate locations.csv with adaptive shock network"""
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
                'population': 50000
            },
            {
                'name': 'Hub',
                'region': 'transit_zone',
                'country': 'TestCountry',
                'lat': 0.5,
                'lon': 0.5,
                'location_type': 'town',
                'conflict_date': '',
                'population': 10000
            },
            {
                'name': 'Primary_Camp',
                'region': 'safe_zone',
                'country': 'NeighborCountry',
                'lat': 1.0,
                'lon': 0.0,
                'location_type': 'camp',
                'conflict_date': '',
                'population': 0,
                'capacity': 8000
            },
            {
                'name': 'Alternative_Camp',
                'region': 'safe_zone',
                'country': 'NeighborCountry',
                'lat': 1.0,
                'lon': 1.0,
                'location_type': 'camp',
                'conflict_date': '',
                'population': 0,
                'capacity': 5000
            },
            {
                'name': 'Backup_Town',
                'region': 'safe_zone',
                'country': 'NeighborCountry',
                'lat': 0.0,
                'lon': 1.0,
                'location_type': 'town',
                'conflict_date': '',
                'population': 15000
            }
        ]
        
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
        """Generate routes.csv with multiple pathways"""
        routes_file = os.path.join(output_dir, "routes.csv")
        
        routes = [
            {'name1': 'Origin', 'name2': 'Hub', 'distance': 50.0, 'forced_redirection': 0},
            {'name1': 'Hub', 'name2': 'Primary_Camp', 'distance': 75.0, 'forced_redirection': 0},
            {'name1': 'Hub', 'name2': 'Alternative_Camp', 'distance': 100.0, 'forced_redirection': 0},
            {'name1': 'Origin', 'name2': 'Backup_Town', 'distance': 120.0, 'forced_redirection': 0},
            {'name1': 'Backup_Town', 'name2': 'Alternative_Camp', 'distance': 80.0, 'forced_redirection': 0}
        ]
        
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
        """Generate conflicts.csv with escalating conflict"""
        conflicts_file = os.path.join(output_dir, "conflicts.csv")
        
        conflicts = []
        
        # Initial conflict escalation
        for day in range(0, 45):
            if day <= 30:
                # Escalating conflict
                intensity = min(0.3 + (day * 0.02), 0.9)
            else:
                # Declining conflict
                intensity = max(0.9 - ((day - 30) * 0.05), 0.1)
            
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
    
    def _generate_closures(self, output_dir: str) -> str:
        """Generate closures.csv with dynamic route closures"""
        closures_file = os.path.join(output_dir, "closures.csv")
        
        closures = []
        
        # Main route closure event
        for day in range(15, 36):  # Closed from day 15-35
            closures.append({
                'day': day,
                'name1': 'Hub',
                'name2': 'Primary_Camp',
                'closure_type': 1  # Complete closure
            })
        
        with open(closures_file, 'w', newline='') as f:
            if closures:
                # Get all possible fieldnames from all closures
                all_fieldnames = set()
                for closure in closures:
                    all_fieldnames.update(closure.keys())
                
                writer = csv.DictWriter(f, fieldnames=sorted(all_fieldnames))
                writer.writeheader()
                writer.writerows(closures)
            else:
                # Create empty file with headers
                writer = csv.DictWriter(f, fieldnames=['day', 'name1', 'name2', 'closure_type'])
                writer.writeheader()
        
        return closures_file
    
    def _generate_population_config(self, output_dir: str, composition: str) -> str:
        """Generate population configuration file"""
        config_file = os.path.join(output_dir, "population_config.yml")
        
        compositions = {
            'pure_s1': {
                'system1_ratio': 1.0,
                'system2_ratio': 0.0,
                'social_connectivity': 0.0,
                'description': '100% System 1 agents (fast, reactive)'
            },
            'pure_s2': {
                'system1_ratio': 0.0,
                'system2_ratio': 1.0,
                'social_connectivity': 8.0,
                'description': '100% System 2 agents (slow, deliberative)'
            },
            'balanced': {
                'system1_ratio': 0.5,
                'system2_ratio': 0.5,
                'social_connectivity': 4.0,
                'description': '50% S1, 50% S2 agents'
            },
            'realistic': {
                'system1_ratio': 0.7,
                'system2_ratio': 0.3,
                'social_connectivity': 3.0,
                'description': '70% S1, 30% S2 agents (research-based)'
            }
        }
        
        config = compositions.get(composition, compositions['balanced'])
        
        config_content = f"""# Population Configuration for H4.1 Adaptive Shock Response
# Composition: {composition}
# Description: {config['description']}

population:
  total_agents: 10000
  system1_ratio: {config['system1_ratio']}
  system2_ratio: {config['system2_ratio']}
  
cognitive_parameters:
  system1:
    decision_speed: 0.9
    heuristic_weight: 0.8
    social_influence: 0.2
  
  system2:
    decision_speed: 0.3
    deliberation_depth: 0.8
    social_connectivity: {config['social_connectivity']}
    
adaptation_parameters:
  shock_sensitivity: 0.7
  learning_rate: 0.1
  memory_decay: 0.05
  information_sharing_rate: 0.6
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
            writer.writerow(['2023-01-01', '2023-02-15'])  # 45 days
        
        return sim_period_file
    
    def _generate_metadata(self, output_dir: str, scenario_name: str, composition: str) -> str:
        """Generate scenario metadata"""
        metadata_file = os.path.join(output_dir, "scenario_metadata.yml")
        
        metadata_content = f"""# H4.1 Adaptive Shock Response Scenario Metadata
scenario_name: {scenario_name}
hypothesis: H4 - Population Diversity
sub_scenario: H4.1 - Adaptive Shock Response
population_composition: {composition}

description: |
  Tests population resilience to unexpected changes through dynamic event timeline.
  Measures how different population compositions adapt to:
  - Route closures
  - Camp capacity limits
  - New destination availability

events:
"""
        
        for event in self.events:
            metadata_content += f"""  - day: {event.day}
    type: {event.event_type}
    location: {event.location}
    description: {event.description}
"""
        
        metadata_content += f"""
expected_outcomes:
  pure_s1: Fast initial response, poor adaptation to shocks
  pure_s2: Slow initial response, better adaptation once processed
  mixed: Complementary strengths, best overall adaptation

metrics:
  - adaptation_speed: Time to respond to unexpected changes
  - recovery_rate: Speed of population recovery after shocks
  - collective_efficiency: Overall population movement efficiency
  - resilience_index: Combined measure of adaptation and recovery

generated: {datetime.now().isoformat()}
"""
        
        with open(metadata_file, 'w') as f:
            f.write(metadata_content)
        
        return metadata_file


class AdaptiveShockScenario:
    """Main interface for H4.1 Adaptive Shock Response scenarios"""
    
    def __init__(self):
        self.generator = AdaptiveShockGenerator({})
    
    def create_scenario(self, 
                       output_dir: str,
                       population_composition: str = "balanced",
                       shock_intensity: float = 0.8) -> Dict[str, str]:
        """
        Create a complete adaptive shock scenario
        
        Args:
            output_dir: Directory to save scenario files
            population_composition: Type of population composition
            shock_intensity: Intensity of shock events
            
        Returns:
            Dictionary of generated file paths
        """
        scenario_name = f"h4_1_adaptive_shock_{population_composition}"
        
        return self.generator.generate_scenario(
            scenario_name=scenario_name,
            output_dir=output_dir,
            population_composition=population_composition,
            shock_intensity=shock_intensity
        )