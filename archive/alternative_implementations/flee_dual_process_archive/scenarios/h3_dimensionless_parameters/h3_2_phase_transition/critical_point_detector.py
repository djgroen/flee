"""
H3.2 Critical Point Detection

Implements advanced critical point detection algorithms with sigmoid fitting
and confidence interval estimation for precise phase transition identification.
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, minimize_scalar
from scipy.stats import t
from sklearn.metrics import r2_score
from typing import Dict, List, Tuple, Optional, Callable
import matplotlib.pyplot as plt
import seaborn as sns


class CriticalPointDetector:
    """Advanced critical point detection for H3.2 phase transition identification."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize critical point detector.
        
        Args:
            confidence_level: Confidence level for interval estimation
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        
        # Sigmoid model variants
        self.sigmoid_models = {
            'standard': self._standard_sigmoid,
            'asymmetric': self._asymmetric_sigmoid,
            'double': self._double_sigmoid
        }
    
    @staticmethod
    def _standard_sigmoid(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
        """
        Standard sigmoid: y = a / (1 + exp(-b * (x - c))) + d
        
        Args:
            x: Input values (cognitive pressure)
            a: Amplitude (height of transition)
            b: Steepness (transition sharpness)
            c: Critical point (inflection point)
            d: Baseline offset
        """
        return a / (1 + np.exp(-b * (x - c))) + d
    
    @staticmethod
    def _asymmetric_sigmoid(x: np.ndarray, a: float, b1: float, b2: float, c: float, d: float) -> np.ndarray:
        """
        Asymmetric sigmoid with different slopes before/after critical point.
        """
        result = np.zeros_like(x)
        mask_left = x <= c
        mask_right = x > c
        
        # Left side (before critical point)
        if np.any(mask_left):
            result[mask_left] = a / (1 + np.exp(-b1 * (x[mask_left] - c))) + d
        
        # Right side (after critical point)
        if np.any(mask_right):
            result[mask_right] = a / (1 + np.exp(-b2 * (x[mask_right] - c))) + d
        
        return result
    
    @staticmethod
    def _double_sigmoid(x: np.ndarray, a1: float, b1: float, c1: float, 
                       a2: float, b2: float, c2: float, d: float) -> np.ndarray:
        """
        Double sigmoid for complex transitions with two critical points.
        """
        sigmoid1 = a1 / (1 + np.exp(-b1 * (x - c1)))
        sigmoid2 = a2 / (1 + np.exp(-b2 * (x - c2)))
        return sigmoid1 + sigmoid2 + d
    
    def fit_sigmoid_model(self, data: pd.DataFrame, 
                         model_type: str = 'standard') -> Dict:
        """
        Fit sigmoid model to S2 activation data.
        
        Args:
            data: DataFrame with 'cognitive_pressure' and 's2_activation_rate' columns
            model_type: Type of sigmoid model to fit
            
        Returns:
            Dictionary with fit results and statistics
        """
        if model_type not in self.sigmoid_models:
            raise ValueError(f"Unknown model type: {model_type}")
        
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        
        # Sort data by cognitive pressure
        sort_idx = np.argsort(x)
        x_sorted = x[sort_idx]
        y_sorted = y[sort_idx]
        
        model_func = self.sigmoid_models[model_type]
        
        try:
            # Set initial parameters and bounds based on model type
            if model_type == 'standard':
                # Standard sigmoid: [a, b, c, d]
                initial_params = [0.8, 3.0, 1.0, 0.1]
                bounds = ([0.1, 0.1, 0.0, 0.0], [1.0, 20.0, 3.0, 0.5])
                
            elif model_type == 'asymmetric':
                # Asymmetric sigmoid: [a, b1, b2, c, d]
                initial_params = [0.8, 3.0, 3.0, 1.0, 0.1]
                bounds = ([0.1, 0.1, 0.1, 0.0, 0.0], [1.0, 20.0, 20.0, 3.0, 0.5])
                
            elif model_type == 'double':
                # Double sigmoid: [a1, b1, c1, a2, b2, c2, d]
                initial_params = [0.4, 3.0, 0.8, 0.4, 3.0, 1.2, 0.1]
                bounds = ([0.05, 0.1, 0.0, 0.05, 0.1, 0.0, 0.0], 
                         [0.5, 20.0, 2.0, 0.5, 20.0, 3.0, 0.5])
            
            # Fit the model
            popt, pcov = curve_fit(model_func, x_sorted, y_sorted,
                                 p0=initial_params,
                                 bounds=bounds,
                                 maxfev=10000)
            
            # Calculate fit statistics
            y_pred = model_func(x_sorted, *popt)
            r_squared = r2_score(y_sorted, y_pred)
            rmse = np.sqrt(np.mean((y_sorted - y_pred) ** 2))
            
            # Calculate parameter uncertainties
            param_errors = np.sqrt(np.diag(pcov))
            
            # Extract critical point(s)
            if model_type == 'standard':
                critical_point = popt[2]  # c parameter
                critical_point_error = param_errors[2]
                
            elif model_type == 'asymmetric':
                critical_point = popt[3]  # c parameter
                critical_point_error = param_errors[3]
                
            elif model_type == 'double':
                critical_points = [popt[2], popt[5]]  # c1, c2 parameters
                critical_point = np.mean(critical_points)  # Average of two points
                critical_point_error = np.sqrt(param_errors[2]**2 + param_errors[5]**2) / 2
            
            # Calculate confidence interval for critical point
            dof = len(x_sorted) - len(popt)  # Degrees of freedom
            t_value = t.ppf(1 - self.alpha/2, dof) if dof > 0 else 1.96
            
            ci_lower = critical_point - t_value * critical_point_error
            ci_upper = critical_point + t_value * critical_point_error
            
            return {
                'model_type': model_type,
                'parameters': popt.tolist(),
                'parameter_errors': param_errors.tolist(),
                'critical_point': critical_point,
                'critical_point_error': critical_point_error,
                'confidence_interval': [ci_lower, ci_upper],
                'confidence_level': self.confidence_level,
                'r_squared': r_squared,
                'rmse': rmse,
                'fit_successful': True,
                'n_data_points': len(x_sorted),
                'degrees_of_freedom': dof
            }
            
        except Exception as e:
            return {
                'model_type': model_type,
                'parameters': None,
                'critical_point': None,
                'confidence_interval': None,
                'r_squared': 0.0,
                'rmse': float('inf'),
                'fit_successful': False,
                'error': str(e)
            }
    
    def compare_sigmoid_models(self, data: pd.DataFrame) -> Dict:
        """
        Compare different sigmoid models and select the best one.
        
        Args:
            data: DataFrame with cognitive pressure and S2 activation data
            
        Returns:
            Dictionary with comparison results and best model selection
        """
        model_results = {}
        
        # Fit all available models
        for model_type in self.sigmoid_models.keys():
            result = self.fit_sigmoid_model(data, model_type)
            model_results[model_type] = result
        
        # Select best model based on R² and successful fit
        successful_models = {k: v for k, v in model_results.items() 
                           if v['fit_successful'] and v['r_squared'] > 0.5}
        
        if successful_models:
            best_model_type = max(successful_models.keys(), 
                                key=lambda k: successful_models[k]['r_squared'])
            best_model = successful_models[best_model_type]
        else:
            best_model_type = None
            best_model = None
        
        return {
            'model_comparison': model_results,
            'best_model_type': best_model_type,
            'best_model_results': best_model,
            'comparison_successful': best_model is not None
        }
    
    def detect_critical_point_bootstrap(self, data: pd.DataFrame, 
                                      n_bootstrap: int = 1000) -> Dict:
        """
        Use bootstrap resampling to estimate critical point confidence intervals.
        
        Args:
            data: DataFrame with cognitive pressure and S2 activation data
            n_bootstrap: Number of bootstrap samples
            
        Returns:
            Dictionary with bootstrap critical point estimates
        """
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        n_samples = len(x)
        
        if n_samples < 10:
            return {'error': 'Insufficient data for bootstrap analysis'}
        
        critical_points = []
        successful_fits = 0
        
        # Bootstrap resampling
        np.random.seed(42)  # For reproducibility
        
        for i in range(n_bootstrap):
            # Resample with replacement
            bootstrap_idx = np.random.choice(n_samples, size=n_samples, replace=True)
            x_boot = x[bootstrap_idx]
            y_boot = y[bootstrap_idx]
            
            # Create bootstrap DataFrame
            boot_data = pd.DataFrame({
                'cognitive_pressure': x_boot,
                's2_activation_rate': y_boot
            })
            
            # Fit sigmoid model
            fit_result = self.fit_sigmoid_model(boot_data, 'standard')
            
            if fit_result['fit_successful'] and fit_result['r_squared'] > 0.7:
                critical_points.append(fit_result['critical_point'])
                successful_fits += 1
        
        if not critical_points:
            return {'error': 'No successful bootstrap fits'}
        
        critical_points = np.array(critical_points)
        
        # Calculate bootstrap statistics
        mean_critical = np.mean(critical_points)
        std_critical = np.std(critical_points)
        
        # Bootstrap confidence intervals (percentile method)
        ci_lower = np.percentile(critical_points, 100 * self.alpha / 2)
        ci_upper = np.percentile(critical_points, 100 * (1 - self.alpha / 2))
        
        return {
            'bootstrap_critical_point': mean_critical,
            'bootstrap_std': std_critical,
            'bootstrap_confidence_interval': [ci_lower, ci_upper],
            'confidence_level': self.confidence_level,
            'successful_fits': successful_fits,
            'total_bootstrap_samples': n_bootstrap,
            'success_rate': successful_fits / n_bootstrap,
            'critical_point_distribution': critical_points.tolist()
        }
    
    def analyze_transition_sharpness(self, data: pd.DataFrame, 
                                   critical_point: float) -> Dict:
        """
        Analyze the sharpness of the phase transition.
        
        Args:
            data: DataFrame with cognitive pressure and S2 activation data
            critical_point: Estimated critical point
            
        Returns:
            Dictionary with transition sharpness metrics
        """
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        
        # Sort data
        sort_idx = np.argsort(x)
        x_sorted = x[sort_idx]
        y_sorted = y[sort_idx]
        
        # Calculate numerical derivative
        if len(x_sorted) > 2:
            dx = np.diff(x_sorted)
            dy = np.diff(y_sorted)
            derivative = dy / dx
            x_deriv = (x_sorted[:-1] + x_sorted[1:]) / 2
            
            # Find maximum derivative (steepest slope)
            max_deriv_idx = np.argmax(derivative)
            max_derivative = derivative[max_deriv_idx]
            steepest_point = x_deriv[max_deriv_idx]
            
            # Calculate transition width (distance between 25% and 75% activation)
            try:
                # Find points where S2 activation is 25% and 75%
                idx_25 = np.where(y_sorted >= 0.25)[0]
                idx_75 = np.where(y_sorted >= 0.75)[0]
                
                if len(idx_25) > 0 and len(idx_75) > 0:
                    x_25 = x_sorted[idx_25[0]]
                    x_75 = x_sorted[idx_75[0]]
                    transition_width = x_75 - x_25
                else:
                    transition_width = None
            except:
                transition_width = None
            
            # Calculate sharpness score (higher = sharper transition)
            sharpness_score = max_derivative / np.std(derivative) if np.std(derivative) > 0 else 0
            
        else:
            max_derivative = 0
            steepest_point = critical_point
            transition_width = None
            sharpness_score = 0
        
        return {
            'max_derivative': max_derivative,
            'steepest_point': steepest_point,
            'transition_width_25_75': transition_width,
            'sharpness_score': sharpness_score,
            'critical_point_deviation': abs(steepest_point - critical_point) if steepest_point else None
        }
    
    def create_phase_diagram_detailed(self, data: pd.DataFrame, 
                                    fit_results: Dict,
                                    output_path: str = None) -> str:
        """
        Create detailed phase diagram with confidence intervals and fit statistics.
        
        Args:
            data: DataFrame with experimental data
            fit_results: Results from sigmoid model fitting
            output_path: Path to save the plot
            
        Returns:
            Path to saved plot
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        
        # Main phase transition plot
        ax1.scatter(x, y, alpha=0.7, s=60, c='blue', label='Experimental data')
        
        if fit_results['comparison_successful']:
            best_model = fit_results['best_model_results']
            model_type = best_model['model_type']
            
            # Plot fitted curve
            x_smooth = np.linspace(x.min(), x.max(), 200)
            model_func = self.sigmoid_models[model_type]
            y_smooth = model_func(x_smooth, *best_model['parameters'])
            
            ax1.plot(x_smooth, y_smooth, 'r-', linewidth=3, 
                    label=f'{model_type.capitalize()} sigmoid fit')
            
            # Mark critical point with confidence interval
            critical_point = best_model['critical_point']
            ci_lower, ci_upper = best_model['confidence_interval']
            
            ax1.axvline(critical_point, color='red', linestyle='--', linewidth=2,
                       label=f'Critical point: {critical_point:.3f}')
            ax1.axvspan(ci_lower, ci_upper, alpha=0.2, color='red',
                       label=f'{self.confidence_level*100:.0f}% CI: [{ci_lower:.3f}, {ci_upper:.3f}]')
            
            # Add fit statistics
            ax1.text(0.05, 0.95, f'R² = {best_model["r_squared"]:.3f}\nRMSE = {best_model["rmse"]:.3f}',
                    transform=ax1.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax1.set_xlabel('Cognitive Pressure')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('Phase Transition: S2 Activation vs Cognitive Pressure')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_ylim(-0.05, 1.05)
        
        # Model comparison plot
        if 'model_comparison' in fit_results:
            model_names = []
            r_squared_values = []
            
            for model_name, result in fit_results['model_comparison'].items():
                if result['fit_successful']:
                    model_names.append(model_name.capitalize())
                    r_squared_values.append(result['r_squared'])
            
            if model_names:
                bars = ax2.bar(model_names, r_squared_values, alpha=0.7)
                ax2.set_ylabel('R² Score')
                ax2.set_title('Model Comparison')
                ax2.set_ylim(0, 1)
                
                # Highlight best model
                if fit_results['best_model_type']:
                    best_idx = model_names.index(fit_results['best_model_type'].capitalize())
                    bars[best_idx].set_color('red')
                    bars[best_idx].set_alpha(1.0)
        
        # Residuals plot
        if fit_results['comparison_successful']:
            best_model = fit_results['best_model_results']
            model_func = self.sigmoid_models[best_model['model_type']]
            y_pred = model_func(x, *best_model['parameters'])
            residuals = y - y_pred
            
            ax3.scatter(x, residuals, alpha=0.7)
            ax3.axhline(0, color='red', linestyle='--')
            ax3.set_xlabel('Cognitive Pressure')
            ax3.set_ylabel('Residuals')
            ax3.set_title('Residuals Plot')
            ax3.grid(True, alpha=0.3)
        
        # Data distribution histogram
        ax4.hist(x, bins=20, alpha=0.7, edgecolor='black')
        ax4.set_xlabel('Cognitive Pressure')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Data Distribution')
        ax4.grid(True, alpha=0.3)
        
        # Mark critical point on histogram
        if fit_results['comparison_successful']:
            critical_point = fit_results['best_model_results']['critical_point']
            ax4.axvline(critical_point, color='red', linestyle='--', linewidth=2,
                       label=f'Critical point: {critical_point:.3f}')
            ax4.legend()
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None


def main():
    """Example usage of critical point detection."""
    # Generate synthetic data with known critical point
    np.random.seed(42)
    
    # Create realistic phase transition data
    cognitive_pressures = np.linspace(0, 2, 50)
    true_critical_point = 1.1
    
    # Generate S2 activation rates with sigmoid pattern
    s2_rates = 0.85 / (1 + np.exp(-4 * (cognitive_pressures - true_critical_point))) + 0.05
    s2_rates += np.random.normal(0, 0.03, len(s2_rates))  # Add noise
    s2_rates = np.clip(s2_rates, 0, 1)
    
    data = pd.DataFrame({
        'cognitive_pressure': cognitive_pressures,
        's2_activation_rate': s2_rates
    })
    
    # Test critical point detection
    detector = CriticalPointDetector(confidence_level=0.95)
    
    # Compare sigmoid models
    fit_results = detector.compare_sigmoid_models(data)
    
    if fit_results['comparison_successful']:
        best_result = fit_results['best_model_results']
        print(f"Best model: {fit_results['best_model_type']}")
        print(f"Critical point: {best_result['critical_point']:.3f} ± {best_result['critical_point_error']:.3f}")
        print(f"95% CI: [{best_result['confidence_interval'][0]:.3f}, {best_result['confidence_interval'][1]:.3f}]")
        print(f"R²: {best_result['r_squared']:.3f}")
        
        # Bootstrap analysis
        bootstrap_results = detector.detect_critical_point_bootstrap(data)
        if 'bootstrap_critical_point' in bootstrap_results:
            print(f"Bootstrap critical point: {bootstrap_results['bootstrap_critical_point']:.3f}")
            print(f"Bootstrap 95% CI: [{bootstrap_results['bootstrap_confidence_interval'][0]:.3f}, {bootstrap_results['bootstrap_confidence_interval'][1]:.3f}]")
        
        # Transition sharpness
        sharpness = detector.analyze_transition_sharpness(data, best_result['critical_point'])
        print(f"Transition width (25%-75%): {sharpness['transition_width_25_75']:.3f}")
        print(f"Sharpness score: {sharpness['sharpness_score']:.2f}")
        
        # Create detailed phase diagram
        detector.create_phase_diagram_detailed(data, fit_results)
    
    else:
        print("Failed to fit sigmoid models to data")


if __name__ == "__main__":
    main()