"""
H3.1 Statistical Analysis

Implements statistical analysis methods for critical point identification
and dimensionless parameter validation.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import kstest, shapiro, levene, ttest_ind, mannwhitneyu
from sklearn.metrics import r2_score
from typing import Dict, List, Tuple, Optional
import warnings


class StatisticalAnalyzer:
    """Statistical analysis for H3.1 parameter grid experiments."""
    
    def __init__(self, alpha: float = 0.05):
        """
        Initialize statistical analyzer.
        
        Args:
            alpha: Significance level for statistical tests
        """
        self.alpha = alpha
    
    def test_dimensionless_scaling(self, data: pd.DataFrame) -> Dict:
        """
        Test whether cognitive pressure provides better scaling than individual parameters.
        
        Args:
            data: DataFrame with parameter columns and s2_activation_rate
            
        Returns:
            Dictionary with scaling test results
        """
        results = {}
        
        # Test correlation strength for each parameter
        parameters = ['conflict_intensity', 'recovery_period', 'connectivity_rate', 'cognitive_pressure']
        correlations = {}
        
        for param in parameters:
            if param in data.columns:
                # Calculate Pearson correlation
                r, p_value = stats.pearsonr(data[param], data['s2_activation_rate'])
                
                # Calculate Spearman correlation (rank-based)
                rho, p_spearman = stats.spearmanr(data[param], data['s2_activation_rate'])
                
                correlations[param] = {
                    'pearson_r': r,
                    'pearson_p': p_value,
                    'spearman_rho': rho,
                    'spearman_p': p_spearman,
                    'significant_pearson': p_value < self.alpha,
                    'significant_spearman': p_spearman < self.alpha
                }
        
        # Test if cognitive pressure correlation is significantly stronger
        if 'cognitive_pressure' in correlations:
            cp_r = abs(correlations['cognitive_pressure']['pearson_r'])
            individual_rs = [abs(correlations[p]['pearson_r']) 
                           for p in ['conflict_intensity', 'recovery_period', 'connectivity_rate']
                           if p in correlations]
            
            results['cognitive_pressure_advantage'] = {
                'cp_correlation': cp_r,
                'max_individual_correlation': max(individual_rs) if individual_rs else 0,
                'advantage_ratio': cp_r / max(individual_rs) if individual_rs and max(individual_rs) > 0 else float('inf'),
                'is_strongest': cp_r > max(individual_rs) if individual_rs else True
            }
        
        results['parameter_correlations'] = correlations
        return results
    
    def identify_critical_points(self, data: pd.DataFrame, 
                               method: str = 'derivative') -> Dict:
        """
        Identify critical points using multiple statistical methods.
        
        Args:
            data: DataFrame with cognitive_pressure and s2_activation_rate
            method: Method for critical point detection ('derivative', 'changepoint', 'threshold')
            
        Returns:
            Dictionary with critical point analysis
        """
        # Sort data by cognitive pressure
        sorted_data = data.sort_values('cognitive_pressure')
        x = sorted_data['cognitive_pressure'].values
        y = sorted_data['s2_activation_rate'].values
        
        results = {}
        
        if method == 'derivative':
            # Find maximum derivative (steepest slope)
            if len(x) > 2:
                # Smooth the data first
                from scipy.ndimage import gaussian_filter1d
                y_smooth = gaussian_filter1d(y, sigma=1.0)
                
                # Calculate derivative
                dx = np.diff(x)
                dy = np.diff(y_smooth)
                derivative = dy / dx
                
                # Find maximum derivative
                max_deriv_idx = np.argmax(derivative)
                critical_point = (x[max_deriv_idx] + x[max_deriv_idx + 1]) / 2
                max_derivative = derivative[max_deriv_idx]
                
                results['derivative_method'] = {
                    'critical_point': critical_point,
                    'max_derivative': max_derivative,
                    'confidence': max_derivative / np.std(derivative) if np.std(derivative) > 0 else 0
                }
        
        elif method == 'changepoint':
            # Simple changepoint detection using variance change
            n = len(y)
            if n > 10:
                variances = []
                split_points = range(5, n-5)  # Avoid edge effects
                
                for split in split_points:
                    var1 = np.var(y[:split])
                    var2 = np.var(y[split:])
                    combined_var = var1 + var2
                    variances.append(combined_var)
                
                min_var_idx = np.argmin(variances)
                critical_point = x[split_points[min_var_idx]]
                
                results['changepoint_method'] = {
                    'critical_point': critical_point,
                    'variance_reduction': max(variances) - min(variances),
                    'confidence': (max(variances) - min(variances)) / max(variances) if max(variances) > 0 else 0
                }
        
        elif method == 'threshold':
            # Find point where S2 activation crosses specific thresholds
            thresholds = [0.25, 0.5, 0.75]
            threshold_points = {}
            
            for threshold in thresholds:
                crossing_indices = np.where(y >= threshold)[0]
                if len(crossing_indices) > 0:
                    threshold_points[threshold] = x[crossing_indices[0]]
            
            results['threshold_method'] = {
                'threshold_crossings': threshold_points,
                'primary_threshold': threshold_points.get(0.5, None)
            }
        
        return results
    
    def test_phase_transition_significance(self, data: pd.DataFrame, 
                                         critical_point: float) -> Dict:
        """
        Test statistical significance of phase transition at critical point.
        
        Args:
            data: DataFrame with cognitive_pressure and s2_activation_rate
            critical_point: Proposed critical point value
            
        Returns:
            Dictionary with significance test results
        """
        # Split data at critical point
        below_critical = data[data['cognitive_pressure'] < critical_point]['s2_activation_rate']
        above_critical = data[data['cognitive_pressure'] >= critical_point]['s2_activation_rate']
        
        if len(below_critical) < 3 or len(above_critical) < 3:
            return {'error': 'Insufficient data for significance testing'}
        
        results = {}
        
        # Test for normality
        _, p_shapiro_below = shapiro(below_critical)
        _, p_shapiro_above = shapiro(above_critical)
        
        normal_below = p_shapiro_below > self.alpha
        normal_above = p_shapiro_above > self.alpha
        
        # Test for equal variances
        _, p_levene = levene(below_critical, above_critical)
        equal_variances = p_levene > self.alpha
        
        # Choose appropriate test
        if normal_below and normal_above:
            if equal_variances:
                # Independent t-test
                statistic, p_value = ttest_ind(below_critical, above_critical)
                test_used = 'independent_t_test'
            else:
                # Welch's t-test
                statistic, p_value = ttest_ind(below_critical, above_critical, equal_var=False)
                test_used = 'welch_t_test'
        else:
            # Mann-Whitney U test (non-parametric)
            statistic, p_value = mannwhitneyu(below_critical, above_critical, alternative='two-sided')
            test_used = 'mann_whitney_u'
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(below_critical) - 1) * np.var(below_critical, ddof=1) + 
                             (len(above_critical) - 1) * np.var(above_critical, ddof=1)) / 
                            (len(below_critical) + len(above_critical) - 2))
        
        cohens_d = (np.mean(above_critical) - np.mean(below_critical)) / pooled_std if pooled_std > 0 else 0
        
        results = {
            'test_used': test_used,
            'statistic': statistic,
            'p_value': p_value,
            'significant': p_value < self.alpha,
            'effect_size_cohens_d': cohens_d,
            'effect_size_interpretation': self._interpret_cohens_d(cohens_d),
            'sample_sizes': {
                'below_critical': len(below_critical),
                'above_critical': len(above_critical)
            },
            'means': {
                'below_critical': np.mean(below_critical),
                'above_critical': np.mean(above_critical)
            },
            'normality_tests': {
                'below_critical_normal': normal_below,
                'above_critical_normal': normal_above
            },
            'equal_variances': equal_variances
        }
        
        return results
    
    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return 'negligible'
        elif abs_d < 0.5:
            return 'small'
        elif abs_d < 0.8:
            return 'medium'
        else:
            return 'large'
    
    def validate_scaling_law(self, data: pd.DataFrame) -> Dict:
        """
        Validate the proposed dimensionless scaling law.
        
        Args:
            data: DataFrame with all parameters and results
            
        Returns:
            Dictionary with scaling law validation results
        """
        results = {}
        
        # Test 1: Correlation strength comparison
        scaling_test = self.test_dimensionless_scaling(data)
        results['correlation_test'] = scaling_test
        
        # Test 2: Data collapse quality
        if 'cognitive_pressure' in data.columns:
            # Group data by cognitive pressure bins
            n_bins = min(10, len(data) // 5)  # Adaptive binning
            data['pressure_bin'] = pd.cut(data['cognitive_pressure'], bins=n_bins)
            
            bin_stats = data.groupby('pressure_bin')['s2_activation_rate'].agg(['mean', 'std', 'count'])
            
            # Calculate coefficient of variation within bins
            bin_stats['cv'] = bin_stats['std'] / bin_stats['mean']
            mean_cv = bin_stats['cv'].mean()
            
            results['data_collapse'] = {
                'mean_coefficient_variation': mean_cv,
                'collapse_quality': 'good' if mean_cv < 0.3 else 'moderate' if mean_cv < 0.5 else 'poor',
                'bin_statistics': bin_stats.to_dict()
            }
        
        # Test 3: Predictive power comparison
        if len(data) > 20:
            from sklearn.model_selection import cross_val_score
            from sklearn.linear_model import LinearRegression
            
            # Compare R² for different parameter sets
            individual_params = ['conflict_intensity', 'recovery_period', 'connectivity_rate']
            available_individual = [p for p in individual_params if p in data.columns]
            
            if len(available_individual) > 0 and 'cognitive_pressure' in data.columns:
                # Individual parameters model
                X_individual = data[available_individual].values
                y = data['s2_activation_rate'].values
                
                individual_scores = cross_val_score(LinearRegression(), X_individual, y, cv=5, scoring='r2')
                
                # Cognitive pressure model
                X_pressure = data[['cognitive_pressure']].values
                pressure_scores = cross_val_score(LinearRegression(), X_pressure, y, cv=5, scoring='r2')
                
                results['predictive_power'] = {
                    'individual_params_r2': {
                        'mean': np.mean(individual_scores),
                        'std': np.std(individual_scores)
                    },
                    'cognitive_pressure_r2': {
                        'mean': np.mean(pressure_scores),
                        'std': np.std(pressure_scores)
                    },
                    'pressure_advantage': np.mean(pressure_scores) > np.mean(individual_scores)
                }
        
        # Overall validation score
        validation_score = 0
        max_score = 0
        
        # Score correlation test
        if 'correlation_test' in results and 'cognitive_pressure_advantage' in results['correlation_test']:
            if results['correlation_test']['cognitive_pressure_advantage']['is_strongest']:
                validation_score += 1
            max_score += 1
        
        # Score data collapse
        if 'data_collapse' in results:
            if results['data_collapse']['collapse_quality'] in ['good', 'moderate']:
                validation_score += 1
            max_score += 1
        
        # Score predictive power
        if 'predictive_power' in results:
            if results['predictive_power']['pressure_advantage']:
                validation_score += 1
            max_score += 1
        
        results['overall_validation'] = {
            'score': validation_score,
            'max_score': max_score,
            'validation_ratio': validation_score / max_score if max_score > 0 else 0,
            'scaling_law_supported': validation_score / max_score > 0.5 if max_score > 0 else False
        }
        
        return results
    
    def generate_statistical_report(self, data: pd.DataFrame, 
                                  critical_point: float = None) -> str:
        """
        Generate comprehensive statistical analysis report.
        
        Args:
            data: DataFrame with experiment results
            critical_point: Critical point for phase transition analysis
            
        Returns:
            Formatted statistical report string
        """
        report = []
        report.append("H3.1 Parameter Grid Statistical Analysis Report")
        report.append("=" * 50)
        report.append("")
        
        # Basic statistics
        report.append("Dataset Summary:")
        report.append(f"  Total experiments: {len(data)}")
        report.append(f"  Cognitive pressure range: {data['cognitive_pressure'].min():.3f} - {data['cognitive_pressure'].max():.3f}")
        report.append(f"  S2 activation rate range: {data['s2_activation_rate'].min():.3f} - {data['s2_activation_rate'].max():.3f}")
        report.append("")
        
        # Scaling law validation
        scaling_results = self.validate_scaling_law(data)
        report.append("Dimensionless Scaling Law Validation:")
        
        if 'correlation_test' in scaling_results:
            corr_test = scaling_results['correlation_test']
            if 'cognitive_pressure_advantage' in corr_test:
                adv = corr_test['cognitive_pressure_advantage']
                report.append(f"  Cognitive pressure correlation: {adv['cp_correlation']:.3f}")
                report.append(f"  Best individual parameter correlation: {adv['max_individual_correlation']:.3f}")
                report.append(f"  Advantage ratio: {adv['advantage_ratio']:.2f}")
                report.append(f"  Cognitive pressure is strongest predictor: {adv['is_strongest']}")
        
        if 'overall_validation' in scaling_results:
            overall = scaling_results['overall_validation']
            report.append(f"  Overall validation score: {overall['score']}/{overall['max_score']}")
            report.append(f"  Scaling law supported: {overall['scaling_law_supported']}")
        
        report.append("")
        
        # Phase transition analysis
        if critical_point is not None:
            transition_test = self.test_phase_transition_significance(data, critical_point)
            report.append("Phase Transition Significance Test:")
            report.append(f"  Critical point: {critical_point:.3f}")
            report.append(f"  Test used: {transition_test.get('test_used', 'N/A')}")
            report.append(f"  p-value: {transition_test.get('p_value', 'N/A'):.6f}")
            report.append(f"  Significant: {transition_test.get('significant', False)}")
            report.append(f"  Effect size (Cohen's d): {transition_test.get('effect_size_cohens_d', 'N/A'):.3f}")
            report.append(f"  Effect interpretation: {transition_test.get('effect_size_interpretation', 'N/A')}")
            report.append("")
        
        return "\n".join(report)


def main():
    """Example usage of statistical analysis."""
    # Generate sample data
    np.random.seed(42)
    
    n_samples = 100
    cognitive_pressures = np.random.uniform(0, 3, n_samples)
    
    # Create realistic S2 activation pattern with phase transition
    s2_rates = 0.8 / (1 + np.exp(-3 * (cognitive_pressures - 1.2))) + 0.1
    s2_rates += np.random.normal(0, 0.05, n_samples)
    s2_rates = np.clip(s2_rates, 0, 1)
    
    data = pd.DataFrame({
        'cognitive_pressure': cognitive_pressures,
        's2_activation_rate': s2_rates,
        'conflict_intensity': np.random.uniform(0.1, 0.9, n_samples),
        'recovery_period': np.random.uniform(10, 50, n_samples),
        'connectivity_rate': np.random.uniform(0, 8, n_samples)
    })
    
    # Run statistical analysis
    analyzer = StatisticalAnalyzer()
    
    # Test scaling law
    scaling_results = analyzer.validate_scaling_law(data)
    print("Scaling law validation:")
    print(f"Supported: {scaling_results['overall_validation']['scaling_law_supported']}")
    
    # Test critical point
    critical_point = 1.2  # Known from data generation
    transition_results = analyzer.test_phase_transition_significance(data, critical_point)
    print(f"\nPhase transition at {critical_point}:")
    print(f"Significant: {transition_results['significant']}")
    print(f"Effect size: {transition_results['effect_size_cohens_d']:.3f}")
    
    # Generate full report
    report = analyzer.generate_statistical_report(data, critical_point)
    print("\n" + report)


if __name__ == "__main__":
    main()