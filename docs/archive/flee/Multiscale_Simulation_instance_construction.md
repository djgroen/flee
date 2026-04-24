# **Multiscale Simulation instance construction**

This documentation details how to construct a Multiscale in two Micro and Macro models for coupled simulation of conflict scenarios. Each conflict situation requires the following inputs in both Micro and Macro models:
Please follow the guidelines in serial mode conflict scenario construction and prepare input and validation data files in the following structure:

- Macro input CSV files:
	- input_files_0/locations-0.csv
	- input_files_0/routes-0.csv
	- input_files_0/closures-0.csv
	- input_files_0/coupled_locations.csv
	- input_files_0/registration_corrections-0.csv
	- input_files_0/conflicts-0.csv

- Micro input CSV files:
	- input_files_1/locations-1.csv
	- input_files_1/routes-1.csv
	- input_files_1/closures-1.csv
	- input_files_1/coupled_locations-1.csv
	- input_files_1/registration_corrections-1.csv
	- input_files_1/conflicts-1.csv

- Macro Validation data files:
	- source_data_0/refugees.csv
	- source_data_0/data_layout.csv
	- source_data_0/<country_name-camp_name1>.csv
	- source_data_0/<country_name-camp_name2>.csv

- Macro Validation data files:
	- source_data_1/refugees.csv
	- source_data_1/data_layout.csv
	- source_data_1/<country_name-camp_name1>.csv
	- source_data_1/<country_name-camp_name2>.csv

As described in serial mode conflict scenario construction, input and validation files are extracted from the following databases:

