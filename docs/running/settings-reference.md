# `simsetting.yml` — Complete Parameter Reference

This page provides a full quick-reference for every parameter that can be set in `simsetting.yml`.
For narrative explanations and worked examples, see also
[Simulation settings (basic)](Simulation_settings_basic.md) and
[Simulation settings (advanced)](Simulation_settings_advanced.md).

---

## Full example

The block below shows the most commonly used parameters together:

```yaml
log_levels:
  agent: 0
  link: 0
  camp: 0
  conflict: 0
  init: 0
  idp_totals: 0
  granularity: location

spawn_rules:
  take_from_population: False
  insert_day0: True
  empty_camps_on_day0: False
  conflict_zone_spawning_only: True
  sum_from_camps: True
  conflict_spawn_decay: [1.0, 1.0, 1.0, 0.5, 0.1]
  conflict_spawn_decay_interval: 30

move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  max_crossing_speed: 20.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 1.0
  camp_movechance: 0.001
  idpcamp_movechance: 0.1
  default_movechance: 0.3
  awareness_level: 1
  capacity_scaling: 1.0
  capacity_buffer: 0.9
  softening: 10.0
  weight_softening: 0.0
  weight_power: 1.0
  distance_power: 1.0
  home_distance_power: 0.0
  avoid_short_stints: False
  start_on_foot: False
  fixed_routes: False

optimisations:
  hasten: 1
```

---

## Top-level parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `number_of_steps` | int | `-1` | Override simulation duration in days. `-1` uses the value defined in `run.py`. |
| `conflict_input_file` | string | `""` | Path to conflict-input CSV file. Leave empty to use the default. |
| `flood_level_input_file` | string | `""` | Path to flood-levels CSV file. Required for DFlee runs. |
| `default_conflict_intensity` | int | `1` | Default conflict intensity multiplier applied to all conflict zones. |

---

## `log_levels`

Controls the verbosity of simulation output.  
All log levels default to `0` (silent). Setting a level to `1` (or higher for `agent`) activates output.

| Parameter | Default | Valid values | Output produced |
|---|---|---|---|
| `agent` | `0` | `0`, `1`, `2`, `3` | `1` = average travel times to camps per timestep; `2` = individual entries including multi-hop duplicates; `3` = hop number included in timestep field |
| `link` | `0` | `0`, `1` | `1` = cumulative agent counts on every link per timestep |
| `camp` | `0` | `0`, `1` | `1` = locations added and conflict zones assigned |
| `conflict` | `0` | `0`, `1` | `1` = conflict-zone spawning information |
| `init` | `0` | `0`, `1` | `1` = initialisation details |
| `idp_totals` | `0` | `0`, `1` | `1` = appends a "total IDPs" column to `out.csv` |
| `granularity` | `"location"` | `"location"`, `"region"` | Controls whether `agent` and `link` logs use individual location names or the region name from `locations.csv` |

---

## `spawn_rules`

### Basic spawning flags

