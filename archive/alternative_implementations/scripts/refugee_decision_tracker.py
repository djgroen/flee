#!/usr/bin/env python3
"""
Refugee Decision Tracker

Integrates with existing Flee S1/S2 system to track refugee-specific decisions.
Hooks into existing calculateMoveChance() and Person.log_decision() methods.
"""

import sys
import csv
import statistics
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

# Add Flee to path
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

@dataclass
class RefugeeDecisionRecord:
    """Record of a refugee decision using existing Flee data structures"""
    time: int
    agent_ref: Any  # Reference to agent object (since Flee agents don't have IDs)
    system2_active: bool
    cognitive_pressure: float
    connections: int
    conflict_level: float
    movechance: float
    evacuation_timing: Optional[int]  # Days from conflict start
    destination_chosen: Optional[str]
    route_length: int
    decision_factors: Dict[str, Any]

class RefugeeDecisionTracker:
    """
    Tracks refugee decisions by hooking into existing Flee S1/S2 system.
    
    Integrates with:
    - existing calculateMoveChance() function
    - existing Person.log_decision() method
    - existing Person.calculate_cognitive_pressure()
    - existing system2_active logic
    """
    
    def __init__(self):
        self.decision_records: List[RefugeeDecisionRecord] = []
        self.conflict_start_times: Dict[str, int] = {}  # location_name -> start_time
        self.evacuation_events: Dict[Any, int] = {}  # agent_ref -> evacuation_time
        
    def track_refugee_decision(self, agent, system2_active: bool, movechance: float, 
                             time: int, route: List = None) -> None:
        """
        Track a refugee decision using existing Flee agent data.
        
        Args:
            agent: Flee Person object with existing attributes
            system2_active: Return value from existing calculateMoveChance()
            movechance: Return value from existing calculateMoveChance()
            time: Current simulation time
            route: Selected route (if any)
        """
        
        # Use existing cognitive pressure calculation
        cognitive_pressure = agent.calculate_cognitive_pressure(time)
        
        # Track conflict start time for evacuation timing
        location_name = agent.location.name if hasattr(agent.location, 'name') else 'Unknown'
        if location_name not in self.conflict_start_times and agent.location.conflict > 0.1:
            self.conflict_start_times[location_name] = time
            
        # Calculate evacuation timing using existing agent data
        evacuation_timing = None
        if movechance > 0.5 and agent not in self.evacuation_events:
            if location_name in self.conflict_start_times:
                evacuation_timing = time - self.conflict_start_times[location_name]
                self.evacuation_events[agent] = time
        
        # Extract destination and route info
        destination_chosen = None
        route_length = 0
        if route and len(route) > 0:
            destination_chosen = route[-1] if isinstance(route[-1], str) else str(route[-1])
            route_length = len(route)
        
        # Create decision record using existing agent attributes
        decision_record = RefugeeDecisionRecord(
            time=time,
            agent_ref=agent,  # Use agent object reference instead of ID
            system2_active=system2_active,
            cognitive_pressure=cognitive_pressure,
            connections=agent.attributes.get('connections', 0),
            conflict_level=agent.location.conflict,
            movechance=movechance,
            evacuation_timing=evacuation_timing,
            destination_chosen=destination_chosen,
            route_length=route_length,
            decision_factors={
                'location': location_name,
                'timesteps_since_departure': agent.timesteps_since_departure,
                'days_in_current_location': getattr(agent, 'days_in_current_location', 0),
                'system2_activations': getattr(agent, 'system2_activations', 0)
            }
        )
        
        self.decision_records.append(decision_record)
        
        # Use existing log_decision method if available
        if hasattr(agent, 'log_decision'):
            agent.log_decision(
                decision_type='refugee_movement',
                factors={
                    'system2_active': system2_active,
                    'cognitive_pressure': cognitive_pressure,
                    'movechance': movechance,
                    'evacuation_timing': evacuation_timing
                },
                time=time
            )
    
    def analyze_evacuation_timing(self) -> Dict[str, Any]:
        """Analyze S1 vs S2 evacuation timing differences"""
        s1_records = [r for r in self.decision_records if not r.system2_active and r.evacuation_timing is not None]
        s2_records = [r for r in self.decision_records if r.system2_active and r.evacuation_timing is not None]
        
        if not s1_records or not s2_records:
            return {'error': 'Insufficient evacuation timing data', 's1_count': len(s1_records), 's2_count': len(s2_records)}
            
        s1_timings = [r.evacuation_timing for r in s1_records]
        s2_timings = [r.evacuation_timing for r in s2_records]
        
        return {
            's1_mean_timing': statistics.mean(s1_timings),
            's1_median_timing': statistics.median(s1_timings),
            's1_std_timing': statistics.stdev(s1_timings) if len(s1_timings) > 1 else 0,
            's2_mean_timing': statistics.mean(s2_timings),
            's2_median_timing': statistics.median(s2_timings),
            's2_std_timing': statistics.stdev(s2_timings) if len(s2_timings) > 1 else 0,
            's1_sample_size': len(s1_timings),
            's2_sample_size': len(s2_timings),
            'timing_difference': statistics.mean(s1_timings) - statistics.mean(s2_timings),
            'effect_size': self._calculate_cohens_d(s1_timings, s2_timings)
        }
    
    def analyze_cognitive_activation_patterns(self) -> Dict[str, Any]:
        """Analyze when System 2 activates using existing cognitive pressure logic"""
        if not self.decision_records:
            return {'error': 'No decision records available'}
            
        # Group by cognitive pressure levels
        pressure_bins = {}
        for record in self.decision_records:
            pressure_bin = round(record.cognitive_pressure, 1)
            if pressure_bin not in pressure_bins:
                pressure_bins[pressure_bin] = {'s1': 0, 's2': 0, 'total': 0}
            
            if record.system2_active:
                pressure_bins[pressure_bin]['s2'] += 1
            else:
                pressure_bins[pressure_bin]['s1'] += 1
            pressure_bins[pressure_bin]['total'] += 1
        
        # Calculate activation rates by pressure level
        activation_rates = {}
        for pressure, counts in pressure_bins.items():
            activation_rates[pressure] = counts['s2'] / counts['total'] if counts['total'] > 0 else 0
        
        total_decisions = len(self.decision_records)
        s2_decisions = len([r for r in self.decision_records if r.system2_active])
        
        return {
            'total_decisions': total_decisions,
            's2_activation_rate': s2_decisions / total_decisions if total_decisions > 0 else 0,
            'activation_by_pressure': pressure_bins,
            'activation_rates_by_pressure': activation_rates,
            'pressure_threshold_analysis': self._analyze_pressure_threshold()
        }
    
    def analyze_route_planning_differences(self) -> Dict[str, Any]:
        """Analyze S1 vs S2 route planning differences"""
        s1_routes = [r.route_length for r in self.decision_records if not r.system2_active and r.route_length > 0]
        s2_routes = [r.route_length for r in self.decision_records if r.system2_active and r.route_length > 0]
        
        if not s1_routes or not s2_routes:
            return {'error': 'Insufficient route data', 's1_count': len(s1_routes), 's2_count': len(s2_routes)}
            
        return {
            's1_mean_route_length': statistics.mean(s1_routes),
            's1_median_route_length': statistics.median(s1_routes),
            's2_mean_route_length': statistics.mean(s2_routes),
            's2_median_route_length': statistics.median(s2_routes),
            's1_sample_size': len(s1_routes),
            's2_sample_size': len(s2_routes),
            'route_length_difference': statistics.mean(s2_routes) - statistics.mean(s1_routes),
            'effect_size': self._calculate_cohens_d(s1_routes, s2_routes)
        }
    
    def _analyze_pressure_threshold(self) -> Dict[str, Any]:
        """Analyze cognitive pressure threshold for System 2 activation"""
        s1_pressures = [r.cognitive_pressure for r in self.decision_records if not r.system2_active]
        s2_pressures = [r.cognitive_pressure for r in self.decision_records if r.system2_active]
        
        if not s1_pressures or not s2_pressures:
            return {'error': 'Insufficient pressure data'}
            
        return {
            's1_mean_pressure': statistics.mean(s1_pressures),
            's1_max_pressure': max(s1_pressures),
            's2_mean_pressure': statistics.mean(s2_pressures),
            's2_min_pressure': min(s2_pressures),
            'pressure_separation': min(s2_pressures) - max(s1_pressures) if s2_pressures and s1_pressures else 0
        }
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        if len(group1) < 2 or len(group2) < 2:
            return 0.0
            
        mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
        std1, std2 = statistics.stdev(group1), statistics.stdev(group2)
        n1, n2 = len(group1), len(group2)
        
        # Pooled standard deviation
        pooled_std = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
        pooled_std = pooled_std**0.5
        
        if pooled_std == 0:
            return 0.0
            
        return (mean1 - mean2) / pooled_std
    
    def generate_refugee_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive S1 vs S2 analysis for refugee contexts"""
        return {
            'evacuation_timing': self.analyze_evacuation_timing(),
            'cognitive_activation': self.analyze_cognitive_activation_patterns(),
            'route_planning': self.analyze_route_planning_differences(),
            'summary_statistics': self._generate_summary_statistics()
        }
    
    def _generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not self.decision_records:
            return {'error': 'No decision records'}
            
        total_records = len(self.decision_records)
        s1_records = len([r for r in self.decision_records if not r.system2_active])
        s2_records = len([r for r in self.decision_records if r.system2_active])
        
        return {
            'total_decisions': total_records,
            's1_decisions': s1_records,
            's2_decisions': s2_records,
            's2_activation_rate': s2_records / total_records if total_records > 0 else 0,
            'unique_agents': len(set(id(r.agent_ref) for r in self.decision_records)),
            'time_span': {
                'start': min(r.time for r in self.decision_records),
                'end': max(r.time for r in self.decision_records)
            } if self.decision_records else None
        }
    
    def save_decision_data(self, output_dir: str) -> None:
        """Save decision data in CSV format compatible with existing Flee analysis"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save all decisions
        with open(output_path / 'refugee_decisions.csv', 'w', newline='') as f:
            if self.decision_records:
                fieldnames = [
                    'time', 'agent_ref_id', 'system2_active', 'cognitive_pressure', 'connections',
                    'conflict_level', 'movechance', 'evacuation_timing', 'destination_chosen',
                    'route_length', 'location', 'timesteps_since_departure'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in self.decision_records:
                    writer.writerow({
                        'time': record.time,
                        'agent_ref_id': id(record.agent_ref),  # Use object ID for CSV
                        'system2_active': record.system2_active,
                        'cognitive_pressure': record.cognitive_pressure,
                        'connections': record.connections,
                        'conflict_level': record.conflict_level,
                        'movechance': record.movechance,
                        'evacuation_timing': record.evacuation_timing or -1,
                        'destination_chosen': record.destination_chosen or '',
                        'route_length': record.route_length,
                        'location': record.decision_factors.get('location', ''),
                        'timesteps_since_departure': record.decision_factors.get('timesteps_since_departure', 0)
                    })
        
        # Save analysis report
        import json
        with open(output_path / 'refugee_analysis_report.json', 'w') as f:
            json.dump(self.generate_refugee_analysis_report(), f, indent=2)
        
        print(f"Saved {len(self.decision_records)} decision records to {output_path}")

# Global tracker instance for easy integration
_global_tracker = None

def get_refugee_tracker() -> RefugeeDecisionTracker:
    """Get or create global refugee decision tracker"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = RefugeeDecisionTracker()
    return _global_tracker

def track_refugee_decision(agent, system2_active: bool, movechance: float, 
                         time: int, route: List = None) -> None:
    """Convenience function to track refugee decision"""
    tracker = get_refugee_tracker()
    tracker.track_refugee_decision(agent, system2_active, movechance, time, route)

if __name__ == "__main__":
    # Example usage
    tracker = RefugeeDecisionTracker()
    print("Refugee Decision Tracker initialized")
    print("Ready to integrate with existing Flee S1/S2 system")