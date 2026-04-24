# Sensitivity analysis via FabFlee

FabFlee integrates with [EasyVVUQ](https://easyvvuq.readthedocs.io/) to run systematic sensitivity analysis on Flee input parameters.

For detailed background on the method and parameter definitions, see [Sensitivity analysis](../advanced/sensitivity.md) in the Advanced topics section.

---

## Prerequisites

In addition to FabFlee, you need:

- [EasyVVUQ](https://easyvvuq.readthedocs.io/en/dev/installation.html)
- [QCG-PilotJob](https://github.com/vecma-project/QCG-PilotJob) (optional, for HPC)

---

## Running on localhost

### Stochastic Collocation (SC)

```sh
fabsim localhost flee_init_SC:<scenario_name>
fabsim localhost fetch_results
fabsim localhost flee_analyse_SC:<scenario_name>
```

### Polynomial Chaos Expansion (PCE)

```sh
fabsim localhost flee_init_PCE:<scenario_name>
fabsim localhost fetch_results
fabsim localhost flee_analyse_PCE:<scenario_name>
```

---

## Running on HPC

```sh
fabsim eagle_vecma flee_init_SC:<scenario_name>
fabsim eagle_vecma fetch_results
fabsim localhost flee_analyse_SC:<scenario_name>
```

Analysis (the `_analyse_` step) is always run locally on the results after fetching.

---

## Parameter configuration

Edit `~/FabSim3/plugins/FabFlee/templates/params.json` to change parameter ranges or add new parameters to explore. See [Sensitivity analysis](../advanced/sensitivity.md#parameters-explored) for the default parameter list.

---

## See also

- [Sensitivity analysis](../advanced/sensitivity.md) — detailed method explanation
- [HPC / supercomputer](hpc.md) — running on a remote machine
