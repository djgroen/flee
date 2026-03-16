"""
H3.1 Phase Transition Detection

Implements algorithms for detecting phase transitions in cognitive mode activation
based on dimensionless parameter scaling.
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns


class PhaseTransitionDetector:
    """Detects phase transitions in S1/S2 cognitive mode activation."""
    
    def __init__(self):
        self.transition_models = {
            'sigmoid': self._sigmoid_model,
            'tanh': self._tanh_model,
            'step': self._step_model
        }
    
    @staticmethod
    def _sigmoid_model(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
        """
        Sigmoid transition model: y = a / (1 + exp(-b * (x - c))) + d
        
        Args:
            x: Cognitive pressure values
            a: Amplitude of transition
            b: Steepness of transition
            c: Critical point (inflection point)
            d: Baseline offset
        """
        return a / (1 + np.exp(-b * (x - c))) + d
    
    @staticmethod
    def _tanh_model(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
        """
        Hyperbolic tangent transition model: y = a * tanh(b * (x - c)) + d
        """
        return a * np.tanh(b * (x - c)) + d
    
    @staticmethod
    def _step_model(x: np.ndarray, a: float, c: float, d: float) -> np.ndarray:
        """
        Step function model: y = a * (x > c) + d
        """
        return a * (x > c) + d
    
    def calculate_s2_activation_rate(self, experiment_results: List[Dict]) -> pd.DataFrame:
        """
        Calculate S2 activation rate for each experiment.
        
        Args:
            experiment_results: List of experiment result dictionaries
            
        Returns:
            DataFrame with cognitive_pressure and s2_activation_rate columns
        """
        data = []
        
        for result in experiment_results:
            cognitive_pressure = result.get('cognitive_pressure', 0.0)
            
            # Extract S2 activation metrics from experiment results
            if 'cognitive_states' in result:
                cognitive_data = result['cognitive_states']
                total_decisions = len(cognitive_data)
                s2_decisions = len([d for d in cognitive_data if d.get('cognitive_state') == 'S2'])
                s2_rate = s2_decisions / total_decisions if total_decisions > 0 else 0.0
            else:
                # Fallback: use summary metrics if available
                s2_rate = result.get('s2_activation_rate', 0.0)
            
            data.append({
                'experiment_id': result.get('experiment_id', ''),
                'cognitive_pressure': cognitive_pressure,
                's2_activation_rate': s2_rate,
                'conflict_intensity': result.get('conflict_intensity', 0.0),
                'recovery_period': result.get('recovery_period', 30.0),
                'connectivity_rate': result.get('connectivity_rate', 0.0)
            })
        
        return pd.DataFrame(data)
    
    def fit_transition_model(self, data: pd.DataFrame, 
                           model_type: str = 'sigmoid') -> Dict:
        """
        Fit a transition model to the S2 activation data.
        
        Args:
            data: DataFrame with cognitive_pressure and s2_activation_rate
            model_type: Type of model to fit ('sigmoid', 'tanh', 'step')
            
        Returns:
            Dictionary with fit parameters and statistics
        """
        if model_type not in self.transition_models:
            raise ValueError(f"Unknown model type: {model_type}")
        
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        
        model_func = self.transition_models[model_type]
        
        try:
            if model_type == 'step':
                # Step function has fewer parameters
                initial_guess = [0.8, 1.0, 0.1]  # a, c, d
                bounds = ([0, 0, 0], [1, 5, 1])
            else:
                # Sigmoid and tanh models
                initial_guess = [0.8, 2.0, 1.0, 0.1]  # a, b, c, d
                bounds = ([0, 0, 0, 0], [1, 10, 5, 1])
            
            popt, pcov = curve_fit(model_func, x, y, 
                                 p0=initial_guess, 
                                 bounds=bounds,
                                 maxfev=5000)
            
            # Calculate fit statistics
            y_pred = model_func(x, *popt)
            r_squared = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
            rmse = np.sqrt(np.mean((y - y_pred) ** 2))
            
            # Extract critical point
            if model_type == 'step':
                critical_point = popt[1]  # c parameter
            else:
                critical_point = popt[2]  # c parameter (inflection point)
            
            return {
                'model_type': model_type,
                'parameters': popt.tolist(),
                'parameter_errors': np.sqrt(np.diag(pcov)).tolist(),
                'critical_point': critical_point,
                'r_squared': r_squared,
                'rmse': rmse,
                'fit_successful': True
            }
            
        except Exception as e:
            return {
                'model_type': model_type,
                'parameters': None,
                'critical_point': None,
                'r_squared': 0.0,
                'rmse': float('inf'),
                'fit_successful': False,
                'error': str(e)
            }
    
    def detect_phase_transition(self, data: pd.DataFrame) -> Dict:
        """
        Detect phase transition using multiple model approaches.
        
        Args:
            data: DataFrame with cognitive_pressure and s2_activation_rate
            
        Returns:
            Dictionary with transition detection results
        """
        results = {}
        
        # Fit all available models
        for model_type in self.transition_models.keys():
            results[model_type] = self.fit_transition_model(data, model_type)
        
        # Select best model based on R-squared
        best_model = max(results.keys(), 
                        key=lambda k: results[k]['r_squared'] if results[k]['fit_successful'] else -1)
        
        # Calculate additional transition metrics
        sorted_data = data.sort_values('cognitive_pressure')
        x = sorted_data['cognitive_pressure'].values
        y = sorted_data['s2_activation_rate'].values
        
        # Find steepest gradient (numerical derivative)
        if len(x) > 2:
            gradient = np.gradient(y, x)
            max_gradient_idx = np.argmax(gradient)
            steepest_point = x[max_gradient_idx]
        else:
            steepest_point = None
        
        # Find 50% activation point (interpolation)
        try:
            activation_50_idx = np.where(y >= 0.5)[0]
            if len(activation_50_idx) > 0:
                activation_50_point = x[activation_50_idx[0]]
            else:
                activation_50_point = None
        except:
            activation_50_point = None
        
        return {
            'model_fits': results,
            'best_model': best_model,
            'critical_point_best': results[best_model]['critical_point'],
            'steepest_gradient_point': steepest_point,
            'activation_50_point': activation_50_point,
            'transition_detected': results[best_model]['fit_successful'] and results[best_model]['r_squared'] > 0.7
        }
    
    def analyze_parameter_sensitivity(self, data: pd.DataFrame) -> Dict:
        """
        Analyze sensitivity of phase transition to individual parameters.
        
        Args:
            data: DataFrame with all parameter columns
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        correlations = {}
        
        # Calculate correlations between individual parameters and S2 activation
        for param in ['conflict_intensity', 'recovery_period', 'connectivity_rate']:
            if param in data.columns:
                corr, p_value = pearsonr(data[param], data['s2_activation_rate'])
                correlations[param] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }
        
        # Compare with cognitive pressure correlation
        if 'cognitive_pressure' in data.columns:
            corr, p_value = pearsonr(data['cognitive_pressure'], data['s2_activation_rate'])
            correlations['cognitive_pressure'] = {
                'correlation': corr,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        
        return {
            'parameter_correlations': correlations,
            'dimensionless_advantage': correlations.get('cognitive_pressure', {}).get('correlation', 0) > 
                                     max([correlations.get(p, {}).get('correlation', 0) 
                                         for p in ['conflict_intensity', 'recovery_period', 'connectivity_rate']])
        }
    
    def create_phase_diagram(self, data: pd.DataFrame, output_path: str = None) -> str:
        """
        Create phase diagram visualization.
        
        Args:
            data: DataFrame with experiment results
            output_path: Path to save the plot
            
        Returns:
            Path to saved plot
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Main phase transition plot
        ax1.scatter(data['cognitive_pressure'], data['s2_activation_rate'], 
                   alpha=0.6, s=50)
        ax1.set_xlabel('Cognitive Pressure')
        ax1.set_ylabel('S2 Activation Rate')
        ax1.set_title('Phase Transition: S2 Activation vs Cognitive Pressure')
        ax1.grid(True, alpha=0.3)
        
        # Fit and plot best model
        transition_results = self.detect_phase_transition(data)
        if transition_results['transition_detected']:
            x_smooth = np.linspace(data['cognitive_pressure'].min(), 
                                 data['cognitive_pressure'].max(), 100)
            best_model = transition_results['best_model']
            params = transition_results['model_fits'][best_model]['parameters']
            
            if params:
                model_func = self.transition_models[best_model]
                y_smooth = model_func(x_smooth, *params)
                ax1.plot(x_smooth, y_smooth, 'r-', linewidth=2, 
                        label=f'{best_model.capitalize()} fit')
                
                # Mark critical point
                critical_point = transition_results['critical_point_best']
                if critical_point:
                    ax1.axvline(critical_point, color='red', linestyle='--', 
                              label=f'Critical point: {critical_point:.2f}')
        
        ax1.legend()
        
        # Parameter correlation heatmap
        param_cols = ['conflict_intensity', 'recovery_period', 'connectivity_rate', 'cognitive_pressure']
        available_cols = [col for col in param_cols if col in data.columns]
        if len(available_cols) > 1:
            corr_matrix = data[available_cols + ['s2_activation_rate']].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax2)
            ax2.set_title('Parameter Correlation Matrix')
        
        # Individual parameter effects
        if 'conflict_intensity' in data.columns:
            ax3.scatter(data['conflict_intensity'], data['s2_activation_rate'], alpha=0.6)
            ax3.set_xlabel('Conflict Intensity')
            ax3.set_ylabel('S2 Activation Rate')
            ax3.set_title('S2 Activation vs Conflict Intensity')
            ax3.grid(True, alpha=0.3)
        
        if 'connectivity_rate' in data.columns:
            ax4.scatter(data['connectivity_rate'], data['s2_activation_rate'], alpha=0.6)
            ax4.set_xlabel('Connectivity Rate')
            ax4.set_ylabel('S2 Activation Rate')
            ax4.set_title('S2 Activation vs Connectivity Rate')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None


def main():
    """Example usage of phase transition detection."""
    # Generate sample data for testing
    np.random.seed(42)
    
    # Create synthetic data with phase transition
    cognitive_pressures = np.linspace(0, 3, 50)
    s2_rates = 0.8 / (1 + np.exp(-3 * (cognitive_pressures - 1.2))) + 0.1
    s2_rates += np.random.normal(0, 0.05, len(s2_rates))  # Add noise
    s2_rates = np.clip(s2_rates, 0, 1)
    
    data = pd.DataFrame({
        'cognitive_pressure': cognitive_pressures,
        's2_activation_rate': s2_rates,
        'conflict_intensity': np.random.uniform(0.1, 0.9, len(cognitive_pressures)),
        'recovery_period': np.random.uniform(10, 50, len(cognitive_pressures)),
        'connectivity_rate': np.random.uniform(0, 8, len(cognitive_pressures))
    })
    
    # Test phase transition detection
    detector = PhaseTransitionDetector()
    results = detector.detect_phase_transition(data)
    
    print("Phase Transition Detection Results:")
    print(f"Best model: {results['best_model']}")
    print(f"Critical point: {results['critical_point_best']:.3f}")
    print(f"Transition detected: {results['transition_detected']}")
    
    # Test sensitivity analysis
    sensitivity = detector.analyze_parameter_sensitivity(data)
    print(f"\nDimensionless parameter advantage: {sensitivity['dimensionless_advantage']}")
    
    # Create visualization
    detector.create_phase_diagram(data)


if __name__ == "__main__":
    main()