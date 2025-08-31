"""
H3.2 Experiment Generator

Generates complete H3.2 phase transition identification experiments.
Creates 50 scenarios with cognitive_pressure from 0 to 2 for precise critical point detection.
"""

import os
import json
import shutil
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from pressure_parameter_generator import PressureParameterGenerator
from critical_point_detector import CriticalPointDetector
from phase_diagram_generator import PhaseDiagramGenerator

# Import from parent modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from topology_generator import TopologyGenerator
from scenario_generator import ConflictScenarioGenerator
from config_manager import ConfigurationManager


class H3_2_ExperimentGenerator:
    """Generates complete H3.2 phase transition identification experiments."""
    
    def __init__(self, base_output_dir: str = "h3_2_experiments"):
        self.base_output_dir = base_output_dir
        self.pressure_generator = PressureParameterGenerator()
        self.topology_generator = TopologyGenerator()
        self.scenario_generator = ConflictScenarioGenerator()
        self.config_manager = ConfigurationManager()
        self.critical_detector = CriticalPointDetector()
        self.diagram_generator = PhaseDiagramGenerator()
        
        # Standard topology for H3.2 experiments (same as H3.1 for consistency)
        self.standard_topology = {
            'type': 'linear',
            'params': {
                'n_nodes': 4,  # Origin -> Hub -> Camp_A/B/C
                'segment_distance': 50.0,
                'start_pop': 10000,
                'pop_decay': 0.8
            }
        }
    
    def generate_experiment_topology(self, output_dir: str) -> Dict[str, str]:
        """
        Generate standard topology for H3.2 experiments.
        
        Args:
            output_dir: Directory to save topology files
            
        Returns:
            Dictionary with paths to generated files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate linear topology
        locations_file, routes_file = self.topology_generator.generate_linear(
            n_nodes=self.standard_topology['params']['n_nodes'],
            segment_distance=self.standard_topology['params']['segment_distance'],
            start_pop=self.standard_topology['params']['start_pop'],
            pop_decay=self.standard_topology['params']['pop_decay']
        )
        
        # Save to experiment directory
        locations_path = os.path.join(output_dir, 'locations.csv')
        routes_path = os.path.join(output_dir, 'routes.csv')
        
        shutil.copy2(locations_file, locations_path)
        shutil.copy2(routes_file, routes_path)
        
        return {
            'locations': locations_path,
            'routes': routes_path
        }
    
    def generate_experiment_scenario(self, output_dir: str, 
                                   conflict_intensity: float,
                                   recovery_period: float) -> str:
        """
        Generate conflict scenario for H3.2 experiment.
        
        Args:
            output_dir: Directory to save scenario files
            conflict_intensity: Conflict intensity level
            recovery_period: Recovery period in days
            
        Returns:
            Path to generated conflicts.csv file
        """
        # Generate gradual conflict scenario
        conflicts_file = self.scenario_generator.generate_gradual_conflict(
            origin="Origin",
            start_day=0,
            end_day=int(recovery_period),
            max_intensity=conflict_intensity
        )
        
        # Save to experiment directory
        conflicts_path = os.path.join(output_dir, 'conflicts.csv')
        shutil.copy2(conflicts_file, conflicts_path)
        
        return conflicts_path
    
    def generate_experiment_config(self, output_dir: str,
                                 connectivity_rate: float,
                                 scenario_id: str) -> str:
        """
        Generate configuration for H3.2 experiment.
        
        Args:
            output_dir: Directory to save configuration
            connectivity_rate: Social connectivity rate
            scenario_id: Unique scenario identifier
            
        Returns:
            Path to generated simsetting.yml file
        """
        # Create dual-process configuration optimized for phase transition detection
        config = {
            'two_system_decision_making': True,
            'average_social_connectivity': connectivity_rate,
            'awareness_level': 3,
            'conflict_threshold': 0.6,
            'recovery_period_max': 30,
            'max_move_speed': 200.0,
            'camp_move_chance': 0.001,
            'conflict_move_chance': 1.0,
            'default_move_chance': 0.3,
            'simulation_period': 120,  # 4 months (shorter for focused analysis)
            'enable_cognitive_tracking': True,
            'enable_decision_logging': True,
            'cognitive_tracking_frequency': 1,  # Track every day for precision
            'output_format': 'csv'
        }
        
        # Generate configuration file
        config_path = os.path.join(output_dir, 'simsetting.yml')
        self.config_manager.create_simsetting_yml(config, config_path)
        
        # Save experiment metadata
        metadata = {
            'scenario_id': scenario_id,
            'experiment_type': 'h3_2_phase_transition',
            'topology_type': self.standard_topology['type'],
            'scenario_type': 'gradual_conflict',
            'cognitive_mode': 'dual_process',
            'parameters': {
                'connectivity_rate': connectivity_rate,
                'topology_params': self.standard_topology['params']
            },
            'analysis_focus': 'critical_point_detection'
        }
        
        metadata_path = os.path.join(output_dir, 'experiment_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return config_path
    
    def generate_single_experiment(self, parameter_combo: Dict, 
                                 base_dir: str) -> str:
        """
        Generate a single H3.2 experiment from parameter combination.
        
        Args:
            parameter_combo: Parameter combination dictionary
            base_dir: Base directory for experiments
            
        Returns:
            Path to generated experiment directory
        """
        scenario_id = parameter_combo['scenario_id']
        experiment_dir = os.path.join(base_dir, scenario_id)
        
        # Create experiment directory
        os.makedirs(experiment_dir, exist_ok=True)
        
        # Generate topology
        topology_files = self.generate_experiment_topology(experiment_dir)
        
        # Generate scenario
        conflicts_file = self.generate_experiment_scenario(
            experiment_dir,
            parameter_combo['conflict_intensity'],
            parameter_combo['recovery_period']
        )
        
        # Generate configuration
        config_file = self.generate_experiment_config(
            experiment_dir,
            parameter_combo['connectivity_rate'],
            scenario_id
        )
        
        # Save parameter combination
        params_file = os.path.join(experiment_dir, 'parameters.json')
        with open(params_file, 'w') as f:
            json.dump(parameter_combo, f, indent=2)
        
        # Create additional required files
        self._create_additional_files(experiment_dir)
        
        return experiment_dir
    
    def _create_additional_files(self, experiment_dir: str):
        """Create additional required files for Flee simulation."""
        # Create empty closures.csv
        closures_path = os.path.join(experiment_dir, 'closures.csv')
        with open(closures_path, 'w') as f:
            f.write('#day,closure_type,name1,name2,closure_start,closure_end\n')
        
        # Create sim_period.csv
        sim_period_path = os.path.join(experiment_dir, 'sim_period.csv')
        with open(sim_period_path, 'w') as f:
            f.write('#start_date,end_date\n')
            f.write('2020-01-01,2020-04-30\n')  # 4 months simulation
    
    def generate_full_experiment_set(self, n_scenarios: int = 50) -> str:
        """
        Generate the complete H3.2 phase transition experiment set.
        
        Args:
            n_scenarios: Number of scenarios to generate (default 50)
            
        Returns:
            Path to experiment set directory
        """
        print("Generating H3.2 Phase Transition Experiment Set...")
        
        # Create base directory
        experiment_set_dir = os.path.join(self.base_output_dir, "phase_transition_experiments")
        os.makedirs(experiment_set_dir, exist_ok=True)
        
        # Generate pressure parameter series
        print(f"Generating {n_scenarios} pressure parameter combinations...")
        parameter_combinations = self.pressure_generator.generate_pressure_series(n_scenarios)
        
        # Save pressure series
        pressure_file = self.pressure_generator.save_pressure_series(experiment_set_dir, n_scenarios)
        print(f"Pressure series saved to: {pressure_file}")
        
        # Analyze coverage
        coverage_analysis = self.pressure_generator.analyze_pressure_coverage(parameter_combinations)
        print(f"Coverage quality: {coverage_analysis['coverage_quality']}")
        print(f"Mean pressure error: {coverage_analysis['pressure_accuracy']['mean_error']:.4f}")
        
        # Generate individual experiments
        print(f"Generating {len(parameter_combinations)} individual experiments...")
        experiment_dirs = []
        
        for i, param_combo in enumerate(parameter_combinations):
            if i % 10 == 0:  # Progress update every 10 experiments
                print(f"  Generated {i}/{len(parameter_combinations)} experiments...")
            
            experiment_dir = self.generate_single_experiment(param_combo, experiment_set_dir)
            experiment_dirs.append(experiment_dir)
        
        print(f"Generated {len(experiment_dirs)} experiments successfully!")
        
        # Create experiment set metadata
        set_metadata = {
            'experiment_set_type': 'h3_2_phase_transition',
            'total_experiments': len(parameter_combinations),
            'generation_date': str(pd.Timestamp.now()),
            'pressure_range': [0.0, 2.0],
            'target_critical_point': 1.0,  # Expected critical point
            'coverage_analysis': coverage_analysis,
            'experiment_directories': [os.path.basename(d) for d in experiment_dirs]
        }
        
        metadata_file = os.path.join(experiment_set_dir, 'experiment_set_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(set_metadata, f, indent=2)
        
        print(f"Experiment set metadata saved to: {metadata_file}")
        print(f"Complete experiment set available at: {experiment_set_dir}")
        
        return experiment_set_dir
    
    def analyze_phase_transition_results(self, experiment_set_dir: str) -> Dict:
        """
        Analyze results from completed H3.2 experiments with focus on critical point detection.
        
        Args:
            experiment_set_dir: Directory containing completed experiments
            
        Returns:
            Dictionary with comprehensive phase transition analysis
        """
        print("Analyzing H3.2 phase transition results...")
        
        # Load experiment metadata
        metadata_file = os.path.join(experiment_set_dir, 'experiment_set_metadata.json')
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Experiment set metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r') as f:
            set_metadata = json.load(f)
        
        # Collect results from individual experiments
        experiment_results = []
        experiment_dirs = set_metadata.get('experiment_directories', [])
        
        print(f"Processing {len(experiment_dirs)} experiments...")
        
        for exp_dir_name in experiment_dirs:
            exp_dir_path = os.path.join(experiment_set_dir, exp_dir_name)
            if os.path.exists(exp_dir_path):
                try:
                    # Load experiment parameters
                    params_file = os.path.join(exp_dir_path, 'parameters.json')
                    if os.path.exists(params_file):
                        with open(params_file, 'r') as f:
                            params = json.load(f)
                        
                        # Load cognitive state data
                        cognitive_file = os.path.join(exp_dir_path, 'cognitive_states.csv')
                        if os.path.exists(cognitive_file):
                            cognitive_data = pd.read_csv(cognitive_file)
                            
                            # Calculate S2 activation rate
                            total_decisions = len(cognitive_data)
                            s2_decisions = len(cognitive_data[cognitive_data['cognitive_state'] == 'S2'])
                            s2_rate = s2_decisions / total_decisions if total_decisions > 0 else 0.0
                            
                            experiment_results.append({
                                'scenario_id': params['scenario_id'],
                                'cognitive_pressure': params['cognitive_pressure'],
                                'target_pressure': params['target_pressure'],
                                's2_activation_rate': s2_rate,
                                'conflict_intensity': params['conflict_intensity'],
                                'recovery_period': params['recovery_period'],
                                'connectivity_rate': params['connectivity_rate'],
                                'total_decisions': total_decisions,
                                's2_decisions': s2_decisions
                            })
                        
                except Exception as e:
                    print(f"Warning: Failed to process {exp_dir_name}: {e}")
        
        if not experiment_results:
            raise ValueError("No experiment results found for analysis")
        
        print(f"Successfully processed {len(experiment_results)} experiments")
        
        # Create analysis DataFrame
        results_df = pd.DataFrame(experiment_results)
        
        # Perform critical point detection
        print("Detecting critical point...")
        fit_results = self.critical_detector.compare_sigmoid_models(results_df)
        
        # Bootstrap analysis for confidence intervals
        print("Performing bootstrap analysis...")
        bootstrap_results = self.critical_detector.detect_critical_point_bootstrap(results_df)
        
        # Transition sharpness analysis
        if fit_results.get('comparison_successful', False):
            critical_point = fit_results['best_model_results']['critical_point']
            sharpness_analysis = self.critical_detector.analyze_transition_sharpness(
                results_df, critical_point
            )
        else:
            sharpness_analysis = {}
        
        # Compile comprehensive analysis
        analysis_results = {
            'experiment_set_metadata': set_metadata,
            'processed_experiments': len(experiment_results),
            'sigmoid_fit_results': fit_results,
            'bootstrap_results': bootstrap_results,
            'transition_sharpness': sharpness_analysis,
            'experiment_data': experiment_results,
            'summary_statistics': {
                'pressure_range_actual': [results_df['cognitive_pressure'].min(), 
                                        results_df['cognitive_pressure'].max()],
                's2_rate_range': [results_df['s2_activation_rate'].min(), 
                                results_df['s2_activation_rate'].max()],
                'mean_s2_rate': results_df['s2_activation_rate'].mean(),
                'std_s2_rate': results_df['s2_activation_rate'].std()
            }
        }
        
        # Save analysis results
        analysis_file = os.path.join(experiment_set_dir, 'h3_2_analysis_results.json')
        with open(analysis_file, 'w') as f:
            # Convert numpy types for JSON serialization
            json_safe_results = self._make_json_safe(analysis_results)
            json.dump(json_safe_results, f, indent=2)
        
        print(f"Analysis results saved to: {analysis_file}")
        
        # Generate visualizations
        print("Generating phase diagrams...")
        try:
            # Main phase diagram
            main_diagram_path = os.path.join(experiment_set_dir, 'h3_2_main_phase_diagram.png')
            self.diagram_generator.create_main_phase_diagram(
                results_df, fit_results, main_diagram_path
            )
            print(f"Main phase diagram saved to: {main_diagram_path}")
            
            # Comprehensive dashboard
            dashboard_path = os.path.join(experiment_set_dir, 'h3_2_analysis_dashboard.png')
            self.diagram_generator.create_transition_analysis_dashboard(
                results_df, fit_results, bootstrap_results, dashboard_path
            )
            print(f"Analysis dashboard saved to: {dashboard_path}")
            
            # Interactive diagram
            interactive_path = os.path.join(experiment_set_dir, 'h3_2_interactive_diagram.html')
            self.diagram_generator.create_interactive_phase_diagram(
                results_df, fit_results, interactive_path
            )
            print(f"Interactive diagram saved to: {interactive_path}")
            
        except Exception as e:
            print(f"Warning: Failed to generate some visualizations: {e}")
        
        # Print summary
        self._print_analysis_summary(analysis_results)
        
        return analysis_results
    
    def _make_json_safe(self, obj):
        """Convert numpy types to JSON-safe types."""
        if isinstance(obj, dict):
            return {key: self._make_json_safe(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif hasattr(obj, 'tolist'):  # numpy array
            return obj.tolist()
        else:
            return obj
    
    def _print_analysis_summary(self, analysis_results: Dict):
        """Print summary of analysis results."""
        print("\n" + "="*60)
        print("H3.2 PHASE TRANSITION ANALYSIS SUMMARY")
        print("="*60)
        
        # Basic statistics
        print(f"Processed experiments: {analysis_results['processed_experiments']}")
        
        summary = analysis_results['summary_statistics']
        print(f"Pressure range: {summary['pressure_range_actual'][0]:.3f} - {summary['pressure_range_actual'][1]:.3f}")
        print(f"S2 activation range: {summary['s2_rate_range'][0]:.3f} - {summary['s2_rate_range'][1]:.3f}")
        
        # Sigmoid fit results
        if analysis_results['sigmoid_fit_results'].get('comparison_successful', False):
            best_model = analysis_results['sigmoid_fit_results']['best_model_results']
            print(f"\nBest sigmoid model: {best_model['model_type']}")
            print(f"R² score: {best_model['r_squared']:.3f}")
            print(f"RMSE: {best_model['rmse']:.3f}")
            print(f"Critical point: {best_model['critical_point']:.3f}")
            
            ci_lower, ci_upper = best_model['confidence_interval']
            ci_width = ci_upper - ci_lower
            print(f"95% confidence interval: [{ci_lower:.3f}, {ci_upper:.3f}] (width: {ci_width:.3f})")
        
        # Bootstrap results
        if 'bootstrap_critical_point' in analysis_results['bootstrap_results']:
            bootstrap = analysis_results['bootstrap_results']
            print(f"\nBootstrap critical point: {bootstrap['bootstrap_critical_point']:.3f}")
            print(f"Bootstrap std: {bootstrap['bootstrap_std']:.3f}")
            
            boot_ci = bootstrap['bootstrap_confidence_interval']
            boot_width = boot_ci[1] - boot_ci[0]
            print(f"Bootstrap 95% CI: [{boot_ci[0]:.3f}, {boot_ci[1]:.3f}] (width: {boot_width:.3f})")
            print(f"Bootstrap success rate: {bootstrap['success_rate']:.1%}")
        
        # Transition sharpness
        if analysis_results['transition_sharpness']:
            sharpness = analysis_results['transition_sharpness']
            print(f"\nTransition analysis:")
            print(f"Maximum derivative: {sharpness.get('max_derivative', 'N/A'):.3f}")
            print(f"Steepest point: {sharpness.get('steepest_point', 'N/A'):.3f}")
            if sharpness.get('transition_width_25_75'):
                print(f"Transition width (25%-75%): {sharpness['transition_width_25_75']:.3f}")
        
        print("="*60)


def main():
    """Generate H3.2 phase transition experiments."""
    generator = H3_2_ExperimentGenerator()
    
    # Generate complete experiment set
    experiment_set_dir = generator.generate_full_experiment_set(n_scenarios=50)
    
    print("\nH3.2 Phase Transition Experiment Generation Complete!")
    print(f"Experiment set location: {experiment_set_dir}")
    print("\nNext steps:")
    print("1. Run the experiments using your preferred execution method")
    print("2. Use analyze_phase_transition_results() to process the results")
    print("3. Review critical point detection and confidence intervals")
    print("4. Examine phase diagrams and transition analysis")


if __name__ == "__main__":
    main()