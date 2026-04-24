# DFlee data files

This page describes the data requirements for a DFlee scenario and where to obtain them.

Finding suitable data for disaster displacement modelling is often challenging — data varies widely in spatial coverage, temporal resolution, and accessibility.

---

## Flood level data

### flood_level.csv format

The key input file is `flood_level.csv` in your `input_csv/` directory. It provides flood severity at each location for each simulation day.

```csv
#Day, F1, F2, F3
0, 1, 3, 2
1, 2, 1, 3
2, 1, 2, 3
3, 1, 1, 1
15, 3, 2, 1
```

- `#Day` — the simulation day
- Column headers (`F1`, `F2`, etc.) — location names, matching those in `locations.csv`
- Values — integer flood level, 0 to `max_flood_level`; `0` = no flooding

!!! note
    You do not need to include every day — flee will interpolate linearly between listed days. The file must cover the full simulation period.

### What the flood levels represent

Flood levels are a simplified representation of flooding severity. You define the mapping from real-world flood data (e.g. inundation percentages, water depth) to integer levels 0–4. For example:

| Flood level | Example meaning |
|-------------|-----------------|
| 0 | No flooding |
| 1 | Minor inundation (<25% area) |
| 2 | Moderate flooding |
| 3 | Severe flooding |
| 4 | Extreme / complete inundation |

### Data sources for flood levels

| Source | Notes |
|--------|-------|
| [GloFAS (Global Flood Awareness System)](https://global-flood.emergency.copernicus.eu) | Historical events and forecasts |
| [UNOSAT](https://unosat.org/products/) | Rapid mapping for major events; some IDP data |
| [Global Flood Database](https://global-flood-database.cloudtostreet.ai) | Cloud-to-Street historical flood data |
| [Copernicus/ERA5](https://cds.climate.copernicus.eu) | Climate reanalysis including hydrological variables |
| [Google Flood Hub](https://sites.research.google/floods/) | River gauge data and flood maps |
| Google Earth Engine / Sentinel-1 | Satellite-derived flood extent mapping |
| ArcGIS data sources | Some open, some require institutional licence |
| National meteorological services | Region-specific gauge and forecast data |
| Scientific literature | Search for "inundation extent", "flood mapping", "remote sensing" |

---

## IDP displacement data

IDP data provides information on the number and location of displaced people during the event — used for validation.

### Requirements

- Pre-flood population distribution by location
- Displacement counts over time (ideally at the same locations used in `locations.csv`)
- Demographic information if available (for calibrating agent attributes)

### Data sources for IDPs

| Source | Notes |
|--------|-------|
| [IDMC](https://www.internal-displacement.org/database/displacement-data/) | Primary global IDP database |
| [Humanitarian Data Exchange (HDX)](https://data.humdata.org) | Repository of humanitarian data including IDP locations |
| [ReliefWeb](https://reliefweb.int) | Humanitarian reports, assessments, and maps |
| [IOM](https://www.iom.int) | Displacement tracking matrix (DTM) data |
| FAO Emergency Data | Food security and migration patterns at regional/national scale |
| Mobile data | Sometimes available in scientific literature; often proprietary |
| News reports | Local/international reports can give displacement counts by region |

---

## Temporal and spatial considerations

| Aspect | Minimum | Ideal |
|--------|---------|-------|
| Temporal resolution | Two distinct time points | Daily data |
| Spatial resolution | Matches `locations.csv` locations | Matches model spatial scale |

If only a few time points are available, Flee can interpolate between them. If data is available at a finer spatial scale than your locations, aggregate appropriately.

---

## Next steps

- [Food security](food-security.md) — add IPC food security data
- [Building a DFlee scenario](construction.md) — step-by-step scenario construction
- [Getting started with DFlee](overview.md) — simsetting.yml configuration
