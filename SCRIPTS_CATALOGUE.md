# Run Scripts and Animation Catalogue

Catalogue of run scripts, experiment runners, and visualization/animation tools. Updated after S1/S2 binary gate refactor.

**S1/S2 documentation:** See **README_S1S2.md** for model overview, config, and merge notes.

---

## Core FLEE Run Scripts (KEEP)

| Script | Purpose | Usage |
|--------|---------|-------|
| `runscripts/run.py` | Standard FLEE: CSV-based refugee simulation with validation data | `python run.py <csv_dir> <refugee_data_dir> <days> [simsetting.yml]` |
| `runscripts/run_par.py` | Parallel FLEE (pflee) | Same args as run.py |
| `runscripts/run_UNHCR_uncertainty.py` | UNHCR uncertainty variant | Similar to run.py |

**Note:** These use generic CSV input (locations.csv, routes.csv, etc.) — not the nuclear topologies.

---

## S1/S2 Nuclear Experiments (KEEP)

| Script | Purpose | Usage |
|--------|---------|-------|
| `run_nuclear_parameter_sweep.py` | **Core sweeper**: ring/star/linear topologies, α/β params | `python run_nuclear_parameter_sweep.py` or import `ParameterSweeper` |
| `run_fork_experiments.py` | Wrapper: runs sweep to `data/experiments/` | `python run_fork_experiments.py` |
| `run_pr_checklist.py` | PR validation: default-off + default-on S1/S2 | `python run_pr_checklist.py` |
| `run_easyvvuq_campaign.py` | EasyVVUQ sensitivity analysis (α, β, topology) | `python run_easyvvuq_campaign.py [-n 16] [--sobol]` |
| `run_easyvvuq_single.py` | Single run (called by EasyVVUQ executor) | Not run directly |
| `run_omega_diagnostic.py` | Omega(β) diagnostic for model nonlinearity | `python run_omega_diagnostic.py` |

**Topologies:** ring, star, linear (from `topologies/{name}/input_csv/`).

---

## Animation Scripts (KEEP — Important)

| Script | Purpose | Usage |
|--------|---------|-------|
| `animate_agents.py` | **Primary animation**: agents on topology layout (mp4/gif) | `python animate_agents.py --topology ring --results data/experiments/ring/results_a2.0_b2.0_s0.csv -o out.mp4` |
| `visualize_refugee_movements.py` | Refugee movement visualization (S1/S2 colored) | Loads from scenario dirs / topology CSVs |
| `flee/postprocessing/video_agents.py` | FLEE postprocessing: agent video from agents.out.* | For standard FLEE output |
| `flee/postprocessing/video_links.py` | FLEE postprocessing: link flow video | For standard FLEE output |

**animate_agents.py** expects `results_*.csv` from `run_nuclear_parameter_sweep` / `run_fork_experiments` (columns: timestep, agent_id, location, p_s2, etc.). See **DATA_ORGANIZATION.md** for output layout.

---

## Analysis & Visualization (KEEP)

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze_fork_experiments.py` | Analyze `data/experiments/` results | `python analyze_fork_experiments.py` |
| `visualize_easyvvuq.py` | EasyVVUQ results: scatter, Sobol, heatmaps | `python visualize_easyvvuq.py [--campaign-dir PATH]` |

---

## Other Simulations (KEEP)

| Script | Purpose | Usage |
|--------|---------|-------|
| `nuclear_evacuation_simulations.py` | Idealized nuclear evacuations, creates topologies | Uses current S1/S2 model (`calculateMoveChance`) |

---

## Removed (Broken — Deleted)

| Script | Reason |
|--------|--------|
| ~~`run_all_10k_experiments.py`~~ | Imports `calculate_systematic_s2_activation` (removed in binary gate refactor) |
| ~~`generate_10k_agent_visualizations.py`~~ | Depends on output from `run_all_10k_experiments` |

---

## Typical Workflows

### Quick S1/S2 validation
```bash
python run_pr_checklist.py
```

### Run experiments and animate
```bash
python run_fork_experiments.py
python analyze_fork_experiments.py
python animate_agents.py --topology ring --results data/experiments/ring/results_a2.0_b2.0_s0.csv -o ring_anim.mp4
```

### EasyVVUQ sensitivity analysis
```bash
pip install easyvvuq chaospy
python run_easyvvuq_campaign.py -n 16
python visualize_easyvvuq.py
```

### Full parameter sweep (ring, star, linear)
```bash
python -c "
from run_nuclear_parameter_sweep import ParameterSweeper
sweeper = ParameterSweeper(output_base_dir='data/results')
sweeper.sweep(limited=True)   # or limited=False for full α,β grid
"
```

---

## Test Data Run Scripts

`test_data/test_data_dflee/*/run.py` and `run_par.py` — used by FLEE/DFlee tests. Keep as-is.

---

## Verification (Last Run)

| Script | Status |
|--------|--------|
| run_pr_checklist.py | OK |
| run_fork_experiments.py | OK |
| analyze_fork_experiments.py | OK |
| run_nuclear_parameter_sweep.py | OK |
| run_omega_diagnostic.py | OK |
| animate_agents.py | OK |
| run_easyvvuq_campaign.py | OK |
| visualize_easyvvuq.py | OK |
| nuclear_evacuation_simulations.py | OK |
| runscripts/run.py | API mismatch (Ecosystem) — may need main-Flee compatibility |
