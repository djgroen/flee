# Validation data

Validation data allows you to compare the simulation output against real-world figures — typically UNHCR camp registration counts. This comparison is the main way to assess how well the simulation captures the real displacement pattern.

---

## Directory structure

Validation data lives in a `source_data/` directory alongside `input_csv/`:

```
<scenario>/
├── input_csv/
└── source_data/
    ├── refugees.csv
    ├── data_layout.csv
    ├── Kenya-KakumaCamp.csv
    ├── Kenya-Dadaab.csv
    └── ...
```

---

## refugees.csv — total displaced counts

This file contains the total number of displaced people over time, covering all camps combined. Obtain it from the UNHCR situations portal (JSON export of the total timeline).

Format:

```
YYYY-MM-DD, count
2014-01-31, 850000
2014-02-28, 920000
...
```

---

## Per-camp CSV files — `<country>-<camp>.csv`

Each camp has its own time series CSV file. The filename format is `<country>-<campname>.csv`.

Format (same as `refugees.csv`):

```
YYYY-MM-DD, count
2014-01-31, 12405
2014-02-28, 14100
...
```

The maximum value across all dates is used as the camp capacity in `locations.csv`.

---

## data_layout.csv — mapping camps to files

This file maps camp names (as used in `locations.csv`) to their validation CSV files:

```
total, refugees.csv
KakumaCamp, Kenya-KakumaCamp.csv
Dadaab, Kenya-Dadaab.csv
```

The first column is the camp name exactly as it appears in `locations.csv`. The second column is the filename in `source_data/`.

!!! note
    The `total` row is mandatory and must point to `refugees.csv`.

---

## How validation is used

When you run a simulation with validation data provided, Flee compares the simulated camp population to the reported figures day-by-day. The output file `out.csv` includes:

- `<camp> sim` — simulated count
- `<camp> data` — reported count
- `<camp> error` — relative error between the two
- `Total error` — average error across all camps

The plotting script `flee/postprocessing/plot_flee_output.py` generates graphs comparing simulation and data for each camp.

---

## What if validation data is not available?

If you are building a scenario for a future or hypothetical situation where no validation data exists:

1. Omit the `source_data/` directory
2. Set `sum_from_camps: False` in `simsetting.yml` under `spawn_rules`
3. The simulation will still run, but no error metrics will be computed

---

## Next steps

- [Running locally](../running/local.md) — run your scenario
- [Settings — logging and spawning](../running/settings-basic.md) — configure how agents are spawned
