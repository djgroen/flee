"""
Event Timeline for H4.1 Adaptive Shock Response

Manages dynamic event sequences that test population adaptation capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import csv
import os
import json


@dataclass
class TimelineEvent:
    """Represents a single event in the adaptive shock timeline"""
    day: int
    event_type: str
    location: str
    parameters: Dict[str, Any]
    description: str
    impact_radius: float = 0.0
    duration: int = 1
    severity: float = 1.0
    adaptation_window: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'day': self.day,
            'event_type': self.event_type,
            'location': self.location,
            'parameters': self.parameters,
            'description': self.description,
            'impact_radius': self.impact_radius,
            'duration': self.duration,
            'severity': self.severity,
            'adaptation_window': self.adaptation_window
        }


@dataclass
class EventSequence:
    """Represents a sequence of related events"""
    name: str
    description: str
    events: List[TimelineEvent] = field(default_factory=list)
    expected_responses: Dict[str, str] = field(default_factory=dict)
    
    def add_event(self, event: TimelineEvent):
        """Add event to sequence"""
        self.events.append(event)
        self.events.sort(key=lambda x: x.day)
    
    def get_events_by_day(self, day: int) -> List[TimelineEvent]:
        """Get all events occurring on a specific day"""
        return [event for event in self.events if event.day == day]
    
    def get_events_in_range(self, start_day: int, end_day: int) -> List[TimelineEvent]:
        """Get all events in a day range"""
        return [event for event in self.events if start_day <= event.day <= end_day]


class EventTimeline:
    """Manages the complete event timeline for adaptive shock scenarios"""
    
    def __init__(self, scenario_name: str = "adaptive_shock"):
        """
        Initialize event timeline
        
        Args:
            scenario_name: Name of the scenario
        """
        self.scenario_name = scenario_name
        self.sequences: Dict[str, EventSequence] = {}
        self.total_duration = 45  # Default scenario length
        self._initialize_default_timeline()
    
    def _initialize_default_timeline(self):
        """Initialize the default adaptive shock timeline"""
        
        # Initial Conflict Sequence
        initial_conflict = EventSequence(
            name="initial_conflict",
            description="Initial conflict escalation at origin",
            expected_responses={
                "pure_s1": "Immediate evacuation, panic responses",
                "pure_s2": "Delayed but planned evacuation",
                "balanced": "Mixed immediate and planned responses",
                "realistic": "Majority immediate with strategic minority"
            }
        )
        
        initial_conflict.add_event(TimelineEvent(
            day=0,
            event_type="conflict_start",
            location="Origin",
            parameters={"intensity": 0.3, "escalation_rate": 0.02},
            description="Initial conflict begins at origin location",
            impact_radius=10.0,
            duration=45,
            severity=0.3,
            adaptation_window=3
        ))
        
        # Route Disruption Sequence
        route_disruption = EventSequence(
            name="route_disruption",
            description="Unexpected route closure disrupts main evacuation path",
            expected_responses={
                "pure_s1": "Confusion, clustering at blocked route",
                "pure_s2": "Systematic search for alternatives",
                "balanced": "S1 scouts find alternatives, S2 optimizes",
                "realistic": "Quick adaptation through S1-S2 cooperation"
            }
        )
        
        route_disruption.add_event(TimelineEvent(
            day=15,
            event_type="route_closure",
            location="Main_Route",
            parameters={"closure_probability": 1.0, "alternative_cost_multiplier": 1.5},
            description="Main evacuation route unexpectedly blocked",
            impact_radius=50.0,
            duration=20,
            severity=0.8,
            adaptation_window=5
        ))
        
        # Capacity Crisis Sequence
        capacity_crisis = EventSequence(
            name="capacity_crisis",
            description="Primary destination reaches capacity, forcing redirection",
            expected_responses={
                "pure_s1": "Overcrowding, poor alternative choices",
                "pure_s2": "Systematic capacity monitoring and planning",
                "balanced": "Efficient redirection to alternatives",
                "realistic": "Mixed responses with learning"
            }
        )
        
        capacity_crisis.add_event(TimelineEvent(
            day=25,
            event_type="camp_full",
            location="Primary_Camp",
            parameters={"capacity_reduction": 0.0, "overflow_handling": "reject"},
            description="Primary destination reaches full capacity",
            impact_radius=0.0,
            duration=20,
            severity=0.6,
            adaptation_window=3
        ))
        
        # Recovery Opportunity Sequence
        recovery_opportunity = EventSequence(
            name="recovery_opportunity",
            description="New destination opens, providing recovery opportunity",
            expected_responses={
                "pure_s1": "Rapid movement to new option",
                "pure_s2": "Careful evaluation before movement",
                "balanced": "Optimal utilization of new opportunity",
                "realistic": "Gradual adoption with information sharing"
            }
        )
        
        recovery_opportunity.add_event(TimelineEvent(
            day=30,
            event_type="new_camp_opens",
            location="Alternative_Camp",
            parameters={"capacity": 5000, "safety_level": 0.85, "accessibility": 0.9},
            description="New alternative destination becomes available",
            impact_radius=0.0,
            duration=15,
            severity=-0.4,  # Negative severity = positive event
            adaptation_window=7
        ))
        
        # Route Recovery Sequence
        route_recovery = EventSequence(
            name="route_recovery",
            description="Original route reopens after repairs",
            expected_responses={
                "pure_s1": "Immediate return to familiar route",
                "pure_s2": "Evaluation of route vs current alternatives",
                "balanced": "Strategic use of multiple routes",
                "realistic": "Gradual route diversification"
            }
        )
        
        route_recovery.add_event(TimelineEvent(
            day=35,
            event_type="route_reopens",
            location="Main_Route",
            parameters={"closure_probability": 0.0, "capacity_multiplier": 1.2},
            description="Main route reopens with improved capacity",
            impact_radius=50.0,
            duration=10,
            severity=-0.3,  # Positive event
            adaptation_window=3
        ))
        
        # Add all sequences to timeline
        self.sequences = {
            "initial_conflict": initial_conflict,
            "route_disruption": route_disruption,
            "capacity_crisis": capacity_crisis,
            "recovery_opportunity": recovery_opportunity,
            "route_recovery": route_recovery
        }
    
    def get_all_events(self) -> List[TimelineEvent]:
        """Get all events from all sequences, sorted by day"""
        all_events = []
        for sequence in self.sequences.values():
            all_events.extend(sequence.events)
        
        return sorted(all_events, key=lambda x: x.day)
    
    def get_events_by_day(self, day: int) -> List[TimelineEvent]:
        """Get all events occurring on a specific day"""
        events = []
        for sequence in self.sequences.values():
            events.extend(sequence.get_events_by_day(day))
        
        return sorted(events, key=lambda x: x.event_type)
    
    def get_shock_events(self) -> List[TimelineEvent]:
        """Get only the shock events (positive severity)"""
        all_events = self.get_all_events()
        return [event for event in all_events if event.severity > 0]
    
    def get_recovery_events(self) -> List[TimelineEvent]:
        """Get only the recovery events (negative severity)"""
        all_events = self.get_all_events()
        return [event for event in all_events if event.severity < 0]
    
    def generate_conflicts_csv(self, output_file: str):
        """Generate conflicts.csv file from timeline events"""
        conflicts = []
        
        # Generate daily conflict intensities
        for day in range(self.total_duration):
            base_intensity = 0.0
            
            # Check for conflict events on this day
            day_events = self.get_events_by_day(day)
            
            for event in day_events:
                if event.event_type == "conflict_start":
                    # Escalating conflict
                    days_since_start = day - event.day
                    intensity = event.parameters.get("intensity", 0.3)
                    escalation_rate = event.parameters.get("escalation_rate", 0.02)
                    base_intensity = min(intensity + (days_since_start * escalation_rate), 0.9)
                elif event.event_type in ["route_closure", "camp_full"]:
                    # Additional stress from disruptions
                    base_intensity += event.severity * 0.3
            
            # Gradual conflict decline after day 30
            if day > 30:
                decline_rate = 0.05
                base_intensity = max(base_intensity - ((day - 30) * decline_rate), 0.1)
            
            conflicts.append({
                'day': day,
                'location': 'Origin',
                'intensity': max(0.0, min(1.0, base_intensity))
            })
        
        # Write conflicts CSV
        with open(output_file, 'w', newline='') as f:
            if conflicts:
                writer = csv.DictWriter(f, fieldnames=conflicts[0].keys())
                writer.writeheader()
                writer.writerows(conflicts)
    
    def generate_closures_csv(self, output_file: str):
        """Generate closures.csv file from timeline events"""
        closures = []
        
        for event in self.get_all_events():
            if event.event_type == "route_closure":
                # Generate closure entries for the duration
                for day_offset in range(event.duration):
                    closures.append({
                        'day': event.day + day_offset,
                        'name1': 'Hub',
                        'name2': 'Primary_Camp',
                        'closure_type': 1  # Complete closure
                    })
            elif event.event_type == "route_reopens":
                # Ensure route is open (no closure entries needed)
                pass
        
        # Write closures CSV
        if closures:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=closures[0].keys())
                writer.writeheader()
                writer.writerows(closures)
        else:
            # Create empty file with headers
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['day', 'name1', 'name2', 'closure_type'])
                writer.writeheader()
    
    def generate_timeline_metadata(self, output_file: str):
        """Generate detailed timeline metadata"""
        metadata = {
            'scenario_name': self.scenario_name,
            'total_duration': self.total_duration,
            'sequences': {},
            'shock_analysis': {
                'total_shocks': len(self.get_shock_events()),
                'total_recovery_events': len(self.get_recovery_events()),
                'shock_intensity_profile': self._calculate_shock_profile(),
                'adaptation_windows': self._calculate_adaptation_windows()
            },
            'expected_population_responses': self._compile_expected_responses(),
            'generated_timestamp': datetime.now().isoformat()
        }
        
        # Add sequence details
        for name, sequence in self.sequences.items():
            metadata['sequences'][name] = {
                'description': sequence.description,
                'event_count': len(sequence.events),
                'events': [event.to_dict() for event in sequence.events],
                'expected_responses': sequence.expected_responses
            }
        
        # Write metadata JSON
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _calculate_shock_profile(self) -> Dict[str, float]:
        """Calculate overall shock intensity profile"""
        shock_events = self.get_shock_events()
        
        if not shock_events:
            return {'max_intensity': 0.0, 'avg_intensity': 0.0, 'shock_frequency': 0.0}
        
        intensities = [event.severity for event in shock_events]
        
        return {
            'max_intensity': max(intensities),
            'avg_intensity': sum(intensities) / len(intensities),
            'shock_frequency': len(shock_events) / self.total_duration
        }
    
    def _calculate_adaptation_windows(self) -> Dict[str, int]:
        """Calculate adaptation windows for each shock type"""
        windows = {}
        
        for event in self.get_shock_events():
            windows[f"{event.event_type}_day_{event.day}"] = event.adaptation_window
        
        return windows
    
    def _compile_expected_responses(self) -> Dict[str, List[str]]:
        """Compile expected responses across all sequences"""
        responses = {
            'pure_s1': [],
            'pure_s2': [],
            'balanced': [],
            'realistic': []
        }
        
        for sequence in self.sequences.values():
            for pop_type, response in sequence.expected_responses.items():
                responses[pop_type].append(f"{sequence.name}: {response}")
        
        return responses
    
    def customize_timeline(self, 
                          shock_intensity: float = 0.8,
                          adaptation_window: int = 5,
                          total_duration: int = 45) -> 'EventTimeline':
        """
        Create customized version of timeline
        
        Args:
            shock_intensity: Overall intensity multiplier for shocks
            adaptation_window: Default adaptation window for events
            total_duration: Total scenario duration in days
            
        Returns:
            New EventTimeline with customized parameters
        """
        custom_timeline = EventTimeline(f"{self.scenario_name}_custom")
        custom_timeline.total_duration = total_duration
        
        # Copy and modify sequences
        for name, sequence in self.sequences.items():
            custom_sequence = EventSequence(
                name=sequence.name,
                description=sequence.description,
                expected_responses=sequence.expected_responses.copy()
            )
            
            for event in sequence.events:
                custom_event = TimelineEvent(
                    day=event.day,
                    event_type=event.event_type,
                    location=event.location,
                    parameters=event.parameters.copy(),
                    description=event.description,
                    impact_radius=event.impact_radius,
                    duration=event.duration,
                    severity=event.severity * shock_intensity,
                    adaptation_window=adaptation_window
                )
                custom_sequence.add_event(custom_event)
            
            custom_timeline.sequences[name] = custom_sequence
        
        return custom_timeline


def create_adaptive_shock_timeline(scenario_name: str = "h4_1_adaptive_shock",
                                 shock_intensity: float = 0.8,
                                 adaptation_window: int = 5) -> EventTimeline:
    """
    Create adaptive shock timeline for H4.1 scenario
    
    Args:
        scenario_name: Name for the scenario
        shock_intensity: Intensity multiplier for shock events
        adaptation_window: Default adaptation window
        
    Returns:
        Configured EventTimeline
    """
    timeline = EventTimeline(scenario_name)
    
    if shock_intensity != 0.8 or adaptation_window != 5:
        timeline = timeline.customize_timeline(
            shock_intensity=shock_intensity,
            adaptation_window=adaptation_window
        )
    
    return timeline