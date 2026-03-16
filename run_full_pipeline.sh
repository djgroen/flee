#!/bin/bash
# Full V3 pipeline: generate topologies → parameter sweep → animations
# Run from repo root: ./run_full_pipeline.sh

set -e
echo "=== 1. Generate topologies ==="
python generate_nuclear_topologies.py

echo ""
echo "=== 2. Parameter sweep (ring, linear, star) ==="
python run_nuclear_parameter_sweep.py

echo ""
echo "=== 3. Create analysis figures (heatmaps, P_S2 plots) ==="
mkdir -p data/results/figures
python analyze_fork_experiments.py --base data/results
echo "  Created heatmap_avg_p_s2.png, heatmap_peak_p_s2.png, p_s2_vs_conflict.png, etc."

echo ""
echo "=== 4. Create animations ==="
mkdir -p data/experiments/figures
for topo in ring linear star; do
  results=$(ls data/results/$topo/results_a2.0_b2.0_s0.csv 2>/dev/null | head -1)
  if [ -n "$results" ]; then
    python animate_agents.py --topology $topo --results "$results" -o data/experiments/figures/${topo}_agents.mp4
    echo "  Created data/experiments/figures/${topo}_agents.mp4"
  else
    echo "  No results for $topo (run sweep first)"
  fi
done

echo ""
echo "=== Pipeline complete ==="
echo "Figures: data/results/figures/"
echo "Animations: data/experiments/figures/"
