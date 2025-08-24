#!/usr/bin/env python3
"""
Test script for the experiment execution system.

This script tests the ExperimentRunner, ProcessPoolManager, and metadata collection
functionality to ensure the experiment execution system works correctly.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the flee_dual_process directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from experiment_runner import (
    ExperimentRunner, ProcessPoolManager, ExperimentStateManager,
    ExperimentMetadataCollector, ResourceMonitor
)
from config_manager import ExperimentConfig


def test_resource_monitor():
    """Test the ResourceMonitor class."""
    print("Testing ResourceMonitor...")
    
    monitor = ResourceMonitor()
    
    # Test basic functionality
    monitor.start_monitoring()
    import time
    time.sleep(2)  # Let it collect some data
    monitor.stop_monitoring()
    
    usage = monitor.get_peak_usage()
    print(f"Peak memory: {usage['peak_memory_bytes'] / (1024**2):.1f} MB")
    print(f"Peak CPU: {usage['peak_cpu_percent']:.1f}%")
    
    assert usage['peak_memory_bytes'] > 0, "Should have recorded some memory usage"
    print("✓ ResourceMonitor test passed")


def test_experiment_metadata_collector():
    """Test the ExperimentMetadataCollector class."""
    print("\nTesting ExperimentMetadataCollector...")
    
    collector = ExperimentMetadataCollector()
    
    # Create a test experiment config
    experiment_config = ExperimentConfig(
        experiment_id="test_metadata",
        topology_type="linear",
        topology_params={"n_nodes": 5, "segment_distance": 50.0},
        scenario_type="spike",
        scenario_params={"start_day": 0, "peak_intensity": 0.8},
        cognitive_mode="dual_process",
        simulation_params={"awareness_level": 2},
        replications=1
    )
    
    # Create temporary experiment directory
    with tempfile.TemporaryDirectory() as temp_dir:
        experiment_dir = os.path.join(temp_dir, "test_experiment")
        os.makedirs(experiment_dir)
        
        # Create basic directory structure
        for subdir in ['input', 'output', 'logs', 'metadata']:
            os.makedirs(os.path.join(experiment_dir, subdir))
        
        # Create some test files
        with open(os.path.join(experiment_dir, 'input', 'test.csv'), 'w') as f:
            f.write("test,data\n1,2\n")
        
        with open(os.path.join(experiment_dir, 'output', 'result.csv'), 'w') as f:
            f.write("result,value\n3,4\n")
        
        # Collect metadata
        import time
        start_time = time.time()
        time.sleep(0.1)  # Simulate some execution time
        
        metadata = collector.collect_experiment_metadata(
            experiment_config, experiment_dir, start_time
        )
        
        # Validate metadata
        assert metadata['experiment_id'] == "test_metadata"
        assert metadata['execution_time_seconds'] > 0
        assert 'system_info' in metadata
        assert 'configuration' in metadata
        assert 'input_files' in metadata
        assert 'output_files' in metadata
        
        # Test metadata validation
        validation = collector.validate_metadata_integrity(metadata)
        assert validation['is_valid'], f"Metadata validation failed: {validation['errors']}"
        assert validation['completeness_score'] > 0.5
        
        print(f"✓ Collected metadata with completeness score: {validation['completeness_score']:.2f}")


def test_experiment_state_manager():
    """Test the ExperimentStateManager class."""
    print("\nTesting ExperimentStateManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        state_manager = ExperimentStateManager(temp_dir)
        
        # Test saving state
        test_state = {
            'status': 'running',
            'progress': 0.5,
            'data': {'key': 'value'}
        }
        
        state_file = state_manager.save_experiment_state("test_exp", test_state)
        assert os.path.exists(state_file)
        
        # Test loading state
        loaded_state = state_manager.load_experiment_state("test_exp")
        assert loaded_state is not None
        assert loaded_state['status'] == 'running'
        assert loaded_state['experiment_id'] == 'test_exp'
        
        # Test listing states
        states = state_manager.list_experiment_states()
        assert len(states) == 1
        assert states[0]['experiment_id'] == 'test_exp'
        
        print("✓ ExperimentStateManager test passed")


def test_process_pool_manager():
    """Test the ProcessPoolManager class."""
    print("\nTesting ProcessPoolManager...")
    
    manager = ProcessPoolManager(max_workers=2, retry_attempts=1)
    
    # Test resource status
    status = manager.get_resource_status()
    assert 'memory_usage_percent' in status
    assert 'cpu_usage_percent' in status
    assert status['max_workers'] == 2
    
    # Test retry statistics
    retry_stats = manager.get_retry_statistics()
    assert 'total_retry_attempts' in retry_stats
    assert retry_stats['total_retry_attempts'] == 0  # No retries yet
    
    print("✓ ProcessPoolManager test passed")


def test_experiment_runner_basic():
    """Test basic ExperimentRunner functionality."""
    print("\nTesting ExperimentRunner (basic functionality)...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock Flee executable (just a Python script that exits successfully)
        mock_flee = os.path.join(temp_dir, "mock_flee.py")
        with open(mock_flee, 'w') as f:
            f.write("""#!/usr/bin/env python3
import sys
import os
import time

# Create some mock output files
if len(sys.argv) >= 3:
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)
    
    # Create mock output files
    with open(os.path.join(output_dir, 'out.csv'), 'w') as f:
        f.write('day,location,population\\n0,camp1,100\\n')
    
    with open(os.path.join(output_dir, 'agents.out'), 'w') as f:
        f.write('Mock agent output\\n')
    
    time.sleep(0.1)  # Simulate some processing time

print("Mock Flee simulation completed")
sys.exit(0)
""")
        
        os.chmod(mock_flee, 0o755)
        
        # Create ExperimentRunner with mock executable
        runner = ExperimentRunner(
            max_parallel=1,
            base_output_dir=temp_dir,
            flee_executable=mock_flee,
            timeout=30
        )
        
        # Test directory setup
        experiment_dir = runner._setup_experiment_directory("test_basic")
        assert os.path.exists(experiment_dir)
        assert os.path.exists(os.path.join(experiment_dir, 'input'))
        assert os.path.exists(os.path.join(experiment_dir, 'output'))
        
        print("✓ ExperimentRunner basic functionality test passed")


def main():
    """Run all tests."""
    print("Running experiment execution system tests...")
    print("=" * 50)
    
    try:
        test_resource_monitor()
        test_experiment_metadata_collector()
        test_experiment_state_manager()
        test_process_pool_manager()
        test_experiment_runner_basic()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()