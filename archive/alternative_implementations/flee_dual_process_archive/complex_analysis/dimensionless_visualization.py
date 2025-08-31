"""
Dimensionless Parameter Visualization Framework

This module provides comprehensive visualization tools for dimensionless parameter
analysis, including data collapse plots, universal scaling curves, and publication-ready
figures for dual-process refugee movement experiments.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import warnings
from scipy import stats
from scipy.optimize import curve_fit
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
# Optional plotly imports
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None
    pyo = None

from flee_dual_process.dimensionless_analysis import (
    DimensionlessParameterCalculator,
    UniversalScalingDetector,
    ScalingRelationship
)


@dataclass
class PlotConfiguration:
    """Configuration for plot styling and formatting."""
    figsize: Tuple[float, float] = (10, 8)
    dpi: int = 300
    style: str = 'seaborn-v0_8-whitegrid'
    color_palette: str = 'Set2'
    font_size: int = 12
    title_size: int = 14
    label_size: int = 12
    legend_size: int = 10
    line_width: float = 2.0
    marker_size: float = 50
    alpha: float = 0.7
    save_format: str = 'png'
    save_dpi: int = 300


class DimensionlessVisualizationGenerator:
    """
    Generator for dimensionless parameter visualizations.
    
    Creates publication-ready plots for dimensionless parameter analysis,
    including data collapse visualization, scaling relationships, and
    parameter sensitivity analysis.
    """
    
    def __init__(self, config: Optional[PlotConfiguration] = None):
        """
        Initialize the visualization generator.
        
        Args:
            config: Plot configuration settings
        """
        self.config = config or PlotConfiguration()
        self.calculator = DimensionlessParameterCalculator()
        self.detector = UniversalScalingDetector()
        
        # Set up matplotlib style
        plt.style.use(self.config.style)
        sns.set_palette(self.config.color_palette)
        
        # Configure matplotlib parameters
        plt.rcParams.update({
            'font.size': self.config.font_size,
            'axes.titlesize': self.config.title_size,
            'axes.labelsize': self.config.label_size,
            'legend.fontsize': self.config.legend_size,
            'lines.linewidth': self.config.line_width,
            'lines.markersize': np.sqrt(self.config.marker_size),
            'figure.dpi': self.config.dpi,
            'savefig.dpi': self.config.save_dpi,
            'savefig.format': self.config.save_format
        })
    
    def create_data_collapse_plot(self, 
                                data: pd.DataFrame,
                                dimensionless_param: str,
                                dependent_variable: str,
                                grouping_column: str,
                                title: Optional[str] = None,
                                save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a data collapse plot showing universal scaling.
        
        Args:
            data: DataFrame containing experimental data
            dimensionless_param: Name of dimensionless parameter column
            dependent_variable: Name of dependent variable column
            grouping_column: Column to group data by (should collapse)
            title: Plot title
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Check if required columns exist
        missing_cols = []
        for col in [dimensionless_param, dependent_variable, grouping_column]:
            if col not in data.columns:
                missing_cols.append(col)
        
        if missing_cols:
            # Create empty plots with error message
            ax1.text(0.5, 0.5, f'Missing columns: {", ".join(missing_cols)}', 
                    ha='center', va='center', transform=ax1.transAxes)
            ax2.text(0.5, 0.5, f'Missing columns: {", ".join(missing_cols)}', 
                    ha='center', va='center', transform=ax2.transAxes)
            ax1.set_title('Data Not Available')
            ax2.set_title('Data Not Available')
            return fig
        
        # Get unique groups
        groups = data[grouping_column].unique()
        colors = sns.color_palette(self.config.color_palette, len(groups))
        
        # Plot 1: Before collapse (separate curves)
        for i, group in enumerate(groups):
            group_data = data[data[grouping_column] == group]
            if len(group_data) > 0:
                ax1.scatter(group_data[dimensionless_param], 
                           group_data[dependent_variable],
                           color=colors[i], 
                           label=f'{grouping_column}={group}',
                           alpha=self.config.alpha,
                           s=self.config.marker_size)
        
        ax1.set_xlabel(f'{dimensionless_param}')
        ax1.set_ylabel(f'{dependent_variable}')
        ax1.set_title('Before Collapse: Separate Curves')
        ax1.legend()
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: After collapse (single curve)
        # Normalize data to demonstrate collapse
        collapsed_data = []
        for group in groups:
            group_data = data[data[grouping_column] == group].copy()
            if len(group_data) > 0:
                # Simple normalization by group mean
                group_mean = group_data[dependent_variable].mean()
                if group_mean > 0:
                    group_data[f'{dependent_variable}_normalized'] = (
                        group_data[dependent_variable] / group_mean
                    )
                    collapsed_data.append(group_data)
        
        if collapsed_data:
            collapsed_df = pd.concat(collapsed_data, ignore_index=True)
            
            # Plot collapsed data
            ax2.scatter(collapsed_df[dimensionless_param], 
                       collapsed_df[f'{dependent_variable}_normalized'],
                       alpha=self.config.alpha,
                       s=self.config.marker_size,
                       c='blue')
            
            # Fit and plot scaling curve
            x_vals = collapsed_df[dimensionless_param].values
            y_vals = collapsed_df[f'{dependent_variable}_normalized'].values
            
            # Remove any invalid values
            valid_mask = (x_vals > 0) & (y_vals > 0) & np.isfinite(x_vals) & np.isfinite(y_vals)
            x_clean = x_vals[valid_mask]
            y_clean = y_vals[valid_mask]
            
            if len(x_clean) > 3:
                try:
                    # Fit power law
                    log_x = np.log(x_clean)
                    log_y = np.log(y_clean)
                    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
                    
                    # Plot fit line
                    x_fit = np.logspace(np.log10(x_clean.min()), np.log10(x_clean.max()), 100)
                    y_fit = np.exp(intercept) * np.power(x_fit, slope)
                    ax2.plot(x_fit, y_fit, 'r-', linewidth=2, 
                            label=f'Power law fit: y ∝ x^{slope:.2f} (R²={r_value**2:.3f})')
                    ax2.legend()
                except Exception:
                    pass
        
        ax2.set_xlabel(f'{dimensionless_param}')
        ax2.set_ylabel(f'{dependent_variable} (normalized)')
        ax2.set_title('After Collapse: Universal Curve')
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax2.grid(True, alpha=0.3)
        
        if title:
            fig.suptitle(title, fontsize=self.config.title_size + 2)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.save_dpi, bbox_inches='tight')
        
        return fig
    
    def create_scaling_relationship_plot(self, 
                                       data: pd.DataFrame,
                                       relationships: List[ScalingRelationship],
                                       title: Optional[str] = None,
                                       save_path: Optional[str] = None) -> plt.Figure:
        """
        Create plots showing universal scaling relationships.
        
        Args:
            data: DataFrame containing experimental data
            relationships: List of detected scaling relationships
            title: Plot title
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        n_relationships = len(relationships)
        if n_relationships == 0:
            raise ValueError("No scaling relationships provided")
        
        # Create subplots
        n_cols = min(3, n_relationships)
        n_rows = (n_relationships + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        
        if n_relationships == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for i, relationship in enumerate(relationships):
            ax = axes[i]
            
            # Get data for this relationship
            x_col = relationship.parameter
            y_col = relationship.dependent_variable
            
            if x_col not in data.columns or y_col not in data.columns:
                ax.text(0.5, 0.5, f'Data not available\nfor {x_col} vs {y_col}', 
                       ha='center', va='center', transform=ax.transAxes)
                continue
            
            # Clean data
            plot_data = data.dropna(subset=[x_col, y_col])
            plot_data = plot_data[
                (plot_data[x_col] > 0) & 
                (plot_data[y_col] > 0) &
                np.isfinite(plot_data[x_col]) &
                np.isfinite(plot_data[y_col])
            ]
            
            if len(plot_data) == 0:
                ax.text(0.5, 0.5, 'No valid data points', 
                       ha='center', va='center', transform=ax.transAxes)
                continue
            
            x_vals = plot_data[x_col].values
            y_vals = plot_data[y_col].values
            
            # Plot data points
            ax.scatter(x_vals, y_vals, alpha=self.config.alpha, 
                      s=self.config.marker_size, color='blue')
            
            # Plot fitted curve
            x_range = np.logspace(np.log10(x_vals.min()), np.log10(x_vals.max()), 100)
            
            try:
                if relationship.scaling_function == 'linear':
                    a = relationship.fit_parameters.get('a', 1.0)
                    b = relationship.fit_parameters.get('b', 0.0)
                    y_fit = a * x_range + b
                    func_str = f'y = {a:.2f}x + {b:.2f}'
                    
                elif relationship.scaling_function == 'power_law':
                    a = relationship.fit_parameters.get('a', 1.0)
                    b = relationship.fit_parameters.get('b', 1.0)
                    y_fit = a * np.power(x_range, b)
                    func_str = f'y = {a:.2f}x^{b:.2f}'
                    
                elif relationship.scaling_function == 'exponential':
                    a = relationship.fit_parameters.get('a', 1.0)
                    b = relationship.fit_parameters.get('b', 1.0)
                    y_fit = a * np.exp(b * x_range)
                    func_str = f'y = {a:.2f}exp({b:.2f}x)'
                    
                elif relationship.scaling_function == 'sigmoid':
                    a = relationship.fit_parameters.get('a', 1.0)
                    b = relationship.fit_parameters.get('b', 1.0)
                    c = relationship.fit_parameters.get('c', 0.5)
                    y_fit = a / (1 + np.exp(-b * (x_range - c)))
                    func_str = f'y = {a:.2f}/(1+exp(-{b:.2f}(x-{c:.2f})))'
                    
                else:
                    y_fit = None
                    func_str = relationship.scaling_function
                
                if y_fit is not None:
                    ax.plot(x_range, y_fit, 'r-', linewidth=2, 
                           label=f'{func_str}\nR² = {relationship.r_squared:.3f}')
                    ax.legend()
                    
            except Exception as e:
                ax.text(0.1, 0.9, f'Fit error: {str(e)[:30]}...', 
                       transform=ax.transAxes, fontsize=8)
            
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.set_title(f'{relationship.scaling_function.replace("_", " ").title()} Scaling')
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(n_relationships, len(axes)):
            axes[i].set_visible(False)
        
        if title:
            fig.suptitle(title, fontsize=self.config.title_size + 2)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.save_dpi, bbox_inches='tight')
        
        return fig
    
    def create_parameter_sensitivity_heatmap(self, 
                                           data: pd.DataFrame,
                                           dimensionless_params: List[str],
                                           dependent_variables: List[str],
                                           title: Optional[str] = None,
                                           save_path: Optional[str] = None) -> plt.Figure:
        """
        Create heatmap showing parameter sensitivity analysis.
        
        Args:
            data: DataFrame containing experimental data
            dimensionless_params: List of dimensionless parameter columns
            dependent_variables: List of dependent variable columns
            title: Plot title
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        # Calculate correlation matrix
        all_params = dimensionless_params + dependent_variables
        available_params = [p for p in all_params if p in data.columns]
        
        if len(available_params) < 2:
            raise ValueError("Need at least 2 parameters for sensitivity analysis")
        
        correlation_data = data[available_params].corr()
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Correlation heatmap
        mask = np.triu(np.ones_like(correlation_data, dtype=bool))
        sns.heatmap(correlation_data, mask=mask, annot=True, cmap='RdBu_r', 
                   center=0, square=True, ax=ax1, cbar_kws={'shrink': 0.8})
        ax1.set_title('Parameter Correlation Matrix')
        
        # Plot 2: Sensitivity analysis (effect sizes)
        sensitivity_matrix = np.zeros((len(dimensionless_params), len(dependent_variables)))
        param_labels = []
        var_labels = []
        
        for i, dim_param in enumerate(dimensionless_params):
            if dim_param not in data.columns:
                continue
            param_labels.append(dim_param.replace('_', ' ').title())
            
            for j, dep_var in enumerate(dependent_variables):
                if dep_var not in data.columns:
                    continue
                if j == 0:  # Only add labels once
                    var_labels.append(dep_var.replace('_', ' ').title())
                
                # Calculate effect size (correlation coefficient)
                clean_data = data.dropna(subset=[dim_param, dep_var])
                if len(clean_data) > 3:
                    try:
                        corr, p_value = stats.pearsonr(clean_data[dim_param], clean_data[dep_var])
                        # Use absolute correlation as effect size
                        sensitivity_matrix[i, j] = abs(corr) if p_value < 0.05 else 0
                    except Exception:
                        sensitivity_matrix[i, j] = 0
        
        # Plot sensitivity heatmap
        if len(param_labels) > 0 and len(var_labels) > 0:
            im = ax2.imshow(sensitivity_matrix[:len(param_labels), :len(var_labels)], 
                           cmap='Reds', aspect='auto', vmin=0, vmax=1)
            
            ax2.set_xticks(range(len(var_labels)))
            ax2.set_yticks(range(len(param_labels)))
            ax2.set_xticklabels(var_labels, rotation=45, ha='right')
            ax2.set_yticklabels(param_labels)
            ax2.set_title('Parameter Sensitivity (|Correlation|)')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax2, shrink=0.8)
            cbar.set_label('Effect Size')
            
            # Add text annotations
            for i in range(len(param_labels)):
                for j in range(len(var_labels)):
                    if i < sensitivity_matrix.shape[0] and j < sensitivity_matrix.shape[1]:
                        text = f'{sensitivity_matrix[i, j]:.2f}'
                        ax2.text(j, i, text, ha='center', va='center',
                               color='white' if sensitivity_matrix[i, j] > 0.5 else 'black')
        
        if title:
            fig.suptitle(title, fontsize=self.config.title_size + 2)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.save_dpi, bbox_inches='tight')
        
        return fig
    
    def create_dimensionless_parameter_table(self, 
                                           data: pd.DataFrame,
                                           dimensionless_params: List[str],
                                           save_path: Optional[str] = None) -> pd.DataFrame:
        """
        Create publication-ready table of dimensionless parameters.
        
        Args:
            data: DataFrame containing experimental data
            dimensionless_params: List of dimensionless parameter columns
            save_path: Path to save the table (CSV format)
            
        Returns:
            DataFrame containing the parameter summary table
        """
        table_data = []
        
        for param in dimensionless_params:
            if param not in data.columns:
                continue
            
            param_data = data[param].dropna()
            if len(param_data) == 0:
                continue
            
            # Get parameter definition if available
            param_def = None
            for known_param in self.calculator.known_dimensionless.values():
                if known_param.name == param:
                    param_def = known_param
                    break
            
            # Calculate statistics
            stats_dict = {
                'Parameter': param.replace('_', ' ').title(),
                'Formula': param_def.formula if param_def else 'N/A',
                'Description': param_def.description if param_def else 'Auto-discovered',
                'Min': f'{param_data.min():.3f}',
                'Max': f'{param_data.max():.3f}',
                'Mean': f'{param_data.mean():.3f}',
                'Std': f'{param_data.std():.3f}',
                'Median': f'{param_data.median():.3f}',
                'N_Points': len(param_data)
            }
            
            table_data.append(stats_dict)
        
        table_df = pd.DataFrame(table_data)
        
        if save_path:
            table_df.to_csv(save_path, index=False)
        
        return table_df
    
    def create_interactive_parameter_explorer(self, 
                                            data: pd.DataFrame,
                                            dimensionless_params: List[str],
                                            dependent_variables: List[str],
                                            save_path: Optional[str] = None) -> Optional[Any]:
        """
        Create interactive plot for exploring dimensionless parameters.
        
        Args:
            data: DataFrame containing experimental data
            dimensionless_params: List of dimensionless parameter columns
            dependent_variables: List of dependent variable columns
            save_path: Path to save the HTML file
            
        Returns:
            Plotly figure object or None if plotly not available
        """
        if len(dimensionless_params) == 0 or len(dependent_variables) == 0:
            raise ValueError("Need at least one dimensionless parameter and one dependent variable")
            
        if not PLOTLY_AVAILABLE:
            warnings.warn("Plotly not available. Interactive plots will be skipped.")
            return None
        
        # Create subplots
        n_plots = len(dimensionless_params) * len(dependent_variables)
        n_cols = min(3, len(dimensionless_params))
        n_rows = (len(dependent_variables) + n_cols - 1) // n_cols
        
        subplot_titles = []
        for dep_var in dependent_variables:
            for dim_param in dimensionless_params:
                subplot_titles.append(f'{dep_var} vs {dim_param}')
        
        from plotly.subplots import make_subplots
        fig = make_subplots(
            rows=n_rows, 
            cols=n_cols,
            subplot_titles=subplot_titles[:n_plots],
            horizontal_spacing=0.1,
            vertical_spacing=0.15
        )
        
        plot_idx = 0
        for i, dep_var in enumerate(dependent_variables):
            for j, dim_param in enumerate(dimensionless_params):
                if dim_param not in data.columns or dep_var not in data.columns:
                    continue
                
                row = plot_idx // n_cols + 1
                col = plot_idx % n_cols + 1
                
                # Clean data
                plot_data = data.dropna(subset=[dim_param, dep_var])
                plot_data = plot_data[
                    (plot_data[dim_param] > 0) & 
                    (plot_data[dep_var] > 0)
                ]
                
                if len(plot_data) > 0:
                    # Add scatter plot
                    fig.add_trace(
                        go.Scatter(
                            x=plot_data[dim_param],
                            y=plot_data[dep_var],
                            mode='markers',
                            name=f'{dep_var} vs {dim_param}',
                            marker=dict(
                                size=8,
                                opacity=0.7,
                                color=plot_data.index,
                                colorscale='Viridis',
                                showscale=False
                            ),
                            hovertemplate=f'<b>{dim_param}</b>: %{{x:.3f}}<br>' +
                                        f'<b>{dep_var}</b>: %{{y:.3f}}<br>' +
                                        '<extra></extra>'
                        ),
                        row=row, col=col
                    )
                    
                    # Add trend line if possible
                    try:
                        x_vals = plot_data[dim_param].values
                        y_vals = plot_data[dep_var].values
                        
                        # Fit power law in log space
                        log_x = np.log(x_vals)
                        log_y = np.log(y_vals)
                        slope, intercept, r_value, _, _ = stats.linregress(log_x, log_y)
                        
                        if r_value**2 > 0.3:  # Only show if reasonable fit
                            x_fit = np.logspace(np.log10(x_vals.min()), np.log10(x_vals.max()), 50)
                            y_fit = np.exp(intercept) * np.power(x_fit, slope)
                            
                            fig.add_trace(
                                go.Scatter(
                                    x=x_fit,
                                    y=y_fit,
                                    mode='lines',
                                    name=f'Fit (R²={r_value**2:.2f})',
                                    line=dict(color='red', width=2),
                                    hovertemplate=f'Power law fit<br>R² = {r_value**2:.3f}<extra></extra>'
                                ),
                                row=row, col=col
                            )
                    except Exception:
                        pass
                
                # Update axes
                fig.update_xaxes(
                    title_text=dim_param.replace('_', ' ').title(),
                    type='log',
                    row=row, col=col
                )
                fig.update_yaxes(
                    title_text=dep_var.replace('_', ' ').title(),
                    type='log',
                    row=row, col=col
                )
                
                plot_idx += 1
        
        # Update layout
        fig.update_layout(
            title='Interactive Dimensionless Parameter Explorer',
            showlegend=False,
            height=400 * n_rows,
            width=400 * n_cols
        )
        
        if save_path:
            pyo.plot(fig, filename=save_path, auto_open=False)
        
        return fig
    
    def generate_publication_figures(self, 
                                   data: pd.DataFrame,
                                   output_dir: str,
                                   prefix: str = 'dimensionless') -> Dict[str, str]:
        """
        Generate complete set of publication-ready figures.
        
        Args:
            data: DataFrame containing experimental data
            output_dir: Directory to save figures
            prefix: Prefix for figure filenames
            
        Returns:
            Dictionary mapping figure types to file paths
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = {}
        
        # Identify dimensionless parameters and dependent variables
        dimensionless_params = []
        dependent_variables = []
        
        for col in data.columns:
            if 'pressure' in col.lower() or 'dimensionless' in col.lower():
                dimensionless_params.append(col)
            elif any(term in col.lower() for term in ['rate', 'response', 'activation', 'movement']):
                dependent_variables.append(col)
        
        if not dimensionless_params:
            dimensionless_params = ['cognitive_pressure']  # Default
        if not dependent_variables:
            dependent_variables = [col for col in data.columns if col not in dimensionless_params][:3]
        
        try:
            # 1. Data collapse plot
            if len(dimensionless_params) > 0 and len(dependent_variables) > 0:
                grouping_cols = [col for col in data.columns 
                               if col not in dimensionless_params + dependent_variables 
                               and data[col].dtype == 'object']
                
                if grouping_cols:
                    collapse_path = os.path.join(output_dir, f'{prefix}_data_collapse.png')
                    fig = self.create_data_collapse_plot(
                        data, dimensionless_params[0], dependent_variables[0], 
                        grouping_cols[0], 
                        title='Universal Scaling and Data Collapse',
                        save_path=collapse_path
                    )
                    plt.close(fig)
                    generated_files['data_collapse'] = collapse_path
        except Exception as e:
            print(f"Warning: Could not generate data collapse plot: {e}")
        
        try:
            # 2. Scaling relationships
            relationships = self.detector.detect_scaling_relationships(
                data, dimensionless_params, dependent_variables
            )
            
            if relationships:
                scaling_path = os.path.join(output_dir, f'{prefix}_scaling_relationships.png')
                fig = self.create_scaling_relationship_plot(
                    data, relationships,
                    title='Universal Scaling Relationships',
                    save_path=scaling_path
                )
                plt.close(fig)
                generated_files['scaling_relationships'] = scaling_path
        except Exception as e:
            print(f"Warning: Could not generate scaling relationships plot: {e}")
        
        try:
            # 3. Parameter sensitivity heatmap
            sensitivity_path = os.path.join(output_dir, f'{prefix}_sensitivity.png')
            fig = self.create_parameter_sensitivity_heatmap(
                data, dimensionless_params, dependent_variables,
                title='Dimensionless Parameter Sensitivity Analysis',
                save_path=sensitivity_path
            )
            plt.close(fig)
            generated_files['sensitivity'] = sensitivity_path
        except Exception as e:
            print(f"Warning: Could not generate sensitivity plot: {e}")
        
        try:
            # 4. Parameter summary table
            table_path = os.path.join(output_dir, f'{prefix}_parameters.csv')
            table_df = self.create_dimensionless_parameter_table(
                data, dimensionless_params, save_path=table_path
            )
            generated_files['parameter_table'] = table_path
        except Exception as e:
            print(f"Warning: Could not generate parameter table: {e}")
        
        try:
            # 5. Interactive explorer
            interactive_path = os.path.join(output_dir, f'{prefix}_interactive.html')
            fig = self.create_interactive_parameter_explorer(
                data, dimensionless_params, dependent_variables,
                save_path=interactive_path
            )
            generated_files['interactive'] = interactive_path
        except Exception as e:
            print(f"Warning: Could not generate interactive plot: {e}")
        
        return generated_files