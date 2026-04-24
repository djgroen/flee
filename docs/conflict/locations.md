# Building locations.csv

`locations.csv` defines all locations in the simulation — conflict zones, camps, towns, and any other nodes in the network graph.

---

## File format

```
name, region, country, lat, long, location_type, conflict_date, population/capacity
A, AA, ABC, xxx, xxx, conflict, xxx, xxx
B, BB, ABC, xxx, xxx, conflict, xxx, xxx
Z, ZZ, ZZZ, xxx, xxx, camp, , xxx
N, NN, ABC, xxx, xxx, town, ,
```

| Column | Description |
|--------|-------------|
| `name` | Unique location name (no spaces; use underscores) |
| `region` | Administrative region name |
| `country` | Country name |
| `lat` | Latitude (decimal degrees) |
| `long` | Longitude (decimal degrees) |
| `location_type` | One of: `conflict`, `camp`, `idpcamp`, `town`, `marker`, `forwarding_hub` |
| `conflict_date` | The date conflict began at this location (if type is `conflict`); leave blank for camps and towns |
| `population/capacity` | For conflict zones and towns: population. For camps: maximum capacity (highest registered count). |

---

## Location types

| Type | Description |
|------|-------------|
| `conflict` | A location where conflict is occurring. Agents spawn here and are driven to move. **Note:** if you use a `conflicts.csv` file, then `town` locations can also become conflict zones at runtime — you do not always need to set type to `conflict` directly. |
| `town` | A regular urban location — neither a conflict zone nor a camp. Agents can pass through. |
| `camp` | A refugee camp or reception centre abroad. Agents are strongly attracted to camps. |
| `idpcamp` | An internally displaced persons (IDP) camp. Functionally similar to `camp`. Added in Flee 3.0. |
| `marker` | A routing waypoint only. Agents do not pause here; it is used for network structure and visualisation. |
| `forwarding_hub` | A transit point. Agents passing through are redirected onward (see `forced_redirection` in `routes.csv`). |

!!! note
    The default value for `population/capacity` is 0. If you want a camp with effectively unlimited capacity, set this to a very large number (e.g. 1000000) rather than leaving it at 0.

---

## Where to get location data

- **Conflict locations** — from ACLED event data (see [Data sources](data-sources.md))
- **Camp locations and capacities** — from UNHCR camp data
- **Town locations** — from OpenStreetMap; identify intermediate towns on key movement corridors
- **Coordinates** — from OpenStreetMap (right-click → "Centre map here" or use the search)
- **Populations** — from [CityPopulation.de](https://www.citypopulation.de/) or SimpleMaps

---

## Custom attributes (Flee 3.0+)

You can add extra columns to `locations.csv` beyond the standard ones. These **custom attributes** are passed through to agents and locations. Some have special meanings:

| Attribute | Effect |
|-----------|--------|
| `initial_idps` | Populates the location with this many IDPs on Day 0 |
| `conflict_intensity` | Overrides the default conflict intensity (1.0) for a `conflict` type location |
| `capacity_per_day` | Increases camp capacity by this number each day (for partially-open camps). Set to 0 for all non-growing locations. |
| `farmer_fraction` | Fraction of spawned agents who are farmers (used with harvest behaviour) |

You can also define entirely custom attributes (e.g. `gdp`, `elevation`) that do not affect model behaviour by default but are available for post-processing or custom code.

---

## Location type changes during simulation

In some scenarios you may want a location to change type during the simulation (e.g. a town becoming an IDP camp). Create a file called `location_changes.csv` in your `input_csv/` directory:

```
#location name, new location type, date
C, idpcamp, 100
A, town, 500
```

This changes location `C` to an IDP camp on Day 100, and location `A` to a town on Day 500. Note that `conflicts.csv` entries can override these changes.

---

## Next steps

- [Building routes.csv](routes.md) — connect your locations with distances
- [Conflict schedule](conflict-schedule.md) — define the conflict timeline
