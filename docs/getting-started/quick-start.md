# Quick start

This guide walks you through running a pre-built test simulation so you can see Flee in action before building your own scenario.

**Time to complete:** approximately 5–10 minutes  
**Prerequisites:** [Flee installed](installation.md)

---

## What you will run

Flee comes with a small test dataset in `test_data/`. This runs a minimal simulation and writes output to a CSV file, which can then be plotted.

---

## Step 1 — Run the test simulation

From inside your `flee/` directory, run:

```sh
mkdir -p out
python3 runscripts/run.py \
    test_data/test_input_csv \
    test_data/test_input_csv/refugee_data \
    0 \
    test_data/simsetting.yml \
    > out/out.csv
```

This runs the simulation and writes output to `out/out.csv`. You should see no output on the terminal if it runs successfully (diagnostic output is suppressed).

---

## Step 2 — Plot the output

```sh
python3 flee/postprocessing/plot_flee_output.py out/ out/
```

Open the `out/` directory — it will contain comparison graphs between the simulated output and reference data for each camp location.

---

## Step 3 — Understand the output

The main output file `out.csv` contains one row per simulation day, with counts of agents at each location. The plotting script produces graphs comparing simulated arrivals at camps against UNHCR validation data (where available).

See [Output files](../running/output.md) for a full description of what each file contains.

---

## Running a real conflict scenario

Once you have the test working, try running one of the pre-built conflict scenarios in `conflict_input/`. For example, to run the South Sudan 2014 scenario:

```sh
mkdir -p outcar
python3 runscripts/run.py \
    conflict_input/ssudan2014/input_csv \
    conflict_validation/ssudan2014 \
    604 \
    conflict_input/ssudan2014/simsetting.yml \
    > outcar/out.csv
python3 flee/postprocessing/plot_flee_output.py outcar/ outcar/
```

---

## Next steps

- Read [How the model works](../concepts/agent-based-model.md) to understand what the simulation is doing
- Follow the [conflict use case guide](../conflict/index.md) to build your own scenario from scratch
- See [Running simulations](../running/local.md) for all command-line options
