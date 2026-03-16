"""
Metrics analysis for H2.2 Dynamic Information Sharing scenario.

This module provides analysis tools for measuring information accuracy, decision timing,
and network information value in the dynamic information sharing scenario.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import os
import json
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt


class H2_2_MetricsAnalyzer:
    """Analyzer for H2.2 Dynamic Information Sharing scenario metrics."""
    
    def __init__(self, output_directory: str):
        """
        Initialize metrics analyzer.
        
        Args:
            output_directory: Path to simulation output directory
        """
        self.output_dir = Path(output_directory)
        self.agent_types = ['s1_baseline', 's2_isolated', 's2_connected']
        
    def analyze_scenario(self) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of H2.2 scenario results.
        
        Returns:
            Dictionary containing all analysis results
        """
        results = {
            'scenario': 'H2.2_Dynamic_Information_Sharing',
            'information_accuracy': self._analyze_information_accuracy(),
            'decision_timing': self._analyze_decision_timing(),
            'secondary_displacement': self._analyze_secondary_displacement(),
            'network_information_value': self._analyze_network_information_value(),
            'capacity_utilization': self._analyze_capacity_utilization(),
            'summary_statistics': {}
        }
        
        # Generate summary statistics
        results['summary_statistics'] = self._generate_summary_statistics(results)
        
        return results
    
    def _analyze_information_accuracy(self) -> Dict[str, Any]:
        """Analyze information accuracy by agent type over time."""
        accuracy_data = {
            'by_agent_type': {},
            'temporal_accuracy': {},
            'information_lag_impact': {},
            'accuracy_correlation': {}
        }
        
        # Load cognitive tracking data if available
        cognitive_file = self.output_dir / 'cognitive_tracking.csv'
        if cognitive_file.exists():
            df = pd.read_csv(cognitive_file)
            
            # Analyze accuracy by agent type
            for agent_type in self.agent_types:
                agent_data = df[df['agent_type'] == agent_type] if 'agent_type' in df.columns else df
                
                if 'information_accuracy' in agent_data.columns:
                    accuracy_stats = {
                        'mean_accuracy': agent_data['information_accuracy'].mean(),
                        'std_accuracy': agent_data['information_accuracy'].std(),
                        'min_accuracy': agent_data['information_accuracy'].min(),
                        'max_accuracy': agent_data['information_accuracy'].max(),
                        'accuracy_trend': self._calculate_trend(agent_data, 'information_accuracy')
                    }
                else:
                    accuracy_stats = {
                        'mean_accuracy': 0.0,
                        'std_accuracy': 0.0,
                        'min_accuracy': 0.0,
                        'max_accuracy': 0.0,
                        'accuracy_trend': 0.0
                    }
                
                accuracy_data['by_agent_type'][agent_type] = accuracy_stats
            
            # Temporal accuracy analysis
            if 'day' in df.columns and 'information_accuracy' in df.columns:
                temporal_accuracy = df.groupby(['day', 'agent_type'])['information_accuracy'].mean().unstack(fill_value=0)
                accuracy_data['temporal_accuracy'] = temporal_accuracy.to_dict()
        
        return accuracy_data
    
    def _analyze_decision_timing(self) -> Dict[str, Any]:
        """Analyze timing of decisions relative to capacity changes."""
        timing_data = {
            'optimal_timing_rate': {},
            'decision_delay': {},
            'capacity_change_response': {},
            'timing_efficiency': {}
        }
        
        # Load decision log if available
        decision_file = self.output_dir / 'decision_log.csv'
        capacity_file = self.output_dir.parent / 'capacity_timeline.csv'
        
        if decision_file.exists() and capacity_file.exists():
            decisions_df = pd.read_csv(decision_file)
            capacity_df = pd.read_csv(capacity_file)
            
            # Analyze timing relative to capacity changes
            capacity_change_days = set(capacity_df['Day'].values)
            
            for agent_type in self.agent_types:
                agent_decisions = decisions_df[decisions_df['agent_type'] == agent_type] if 'agent_type' in decisions_df.columns else decisions_df
                
                if 'day' in agent_decisions.columns and 'decision_type' in agent_decisions.columns:
                    movement_decisions = agent_decisions[agent_decisions['decision_type'] == 'movement']
                    
                    # Calculate timing efficiency
                    optimal_moves = 0
                    total_moves = len(movement_decisions)
                    
                    for _, decision in movement_decisions.iterrows():
                        decision_day = decision['day']
                        
                        # Check if decision was made within optimal window after capacity change
                        for change_day in capacity_change_days:
                            if change_day <= decision_day <= change_day + 7:  # 7-day optimal window
                                optimal_moves += 1
                                break
                    
                    timing_efficiency = optimal_moves / total_moves if total_moves > 0 else 0.0
                    
                    timing_data['optimal_timing_rate'][agent_type] = optimal_moves / total_moves if total_moves > 0 else 0.0
                    timing_data['timing_efficiency'][agent_type] = timing_efficiency
                    
                    # Calculate average decision delay
                    if 'information_age' in agent_decisions.columns:
                        avg_delay = agent_decisions['information_age'].mean()
                        timing_data['decision_delay'][agent_type] = avg_delay
        
        return timing_data
    
    def _analyze_secondary_displacement(self) -> Dict[str, Any]:
        """Analyze secondary displacement due to overcrowding."""
        displacement_data = {
            'secondary_move_rate': {},
            'overcrowding_incidents': {},
            'displacement_causes': {},
            'recovery_time': {}
        }
        
        # Load movement data
        output_file = self.output_dir / 'out.csv'
        if output_file.exists():
            df = pd.read_csv(output_file)
            
            # Analyze movement patterns by agent type
            for agent_type in self.agent_types:
                # This would require agent type tracking in output
                # For now, estimate based on movement patterns
                
                if 'agent_id' in df.columns and 'day' in df.columns and 'location' in df.columns:
                    # Count agents who moved multiple times
                    agent_moves = df.groupby('agent_id')['location'].nunique()
                    secondary_movers = (agent_moves > 2).sum()  # More than origin + first destination
                    total_agents = len(agent_moves)
                    
                    displacement_data['secondary_move_rate'][agent_type] = secondary_movers / total_agents if total_agents > 0 else 0.0
                
                # Analyze overcrowding incidents
                if 'location' in df.columns and 'day' in df.columns:
                    daily_occupancy = df.groupby(['day', 'location']).size()
                    
                    # Define capacity limits (would be loaded from capacity timeline)
                    capacity_limits = {
                        'Camp_Alpha': 4000,  # Initial capacity
                        'Camp_Beta': 2500,
                        'Camp_Gamma': 1500
                    }
                    
                    overcrowding_count = 0
                    for (day, location), occupancy in daily_occupancy.items():
                        if location in capacity_limits and occupancy > capacity_limits[location]:
                            overcrowding_count += 1
                    
                    displacement_data['overcrowding_incidents'][agent_type] = overcrowding_count
        
        return displacement_data
    
    def _analyze_network_information_value(self) -> Dict[str, Any]:
        """Analyze the value of network information sharing."""
        network_value_data = {
            'information_advantage': {},
            'network_efficiency': {},
            'sharing_impact': {},
            'connectivity_benefit': {}
        }
        
        # Compare connected vs isolated agents
        accuracy_data = self._analyze_information_accuracy()['by_agent_type']
        timing_data = self._analyze_decision_timing()
        
        if 's2_connected' in accuracy_data and 's2_isolated' in accuracy_data:
            connected_accuracy = accuracy_data['s2_connected']['mean_accuracy']
            isolated_accuracy = accuracy_data['s2_isolated']['mean_accuracy']
            
            network_value_data['information_advantage'] = connected_accuracy - isolated_accuracy
            
            if isolated_accuracy > 0:
                network_value_data['network_efficiency'] = (connected_accuracy - isolated_accuracy) / isolated_accuracy
            else:
                network_value_data['network_efficiency'] = float('inf') if connected_accuracy > 0 else 0.0
        
        # Analyze timing advantages
        if 'optimal_timing_rate' in timing_data:
            timing_rates = timing_data['optimal_timing_rate']
            if 's2_connected' in timing_rates and 's2_isolated' in timing_rates:
                timing_advantage = timing_rates['s2_connected'] - timing_rates['s2_isolated']
                network_value_data['timing_advantage'] = timing_advantage
        
        # Load information sharing events if available
        sharing_file = self.output_dir / 'information_sharing_log.csv'
        if sharing_file.exists():
            sharing_df = pd.read_csv(sharing_file)
            
            network_value_data['sharing_impact'] = {
                'total_sharing_events': len(sharing_df),
                'unique_sharers': sharing_df['sharer'].nunique() if 'sharer' in sharing_df.columns else 0,
                'unique_receivers': sharing_df['receiver'].nunique() if 'receiver' in sharing_df.columns else 0,
                'information_spread_rate': len(sharing_df) / sharing_df['day'].nunique() if 'day' in sharing_df.columns and len(sharing_df) > 0 else 0
            }
        
        return network_value_data
    
    def _analyze_capacity_utilization(self) -> Dict[str, Any]:
        """Analyze how well agents utilized available capacity."""
        utilization_data = {
            'efficiency_by_agent_type': {},
            'capacity_waste': {},
            'utilization_timeline': {},
            'optimal_distribution': {}
        }
        
        # Load output data and capacity timeline
        output_file = self.output_dir / 'out.csv'
        capacity_file = self.output_dir.parent / 'capacity_timeline.csv'
        
        if output_file.exists() and capacity_file.exists():
            output_df = pd.read_csv(output_file)
            capacity_df = pd.read_csv(capacity_file)
            
            # Calculate utilization efficiency
            if 'location' in output_df.columns and 'day' in output_df.columns:
                daily_occupancy = output_df.groupby(['day', 'location']).size().unstack(fill_value=0)
                
                # Calculate capacity utilization over time
                for day in daily_occupancy.index:
                    day_utilization = {}
                    
                    # Get capacity for this day
                    current_capacities = self._get_capacity_for_day(capacity_df, day)
                    
                    for location in daily_occupancy.columns:
                        occupancy = daily_occupancy.loc[day, location]
                        capacity = current_capacities.get(location, 1)
                        utilization = min(occupancy / capacity, 1.0) if capacity > 0 else 0.0
                        day_utilization[location] = utilization
                    
                    utilization_data['utilization_timeline'][day] = day_utilization
        
        return utilization_data
    
    def _get_capacity_for_day(self, capacity_df: pd.DataFrame, day: int) -> Dict[str, int]:
        """Get capacity values for a specific day."""
        capacities = {}
        
        # Get most recent capacity update for each location
        for location in capacity_df['Location'].unique():
            location_updates = capacity_df[capacity_df['Location'] == location]
            location_updates = location_updates[location_updates['Day'] <= day]
            
            if not location_updates.empty:
                latest_update = location_updates.iloc[-1]
                capacities[location] = latest_update['Capacity']
        
        return capacities
    
    def _calculate_trend(self, data: pd.DataFrame, column: str) -> float:
        """Calculate trend (slope) for a time series."""
        if 'day' not in data.columns or column not in data.columns:
            return 0.0
        
        if len(data) < 2:
            return 0.0
        
        x = data['day'].values
        y = data[column].values
        
        # Remove NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 2:
            return 0.0
        
        x_clean = x[mask]
        y_clean = y[mask]
        
        # Calculate linear regression slope
        slope, _, _, _, _ = stats.linregress(x_clean, y_clean)
        return slope
    
    def _generate_summary_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from analysis results."""
        summary = {
            'information_sharing_effective': False,
            'network_advantage_detected': False,
            'timing_improvement_observed': False,
            'secondary_displacement_reduced': False,
            'key_findings': []
        }
        
        # Check information sharing effectiveness
        network_value = results['network_information_value']
        if 'information_advantage' in network_value and network_value['information_advantage'] > 0.1:
            summary['information_sharing_effective'] = True
            summary['key_findings'].append("Information sharing provides significant accuracy advantage")
        
        # Check network advantage
        if 'network_efficiency' in network_value and network_value['network_efficiency'] > 0.2:
            summary['network_advantage_detected'] = True
            summary['key_findings'].append("Network connectivity provides substantial benefits")
        
        # Check timing improvements
        if 'timing_advantage' in network_value and network_value['timing_advantage'] > 0.1:
            summary['timing_improvement_observed'] = True
            summary['key_findings'].append("Connected agents show better decision timing")
        
        # Check secondary displacement reduction
        displacement_data = results['secondary_displacement']['secondary_move_rate']
        if 's2_connected' in displacement_data and 's2_isolated' in displacement_data:
            if displacement_data['s2_connected'] < displacement_data['s2_isolated']:
                summary['secondary_displacement_reduced'] = True
                summary['key_findings'].append("Network information reduces secondary displacement")
        
        return summary
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate a comprehensive analysis report.
        
        Args:
            output_file: Optional file path to save report
            
        Returns:
            Report text
        """
        results = self.analyze_scenario()
        
        report_lines = [
            "# H2.2 Dynamic Information Sharing Scenario Analysis Report",
            "",
            "## Summary",
            f"- Scenario: {results['scenario']}",
            f"- Information Sharing Effective: {results['summary_statistics']['information_sharing_effective']}",
            f"- Network Advantage Detected: {results['summary_statistics']['network_advantage_detected']}",
            f"- Timing Improvement Observed: {results['summary_statistics']['timing_improvement_observed']}",
            f"- Secondary Displacement Reduced: {results['summary_statistics']['secondary_displacement_reduced']}",
            "",
            "## Information Accuracy by Agent Type"
        ]
        
        for agent_type, data in results['information_accuracy']['by_agent_type'].items():
            report_lines.extend([
                f"### {agent_type.replace('_', ' ').title()}",
                f"- Mean Accuracy: {data['mean_accuracy']:.3f}",
                f"- Accuracy Range: {data['min_accuracy']:.3f} - {data['max_accuracy']:.3f}",
                f"- Accuracy Trend: {data['accuracy_trend']:.4f} per day",
                ""
            ])
        
        report_lines.extend([
            "## Network Information Value",
            f"- Information Advantage: {results['network_information_value'].get('information_advantage', 0):.3f}",
            f"- Network Efficiency: {results['network_information_value'].get('network_efficiency', 0):.3f}",
            f"- Timing Advantage: {results['network_information_value'].get('timing_advantage', 0):.3f}",
            "",
            "## Decision Timing Analysis"
        ])
        
        timing_data = results['decision_timing']
        for agent_type in self.agent_types:
            if agent_type in timing_data.get('optimal_timing_rate', {}):
                rate = timing_data['optimal_timing_rate'][agent_type]
                report_lines.append(f"- {agent_type.replace('_', ' ').title()}: {rate:.2%} optimal timing")
        
        report_lines.extend([
            "",
            "## Key Findings"
        ])
        
        for finding in results['summary_statistics']['key_findings']:
            report_lines.append(f"- {finding}")
        
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text


