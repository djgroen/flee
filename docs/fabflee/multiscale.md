# Multiscale and coupled runs

FabFlee supports coupled macro/micro multiscale simulations. This mirrors the [Multiscale simulations](../advanced/multiscale.md) feature described in the Advanced topics section.

---

## Running a coupled simulation

```sh
fabsim localhost pflee_conflict_coupled:<scenario_name>,simulation_period=<days>
```

---

## Coupled Flee + Flare (conflict forecast)

To couple Flee with the Flare conflict evolution model for forecast ensembles:

```sh
fabsim localhost flee_conflict_forecast:<scenario_name>,N=<n_runs>,simulation_period=<days>
```

After completion:

```sh
fabsim localhost fetch_results
fabsim localhost plot_uq_output:<results_dir>,out
```

---

## On HPC

```sh
fabsim eagle_vecma flee_conflict_forecast:<scenario_name>,N=20,simulation_period=50
fabsim eagle_vecma fetch_results
fabsim localhost plot_uq_output:<results_dir>,out
```

---

## Scenario structure

See [Building scenarios](construction.md) for the multiscale directory structure (`input_files_0/`, `input_files_1/`, `source_data_0/`, `source_data_1/`).

---

## See also

- [Multiscale simulations](../advanced/multiscale.md) — concepts and directory structure
- [HPC / supercomputer](hpc.md) — remote execution setup
