"""
H2: Social Connectivity Impact Scenarios

This package contains scenarios for testing Hypothesis 2 (Social Connectivity Effects)
in the dual-process refugee movement model.

Scenarios:
- H2.1: Hidden Information - Tests destination discovery through social networks
- H2.2: Dynamic Information Sharing - Tests real-time information sharing effectiveness
"""

from pathlib import Path

# Package metadata
__version__ = "1.0.0"
__author__ = "Dual Process Experiments Framework"

# Scenario paths
SCENARIO_DIR = Path(__file__).parent
H2_1_DIR = SCENARIO_DIR / "h2_1_hidden_information"
H2_2_DIR = SCENARIO_DIR / "h2_2_dynamic_information"

# Available scenarios
SCENARIOS = {
    "h2_1_hidden_information": {
        "name": "H2.1 Hidden Information",
        "description": "Tests destination discovery through social networks",
        "path": H2_1_DIR,
        "metrics_module": "h2_1_metrics"
    },
    "h2_2_dynamic_information": {
        "name": "H2.2 Dynamic Information Sharing", 
        "description": "Tests real-time information sharing effectiveness",
        "path": H2_2_DIR,
        "metrics_module": "h2_2_metrics"
    }
}

def get_scenario_info(scenario_name: str) -> dict:
    """Get information about a specific scenario."""
    return SCENARIOS.get(scenario_name, {})

def list_scenarios() -> list:
    """List all available H2 scenarios."""
    return list(SCENARIOS.keys())