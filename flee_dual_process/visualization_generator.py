"""
Visualization Generator System for Dual Process Experiments

This module provides comprehensive visualization capabilities for dual-process experiments,
including cognitive state plots, movement pattern visualizations, and parameter sensitivity analysis.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import warnings

# Optional plotly imports
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from .utils import LoggingUtils, ValidationUtils, FileUtils
    from .analysis_pipeline import AnalysisPipeline, ExperimentResults
except ImportError:
    from utils import LoggingUtils, ValidationUtils, FileUtils
    from analysis_pipeline import AnalysisPipeline, ExperimentResults


@dataclass
class PlotConfig:
    """Configuration for plot styling and formatting."""
    figsize: Tuple[int, int] = (12, 8)
    dpi: int = 300
    style: str = 'seaborn-v0_8'
    color_palette: str = 'Set2'
    font_size: int = 12
    title_size: int = 14
    label_size: int = 11
    legend_size: int = 10
    line_width: float = 2.0
    marker_size: float = 6.0
    alpha: float = 0.7
    save_format: str = 'png'
    save_dpi: int = 300


class VisualizationGenerator:
    """
    Visualization generator class with matplotlib and plotly backends.
    
    This class creates publication-ready visualizations for dual-process experiments,
    including cognitive state evolution, movement patterns, and parameter sensitivity analysis.
    """
    
    def __init__(self, results_directory: str, output_directory: str = None, 
                 backend: str = 'matplotlib', plot_config: PlotConfig = None):
        """
        Initialize visualization generator.
        
        Args:
            results_directory: Directory containing experiment results
            output_directory: Directory for visualization outputs (default: results_directory/visualizations)
            backend: Visualization backend ('matplotlib' or 'plotly')
            plot_config: Configuration for plot styling
        """
        self.results_directory = Path(results_directory)
        self.output_directory = Path(output_directory) if output_directory else self.results_directory / "visualizations"
        self.backend = backend.lower()
        self.plot_config = plot_config or PlotConfig()
        
        # Initialize utilities
        self.logging_utils = LoggingUtils()
        self.validation_utils = ValidationUtils()
        self.file_utils = FileUtils()
        
        # Setup logger
        self.logger = self.logging_utils.get_logger('VisualizationGenerator')
        
        # Ensure output directory exists
        self.file_utils.ensure_directory(str(self.output_directory))
        
        # Initialize analysis pipeline for data loading
        self.analysis_pipeline = AnalysisPipeline(str(self.results_directory))
        
        # Validate backend
        if self.backend == 'plotly' and not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available, falling back to matplotlib")
            self.backend = 'matplotlib'
        
        # Setup matplotlib style
        if self.backend == 'matplotlib':
            self._setup_matplotlib_style()
        
        self.logger.info(f"VisualizationGenerator initialized with backend: {self.backend}")
        self.logger.info(f"Visualizations will be saved to: {self.output_directory}")
    
    def _setup_matplotlib_style(self):
        """Setup matplotlib styling for publication-ready plots."""
        try:
            plt.style.use(self.plot_config.style)
        except OSError:
            # Fallback to default style if specified style not available
            plt.style.use('default')
            self.logger.warning(f"Style '{self.plot_config.style}' not available, using default")
        
        # Set global font sizes
        plt.rcParams.update({
            'font.size': self.plot_config.font_size,
            'axes.titlesize': self.plot_config.title_size,
            'axes.labelsize': self.plot_config.label_size,
            'xtick.labelsize': self.plot_config.label_size,
            'ytick.labelsize': self.plot_config.label_size,
            'legend.fontsize': self.plot_config.legend_size,
            'figure.titlesize': self.plot_config.title_size,
            'lines.linewidth': self.plot_config.line_width,
            'lines.markersize': self.plot_config.marker_size,
            'figure.dpi': self.plot_config.dpi,
            'savefig.dpi': self.plot_config.save_dpi,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1
        })
        
        # Set color palette
        try:
            sns.set_palette(self.plot_config.color_palette)
        except ValueError:
            self.logger.warning(f"Color palette '{self.plot_config.color_palette}' not available")
    
    def create_cognitive_state_plots(self, experiment_dirs: List[str], 
                                   plot_types: List[str] = None) -> List[str]:
        """
        Create cognitive state evolution plots for temporal state analysis.
        
        Args:
            experiment_dirs: List of experiment directory paths
            plot_types: List of plot types to generate ('evolution', 'distribution', 'transitions')
            
        Returns:
            List of generated plot file paths
        """
        if plot_types is None:
            plot_types = ['evolution', 'distribution', 'transitions']
        
        self.logger.info(f"Creating cognitive state plots for {len(experiment_dirs)} experiments")
        
        generated_plots = []
        
        for plot_type in plot_types:
            try:
                if plot_type == 'evolution':
                    plot_files = self._create_cognitive_evolution_plots(experiment_dirs)
                    generated_plots.extend(plot_files)
                elif plot_type == 'distribution':
                    plot_files = self._create_cognitive_distribution_plots(experiment_dirs)
                    generated_plots.extend(plot_files)
                elif plot_type == 'transitions':
                    plot_files = self._create_cognitive_transition_plots(experiment_dirs)
                    generated_plots.extend(plot_files)
                else:
                    self.logger.warning(f"Unknown plot type: {plot_type}")
                    
            except Exception as e:
                self.logger.error(f"Failed to create {plot_type} plots: {e}")
                continue
        
        self.logger.info(f"Generated {len(generated_plots)} cognitive state plots")
        return generated_plots
    
    def _create_cognitive_evolution_plots(self, experiment_dirs: List[str]) -> List[str]:
        """
        Create cognitive state evolution plots over time.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        for experiment_dir in experiment_dirs:
            try:
                # Load experiment data
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.cognitive_states is None or results.cognitive_states.empty:
                    self.logger.warning(f"No cognitive states data for {results.experiment_id}")
                    continue
                
                cognitive_data = results.cognitive_states
                
                if self.backend == 'matplotlib':
                    plot_file = self._create_matplotlib_cognitive_evolution(cognitive_data, results.experiment_id)
                else:
                    plot_file = self._create_plotly_cognitive_evolution(cognitive_data, results.experiment_id)
                
                if plot_file:
                    generated_plots.append(plot_file)
                    
            except Exception as e:
                self.logger.error(f"Failed to create cognitive evolution plot for {experiment_dir}: {e}")
                continue
        
        return generated_plots
    
    def _create_matplotlib_cognitive_evolution(self, cognitive_data: pd.DataFrame, 
                                             experiment_id: str) -> Optional[str]:
        """
        Create cognitive state evolution plot using matplotlib.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'Cognitive State Evolution - {experiment_id}', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Plot 1: Overall cognitive state proportions over time
            if 'day' in cognitive_data.columns and 'cognitive_state' in cognitive_data.columns:
                daily_states = cognitive_data.groupby(['day', 'cognitive_state']).size().unstack(fill_value=0)
                daily_proportions = daily_states.div(daily_states.sum(axis=1), axis=0)
                
                ax1 = axes[0, 0]
                for state in daily_proportions.columns:
                    ax1.plot(daily_proportions.index, daily_proportions[state], 
                            label=state, linewidth=self.plot_config.line_width, alpha=self.plot_config.alpha)
                
                ax1.set_xlabel('Day')
                ax1.set_ylabel('Proportion of Agents')
                ax1.set_title('Cognitive State Proportions Over Time')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            
            # Plot 2: Cumulative cognitive state transitions
            if 'day' in cognitive_data.columns and 'agent_id' in cognitive_data.columns:
                # Calculate transitions for each agent
                transitions = []
                for agent_id in cognitive_data['agent_id'].unique():
                    agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                    if len(agent_data) > 1:
                        state_changes = (agent_data['cognitive_state'] != agent_data['cognitive_state'].shift()).sum() - 1
                        transitions.append(state_changes)
                
                ax2 = axes[0, 1]
                if transitions:
                    ax2.hist(transitions, bins=max(1, len(set(transitions))), alpha=self.plot_config.alpha, 
                            edgecolor='black', linewidth=0.5)
                    ax2.set_xlabel('Number of State Transitions')
                    ax2.set_ylabel('Number of Agents')
                    ax2.set_title('Distribution of State Transitions per Agent')
                    ax2.grid(True, alpha=0.3)
            
            # Plot 3: Agent-level cognitive state timeline (sample of agents)
            if 'day' in cognitive_data.columns and 'agent_id' in cognitive_data.columns:
                ax3 = axes[1, 0]
                
                # Sample up to 20 agents for visualization
                sample_agents = cognitive_data['agent_id'].unique()[:20]
                state_mapping = {'S1': 0, 'S2': 1}  # Map states to numeric values
                
                for i, agent_id in enumerate(sample_agents):
                    agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                    if 'cognitive_state' in agent_data.columns:
                        states_numeric = agent_data['cognitive_state'].map(state_mapping)
                        ax3.plot(agent_data['day'], states_numeric + i * 0.1, 
                                alpha=0.6, linewidth=1.0)
                
                ax3.set_xlabel('Day')
                ax3.set_ylabel('Cognitive State (S1=0, S2=1)')
                ax3.set_title('Individual Agent Cognitive State Timelines (Sample)')
                ax3.grid(True, alpha=0.3)
            
            # Plot 4: State duration analysis
            if 'day' in cognitive_data.columns and 'agent_id' in cognitive_data.columns:
                ax4 = axes[1, 1]
                
                # Calculate state durations
                state_durations = {'S1': [], 'S2': []}
                
                for agent_id in cognitive_data['agent_id'].unique():
                    agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                    if len(agent_data) > 1:
                        current_state = None
                        state_start = None
                        
                        for _, row in agent_data.iterrows():
                            if current_state != row['cognitive_state']:
                                if current_state is not None and state_start is not None:
                                    duration = row['day'] - state_start
                                    if current_state in state_durations:
                                        state_durations[current_state].append(duration)
                                
                                current_state = row['cognitive_state']
                                state_start = row['day']
                
                # Plot duration distributions
                for state, durations in state_durations.items():
                    if durations:
                        ax4.hist(durations, alpha=0.6, label=f'{state} (n={len(durations)})', 
                                bins=min(20, len(set(durations))))
                
                ax4.set_xlabel('State Duration (Days)')
                ax4.set_ylabel('Frequency')
                ax4.set_title('Cognitive State Duration Distribution')
                ax4.legend()
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"cognitive_evolution_{experiment_id}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created cognitive evolution plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib cognitive evolution plot: {e}")
            return None
    
    def _create_plotly_cognitive_evolution(self, cognitive_data: pd.DataFrame, 
                                         experiment_id: str) -> Optional[str]:
        """
        Create cognitive state evolution plot using plotly.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated plot file
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Cognitive State Proportions Over Time', 
                               'State Transitions Distribution',
                               'Individual Agent Timelines (Sample)', 
                               'State Duration Distribution'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Plot 1: Overall cognitive state proportions over time
            if 'day' in cognitive_data.columns and 'cognitive_state' in cognitive_data.columns:
                daily_states = cognitive_data.groupby(['day', 'cognitive_state']).size().unstack(fill_value=0)
                daily_proportions = daily_states.div(daily_states.sum(axis=1), axis=0)
                
                for state in daily_proportions.columns:
                    fig.add_trace(
                        go.Scatter(x=daily_proportions.index, y=daily_proportions[state],
                                  mode='lines', name=state, line=dict(width=3)),
                        row=1, col=1
                    )
            
            # Plot 2: Cumulative cognitive state transitions
            if 'day' in cognitive_data.columns and 'agent_id' in cognitive_data.columns:
                transitions = []
                for agent_id in cognitive_data['agent_id'].unique():
                    agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                    if len(agent_data) > 1:
                        state_changes = (agent_data['cognitive_state'] != agent_data['cognitive_state'].shift()).sum() - 1
                        transitions.append(state_changes)
                
                if transitions:
                    fig.add_trace(
                        go.Histogram(x=transitions, name='Transitions', opacity=0.7),
                        row=1, col=2
                    )
            
            # Plot 3: Agent-level cognitive state timeline (sample)
            if 'day' in cognitive_data.columns and 'agent_id' in cognitive_data.columns:
                sample_agents = cognitive_data['agent_id'].unique()[:10]  # Fewer for plotly
                state_mapping = {'S1': 0, 'S2': 1}
                
                for i, agent_id in enumerate(sample_agents):
                    agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                    if 'cognitive_state' in agent_data.columns:
                        states_numeric = agent_data['cognitive_state'].map(state_mapping)
                        fig.add_trace(
                            go.Scatter(x=agent_data['day'], y=states_numeric + i * 0.1,
                                      mode='lines', name=f'Agent {agent_id}', 
                                      line=dict(width=2), opacity=0.7),
                            row=2, col=1
                        )
            
            # Plot 4: State duration analysis
            if 'day' in cognitive_data.columns and 'agent_id' in cognitive_data.columns:
                state_durations = {'S1': [], 'S2': []}
                
                for agent_id in cognitive_data['agent_id'].unique():
                    agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                    if len(agent_data) > 1:
                        current_state = None
                        state_start = None
                        
                        for _, row in agent_data.iterrows():
                            if current_state != row['cognitive_state']:
                                if current_state is not None and state_start is not None:
                                    duration = row['day'] - state_start
                                    if current_state in state_durations:
                                        state_durations[current_state].append(duration)
                                
                                current_state = row['cognitive_state']
                                state_start = row['day']
                
                for state, durations in state_durations.items():
                    if durations:
                        fig.add_trace(
                            go.Histogram(x=durations, name=f'{state} Duration', opacity=0.7),
                            row=2, col=2
                        )
            
            # Update layout
            fig.update_layout(
                title_text=f'Cognitive State Evolution - {experiment_id}',
                title_x=0.5,
                height=800,
                showlegend=True
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Day", row=1, col=1)
            fig.update_yaxes(title_text="Proportion of Agents", row=1, col=1)
            fig.update_xaxes(title_text="Number of Transitions", row=1, col=2)
            fig.update_yaxes(title_text="Number of Agents", row=1, col=2)
            fig.update_xaxes(title_text="Day", row=2, col=1)
            fig.update_yaxes(title_text="Cognitive State", row=2, col=1)
            fig.update_xaxes(title_text="Duration (Days)", row=2, col=2)
            fig.update_yaxes(title_text="Frequency", row=2, col=2)
            
            # Save plot
            output_file = self.output_directory / f"cognitive_evolution_{experiment_id}.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created cognitive evolution plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly cognitive evolution plot: {e}")
            return None
    
    def _create_cognitive_distribution_plots(self, experiment_dirs: List[str]) -> List[str]:
        """
        Create cognitive state distribution plots.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        # Aggregate data from all experiments
        all_cognitive_data = []
        experiment_labels = []
        
        for experiment_dir in experiment_dirs:
            try:
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.cognitive_states is None or results.cognitive_states.empty:
                    continue
                
                cognitive_data = results.cognitive_states.copy()
                cognitive_data['experiment_id'] = results.experiment_id
                all_cognitive_data.append(cognitive_data)
                experiment_labels.append(results.experiment_id)
                
            except Exception as e:
                self.logger.error(f"Failed to load data for distribution plot: {e}")
                continue
        
        if not all_cognitive_data:
            self.logger.warning("No cognitive states data available for distribution plots")
            return generated_plots
        
        # Combine all data
        combined_data = pd.concat(all_cognitive_data, ignore_index=True)
        
        if self.backend == 'matplotlib':
            plot_file = self._create_matplotlib_cognitive_distribution(combined_data, experiment_labels)
        else:
            plot_file = self._create_plotly_cognitive_distribution(combined_data, experiment_labels)
        
        if plot_file:
            generated_plots.append(plot_file)
        
        return generated_plots
    
    def _create_matplotlib_cognitive_distribution(self, combined_data: pd.DataFrame, 
                                                experiment_labels: List[str]) -> Optional[str]:
        """
        Create cognitive state distribution plot using matplotlib.
        
        Args:
            combined_data: Combined cognitive states data from all experiments
            experiment_labels: List of experiment identifiers
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Cognitive State Distribution Analysis', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Plot 1: Overall state distribution by experiment
            if 'experiment_id' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                ax1 = axes[0, 0]
                state_counts = combined_data.groupby(['experiment_id', 'cognitive_state']).size().unstack(fill_value=0)
                state_proportions = state_counts.div(state_counts.sum(axis=1), axis=0)
                
                state_proportions.plot(kind='bar', ax=ax1, alpha=self.plot_config.alpha)
                ax1.set_xlabel('Experiment')
                ax1.set_ylabel('Proportion')
                ax1.set_title('Cognitive State Distribution by Experiment')
                ax1.legend(title='Cognitive State')
                ax1.tick_params(axis='x', rotation=45)
                ax1.grid(True, alpha=0.3)
            
            # Plot 2: State distribution over time (aggregated)
            if 'day' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                ax2 = axes[0, 1]
                daily_states = combined_data.groupby(['day', 'cognitive_state']).size().unstack(fill_value=0)
                daily_proportions = daily_states.div(daily_states.sum(axis=1), axis=0)
                
                for state in daily_proportions.columns:
                    ax2.plot(daily_proportions.index, daily_proportions[state], 
                            label=state, linewidth=self.plot_config.line_width, alpha=self.plot_config.alpha)
                
                ax2.set_xlabel('Day')
                ax2.set_ylabel('Proportion')
                ax2.set_title('Aggregated State Distribution Over Time')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            
            # Plot 3: Box plot of state proportions by experiment
            if 'experiment_id' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                ax3 = axes[1, 0]
                
                # Calculate daily proportions for each experiment
                exp_daily_props = []
                for exp_id in combined_data['experiment_id'].unique():
                    exp_data = combined_data[combined_data['experiment_id'] == exp_id]
                    daily_states = exp_data.groupby(['day', 'cognitive_state']).size().unstack(fill_value=0)
                    if not daily_states.empty:
                        daily_props = daily_states.div(daily_states.sum(axis=1), axis=0)
                        for state in daily_props.columns:
                            for prop in daily_props[state]:
                                exp_daily_props.append({'experiment': exp_id, 'state': state, 'proportion': prop})
                
                if exp_daily_props:
                    props_df = pd.DataFrame(exp_daily_props)
                    
                    # Create box plot
                    states = props_df['state'].unique()
                    positions = []
                    labels = []
                    
                    for i, state in enumerate(states):
                        state_data = props_df[props_df['state'] == state]
                        for j, exp in enumerate(state_data['experiment'].unique()):
                            exp_data = state_data[state_data['experiment'] == exp]['proportion']
                            pos = i * len(experiment_labels) + j
                            positions.append(pos)
                            labels.append(f"{state}\n{exp}")
                            
                            bp = ax3.boxplot(exp_data, positions=[pos], widths=0.6, patch_artist=True)
                            bp['boxes'][0].set_facecolor(plt.cm.Set2(i))
                            bp['boxes'][0].set_alpha(self.plot_config.alpha)
                    
                    ax3.set_xticks(positions)
                    ax3.set_xticklabels(labels, rotation=45, ha='right')
                    ax3.set_ylabel('Proportion')
                    ax3.set_title('State Proportion Variability by Experiment')
                    ax3.grid(True, alpha=0.3)
            
            # Plot 4: Heatmap of state transitions
            if 'agent_id' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                ax4 = axes[1, 1]
                
                # Calculate transition matrix
                transitions = []
                for agent_id in combined_data['agent_id'].unique():
                    agent_data = combined_data[combined_data['agent_id'] == agent_id].sort_values('day')
                    if len(agent_data) > 1:
                        for i in range(len(agent_data) - 1):
                            from_state = agent_data.iloc[i]['cognitive_state']
                            to_state = agent_data.iloc[i + 1]['cognitive_state']
                            transitions.append((from_state, to_state))
                
                if transitions:
                    states = list(set([t[0] for t in transitions] + [t[1] for t in transitions]))
                    transition_matrix = pd.DataFrame(0, index=states, columns=states)
                    
                    for from_state, to_state in transitions:
                        transition_matrix.loc[from_state, to_state] += 1
                    
                    # Normalize by row sums
                    transition_probs = transition_matrix.div(transition_matrix.sum(axis=1), axis=0).fillna(0)
                    
                    im = ax4.imshow(transition_probs.values, cmap='Blues', alpha=self.plot_config.alpha)
                    ax4.set_xticks(range(len(states)))
                    ax4.set_yticks(range(len(states)))
                    ax4.set_xticklabels(states)
                    ax4.set_yticklabels(states)
                    ax4.set_xlabel('To State')
                    ax4.set_ylabel('From State')
                    ax4.set_title('State Transition Probabilities')
                    
                    # Add text annotations
                    for i in range(len(states)):
                        for j in range(len(states)):
                            text = ax4.text(j, i, f'{transition_probs.iloc[i, j]:.2f}',
                                          ha="center", va="center", color="black")
                    
                    plt.colorbar(im, ax=ax4)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"cognitive_distribution_analysis.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created cognitive distribution plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib cognitive distribution plot: {e}")
            return None 
   
    def _create_plotly_cognitive_distribution(self, combined_data: pd.DataFrame, 
                                            experiment_labels: List[str]) -> Optional[str]:
        """
        Create cognitive state distribution plot using plotly.
        
        Args:
            combined_data: Combined cognitive states data from all experiments
            experiment_labels: List of experiment identifiers
            
        Returns:
            Path to generated plot file
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('State Distribution by Experiment', 
                               'Aggregated State Distribution Over Time',
                               'State Proportion Variability', 
                               'State Transition Heatmap'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Plot 1: Overall state distribution by experiment
            if 'experiment_id' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                state_counts = combined_data.groupby(['experiment_id', 'cognitive_state']).size().unstack(fill_value=0)
                state_proportions = state_counts.div(state_counts.sum(axis=1), axis=0)
                
                for state in state_proportions.columns:
                    fig.add_trace(
                        go.Bar(x=state_proportions.index, y=state_proportions[state], 
                              name=state, opacity=0.7),
                        row=1, col=1
                    )
            
            # Plot 2: State distribution over time (aggregated)
            if 'day' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                daily_states = combined_data.groupby(['day', 'cognitive_state']).size().unstack(fill_value=0)
                daily_proportions = daily_states.div(daily_states.sum(axis=1), axis=0)
                
                for state in daily_proportions.columns:
                    fig.add_trace(
                        go.Scatter(x=daily_proportions.index, y=daily_proportions[state],
                                  mode='lines', name=f'{state} (Time)', line=dict(width=3)),
                        row=1, col=2
                    )
            
            # Plot 3: Box plot of state proportions by experiment
            if 'experiment_id' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                exp_daily_props = []
                for exp_id in combined_data['experiment_id'].unique():
                    exp_data = combined_data[combined_data['experiment_id'] == exp_id]
                    daily_states = exp_data.groupby(['day', 'cognitive_state']).size().unstack(fill_value=0)
                    if not daily_states.empty:
                        daily_props = daily_states.div(daily_states.sum(axis=1), axis=0)
                        for state in daily_props.columns:
                            for prop in daily_props[state]:
                                exp_daily_props.append({'experiment': exp_id, 'state': state, 'proportion': prop})
                
                if exp_daily_props:
                    props_df = pd.DataFrame(exp_daily_props)
                    
                    for state in props_df['state'].unique():
                        state_data = props_df[props_df['state'] == state]
                        for exp in state_data['experiment'].unique():
                            exp_data = state_data[state_data['experiment'] == exp]['proportion']
                            fig.add_trace(
                                go.Box(y=exp_data, name=f'{state}-{exp}', opacity=0.7),
                                row=2, col=1
                            )
            
            # Plot 4: Heatmap of state transitions
            if 'agent_id' in combined_data.columns and 'cognitive_state' in combined_data.columns:
                transitions = []
                for agent_id in combined_data['agent_id'].unique():
                    agent_data = combined_data[combined_data['agent_id'] == agent_id].sort_values('day')
                    if len(agent_data) > 1:
                        for i in range(len(agent_data) - 1):
                            from_state = agent_data.iloc[i]['cognitive_state']
                            to_state = agent_data.iloc[i + 1]['cognitive_state']
                            transitions.append((from_state, to_state))
                
                if transitions:
                    states = list(set([t[0] for t in transitions] + [t[1] for t in transitions]))
                    transition_matrix = pd.DataFrame(0, index=states, columns=states)
                    
                    for from_state, to_state in transitions:
                        transition_matrix.loc[from_state, to_state] += 1
                    
                    # Normalize by row sums
                    transition_probs = transition_matrix.div(transition_matrix.sum(axis=1), axis=0).fillna(0)
                    
                    fig.add_trace(
                        go.Heatmap(z=transition_probs.values, 
                                  x=states, y=states,
                                  colorscale='Blues', 
                                  text=transition_probs.values,
                                  texttemplate="%{text:.2f}",
                                  textfont={"size": 10}),
                        row=2, col=2
                    )
            
            # Update layout
            fig.update_layout(
                title_text='Cognitive State Distribution Analysis',
                title_x=0.5,
                height=800,
                showlegend=True
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Experiment", row=1, col=1)
            fig.update_yaxes(title_text="Proportion", row=1, col=1)
            fig.update_xaxes(title_text="Day", row=1, col=2)
            fig.update_yaxes(title_text="Proportion", row=1, col=2)
            fig.update_yaxes(title_text="Proportion", row=2, col=1)
            fig.update_xaxes(title_text="To State", row=2, col=2)
            fig.update_yaxes(title_text="From State", row=2, col=2)
            
            # Save plot
            output_file = self.output_directory / f"cognitive_distribution_analysis.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created cognitive distribution plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly cognitive distribution plot: {e}")
            return None
    
    def _create_cognitive_transition_plots(self, experiment_dirs: List[str]) -> List[str]:
        """
        Create cognitive state transition analysis plots.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        for experiment_dir in experiment_dirs:
            try:
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.cognitive_states is None or results.cognitive_states.empty:
                    continue
                
                cognitive_data = results.cognitive_states
                
                if self.backend == 'matplotlib':
                    plot_file = self._create_matplotlib_cognitive_transitions(cognitive_data, results.experiment_id)
                else:
                    plot_file = self._create_plotly_cognitive_transitions(cognitive_data, results.experiment_id)
                
                if plot_file:
                    generated_plots.append(plot_file)
                    
            except Exception as e:
                self.logger.error(f"Failed to create cognitive transition plot for {experiment_dir}: {e}")
                continue
        
        return generated_plots
    
    def _create_matplotlib_cognitive_transitions(self, cognitive_data: pd.DataFrame, 
                                               experiment_id: str) -> Optional[str]:
        """
        Create cognitive state transition analysis plot using matplotlib.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'Cognitive State Transition Analysis - {experiment_id}', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            # Analyze transitions
            transition_data = self._analyze_transitions(cognitive_data)
            
            if not transition_data:
                self.logger.warning(f"No transition data available for {experiment_id}")
                plt.close()
                return None
            
            # Plot 1: Transition frequency over time
            ax1 = axes[0, 0]
            if 'transition_day' in transition_data[0]:
                transition_days = [t['transition_day'] for t in transition_data]
                ax1.hist(transition_days, bins=20, alpha=self.plot_config.alpha, edgecolor='black')
                ax1.set_xlabel('Day')
                ax1.set_ylabel('Number of Transitions')
                ax1.set_title('Transition Frequency Over Time')
                ax1.grid(True, alpha=0.3)
            
            # Plot 2: Transition types distribution
            ax2 = axes[0, 1]
            transition_types = [f"{t['from_state']} → {t['to_state']}" for t in transition_data]
            type_counts = pd.Series(transition_types).value_counts()
            
            type_counts.plot(kind='bar', ax=ax2, alpha=self.plot_config.alpha)
            ax2.set_xlabel('Transition Type')
            ax2.set_ylabel('Count')
            ax2.set_title('Transition Type Distribution')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Transition triggers analysis
            ax3 = axes[1, 0]
            if 'trigger' in transition_data[0]:
                triggers = [t['trigger'] for t in transition_data if t['trigger']]
                if triggers:
                    trigger_counts = pd.Series(triggers).value_counts()
                    trigger_counts.plot(kind='pie', ax=ax3, autopct='%1.1f%%', alpha=self.plot_config.alpha)
                    ax3.set_title('Transition Triggers')
                    ax3.set_ylabel('')
            
            # Plot 4: Agent transition patterns
            ax4 = axes[1, 1]
            agent_transitions = {}
            for t in transition_data:
                agent_id = t['agent_id']
                if agent_id not in agent_transitions:
                    agent_transitions[agent_id] = 0
                agent_transitions[agent_id] += 1
            
            if agent_transitions:
                transition_counts = list(agent_transitions.values())
                ax4.hist(transition_counts, bins=max(1, len(set(transition_counts))), 
                        alpha=self.plot_config.alpha, edgecolor='black')
                ax4.set_xlabel('Number of Transitions per Agent')
                ax4.set_ylabel('Number of Agents')
                ax4.set_title('Agent Transition Activity Distribution')
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"cognitive_transitions_{experiment_id}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created cognitive transitions plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib cognitive transitions plot: {e}")
            return None
    
    def _create_plotly_cognitive_transitions(self, cognitive_data: pd.DataFrame, 
                                           experiment_id: str) -> Optional[str]:
        """
        Create cognitive state transition analysis plot using plotly.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            experiment_id: Experiment identifier
            
        Returns:
            Path to generated plot file
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Transition Frequency Over Time', 
                               'Transition Type Distribution',
                               'Transition Triggers', 
                               'Agent Transition Activity'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"type": "pie"}, {"secondary_y": False}]]
            )
            
            # Analyze transitions
            transition_data = self._analyze_transitions(cognitive_data)
            
            if not transition_data:
                self.logger.warning(f"No transition data available for {experiment_id}")
                return None
            
            # Plot 1: Transition frequency over time
            if 'transition_day' in transition_data[0]:
                transition_days = [t['transition_day'] for t in transition_data]
                fig.add_trace(
                    go.Histogram(x=transition_days, name='Transitions', opacity=0.7),
                    row=1, col=1
                )
            
            # Plot 2: Transition types distribution
            transition_types = [f"{t['from_state']} → {t['to_state']}" for t in transition_data]
            type_counts = pd.Series(transition_types).value_counts()
            
            fig.add_trace(
                go.Bar(x=type_counts.index, y=type_counts.values, 
                      name='Transition Types', opacity=0.7),
                row=1, col=2
            )
            
            # Plot 3: Transition triggers analysis
            if 'trigger' in transition_data[0]:
                triggers = [t['trigger'] for t in transition_data if t['trigger']]
                if triggers:
                    trigger_counts = pd.Series(triggers).value_counts()
                    fig.add_trace(
                        go.Pie(labels=trigger_counts.index, values=trigger_counts.values,
                              name='Triggers'),
                        row=2, col=1
                    )
            
            # Plot 4: Agent transition patterns
            agent_transitions = {}
            for t in transition_data:
                agent_id = t['agent_id']
                if agent_id not in agent_transitions:
                    agent_transitions[agent_id] = 0
                agent_transitions[agent_id] += 1
            
            if agent_transitions:
                transition_counts = list(agent_transitions.values())
                fig.add_trace(
                    go.Histogram(x=transition_counts, name='Agent Activity', opacity=0.7),
                    row=2, col=2
                )
            
            # Update layout
            fig.update_layout(
                title_text=f'Cognitive State Transition Analysis - {experiment_id}',
                title_x=0.5,
                height=800,
                showlegend=True
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Day", row=1, col=1)
            fig.update_yaxes(title_text="Number of Transitions", row=1, col=1)
            fig.update_xaxes(title_text="Transition Type", row=1, col=2)
            fig.update_yaxes(title_text="Count", row=1, col=2)
            fig.update_xaxes(title_text="Transitions per Agent", row=2, col=2)
            fig.update_yaxes(title_text="Number of Agents", row=2, col=2)
            
            # Save plot
            output_file = self.output_directory / f"cognitive_transitions_{experiment_id}.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created cognitive transitions plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly cognitive transitions plot: {e}")
            return None
    
    def _analyze_transitions(self, cognitive_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyze cognitive state transitions from data.
        
        Args:
            cognitive_data: DataFrame with cognitive states data
            
        Returns:
            List of transition records
        """
        transitions = []
        
        if 'agent_id' not in cognitive_data.columns or 'cognitive_state' not in cognitive_data.columns:
            return transitions
        
        for agent_id in cognitive_data['agent_id'].unique():
            agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
            
            if len(agent_data) < 2:
                continue
            
            for i in range(len(agent_data) - 1):
                current_row = agent_data.iloc[i]
                next_row = agent_data.iloc[i + 1]
                
                if current_row['cognitive_state'] != next_row['cognitive_state']:
                    transition = {
                        'agent_id': agent_id,
                        'from_state': current_row['cognitive_state'],
                        'to_state': next_row['cognitive_state'],
                        'transition_day': next_row['day'] if 'day' in agent_data.columns else i + 1,
                        'trigger': None  # Could be enhanced with trigger analysis
                    }
                    
                    # Add location information if available
                    if 'location' in agent_data.columns:
                        transition['location'] = current_row['location']
                    
                    transitions.append(transition)
        
        return transitions 
   
    def create_movement_comparison_charts(self, experiment_dirs: List[str], 
                                        comparison_groups: Dict[str, List[str]] = None) -> List[str]:
        """
        Create movement comparison charts for cognitive mode comparisons.
        
        Args:
            experiment_dirs: List of experiment directory paths
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            List of generated plot file paths
        """
        self.logger.info(f"Creating movement comparison charts for {len(experiment_dirs)} experiments")
        
        generated_plots = []
        
        try:
            # Load and process movement data from all experiments
            movement_data = self._load_movement_data_for_comparison(experiment_dirs)
            
            if not movement_data:
                self.logger.warning("No movement data available for comparison charts")
                return generated_plots
            
            # Create different types of movement comparison charts
            plot_types = ['timing_comparison', 'destination_comparison', 'flow_comparison', 'trajectory_comparison']
            
            for plot_type in plot_types:
                try:
                    if plot_type == 'timing_comparison':
                        plot_files = self._create_timing_comparison_charts(movement_data, comparison_groups)
                    elif plot_type == 'destination_comparison':
                        plot_files = self._create_destination_comparison_charts(movement_data, comparison_groups)
                    elif plot_type == 'flow_comparison':
                        plot_files = self._create_flow_comparison_charts(movement_data, comparison_groups)
                    elif plot_type == 'trajectory_comparison':
                        plot_files = self._create_trajectory_comparison_charts(movement_data, comparison_groups)
                    
                    if plot_files:
                        generated_plots.extend(plot_files)
                        
                except Exception as e:
                    self.logger.error(f"Failed to create {plot_type} charts: {e}")
                    continue
            
            self.logger.info(f"Generated {len(generated_plots)} movement comparison charts")
            
        except Exception as e:
            self.logger.error(f"Failed to create movement comparison charts: {e}")
        
        return generated_plots
    
    def _load_movement_data_for_comparison(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Load and organize movement data from multiple experiments for comparison.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary with organized movement data
        """
        movement_data = {
            'experiments': {},
            'combined_data': [],
            'metadata': {}
        }
        
        for experiment_dir in experiment_dirs:
            try:
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Store individual experiment data
                movement_data['experiments'][results.experiment_id] = {
                    'data': results.movement_data,
                    'metadata': results.metrics.get('metadata', {}),
                    'cognitive_data': results.cognitive_states
                }
                
                # Add to combined dataset
                combined_df = results.movement_data.copy()
                combined_df['experiment_id'] = results.experiment_id
                movement_data['combined_data'].append(combined_df)
                
                # Extract cognitive mode from metadata if available
                metadata = results.metrics.get('metadata', {})
                cognitive_mode = metadata.get('cognitive_mode', 'unknown')
                movement_data['metadata'][results.experiment_id] = {
                    'cognitive_mode': cognitive_mode,
                    'topology': metadata.get('topology_type', 'unknown'),
                    'scenario': metadata.get('scenario_type', 'unknown')
                }
                
            except Exception as e:
                self.logger.error(f"Failed to load movement data for {experiment_dir}: {e}")
                continue
        
        # Combine all data
        if movement_data['combined_data']:
            movement_data['combined_df'] = pd.concat(movement_data['combined_data'], ignore_index=True)
        else:
            movement_data['combined_df'] = pd.DataFrame()
        
        return movement_data
    
    def _create_timing_comparison_charts(self, movement_data: Dict[str, Any], 
                                       comparison_groups: Dict[str, List[str]] = None) -> List[str]:
        """
        Create timing comparison charts between experiments.
        
        Args:
            movement_data: Dictionary with movement data from multiple experiments
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        try:
            if self.backend == 'matplotlib':
                plot_file = self._create_matplotlib_timing_comparison(movement_data, comparison_groups)
            else:
                plot_file = self._create_plotly_timing_comparison(movement_data, comparison_groups)
            
            if plot_file:
                generated_plots.append(plot_file)
                
        except Exception as e:
            self.logger.error(f"Failed to create timing comparison charts: {e}")
        
        return generated_plots
    
    def _create_matplotlib_timing_comparison(self, movement_data: Dict[str, Any], 
                                           comparison_groups: Dict[str, List[str]] = None) -> Optional[str]:
        """
        Create timing comparison chart using matplotlib.
        
        Args:
            movement_data: Dictionary with movement data
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Movement Timing Comparison Analysis', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            combined_df = movement_data['combined_df']
            metadata = movement_data['metadata']
            
            if combined_df.empty:
                return None
            
            # Plot 1: Daily movement patterns by cognitive mode
            ax1 = axes[0, 0]
            if 'day' in combined_df.columns and 'refugees' in combined_df.columns:
                # Group by cognitive mode
                cognitive_modes = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    if mode not in cognitive_modes:
                        cognitive_modes[mode] = []
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    daily_totals = exp_data.groupby('day')['refugees'].sum()
                    cognitive_modes[mode].append(daily_totals)
                
                # Plot average daily movement for each cognitive mode
                for mode, daily_data_list in cognitive_modes.items():
                    if daily_data_list:
                        # Align all series to same index and calculate mean
                        all_days = set()
                        for daily_data in daily_data_list:
                            all_days.update(daily_data.index)
                        all_days = sorted(all_days)
                        
                        aligned_data = []
                        for daily_data in daily_data_list:
                            aligned_series = daily_data.reindex(all_days, fill_value=0)
                            aligned_data.append(aligned_series)
                        
                        if aligned_data:
                            mean_daily = pd.concat(aligned_data, axis=1).mean(axis=1)
                            std_daily = pd.concat(aligned_data, axis=1).std(axis=1)
                            
                            ax1.plot(mean_daily.index, mean_daily.values, 
                                    label=f'{mode} (n={len(aligned_data)})', 
                                    linewidth=self.plot_config.line_width, alpha=self.plot_config.alpha)
                            ax1.fill_between(mean_daily.index, 
                                           mean_daily - std_daily, 
                                           mean_daily + std_daily, 
                                           alpha=0.2)
                
                ax1.set_xlabel('Day')
                ax1.set_ylabel('Average Daily Refugees')
                ax1.set_title('Daily Movement Patterns by Cognitive Mode')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            
            # Plot 2: First movement day comparison
            ax2 = axes[0, 1]
            first_movement_days = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'refugees' in data.columns:
                    refugee_data = data[data['refugees'] > 0]
                    if not refugee_data.empty:
                        first_day = refugee_data['day'].min()
                        mode = metadata[exp_id]['cognitive_mode']
                        if mode not in first_movement_days:
                            first_movement_days[mode] = []
                        first_movement_days[mode].append(first_day)
            
            if first_movement_days:
                modes = list(first_movement_days.keys())
                first_days_data = [first_movement_days[mode] for mode in modes]
                
                bp = ax2.boxplot(first_days_data, labels=modes, patch_artist=True)
                for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(self.plot_config.alpha)
                
                ax2.set_xlabel('Cognitive Mode')
                ax2.set_ylabel('First Movement Day')
                ax2.set_title('First Movement Day by Cognitive Mode')
                ax2.grid(True, alpha=0.3)
            
            # Plot 3: Peak movement timing
            ax3 = axes[1, 0]
            peak_days = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'refugees' in data.columns:
                    daily_totals = data.groupby('day')['refugees'].sum()
                    if not daily_totals.empty:
                        peak_day = daily_totals.idxmax()
                        mode = metadata[exp_id]['cognitive_mode']
                        if mode not in peak_days:
                            peak_days[mode] = []
                        peak_days[mode].append(peak_day)
            
            if peak_days:
                modes = list(peak_days.keys())
                peak_days_data = [peak_days[mode] for mode in modes]
                
                bp = ax3.boxplot(peak_days_data, labels=modes, patch_artist=True)
                for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(self.plot_config.alpha)
                
                ax3.set_xlabel('Cognitive Mode')
                ax3.set_ylabel('Peak Movement Day')
                ax3.set_title('Peak Movement Timing by Cognitive Mode')
                ax3.grid(True, alpha=0.3)
            
            # Plot 4: Movement duration comparison
            ax4 = axes[1, 1]
            movement_durations = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'refugees' in data.columns:
                    refugee_data = data[data['refugees'] > 0]
                    if not refugee_data.empty:
                        duration = refugee_data['day'].max() - refugee_data['day'].min() + 1
                        mode = metadata[exp_id]['cognitive_mode']
                        if mode not in movement_durations:
                            movement_durations[mode] = []
                        movement_durations[mode].append(duration)
            
            if movement_durations:
                modes = list(movement_durations.keys())
                duration_data = [movement_durations[mode] for mode in modes]
                
                bp = ax4.boxplot(duration_data, labels=modes, patch_artist=True)
                for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(self.plot_config.alpha)
                
                ax4.set_xlabel('Cognitive Mode')
                ax4.set_ylabel('Movement Duration (Days)')
                ax4.set_title('Movement Duration by Cognitive Mode')
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"movement_timing_comparison.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created timing comparison chart: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib timing comparison: {e}")
            return None
    
    def _create_plotly_timing_comparison(self, movement_data: Dict[str, Any], 
                                       comparison_groups: Dict[str, List[str]] = None) -> Optional[str]:
        """
        Create timing comparison chart using plotly.
        
        Args:
            movement_data: Dictionary with movement data
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            Path to generated plot file
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Daily Movement Patterns by Cognitive Mode', 
                               'First Movement Day Distribution',
                               'Peak Movement Timing', 
                               'Movement Duration Comparison')
            )
            
            combined_df = movement_data['combined_df']
            metadata = movement_data['metadata']
            
            if combined_df.empty:
                return None
            
            # Plot 1: Daily movement patterns by cognitive mode
            if 'day' in combined_df.columns and 'refugees' in combined_df.columns:
                cognitive_modes = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    if mode not in cognitive_modes:
                        cognitive_modes[mode] = []
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    daily_totals = exp_data.groupby('day')['refugees'].sum()
                    cognitive_modes[mode].append(daily_totals)
                
                for mode, daily_data_list in cognitive_modes.items():
                    if daily_data_list:
                        all_days = set()
                        for daily_data in daily_data_list:
                            all_days.update(daily_data.index)
                        all_days = sorted(all_days)
                        
                        aligned_data = []
                        for daily_data in daily_data_list:
                            aligned_series = daily_data.reindex(all_days, fill_value=0)
                            aligned_data.append(aligned_series)
                        
                        if aligned_data:
                            mean_daily = pd.concat(aligned_data, axis=1).mean(axis=1)
                            std_daily = pd.concat(aligned_data, axis=1).std(axis=1)
                            
                            fig.add_trace(
                                go.Scatter(x=mean_daily.index, y=mean_daily.values,
                                          mode='lines', name=f'{mode} (n={len(aligned_data)})',
                                          line=dict(width=3)),
                                row=1, col=1
                            )
                            
                            # Add confidence bands
                            fig.add_trace(
                                go.Scatter(x=mean_daily.index, 
                                          y=mean_daily + std_daily,
                                          mode='lines', line=dict(width=0),
                                          showlegend=False, hoverinfo='skip'),
                                row=1, col=1
                            )
                            fig.add_trace(
                                go.Scatter(x=mean_daily.index, 
                                          y=mean_daily - std_daily,
                                          mode='lines', line=dict(width=0),
                                          fill='tonexty', fillcolor=f'rgba(0,100,80,0.2)',
                                          showlegend=False, hoverinfo='skip'),
                                row=1, col=1
                            )
            
            # Plot 2: First movement day comparison
            first_movement_days = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'refugees' in data.columns:
                    refugee_data = data[data['refugees'] > 0]
                    if not refugee_data.empty:
                        first_day = refugee_data['day'].min()
                        mode = metadata[exp_id]['cognitive_mode']
                        if mode not in first_movement_days:
                            first_movement_days[mode] = []
                        first_movement_days[mode].append(first_day)
            
            for mode, days in first_movement_days.items():
                fig.add_trace(
                    go.Box(y=days, name=f'{mode} First Day', opacity=0.7),
                    row=1, col=2
                )
            
            # Plot 3: Peak movement timing
            peak_days = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'refugees' in data.columns:
                    daily_totals = data.groupby('day')['refugees'].sum()
                    if not daily_totals.empty:
                        peak_day = daily_totals.idxmax()
                        mode = metadata[exp_id]['cognitive_mode']
                        if mode not in peak_days:
                            peak_days[mode] = []
                        peak_days[mode].append(peak_day)
            
            for mode, days in peak_days.items():
                fig.add_trace(
                    go.Box(y=days, name=f'{mode} Peak Day', opacity=0.7),
                    row=2, col=1
                )
            
            # Plot 4: Movement duration comparison
            movement_durations = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'refugees' in data.columns:
                    refugee_data = data[data['refugees'] > 0]
                    if not refugee_data.empty:
                        duration = refugee_data['day'].max() - refugee_data['day'].min() + 1
                        mode = metadata[exp_id]['cognitive_mode']
                        if mode not in movement_durations:
                            movement_durations[mode] = []
                        movement_durations[mode].append(duration)
            
            for mode, durations in movement_durations.items():
                fig.add_trace(
                    go.Box(y=durations, name=f'{mode} Duration', opacity=0.7),
                    row=2, col=2
                )
            
            # Update layout
            fig.update_layout(
                title_text='Movement Timing Comparison Analysis',
                title_x=0.5,
                height=800,
                showlegend=True
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Day", row=1, col=1)
            fig.update_yaxes(title_text="Average Daily Refugees", row=1, col=1)
            fig.update_yaxes(title_text="First Movement Day", row=1, col=2)
            fig.update_yaxes(title_text="Peak Movement Day", row=2, col=1)
            fig.update_yaxes(title_text="Duration (Days)", row=2, col=2)
            
            # Save plot
            output_file = self.output_directory / f"movement_timing_comparison.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created timing comparison chart: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly timing comparison: {e}")
            return None  
  
    def _create_destination_comparison_charts(self, movement_data: Dict[str, Any], 
                                            comparison_groups: Dict[str, List[str]] = None) -> List[str]:
        """
        Create destination comparison charts between experiments.
        
        Args:
            movement_data: Dictionary with movement data from multiple experiments
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        try:
            if self.backend == 'matplotlib':
                plot_file = self._create_matplotlib_destination_comparison(movement_data, comparison_groups)
            else:
                plot_file = self._create_plotly_destination_comparison(movement_data, comparison_groups)
            
            if plot_file:
                generated_plots.append(plot_file)
                
        except Exception as e:
            self.logger.error(f"Failed to create destination comparison charts: {e}")
        
        return generated_plots
    
    def _create_matplotlib_destination_comparison(self, movement_data: Dict[str, Any], 
                                                comparison_groups: Dict[str, List[str]] = None) -> Optional[str]:
        """
        Create destination comparison chart using matplotlib.
        
        Args:
            movement_data: Dictionary with movement data
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Destination Distribution Comparison Analysis', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            combined_df = movement_data['combined_df']
            metadata = movement_data['metadata']
            
            if combined_df.empty:
                return None
            
            # Plot 1: Final destination distribution by cognitive mode
            ax1 = axes[0, 0]
            if 'day' in combined_df.columns and 'location' in combined_df.columns and 'refugees' in combined_df.columns:
                # Get final day data for each experiment
                final_destinations = {}
                for exp_id, exp_data in movement_data['experiments'].items():
                    data = exp_data['data']
                    if 'day' in data.columns:
                        final_day = data['day'].max()
                        final_data = data[data['day'] == final_day]
                        if not final_data.empty and 'refugees' in final_data.columns:
                            dest_counts = final_data.groupby('location')['refugees'].sum()
                            total_refugees = dest_counts.sum()
                            if total_refugees > 0:
                                dest_props = dest_counts / total_refugees
                                mode = metadata[exp_id]['cognitive_mode']
                                if mode not in final_destinations:
                                    final_destinations[mode] = []
                                final_destinations[mode].append(dest_props)
                
                # Plot average destination distributions
                if final_destinations:
                    all_locations = set()
                    for mode_data in final_destinations.values():
                        for dest_props in mode_data:
                            all_locations.update(dest_props.index)
                    all_locations = sorted(all_locations)
                    
                    x_pos = np.arange(len(all_locations))
                    width = 0.8 / len(final_destinations)
                    
                    for i, (mode, dest_data_list) in enumerate(final_destinations.items()):
                        if dest_data_list:
                            # Average across experiments
                            aligned_data = []
                            for dest_props in dest_data_list:
                                aligned_props = dest_props.reindex(all_locations, fill_value=0)
                                aligned_data.append(aligned_props)
                            
                            mean_props = pd.concat(aligned_data, axis=1).mean(axis=1)
                            std_props = pd.concat(aligned_data, axis=1).std(axis=1)
                            
                            ax1.bar(x_pos + i * width, mean_props.values, width, 
                                   label=f'{mode} (n={len(aligned_data)})', 
                                   alpha=self.plot_config.alpha,
                                   yerr=std_props.values, capsize=3)
                    
                    ax1.set_xlabel('Destination Location')
                    ax1.set_ylabel('Average Proportion of Refugees')
                    ax1.set_title('Final Destination Distribution by Cognitive Mode')
                    ax1.set_xticks(x_pos + width * (len(final_destinations) - 1) / 2)
                    ax1.set_xticklabels(all_locations, rotation=45, ha='right')
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)
            
            # Plot 2: Destination concentration metrics
            ax2 = axes[0, 1]
            concentration_metrics = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'location' in data.columns and 'refugees' in data.columns:
                    final_day = data['day'].max()
                    final_data = data[data['day'] == final_day]
                    if not final_data.empty:
                        dest_counts = final_data.groupby('location')['refugees'].sum()
                        total_refugees = dest_counts.sum()
                        if total_refugees > 0:
                            dest_props = dest_counts / total_refugees
                            
                            # Calculate Gini coefficient
                            sorted_props = np.sort(dest_props.values)
                            n = len(sorted_props)
                            index = np.arange(1, n + 1)
                            gini = (2 * np.sum(index * sorted_props)) / (n * np.sum(sorted_props)) - (n + 1) / n
                            
                            # Calculate entropy
                            entropy = -np.sum(dest_props * np.log2(dest_props + 1e-10))
                            max_entropy = np.log2(len(dest_props))
                            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
                            
                            mode = metadata[exp_id]['cognitive_mode']
                            if mode not in concentration_metrics:
                                concentration_metrics[mode] = {'gini': [], 'entropy': []}
                            concentration_metrics[mode]['gini'].append(gini)
                            concentration_metrics[mode]['entropy'].append(normalized_entropy)
            
            if concentration_metrics:
                modes = list(concentration_metrics.keys())
                gini_data = [concentration_metrics[mode]['gini'] for mode in modes]
                
                bp = ax2.boxplot(gini_data, labels=modes, patch_artist=True)
                for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(self.plot_config.alpha)
                
                ax2.set_xlabel('Cognitive Mode')
                ax2.set_ylabel('Gini Coefficient')
                ax2.set_title('Destination Concentration (Gini) by Cognitive Mode')
                ax2.grid(True, alpha=0.3)
            
            # Plot 3: Entropy comparison
            ax3 = axes[1, 0]
            if concentration_metrics:
                entropy_data = [concentration_metrics[mode]['entropy'] for mode in modes]
                
                bp = ax3.boxplot(entropy_data, labels=modes, patch_artist=True)
                for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(self.plot_config.alpha)
                
                ax3.set_xlabel('Cognitive Mode')
                ax3.set_ylabel('Normalized Entropy')
                ax3.set_title('Destination Diversity (Entropy) by Cognitive Mode')
                ax3.grid(True, alpha=0.3)
            
            # Plot 4: Top destination preferences
            ax4 = axes[1, 1]
            top_destinations = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'location' in data.columns and 'refugees' in data.columns:
                    final_day = data['day'].max()
                    final_data = data[data['day'] == final_day]
                    if not final_data.empty:
                        dest_counts = final_data.groupby('location')['refugees'].sum().sort_values(ascending=False)
                        if not dest_counts.empty:
                            top_dest = dest_counts.index[0]
                            top_prop = dest_counts.iloc[0] / dest_counts.sum()
                            
                            mode = metadata[exp_id]['cognitive_mode']
                            if mode not in top_destinations:
                                top_destinations[mode] = []
                            top_destinations[mode].append(top_prop)
            
            if top_destinations:
                modes = list(top_destinations.keys())
                top_dest_data = [top_destinations[mode] for mode in modes]
                
                bp = ax4.boxplot(top_dest_data, labels=modes, patch_artist=True)
                for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(self.plot_config.alpha)
                
                ax4.set_xlabel('Cognitive Mode')
                ax4.set_ylabel('Proportion in Top Destination')
                ax4.set_title('Top Destination Concentration by Cognitive Mode')
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"destination_comparison.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created destination comparison chart: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib destination comparison: {e}")
            return None
    
    def _create_plotly_destination_comparison(self, movement_data: Dict[str, Any], 
                                            comparison_groups: Dict[str, List[str]] = None) -> Optional[str]:
        """
        Create destination comparison chart using plotly.
        
        Args:
            movement_data: Dictionary with movement data
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            Path to generated plot file
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Final Destination Distribution by Cognitive Mode', 
                               'Destination Concentration (Gini)',
                               'Destination Diversity (Entropy)', 
                               'Top Destination Concentration')
            )
            
            combined_df = movement_data['combined_df']
            metadata = movement_data['metadata']
            
            if combined_df.empty:
                return None
            
            # Plot 1: Final destination distribution by cognitive mode
            if 'day' in combined_df.columns and 'location' in combined_df.columns and 'refugees' in combined_df.columns:
                final_destinations = {}
                for exp_id, exp_data in movement_data['experiments'].items():
                    data = exp_data['data']
                    if 'day' in data.columns:
                        final_day = data['day'].max()
                        final_data = data[data['day'] == final_day]
                        if not final_data.empty and 'refugees' in final_data.columns:
                            dest_counts = final_data.groupby('location')['refugees'].sum()
                            total_refugees = dest_counts.sum()
                            if total_refugees > 0:
                                dest_props = dest_counts / total_refugees
                                mode = metadata[exp_id]['cognitive_mode']
                                if mode not in final_destinations:
                                    final_destinations[mode] = []
                                final_destinations[mode].append(dest_props)
                
                if final_destinations:
                    all_locations = set()
                    for mode_data in final_destinations.values():
                        for dest_props in mode_data:
                            all_locations.update(dest_props.index)
                    all_locations = sorted(all_locations)
                    
                    for mode, dest_data_list in final_destinations.items():
                        if dest_data_list:
                            aligned_data = []
                            for dest_props in dest_data_list:
                                aligned_props = dest_props.reindex(all_locations, fill_value=0)
                                aligned_data.append(aligned_props)
                            
                            mean_props = pd.concat(aligned_data, axis=1).mean(axis=1)
                            std_props = pd.concat(aligned_data, axis=1).std(axis=1)
                            
                            fig.add_trace(
                                go.Bar(x=all_locations, y=mean_props.values,
                                      name=f'{mode} (n={len(aligned_data)})',
                                      error_y=dict(type='data', array=std_props.values),
                                      opacity=0.7),
                                row=1, col=1
                            )
            
            # Plot 2-4: Concentration metrics
            concentration_metrics = {}
            for exp_id, exp_data in movement_data['experiments'].items():
                data = exp_data['data']
                if 'day' in data.columns and 'location' in data.columns and 'refugees' in data.columns:
                    final_day = data['day'].max()
                    final_data = data[data['day'] == final_day]
                    if not final_data.empty:
                        dest_counts = final_data.groupby('location')['refugees'].sum()
                        total_refugees = dest_counts.sum()
                        if total_refugees > 0:
                            dest_props = dest_counts / total_refugees
                            
                            # Calculate metrics
                            sorted_props = np.sort(dest_props.values)
                            n = len(sorted_props)
                            index = np.arange(1, n + 1)
                            gini = (2 * np.sum(index * sorted_props)) / (n * np.sum(sorted_props)) - (n + 1) / n
                            
                            entropy = -np.sum(dest_props * np.log2(dest_props + 1e-10))
                            max_entropy = np.log2(len(dest_props))
                            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
                            
                            top_prop = dest_props.max()
                            
                            mode = metadata[exp_id]['cognitive_mode']
                            if mode not in concentration_metrics:
                                concentration_metrics[mode] = {'gini': [], 'entropy': [], 'top_prop': []}
                            concentration_metrics[mode]['gini'].append(gini)
                            concentration_metrics[mode]['entropy'].append(normalized_entropy)
                            concentration_metrics[mode]['top_prop'].append(top_prop)
            
            # Add box plots for metrics
            for mode, metrics in concentration_metrics.items():
                fig.add_trace(
                    go.Box(y=metrics['gini'], name=f'{mode} Gini', opacity=0.7),
                    row=1, col=2
                )
                fig.add_trace(
                    go.Box(y=metrics['entropy'], name=f'{mode} Entropy', opacity=0.7),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Box(y=metrics['top_prop'], name=f'{mode} Top Dest', opacity=0.7),
                    row=2, col=2
                )
            
            # Update layout
            fig.update_layout(
                title_text='Destination Distribution Comparison Analysis',
                title_x=0.5,
                height=800,
                showlegend=True
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Destination Location", row=1, col=1)
            fig.update_yaxes(title_text="Average Proportion", row=1, col=1)
            fig.update_yaxes(title_text="Gini Coefficient", row=1, col=2)
            fig.update_yaxes(title_text="Normalized Entropy", row=2, col=1)
            fig.update_yaxes(title_text="Top Destination Proportion", row=2, col=2)
            
            # Save plot
            output_file = self.output_directory / f"destination_comparison.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created destination comparison chart: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly destination comparison: {e}")
            return None
    
    def _create_flow_comparison_charts(self, movement_data: Dict[str, Any], 
                                     comparison_groups: Dict[str, List[str]] = None) -> List[str]:
        """
        Create network flow diagrams showing agent movement patterns.
        
        Args:
            movement_data: Dictionary with movement data from multiple experiments
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        try:
            # Create flow diagrams for each cognitive mode
            metadata = movement_data['metadata']
            cognitive_modes = set(meta['cognitive_mode'] for meta in metadata.values())
            
            for mode in cognitive_modes:
                mode_experiments = [exp_id for exp_id, meta in metadata.items() 
                                 if meta['cognitive_mode'] == mode]
                
                if self.backend == 'matplotlib':
                    plot_file = self._create_matplotlib_flow_diagram(movement_data, mode, mode_experiments)
                else:
                    plot_file = self._create_plotly_flow_diagram(movement_data, mode, mode_experiments)
                
                if plot_file:
                    generated_plots.append(plot_file)
                    
        except Exception as e:
            self.logger.error(f"Failed to create flow comparison charts: {e}")
        
        return generated_plots
    
    def _create_matplotlib_flow_diagram(self, movement_data: Dict[str, Any], 
                                      cognitive_mode: str, experiment_ids: List[str]) -> Optional[str]:
        """
        Create network flow diagram using matplotlib.
        
        Args:
            movement_data: Dictionary with movement data
            cognitive_mode: Cognitive mode to analyze
            experiment_ids: List of experiment IDs for this mode
            
        Returns:
            Path to generated plot file
        """
        try:
            # This is a simplified flow diagram - in practice, you might want to use networkx
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            
            # Aggregate flow data across experiments
            flow_data = {}
            location_totals = {}
            
            for exp_id in experiment_ids:
                if exp_id not in movement_data['experiments']:
                    continue
                
                data = movement_data['experiments'][exp_id]['data']
                if 'day' in data.columns and 'location' in data.columns and 'refugees' in data.columns:
                    # Calculate flows between time periods
                    for day in sorted(data['day'].unique()):
                        day_data = data[data['day'] == day]
                        for _, row in day_data.iterrows():
                            location = row['location']
                            refugees = row['refugees']
                            
                            if location not in location_totals:
                                location_totals[location] = 0
                            location_totals[location] += refugees
            
            if location_totals:
                # Create a simple bar chart showing total refugees by location
                locations = list(location_totals.keys())
                totals = list(location_totals.values())
                
                bars = ax.bar(locations, totals, alpha=self.plot_config.alpha)
                
                # Color bars by refugee count
                max_total = max(totals) if totals else 1
                for bar, total in zip(bars, totals):
                    color_intensity = total / max_total
                    bar.set_color(plt.cm.Blues(color_intensity))
                
                ax.set_xlabel('Location')
                ax.set_ylabel('Total Refugees')
                ax.set_title(f'Refugee Distribution - {cognitive_mode} Mode')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar, total in zip(bars, totals):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(total)}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"flow_diagram_{cognitive_mode.replace(' ', '_')}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created flow diagram: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib flow diagram: {e}")
            return None
    
    def _create_plotly_flow_diagram(self, movement_data: Dict[str, Any], 
                                  cognitive_mode: str, experiment_ids: List[str]) -> Optional[str]:
        """
        Create network flow diagram using plotly.
        
        Args:
            movement_data: Dictionary with movement data
            cognitive_mode: Cognitive mode to analyze
            experiment_ids: List of experiment IDs for this mode
            
        Returns:
            Path to generated plot file
        """
        try:
            # Aggregate flow data across experiments
            flow_data = {}
            location_totals = {}
            
            for exp_id in experiment_ids:
                if exp_id not in movement_data['experiments']:
                    continue
                
                data = movement_data['experiments'][exp_id]['data']
                if 'day' in data.columns and 'location' in data.columns and 'refugees' in data.columns:
                    for day in sorted(data['day'].unique()):
                        day_data = data[data['day'] == day]
                        for _, row in day_data.iterrows():
                            location = row['location']
                            refugees = row['refugees']
                            
                            if location not in location_totals:
                                location_totals[location] = 0
                            location_totals[location] += refugees
            
            if location_totals:
                locations = list(location_totals.keys())
                totals = list(location_totals.values())
                
                # Create bar chart
                fig = go.Figure(data=[
                    go.Bar(x=locations, y=totals, 
                          marker_color=totals,
                          marker_colorscale='Blues',
                          text=[f'{int(total)}' for total in totals],
                          textposition='auto')
                ])
                
                fig.update_layout(
                    title=f'Refugee Distribution - {cognitive_mode} Mode',
                    xaxis_title='Location',
                    yaxis_title='Total Refugees',
                    xaxis_tickangle=-45
                )
                
                # Save plot
                output_file = self.output_directory / f"flow_diagram_{cognitive_mode.replace(' ', '_')}.html"
                fig.write_html(str(output_file))
                
                self.logger.debug(f"Created flow diagram: {output_file}")
                return str(output_file)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly flow diagram: {e}")
            return None
    
    def _create_trajectory_comparison_charts(self, movement_data: Dict[str, Any], 
                                           comparison_groups: Dict[str, List[str]] = None) -> List[str]:
        """
        Create trajectory comparison charts for different cognitive modes.
        
        Args:
            movement_data: Dictionary with movement data from multiple experiments
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        try:
            if self.backend == 'matplotlib':
                plot_file = self._create_matplotlib_trajectory_comparison(movement_data, comparison_groups)
            else:
                plot_file = self._create_plotly_trajectory_comparison(movement_data, comparison_groups)
            
            if plot_file:
                generated_plots.append(plot_file)
                
        except Exception as e:
            self.logger.error(f"Failed to create trajectory comparison charts: {e}")
        
        return generated_plots
    
    def _create_matplotlib_trajectory_comparison(self, movement_data: Dict[str, Any], 
                                               comparison_groups: Dict[str, List[str]] = None) -> Optional[str]:
        """
        Create trajectory comparison chart using matplotlib.
        
        Args:
            movement_data: Dictionary with movement data
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Movement Trajectory Comparison Analysis', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            combined_df = movement_data['combined_df']
            metadata = movement_data['metadata']
            
            if combined_df.empty:
                return None
            
            # Plot 1: Cumulative refugee movements over time by cognitive mode
            ax1 = axes[0, 0]
            if 'day' in combined_df.columns and 'refugees' in combined_df.columns:
                cognitive_modes = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    if mode not in cognitive_modes:
                        cognitive_modes[mode] = []
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    daily_totals = exp_data.groupby('day')['refugees'].sum().cumsum()
                    cognitive_modes[mode].append(daily_totals)
                
                for mode, daily_data_list in cognitive_modes.items():
                    if daily_data_list:
                        all_days = set()
                        for daily_data in daily_data_list:
                            all_days.update(daily_data.index)
                        all_days = sorted(all_days)
                        
                        aligned_data = []
                        for daily_data in daily_data_list:
                            aligned_series = daily_data.reindex(all_days, method='ffill', fill_value=0)
                            aligned_data.append(aligned_series)
                        
                        if aligned_data:
                            mean_cumulative = pd.concat(aligned_data, axis=1).mean(axis=1)
                            std_cumulative = pd.concat(aligned_data, axis=1).std(axis=1)
                            
                            ax1.plot(mean_cumulative.index, mean_cumulative.values, 
                                    label=f'{mode} (n={len(aligned_data)})', 
                                    linewidth=self.plot_config.line_width, alpha=self.plot_config.alpha)
                            ax1.fill_between(mean_cumulative.index, 
                                           mean_cumulative - std_cumulative, 
                                           mean_cumulative + std_cumulative, 
                                           alpha=0.2)
                
                ax1.set_xlabel('Day')
                ax1.set_ylabel('Cumulative Refugees')
                ax1.set_title('Cumulative Movement Trajectories by Cognitive Mode')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            
            # Plot 2: Movement velocity (daily change) comparison
            ax2 = axes[0, 1]
            if 'day' in combined_df.columns and 'refugees' in combined_df.columns:
                velocity_data = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    daily_totals = exp_data.groupby('day')['refugees'].sum()
                    daily_changes = daily_totals.diff().dropna()
                    
                    if mode not in velocity_data:
                        velocity_data[mode] = []
                    velocity_data[mode].extend(daily_changes.values)
                
                if velocity_data:
                    modes = list(velocity_data.keys())
                    velocity_values = [velocity_data[mode] for mode in modes]
                    
                    bp = ax2.boxplot(velocity_values, labels=modes, patch_artist=True)
                    for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                        patch.set_facecolor(color)
                        patch.set_alpha(self.plot_config.alpha)
                    
                    ax2.set_xlabel('Cognitive Mode')
                    ax2.set_ylabel('Daily Movement Change')
                    ax2.set_title('Movement Velocity Distribution by Cognitive Mode')
                    ax2.grid(True, alpha=0.3)
            
            # Plot 3: Location diversity over time
            ax3 = axes[1, 0]
            if 'day' in combined_df.columns and 'location' in combined_df.columns:
                diversity_data = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    
                    daily_diversity = []
                    for day in sorted(exp_data['day'].unique()):
                        day_data = exp_data[exp_data['day'] == day]
                        unique_locations = day_data['location'].nunique()
                        daily_diversity.append(unique_locations)
                    
                    if mode not in diversity_data:
                        diversity_data[mode] = []
                    diversity_data[mode].append(pd.Series(daily_diversity, index=sorted(exp_data['day'].unique())))
                
                for mode, diversity_list in diversity_data.items():
                    if diversity_list:
                        all_days = set()
                        for diversity_series in diversity_list:
                            all_days.update(diversity_series.index)
                        all_days = sorted(all_days)
                        
                        aligned_data = []
                        for diversity_series in diversity_list:
                            aligned_series = diversity_series.reindex(all_days, method='ffill', fill_value=0)
                            aligned_data.append(aligned_series)
                        
                        if aligned_data:
                            mean_diversity = pd.concat(aligned_data, axis=1).mean(axis=1)
                            
                            ax3.plot(mean_diversity.index, mean_diversity.values, 
                                    label=f'{mode} (n={len(aligned_data)})', 
                                    linewidth=self.plot_config.line_width, alpha=self.plot_config.alpha)
                
                ax3.set_xlabel('Day')
                ax3.set_ylabel('Number of Active Locations')
                ax3.set_title('Location Diversity Over Time by Cognitive Mode')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
            
            # Plot 4: Movement efficiency (refugees per location)
            ax4 = axes[1, 1]
            if 'day' in combined_df.columns and 'location' in combined_df.columns and 'refugees' in combined_df.columns:
                efficiency_data = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    
                    # Calculate final efficiency
                    final_day = exp_data['day'].max()
                    final_data = exp_data[exp_data['day'] == final_day]
                    total_refugees = final_data['refugees'].sum()
                    unique_locations = final_data['location'].nunique()
                    
                    if unique_locations > 0:
                        efficiency = total_refugees / unique_locations
                        if mode not in efficiency_data:
                            efficiency_data[mode] = []
                        efficiency_data[mode].append(efficiency)
                
                if efficiency_data:
                    modes = list(efficiency_data.keys())
                    efficiency_values = [efficiency_data[mode] for mode in modes]
                    
                    bp = ax4.boxplot(efficiency_values, labels=modes, patch_artist=True)
                    for patch, color in zip(bp['boxes'], plt.cm.Set2.colors):
                        patch.set_facecolor(color)
                        patch.set_alpha(self.plot_config.alpha)
                    
                    ax4.set_xlabel('Cognitive Mode')
                    ax4.set_ylabel('Refugees per Location')
                    ax4.set_title('Movement Efficiency by Cognitive Mode')
                    ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"trajectory_comparison.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created trajectory comparison chart: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib trajectory comparison: {e}")
            return None
    
    def _create_plotly_trajectory_comparison(self, movement_data: Dict[str, Any], 
                                           comparison_groups: Dict[str, List[str]] = None) -> Optional[str]:
        """
        Create trajectory comparison chart using plotly.
        
        Args:
            movement_data: Dictionary with movement data
            comparison_groups: Dictionary mapping group names to experiment lists
            
        Returns:
            Path to generated plot file
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Cumulative Movement Trajectories', 
                               'Movement Velocity Distribution',
                               'Location Diversity Over Time', 
                               'Movement Efficiency')
            )
            
            combined_df = movement_data['combined_df']
            metadata = movement_data['metadata']
            
            if combined_df.empty:
                return None
            
            # Plot 1: Cumulative refugee movements
            if 'day' in combined_df.columns and 'refugees' in combined_df.columns:
                cognitive_modes = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    if mode not in cognitive_modes:
                        cognitive_modes[mode] = []
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    daily_totals = exp_data.groupby('day')['refugees'].sum().cumsum()
                    cognitive_modes[mode].append(daily_totals)
                
                for mode, daily_data_list in cognitive_modes.items():
                    if daily_data_list:
                        all_days = set()
                        for daily_data in daily_data_list:
                            all_days.update(daily_data.index)
                        all_days = sorted(all_days)
                        
                        aligned_data = []
                        for daily_data in daily_data_list:
                            aligned_series = daily_data.reindex(all_days, method='ffill', fill_value=0)
                            aligned_data.append(aligned_series)
                        
                        if aligned_data:
                            mean_cumulative = pd.concat(aligned_data, axis=1).mean(axis=1)
                            std_cumulative = pd.concat(aligned_data, axis=1).std(axis=1)
                            
                            fig.add_trace(
                                go.Scatter(x=mean_cumulative.index, y=mean_cumulative.values,
                                          mode='lines', name=f'{mode} (n={len(aligned_data)})',
                                          line=dict(width=3)),
                                row=1, col=1
                            )
                            
                            # Add confidence bands
                            fig.add_trace(
                                go.Scatter(x=mean_cumulative.index, 
                                          y=mean_cumulative + std_cumulative,
                                          mode='lines', line=dict(width=0),
                                          showlegend=False, hoverinfo='skip'),
                                row=1, col=1
                            )
                            fig.add_trace(
                                go.Scatter(x=mean_cumulative.index, 
                                          y=mean_cumulative - std_cumulative,
                                          mode='lines', line=dict(width=0),
                                          fill='tonexty', fillcolor=f'rgba(0,100,80,0.2)',
                                          showlegend=False, hoverinfo='skip'),
                                row=1, col=1
                            )
            
            # Plot 2: Movement velocity
            if 'day' in combined_df.columns and 'refugees' in combined_df.columns:
                velocity_data = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    daily_totals = exp_data.groupby('day')['refugees'].sum()
                    daily_changes = daily_totals.diff().dropna()
                    
                    if mode not in velocity_data:
                        velocity_data[mode] = []
                    velocity_data[mode].extend(daily_changes.values)
                
                for mode, velocities in velocity_data.items():
                    fig.add_trace(
                        go.Box(y=velocities, name=f'{mode} Velocity', opacity=0.7),
                        row=1, col=2
                    )
            
            # Plot 3: Location diversity over time
            if 'day' in combined_df.columns and 'location' in combined_df.columns:
                diversity_data = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    
                    daily_diversity = []
                    for day in sorted(exp_data['day'].unique()):
                        day_data = exp_data[exp_data['day'] == day]
                        unique_locations = day_data['location'].nunique()
                        daily_diversity.append(unique_locations)
                    
                    if mode not in diversity_data:
                        diversity_data[mode] = []
                    diversity_data[mode].append(pd.Series(daily_diversity, index=sorted(exp_data['day'].unique())))
                
                for mode, diversity_list in diversity_data.items():
                    if diversity_list:
                        all_days = set()
                        for diversity_series in diversity_list:
                            all_days.update(diversity_series.index)
                        all_days = sorted(all_days)
                        
                        aligned_data = []
                        for diversity_series in diversity_list:
                            aligned_series = diversity_series.reindex(all_days, method='ffill', fill_value=0)
                            aligned_data.append(aligned_series)
                        
                        if aligned_data:
                            mean_diversity = pd.concat(aligned_data, axis=1).mean(axis=1)
                            
                            fig.add_trace(
                                go.Scatter(x=mean_diversity.index, y=mean_diversity.values,
                                          mode='lines', name=f'{mode} Diversity',
                                          line=dict(width=3)),
                                row=2, col=1
                            )
            
            # Plot 4: Movement efficiency
            if 'day' in combined_df.columns and 'location' in combined_df.columns and 'refugees' in combined_df.columns:
                efficiency_data = {}
                for exp_id, meta in metadata.items():
                    mode = meta['cognitive_mode']
                    exp_data = combined_df[combined_df['experiment_id'] == exp_id]
                    
                    final_day = exp_data['day'].max()
                    final_data = exp_data[exp_data['day'] == final_day]
                    total_refugees = final_data['refugees'].sum()
                    unique_locations = final_data['location'].nunique()
                    
                    if unique_locations > 0:
                        efficiency = total_refugees / unique_locations
                        if mode not in efficiency_data:
                            efficiency_data[mode] = []
                        efficiency_data[mode].append(efficiency)
                
                for mode, efficiencies in efficiency_data.items():
                    fig.add_trace(
                        go.Box(y=efficiencies, name=f'{mode} Efficiency', opacity=0.7),
                        row=2, col=2
                    )
            
            # Update layout
            fig.update_layout(
                title_text='Movement Trajectory Comparison Analysis',
                title_x=0.5,
                height=800,
                showlegend=True
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Day", row=1, col=1)
            fig.update_yaxes(title_text="Cumulative Refugees", row=1, col=1)
            fig.update_yaxes(title_text="Daily Movement Change", row=1, col=2)
            fig.update_xaxes(title_text="Day", row=2, col=1)
            fig.update_yaxes(title_text="Active Locations", row=2, col=1)
            fig.update_yaxes(title_text="Refugees per Location", row=2, col=2)
            
            # Save plot
            output_file = self.output_directory / f"trajectory_comparison.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created trajectory comparison chart: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly trajectory comparison: {e}")
            return None   
 
    def create_parameter_sensitivity_plots(self, sweep_results_dir: str, 
                                         parameters: List[str] = None,
                                         metrics: List[str] = None) -> List[str]:
        """
        Create parameter sensitivity plots for sweep result analysis.
        
        Args:
            sweep_results_dir: Directory containing parameter sweep results
            parameters: List of parameters to analyze (if None, analyze all found)
            metrics: List of metrics to analyze (if None, use default set)
            
        Returns:
            List of generated plot file paths
        """
        self.logger.info(f"Creating parameter sensitivity plots from: {sweep_results_dir}")
        
        generated_plots = []
        
        try:
            # Load parameter sweep data
            sweep_data = self._load_parameter_sweep_data(sweep_results_dir)
            
            if not sweep_data:
                self.logger.warning("No parameter sweep data found")
                return generated_plots
            
            # Determine parameters and metrics to analyze
            if parameters is None:
                parameters = self._identify_sweep_parameters(sweep_data)
            
            if metrics is None:
                metrics = ['movement_timing', 'destination_entropy', 'cognitive_transitions']
            
            # Create different types of sensitivity plots
            plot_types = ['heatmaps', 'contour_plots', 'sensitivity_analysis', 'interaction_effects']
            
            for plot_type in plot_types:
                try:
                    if plot_type == 'heatmaps':
                        plot_files = self._create_parameter_heatmaps(sweep_data, parameters, metrics)
                    elif plot_type == 'contour_plots':
                        plot_files = self._create_parameter_contour_plots(sweep_data, parameters, metrics)
                    elif plot_type == 'sensitivity_analysis':
                        plot_files = self._create_sensitivity_analysis_plots(sweep_data, parameters, metrics)
                    elif plot_type == 'interaction_effects':
                        plot_files = self._create_interaction_effects_plots(sweep_data, parameters, metrics)
                    
                    if plot_files:
                        generated_plots.extend(plot_files)
                        
                except Exception as e:
                    self.logger.error(f"Failed to create {plot_type} plots: {e}")
                    continue
            
            self.logger.info(f"Generated {len(generated_plots)} parameter sensitivity plots")
            
        except Exception as e:
            self.logger.error(f"Failed to create parameter sensitivity plots: {e}")
        
        return generated_plots
    
    def _load_parameter_sweep_data(self, sweep_results_dir: str) -> Dict[str, Any]:
        """
        Load parameter sweep data from results directory.
        
        Args:
            sweep_results_dir: Directory containing sweep results
            
        Returns:
            Dictionary with sweep data
        """
        sweep_data = {
            'experiments': {},
            'parameters': {},
            'metrics': {},
            'parameter_combinations': []
        }
        
        sweep_path = Path(sweep_results_dir)
        
        if not sweep_path.exists():
            self.logger.warning(f"Sweep results directory does not exist: {sweep_path}")
            return sweep_data
        
        # Look for experiment directories
        for exp_dir in sweep_path.iterdir():
            if not exp_dir.is_dir():
                continue
            
            try:
                # Load experiment results
                results = self.analysis_pipeline.load_experiment_data(str(exp_dir))
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Extract parameter values from metadata
                metadata = results.metrics.get('metadata', {})
                parameters = metadata.get('parameters', {})
                
                if not parameters:
                    continue
                
                # Store experiment data
                sweep_data['experiments'][results.experiment_id] = {
                    'results': results,
                    'parameters': parameters
                }
                
                # Track parameter combinations
                sweep_data['parameter_combinations'].append({
                    'experiment_id': results.experiment_id,
                    'parameters': parameters
                })
                
                # Calculate key metrics for this experiment
                metrics = self._calculate_sweep_metrics(results)
                sweep_data['metrics'][results.experiment_id] = metrics
                
            except Exception as e:
                self.logger.error(f"Failed to load sweep experiment {exp_dir}: {e}")
                continue
        
        # Organize parameter data
        if sweep_data['parameter_combinations']:
            all_params = set()
            for combo in sweep_data['parameter_combinations']:
                all_params.update(combo['parameters'].keys())
            
            for param in all_params:
                param_values = []
                for combo in sweep_data['parameter_combinations']:
                    if param in combo['parameters']:
                        param_values.append(combo['parameters'][param])
                
                sweep_data['parameters'][param] = {
                    'values': param_values,
                    'unique_values': sorted(list(set(param_values)))
                }
        
        self.logger.debug(f"Loaded {len(sweep_data['experiments'])} sweep experiments")
        return sweep_data
    
    def _calculate_sweep_metrics(self, results: ExperimentResults) -> Dict[str, float]:
        """
        Calculate key metrics for parameter sweep analysis.
        
        Args:
            results: ExperimentResults object
            
        Returns:
            Dictionary with calculated metrics
        """
        metrics = {}
        
        try:
            # Movement timing metrics
            if results.movement_data is not None and not results.movement_data.empty:
                movement_data = results.movement_data
                
                if 'day' in movement_data.columns and 'refugees' in movement_data.columns:
                    # First movement day
                    refugee_data = movement_data[movement_data['refugees'] > 0]
                    if not refugee_data.empty:
                        metrics['first_movement_day'] = float(refugee_data['day'].min())
                    
                    # Peak movement day
                    daily_totals = movement_data.groupby('day')['refugees'].sum()
                    if not daily_totals.empty:
                        metrics['peak_movement_day'] = float(daily_totals.idxmax())
                        metrics['peak_movement_intensity'] = float(daily_totals.max())
                    
                    # Movement duration
                    if not refugee_data.empty:
                        metrics['movement_duration'] = float(refugee_data['day'].max() - refugee_data['day'].min() + 1)
                
                # Destination metrics
                if 'location' in movement_data.columns:
                    final_day = movement_data['day'].max()
                    final_data = movement_data[movement_data['day'] == final_day]
                    
                    if not final_data.empty and 'refugees' in final_data.columns:
                        dest_counts = final_data.groupby('location')['refugees'].sum()
                        total_refugees = dest_counts.sum()
                        
                        if total_refugees > 0:
                            dest_props = dest_counts / total_refugees
                            
                            # Entropy
                            entropy = -np.sum(dest_props * np.log2(dest_props + 1e-10))
                            max_entropy = np.log2(len(dest_props))
                            metrics['destination_entropy'] = float(entropy / max_entropy if max_entropy > 0 else 0)
                            
                            # Gini coefficient
                            sorted_props = np.sort(dest_props.values)
                            n = len(sorted_props)
                            index = np.arange(1, n + 1)
                            gini = (2 * np.sum(index * sorted_props)) / (n * np.sum(sorted_props)) - (n + 1) / n
                            metrics['destination_gini'] = float(gini)
                            
                            # Top destination concentration
                            metrics['top_destination_prop'] = float(dest_props.max())
            
            # Cognitive state metrics
            if results.cognitive_states is not None and not results.cognitive_states.empty:
                cognitive_data = results.cognitive_states
                
                if 'cognitive_state' in cognitive_data.columns:
                    # S1/S2 proportions
                    state_counts = cognitive_data['cognitive_state'].value_counts()
                    total_observations = state_counts.sum()
                    
                    if total_observations > 0:
                        metrics['s1_proportion'] = float(state_counts.get('S1', 0) / total_observations)
                        metrics['s2_proportion'] = float(state_counts.get('S2', 0) / total_observations)
                
                # Transition frequency
                if 'agent_id' in cognitive_data.columns:
                    transitions = 0
                    total_agents = cognitive_data['agent_id'].nunique()
                    
                    for agent_id in cognitive_data['agent_id'].unique():
                        agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                        if len(agent_data) > 1:
                            state_changes = (agent_data['cognitive_state'] != agent_data['cognitive_state'].shift()).sum() - 1
                            transitions += state_changes
                    
                    metrics['avg_transitions_per_agent'] = float(transitions / total_agents if total_agents > 0 else 0)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate sweep metrics: {e}")
        
        return metrics
    
    def _identify_sweep_parameters(self, sweep_data: Dict[str, Any]) -> List[str]:
        """
        Identify parameters that were varied in the sweep.
        
        Args:
            sweep_data: Dictionary with sweep data
            
        Returns:
            List of parameter names that were varied
        """
        varied_parameters = []
        
        for param, param_info in sweep_data['parameters'].items():
            unique_values = param_info['unique_values']
            if len(unique_values) > 1:  # Parameter was varied
                varied_parameters.append(param)
        
        return varied_parameters
    
    def _create_parameter_heatmaps(self, sweep_data: Dict[str, Any], 
                                 parameters: List[str], metrics: List[str]) -> List[str]:
        """
        Create heatmaps for multi-parameter relationships.
        
        Args:
            sweep_data: Dictionary with sweep data
            parameters: List of parameters to analyze
            metrics: List of metrics to analyze
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        # Create heatmaps for each pair of parameters and each metric
        for i, param1 in enumerate(parameters):
            for j, param2 in enumerate(parameters[i+1:], i+1):
                for metric in metrics:
                    try:
                        if self.backend == 'matplotlib':
                            plot_file = self._create_matplotlib_heatmap(sweep_data, param1, param2, metric)
                        else:
                            plot_file = self._create_plotly_heatmap(sweep_data, param1, param2, metric)
                        
                        if plot_file:
                            generated_plots.append(plot_file)
                            
                    except Exception as e:
                        self.logger.error(f"Failed to create heatmap for {param1} vs {param2} ({metric}): {e}")
                        continue
        
        return generated_plots
    
    def _create_matplotlib_heatmap(self, sweep_data: Dict[str, Any], 
                                 param1: str, param2: str, metric: str) -> Optional[str]:
        """
        Create parameter heatmap using matplotlib.
        
        Args:
            sweep_data: Dictionary with sweep data
            param1: First parameter name
            param2: Second parameter name
            metric: Metric to visualize
            
        Returns:
            Path to generated plot file
        """
        try:
            # Prepare data for heatmap
            data_points = []
            for exp_id, exp_data in sweep_data['experiments'].items():
                params = exp_data['parameters']
                metrics = sweep_data['metrics'][exp_id]
                
                if param1 in params and param2 in params and metric in metrics:
                    data_points.append({
                        'param1': params[param1],
                        'param2': params[param2],
                        'metric': metrics[metric]
                    })
            
            if not data_points:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data_points)
            
            # Create pivot table for heatmap
            pivot_table = df.pivot_table(values='metric', index='param2', columns='param1', aggfunc='mean')
            
            if pivot_table.empty:
                return None
            
            # Create heatmap
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            
            im = ax.imshow(pivot_table.values, cmap='viridis', aspect='auto', alpha=self.plot_config.alpha)
            
            # Set ticks and labels
            ax.set_xticks(range(len(pivot_table.columns)))
            ax.set_yticks(range(len(pivot_table.index)))
            ax.set_xticklabels([f'{val:.3f}' for val in pivot_table.columns])
            ax.set_yticklabels([f'{val:.3f}' for val in pivot_table.index])
            
            ax.set_xlabel(param1)
            ax.set_ylabel(param2)
            ax.set_title(f'{metric} Sensitivity: {param1} vs {param2}')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(metric)
            
            # Add text annotations
            for i in range(len(pivot_table.index)):
                for j in range(len(pivot_table.columns)):
                    if not np.isnan(pivot_table.iloc[i, j]):
                        text = ax.text(j, i, f'{pivot_table.iloc[i, j]:.3f}',
                                     ha="center", va="center", color="white", fontsize=8)
            
            plt.tight_layout()
            
            # Save plot
            safe_metric = metric.replace('_', '-')
            safe_param1 = param1.replace('_', '-')
            safe_param2 = param2.replace('_', '-')
            output_file = self.output_directory / f"heatmap_{safe_param1}_vs_{safe_param2}_{safe_metric}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created heatmap: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib heatmap: {e}")
            return None
    
    def _create_plotly_heatmap(self, sweep_data: Dict[str, Any], 
                             param1: str, param2: str, metric: str) -> Optional[str]:
        """
        Create parameter heatmap using plotly.
        
        Args:
            sweep_data: Dictionary with sweep data
            param1: First parameter name
            param2: Second parameter name
            metric: Metric to visualize
            
        Returns:
            Path to generated plot file
        """
        try:
            # Prepare data for heatmap
            data_points = []
            for exp_id, exp_data in sweep_data['experiments'].items():
                params = exp_data['parameters']
                metrics = sweep_data['metrics'][exp_id]
                
                if param1 in params and param2 in params and metric in metrics:
                    data_points.append({
                        'param1': params[param1],
                        'param2': params[param2],
                        'metric': metrics[metric]
                    })
            
            if not data_points:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data_points)
            
            # Create pivot table for heatmap
            pivot_table = df.pivot_table(values='metric', index='param2', columns='param1', aggfunc='mean')
            
            if pivot_table.empty:
                return None
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=pivot_table.values,
                x=[f'{val:.3f}' for val in pivot_table.columns],
                y=[f'{val:.3f}' for val in pivot_table.index],
                colorscale='Viridis',
                text=pivot_table.values,
                texttemplate="%{text:.3f}",
                textfont={"size": 10},
                hoverongaps=False
            ))
            
            fig.update_layout(
                title=f'{metric} Sensitivity: {param1} vs {param2}',
                xaxis_title=param1,
                yaxis_title=param2,
                width=800,
                height=600
            )
            
            # Save plot
            safe_metric = metric.replace('_', '-')
            safe_param1 = param1.replace('_', '-')
            safe_param2 = param2.replace('_', '-')
            output_file = self.output_directory / f"heatmap_{safe_param1}_vs_{safe_param2}_{safe_metric}.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created heatmap: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly heatmap: {e}")
            return None
    
    def _create_parameter_contour_plots(self, sweep_data: Dict[str, Any], 
                                      parameters: List[str], metrics: List[str]) -> List[str]:
        """
        Create contour plots for multi-parameter relationships.
        
        Args:
            sweep_data: Dictionary with sweep data
            parameters: List of parameters to analyze
            metrics: List of metrics to analyze
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        # Create contour plots for each pair of parameters and each metric
        for i, param1 in enumerate(parameters):
            for j, param2 in enumerate(parameters[i+1:], i+1):
                for metric in metrics:
                    try:
                        if self.backend == 'matplotlib':
                            plot_file = self._create_matplotlib_contour(sweep_data, param1, param2, metric)
                        else:
                            plot_file = self._create_plotly_contour(sweep_data, param1, param2, metric)
                        
                        if plot_file:
                            generated_plots.append(plot_file)
                            
                    except Exception as e:
                        self.logger.error(f"Failed to create contour plot for {param1} vs {param2} ({metric}): {e}")
                        continue
        
        return generated_plots
    
    def _create_matplotlib_contour(self, sweep_data: Dict[str, Any], 
                                 param1: str, param2: str, metric: str) -> Optional[str]:
        """
        Create parameter contour plot using matplotlib.
        
        Args:
            sweep_data: Dictionary with sweep data
            param1: First parameter name
            param2: Second parameter name
            metric: Metric to visualize
            
        Returns:
            Path to generated plot file
        """
        try:
            # Prepare data for contour plot
            data_points = []
            for exp_id, exp_data in sweep_data['experiments'].items():
                params = exp_data['parameters']
                metrics = sweep_data['metrics'][exp_id]
                
                if param1 in params and param2 in params and metric in metrics:
                    data_points.append({
                        'param1': params[param1],
                        'param2': params[param2],
                        'metric': metrics[metric]
                    })
            
            if len(data_points) < 4:  # Need minimum points for contour
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data_points)
            
            # Create grid for interpolation
            from scipy.interpolate import griddata
            
            param1_vals = df['param1'].values
            param2_vals = df['param2'].values
            metric_vals = df['metric'].values
            
            # Create regular grid
            param1_grid = np.linspace(param1_vals.min(), param1_vals.max(), 50)
            param2_grid = np.linspace(param2_vals.min(), param2_vals.max(), 50)
            param1_mesh, param2_mesh = np.meshgrid(param1_grid, param2_grid)
            
            # Interpolate metric values
            metric_mesh = griddata((param1_vals, param2_vals), metric_vals, 
                                 (param1_mesh, param2_mesh), method='cubic', fill_value=np.nan)
            
            # Create contour plot
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            
            # Create filled contour
            contour_filled = ax.contourf(param1_mesh, param2_mesh, metric_mesh, 
                                       levels=20, cmap='viridis', alpha=self.plot_config.alpha)
            
            # Add contour lines
            contour_lines = ax.contour(param1_mesh, param2_mesh, metric_mesh, 
                                     levels=10, colors='black', alpha=0.5, linewidths=0.5)
            
            # Add colorbar
            cbar = plt.colorbar(contour_filled, ax=ax)
            cbar.set_label(metric)
            
            # Add data points
            ax.scatter(param1_vals, param2_vals, c='red', s=20, alpha=0.8, zorder=5)
            
            ax.set_xlabel(param1)
            ax.set_ylabel(param2)
            ax.set_title(f'{metric} Contour: {param1} vs {param2}')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            safe_metric = metric.replace('_', '-')
            safe_param1 = param1.replace('_', '-')
            safe_param2 = param2.replace('_', '-')
            output_file = self.output_directory / f"contour_{safe_param1}_vs_{safe_param2}_{safe_metric}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created contour plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib contour plot: {e}")
            return None
    
    def _create_plotly_contour(self, sweep_data: Dict[str, Any], 
                             param1: str, param2: str, metric: str) -> Optional[str]:
        """
        Create parameter contour plot using plotly.
        
        Args:
            sweep_data: Dictionary with sweep data
            param1: First parameter name
            param2: Second parameter name
            metric: Metric to visualize
            
        Returns:
            Path to generated plot file
        """
        try:
            # Prepare data for contour plot
            data_points = []
            for exp_id, exp_data in sweep_data['experiments'].items():
                params = exp_data['parameters']
                metrics = sweep_data['metrics'][exp_id]
                
                if param1 in params and param2 in params and metric in metrics:
                    data_points.append({
                        'param1': params[param1],
                        'param2': params[param2],
                        'metric': metrics[metric]
                    })
            
            if len(data_points) < 4:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data_points)
            
            # Create contour plot
            fig = go.Figure()
            
            # Add contour
            fig.add_trace(go.Contour(
                x=df['param1'],
                y=df['param2'],
                z=df['metric'],
                colorscale='Viridis',
                contours=dict(
                    showlabels=True,
                    labelfont=dict(size=10, color='white')
                ),
                hoverongaps=False
            ))
            
            # Add scatter points
            fig.add_trace(go.Scatter(
                x=df['param1'],
                y=df['param2'],
                mode='markers',
                marker=dict(color='red', size=8),
                name='Data Points',
                hovertemplate=f'{param1}: %{{x}}<br>{param2}: %{{y}}<br>{metric}: %{{text}}<extra></extra>',
                text=df['metric']
            ))
            
            fig.update_layout(
                title=f'{metric} Contour: {param1} vs {param2}',
                xaxis_title=param1,
                yaxis_title=param2,
                width=800,
                height=600
            )
            
            # Save plot
            safe_metric = metric.replace('_', '-')
            safe_param1 = param1.replace('_', '-')
            safe_param2 = param2.replace('_', '-')
            output_file = self.output_directory / f"contour_{safe_param1}_vs_{safe_param2}_{safe_metric}.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created contour plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly contour plot: {e}")
            return None  
  
    def _create_sensitivity_analysis_plots(self, sweep_data: Dict[str, Any], 
                                          parameters: List[str], metrics: List[str]) -> List[str]:
        """
        Create sensitivity analysis plots with statistical significance indicators.
        
        Args:
            sweep_data: Dictionary with sweep data
            parameters: List of parameters to analyze
            metrics: List of metrics to analyze
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        try:
            if self.backend == 'matplotlib':
                plot_file = self._create_matplotlib_sensitivity_analysis(sweep_data, parameters, metrics)
            else:
                plot_file = self._create_plotly_sensitivity_analysis(sweep_data, parameters, metrics)
            
            if plot_file:
                generated_plots.append(plot_file)
                
        except Exception as e:
            self.logger.error(f"Failed to create sensitivity analysis plots: {e}")
        
        return generated_plots
    
    def _create_matplotlib_sensitivity_analysis(self, sweep_data: Dict[str, Any], 
                                              parameters: List[str], metrics: List[str]) -> Optional[str]:
        """
        Create sensitivity analysis plot using matplotlib.
        
        Args:
            sweep_data: Dictionary with sweep data
            parameters: List of parameters to analyze
            metrics: List of metrics to analyze
            
        Returns:
            Path to generated plot file
        """
        try:
            # Calculate sensitivity indices for each parameter-metric combination
            sensitivity_data = self._calculate_sensitivity_indices(sweep_data, parameters, metrics)
            
            if not sensitivity_data:
                return None
            
            # Create subplot grid
            n_metrics = len(metrics)
            n_cols = min(3, n_metrics)
            n_rows = (n_metrics + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
            if n_metrics == 1:
                axes = [axes]
            elif n_rows == 1:
                axes = [axes]
            else:
                axes = axes.flatten()
            
            fig.suptitle('Parameter Sensitivity Analysis', 
                        fontsize=self.plot_config.title_size, fontweight='bold')
            
            for i, metric in enumerate(metrics):
                ax = axes[i] if i < len(axes) else axes[-1]
                
                if metric in sensitivity_data:
                    param_names = list(sensitivity_data[metric].keys())
                    sensitivity_values = [sensitivity_data[metric][param]['sensitivity'] for param in param_names]
                    p_values = [sensitivity_data[metric][param]['p_value'] for param in param_names]
                    
                    # Create bar plot
                    bars = ax.bar(param_names, sensitivity_values, alpha=self.plot_config.alpha)
                    
                    # Color bars by significance
                    for bar, p_val in zip(bars, p_values):
                        if p_val < 0.001:
                            bar.set_color('darkred')  # Highly significant
                        elif p_val < 0.01:
                            bar.set_color('red')      # Significant
                        elif p_val < 0.05:
                            bar.set_color('orange')   # Marginally significant
                        else:
                            bar.set_color('lightgray')  # Not significant
                    
                    # Add significance indicators
                    for j, (bar, p_val) in enumerate(zip(bars, p_values)):
                        height = bar.get_height()
                        if p_val < 0.001:
                            sig_text = '***'
                        elif p_val < 0.01:
                            sig_text = '**'
                        elif p_val < 0.05:
                            sig_text = '*'
                        else:
                            sig_text = 'ns'
                        
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                               sig_text, ha='center', va='bottom', fontweight='bold')
                    
                    ax.set_xlabel('Parameters')
                    ax.set_ylabel('Sensitivity Index')
                    ax.set_title(f'{metric}')
                    ax.tick_params(axis='x', rotation=45)
                    ax.grid(True, alpha=0.3)
            
            # Hide unused subplots
            for i in range(n_metrics, len(axes)):
                axes[i].set_visible(False)
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='darkred', label='p < 0.001 (***)'),
                Patch(facecolor='red', label='p < 0.01 (**)'),
                Patch(facecolor='orange', label='p < 0.05 (*)'),
                Patch(facecolor='lightgray', label='p ≥ 0.05 (ns)')
            ]
            fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
            
            plt.tight_layout()
            
            # Save plot
            output_file = self.output_directory / f"sensitivity_analysis.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created sensitivity analysis plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib sensitivity analysis: {e}")
            return None
    
    def _create_plotly_sensitivity_analysis(self, sweep_data: Dict[str, Any], 
                                          parameters: List[str], metrics: List[str]) -> Optional[str]:
        """
        Create sensitivity analysis plot using plotly.
        
        Args:
            sweep_data: Dictionary with sweep data
            parameters: List of parameters to analyze
            metrics: List of metrics to analyze
            
        Returns:
            Path to generated plot file
        """
        try:
            # Calculate sensitivity indices
            sensitivity_data = self._calculate_sensitivity_indices(sweep_data, parameters, metrics)
            
            if not sensitivity_data:
                return None
            
            # Create subplots
            n_metrics = len(metrics)
            n_cols = min(3, n_metrics)
            n_rows = (n_metrics + n_cols - 1) // n_cols
            
            subplot_titles = [f'{metric} Sensitivity' for metric in metrics]
            
            fig = make_subplots(
                rows=n_rows, cols=n_cols,
                subplot_titles=subplot_titles
            )
            
            for i, metric in enumerate(metrics):
                row = i // n_cols + 1
                col = i % n_cols + 1
                
                if metric in sensitivity_data:
                    param_names = list(sensitivity_data[metric].keys())
                    sensitivity_values = [sensitivity_data[metric][param]['sensitivity'] for param in param_names]
                    p_values = [sensitivity_data[metric][param]['p_value'] for param in param_names]
                    
                    # Create colors based on significance
                    colors = []
                    for p_val in p_values:
                        if p_val < 0.001:
                            colors.append('darkred')
                        elif p_val < 0.01:
                            colors.append('red')
                        elif p_val < 0.05:
                            colors.append('orange')
                        else:
                            colors.append('lightgray')
                    
                    # Create significance text
                    sig_text = []
                    for p_val in p_values:
                        if p_val < 0.001:
                            sig_text.append('***')
                        elif p_val < 0.01:
                            sig_text.append('**')
                        elif p_val < 0.05:
                            sig_text.append('*')
                        else:
                            sig_text.append('ns')
                    
                    fig.add_trace(
                        go.Bar(x=param_names, y=sensitivity_values,
                              marker_color=colors,
                              text=sig_text,
                              textposition='outside',
                              name=metric,
                              hovertemplate='Parameter: %{x}<br>Sensitivity: %{y:.3f}<br>Significance: %{text}<extra></extra>'),
                        row=row, col=col
                    )
            
            fig.update_layout(
                title_text='Parameter Sensitivity Analysis',
                title_x=0.5,
                height=400 * n_rows,
                showlegend=False
            )
            
            # Update axes labels
            for i in range(n_metrics):
                row = i // n_cols + 1
                col = i % n_cols + 1
                fig.update_xaxes(title_text="Parameters", row=row, col=col)
                fig.update_yaxes(title_text="Sensitivity Index", row=row, col=col)
            
            # Save plot
            output_file = self.output_directory / f"sensitivity_analysis.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created sensitivity analysis plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly sensitivity analysis: {e}")
            return None
    
    def _calculate_sensitivity_indices(self, sweep_data: Dict[str, Any], 
                                     parameters: List[str], metrics: List[str]) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Calculate sensitivity indices for parameter-metric combinations.
        
        Args:
            sweep_data: Dictionary with sweep data
            parameters: List of parameters to analyze
            metrics: List of metrics to analyze
            
        Returns:
            Dictionary with sensitivity indices and p-values
        """
        sensitivity_data = {}
        
        try:
            from scipy.stats import pearsonr, spearmanr
            
            for metric in metrics:
                sensitivity_data[metric] = {}
                
                # Get metric values for all experiments
                metric_values = []
                param_values = {param: [] for param in parameters}
                
                for exp_id, exp_data in sweep_data['experiments'].items():
                    if exp_id in sweep_data['metrics'] and metric in sweep_data['metrics'][exp_id]:
                        metric_val = sweep_data['metrics'][exp_id][metric]
                        metric_values.append(metric_val)
                        
                        params = exp_data['parameters']
                        for param in parameters:
                            if param in params:
                                param_values[param].append(params[param])
                            else:
                                param_values[param].append(np.nan)
                
                if len(metric_values) < 3:  # Need minimum data points
                    continue
                
                # Calculate sensitivity for each parameter
                for param in parameters:
                    param_vals = param_values[param]
                    
                    # Remove NaN values
                    valid_indices = [i for i, (m, p) in enumerate(zip(metric_values, param_vals)) 
                                   if not (np.isnan(m) or np.isnan(p))]
                    
                    if len(valid_indices) < 3:
                        continue
                    
                    valid_metric = [metric_values[i] for i in valid_indices]
                    valid_param = [param_vals[i] for i in valid_indices]
                    
                    # Calculate correlation (sensitivity index)
                    try:
                        # Use Spearman correlation for robustness
                        correlation, p_value = spearmanr(valid_param, valid_metric)
                        
                        sensitivity_data[metric][param] = {
                            'sensitivity': abs(correlation) if not np.isnan(correlation) else 0.0,
                            'p_value': p_value if not np.isnan(p_value) else 1.0,
                            'correlation': correlation if not np.isnan(correlation) else 0.0
                        }
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to calculate sensitivity for {param}-{metric}: {e}")
                        sensitivity_data[metric][param] = {
                            'sensitivity': 0.0,
                            'p_value': 1.0,
                            'correlation': 0.0
                        }
        
        except Exception as e:
            self.logger.error(f"Failed to calculate sensitivity indices: {e}")
        
        return sensitivity_data
    
    def _create_interaction_effects_plots(self, sweep_data: Dict[str, Any], 
                                        parameters: List[str], metrics: List[str]) -> List[str]:
        """
        Create interaction effects plots for parameter combinations.
        
        Args:
            sweep_data: Dictionary with sweep data
            parameters: List of parameters to analyze
            metrics: List of metrics to analyze
            
        Returns:
            List of generated plot file paths
        """
        generated_plots = []
        
        # Create interaction plots for each pair of parameters
        for i, param1 in enumerate(parameters):
            for j, param2 in enumerate(parameters[i+1:], i+1):
                for metric in metrics:
                    try:
                        if self.backend == 'matplotlib':
                            plot_file = self._create_matplotlib_interaction_plot(sweep_data, param1, param2, metric)
                        else:
                            plot_file = self._create_plotly_interaction_plot(sweep_data, param1, param2, metric)
                        
                        if plot_file:
                            generated_plots.append(plot_file)
                            
                    except Exception as e:
                        self.logger.error(f"Failed to create interaction plot for {param1} x {param2} ({metric}): {e}")
                        continue
        
        return generated_plots
    
    def _create_matplotlib_interaction_plot(self, sweep_data: Dict[str, Any], 
                                          param1: str, param2: str, metric: str) -> Optional[str]:
        """
        Create parameter interaction plot using matplotlib.
        
        Args:
            sweep_data: Dictionary with sweep data
            param1: First parameter name
            param2: Second parameter name
            metric: Metric to visualize
            
        Returns:
            Path to generated plot file
        """
        try:
            # Prepare data for interaction plot
            data_points = []
            for exp_id, exp_data in sweep_data['experiments'].items():
                params = exp_data['parameters']
                metrics = sweep_data['metrics'][exp_id]
                
                if param1 in params and param2 in params and metric in metrics:
                    data_points.append({
                        'param1': params[param1],
                        'param2': params[param2],
                        'metric': metrics[metric]
                    })
            
            if len(data_points) < 4:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data_points)
            
            # Create interaction plot
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            
            # Group by param2 values and plot lines for each
            param2_values = sorted(df['param2'].unique())
            
            for param2_val in param2_values:
                subset = df[df['param2'] == param2_val]
                if len(subset) > 1:
                    # Sort by param1 for proper line plotting
                    subset = subset.sort_values('param1')
                    
                    ax.plot(subset['param1'], subset['metric'], 
                           marker='o', linewidth=self.plot_config.line_width, 
                           markersize=self.plot_config.marker_size,
                           alpha=self.plot_config.alpha,
                           label=f'{param2} = {param2_val:.3f}')
            
            ax.set_xlabel(param1)
            ax.set_ylabel(metric)
            ax.set_title(f'Interaction Effect: {param1} × {param2} on {metric}')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            safe_metric = metric.replace('_', '-')
            safe_param1 = param1.replace('_', '-')
            safe_param2 = param2.replace('_', '-')
            output_file = self.output_directory / f"interaction_{safe_param1}_x_{safe_param2}_{safe_metric}.{self.plot_config.save_format}"
            plt.savefig(output_file, dpi=self.plot_config.save_dpi, bbox_inches='tight')
            plt.close()
            
            self.logger.debug(f"Created interaction plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create matplotlib interaction plot: {e}")
            return None
    
    def _create_plotly_interaction_plot(self, sweep_data: Dict[str, Any], 
                                      param1: str, param2: str, metric: str) -> Optional[str]:
        """
        Create parameter interaction plot using plotly.
        
        Args:
            sweep_data: Dictionary with sweep data
            param1: First parameter name
            param2: Second parameter name
            metric: Metric to visualize
            
        Returns:
            Path to generated plot file
        """
        try:
            # Prepare data for interaction plot
            data_points = []
            for exp_id, exp_data in sweep_data['experiments'].items():
                params = exp_data['parameters']
                metrics = sweep_data['metrics'][exp_id]
                
                if param1 in params and param2 in params and metric in metrics:
                    data_points.append({
                        'param1': params[param1],
                        'param2': params[param2],
                        'metric': metrics[metric]
                    })
            
            if len(data_points) < 4:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data_points)
            
            # Create interaction plot
            fig = go.Figure()
            
            # Group by param2 values and plot lines for each
            param2_values = sorted(df['param2'].unique())
            
            for param2_val in param2_values:
                subset = df[df['param2'] == param2_val]
                if len(subset) > 1:
                    # Sort by param1 for proper line plotting
                    subset = subset.sort_values('param1')
                    
                    fig.add_trace(go.Scatter(
                        x=subset['param1'],
                        y=subset['metric'],
                        mode='lines+markers',
                        name=f'{param2} = {param2_val:.3f}',
                        line=dict(width=3),
                        marker=dict(size=8)
                    ))
            
            fig.update_layout(
                title=f'Interaction Effect: {param1} × {param2} on {metric}',
                xaxis_title=param1,
                yaxis_title=metric,
                width=800,
                height=600
            )
            
            # Save plot
            safe_metric = metric.replace('_', '-')
            safe_param1 = param1.replace('_', '-')
            safe_param2 = param2.replace('_', '-')
            output_file = self.output_directory / f"interaction_{safe_param1}_x_{safe_param2}_{safe_metric}.html"
            fig.write_html(str(output_file))
            
            self.logger.debug(f"Created interaction plot: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create plotly interaction plot: {e}")
            return None    

    def generate_experiment_report(self, experiment_dirs: List[str], 
                                 report_title: str = "Dual Process Experiment Report",
                                 output_format: str = "html") -> Optional[str]:
        """
        Generate automated experiment report with standardized templates.
        
        Args:
            experiment_dirs: List of experiment directory paths
            report_title: Title for the report
            output_format: Output format ('html' or 'latex')
            
        Returns:
            Path to generated report file
        """
        self.logger.info(f"Generating experiment report for {len(experiment_dirs)} experiments")
        
        try:
            # Load and analyze all experiment data
            report_data = self._prepare_report_data(experiment_dirs)
            
            if not report_data:
                self.logger.warning("No data available for report generation")
                return None
            
            # Generate visualizations for the report
            self._generate_report_visualizations(report_data)
            
            # Create report based on format
            if output_format.lower() == 'latex':
                report_file = self._generate_latex_report(report_data, report_title)
            else:
                report_file = self._generate_html_report(report_data, report_title)
            
            if report_file:
                self.logger.info(f"Generated experiment report: {report_file}")
            
            return report_file
            
        except Exception as e:
            self.logger.error(f"Failed to generate experiment report: {e}")
            return None
    
    def _prepare_report_data(self, experiment_dirs: List[str]) -> Dict[str, Any]:
        """
        Prepare data for report generation.
        
        Args:
            experiment_dirs: List of experiment directory paths
            
        Returns:
            Dictionary with organized report data
        """
        report_data = {
            'experiments': {},
            'summary_statistics': {},
            'comparative_analysis': {},
            'visualizations': [],
            'metadata': {
                'generation_time': datetime.now().isoformat(),
                'total_experiments': len(experiment_dirs),
                'cognitive_modes': set(),
                'topologies': set(),
                'scenarios': set()
            }
        }
        
        # Load all experiment data
        for experiment_dir in experiment_dirs:
            try:
                results = self.analysis_pipeline.load_experiment_data(experiment_dir)
                
                if results.movement_data is None or results.movement_data.empty:
                    continue
                
                # Store experiment results
                report_data['experiments'][results.experiment_id] = results
                
                # Extract metadata
                metadata = results.metrics.get('metadata', {})
                if 'cognitive_mode' in metadata:
                    report_data['metadata']['cognitive_modes'].add(metadata['cognitive_mode'])
                if 'topology_type' in metadata:
                    report_data['metadata']['topologies'].add(metadata['topology_type'])
                if 'scenario_type' in metadata:
                    report_data['metadata']['scenarios'].add(metadata['scenario_type'])
                
            except Exception as e:
                self.logger.error(f"Failed to load experiment data for report: {e}")
                continue
        
        # Calculate summary statistics
        report_data['summary_statistics'] = self._calculate_report_summary_statistics(report_data['experiments'])
        
        # Perform comparative analysis
        report_data['comparative_analysis'] = self._perform_comparative_analysis(report_data['experiments'])
        
        return report_data
    
    def _calculate_report_summary_statistics(self, experiments: Dict[str, ExperimentResults]) -> Dict[str, Any]:
        """
        Calculate summary statistics for the report.
        
        Args:
            experiments: Dictionary of experiment results
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'movement_metrics': {},
            'cognitive_metrics': {},
            'destination_metrics': {}
        }
        
        try:
            # Aggregate movement metrics
            first_movement_days = []
            peak_movement_days = []
            movement_durations = []
            
            # Aggregate cognitive metrics
            s1_proportions = []
            s2_proportions = []
            transition_rates = []
            
            # Aggregate destination metrics
            destination_entropies = []
            destination_ginis = []
            
            for exp_id, results in experiments.items():
                # Movement metrics
                if results.movement_data is not None and not results.movement_data.empty:
                    movement_data = results.movement_data
                    
                    if 'day' in movement_data.columns and 'refugees' in movement_data.columns:
                        refugee_data = movement_data[movement_data['refugees'] > 0]
                        if not refugee_data.empty:
                            first_movement_days.append(refugee_data['day'].min())
                            movement_durations.append(refugee_data['day'].max() - refugee_data['day'].min() + 1)
                        
                        daily_totals = movement_data.groupby('day')['refugees'].sum()
                        if not daily_totals.empty:
                            peak_movement_days.append(daily_totals.idxmax())
                    
                    # Destination metrics
                    if 'location' in movement_data.columns:
                        final_day = movement_data['day'].max()
                        final_data = movement_data[movement_data['day'] == final_day]
                        
                        if not final_data.empty and 'refugees' in final_data.columns:
                            dest_counts = final_data.groupby('location')['refugees'].sum()
                            total_refugees = dest_counts.sum()
                            
                            if total_refugees > 0:
                                dest_props = dest_counts / total_refugees
                                
                                # Entropy
                                entropy = -np.sum(dest_props * np.log2(dest_props + 1e-10))
                                max_entropy = np.log2(len(dest_props))
                                normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
                                destination_entropies.append(normalized_entropy)
                                
                                # Gini coefficient
                                sorted_props = np.sort(dest_props.values)
                                n = len(sorted_props)
                                index = np.arange(1, n + 1)
                                gini = (2 * np.sum(index * sorted_props)) / (n * np.sum(sorted_props)) - (n + 1) / n
                                destination_ginis.append(gini)
                
                # Cognitive metrics
                if results.cognitive_states is not None and not results.cognitive_states.empty:
                    cognitive_data = results.cognitive_states
                    
                    if 'cognitive_state' in cognitive_data.columns:
                        state_counts = cognitive_data['cognitive_state'].value_counts()
                        total_observations = state_counts.sum()
                        
                        if total_observations > 0:
                            s1_proportions.append(state_counts.get('S1', 0) / total_observations)
                            s2_proportions.append(state_counts.get('S2', 0) / total_observations)
                    
                    # Calculate transition rate
                    if 'agent_id' in cognitive_data.columns:
                        transitions = 0
                        total_agents = cognitive_data['agent_id'].nunique()
                        
                        for agent_id in cognitive_data['agent_id'].unique():
                            agent_data = cognitive_data[cognitive_data['agent_id'] == agent_id].sort_values('day')
                            if len(agent_data) > 1:
                                state_changes = (agent_data['cognitive_state'] != agent_data['cognitive_state'].shift()).sum() - 1
                                transitions += state_changes
                        
                        if total_agents > 0:
                            transition_rates.append(transitions / total_agents)
            
            # Calculate summary statistics
            if first_movement_days:
                summary['movement_metrics']['first_movement_day'] = {
                    'mean': float(np.mean(first_movement_days)),
                    'std': float(np.std(first_movement_days)),
                    'min': float(np.min(first_movement_days)),
                    'max': float(np.max(first_movement_days))
                }
            
            if peak_movement_days:
                summary['movement_metrics']['peak_movement_day'] = {
                    'mean': float(np.mean(peak_movement_days)),
                    'std': float(np.std(peak_movement_days)),
                    'min': float(np.min(peak_movement_days)),
                    'max': float(np.max(peak_movement_days))
                }
            
            if movement_durations:
                summary['movement_metrics']['movement_duration'] = {
                    'mean': float(np.mean(movement_durations)),
                    'std': float(np.std(movement_durations)),
                    'min': float(np.min(movement_durations)),
                    'max': float(np.max(movement_durations))
                }
            
            if s1_proportions:
                summary['cognitive_metrics']['s1_proportion'] = {
                    'mean': float(np.mean(s1_proportions)),
                    'std': float(np.std(s1_proportions)),
                    'min': float(np.min(s1_proportions)),
                    'max': float(np.max(s1_proportions))
                }
            
            if s2_proportions:
                summary['cognitive_metrics']['s2_proportion'] = {
                    'mean': float(np.mean(s2_proportions)),
                    'std': float(np.std(s2_proportions)),
                    'min': float(np.min(s2_proportions)),
                    'max': float(np.max(s2_proportions))
                }
            
            if transition_rates:
                summary['cognitive_metrics']['transition_rate'] = {
                    'mean': float(np.mean(transition_rates)),
                    'std': float(np.std(transition_rates)),
                    'min': float(np.min(transition_rates)),
                    'max': float(np.max(transition_rates))
                }
            
            if destination_entropies:
                summary['destination_metrics']['entropy'] = {
                    'mean': float(np.mean(destination_entropies)),
                    'std': float(np.std(destination_entropies)),
                    'min': float(np.min(destination_entropies)),
                    'max': float(np.max(destination_entropies))
                }
            
            if destination_ginis:
                summary['destination_metrics']['gini'] = {
                    'mean': float(np.mean(destination_ginis)),
                    'std': float(np.std(destination_ginis)),
                    'min': float(np.min(destination_ginis)),
                    'max': float(np.max(destination_ginis))
                }
        
        except Exception as e:
            self.logger.error(f"Failed to calculate report summary statistics: {e}")
        
        return summary
    
    def _perform_comparative_analysis(self, experiments: Dict[str, ExperimentResults]) -> Dict[str, Any]:
        """
        Perform comparative analysis between different experimental conditions.
        
        Args:
            experiments: Dictionary of experiment results
            
        Returns:
            Dictionary with comparative analysis results
        """
        comparative_analysis = {
            'cognitive_mode_comparison': {},
            'topology_comparison': {},
            'scenario_comparison': {},
            'statistical_tests': {}
        }
        
        try:
            from scipy.stats import mannwhitneyu, kruskal
            
            # Group experiments by conditions
            cognitive_mode_groups = {}
            topology_groups = {}
            scenario_groups = {}
            
            for exp_id, results in experiments.items():
                metadata = results.metrics.get('metadata', {})
                
                # Group by cognitive mode
                cognitive_mode = metadata.get('cognitive_mode', 'unknown')
                if cognitive_mode not in cognitive_mode_groups:
                    cognitive_mode_groups[cognitive_mode] = []
                cognitive_mode_groups[cognitive_mode].append(results)
                
                # Group by topology
                topology = metadata.get('topology_type', 'unknown')
                if topology not in topology_groups:
                    topology_groups[topology] = []
                topology_groups[topology].append(results)
                
                # Group by scenario
                scenario = metadata.get('scenario_type', 'unknown')
                if scenario not in scenario_groups:
                    scenario_groups[scenario] = []
                scenario_groups[scenario].append(results)
            
            # Perform statistical comparisons
            comparative_analysis['cognitive_mode_comparison'] = self._compare_groups(
                cognitive_mode_groups, 'cognitive_mode'
            )
            comparative_analysis['topology_comparison'] = self._compare_groups(
                topology_groups, 'topology'
            )
            comparative_analysis['scenario_comparison'] = self._compare_groups(
                scenario_groups, 'scenario'
            )
        
        except Exception as e:
            self.logger.error(f"Failed to perform comparative analysis: {e}")
        
        return comparative_analysis
    
    def _compare_groups(self, groups: Dict[str, List[ExperimentResults]], 
                       comparison_type: str) -> Dict[str, Any]:
        """
        Compare groups of experiments statistically.
        
        Args:
            groups: Dictionary mapping group names to experiment results
            comparison_type: Type of comparison being performed
            
        Returns:
            Dictionary with comparison results
        """
        comparison_results = {
            'group_statistics': {},
            'statistical_tests': {},
            'effect_sizes': {}
        }
        
        try:
            from scipy.stats import mannwhitneyu, kruskal
            
            # Calculate group statistics
            for group_name, group_experiments in groups.items():
                if len(group_experiments) < 2:
                    continue
                
                # Extract key metrics for comparison
                first_movement_days = []
                destination_entropies = []
                s1_proportions = []
                
                for results in group_experiments:
                    # Movement timing
                    if results.movement_data is not None and not results.movement_data.empty:
                        movement_data = results.movement_data
                        if 'day' in movement_data.columns and 'refugees' in movement_data.columns:
                            refugee_data = movement_data[movement_data['refugees'] > 0]
                            if not refugee_data.empty:
                                first_movement_days.append(refugee_data['day'].min())
                        
                        # Destination entropy
                        if 'location' in movement_data.columns:
                            final_day = movement_data['day'].max()
                            final_data = movement_data[movement_data['day'] == final_day]
                            
                            if not final_data.empty and 'refugees' in final_data.columns:
                                dest_counts = final_data.groupby('location')['refugees'].sum()
                                total_refugees = dest_counts.sum()
                                
                                if total_refugees > 0:
                                    dest_props = dest_counts / total_refugees
                                    entropy = -np.sum(dest_props * np.log2(dest_props + 1e-10))
                                    max_entropy = np.log2(len(dest_props))
                                    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
                                    destination_entropies.append(normalized_entropy)
                    
                    # Cognitive state proportions
                    if results.cognitive_states is not None and not results.cognitive_states.empty:
                        cognitive_data = results.cognitive_states
                        if 'cognitive_state' in cognitive_data.columns:
                            state_counts = cognitive_data['cognitive_state'].value_counts()
                            total_observations = state_counts.sum()
                            if total_observations > 0:
                                s1_proportions.append(state_counts.get('S1', 0) / total_observations)
                
                # Store group statistics
                comparison_results['group_statistics'][group_name] = {
                    'n_experiments': len(group_experiments),
                    'first_movement_day': {
                        'mean': float(np.mean(first_movement_days)) if first_movement_days else None,
                        'std': float(np.std(first_movement_days)) if first_movement_days else None
                    },
                    'destination_entropy': {
                        'mean': float(np.mean(destination_entropies)) if destination_entropies else None,
                        'std': float(np.std(destination_entropies)) if destination_entropies else None
                    },
                    's1_proportion': {
                        'mean': float(np.mean(s1_proportions)) if s1_proportions else None,
                        'std': float(np.std(s1_proportions)) if s1_proportions else None
                    }
                }
            
            # Perform pairwise statistical tests
            group_names = list(groups.keys())
            if len(group_names) >= 2:
                for i, group1 in enumerate(group_names):
                    for j, group2 in enumerate(group_names[i+1:], i+1):
                        comparison_key = f"{group1}_vs_{group2}"
                        
                        # Extract data for both groups
                        group1_data = self._extract_group_metrics(groups[group1])
                        group2_data = self._extract_group_metrics(groups[group2])
                        
                        # Perform statistical tests
                        test_results = {}
                        
                        for metric in ['first_movement_day', 'destination_entropy', 's1_proportion']:
                            if metric in group1_data and metric in group2_data:
                                data1 = group1_data[metric]
                                data2 = group2_data[metric]
                                
                                if len(data1) >= 3 and len(data2) >= 3:
                                    try:
                                        statistic, p_value = mannwhitneyu(data1, data2, alternative='two-sided')
                                        test_results[metric] = {
                                            'statistic': float(statistic),
                                            'p_value': float(p_value),
                                            'significant': p_value < 0.05
                                        }
                                    except Exception as e:
                                        self.logger.warning(f"Failed to perform test for {metric}: {e}")
                        
                        comparison_results['statistical_tests'][comparison_key] = test_results
        
        except Exception as e:
            self.logger.error(f"Failed to compare groups: {e}")
        
        return comparison_results
    
    def _extract_group_metrics(self, group_experiments: List[ExperimentResults]) -> Dict[str, List[float]]:
        """
        Extract metrics from a group of experiments.
        
        Args:
            group_experiments: List of experiment results
            
        Returns:
            Dictionary with extracted metrics
        """
        metrics = {
            'first_movement_day': [],
            'destination_entropy': [],
            's1_proportion': []
        }
        
        for results in group_experiments:
            # Movement timing
            if results.movement_data is not None and not results.movement_data.empty:
                movement_data = results.movement_data
                if 'day' in movement_data.columns and 'refugees' in movement_data.columns:
                    refugee_data = movement_data[movement_data['refugees'] > 0]
                    if not refugee_data.empty:
                        metrics['first_movement_day'].append(refugee_data['day'].min())
                
                # Destination entropy
                if 'location' in movement_data.columns:
                    final_day = movement_data['day'].max()
                    final_data = movement_data[movement_data['day'] == final_day]
                    
                    if not final_data.empty and 'refugees' in final_data.columns:
                        dest_counts = final_data.groupby('location')['refugees'].sum()
                        total_refugees = dest_counts.sum()
                        
                        if total_refugees > 0:
                            dest_props = dest_counts / total_refugees
                            entropy = -np.sum(dest_props * np.log2(dest_props + 1e-10))
                            max_entropy = np.log2(len(dest_props))
                            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
                            metrics['destination_entropy'].append(normalized_entropy)
            
            # Cognitive state proportions
            if results.cognitive_states is not None and not results.cognitive_states.empty:
                cognitive_data = results.cognitive_states
                if 'cognitive_state' in cognitive_data.columns:
                    state_counts = cognitive_data['cognitive_state'].value_counts()
                    total_observations = state_counts.sum()
                    if total_observations > 0:
                        metrics['s1_proportion'].append(state_counts.get('S1', 0) / total_observations)
        
        return metrics
    
    def _generate_report_visualizations(self, report_data: Dict[str, Any]) -> None:
        """
        Generate visualizations for the report.
        
        Args:
            report_data: Dictionary with report data
        """
        try:
            experiment_dirs = [str(self.results_directory / exp_id) for exp_id in report_data['experiments'].keys()]
            
            # Generate key visualizations
            self.logger.info("Generating report visualizations...")
            
            # Cognitive state plots
            cognitive_plots = self.create_cognitive_state_plots(experiment_dirs, ['evolution', 'distribution'])
            report_data['visualizations'].extend(cognitive_plots)
            
            # Movement comparison charts
            movement_plots = self.create_movement_comparison_charts(experiment_dirs)
            report_data['visualizations'].extend(movement_plots)
            
            self.logger.info(f"Generated {len(report_data['visualizations'])} visualizations for report")
            
        except Exception as e:
            self.logger.error(f"Failed to generate report visualizations: {e}")
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_title: str) -> Optional[str]:
        """
        Generate HTML report.
        
        Args:
            report_data: Dictionary with report data
            report_title: Title for the report
            
        Returns:
            Path to generated HTML report
        """
        try:
            html_content = self._create_html_template(report_data, report_title)
            
            # Save HTML report
            output_file = self.output_directory / "experiment_report.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.debug(f"Generated HTML report: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            return None
    
    def _create_html_template(self, report_data: Dict[str, Any], report_title: str) -> str:
        """
        Create HTML template for the report.
        
        Args:
            report_data: Dictionary with report data
            report_title: Title for the report
            
        Returns:
            HTML content string
        """
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
        }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .statistics-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .statistics-table th, .statistics-table td {{
            border: 1px solid #bdc3c7;
            padding: 12px;
            text-align: left;
        }}
        .statistics-table th {{
            background-color: #3498db;
            color: white;
        }}
        .statistics-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .visualization {{
            text-align: center;
            margin: 30px 0;
        }}
        .visualization img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .significant {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .not-significant {{
            color: #95a5a6;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report_title}</h1>
        
        <div class="metadata">
            <h3>Report Metadata</h3>
            <p><strong>Generated:</strong> {report_data['metadata']['generation_time']}</p>
            <p><strong>Total Experiments:</strong> {report_data['metadata']['total_experiments']}</p>
            <p><strong>Cognitive Modes:</strong> {', '.join(sorted(report_data['metadata']['cognitive_modes']))}</p>
            <p><strong>Topologies:</strong> {', '.join(sorted(report_data['metadata']['topologies']))}</p>
            <p><strong>Scenarios:</strong> {', '.join(sorted(report_data['metadata']['scenarios']))}</p>
        </div>
        
        <h2>Summary Statistics</h2>
        {self._create_summary_statistics_html(report_data['summary_statistics'])}
        
        <h2>Comparative Analysis</h2>
        {self._create_comparative_analysis_html(report_data['comparative_analysis'])}
        
        <h2>Visualizations</h2>
        {self._create_visualizations_html(report_data['visualizations'])}
        
        <div class="footer">
            <p>Report generated by Flee Dual Process Experiments Framework</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _create_summary_statistics_html(self, summary_stats: Dict[str, Any]) -> str:
        """
        Create HTML for summary statistics section.
        
        Args:
            summary_stats: Dictionary with summary statistics
            
        Returns:
            HTML content string
        """
        html = ""
        
        for category, metrics in summary_stats.items():
            if not metrics:
                continue
            
            html += f"<h3>{category.replace('_', ' ').title()}</h3>"
            html += '<table class="statistics-table">'
            html += '<tr><th>Metric</th><th>Mean</th><th>Std Dev</th><th>Min</th><th>Max</th></tr>'
            
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and 'mean' in metric_data:
                    html += f"""
                    <tr>
                        <td>{metric_name.replace('_', ' ').title()}</td>
                        <td>{metric_data['mean']:.3f}</td>
                        <td>{metric_data['std']:.3f}</td>
                        <td>{metric_data['min']:.3f}</td>
                        <td>{metric_data['max']:.3f}</td>
                    </tr>
                    """
            
            html += '</table>'
        
        return html
    
    def _create_comparative_analysis_html(self, comparative_analysis: Dict[str, Any]) -> str:
        """
        Create HTML for comparative analysis section.
        
        Args:
            comparative_analysis: Dictionary with comparative analysis results
            
        Returns:
            HTML content string
        """
        html = ""
        
        for comparison_type, comparison_data in comparative_analysis.items():
            if not comparison_data or comparison_type == 'statistical_tests':
                continue
            
            html += f"<h3>{comparison_type.replace('_', ' ').title()}</h3>"
            
            # Group statistics
            if 'group_statistics' in comparison_data:
                html += '<table class="statistics-table">'
                html += '<tr><th>Group</th><th>N</th><th>First Movement Day</th><th>Destination Entropy</th><th>S1 Proportion</th></tr>'
                
                for group_name, group_stats in comparison_data['group_statistics'].items():
                    first_movement = group_stats.get('first_movement_day', {})
                    dest_entropy = group_stats.get('destination_entropy', {})
                    s1_prop = group_stats.get('s1_proportion', {})
                    
                    html += f"""
                    <tr>
                        <td>{group_name}</td>
                        <td>{group_stats.get('n_experiments', 0)}</td>
                        <td>{first_movement.get('mean', 'N/A'):.3f} ± {first_movement.get('std', 0):.3f}</td>
                        <td>{dest_entropy.get('mean', 'N/A'):.3f} ± {dest_entropy.get('std', 0):.3f}</td>
                        <td>{s1_prop.get('mean', 'N/A'):.3f} ± {s1_prop.get('std', 0):.3f}</td>
                    </tr>
                    """
                
                html += '</table>'
            
            # Statistical tests
            if 'statistical_tests' in comparison_data:
                html += '<h4>Statistical Tests</h4>'
                html += '<table class="statistics-table">'
                html += '<tr><th>Comparison</th><th>Metric</th><th>p-value</th><th>Significant</th></tr>'
                
                for comparison_key, test_results in comparison_data['statistical_tests'].items():
                    for metric, test_data in test_results.items():
                        p_value = test_data.get('p_value', 1.0)
                        significant = test_data.get('significant', False)
                        
                        significance_class = 'significant' if significant else 'not-significant'
                        significance_text = 'Yes' if significant else 'No'
                        
                        html += f"""
                        <tr>
                            <td>{comparison_key.replace('_', ' ')}</td>
                            <td>{metric.replace('_', ' ').title()}</td>
                            <td class="{significance_class}">{p_value:.4f}</td>
                            <td class="{significance_class}">{significance_text}</td>
                        </tr>
                        """
                
                html += '</table>'
        
        return html
    
    def _create_visualizations_html(self, visualizations: List[str]) -> str:
        """
        Create HTML for visualizations section.
        
        Args:
            visualizations: List of visualization file paths
            
        Returns:
            HTML content string
        """
        html = ""
        
        for viz_path in visualizations:
            viz_file = Path(viz_path)
            
            if viz_file.exists():
                # Get relative path for HTML
                relative_path = viz_file.relative_to(self.output_directory)
                
                if viz_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg']:
                    html += f"""
                    <div class="visualization">
                        <h4>{viz_file.stem.replace('_', ' ').title()}</h4>
                        <img src="{relative_path}" alt="{viz_file.stem}">
                    </div>
                    """
                elif viz_file.suffix.lower() == '.html':
                    html += f"""
                    <div class="visualization">
                        <h4>{viz_file.stem.replace('_', ' ').title()}</h4>
                        <p><a href="{relative_path}" target="_blank">View Interactive Plot</a></p>
                    </div>
                    """
        
        return html
    
    def _generate_latex_report(self, report_data: Dict[str, Any], report_title: str) -> Optional[str]:
        """
        Generate LaTeX report.
        
        Args:
            report_data: Dictionary with report data
            report_title: Title for the report
            
        Returns:
            Path to generated LaTeX report
        """
        try:
            latex_content = self._create_latex_template(report_data, report_title)
            
            # Save LaTeX report
            output_file = self.output_directory / "experiment_report.tex"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            self.logger.debug(f"Generated LaTeX report: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to generate LaTeX report: {e}")
            return None
    
    def _create_latex_template(self, report_data: Dict[str, Any], report_title: str) -> str:
        """
        Create LaTeX template for the report.
        
        Args:
            report_data: Dictionary with report data
            report_title: Title for the report
            
        Returns:
            LaTeX content string
        """
        latex_template = f"""
