Simulation instance construction tutorial for Multiscale Migration Prediction 
=====

# 1. Data extraction
## The UNHCR situations
The  United Nations High Commissioner for Refugees ([UNHCR](https://data2.unhcr.org/en/situations)) database provides an 
overview of active situations worldwide that are facing forced displacement distress. To construct a new conflict situation:
  - Select an active (conflict) situation of interest from an interactive map and click to access data and documentation 
relevant to a chosen conflict situation from https://data2.unhcr.org/en/situations.
  - Select a simulation period for conflict situation from `Refugees and asylum-seekers from 'chosen situation name' - Total`    timeline, which also presents forced displacement counts for a chosen period.
  - Obtain total counts of forcibly displaced people by clicking JSON button of `Refugees and asylum-seekers from 'chosen situation name' - Total` section. 
  - Identify camps for each neighbouring country through `Breakdown by Country` section of the conflict situation.
  - Collect and save data for each camp (e.g. country_name-camp_name.csv).

## The ACLED database
The Armed Conflict Location and Event Data Project ([ACLED](https://www.acleddata.com/data)) database provides conflict location data for forced displacement simulations. To obtain data on chosen conflict situation, complete the ACLED data export tool fields (https://www.acleddata.com/data) as follows:
  - Provide dates of interest for conflict situation (i.e. From and To).
  - Select `Event Type: Battle`.
  - Select `Sub Event Type: Armed clash, Attack, Government regains territory and Non-state actor overtakes territory`.
  - Specify `Region` and `Country` of conflict situation choice.
  - Accept `Terms of Use and Attribution Policy`.
  - `name.csv` file exports to Downloads automatically.
  - Revise the downloaded `name.csv` file:
     - Target the `fatalities` column and remove all rows in `name.csv` file with fatalities less than 1.
     - Choose the first conflict location occurrences of each location but exclude syndicated (repeated) locations 

# 2. Construct input CSV files
## Construct an input **locations.csv** file:
ACLED conflict data provides conflict locations to construct **locations.csv** input file for simulation purposes. After identifying conflict locations and producing **locations.csv**, the last column is filled with population data for conflict locations. Population distributions can be obtained from https://www.citypopulation.de or other population databases.

**locations.csv** has the following format:

name | region | country | lat | long | location_type | conflict_date | population/capacity |
-----|--------|---------|-----|------|---------------|---------------|---------------------|
 A   |   AA   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
 B   |   BB   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
 C   |   CC   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
...  |   ...  |   ...   | ... |  ... |       ...     |      ...      |         ...         |

Input camp names (i.e. destination locations) and their capacity into **locations.csv** file. Camp capacity is the highest number of forced migrants for each camp and obtained from individual camp CSV files that we set in **locations.csv.

## Construct an input **routes.csv** file:
Identified conflict zones and camps provide origin and destination locations. We connect these locations to represent how forcibly displaced people flee. We use http://www.bing.com/maps (or other mapping services) to connect conflict zones and camps, and add additional locations (if required) as a location type **town** to locations.csv as illustrated below:

name | region | country | lat | long | location_type | conflict_date | population/capacity |
-----|--------|---------|-----|------|---------------|---------------|---------------------|
 A   |   AA   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
 B   |   BB   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
 C   |   CC   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
 Z   |   ZZ   |   ZZZ   | xxx |  xxx |      camp     |       -       |         xxx         |
 N   |   NN   |   ABC   | xxx |  xxx |      town     |       -       |          -          | 
...  |   ...  |   ...   | ... |  ... |       ...     |      ...      |         ...         |

Record distances between locations in **routes.csv** file for simulation using the following format:

name1 | name2 | distance [km] | forced_redirection |
------|-------|---------------|--------------------|
  A   |   B   |       x1      |                    |
  B   |   C   |       x2      |                    |
  A   |   C   |       x3      |                    |
  B   |   N   |       x4      |                    |
  C   |   N   |       x3      |                    | 
  N   |   Z   |       x5      |                    |
 ...  |  ...  |      ...      |                    |

**forced_redirection** refers to redirection from source location (can be town or camp) to destination location (mainly camp) and source location indicated as forwarding_hub. The value of 0 indicates no redirection, 1 indicates redirection (from name2) to name1and 2 corresponds to redirection (from name1) to name2.

## Define location and border closures in **closures.csv** file:
We identify location or border closure events and document them in **closures.csv** file:

closure_type | name1 | name2 | closure_start = 0 | closure_end = -1 |
-------------|-------|-------|-------------------|------------------|
   location  |   A   |   B   |        xxx	 |        xxx       |
   country   |  ABC  |  ZZZ  |        xxx	 |        xxx       |
      
**closure_type** has 2 possible values: 
- **location** corresponding to camp or town closure and 
- **country** referring to border closure. 

**closure_start** and **closure_end** are given as integers, counting the number of days after the simulation start. The value of 0 indicates the start, while -1 indicates the end of the simulation.

## Construct a network map for a conflict situation
Construct an agent-based network map from **locations.csv** and **routes.csv** using https://carto.com.

# Validation data
There are three CSV file formats required for validation of simulation outputs:
- CSV file containing total forced migrant counts **forced_migrants.csv** comprises total counts of forcibly displaced people from `Refugees and asylum-seekers from `chosen situation name` - Total` JSON file and has the format as demonstrated:

...        | ... |
-----------|-----|
YYYY-MM-DD | xxx |
YYYY-MM-DD | xxx |
...        | ... |

- We obtain data for each camp using the format and label them as **country_name-camp_name.csv**.
    
...        | ... |
-----------|-----|
YYYY-MM-DD | xxx |
YYYY-MM-DD | xxx |
...        | ... |

- **data_layout.csv** contains camp names for each camp/destination locations.
    
Total      | forced_migrants.csv         |
-----------|-----------------------------|
camp_name1 | country_name-camp_name1.csv |
camp_name2 | country_name-camp_name2.csv |
...        | ...                         |   

# Summary list of data files
Each conflict situation requires:
- Three input CSV files
   - csv_input_directory/locations.csv
   - csv_input_directory/routes.csv
   - csv_input_directory/closures.csv
   
- Validation data files
    - validation_data_directory/forced_migrants.csv
    - validation_data_directory/country_name-camp_name1.csv
    - validation_data_directory/country_name-camp_name2.csv
    - validation_data_directory/data_layout.csv
