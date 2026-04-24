# Camp capacity

This page explains how camp capacity is enforced in Flee and how to configure it.

---

## What is camp capacity?

Each camp location has a `capacity` attribute representing the maximum number of agents (displaced persons) it can hold. This is usually taken from UNHCR data (see [camps](../conflict/camps.md)).

When a camp is near or at capacity, Flee reduces the probability that agents will choose it as a destination.

---

## How capacity is enforced

The capacity multiplier function (`getCapMultiplier`) in `flee/moving.py` returns a value between 0.0 and 1.0 that scales the attractiveness of a camp:

| Occupancy | Multiplier | Effect |
|-----------|-----------|--------|
| Below `CapacityBuffer` (default 90%) | 1.0 | Camp fully accessible |
| Between 90% and 100% | 0.0–1.0 | Gradually less attractive |
| At or above 100% | 0.0 | Camp not chosen |

The multiplier is applied to the link weight during pathfinding, so a full camp becomes effectively invisible to agents searching for a destination.

### The formula

Between 90% and 100% occupancy, the multiplier decreases linearly:

$$\text{multiplier} = 1 - \frac{n_\text{agents} - 0.9 \times \text{capacity}}{0.1 \times \text{capacity}}$$

---

## Configuration

Two parameters in `simsetting.yml` control capacity behaviour:

```yaml
move_rules:
  CapacityBuffer: 0.9      # Fraction of capacity at which softening begins
  CapacityScaling: 1.0     # Multiplier applied to all camp capacities
```

**`CapacityBuffer`** — default `0.9`. At this fraction of capacity, the camp begins to become less attractive. Set lower to make camps fill more smoothly; set to 1.0 to use hard cutoffs.

**`CapacityScaling`** — default `1.0`. A global multiplier applied to all camp capacities. Set to `2.0` to double all camp capacities, for example to test scenarios where camp infrastructure is expanded.

---

## Practical notes

- If you see all agents concentrating in one camp, check that other camps have capacity set.
- A capacity of 0 (or absent) is treated as unlimited.
- Very small `CapacityBuffer` values (e.g. 0.5) mean camps start deflecting agents when they are only half full.

---

## See also

- [Camps](../conflict/camps.md) — setting camp capacity from UNHCR data
- [Movement settings](../running/settings-move.md) — other parameters affecting movement and location weights
