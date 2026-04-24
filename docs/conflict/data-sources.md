# Data sources

Building a conflict scenario requires data from several external sources. This page explains what you need and how to obtain it.

---

## ACLED — conflict event data

The [Armed Conflict Location and Event Data Project (ACLED)](https://acleddata.com/) provides detailed records of conflict events including dates, locations, and fatality counts.

!!! note
    An institutional or school email address is required to register for ACLED access.

**To download data:**

1. Go to the [ACLED data export tool](https://acleddata.com/acleddatanew/data-export-tool/)
2. Set your date range (the simulation period)
3. Select **Event Type: Battle**
4. Select **Sub Event Types:** Armed clash, Attack, Government regains territory, Non-state actor overtakes territory
5. Set your **Region** and **Country**
6. Click **Export**, accept the terms, and download the CSV file

The resulting CSV provides the conflict locations you will use to populate `locations.csv` and `conflicts.csv`.

---

## UNHCR — camp locations and registered counts

The [UNHCR Situations portal](https://data2.unhcr.org/en/situations) provides an interactive map of active displacement situations with camp-level registration data.

**To obtain data:**

1. Find your conflict situation on the [UNHCR situations map](https://data2.unhcr.org/en/situations)
2. Note the date range available under *Refugees and asylum-seekers — Total timeline* — this defines your simulation period
3. Download total counts via the **JSON** button in the Total section
4. Under **Breakdown by Country**, find individual camps and download their time series CSV files

!!! note
    The UNHCR portal interface varies between conflict situations. Some older situations have limited or differently structured data.

Camp registration figures are used to:
- Set camp capacity values in `locations.csv`
- Create validation files in `source_data/`

---

## Population data

Population figures for towns and conflict zones can be obtained from:

- [CityPopulation.de](https://www.citypopulation.de/) — a comprehensive database of city and administrative region populations worldwide
- [SimpleMaps](https://simplemaps.com/data/world-cities) — alternative source with latitude/longitude included
- National statistics offices for the country of interest

Population data is used to set the `population/capacity` column in `locations.csv` for non-camp locations.

---

## Geographic / routing data

To determine distances between locations and find intermediate towns:

- [OpenStreetMap](https://www.openstreetmap.org/) — open geographic data; use for finding coordinates and approximate road routes
- [Bing Maps](https://www.bing.com/maps) or Google Maps — alternative for route distance estimates
- [ORS Tools (QGIS plugin)](https://plugins.qgis.org/plugins/ORStools/) — useful for batch route distance calculation between many location pairs

Distances between locations are entered in `routes.csv`.

---

## Next steps

Once you have your data, proceed to:

- [Building locations.csv](locations.md) — create the list of all locations
- [Building routes.csv](routes.md) — connect locations with distances
- [Conflict schedule](conflict-schedule.md) — define when and where conflict occurs
