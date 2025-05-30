<!--
This document outlines the ensemble simulation setup for the Flee project. It provides details on managing and executing multiple simulation scenarios collectively.
-->
# Running Ensembles and Parameter Sweeps in Flee

Flee supports ensemble simulations and parameter sweeps to help users systematically explore how model outputs vary with different input settings. This is especially useful for sensitivity analysis, uncertainty quantification, and policy scenario exploration.

---

## What is an Ensemble or Parameter Sweep?

An **ensemble** is a set of simulation runs, each with slightly different input parameters or configurations. A **parameter sweep** is a systematic way to vary one or more parameters across a range of values, running a simulation for each combination.

---

## Organizing Input Files for an Ensemble

To run an ensemble in Flee (using FabFlee), you organise your scenario as follows:

```
config_files/<scenario_name>/
  ├── input_csv/
  ├── source_data/
  ├── SWEEP/
  │    ├── variant1/
  │    │    ├── simsetting.csv
  │    │    ├── locations.csv
  │    │    └── ...
  │    ├── variant2/
  │    │    ├── simsetting.csv
  │    │    ├── locations.csv
  │    │    └── ...
  │    └── ...
  └── ...
```

- Each subdirectory in `SWEEP/` (e.g., `variant1`, `variant2`) contains a full set of input files for a single simulation run.
- You can create these by copying your base input files and modifying parameters of interest in each variant.
- For example, you could change a simulation setting in the simsetting.yml file in each subdirectory to explore what difference it makes to your results. 

---

## Running an Ensemble with FabFlee

FabFlee provides commands to automate ensemble execution. For parallel Flee runs, use:

```sh
fabsim localhost pflee_ensemble:<scenario_name>,simulation_period=<days>
```

- This command will run a simulation for each subdirectory in `SWEEP/`.
- Each run uses the input files found in its respective subdirectory.

For serial (non-parallel) runs, use `flee_ensemble` instead of `pflee_ensemble`.

---

## Output Organization

After execution, results are collected in a `RUNS` directory under your results folder:

```
results/<job_name>/RUNS/
  ├── variant1/
  │    └── out.csv
  ├── variant2/
  │    └── out.csv
  └── ...
```

- Each subdirectory matches a variant from `SWEEP` and contains the output files for that simulation.
- This structure makes it easy to compare results across different input configurations.
- Note: FabFlee/config_files/flee3_validation shows an example SWEEP directory that runs all of the scenarios with one command. 

---

## Example: Creating a Parameter Sweep with simsetting.yml

Suppose you want to test three different maximum move speeds. You would:

1. Copy your base input files into three subdirectories under SWEEP/ (e.g., scenario1, scenario2, scenario3).
2. Edit `simsetting.yml` in each directory to set the desired value for `max_move_speed`.
3. Run the ensemble as described above.

---

## Further Reading

- See [FabFlee_Automated_Flee_based_simulation.md](FabFlee_Automated_Flee_based_simulation.md) for more details on automated scenario construction and execution.
- For sensitivity analysis, see [Sensitivity_analysis_of_parameters_using_EasyVVUQ.md](Sensitivity_analysis_of_parameters_using_EasyVVUQ.md).

---