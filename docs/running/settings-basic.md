# Settings — logging and spawning

This page covers the `log_levels` and `spawn_rules` sections of `simsetting.yml`.

---

## Example

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
  sum_from_camps: True
```

---

## Log levels (log_levels)

Setting a log level to `0` suppresses that output. Setting it to `1` or higher enables it. Higher values produce more detailed output.

| Variable | Values | What it records |
|----------|--------|-----------------|
| `agent` | 0, 1, 2, 3 | `1`: average agent travel times to camps. `2`: individual hop entries. `3`: hop number included in time step. |
| `link` | 0, 1 | Cumulative agent counts on each route at every time step |
| `camp` | 0, 1 | Locations added and conflict zones assigned per time step |
| `conflict` | 0, 1 | Agent spawning from conflict zones |
| `init` | 0, 1 | Initialisation steps |
| `idp_totals` | 0, 1 | Adds a "total IDPs" column to `out.csv` |

### Granularity

```yaml
log_levels:
  granularity: location   # or: region
```

- `location` (default) — logs use individual location names
- `region` — logs use the region name from `locations.csv`. Useful for admin-level analysis without location-level detail.

---

## Spawn rules (spawn_rules)

Spawn rules control how and when agents are introduced into the simulation.

### take_from_population

```yaml
take_from_population: False
```

If `True`, spawned agents are subtracted from the location's population. This can cause crashes if the number of agents exceeds the population. Leave as `False` unless you have a specific reason.

### insert_day0

```yaml
insert_day0: True
```

If `True`, the simulation inserts a count of zero agents at camps on Day 0 (so the output file starts from Day 0). Set to `False` if this is not needed for your scenario.

### sum_from_camps

```yaml
sum_from_camps: True
```

Controls how the total number of agents is derived:

- `True` (default) — total agents = sum of changes across all camp CSV files
- `False` — total agents = from `refugees.csv` total count

Set to `False` when there is no camp-level validation data and `conflict_driven_spawning` is disabled, otherwise the simulation may not spawn any agents.

### Reading agents from a file

You can pre-populate the simulation with agents by loading an `agents.csv` file:

```yaml
spawn_rules:
  read_from_agents_csv_file: True
```

Format of `agents.csv`:

```
location name, attribute1, attribute2, ...
LocationA, value1, value2, ...
```

An example is provided in `test_data/test_input_csv/agents.csv`.

!!! note
    This mechanism adds agents on top of any other spawning. Disable other spawning mechanisms if you only want to use the CSV file.

---

## Next steps

- [Settings — movement rules](settings-move.md) — control how agents move
- [Settings — full reference](settings-reference.md) — all parameters in one place
