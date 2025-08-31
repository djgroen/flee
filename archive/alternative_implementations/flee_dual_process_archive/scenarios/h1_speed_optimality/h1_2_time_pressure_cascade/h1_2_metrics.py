"""
H1.2 Time Pressure Cascade Scenario Metrics

This module provides temporal pressure measurements for the H1.2 scenario
testing S1 (immediate) vs S2 (anticipatory) responses to cascading conflicts.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
import json


class H1_2_Metrics:
    """
    Metrics calculator for H1.2 Time Pressure Cascade scenario.
    
    Measures temporal decision-making through:
    - evacuation_timing: Speed of response to approaching threats
    - anticipatory_behavior: Evidence of forward-looking decisions
    - cascade_response_quality: Effectiveness of responses to sequential threats
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize metrics calculator.
        
        Args:
            output_dir: Directory containing simulation output files
        """
        self.output_dir = output_dir
        self.conflict_schedule = {
            'Town_A': [0, 20],  # Initial conflict at day 0, escalation at day 20
            'Town_B': [5, 25],  # Initial conflict at day 5, escalation at day 25
            'Town_C': [10, 30], # Initial conflict at day 10, escalation at day 30
            'Town_D': [15, 35]  # Initial conflict at day 15, escalation at day 35
        }
        self.town_populations = {
            'Town_A': 8000,
            'Town_B': 6000, 
            'Town_C': 4000,
            'Town_D': 2000
        }
        
    def calculate_evacuation_timing(self, out_csv_path: str) -> Dict[str, Dict]:
        """
        Calculate evacuation timing metrics for each town.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with evacuation timing analysis by town
        """
        try:
            df = pd.read_csv(out_csv_path, comment='#')
            
            evacuation_metrics = {}
            
            for town, conflict_days in self.conflict_schedule.items():
                if town not in df.columns:
                    evacuation_metrics[town] = {'error': f'No data for {town}'}
                    continue
                    
                population_data = df[town].values
                initial_pop = self.town_populations[town]
                
                # Find evacuation start (10% population decline)
                evacuation_threshold = 0.9 * initial_pop
                evacuation_start_day = None
                
                for day, pop in enumerate(population_data):
                    if pop < evacuation_threshold:
                        evacuation_start_day = day
                        break
                        
                # Calculate evacuation rate (steepest decline period)
                if len(population_data) > 1:
                    daily_changes = np.diff(population_data)
                    max_evacuation_day = np.argmin(daily_changes)
                    max_evacuation_rate = abs(daily_changes[max_evacuation_day])
                else:
                    max_evacuation_day = 0
                    max_evacuation_rate = 0
                    
                # Analyze timing relative to conflict
                first_conflict_day = conflict_days[0]
                second_conflict_day = conflict_days[1]
                
                # Categorize response type
                response_type = "no_evacuation"
                if evacuation_start_day is not None:
                    if evacuation_start_day <= first_conflict_day:
                        response_type = "anticipatory"  # Evacuated before/during initial conflict
                    elif evacuation_start_day <= first_conflict_day + 2:
                        response_type = "immediate"     # Evacuated within 2 days of conflict
                    elif evacuation_start_day <= second_conflict_day:
                        response_type = "delayed"       # Evacuated before escalation
                    else:
                        response_type = "crisis"        # Evacuated only after escalation
                        
                evacuation_metrics[town] = {
                    'evacuation_start_day': evacuation_start_day,
                    'max_evacuation_day': int(max_evacuation_day),
                    'max_evacuation_rate': float(max_evacuation_rate),
                    'first_conflict_day': first_conflict_day,
                    'second_conflict_day': second_conflict_day,
                    'response_type': response_type,
                    'initial_population': initial_pop,
                    'final_population': float(population_data[-1]) if len(population_data) > 0 else 0.0
                }
                
            return evacuation_metrics
            
        except Exception as e:
            return {'error': f'Failed to calculate evacuation_timing: {str(e)}'}
    
    def calculate_anticipatory_behavior(self, out_csv_path: str) -> Dict[str, float]:
        """
        Calculate anticipatory behavior metrics.
        
        Measures evidence of forward-looking decision-making by analyzing
        evacuation patterns before conflicts reach each town.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with anticipatory behavior metrics
        """
        try:
            evacuation_data = self.calculate_evacuation_timing(out_csv_path)
            
            anticipatory_count = 0
            immediate_count = 0
            delayed_count = 0
            crisis_count = 0
            total_towns = 0
            
            for town, metrics in evacuation_data.items():
                if 'error' in metrics:
                    continue
                    
                total_towns += 1
                response_type = metrics['response_type']
                
                if response_type == 'anticipatory':
                    anticipatory_count += 1
                elif response_type == 'immediate':
                    immediate_count += 1
                elif response_type == 'delayed':
                    delayed_count += 1
                elif response_type == 'crisis':
                    crisis_count += 1
                    
            # Calculate anticipatory behavior score
            if total_towns > 0:
                anticipatory_score = anticipatory_count / total_towns
                immediate_score = immediate_count / total_towns
                delayed_score = delayed_count / total_towns
                crisis_score = crisis_count / total_towns
            else:
                anticipatory_score = immediate_score = delayed_score = crisis_score = 0.0
                
            return {
                'anticipatory_score': anticipatory_score,
                'immediate_score': immediate_score,
                'delayed_score': delayed_score,
                'crisis_score': crisis_score,
                'total_towns_analyzed': total_towns,
                'response_distribution': {
                    'anticipatory': anticipatory_count,
                    'immediate': immediate_count,
                    'delayed': delayed_count,
                    'crisis': crisis_count
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to calculate anticipatory_behavior: {str(e)}'}
    
    def calculate_cascade_response_quality(self, out_csv_path: str) -> Dict[str, float]:
        """
        Calculate cascade response quality metrics.
        
        Measures how effectively agents respond to the sequential threat pattern.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with cascade response quality metrics
        """
        try:
            df = pd.read_csv(out_csv_path, comment='#')
            evacuation_data = self.calculate_evacuation_timing(out_csv_path)
            
            # Calculate total evacuation efficiency
            total_initial_pop = sum(self.town_populations.values())
            total_final_pop = 0
            
            for town in self.town_populations.keys():
                if town in df.columns and len(df) > 0:
                    total_final_pop += df[town].iloc[-1]
                    
            evacuation_rate = (total_initial_pop - total_final_pop) / total_initial_pop if total_initial_pop > 0 else 0
            
            # Calculate camp utilization
            camp_populations = {}
            for camp in ['Safe_Camp_North', 'Safe_Camp_South']:
                if camp in df.columns and len(df) > 0:
                    camp_populations[camp] = df[camp].iloc[-1]
                else:
                    camp_populations[camp] = 0
                    
            total_camp_population = sum(camp_populations.values())
            
            # Calculate response timing quality (earlier is better)
            timing_scores = []
            for town, metrics in evacuation_data.items():
                if 'error' not in metrics and metrics['evacuation_start_day'] is not None:
                    # Score based on how early evacuation started relative to conflict
                    conflict_day = metrics['first_conflict_day']
                    evacuation_day = metrics['evacuation_start_day']
                    
                    if evacuation_day <= conflict_day:
                        timing_score = 1.0  # Perfect anticipation
                    elif evacuation_day <= conflict_day + 5:
                        timing_score = 0.8  # Good immediate response
                    elif evacuation_day <= conflict_day + 10:
                        timing_score = 0.6  # Acceptable delayed response
                    else:
                        timing_score = 0.2  # Poor crisis response
                        
                    timing_scores.append(timing_score)
                    
            avg_timing_quality = np.mean(timing_scores) if timing_scores else 0.0
            
            # Composite cascade response quality
            cascade_quality = (evacuation_rate + avg_timing_quality) / 2.0
            
            return {
                'evacuation_rate': evacuation_rate,
                'total_evacuated': total_initial_pop - total_final_pop,
                'camp_populations': camp_populations,
                'total_camp_population': total_camp_population,
                'avg_timing_quality': avg_timing_quality,
                'cascade_response_quality': cascade_quality,
                'timing_scores_by_town': dict(zip(evacuation_data.keys(), timing_scores))
            }
            
        except Exception as e:
            return {'error': f'Failed to calculate cascade_response_quality: {str(e)}'}
    
    def calculate_temporal_pressure_index(self, out_csv_path: str) -> Dict[str, float]:
        """
        Calculate composite temporal pressure response index.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            
        Returns:
            Dictionary with composite temporal pressure metrics
        """
        evacuation_metrics = self.calculate_evacuation_timing(out_csv_path)
        anticipatory_metrics = self.calculate_anticipatory_behavior(out_csv_path)
        cascade_metrics = self.calculate_cascade_response_quality(out_csv_path)
        
        # Extract key scores
        anticipatory_score = anticipatory_metrics.get('anticipatory_score', 0.0)
        cascade_quality = cascade_metrics.get('cascade_response_quality', 0.0)
        evacuation_rate = cascade_metrics.get('evacuation_rate', 0.0)
        
        # Composite temporal pressure index
        temporal_pressure_index = (anticipatory_score + cascade_quality + evacuation_rate) / 3.0
        
        return {
            'anticipatory_score': anticipatory_score,
            'cascade_quality': cascade_quality,
            'evacuation_rate': evacuation_rate,
            'temporal_pressure_index': temporal_pressure_index,
            'evacuation_metrics': evacuation_metrics,
            'anticipatory_metrics': anticipatory_metrics,
            'cascade_metrics': cascade_metrics
        }
    
    def generate_h1_2_report(self, out_csv_path: str, output_file: Optional[str] = None) -> Dict:
        """
        Generate comprehensive H1.2 scenario analysis report.
        
        Args:
            out_csv_path: Path to out.csv file with population data
            output_file: Optional path to save JSON report
            
        Returns:
            Complete analysis results dictionary
        """
        results = self.calculate_temporal_pressure_index(out_csv_path)
        
        # Add scenario metadata
        results['scenario'] = 'H1.2_Time_Pressure_Cascade'
        results['description'] = 'Temporal pressure testing with cascading conflicts'
        results['conflict_schedule'] = self.conflict_schedule
        results['town_populations'] = self.town_populations
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
                
        return results


def analyze_h1_2_scenario(output_dir: str, save_report: bool = True) -> Dict:
    """
    Convenience function to analyze H1.2 scenario results.
    
    Args:
        output_dir: Directory containing simulation output files
        save_report: Whether to save analysis report to file
        
    Returns:
        Analysis results dictionary
    """
    metrics = H1_2_Metrics(output_dir)
    out_csv_path = os.path.join(output_dir, 'out.csv')
    
    if not os.path.exists(out_csv_path):
        return {'error': f'Output file not found: {out_csv_path}'}
    
    output_file = os.path.join(output_dir, 'h1_2_analysis.json') if save_report else None
    return metrics.generate_h1_2_report(out_csv_path, output_file)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
        results = analyze_h1_2_scenario(output_dir)
        print(json.dumps(results, indent=2))
    else:
        print("Usage: python h1_2_metrics.py <output_directory>")