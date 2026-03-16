#!/usr/bin/env python3
"""
Setup script for Dual Process Experiments Framework

This script provides automated setup and configuration for the dual process
experiments framework, including dependency installation, configuration
validation, and performance optimization.
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import argparse


class DualProcessSetup:
    """Setup manager for dual process experiments framework."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.framework_dir = Path(__file__).parent
        self.base_dir = self.framework_dir.parent
        
    def log(self, message: str, level: str = "INFO"):
        """Log setup messages."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{level}] {message}")
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        self.log("Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log(f"Python {version.major}.{version.minor} is not supported. "
                    f"Please use Python 3.8 or higher.", "ERROR")
            return False
        
        self.log(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    
    def install_dependencies(self, dev: bool = False) -> bool:
        """Install required dependencies."""
        self.log("Installing dependencies...")
        
        try:
            # Install core dependencies
            requirements_file = self.framework_dir / "requirements_dual_process.txt"
            if requirements_file.exists():
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True, capture_output=not self.verbose)
                self.log("Core dependencies installed successfully")
            else:
                self.log("Requirements file not found, installing minimal dependencies", "WARNING")
                minimal_deps = ["numpy", "pandas", "scipy", "matplotlib", "pyyaml", "networkx"]
                subprocess.run([
                    sys.executable, "-m", "pip", "install"
                ] + minimal_deps, check=True, capture_output=not self.verbose)
            
            # Install development dependencies if requested
            if dev:
                dev_requirements = self.base_dir / "requirements_dev.txt"
                if dev_requirements.exists():
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", "-r", str(dev_requirements)
                    ], check=True, capture_output=not self.verbose)
                    self.log("Development dependencies installed successfully")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to install dependencies: {e}", "ERROR")
            return False
    
    def install_framework(self, editable: bool = False) -> bool:
        """Install the framework package."""
        self.log("Installing dual process framework...")
        
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if editable:
                cmd.extend(["-e", str(self.base_dir)])
            else:
                cmd.append(str(self.base_dir))
            
            subprocess.run(cmd, check=True, capture_output=not self.verbose)
            self.log("Framework installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to install framework: {e}", "ERROR")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that the installation is working correctly."""
        self.log("Verifying installation...")
        
        try:
            # Test basic imports
            test_imports = [
                "flee_dual_process.topology_generator",
                "flee_dual_process.scenario_generator",
                "flee_dual_process.config_manager",
                "flee_dual_process.experiment_runner",
                "flee_dual_process.analysis_pipeline"
            ]
            
            for module in test_imports:
                try:
                    __import__(module)
                    self.log(f"✓ {module}")
                except ImportError as e:
                    self.log(f"✗ {module}: {e}", "ERROR")
                    return False
            
            # Test basic functionality
            self.log("Testing basic functionality...")
            
            test_code = '''
import tempfile
import os
from flee_dual_process.topology_generator import LinearTopologyGenerator
from flee_dual_process.config_manager import ConfigurationManager

# Test topology generation
with tempfile.TemporaryDirectory() as temp_dir:
    base_config = {"output_dir": temp_dir}
    generator = LinearTopologyGenerator(base_config)
    locations_file, routes_file = generator.generate_linear(
        n_nodes=3, segment_distance=50.0, start_pop=1000, pop_decay=0.8
    )
    
    if not (os.path.exists(locations_file) and os.path.exists(routes_file)):
        raise RuntimeError("Topology generation failed")

# Test configuration management
config_manager = ConfigurationManager()
config = config_manager.create_cognitive_config("dual_process")

if not isinstance(config, dict) or "two_system_decision_making" not in config:
    raise RuntimeError("Configuration generation failed")

print("Basic functionality test passed")
'''
            
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✓ Basic functionality test passed")
                return True
            else:
                self.log(f"✗ Basic functionality test failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Verification failed: {e}", "ERROR")
            return False
    
    def create_config_directory(self) -> bool:
        """Create user configuration directory."""
        self.log("Creating configuration directory...")
        
        try:
            config_dir = Path.home() / ".flee_dual_process"
            config_dir.mkdir(exist_ok=True)
            
            # Copy default configuration templates
            templates_src = self.framework_dir / "configs" / "production_templates.yml"
            templates_dst = config_dir / "default_templates.yml"
            
            if templates_src.exists():
                shutil.copy2(templates_src, templates_dst)
                self.log(f"Configuration templates copied to {templates_dst}")
            
            # Create directories for experiments and results
            (config_dir / "experiments").mkdir(exist_ok=True)
            (config_dir / "results").mkdir(exist_ok=True)
            (config_dir / "logs").mkdir(exist_ok=True)
            
            self.log(f"Configuration directory created at {config_dir}")
            return True
            
        except Exception as e:
            self.log(f"Failed to create configuration directory: {e}", "ERROR")
            return False
    
    def run_performance_test(self) -> bool:
        """Run a quick performance test."""
        self.log("Running performance test...")
        
        try:
            test_code = '''
import time
import tempfile
from flee_dual_process.topology_generator import LinearTopologyGenerator
from flee_dual_process.scenario_generator import SpikeConflictGenerator
from flee_dual_process.config_manager import ConfigurationManager, ExperimentConfig

# Performance test
start_time = time.time()

with tempfile.TemporaryDirectory() as temp_dir:
    # Generate topology
    base_config = {"output_dir": temp_dir}
    topology_generator = LinearTopologyGenerator(base_config)
    locations_file, routes_file = topology_generator.generate_linear(
        n_nodes=10, segment_distance=50.0, start_pop=1000, pop_decay=0.8
    )
    
    # Generate scenario
    scenario_generator = SpikeConflictGenerator(locations_file)
    conflicts_file = scenario_generator.generate_spike_conflict(
        origin="Origin", start_day=5, peak_intensity=0.8, output_dir=temp_dir
    )
    
    # Create configuration
    config_manager = ConfigurationManager()
    config = config_manager.create_cognitive_config("dual_process")
    
    # Create experiment config
    experiment_config = ExperimentConfig(
        experiment_id="performance_test",
        topology_type="linear",
        topology_params={"n_nodes": 10, "segment_distance": 50.0, "start_pop": 1000, "pop_decay": 0.8},
        scenario_type="spike",
        scenario_params={"origin": "Origin", "start_day": 5, "peak_intensity": 0.8},
        cognitive_mode="dual_process",
        simulation_params=config,
        replications=1
    )

execution_time = time.time() - start_time
print(f"Performance test completed in {execution_time:.4f} seconds")

if execution_time > 5.0:
    print("WARNING: Performance test took longer than expected")
else:
    print("Performance test passed")
'''
            
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log("✓ Performance test completed")
                if self.verbose:
                    self.log(result.stdout.strip())
                return True
            else:
                self.log(f"✗ Performance test failed: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("✗ Performance test timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Performance test failed: {e}", "ERROR")
            return False
    
    def setup_complete(self, mode: str) -> None:
        """Display setup completion message."""
        print("\n" + "="*60)
        print("🎉 Dual Process Experiments Framework Setup Complete!")
        print("="*60)
        
        print(f"\nInstallation mode: {mode}")
        print(f"Framework location: {self.framework_dir}")
        
        print("\n📚 Quick Start:")
        print("1. Check the deployment guide: flee_dual_process/DEPLOYMENT_GUIDE.md")
        print("2. Run example experiments: python flee_dual_process/examples/basic_experiment.py")
        print("3. View configuration templates: ~/.flee_dual_process/default_templates.yml")
        
        print("\n🔧 Useful Commands:")
        print("- Run tests: python -m pytest flee_dual_process/test_integration_simple.py")
        print("- View documentation: python -m pydoc flee_dual_process.config_manager")
        print("- Performance test: python flee_dual_process/test_performance_optimization.py")
        
        print("\n📖 Documentation:")
        print("- API Reference: flee_dual_process/docs/api/")
        print("- Tutorials: flee_dual_process/docs/tutorials/")
        print("- Examples: flee_dual_process/examples/")
        
        print("\n" + "="*60)


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup script for Dual Process Experiments Framework"
    )
    parser.add_argument(
        "--mode", 
        choices=["user", "dev", "minimal"],
        default="user",
        help="Installation mode (default: user)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency installation"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip verification tests"
    )
    
    args = parser.parse_args()
    
    setup = DualProcessSetup(verbose=args.verbose)
    
    print("🚀 Starting Dual Process Experiments Framework Setup")
    print(f"Mode: {args.mode}")
    
    # Check Python version
    if not setup.check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not args.skip_deps:
        if not setup.install_dependencies(dev=(args.mode == "dev")):
            sys.exit(1)
    
    # Install framework
    if not setup.install_framework(editable=(args.mode == "dev")):
        sys.exit(1)
    
    # Create configuration directory
    if not setup.create_config_directory():
        sys.exit(1)
    
    # Run verification tests
    if not args.skip_tests:
        if not setup.verify_installation():
            sys.exit(1)
        
        if args.mode != "minimal":
            if not setup.run_performance_test():
                print("⚠️  Performance test failed, but installation is functional")
    
    # Setup complete
    setup.setup_complete(args.mode)


if __name__ == "__main__":
    main()