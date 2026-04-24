# Sensitivity analysis with EasyVVUQ

Flee integrates with [EasyVVUQ](https://easyvvuq.readthedocs.io) for systematic sensitivity analysis of simulation parameters. This lets you understand which parameters most strongly influence output, and quantify uncertainty in predictions.

!!! note
    This tutorial uses the [VECMAtk](https://www.vecma-toolkit.eu/) toolkit. You will need EasyVVUQ and QCG-PilotJob installed in addition to FabFlee.

---

## What you need

- FabFlee installed and configured
- [EasyVVUQ](https://easyvvuq.readthedocs.io/en/dev/installation.html)
- [QCG-PilotJob](https://github.com/vecma-project/QCG-PilotJob) (for HPC execution)
- The FabFlee sensitivity scripts in `plugins/FabFlee/`

---

## Sampling methods

Two sampling scripts are provided in FabFlee:

| Script | Method |
|--------|--------|
| `flee_easyvvuq_SCSampler.py` | Stochastic Collocation (SC) sampling |
| `flee_easyvvuq_PCESampler.py` | Polynomial Chaos Expansion (PCE) sampling |

Each script provides two functions:
- `flee_init_*` — sets up and runs the parameter exploration
- `flee_analyse_*` — analyses the results using Sobol indices

---

## Parameters explored

The parameters available for sensitivity analysis are defined in:
```
(FabSim3_home)/plugins/FabFlee/templates/params.json
```

Default parameters include:

| Parameter | Type | Default | Range |
|-----------|------|---------|-------|
| `awareness_level` | integer | 1 | 0–2 |
| `max_move_speed` | float | 200 | 0–40000 |
| `max_walk_speed` | float | 35 | 0–40000 |
| `camp_move_chance` | float | 0.001 | 0–1.0 |
| `conflict_move_chance` | float | 1.0 | 0–1.0 |
| `default_move_chance` | float | 0.3 | 0–1.0 |
| `camp_weight` | float | 1.0 | 0–10.0 |
| `conflict_weight` | float | 0.25 | 0–1.0 |

Edit `params.json` to change ranges or add new parameters.

---

## Running sensitivity analysis

### Stochastic Collocation

```sh
fabsim localhost flee_init_SC:<scenario_name>
```

After runs complete:

```sh
fabsim localhost flee_analyse_SC:<scenario_name>
```

### Polynomial Chaos Expansion

```sh
fabsim localhost flee_init_PCE:<scenario_name>
```

```sh
fabsim localhost flee_analyse_PCE:<scenario_name>
```

---

## Interpreting results

Results are expressed as **Sobol indices**, which indicate the relative contribution of each parameter to output variance. A high first-order Sobol index for `max_move_speed` means that varying this parameter explains a large fraction of variance in the output.

---

## Further reading

- [EasyVVUQ documentation](https://easyvvuq.readthedocs.io)
- [EasyVVUQ + QCG-PilotJob](https://easyvvuq-qcgpj.readthedocs.io)
- [Ensemble runs](ensemble.md) — running parameter sweeps without EasyVVUQ
- [FabFlee overview](../fabflee/index.md) — FabFlee setup required for these tutorials
