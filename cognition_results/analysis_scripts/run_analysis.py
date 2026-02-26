#!/usr/bin/env python3
"""
Cognition Results Analysis Script

Run this script to generate all results and figures locally.
Results are saved in cognition_results/ directory.
"""

import sys
import os
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent / 'code'))

def main():
    print("🧠 Cognition Results Analysis")
    print("=" * 40)
    
    # Import and run analysis
    try:
        from systematic_network_scaling_framework import main as run_scaling
        from comprehensive_visualization_suite import main as run_viz
        
        print("📊 Running systematic network scaling...")
        run_scaling()
        
        print("\n📈 Generating visualizations...")
        run_viz()
        
        print("\n🎯 Analysis complete!")
        print("   Results saved in cognition_results/")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r config/requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
