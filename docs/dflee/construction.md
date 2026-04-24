# Building a DFlee scenario

This guide walks through building a DFlee scenario from scratch, using Pakistan or a similar flood event as an example context. The process mirrors the [conflict scenario setup](../conflict/index.md) but uses flood data instead of conflict event data.

---

## Before you start

You need:

- A list of locations (towns/regions) in the flood-affected area, with populations
- Flood extent/severity data for each location over time (see [Data files](data-files.md))
- IDP displacement data for validation, if available
- OpenStreetMap or similar for estimating route distances

---

## Step 1 — Create the scenario directory

Copy the structure of an existing scenario, for example `dflee_test`:

```sh
cp -r ~/FabSim3/plugins/FabFlee/config_files/dflee_test \
      ~/FabSim3/plugins/FabFlee/config_files/my_dflee_scenario
```

The directory should have this structure:

```
my_dflee_scenario/
├── input_csv/
│   ├── locations.csv
│   ├── routes.csv
│   ├── closures.csv
│   ├── flood_level.csv
│   └── (optional) region_attributes_IPC.csv
├── source_data/
│   ├── idp_data.csv      (IDP counts per location per day, for validation)
│   └── data_layout.csv
└── simsetting.yml
```

---

## Step 2 — Create locations.csv

Identify towns, regions, and IDP settlements relevant to the flood. Create `input_csv/locations.csv` with:

```csv
name, region, country, lat, lon, location_type, conflict_date, population, custom_attribute1
TownA, RegionX, PK, 25.4, 68.3, conflict, , 50000,
TownB, RegionX, PK, 25.8, 68.7, town, , 30000,
CampC, RegionY, PK, 24.1, 67.5, camp, , 0,
```

For DFlee, locations that can be flooded should use location type `conflict` or `town`. Evacuation destinations should be marked `camp`. This is discussed in [locations](../conflict/locations.md).

!!! note
    The names in the `name` column for flood-affected locations must match the column headers in `flood_level.csv`.

---

## Step 3 — Create routes.csv

Define movement routes between locations. For floods, include routes that model movement from flooded areas to higher ground or IDP camps. See [routes](../conflict/routes.md) for format details.

```csv
#name1, name2, distance, forced_redirection
TownA, TownB, 45, 0
TownB, CampC, 80, 0
```

---

## Step 4 — Create flood_level.csv

Build the flood level time series for each flood-affected location. Values 0–4 represent increasing flood severity:

```csv
#Day, TownA, TownB
0, 2, 0
1, 3, 1
2, 4, 2
3, 3, 3
4, 2, 2
5, 1, 1
6, 0, 0
```

See [Data files](data-files.md) for sources of flood extent data and how to convert to integer flood levels.

---

## Step 5 — Configure simsetting.yml

Start from the `dflee_test` example and modify:

```yaml
spawn_rules:
  flood_driven_spawning: True
  flood_zone_spawning_only: True
  take_from_population: True
  flood_driven_spawning:
    flood_spawn_mode: "pop_ratio"
    displaced_per_flood_day: [0.0, 0.1, 0.2, 0.5, 0.9]

move_rules:
  max_flood_level: 4
  flood_movechances: [0.3, 0.4, 0.7, 1.0, 1.0]
  flood_loc_weights: [1.0, 0.5, 0.2, 0.0, 0.0]
```

See [Getting started with DFlee](overview.md) for the full list of available settings and what they mean.

---

## Step 6 — Add validation data (optional but recommended)

If you have IDP displacement data, add it to `source_data/` as per the [validation data format](../conflict/validation-data.md). This enables Flee to produce accuracy metrics alongside simulation output.

---

## Step 7 — Add food security data (optional)

If IPC data is available for your region, add `input_csv/region_attributes_IPC.csv` and enable the food security mechanisms in `simsetting.yml`. See [Food security](food-security.md).

---

## Step 8 — Run the simulation

Via FabFlee:

```sh
fabsim localhost pflee:my_dflee_scenario,simulation_period=15
```

Or directly:

```sh
python3 flee/runscripts/run.py \
    input_csv/ \
    source_data/ \
    15 \
    simsetting.yml \
    > out/out.csv
```

---

## Step 9 — Plot and inspect results

```sh
python3 flee/scripts/plot_output.py out/out.csv
```

Compare against your `source_data/` validation files if available.

---

## Common problems

| Problem | Likely cause |
|---------|--------------|
| Simulation spawns nobody | `flood_driven_spawning` not set to True, or `flood_level.csv` missing |
| Very high spawn numbers | `take_from_population` not set to True |
| Locations not found | Column headers in `flood_level.csv` don't match location names in `locations.csv` |
| No movement towards camps | Check `flood_loc_weights` — flooded camp locations will be avoided |
