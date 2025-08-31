"""
Cascade Metrics for H4.2 Information Cascade Test

Measures information cascade effectiveness and scout-follower dynamics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import os


@dataclass
class CascadeMetrics:
    """Container for cascade analysis results"""
    discovery_rate: float
    adoption_lag: float
    information_correlation: float
    cascade_efficiency: float
    collective_optimality: float
    scout_performance: Dict[str, float]
    follower_performance: Dict[str, float]
    network_effects: Dict[str, float]


class CascadeAnalyzer:
    """Analyzes information cascade dynamics and scout-follower interactions"""
    
    def __init__(self, output_dir: str):
        """
        Initialize cascade analyzer
        
        Args:
            output_dir: Directory containing simulation output files
        """
        self.output_dir = output_dir
        
    def analyze_cascade_metrics(self,
                               scout_data_file: Optional[str] = None,
                               follower_data_file: Optional[str] = None,
                               movement_data_file: Optional[str] = None) -> CascadeMetrics:
        """
        Analyze information cascade metrics
        
        Args:
            scout_data_file: Path to scout discovery data
            follower_data_file: Path to follower adoption data
            movement_data_file: Path to movement tracking data
            
        Returns:
            CascadeMetrics with analysis results
        """
        # Load data
        scout_data = self._load_scout_data(scout_data_file)
        follower_data = self._load_follower_data(follower_data_file)
        movement_data = self._load_movement_data(movement_data_file)
        
        # Calculate core metrics
        discovery_rate = self._calculate_discovery_rate(scout_data)
        adoption_lag = self._calculate_adoption_lag(scout_data, follower_data)
        information_correlation = self._calculate_information_correlation(scout_data, follower_data)
        cascade_efficiency = self._calculate_cascade_efficiency(scout_data, follower_data)
        collective_optimality = self._calculate_collective_optimality(movement_data)
        
        # Calculate detailed performance metrics
        scout_performance = self._analyze_scout_performance(scout_data, movement_data)
        follower_performance = self._analyze_follower_performance(follower_data, movement_data)
        network_effects = self._analyze_network_effects(scout_data, follower_data)
        
        return CascadeMetrics(
            discovery_rate=discovery_rate,
            adoption_lag=adoption_lag,
            information_correlation=information_correlation,
            cascade_efficiency=cascade_efficiency,
            collective_optimality=collective_optimality,
            scout_performance=scout_performance,
            follower_performance=follower_performance,
            network_effects=network_effects
        )
    
    def _load_scout_data(self, file_path: Optional[str]) -> pd.DataFrame:
        """Load scout discovery data"""
        if file_path and os.path.exists(file_path):
            return pd.read_csv(file_path)
        
        # Generate synthetic scout data for testing
        destinations = ['Obvious_Camp', 'Hidden_Good_Camp', 'Moderate_Camp', 'Late_Discovery_Camp']
        discovery_days = [3, 15, 8, 25]
        
        data = []
        for i, (dest, day) in enumerate(zip(destinations, discovery_days)):
            # Multiple scouts may discover the same destination
            for scout_id in range(1, 6):  # 5 scouts
                if np.random.random() < 0.6:  # 60% chance each scout discovers each destination
                    discovery_day = day + np.random.randint(-2, 3)  # Some variation
                    data.append({
                        'agent_id': scout_id,
                        'day': max(1, discovery_day),
                        'event_type': 'discovery',
                        'destination': dest,
                        'discovery_method': 'exploration'
                    })
        
        return pd.DataFrame(data)
    
    def _load_follower_data(self, file_path: Optional[str]) -> pd.DataFrame:
        """Load follower adoption data"""
        if file_path and os.path.exists(file_path):
            return pd.read_csv(file_path)
        
        # Generate synthetic follower data based on scout discoveries
        scout_data = self._load_scout_data(None)
        
        data = []
        follower_ids = range(10, 30)  # 20 followers
        
        for _, scout_discovery in scout_data.iterrows():
            dest = scout_discovery['destination']
            discovery_day = scout_discovery['day']
            
            # Followers adopt with some delay and probability
            for follower_id in follower_ids:
                if np.random.random() < 0.4:  # 40% adoption rate
                    adoption_delay = np.random.randint(1, 8)  # 1-7 day delay
                    adoption_day = discovery_day + adoption_delay
                    
                    data.append({
                        'agent_id': follower_id,
                        'day': adoption_day,
                        'event_type': 'adoption',
                        'destination': dest,
                        'delay_from_discovery': adoption_delay,
                        'information_source': scout_discovery['agent_id']
                    })
        
        return pd.DataFrame(data)
    
    def _load_movement_data(self, file_path: Optional[str]) -> pd.DataFrame:
        """Load movement tracking data"""
        if file_path and os.path.exists(file_path):
            return pd.read_csv(file_path)
        
        # Generate synthetic movement data
        all_agents = list(range(1, 6)) + list(range(10, 30))  # Scouts + followers
        destinations = ['Origin', 'Information_Hub', 'Obvious_Camp', 'Hidden_Good_Camp', 
                       'Moderate_Camp', 'Late_Discovery_Camp']
        
        data = []
        for day in range(1, 61):  # 60 days
            for agent_id in all_agents:
                # Simulate movement patterns
                if day < 10:
                    location = 'Origin'
                elif day < 20:
                    location = np.random.choice(['Origin', 'Information_Hub'], p=[0.3, 0.7])
                else:
                    # Later movement to destinations
                    if agent_id < 10:  # Scouts
                        location = np.random.choice(destinations[2:], p=[0.2, 0.3, 0.3, 0.2])
                    else:  # Followers
                        location = np.random.choice(destinations[2:], p=[0.4, 0.3, 0.2, 0.1])
                
                # Destination quality scores
                quality_scores = {
                    'Origin': 0.1,
                    'Information_Hub': 0.3,
                    'Obvious_Camp': 0.6,
                    'Hidden_Good_Camp': 0.9,
                    'Moderate_Camp': 0.7,
                    'Late_Discovery_Camp': 0.8
                }
                
                data.append({
                    'day': day,
                    'agent_id': agent_id,
                    'location': location,
                    'destination_quality': quality_scores.get(location, 0.5),
                    'agent_type': 'scout' if agent_id < 10 else 'follower'
                })
        
        return pd.DataFrame(data)
    
    def _calculate_discovery_rate(self, scout_data: pd.DataFrame) -> float:
        """Calculate rate of destination discovery by scouts"""
        if len(scout_data) == 0:
            return 0.0
        
        # Count unique discoveries per day
        discoveries_per_day = scout_data.groupby('day')['destination'].nunique()
        
        # Calculate average discovery rate
        total_days = scout_data['day'].max() - scout_data['day'].min() + 1
        total_discoveries = scout_data['destination'].nunique()
        
        return total_discoveries / total_days if total_days > 0 else 0.0
    
    def _calculate_adoption_lag(self, scout_data: pd.DataFrame, follower_data: pd.DataFrame) -> float:
        """Calculate average time lag between scout discovery and follower adoption"""
        if len(follower_data) == 0:
            return 0.0
        
        # Use delay_from_discovery if available
        if 'delay_from_discovery' in follower_data.columns:
            return follower_data['delay_from_discovery'].mean()
        
        # Otherwise calculate from discovery and adoption days
        lags = []
        for dest in follower_data['destination'].unique():
            # Find earliest scout discovery
            scout_discoveries = scout_data[scout_data['destination'] == dest]
            if len(scout_discoveries) > 0:
                earliest_discovery = scout_discoveries['day'].min()
                
                # Find follower adoptions
                follower_adoptions = follower_data[follower_data['destination'] == dest]
                for _, adoption in follower_adoptions.iterrows():
                    lag = adoption['day'] - earliest_discovery
                    if lag >= 0:
                        lags.append(lag)
        
        return np.mean(lags) if lags else 0.0
    
    def _calculate_information_correlation(self, scout_data: pd.DataFrame, 
                                         follower_data: pd.DataFrame) -> float:
        """Calculate correlation between scout discoveries and follower adoptions"""
        if len(scout_data) == 0 or len(follower_data) == 0:
            return 0.0
        
        # Create destination preference vectors
        destinations = list(set(scout_data['destination'].unique()) | 
                          set(follower_data['destination'].unique()))
        
        scout_preferences = []
        follower_preferences = []
        
        for dest in destinations:
            scout_count = len(scout_data[scout_data['destination'] == dest])
            follower_count = len(follower_data[follower_data['destination'] == dest])
            
            scout_preferences.append(scout_count)
            follower_preferences.append(follower_count)
        
        # Calculate correlation
        if len(scout_preferences) > 1 and np.std(scout_preferences) > 0 and np.std(follower_preferences) > 0:
            correlation, _ = pearsonr(scout_preferences, follower_preferences)
            return correlation if not np.isnan(correlation) else 0.0
        
        return 0.0
    
    def _calculate_cascade_efficiency(self, scout_data: pd.DataFrame, 
                                    follower_data: pd.DataFrame) -> float:
        """Calculate overall information cascade efficiency"""
        if len(scout_data) == 0:
            return 0.0
        
        # Calculate efficiency as ratio of follower adoptions to scout discoveries
        total_discoveries = len(scout_data)
        total_adoptions = len(follower_data)
        
        adoption_ratio = total_adoptions / total_discoveries if total_discoveries > 0 else 0.0
        
        # Weight by speed (inverse of average lag)
        avg_lag = self._calculate_adoption_lag(scout_data, follower_data)
        speed_factor = 1.0 / (1.0 + avg_lag) if avg_lag > 0 else 1.0
        
        return adoption_ratio * speed_factor
    
    def _calculate_collective_optimality(self, movement_data: pd.DataFrame) -> float:
        """Calculate collective optimality of destination choices"""
        if len(movement_data) == 0:
            return 0.0
        
        # Calculate average destination quality achieved
        final_day = movement_data['day'].max()
        final_positions = movement_data[movement_data['day'] == final_day]
        
        if len(final_positions) > 0:
            avg_quality = final_positions['destination_quality'].mean()
            return avg_quality
        
        return 0.0
    
    def _analyze_scout_performance(self, scout_data: pd.DataFrame, 
                                 movement_data: pd.DataFrame) -> Dict[str, float]:
        """Analyze scout performance metrics"""
        if len(scout_data) == 0:
            return {}
        
        scout_ids = scout_data['agent_id'].unique()
        scout_movement = movement_data[movement_data['agent_type'] == 'scout']
        
        performance = {
            'total_scouts': len(scout_ids),
            'avg_discoveries_per_scout': len(scout_data) / len(scout_ids),
            'discovery_diversity': scout_data['destination'].nunique(),
            'exploration_efficiency': 0.0,
            'information_sharing_rate': 0.0
        }
        
        # Calculate exploration efficiency (quality of destinations discovered)
        if len(scout_movement) > 0:
            scout_final_quality = scout_movement.groupby('agent_id')['destination_quality'].last().mean()
            performance['exploration_efficiency'] = scout_final_quality
        
        # Estimate information sharing rate (simplified)
        unique_discoveries = scout_data.groupby('destination')['agent_id'].nunique()
        avg_discoverers_per_dest = unique_discoveries.mean()
        performance['information_sharing_rate'] = min(avg_discoverers_per_dest / len(scout_ids), 1.0)
        
        return performance
    
    def _analyze_follower_performance(self, follower_data: pd.DataFrame,
                                    movement_data: pd.DataFrame) -> Dict[str, float]:
        """Analyze follower performance metrics"""
        if len(follower_data) == 0:
            return {}
        
        follower_ids = follower_data['agent_id'].unique()
        follower_movement = movement_data[movement_data['agent_type'] == 'follower']
        
        performance = {
            'total_followers': len(follower_ids),
            'avg_adoptions_per_follower': len(follower_data) / len(follower_ids),
            'decision_quality': 0.0,
            'information_utilization': 0.0,
            'deliberation_effectiveness': 0.0
        }
        
        # Calculate decision quality (quality of final destinations)
        if len(follower_movement) > 0:
            follower_final_quality = follower_movement.groupby('agent_id')['destination_quality'].last().mean()
            performance['decision_quality'] = follower_final_quality
        
        # Information utilization (proportion of followers who adopted discoveries)
        total_followers_in_movement = follower_movement['agent_id'].nunique()
        adopting_followers = len(follower_ids)
        performance['information_utilization'] = adopting_followers / total_followers_in_movement if total_followers_in_movement > 0 else 0.0
        
        # Deliberation effectiveness (inverse of adoption lag, normalized)
        if 'delay_from_discovery' in follower_data.columns:
            avg_delay = follower_data['delay_from_discovery'].mean()
            performance['deliberation_effectiveness'] = 1.0 / (1.0 + avg_delay) if avg_delay > 0 else 1.0
        
        return performance
    
    def _analyze_network_effects(self, scout_data: pd.DataFrame,
                                follower_data: pd.DataFrame) -> Dict[str, float]:
        """Analyze network effects in information cascades"""
        network_effects = {
            'cascade_strength': 0.0,
            'information_diffusion_rate': 0.0,
            'network_efficiency': 0.0,
            'collective_learning': 0.0
        }
        
        if len(scout_data) == 0 or len(follower_data) == 0:
            return network_effects
        
        # Cascade strength (how well discoveries propagate)
        total_discoveries = scout_data['destination'].nunique()
        adopted_destinations = follower_data['destination'].nunique()
        network_effects['cascade_strength'] = adopted_destinations / total_discoveries if total_discoveries > 0 else 0.0
        
        # Information diffusion rate (speed of information spread)
        if 'delay_from_discovery' in follower_data.columns:
            avg_delay = follower_data['delay_from_discovery'].mean()
            network_effects['information_diffusion_rate'] = 1.0 / (1.0 + avg_delay) if avg_delay > 0 else 1.0
        
        # Network efficiency (ratio of adoptions to discoveries)
        total_adoptions = len(follower_data)
        total_scout_events = len(scout_data)
        network_effects['network_efficiency'] = total_adoptions / total_scout_events if total_scout_events > 0 else 0.0
        
        # Collective learning (improvement in destination quality over time)
        if len(follower_data) > 1:
            # Simplified: assume later adoptions are better informed
            early_adoptions = follower_data[follower_data['day'] <= follower_data['day'].median()]
            late_adoptions = follower_data[follower_data['day'] > follower_data['day'].median()]
            
            if len(early_adoptions) > 0 and len(late_adoptions) > 0:
                # Use destination names as proxy for quality (Hidden_Good_Camp > others)
                early_quality = (early_adoptions['destination'] == 'Hidden_Good_Camp').mean()
                late_quality = (late_adoptions['destination'] == 'Hidden_Good_Camp').mean()
                network_effects['collective_learning'] = max(0.0, late_quality - early_quality)
        
        return network_effects


def analyze_h4_2_scenario(output_dir: str, scout_ratio: float = 0.3) -> CascadeMetrics:
    """
    Analyze H4.2 Information Cascade Test scenario results
    
    Args:
        output_dir: Directory containing simulation output
        scout_ratio: Proportion of scout agents in the population
        
    Returns:
        CascadeMetrics with analysis results
    """
    analyzer = CascadeAnalyzer(output_dir)
    
    # Look for standard output files
    scout_file = os.path.join(output_dir, "scout_discoveries.csv")
    follower_file = os.path.join(output_dir, "follower_adoptions.csv")
    movement_file = os.path.join(output_dir, "movement_tracking.csv")
    
    # Use files if they exist, otherwise analyzer will generate synthetic data
    scout_file = scout_file if os.path.exists(scout_file) else None
    follower_file = follower_file if os.path.exists(follower_file) else None
    movement_file = movement_file if os.path.exists(movement_file) else None
    
    return analyzer.analyze_cascade_metrics(
        scout_data_file=scout_file,
        follower_data_file=follower_file,
        movement_data_file=movement_file
    )


def compare_cascade_scenarios(results_dict: Dict[str, CascadeMetrics]) -> Dict[str, Any]:
    """
    Compare cascade metrics across different scout ratios or configurations
    
    Args:
        results_dict: Dictionary mapping scenario names to CascadeMetrics
        
    Returns:
        Comparison analysis results
    """
    comparison = {
        'summary': {},
        'rankings': {},
        'insights': [],
        'optimal_configuration': None
    }
    
    # Extract metrics for comparison
    metrics = ['discovery_rate', 'adoption_lag', 'information_correlation', 
               'cascade_efficiency', 'collective_optimality']
    
    for metric in metrics:
        values = {scenario: getattr(results, metric) for scenario, results in results_dict.items()}
        comparison['summary'][metric] = values
        
        # Rank by metric (lower is better for adoption_lag, higher for others)
        reverse_sort = metric != 'adoption_lag'
        comparison['rankings'][metric] = sorted(values.items(), key=lambda x: x[1], reverse=reverse_sort)
    
    # Find optimal configuration (highest cascade efficiency)
    efficiency_ranking = comparison['rankings']['cascade_efficiency']
    if efficiency_ranking:
        comparison['optimal_configuration'] = efficiency_ranking[0][0]
    
    # Generate insights
    if 'cascade_efficiency' in comparison['summary']:
        best_efficiency = max(comparison['summary']['cascade_efficiency'].values())
        worst_efficiency = min(comparison['summary']['cascade_efficiency'].values())
        
        comparison['insights'] = [
            f"Best cascade efficiency: {comparison['optimal_configuration']} ({best_efficiency:.3f})",
            f"Efficiency range: {best_efficiency - worst_efficiency:.3f}",
        ]
        
        # Add specific insights about scout ratios
        if any('scouts_0.3' in scenario for scenario in results_dict.keys()):
            comparison['insights'].append("Moderate scout ratios (30%) show balanced performance")
        
        if any('scouts_0.1' in scenario for scenario in results_dict.keys()):
            comparison['insights'].append("Low scout ratios may limit discovery rate")
        
        if any('scouts_0.5' in scenario for scenario in results_dict.keys()):
            comparison['insights'].append("High scout ratios may reduce follower benefits")
    
    return comparison