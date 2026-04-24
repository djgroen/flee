# FabFlee — automating Flee with FabSim3

**FabFlee** is a [FabSim3](https://fabsim3.readthedocs.io/) plugin that automates running Flee simulations, especially for ensemble runs, sensitivity analysis, and execution on remote HPC systems.

Without FabFlee, you run Flee directly from the command line on your local machine. With FabFlee, you can:

- Run Flee on a supercomputer with a single command
- Launch ensemble or parameter sweep simulations automatically
- Fetch and validate results from multiple runs
- Integrate with [EasyVVUQ](https://easyvvuq.readthedocs.io/) for uncertainty quantification

!!! note
    FabFlee is optional. If you only want to run Flee locally and don't need HPC or ensemble support, you don't need it.

---

## Pages in this section

- **[Setup](setup.md)** — installing FabSim3, FabFlee, and configuring machines
- **[Running locally with FabFlee](running-local.md)** — single runs, ensembles, and replicas with FabFlee commands
- **[Building scenarios](construction.md)** — FabFlee scenario directory structure
- **[Validation (VVP3)](validation.md)** — ensemble output validation across multiple simulation runs
- **[Ensemble runs](ensemble.md)** — running multiple simulations with FabFlee
- **[HPC / supercomputer](hpc.md)** — configuring and running Flee on a remote supercomputer
- **[Sensitivity analysis](sensitivity.md)** — EasyVVUQ integration
- **[Multi-objective optimisation](multiobjective.md)** — camp location optimisation
- **[Multiscale / coupled runs](multiscale.md)** — coupled macro/micro simulations
- **[QCG Pilot Job](qcg-pilot.md)** — efficient HPC ensemble execution

---

## Overview

FabFlee sits between you and Flee. You describe what you want to run via a scenario directory, then issue a `fabsim` command. FabFlee handles staging input files, launching the simulation, and collecting outputs.

```
                     ┌─────────────────┐
  fabsim command ──▶ │    FabFlee      │ ──▶  flee simulation
                     │  (FabSim3)      │ ──▶  output collection
                     └─────────────────┘
```

FabFlee also integrates with:
- **Flare** — a stochastic conflict evolution model, for running ensembles based on different conflict progressions
- **EasyVVUQ** — for sampling parameter space and computing Sobol sensitivity indices
- **QCG-PilotJob** — for efficient HPC job submission

---

## Where to find example config files

Pre-built scenario config files are in:
```
~/FabSim3/plugins/FabFlee/config_files/
```

For example:
- `mali` — 2012 Northern Mali conflict
- `dflee_test` — DFlee flood scenario example
- `ethiopia` — Ethiopia conflict scenario for ensemble validation
