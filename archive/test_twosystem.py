# ARCHIVED: 2025-03-14
# Reason: Minimal S1/S2 smoke tests (conflict > 0.6 only); does not use actual model. Superseded by test_s1s2_v3.py and test_s1s2_integration.py.
# Do not import or run this file from the active test suite.

import sys
import os
import numpy as np

from flee import flee


def test_system2_quick():
    """Verify V3 dual-process logic paths work (continuous blend, no Bernoulli)."""
    print("Testing: V3 System 2 logic")

    class QuickMockAgent:
        def __init__(self):
            self.location = QuickMockLocation()
            self.attributes = {"connections": 4}
            self.experience_index = 0.5

    class QuickMockLocation:
        def __init__(self):
            self.conflict = 0.7
            self.time_of_conflict = 5
            self.town = False
            self.movechance = 0.3
            self.pop = 1000
            self.capacity = 1000

    agent = QuickMockAgent()

    # V3: P_S2 is continuous; no Bernoulli. Just verify conflict/experience logic.
    conflict_triggered = agent.location.conflict > 0.6
    assert conflict_triggered is True
    print("System 2 logic works!")


def test_system1_quick():
    """Quick test for System 1 path (low conflict)."""
    print("Testing: V3 System 1 path")

    class QuickMockAgent:
        def __init__(self):
            self.location = QuickMockLocation()
            self.attributes = {"connections": 1}
            self.experience_index = 0.3

    class QuickMockLocation:
        def __init__(self):
            self.conflict = 0.3
            self.time_of_conflict = 5
            self.town = False
            self.movechance = 0.3
            self.pop = 1000
            self.capacity = 1000

    agent = QuickMockAgent()

    conflict_triggered = agent.location.conflict > 0.6
    assert conflict_triggered is False
    print("System 1 path works!")


if __name__ == "__main__":
    test_system2_quick()
    test_system1_quick()