| Parameter | Type | Default | Description |
|---|---|---|---|
| `take_from_population` | bool | `False` | Subtract spawned agents from the location's population. **Must be `True` for DFlee.** Can cause crashes if spawned count exceeds the source population. |
| `insert_day0` | bool | `True` | Pre-populate camp destinations on Day 0 from source data. Set to `False` if no Day 0 population data is available. |
| `empty_camps_on_day0` | bool | `False` | Start all destinations with 0 agents and adjust validation data accordingly. Useful when a large static background population exists in camps. |
| `conflict_zone_spawning_only` | bool | `True` | Spawn agents only from conflict zones. **Mutually exclusive with `flood_zone_spawning_only`.** |
| `flood_zone_spawning_only` | bool | `False` | Spawn agents only from flood zones. Activates the DFlee flood spawning path. **Mutually exclusive with `conflict_zone_spawning_only`.** |
| `camps_are_sinks` | bool | `False` | Activates the `deactivation_probability` attribute on camp locations in `locations.csv`. Set `deactivation_probability` to `1.0` for a perfect sink. |
| `read_from_agents_csv_file` | bool | `False` | Load initial agents from `agents.csv` at startup. Complements (does not replace) other spawning mechanisms. |
| `sum_from_camps` | bool | `True` | Sum total migrant numbers from camp CSV files instead of `refugees.csv`. Set to `False` when no camp-level validation data is available and `conflict_driven_spawning` is disabled. |
| `conflict_spawn_decay` | float list | `None` | Multipliers applied sequentially to the spawning rate over time (used only when `conflict_driven_spawning` is **not** configured). Empirically derived value: `[1.0, 1.0, 1.0, 0.5, 0.1]`. |
| `conflict_spawn_decay_interval` | int | `30` | Days per step in the `conflict_spawn_decay` list. With the default list and interval, spawning halves after 90 days. |
| `average_social_connectivity` | float | `3.0` | Average number of social connections per agent. Used by the two-system decision-making model. |

### `conflict_driven_spawning` subsection

Add this subsection to spawn agents based solely on ongoing conflicts rather than from `refugees.csv`.
Only active when `conflict_zone_spawning_only: True`.

```yaml
spawn_rules:
  conflict_driven_spawning:
    spawn_mode: "pop_ratio"
    displaced_per_conflict_day: 0.01
```

| Parameter | Default | Valid values | Description |
|---|---|---|---|
| `spawn_mode` | `"constant"` | `"constant"`, `"poisson"`, `"pop_ratio"` | `constant` = fixed number per conflict zone per day; `poisson` = Poisson-distributed count around that number; `pop_ratio` = fraction of the zone's population per day |
| `displaced_per_conflict_day` | `500` (constant/poisson) or `0.01` (pop_ratio) | number | Persons displaced (constant/poisson) or fraction of population displaced (pop_ratio) per conflict zone per conflict day, at intensity 1.0 |

### `flood_driven_spawn_mode` subsection

Add this subsection when `flood_zone_spawning_only: True` (DFlee runs).

```yaml
spawn_rules:
  flood_zone_spawning_only: True
  conflict_zone_spawning_only: False
  take_from_population: True
  flood_driven_spawn_mode:
    flood_spawn_mode: "pop_ratio"
    displaced_per_flood_day: [0.0, 0.1, 0.2, 0.5, 0.9]
```

| Parameter | Default | Valid values | Description |
|---|---|---|---|
| `flood_spawn_mode` | `"pop_ratio"` | `"constant"`, `"pop_ratio"` | Spawning mode for flood-driven displacement |
| `displaced_per_flood_day` | `[0.0, 0.1, 0.2, 0.5, 0.9]` | float list | Displacement fraction (pop_ratio) or count (constant) per flood level per day. Index 0 = no flood (ignored); index 4 = highest flood level. |

---

## `move_rules`

### Movement speeds

| Parameter | Type | Default | Other values used | Description |
|---|---|---|---|---|
| `max_move_speed` | float | `360.0` | `200` (Flee v1), `600` (Ukraine 2022) | Maximum km per timestep for motorised travel (30 km/h × 12 h) |
| `max_walk_speed` | float | `35.0` | `42` (Ukraine 2022) | Maximum km per timestep on foot (3.5 km/h × 10 h) |
| `max_crossing_speed` | float | `20.0` | — | Maximum km per timestep crossing water (2 km/h × 10 h) |

### Location weights

