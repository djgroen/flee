# Food security

Flee supports integration of IPC (Integrated Food Security Phase Classification) data to model how food insecurity influences displacement decisions.

This mechanism works for both the conflict and DFlee use cases, but is particularly relevant for disaster scenarios where food supply disruption is a major driver of secondary displacement.

---

## IPC data file

IPC data is provided at a regional level in `input_csv/region_attributes_IPC.csv`:

```csv
#Day, AB, C, D, EF
0, 5.0, 11.0, 20.0, 6.0
10, 9.0, 11.0, 5.0, 10.0
20, 1.0, 3.0, 15.0, 15.0
501, 0.0, 0.0, 0.0, 0.0
```

- `#Day` — simulation day
- Column headers — **region** names (not individual location names)
- Values — percentage of persons with **critical food deprivation** (0–100)

!!! warning
    All regions used in your scenario must be included in this file, even if their food security value is 0. flee will linearly interpolate between listed days, so you do not need to list every day.

---

## Enabling food-related rules

Food rules are enabled in `simsetting.yml`. Add any of the following as needed.

### Spawn rules

```yaml
spawn_rules:
  starvation_driven_spawning: True
```

`starvation_driven_spawning` — increases the spawn rate by:

$$\text{extra spawns} = \text{IPC\_score} \times \frac{\text{population}}{100}$$

capped at the total location population.

!!! note
    Setting `conflict_zone_spawning_only: True` disables this for non-conflict locations and nullifies it in conflict zones with a score of 1.0.

---

### Movement rules

```yaml
move_rules:
  flee_when_starving: True
  avoid_food_deprived_locations: True
```

**`flee_when_starving`** — linearly increases the move chance according to the fraction of people with critical food deprivation. At 100% deprivation, move chance reaches 1.0.

**`avoid_food_deprived_locations`** — quadratically decreases the location weight (attractiveness) based on the fraction of the population with critical food deprivation. Severely food-deprived locations become less likely to be chosen as destinations.

---

## Further reading

- [Vanhille Campos et al. 2019](https://doi.org/10.1007/978-3-030-22750-0_71) — original publication describing these mechanisms
- [Getting started with DFlee](overview.md) — DFlee simsetting.yml configuration
- [Building a DFlee scenario](construction.md) — how to add IPC data to a full scenario
