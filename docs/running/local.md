# Running locally

This page explains how to run a Flee simulation on your local machine.

---

## Basic run command

```sh
python3 runscripts/run.py \
    <input_csv_dir> \
    <validation_data_dir> \
    <simulation_days> \
    <simsetting.yml path> \
    > <output_dir>/out.csv
```

| Argument | Description |
|----------|-------------|
| `<input_csv_dir>` | Path to the directory containing `locations.csv`, `routes.csv`, `conflicts.csv`, etc. |
| `<validation_data_dir>` | Path to the directory containing UNHCR validation data. Pass the same as `<input_csv_dir>` if no separate validation data exists. |
| `<simulation_days>` | Number of days to simulate. Use `0` to infer from the data. |
| `<simsetting.yml path>` | Path to the simulation settings file |

Output is written to stdout and redirected to `out.csv`.

---

## Running the built-in test

```sh
mkdir -p out
python3 runscripts/run.py \
    test_data/test_input_csv \
    test_data/test_input_csv/refugee_data \
    0 \
    test_data/simsetting.yml \
    > out/out.csv
```

---

## Running a pre-built scenario

To run the South Sudan 2014 scenario included with Flee:

```sh
mkdir -p outcar
python3 runscripts/run.py \
    conflict_input/ssudan2014/input_csv \
    conflict_validation/ssudan2014 \
    604 \
    conflict_input/ssudan2014/simsetting.yml \
    > outcar/out.csv
```

---

## Plotting output

After a run completes, generate comparison graphs:

```sh
python3 flee/postprocessing/plot_flee_output.py <output_dir>/ <output_dir>/
```

The output directory will then contain graphs for each camp comparing simulated versus reported numbers, plus an overall error plot.

---

## Parallel execution (pflee)

To run in parallel across multiple CPU cores:

```sh
mpirun -np <number_of_cores> python3 runscripts/run_par.py \
    <input_csv_dir> \
    <validation_data_dir> \
    <simulation_days> \
    <simsetting.yml path> \
    > <output_dir>/out.csv
```

`mpirun` must be installed on your system (see [Installation](../getting-started/installation.md)).

---

## Parallel performance testing

Use `test_par.py` to benchmark parallel performance:

```sh
mpirun -np <cores> python3 tests/test_par.py \
    -N 500000 \
    -p advanced \
    -d 10000 \
    -t 10
```

Options:

| Flag | Description | Default |
|------|-------------|---------|
| `-p` | Parallelisation mode: `advanced`, `classic`, `cl-hilat`, `adv-lowlat` | `advanced` |
| `-N` | Initial number of agents | 100000 |
| `-d` | New agents added per time step | 1000 |
| `-t` | Simulation duration in days | 10 |

---

## Next steps

- [Output files](output.md) — understand what the simulation produces
- [Settings — logging and spawning](settings-basic.md) — configure the simulation
- [FabFlee — HPC](../fabflee/hpc.md) — run on a supercomputer
