#!/usr/bin/env python3
"""
Automated Hypothesis Testing Pipeline

This script provides systematic testing of all four hypotheses (H1-H4) 
with parallel execution, result aggregation, and statistical validation.
"""

import os
import sys
import json
import time
import argparse
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd
from scipy import stats
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from experiment_runner import ExperimentRunner
    from config_manager import ConfigurationManager, ExperimentConfig
    from utils import LoggingUtils, ValidationUtils, FileUtils
    from scenarios.h1_speed_optimality.h1_1_multi_destination.h1_1_metrics import H1_1_Metrics
    from scenarios.h1_speed_optimality.h1_2_time_pressure_cascade.h1_2_metrics import H1_2_Metrics
    from scenarios.h2_connectivity_effects.h2_1_hidden_information.h2_1_metrics import H2_1_Metrics
    from scenarios.h2_connectivity_effects.h2_2_dynamic_information.h2_2_metrics import H2_2_Metrics
    from scenarios.h3_dimensionless_parameters.h3_1_parameter_grid.h3_1_metrics import H3_1_Metrics
    from scenarios.h4_population_diversity.h4_1_adaptive_shock.resilience_metrics import ResilienceMetrics
    from scenarios.h4_population_diversity.h4_2_information_cascade.cascade_metrics import CascadeMetrics
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the flee_dual_process directory")
    sys.exit(1)


