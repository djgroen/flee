#!/usr/bin/env python3
"""
Test YAML reading to debug the S2 threshold issue
"""

import yaml
from flee.SimulationSettings import fetchss

def test_yaml_reading():
    """Test YAML reading"""
    
    ymlfile = "proper_10k_agent_experiments/star_n7_medium_s2_10k/simsetting.yml"
    
    print(f"Reading YAML file: {ymlfile}")
    
    with open(ymlfile) as f:
        dp = yaml.safe_load(f)
    
    print(f"YAML content: {dp}")
    
    # Test fetchss function
    result = fetchss(dp, "two_system_decision_making", False)
    print(f"fetchss result: {result} (type: {type(result)})")
    
    # Test float conversion
    float_result = float(result)
    print(f"float conversion: {float_result}")

if __name__ == "__main__":
    test_yaml_reading()






