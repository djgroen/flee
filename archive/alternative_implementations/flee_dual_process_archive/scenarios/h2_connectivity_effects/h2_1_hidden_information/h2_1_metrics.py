"""
Metrics analysis for H2.1 Hidden Information scenario.

This module provides analysis tools for measuring information sharing effectiveness,
destination discovery rates, and network effects in the hidden information scenario.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import os
import json
from pathlib import Path


class H2_1_MetricsAnalyzer:
    """Analyzer for H2.1 Hidden Information scenario metrics."""
    
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
        Perform comprehensive analysis of H2.1 scenario results.
        
        Returns:
            Dictionary containing all analysis results
        """
        results = {
            'scenario': 'H2.1_Hidden_Information',
            'discovery_rates': self._analyze_discovery_rates(),
            'information_propagation': self._analyze_information_propagation(),
            'destination_quality': self._analyze_destination_quality(),
            'network_effects': self._analyze_network_effects(),
            'decision_timing': self._analyze_decision_timing(),
            'summary_statistics': {}
        }
        
        # Generate summary statistics
        results['summary_statistics'] = self._generate_summary_statistics(results)
        
        return results
    
    def _analyze_discovery_rates(self) -> Dict[str, Any]:
        """Analyze destination discovery rates by agent type."""
        discovery_data = {
            'by_agent_type': {},
            'overall_discovery_rate': 0.0,
            'discovery_timeline': {}
        }
        
        # Load cognitive tracking data if available
        cognitive_file = self.output_dir / 'cognitive_tracking.csv'
        if cognitive_file.exists():
            df = pd.read_csv(cognitive_file)
            
            # Analyze discovery by agent type
            for agent_type in self.agent_types:
                agent_data = df[df['agent_type'] == agent_type] if 'agent_type' in df.columns else df
                
                # Count agents who discovered Hidden_Camp
                discovered_hidden = len(agent_data[agent_data['known_locations'].str.contains('Hidden_Camp', na=False)])
                total_agents = len(agent_data['agent_id'].unique()) if 'agent_id' in agent_data.columns else len(agent_data)
                
                discovery_rate = discovered_hidden / total_agents if total_agents > 0 else 0.0
                
                discovery_data['by_agent_type'][agent_type] = {
                    'discovery_rate': discovery_rate,
                    'discovered_count': discovered_hidden,
                    'total_count': total_agents
                }
            
            # Overall discovery rate
            total_discovered = sum(data['discovered_count'] for data in discovery_data['by_agent_type'].values())
            total_agents = sum(data['total_count'] for data in discovery_data['by_agent_type'].values())
            discovery_data['overall_discovery_rate'] = total_discovered / total_agents if total_agents > 0 else 0.0
        
        return discovery_data
    
    def _analyze_information_propagation(self) -> Dict[str, Any]:
        """Analyze information propagation speed and patterns."""
        propagation_data = {
            'propagation_speed': 0.0,
            'information_cascade_timeline': [],
            'network_efficiency': 0.0,
            'sharing_events': 0
        }
        
        # Load decision log if available
        decision_file = self.output_dir / 'decision_log.csv'
        if decision_file.exists():
            df = pd.read_csv(decision_file)
            
            # Analyze information sharing events
            sharing_events = df[df['decision_type'] == 'information_sharing'] if 'decision_type' in df.columns else pd.DataFrame()
            propagation_data['sharing_events'] = len(sharing_events)
            
            # Analyze discovery timeline
            discovery_events = df[df['decision_factors'].str.contains('Hidden_Camp', na=False)] if 'decision_factors' in df.columns else pd.DataFrame()
            
            if not discovery_events.empty and 'day' in discovery_events.columns:
                # Calculate propagation speed (days to reach 50% of connected agents)
                discovery_timeline = discovery_events.groupby('day').size().cumsum()
                total_connected = len(df[df['agent_type'] == 's2_connected']['agent_id'].unique()) if 'agent_type' in df.columns else 1
                
                halfway_point = total_connected * 0.5
                propagation_day = discovery_timeline[discovery_timeline >= halfway_point].index[0] if len(discovery_timeline[discovery_timeline >= halfway_point]) > 0 else 150
                propagation_data['propagation_speed'] = propagation_day
                
                # Create timeline data
                propagation_data['information_cascade_timeline'] = [
                    {'day': int(day), 'cumulative_discoveries': int(count)}
                    for day, count in discovery_timeline.items()
                ]
        
        return propagation_data
    
    def _analyze_destination_quality(self) -> Dict[str, Any]:
        """Analyze quality of destination choices by agent type."""
        quality_data = {
            'by_agent_type': {},
            'overall_quality_index': 0.0,
            'safety_outcomes': {},
            'capacity_utilization': {}
        }
        
        # Load output data
        output_file = self.output_dir / 'out.csv'
        if output_file.exists():
            df = pd.read_csv(output_file)
            
            # Define destination quality scores
            destination_scores = {
                'Origin': 0.0,  # Staying at origin is worst outcome
                'Information_Hub': 0.2,  # Temporary location
                'Obvious_Camp': 0.6,  # Suboptimal but accessible
                'Hidden_Camp': 0.9   # Optimal destination
            }
            
            # Analyze by agent type if data is available
            for agent_type in self.agent_types:
                # This would need agent type tracking in output
                # For now, estimate based on destination patterns
                
                agent_quality = {
                    'average_safety': 0.0,
                    'average_capacity_utilization': 0.0,
                    'destination_distribution': {},
                    'quality_index': 0.0
                }
                
                # Calculate destination distribution
                if 'location' in df.columns:
                    locations = df['location'].value_counts()
                    total = locations.sum()
                    
                    for location, count in locations.items():
                        agent_quality['destination_distribution'][location] = count / total
                        agent_quality['quality_index'] += (count / total) * destination_scores.get(location, 0.0)
                
                quality_data['by_agent_type'][agent_type] = agent_quality
        
        return quality_data
    
    def _analyze_network_effects(self) -> Dict[str, Any]:
        """Analyze the impact of social network connectivity."""
        network_data = {
            'connectivity_advantage': 0.0,
            'isolation_penalty': 0.0,
            'network_efficiency': 0.0,
            'comparative_outcomes': {}
        }
        
        # Compare outcomes between connected and isolated agents
        discovery_rates = self._analyze_discovery_rates()['by_agent_type']
        
        if 's2_connected' in discovery_rates and 's2_isolated' in discovery_rates:
            connected_rate = discovery_rates['s2_connected']['discovery_rate']
            isolated_rate = discovery_rates['s2_isolated']['discovery_rate']
            
            network_data['connectivity_advantage'] = connected_rate - isolated_rate
            network_data['isolation_penalty'] = isolated_rate - discovery_rates.get('s1_baseline', {}).get('discovery_rate', 0.0)
            
            # Network efficiency: how much better connected agents perform
            if isolated_rate > 0:
                network_data['network_efficiency'] = (connected_rate - isolated_rate) / isolated_rate
            else:
                network_data['network_efficiency'] = float('inf') if connected_rate > 0 else 0.0
        
        return network_data
    
    def _analyze_decision_timing(self) -> Dict[str, Any]:
        """Analyze timing of decisions by agent type."""
        timing_data = {
            'by_agent_type': {},
            'evacuation_waves': [],
            'decision_speed_comparison': {}
        }
        
        # Load movement data
        output_file = self.output_dir / 'out.csv'
        if output_file.exists():
            df = pd.read_csv(output_file)
            
            # Analyze evacuation timing patterns
            if 'day' in df.columns:
                # Find evacuation waves (days with high movement)
                daily_movements = df.groupby('day').size()
                threshold = daily_movements.mean() + daily_movements.std()
                
                evacuation_waves = daily_movements[daily_movements > threshold]
                timing_data['evacuation_waves'] = [
                    {'day': int(day), 'movement_count': int(count)}
                    for day, count in evacuation_waves.items()
                ]
        
        return timing_data
    
    def _generate_summary_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from analysis results."""
        summary = {
            'total_agents_analyzed': 0,
            'hidden_camp_discovery_success': False,
            'network_effect_detected': False,
            'information_sharing_effective': False,
            'key_findings': []
        }
        
        # Check if hidden camp discovery was successful
        discovery_rates = results['discovery_rates']['by_agent_type']
        if 's2_connected' in discovery_rates:
            connected_rate = discovery_rates['s2_connected']['discovery_rate']
            summary['hidden_camp_discovery_success'] = connected_rate > 0.1  # At least 10% discovery
            
            if connected_rate > 0.5:
                summary['key_findings'].append("High discovery rate for connected agents")
        
        # Check for network effects
        network_effects = results['network_effects']
        if network_effects['connectivity_advantage'] > 0.1:  # At least 10% advantage
            summary['network_effect_detected'] = True
            summary['key_findings'].append("Significant connectivity advantage detected")
        
        # Check information sharing effectiveness
        propagation = results['information_propagation']
        if propagation['sharing_events'] > 0:
            summary['information_sharing_effective'] = True
            summary['key_findings'].append("Information sharing events observed")
        
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
            "# H2.1 Hidden Information Scenario Analysis Report",
            "",
            "## Summary",
            f"- Scenario: {results['scenario']}",
            f"- Hidden Camp Discovery Success: {results['summary_statistics']['hidden_camp_discovery_success']}",
            f"- Network Effect Detected: {results['summary_statistics']['network_effect_detected']}",
            f"- Information Sharing Effective: {results['summary_statistics']['information_sharing_effective']}",
            "",
            "## Discovery Rates by Agent Type"
        ]
        
        for agent_type, data in results['discovery_rates']['by_agent_type'].items():
            report_lines.extend([
                f"### {agent_type.replace('_', ' ').title()}",
                f"- Discovery Rate: {data['discovery_rate']:.2%}",
                f"- Agents Discovered: {data['discovered_count']}/{data['total_count']}",
                ""
            ])
        
        report_lines.extend([
            "## Network Effects",
            f"- Connectivity Advantage: {results['network_effects']['connectivity_advantage']:.2%}",
            f"- Network Efficiency: {results['network_effects']['network_efficiency']:.2f}",
            "",
            "## Information Propagation",
            f"- Propagation Speed: {results['information_propagation']['propagation_speed']:.1f} days",
            f"- Sharing Events: {results['information_propagation']['sharing_events']}",
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


def analyze_h2_1_scenario(output_directory: str) -> Dict[str, Any]:
    """
    Convenience function to analyze H2.1 scenario results.
    
    Args:
        output_directory: Path to simulation output directory
        
    Returns:
        Analysis results dictionary
    """
    analyzer = H2_1_MetricsAnalyzer(output_directory)
    return analyzer.analyze_scenario()


def generate_h2_1_report(output_directory: str, report_file: Optional[str] = None) -> str:
    """
    Convenience function to generate H2.1 analysis report.
    
    Args:
        output_directory: Path to simulation output directory
        report_file: Optional file path to save report
        
    Returns:
        Report text
    """
    analyzer = H2_1_MetricsAnalyzer(output_directory)
    return analyzer.generate_report(report_file)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
        results = analyze_h2_1_scenario(output_dir)
        
        print("H2.1 Hidden Information Scenario Analysis")
        print("=" * 50)
        print(f"Overall Discovery Rate: {results['discovery_rates']['overall_discovery_rate']:.2%}")
        print(f"Network Advantage: {results['network_effects']['connectivity_advantage']:.2%}")
        print(f"Information Sharing Events: {results['information_propagation']['sharing_events']}")
        
        # Generate full report
        report = generate_h2_1_report(output_dir)
        print("\nFull Report:")
        print(report)
    else:
        print("Usage: python h2_1_metrics.py <output_directory>")