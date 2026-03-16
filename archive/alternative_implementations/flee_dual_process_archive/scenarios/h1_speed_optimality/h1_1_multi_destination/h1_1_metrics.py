"""
H1.1 Multi-Destination Choice Scenario Metrics

This module provides decision quality measurements for the H1.1 scenario
testing speed vs optimality trade-offs in multi-destination choice situations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
import json


class H1_1_Metrics:
    """
    Metrics calculator for H1.1 Multi-Destination Choice scenario.
    
    Measures decision quality through:
    - time_to_move: Speed of evacuation decisions
    - camp_efficiency: Quality of destination choices
    - avg_safety_achieved: Safety outcomes of decisions
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize metrics calculator.
        
        Args:
            output_dir: Directory containing simulation output files
        """
        self.output_dir = output_dir
        self.camp_properties = {
            'Camp_A': {'capacity': 3000, 'distance': 50, 'safety_score': 0.9},
            'Camp_B': {'capacity': 5000, 'distance': 75, 'safety_score': 0.8}, 
            'Camp_C': {'capacity': 8000, 'distance': 100, 'safety_score': 0.7}
        }
        
    def calculate_time_to_move(self, out_csv_path: str) -> Dict[str, float]:
        """
        Calculate time to move metrics for different cognitive modes.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with time to move statistics by location
        """
        try:
            df = pd.read_csv(out_csv_path, comment='#')
            
            # Find when Origin population starts declining significantly
            origin_pop = df['Origin'].values if 'Origin' in df.columns else []
            
            if len(origin_pop) == 0:
                return {'error': 'No Origin population data found'}
                
            initial_pop = origin_pop[0]
            movement_threshold = 0.1 * initial_pop  # 10% population decline
            
            # Find first day when population drops below threshold
            movement_start_day = None
            for day, pop in enumerate(origin_pop):
                if pop < (initial_pop - movement_threshold):
                    movement_start_day = day
                    break
                    
            # Calculate peak movement day (steepest decline)
            if len(origin_pop) > 1:
                daily_changes = np.diff(origin_pop)
                peak_movement_day = np.argmin(daily_changes)  # Most negative change
            else:
                peak_movement_day = 0
                
            return {
                'movement_start_day': movement_start_day if movement_start_day else -1,
                'peak_movement_day': int(peak_movement_day),
                'initial_population': float(initial_pop),
                'final_population': float(origin_pop[-1]) if len(origin_pop) > 0 else 0.0
            }
            
        except Exception as e:
            return {'error': f'Failed to calculate time_to_move: {str(e)}'}
    
    def calculate_camp_efficiency(self, out_csv_path: str) -> Dict[str, float]:
        """
        Calculate camp efficiency metrics based on destination choices.
        
        Efficiency considers capacity utilization vs distance trade-offs.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with camp efficiency metrics
        """
        try:
            df = pd.read_csv(out_csv_path, comment='#')
            
            # Get final populations at each camp
            final_populations = {}
            efficiency_scores = {}
            
            for camp, properties in self.camp_properties.items():
                if camp in df.columns:
                    final_pop = df[camp].iloc[-1] if len(df) > 0 else 0
                    final_populations[camp] = final_pop
                    
                    # Calculate efficiency: (population/capacity) / (distance/50km)
                    # Higher score = better utilization relative to distance
                    capacity_util = final_pop / properties['capacity']
                    distance_penalty = properties['distance'] / 50.0  # Normalize to Camp_A distance
                    efficiency_scores[camp] = capacity_util / distance_penalty if distance_penalty > 0 else 0
                else:
                    final_populations[camp] = 0
                    efficiency_scores[camp] = 0
                    
            # Overall efficiency is weighted average
            total_refugees = sum(final_populations.values())
            if total_refugees > 0:
                weighted_efficiency = sum(
                    pop * efficiency_scores[camp] 
                    for camp, pop in final_populations.items()
                ) / total_refugees
            else:
                weighted_efficiency = 0.0
                
            return {
                'final_populations': final_populations,
                'efficiency_scores': efficiency_scores,
                'weighted_efficiency': weighted_efficiency,
                'total_refugees_settled': total_refugees
            }
            
        except Exception as e:
            return {'error': f'Failed to calculate camp_efficiency: {str(e)}'}
    
    def calculate_avg_safety_achieved(self, out_csv_path: str) -> Dict[str, float]:
        """
        Calculate average safety achieved based on destination choices.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with safety metrics
        """
        try:
            df = pd.read_csv(out_csv_path, comment='#')
            
            # Get final populations at each camp
            final_populations = {}
            safety_scores = {}
            
            for camp, properties in self.camp_properties.items():
                if camp in df.columns:
                    final_pop = df[camp].iloc[-1] if len(df) > 0 else 0
                    final_populations[camp] = final_pop
                    safety_scores[camp] = properties['safety_score']
                else:
                    final_populations[camp] = 0
                    safety_scores[camp] = properties['safety_score']
                    
            # Calculate weighted average safety
            total_refugees = sum(final_populations.values())
            if total_refugees > 0:
                weighted_safety = sum(
                    pop * safety_scores[camp] 
                    for camp, pop in final_populations.items()
                ) / total_refugees
            else:
                weighted_safety = 0.0
                
            return {
                'final_populations': final_populations,
                'safety_scores': safety_scores,
                'weighted_safety': weighted_safety,
                'total_refugees_settled': total_refugees
            }
            
        except Exception as e:
            return {'error': f'Failed to calculate avg_safety_achieved: {str(e)}'}
    
    def calculate_decision_quality_index(self, out_csv_path: str) -> Dict[str, float]:
        """
        Calculate composite decision quality index combining all metrics.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with composite decision quality metrics
        """
        time_metrics = self.calculate_time_to_move(out_csv_path)
        efficiency_metrics = self.calculate_camp_efficiency(out_csv_path)
        safety_metrics = self.calculate_avg_safety_achieved(out_csv_path)
        
        # Combine metrics into decision quality index
        # Speed component (inverse of movement start day, normalized)
        speed_score = 0.0
        if 'movement_start_day' in time_metrics and time_metrics['movement_start_day'] > 0:
            # Earlier movement = higher speed score (max 1.0)
            speed_score = max(0.0, 1.0 - (time_metrics['movement_start_day'] / 50.0))
        
        # Efficiency component
        efficiency_score = efficiency_metrics.get('weighted_efficiency', 0.0)
        
        # Safety component  
        safety_score = safety_metrics.get('weighted_safety', 0.0)
        
        # Composite index (equal weights)
        decision_quality_index = (speed_score + efficiency_score + safety_score) / 3.0
        
        return {
            'speed_score': speed_score,
            'efficiency_score': efficiency_score,
            'safety_score': safety_score,
            'decision_quality_index': decision_quality_index,
            'time_metrics': time_metrics,
            'efficiency_metrics': efficiency_metrics,
            'safety_metrics': safety_metrics
        }
    
    def generate_h1_1_report(self, out_csv_path: str, output_file: Optional[str] = None) -> Dict:
        """
        Generate comprehensive H1.1 scenario analysis report.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            output_file: Optional path to save JSON report
            
        Returns:
            Complete analysis results dictionary
        """
        results = self.calculate_decision_quality_index(out_csv_path)
        
        # Add scenario metadata
        results['scenario'] = 'H1.1_Multi_Destination_Choice'
        results['description'] = 'Speed vs Optimality testing with multiple camp options'
        results['camp_properties'] = self.camp_properties
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
                
        return results


def analyze_h1_1_scenario(output_dir: str, save_report: bool = True) -> Dict:
    """
    Convenience function to analyze H1.1 scenario results.
    
    Args:
        output_dir: Directory containing simulation output files
        save_report: Whether to save analysis report to file
        
    Returns:
        Analysis results dictionary
    """
    metrics = H1_1_Metrics(output_dir)
    out_csv_path = os.path.join(output_dir, 'out.csv')
    
    if not os.path.exists(out_csv_path):
        return {'error': f'Output file not found: {out_csv_path}'}
    
    output_file = os.path.join(output_dir, 'h1_1_analysis.json') if save_report else None
    return metrics.generate_h1_1_report(out_csv_path, output_file)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
        results = analyze_h1_1_scenario(output_dir)
        print(json.dumps(results, indent=2))
    else:
        print("Usage: python h1_1_metrics.py <output_directory>")