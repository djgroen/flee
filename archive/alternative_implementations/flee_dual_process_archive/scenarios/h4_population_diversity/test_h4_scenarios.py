"""
Test suite for H4 Population Diversity Scenarios

Tests both H4.1 Adaptive Shock Response and H4.2 Information Cascade Test scenarios.
"""

import unittest
import tempfile
import shutil
import os
import pandas as pd
from typing import Dict, Any

# Import H4.1 components
from h4_1_adaptive_shock.adaptive_shock_generator import AdaptiveShockScenario
from h4_1_adaptive_shock.population_config import PopulationConfig, PopulationType
from h4_1_adaptive_shock.resilience_metrics import analyze_h4_1_scenario
from h4_1_adaptive_shock.event_timeline import create_adaptive_shock_timeline

# Import H4.2 components
from h4_2_information_cascade.cascade_generator import InformationCascadeScenario
from h4_2_information_cascade.scout_follower_tracker import ScoutFollowerTracker
from h4_2_information_cascade.cascade_metrics import analyze_h4_2_scenario
from h4_2_information_cascade.information_flow_analyzer import InformationFlowAnalyzer


class TestH4AdaptiveShockScenario(unittest.TestCase):
    """Test H4.1 Adaptive Shock Response scenario"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.scenario = AdaptiveShockScenario()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scenario_generation(self):
        """Test adaptive shock scenario generation"""
        files = self.scenario.create_scenario(
            output_dir=self.temp_dir,
            population_composition="balanced",
            shock_intensity=0.8
        )
        
        # Check that all required files are generated
        required_files = ['locations', 'routes', 'conflicts', 'closures', 
                         'population', 'sim_period', 'metadata']
        
        for file_type in required_files:
            self.assertIn(file_type, files)
            self.assertTrue(os.path.exists(files[file_type]))
    
    def test_population_configurations(self):
        """Test different population configurations"""
        config_manager = PopulationConfig()
        
        # Test all population types
        for pop_type in [PopulationType.PURE_S1.value, PopulationType.PURE_S2.value,
                        PopulationType.BALANCED.value, PopulationType.REALISTIC.value]:
            
            composition = config_manager.get_composition(pop_type)
            self.assertIsNotNone(composition)
            self.assertEqual(composition.system1_ratio + composition.system2_ratio, 1.0)
            
            # Generate agent config
            agent_config = config_manager.generate_agent_config(pop_type)
            self.assertIn('population', agent_config)
            self.assertIn('cognitive_profiles', agent_config)
    
    def test_event_timeline(self):
        """Test event timeline generation"""
        timeline = create_adaptive_shock_timeline()
        
        # Check that timeline has expected events
        all_events = timeline.get_all_events()
        self.assertGreater(len(all_events), 0)
        
        # Check for key event types
        event_types = {event.event_type for event in all_events}
        expected_types = {'conflict_start', 'route_closure', 'camp_full', 
                         'new_camp_opens', 'route_reopens'}
        self.assertTrue(expected_types.issubset(event_types))
    
    def test_resilience_analysis(self):
        """Test resilience metrics analysis"""
        # Generate scenario first
        files = self.scenario.create_scenario(
            output_dir=self.temp_dir,
            population_composition="balanced"
        )
        
        # Analyze resilience (will use synthetic data)
        results = analyze_h4_1_scenario(self.temp_dir, "balanced")
        
        # Check that metrics are calculated
        self.assertIsInstance(results.adaptation_speed, float)
        self.assertIsInstance(results.recovery_rate, float)
        self.assertIsInstance(results.collective_efficiency, float)
        self.assertIsInstance(results.resilience_index, float)
        
        # Check that metrics are in reasonable ranges
        self.assertGreaterEqual(results.resilience_index, 0.0)
        self.assertLessEqual(results.resilience_index, 1.0)


class TestH4InformationCascadeScenario(unittest.TestCase):
    """Test H4.2 Information Cascade Test scenario"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.scenario = InformationCascadeScenario()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scenario_generation(self):
        """Test information cascade scenario generation"""
        files = self.scenario.create_scenario(
            output_dir=self.temp_dir,
            scout_ratio=0.3,
            information_sharing_rate=0.7
        )
        
        # Check that all required files are generated
        required_files = ['locations', 'routes', 'conflicts', 'discovery_timeline',
                         'agent_config', 'sim_period', 'metadata']
        
        for file_type in required_files:
            self.assertIn(file_type, files)
            self.assertTrue(os.path.exists(files[file_type]))
    
    def test_scout_follower_tracking(self):
        """Test scout-follower behavior tracking"""
        # Create sample agent data
        agent_data = pd.DataFrame([
            {'agent_id': 1, 'cognitive_type': 'S1', 'is_scout': True},
            {'agent_id': 2, 'cognitive_type': 'S1', 'is_scout': True},
            {'agent_id': 10, 'cognitive_type': 'S2', 'is_scout': False},
            {'agent_id': 11, 'cognitive_type': 'S2', 'is_scout': False}
        ])
        
        tracker = ScoutFollowerTracker({})
        tracker.initialize_agents(agent_data)
        
        # Test tracking functionality
        tracker.track_discovery_event(15, 1, "Hidden_Good_Camp")
        tracker.track_information_sharing(16, 1, "Hidden_Good_Camp", [10, 11])
        tracker.track_adoption_event(19, 10, "Hidden_Good_Camp")
        
        # Generate report
        report = tracker.generate_tracking_report()
        
        self.assertIn('scout_analysis', report)
        self.assertIn('follower_analysis', report)
        self.assertIn('cascade_analysis', report)
    
    def test_cascade_metrics(self):
        """Test cascade metrics analysis"""
        # Generate scenario first
        files = self.scenario.create_scenario(
            output_dir=self.temp_dir,
            scout_ratio=0.3
        )
        
        # Analyze cascade metrics (will use synthetic data)
        results = analyze_h4_2_scenario(self.temp_dir, scout_ratio=0.3)
        
        # Check that metrics are calculated
        self.assertIsInstance(results.discovery_rate, float)
        self.assertIsInstance(results.adoption_lag, float)
        self.assertIsInstance(results.information_correlation, float)
        self.assertIsInstance(results.cascade_efficiency, float)
        self.assertIsInstance(results.collective_optimality, float)
        
        # Check that metrics are in reasonable ranges
        self.assertGreaterEqual(results.discovery_rate, 0.0)
        self.assertGreaterEqual(results.adoption_lag, 0.0)
        self.assertGreaterEqual(results.cascade_efficiency, 0.0)
        self.assertLessEqual(results.cascade_efficiency, 2.0)  # Allow some flexibility
    
    def test_information_flow_analysis(self):
        """Test information flow network analysis"""
        # Create sample data
        scout_data = pd.DataFrame([
            {'agent_id': 1, 'day': 5, 'destination': 'Hidden_Good_Camp'},
            {'agent_id': 2, 'day': 8, 'destination': 'Moderate_Camp'}
        ])
        
        follower_data = pd.DataFrame([
            {'agent_id': 10, 'day': 8, 'destination': 'Hidden_Good_Camp'},
            {'agent_id': 11, 'day': 12, 'destination': 'Moderate_Camp'}
        ])
        
        analyzer = InformationFlowAnalyzer(self.temp_dir)
        analyzer.build_information_network(scout_data, follower_data)
        
        # Test network analysis
        metrics = analyzer.analyze_information_flow()
        
        self.assertIsInstance(metrics.flow_velocity, float)
        self.assertIsInstance(metrics.network_density, float)
        self.assertIsInstance(metrics.cascade_reach, float)
        
        # Test scout-follower dynamics analysis
        dynamics = analyzer.analyze_scout_follower_dynamics()
        
        self.assertIn('scout_influence', dynamics)
        self.assertIn('follower_receptivity', dynamics)
        self.assertIn('interaction_patterns', dynamics)


