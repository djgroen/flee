# Input file generator

Flee includes a set of numbered scripts in `flee/preprocessing/` (and in the FabFlee plugin under `scripts/`) that automate the creation of input files from raw ACLED and population data. This is useful when building a new scenario from scratch.

The scripts are intended to be run in order — each one takes the output of the previous step as input.

---

## Prerequisites

Before running the scripts, prepare:

1. An `acled.csv` file — exported from ACLED for your country and date range (see [Data sources](data-sources.md))
2. A `population.html` file — saved from [CityPopulation.de](https://www.citypopulation.de/) for your country

Create a directory named after your scenario (e.g. `nigeria2016`) and place both files inside it.

---

## Script 00 — Extract location names from ACLED

```sh
python 00_extract_location_names.py nigeria2016 admin2
```

**Input:** `acled.csv`  
**Output:** List of location names at the specified admin level  

Arguments: `<country_dir>` `<location_type>` (e.g. `admin1`, `admin2`, `location`)

---

## Script 01 — Extract population data from HTML

```sh
python 01_extract_population_csv.py nigeria2016 0 7 10000
```

**Input:** `population.html`  
**Output:** `population.csv`  

Arguments: `<country_dir>` `<table_index>` `<population_column_index>` `<minimum_population_threshold>`

---

## Script 02 — Build locations.csv

```sh
python 02_extract_locations_csv.py nigeria2016 01-01-2016 admin1 0 100
```

**Input:** `acled.csv`, `population.csv`  
**Output:** `locations.csv`  

Classifies locations into towns and conflict zones based on conflict event counts.

Arguments: `<country_dir>` `<start_date>` `<location_type>` `<fatalities_threshold>` `<conflict_threshold>`

---

## Script 03 — Extract conflict periods

```sh
python 03_extract_conflict_info.py nigeria2016 01-01-2016 31-12-2016 admin2 7
```

**Input:** `acled.csv`  
**Output:** `conflict_info.csv`  

Calculates the duration of conflict at each location, with an optional extension of `<added_conflict_days>` days beyond the last event.

Arguments: `<country_dir>` `<start_date>` `<end_date>` `<location_type>` `<added_conflict_days>`

---

## Script 04 — Build conflicts.csv

```sh
python 04_extract_conflicts_csv.py nigeria2016 1-1-2016 31-12-2016
```

**Input:** `conflict_info.csv`  
**Output:** `conflicts.csv`  

Generates the day-by-day conflict schedule for all locations.

Arguments: `<country_dir>` `<start_date>` `<end_date>`

---

## Add camps manually

Before generating routes, add your camp locations to `locations.csv` by hand. Each camp needs:

- A unique name
- Latitude and longitude
- `location_type = camp`
- `population/capacity` set to the peak UNHCR count

See [Camp data](camps.md) for details.

---

## Script 05 — Build routes.csv

```sh
python 05_extract_routes_csv.py nigeria2016
```

**Input:** `locations.csv`  
**Output:** `routes.csv`  

Uses a nearest-neighbour algorithm based on Euclidean distance to generate routes between locations.

!!! note
    Automatically generated routes are a starting point only. Review them carefully — some connections may be unrealistic (e.g. across impassable terrain or national borders). Edit `routes.csv` manually to correct these.

Arguments: `<country_dir>`

---

## Script 06 — Visualise routes

```sh
python 06_extract_routes_info.py nigeria2016
```

**Input:** `locations.csv`, `routes.csv`  
**Output:** Interactive HTML map

Opens an interactive map showing all locations and routes. Use this to check that the network looks geographically plausible before running a simulation.

Arguments: `<country_dir>`

---

## Next steps

- [Running locally](../running/local.md) — execute your simulation
- [Validation data](validation-data.md) — set up comparison data
