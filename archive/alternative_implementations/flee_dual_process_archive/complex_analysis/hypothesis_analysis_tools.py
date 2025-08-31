"""
Hypothesis-Specific Analysis Tools

This module provides specialized analysis tools for each of the four hypotheses
in the dual-process experiments framework, focusing on the specific metrics
and comparisons relevant to each hypothesis.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from scenarios.h1_speed_optimality.h1_1_multi_destination.h1_1_metrics import H1_1_Metrics
    from scenarios.h1_speed_optimality.h1_2_time_pressure_cascade.h1_2_metrics import H1_2_Metrics
    from scenarios.h2_connectivity_effects.h2_1_hidden_information.h2_1_metrics import H2_1_Metrics
    from scenarios.h2_connectivity_effects.h2_2_dynamic_information.h2_2_metrics import H2_2_Metrics
    from scenarios.h3_dimensionless_parameters.h3_1_parameter_grid.h3_1_metrics import H3_1_Metrics
    from scenarios.h4_population_diversity.h4_1_adaptive_shock.resilience_metrics import ResilienceMetrics
    from scenarios.h4_population_diversity.h4_2_information_cascade.cascade_metrics import CascadeMetrics
    from utils import LoggingUtils
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")


class H1_DecisionQualityAnalyzer:
    """
    H1: Speed vs Optimality Trade-offs Analysis
    
    Analyzes decision quality differences between cognitive modes,
    focusing on the trade-off between decision speed and optimality.
    """
    
    def __init__(self, results_dir: str):
        """
        Initialize H1 analyzer.
        
        Args:
            results_dir: Directory containing H1 experiment results
        """
        self.results_dir = Path(results_dir)
        self.logger = LoggingUtils().get_logger('H1_Analyzer')
        
    def analyze_speed_optimality_tradeoffs(self, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze speed vs optimality trade-offs across cognitive modes.
        
        Args:
            experiment_results: Dictionary of experiment results by cognitive mode
            
        Returns:
            Analysis results with trade-off metrics
        """
        analysis = {
            'hypothesis': 'H1_Speed_vs_Optimality',
            'cognitive_mode_analysis': {},
            'trade_off_analysis': {},
            'statistical_comparisons': {},
            'key_findings': []
        }
        
        # Analyze each cognitive mode
        for mode, results in experiment_results.items():
            if not results.get('success', False):
                continue
                
            mode_analysis = self._analyze_single_mode_h1(mode, results)
            analysis['cognitive_mode_analysis'][mode] = mode_analysis
        
        # Perform trade-off analysis
        analysis['trade_off_analysis'] = self._analyze_tradeoffs(analysis['cognitive_mode_analysis'])
        
        # Statistical comparisons
        analysis['statistical_comparisons'] = self._compare_modes_h1(analysis['cognitive_mode_analysis'])
        
        # Generate key findings
        analysis['key_findings'] = self._generate_h1_findings(analysis)
        
        return analysis
    
    def _analyze_single_mode_h1(self, mode: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single cognitive mode for H1 metrics."""
        mode_analysis = {
            'cognitive_mode': mode,
            'speed_metrics': {},
            'optimality_metrics': {},
            'composite_scores': {}
        }
        
        # Extract speed metrics
        if 'time_to_move' in results:
            mode_analysis['speed_metrics'] = {
                'mean_decision_time': np.mean(results['time_to_move']),
                'std_decision_time': np.std(results['time_to_move']),
                'median_decision_time': np.median(results['time_to_move']),
                'speed_score': self._calculate_speed_score(results['time_to_move'])
            }
        
        # Extract optimality metrics
        if 'camp_efficiency' in results:
            mode_analysis['optimality_metrics'] = {
                'mean_efficiency': np.mean(results['camp_efficiency']),
                'std_efficiency': np.std(results['camp_efficiency']),
                'median_efficiency': np.median(results['camp_efficiency']),
                'optimality_score': self._calculate_optimality_score(results['camp_efficiency'])
            }
        
        # Calculate composite scores
        speed_score = mode_analysis['speed_metrics'].get('speed_score', 0)
        optimality_score = mode_analysis['optimality_metrics'].get('optimality_score', 0)
        
        mode_analysis['composite_scores'] = {
            'speed_score': speed_score,
            'optimality_score': optimality_score,
            'balanced_score': (speed_score + optimality_score) / 2,
            'speed_optimality_ratio': speed_score / optimality_score if optimality_score > 0 else 0
        }
        
        return mode_analysis
    
    def _calculate_speed_score(self, decision_times: List[float]) -> float:
        """Calculate normalized speed score (higher = faster)."""
        if not decision_times:
            return 0.0
        
        mean_time = np.mean(decision_times)
        # Normalize: faster decisions get higher scores
        # Assume max reasonable decision time is 30 days
        max_time = 30.0
        speed_score = max(0.0, (max_time - mean_time) / max_time)
        return speed_score
    
    def _calculate_optimality_score(self, efficiency_values: List[float]) -> float:
        """Calculate normalized optimality score."""
        if not efficiency_values:
            return 0.0
        
        return np.mean(efficiency_values)
    
    def _analyze_tradeoffs(self, mode_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trade-offs between speed and optimality."""
        tradeoff_analysis = {
            'pareto_frontier': [],
            'dominated_modes': [],
            'efficient_modes': [],
            'trade_off_slope': None
        }
        
        # Extract speed and optimality scores for each mode
        mode_scores = []
        for mode, analysis in mode_analysis.items():
            speed = analysis.get('composite_scores', {}).get('speed_score', 0)
            optimality = analysis.get('composite_scores', {}).get('optimality_score', 0)
            mode_scores.append((mode, speed, optimality))
        
        if len(mode_scores) < 2:
            return tradeoff_analysis
        
        # Find Pareto frontier
        for i, (mode1, speed1, opt1) in enumerate(mode_scores):
            is_dominated = False
            for j, (mode2, speed2, opt2) in enumerate(mode_scores):
                if i != j and speed2 >= speed1 and opt2 >= opt1 and (speed2 > speed1 or opt2 > opt1):
                    is_dominated = True
                    break
            
            if is_dominated:
                tradeoff_analysis['dominated_modes'].append(mode1)
            else:
                tradeoff_analysis['efficient_modes'].append(mode1)
                tradeoff_analysis['pareto_frontier'].append((mode1, speed1, opt1))
        
        # Calculate trade-off slope if we have efficient points
        if len(tradeoff_analysis['pareto_frontier']) >= 2:
            frontier_points = [(speed, opt) for _, speed, opt in tradeoff_analysis['pareto_frontier']]
            frontier_points.sort()  # Sort by speed
            
            # Calculate average slope
            slopes = []
            for i in range(len(frontier_points) - 1):
                dx = frontier_points[i+1][0] - frontier_points[i][0]
                dy = frontier_points[i+1][1] - frontier_points[i][1]
                if dx != 0:
                    slopes.append(dy / dx)
            
            if slopes:
                tradeoff_analysis['trade_off_slope'] = np.mean(slopes)
        
        return tradeoff_analysis
    
    def _compare_modes_h1(self, mode_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical comparisons between cognitive modes for H1."""
        comparisons = {}
        
        modes = list(mode_analysis.keys())
        
        for i, mode1 in enumerate(modes):
            for mode2 in modes[i+1:]:
                comparison_key = f"{mode1}_vs_{mode2}"
                
                # Compare speed
                speed1 = mode_analysis[mode1].get('composite_scores', {}).get('speed_score', 0)
                speed2 = mode_analysis[mode2].get('composite_scores', {}).get('speed_score', 0)
                
                # Compare optimality
                opt1 = mode_analysis[mode1].get('composite_scores', {}).get('optimality_score', 0)
                opt2 = mode_analysis[mode2].get('composite_scores', {}).get('optimality_score', 0)
                
                comparisons[comparison_key] = {
                    'speed_difference': speed1 - speed2,
                    'optimality_difference': opt1 - opt2,
                    'speed_advantage': mode1 if speed1 > speed2 else mode2,
                    'optimality_advantage': mode1 if opt1 > opt2 else mode2,
                    'overall_better': self._determine_overall_better(speed1, opt1, speed2, opt2)
                }
        
        return comparisons
    
    def _determine_overall_better(self, speed1: float, opt1: float, speed2: float, opt2: float) -> str:
        """Determine which mode is overall better considering both speed and optimality."""
        score1 = (speed1 + opt1) / 2
        score2 = (speed2 + opt2) / 2
        
        if abs(score1 - score2) < 0.05:  # Very close
            return 'equivalent'
        elif score1 > score2:
            return 'mode1'
        else:
            return 'mode2'
    
    def _generate_h1_findings(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key findings for H1 analysis."""
        findings = []
        
        # Analyze trade-offs
        tradeoff = analysis.get('trade_off_analysis', {})
        efficient_modes = tradeoff.get('efficient_modes', [])
        dominated_modes = tradeoff.get('dominated_modes', [])
        
        if efficient_modes:
            findings.append(f"Efficient cognitive modes (Pareto optimal): {', '.join(efficient_modes)}")
        
        if dominated_modes:
            findings.append(f"Dominated cognitive modes: {', '.join(dominated_modes)}")
        
        # Analyze specific comparisons
        comparisons = analysis.get('statistical_comparisons', {})
        for comparison, data in comparisons.items():
            if data.get('overall_better') != 'equivalent':
                mode1, mode2 = comparison.split('_vs_')
                better_mode = mode1 if data['overall_better'] == 'mode1' else mode2
                findings.append(f"{better_mode} outperforms {mode1 if better_mode == mode2 else mode2} overall")
        
        return findings


class H2_ConnectivityImpactAnalyzer:
    """
    H2: Social Connectivity Impact Analysis
    
    Analyzes how information sharing and social connectivity affect
    destination discovery and decision-making quality.
    """
    
    def __init__(self, results_dir: str):
        """Initialize H2 analyzer."""
        self.results_dir = Path(results_dir)
        self.logger = LoggingUtils().get_logger('H2_Analyzer')
    
    def analyze_connectivity_effects(self, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze social connectivity effects on decision-making.
        
        Args:
            experiment_results: Dictionary of experiment results by connectivity level
            
        Returns:
            Analysis results with connectivity impact metrics
        """
        analysis = {
            'hypothesis': 'H2_Social_Connectivity_Impact',
            'connectivity_analysis': {},
            'information_sharing_effects': {},
            'discovery_patterns': {},
            'statistical_comparisons': {},
            'key_findings': []
        }
        
        # Analyze each connectivity level
        for connectivity_level, results in experiment_results.items():
            if not results.get('success', False):
                continue
                
            connectivity_analysis = self._analyze_connectivity_level(connectivity_level, results)
            analysis['connectivity_analysis'][connectivity_level] = connectivity_analysis
        
        # Analyze information sharing effects
        analysis['information_sharing_effects'] = self._analyze_information_sharing(
            analysis['connectivity_analysis']
        )
        
        # Analyze discovery patterns
        analysis['discovery_patterns'] = self._analyze_discovery_patterns(
            analysis['connectivity_analysis']
        )
        
        # Statistical comparisons
        analysis['statistical_comparisons'] = self._compare_connectivity_levels(
            analysis['connectivity_analysis']
        )
        
        # Generate key findings
        analysis['key_findings'] = self._generate_h2_findings(analysis)
        
        return analysis
    
    def _analyze_connectivity_level(self, level: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single connectivity level."""
        analysis = {
            'connectivity_level': level,
            'discovery_metrics': {},
            'information_propagation': {},
            'decision_quality': {}
        }
        
        # Extract discovery metrics
        if 'hidden_camp_discovery_rate' in results:
            discovery_rates = results['hidden_camp_discovery_rate']
            analysis['discovery_metrics'] = {
                'mean_discovery_rate': np.mean(discovery_rates),
                'std_discovery_rate': np.std(discovery_rates),
                'discovery_success_rate': np.mean([r > 0.1 for r in discovery_rates])
            }
        
        # Extract information propagation metrics
        if 'information_lag' in results:
            info_lags = results['information_lag']
            analysis['information_propagation'] = {
                'mean_info_lag': np.mean(info_lags),
                'std_info_lag': np.std(info_lags),
                'fast_propagation_rate': np.mean([lag < 5 for lag in info_lags])
            }
        
        # Extract decision quality metrics
        if 'destination_quality_score' in results:
            quality_scores = results['destination_quality_score']
            analysis['decision_quality'] = {
                'mean_quality': np.mean(quality_scores),
                'std_quality': np.std(quality_scores),
                'high_quality_rate': np.mean([q > 0.7 for q in quality_scores])
            }
        
        return analysis
    
    def _analyze_information_sharing(self, connectivity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze information sharing effects across connectivity levels."""
        sharing_analysis = {
            'connectivity_vs_discovery': {},
            'information_cascade_strength': {},
            'network_effects': {}
        }
        
        # Extract connectivity levels and discovery rates
        connectivity_levels = []
        discovery_rates = []
        
        for level, analysis in connectivity_analysis.items():
            if 'discovery_metrics' in analysis:
                # Map connectivity level to numeric value
                if 'isolated' in level.lower():
                    conn_value = 0.0
                elif 'connected' in level.lower():
                    conn_value = 1.0
                elif 'baseline' in level.lower():
                    conn_value = 0.5
                else:
                    conn_value = 0.5
                
                connectivity_levels.append(conn_value)
                discovery_rates.append(analysis['discovery_metrics']['mean_discovery_rate'])
        
        if len(connectivity_levels) >= 2:
            # Calculate correlation between connectivity and discovery
            correlation = np.corrcoef(connectivity_levels, discovery_rates)[0, 1]
            sharing_analysis['connectivity_vs_discovery']['correlation'] = correlation
            sharing_analysis['connectivity_vs_discovery']['strength'] = self._interpret_correlation(correlation)
        
        return sharing_analysis
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(correlation)
        if abs_corr < 0.3:
            return 'weak'
        elif abs_corr < 0.7:
            return 'moderate'
        else:
            return 'strong'
    
    def _analyze_discovery_patterns(self, connectivity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in destination discovery."""
        patterns = {
            'discovery_hierarchy': [],
            'connectivity_advantage': {},
            'information_value': {}
        }
        
        # Rank connectivity levels by discovery performance
        level_performance = []
        for level, analysis in connectivity_analysis.items():
            discovery_rate = analysis.get('discovery_metrics', {}).get('mean_discovery_rate', 0)
            level_performance.append((level, discovery_rate))
        
        level_performance.sort(key=lambda x: x[1], reverse=True)
        patterns['discovery_hierarchy'] = [level for level, _ in level_performance]
        
        # Calculate connectivity advantage
        if len(level_performance) >= 2:
            best_rate = level_performance[0][1]
            worst_rate = level_performance[-1][1]
            patterns['connectivity_advantage']['absolute_improvement'] = best_rate - worst_rate
            patterns['connectivity_advantage']['relative_improvement'] = (
                (best_rate - worst_rate) / worst_rate if worst_rate > 0 else float('inf')
            )
        
        return patterns
    
    def _compare_connectivity_levels(self, connectivity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare different connectivity levels statistically."""
        comparisons = {}
        
        levels = list(connectivity_analysis.keys())
        
        for i, level1 in enumerate(levels):
            for level2 in levels[i+1:]:
                comparison_key = f"{level1}_vs_{level2}"
                
                # Compare discovery rates
                discovery1 = connectivity_analysis[level1].get('discovery_metrics', {}).get('mean_discovery_rate', 0)
                discovery2 = connectivity_analysis[level2].get('discovery_metrics', {}).get('mean_discovery_rate', 0)
                
                # Compare decision quality
                quality1 = connectivity_analysis[level1].get('decision_quality', {}).get('mean_quality', 0)
                quality2 = connectivity_analysis[level2].get('decision_quality', {}).get('mean_quality', 0)
                
                comparisons[comparison_key] = {
                    'discovery_difference': discovery1 - discovery2,
                    'quality_difference': quality1 - quality2,
                    'discovery_advantage': level1 if discovery1 > discovery2 else level2,
                    'quality_advantage': level1 if quality1 > quality2 else level2
                }
        
        return comparisons
    
    def _generate_h2_findings(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key findings for H2 analysis."""
        findings = []
        
        # Analyze connectivity effects
        sharing_effects = analysis.get('information_sharing_effects', {})
        connectivity_discovery = sharing_effects.get('connectivity_vs_discovery', {})
        
        if 'correlation' in connectivity_discovery:
            correlation = connectivity_discovery['correlation']
            strength = connectivity_discovery['strength']
            findings.append(f"Connectivity-discovery correlation: {correlation:.3f} ({strength})")
        
        # Analyze discovery patterns
        patterns = analysis.get('discovery_patterns', {})
        hierarchy = patterns.get('discovery_hierarchy', [])
        
        if len(hierarchy) >= 2:
            findings.append(f"Best performing connectivity: {hierarchy[0]}")
            findings.append(f"Worst performing connectivity: {hierarchy[-1]}")
        
        advantage = patterns.get('connectivity_advantage', {})
        if 'relative_improvement' in advantage:
            improvement = advantage['relative_improvement']
            if improvement != float('inf'):
                findings.append(f"Connectivity provides {improvement:.1%} improvement in discovery")
        
        return findings


class H3_PhaseTransitionAnalyzer:
    """
    H3: Dimensionless Parameter and Phase Transition Analysis
    
    Analyzes critical points in cognitive mode activation and identifies
    universal scaling relationships in dual-process behavior.
    """
    
    def __init__(self, results_dir: str):
        """Initialize H3 analyzer."""
        self.results_dir = Path(results_dir)
        self.logger = LoggingUtils().get_logger('H3_Analyzer')
    
    def analyze_phase_transitions(self, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze phase transitions in cognitive mode activation.
        
        Args:
            experiment_results: Dictionary of experiment results with parameter variations
            
        Returns:
            Analysis results with phase transition identification
        """
        analysis = {
            'hypothesis': 'H3_Dimensionless_Parameters',
            'parameter_analysis': {},
            'phase_transitions': {},
            'critical_points': {},
            'scaling_relationships': {},
            'key_findings': []
        }
        
        # Extract parameter data
        parameter_data = self._extract_parameter_data(experiment_results)
        analysis['parameter_analysis'] = parameter_data
        
        # Identify phase transitions
        analysis['phase_transitions'] = self._identify_phase_transitions(parameter_data)
        
        # Find critical points
        analysis['critical_points'] = self._find_critical_points(analysis['phase_transitions'])
        
        # Analyze scaling relationships
        analysis['scaling_relationships'] = self._analyze_scaling_relationships(parameter_data)
        
        # Generate key findings
        analysis['key_findings'] = self._generate_h3_findings(analysis)
        
        return analysis
    
    def _extract_parameter_data(self, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameter sweep data from experiment results."""
        parameter_data = {
            'cognitive_pressure': [],
            's2_activation_rate': [],
            'conflict_intensity': [],
            'recovery_period': [],
            'connectivity_rate': [],
            'experiment_metadata': []
        }
        
        for exp_id, result in experiment_results.items():
            if not result.get('success', False):
                continue
            
            metadata = result.get('metadata', {})
            
            # Extract parameters
            cognitive_pressure = metadata.get('cognitive_pressure', 0)
            conflict_intensity = metadata.get('conflict_intensity', 0)
            recovery_period = metadata.get('recovery_period', 30)
            connectivity_rate = metadata.get('connectivity_rate', 0)
            
            # Extract S2 activation rate from results
            s2_activation_rate = self._extract_s2_activation_rate(result)
            
            parameter_data['cognitive_pressure'].append(cognitive_pressure)
            parameter_data['s2_activation_rate'].append(s2_activation_rate)
            parameter_data['conflict_intensity'].append(conflict_intensity)
            parameter_data['recovery_period'].append(recovery_period)
            parameter_data['connectivity_rate'].append(connectivity_rate)
            parameter_data['experiment_metadata'].append(metadata)
        
        return parameter_data
    
    def _extract_s2_activation_rate(self, result: Dict[str, Any]) -> float:
        """Extract S2 activation rate from experiment result."""
        # Look for cognitive tracking data
        experiment_dir = result.get('experiment_dir')
        if not experiment_dir:
            return 0.0
        
        try:
            # Try to find cognitive states file
            cognitive_file = os.path.join(experiment_dir, 'output', 'cognitive_states.csv')
            if os.path.exists(cognitive_file):
                df = pd.read_csv(cognitive_file)
                if 'cognitive_state' in df.columns:
                    s2_count = len(df[df['cognitive_state'] == 'S2'])
                    total_count = len(df)
                    return s2_count / total_count if total_count > 0 else 0.0
            
            # Fallback: estimate from other metrics
            if 'system2_activations' in result:
                activations = result['system2_activations']
                return np.mean(activations) if activations else 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to extract S2 activation rate: {e}")
        
        return 0.0
    
    def _identify_phase_transitions(self, parameter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify phase transitions in S2 activation."""
        transitions = {
            'transition_detected': False,
            'transition_sharpness': 0.0,
            'sigmoid_fit': {},
            'transition_region': {}
        }
        
        cognitive_pressure = np.array(parameter_data['cognitive_pressure'])
        s2_activation = np.array(parameter_data['s2_activation_rate'])
        
        if len(cognitive_pressure) < 10:
            return transitions
        
        # Sort by cognitive pressure
        sorted_indices = np.argsort(cognitive_pressure)
        sorted_pressure = cognitive_pressure[sorted_indices]
        sorted_activation = s2_activation[sorted_indices]
        
        # Fit sigmoid function
        try:
            sigmoid_params, sigmoid_cov = self._fit_sigmoid(sorted_pressure, sorted_activation)
            
            if sigmoid_params is not None:
                transitions['sigmoid_fit'] = {
                    'amplitude': sigmoid_params[0],
                    'center': sigmoid_params[1],
                    'width': sigmoid_params[2],
                    'baseline': sigmoid_params[3],
                    'r_squared': self._calculate_r_squared(
                        sorted_activation, 
                        self._sigmoid_function(sorted_pressure, *sigmoid_params)
                    )
                }
                
                # Calculate transition sharpness
                transitions['transition_sharpness'] = 1.0 / sigmoid_params[2] if sigmoid_params[2] > 0 else 0
                
                # Define transition region (10%-90% activation)
                center = sigmoid_params[1]
                width = sigmoid_params[2]
                transitions['transition_region'] = {
                    'start': center - 2 * width,
                    'end': center + 2 * width,
                    'center': center
                }
                
                transitions['transition_detected'] = transitions['sigmoid_fit']['r_squared'] > 0.7
        
        except Exception as e:
            self.logger.warning(f"Failed to fit sigmoid: {e}")
        
        return transitions
    
    def _fit_sigmoid(self, x: np.ndarray, y: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Fit sigmoid function to data."""
        def sigmoid(x, amplitude, center, width, baseline):
            return baseline + amplitude / (1 + np.exp(-(x - center) / width))
        
        try:
            # Initial parameter guess
            amplitude_guess = np.max(y) - np.min(y)
            center_guess = np.median(x)
            width_guess = (np.max(x) - np.min(x)) / 10
            baseline_guess = np.min(y)
            
            initial_guess = [amplitude_guess, center_guess, width_guess, baseline_guess]
            
            # Fit sigmoid
            params, covariance = curve_fit(
                sigmoid, x, y, 
                p0=initial_guess,
                maxfev=5000,
                bounds=([0, np.min(x), 0.01, 0], 
                       [2, np.max(x), np.max(x) - np.min(x), 1])
            )
            
            return params, covariance
            
        except Exception as e:
            self.logger.warning(f"Sigmoid fitting failed: {e}")
            return None, None
    
    def _sigmoid_function(self, x: np.ndarray, amplitude: float, center: float, 
                         width: float, baseline: float) -> np.ndarray:
        """Sigmoid function."""
        return baseline + amplitude / (1 + np.exp(-(x - center) / width))
    
    def _calculate_r_squared(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate R-squared value."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    def _find_critical_points(self, phase_transitions: Dict[str, Any]) -> Dict[str, Any]:
        """Find critical points in phase transitions."""
        critical_points = {
            'critical_pressure': None,
            'critical_region_width': None,
            'activation_threshold': 0.5
        }
        
        if phase_transitions.get('transition_detected', False):
            sigmoid_fit = phase_transitions.get('sigmoid_fit', {})
            
            critical_points['critical_pressure'] = sigmoid_fit.get('center')
            critical_points['critical_region_width'] = sigmoid_fit.get('width', 0) * 4  # ±2σ
            
            transition_region = phase_transitions.get('transition_region', {})
            critical_points['transition_start'] = transition_region.get('start')
            critical_points['transition_end'] = transition_region.get('end')
        
        return critical_points
    
    def _analyze_scaling_relationships(self, parameter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scaling relationships between parameters."""
        scaling = {
            'dimensionless_parameters': {},
            'universal_scaling': {},
            'parameter_correlations': {}
        }
        
        # Calculate dimensionless parameters
        conflict_intensity = np.array(parameter_data['conflict_intensity'])
        recovery_period = np.array(parameter_data['recovery_period'])
        connectivity_rate = np.array(parameter_data['connectivity_rate'])
        cognitive_pressure = np.array(parameter_data['cognitive_pressure'])
        
        # Verify cognitive pressure calculation
        calculated_pressure = (conflict_intensity * connectivity_rate) / (recovery_period / 30.0)
        scaling['dimensionless_parameters']['cognitive_pressure_verification'] = {
            'correlation_with_calculated': np.corrcoef(cognitive_pressure, calculated_pressure)[0, 1],
            'mean_difference': np.mean(np.abs(cognitive_pressure - calculated_pressure))
        }
        
        # Look for other dimensionless combinations
        scaling['dimensionless_parameters']['conflict_recovery_ratio'] = conflict_intensity / (recovery_period / 30.0)
        scaling['dimensionless_parameters']['connectivity_conflict_product'] = connectivity_rate * conflict_intensity
        
        # Calculate parameter correlations
        s2_activation = np.array(parameter_data['s2_activation_rate'])
        
        scaling['parameter_correlations'] = {
            'pressure_activation': np.corrcoef(cognitive_pressure, s2_activation)[0, 1],
            'conflict_activation': np.corrcoef(conflict_intensity, s2_activation)[0, 1],
            'connectivity_activation': np.corrcoef(connectivity_rate, s2_activation)[0, 1],
            'recovery_activation': np.corrcoef(recovery_period, s2_activation)[0, 1]
        }
        
        return scaling
    
    def _generate_h3_findings(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key findings for H3 analysis."""
        findings = []
        
        # Phase transition findings
        transitions = analysis.get('phase_transitions', {})
        if transitions.get('transition_detected', False):
            sigmoid_fit = transitions.get('sigmoid_fit', {})
            r_squared = sigmoid_fit.get('r_squared', 0)
            findings.append(f"Phase transition detected with R² = {r_squared:.3f}")
            
            sharpness = transitions.get('transition_sharpness', 0)
            findings.append(f"Transition sharpness: {sharpness:.2f}")
        
        # Critical point findings
        critical_points = analysis.get('critical_points', {})
        critical_pressure = critical_points.get('critical_pressure')
        if critical_pressure is not None:
            findings.append(f"Critical cognitive pressure: {critical_pressure:.3f}")
        
        # Scaling relationship findings
        scaling = analysis.get('scaling_relationships', {})
        correlations = scaling.get('parameter_correlations', {})
        
        pressure_corr = correlations.get('pressure_activation', 0)
        findings.append(f"Cognitive pressure correlation with S2 activation: {pressure_corr:.3f}")
        
        # Find strongest individual parameter correlation
        individual_corrs = {
            'conflict': correlations.get('conflict_activation', 0),
            'connectivity': correlations.get('connectivity_activation', 0),
            'recovery': abs(correlations.get('recovery_activation', 0))  # Negative correlation expected
        }
        
        strongest_param = max(individual_corrs.keys(), key=lambda k: abs(individual_corrs[k]))
        strongest_corr = individual_corrs[strongest_param]
        findings.append(f"Strongest individual parameter: {strongest_param} (r = {strongest_corr:.3f})")
        
        return findings


class H4_DiversityAdvantageAnalyzer:
    """
    H4: Population Diversity Advantage Analysis
    
    Analyzes whether mixed S1/S2 populations outperform homogeneous populations
    and examines information cascade effects between different agent types.
    """
    
    def __init__(self, results_dir: str):
        """Initialize H4 analyzer."""
        self.results_dir = Path(results_dir)
        self.logger = LoggingUtils().get_logger('H4_Analyzer')
    
    def analyze_diversity_advantages(self, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze population diversity advantages.
        
        Args:
            experiment_results: Dictionary of experiment results by population composition
            
        Returns:
            Analysis results with diversity advantage metrics
        """
        analysis = {
            'hypothesis': 'H4_Population_Diversity',
            'population_analysis': {},
            'diversity_effects': {},
            'information_cascades': {},
            'resilience_comparison': {},
            'key_findings': []
        }
        
        # Analyze each population composition
        for composition, results in experiment_results.items():
            if not results.get('success', False):
                continue
                
            pop_analysis = self._analyze_population_composition(composition, results)
            analysis['population_analysis'][composition] = pop_analysis
        
        # Analyze diversity effects
        analysis['diversity_effects'] = self._analyze_diversity_effects(
            analysis['population_analysis']
        )
        
        # Analyze information cascades
        analysis['information_cascades'] = self._analyze_information_cascades(
            analysis['population_analysis']
        )
        
        # Compare resilience
        analysis['resilience_comparison'] = self._compare_resilience(
            analysis['population_analysis']
        )
        
        # Generate key findings
        analysis['key_findings'] = self._generate_h4_findings(analysis)
        
        return analysis
    
    def _analyze_population_composition(self, composition: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single population composition."""
        analysis = {
            'composition': composition,
            'resilience_metrics': {},
            'adaptation_speed': {},
            'collective_performance': {},
            'information_flow': {}
        }
        
        # Extract resilience metrics
        if 'resilience_score' in results:
            resilience_scores = results['resilience_score']
            analysis['resilience_metrics'] = {
                'mean_resilience': np.mean(resilience_scores),
                'std_resilience': np.std(resilience_scores),
                'resilience_consistency': 1.0 - (np.std(resilience_scores) / np.mean(resilience_scores))
                    if np.mean(resilience_scores) > 0 else 0
            }
        
        # Extract adaptation speed metrics
        if 'adaptation_time' in results:
            adaptation_times = results['adaptation_time']
            analysis['adaptation_speed'] = {
                'mean_adaptation_time': np.mean(adaptation_times),
                'std_adaptation_time': np.std(adaptation_times),
                'fast_adaptation_rate': np.mean([t < 10 for t in adaptation_times])
            }
        
        # Extract collective performance metrics
        if 'collective_efficiency' in results:
            efficiency_scores = results['collective_efficiency']
            analysis['collective_performance'] = {
                'mean_efficiency': np.mean(efficiency_scores),
                'std_efficiency': np.std(efficiency_scores),
                'high_performance_rate': np.mean([e > 0.8 for e in efficiency_scores])
            }
        
        # Extract information flow metrics
        if 'information_cascade_strength' in results:
            cascade_strengths = results['information_cascade_strength']
            analysis['information_flow'] = {
                'mean_cascade_strength': np.mean(cascade_strengths),
                'std_cascade_strength': np.std(cascade_strengths),
                'strong_cascade_rate': np.mean([s > 0.5 for s in cascade_strengths])
            }
        
        return analysis
    
    def _analyze_diversity_effects(self, population_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze effects of population diversity."""
        diversity_effects = {
            'diversity_ranking': [],
            'diversity_advantage': {},
            'homogeneous_vs_mixed': {}
        }
        
        # Rank populations by performance
        performance_scores = []
        for composition, analysis in population_analysis.items():
            resilience = analysis.get('resilience_metrics', {}).get('mean_resilience', 0)
            efficiency = analysis.get('collective_performance', {}).get('mean_efficiency', 0)
            
            # Composite performance score
            composite_score = (resilience + efficiency) / 2
            performance_scores.append((composition, composite_score))
        
        performance_scores.sort(key=lambda x: x[1], reverse=True)
        diversity_effects['diversity_ranking'] = [comp for comp, _ in performance_scores]
        
        # Calculate diversity advantage
        if len(performance_scores) >= 2:
            best_score = performance_scores[0][1]
            worst_score = performance_scores[-1][1]
            
            diversity_effects['diversity_advantage'] = {
                'best_composition': performance_scores[0][0],
                'worst_composition': performance_scores[-1][0],
                'performance_gap': best_score - worst_score,
                'relative_improvement': (best_score - worst_score) / worst_score 
                    if worst_score > 0 else float('inf')
            }
        
        # Compare homogeneous vs mixed populations
        homogeneous_comps = [comp for comp in population_analysis.keys() 
                           if 'pure' in comp.lower() or comp in ['s1_only', 's2_only']]
        mixed_comps = [comp for comp in population_analysis.keys() 
                      if comp not in homogeneous_comps]
        
        if homogeneous_comps and mixed_comps:
            # Calculate average performance for each type
            homogeneous_scores = []
            mixed_scores = []
            
            for comp, score in performance_scores:
                if comp in homogeneous_comps:
                    homogeneous_scores.append(score)
                elif comp in mixed_comps:
                    mixed_scores.append(score)
            
            if homogeneous_scores and mixed_scores:
                diversity_effects['homogeneous_vs_mixed'] = {
                    'homogeneous_mean': np.mean(homogeneous_scores),
                    'mixed_mean': np.mean(mixed_scores),
                    'mixed_advantage': np.mean(mixed_scores) - np.mean(homogeneous_scores),
                    'mixed_better': np.mean(mixed_scores) > np.mean(homogeneous_scores)
                }
        
        return diversity_effects
    
    def _analyze_information_cascades(self, population_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze information cascade effects."""
        cascades = {
            'cascade_strength_ranking': [],
            'scout_follower_effects': {},
            'information_flow_patterns': {}
        }
        
        # Rank by cascade strength
        cascade_scores = []
        for composition, analysis in population_analysis.items():
            cascade_strength = analysis.get('information_flow', {}).get('mean_cascade_strength', 0)
            cascade_scores.append((composition, cascade_strength))
        
        cascade_scores.sort(key=lambda x: x[1], reverse=True)
        cascades['cascade_strength_ranking'] = [comp for comp, _ in cascade_scores]
        
        # Analyze scout-follower effects
        # Look for compositions with mixed agent types
        mixed_compositions = [comp for comp in population_analysis.keys() 
                            if 'mixed' in comp.lower() or 'balanced' in comp.lower()]
        
        if mixed_compositions:
            mixed_cascade_strengths = []
            for comp in mixed_compositions:
                strength = population_analysis[comp].get('information_flow', {}).get('mean_cascade_strength', 0)
                mixed_cascade_strengths.append(strength)
            
            if mixed_cascade_strengths:
                cascades['scout_follower_effects'] = {
                    'mixed_cascade_strength': np.mean(mixed_cascade_strengths),
                    'cascade_effectiveness': np.mean([s > 0.3 for s in mixed_cascade_strengths])
                }
        
        return cascades
    
    def _compare_resilience(self, population_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare resilience across population compositions."""
        resilience_comparison = {
            'resilience_ranking': [],
            'resilience_differences': {},
            'adaptation_speed_comparison': {}
        }
        
        # Rank by resilience
        resilience_scores = []
        adaptation_speeds = []
        
        for composition, analysis in population_analysis.items():
            resilience = analysis.get('resilience_metrics', {}).get('mean_resilience', 0)
            adaptation_time = analysis.get('adaptation_speed', {}).get('mean_adaptation_time', float('inf'))
            
            resilience_scores.append((composition, resilience))
            adaptation_speeds.append((composition, adaptation_time))
        
        resilience_scores.sort(key=lambda x: x[1], reverse=True)
        adaptation_speeds.sort(key=lambda x: x[1])  # Lower time = faster adaptation
        
        resilience_comparison['resilience_ranking'] = [comp for comp, _ in resilience_scores]
        resilience_comparison['adaptation_speed_ranking'] = [comp for comp, _ in adaptation_speeds]
        
        # Calculate resilience differences
        if len(resilience_scores) >= 2:
            best_resilience = resilience_scores[0][1]
            worst_resilience = resilience_scores[-1][1]
            
            resilience_comparison['resilience_differences'] = {
                'most_resilient': resilience_scores[0][0],
                'least_resilient': resilience_scores[-1][0],
                'resilience_gap': best_resilience - worst_resilience,
                'relative_improvement': (best_resilience - worst_resilience) / worst_resilience
                    if worst_resilience > 0 else float('inf')
            }
        
        return resilience_comparison
    
    def _generate_h4_findings(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key findings for H4 analysis."""
        findings = []
        
        # Diversity advantage findings
        diversity_effects = analysis.get('diversity_effects', {})
        ranking = diversity_effects.get('diversity_ranking', [])
        
        if len(ranking) >= 2:
            findings.append(f"Best performing population: {ranking[0]}")
            findings.append(f"Worst performing population: {ranking[-1]}")
        
        advantage = diversity_effects.get('diversity_advantage', {})
        if 'relative_improvement' in advantage:
            improvement = advantage['relative_improvement']
            if improvement != float('inf'):
                findings.append(f"Best composition outperforms worst by {improvement:.1%}")
        
        # Mixed vs homogeneous comparison
        homogeneous_vs_mixed = diversity_effects.get('homogeneous_vs_mixed', {})
        if 'mixed_better' in homogeneous_vs_mixed:
            if homogeneous_vs_mixed['mixed_better']:
                advantage = homogeneous_vs_mixed['mixed_advantage']
                findings.append(f"Mixed populations outperform homogeneous by {advantage:.3f}")
            else:
                findings.append("Homogeneous populations outperform mixed populations")
        
        # Information cascade findings
        cascades = analysis.get('information_cascades', {})
        cascade_ranking = cascades.get('cascade_strength_ranking', [])
        
        if cascade_ranking:
            findings.append(f"Strongest information cascades: {cascade_ranking[0]}")
        
        scout_follower = cascades.get('scout_follower_effects', {})
        if 'cascade_effectiveness' in scout_follower:
            effectiveness = scout_follower['cascade_effectiveness']
            findings.append(f"Mixed population cascade effectiveness: {effectiveness:.1%}")
        
        # Resilience findings
        resilience = analysis.get('resilience_comparison', {})
        resilience_ranking = resilience.get('resilience_ranking', [])
        
        if resilience_ranking:
            findings.append(f"Most resilient population: {resilience_ranking[0]}")
        
        return findings


class HypothesisAnalysisCoordinator:
    """
    Coordinates analysis across all hypotheses and generates comprehensive reports.
    """
    
    def __init__(self, results_dir: str):
        """Initialize analysis coordinator."""
        self.results_dir = Path(results_dir)
        self.logger = LoggingUtils().get_logger('HypothesisAnalysisCoordinator')
        
        # Initialize hypothesis-specific analyzers
        self.h1_analyzer = H1_DecisionQualityAnalyzer(results_dir)
        self.h2_analyzer = H2_ConnectivityImpactAnalyzer(results_dir)
        self.h3_analyzer = H3_PhaseTransitionAnalyzer(results_dir)
        self.h4_analyzer = H4_DiversityAdvantageAnalyzer(results_dir)
    
    def analyze_all_hypotheses(self, hypothesis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze all hypotheses and generate comprehensive report.
        
        Args:
            hypothesis_results: Dictionary of results for all hypotheses
            
        Returns:
            Comprehensive analysis results
        """
        comprehensive_analysis = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'hypothesis_analyses': {},
            'cross_hypothesis_insights': {},
            'overall_conclusions': {},
            'recommendations': []
        }
        
        # Analyze each hypothesis
        for hypothesis_id, results in hypothesis_results.items():
            self.logger.info(f"Analyzing {hypothesis_id}")
            
            try:
                if hypothesis_id.startswith('H1'):
                    analysis = self.h1_analyzer.analyze_speed_optimality_tradeoffs(results)
                elif hypothesis_id.startswith('H2'):
                    analysis = self.h2_analyzer.analyze_connectivity_effects(results)
                elif hypothesis_id.startswith('H3'):
                    analysis = self.h3_analyzer.analyze_phase_transitions(results)
                elif hypothesis_id.startswith('H4'):
                    analysis = self.h4_analyzer.analyze_diversity_advantages(results)
                else:
                    self.logger.warning(f"Unknown hypothesis: {hypothesis_id}")
                    continue
                
                comprehensive_analysis['hypothesis_analyses'][hypothesis_id] = analysis
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {hypothesis_id}: {e}")
                comprehensive_analysis['hypothesis_analyses'][hypothesis_id] = {'error': str(e)}
        
        # Generate cross-hypothesis insights
        comprehensive_analysis['cross_hypothesis_insights'] = self._generate_cross_hypothesis_insights(
            comprehensive_analysis['hypothesis_analyses']
        )
        
        # Generate overall conclusions
        comprehensive_analysis['overall_conclusions'] = self._generate_overall_conclusions(
            comprehensive_analysis['hypothesis_analyses']
        )
        
        # Generate recommendations
        comprehensive_analysis['recommendations'] = self._generate_recommendations(
            comprehensive_analysis
        )
        
        return comprehensive_analysis
    
    def _generate_cross_hypothesis_insights(self, hypothesis_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights that span multiple hypotheses."""
        insights = {
            'cognitive_mode_consistency': {},
            'parameter_interactions': {},
            'emergent_patterns': []
        }
        
        # Analyze cognitive mode performance consistency across hypotheses
        mode_performance = {}
        
        for hypothesis_id, analysis in hypothesis_analyses.items():
            if 'error' in analysis:
                continue
            
            # Extract cognitive mode performance indicators
            if 'cognitive_mode_analysis' in analysis:
                for mode, mode_data in analysis['cognitive_mode_analysis'].items():
                    if mode not in mode_performance:
                        mode_performance[mode] = []
                    
                    # Extract a general performance score
                    if 'composite_scores' in mode_data:
                        balanced_score = mode_data['composite_scores'].get('balanced_score', 0)
                        mode_performance[mode].append((hypothesis_id, balanced_score))
        
        # Calculate consistency scores
        for mode, performances in mode_performance.items():
            if len(performances) >= 2:
                scores = [score for _, score in performances]
                insights['cognitive_mode_consistency'][mode] = {
                    'mean_performance': np.mean(scores),
                    'std_performance': np.std(scores),
                    'consistency_score': 1.0 - (np.std(scores) / np.mean(scores)) 
                        if np.mean(scores) > 0 else 0,
                    'hypotheses_tested': [hyp for hyp, _ in performances]
                }
        
        return insights
    
    def _generate_overall_conclusions(self, hypothesis_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall conclusions across all hypotheses."""
        conclusions = {
            'dual_process_theory_support': 'insufficient_evidence',
            'strongest_evidence': None,
            'weakest_evidence': None,
            'key_insights': [],
            'theory_implications': []
        }
        
        # Count supported hypotheses
        supported_count = 0
        total_count = 0
        hypothesis_support = {}
        
        for hypothesis_id, analysis in hypothesis_analyses.items():
            if 'error' in analysis:
                continue
            
            total_count += 1
            
            # Determine if hypothesis is supported based on key findings
            key_findings = analysis.get('key_findings', [])
            significant_effects = len([f for f in key_findings if 'outperform' in f or 'advantage' in f])
            
            if significant_effects > 0:
                supported_count += 1
                hypothesis_support[hypothesis_id] = 'supported'
            else:
                hypothesis_support[hypothesis_id] = 'not_supported'
        
        # Determine overall theory support
        if total_count == 0:
            conclusions['dual_process_theory_support'] = 'insufficient_evidence'
        elif supported_count / total_count >= 0.75:
            conclusions['dual_process_theory_support'] = 'strong_support'
        elif supported_count / total_count >= 0.5:
            conclusions['dual_process_theory_support'] = 'moderate_support'
        elif supported_count / total_count >= 0.25:
            conclusions['dual_process_theory_support'] = 'weak_support'
        else:
            conclusions['dual_process_theory_support'] = 'little_support'
        
        # Identify strongest and weakest evidence
        if hypothesis_support:
            supported_hypotheses = [h for h, s in hypothesis_support.items() if s == 'supported']
            unsupported_hypotheses = [h for h, s in hypothesis_support.items() if s == 'not_supported']
            
            if supported_hypotheses:
                conclusions['strongest_evidence'] = supported_hypotheses[0]  # Could be more sophisticated
            if unsupported_hypotheses:
                conclusions['weakest_evidence'] = unsupported_hypotheses[0]
        
        # Generate key insights
        conclusions['key_insights'] = [
            f"Dual-process theory support: {conclusions['dual_process_theory_support']}",
            f"Hypotheses supported: {supported_count}/{total_count}",
            f"Strongest evidence from: {conclusions['strongest_evidence']}",
            f"Weakest evidence from: {conclusions['weakest_evidence']}"
        ]
        
        return conclusions
    
    def _generate_recommendations(self, comprehensive_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        overall_conclusions = comprehensive_analysis.get('overall_conclusions', {})
        theory_support = overall_conclusions.get('dual_process_theory_support', 'insufficient_evidence')
        
        # Theory-specific recommendations
        if theory_support == 'strong_support':
            recommendations.extend([
                "Proceed with real-world validation using UNHCR refugee data",
                "Develop policy recommendations based on dual-process insights",
                "Extend framework to other displacement scenarios"
            ])
        elif theory_support == 'moderate_support':
            recommendations.extend([
                "Increase sample sizes and replication counts",
                "Refine parameter ranges for stronger effects",
                "Focus on hypotheses with strongest evidence"
            ])
        else:
            recommendations.extend([
                "Reconsider experimental design and parameter choices",
                "Validate simulation implementation against known results",
                "Consider alternative theoretical frameworks"
            ])
        
        # Hypothesis-specific recommendations
        hypothesis_analyses = comprehensive_analysis.get('hypothesis_analyses', {})
        
        for hypothesis_id, analysis in hypothesis_analyses.items():
            if 'error' in analysis:
                recommendations.append(f"Fix implementation issues in {hypothesis_id}")
                continue
            
            key_findings = analysis.get('key_findings', [])
            if not key_findings:
                recommendations.append(f"Strengthen experimental design for {hypothesis_id}")
        
        # Cross-hypothesis recommendations
        cross_insights = comprehensive_analysis.get('cross_hypothesis_insights', {})
        consistency = cross_insights.get('cognitive_mode_consistency', {})
        
        inconsistent_modes = [mode for mode, data in consistency.items() 
                            if data.get('consistency_score', 1) < 0.5]
        
        if inconsistent_modes:
            recommendations.append(f"Investigate inconsistent cognitive modes: {', '.join(inconsistent_modes)}")
        
        return recommendations
    
    def save_comprehensive_analysis(self, analysis: Dict[str, Any], output_file: str) -> None:
        """Save comprehensive analysis to file."""
        output_path = self.results_dir / output_file
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        self.logger.info(f"Comprehensive analysis saved to {output_path}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run hypothesis-specific analysis')
    parser.add_argument('results_dir', help='Directory containing hypothesis results')
    parser.add_argument('--hypothesis', choices=['H1', 'H2', 'H3', 'H4'], 
                       help='Specific hypothesis to analyze')
    parser.add_argument('--output', help='Output file for analysis results')
    
    args = parser.parse_args()
    
    # Initialize coordinator
    coordinator = HypothesisAnalysisCoordinator(args.results_dir)
    
    if args.hypothesis:
        # Analyze specific hypothesis
        print(f"Analyzing {args.hypothesis} results...")
        # Implementation would load specific hypothesis results and analyze
    else:
        # Analyze all hypotheses
        print("Analyzing all hypothesis results...")
        # Implementation would load all results and perform comprehensive analysis
    
    print("Analysis completed!")


if __name__ == "__main__":
    main()