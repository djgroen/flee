# Synthetic verification topologies

This directory contains synthetic agent-based simulations used to verify
the dual-process cognitive architecture before empirical calibration.
These are not real conflict cases and do not follow flee's conflict_input
convention.

## Contents
- `run_comparison_ring.py` — 10-location linear chain, four-condition
  comparison (original_flee, s1_only, s2_only, full_mixture).
  Run from repository root: `python synthetic/run_comparison_ring.py`
- `results/comparison_ring/` — CSV outputs from the comparison run.

## Theoretical basis
See main.tex Section 5.2 for phase boundary definitions (t*, t**).
See tests/test_s1s2_integration.py for the four topology-independent
predictions tested against these results.
