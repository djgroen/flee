#!/usr/bin/env python3
"""
Test Runner for Validation and Testing Framework

Runs all validation and testing framework tests with comprehensive reporting.
"""

import sys
import os
import unittest
import time
from typing import Dict, List, Any

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all test modules
try:
    from test_topology_generator import *
    from test_scenario_generator import *
    from test_integration_pipeline import *
    from test_performance_benchmarks import *
    from test_validation_framework import *
except ImportError as e:
    print(f"Error importing test modules: {e}")
    print("Make sure all test files are present in the flee_dual_process directory")
    sys.exit(1)


class TestSuiteRunner:
    """Test suite runner with comprehensive reporting."""
    
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.total_skipped = 0
    
    def run_test_suite(self, suite_name: str, test_classes: List[type]) -> Dict[str, Any]:
        """Run a test suite and return results."""
        print(f"\n{'='*60}")
        print(f"Running {suite_name}")
        print(f"{'='*60}")
        
        suite = unittest.TestSuite()
        
        # Add all test methods from test classes
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests with detailed output
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=sys.stdout,
            buffer=True
        )
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Collect results
        suite_results = {
            'name': suite_name,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / max(result.testsRun, 1),
            'execution_time': end_time - start_time,
            'failure_details': [str(failure[1]) for failure in result.failures],
            'error_details': [str(error[1]) for error in result.errors]
        }
        
        # Update totals
        self.total_tests += result.testsRun
        self.total_failures += len(result.failures)
        self.total_errors += len(result.errors)
        self.total_skipped += len(result.skipped)
        
        return suite_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        print("Starting Validation and Testing Framework Test Suite")
        print(f"Python version: {sys.version}")
        print(f"Test directory: {os.path.dirname(os.path.abspath(__file__))}")
        
        overall_start_time = time.time()
        
        # Define test suites
        test_suites = [
            {
                'name': 'Unit Tests - Topology Generators',
                'classes': [
                    TestTopologyGeneratorBase,
                    TestLinearTopologyGenerator,
                    TestStarTopologyGenerator,
                    TestTreeTopologyGenerator,
                    TestGridTopologyGenerator
                ]
            },
            {
                'name': 'Unit Tests - Scenario Generators',
                'classes': [
                    TestConflictScenarioGeneratorBase,
                    TestSpikeConflictGenerator,
                    TestGradualConflictGenerator,
                    TestCascadingConflictGenerator,
                    TestOscillatingConflictGenerator
                ]
            },
            {
                'name': 'Integration Tests - End-to-End Pipeline',
                'classes': [
                    TestEndToEndPipeline,
                    TestParallelExecutionStability,
                    TestDataIntegrityValidation
                ]
            },
            {
                'name': 'Performance Benchmarks',
                'classes': [
                    TestTopologyGenerationPerformance,
                    TestScenarioGenerationPerformance,
                    TestExperimentExecutionThroughput,
                    TestAnalysisPipelinePerformance,
                    TestParameterSweepScalability
                ]
            },
            {
                'name': 'Validation Framework Tests',
                'classes': [
                    TestValidationResult,
                    TestExperimentConfigValidator,
                    TestFileFormatValidator,
                    TestStatisticalValidator,
                    TestExperimentValidator
                ]
            }
        ]
        
        # Run each test suite
        suite_results = []
        for suite_config in test_suites:
            try:
                result = self.run_test_suite(suite_config['name'], suite_config['classes'])
                suite_results.append(result)
                self.results[suite_config['name']] = result
            except Exception as e:
                print(f"Error running test suite '{suite_config['name']}': {e}")
                error_result = {
                    'name': suite_config['name'],
                    'tests_run': 0,
                    'failures': 0,
                    'errors': 1,
                    'skipped': 0,
                    'success_rate': 0.0,
                    'execution_time': 0.0,
                    'failure_details': [],
                    'error_details': [str(e)]
                }
                suite_results.append(error_result)
                self.results[suite_config['name']] = error_result
                self.total_errors += 1
        
        overall_end_time = time.time()
        
        # Generate summary report
        summary = self.generate_summary_report(suite_results, overall_end_time - overall_start_time)
        
        return summary
    
    def generate_summary_report(self, suite_results: List[Dict[str, Any]], 
                              total_time: float) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        print(f"\n{'='*80}")
        print("TEST SUITE SUMMARY REPORT")
        print(f"{'='*80}")
        
        # Overall statistics
        overall_success_rate = (self.total_tests - self.total_failures - self.total_errors) / max(self.total_tests, 1)
        
        print(f"\nOverall Results:")
        print(f"  Total Tests Run: {self.total_tests}")
        print(f"  Passed: {self.total_tests - self.total_failures - self.total_errors}")
        print(f"  Failed: {self.total_failures}")
        print(f"  Errors: {self.total_errors}")
        print(f"  Skipped: {self.total_skipped}")
        print(f"  Success Rate: {overall_success_rate:.1%}")
        print(f"  Total Execution Time: {total_time:.2f} seconds")
        
        # Per-suite breakdown
        print(f"\nPer-Suite Breakdown:")
        print(f"{'Suite Name':<40} {'Tests':<8} {'Pass':<8} {'Fail':<8} {'Error':<8} {'Rate':<8} {'Time':<8}")
        print(f"{'-'*40} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
        
        for result in suite_results:
            passed = result['tests_run'] - result['failures'] - result['errors']
            print(f"{result['name']:<40} {result['tests_run']:<8} {passed:<8} "
                  f"{result['failures']:<8} {result['errors']:<8} "
                  f"{result['success_rate']:.1%:<8} {result['execution_time']:.1f}s")
        
        # Failure and error details
        if self.total_failures > 0 or self.total_errors > 0:
            print(f"\nFailure and Error Details:")
            for result in suite_results:
                if result['failures'] > 0 or result['errors'] > 0:
                    print(f"\n{result['name']}:")
                    
                    for failure in result['failure_details']:
                        print(f"  FAILURE: {failure[:200]}...")
                    
                    for error in result['error_details']:
                        print(f"  ERROR: {error[:200]}...")
        
        # Performance insights
        print(f"\nPerformance Insights:")
        fastest_suite = min(suite_results, key=lambda x: x['execution_time'])
        slowest_suite = max(suite_results, key=lambda x: x['execution_time'])
        
        print(f"  Fastest Suite: {fastest_suite['name']} ({fastest_suite['execution_time']:.2f}s)")
        print(f"  Slowest Suite: {slowest_suite['name']} ({slowest_suite['execution_time']:.2f}s)")
        
        # Recommendations
        print(f"\nRecommendations:")
        if overall_success_rate < 0.95:
            print("  - Address failing tests before proceeding with implementation")
        if any(result['errors'] > 0 for result in suite_results):
            print("  - Fix test errors which may indicate setup or import issues")
        if total_time > 300:  # 5 minutes
            print("  - Consider optimizing slow tests for faster development cycles")
        if overall_success_rate >= 0.95:
            print("  - Test suite is in good condition for development")
        
        # Return summary data
        summary = {
            'overall_success': overall_success_rate >= 0.95,
            'total_tests': self.total_tests,
            'total_failures': self.total_failures,
            'total_errors': self.total_errors,
            'total_skipped': self.total_skipped,
            'success_rate': overall_success_rate,
            'execution_time': total_time,
            'suite_results': suite_results
        }
        
        return summary


def main():
    """Main entry point for test runner."""
    runner = TestSuiteRunner()
    
    try:
        summary = runner.run_all_tests()
        
        # Exit with appropriate code
        if summary['overall_success']:
            print(f"\n✅ All tests passed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Some tests failed. Please review the results above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Test execution interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during test execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()