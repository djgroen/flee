# Getting started with DFlee

This page explains the key `simsetting.yml` settings needed to configure Flee for flood-driven displacement.

---

## Required simsetting.yml changes

### Spawn rules

Add or modify the following in the `spawn_rules` section:

```yaml
spawn_rules:
  flood_driven_spawning: True
  flood_zone_spawning_only: True
  take_from_population: True
  flood_driven_spawning:
    flood_spawn_mode: "pop_ratio"
    displaced_per_flood_day: [0.0, 0.1, 0.2, 0.5, 0.9]
```

**`displaced_per_flood_day`** is a list of floats, one per flood level (0 to `max_flood_level`). Each value is the fraction of the remaining population that is displaced per simulation day at that flood level.

Example: if `flood_level = 3` at a location with 1,000 people remaining:
- Day 1: 0.5 × 1000 = 500 people displaced
- Day 2: 0.5 × 500 = 250 people displaced (population has fallen)

!!! note
    The first entry (index 0, flood level 0) is ignored — unflooded locations use normal movement rules.

!!! warning
    `take_from_population` **must** be set to `True` for DFlee to prevent unrealistically high spawning rates.

---

### Movement rules

Add or modify the following in the `move_rules` section:

```yaml
move_rules:
  max_flood_level: 4
  flood_movechances: [0.3, 0.4, 0.7, 1.0, 1.0]
  flood_loc_weights: [1.0, 0.5, 0.2, 0.0, 0.0]
```

**`max_flood_level`** — the maximum flood level used in your `flood_level.csv` (typically 4).

**`flood_movechances`** — overrides the normal location move chance based on flood level. First entry is ignored (unflooded). Higher flood levels should have higher move chances (e.g. 1.0 = everyone moves).

**`flood_loc_weights`** — multiplies location attractiveness weights based on flood level. First entry ignored. A weight of 0.0 means the location is completely avoided in pathfinding.

!!! note
    The values in `displaced_per_flood_day`, `flood_movechances`, and `flood_loc_weights` are informed guesses. A completely inaccessible flooded area should have move chance 1.0 and weight multiplier 0.0. Calibrate against real IDP data where possible.

---

## The flood level file (flood_level.csv)

Flood levels must be provided in `input_csv/flood_level.csv`. This file has one column per flooded location and one row per simulation day:

```csv
#Day, A, B
0, 0, 1
1, 0, 1
2, 1, 1
3, 1, 3
4, 2, 1
5, 1, 1
```

Values are integers between 0 and `max_flood_level`. A value of 0 means no flooding — regular rules apply. See [Data files](data-files.md) for sources of flood data.

---

## Flood forecasting

DFlee supports an optional flood forecasting mechanism, where agents are aware of predicted future flood levels when making movement decisions.

### Enabling the forecaster

```yaml
flood_forecaster: True
flood_forecaster_timescale: 5
flood_forecaster_end_time: 9
flood_forecaster_weights: [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.1, 0.3, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0]
flood_awareness_weights: [0.0, 0.5, 1.0]
```

| Parameter | Description |
|-----------|-------------|
| `flood_forecaster_timescale` | Number of days ahead the forecast covers. `0` = no knowledge of future. |
| `flood_forecaster_end_time` | The last day in the simulation for which forecast data is available. Default: `simulation_length - timescale`. |
| `flood_forecaster_weights` | Weights for each day in the forecast window (1.0 = highest importance, 0.0 = ignored) |
| `flood_awareness_weights` | Weights per agent awareness group (0.0 = no awareness, 1.0 = full awareness). Must match the groups defined in `demographics_floodawareness.csv`. |

### Agent flood awareness

Agents can be assigned different levels of flood awareness using a demographics file:

```
demographics_floodawareness.csv
```

Format:
```
floodawareness, Default, F1, F2, F3
0.0, 0.1, 0.1, 0.1, 0.1
1.0, 0.2, 0.2, 0.2, 0.2
2.0, 0.7, 0.7, 0.7, 0.7
```

The first column defines the awareness group. Each subsequent column is a location, with values representing the probability of an agent belonging to each awareness group.

---

## Running a DFlee simulation

Via FabFlee (recommended):

```sh
fabsim localhost pflee:<config_name>,simulation_period=10
```

Or directly:

```sh
python3 runscripts/run.py \
    <input_csv_dir> \
    <validation_data_dir> \
    <simulation_days> \
    <simsetting.yml> \
    > out/out.csv
```

Ensure `FabSim3` is in your `PYTHONPATH` if using FabFlee.

---

## Next steps

- [Data files](data-files.md) — how to find and format flood and IDP data
- [Food security](food-security.md) — add IPC food security data to your scenario
- [Building a DFlee scenario](construction.md) — full step-by-step walkthrough
