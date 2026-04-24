# Conflict schedule (conflicts.csv)

`conflicts.csv` defines which locations experience conflict on which days of the simulation, and at what intensity. It is the primary mechanism for driving agent spawning in the conflict use case.

---

## File format

The file has one column per location that can be a conflict zone, and one row per simulation day:

```
#Day, name, A, B, C, Z
0, 0, 1, 0, 0, 0
1, 0, 1, 0, 0, 0
2, 0, 1, 1, 0, 0
3, 0, 1, 1, 0, 0
4, 0, 1, 1, 1, 0
5, 0, 1, 1, 1, 0
```

| Column | Description |
|--------|-------------|
| `#Day` | Simulation day number (0-indexed) |
| `name` | Usually set to 0 (legacy column) |
| `<location>` | Conflict intensity at this location on this day. `0` = no conflict; `1` = full conflict. Values between 0 and 1 represent partial conflict intensity. |

---

## How conflict intensity works

- A value of `0` means no conflict at that location on that day — no agents are spawned there
- A value of `1` means full conflict — the maximum number of agents are spawned, scaled by the location population
- Values between `0` and `1` scale the number of spawned agents proportionally

The actual number of agents spawned per day at a location depends on:
- The conflict intensity value
- The location's population (from `locations.csv`)
- The total number of displaced people (derived from validation data)
- The spawning rules in `simsetting.yml`

---

## Simulation period

Define the start date and duration of the simulation in `sim_period.csv`:

```
StartDate, YYYY-MM-DD
Length, <number of days>
```

The number of rows in `conflicts.csv` should match the simulation length.

---

## How to derive conflict schedules from ACLED

ACLED provides event-level data with dates and locations. To convert this to a `conflicts.csv`:

1. For each location in your simulation, find the first date a conflict event occurred there in ACLED
2. Decide on a conflict intensity value (1 for active conflict; lower values for sporadic events)
3. Set conflict intensity to > 0 for all days between conflict start and end at that location

The [input file generator scripts](input-file-generator.md) can automate this process.

---

## Notes

- Camps and towns do not appear as columns in `conflicts.csv` — only locations that can be conflict zones
- If you define `location_type = conflict` directly in `locations.csv` and do not use `conflicts.csv`, those locations will always be conflict zones for the entire simulation. Using `conflicts.csv` gives you per-day control.
- If a `conflicts.csv` entry turns a `town` into a conflict zone, it reverts when the intensity returns to 0

---

## Next steps

- [Camp data](camps.md) — set camp capacities
- [Validation data](validation-data.md) — format data for comparing results to reality
