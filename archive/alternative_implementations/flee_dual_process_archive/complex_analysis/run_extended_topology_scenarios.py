#!/usr/bin/env python3
"""
Extended Topology Testing for Dual-Process Hypotheses

This script extends the basic hypothesis testing to include comprehensive
topology robustness testing across all network types.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_hypothesis_scenarios import HypothesisTestingPipeline
from experiment_runner import ExperimentRunner, ExperimentConfig


class ExtendedTopologyTestingPipeline(HypothesisTestingPipeline):
    """
    Extended pipeline that tests each hypothesis across multiple network topologies
    to assess robustness and topology-dependent effects.
    """
    
    def __init__(self, output_dir: str = "extended_topology_results", 
                 max_parallel: int = 4, replications: int = 10):
        """
        Initialize extended topology testing pipeline.
        
        Args:
            output_dir: Base directory for all results
            max_parallel: Maximum parallel experiments
            replications: Number of replications per scenario
        """
        super().__init__(output_dir, max_parallel, replications)
        
        # Extended topology configurations
        self.extended_topologies = {
            'linear': {
                'name': 'Linear Chain',
                'params': {
                    'n_nodes': 5,
                    'segment_distance': 30.0,
                    'start_pop': 8000,
                    'pop_decay': 0.8
                },
                'characteristics': {
                    'connectivity': 0.4,
                    'clustering': 0.0,
                    'path_length': 4.0,
                    'bottlenecks': 'high'
                }
            },
            'star': {
                'name': 'Hub-and-Spoke',
                'params': {
                    'n_camps': 4,
                    'hub_pop': 6000,
                    'camp_capacity': 1200,
                    'radius': 50.0
                },
                'characteristics': {
                    'connectivity': 0.8,
                    'clustering': 0.2,
                    'path_length': 2.0,
                    'bottlenecks': 'central'
                }
            },
            'grid': {
                'name': 'Rectangular Grid',
                'params': {
                    'rows': 3,
                    'cols': 3,
                    'cell_distance': 35.0,
                    'pop_distribution': 'uniform'
                },
                'characteristics': {
                    'connectivity': 0.6,
                    'clustering': 0.4,
                    'path_length': 2.8,
                    'bottlenecks': 'distributed'
                }
            },
            'small_world': {
                'name': 'Small-World Network',
                'params': {
                    'n_nodes': 8,
                    'k_neighbors': 4,
                    'rewiring_prob': 0.3,
                    'base_pop': 4000
                },
                'characteristics': {
                    'connectivity': 0.7,
                    'clustering': 0.6,
                    'path_length': 2.2,
                    'bottlenecks': 'low'
                }
            },
            'scale_free': {
                'name': 'Scale-Free Network',
                'params': {
                    'n_nodes': 8,
                    'preferential_attachment': 2,
                    'hub_pop_multiplier': 3.0,
                    'base_pop': 3000
                },
                'characteristics': {
                    'connectivity': 0.75,
                    'clustering': 0.3,
                    'path_length': 2.5,
                    'bottlenecks': 'hub_dependent'
                }
            }
        }
        
        self.logger.info(f"Extended topology testing initialized with {len(self.extended_topologies)} topology types")
    
    def run_topology_robustness_analysis(self, hypotheses: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run comprehensive topology robustness analysis for all hypotheses.
        
        Args:
            hypotheses: List of hypothesis IDs to test (None for all)
            
        Returns:
            Dictionary with topology robustness results
        """
        if hypotheses is None:
            hypotheses = list(self.hypothesis_configs.keys())
        
        self.logger.info(f"Starting topology robustness analysis for: {hypotheses}")
        
        topology_results = {}
        
        for hypothesis_id in hypotheses:
            self.logger.info(f"Testing hypothesis {hypothesis_id} across all topologies")
            
            hypothesis_topology_results = {}
            
            for topology_type, topology_config in self.extended_topologies.items():
                self.logger.info(f"Running {hypothesis_id} with {topology_config['name']} topology")
                
                try:
                    # Adapt hypothesis to use this topology
                    adapted_config = self._adapt_hypothesis_to_topology(hypothesis_id, topology_type, topology_config)
                    
                    # Run experiments for this hypothesis-topology combination
                    results = self.run_adapted_hypothesis(hypothesis_id, topology_type, adapted_config)
                    
                    hypothesis_topology_results[topology_type] = results
                    
                    self.logger.info(f"Completed {hypothesis_id} with {topology_type} topology")
                    
                except Exception as e:
                    self.logger.error(f"Failed to run {hypothesis_id} with {topology_type}: {e}")
                    hypothesis_topology_results[topology_type] = {'error': str(e)}
            
            # Analyze topology effects for this hypothesis
            topology_analysis = self._analyze_topology_effects(hypothesis_id, hypothesis_topology_results)
            
            topology_results[hypothesis_id] = {
                'topology_results': hypothesis_topology_results,
                'topology_analysis': topology_analysis
            }
        
        # Cross-hypothesis topology analysis
        cross_analysis = self._analyze_cross_hypothesis_topology_effects(topology_results)
        
        # Save comprehensive results
        self._save_topology_robustness_results(topology_results, cross_analysis)
        
        return {
            'hypothesis_topology_results': topology_results,
            'cross_hypothesis_analysis': cross_analysis
        }
    
    def _adapt_hypothesis_to_topology(self, hypothesis_id: str, topology_type: str, 
                                    topology_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt a hypothesis configuration to use a specific topology.
        
        Args:
            hypothesis_id: Hypothesis identifier
            topology_type: Type of topology to use
            topology_config: Topology configuration
            
        Returns:
            Adapted hypothesis configuration
        """
        base_config = self.hypothesis_configs[hypothesis_id].copy()
        
        # Replace topology configuration
        base_config['topology_type'] = topology_type
        base_config['topology_params'] = topology_config['params'].copy()
        
        # Adjust scenario parameters based on topology characteristics
        if topology_type == 'linear':
            # Linear topologies may need adjusted conflict propagation
            if 'cascade_intervals' in base_config['scenario_params']:
                base_config['scenario_params']['cascade_intervals'] = [0, 3, 6, 9, 12]
        
        elif topology_type == 'star':
            # Star topologies concentrate activity at hub
            if 'hub_pop' in topology_config['params']:
                base_config['scenario_params']['origin'] = 'Hub_Center'
        
        elif topology_type == 'grid':
            # Grid topologies may need multiple conflict origins
            if base_config['scenario_type'] == 'cascading_conflict':
                base_config['scenario_params']['origins'] = ['Grid_1_1', 'Grid_2_2']
        
        elif topology_type == 'small_world':
            # Small-world networks enable rapid information spread
            if 'information_lag' in base_config['scenario_params']:
                base_config['scenario_params']['information_lag'] = [0, 2, 4]  # Faster spread
        
        elif topology_type == 'scale_free':
            # Scale-free networks are vulnerable to hub failures
            if base_config['scenario_type'] == 'dynamic_events':
                # Add hub failure event
                events = base_config['scenario_params'].get('event_timeline', [])
                events.append({'day': 45, 'type': 'hub_disruption', 'location': 'SF_Hub1'})
                base_config['scenario_params']['event_timeline'] = events
        
        # Add topology metadata
        base_config['topology_metadata'] = {
            'topology_name': topology_config['name'],
            'characteristics': topology_config['characteristics'],
            'adaptation_notes': f"Adapted {hypothesis_id} for {topology_type} topology"
        }
        
        return base_config
    
    def run_adapted_hypothesis(self, hypothesis_id: str, topology_type: str, 
                             adapted_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a hypothesis with adapted topology configuration.
        
        Args:
            hypothesis_id: Hypothesis identifier
            topology_type: Topology type being tested
            adapted_config: Adapted configuration
            
        Returns:
            Experiment results
        """
        # Generate experiment configurations
        experiment_configs = []
        
        cognitive_modes = adapted_config['cognitive_modes']
        
        for mode in cognitive_modes:
            for rep in range(self.replications):
                experiment_id = f"{hypothesis_id}_{topology_type}_{mode}_rep{rep:02d}"
                
                exp_config = ExperimentConfig(
                    experiment_id=experiment_id,
                    topology_type=adapted_config['topology_type'],
                    topology_params=adapted_config['topology_params'].copy(),
                    scenario_type=adapted_config['scenario_type'],
                    scenario_params=adapted_config['scenario_params'].copy(),
                    cognitive_mode=mode,
                    simulation_params={
                        'max_agents': 8000,
                        'print_progress': False
                    },
                    replications=1,
                    metadata={
                        'hypothesis_id': hypothesis_id,
                        'topology_type': topology_type,
                        'cognitive_mode': mode,
                        'replication': rep,
                        'topology_metadata': adapted_config['topology_metadata']
                    }
                )
                
                experiment_configs.append(exp_config)
        
        # Execute experiments
        experiment_results = self._execute_experiments_parallel(experiment_configs)
        
        # Aggregate results by cognitive mode
        aggregated_results = self._aggregate_results_by_mode(experiment_results, adapted_config)
        
        # Calculate topology-specific metrics
        topology_metrics = self._calculate_topology_specific_metrics(
            hypothesis_id, topology_type, aggregated_results
        )
        
        return {
            'hypothesis_id': hypothesis_id,
            'topology_type': topology_type,
            'config': adapted_config,
            'experiment_results': experiment_results,
            'aggregated_results': aggregated_results,
            'topology_metrics': topology_metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_topology_specific_metrics(self, hypothesis_id: str, topology_type: str,
                                           aggregated_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate metrics specific to topology effects.
        
        Args:
            hypothesis_id: Hypothesis identifier
            topology_type: Topology type
            aggregated_results: Aggregated results by cognitive mode
            
        Returns:
            Topology-specific metrics
        """
        topology_metrics = {
            'topology_type': topology_type,
            'topology_characteristics': self.extended_topologies[topology_type]['characteristics']
        }
        
        # Calculate topology-dependent effects
        if len(aggregated_results) >= 2:
            modes = list(aggregated_results.keys())
            
            # Network utilization efficiency
            network_efficiency = []
            for mode in modes:
                mode_results = aggregated_results[mode]
                if 'metrics' in mode_results:
                    efficiency = mode_results['metrics'].get('network_utilization', 0)
                    network_efficiency.append(efficiency)
            
            if network_efficiency:
                topology_metrics['network_efficiency'] = {
                    'mean': sum(network_efficiency) / len(network_efficiency),
                    'variance': sum((x - sum(network_efficiency)/len(network_efficiency))**2 
                                  for x in network_efficiency) / len(network_efficiency)
                }
            
            # Information flow efficiency (for topologies that support it)
            if topology_type in ['star', 'small_world', 'scale_free']:
                info_flow_metrics = []
                for mode in modes:
                    mode_results = aggregated_results[mode]
                    if 'metrics' in mode_results:
                        flow_rate = mode_results['metrics'].get('information_flow_rate', 0)
                        info_flow_metrics.append(flow_rate)
                
                if info_flow_metrics:
                    topology_metrics['information_flow_efficiency'] = {
                        'mean': sum(info_flow_metrics) / len(info_flow_metrics),
                        'topology_advantage': self._calculate_topology_advantage(
                            topology_type, info_flow_metrics
                        )
                    }
            
            # Bottleneck analysis
            bottleneck_severity = self._analyze_bottleneck_effects(topology_type, aggregated_results)
            topology_metrics['bottleneck_analysis'] = bottleneck_severity
        
        return topology_metrics
    
    def _calculate_topology_advantage(self, topology_type: str, metrics: List[float]) -> float:
        """Calculate topology-specific advantages."""
        baseline = 0.5  # Baseline performance
        
        if topology_type == 'star':
            # Star networks should show centralization advantages
            return (sum(metrics) / len(metrics)) - baseline
        elif topology_type == 'small_world':
            # Small-world networks should show efficiency advantages
            return (sum(metrics) / len(metrics)) - baseline
        elif topology_type == 'scale_free':
            # Scale-free networks should show robustness advantages
            return min(metrics) / baseline if metrics else 0  # Focus on worst-case performance
        else:
            return 0.0
    
    def _analyze_bottleneck_effects(self, topology_type: str, 
                                  aggregated_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bottleneck effects for different topologies."""
        bottleneck_analysis = {
            'topology_type': topology_type,
            'expected_bottlenecks': self.extended_topologies[topology_type]['characteristics']['bottlenecks']
        }
        
        # Extract congestion metrics if available
        congestion_levels = []
        for mode, results in aggregated_results.items():
            if 'metrics' in results:
                congestion = results['metrics'].get('congestion_index', 0)
                congestion_levels.append(congestion)
        
        if congestion_levels:
            bottleneck_analysis['observed_congestion'] = {
                'mean': sum(congestion_levels) / len(congestion_levels),
                'max': max(congestion_levels),
                'severity': 'high' if max(congestion_levels) > 0.7 else 'moderate' if max(congestion_levels) > 0.4 else 'low'
            }
        
        return bottleneck_analysis
    
    def _analyze_topology_effects(self, hypothesis_id: str, 
                                topology_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze how different topologies affect hypothesis outcomes.
        
        Args:
            hypothesis_id: Hypothesis identifier
            topology_results: Results across all topologies
            
        Returns:
            Topology effects analysis
        """
        analysis = {
            'hypothesis_id': hypothesis_id,
            'topology_robustness': {},
            'topology_rankings': {},
            'topology_interactions': {}
        }
        
        # Extract key metrics across topologies
        topology_metrics = {}
        for topology_type, results in topology_results.items():
            if 'error' not in results and 'topology_metrics' in results:
                topology_metrics[topology_type] = results['topology_metrics']
        
        if len(topology_metrics) < 2:
            analysis['insufficient_data'] = True
            return analysis
        
        # Robustness analysis: How consistent are effects across topologies?
        robustness_scores = []
        for topology_type, metrics in topology_metrics.items():
            if 'network_efficiency' in metrics:
                efficiency = metrics['network_efficiency']['mean']
                robustness_scores.append(efficiency)
        
        if robustness_scores:
            analysis['topology_robustness'] = {
                'mean_performance': sum(robustness_scores) / len(robustness_scores),
                'performance_variance': sum((x - sum(robustness_scores)/len(robustness_scores))**2 
                                          for x in robustness_scores) / len(robustness_scores),
                'robustness_score': 1.0 / (1.0 + sum((x - sum(robustness_scores)/len(robustness_scores))**2 
                                                    for x in robustness_scores) / len(robustness_scores))
            }
        
        # Topology rankings: Which topologies work best for this hypothesis?
        if robustness_scores:
            topology_performance = list(zip(topology_metrics.keys(), robustness_scores))
            topology_performance.sort(key=lambda x: x[1], reverse=True)
            
            analysis['topology_rankings'] = {
                'best_topology': topology_performance[0][0],
                'worst_topology': topology_performance[-1][0],
                'performance_ranking': [{'topology': topo, 'score': score} 
                                      for topo, score in topology_performance]
            }
        
        # Topology interactions: How do topology characteristics interact with hypothesis?
        analysis['topology_interactions'] = self._analyze_topology_hypothesis_interactions(
            hypothesis_id, topology_metrics
        )
        
        return analysis
    
    def _analyze_topology_hypothesis_interactions(self, hypothesis_id: str,
                                                topology_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interactions between topology characteristics and hypothesis effects."""
        interactions = {}
        
        # H1: Speed vs Optimality should interact with path complexity
        if hypothesis_id.startswith('H1'):
            interactions['path_complexity_effects'] = {}
            for topology_type, metrics in topology_metrics.items():
                characteristics = self.extended_topologies[topology_type]['characteristics']
                path_length = characteristics['path_length']
                performance = metrics.get('network_efficiency', {}).get('mean', 0)
                interactions['path_complexity_effects'][topology_type] = {
                    'path_length': path_length,
                    'performance': performance,
                    'complexity_penalty': max(0, path_length - 2.0) * 0.1  # Penalty for complex paths
                }
        
        # H2: Connectivity effects should interact with network connectivity
        elif hypothesis_id.startswith('H2'):
            interactions['connectivity_amplification'] = {}
            for topology_type, metrics in topology_metrics.items():
                characteristics = self.extended_topologies[topology_type]['characteristics']
                connectivity = characteristics['connectivity']
                info_flow = metrics.get('information_flow_efficiency', {}).get('mean', 0)
                interactions['connectivity_amplification'][topology_type] = {
                    'base_connectivity': connectivity,
                    'information_flow': info_flow,
                    'amplification_factor': info_flow / connectivity if connectivity > 0 else 0
                }
        
        # H3: Dimensionless parameters should show universal scaling
        elif hypothesis_id.startswith('H3'):
            interactions['scaling_universality'] = {}
            scaling_consistency = []
            for topology_type, metrics in topology_metrics.items():
                performance = metrics.get('network_efficiency', {}).get('mean', 0)
                scaling_consistency.append(performance)
            
            if scaling_consistency:
                interactions['scaling_universality'] = {
                    'mean_scaling': sum(scaling_consistency) / len(scaling_consistency),
                    'scaling_variance': sum((x - sum(scaling_consistency)/len(scaling_consistency))**2 
                                          for x in scaling_consistency) / len(scaling_consistency),
                    'universality_score': 1.0 / (1.0 + sum((x - sum(scaling_consistency)/len(scaling_consistency))**2 
                                                          for x in scaling_consistency) / len(scaling_consistency))
                }
        
        # H4: Population diversity should interact with network structure
        elif hypothesis_id.startswith('H4'):
            interactions['diversity_network_synergy'] = {}
            for topology_type, metrics in topology_metrics.items():
                characteristics = self.extended_topologies[topology_type]['characteristics']
                clustering = characteristics['clustering']
                performance = metrics.get('network_efficiency', {}).get('mean', 0)
                interactions['diversity_network_synergy'][topology_type] = {
                    'clustering_coefficient': clustering,
                    'performance': performance,
                    'synergy_score': performance * clustering  # Higher clustering should amplify diversity benefits
                }
        
        return interactions
    
    def _analyze_cross_hypothesis_topology_effects(self, topology_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze topology effects across all hypotheses."""
        cross_analysis = {
            'universal_topology_effects': {},
            'hypothesis_specific_effects': {},
            'topology_recommendations': {}
        }
        
        # Collect performance data across all hypotheses and topologies
        topology_performance = {}
        for hypothesis_id, results in topology_results.items():
            if 'topology_results' in results:
                for topology_type, topology_result in results['topology_results'].items():
                    if 'error' not in topology_result and 'topology_metrics' in topology_result:
                        if topology_type not in topology_performance:
                            topology_performance[topology_type] = []
                        
                        metrics = topology_result['topology_metrics']
                        performance = metrics.get('network_efficiency', {}).get('mean', 0)
                        topology_performance[topology_type].append(performance)
        
        # Universal effects: Which topologies consistently perform well?
        if topology_performance:
            universal_rankings = []
            for topology_type, performances in topology_performance.items():
                mean_performance = sum(performances) / len(performances)
                performance_consistency = 1.0 / (1.0 + sum((x - mean_performance)**2 for x in performances) / len(performances))
                
                universal_rankings.append({
                    'topology': topology_type,
                    'mean_performance': mean_performance,
                    'consistency': performance_consistency,
                    'overall_score': mean_performance * performance_consistency
                })
            
            universal_rankings.sort(key=lambda x: x['overall_score'], reverse=True)
            cross_analysis['universal_topology_effects'] = {
                'best_overall_topology': universal_rankings[0]['topology'],
                'most_consistent_topology': max(universal_rankings, key=lambda x: x['consistency'])['topology'],
                'topology_rankings': universal_rankings
            }
        
        # Recommendations for different research goals
        cross_analysis['topology_recommendations'] = {
            'for_robustness_testing': 'Use multiple topologies to ensure effects are not topology-dependent',
            'for_maximum_effects': f"Use {cross_analysis.get('universal_topology_effects', {}).get('best_overall_topology', 'star')} topology",
            'for_realistic_scenarios': 'Use small-world or scale-free topologies that match real-world networks',
            'for_controlled_experiments': 'Use linear or grid topologies for clear causal interpretation'
        }
        
        return cross_analysis
    
    def _save_topology_robustness_results(self, topology_results: Dict[str, Any], 
                                        cross_analysis: Dict[str, Any]) -> None:
        """Save comprehensive topology robustness results."""
        # Save main results
        results_file = self.output_dir / "topology_robustness_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'topology_results': topology_results,
                'cross_analysis': cross_analysis,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'topologies_tested': list(self.extended_topologies.keys()),
                    'replications_per_condition': self.replications
                }
            }, f, indent=2, default=str)
        
        # Save summary report
        summary_file = self.output_dir / "topology_robustness_summary.md"
        self._generate_topology_summary_report(topology_results, cross_analysis, summary_file)
        
        self.logger.info(f"Topology robustness results saved to {results_file}")
        self.logger.info(f"Summary report saved to {summary_file}")
    
    def _generate_topology_summary_report(self, topology_results: Dict[str, Any],
                                        cross_analysis: Dict[str, Any], 
                                        output_file: Path) -> None:
        """Generate human-readable summary report."""
        with open(output_file, 'w') as f:
            f.write("# Topology Robustness Analysis Summary\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Universal effects
            if 'universal_topology_effects' in cross_analysis:
                universal = cross_analysis['universal_topology_effects']
                f.write("## Universal Topology Effects\n\n")
                f.write(f"**Best Overall Topology**: {universal.get('best_overall_topology', 'N/A')}\n")
                f.write(f"**Most Consistent Topology**: {universal.get('most_consistent_topology', 'N/A')}\n\n")
                
                f.write("### Topology Rankings\n\n")
                for ranking in universal.get('topology_rankings', []):
                    f.write(f"- **{ranking['topology']}**: Performance={ranking['mean_performance']:.3f}, "
                           f"Consistency={ranking['consistency']:.3f}\n")
                f.write("\n")
            
            # Hypothesis-specific effects
            f.write("## Hypothesis-Specific Topology Effects\n\n")
            for hypothesis_id, results in topology_results.items():
                if 'topology_analysis' in results:
                    analysis = results['topology_analysis']
                    f.write(f"### {hypothesis_id}\n\n")
                    
                    if 'topology_rankings' in analysis:
                        rankings = analysis['topology_rankings']
                        f.write(f"**Best Topology**: {rankings.get('best_topology', 'N/A')}\n")
                        f.write(f"**Worst Topology**: {rankings.get('worst_topology', 'N/A')}\n")
                    
                    if 'topology_robustness' in analysis:
                        robustness = analysis['topology_robustness']
                        f.write(f"**Robustness Score**: {robustness.get('robustness_score', 0):.3f}\n")
                    
                    f.write("\n")
            
            # Recommendations
            if 'topology_recommendations' in cross_analysis:
                f.write("## Recommendations\n\n")
                recommendations = cross_analysis['topology_recommendations']
                for goal, recommendation in recommendations.items():
                    f.write(f"**{goal.replace('_', ' ').title()}**: {recommendation}\n")


def main():
    """Main function for extended topology testing."""
    parser = argparse.ArgumentParser(description='Extended Topology Testing for Dual-Process Hypotheses')
    parser.add_argument('--hypotheses', nargs='+', help='Specific hypotheses to test (e.g., H1.1 H2.1)')
    parser.add_argument('--replications', type=int, default=5, help='Number of replications per condition')
    parser.add_argument('--max-parallel', type=int, default=4, help='Maximum parallel processes')
    parser.add_argument('--output-dir', default='extended_topology_results', help='Output directory')
    
    args = parser.parse_args()
    
    print("🌐 Extended Topology Testing for Dual-Process Hypotheses")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = ExtendedTopologyTestingPipeline(
        output_dir=args.output_dir,
        max_parallel=args.max_parallel,
        replications=args.replications
    )
    
    # Run topology robustness analysis
    start_time = time.time()
    
    results = pipeline.run_topology_robustness_analysis(hypotheses=args.hypotheses)
    
    elapsed = time.time() - start_time
    
    print("=" * 60)
    print(f"✅ Extended topology testing complete! ({elapsed:.1f}s)")
    print(f"📁 Results saved to: {args.output_dir}")
    
    # Print summary
    if 'cross_hypothesis_analysis' in results:
        cross_analysis = results['cross_hypothesis_analysis']
        if 'universal_topology_effects' in cross_analysis:
            universal = cross_analysis['universal_topology_effects']
            print(f"\n🏆 Best Overall Topology: {universal.get('best_overall_topology', 'N/A')}")
            print(f"🎯 Most Consistent Topology: {universal.get('most_consistent_topology', 'N/A')}")
    
    print("\n🎯 Ready for comprehensive dual-process analysis!")


if __name__ == "__main__":
    main()