\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{longtable}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{amssymb}}
\\usepackage{{hyperref}}
\\usepackage{{xcolor}}

\\geometry{{margin=1in}}

\\title{{{report_title}}}
\\author{{Flee Dual Process Experiments Framework}}
\\date{{{report_data['metadata']['generation_time'][:10]}}}

\\begin{{document}}

\\maketitle

\\section{{Executive Summary}}

This report presents the results of {report_data['metadata']['total_experiments']} dual-process experiments 
analyzing refugee movement patterns under different cognitive modes. The experiments covered 
{len(report_data['metadata']['cognitive_modes'])} cognitive modes, 
{len(report_data['metadata']['topologies'])} network topologies, and 
{len(report_data['metadata']['scenarios'])} conflict scenarios.

\\section{{Experimental Setup}}

\\subsection{{Cognitive Modes}}
The following cognitive modes were tested:
\\begin{{itemize}}
{self._create_latex_list(sorted(report_data['metadata']['cognitive_modes']))}
\\end{{itemize}}

\\subsection{{Network Topologies}}
The following network topologies were used:
\\begin{{itemize}}
{self._create_latex_list(sorted(report_data['metadata']['topologies']))}
\\end{{itemize}}

\\subsection{{Conflict Scenarios}}
The following conflict scenarios were simulated:
\\begin{{itemize}}
{self._create_latex_list(sorted(report_data['metadata']['scenarios']))}
\\end{{itemize}}

