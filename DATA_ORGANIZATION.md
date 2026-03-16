# Data Output Organization

All simulation and analysis outputs live under `data/` to avoid scattered folders.

## Layout

```
data/
├── experiments/           # run_fork_experiments, analyze_fork_experiments
│   ├── configs/           # Small configs (ring/star/linear)
│   ├── ring/
│   ├── star/
│   ├── linear/
│   └── figures/
├── pr_checklist/         # run_pr_checklist (default-off, default-on)
├── easyvvuq/
│   └── s1s2_campaign/   # EasyVVUQ campaign + omega diagnostic
├── nuclear_evacuation/   # nuclear_evacuation_simulations
├── systematic/          # systematic_topology_experiments
├── comprehensive/       # comprehensive_topology_paper_experiments
├── sweep/               # parameter_sweep_experiments, fix_plots
└── refugee/             # refugee_simulations, create_agu_figures input
```

## Script → Output Mapping

| Script | Output |
|--------|--------|
| `run_fork_experiments.py` | `data/experiments/` |
| `analyze_fork_experiments.py` | `data/experiments/figures/` |
| `run_pr_checklist.py` | `data/pr_checklist/` |
| `run_easyvvuq_campaign.py` | `data/easyvvuq/s1s2_campaign/` |
| `run_omega_diagnostic.py` | `data/easyvvuq/s1s2_campaign/omega_diagnostic/` |
| `nuclear_evacuation_simulations.py` | `data/nuclear_evacuation/` |
| `systematic_topology_experiments.py` | `data/systematic/` |
| `comprehensive_topology_paper_experiments.py` | `data/comprehensive/` |
| `parameter_sweep_experiments.py` | `data/sweep/` |
| `refugee_simulations.py` | `data/refugee/` |
| `create_agu_figures.py` | reads `data/refugee/`, writes `agu_figures/` |

## Migration

If you have existing output in old locations, move it:

```bash
mkdir -p data/experiments data/nuclear_evacuation data/systematic data/comprehensive data/sweep data/refugee
[ -d data/fork_experiments ] && mv data/fork_experiments/* data/experiments/ 2>/dev/null; rmdir data/fork_experiments 2>/dev/null
[ -d nuclear_evacuation_results ] && mv nuclear_evacuation_results/* data/nuclear_evacuation/ 2>/dev/null; rmdir nuclear_evacuation_results 2>/dev/null
[ -d systematic_results ] && mv systematic_results/* data/systematic/ 2>/dev/null; rmdir systematic_results 2>/dev/null
[ -d comprehensive_results ] && mv comprehensive_results/* data/comprehensive/ 2>/dev/null; rmdir comprehensive_results 2>/dev/null
[ -d sweep_results ] && mv sweep_results/* data/sweep/ 2>/dev/null; rmdir sweep_results 2>/dev/null
[ -d refugee_simulation_results ] && mv refugee_simulation_results/* data/refugee/ 2>/dev/null; rmdir refugee_simulation_results 2>/dev/null
```
