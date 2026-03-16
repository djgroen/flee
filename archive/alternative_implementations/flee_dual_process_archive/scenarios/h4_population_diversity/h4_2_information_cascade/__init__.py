"""
H4.2: Information Cascade Test Scenario

Tests information flow and decision correlation between S1 "scouts" and S2 "followers".
"""

from .cascade_generator import InformationCascadeGenerator
from .scout_follower_tracker import ScoutFollowerTracker
from .cascade_metrics import CascadeMetrics
from .information_flow_analyzer import InformationFlowAnalyzer

__all__ = ['InformationCascadeGenerator', 'ScoutFollowerTracker', 'CascadeMetrics', 'InformationFlowAnalyzer']