| Parameter | Type | Default | Other values used | Description |
|---|---|---|---|---|
| `camp_weight` | float | `1.0` | `1.5`–`5.0` | Attraction multiplier for camp locations. Higher values make camps more attractive relative to other locations. |
| `conflict_weight` | float | `≈0.316` (1/√10) | `0.25` | Attraction multiplier for conflict zones. Lower values make agents more eager to leave. |
| `foreign_weight` | float | `1.0` | — | Attraction multiplier for foreign locations; stacks multiplicatively with `camp_weight`. |
| `use_pop_for_loc_weight` | bool | `False` | `True` | Include location population as an additional weighting factor for non-camp locations. |
| `pop_power_for_loc_weight` | float | `0.1` | — | Power factor on population: `multiplier = population ^ power`. At 0.1, a 1M-population location is weighted 2× a 1000-person location. Only used when `use_pop_for_loc_weight: True`. If enabled, consider increasing `camp_weight` (e.g. ×3) to compensate. |

### Move chances (probability per day)

| Parameter | Type | Default | Other values used | Description |
|---|---|---|---|---|
| `conflict_movechance` | float | `1.0` | — | Probability of an agent leaving a conflict zone per day (0.0–1.0) |
| `camp_movechance` | float | `0.001` | — | Probability of an agent leaving a camp per day |
| `idpcamp_movechance` | float | `0.1` | — | Probability of an agent leaving an IDP camp per day |
| `default_movechance` | float | `0.3` | `0.8` (Ukraine 2022) | Probability of an agent leaving a regular town per day |
| `movechance_pop_base` | float | `10000.0` | — | Population level at which move chances are unchanged. Used for population-based scaling. |
| `movechance_pop_scale_factor` | float | `0.0` | — | Power factor for population-based move-chance scaling: `movechance *= (max(pop, capacity) / pop_base) ^ scale_factor`. Set to `0.0` (default) to disable. |

### Awareness

| Parameter | Type | Default | Valid values | Description |
|---|---|---|---|---|
| `awareness_level` | int | `1` | `-1`, `0`, `1`, `2`, `3` | How many link-hops ahead agents can perceive destination types when weighting routes. `-1` = no weighting; `0` = road length only; `1` = type of nearest settlement; `2` = settlements two hops away; `3` = three hops |

### Capacity

| Parameter | Type | Default | Other values used | Description |
|---|---|---|---|---|
| `capacity_scaling` | float | `1.0` | — | Multiplier applied to all capacity values from `locations.csv`. Use to globally loosen or tighten camp capacity constraints. |
| `capacity_buffer` | float | `0.9` | `0.75` | Occupancy fraction at which a location starts losing attractiveness. Attractiveness reaches 0 at `capacity_buffer × capacity × capacity_scaling`. Range: 0.0–1.0. |

### Route parameters

| Parameter | Type | Default | Other values used | Description |
|---|---|---|---|---|
| `softening` | float | `10.0` | `50.0` | Kilometres added to every link distance, reducing sensitivity among very short routes. |
| `weight_softening` | float | `0.0` | `0.1` | Constant added to all link weights, increasing route randomness. |
| `weight_power` | float | `1.0` | — | Power applied to the total route weight. `0.0` = random walk; `1.0` = default; `>1.0` = agents dismiss suboptimal routes more aggressively. |
| `distance_power` | float | `1.0` | `0.5`, `0.75` | Exponent on distance in weight calculations: `weight ∝ 1 / distance ^ distance_power`. `0.0` = distance is irrelevant; `2.0` = quadratic distance penalty. |
| `pruning_threshold` | float | `1.0` | — | Routes with weight below this fraction of the best route are pruned. Values ≥ 1.0 disable pruning. |
| `fixed_routes` | bool | `False` | `True` | Replace agent-generated routes with pre-computed location routes. Much faster but all agents travelling A→B on a given day share the same route. |
| `avoid_short_stints` | bool | `False` | `True` | Agents will not stop at intermediate locations unless they have travelled at least a full day's distance in the previous two days. |
| `start_on_foot` | bool | `False` | `True` | Agents traverse the first link on foot (at `max_walk_speed`) regardless of the link type. |
| `stay_close_to_home` | bool | `False` | `True` | Adds a weight component favouring locations nearer to the agent's origin. |
| `home_distance_power` | float | `0.5` | `0.0` | Power factor for home-proximity weighting (inverse sqrt by default). Only used when `stay_close_to_home: True`. |
| `use_v1_rules` | bool | `False` | `True` | Use Flee v1 legacy movement rules. Overrides: `max_move_speed=200`, `camp_weight=2.0`, `conflict_weight=0.25`; disables `avoid_short_stints` and `start_on_foot`. For reproducing Flee v1 results only. |

