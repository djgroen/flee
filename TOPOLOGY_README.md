# Topology and V3 Experiment Workflow

Canonical workflow for nuclear evacuation topologies and V3 dual-process experiments.

## Full Pipeline (Generate → Run → Animate)

```bash
# One-liner (runs all three steps)
./run_full_pipeline.sh

# Or step by step:
# 1. Generate topologies
python generate_nuclear_topologies.py

# 2. Full parameter sweep (ring, linear, star)
python run_nuclear_parameter_sweep.py
# Output: data/results/{ring,linear,star}/results_a*_b*_s*.csv

# 3. Create analysis figures (heatmaps, P_S2 plots)
python analyze_fork_experiments.py --base data/results
# Output: data/results/figures/heatmap_avg_p_s2.png, heatmap_peak_p_s2.png, p_s2_vs_conflict.png, etc.

# 4. Create animations from results
python animate_agents.py --topology ring --results data/results/ring/results_a2.0_b2.0_s0.csv -o data/experiments/figures/ring_agents.mp4
python animate_agents.py --topology linear --results data/results/linear/results_a2.0_b2.0_s0.csv -o data/experiments/figures/linear_agents.mp4
python animate_agents.py --topology star --results data/results/star/results_a2.0_b2.0_s0.csv -o data/experiments/figures/star_agents.mp4
```

Figures: `data/results/figures/` (heatmap_avg_p_s2.png, heatmap_peak_p_s2.png, p_s2_vs_conflict.png, p_s2_over_time.png, evacuation_by_params.png)

## Model Comparison Pipeline (4 Variants)

Run original FLEE, S1-only, S2-only, and full S1/S2 across topologies; generate journal-quality diagnostic plots.

```bash
# Full run (4 × 3 = 12 simulations, ~10k agents each)
./run_model_comparison_pipeline.sh

# Quick test (500 agents, 15 timesteps)
./run_model_comparison_pipeline.sh --quick
```

Output: `data/model_comparison/figures/`
- `model_comparison_multipanel.png` — 9-panel diagnostic (topology metrics, evacuation, P_S2, timing, etc.)
- `model_comparison_arrival_rates.png` — Arrival rate time series at SafeZones (sanity check: Original ≈ S1-only)
- `model_comparison_heatmaps.png` — Evacuation rate, mean/peak P_S2, evacuation time (topology × variant)
- `network_spatial_{ring,linear,star}.png` — Static network plots: node color = conflict; node size = P_move (S1), σ (S2), or proximity to safety

Note: Original and S1-only are designed to be identical (P_S2≈0). Arrival-rate panels verify this.
Original FLEE already uses `awareness_level` to look beyond immediate neighbors when scoring
routes — so it has deliberative elements. S2 mode increases look-ahead further.

---

## EasyVVUQ Sensitivity Analysis

```bash
pip install easyvvuq chaospy   # one-time

# Quick run (16 samples across ring/star/linear)
python run_easyvvuq_campaign.py

# Sobol indices (~200 runs)
python run_easyvvuq_campaign.py --sobol

# Visualize results
python visualize_easyvvuq.py
```

Output: `data/easyvvuq/s1s2_campaign/` with figures, evacuation_by_topology.png, Sobol bar charts.

---

## Individual Steps

### Generate Topologies

```bash
python generate_nuclear_topologies.py
```

Creates `topologies/ring`, `topologies/linear`, `topologies/star` with FLEE input CSVs:
- `locations.csv`, `routes.csv`, `conflicts.csv`, `closures.csv`, `sim_period.csv`

### Run PR Checklist

```bash
python run_pr_checklist.py
```

Runs default-off and default-on S1/S2 simulations on ring topology. Verifies V3 output.

### Run V3 Experiments

```bash
mkdir -p experiments/outputs
python experiments/run_v3_experiments.py
```

Runs 6 experiments:
1. Parameter sweep heatmaps (α × β)
2. 72-hour conflict trajectory
3. Non-compensability validation
4. Population heterogeneity
5. Generate comparison run configs
6. Topology comparison (ring, linear, star) — requires topologies from step 1

### Run Topology Parameter Sweep

```bash
python run_nuclear_parameter_sweep.py
```

Full parameter sweep across ring, linear, star with (α, β) grid. Output: `data/results/`.

### Create Animations

```bash
python animate_agents.py --topology {ring|star|linear} --results PATH_TO_RESULTS_CSV [-o output.mp4]
```

Requires results CSV with `location`, `timestep`, `agent_id` columns (from run_nuclear_parameter_sweep or Experiment 6).

### Model Comparison (4 Variants)

```bash
python run_model_comparison.py          # Full: 10k agents × 30 steps
python run_model_comparison.py --quick  # Quick: 500 agents × 15 steps
python create_model_diagnostic_plots.py # Multipanel figures
```

---

## Directory Layout

```
topologies/
  ring/input_csv/     # locations.csv, routes.csv, conflicts.csv, ...
  linear/input_csv/
  star/input_csv/

configs/
  ring_topology.yml
  linear_topology.yml
  star_topology.yml

data/
  results/            # run_nuclear_parameter_sweep output
    ring/
    linear/
    star/
    figures/          # analyze_fork_experiments output (heatmaps, P_S2 plots)
  model_comparison/   # run_model_comparison output
    ring|linear|star/
      original|s1_only|s2_only|full_s1s2/
    figures/          # create_model_diagnostic_plots output
  experiments/figures/   # animate_agents output (mp4)
  easyvvuq/s1s2_campaign/  # EasyVVUQ output

experiments/
  run_v3_experiments.py
  outputs/            # heatmaps, trajectories, topology_comparison/
  configs/            # simsetting_runN.yml, topology_quick_*.yml
```
