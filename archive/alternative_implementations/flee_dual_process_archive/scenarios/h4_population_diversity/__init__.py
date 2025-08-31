"""
H4: Population Diversity Scenarios

This module contains scenarios for testing Hypothesis 4 of dual-process theory:
Mixed S1/S2 populations outperform homogeneous populations in adaptive responses.
"""

from .h4_1_adaptive_shock import AdaptiveShockScenario
from .h4_2_information_cascade import InformationCascadeScenario

__all__ = ['AdaptiveShockScenario', 'InformationCascadeScenario']