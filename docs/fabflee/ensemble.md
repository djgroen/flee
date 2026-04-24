# Ensemble runs with FabFlee

FabFlee makes it straightforward to run many simulations simultaneously — each with different inputs. This is useful for exploring how changes to parameters or conflict scenarios affect the output.

See [Ensemble runs and parameter sweeps](../advanced/ensemble.md) in the Advanced topics section for background on what ensembles are and how to organise the `SWEEP/` directory.

---

## Running an ensemble

```sh
fabsim localhost flee_ensemble:<scenario_name>,simulation_period=<days>
```

For parallel runs (recommended for large ensembles):

```sh
fabsim localhost pflee_ensemble:<scenario_name>,simulation_period=<days>
```

### Replicated runs

To run each configuration multiple times to account for Flee's non-determinism:

```sh
fabsim localhost flee:<scenario_name>,simulation_period=<days>,replicas=<n>
```

---

## Flare-coupled ensemble

[Flare](https://github.com/djgroen/flare-release) is a stochastic conflict evolution model. You can combine it with Flee to produce an ensemble where each run uses a different conflict progression:

```sh
fabsim localhost flee_conflict_evolution:<scenario_name>,simulation_period=<days>
```

This runs multiple Flee+Flare pairs and produces results with confidence intervals.

---

## Fetching and validating results

```sh
fabsim localhost fetch_results
fabsim localhost validate_flee_output:<results_dir>
```

See [Validation (VVP3)](validation.md) for details on ensemble validation.

---

## On HPC

Replace `localhost` with your machine name:

```sh
fabsim eagle_vecma pflee_ensemble:<scenario_name>,simulation_period=<days>
```

See [HPC / supercomputer](hpc.md) for machine configuration.
