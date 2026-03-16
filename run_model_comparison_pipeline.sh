#!/bin/bash
# Model comparison pipeline: run 4 variants (original, S1-only, S2-only, full S1/S2) and create diagnostic plots.
# Run from repo root: ./run_model_comparison_pipeline.sh
# Use --quick for fast testing (500 agents, 15 timesteps).

set -e
echo "=== 1. Generate topologies (if missing) ==="
if [ ! -d "topologies/ring" ]; then
  python generate_nuclear_topologies.py
else
  echo "  Topologies exist, skipping."
fi

echo ""
echo "=== 2. Run model comparison (4 variants × 3 topologies) ==="
python run_model_comparison.py "$@"

echo ""
echo "=== 3. Create multipanel diagnostic plots ==="
python create_model_diagnostic_plots.py

echo ""
echo "=== Model comparison complete ==="
echo "Figures: data/model_comparison/figures/"
echo "  - model_comparison_multipanel.png  (9-panel diagnostic)"
echo "  - model_comparison_heatmaps.png    (topology × variant heatmaps)"
