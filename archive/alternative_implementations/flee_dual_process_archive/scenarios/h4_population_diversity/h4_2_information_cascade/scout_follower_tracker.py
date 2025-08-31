"""
Scout-Follower Behavior Tracker for H4.2 Information Cascade Test

Tracks S1 "scout" and S2 "follower" behavior interactions and information flow.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class ScoutBehavior:
    """Tracks behavior of S1 scout agents"""
    agent_id: int
    discovery_events: List[Tuple[int, str]]  # (day, destination)
    exploration_pattern: List[Tuple[int, str]]  # (day, location)
    information_shared: List[Tuple[int, str, List[int]]]  # (day, info, recipients)
    risk_taking_events: List[Tuple[int, str, float]]  # (day, decision, risk_level)


@dataclass
class FollowerBehavior:
    """Tracks behavior of S2 follower agents"""
    agent_id: int
    information_received: List[Tuple[int, str, int]]  # (day, info, source_agent)
    adoption_events: List[Tuple[int, str, int]]  # (day, destination, delay_from_discovery)
    deliberation_periods: List[Tuple[int, int, str]]  # (start_day, duration, decision)
    network_connections: List[int]  # Connected agent IDs


@dataclass
class CascadeEvent:
    """Represents an information cascade event"""
    discovery_day: int
    destination: str
    scout_discoverer: int
    adoption_timeline: List[Tuple[int, int]]  # (day, adopter_agent_id)
    cascade_speed: float
    final_adoption_rate: float


class ScoutFollowerTracker:
    """Tracks scout-follower dynamics in information cascade scenarios"""
    
    def __init__(self, scenario_config: Dict[str, Any]):
        """
        Initialize scout-follower tracker
        
        Args:
            scenario_config: Configuration for the scenario
        """
        self.config = scenario_config
        self.scouts: Dict[int, ScoutBehavior] = {}
        self.followers: Dict[int, FollowerBehavior] = {}
        self.cascade_events: List[CascadeEvent] = []
        self.information_network: Dict[int, Set[int]] = defaultdict(set)
        
    def initialize_agents(self, agent_data: pd.DataFrame):
        """
        Initialize agent tracking from agent configuration data
        
        Args:
            agent_data: DataFrame with agent information
        """
        for _, agent in agent_data.iterrows():
            agent_id = agent['agent_id']
            cognitive_type = agent.get('cognitive_type', 'S1')
            
            if cognitive_type == 'S1' or agent.get('is_scout', False):
                self.scouts[agent_id] = ScoutBehavior(
                    agent_id=agent_id,
                    discovery_events=[],
                    exploration_pattern=[],
                    information_shared=[],
                    risk_taking_events=[]
                )
            else:
                self.followers[agent_id] = FollowerBehavior(
                    agent_id=agent_id,
                    information_received=[],
                    adoption_events=[],
                    deliberation_periods=[],
                    network_connections=[]
                )
    
    def track_discovery_event(self, day: int, agent_id: int, destination: str, 
                            discovery_method: str = "exploration"):
        """
        Track a destination discovery by a scout agent
        
        Args:
            day: Day of discovery
            agent_id: ID of discovering agent
            destination: Name of discovered destination
            discovery_method: How the destination was discovered
        """
        if agent_id in self.scouts:
            self.scouts[agent_id].discovery_events.append((day, destination))
            
            # Check if this starts a cascade
            self._check_cascade_initiation(day, agent_id, destination)
    
    def track_information_sharing(self, day: int, sender_id: int, 
                                information: str, recipients: List[int]):
        """
        Track information sharing from scout to followers
        
        Args:
            day: Day of information sharing
            sender_id: ID of agent sharing information
            information: Information being shared
            recipients: List of recipient agent IDs
        """
        if sender_id in self.scouts:
            self.scouts[sender_id].information_shared.append((day, information, recipients))
        
        # Track receipt by followers
        for recipient_id in recipients:
            if recipient_id in self.followers:
                self.followers[recipient_id].information_received.append(
                    (day, information, sender_id)
                )
                
                # Update network connections
                self.information_network[sender_id].add(recipient_id)
                self.information_network[recipient_id].add(sender_id)
    
    def track_adoption_event(self, day: int, agent_id: int, destination: str):
        """
        Track adoption of a destination by a follower agent
        
        Args:
            day: Day of adoption
            agent_id: ID of adopting agent
            destination: Name of adopted destination
        """
        if agent_id in self.followers:
            # Calculate delay from discovery
            discovery_day = self._find_discovery_day(destination)
            delay = day - discovery_day if discovery_day is not None else 0
            
            self.followers[agent_id].adoption_events.append((day, destination, delay))
            
            # Update cascade tracking
            self._update_cascade_adoption(day, agent_id, destination)
    
    def track_exploration_pattern(self, day: int, agent_id: int, location: str):
        """
        Track exploration patterns of scout agents
        
        Args:
            day: Day of exploration
            agent_id: ID of exploring agent
            location: Location being explored
        """
        if agent_id in self.scouts:
            self.scouts[agent_id].exploration_pattern.append((day, location))
    
    def track_deliberation_period(self, agent_id: int, start_day: int, 
                                duration: int, decision: str):
        """
        Track deliberation periods of follower agents
        
        Args:
            agent_id: ID of deliberating agent
            start_day: Start day of deliberation
            duration: Duration of deliberation in days
            decision: Final decision made
        """
        if agent_id in self.followers:
            self.followers[agent_id].deliberation_periods.append(
                (start_day, duration, decision)
            )
    
    def _check_cascade_initiation(self, day: int, scout_id: int, destination: str):
        """Check if a discovery initiates an information cascade"""
        # Create new cascade event
        cascade = CascadeEvent(
            discovery_day=day,
            destination=destination,
            scout_discoverer=scout_id,
            adoption_timeline=[],
            cascade_speed=0.0,
            final_adoption_rate=0.0
        )
        
        self.cascade_events.append(cascade)
    
    def _update_cascade_adoption(self, day: int, agent_id: int, destination: str):
        """Update cascade event with new adoption"""
        for cascade in self.cascade_events:
            if cascade.destination == destination:
                cascade.adoption_timeline.append((day, agent_id))
                break
    
    def _find_discovery_day(self, destination: str) -> Optional[int]:
        """Find the day a destination was first discovered"""
        earliest_day = None
        
        for scout in self.scouts.values():
            for day, dest in scout.discovery_events:
                if dest == destination:
                    if earliest_day is None or day < earliest_day:
                        earliest_day = day
        
        return earliest_day
    
    def analyze_scout_behavior(self) -> Dict[str, Any]:
        """Analyze overall scout behavior patterns"""
        if not self.scouts:
            return {}
        
        analysis = {
            'total_scouts': len(self.scouts),
            'total_discoveries': 0,
            'avg_discoveries_per_scout': 0.0,
            'discovery_timeline': {},
            'exploration_diversity': 0.0,
            'information_sharing_rate': 0.0
        }
        
        all_discoveries = []
        all_locations = set()
        total_sharing_events = 0
        
        for scout in self.scouts.values():
            all_discoveries.extend(scout.discovery_events)
            all_locations.update([loc for _, loc in scout.exploration_pattern])
            total_sharing_events += len(scout.information_shared)
        
        analysis['total_discoveries'] = len(all_discoveries)
        analysis['avg_discoveries_per_scout'] = len(all_discoveries) / len(self.scouts)
        analysis['exploration_diversity'] = len(all_locations)
        analysis['information_sharing_rate'] = total_sharing_events / len(self.scouts)
        
        # Discovery timeline
        for day, dest in all_discoveries:
            if day not in analysis['discovery_timeline']:
                analysis['discovery_timeline'][day] = []
            analysis['discovery_timeline'][day].append(dest)
        
        return analysis
    
    def analyze_follower_behavior(self) -> Dict[str, Any]:
        """Analyze overall follower behavior patterns"""
        if not self.followers:
            return {}
        
        analysis = {
            'total_followers': len(self.followers),
            'total_adoptions': 0,
            'avg_adoptions_per_follower': 0.0,
            'avg_adoption_delay': 0.0,
            'information_receptivity': 0.0,
            'deliberation_patterns': {}
        }
        
        all_adoptions = []
        all_delays = []
        total_info_received = 0
        deliberation_durations = []
        
        for follower in self.followers.values():
            all_adoptions.extend(follower.adoption_events)
            all_delays.extend([delay for _, _, delay in follower.adoption_events])
            total_info_received += len(follower.information_received)
            deliberation_durations.extend([dur for _, dur, _ in follower.deliberation_periods])
        
        analysis['total_adoptions'] = len(all_adoptions)
        analysis['avg_adoptions_per_follower'] = len(all_adoptions) / len(self.followers)
        analysis['avg_adoption_delay'] = np.mean(all_delays) if all_delays else 0.0
        analysis['information_receptivity'] = total_info_received / len(self.followers)
        
        if deliberation_durations:
            analysis['deliberation_patterns'] = {
                'avg_duration': np.mean(deliberation_durations),
                'median_duration': np.median(deliberation_durations),
                'max_duration': max(deliberation_durations)
            }
        
        return analysis
    
    def analyze_cascade_dynamics(self) -> Dict[str, Any]:
        """Analyze information cascade dynamics"""
        if not self.cascade_events:
            return {}
        
        analysis = {
            'total_cascades': len(self.cascade_events),
            'cascade_details': [],
            'avg_cascade_speed': 0.0,
            'avg_adoption_rate': 0.0,
            'most_successful_cascade': None,
            'cascade_efficiency': 0.0
        }
        
        cascade_speeds = []
        adoption_rates = []
        
        for cascade in self.cascade_events:
            # Calculate cascade speed (adoptions per day)
            if cascade.adoption_timeline:
                timeline_days = [day for day, _ in cascade.adoption_timeline]
                cascade_duration = max(timeline_days) - min(timeline_days) + 1
                cascade_speed = len(cascade.adoption_timeline) / cascade_duration
                cascade.cascade_speed = cascade_speed
                cascade_speeds.append(cascade_speed)
                
                # Calculate adoption rate (proportion of followers who adopted)
                adoption_rate = len(cascade.adoption_timeline) / len(self.followers) if self.followers else 0
                cascade.final_adoption_rate = adoption_rate
                adoption_rates.append(adoption_rate)
                
                cascade_detail = {
                    'destination': cascade.destination,
                    'discovery_day': cascade.discovery_day,
                    'scout_discoverer': cascade.scout_discoverer,
                    'total_adoptions': len(cascade.adoption_timeline),
                    'cascade_speed': cascade_speed,
                    'adoption_rate': adoption_rate,
                    'timeline': cascade.adoption_timeline
                }
                
                analysis['cascade_details'].append(cascade_detail)
        
        if cascade_speeds:
            analysis['avg_cascade_speed'] = np.mean(cascade_speeds)
            analysis['avg_adoption_rate'] = np.mean(adoption_rates)
            
            # Find most successful cascade
            best_cascade = max(self.cascade_events, key=lambda c: c.final_adoption_rate)
            analysis['most_successful_cascade'] = {
                'destination': best_cascade.destination,
                'adoption_rate': best_cascade.final_adoption_rate,
                'cascade_speed': best_cascade.cascade_speed
            }
            
            # Calculate overall cascade efficiency
            analysis['cascade_efficiency'] = np.mean(adoption_rates) * np.mean(cascade_speeds)
        
        return analysis
    
    def analyze_information_network(self) -> Dict[str, Any]:
        """Analyze the information sharing network"""
        if not self.information_network:
            return {}
        
        # Calculate network metrics
        total_connections = sum(len(connections) for connections in self.information_network.values())
        unique_agents = len(self.information_network)
        
        # Calculate connectivity metrics
        scout_connections = {}
        follower_connections = {}
        
        for agent_id, connections in self.information_network.items():
            if agent_id in self.scouts:
                scout_connections[agent_id] = len(connections)
            elif agent_id in self.followers:
                follower_connections[agent_id] = len(connections)
        
        analysis = {
            'total_connections': total_connections,
            'unique_connected_agents': unique_agents,
            'avg_connections_per_agent': total_connections / unique_agents if unique_agents > 0 else 0,
            'scout_connectivity': {
                'avg_connections': np.mean(list(scout_connections.values())) if scout_connections else 0,
                'max_connections': max(scout_connections.values()) if scout_connections else 0,
                'total_scouts_connected': len(scout_connections)
            },
            'follower_connectivity': {
                'avg_connections': np.mean(list(follower_connections.values())) if follower_connections else 0,
                'max_connections': max(follower_connections.values()) if follower_connections else 0,
                'total_followers_connected': len(follower_connections)
            }
        }
        
        return analysis
    
    def generate_tracking_report(self) -> Dict[str, Any]:
        """Generate comprehensive tracking report"""
        report = {
            'scenario_summary': {
                'total_scouts': len(self.scouts),
                'total_followers': len(self.followers),
                'tracking_period': self._get_tracking_period()
            },
            'scout_analysis': self.analyze_scout_behavior(),
            'follower_analysis': self.analyze_follower_behavior(),
            'cascade_analysis': self.analyze_cascade_dynamics(),
            'network_analysis': self.analyze_information_network(),
            'key_insights': self._generate_insights()
        }
        
        return report
    
    def _get_tracking_period(self) -> Tuple[int, int]:
        """Get the tracking period (start day, end day)"""
        all_days = []
        
        for scout in self.scouts.values():
            all_days.extend([day for day, _ in scout.discovery_events])
            all_days.extend([day for day, _ in scout.exploration_pattern])
        
        for follower in self.followers.values():
            all_days.extend([day for day, _, _ in follower.information_received])
            all_days.extend([day for day, _, _ in follower.adoption_events])
        
        return (min(all_days), max(all_days)) if all_days else (0, 0)
    
    def _generate_insights(self) -> List[str]:
        """Generate key insights from the tracking data"""
        insights = []
        
        scout_analysis = self.analyze_scout_behavior()
        follower_analysis = self.analyze_follower_behavior()
        cascade_analysis = self.analyze_cascade_dynamics()
        
        # Scout insights
        if scout_analysis.get('avg_discoveries_per_scout', 0) > 1:
            insights.append(f"Scouts are highly active with {scout_analysis['avg_discoveries_per_scout']:.1f} discoveries per scout on average")
        
        # Follower insights
        if follower_analysis.get('avg_adoption_delay', 0) > 0:
            insights.append(f"Followers adopt scout discoveries with an average delay of {follower_analysis['avg_adoption_delay']:.1f} days")
        
        # Cascade insights
        if cascade_analysis.get('avg_adoption_rate', 0) > 0.5:
            insights.append(f"Strong information cascades with {cascade_analysis['avg_adoption_rate']:.1%} average adoption rate")
        elif cascade_analysis.get('avg_adoption_rate', 0) > 0.2:
            insights.append(f"Moderate information cascades with {cascade_analysis['avg_adoption_rate']:.1%} average adoption rate")
        else:
            insights.append("Weak information cascade effects observed")
        
        # Network insights
        network_analysis = self.analyze_information_network()
        if network_analysis.get('avg_connections_per_agent', 0) > 3:
            insights.append("High connectivity in information sharing network")
        
        return insights
    
    def export_tracking_data(self, output_dir: str):
        """Export tracking data to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export scout data
        scout_data = []
        for scout in self.scouts.values():
            for day, dest in scout.discovery_events:
                scout_data.append({
                    'agent_id': scout.agent_id,
                    'day': day,
                    'event_type': 'discovery',
                    'destination': dest
                })
        
        if scout_data:
            scout_df = pd.DataFrame(scout_data)
            scout_df.to_csv(os.path.join(output_dir, 'scout_discoveries.csv'), index=False)
        
        # Export follower data
        follower_data = []
        for follower in self.followers.values():
            for day, dest, delay in follower.adoption_events:
                follower_data.append({
                    'agent_id': follower.agent_id,
                    'day': day,
                    'event_type': 'adoption',
                    'destination': dest,
                    'delay_from_discovery': delay
                })
        
        if follower_data:
            follower_df = pd.DataFrame(follower_data)
            follower_df.to_csv(os.path.join(output_dir, 'follower_adoptions.csv'), index=False)
        
        # Export cascade data
        cascade_data = []
        for cascade in self.cascade_events:
            cascade_data.append({
                'destination': cascade.destination,
                'discovery_day': cascade.discovery_day,
                'scout_discoverer': cascade.scout_discoverer,
                'total_adoptions': len(cascade.adoption_timeline),
                'cascade_speed': cascade.cascade_speed,
                'final_adoption_rate': cascade.final_adoption_rate
            })
        
        if cascade_data:
            cascade_df = pd.DataFrame(cascade_data)
            cascade_df.to_csv(os.path.join(output_dir, 'cascade_summary.csv'), index=False)
        
        # Export full report
        report = self.generate_tracking_report()
        with open(os.path.join(output_dir, 'tracking_report.json'), 'w') as f:
            json.dump(report, f, indent=2)