class HypothesisTestingPipeline:
    """
    Automated pipeline for systematic hypothesis testing across all scenarios.
    
    This class orchestrates the execution of all hypothesis scenarios,
    aggregates results, and performs statistical validation.
    """
    
    def __init__(self, output_dir: str = "hypothesis_results", 
                 max_parallel: int = 4, replications: int = 10):
        """
        Initialize hypothesis testing pipeline.
        
        Args:
            output_dir: Base directory for all hypothesis results
            max_parallel: Maximum parallel experiments
            replications: Number of replications per scenario
        """
        self.output_dir = Path(output_dir)
        self.max_parallel = max_parallel
        self.replications = replications
        
        # Initialize utilities
        self.logging_utils = LoggingUtils()
        self.validation_utils = ValidationUtils()
        self.file_utils = FileUtils()
        
        # Setup logger
        self.logger = self.logging_utils.get_logger('HypothesisTestingPipeline')
        
        # Initialize experiment runner
        self.experiment_runner = ExperimentRunner(
            max_parallel=max_parallel,
            base_output_dir=str(self.output_dir / "raw_experiments")
        )
        
        # Create output directory structure
        self._setup_output_directories()
        
        # Initialize hypothesis configurations
        self.hypothesis_configs = self._initialize_hypothesis_configs()
        
        # Results storage
        self.all_results = {}
        self.statistical_results = {}
        
        self.logger.info(f"HypothesisTestingPipeline initialized with {replications} replications")
    
    def _setup_output_directories(self) -> None:
        """Setup directory structure for hypothesis testing results."""
        directories = [
            self.output_dir,
            self.output_dir / "raw_experiments",
            self.output_dir / "aggregated_results",
            self.output_dir / "statistical_analysis",
            self.output_dir / "reports",
            self.output_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _initialize_hypothesis_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize configurations for all hypothesis scenarios.
        
        Returns:
            Dictionary mapping hypothesis IDs to their configurations
        """
        configs = {}
        
        # H1: Speed vs Optimality Testing
        configs['H1.1'] = {
            'name': 'Multi-Destination Choice',
            'topology_type': 'custom',
            'topology_params': {
                'network_type': 'origin_hub_camps',
                'n_camps': 3,
                'distances': [30, 60, 120],  # More dramatic distance differences
                'capacities': [500, 1500, 3000],  # More dramatic capacity differences
                'safety_levels': [0.6, 0.8, 0.95]  # More dramatic safety differences
            },
            'scenario_type': 'escalating_conflict',
            'scenario_params': {
                'origin': 'Origin',
                'start_day': 2,  # Start conflict very early
                'escalation_days': [5, 15],  # Very fast escalation
                'peak_intensity': 1.0,  # Maximum intensity
                'duration': 60  # Shorter duration for more pressure
            },
            'cognitive_modes': ['s1_only', 's2_disconnected', 's2_full', 'dual_process'],
            'metrics_class': H1_1_Metrics
        }
        
        configs['H1.2'] = {
            'name': 'Time Pressure Cascade',
            'topology_type': 'linear',
            'topology_params': {
                'n_nodes': 5,  # Town_A -> B -> C -> D -> Camp
                'segment_distance': 25.0,
                'start_pop': 5000,
                'pop_decay': 0.8
            },
            'scenario_type': 'cascading_conflict',
            'scenario_params': {
                'origins': ['Town_A', 'Town_B', 'Town_C', 'Town_D'],
                'cascade_intervals': [0, 5, 10, 15],  # Days between conflicts
                'intensity': 0.8,
                'duration': 50
            },
            'cognitive_modes': ['s1_only', 's2_disconnected', 's2_full', 'dual_process'],
            'metrics_class': H1_2_Metrics
        }
        
        # H2: Social Connectivity Impact
        configs['H2.1'] = {
            'name': 'Hidden Information',
            'topology_type': 'custom',
            'topology_params': {
                'network_type': 'hidden_camp',
                'obvious_camp': {'capacity': 500, 'visibility': 1.0, 'quality': 0.6},
                'hidden_camp': {'capacity': 1000, 'visibility': 0.1, 'quality': 0.9}
            },
            'scenario_type': 'spike_conflict',
            'scenario_params': {
                'origin': 'Origin',
                'start_day': 10,
                'peak_intensity': 0.8,
                'duration': 100
            },
            'cognitive_modes': ['s2_connected', 's2_isolated', 's1_baseline'],
            'metrics_class': H2_1_Metrics
        }
        
        configs['H2.2'] = {
            'name': 'Dynamic Information Sharing',
            'topology_type': 'star',
            'topology_params': {
                'n_camps': 4,
                'hub_pop': 3000,
                'camp_capacity': 800,
                'radius': 60.0
            },
            'scenario_type': 'dynamic_capacity',
            'scenario_params': {
                'capacity_updates': True,
                'information_lag': [0, 5, 10],  # Days for different agent types
                'update_frequency': 7,  # Weekly updates
                'duration': 120
            },
            'cognitive_modes': ['s2_connected', 's2_isolated', 's1_baseline'],
            'metrics_class': H2_2_Metrics
        }
        
        # H3: Dimensionless Parameter Testing
        configs['H3.1'] = {
            'name': 'Parameter Grid Search',
            'topology_type': 'grid',
            'topology_params': {
                'rows': 3,
                'cols': 3,
                'cell_distance': 30.0,
                'pop_distribution': 'uniform'
            },
            'scenario_type': 'parameter_grid',
            'scenario_params': {
                'conflict_intensities': [0.3, 0.5, 0.7, 0.9],
                'recovery_periods': [10, 20, 30, 40, 50],
                'connectivity_rates': [0.0, 0.2, 0.5, 0.8, 1.0],
                'duration': 150
            },
            'cognitive_modes': ['dual_process'],  # Focus on dual-process for phase transitions
            'metrics_class': H3_1_Metrics
        }
        
        # H4: Population Diversity
        configs['H4.1'] = {
            'name': 'Adaptive Shock Response',
            'topology_type': 'tree',
            'topology_params': {
                'branching_factor': 2,
                'depth': 3,
                'root_pop': 4000
            },
            'scenario_type': 'dynamic_events',
            'scenario_params': {
                'event_timeline': [
                    {'day': 0, 'type': 'conflict', 'location': 'Root'},
                    {'day': 30, 'type': 'route_closure', 'route': 'Root-Branch1'},
                    {'day': 60, 'type': 'camp_full', 'location': 'Camp_A'},
                    {'day': 90, 'type': 'new_camp', 'location': 'Emergency_Camp'}
                ],
                'duration': 150
            },
            'cognitive_modes': ['pure_s1', 'pure_s2', 'balanced', 'realistic'],
            'metrics_class': ResilienceMetrics
        }
        
        configs['H4.2'] = {
            'name': 'Information Cascade Test',
            'topology_type': 'star',
            'topology_params': {
                'n_camps': 5,
                'hub_pop': 2000,
                'camp_capacity': 600,
                'radius': 45.0
            },
            'scenario_type': 'information_cascade',
            'scenario_params': {
                's1_scout_ratio': 0.2,  # 20% S1 scouts
                's2_follower_ratio': 0.8,  # 80% S2 followers
                'information_delay': 3,  # Days for information to propagate
                'duration': 100
            },
            'cognitive_modes': ['mixed_population'],
            'metrics_class': CascadeMetrics
        }
        
        return configs
    
    def run_all_hypotheses(self, hypotheses: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run all hypothesis scenarios with systematic testing.
        
        Args:
            hypotheses: List of hypothesis IDs to run (None for all)
            
        Returns:
            Dictionary with all results and statistical analysis
        """
        if hypotheses is None:
            hypotheses = list(self.hypothesis_configs.keys())
        
        self.logger.info(f"Starting hypothesis testing for: {hypotheses}")
        
        # Run each hypothesis
        for hypothesis_id in hypotheses:
            self.logger.info(f"Running hypothesis {hypothesis_id}")
            
            try:
                results = self.run_single_hypothesis(hypothesis_id)
                self.all_results[hypothesis_id] = results
                
                # Perform statistical analysis
                stats_results = self.analyze_hypothesis_results(hypothesis_id, results)
                self.statistical_results[hypothesis_id] = stats_results
                
                self.logger.info(f"Completed hypothesis {hypothesis_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to run hypothesis {hypothesis_id}: {e}")
                self.all_results[hypothesis_id] = {'error': str(e)}
        
        # Generate comprehensive report
        final_report = self.generate_final_report()
        
        # Save all results
        self.save_all_results()
        
        return {
            'raw_results': self.all_results,
            'statistical_results': self.statistical_results,
            'final_report': final_report
        }
    
    def run_single_hypothesis(self, hypothesis_id: str) -> Dict[str, Any]:
        """
        Run all scenarios for a single hypothesis.
        
        Args:
            hypothesis_id: Hypothesis identifier (e.g., 'H1.1')
            
        Returns:
            Dictionary with hypothesis results
        """
        config = self.hypothesis_configs[hypothesis_id]
        self.logger.info(f"Running {config['name']} scenarios")
        
        # Generate experiment configurations
        experiment_configs = self._generate_hypothesis_experiments(hypothesis_id, config)
        
        self.logger.info(f"Generated {len(experiment_configs)} experiment configurations")
        
        # Execute experiments in parallel
        experiment_results = self._execute_experiments_parallel(experiment_configs)
        
        # Aggregate results by cognitive mode
        aggregated_results = self._aggregate_results_by_mode(experiment_results, config)
        
        # Calculate hypothesis-specific metrics
        hypothesis_metrics = self._calculate_hypothesis_metrics(hypothesis_id, aggregated_results)
        
        return {
            'hypothesis_id': hypothesis_id,
            'config': config,
            'experiment_results': experiment_results,
            'aggregated_results': aggregated_results,
            'hypothesis_metrics': hypothesis_metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_hypothesis_experiments(self, hypothesis_id: str, 
                                       config: Dict[str, Any]) -> List[ExperimentConfig]:
        """
        Generate experiment configurations for a hypothesis.
        
        Args:
            hypothesis_id: Hypothesis identifier
            config: Hypothesis configuration
            
        Returns:
            List of experiment configurations
        """
        experiment_configs = []
        
        # Handle special case for H3.1 parameter grid
        if hypothesis_id == 'H3.1':
            return self._generate_h3_parameter_grid(hypothesis_id, config)
        
        # Standard hypothesis experiments
        cognitive_modes = config['cognitive_modes']
        
        for mode in cognitive_modes:
            for rep in range(self.replications):
                experiment_id = f"{hypothesis_id}_{mode}_rep{rep:02d}"
                
                exp_config = ExperimentConfig(
                    experiment_id=experiment_id,
                    topology_type=config['topology_type'],
                    topology_params=config['topology_params'].copy(),
                    scenario_type=config['scenario_type'],
                    scenario_params=config['scenario_params'].copy(),
                    cognitive_mode=mode,
                    simulation_params={
                        'max_agents': 10000,
                        'print_progress': False
                    },
                    replications=1,
                    metadata={
                        'hypothesis_id': hypothesis_id,
                        'cognitive_mode': mode,
                        'replication': rep
                    }
                )
                
                experiment_configs.append(exp_config)
        
        return experiment_configs
    
    def _generate_h3_parameter_grid(self, hypothesis_id: str, 
                                  config: Dict[str, Any]) -> List[ExperimentConfig]:
        """
        Generate parameter grid experiments for H3.1.
        
        Args:
            hypothesis_id: Hypothesis identifier
            config: Hypothesis configuration
            
        Returns:
            List of experiment configurations for parameter grid
        """
        experiment_configs = []
        scenario_params = config['scenario_params']
        
        # Generate all parameter combinations
        conflict_intensities = scenario_params['conflict_intensities']
        recovery_periods = scenario_params['recovery_periods']
        connectivity_rates = scenario_params['connectivity_rates']
        
        for conflict in conflict_intensities:
            for recovery in recovery_periods:
                for connectivity in connectivity_rates:
                    # Calculate cognitive pressure
                    cognitive_pressure = (conflict * connectivity) / (recovery / 30.0)
                    
                    for rep in range(self.replications):
                        experiment_id = f"{hypothesis_id}_c{conflict}_r{recovery}_conn{connectivity}_rep{rep:02d}"
                        
                        # Create scenario parameters for this combination
                        scenario_params_copy = config['scenario_params'].copy()
                        scenario_params_copy.update({
                            'conflict_intensity': conflict,
                            'recovery_period': recovery,
                            'connectivity_rate': connectivity,
                            'cognitive_pressure': cognitive_pressure
                        })
                        
                        exp_config = ExperimentConfig(
                            experiment_id=experiment_id,
                            topology_type=config['topology_type'],
                            topology_params=config['topology_params'].copy(),
                            scenario_type=config['scenario_type'],
                            scenario_params=scenario_params_copy,
                            cognitive_mode='dual_process',
                            simulation_params={
                                'max_agents': 5000,  # Smaller for parameter grid
                                'print_progress': False,
                                'average_social_connectivity': connectivity * 8.0,
                                'conflict_threshold': 0.5,
                                'recovery_period_max': recovery
                            },
                            replications=1,
                            metadata={
                                'hypothesis_id': hypothesis_id,
                                'conflict_intensity': conflict,
                                'recovery_period': recovery,
                                'connectivity_rate': connectivity,
                                'cognitive_pressure': cognitive_pressure,
                                'replication': rep
                            }
                        )
                        
                        experiment_configs.append(exp_config)
        
        return experiment_configs
    
    def _execute_experiments_parallel(self, experiment_configs: List[ExperimentConfig]) -> List[Dict[str, Any]]:
        """
        Execute experiments in parallel with progress tracking.
        
        Args:
            experiment_configs: List of experiment configurations
            
        Returns:
            List of experiment results
        """
        self.logger.info(f"Executing {len(experiment_configs)} experiments with {self.max_parallel} parallel workers")
        
        results = []
        
        with ProcessPoolExecutor(max_workers=self.max_parallel) as executor:
            # Submit all experiments
            future_to_config = {
                executor.submit(self._run_single_experiment_worker, config): config
                for config in experiment_configs
            }
            
            # Process completed experiments
            completed = 0
            total = len(experiment_configs)
            
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Log progress
                    progress = (completed / total) * 100
                    status = "SUCCESS" if result.get('success', False) else "FAILED"
                    self.logger.info(f"Progress: {completed}/{total} ({progress:.1f}%) - "
                                   f"{config.experiment_id}: {status}")
                    
                except Exception as e:
                    self.logger.error(f"Experiment {config.experiment_id} failed: {e}")
                    results.append({
                        'experiment_id': config.experiment_id,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def _run_single_experiment_worker(self, experiment_config: ExperimentConfig) -> Dict[str, Any]:
        """
        Worker function for running single experiment.
        
        Args:
            experiment_config: Experiment configuration
            
        Returns:
            Experiment result
        """
        # Create new experiment runner for worker process
        worker_runner = ExperimentRunner(
            max_parallel=1,
            base_output_dir=str(self.output_dir / "raw_experiments"),
            timeout=1800  # 30 minutes per experiment
        )
        
        return worker_runner.run_single_experiment(experiment_config)
    
    def _aggregate_results_by_mode(self, experiment_results: List[Dict[str, Any]], 
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate experiment results by cognitive mode.
        
        Args:
            experiment_results: List of experiment results
            config: Hypothesis configuration
            
        Returns:
            Aggregated results by cognitive mode
        """
        aggregated = {}
        
        # Group results by cognitive mode
        mode_results = {}
        for result in experiment_results:
            if not result.get('success', False):
                continue
            
            metadata = result.get('metadata', {})
            mode = metadata.get('cognitive_mode', 'unknown')
            
            if mode not in mode_results:
                mode_results[mode] = []
            
            mode_results[mode].append(result)
        
        # Calculate statistics for each mode
        for mode, results in mode_results.items():
            if not results:
                continue
            
            # Extract metrics from results
            metrics = self._extract_metrics_from_results(results, config)
            
            # Calculate summary statistics
            aggregated[mode] = {
                'n_experiments': len(results),
                'success_rate': len([r for r in results if r.get('success', False)]) / len(results),
                'metrics': metrics,
                'summary_stats': self._calculate_summary_statistics(metrics)
            }
        
        return aggregated
    
    def _extract_metrics_from_results(self, results: List[Dict[str, Any]], 
                                    config: Dict[str, Any]) -> Dict[str, List[float]]:
        """
        Extract metrics from experiment results.
        
        Args:
            results: List of experiment results
            config: Hypothesis configuration
            
        Returns:
            Dictionary of metric lists
        """
        metrics = {}
        
        # Use hypothesis-specific metrics class if available
        metrics_class = config.get('metrics_class')
        
        for result in results:
            if not result.get('success', False):
                continue
            
            experiment_dir = result.get('experiment_dir')
            if not experiment_dir or not os.path.exists(experiment_dir):
                continue
            
            try:
                if metrics_class:
                    # Use hypothesis-specific metrics
                    metric_calculator = metrics_class(experiment_dir)
                    result_metrics = metric_calculator.calculate_all_metrics()
                else:
                    # Use generic metrics
                    result_metrics = self._calculate_generic_metrics(experiment_dir)
                
                # Add metrics to aggregated lists
                for metric_name, value in result_metrics.items():
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    metrics[metric_name].append(value)
                    
            except Exception as e:
                self.logger.warning(f"Failed to extract metrics from {experiment_dir}: {e}")
        
        return metrics
    
    def _calculate_generic_metrics(self, experiment_dir: str) -> Dict[str, float]:
        """
        Calculate generic metrics for experiments without specific metrics class.
        
        Args:
            experiment_dir: Experiment directory path
            
        Returns:
            Dictionary of generic metrics
        """
        metrics = {}
        
        try:
            # Look for standard Flee output files
            output_dir = os.path.join(experiment_dir, 'output')
            
            # Check for out.csv (camp populations over time)
            out_csv = os.path.join(output_dir, 'out.csv')
            if os.path.exists(out_csv):
                df = pd.read_csv(out_csv)
                
                # Calculate basic movement metrics
                if len(df) > 0:
                    # Total displaced at end
                    final_row = df.iloc[-1]
                    total_displaced = sum([final_row[col] for col in df.columns 
                                         if col.startswith('camp') or col.startswith('location')])
                    metrics['total_displaced'] = total_displaced
                    
                    # Peak displacement day
                    daily_totals = df.sum(axis=1, numeric_only=True)
                    peak_day = daily_totals.idxmax()
                    metrics['peak_displacement_day'] = peak_day
                    
                    # Settlement efficiency (how quickly people settle)
                    settlement_rate = daily_totals.iloc[-1] / daily_totals.max() if daily_totals.max() > 0 else 0
                    metrics['settlement_efficiency'] = settlement_rate
            
            # Add execution time if available
            metadata_file = os.path.join(experiment_dir, 'metadata', 'experiment_metadata.json')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    metrics['execution_time'] = metadata.get('execution_time', 0)
        
        except Exception as e:
            self.logger.warning(f"Error calculating generic metrics: {e}")
        
        return metrics
    
    def _calculate_summary_statistics(self, metrics: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate summary statistics for metrics.
        
        Args:
            metrics: Dictionary of metric lists
            
        Returns:
            Dictionary of summary statistics
        """
        summary = {}
        
        for metric_name, values in metrics.items():
            if not values:
                continue
            
            values_array = np.array(values)
            
            summary[metric_name] = {
                'mean': float(np.mean(values_array)),
                'std': float(np.std(values_array)),
                'median': float(np.median(values_array)),
                'min': float(np.min(values_array)),
                'max': float(np.max(values_array)),
                'n': len(values_array),
                'ci_lower': float(np.percentile(values_array, 2.5)),
                'ci_upper': float(np.percentile(values_array, 97.5))
            }
        
        return summary
    
    def _calculate_hypothesis_metrics(self, hypothesis_id: str, 
                                    aggregated_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate hypothesis-specific metrics and comparisons.
        
        Args:
            hypothesis_id: Hypothesis identifier
            aggregated_results: Aggregated results by cognitive mode
            
        Returns:
            Dictionary of hypothesis-specific metrics
        """
        hypothesis_metrics = {
            'hypothesis_id': hypothesis_id,
            'cognitive_mode_comparisons': {},
            'key_findings': []
        }
        
        # Get cognitive modes for this hypothesis
        modes = list(aggregated_results.keys())
        
        if len(modes) < 2:
            self.logger.warning(f"Insufficient cognitive modes for comparison in {hypothesis_id}")
            return hypothesis_metrics
        
        # Perform pairwise comparisons between cognitive modes
        for i, mode1 in enumerate(modes):
            for mode2 in modes[i+1:]:
                comparison_key = f"{mode1}_vs_{mode2}"
                
                comparison_results = self._compare_cognitive_modes(
                    aggregated_results[mode1],
                    aggregated_results[mode2],
                    mode1,
                    mode2
                )
                
                hypothesis_metrics['cognitive_mode_comparisons'][comparison_key] = comparison_results
        
        # Add hypothesis-specific analysis
        if hypothesis_id.startswith('H1'):
            hypothesis_metrics['key_findings'] = self._analyze_h1_findings(aggregated_results)
        elif hypothesis_id.startswith('H2'):
            hypothesis_metrics['key_findings'] = self._analyze_h2_findings(aggregated_results)
        elif hypothesis_id.startswith('H3'):
            hypothesis_metrics['key_findings'] = self._analyze_h3_findings(aggregated_results)
        elif hypothesis_id.startswith('H4'):
            hypothesis_metrics['key_findings'] = self._analyze_h4_findings(aggregated_results)
        
        return hypothesis_metrics
    
    def _compare_cognitive_modes(self, results1: Dict[str, Any], results2: Dict[str, Any],
                               mode1: str, mode2: str) -> Dict[str, Any]:
        """
        Compare two cognitive modes statistically.
        
        Args:
            results1: Results for first cognitive mode
            results2: Results for second cognitive mode
            mode1: Name of first cognitive mode
            mode2: Name of second cognitive mode
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'mode1': mode1,
            'mode2': mode2,
            'metric_comparisons': {},
            'significant_differences': []
        }
        
        metrics1 = results1.get('metrics', {})
        metrics2 = results2.get('metrics', {})
        
        # Compare each metric
        common_metrics = set(metrics1.keys()) & set(metrics2.keys())
        
        for metric in common_metrics:
            values1 = np.array(metrics1[metric])
            values2 = np.array(metrics2[metric])
            
            if len(values1) < 2 or len(values2) < 2:
                continue
            
            # Perform t-test
            try:
                t_stat, p_value = stats.ttest_ind(values1, values2)
                
                # Calculate effect size (Cohen's d)
                pooled_std = np.sqrt(((len(values1) - 1) * np.var(values1, ddof=1) + 
                                    (len(values2) - 1) * np.var(values2, ddof=1)) / 
                                   (len(values1) + len(values2) - 2))
                
                cohens_d = (np.mean(values1) - np.mean(values2)) / pooled_std if pooled_std > 0 else 0
                
                comparison['metric_comparisons'][metric] = {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'cohens_d': float(cohens_d),
                    'mean_difference': float(np.mean(values1) - np.mean(values2)),
                    'significant': p_value < 0.05,
                    'effect_size': self._interpret_effect_size(abs(cohens_d))
                }
                
                # Track significant differences
                if p_value < 0.05:
                    comparison['significant_differences'].append({
                        'metric': metric,
                        'p_value': float(p_value),
                        'effect_size': float(cohens_d),
                        'direction': 'higher' if np.mean(values1) > np.mean(values2) else 'lower',
                        'mode_with_higher_value': mode1 if np.mean(values1) > np.mean(values2) else mode2
                    })
                    
            except Exception as e:
                self.logger.warning(f"Failed to compare metric {metric}: {e}")
        
        return comparison
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """
        Interpret Cohen's d effect size.
        
        Args:
            cohens_d: Cohen's d value
            
        Returns:
            Effect size interpretation
        """
        if cohens_d < 0.2:
            return 'negligible'
        elif cohens_d < 0.5:
            return 'small'
        elif cohens_d < 0.8:
            return 'medium'
        else:
            return 'large'
    
    def _analyze_h1_findings(self, aggregated_results: Dict[str, Any]) -> List[str]:
        """Analyze H1 (Speed vs Optimality) specific findings."""
        findings = []
        
        # Look for speed vs optimality trade-offs
        if 's1_only' in aggregated_results and 's2_full' in aggregated_results:
            s1_metrics = aggregated_results['s1_only'].get('summary_stats', {})
            s2_metrics = aggregated_results['s2_full'].get('summary_stats', {})
            
            # Check decision speed
            if 'time_to_move' in s1_metrics and 'time_to_move' in s2_metrics:
                s1_speed = s1_metrics['time_to_move']['mean']
                s2_speed = s2_metrics['time_to_move']['mean']
                
                if s1_speed < s2_speed:
                    findings.append(f"S1 agents move {s2_speed - s1_speed:.1f} days faster on average")
                
            # Check destination quality
            if 'camp_efficiency' in s1_metrics and 'camp_efficiency' in s2_metrics:
                s1_quality = s1_metrics['camp_efficiency']['mean']
                s2_quality = s2_metrics['camp_efficiency']['mean']
                
                if s2_quality > s1_quality:
                    findings.append(f"S2 agents achieve {(s2_quality - s1_quality) * 100:.1f}% better camp efficiency")
        
        return findings
    
    def _analyze_h2_findings(self, aggregated_results: Dict[str, Any]) -> List[str]:
        """Analyze H2 (Social Connectivity) specific findings."""
        findings = []
        
        # Look for connectivity effects
        if 's2_connected' in aggregated_results and 's2_isolated' in aggregated_results:
            connected_metrics = aggregated_results['s2_connected'].get('summary_stats', {})
            isolated_metrics = aggregated_results['s2_isolated'].get('summary_stats', {})
            
            # Check information discovery
            if 'hidden_camp_discovery_rate' in connected_metrics and 'hidden_camp_discovery_rate' in isolated_metrics:
                connected_discovery = connected_metrics['hidden_camp_discovery_rate']['mean']
                isolated_discovery = isolated_metrics['hidden_camp_discovery_rate']['mean']
                
                if connected_discovery > isolated_discovery:
                    improvement = (connected_discovery - isolated_discovery) * 100
                    findings.append(f"Connected agents discover hidden camps {improvement:.1f}% more often")
        
        return findings
    
    def _analyze_h3_findings(self, aggregated_results: Dict[str, Any]) -> List[str]:
        """Analyze H3 (Dimensionless Parameters) specific findings."""
        findings = []
        
        # Look for phase transitions in dual-process mode
        if 'dual_process' in aggregated_results:
            metrics = aggregated_results['dual_process'].get('metrics', {})
            
            if 'cognitive_pressure' in metrics and 's2_activation_rate' in metrics:
                # Analyze relationship between cognitive pressure and S2 activation
                pressures = np.array(metrics['cognitive_pressure'])
                activations = np.array(metrics['s2_activation_rate'])
                
                # Find critical pressure point
                sorted_indices = np.argsort(pressures)
                sorted_pressures = pressures[sorted_indices]
                sorted_activations = activations[sorted_indices]
                
                # Look for steep transition
                activation_gradient = np.gradient(sorted_activations)
                max_gradient_idx = np.argmax(activation_gradient)
                critical_pressure = sorted_pressures[max_gradient_idx]
                
                findings.append(f"Critical cognitive pressure for S2 activation: {critical_pressure:.2f}")
        
        return findings
    
    def _analyze_h4_findings(self, aggregated_results: Dict[str, Any]) -> List[str]:
        """Analyze H4 (Population Diversity) specific findings."""
        findings = []
        
        # Look for diversity advantages
        mode_performance = {}
        
        for mode, results in aggregated_results.items():
            summary_stats = results.get('summary_stats', {})
            if 'resilience_score' in summary_stats:
                mode_performance[mode] = summary_stats['resilience_score']['mean']
        
        if mode_performance:
            best_mode = max(mode_performance.keys(), key=lambda k: mode_performance[k])
            worst_mode = min(mode_performance.keys(), key=lambda k: mode_performance[k])
            
            improvement = mode_performance[best_mode] - mode_performance[worst_mode]
            findings.append(f"{best_mode} population shows {improvement:.2f} higher resilience than {worst_mode}")
        
        return findings
    
    def analyze_hypothesis_results(self, hypothesis_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform statistical analysis on hypothesis results.
        
        Args:
            hypothesis_id: Hypothesis identifier
            results: Hypothesis results
            
        Returns:
            Statistical analysis results
        """
        analysis = {
            'hypothesis_id': hypothesis_id,
            'statistical_tests': {},
            'effect_sizes': {},
            'confidence_intervals': {},
            'hypothesis_supported': None,
            'evidence_strength': 'insufficient'
        }
        
        aggregated_results = results.get('aggregated_results', {})
        hypothesis_metrics = results.get('hypothesis_metrics', {})
        
        # Analyze cognitive mode comparisons
        comparisons = hypothesis_metrics.get('cognitive_mode_comparisons', {})
        
        significant_effects = []
        large_effects = []
        
        for comparison_name, comparison_data in comparisons.items():
            significant_diffs = comparison_data.get('significant_differences', [])
            
            for diff in significant_diffs:
                significant_effects.append({
                    'comparison': comparison_name,
                    'metric': diff['metric'],
                    'p_value': diff['p_value'],
                    'effect_size': diff['effect_size'],
                    'direction': diff['direction']
                })
                
                if abs(diff['effect_size']) > 0.5:  # Medium to large effect
                    large_effects.append(diff)
        
        analysis['statistical_tests']['significant_effects'] = significant_effects
        analysis['statistical_tests']['large_effects'] = large_effects
        
        # Determine hypothesis support
        if len(significant_effects) > 0:
            if len(large_effects) > 0:
                analysis['hypothesis_supported'] = True
                analysis['evidence_strength'] = 'strong'
            else:
                analysis['hypothesis_supported'] = True
                analysis['evidence_strength'] = 'moderate'
        else:
            analysis['hypothesis_supported'] = False
            analysis['evidence_strength'] = 'insufficient'
        
        return analysis
    
    def generate_final_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive final report across all hypotheses.
        
        Returns:
            Final report dictionary
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_hypotheses_tested': len(self.all_results),
                'hypotheses_supported': 0,
                'hypotheses_rejected': 0,
                'hypotheses_inconclusive': 0
            },
            'hypothesis_summaries': {},
            'overall_conclusions': [],
            'recommendations': []
        }
        
        # Analyze each hypothesis
        for hypothesis_id, stats_results in self.statistical_results.items():
            supported = stats_results.get('hypothesis_supported')
            evidence_strength = stats_results.get('evidence_strength', 'insufficient')
            
            if supported is True:
                report['summary']['hypotheses_supported'] += 1
            elif supported is False:
                report['summary']['hypotheses_rejected'] += 1
            else:
                report['summary']['hypotheses_inconclusive'] += 1
            
            # Create hypothesis summary
            report['hypothesis_summaries'][hypothesis_id] = {
                'supported': supported,
                'evidence_strength': evidence_strength,
                'key_findings': self.all_results[hypothesis_id].get('hypothesis_metrics', {}).get('key_findings', []),
                'significant_effects': len(stats_results.get('statistical_tests', {}).get('significant_effects', []))
            }
        
        # Generate overall conclusions
        supported_count = report['summary']['hypotheses_supported']
        total_count = report['summary']['total_hypotheses_tested']
        
        if supported_count > total_count * 0.75:
            report['overall_conclusions'].append("Strong evidence for dual-process theory in refugee movement")
        elif supported_count > total_count * 0.5:
            report['overall_conclusions'].append("Moderate evidence for dual-process theory effects")
        else:
            report['overall_conclusions'].append("Limited evidence for dual-process theory predictions")
        
        # Generate recommendations
        report['recommendations'] = [
            "Increase replication count for more robust statistical power",
            "Extend simulation duration to capture long-term effects",
            "Validate findings with real-world refugee movement data",
            "Investigate parameter sensitivity for key findings"
        ]
        
        return report
    
    def save_all_results(self) -> None:
        """Save all results to files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save raw results
        raw_results_file = self.output_dir / "aggregated_results" / f"raw_results_{timestamp}.json"
        with open(raw_results_file, 'w') as f:
            json.dump(self.all_results, f, indent=2, default=str)
        
        # Save statistical results
        stats_results_file = self.output_dir / "statistical_analysis" / f"statistical_results_{timestamp}.json"
        with open(stats_results_file, 'w') as f:
            json.dump(self.statistical_results, f, indent=2, default=str)
        
        # Save final report
        final_report = self.generate_final_report()
        report_file = self.output_dir / "reports" / f"final_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        self.logger.info(f"All results saved to {self.output_dir}")


def main():
    """Main function for command-line execution."""
    parser = argparse.ArgumentParser(description='Run automated hypothesis testing pipeline')
    
    parser.add_argument('--hypotheses', nargs='+', 
                       choices=['H1.1', 'H1.2', 'H2.1', 'H2.2', 'H3.1', 'H4.1', 'H4.2'],
                       help='Specific hypotheses to test (default: all)')
    
    parser.add_argument('--output-dir', default='hypothesis_results',
                       help='Output directory for results')
    
    parser.add_argument('--max-parallel', type=int, default=4,
                       help='Maximum parallel experiments')
    
    parser.add_argument('--replications', type=int, default=10,
                       help='Number of replications per scenario')
    
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    parser.add_argument('--extended-topology', action='store_true',
                       help='Run extended topology robustness testing across all network types')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize pipeline
    pipeline = HypothesisTestingPipeline(
        output_dir=args.output_dir,
        max_parallel=args.max_parallel,
        replications=args.replications
    )
    
    # Run hypothesis testing
    try:
        if args.extended_topology:
            # Import and use extended topology pipeline
            from run_extended_topology_scenarios import ExtendedTopologyTestingPipeline
            
            extended_pipeline = ExtendedTopologyTestingPipeline(
                output_dir=args.output_dir,
                max_parallel=args.max_parallel,
                replications=args.replications
            )
            
            print("🌐 Running Extended Topology Robustness Testing...")
            results = extended_pipeline.run_topology_robustness_analysis(args.hypotheses)
            
            # Print topology-specific summary
            if 'cross_hypothesis_analysis' in results:
                cross_analysis = results['cross_hypothesis_analysis']
                if 'universal_topology_effects' in cross_analysis:
                    universal = cross_analysis['universal_topology_effects']
                    print(f"\n🏆 Best Overall Topology: {universal.get('best_overall_topology', 'N/A')}")
                    print(f"🎯 Most Consistent Topology: {universal.get('most_consistent_topology', 'N/A')}")
            
            print(f"\n📁 Extended topology results saved to: {args.output_dir}")
            return
        
        results = pipeline.run_all_hypotheses(args.hypotheses)
        
        print("\n" + "="*80)
        print("HYPOTHESIS TESTING COMPLETED")
        print("="*80)
        
        final_report = results['final_report']
        summary = final_report['summary']
        
        print(f"Total hypotheses tested: {summary['total_hypotheses_tested']}")
        print(f"Hypotheses supported: {summary['hypotheses_supported']}")
        print(f"Hypotheses rejected: {summary['hypotheses_rejected']}")
        print(f"Inconclusive results: {summary['hypotheses_inconclusive']}")
        
        print("\nOverall conclusions:")
        for conclusion in final_report['overall_conclusions']:
            print(f"  - {conclusion}")
        
        print(f"\nDetailed results saved to: {args.output_dir}")
        
    except Exception as e:
        print(f"Error running hypothesis testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()