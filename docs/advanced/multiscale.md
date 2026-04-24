# Multiscale simulations

Flee supports a multiscale mode that couples a **macro** (coarse-grained) model with a **micro** (fine-grained) model for conflict scenarios. This is useful when you want national-level coverage but higher spatial resolution in a specific region of interest.

---

## Overview

In a multiscale simulation:

- The **macro model** covers the broad geographic area (e.g., all regions of a country)
- The **micro model** covers a smaller area in higher detail (e.g., a single province)
- The two models exchange information at **coupled locations** — locations that exist in both models

---

## Directory structure

Each model (macro and micro) has its own input and validation data:

```
config_files/<scenario_name>/
├── input_files_0/              # Macro input CSV files
│   ├── locations-0.csv
│   ├── routes-0.csv
│   ├── closures-0.csv
│   ├── coupled_locations.csv
│   ├── registration_corrections-0.csv
│   └── conflicts-0.csv
├── input_files_1/              # Micro input CSV files
│   ├── locations-1.csv
│   ├── routes-1.csv
│   ├── closures-1.csv
│   ├── coupled_locations-1.csv
│   ├── registration_corrections-1.csv
│   └── conflicts-1.csv
├── source_data_0/              # Macro validation data
│   ├── refugees.csv
│   ├── data_layout.csv
│   └── <country-camp>.csv
└── source_data_1/              # Micro validation data
    ├── refugees.csv
    ├── data_layout.csv
    └── <country-camp>.csv
```

The suffix `-0` refers to the macro model and `-1` to the micro model.

---

## Coupled locations

`coupled_locations.csv` defines which locations are shared between the macro and micro models. Agents can transfer between models at these points. The format mirrors `locations.csv` but includes both model's location identifiers.

---

## Running a multiscale simulation

Via FabFlee:

```sh
fabsim localhost pflee_conflict_coupled:<scenario_name>,simulation_period=<days>
```

Refer to the [FabFlee documentation](../fabflee/index.md) for setup requirements.

---

## See also

- [Location types](../concepts/location-types.md) — background on location-based vs region-based graphs
- [Conflict scenario](../conflict/index.md) — setting up the underlying conflict data
- [FabFlee](../fabflee/index.md) — running multiscale simulations via FabFlee
