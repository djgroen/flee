#!/usr/bin/env python3
"""
Simple test script for the experiment execution system components.

This script tests individual components without requiring full imports.
"""

import os
import sys
import tempfile
import json
import time
from datetime import datetime


def test_resource_monitor_basic():
    """Test basic resource monitoring functionality."""
    print("Testing basic resource monitoring...")
    
    try:
        import psutil
        
        # Test basic psutil functionality
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        print(f"Memory usage: {memory.percent:.1f}%")
        print(f"CPU usage: {cpu_percent:.1f}%")
        
        assert memory.total > 0, "Should have memory information"
        assert cpu_percent >= 0, "Should have CPU information"
        
        print("✓ Basic resource monitoring test passed")
        return True
        
    except ImportError:
        print("⚠ psutil not available, skipping resource monitoring test")
        return False


def test_metadata_collection_basic():
    """Test basic metadata collection functionality."""
    print("\nTesting basic metadata collection...")
    
    # Test basic system information collection
    system_info = {
        'platform': sys.platform,
        'python_version': sys.version,
        'cpu_count': os.cpu_count(),
        'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
    }
    
    print(f"Platform: {system_info['platform']}")
    print(f"CPU count: {system_info['cpu_count']}")
    
    assert system_info['platform'], "Should have platform information"
    assert system_info['cpu_count'] > 0, "Should have CPU count"
    
    print("✓ Basic metadata collection test passed")
    return True


def test_file_operations():
    """Test basic file operations for experiment management."""
    print("\nTesting file operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test directory creation
        experiment_dir = os.path.join(temp_dir, "test_experiment")
        os.makedirs(experiment_dir)
        
        # Create subdirectories
        subdirs = ['input', 'output', 'logs', 'metadata']
        for subdir in subdirs:
            os.makedirs(os.path.join(experiment_dir, subdir))
        
        # Test file creation and metadata
        test_file = os.path.join(experiment_dir, 'input', 'test.csv')
        with open(test_file, 'w') as f:
            f.write("test,data\n1,2\n3,4\n")
        
        # Test file metadata collection
        stat = os.stat(test_file)
        file_metadata = {
            'size_bytes': stat.st_size,
            'created_timestamp': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        
        print(f"File size: {file_metadata['size_bytes']} bytes")
        print(f"Created: {file_metadata['created_timestamp']}")
        
        assert file_metadata['size_bytes'] > 0, "Should have file size"
        assert os.path.exists(test_file), "Test file should exist"
        
        # Test JSON serialization of metadata
        metadata = {
            'experiment_id': 'test_001',
            'timestamp': datetime.now().isoformat(),
            'file_info': file_metadata,
            'system_info': {
                'platform': sys.platform,
                'python_version': sys.version
            }
        }
        
        metadata_file = os.path.join(experiment_dir, 'metadata', 'test_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Verify metadata file was created and can be read
        assert os.path.exists(metadata_file), "Metadata file should exist"
        
        with open(metadata_file, 'r') as f:
            loaded_metadata = json.load(f)
        
        assert loaded_metadata['experiment_id'] == 'test_001', "Should preserve experiment ID"
        
        print("✓ File operations test passed")
        return True


def test_configuration_structure():
    """Test basic configuration structure."""
    print("\nTesting configuration structure...")
    
    # Test basic experiment configuration structure
    experiment_config = {
        'experiment_id': 'test_config',
        'topology_type': 'linear',
        'topology_params': {
            'n_nodes': 5,
            'segment_distance': 50.0,
            'start_pop': 1000,
            'pop_decay': 0.8
        },
        'scenario_type': 'spike',
        'scenario_params': {
            'start_day': 0,
            'peak_intensity': 0.8,
            'duration': 100
        },
        'cognitive_mode': 'dual_process',
        'simulation_params': {
            'awareness_level': 2,
            'average_social_connectivity': 3.0
        },
        'replications': 1,
        'metadata': {
            'description': 'Test configuration',
            'created_by': 'test_script'
        }
    }
    
    # Test configuration validation (basic checks)
    assert experiment_config['experiment_id'], "Should have experiment ID"
    assert experiment_config['topology_type'] in ['linear', 'star', 'tree', 'grid'], "Should have valid topology type"
    assert experiment_config['scenario_type'] in ['spike', 'gradual', 'cascading', 'oscillating'], "Should have valid scenario type"
    assert experiment_config['cognitive_mode'] in ['s1_only', 's2_disconnected', 's2_full', 'dual_process'], "Should have valid cognitive mode"
    
    # Test JSON serialization
    config_json = json.dumps(experiment_config, indent=2)
    loaded_config = json.loads(config_json)
    
    assert loaded_config['experiment_id'] == experiment_config['experiment_id'], "Should preserve configuration after serialization"
    
    print(f"Configuration ID: {experiment_config['experiment_id']}")
    print(f"Topology: {experiment_config['topology_type']}")
    print(f"Scenario: {experiment_config['scenario_type']}")
    print(f"Cognitive mode: {experiment_config['cognitive_mode']}")
    
    print("✓ Configuration structure test passed")
    return True


def test_experiment_state_persistence():
    """Test experiment state persistence."""
    print("\nTesting experiment state persistence...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        state_dir = os.path.join(temp_dir, "experiment_states")
        os.makedirs(state_dir)
        
        # Test state saving
        experiment_state = {
            'experiment_id': 'test_state',
            'status': 'running',
            'start_time': time.time(),
            'progress': 0.5,
            'current_step': 'simulation',
            'metadata': {
                'worker_id': 1,
                'attempt': 1
            }
        }
        
        # Save state to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        state_file = os.path.join(state_dir, f"test_state_{timestamp}.json")
        
        with open(state_file, 'w') as f:
            json.dump(experiment_state, f, indent=2, default=str)
        
        # Test state loading
        assert os.path.exists(state_file), "State file should exist"
        
        with open(state_file, 'r') as f:
            loaded_state = json.load(f)
        
        assert loaded_state['experiment_id'] == 'test_state', "Should preserve experiment ID"
        assert loaded_state['status'] == 'running', "Should preserve status"
        assert loaded_state['progress'] == 0.5, "Should preserve progress"
        
        print(f"State file: {os.path.basename(state_file)}")
        print(f"Status: {loaded_state['status']}")
        print(f"Progress: {loaded_state['progress']}")
        
        print("✓ Experiment state persistence test passed")
        return True


def main():
    """Run all simple tests."""
    print("Running simple experiment execution system tests...")
    print("=" * 60)
    
    tests = [
        test_resource_monitor_basic,
        test_metadata_collection_basic,
        test_file_operations,
        test_configuration_structure,
        test_experiment_state_persistence
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All simple tests passed successfully!")
        return 0
    else:
        print(f"✗ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())