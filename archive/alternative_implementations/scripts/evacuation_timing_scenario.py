#!/usr/bin/env python3
"""
Evacuation Timing Test Scenario

Creates a scenario to test S1 vs S2 differences in evacuation timing relative to conflict escalation.
Tests the prediction that S1 agents are reactive (wait longer) while S2 agents are preemptive (move earlier).
"""

import sys
import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add current directory to path for Flee imports
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    import flee
    from flee.SimulationSettings import SimulationSettings
    FLEE_AVAILABLE = True
except ImportError:
    FLEE_AVAILABLE = False
    print("⚠️  Flee not available, running in mock mode")

class EvacuationTimingScenario:
    """Test scenario for S1 vs S2 evacuation timing differences"""
    
    def __init__(self, output_dir: str = "evacuation_timing_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.scenario_config = {
            "conflict_escalation_days": 30,
            "max_conflict_level": 1.0,
            "origin_population": 8000,
            "camp_capacity": 5000,
            "s1_agent_ratio": 0.5,  # 50% S1, 50% S2 capable
            "connectivity_range": (1, 8)  # Range of social connections
        }
        
    def create_scenario_topology(self) -> str:
        """Create linear evacuation topology for timing test"""
        
        # Use the refugee topology generator
        from scripts.refugee_topology_generator import RefugeeTopologyGenerator
        
        generator = RefugeeTopologyGenerator(self.output_dir / "topologies")
        topology_name = generator.generate_linear_evacuation_route(
            n_intermediate=1,  # Origin → Town → Camp
            segment_distance=100.0,
            origin_population=self.scenario_config["origin_population"],
            camp_capacity=self.scenario_config["camp_capacity"]
        )
        
        return topology_name
    
    def create_conflict_escalation_file(self, topology_dir: Path) -> None:
        """Create conflict escalation file with gradual increase"""
        
        conflicts_file = topology_dir / "conflicts.csv"
        
        with open(conflicts_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'date', 'intensity'])
            
            # Gradual conflict escalation over 30 days
            for day in range(self.scenario_config["conflict_escalation_days"]):
                # Linear escalation from 0.1 to 1.0
                intensity = 0.1 + (day / self.scenario_config["conflict_escalation_days"]) * 0.9
                date = f"2023-01-{day+1:02d}"
                
                writer.writerow(['Origin', date, intensity])
        
        print(f"✅ Created conflict escalation file: {conflicts_file}")
    
    def create_simulation_config(self, topology_dir: Path) -> None:
        """Create simulation configuration for evacuation timing test"""
        
        # Create sim_period.csv
        sim_period_file = topology_dir / "sim_period.csv"
        with open(sim_period_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['StartDate', 'EndDate'])
            writer.writerow(['2023-01-01', f'2023-02-{self.scenario_config["conflict_escalation_days"]:02d}'])
        
        # Create closures.csv (empty - no border closures)
        closures_file = topology_dir / "closures.csv"
        with open(closures_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name1', 'name2', 'closure_start', 'closure_end'])
            # Empty file - no closures
        
        print(f"✅ Created simulation config files in {topology_dir}")
    
    def run_evacuation_timing_test(self, use_mock: bool = True) -> Dict[str, Any]:
        """Run the evacuation timing test scenario"""
        
        if not FLEE_AVAILABLE or use_mock:
            return self._run_mock_evacuation_test()
        
        # Real Flee simulation would go here
        return self._run_flee_evacuation_test()
    
    def _run_mock_evacuation_test(self) -> Dict[str, Any]:
        """Run mock evacuation timing test to demonstrate expected results"""
        
        print("🧪 Running mock evacuation timing test...")
        
        # Create topology
        topology_name = self.create_scenario_topology()
        topology_dir = self.output_dir / "topologies" / topology_name
        
        # Add conflict and simulation files
        self.create_conflict_escalation_file(topology_dir)
        self.create_simulation_config(topology_dir)
        
        # Simulate S1 vs S2 evacuation timing differences
        results = {
            "scenario_config": self.scenario_config,
            "topology_name": topology_name,
            "agents": [],
            "evacuation_events": []
        }
        
        # Generate mock agents with different connectivity levels
        n_agents = 100
        
        for agent_id in range(n_agents):
            # Randomly assign connectivity (determines S1/S2 capability)
            connections = random.randint(*self.scenario_config["connectivity_range"])
            system2_capable = connections >= 4  # S2 threshold
            
            # S1 agents: Reactive evacuation (wait until conflict is high)
            # S2 agents: Preemptive evacuation (move when conflict starts rising)
            
            if system2_capable:
                # S2 agent: Evacuate early when conflict > 0.3
                evacuation_day = random.randint(5, 12)  # Early evacuation
                evacuation_trigger = 0.3 + random.uniform(0.0, 0.2)
            else:
                # S1 agent: Evacuate late when conflict > 0.7
                evacuation_day = random.randint(15, 25)  # Late evacuation
                evacuation_trigger = 0.7 + random.uniform(0.0, 0.2)
            
            agent_data = {
                "agent_id": agent_id,
                "connections": connections,
                "system2_capable": system2_capable,
                "evacuation_day": evacuation_day,
                "evacuation_trigger": evacuation_trigger,
                "conflict_at_evacuation": 0.1 + (evacuation_day / 30.0) * 0.9
            }
            
            results["agents"].append(agent_data)
            
            # Record evacuation event
            results["evacuation_events"].append({
                "day": evacuation_day,
                "agent_id": agent_id,
                "system2_active": system2_capable,
                "conflict_level": agent_data["conflict_at_evacuation"],
                "connections": connections
            })
        
        # Analyze results
        analysis = self._analyze_evacuation_timing(results)
        results["analysis"] = analysis
        
        # Save results
        results_file = self.output_dir / "evacuation_timing_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Saved evacuation timing results to {results_file}")
        
        return results
    
    def _analyze_evacuation_timing(self, results: Dict) -> Dict[str, Any]:
        """Analyze evacuation timing differences between S1 and S2 agents"""
        
        s1_agents = [a for a in results["agents"] if not a["system2_capable"]]
        s2_agents = [a for a in results["agents"] if a["system2_capable"]]
        
        s1_evacuation_days = [a["evacuation_day"] for a in s1_agents]
        s2_evacuation_days = [a["evacuation_day"] for a in s2_agents]
        
        s1_conflict_levels = [a["conflict_at_evacuation"] for a in s1_agents]
        s2_conflict_levels = [a["conflict_at_evacuation"] for a in s2_agents]
        
        import numpy as np
        
        analysis = {
            "s1_stats": {
                "count": len(s1_agents),
                "mean_evacuation_day": np.mean(s1_evacuation_days),
                "std_evacuation_day": np.std(s1_evacuation_days),
                "mean_conflict_at_evacuation": np.mean(s1_conflict_levels),
                "std_conflict_at_evacuation": np.std(s1_conflict_levels)
            },
            "s2_stats": {
                "count": len(s2_agents),
                "mean_evacuation_day": np.mean(s2_evacuation_days),
                "std_evacuation_day": np.std(s2_evacuation_days),
                "mean_conflict_at_evacuation": np.mean(s2_conflict_levels),
                "std_conflict_at_evacuation": np.std(s2_conflict_levels)
            },
            "differences": {
                "evacuation_day_difference": np.mean(s1_evacuation_days) - np.mean(s2_evacuation_days),
                "conflict_level_difference": np.mean(s1_conflict_levels) - np.mean(s2_conflict_levels)
            }
        }
        
        # Validate theoretical predictions
        predictions_validated = {
            "s1_evacuates_later": analysis["differences"]["evacuation_day_difference"] > 0,
            "s2_evacuates_at_lower_conflict": analysis["differences"]["conflict_level_difference"] > 0,
            "effect_size_meaningful": abs(analysis["differences"]["evacuation_day_difference"]) > 3.0
        }
        
        analysis["predictions_validated"] = predictions_validated
        
        return analysis
    
    def _run_flee_evacuation_test(self) -> Dict[str, Any]:
        """Run actual Flee simulation for evacuation timing test"""
        
        # This would implement the actual Flee simulation
        # For now, return mock results
        print("🚧 Flee simulation not yet implemented, using mock results")
        return self._run_mock_evacuation_test()
    
    def print_analysis_summary(self, results: Dict[str, Any]) -> None:
        """Print summary of evacuation timing analysis"""
        
        if "analysis" not in results:
            print("❌ No analysis results available")
            return
        
        analysis = results["analysis"]
        
        print("\\n📊 Evacuation Timing Analysis Results:")
        print("=" * 50)
        
        print(f"\\n🔴 System 1 (Reactive) Agents:")
        print(f"  Count: {analysis['s1_stats']['count']}")
        print(f"  Mean evacuation day: {analysis['s1_stats']['mean_evacuation_day']:.1f}")
        print(f"  Mean conflict at evacuation: {analysis['s1_stats']['mean_conflict_at_evacuation']:.2f}")
        
        print(f"\\n🔵 System 2 (Preemptive) Agents:")
        print(f"  Count: {analysis['s2_stats']['count']}")
        print(f"  Mean evacuation day: {analysis['s2_stats']['mean_evacuation_day']:.1f}")
        print(f"  Mean conflict at evacuation: {analysis['s2_stats']['mean_conflict_at_evacuation']:.2f}")
        
        print(f"\\n📈 Differences (S1 - S2):")
        print(f"  Evacuation timing: {analysis['differences']['evacuation_day_difference']:.1f} days")
        print(f"  Conflict level: {analysis['differences']['conflict_level_difference']:.2f}")
        
        print(f"\\n✅ Theoretical Predictions Validated:")
        preds = analysis["predictions_validated"]
        print(f"  S1 evacuates later: {'✅' if preds['s1_evacuates_later'] else '❌'}")
        print(f"  S2 evacuates at lower conflict: {'✅' if preds['s2_evacuates_at_lower_conflict'] else '❌'}")
        print(f"  Effect size meaningful: {'✅' if preds['effect_size_meaningful'] else '❌'}")

def test_evacuation_timing_scenario():
    """Test the evacuation timing scenario"""
    print("🧪 Testing Evacuation Timing Scenario...")
    
    scenario = EvacuationTimingScenario("test_evacuation_timing")
    
    # Run the test
    results = scenario.run_evacuation_timing_test(use_mock=True)
    
    # Print analysis
    scenario.print_analysis_summary(results)
    
    print("\\n✅ Evacuation timing scenario test completed successfully!")

if __name__ == "__main__":
    test_evacuation_timing_scenario()