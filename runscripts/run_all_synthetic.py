#!/usr/bin/env python3
"""
Run all synthetic topologies and generate figures/animations.
Uses standardized output layout: output/results/synthetic/<topology>, output/figures/synthetic/<topology>.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TOPOLOGIES = ["linear", "ring", "star", "fully_connected"]


def main():
    print("=" * 60)
    print("Running synthetic experiments (all topologies, threshold-based SwitchEngine)")
    print("=" * 60)

    for topo in TOPOLOGIES:
        print(f"\n--- Topology: {topo} ---")
        ret = subprocess.run(
            [sys.executable, "runscripts/run_synthetic.py", "--topology", topo],
            cwd=REPO_ROOT,
        )
        if ret.returncode != 0:
            print(f"FAILED: run_synthetic.py --topology {topo}")
            return ret.returncode

    print("\n--- Generating figures and animations ---")
    ret = subprocess.run(
        [sys.executable, "figures/make_synthetic_figures.py", "--topology", "all"],
        cwd=REPO_ROOT,
    )
    if ret.returncode != 0:
        print("FAILED: make_synthetic_figures.py --topology all")
        return ret.returncode

    print("\n" + "=" * 60)
    print("Done. Outputs:")
    print("  - output/results/synthetic/<topology>/  (data)")
    print("  - output/figures/synthetic/<topology>/   (figures + animations)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
