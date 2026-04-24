# Building routes.csv

`routes.csv` defines the connections (links) between locations, and the distances along those connections. Together with `locations.csv` it forms the network graph that agents navigate.

---

## File format

```
name1, name2, distance[km], forced_redirection
A, B, 120,
B, C, 85,
A, C, 200,
B, N, 40,
N, Z, 60,
```

| Column | Description |
|--------|-------------|
| `name1` | Name of the first location (must match a name in `locations.csv`) |
| `name2` | Name of the second location (must match a name in `locations.csv`) |
| `distance[km]` | Distance between the two locations in kilometres |
| `forced_redirection` | Optional. `0` = no redirection; `1` = redirect from `name2` to `name1`; `2` = redirect from `name1` to `name2`. Used with `forwarding_hub` locations. |

Routes are **bidirectional by default** — a single row represents a connection in both directions.

---

## How to measure distances

Use mapping tools to estimate road distances:

- [OpenStreetMap](https://www.openstreetmap.org/) with the routing function
- [ORS Tools (QGIS plugin)](https://plugins.qgis.org/plugins/ORStools/) for batch calculation
- Google Maps or Bing Maps as alternatives

Use **road distances**, not straight-line distances, wherever possible.

---

## Which routes to include

Include routes that represent realistic movement corridors:

1. Connect all conflict zones to nearby towns
2. Connect towns along the main escape routes leading toward borders and camps
3. Connect border towns to camps in neighbouring countries
4. Add additional intermediate towns if there are no direct connections

You do not need to include every possible road — only the main corridors that displaced people would realistically use. Avoid connecting locations that have no direct road link between them.

---

## Custom attributes on routes (Flee 3.0+)

You can add extra columns to `routes.csv`, similar to `locations.csv`. One special attribute:

| Attribute | Effect |
|-----------|--------|
| `max_move_speed` | Overrides the global `max_move_speed` for this specific link (e.g. for rough terrain or borders). Note: either all links or no links must define this attribute. |

---

## Major routes (Flee 3.2+, in testing)

Major routes are well-known corridors that are included in agents' awareness even if they are beyond the normal `awareness_level` setting. Define them in a file called `major_routes.csv`:

```
<location1>, <location2>, <location3>, ...
```

Each line defines one major route. Routes are always two-way. See [Movement settings](../running/settings-move.md) for how `awareness_level` interacts with major routes.

---

## Closures

To model border or route closures, create a `closures.csv` file:

```
closure_type, name1, name2, closure_start, closure_end
location, A, B, 50, 100
country, ABC, ZZZ, 200, -1
```

| Column | Description |
|--------|-------------|
| `closure_type` | `location` (town/camp closure), `country` (border closure), `camp`, `idpcamp`, or `remove_forced_redirection` |
| `name1`, `name2` | Location or country names involved |
| `closure_start` | Day number when the closure starts (0 = simulation start) |
| `closure_end` | Day number when it ends (-1 = end of simulation) |

---

## Next steps

- [Conflict schedule](conflict-schedule.md) — define when and where conflict occurs
- [Camp data](camps.md) — set camp capacities
