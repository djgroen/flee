# Ensemble runs and parameter sweeps

Flee supports ensemble simulations, where many runs are executed together — each with different input parameters or configuration variants. This is useful for:

- Testing how sensitive outputs are to individual parameters
- Exploring policy scenarios (e.g., opening or closing a route)
- Uncertainty quantification

---

## Directory structure

To run an ensemble, organise your scenario with a `SWEEP/` directory:

```
config_files/<scenario_name>/
└── SWEEP/
    ├── variant1/
    │   ├── input_csv/
    │   │   ├── locations.csv
    │   │   └── ...
    │   ├── source_data/
    │   └── simsetting.yml
    ├── variant2/
    │   ├── input_csv/
    │   └── ...
    └── ...
```

Each subdirectory under `SWEEP/` is a separate simulation run. Create variants by copying your base input files and modifying the parameter of interest in each.

For example, to sweep over values of `max_move_speed`, create one variant directory per value and edit `simsetting.yml` in each.

---

## Running with FabFlee

### Parallel runs

```sh
fabsim localhost pflee_ensemble:<scenario_name>,simulation_period=<days>
```

This runs one simulation per `SWEEP/` subdirectory, in parallel.

### Serial runs

```sh
fabsim localhost flee_ensemble:<scenario_name>,simulation_period=<days>
```

Use `flee_ensemble` for non-parallel execution.

---

## Fetching results

After all runs complete:

```sh
fabsim localhost fetch_results
```

This collects outputs from all runs into a local `RUNS/` directory:

```
results/<job_name>/RUNS/
├── variant1/
│   └── out.csv
├── variant2/
│   └── out.csv
└── ...
```

---

## Comparing outputs

Once results are collected, you can compare `out.csv` files across variants to see how each parameter change affected the simulation. Flee's plotting scripts can be adapted for this.

For automated statistical analysis across ensembles, see [Sensitivity analysis with EasyVVUQ](sensitivity.md).
