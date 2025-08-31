"""
H3.1 Experiment Generator

Generates complete H3.1 parameter grid experiments with topology, scenarios, and configurations.
Integrates parameter grid generation, phase transition detection, and statistical analysis.
"""

import os
import json
import shutil
from typing import Dict, List, Optional
import pandas as pd

from parameter_grid_generator import ParameterGridGenerator
from phase_transition_detector import PhaseTransitionDetector
from statistical_analysis import StatisticalAnalyzer
from h3_1_metrics import H3_1_Metrics

# Import from parent modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from topology_generator import TopologyGenerator
from scenario_generator import ConflictScenarioGenerator
from config_manager import ConfigurationManager


class H3_1_ExperimentGenerator:
    """Generates complete H3.1 parameter grid experiments."""
    
    def __init__(self, base_output_dir: str = "h3_1_experiments"):
        self.base_output_dir = base_output_dir
        self.parameter_generator = ParameterGridGenerator()
        self.topology_generator = TopologyGenerator()
        self.scenario_generator = ConflictScenarioGenerator()
        self.config_manager = ConfigurationManager()
        self.metrics_calculator = H3_1_Metrics()
        
        # Standard topology for H3.1 experiments
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
        Generate standard topology for H3.1 experiments.
        
        Args:
            output_dir: Directory to save topology files
            
        Returns:
            Dictionary with paths to generated files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate linear topology: Origin -> Hub -> Camp_A -> Camp_B -> Camp_C
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
        Generate conflict scenario for H3.1 experiment.
        
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
                                 experiment_id: str) -> str:
        """
        Generate configuration for H3.1 experiment.
        
        Args:
            output_dir: Directory to save configuration
            connectivity_rate: Social connectivity rate
            experiment_id: Unique experiment identifier
            
        Returns:
            Path to generated simsetting.yml file
        """
        # Create dual-process configuration
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
            'simulation_period': 180,  # 6 months
            'enable_cognitive_tracking': True,
            'enable_decision_logging': True,
            'output_format': 'csv'
        }
        
        # Generate configuration file
        config_path = os.path.join(output_dir, 'simsetting.yml')
        self.config_manager.create_simsetting_yml(config, config_path)
        
        # Save experiment metadata
        metadata = {
            'experiment_id': experiment_id,
            'experiment_type': 'h3_1_parameter_grid',
            'topology_type': self.standard_topology['type'],
            'scenario_type': 'gradual_conflict',
            'cognitive_mode': 'dual_process',
            'parameters': {
                'connectivity_rate': connectivity_rate,
                'topology_params': self.standard_topology['params']
            }
        }
        
        metadata_path = os.path.join(output_dir, 'experiment_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return config_path
    
    def generate_single_experiment(self, parameter_combo: Dict, 
                                 base_dir: str) -> str:
        """
        Generate a single H3.1 experiment from parameter combination.
        
        Args:
            parameter_combo: Parameter combination dictionary
            base_dir: Base directory for experiments
            
        Returns:
            Path to generated experiment directory
        """
        experiment_id = parameter_combo['experiment_id']
        experiment_dir = os.path.join(base_dir, experiment_id)
        
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
            experiment_id
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
            f.write('2020-01-01,2020-06-30\n')  # 6 months simulation
    
    def generate_full_experiment_set(self) -> str:
        """
        Generate the complete H3.1 parameter grid experiment set.
        
        Returns:
            Path to experiment set directory
        """
        print("Generating H3.1 Parameter Grid Experiment Set...")
        
        # Create base directory
        experiment_set_dir = os.path.join(self.base_output_dir, "parameter_grid_experiments")
        os.makedirs(experiment_set_dir, exist_ok=True)
        
        # Generate parameter grid
        print("Generating parameter combinations...")
        parameter_combinations = self.parameter_generator.generate_full_grid()
        
        # Save parameter grid
        grid_file = self.parameter_generator.save_parameter_grid(experiment_set_dir)
        print(f"Parameter grid saved to: {grid_file}")
        
        # Generate individual experiments
        print(f"Generating {len(parameter_combinations)} individual experiments...")
        experiment_dirs = []
        
        for i, param_combo in enumerate(parameter_combinations):
            if i % 25 == 0:  # Progress update every 25 experiments
                print(f"  Generated {i}/{len(parameter_combinations)} experiments...")
            
            experiment_dir = self.generate_single_experiment(param_combo, experiment_set_dir)
            experiment_dirs.append(experiment_dir)
        
        print(f"Generated {len(experiment_dirs)} experiments successfully!")
        
        # Create experiment set metadata
        set_metadata = {
            'experiment_set_type': 'h3_1_parameter_grid',
            'total_experiments': len(parameter_combinations),
            'generation_date': str(pd.Timestamp.now()),
            'parameter_ranges': {
                'conflict_intensity': [0.1, 0.9],
                'recovery_period': [10, 50],
                'connectivity_rate': [0.0, 8.0]
            },
            'cognitive_pressure_range': [
                min(combo['cognitive_pressure'] for combo in parameter_combinations),
                max(combo['cognitive_pressure'] for combo in parameter_combinations)
            ],
            'experiment_directories': [os.path.basename(d) for d in experiment_dirs]
        }
        
        metadata_file = os.path.join(experiment_set_dir, 'experiment_set_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(set_metadata, f, indent=2)
        
        print(f"Experiment set metadata saved to: {metadata_file}")
        print(f"Complete experiment set available at: {experiment_set_dir}")
        
        return experiment_set_dir
    
    def analyze_experiment_results(self, experiment_set_dir: str) -> Dict:
        """
        Analyze results from completed H3.1 experiments.
        
        Args:
            experiment_set_dir: Directory containing completed experiments
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        print("Analyzing H3.1 experiment results...")
        
        # Load experiment metadata
        metadata_file = os.path.join(experiment_set_dir, 'experiment_set_metadata.json')
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Experiment set metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r') as f:
            set_metadata = json.load(f)
        
        # Collect results from individual experiments
        experiment_results = []
        experiment_dirs = set_metadata.get('experiment_directories', [])
        
        for exp_dir_name in experiment_dirs:
            exp_dir_path = os.path.join(experiment_set_dir, exp_dir_name)
            if os.path.exists(exp_dir_path):
                try:
                    metrics = self.metrics_calculator.calculate_experiment_metrics(exp_dir_path)
                    experiment_results.append(metrics)
                except Exception as e:
                    print(f"Warning: Failed to analyze {exp_dir_name}: {e}")
        
        if not experiment_results:
            raise ValueError("No experiment results found for analysis")
        
        print(f"Analyzed {len(experiment_results)} experiments")
        
        # Aggregate metrics
        aggregate_metrics = self.metrics_calculator.aggregate_grid_metrics(experiment_results)
        
        # Phase transition detection
        detector = PhaseTransitionDetector()
        
        # Create summary DataFrame for analysis
        summary_data = pd.DataFrame(aggregate_metrics['summary_data'])
        
        # Detect phase transitions
        transition_results = detector.detect_phase_transition(summary_data)
        
        # Statistical analysis
        analyzer = StatisticalAnalyzer()
        scaling_validation = analyzer.validate_scaling_law(summary_data)
        
        # Generate comprehensive analysis
        analysis_results = {
            'experiment_set_metadata': set_metadata,
            'aggregate_metrics': aggregate_metrics,
            'phase_transition_analysis': transition_results,
            'scaling_law_validation': scaling_validation,
            'individual_experiment_results': experiment_results
        }
        
        # Save analysis results
        analysis_file = os.path.join(experiment_set_dir, 'h3_1_analysis_results.json')
        with open(analysis_file, 'w') as f:
            # Convert numpy types for JSON serialization
            json_safe_results = self._make_json_safe(analysis_results)
            json.dump(json_safe_results, f, indent=2)
        
        print(f"Analysis results saved to: {analysis_file}")
        
        # Generate visualizations
        try:
            plot_path = os.path.join(experiment_set_dir, 'h3_1_phase_diagram.png')
            detector.create_phase_diagram(summary_data, plot_path)
            print(f"Phase diagram saved to: {plot_path}")
        except Exception as e:
            print(f"Warning: Failed to generate phase diagram: {e}")
        
        # Generate statistical report
        if transition_results.get('critical_point_best'):
            report = analyzer.generate_statistical_report(
                summary_data, 
                transition_results['critical_point_best']
            )
            
            report_file = os.path.join(experiment_set_dir, 'h3_1_statistical_report.txt')
            with open(report_file, 'w') as f:
                f.write(report)
            
            print(f"Statistical report saved to: {report_file}")
        
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


def main():
    """Generate H3.1 parameter grid experiments."""
    generator = H3_1_ExperimentGenerator()
    
    # Generate complete experiment set
    experiment_set_dir = generator.generate_full_experiment_set()
    
    print("\nH3.1 Parameter Grid Experiment Generation Complete!")
    print(f"Experiment set location: {experiment_set_dir}")
    print("\nNext steps:")
    print("1. Run the experiments using your preferred execution method")
    print("2. Use analyze_experiment_results() to process the results")
    print("3. Review phase transition detection and scaling law validation")


if __name__ == "__main__":
    main()