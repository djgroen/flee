# Data Considerations for DFlee

This guide outlines the data requirements for DFlee, an agent-based model simulating internally displaced persons (IDPs) during flood events. Due to the diverse nature of flood events and the complexities of data collection in disaster zones, finding suitable data sources can be challenging. Available data often varies significantly in scale, temporal coverage, and spatial resolution, requiring careful evaluation and potential modification before use in the model. 

Example input data files can be viewed here: [https://github.com/djgroen/FabFlee/tree/master/config_files/dflee_test_laura](https://github.com/djgroen/FabFlee/tree/master/config_files/dflee_test_laura)

## Flood Level Data File Format
*   **`flood_level.csv` File Format:** This file provides a simplified representation of flood levels over time for different locations. The file should be formatted as a comma-separated value (CSV) file with the following structure:
*   **Header Row:** The first row contains the column names. The first column should be named `#Day` representing the time step (e.g., days). Subsequent columns (e.g., `F1`, `F2`, `F3`) represent flood levels at different flooded locations or areas. 
*   **Data Rows:** Each subsequent row represents a time step. The first value in each row is the day number. The remaining values represent the flood levels at each location for that day.
*   **Example:**
    ```csv
    #Day,F1,F2,F3
    0,1,3,2
    1,2,1,3
    2,1,2,3
    3,1,1,1
    ...
    15,3,2,1
    ```
    In this example, on day 0, location F1 has a flood level of 1, F2 has a flood level of 3, and F3 has a flood level of 2.

  *   The `#Day` column determines the temporal resolution. The flood_level file should cover the entire period relevant to the simulation. If data is not available for the full period, extrapolation or interpolation must be used. To simulate an hourly cadence, use the same file format, but when plotting outputs modify the graphs to show hours not days. 
 *  The column names (e.g., `F1`, `F2`, `F3`) determine the spatial resolution. The number and names of these columns should correspond to the spatial units used in the model e.g. towns or regions. 

## Flood Data Requirements

*   **Inundation/Flood Severity/Flood Extent:** This is to determine the impact of flooding in each area, by providing a flood level between 0 -4 in the example flood_level.csv. Data should be quantitative and may include:
    *   Water depth/severity - which areas are worse affected? Can you define this quantitatively? For example, inundation percentages can be binned to give flood levels. 
    *   Flood extent maps (showing the area covered by floodwaters) - which locations are flooded?
    *   Flood duration (multiple maps/data sets for different periods) - when are locations flooded?
*   **Temporal Resolution (Time Cadence):** 
    *   **Minimum Requirement:** At least two distinct time points (e.g., Day 1 and Day 10) are necessary.
    *   **Ideal Scenario:** Hourly data provides the most granular and accurate representation of the flood's progression but is hard to find.
    *   **Practical Approach:** Daily data is a good compromise. If only a few data points are available, consider interpolation or extrapolation.
*   **Spatial Resolution (Spatial Cadence):**
    *   **Granularity:** Data should ideally match the model's spatial scale (e.g., town, region, district, or postcode).
 
## Flood Data Sources (in no particular order)
*    **UNOSAT**: [https://unosat.org/products/](https://unosat.org/products/) (Provides rapid mapping for some disaster events, and also has some IDP data. 
*   **Global Flood Awareness System (GloFAS):** [https://global-flood.emergency.copernicus.eu](https://global-flood.emergency.copernicus.eu) (Provides global flood mapping of historical events and forecasts)
*   **Global Flood Database** [https://global-flood-database.cloudtostreet.ai](https://global-flood-database.cloudtostreet.ai)
*   **Copernicus Climate Change Service (C3S) - ERA5 Reanalysis:** [https://cds.climate.copernicus.eu](https://cds.climate.copernicus.eu) (A comprehensive climate reanalysis dataset that includes hydrological variables)
*   **Local/National Weather Services:** Consult national meteorological agencies or disaster management organizations for region-specific flood data.
*   **Global Flood Hub/River Gauge Data:** There is another website with river gauge data and this flood hub:[https://sites.research.google/floods/l/0/0/3]([https://sites.research.google/floods/l/0/0/3)
*   **National River Gauge Data** Search online for data from river gauges in the affected area recorded by national/local weather services.                                          
*   **Satellite Imagery:**
    *   Google Earth Engine: (Provides access to a vast archive of satellite imagery)
    *   Sentinel-1: (Radar satellite data useful for flood mapping)
*   **Scientific Literature:** Search for research papers using keywords such as "inundation extent," "flood mapping," and "remote sensing." You may also use key terms for the disaster e.g. cyclone/hurricane. Example inundation mapping from literature: [https://www.mdpi.com/2072-4292/12/20/3454](https://www.mdpi.com/2072-4292/12/20/3454)

## IDP Data Requirements

*   **IDP Data:** Information on the number and location of IDPs is essential. This can include:
    *   Pre-flood population distribution
    *   Displacement locations
    *   Demographic information of displaced populations (age, gender, etc.)
*   **Temporal Resolution (Time Cadence):** Should ideally align with the flood data's temporal resolution to understand displacement dynamics over time. This data is hard to find. 
*   **Spatial Resolution (Spatial Cadence):** Should ideally align with the flood data's spatial resolution to link displacement to specific flood-affected areas. This data is hard to find.

## IDP Data Sources (in no particular order)

*   **Internal Displacement Monitoring Centre (IDMC):** [https://www.internal-displacement.org/database/displacement-data/](https://www.internal-displacement.org/database/displacement-data/) (A primary source for global IDP data)
*   **Humanitarian Data Exchange (HDX)**: [https://data.humdata.org](https://data.humdata.org) (A repository for humanitarian data, including locations, demographics, and IDP information)
*   **ReliefWeb:** [https://reliefweb.int](https://reliefweb.int) (Provides access to humanitarian reports, assessments, and maps)
*   **Government and NGO Reports:** Look for reports published by government agencies, international organizations, and NGOs working in the affected area.
*   **Food and Agriculture Organization of the United Nations (FAO) Emergency Data Database:** (While potentially sparse and with limited regional specificity, it can offer insights into migration patterns, shocks, and food security on a regional/national scale).


