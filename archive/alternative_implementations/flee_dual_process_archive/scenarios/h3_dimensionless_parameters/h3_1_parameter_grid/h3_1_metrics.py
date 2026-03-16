"""
H3.1 Parameter Grid Metrics

Implements metrics calculation for H3.1 parameter grid search experiments.
Focuses on measuring S2 activation rates, decision quality, and phase transition indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import json
import os


class H3_1_Metrics:
    """Metrics calculator for H3.1 parameter grid experiments."""
    
    def __init__(self):
        self.required_columns = [
            'day', 'agent_id', 'cognitive_state', 'location', 
            'decision_factors', 'movement_decision'
        ]
    
    def calculate_s2_activation_metrics(self, cognitive_data: pd.DataFrame) -> Dict:
        """
        Calculate S2 activation rate and related metrics.
        
        Args:
            cognitive_data: DataFrame with cognitive state tracking data
            
        Returns:
            Dictionary with S2 activation metrics
        """
        if cognitive_data.empty:
            return self._empty_metrics_dict()
        
        total_decisions = len(cognitive_data)
        s2_decisions = len(cognitive_data[cognitive_data['cognitive_state'] == 'S2'])
        s1_decisions = len(cognitive_data[cognitive_data['cognitive_state'] == 'S1'])
        
        # Calculate activation rate
        s2_activation_rate = s2_decisions / total_decisions if total_decisions > 0 else 0.0
        
        # Calculate temporal patterns
        s2_data = cognitive_data[cognitive_data['cognitive_state'] == 'S2']
        if not s2_data.empty:
            first_s2_day = s2_data['day'].min()
            last_s2_day = s2_data['day'].max()
            s2_duration = last_s2_day - first_s2_day + 1
            
            # Calculate S2 activation by day
            daily_s2 = s2_data.groupby('day').size()
            peak_s2_day = daily_s2.idxmax() if not daily_s2.empty else None
            peak_s2_count = daily_s2.max() if not daily_s2.empty else 0
        else:
            first_s2_day = None
            last_s2_day = None
            s2_duration = 0
            peak_s2_day = None
            peak_s2_count = 0
        
        # Calculate agent-level statistics
        agent_s2_rates = cognitive_data.groupby('agent_id')['cognitive_state'].apply(
            lambda x: (x == 'S2').mean()
        )
        
        return {
            'total_decisions': total_decisions,
            's2_decisions': s2_decisions,
            's1_decisions': s1_decisions,
            's2_activation_rate': s2_activation_rate,
            's1_activation_rate': 1.0 - s2_activation_rate,
            'temporal_patterns': {
                'first_s2_day': first_s2_day,
                'last_s2_day': last_s2_day,
                's2_duration_days': s2_duration,
                'peak_s2_day': peak_s2_day,
                'peak_s2_count': peak_s2_count
            },
            'agent_statistics': {
                'mean_agent_s2_rate': agent_s2_rates.mean(),
                'std_agent_s2_rate': agent_s2_rates.std(),
                'min_agent_s2_rate': agent_s2_rates.min(),
                'max_agent_s2_rate': agent_s2_rates.max(),
                'agents_with_s2': (agent_s2_rates > 0).sum(),
                'agents_pure_s2': (agent_s2_rates == 1.0).sum(),
                'agents_pure_s1': (agent_s2_rates == 0.0).sum()
            }
        }
    
    def calculate_decision_quality_metrics(self, decision_data: pd.DataFrame, 
                                         movement_data: pd.DataFrame) -> Dict:
        """
        Calculate decision quality metrics comparing S1 vs S2 decisions.
        
        Args:
            decision_data: DataFrame with decision log data
            movement_data: DataFrame with agent movement data
            
        Returns:
            Dictionary with decision quality metrics
        """
        if decision_data.empty or movement_data.empty:
            return self._empty_decision_quality_dict()
        
        # Merge decision and movement data
        merged_data = pd.merge(decision_data, movement_data, 
                              on=['day', 'agent_id'], how='inner')
        
        if merged_data.empty:
            return self._empty_decision_quality_dict()
        
        # Split by cognitive state
        s1_decisions = merged_data[merged_data['cognitive_state'] == 'S1']
        s2_decisions = merged_data[merged_data['cognitive_state'] == 'S2']
        
        metrics = {}
        
        # Decision timing metrics
        if not s1_decisions.empty:
            s1_timing = self._calculate_timing_metrics(s1_decisions)
            metrics['s1_timing'] = s1_timing
        
        if not s2_decisions.empty:
            s2_timing = self._calculate_timing_metrics(s2_decisions)
            metrics['s2_timing'] = s2_timing
        
        # Decision optimality metrics
        if not s1_decisions.empty and not s2_decisions.empty:
            optimality_comparison = self._compare_decision_optimality(s1_decisions, s2_decisions)
            metrics['optimality_comparison'] = optimality_comparison
        
        return metrics
    
    def _calculate_timing_metrics(self, decision_data: pd.DataFrame) -> Dict:
        """Calculate timing-related metrics for decisions."""
        if decision_data.empty:
            return {}
        
        # Time to first movement
        first_moves = decision_data[decision_data['movement_decision'] == True].groupby('agent_id')['day'].min()
        
        # Decision frequency
        decision_frequency = decision_data.groupby('agent_id').size()
        
        return {
            'mean_time_to_first_move': first_moves.mean() if not first_moves.empty else None,
            'std_time_to_first_move': first_moves.std() if not first_moves.empty else None,
            'mean_decision_frequency': decision_frequency.mean(),
            'std_decision_frequency': decision_frequency.std(),
            'agents_who_moved': len(first_moves),
            'total_agents': decision_data['agent_id'].nunique()
        }
    
    def _compare_decision_optimality(self, s1_data: pd.DataFrame, s2_data: pd.DataFrame) -> Dict:
        """Compare decision optimality between S1 and S2 modes."""
        # Extract decision factors (assuming JSON format)
        s1_factors = self._extract_decision_factors(s1_data)
        s2_factors = self._extract_decision_factors(s2_data)
        
        comparison = {}
        
        # Compare safety considerations
        if 'safety_score' in s1_factors and 'safety_score' in s2_factors:
            comparison['safety_consideration'] = {
                's1_mean_safety': s1_factors['safety_score'].mean(),
                's2_mean_safety': s2_factors['safety_score'].mean(),
                's2_safety_advantage': s2_factors['safety_score'].mean() - s1_factors['safety_score'].mean()
            }
        
        # Compare information usage
        if 'information_sources' in s1_factors and 'information_sources' in s2_factors:
            comparison['information_usage'] = {
                's1_mean_sources': s1_factors['information_sources'].mean(),
                's2_mean_sources': s2_factors['information_sources'].mean(),
                's2_information_advantage': s2_factors['information_sources'].mean() - s1_factors['information_sources'].mean()
            }
        
        return comparison
    
    def _extract_decision_factors(self, decision_data: pd.DataFrame) -> pd.DataFrame:
        """Extract decision factors from JSON strings."""
        factors_list = []
        
        for _, row in decision_data.iterrows():
            try:
                if pd.notna(row['decision_factors']):
                    factors = json.loads(row['decision_factors'])
                    factors['agent_id'] = row['agent_id']
                    factors['day'] = row['day']
                    factors_list.append(factors)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return pd.DataFrame(factors_list) if factors_list else pd.DataFrame()
    
    def calculate_phase_transition_indicators(self, cognitive_data: pd.DataFrame,
                                            conflict_intensity: float,
                                            recovery_period: float,
                                            connectivity_rate: float) -> Dict:
        """
        Calculate indicators of phase transition behavior.
        
        Args:
            cognitive_data: DataFrame with cognitive state data
            conflict_intensity: Experiment conflict intensity
            recovery_period: Experiment recovery period
            connectivity_rate: Experiment connectivity rate
            
        Returns:
            Dictionary with phase transition indicators
        """
        # Calculate cognitive pressure
        cognitive_pressure = (conflict_intensity * connectivity_rate) / (recovery_period / 30.0)
        
        # Get S2 activation metrics
        s2_metrics = self.calculate_s2_activation_metrics(cognitive_data)
        
        # Calculate transition sharpness
        if not cognitive_data.empty:
            daily_s2_rates = cognitive_data.groupby('day')['cognitive_state'].apply(
                lambda x: (x == 'S2').mean()
            )
            
            # Calculate rate of change in S2 activation
            if len(daily_s2_rates) > 1:
                s2_rate_changes = daily_s2_rates.diff().abs()
                max_rate_change = s2_rate_changes.max()
                mean_rate_change = s2_rate_changes.mean()
            else:
                max_rate_change = 0
                mean_rate_change = 0
        else:
            max_rate_change = 0
            mean_rate_change = 0
        
        return {
            'cognitive_pressure': cognitive_pressure,
            's2_activation_rate': s2_metrics['s2_activation_rate'],
            'transition_sharpness': {
                'max_daily_change': max_rate_change,
                'mean_daily_change': mean_rate_change
            },
            'parameter_components': {
                'conflict_intensity': conflict_intensity,
                'recovery_period': recovery_period,
                'connectivity_rate': connectivity_rate
            }
        }
    
    def calculate_experiment_metrics(self, experiment_dir: str) -> Dict:
        """
        Calculate comprehensive metrics for a single H3.1 experiment.
        
        Args:
            experiment_dir: Directory containing experiment output files
            
        Returns:
            Dictionary with all calculated metrics
        """
        metrics = {}
        
        try:
            # Load experiment configuration
            config_file = os.path.join(experiment_dir, 'experiment_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                conflict_intensity = config.get('conflict_intensity', 0.5)
                recovery_period = config.get('recovery_period', 30)
                connectivity_rate = config.get('connectivity_rate', 3.0)
            else:
                # Default values if config not found
                conflict_intensity = 0.5
                recovery_period = 30
                connectivity_rate = 3.0
            
            # Load cognitive state data
            cognitive_file = os.path.join(experiment_dir, 'cognitive_states.csv')
            if os.path.exists(cognitive_file):
                cognitive_data = pd.read_csv(cognitive_file)
                
                # Calculate S2 activation metrics
                s2_metrics = self.calculate_s2_activation_metrics(cognitive_data)
                metrics['s2_activation'] = s2_metrics
                
                # Calculate phase transition indicators
                transition_metrics = self.calculate_phase_transition_indicators(
                    cognitive_data, conflict_intensity, recovery_period, connectivity_rate
                )
                metrics['phase_transition'] = transition_metrics
            
            # Load decision log data
            decision_file = os.path.join(experiment_dir, 'decision_log.csv')
            movement_file = os.path.join(experiment_dir, 'out.csv')  # Standard Flee output
            
            if os.path.exists(decision_file) and os.path.exists(movement_file):
                decision_data = pd.read_csv(decision_file)
                movement_data = pd.read_csv(movement_file)
                
                # Calculate decision quality metrics
                quality_metrics = self.calculate_decision_quality_metrics(decision_data, movement_data)
                metrics['decision_quality'] = quality_metrics
            
            # Add experiment metadata
            metrics['experiment_metadata'] = {
                'experiment_dir': experiment_dir,
                'conflict_intensity': conflict_intensity,
                'recovery_period': recovery_period,
                'connectivity_rate': connectivity_rate,
                'cognitive_pressure': (conflict_intensity * connectivity_rate) / (recovery_period / 30.0)
            }
            
        except Exception as e:
            metrics['error'] = str(e)
            metrics['calculation_successful'] = False
        else:
            metrics['calculation_successful'] = True
        
        return metrics
    
    def _empty_metrics_dict(self) -> Dict:
        """Return empty metrics dictionary for error cases."""
        return {
            'total_decisions': 0,
            's2_decisions': 0,
            's1_decisions': 0,
            's2_activation_rate': 0.0,
            's1_activation_rate': 1.0,
            'temporal_patterns': {},
            'agent_statistics': {}
        }
    
    def _empty_decision_quality_dict(self) -> Dict:
        """Return empty decision quality dictionary for error cases."""
        return {
            's1_timing': {},
            's2_timing': {},
            'optimality_comparison': {}
        }
    
    def aggregate_grid_metrics(self, experiment_results: List[Dict]) -> Dict:
        """
        Aggregate metrics across all parameter grid experiments.
        
        Args:
            experiment_results: List of individual experiment metrics
            
        Returns:
            Dictionary with aggregated grid-level metrics
        """
        if not experiment_results:
            return {'error': 'No experiment results provided'}
        
        # Extract key metrics for aggregation
        cognitive_pressures = []
        s2_activation_rates = []
        successful_experiments = []
        
        for result in experiment_results:
            if result.get('calculation_successful', False):
                successful_experiments.append(result)
                
                if 'phase_transition' in result:
                    cognitive_pressures.append(result['phase_transition']['cognitive_pressure'])
                    s2_activation_rates.append(result['phase_transition']['s2_activation_rate'])
        
        if not successful_experiments:
            return {'error': 'No successful experiments to aggregate'}
        
        # Create summary DataFrame
        summary_data = pd.DataFrame({
            'cognitive_pressure': cognitive_pressures,
            's2_activation_rate': s2_activation_rates
        })
        
        # Add parameter columns
        for param in ['conflict_intensity', 'recovery_period', 'connectivity_rate']:
            param_values = []
            for result in successful_experiments:
                if 'experiment_metadata' in result:
                    param_values.append(result['experiment_metadata'].get(param, 0))
                else:
                    param_values.append(0)
            summary_data[param] = param_values
        
        # Calculate aggregate statistics
        aggregate_metrics = {
            'total_experiments': len(experiment_results),
            'successful_experiments': len(successful_experiments),
            'success_rate': len(successful_experiments) / len(experiment_results),
            'cognitive_pressure_range': {
                'min': min(cognitive_pressures) if cognitive_pressures else 0,
                'max': max(cognitive_pressures) if cognitive_pressures else 0,
                'mean': np.mean(cognitive_pressures) if cognitive_pressures else 0,
                'std': np.std(cognitive_pressures) if cognitive_pressures else 0
            },
            's2_activation_range': {
                'min': min(s2_activation_rates) if s2_activation_rates else 0,
                'max': max(s2_activation_rates) if s2_activation_rates else 0,
                'mean': np.mean(s2_activation_rates) if s2_activation_rates else 0,
                'std': np.std(s2_activation_rates) if s2_activation_rates else 0
            },
            'summary_data': summary_data.to_dict('records')
        }
        
        return aggregate_metrics


def main():
    """Example usage of H3.1 metrics calculation."""
    # Create sample cognitive data
    np.random.seed(42)
    
    n_agents = 50
    n_days = 100
    
    # Generate sample data
    data = []
    for agent_id in range(n_agents):
        for day in range(n_days):
            # Simulate cognitive pressure effect
            cognitive_pressure = 1.5  # Example value
            s2_prob = 0.8 / (1 + np.exp(-3 * (cognitive_pressure - 1.2))) + 0.1
            
            cognitive_state = 'S2' if np.random.random() < s2_prob else 'S1'
            
            data.append({
                'day': day,
                'agent_id': agent_id,
                'cognitive_state': cognitive_state,
                'location': f'Location_{np.random.randint(1, 5)}',
                'decision_factors': json.dumps({
                    'safety_score': np.random.uniform(0.3, 0.9),
                    'information_sources': np.random.randint(1, 5)
                }),
                'movement_decision': np.random.random() < 0.1
            })
    
    cognitive_data = pd.DataFrame(data)
    
    # Calculate metrics
    metrics_calculator = H3_1_Metrics()
    
    # S2 activation metrics
    s2_metrics = metrics_calculator.calculate_s2_activation_metrics(cognitive_data)
    print("S2 Activation Metrics:")
    print(f"  S2 activation rate: {s2_metrics['s2_activation_rate']:.3f}")
    print(f"  Mean agent S2 rate: {s2_metrics['agent_statistics']['mean_agent_s2_rate']:.3f}")
    
    # Phase transition indicators
    transition_metrics = metrics_calculator.calculate_phase_transition_indicators(
        cognitive_data, conflict_intensity=0.7, recovery_period=25, connectivity_rate=4.0
    )
    print(f"\nPhase Transition Indicators:")
    print(f"  Cognitive pressure: {transition_metrics['cognitive_pressure']:.3f}")
    print(f"  S2 activation rate: {transition_metrics['s2_activation_rate']:.3f}")


if __name__ == "__main__":
    main()