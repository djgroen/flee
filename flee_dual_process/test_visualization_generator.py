#!/usr/bin/env python3
"""
Test script for the Visualization Generator System

This script tests the visualization generator functionality with sample data.
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from visualization_generator import VisualizationGenerator, PlotConfig
    from utils import LoggingUtils
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)


def create_sample_experiment_data(experiment_dir: Path, experiment_id: str, 
                                cognitive_mode: str = "s1_only", 
                                topology: str = "linear", 
                                scenario: str = "spike"):
    """
    Create sample experiment data for testing.
    
    Args:
        experiment_dir: Directory to create experiment data in
        experiment_id: Experiment identifier
        cognitive_mode: Cognitive mode for the experiment
        topology: Topology type
        scenario: Scenario type
    """
    # Create directory structure
    output_dir = experiment_dir / "output"
    metadata_dir = experiment_dir / "metadata"
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample movement data (out.csv)
    days = range(0, 100)
    locations = ['Origin', 'Camp_A', 'Camp_B', 'Camp_C']
    
    movement_data = []
    for day in days:
        for location in locations:
            if location == 'Origin':
                # Origin population decreases over time
                refugees = max(0, 1000 - day * 10 + np.random.normal(0, 50))
            else:
                # Camp populations increase over time with some randomness
                base_pop = min(day * 3, 300) + np.random.normal(0, 20)
                refugees = max(0, base_pop)
            
            movement_data.append({
                'day': day,
                'location': location,
                'refugees': int(refugees),
                'total_refugees': int(refugees)  # Simplified
            })
    
    movement_df = pd.DataFrame(movement_data)
    movement_df.to_csv(output_dir / "out.csv", index=False)
    
    # Create sample cognitive states data
    if cognitive_mode != "s1_only":
        cognitive_data = []
        n_agents = 50
        
        for day in range(0, 100, 5):  # Sample every 5 days
            for agent_id in range(1, n_agents + 1):
                # Simulate cognitive state transitions
                if cognitive_mode == "s2_full":
                    # More S2 states
                    state = np.random.choice(['S1', 'S2'], p=[0.3, 0.7])
                elif cognitive_mode == "dual_process":
                    # Balanced states
                    state = np.random.choice(['S1', 'S2'], p=[0.5, 0.5])
                else:
                    # Mostly S1
                    state = np.random.choice(['S1', 'S2'], p=[0.8, 0.2])
                
                location = np.random.choice(locations)
                connections = np.random.randint(0, 5) if state == 'S2' else 0
                
                cognitive_data.append({
                    'day': day,
                    'agent_id': agent_id,
                    'cognitive_state': state,
                    'location': location,
                    'connections': connections,
                    'last_transition': day - np.random.randint(0, 10),
                    'decision_factors': f'{{"conflict_level": {np.random.random():.2f}, "social_info": {state == "S2"}}}'
                })
        
        cognitive_df = pd.DataFrame(cognitive_data)
        
        # Write with header
        with open(output_dir / "cognitive_states.out", 'w') as f:
            f.write("#day,agent_id,cognitive_state,location,connections,last_transition,decision_factors\n")
            cognitive_df.to_csv(f, index=False, header=False)
    
    # Create sample decision log data
    decision_data = []
    for day in range(0, 100, 10):  # Sample every 10 days
        for agent_id in range(1, 20):  # Fewer agents for decision log
            decision_data.append({
                'day': day,
                'agent_id': agent_id,
                'decision_type': np.random.choice(['move', 'stay', 'explore']),
                'cognitive_state': np.random.choice(['S1', 'S2']),
                'factors': f'{{"distance": {np.random.random():.2f}, "capacity": {np.random.random():.2f}}}',
                'location': np.random.choice(locations)
            })
    
    decision_df = pd.DataFrame(decision_data)
    
    # Write with header
    with open(output_dir / "decision_log.out", 'w') as f:
        f.write("#day,agent_id,decision_type,cognitive_state,factors,location\n")
        decision_df.to_csv(f, index=False, header=False)
    
    # Create experiment metadata
    metadata = {
        'experiment_id': experiment_id,
        'cognitive_mode': cognitive_mode,
        'topology_type': topology,
        'scenario_type': scenario,
        'parameters': {
            'awareness_level': np.random.uniform(1, 3),
            'social_connectivity': np.random.uniform(0, 8),
            'conflict_threshold': np.random.uniform(0.3, 0.8)
        },
        'timestamp': '2024-01-01T00:00:00',
        'simulation_duration': 100
    }
    
    with open(metadata_dir / "experiment_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)


def test_visualization_generator():
    """Test the visualization generator with sample data."""
    
    # Setup logging
    logging_utils = LoggingUtils()
    logger = logging_utils.get_logger('TestVisualizationGenerator')
    
    logger.info("Starting visualization generator tests...")
    
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        results_dir = temp_path / "results"
        results_dir.mkdir()
        
        # Create sample experiments
        experiments = [
            ('exp_s1_linear_spike', 's1_only', 'linear', 'spike'),
            ('exp_s2_linear_spike', 's2_full', 'linear', 'spike'),
            ('exp_dual_linear_spike', 'dual_process', 'linear', 'spike'),
            ('exp_s1_star_gradual', 's1_only', 'star', 'gradual'),
            ('exp_s2_star_gradual', 's2_full', 'star', 'gradual'),
        ]
        
        experiment_dirs = []
        for exp_id, cognitive_mode, topology, scenario in experiments:
            exp_dir = results_dir / exp_id
            create_sample_experiment_data(exp_dir, exp_id, cognitive_mode, topology, scenario)
            experiment_dirs.append(str(exp_dir))
            logger.info(f"Created sample experiment: {exp_id}")
        
        # Test visualization generator
        try:
            # Test matplotlib backend
            logger.info("Testing matplotlib backend...")
            viz_gen_mpl = VisualizationGenerator(
                results_directory=str(results_dir),
                backend='matplotlib',
                plot_config=PlotConfig(figsize=(10, 6), dpi=150)
            )
            
            # Test cognitive state plots
            logger.info("Testing cognitive state plots...")
            cognitive_plots = viz_gen_mpl.create_cognitive_state_plots(
                experiment_dirs, 
                plot_types=['evolution', 'distribution']
            )
            logger.info(f"Generated {len(cognitive_plots)} cognitive state plots")
            
            # Test movement comparison charts
            logger.info("Testing movement comparison charts...")
            movement_plots = viz_gen_mpl.create_movement_comparison_charts(experiment_dirs)
            logger.info(f"Generated {len(movement_plots)} movement comparison charts")
            
            # Test parameter sensitivity plots (create fake sweep data)
            logger.info("Testing parameter sensitivity plots...")
            sweep_dir = temp_path / "sweep_results"
            sweep_dir.mkdir()
            
            # Copy some experiments to sweep directory for testing
            for i, exp_dir in enumerate(experiment_dirs[:3]):
                shutil.copytree(exp_dir, sweep_dir / f"sweep_exp_{i}")
            
            sensitivity_plots = viz_gen_mpl.create_parameter_sensitivity_plots(
                str(sweep_dir),
                parameters=['awareness_level', 'social_connectivity'],
                metrics=['first_movement_day', 'destination_entropy']
            )
            logger.info(f"Generated {len(sensitivity_plots)} parameter sensitivity plots")
            
            # Test report generation
            logger.info("Testing report generation...")
            report_file = viz_gen_mpl.generate_experiment_report(
                experiment_dirs,
                report_title="Test Dual Process Experiment Report",
                output_format="html"
            )
            
            if report_file:
                logger.info(f"Generated report: {report_file}")
            else:
                logger.warning("Report generation failed")
            
            # Test plotly backend if available
            try:
                import plotly
                logger.info("Testing plotly backend...")
                
                viz_gen_plotly = VisualizationGenerator(
                    results_directory=str(results_dir),
                    backend='plotly'
                )
                
                plotly_plots = viz_gen_plotly.create_cognitive_state_plots(
                    experiment_dirs[:2],  # Test with fewer experiments
                    plot_types=['evolution']
                )
                logger.info(f"Generated {len(plotly_plots)} plotly plots")
                
            except ImportError:
                logger.info("Plotly not available, skipping plotly tests")
            
            # List all generated files
            viz_output_dir = Path(viz_gen_mpl.output_directory)
            if viz_output_dir.exists():
                generated_files = list(viz_output_dir.rglob('*'))
                logger.info(f"Total generated files: {len(generated_files)}")
                
                for file_path in generated_files:
                    if file_path.is_file():
                        logger.info(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")
            
            logger.info("All visualization generator tests completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Visualization generator test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = test_visualization_generator()
    sys.exit(0 if success else 1)