#!/usr/bin/env python3
"""
Staged Execution of Comprehensive Topology-S1/S2 Experiments

This script runs the comprehensive topology experiments in stages, allowing for
incremental validation, debugging, and analysis of results as they are generated.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from pathlib import Path
import time

# Add current directory to path
sys.path.insert(0, '.')

class StagedTopologyExperimentRunner:
    """Staged execution of topology experiments with validation."""
    
    def __init__(self):
        self.stages = [
            {
                "name": "Stage 1: Validation",
                "description": "Test basic functionality with minimal experiments",
                "topologies": ["linear_4", "star_4", "grid_4"],
                "s1s2_configs": ["baseline", "constant_s2"],
                "replicates": 2,
                "timesteps": 20
            },
            {
                "name": "Stage 2: Core Topologies",
                "description": "Test core topology types with all S1/S2 configs",
                "topologies": ["linear_4", "linear_8", "star_4", "star_8", "grid_4", "grid_9"],
                "s1s2_configs": ["baseline", "constant_s2", "soft_gate", "diminishing"],
                "replicates": 3,
                "timesteps": 50
            },
            {
                "name": "Stage 3: Extended Topologies",
                "description": "Add random and scale-free topologies",
                "topologies": ["random_8_p0.2", "random_8_p0.4", "scale_free_8_m2", "scale_free_8_m4", "ring_8"],
                "s1s2_configs": ["baseline", "constant_s2", "soft_gate", "diminishing"],
                "replicates": 3,
                "timesteps": 50
            },
            {
                "name": "Stage 4: Full Scale",
                "description": "Run all topologies with all S1/S2 configs",
                "topologies": "all",
                "s1s2_configs": "all",
                "replicates": 5,
                "timesteps": 75
            },
            {
                "name": "Stage 5: High Power",
                "description": "Final high-statistical-power runs",
                "topologies": "all",
                "s1s2_configs": "all",
                "replicates": 10,
                "timesteps": 100
            }
        ]
        
        self.current_stage = 0
        self.results = {}
        self.stage_results = {}
        
    def get_stage_info(self, stage_idx):
        """Get information about a specific stage."""
        if stage_idx >= len(self.stages):
            return None
        return self.stages[stage_idx]
    
    def calculate_stage_experiments(self, stage_idx):
        """Calculate number of experiments for a stage."""
        stage = self.stages[stage_idx]
        
        if stage["topologies"] == "all":
            n_topologies = 6  # All topology types
        else:
            n_topologies = len(stage["topologies"])
        
        if stage["s1s2_configs"] == "all":
            n_configs = 6  # All S1/S2 configs
        else:
            n_configs = len(stage["s1s2_configs"])
        
        n_replicates = stage["replicates"]
        
        return n_topologies * n_configs * n_replicates
    
    def run_stage(self, stage_idx, validate_only=False):
        """Run a specific stage of experiments."""
        
        stage = self.stages[stage_idx]
        print(f"\n🚀 RUNNING {stage['name'].upper()}")
        print("=" * 80)
        print(f"Description: {stage['description']}")
        
        # Calculate experiments
        n_experiments = self.calculate_stage_experiments(stage_idx)
        print(f"Total experiments: {n_experiments}")
        print(f"Timesteps per experiment: {stage['timesteps']}")
        print(f"Replicates per combination: {stage['replicates']}")
        
        if validate_only:
            print("🔍 VALIDATION MODE - Will run 1 experiment per combination")
            stage["replicates"] = 1
        
        # Import the comprehensive experiment class
        from comprehensive_topology_s1s2_experiments import ComprehensiveTopologyExperiment
        
        # Create experiment instance
        experiment = ComprehensiveTopologyExperiment()
        
        # Modify experiment parameters for this stage
        experiment.n_replicates = stage["replicates"]
        experiment.timesteps = stage["timesteps"]
        
        # Filter topologies and configs if specified
        if stage["topologies"] != "all":
            # Filter topology specs
            filtered_specs = []
            for spec in experiment.topology_specs:
                if spec.name in stage["topologies"]:
                    filtered_specs.append(spec)
            experiment.topology_specs = filtered_specs
        
        if stage["s1s2_configs"] != "all":
            # Filter S1/S2 configs
            filtered_configs = []
            for config in experiment.s1s2_configs:
                if config.name in stage["s1s2_configs"]:
                    filtered_configs.append(config)
            experiment.s1s2_configs = filtered_configs
        
        # Create stage-specific output directory
        stage_output_dir = f"results/stage_{stage_idx+1}_{stage['name'].split(':')[1].strip().lower().replace(' ', '_')}"
        os.makedirs(stage_output_dir, exist_ok=True)
        
        print(f"Output directory: {stage_output_dir}")
        
        # Run experiments
        start_time = time.time()
        results = experiment.run_comprehensive_experiments()
        end_time = time.time()
        
        # Save stage results
        self.stage_results[stage_idx] = {
            "stage_info": stage,
            "results": results,
            "execution_time": end_time - start_time,
            "n_experiments": n_experiments
        }
        
        # Save stage results to file
        stage_results_file = os.path.join(stage_output_dir, f"stage_{stage_idx+1}_results.json")
        with open(stage_results_file, 'w') as f:
            json.dump(self.stage_results[stage_idx], f, indent=2, default=str)
        
        print(f"\n✅ Stage {stage_idx+1} completed in {end_time - start_time:.1f} seconds")
        print(f"📁 Results saved to: {stage_output_dir}")
        
        return results
    
    def analyze_stage_results(self, stage_idx):
        """Analyze results from a specific stage."""
        
        if stage_idx not in self.stage_results:
            print(f"❌ No results found for stage {stage_idx+1}")
            return None
        
        print(f"\n📊 ANALYZING STAGE {stage_idx+1} RESULTS")
        print("=" * 60)
        
        stage_data = self.stage_results[stage_idx]
        results = stage_data["results"]
        
        # Extract key metrics
        analysis_data = []
        for topology_name, s1s2_results in results.items():
            for s1s2_config_name, replicates in s1s2_results.items():
                for replicate in replicates:
                    final_evacuation = replicate['evacuation_rates'][-1]
                    final_s2_rate = replicate['s2_activation_rates'][-1]
                    avg_pressure = np.mean([stat['mean'] for stat in replicate['pressure_stats']])
                    
                    analysis_data.append({
                        'topology': topology_name,
                        's1s2_config': s1s2_config_name,
                        'final_evacuation': final_evacuation,
                        'final_s2_rate': final_s2_rate,
                        'avg_pressure': avg_pressure
                    })
        
        analysis_df = pd.DataFrame(analysis_data)
        
        # Print summary statistics
        print("📈 Summary Statistics:")
        print(f"Total experiments: {len(analysis_data)}")
        print(f"Topologies tested: {len(analysis_df['topology'].unique())}")
        print(f"S1/S2 configs tested: {len(analysis_df['s1s2_config'].unique())}")
        
        print("\n🎯 Evacuation Success by Topology:")
        topology_means = analysis_df.groupby('topology')['final_evacuation'].mean().sort_values(ascending=False)
        for topology, mean_val in topology_means.items():
            print(f"  {topology}: {mean_val:.3f}")
        
        print("\n🔧 Evacuation Success by S1/S2 Config:")
        config_means = analysis_df.groupby('s1s2_config')['final_evacuation'].mean().sort_values(ascending=False)
        for config, mean_val in config_means.items():
            print(f"  {config}: {mean_val:.3f}")
        
        # Check for issues
        print("\n🔍 Quality Checks:")
        
        # Check for zero evacuation rates
        zero_evacuation = (analysis_df['final_evacuation'] == 0).sum()
        if zero_evacuation > 0:
            print(f"  ⚠️  {zero_evacuation} experiments with zero evacuation")
        else:
            print("  ✅ All experiments show some evacuation")
        
        # Check for high S2 activation
        high_s2 = (analysis_df['final_s2_rate'] > 0.5).sum()
        if high_s2 > 0:
            print(f"  ✅ {high_s2} experiments with high S2 activation (>50%)")
        else:
            print("  ⚠️  No experiments with high S2 activation")
        
        # Check pressure ranges
        pressure_range = analysis_df['avg_pressure'].max() - analysis_df['avg_pressure'].min()
        if pressure_range > 0.1:
            print(f"  ✅ Good pressure variation (range: {pressure_range:.3f})")
        else:
            print(f"  ⚠️  Limited pressure variation (range: {pressure_range:.3f})")
        
        return analysis_df
    
    def create_stage_summary_plot(self, stage_idx):
        """Create summary plot for a stage."""
        
        if stage_idx not in self.stage_results:
            print(f"❌ No results found for stage {stage_idx+1}")
            return
        
        print(f"\n📊 Creating Stage {stage_idx+1} Summary Plot...")
        
        # Analyze results
        analysis_df = self.analyze_stage_results(stage_idx)
        if analysis_df is None:
            return
        
        # Create plot
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'Stage {stage_idx+1} Results Summary', fontsize=16, fontweight='bold')
        
        # Plot 1: Evacuation by topology
        ax1 = axes[0, 0]
        sns.boxplot(data=analysis_df, x='topology', y='final_evacuation', ax=ax1)
        ax1.set_title('Evacuation Success by Topology')
        ax1.set_ylabel('Final Evacuation Rate')
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Evacuation by S1/S2 config
        ax2 = axes[0, 1]
        sns.boxplot(data=analysis_df, x='s1s2_config', y='final_evacuation', ax=ax2)
        ax2.set_title('Evacuation Success by S1/S2 Config')
        ax2.set_ylabel('Final Evacuation Rate')
        ax2.tick_params(axis='x', rotation=45)
        
        # Plot 3: S2 activation by topology
        ax3 = axes[1, 0]
        sns.boxplot(data=analysis_df, x='topology', y='final_s2_rate', ax=ax3)
        ax3.set_title('S2 Activation by Topology')
        ax3.set_ylabel('Final S2 Activation Rate')
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: Pressure by topology
        ax4 = axes[1, 1]
        sns.boxplot(data=analysis_df, x='topology', y='avg_pressure', ax=ax4)
        ax4.set_title('Average Pressure by Topology')
        ax4.set_ylabel('Average Pressure')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        stage_output_dir = f"results/stage_{stage_idx+1}_{self.stages[stage_idx]['name'].split(':')[1].strip().lower().replace(' ', '_')}"
        plot_file = os.path.join(stage_output_dir, f"stage_{stage_idx+1}_summary.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ Summary plot saved to: {plot_file}")
    
    def run_all_stages(self, start_stage=0, validate_first=True):
        """Run all stages starting from a specific stage."""
        
        print("🚀 STAGED TOPOLOGY EXPERIMENT EXECUTION")
        print("=" * 80)
        print(f"Total stages: {len(self.stages)}")
        print(f"Starting from stage: {start_stage + 1}")
        
        for stage_idx in range(start_stage, len(self.stages)):
            stage = self.stages[stage_idx]
            
            print(f"\n{'='*80}")
            print(f"STAGE {stage_idx+1}/{len(self.stages)}: {stage['name']}")
            print(f"{'='*80}")
            
            # Ask for confirmation
            if stage_idx > 0:  # Skip confirmation for first stage
                response = input(f"Run {stage['name']}? (y/n/s for skip): ").lower().strip()
                if response == 'n':
                    print("❌ Stage cancelled by user")
                    break
                elif response == 's':
                    print("⏭️  Stage skipped")
                    continue
            
            # Run stage
            try:
                results = self.run_stage(stage_idx, validate_only=validate_first and stage_idx == 0)
                
                # Analyze results
                analysis_df = self.analyze_stage_results(stage_idx)
                
                # Create summary plot
                self.create_stage_summary_plot(stage_idx)
                
                # Ask if user wants to continue
                if stage_idx < len(self.stages) - 1:
                    response = input(f"\nContinue to next stage? (y/n): ").lower().strip()
                    if response == 'n':
                        print("❌ Execution stopped by user")
                        break
                
            except Exception as e:
                print(f"❌ Error in stage {stage_idx+1}: {e}")
                response = input("Continue to next stage? (y/n): ").lower().strip()
                if response == 'n':
                    break
        
        print(f"\n🎉 STAGED EXECUTION COMPLETE!")
        print(f"Completed stages: {list(self.stage_results.keys())}")


def main():
    """Main function for staged execution."""
    
    print("🚀 STAGED TOPOLOGY EXPERIMENT EXECUTION")
    print("=" * 80)
    print("This runs comprehensive topology experiments in stages for validation and debugging.")
    print()
    
    # Create staged runner
    runner = StagedTopologyExperimentRunner()
    
    # Show stage information
    print("📋 STAGE OVERVIEW:")
    for i, stage in enumerate(runner.stages):
        n_experiments = runner.calculate_stage_experiments(i)
        print(f"  Stage {i+1}: {stage['name']}")
        print(f"    - {stage['description']}")
        print(f"    - {n_experiments} experiments")
        print(f"    - {stage['timesteps']} timesteps per experiment")
        print()
    
    # Ask user what to do
    print("🎯 OPTIONS:")
    print("1. Run all stages")
    print("2. Run specific stage")
    print("3. Validate first stage only")
    print("4. Show stage details")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        validate_first = input("Validate first stage only? (y/n): ").lower().strip() == 'y'
        runner.run_all_stages(validate_first=validate_first)
    
    elif choice == "2":
        stage_num = int(input("Enter stage number (1-5): ")) - 1
        if 0 <= stage_num < len(runner.stages):
            runner.run_stage(stage_num)
            runner.analyze_stage_results(stage_num)
            runner.create_stage_summary_plot(stage_num)
        else:
            print("❌ Invalid stage number")
    
    elif choice == "3":
        runner.run_stage(0, validate_only=True)
        runner.analyze_stage_results(0)
        runner.create_stage_summary_plot(0)
    
    elif choice == "4":
        stage_num = int(input("Enter stage number (1-5): ")) - 1
        if 0 <= stage_num < len(runner.stages):
            stage = runner.get_stage_info(stage_num)
            print(f"\n📋 STAGE {stage_num+1} DETAILS:")
            print(f"Name: {stage['name']}")
            print(f"Description: {stage['description']}")
            print(f"Topologies: {stage['topologies']}")
            print(f"S1/S2 Configs: {stage['s1s2_configs']}")
            print(f"Replicates: {stage['replicates']}")
            print(f"Timesteps: {stage['timesteps']}")
            print(f"Total experiments: {runner.calculate_stage_experiments(stage_num)}")
        else:
            print("❌ Invalid stage number")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()