### Agent-attribute conditionals (Flee 3.0)

These settings activate demographic-based decision rules.
All default to `False`. Requires appropriate attribute columns in `agents.csv`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ChildrenAvoidHazards` | bool | `False` | Child agents apply a safety preference weight when choosing routes |
| `BoysTakeRisk` | bool | `False` | Male child agents are more risk-tolerant than female child agents |
| `MatchCampReligion` | bool | `False` | Agents prefer camp locations that match their own religion attribute |
| `MatchCampEthnicity` | bool | `False` | Agents prefer camp locations that match their own ethnicity attribute |
| `MatchTownEthnicity` | bool | `False` | Agents prefer town locations that match their own ethnicity attribute |
| `MatchConflictEthnicity` | bool | `False` | Agents prefer conflict zones that match their own ethnicity attribute |
| `avg_religion_fraction` | float | `0.25` | Average fraction of agents sharing a religion; used to compute the base matching rate: `ReligionBaseRate = 1 / avg_religion_fraction` |
| `two_system_decision_making` | bool | `False` | Enable dual-process (System 1 / System 2) decision logic. Requires `average_social_connectivity` to be set in `spawn_rules`. |

### `flood_rules` subsection (DFlee only)

Add this subsection under `move_rules` for DFlee runs.

```yaml
move_rules:
  flood_rules:
    flood_movechances: [0.3, 0.4, 0.7, 1.0, 1.0]
    flood_loc_weights: [1.0, 0.5, 0.2, 0.0, 0.0]
    flood_forecaster: True
    flood_forecaster_timescale: 5
    flood_forecaster_end_time: 9
    flood_forecaster_weights: [1.0, 0.9, 0.8, 0.7, 0.6]
    flood_awareness_weights: [0.0, 0.5, 1.0]
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `flood_movechances` | float list | `None` | Per-flood-level move-chance override. Index 0 = no flood (ignored); highest index = most severe flood level. Overrides `default_movechance` for flooded locations. |
| `flood_loc_weights` | float list | `None` | Per-flood-level location-weight multiplier. Index 0 ignored. Values below 1.0 reduce the attractiveness of flooded locations. |
| `flood_forecaster` | bool | `False` | Enable flood-forecast awareness so agents can react to predicted future flood levels. |
| `flood_forecaster_timescale` | int | `0` | Number of days ahead that agents can forecast. `0` disables forecast awareness. |
| `flood_forecaster_end_time` | int | `0` | Last simulation day for which forecast data is available. |
| `flood_forecaster_weights` | float list | `None` | Importance weight applied to each forecast day (1.0 = full weight, 0.0 = ignored). Length must equal `flood_forecaster_timescale`. |
| `flood_awareness_weights` | float list | `None` | Per-awareness-group weight for flood forecasts, e.g. `[0.0, 0.5, 1.0]` for three awareness groups. |

---

## `optimisations`

| Parameter | Type | Default | Other values used | Description |
|---|---|---|---|---|
| `hasten` | int | `1` | `5`, `10`, `100` | Speed-up factor. `hasten=N` runs the simulation with 1/N of the agents at N× the speed. Higher values increase stochastic variability. Use `1` for production runs; `10`–`100` for exploratory sweeps. |

!!! note
    Flee is not fully deterministic. Even at `hasten=1`, results can vary by ~1% between identically configured runs due to stochastic movement decisions.

---
