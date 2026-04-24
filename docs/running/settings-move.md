# Settings — movement rules

This page covers the `move_rules` section of `simsetting.yml`, which controls how agents decide whether to move and where to go.

---

## Example

```yaml
move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 1.0
  camp_movechance: 0.001
  default_movechance: 0.3
  awareness_level: 1
  capacity_scaling: 1.0
  avoid_short_stints: False
  start_on_foot: False
  weight_power: 1.0
```

---

## Movement speeds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_move_speed` | 360.0 | Maximum distance (km) an agent can travel per day when using vehicles. Based on 30 km/h × 12 hours. |
| `max_walk_speed` | 35.0 | Maximum distance (km) per day on foot. Based on 3.5 km/h × 10 hours. |

These can also be overridden per-link in `routes.csv` using a `max_move_speed` custom attribute (see [Building routes.csv](../conflict/routes.md)).

---

## Location weights

Weights control how attractive each location type is as a destination. Higher weights make a location more attractive.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `camp_weight` | 1.0 | Attraction multiplier for camp locations |
| `conflict_weight` | 0.25 | Attraction multiplier for conflict locations (lower = agents avoid conflict) |
| `foreign_weight` | 1.0 | Additional multiplier for locations in a foreign country, stacked on top of `camp_weight` |

---

## Move chances

Move chance is the probability that an agent leaves their current location on any given day.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `conflict_movechance` | 1.0 | Probability of leaving a conflict zone per day (1.0 = always move) |
| `camp_movechance` | 0.001 | Probability of leaving a camp per day (very low — agents tend to stay once they arrive) |
| `default_movechance` | 0.3 | Probability of leaving a regular town per day |

---

## Awareness level

`awareness_level` controls how many steps ahead in the network graph an agent can "see" when choosing a destination.

| Value | Effect |
|-------|--------|
| -1 | No weighting — random walk |
| 0 | Agent can see only immediate neighbours (one hop) |
| 1 | Agent is aware of the type of location one hop away |
| 2 | Agent is aware of locations two hops away |
| 3 | Agent is aware of locations three hops away |

Higher awareness levels make agents better at finding camps, but increase computation time.

---

## Capacity scaling

```yaml
capacity_scaling: 1.0
```

A global multiplier applied to all camp capacities from `locations.csv`. Setting it to 2.0 doubles all camp capacities; setting it very large effectively removes capacity limits. Useful for sensitivity testing.

---

## Advanced movement parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `avoid_short_stints` | False | If `True`, agents will not stop unless they have travelled at least a full day's distance in the last two days |
| `start_on_foot` | False | If `True`, agents traverse the first link on foot (at `max_walk_speed`) rather than by vehicle |
| `stay_close_to_home` | — | Adds a weight that favours locations closer to the agent's origin location |
| `softening` | 10.0 | Adds this many kilometres to every link distance to reduce route preference sensitivity for very short routes |
| `weight_power` | 1.0 | Power factor applied to the total destination weight. `0.0` = random walk; `1.0` = default; larger values make agents more strongly prefer the best-scored route. |

### Harvest behaviour

Agents that are farmers (set by `farmer_fraction` in `locations.csv`) will return to their origin location during harvest months:

```yaml
move_rules:
  harvest_months: [6, 11]
```

This example triggers harvest behaviour in June and November. The `farmer_fraction` attribute in `locations.csv` controls what fraction of agents at each location are farmers.

---

## Next steps

- [Settings — optimisation](settings-optimisation.md) — speed up large runs
- [Settings — full reference](settings-reference.md) — all parameters in one table