\\section{{Results}}

\\subsection{{Summary Statistics}}
{self._create_latex_summary_statistics(report_data['summary_statistics'])}

\\subsection{{Comparative Analysis}}
{self._create_latex_comparative_analysis(report_data['comparative_analysis'])}

\\section{{Visualizations}}
{self._create_latex_visualizations(report_data['visualizations'])}

\\section{{Conclusions}}

The experimental results demonstrate significant differences in refugee movement patterns 
across different cognitive modes, with implications for understanding decision-making 
processes in crisis situations.

\\end{{document}}
        """
        
        return latex_template
    
    def _create_latex_list(self, items: List[str]) -> str:
        """Create LaTeX itemize list from items."""
        return '\n'.join([f"\\item {item}" for item in items])
    
    def _create_latex_summary_statistics(self, summary_stats: Dict[str, Any]) -> str:
        """Create LaTeX tables for summary statistics."""
        latex = ""
        
        for category, metrics in summary_stats.items():
            if not metrics:
                continue
            
            latex += f"\\subsubsection{{{category.replace('_', ' ').title()}}}\n"
            latex += "\\begin{longtable}{lrrrr}\n"
            latex += "\\toprule\n"
            latex += "Metric & Mean & Std Dev & Min & Max \\\\\n"
            latex += "\\midrule\n"
            
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and 'mean' in metric_data:
                    latex += f"{metric_name.replace('_', ' ').title()} & "
                    latex += f"{metric_data['mean']:.3f} & "
                    latex += f"{metric_data['std']:.3f} & "
                    latex += f"{metric_data['min']:.3f} & "
                    latex += f"{metric_data['max']:.3f} \\\\\n"
            
            latex += "\\bottomrule\n"
            latex += "\\end{longtable}\n\n"
        
        return latex
    
    def _create_latex_comparative_analysis(self, comparative_analysis: Dict[str, Any]) -> str:
        """Create LaTeX content for comparative analysis."""
        latex = ""
        
        for comparison_type, comparison_data in comparative_analysis.items():
            if not comparison_data or comparison_type == 'statistical_tests':
                continue
            
            latex += f"\\subsubsection{{{comparison_type.replace('_', ' ').title()}}}\n"
            
            # Statistical tests table
            if 'statistical_tests' in comparison_data:
                latex += "\\begin{longtable}{llrl}\n"
                latex += "\\toprule\n"
                latex += "Comparison & Metric & p-value & Significant \\\\\n"
                latex += "\\midrule\n"
                
                for comparison_key, test_results in comparison_data['statistical_tests'].items():
                    for metric, test_data in test_results.items():
                        p_value = test_data.get('p_value', 1.0)
                        significant = 'Yes' if test_data.get('significant', False) else 'No'
                        
                        latex += f"{comparison_key.replace('_', ' ')} & "
                        latex += f"{metric.replace('_', ' ').title()} & "
                        latex += f"{p_value:.4f} & "
                        latex += f"{significant} \\\\\n"
                
                latex += "\\bottomrule\n"
                latex += "\\end{longtable}\n\n"
        
        return latex
    
    def _create_latex_visualizations(self, visualizations: List[str]) -> str:
        """Create LaTeX content for visualizations."""
        latex = ""
        
        for viz_path in visualizations:
            viz_file = Path(viz_path)
            
            if viz_file.exists() and viz_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.pdf']:
                # Get relative path
                relative_path = viz_file.relative_to(self.output_directory)
                
                latex += f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.8\\textwidth]{{{relative_path}}}
\\caption{{{viz_file.stem.replace('_', ' ').title()}}}
\\label{{fig:{viz_file.stem}}}
\\end{{figure}}

"""
        
        return latex