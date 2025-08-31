#!/usr/bin/env python3
"""
Example: Individual Agent Analysis for Dual Process Experiments

This script demonstrates how to use the individual agent analysis tools
to analyze agent trajectories, decision-making patterns, and behavioral clustering.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import flee modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from flee_dual_process.individual_agent_analysis import IndividualAgentAnalyzer
from flee_dual_process.individual_agent_tracker import (
    IndividualAgentTracker, create_flee_compatible_config
)


def main():
    """Main example function."""
    print("Individual Agent Analysis Example")
    print("=" * 50)
    
    # Configuration
    data_directory = "output"  # Directory containing agent tracking data
    analysis_output = "analysis_results"
    rank = 0  # MPI rank (0 for single-process runs)
    
    # Create output directory
    Path(analysis_output).mkdir(exist_ok=True)
    
    print(f"Analyzing data from: {data_directory}")
    print(f"Output directory: {analysis_output}")
    print()
    
    # Step 1: Initialize the analyzer
    print("Step 1: Initializing Individual Agent Analyzer")
    analyzer = IndividualAgentAnalyzer(data_directory, rank=rank)
    
    # Step 2: Load data from various sources
    print("Step 2: Loading agent tracking data")
    
    # Load Flee's standard agent logs
    flee_success = analyzer.load_flee_agent_data()
    if flee_success:
        print("✓ Loaded Flee agent data")
    else:
        print("⚠ Flee agent data not found - will use dual-process data only")
    
    # Load dual-process tracking data
    dp_success = analyzer.load_dual_process_data()
    if dp_success:
        print("✓ Loaded dual-process tracking data")
        print(f"  - Data sources: {analyzer.loaded_data_sources}")
    else:
        print("✗ No dual-process data found")
        return
    
    print()
    
    # Step 3: Build complete agent trajectories
    print("Step 3: Building agent trajectories")
    trajectories = analyzer.build_agent_trajectories()
    
    if not trajectories:
        print("✗ No agent trajectories could be built")
        return
        
    print(f"✓ Built trajectories for {len(trajectories)} agents")
    
    # Show sample trajectory info
    sample_agent_id = list(trajectories.keys())[0]
    sample_trajectory = trajectories[sample_agent_id]
    
    print(f"\nSample trajectory ({sample_agent_id}):")
    print(f"  - Trajectory points: {len(sample_trajectory.trajectory_points)}")
    print(f"  - Decisions: {len(sample_trajectory.decisions)}")
    print(f"  - Cognitive transitions: {len(sample_trajectory.cognitive_transitions)}")
    print(f"  - Social interactions: {len(sample_trajectory.social_interactions)}")
    print()
    
    # Step 4: Identify movement patterns
    print("Step 4: Identifying movement patterns")
    try:
        movement_patterns = analyzer.identify_movement_patterns(n_clusters=3)
        print(f"✓ Identified {len(movement_patterns)} movement patterns")
        
        for i, pattern in enumerate(movement_patterns):
            print(f"\nPattern {i+1}: {pattern.pattern_id}")
            print(f"  - Agents: {len(pattern.agent_ids)}")
            print(f"  - Dominant cognitive mode: {pattern.cognitive_profile.get('dominant_mode', 'Unknown')}")
            print(f"  - Spatial range: {pattern.spatial_signature.get('range', 'Unknown')}")
            
    except Exception as e:
        print(f"⚠ Movement pattern analysis failed: {e}")
    
    print()
    
    # Step 5: Analyze decision-making patterns
    print("Step 5: Analyzing decision-making patterns")
    decision_clusters = analyzer.analyze_decision_making_patterns()
    
    if decision_clusters:
        print("✓ Decision pattern analysis complete")
        
        for pattern_name, agent_list in decision_clusters.items():
            if agent_list:  # Only show non-empty clusters
                print(f"  - {pattern_name}: {len(agent_list)} agents")
    else:
        print("⚠ No decision data available for clustering")
    
    print()
    
    # Step 6: Compare individual vs aggregate patterns
    print("Step 6: Comparing individual vs aggregate patterns")
    comparison = analyzer.compare_individual_vs_aggregate_patterns()
    
    if comparison:
        print("✓ Individual vs aggregate comparison complete")
        
        # Distance analysis
        if 'distance_analysis' in comparison:
            dist_analysis = comparison['distance_analysis']
            print(f"\nDistance Analysis:")
            print(f"  - Mean distance: {dist_analysis['individual_mean']:.1f}")
            print(f"  - Distance inequality (Gini): {dist_analysis['distance_inequality_gini']:.3f}")
        
        # Cognitive analysis
        if 'cognitive_analysis' in comparison:
            cog_analysis = comparison['cognitive_analysis']
            print(f"\nCognitive Analysis:")
            print(f"  - Mean S2 usage: {cog_analysis['individual_s2_mean']:.3f}")
            print(f"  - Cognitive diversity: {cog_analysis['cognitive_diversity']}")
        
        # Spatial analysis
        if 'spatial_analysis' in comparison:
            spatial_analysis = comparison['spatial_analysis']
            print(f"\nSpatial Analysis:")
            print(f"  - Mean location diversity: {spatial_analysis['individual_diversity_mean']:.3f}")
            print(f"  - Exploration inequality: {spatial_analysis['spatial_exploration_inequality']:.3f}")
    
    print()
    
    # Step 7: Generate individual agent reports
    print("Step 7: Generating individual agent reports")
    
    # Generate reports for first few agents
    report_count = min(3, len(trajectories))
    agent_ids = list(trajectories.keys())[:report_count]
    
    for i, agent_id in enumerate(agent_ids):
        print(f"\nGenerating report for agent {agent_id}...")
        
        report_file = Path(analysis_output) / f"agent_report_{agent_id.replace('-', '_')}.json"
        report = analyzer.generate_individual_agent_report(agent_id, str(report_file))
        
        if report:
            print(f"✓ Report saved to {report_file}")
            
            # Show key insights
            summary = report['summary_statistics']
            print(f"  - Total distance: {summary.get('total_distance', 0):.1f}")
            print(f"  - Unique locations: {summary.get('unique_locations_visited', 0)}")
            print(f"  - S2 proportion: {summary.get('s2_proportion', 0):.3f}")
            print(f"  - Total decisions: {summary.get('total_decisions', 0)}")
    
    print()
    
    # Step 8: Export all analysis results
    print("Step 8: Exporting analysis results")
    analyzer.export_analysis_results(analysis_output)
    print(f"✓ All analysis results exported to {analysis_output}")
    
    # List generated files
    output_files = list(Path(analysis_output).glob("*"))
    print(f"\nGenerated files ({len(output_files)}):")
    for file_path in sorted(output_files):
        print(f"  - {file_path.name}")
    
    print()
    print("Analysis complete! 🎉")
    print()
    print("Next steps:")
    print("1. Review individual agent reports for detailed behavioral analysis")
    print("2. Examine movement patterns to understand population heterogeneity")
    print("3. Use decision clusters to identify cognitive behavioral types")
    print("4. Compare individual vs aggregate metrics for emergent behavior insights")


def demonstrate_integration_with_tracking():
    """Demonstrate integration with the tracking system."""
    print("\nDemonstration: Integration with Agent Tracking")
    print("=" * 50)
    
    # This would typically be called during simulation
    print("During simulation, you would:")
    print("1. Configure agent tracking based on Flee's logging level")
    print("2. Track agents during simulation timesteps")
    print("3. Analyze results after simulation completes")
    print()
    
    # Example configuration
    print("Example tracking configuration:")
    
    # Determine Flee's agent logging level (would come from SimulationSettings)
    flee_agent_level = 1  # Example: basic Flee logging enabled
    
    # Create compatible configuration
    config = create_flee_compatible_config("output", flee_agent_level)
    
    print(f"  - Flee agent logging level: {flee_agent_level}")
    print(f"  - Recommended tracking level: {config.tracking_level.value}")
    print(f"  - Storage format: {config.storage_format.value}")
    print(f"  - Sampling rate: {config.sampling_rate}")
    print()
    
    print("Integration benefits:")
    print("  ✓ Avoids duplication of basic trajectory data")
    print("  ✓ Adds cognitive state and decision-making analysis")
    print("  ✓ Provides efficient storage for large-scale simulations")
    print("  ✓ Enables comprehensive individual behavior analysis")


def show_analysis_capabilities():
    """Show the analysis capabilities available."""
    print("\nAnalysis Capabilities Overview")
    print("=" * 50)
    
    capabilities = {
        "Trajectory Analysis": [
            "Complete movement histories with GPS coordinates",
            "Location sequence and stay duration patterns",
            "Movement velocity and consistency metrics",
            "Spatial exploration diversity indices"
        ],
        "Decision Analysis": [
            "Decision type classification and frequency",
            "Confidence levels and temporal patterns",
            "Cognitive state during decision-making",
            "Decision outcome tracking and success rates"
        ],
        "Cognitive Behavior": [
            "System 1/System 2 usage patterns",
            "Cognitive state transition analysis",
            "Trigger identification for state changes",
            "Individual cognitive profiles and clustering"
        ],
        "Social Network Analysis": [
            "Connection formation and dissolution",
            "Information sharing and receiving patterns",
            "Network position and influence metrics",
            "Social interaction temporal dynamics"
        ],
        "Comparative Analysis": [
            "Individual vs population comparisons",
            "Behavioral clustering and pattern identification",
            "Inequality metrics (Gini coefficients)",
            "Emergent behavior detection"
        ]
    }
    
    for category, features in capabilities.items():
        print(f"\n{category}:")
        for feature in features:
            print(f"  • {feature}")
    
    print("\nOutput Formats:")
    print("  • JSON reports for detailed individual analysis")
    print("  • CSV summaries for statistical analysis")
    print("  • Clustering results for population segmentation")
    print("  • Integration guides for combining with Flee data")


if __name__ == "__main__":
    # Check if data directory exists
    if not Path("output").exists():
        print("Creating example output directory structure...")
        Path("output").mkdir(exist_ok=True)
        
        print("⚠ No simulation data found in 'output' directory.")
        print("To run this example with real data:")
        print("1. Run a Flee simulation with dual-process tracking enabled")
        print("2. Ensure agent tracking data is saved to 'output' directory")
        print("3. Re-run this example script")
        print()
        
        # Show capabilities instead
        show_analysis_capabilities()
        demonstrate_integration_with_tracking()
    else:
        # Run the main analysis
        main()
        demonstrate_integration_with_tracking()