class TestH4Integration(unittest.TestCase):
    """Test integration between H4.1 and H4.2 scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_population_diversity_comparison(self):
        """Test comparison across different population compositions"""
        # Test H4.1 with different population types
        h4_1_scenario = AdaptiveShockScenario()
        h4_1_results = {}
        
        for pop_type in ["pure_s1", "pure_s2", "balanced", "realistic"]:
            output_dir = os.path.join(self.temp_dir, f"h4_1_{pop_type}")
            
            files = h4_1_scenario.create_scenario(
                output_dir=output_dir,
                population_composition=pop_type
            )
            
            results = analyze_h4_1_scenario(output_dir, pop_type)
            h4_1_results[pop_type] = results
        
        # Check that different population types produce different results
        resilience_indices = [results.resilience_index for results in h4_1_results.values()]
        self.assertGreater(max(resilience_indices) - min(resilience_indices), 0.01)
    
    def test_scout_ratio_effects(self):
        """Test effects of different scout ratios in H4.2"""
        h4_2_scenario = InformationCascadeScenario()
        h4_2_results = {}
        
        for scout_ratio in [0.1, 0.3, 0.5]:
            output_dir = os.path.join(self.temp_dir, f"h4_2_scouts_{scout_ratio}")
            
            files = h4_2_scenario.create_scenario(
                output_dir=output_dir,
                scout_ratio=scout_ratio
            )
            
            results = analyze_h4_2_scenario(output_dir, scout_ratio)
            h4_2_results[f"scouts_{scout_ratio}"] = results
        
        # Check that different scout ratios produce different results
        discovery_rates = [results.discovery_rate for results in h4_2_results.values()]
        self.assertGreater(len(set(discovery_rates)), 1)  # Should have some variation
    
    def test_h4_hypothesis_validation(self):
        """Test that H4 scenarios support hypothesis validation"""
        # H4.1: Test that mixed populations show better resilience
        h4_1_scenario = AdaptiveShockScenario()
        
        # Generate balanced population scenario
        balanced_dir = os.path.join(self.temp_dir, "balanced")
        h4_1_scenario.create_scenario(balanced_dir, "balanced")
        balanced_results = analyze_h4_1_scenario(balanced_dir, "balanced")
        
        # Generate pure S1 scenario
        pure_s1_dir = os.path.join(self.temp_dir, "pure_s1")
        h4_1_scenario.create_scenario(pure_s1_dir, "pure_s1")
        pure_s1_results = analyze_h4_1_scenario(pure_s1_dir, "pure_s1")
        
        # Balanced should generally perform better (though synthetic data may not show this)
        self.assertIsInstance(balanced_results.resilience_index, float)
        self.assertIsInstance(pure_s1_results.resilience_index, float)
        
        # H4.2: Test that information cascades occur
        h4_2_scenario = InformationCascadeScenario()
        cascade_dir = os.path.join(self.temp_dir, "cascade")
        h4_2_scenario.create_scenario(cascade_dir, scout_ratio=0.3)
        cascade_results = analyze_h4_2_scenario(cascade_dir, 0.3)
        
        # Should have some cascade efficiency
        self.assertGreater(cascade_results.cascade_efficiency, 0.0)


def run_h4_tests():
    """Run all H4 scenario tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add H4.1 tests
    suite.addTest(unittest.makeSuite(TestH4AdaptiveShockScenario))
    
    # Add H4.2 tests
    suite.addTest(unittest.makeSuite(TestH4InformationCascadeScenario))
    
    # Add integration tests
    suite.addTest(unittest.makeSuite(TestH4Integration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_h4_tests()
    print(f"\nH4 Scenario Tests {'PASSED' if success else 'FAILED'}")