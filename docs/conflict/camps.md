# Camp data

Camps are the destination locations in a conflict scenario — places where displaced people seek refuge. This page explains how to set up camp entries in `locations.csv` and where to get the data.

---

## Camp entries in locations.csv

Each camp is a row in `locations.csv` with `location_type` set to `camp` (for refugee/asylum seeker camps abroad) or `idpcamp` (for internally displaced persons camps within the conflict country).

```
name, region, country, lat, long, location_type, conflict_date, population/capacity
KakumaCamp, Turkana, Kenya, 3.72, 34.88, camp, , 185000
Dadaab, Garissa, Kenya, 1.19, 40.31, camp, , 350000
```

The `population/capacity` column for camps should be set to the **maximum registered population** of the camp over the simulation period. This is used as the camp capacity in the model.

!!! note
    The default capacity is 0, meaning the camp will immediately be "full". Always set camp capacity to a realistic value. If you want no capacity limit, use a very large number such as 1000000.

---

## Getting camp capacity from UNHCR data

Each camp's capacity is derived from the peak value in its UNHCR time series:

1. Download the camp's registration CSV from the [UNHCR data portal](https://data2.unhcr.org/en/situations)
2. Find the maximum count across the whole time series
3. Use that value as the `population/capacity` for the camp in `locations.csv`

For example, if the highest entry in `KenyaCamp1.csv` is 18,129 on 2015-09-30, then set `population/capacity = 18129` for that camp.

---

## Partially-open camps (capacity_per_day)

Some camps were not open at full capacity from day one — they expanded gradually as the crisis grew. You can model this using the `capacity_per_day` custom attribute in `locations.csv`:

```
name, ..., population/capacity, capacity_per_day
KakumaCamp, ..., 0, 500
OtherLocation, ..., 50000, 0
```

This increases the camp capacity by 500 each simulation day. Set `capacity_per_day = 0` for all other locations (towns, conflict zones) if you use this column.

---

## IDP camps

IDP camps (`idpcamp`) work the same way as regular camps, but represent facilities within the conflict country. Agents in IDP camps are tracked separately in the output. Supported as of Flee 3.0.

---

## Camp capacity scaling

If you want to loosen camp capacity constraints globally (e.g. for sensitivity testing), you can use `capacity_scaling` in `simsetting.yml`:

```yaml
move_rules:
  capacity_scaling: 1.5
```

This multiplies all camp capacities by 1.5. Setting it to a very large value effectively removes capacity constraints.

See [Settings — movement rules](../running/settings-move.md) for details.

---

## Next steps

- [Validation data](validation-data.md) — format time-series data for comparing simulation output to UNHCR registration figures
