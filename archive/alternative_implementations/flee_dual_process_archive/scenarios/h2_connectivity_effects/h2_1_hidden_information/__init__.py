"""
H2.1 Hidden Information Scenario

This scenario tests whether socially connected agents can discover better destinations
that are not immediately visible to isolated agents.
"""

from .agent_config import AgentTypeConfig, InformationSharingMechanics
from .h2_1_metrics import analyze_h2_1_scenario, generate_h2_1_report

__all__ = [
    'AgentTypeConfig',
    'InformationSharingMechanics', 
    'analyze_h2_1_scenario',
    'generate_h2_1_report'
]