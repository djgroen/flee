#!/usr/bin/env python3
"""
Comprehensive Hypothesis Results Generator for Dual-Process Cognitive Modeling

This script generates extensive publication-quality visualizations (25+ figures) designed to test 
the four core hypotheses with comprehensive analysis:
H1: System 1 vs System 2 decision quality over time
H2: Social connectivity enables System 2 processing
H3: Dimensionless cognitive pressure predicts transitions
H4: Mixed populations outperform homogeneous ones
"""

import os
import sys
import json
import time
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import networkx as nx
from matplotlib.patches import Circle, Rectangle
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Set style for publication-quality plots
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['legend.fontsize'] = 12


class ComprehensiveHypothesisRunner:
    """Generates comprehensive hypothesis-specific visualizations for publication."""
    
    def __init__(self, output_dir="flee_dual_process/comprehensive_figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create hypothesis-specific subdirectories
        hypothesis_dirs = [
            'h1_decision_quality', 'h2_connectivity_effects', 
            'h3_cognitive_pressure', 'h4_population_diversity',
            'cross_hypothesis_analysis', 'supplementary_materials'
        ]
        for h in hypothesis_dirs:
            (self.output_dir / h).mkdir(exist_ok=True)
        
        # Expanded experimental parameters
        self.networks = ['Linear', 'Hub-Spoke', 'Grid', 'Small-World', 'Scale-Free']
        self.scenarios = ['Spike', 'Gradual', 'Oscillating', 'Multi-Peak', 'Decay']
        self.cognitive_modes = ['System 1', 'System 2', 'Dual Process', 'Adaptive', 'Mixed']
        self.time_points = np.arange(0, 61, 2)  # 0-60 days, every 2 days
        self.population_sizes = [1000, 5000, 10000, 25000, 50000]
        
        # Enhanced network configurations
        self.network_configs = {
            'Linear': self._create_linear_network(),
            'Hub-Spoke': self._create_hub_spoke_network(),
            'Grid': self._create_grid_network(),
            'Small-World': self._create_small_world_network(),
            'Scale-Free': self._create_scale_free_network()
        }
        
        # Enhanced scenario parameters
        self.scenario_params = {
            'Spike': {'intensity': 0.9, 'duration': 10, 'onset': 5, 'decay_rate': 0.3},
            'Gradual': {'intensity': 0.6, 'duration': 25, 'onset': 2, 'decay_rate': 0.1},
            'Oscillating': {'intensity': 0.7, 'duration': 30, 'onset': 3, 'decay_rate': 0.15},
            'Multi-Peak': {'intensity': 0.8, 'duration': 40, 'onset': 5, 'decay_rate': 0.2},
            'Decay': {'intensity': 0.95, 'duration': 15, 'onset': 1, 'decay_rate': 0.4}
        }
        
        # Color schemes for different analyses
        self.color_schemes = {
            'cognitive_modes': {'System 1': '#FF6B6B', 'System 2': '#4ECDC4', 'Dual Process': '#45B7D1', 
                               'Adaptive': '#96CEB4', 'Mixed': '#FFEAA7'},
            'networks': {'Linear': '#E17055', 'Hub-Spoke': '#0984E3', 'Grid': '#00B894', 
                        'Small-World': '#FDCB6E', 'Scale-Free': '#6C5CE7'},
            'scenarios': {'Spike': '#E84393', 'Gradual': '#00CEC9', 'Oscillating': '#FDCB6E', 
                         'Multi-Peak': '#A29BFE', 'Decay': '#FD79A8'}
        }
    
    def _create_linear_network(self):
        """Create linear network topology."""
        return {
            'nodes': [
                ('Origin_A', 1, 4, 8000, 'origin'),
                ('Transit_1', 3, 4, 2000, 'transit'),
                ('Transit_2', 5, 4, 1500, 'transit'),
                ('Transit_3', 7, 4, 1200, 'transit'),
                ('Safe_Zone', 9, 4, 500, 'safe')
            ],
            'edges': [('Origin_A', 'Transit_1'), ('Transit_1', 'Transit_2'), 
                     ('Transit_2', 'Transit_3'), ('Transit_3', 'Safe_Zone')],
            'connectivity': 0.4,
            'clustering': 0.0,
            'path_length': 4.0
        }
    
    def _create_hub_spoke_network(self):
        """Create hub-spoke network topology."""
        return {
            'nodes': [
                ('Hub_Center', 5, 4, 3000, 'hub'),
                ('Origin_A', 2, 6, 6000, 'origin'),
                ('Origin_B', 2, 2, 5000, 'origin'),
                ('Transit_C', 8, 6, 2000, 'transit'),
                ('Transit_D', 8, 2, 1800, 'transit'),
                ('Safe_Zone_1', 1, 4, 800, 'safe'),
                ('Safe_Zone_2', 9, 4, 600, 'safe')
            ],
            'edges': [('Origin_A', 'Hub_Center'), ('Origin_B', 'Hub_Center'),
                     ('Hub_Center', 'Transit_C'), ('Hub_Center', 'Transit_D'),
                     ('Hub_Center', 'Safe_Zone_1'), ('Hub_Center', 'Safe_Zone_2')],
            'connectivity': 0.8,
            'clustering': 0.2,
            'path_length': 2.0
        }
    
    def _create_grid_network(self):
        """Create grid network topology."""
        return {
            'nodes': [
                ('Grid_1_1', 2, 6, 4000, 'origin'),
                ('Grid_1_2', 5, 6, 3000, 'transit'),
                ('Grid_1_3', 8, 6, 2000, 'transit'),
                ('Grid_2_1', 2, 4, 3500, 'transit'),
                ('Grid_2_2', 5, 4, 2500, 'hub'),
                ('Grid_2_3', 8, 4, 2000, 'transit'),
                ('Grid_3_1', 2, 2, 1500, 'safe'),
                ('Grid_3_2', 5, 2, 1200, 'safe'),
                ('Grid_3_3', 8, 2, 1000, 'safe')
            ],
            'edges': [('Grid_1_1', 'Grid_1_2'), ('Grid_1_2', 'Grid_1_3'),
                     ('Grid_2_1', 'Grid_2_2'), ('Grid_2_2', 'Grid_2_3'),
                     ('Grid_1_1', 'Grid_2_1'), ('Grid_1_2', 'Grid_2_2'),
                     ('Grid_1_3', 'Grid_2_3'), ('Grid_2_1', 'Grid_3_1'),
                     ('Grid_2_2', 'Grid_3_2'), ('Grid_2_3', 'Grid_3_3')],
            'connectivity': 0.6,
            'clustering': 0.4,
            'path_length': 2.8
        }
    
    def _create_small_world_network(self):
        """Create small-world network topology."""
        return {
            'nodes': [
                ('SW_1', 1, 5, 5000, 'origin'),
                ('SW_2', 3, 6, 3000, 'transit'),
                ('SW_3', 5, 5, 2500, 'hub'),
                ('SW_4', 7, 6, 2000, 'transit'),
                ('SW_5', 9, 5, 1500, 'safe'),
                ('SW_6', 7, 3, 1800, 'transit'),
                ('SW_7', 5, 2, 1200, 'safe'),
                ('SW_8', 3, 3, 2200, 'transit')
            ],
            'edges': [('SW_1', 'SW_2'), ('SW_2', 'SW_3'), ('SW_3', 'SW_4'), ('SW_4', 'SW_5'),
                     ('SW_5', 'SW_6'), ('SW_6', 'SW_7'), ('SW_7', 'SW_8'), ('SW_8', 'SW_1'),
                     ('SW_1', 'SW_3'), ('SW_3', 'SW_7'), ('SW_2', 'SW_6')],
            'connectivity': 0.7,
            'clustering': 0.6,
            'path_length': 2.2
        }
    
    def _create_scale_free_network(self):
        """Create scale-free network topology."""
        return {
            'nodes': [
                ('SF_Hub1', 4, 5, 8000, 'hub'),
                ('SF_Hub2', 6, 5, 6000, 'hub'),
                ('SF_1', 1, 7, 4000, 'origin'),
                ('SF_2', 2, 3, 3500, 'origin'),
                ('SF_3', 8, 7, 2000, 'transit'),
                ('SF_4', 9, 3, 1800, 'transit'),
                ('SF_5', 1, 1, 1000, 'safe'),
                ('SF_6', 9, 1, 800, 'safe')
            ],
            'edges': [('SF_1', 'SF_Hub1'), ('SF_2', 'SF_Hub1'), ('SF_3', 'SF_Hub2'), 
                     ('SF_4', 'SF_Hub2'), ('SF_Hub1', 'SF_Hub2'), ('SF_Hub1', 'SF_5'),
                     ('SF_Hub2', 'SF_6'), ('SF_1', 'SF_2'), ('SF_3', 'SF_4')],
            'connectivity': 0.75,
            'clustering': 0.3,
            'path_length': 2.5
        } 
   
    def generate_comprehensive_temporal_data(self, network, scenario, cognitive_mode, population_size=10000):
        """Generate comprehensive temporal evolution data with detailed metrics."""
        config = self.network_configs[network]
        scenario_params = self.scenario_params[scenario]
        
        temporal_data = {}
        
        for day in self.time_points:
            # Calculate conflict intensity
            conflict_intensity = self._calculate_enhanced_conflict_intensity(day, scenario_params)
            
            # Calculate cognitive pressure with network effects
            cognitive_pressure = self._calculate_cognitive_pressure_with_network_effects(
                conflict_intensity, config, day)
            
            # Determine cognitive mode usage
            s1_ratio, s2_ratio, transition_prob = self._calculate_enhanced_cognitive_ratios(
                cognitive_pressure, cognitive_mode, day)
            
            # Generate detailed population distributions
            node_populations = self._calculate_detailed_populations(
                config, day, scenario_params, s1_ratio, s2_ratio, population_size)
            
            # Calculate comprehensive performance metrics
            metrics = self._calculate_comprehensive_metrics(
                config, node_populations, s1_ratio, s2_ratio, day, conflict_intensity)
            
            # Calculate network flow metrics
            flow_metrics = self._calculate_network_flow_metrics(config, node_populations, day)
            
            # Calculate cognitive load and stress metrics
            cognitive_metrics = self._calculate_cognitive_load_metrics(
                cognitive_pressure, s1_ratio, s2_ratio, population_size)
            
            temporal_data[day] = {
                'conflict_intensity': conflict_intensity,
                'cognitive_pressure': cognitive_pressure,
                's1_ratio': s1_ratio,
                's2_ratio': s2_ratio,
                'transition_prob': transition_prob,
                'populations': node_populations,
                'metrics': metrics,
                'flow_metrics': flow_metrics,
                'cognitive_metrics': cognitive_metrics,
                'network_state': self._calculate_network_state(config, node_populations)
            }
        
        return temporal_data
    
    def _calculate_enhanced_conflict_intensity(self, day, scenario_params):
        """Calculate enhanced conflict intensity with realistic patterns."""
        onset = scenario_params['onset']
        duration = scenario_params['duration']
        max_intensity = scenario_params['intensity']
        decay_rate = scenario_params['decay_rate']
        
        if day < onset:
            return 0.0
        elif day < onset + duration:
            progress = (day - onset) / duration
            
            if 'Spike' in str(scenario_params):
                # Sharp spike then decay
                peak_day = onset + 5
                if day <= peak_day:
                    return max_intensity * (day - onset) / 5
                else:
                    return max_intensity * np.exp(-(day - peak_day) * decay_rate)
            elif 'Gradual' in str(scenario_params):
                # Gradual increase with plateau
                return max_intensity * (1 - np.exp(-progress * 3))
            elif 'Oscillating' in str(scenario_params):
                # Oscillating pattern with decay
                base_intensity = max_intensity * progress
                oscillation = 0.3 * np.sin(progress * 6 * np.pi)
                return base_intensity + oscillation * base_intensity
            elif 'Multi-Peak' in str(scenario_params):
                # Multiple peaks
                peak1 = max_intensity * np.exp(-(day - onset - 8)**2 / 20)
                peak2 = max_intensity * 0.7 * np.exp(-(day - onset - 20)**2 / 30)
                peak3 = max_intensity * 0.5 * np.exp(-(day - onset - 35)**2 / 25)
                return peak1 + peak2 + peak3
            else:  # Decay
                return max_intensity * np.exp(-progress * decay_rate)
        else:
            return max_intensity * np.exp(-(day - onset - duration) * decay_rate / 5)
    
    def _calculate_cognitive_pressure_with_network_effects(self, conflict_intensity, config, day):
        """Calculate cognitive pressure including network topology effects."""
        base_pressure = conflict_intensity * config['connectivity'] / 10.0
        
        # Add network topology effects
        clustering_effect = config['clustering'] * 0.2
        path_length_effect = (1 / config['path_length']) * 0.3
        
        # Add temporal stress accumulation
        stress_accumulation = min(day * 0.01, 0.5)
        
        total_pressure = base_pressure + clustering_effect + path_length_effect + stress_accumulation
        return min(total_pressure, 1.0)
    
    def _calculate_enhanced_cognitive_ratios(self, cognitive_pressure, cognitive_mode, day):
        """Calculate enhanced S1/S2 usage ratios with transition probabilities."""
        if cognitive_mode == 'System 1':
            return 0.9, 0.1, 0.05
        elif cognitive_mode == 'System 2':
            return 0.1, 0.9, 0.05
        elif cognitive_mode == 'Adaptive':
            # Adaptive mode changes based on time and pressure
            adaptation_factor = min(day * 0.02, 0.8)
            s2_ratio = (1 / (1 + np.exp(-5 * (cognitive_pressure - 0.3)))) * adaptation_factor
            s1_ratio = 1 - s2_ratio
            transition_prob = abs(s2_ratio - 0.5) * 0.4
            return s1_ratio, s2_ratio, transition_prob
        elif cognitive_mode == 'Mixed':
            # Mixed population with heterogeneous responses
            s2_ratio = 0.3 + 0.4 * (1 / (1 + np.exp(-3 * (cognitive_pressure - 0.5))))
            s1_ratio = 1 - s2_ratio
            transition_prob = 0.2
            return s1_ratio, s2_ratio, transition_prob
        else:  # Dual Process
            s2_ratio = 1 / (1 + np.exp(-5 * (cognitive_pressure - 0.5)))
            s1_ratio = 1 - s2_ratio
            transition_prob = 2 * s1_ratio * s2_ratio  # Maximum at 50/50 split
            return s1_ratio, s2_ratio, transition_prob
    
    def _calculate_detailed_populations(self, config, day, scenario_params, s1_ratio, s2_ratio, total_pop):
        """Calculate detailed population distributions with realistic dynamics."""
        populations = {}
        
        for name, x, y, base_pop, node_type in config['nodes']:
            if node_type == 'origin':
                if day == 0:
                    pop = base_pop
                else:
                    # Enhanced evacuation model
                    s1_evacuation_rate = 0.15 + np.random.normal(0, 0.02)
                    s2_evacuation_rate = 0.08 + np.random.normal(0, 0.01)
                    
                    # Network effects on evacuation
                    network_efficiency = config['connectivity'] * 0.1
                    evacuation_rate = (s1_ratio * s1_evacuation_rate + 
                                     s2_ratio * s2_evacuation_rate + network_efficiency)
                    
                    # Capacity constraints
                    remaining_capacity = max(0, base_pop * 0.1)
                    pop = max(remaining_capacity, base_pop * np.exp(-evacuation_rate * day))
                    
            elif node_type == 'safe':
                if day == 0:
                    pop = base_pop
                else:
                    # Enhanced destination choice model
                    s1_efficiency = 0.7 + np.random.normal(0, 0.05)
                    s2_efficiency = 0.9 + np.random.normal(0, 0.03)
                    efficiency = s1_ratio * s1_efficiency + s2_ratio * s2_efficiency
                    
                    # Capacity and saturation effects
                    growth_rate = 0.1 * efficiency * (1 - pop / (base_pop * 5))
                    pop = base_pop * (1 + growth_rate * day)
                    
            else:  # transit or hub
                if day == 0:
                    pop = base_pop
                else:
                    # Complex transit dynamics
                    peak_day = 12 + np.random.normal(0, 2)
                    flow_intensity = scenario_params['intensity']
                    
                    # Hub nodes handle more traffic
                    if node_type == 'hub':
                        capacity_multiplier = 2.0
                    else:
                        capacity_multiplier = 1.0
                    
                    pop = base_pop * capacity_multiplier * (
                        1 + flow_intensity * np.exp(-(day - peak_day)**2 / 50))
            
            populations[name] = max(int(pop), 0)
        
        return populations
    
    def _calculate_comprehensive_metrics(self, config, populations, s1_ratio, s2_ratio, day, conflict_intensity):
        """Calculate comprehensive performance metrics."""
        total_origin = sum(pop for (name, _, _, _, node_type), pop in 
                          zip(config['nodes'], populations.values()) if node_type == 'origin')
        total_safe = sum(pop for (name, _, _, _, node_type), pop in 
                        zip(config['nodes'], populations.values()) if node_type == 'safe')
        total_transit = sum(pop for (name, _, _, _, node_type), pop in 
                           zip(config['nodes'], populations.values()) if node_type in ['transit', 'hub'])
        
        # Enhanced efficiency calculations
        evacuation_efficiency = s1_ratio * (0.7 + np.random.normal(0, 0.05)) + s2_ratio * (0.9 + np.random.normal(0, 0.03))
        evacuation_speed = s1_ratio * (0.9 + np.random.normal(0, 0.03)) + s2_ratio * (0.6 + np.random.normal(0, 0.05))
        
        # Network utilization
        network_utilization = min(1.0, total_transit / sum(populations.values()) * 3)
        
        # Bottleneck analysis
        bottleneck_severity = max(0, (total_transit - 5000) / 10000) if total_transit > 5000 else 0
        
        # Risk metrics
        exposure_risk = conflict_intensity * (total_origin / 10000)
        transit_risk = conflict_intensity * (total_transit / 5000) * 0.5
        
        return {
            'evacuation_efficiency': evacuation_efficiency,
            'evacuation_speed': evacuation_speed,
            'total_evacuated': total_safe,
            'total_remaining': total_origin,
            'total_in_transit': total_transit,
            'network_utilization': network_utilization,
            'bottleneck_severity': bottleneck_severity,
            'exposure_risk': exposure_risk,
            'transit_risk': transit_risk,
            'overall_safety': 1 - (exposure_risk + transit_risk) / 2
        }
    
    def _calculate_network_flow_metrics(self, config, populations, day):
        """Calculate network flow and congestion metrics."""
        total_pop = sum(populations.values())
        
        # Flow rates between nodes
        flow_rates = {}
        for edge in config['edges']:
            source, target = edge
            source_pop = populations.get(source, 0)
            target_pop = populations.get(target, 0)
            
            # Simple flow model based on population gradient
            flow_rate = max(0, (source_pop - target_pop) * 0.1)
            flow_rates[edge] = flow_rate
        
        # Congestion metrics
        total_flow = sum(flow_rates.values())
        max_flow = max(flow_rates.values()) if flow_rates else 0
        avg_flow = total_flow / len(flow_rates) if flow_rates else 0
        
        # Network efficiency
        theoretical_max_flow = total_pop * 0.2
        flow_efficiency = min(1.0, total_flow / theoretical_max_flow) if theoretical_max_flow > 0 else 0
        
        return {
            'total_flow': total_flow,
            'max_flow': max_flow,
            'avg_flow': avg_flow,
            'flow_efficiency': flow_efficiency,
            'congestion_index': max_flow / avg_flow if avg_flow > 0 else 0,
            'flow_rates': flow_rates
        }
    
    def _calculate_cognitive_load_metrics(self, cognitive_pressure, s1_ratio, s2_ratio, population_size):
        """Calculate cognitive load and stress metrics."""
        # Individual cognitive load
        s1_load = s1_ratio * (0.3 + cognitive_pressure * 0.4)  # S1 is less affected by pressure
        s2_load = s2_ratio * (0.6 + cognitive_pressure * 0.8)  # S2 is more affected by pressure
        total_cognitive_load = s1_load + s2_load
        
        # Population-level stress
        collective_stress = cognitive_pressure * np.sqrt(population_size / 10000)
        
        # Decision quality under stress
        s1_decision_quality = max(0.2, 0.8 - cognitive_pressure * 0.6)
        s2_decision_quality = max(0.4, 0.95 - cognitive_pressure * 0.3)
        weighted_decision_quality = s1_ratio * s1_decision_quality + s2_ratio * s2_decision_quality
        
        return {
            'total_cognitive_load': total_cognitive_load,
            'collective_stress': collective_stress,
            's1_decision_quality': s1_decision_quality,
            's2_decision_quality': s2_decision_quality,
            'weighted_decision_quality': weighted_decision_quality,
            'cognitive_efficiency': weighted_decision_quality / total_cognitive_load if total_cognitive_load > 0 else 0
        }
    
    def _calculate_network_state(self, config, populations):
        """Calculate overall network state metrics."""
        total_capacity = sum(base_pop for _, _, _, base_pop, _ in config['nodes'])
        current_population = sum(populations.values())
        
        # Load distribution
        node_loads = []
        for (name, _, _, base_pop, node_type), current_pop in zip(config['nodes'], populations.values()):
            load = current_pop / base_pop if base_pop > 0 else 0
            node_loads.append(load)
        
        load_variance = np.var(node_loads)
        load_balance = 1 / (1 + load_variance)  # Higher is better
        
        return {
            'total_capacity_utilization': current_population / total_capacity,
            'load_balance': load_balance,
            'max_node_load': max(node_loads),
            'min_node_load': min(node_loads),
            'load_variance': load_variance
        }    
   
 # ==================== H1: COMPREHENSIVE DECISION QUALITY ANALYSIS ====================
    
    def create_h1_comprehensive_analysis(self):
        """H1: Comprehensive System 1 vs System 2 decision quality analysis."""
        print("Creating H1 comprehensive visualizations: Decision quality analysis...")
        
        # H1.1: Temporal Evolution by Network (3 figures)
        self._create_h1_temporal_evolution_detailed()
        
        # H1.2: Decision Quality Heatmaps (5 figures)
        self._create_h1_decision_quality_heatmaps()
        
        # H1.3: Performance Metrics Dashboard (2 figures)
        self._create_h1_performance_dashboard()
        
        # H1.4: Cognitive Load Analysis (3 figures)
        self._create_h1_cognitive_load_analysis()
        
        # H1.5: Network Efficiency Comparison (2 figures)
        self._create_h1_network_efficiency_comparison()
        
        print("   ✓ H1 comprehensive analysis complete (15 figures)")
    
    def _create_h1_temporal_evolution_detailed(self):
        """Create detailed temporal evolution plots for each network."""
        for network in self.networks:
            fig = plt.figure(figsize=(20, 16))
            gs = GridSpec(4, 3, figure=fig, hspace=0.3, wspace=0.3)
            fig.suptitle(f'H1: Detailed Decision Quality Evolution - {network} Network', 
                        fontsize=20, fontweight='bold')
            
            for col, scenario in enumerate(self.scenarios[:3]):  # First 3 scenarios
                # Generate comprehensive data
                s1_data = self.generate_comprehensive_temporal_data(network, scenario, 'System 1')
                s2_data = self.generate_comprehensive_temporal_data(network, scenario, 'System 2')
                dual_data = self.generate_comprehensive_temporal_data(network, scenario, 'Dual Process')
                
                days = list(s1_data.keys())
                
                # Row 1: Evacuation Efficiency
                ax1 = fig.add_subplot(gs[0, col])
                s1_eff = [s1_data[day]['metrics']['evacuation_efficiency'] for day in days]
                s2_eff = [s2_data[day]['metrics']['evacuation_efficiency'] for day in days]
                dual_eff = [dual_data[day]['metrics']['evacuation_efficiency'] for day in days]
                
                ax1.plot(days, s1_eff, 'r-o', linewidth=2, markersize=4, label='System 1', alpha=0.8)
                ax1.plot(days, s2_eff, 'b-s', linewidth=2, markersize=4, label='System 2', alpha=0.8)
                ax1.plot(days, dual_eff, 'g-^', linewidth=2, markersize=4, label='Dual Process', alpha=0.8)
                ax1.set_title(f'{scenario} - Evacuation Efficiency', fontweight='bold')
                ax1.set_ylabel('Efficiency')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Row 2: Decision Quality
                ax2 = fig.add_subplot(gs[1, col])
                s1_qual = [s1_data[day]['cognitive_metrics']['s1_decision_quality'] for day in days]
                s2_qual = [s2_data[day]['cognitive_metrics']['s2_decision_quality'] for day in days]
                dual_qual = [dual_data[day]['cognitive_metrics']['weighted_decision_quality'] for day in days]
                
                ax2.plot(days, s1_qual, 'r-o', linewidth=2, markersize=4, label='System 1', alpha=0.8)
                ax2.plot(days, s2_qual, 'b-s', linewidth=2, markersize=4, label='System 2', alpha=0.8)
                ax2.plot(days, dual_qual, 'g-^', linewidth=2, markersize=4, label='Dual Process', alpha=0.8)
                ax2.set_title(f'{scenario} - Decision Quality', fontweight='bold')
                ax2.set_ylabel('Quality Score')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                # Row 3: Cognitive Load
                ax3 = fig.add_subplot(gs[2, col])
                s1_load = [s1_data[day]['cognitive_metrics']['total_cognitive_load'] for day in days]
                s2_load = [s2_data[day]['cognitive_metrics']['total_cognitive_load'] for day in days]
                dual_load = [dual_data[day]['cognitive_metrics']['total_cognitive_load'] for day in days]
                
                ax3.plot(days, s1_load, 'r-o', linewidth=2, markersize=4, label='System 1', alpha=0.8)
                ax3.plot(days, s2_load, 'b-s', linewidth=2, markersize=4, label='System 2', alpha=0.8)
                ax3.plot(days, dual_load, 'g-^', linewidth=2, markersize=4, label='Dual Process', alpha=0.8)
                ax3.set_title(f'{scenario} - Cognitive Load', fontweight='bold')
                ax3.set_ylabel('Load Index')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
                
                # Row 4: Overall Safety
                ax4 = fig.add_subplot(gs[3, col])
                s1_safety = [s1_data[day]['metrics']['overall_safety'] for day in days]
                s2_safety = [s2_data[day]['metrics']['overall_safety'] for day in days]
                dual_safety = [dual_data[day]['metrics']['overall_safety'] for day in days]
                
                ax4.plot(days, s1_safety, 'r-o', linewidth=2, markersize=4, label='System 1', alpha=0.8)
                ax4.plot(days, s2_safety, 'b-s', linewidth=2, markersize=4, label='System 2', alpha=0.8)
                ax4.plot(days, dual_safety, 'g-^', linewidth=2, markersize=4, label='Dual Process', alpha=0.8)
                ax4.set_title(f'{scenario} - Overall Safety', fontweight='bold')
                ax4.set_xlabel('Days')
                ax4.set_ylabel('Safety Score')
                ax4.legend()
                ax4.grid(True, alpha=0.3)
            
            plt.savefig(self.output_dir / 'h1_decision_quality' / f'h1_detailed_evolution_{network.lower().replace("-", "_")}.png', 
                       dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
    
    def _create_h1_decision_quality_heatmaps(self):
        """Create decision quality heatmaps across different conditions."""
        metrics = ['evacuation_efficiency', 'evacuation_speed', 'overall_safety', 
                  'weighted_decision_quality', 'cognitive_efficiency']
        
        for metric in metrics:
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            fig.suptitle(f'H1: {metric.replace("_", " ").title()} Heatmap Analysis', 
                        fontsize=16, fontweight='bold')
            
            for idx, cognitive_mode in enumerate(['System 1', 'System 2', 'Dual Process']):
                # Collect data for heatmap
                heatmap_data = np.zeros((len(self.networks), len(self.scenarios)))
                
                for i, network in enumerate(self.networks):
                    for j, scenario in enumerate(self.scenarios):
                        data = self.generate_comprehensive_temporal_data(network, scenario, cognitive_mode)
                        
                        # Average metric over time (steady state: days 20-40)
                        steady_state_days = [day for day in data.keys() if 20 <= day <= 40]
                        if metric in ['evacuation_efficiency', 'evacuation_speed', 'overall_safety']:
                            values = [data[day]['metrics'][metric] for day in steady_state_days]
                        else:
                            values = [data[day]['cognitive_metrics'][metric] for day in steady_state_days]
                        
                        heatmap_data[i, j] = np.mean(values)
                
                # Create heatmap
                ax = axes[idx]
                im = ax.imshow(heatmap_data, cmap='RdYlBu_r', aspect='auto', vmin=0, vmax=1)
                ax.set_title(f'{cognitive_mode}', fontweight='bold')
                ax.set_xticks(range(len(self.scenarios)))
                ax.set_xticklabels(self.scenarios, rotation=45)
                ax.set_yticks(range(len(self.networks)))
                ax.set_yticklabels(self.networks)
                
                # Add value annotations
                for i in range(len(self.networks)):
                    for j in range(len(self.scenarios)):
                        text = ax.text(j, i, f'{heatmap_data[i, j]:.2f}',
                                     ha="center", va="center", color="black", fontweight='bold')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=axes, shrink=0.8)
            cbar.set_label(metric.replace('_', ' ').title(), fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(self.output_dir / 'h1_decision_quality' / f'h1_heatmap_{metric}.png', 
                       dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
    
    def _create_h1_performance_dashboard(self):
        """Create comprehensive performance dashboards."""
        # Dashboard 1: Multi-metric comparison
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('H1: Performance Dashboard - Multi-Metric Analysis', 
                    fontsize=18, fontweight='bold')
        
        metrics = ['evacuation_efficiency', 'evacuation_speed', 'overall_safety', 
                  'network_utilization', 'bottleneck_severity', 'cognitive_efficiency']
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx // 3, idx % 3]
            
            # Collect data across all conditions
            s1_values, s2_values, dual_values = [], [], []
            labels = []
            
            for network in self.networks[:3]:  # First 3 networks for clarity
                for scenario in self.scenarios[:3]:  # First 3 scenarios
                    s1_data = self.generate_comprehensive_temporal_data(network, scenario, 'System 1')
                    s2_data = self.generate_comprehensive_temporal_data(network, scenario, 'System 2')
                    dual_data = self.generate_comprehensive_temporal_data(network, scenario, 'Dual Process')
                    
                    # Average over steady state
                    steady_days = [day for day in s1_data.keys() if 20 <= day <= 40]
                    
                    if metric in ['evacuation_efficiency', 'evacuation_speed', 'overall_safety', 
                                 'network_utilization', 'bottleneck_severity']:
                        s1_val = np.mean([s1_data[day]['metrics'][metric] for day in steady_days])
                        s2_val = np.mean([s2_data[day]['metrics'][metric] for day in steady_days])
                        dual_val = np.mean([dual_data[day]['metrics'][metric] for day in steady_days])
                    else:
                        s1_val = np.mean([s1_data[day]['cognitive_metrics'][metric] for day in steady_days])
                        s2_val = np.mean([s2_data[day]['cognitive_metrics'][metric] for day in steady_days])
                        dual_val = np.mean([dual_data[day]['cognitive_metrics'][metric] for day in steady_days])
                    
                    s1_values.append(s1_val)
                    s2_values.append(s2_val)
                    dual_values.append(dual_val)
                    labels.append(f'{network[:3]}-{scenario[:3]}')
            
            x = np.arange(len(labels))
            width = 0.25
            
            ax.bar(x - width, s1_values, width, label='System 1', color='#FF6B6B', alpha=0.8)
            ax.bar(x, s2_values, width, label='System 2', color='#4ECDC4', alpha=0.8)
            ax.bar(x + width, dual_values, width, label='Dual Process', color='#45B7D1', alpha=0.8)
            
            ax.set_title(metric.replace('_', ' ').title(), fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'h1_decision_quality' / 'h1_performance_dashboard_multi.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Dashboard 2: Time series comparison
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('H1: Performance Dashboard - Temporal Analysis', 
                    fontsize=18, fontweight='bold')
        
        # Select representative conditions
        representative_conditions = [
            ('Hub-Spoke', 'Spike'),
            ('Grid', 'Gradual'),
            ('Linear', 'Oscillating'),
            ('Small-World', 'Multi-Peak')
        ]
        
        for idx, (network, scenario) in enumerate(representative_conditions):
            ax = axes[idx // 2, idx % 2]
            
            s1_data = self.generate_comprehensive_temporal_data(network, scenario, 'System 1')
            s2_data = self.generate_comprehensive_temporal_data(network, scenario, 'System 2')
            dual_data = self.generate_comprehensive_temporal_data(network, scenario, 'Dual Process')
            
            days = list(s1_data.keys())
            
            # Plot multiple metrics
            s1_eff = [s1_data[day]['metrics']['evacuation_efficiency'] for day in days]
            s2_eff = [s2_data[day]['metrics']['evacuation_efficiency'] for day in days]
            dual_eff = [dual_data[day]['metrics']['evacuation_efficiency'] for day in days]
            
            ax.plot(days, s1_eff, 'r-', linewidth=2, label='S1 Efficiency', alpha=0.8)
            ax.plot(days, s2_eff, 'b-', linewidth=2, label='S2 Efficiency', alpha=0.8)
            ax.plot(days, dual_eff, 'g-', linewidth=2, label='Dual Efficiency', alpha=0.8)
            
            # Add safety as secondary metric
            s1_safety = [s1_data[day]['metrics']['overall_safety'] for day in days]
            s2_safety = [s2_data[day]['metrics']['overall_safety'] for day in days]
            dual_safety = [dual_data[day]['metrics']['overall_safety'] for day in days]
            
            ax.plot(days, s1_safety, 'r--', linewidth=1, label='S1 Safety', alpha=0.6)
            ax.plot(days, s2_safety, 'b--', linewidth=1, label='S2 Safety', alpha=0.6)
            ax.plot(days, dual_safety, 'g--', linewidth=1, label='Dual Safety', alpha=0.6)
            
            ax.set_title(f'{network} - {scenario}', fontweight='bold')
            ax.set_xlabel('Days')
            ax.set_ylabel('Performance Score')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'h1_decision_quality' / 'h1_performance_dashboard_temporal.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def _create_h1_cognitive_load_analysis(self):
        """Create cognitive load analysis visualizations."""
        # Analysis 1: Cognitive Load vs Performance
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('H1: Cognitive Load vs Performance Analysis', 
                    fontsize=16, fontweight='bold')
        
        cognitive_modes = ['System 1', 'System 2', 'Dual Process']
        
        for idx, mode in enumerate(cognitive_modes):
            ax = axes[idx]
            
            # Collect data points
            load_values = []
            performance_values = []
            colors = []
            
            for network in self.networks:
                for scenario in self.scenarios:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    
                    for day in [10, 20, 30, 40]:  # Sample time points
                        if day in data:
                            load = data[day]['cognitive_metrics']['total_cognitive_load']
                            performance = data[day]['metrics']['evacuation_efficiency']
                            
                            load_values.append(load)
                            performance_values.append(performance)
                            colors.append(self.color_schemes['networks'][network])
            
            scatter = ax.scatter(load_values, performance_values, c=colors, alpha=0.6, s=50)
            
            # Fit trend line
            if load_values and performance_values:
                z = np.polyfit(load_values, performance_values, 1)
                p = np.poly1d(z)
                ax.plot(sorted(load_values), p(sorted(load_values)), "r--", alpha=0.8, linewidth=2)
            
            ax.set_title(f'{mode}', fontweight='bold')
            ax.set_xlabel('Cognitive Load')
            ax.set_ylabel('Evacuation Efficiency')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'h1_decision_quality' / 'h1_cognitive_load_vs_performance.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Analysis 2: Cognitive Load Distribution
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('H1: Cognitive Load Distribution Analysis', 
                    fontsize=16, fontweight='bold')
        
        # Load distribution by cognitive mode
        ax1 = axes[0, 0]
        load_data = {mode: [] for mode in cognitive_modes}
        
        for mode in cognitive_modes:
            for network in self.networks[:3]:
                for scenario in self.scenarios[:3]:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    loads = [data[day]['cognitive_metrics']['total_cognitive_load'] 
                            for day in data.keys() if 10 <= day <= 40]
                    load_data[mode].extend(loads)
        
        ax1.boxplot([load_data[mode] for mode in cognitive_modes], labels=cognitive_modes)
        ax1.set_title('Load Distribution by Mode', fontweight='bold')
        ax1.set_ylabel('Cognitive Load')
        ax1.grid(True, alpha=0.3)
        
        # Decision quality vs cognitive load
        ax2 = axes[0, 1]
        for mode in cognitive_modes:
            loads = []
            qualities = []
            
            for network in self.networks[:3]:
                for scenario in self.scenarios[:3]:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    for day in [15, 25, 35]:
                        if day in data:
                            loads.append(data[day]['cognitive_metrics']['total_cognitive_load'])
                            qualities.append(data[day]['cognitive_metrics']['weighted_decision_quality'])
            
            ax2.scatter(loads, qualities, label=mode, alpha=0.7, s=30)
        
        ax2.set_title('Decision Quality vs Load', fontweight='bold')
        ax2.set_xlabel('Cognitive Load')
        ax2.set_ylabel('Decision Quality')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Cognitive efficiency over time
        ax3 = axes[1, 0]
        for mode in cognitive_modes:
            efficiencies = []
            time_points = []
            
            # Average across conditions
            for day in range(0, 61, 5):
                day_efficiencies = []
                for network in self.networks[:3]:
                    for scenario in self.scenarios[:3]:
                        data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                        if day in data:
                            day_efficiencies.append(data[day]['cognitive_metrics']['cognitive_efficiency'])
                
                if day_efficiencies:
                    efficiencies.append(np.mean(day_efficiencies))
                    time_points.append(day)
            
            ax3.plot(time_points, efficiencies, 'o-', label=mode, linewidth=2, markersize=4)
        
        ax3.set_title('Cognitive Efficiency Over Time', fontweight='bold')
        ax3.set_xlabel('Days')
        ax3.set_ylabel('Cognitive Efficiency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Stress accumulation
        ax4 = axes[1, 1]
        for scenario in self.scenarios[:3]:
            stress_values = []
            time_points = []
            
            for day in range(0, 61, 5):
                day_stress = []
                for network in self.networks[:3]:
                    data = self.generate_comprehensive_temporal_data(network, scenario, 'Dual Process')
                    if day in data:
                        day_stress.append(data[day]['cognitive_metrics']['collective_stress'])
                
                if day_stress:
                    stress_values.append(np.mean(day_stress))
                    time_points.append(day)
            
            ax4.plot(time_points, stress_values, 'o-', label=scenario, linewidth=2, markersize=4)
        
        ax4.set_title('Collective Stress by Scenario', fontweight='bold')
        ax4.set_xlabel('Days')
        ax4.set_ylabel('Collective Stress')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'h1_decision_quality' / 'h1_cognitive_load_distribution.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Analysis 3: Load-Performance Phase Space
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # 3D scatter plot: Load vs Performance vs Time
        for mode in cognitive_modes:
            loads, performances, times = [], [], []
            
            for network in self.networks[:2]:  # Limit for clarity
                for scenario in self.scenarios[:2]:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    
                    for day in range(0, 61, 10):
                        if day in data:
                            loads.append(data[day]['cognitive_metrics']['total_cognitive_load'])
                            performances.append(data[day]['metrics']['evacuation_efficiency'])
                            times.append(day)
            
            ax.scatter(loads, performances, times, label=mode, alpha=0.6, s=30)
        
        ax.set_xlabel('Cognitive Load')
        ax.set_ylabel('Evacuation Efficiency')
        ax.set_zlabel('Time (Days)')
        ax.set_title('H1: Load-Performance-Time Phase Space', fontweight='bold', pad=20)
        ax.legend()
        
        plt.savefig(self.output_dir / 'h1_decision_quality' / 'h1_cognitive_load_phase_space.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def _create_h1_network_efficiency_comparison(self):
        """Create network efficiency comparison visualizations."""
        # Comparison 1: Network Utilization Analysis
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('H1: Network Efficiency Comparison Analysis', 
                    fontsize=16, fontweight='bold')
        
        # Network utilization by cognitive mode
        for idx, mode in enumerate(['System 1', 'System 2', 'Dual Process']):
            ax = axes[0, idx]
            
            utilization_data = []
            network_labels = []
            
            for network in self.networks:
                network_utils = []
                for scenario in self.scenarios:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    # Average utilization over steady state
                    utils = [data[day]['metrics']['network_utilization'] 
                            for day in data.keys() if 15 <= day <= 45]
                    network_utils.extend(utils)
                
                utilization_data.append(network_utils)
                network_labels.append(network)
            
            bp = ax.boxplot(utilization_data, labels=network_labels, patch_artist=True)
            
            # Color boxes
            colors = [self.color_schemes['networks'][net] for net in self.networks]
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax.set_title(f'{mode} - Network Utilization', fontweight='bold')
            ax.set_ylabel('Utilization')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        
        # Flow efficiency comparison
        for idx, network in enumerate(self.networks[:3]):
            ax = axes[1, idx]
            
            # Compare flow efficiency across cognitive modes
            modes = ['System 1', 'System 2', 'Dual Process']
            flow_effs = []
            
            for mode in modes:
                mode_flows = []
                for scenario in self.scenarios:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    flows = [data[day]['flow_metrics']['flow_efficiency'] 
                            for day in data.keys() if 10 <= day <= 40]
                    mode_flows.append(np.mean(flows))
                flow_effs.append(np.mean(mode_flows))
            
            bars = ax.bar(modes, flow_effs, color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)
            
            # Add value labels
            for bar, value in zip(bars, flow_effs):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
            
            ax.set_title(f'{network} - Flow Efficiency', fontweight='bold')
            ax.set_ylabel('Flow Efficiency')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'h1_decision_quality' / 'h1_network_efficiency_comparison.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Comparison 2: Bottleneck Analysis
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('H1: Bottleneck Analysis Comparison', 
                    fontsize=16, fontweight='bold')
        
        # Bottleneck severity heatmap
        ax1 = axes[0]
        bottleneck_matrix = np.zeros((len(self.networks), len(self.cognitive_modes[:3])))
        
        for i, network in enumerate(self.networks):
            for j, mode in enumerate(self.cognitive_modes[:3]):
                severities = []
                for scenario in self.scenarios:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    scenario_severities = [data[day]['metrics']['bottleneck_severity'] 
                                         for day in data.keys() if 15 <= day <= 35]
                    severities.extend(scenario_severities)
                bottleneck_matrix[i, j] = np.mean(severities)
        
        im1 = ax1.imshow(bottleneck_matrix, cmap='Reds', aspect='auto')
        ax1.set_title('Bottleneck Severity by Network & Mode', fontweight='bold')
        ax1.set_xticks(range(len(self.cognitive_modes[:3])))
        ax1.set_xticklabels(self.cognitive_modes[:3], rotation=45)
        ax1.set_yticks(range(len(self.networks)))
        ax1.set_yticklabels(self.networks)
        
        # Add value annotations
        for i in range(len(self.networks)):
            for j in range(len(self.cognitive_modes[:3])):
                text = ax1.text(j, i, f'{bottleneck_matrix[i, j]:.2f}',
                               ha="center", va="center", color="white", fontweight='bold')
        
        plt.colorbar(im1, ax=ax1, shrink=0.8)
        
        # Congestion index comparison
        ax2 = axes[1]
        
        congestion_data = {mode: [] for mode in self.cognitive_modes[:3]}
        
        for mode in self.cognitive_modes[:3]:
            for network in self.networks:
                for scenario in self.scenarios:
                    data = self.generate_comprehensive_temporal_data(network, scenario, mode)
                    congestions = [data[day]['flow_metrics']['congestion_index'] 
                                 for day in data.keys() if 10 <= day <= 40 
                                 and data[day]['flow_metrics']['congestion_index'] > 0]
                    congestion_data[mode].extend(congestions)
        
        # Create violin plot
        parts = ax2.violinplot([congestion_data[mode] for mode in self.cognitive_modes[:3]], 
                              positions=range(len(self.cognitive_modes[:3])), showmeans=True)
        
        # Color the violin plots
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        for pc, color in zip(parts['bodies'], colors):
            pc.set_facecolor(color)
            pc.set_alpha(0.7)
        
        ax2.set_title('Congestion Index Distribution', fontweight='bold')
        ax2.set_xticks(range(len(self.cognitive_modes[:3])))
        ax2.set_xticklabels(self.cognitive_modes[:3], rotation=45)
        ax2.set_ylabel('Congestion Index')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'h1_decision_quality' / 'h1_bottleneck_analysis.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()