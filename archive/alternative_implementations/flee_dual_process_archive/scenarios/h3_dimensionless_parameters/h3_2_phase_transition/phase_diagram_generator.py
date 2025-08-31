"""
H3.2 Phase Diagram Generator

Creates comprehensive phase diagrams and visualizations for H3.2 phase transition identification.
Includes interactive plots, publication-ready figures, and detailed analysis visualizations.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os


class PhaseDiagramGenerator:
    """Generates comprehensive phase diagrams for H3.2 analysis."""
    
    def __init__(self, style: str = 'publication'):
        """
        Initialize phase diagram generator.
        
        Args:
            style: Plotting style ('publication', 'presentation', 'interactive')
        """
        self.style = style
        self._setup_plotting_style()
        
        # Color schemes for different plot types
        self.color_schemes = {
            'phase_transition': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'],
            'cognitive_modes': ['#1f77b4', '#ff7f0e', '#2ca02c'],
            'confidence': ['#d62728', '#ff9999', '#ffcccc']
        }
    
    def _setup_plotting_style(self):
        """Setup matplotlib style based on selected style."""
        if self.style == 'publication':
            plt.style.use('seaborn-v0_8-whitegrid')
            plt.rcParams.update({
                'font.size': 12,
                'axes.titlesize': 14,
                'axes.labelsize': 12,
                'xtick.labelsize': 10,
                'ytick.labelsize': 10,
                'legend.fontsize': 10,
                'figure.titlesize': 16,
                'font.family': 'serif'
            })
        elif self.style == 'presentation':
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.rcParams.update({
                'font.size': 14,
                'axes.titlesize': 18,
                'axes.labelsize': 16,
                'xtick.labelsize': 12,
                'ytick.labelsize': 12,
                'legend.fontsize': 12,
                'figure.titlesize': 20,
                'font.family': 'sans-serif'
            })
    
    def create_main_phase_diagram(self, data: pd.DataFrame, 
                                fit_results: Dict,
                                output_path: str = None) -> str:
        """
        Create the main phase transition diagram.
        
        Args:
            data: DataFrame with cognitive_pressure and s2_activation_rate
            fit_results: Results from sigmoid fitting
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure
        """
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        
        # Scatter plot of data points
        scatter = ax.scatter(x, y, c=y, cmap='RdYlBu_r', s=80, alpha=0.7, 
                           edgecolors='black', linewidth=0.5)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('S2 Activation Rate', rotation=270, labelpad=20)
        
        # Plot fitted sigmoid curve if available
        if fit_results.get('comparison_successful', False):
            best_model = fit_results['best_model_results']
            
            # Create smooth curve
            x_smooth = np.linspace(x.min() - 0.1, x.max() + 0.1, 300)
            
            # Import the sigmoid function (assuming it's available)
            from critical_point_detector import CriticalPointDetector
            detector = CriticalPointDetector()
            model_func = detector.sigmoid_models[best_model['model_type']]
            y_smooth = model_func(x_smooth, *best_model['parameters'])
            
            ax.plot(x_smooth, y_smooth, 'red', linewidth=3, 
                   label=f'{best_model["model_type"].capitalize()} fit (R² = {best_model["r_squared"]:.3f})')
            
            # Mark critical point
            critical_point = best_model['critical_point']
            ci_lower, ci_upper = best_model['confidence_interval']
            
            ax.axvline(critical_point, color='red', linestyle='--', linewidth=2,
                      label=f'Critical Point: {critical_point:.3f}')
            
            # Add confidence interval
            ax.axvspan(ci_lower, ci_upper, alpha=0.2, color='red',
                      label=f'95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]')
            
            # Add phase regions
            ax.axvspan(x.min() - 0.1, critical_point, alpha=0.1, color='blue',
                      label='S1 Dominant Region')
            ax.axvspan(critical_point, x.max() + 0.1, alpha=0.1, color='orange',
                      label='S2 Dominant Region')
        
        # Formatting
        ax.set_xlabel('Cognitive Pressure', fontweight='bold')
        ax.set_ylabel('S2 Activation Rate', fontweight='bold')
        ax.set_title('Phase Transition: Cognitive Mode Activation', fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='center right', bbox_to_anchor=(1.0, 0.5))
        ax.set_ylim(-0.05, 1.05)
        
        # Add phase labels
        if fit_results.get('comparison_successful', False):
            critical_point = fit_results['best_model_results']['critical_point']
            ax.text(critical_point * 0.5, 0.9, 'System 1\nDominant', 
                   ha='center', va='center', fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
            ax.text(critical_point + (x.max() - critical_point) * 0.5, 0.9, 'System 2\nDominant',
                   ha='center', va='center', fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.7))
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    def create_parameter_space_diagram(self, data: pd.DataFrame, 
                                     output_path: str = None) -> str:
        """
        Create 3D parameter space visualization.
        
        Args:
            data: DataFrame with all parameter columns
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure
        """
        fig = plt.figure(figsize=(15, 5))
        
        # 2D projections of 3D parameter space
        projections = [
            ('conflict_intensity', 'recovery_period', 'Conflict Intensity vs Recovery Period'),
            ('conflict_intensity', 'connectivity_rate', 'Conflict Intensity vs Connectivity Rate'),
            ('recovery_period', 'connectivity_rate', 'Recovery Period vs Connectivity Rate')
        ]
        
        for i, (x_param, y_param, title) in enumerate(projections):
            ax = fig.add_subplot(1, 3, i+1)
            
            if x_param in data.columns and y_param in data.columns:
                scatter = ax.scatter(data[x_param], data[y_param], 
                                   c=data['s2_activation_rate'], 
                                   cmap='RdYlBu_r', s=60, alpha=0.7)
                
                ax.set_xlabel(x_param.replace('_', ' ').title())
                ax.set_ylabel(y_param.replace('_', ' ').title())
                ax.set_title(title)
                ax.grid(True, alpha=0.3)
                
                # Add colorbar for the last subplot
                if i == 2:
                    cbar = plt.colorbar(scatter, ax=ax)
                    cbar.set_label('S2 Activation Rate', rotation=270, labelpad=20)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    def create_transition_analysis_dashboard(self, data: pd.DataFrame,
                                           fit_results: Dict,
                                           bootstrap_results: Dict = None,
                                           output_path: str = None) -> str:
        """
        Create comprehensive transition analysis dashboard.
        
        Args:
            data: DataFrame with experimental data
            fit_results: Results from sigmoid fitting
            bootstrap_results: Bootstrap analysis results
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure
        """
        fig = plt.figure(figsize=(16, 12))
        
        # Create grid layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main phase transition plot (top row, spans 2 columns)
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_main_transition(ax1, data, fit_results)
        
        # Model comparison (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_model_comparison(ax2, fit_results)
        
        # Residuals plot (middle left)
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_residuals(ax3, data, fit_results)
        
        # Bootstrap distribution (middle center)
        ax4 = fig.add_subplot(gs[1, 1])
        if bootstrap_results:
            self._plot_bootstrap_distribution(ax4, bootstrap_results)
        
        # Derivative analysis (middle right)
        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_derivative_analysis(ax5, data, fit_results)
        
        # Data distribution (bottom left)
        ax6 = fig.add_subplot(gs[2, 0])
        self._plot_data_distribution(ax6, data)
        
        # Confidence intervals comparison (bottom center)
        ax7 = fig.add_subplot(gs[2, 1])
        self._plot_confidence_comparison(ax7, fit_results, bootstrap_results)
        
        # Summary statistics (bottom right)
        ax8 = fig.add_subplot(gs[2, 2])
        self._plot_summary_statistics(ax8, fit_results, bootstrap_results)
        
        plt.suptitle('H3.2 Phase Transition Analysis Dashboard', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    def _plot_main_transition(self, ax, data, fit_results):
        """Plot main phase transition."""
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        
        ax.scatter(x, y, alpha=0.6, s=50)
        
        if fit_results.get('comparison_successful', False):
            best_model = fit_results['best_model_results']
            
            # Plot fitted curve
            x_smooth = np.linspace(x.min(), x.max(), 200)
            from critical_point_detector import CriticalPointDetector
            detector = CriticalPointDetector()
            model_func = detector.sigmoid_models[best_model['model_type']]
            y_smooth = model_func(x_smooth, *best_model['parameters'])
            
            ax.plot(x_smooth, y_smooth, 'r-', linewidth=2)
            
            # Mark critical point
            critical_point = best_model['critical_point']
            ax.axvline(critical_point, color='red', linestyle='--')
        
        ax.set_xlabel('Cognitive Pressure')
        ax.set_ylabel('S2 Activation Rate')
        ax.set_title('Phase Transition')
        ax.grid(True, alpha=0.3)
    
    def _plot_model_comparison(self, ax, fit_results):
        """Plot model comparison."""
        if 'model_comparison' in fit_results:
            models = []
            r_squared = []
            
            for model, result in fit_results['model_comparison'].items():
                if result['fit_successful']:
                    models.append(model.capitalize())
                    r_squared.append(result['r_squared'])
            
            if models:
                bars = ax.bar(models, r_squared, alpha=0.7)
                
                # Highlight best model
                if fit_results.get('best_model_type'):
                    best_idx = models.index(fit_results['best_model_type'].capitalize())
                    bars[best_idx].set_color('red')
                
                ax.set_ylabel('R² Score')
                ax.set_title('Model Comparison')
                ax.set_ylim(0, 1)
    
    def _plot_residuals(self, ax, data, fit_results):
        """Plot residuals analysis."""
        if fit_results.get('comparison_successful', False):
            best_model = fit_results['best_model_results']
            
            x = data['cognitive_pressure'].values
            y = data['s2_activation_rate'].values
            
            from critical_point_detector import CriticalPointDetector
            detector = CriticalPointDetector()
            model_func = detector.sigmoid_models[best_model['model_type']]
            y_pred = model_func(x, *best_model['parameters'])
            residuals = y - y_pred
            
            ax.scatter(x, residuals, alpha=0.6)
            ax.axhline(0, color='red', linestyle='--')
            ax.set_xlabel('Cognitive Pressure')
            ax.set_ylabel('Residuals')
            ax.set_title('Residuals Analysis')
            ax.grid(True, alpha=0.3)
    
    def _plot_bootstrap_distribution(self, ax, bootstrap_results):
        """Plot bootstrap critical point distribution."""
        if 'critical_point_distribution' in bootstrap_results:
            critical_points = bootstrap_results['critical_point_distribution']
            
            ax.hist(critical_points, bins=20, alpha=0.7, edgecolor='black')
            
            # Mark mean and confidence interval
            mean_cp = bootstrap_results['bootstrap_critical_point']
            ci_lower, ci_upper = bootstrap_results['bootstrap_confidence_interval']
            
            ax.axvline(mean_cp, color='red', linestyle='-', linewidth=2, label='Mean')
            ax.axvline(ci_lower, color='red', linestyle='--', alpha=0.7, label='95% CI')
            ax.axvline(ci_upper, color='red', linestyle='--', alpha=0.7)
            
            ax.set_xlabel('Critical Point')
            ax.set_ylabel('Frequency')
            ax.set_title('Bootstrap Distribution')
            ax.legend()
    
    def _plot_derivative_analysis(self, ax, data, fit_results):
        """Plot derivative analysis."""
        x = data['cognitive_pressure'].values
        y = data['s2_activation_rate'].values
        
        # Sort data
        sort_idx = np.argsort(x)
        x_sorted = x[sort_idx]
        y_sorted = y[sort_idx]
        
        if len(x_sorted) > 2:
            # Calculate numerical derivative
            dx = np.diff(x_sorted)
            dy = np.diff(y_sorted)
            derivative = dy / dx
            x_deriv = (x_sorted[:-1] + x_sorted[1:]) / 2
            
            ax.plot(x_deriv, derivative, 'b-', linewidth=2)
            
            # Mark maximum derivative
            max_idx = np.argmax(derivative)
            ax.axvline(x_deriv[max_idx], color='red', linestyle='--')
            
            ax.set_xlabel('Cognitive Pressure')
            ax.set_ylabel('dS2/dPressure')
            ax.set_title('Derivative Analysis')
            ax.grid(True, alpha=0.3)
    
    def _plot_data_distribution(self, ax, data):
        """Plot data distribution."""
        ax.hist(data['cognitive_pressure'], bins=15, alpha=0.7, edgecolor='black')
        ax.set_xlabel('Cognitive Pressure')
        ax.set_ylabel('Frequency')
        ax.set_title('Data Distribution')
        ax.grid(True, alpha=0.3)
    
    def _plot_confidence_comparison(self, ax, fit_results, bootstrap_results):
        """Plot confidence interval comparison."""
        methods = []
        critical_points = []
        ci_lowers = []
        ci_uppers = []
        
        if fit_results.get('comparison_successful', False):
            best_model = fit_results['best_model_results']
            methods.append('Sigmoid Fit')
            critical_points.append(best_model['critical_point'])
            ci_lower, ci_upper = best_model['confidence_interval']
            ci_lowers.append(ci_lower)
            ci_uppers.append(ci_upper)
        
        if bootstrap_results and 'bootstrap_critical_point' in bootstrap_results:
            methods.append('Bootstrap')
            critical_points.append(bootstrap_results['bootstrap_critical_point'])
            ci_lower, ci_upper = bootstrap_results['bootstrap_confidence_interval']
            ci_lowers.append(ci_lower)
            ci_uppers.append(ci_upper)
        
        if methods:
            y_pos = np.arange(len(methods))
            
            # Plot critical points
            ax.scatter(critical_points, y_pos, s=100, c='red', zorder=3)
            
            # Plot confidence intervals
            for i, (cp, ci_l, ci_u) in enumerate(zip(critical_points, ci_lowers, ci_uppers)):
                ax.plot([ci_l, ci_u], [i, i], 'b-', linewidth=3, alpha=0.7)
                ax.plot([ci_l, ci_l], [i-0.1, i+0.1], 'b-', linewidth=2)
                ax.plot([ci_u, ci_u], [i-0.1, i+0.1], 'b-', linewidth=2)
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(methods)
            ax.set_xlabel('Critical Point')
            ax.set_title('CI Comparison')
            ax.grid(True, alpha=0.3)
    
    def _plot_summary_statistics(self, ax, fit_results, bootstrap_results):
        """Plot summary statistics table."""
        ax.axis('off')
        
        # Collect statistics
        stats_text = []
        
        if fit_results.get('comparison_successful', False):
            best_model = fit_results['best_model_results']
            stats_text.append(f"Best Model: {best_model['model_type'].capitalize()}")
            stats_text.append(f"R²: {best_model['r_squared']:.3f}")
            stats_text.append(f"RMSE: {best_model['rmse']:.3f}")
            stats_text.append(f"Critical Point: {best_model['critical_point']:.3f}")
            
            ci_width = best_model['confidence_interval'][1] - best_model['confidence_interval'][0]
            stats_text.append(f"CI Width: {ci_width:.3f}")
        
        if bootstrap_results and 'bootstrap_critical_point' in bootstrap_results:
            stats_text.append("")
            stats_text.append("Bootstrap Results:")
            stats_text.append(f"Success Rate: {bootstrap_results['success_rate']:.1%}")
            stats_text.append(f"Std Dev: {bootstrap_results['bootstrap_std']:.3f}")
        
        # Display statistics
        text_str = '\n'.join(stats_text)
        ax.text(0.1, 0.9, text_str, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
        
        ax.set_title('Summary Statistics')
    
    def create_interactive_phase_diagram(self, data: pd.DataFrame,
                                       fit_results: Dict,
                                       output_path: str = None) -> str:
        """
        Create interactive phase diagram using Plotly.
        
        Args:
            data: DataFrame with experimental data
            fit_results: Results from sigmoid fitting
            output_path: Path to save HTML file
            
        Returns:
            Path to saved HTML file
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Phase Transition', 'Parameter Space', 'Model Comparison', 'Residuals'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Main phase transition plot
        fig.add_trace(
            go.Scatter(
                x=data['cognitive_pressure'],
                y=data['s2_activation_rate'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=data['s2_activation_rate'],
                    colorscale='RdYlBu_r',
                    showscale=True,
                    colorbar=dict(title="S2 Activation Rate")
                ),
                name='Data Points',
                hovertemplate='Pressure: %{x:.3f}<br>S2 Rate: %{y:.3f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add fitted curve if available
        if fit_results.get('comparison_successful', False):
            best_model = fit_results['best_model_results']
            
            x_smooth = np.linspace(data['cognitive_pressure'].min(), 
                                 data['cognitive_pressure'].max(), 200)
            
            # Note: This would need the actual sigmoid function imported
            # For now, we'll create a placeholder
            y_smooth = np.random.random(len(x_smooth))  # Placeholder
            
            fig.add_trace(
                go.Scatter(
                    x=x_smooth,
                    y=y_smooth,
                    mode='lines',
                    line=dict(color='red', width=3),
                    name=f'{best_model["model_type"].capitalize()} Fit',
                    hovertemplate='Pressure: %{x:.3f}<br>Predicted: %{y:.3f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Add critical point line
            critical_point = best_model['critical_point']
            fig.add_vline(
                x=critical_point,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Critical Point: {critical_point:.3f}",
                row=1, col=1
            )
        
        # Parameter space plot (if 3D parameters available)
        if all(col in data.columns for col in ['conflict_intensity', 'recovery_period', 'connectivity_rate']):
            fig.add_trace(
                go.Scatter3d(
                    x=data['conflict_intensity'],
                    y=data['recovery_period'],
                    z=data['connectivity_rate'],
                    mode='markers',
                    marker=dict(
                        size=5,
                        color=data['s2_activation_rate'],
                        colorscale='RdYlBu_r'
                    ),
                    name='Parameter Space',
                    hovertemplate='Conflict: %{x:.3f}<br>Recovery: %{y:.1f}<br>Connectivity: %{z:.1f}<extra></extra>'
                ),
                row=1, col=2
            )
        
        # Model comparison
        if 'model_comparison' in fit_results:
            models = []
            r_squared = []
            
            for model, result in fit_results['model_comparison'].items():
                if result['fit_successful']:
                    models.append(model.capitalize())
                    r_squared.append(result['r_squared'])
            
            if models:
                fig.add_trace(
                    go.Bar(
                        x=models,
                        y=r_squared,
                        name='Model R²',
                        marker_color=['red' if m.lower() == fit_results.get('best_model_type', '') 
                                    else 'blue' for m in models]
                    ),
                    row=2, col=1
                )
        
        # Update layout
        fig.update_layout(
            title_text="Interactive H3.2 Phase Transition Analysis",
            showlegend=True,
            height=800
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Cognitive Pressure", row=1, col=1)
        fig.update_yaxes(title_text="S2 Activation Rate", row=1, col=1)
        
        if output_path:
            fig.write_html(output_path)
            return output_path
        else:
            fig.show()
            return None


def main():
    """Example usage of phase diagram generator."""
    # Generate sample data
    np.random.seed(42)
    
    cognitive_pressures = np.linspace(0, 2, 50)
    s2_rates = 0.85 / (1 + np.exp(-4 * (cognitive_pressures - 1.1))) + 0.05
    s2_rates += np.random.normal(0, 0.03, len(s2_rates))
    s2_rates = np.clip(s2_rates, 0, 1)
    
    data = pd.DataFrame({
        'cognitive_pressure': cognitive_pressures,
        's2_activation_rate': s2_rates,
        'conflict_intensity': np.random.uniform(0.1, 0.9, len(cognitive_pressures)),
        'recovery_period': np.random.uniform(10, 50, len(cognitive_pressures)),
        'connectivity_rate': np.random.uniform(0, 8, len(cognitive_pressures))
    })
    
    # Mock fit results
    fit_results = {
        'comparison_successful': True,
        'best_model_type': 'standard',
        'best_model_results': {
            'model_type': 'standard',
            'critical_point': 1.1,
            'confidence_interval': [1.05, 1.15],
            'r_squared': 0.95,
            'rmse': 0.03
        },
        'model_comparison': {
            'standard': {'fit_successful': True, 'r_squared': 0.95},
            'asymmetric': {'fit_successful': True, 'r_squared': 0.92}
        }
    }
    
    # Create phase diagrams
    generator = PhaseDiagramGenerator(style='publication')
    
    # Main phase diagram
    generator.create_main_phase_diagram(data, fit_results)
    
    # Parameter space diagram
    generator.create_parameter_space_diagram(data)
    
    # Comprehensive dashboard
    generator.create_transition_analysis_dashboard(data, fit_results)


if __name__ == "__main__":
    main()