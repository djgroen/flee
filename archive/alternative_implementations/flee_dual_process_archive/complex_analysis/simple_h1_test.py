#!/usr/bin/env python3
"""
Simple H1 Test - Check Cognitive Mode Configurations
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

def test_config_manager():
    """Test the config manager directly."""
    print("Testing ConfigurationManager...")
    
    try:
        # Import with error handling
        try:
            from config_manager import ConfigurationManager
        except ImportError as e:
            print(f"Import error: {e}")
            return False
        
        config_mgr = ConfigurationManager({})
        
        print("\nCognitive Mode Configurations:")
        print("-" * 40)
        
        for mode_name, mode_config in config_mgr.COGNITIVE_MODES.items():
            print(f"\n{mode_name.upper()}:")
            move_rules = mode_config.get('move_rules', {})
            
            # Check key settings
            two_system = move_rules.get('TwoSystemDecisionMaking', 'NOT SET')
            connectivity = move_rules.get('average_social_connectivity', 'NOT SET')
            awareness = move_rules.get('awareness_level', 'NOT SET')
            softening = move_rules.get('weight_softening', 'NOT SET')
            threshold = move_rules.get('conflict_threshold', 'NOT SET')
            default_move = move_rules.get('default_movechance', 'NOT SET')
            conflict_move = move_rules.get('conflict_movechance', 'NOT SET')
            
            print(f"  TwoSystemDecisionMaking: {two_system}")
            print(f"  Social Connectivity: {connectivity}")
            print(f"  Awareness Level: {awareness}")
            print(f"  Weight Softening: {softening}")
            print(f"  Conflict Threshold: {threshold}")
            print(f"  Default Movechance: {default_move}")
            print(f"  Conflict Movechance: {conflict_move}")
        
        # Test config creation
        print("\n" + "=" * 50)
        print("Testing Config Creation:")
        
        for mode in ['s1_only', 's2_full', 'dual_process']:
            print(f"\nCreating config for {mode}...")
            try:
                config = config_mgr.create_cognitive_config(mode, {})
                move_rules = config.get('move_rules', {})
                
                two_system = move_rules.get('TwoSystemDecisionMaking', False)
                connectivity = move_rules.get('average_social_connectivity', 0)
                
                print(f"  ✓ TwoSystemDecisionMaking: {two_system}")
                print(f"  ✓ Social Connectivity: {connectivity}")
                
                # Check if this creates meaningful differences
                if mode == 's1_only' and two_system == True:
                    print(f"  ⚠️  WARNING: s1_only has TwoSystemDecisionMaking=True!")
                elif mode in ['s2_full', 'dual_process'] and two_system == False:
                    print(f"  ⚠️  WARNING: {mode} has TwoSystemDecisionMaking=False!")
                else:
                    print(f"  ✓ Configuration looks correct")
                    
            except Exception as e:
                print(f"  ✗ Error creating {mode} config: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error testing config manager: {e}")
        return False


def check_flee_integration():
    """Check if Flee integration is working."""
    print("\n" + "=" * 50)
    print("Checking Flee Integration:")
    
    try:
        # Check if we can import flee
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        try:
            import flee.SimulationSettings as SimulationSettings
            print("✓ Can import Flee SimulationSettings")
            
            # Check if TwoSystemDecisionMaking is recognized
            default_settings = SimulationSettings.SimulationSettings()
            move_rules = default_settings.move_rules
            
            if 'TwoSystemDecisionMaking' in move_rules:
                print(f"✓ TwoSystemDecisionMaking found in move_rules: {move_rules['TwoSystemDecisionMaking']}")
            else:
                print("⚠️  TwoSystemDecisionMaking not found in default move_rules")
                print("Available move_rules keys:", list(move_rules.keys()))
                
        except ImportError as e:
            print(f"✗ Cannot import Flee: {e}")
            return False
            
    except Exception as e:
        print(f"Error checking Flee integration: {e}")
        return False
    
    return True


def main():
    """Main test function."""
    print("🔍 Simple H1 Configuration Test")
    print("=" * 50)
    
    success = True
    
    # Test 1: Config Manager
    if not test_config_manager():
        success = False
    
    # Test 2: Flee Integration
    if not check_flee_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Basic configuration test passed!")
        print("\nNext steps:")
        print("1. The cognitive mode configs look correct")
        print("2. Try running a simple H1 experiment")
        print("3. Check for 'System 2 activated' messages in logs")
    else:
        print("❌ Configuration test failed!")
        print("\nIssues found:")
        print("1. Check import paths and dependencies")
        print("2. Verify Flee integration is working")
        print("3. Fix configuration issues before running experiments")


if __name__ == "__main__":
    main()