- the United Nations High Commissioner for Refugees database (UNHCR, https://data2.unhcr.org/en/situations).
- the Armed Conflict Location and Event Data Project (ACLED, https://www.acleddata.com/data).

For more information about how to extract input data please follow the same appraoch in the serial mode.

## **How to construct Multiscale simulation input files?**

### *1. Construct an input `locations-0.csv` file for macro model*
As mentioned before, the ACLED conflict data provides conflict locations to construct **locations.csv** input file for simulation purposes.

However, there is a little difference between serial mode and the coupled mode which needs attention.

First, after identifying all Macro region locations including (conflicts, camps, towns, etc) to produce locations.csv of both Macro and Micro models, all Micro model's conflict locations must be added as ghost locations in the Macro model location.csv file.

Besides, make sure both Macro and Micro locations are including coupled locations which will be described separately later.

| **name** | **region** | **country** | **lat** | **long** | **location_type** | **conflict_date** | **population/capacity** |
|:----:|:------:|:-------:|:---:|:----:|:-------------:|:-------------:|:-------------------:|
|   A  |   AA   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
|   B  |   BB   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
|   C  |   CC   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
| ...  |  ...   |   ...   | ... |  ... |       ...     |      ...      |         ...         |

### *2. Construct an input `locations-1.csv` file for micro model*


It should be constructed after identifying the Micro region locations (conflicts, camps, towns, etc) and adding missing coupled locations to the list of locations.
The only difference between micro and macro models in this regard is that Micro model locations include more location types like forwarding hubs and markers.

### *3. Construct Macro and Micro models input `routes-0.csv` and `routes-1.csv` files respectively.*

Identified conflict zones and camps in models provide origin and destination locations in corresponding routes file.
Note: don't forget to add routes to or from coupled locations.
We connect these locations to represent how forcibly displaced people flee.

Record distances between locations in **routes.csv** file for simulation using the following format:

| **name1** | **name2** | **distance[km]** | **forced_redirection** | **link_type** |
|:---------:|:---------:|:----------------:|:----------------------:|:-------------:|
| A         | B         | x1               |                        | walk          |
| B         | C         | x2               |                        | drive         |
| A         | C         | x3               |                        | crossing      |
| B         | N         | x4               |                        | ...           |
| C         | N         | x3               |                        | ...           |
| N         | Z         | x5               |                        | ...           |
| ...       | ...       | ...              |                        | ...           |

- **forced_redirection** refers to redirection from source location (can be town or camp) to destination location (mainly camp) and source location indicated as forwarding_hub. The value of 0 indicates no redirection, 1 indicates redirection (from name2) to name1and 2 corresponds to redirection (from name1) to name2.

- **link_type**: The main difference between Macro and Micro models' routes file is that in the Micro model all links have specific type which are represented by the link_type column with three possible values; walk, drive, and crossing.

### *4. Define location and border closures in `closures-#.csv` file*
We identify location or border closure events and document them in **closures-0.csv** file for Macro model and **closures-1.csv** file for Micro model in the following structure:

| **closure_type** | **name1** | **name2** | **closure_start = 0** | **closure_end = -1** |
|:----------------:|:---------:|:---------:|:---------------------:|:--------------------:|
| location         | A         | B         | xxx                   | xxx                  |
| country          | ABC       | ZZZ       | xxx                   | xxx                  |
| ...              | ...       | ...       | ...                   | ...                  |

- **closure_type** has 2 possible values:
	- **location** corresponding to camp or town closure and
	- **country** referring to border closure.

- **closure_start** and **closure_end** are given as integers, counting the number of days after the simulation start. The value of 0 indicates the start, while -1 indicates the end of the simulation.

### *5. Define registration corrections*


For each Macro and Micro models we will define and construct registration corrections based of validation camp files.

|        |            |           |
|:------:|:----------:|:---------:|
| camp_A | YYYY-MM-DD | normalize |
| camp_B | YYYY-MM-DD | normalize |
| camp_C | YYYY-MM-DD | normalize |
| ...    |  ...       |  ...      |

### *6. Record conflict locations in `conflicts-#.csv` file*
We create a **conflicts-0.csv** file for Macro Model and a **conflicts-1.csv** file for Micro Model to record conflict locations indicating the start of conflicts in the simulation execution (represented as 1):

| **#Day** | **name** | **A** | **B** | **C** | **Z** |
|:--------:|:--------:|:-----:|:-----:|:-----:|:-----:|
| 0        | 0        | 1     | 0     | 0     | 0     |
| 1        | 0        | 1     | 0     | 0     | 0     |
| 2        | 0        | 1     | 1     | 0     | 0     |
| 3        | 0        | 1     | 1     | 0     | 0     |
| 4        | 0        | 1     | 1     | 1     | 0     |
| 5        | 0        | 1     | 1     | 1     | 0     |
| ...      | ...      | ...   | ...   | ...   | ...   |

### *7. Define a conflict period for a conflict situation*

We define the simulation period of a conflict situation using sim_period.csv file, which has the following format:

| **StartDate** |  **YYYY-MM-DD**    |
|:-------------:|:------------------:|
| Length        | simulation_period  |

### *8. Define coupled locations for coupling between both models*

In order to make coupling works between both Macro and Micro models, there is a need to define the coupled locations in a separate file.

Besides, since the conflict locations of Micro Model should be added to Macro model and then agents will be spawned through these ghost locations to the Micro model, then all these ghost locations or in fact all Micro model conflict locations must be added to coupled_locations.csv file.

|     |
|:---:|
| ... |
| A   |
| B   |
| C   |
| ... |

### *9. Construct a network map for a conflict situation*

Construct an agent-based network map from **locations.csv** and **routes.csv** using https://carto.com.

<p align="center">
    <img src="../images/network.png" alt="Image" width="200" height="200" />
</p>

## **Constructing validation data**
There are three CSV file formats required for validation of simulation outputs in both Macro and Micro models.
CSV file containing total forced migrant counts **refugees.csv** comprises total counts of forcibly displaced people from ``Refugees and asylum-seekers from `chosen situation name` - Total`` JSON file and has the format as demonstrated:

The **refugees.csv** file has the same value in both models.

|            |     | 
|:----------:|:---:|
| YYYY-MM-DD | xxx |
| YYYY-MM-DD | xxx |
| ...        | ... |

We obtain data for each camp in each model regions (Macro or Micro) using the format and label them as **country_name-camp_name.csv**:

|            |     | 
|:----------:|:---:|
| YYYY-MM-DD | xxx |
| YYYY-MM-DD | xxx |
| ...        | ... |

**data_layout.csv** contains camp names for each camp/destination locations:

| **Total**   |    **forced_migrants.csv**   |
|:-----------:|:----------------------------:|
| camp_name1  | country_name-camp_name1.csv  |
| camp_name2  | country_name-camp_name2.csv  |
| ...         | ...                          |