def analyze_h2_2_scenario(output_directory: str) -> Dict[str, Any]:
    """
    Convenience function to analyze H2.2 scenario results.
    
    Args:
        output_directory: Path to simulation output directory
        
    Returns:
        Analysis results dictionary
    """
    analyzer = H2_2_MetricsAnalyzer(output_directory)
    return analyzer.analyze_scenario()


def generate_h2_2_report(output_directory: str, report_file: Optional[str] = None) -> str:
    """
    Convenience function to generate H2.2 analysis report.
    
    Args:
        output_directory: Path to simulation output directory
        report_file: Optional file path to save report
        
    Returns:
        Report text
    """
    analyzer = H2_2_MetricsAnalyzer(output_directory)
    return analyzer.generate_report(report_file)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
        results = analyze_h2_2_scenario(output_dir)
        
        print("H2.2 Dynamic Information Sharing Scenario Analysis")
        print("=" * 60)
        
        # Display key metrics
        accuracy_data = results['information_accuracy']['by_agent_type']
        for agent_type, data in accuracy_data.items():
            print(f"{agent_type.replace('_', ' ').title()}: {data['mean_accuracy']:.3f} accuracy")
        
        network_value = results['network_information_value']
        if 'information_advantage' in network_value:
            print(f"Network Information Advantage: {network_value['information_advantage']:.3f}")
        
        # Generate full report
        report = generate_h2_2_report(output_dir)
        print("\nFull Report:")
        print(report)
    else:
        print("Usage: python h2_2_metrics.py <output_directory>")