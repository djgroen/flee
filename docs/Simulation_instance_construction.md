# **Simulation instance construction**

This documentation details how to construct a conflict scenario for forced displacement simulation. Each conflict situation requires input data (in `input_csv` directory), validation data (in `source_data` directory), simulation settings configuration file (`simsetting.yml`) and execution scripts (`run.py` and `run_par.py`) as illustrated below:

<p align="center">
    <img src="../images/config_template.png" alt="Image" width="300" height="300" />
</p>


To create input and validation data files, the following forced displacement databases are considered:



* the Armed Conflict Location and Event Data Project (ACLED, [https://www.acleddata.com/data](https://www.acleddata.com/data));
* the United Nations High Commissioner for Refugees database (UNHCR, [https://data2.unhcr.org/en/situations](https://data2.unhcr.org/en/situations));
* the population databases (e.g. <https://www.citypopulation.de>);
* the geospatial databases (e.g. <https://www.openstreetmap.org>)  or [http://www.bing.com/maps](http://www.bing.com/maps)).

## **Construct an input locations.csv file**

### **ACLED conflict locations extraction**

The ACLED database provides conflict location data for forced displacement simulations. To obtain data on chosen conflict situation, complete the ACLED data export tool fields ([https://acleddata.com/acleddatanew/data-export-tool/](https://acleddata.com/acleddatanew/data-export-tool/)) as follows:

!!! note
	A School/Institution Email will be needed to access ACLED resources.


* Provide dates of interest for conflict situations (i.e. From and To).
* Select `Event Type: Battle`.
* Select `Sub Event Type`
	* Armed clash,
	* Attack,
	* Government regains territory and
	* Non-state actor overtakes territory.
* Specify `Region` and `Country` of conflict situation choice.
* Click on Export and Accept Terms of Use and Attribution Policy.
* Click Export again and `<name>.csv` file exports to Downloads automatically.


The ACLED conflict data provides conflict locations to construct **`locations.csv`** input file for simulation purposes. After identifying conflict locations and producing **`locations.csv`**, the last column is filled with population data for conflict locations.


| **name** | **region** | **country** | **lat** | **long** | **location_type** | **conflict_date** | **population/capacity** |
|:----:|:------:|:-------:|:---:|:----:|:-------------:|:-------------:|:-------------------:|
|   A  |   AA   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
|   B  |   BB   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
|   C  |   CC   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
| ...  |  ...   |   ...   | ... |  ... |       ...     |      ...      |         ...         |



!!! note
	The default value for population/capacity is 0. Therefore, if you wish to have camps with infinite capacity you must set them to a very high value instead.


### **UNHCR forced migrant counts and camp locations extraction**

<p align="center">
    <img src="../images/unhcr_screenshot.png" alt="Image" width="70%" />
</p>


The UNHCR situations provide an overview of active situations worldwide that are facing forced displacement distress. To construct a new conflict situation:

* Select an active (conflict) situation of interest from an interactive map and click to access data and documentation relevant to a chosen conflict situation from [https://data2.unhcr.org/en/situations](https://data2.unhcr.org/en/situations).

* Select a simulation period for conflict situation from `Refugees and asylum-seekers from 'chosen situation name' - Total timeline`, which also presents forced displacement counts for a chosen period.

* Obtain total counts of forcibly displaced people by clicking JSON button of `Refugees and asylum-seekers from 'chosen situation name' - Total section`.

* Identify camps for each neighbouring country through `Breakdown by Country` section of the conflict situation.

* Collect and save data for each camp (e.g. `<country_name-camp_name>.csv`).

!!! note
        The UNHCR Data Portal tends to have a different interface for different conflict situations. Therefore, data on the location level may need to be retrieved differently for some situations, or may be unavailable altogether.

Input camp names (i.e. destination locations) and their capacity into **`locations.csv`** file. Camp capacity is the highest number of forced migrants for each camp and is obtained from individual camp CSV files that are set in **`locations.csv`**. For instance, `CampZ.csv` has the highest number of forcibly displaced people (18129) on 2015-09-30, which is the camp capacity for CampZ.


|     ...      |   ...   |
|:------------:|:-------:|
|  2015-03-31  |  11470  |
|  2015-06-02  |  12405  |
|  2015-07-24  |  12405  |
|  2015-08-31  |  11359  |
|  2015-09-30  |  18129  |
|     ...      |   ...   |


### **Population data extraction**

Currently, the population figures for each location will need to be collected and written to the *population/capacity* column from <www.citypopulation.de>. After the population data has been collected for each location, input these population numbers in `locations.csv`, which can be then used for simulation execution.


## **Construct location graph CSV files**

The `locations.csv` file contain information about all the locations in the location graph. Flee 3.0 supports four location types:

* `conflict`: places where conflicts are taking place during the conflict. This type is not needed if you are loading in a `conflicts.csv` file or if you are using Flee for disaster displacement.
* `town`: places that are neither conflict zones nor camps. **NOTE: if you use a conflicts.csv input file, then town type locations can change into conflict type locations at runtime**.
* `camp`: places where asylum seekers / unrecognized refugees are received and looked after.
* `idpcamp`: places where internally displaced persons are received and looked after. **NOTE: this type is supported as of Flee 3.0**
* `marker`: these places are entirely ignored in decision-making, but are represented for output/viz purposes. Useful for embedding crossroads, where people are extremely unlikely to pause.


Identified conflict zones and camps provide origin and destination locations. We connect these locations to represent how forcibly displaced people flee. We use [https://www.openstreetmap.org](https://www.openstreetmap.org) or [http://www.bing.com/maps](http://www.bing.com/maps) (or other mapping services) to connect conflict zones and camps, and add additional locations (if required) as a location type **town** to **`locations.csv`** as illustrated below:


| **name** | **region** | **country** | **lat** | **long** | **location_type** | **conflict_date** | **population/capacity** | **custom_attributes...**|
|:----:|:------:|:-------:|:---:|:----:|:-------------:|:-------------:|:-------------------:|:------------:|
|   A  |   AA   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |      xxx     |
|   B  |   BB   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |      xxx     |
|   C  |   CC   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |      xxx     |
|   Z  |   ZZ   |   ZZZ   | xxx |  xxx |      camp     |               |         xxx         |      xxx     |
|   N  |   NN   |   ABC   | xxx |  xxx |      town     |               |                     |      xxx     |
| ...  |  ...   |   ...   | ... |  ... |       ...     |      ...      |         ...         |      xxx     |

Here, **custom_attributes** can be a list of optional location-specific (static) attributes that you can assign manually. For instance, you could assign an attribute named gdp to each location to indicate the average GPD in each place. You can define as many custom attributes as you like. (new as of Flee 3.0)

Several **custom_attributes** trigger behavioral changes in the Flee 3 simulations, including:
* `initial\_idps`, which is an attribute that can be added to any location to populate it with the indicated number of IDPs on Day 0. This attribute also technically works for refugee camps abroad, but hasn't yet been tested for this use case. (**new as of 6-9-2024**)
* `conflict\_intensity`, which when explicitly defined for a location of type conflict, will override the default value (1.0) for conflict intensity to a custom-defined intensity level.

Record distances between locations in **`routes.csv`** file for simulation using the following format:

| **name1** | **name2** | **distance[km]** | **forced_redirection** | **custom_attributes...**|
|:----:|:------:|:-------:|:---:|:------------:|
| A    |   B    |   x1    |     |      xxx     |
| B    |   C    |   x2    |     |      xxx     |
| A    |   C    |   x3    |     |      xxx     |
| B    |   N    |   x4    |     |      xxx     |
| C    |   N    |   x3    |     |      xxx     |
| N    |   Z    |   x5    |     |      xxx     |
| ...  |  ...   |   ...   | ... |      xxx     |

**forced_redirection** refers to redirection from source location (can be town or camp) to destination location (mainly camp) and source location indicated as forwarding_hub. The value of `0` indicates no redirection, `1` indicates redirection (from name2) to name1 and 2 corresponds to redirection (from name1) to name2.

**custom_attributes** work in the same way here as for `locations.csv`, providing users with the ability to add custom link attributes and set different values for individual links. Some attributes automatically trigger behaviors in Flee 3.0, including:

* `max\_move\_speed`: when explicitly defined, this will override the MaxMoveSpeed set in `simsetting.yml` for individual links. Note that it is only possible to override this for all links or for none of the links at the moment.

!!! note 
	Group-specific instrucitons for locations.csv. For those working with our group, here are some more specific instructions:
	1. Populations for the largest cities tend to be listed on citypopulation.de, then include additional cities/towns in the regions you are interested in. Alternatively, the web tables on citypopulation.de can be converted to csv by downloading the webpage.
	2. Q: Have you studied how location selection affects the accuracy of your models? For example, does including many smaller settlements/towns improve the model or does this level of granular detail make little difference, as it is other parameters such as the total distance/time travelled in a day the agents are allowed to make that mainly affect the results?
	3. Q: If citypopulation.de does not contain the city, or does not have recent data. look for other websites that already list location name/latitude/longitude/populations e.g. simple maps.
	4. Find Latitudes and longitudes by identifying the places on OpenStreetMap. We tend to use OpenStreetMap because of its openness, but have used Bing and Google maps in the past.

## **Defining Major Routes**

(This feature is currently in testing and will be new in Flee 3.2)

Major routes are routes that are known by most displaced persons in a country, and will be added to their awareness if the end point of such a route is within their base awareness range (which is equal to the number of steps set by `AwarenessLevel` in `simsetting.yml`).

Major routes are set in a comma-separated fashion in a file named **major_routes.csv**.

For each line the format is as follows:
`<first location name>,<second location name>, ... , <last location name>`

For the time being the following constraints apply:
* Major routes are always considered to be two-way.
* Major routes cannot be closed (but agents may be interrupted and redirect themselves if there is a conflict on the way).
* Major routes should have a length of at least one step.
* Major routes are not recursively applied to an agent awareness. I.e. if an agent is aware of location A, and there are major routes `A->B` and `B->C`, then the agent will not be aware of location C and its accessibility through B. To include this awareness, you'll need to explicitly add a major route for `A->C`.

## **Define Location and Border Closures**

We identify location or border closure events and document them in a file named **closures.csv**:

| **closure_type** | **name1** | **name2** | **closure_start = 0** | **closure_end = -1** |
|:----:|:------:|:-------:|:---:|:---:|
| location | A  | B |  xxx | xxx |
| country | ABC  | ZZZ |  xxx | xxx |
| ...  | ... | ... | ... | ... |

**closure_type** has 2 possible values:

* **location** corresponding to camp or town closure and
* **country** referring to border closure.
* **camp** refers to camp closuresi for camp `name1` (these are converted to normal towns when closed).
* **idpcamp** can be used in the same way as camp, but for IDP camps.
* **remove_forced_redirection** can be used to remove any forced redirection mechanism on a particular one-way link from `name1` to `name2`.
* **closure_start** and **closure_end** are given as integers, counting the number of days after the simulation start. The value of `0` indicates the start, while `-1` indicates the end of the simulation.


## **Define a conflict period for a conflict situation**

We define the simulation period of a conflict situation using **sim_period.csv** file, which has the following format:

| **StartDate** | **YYYY-MM-DD** |
|:----:|:------:|
| Length | simulation_period  |


## **Record conflict locations in conflicts.csv file**

We create a **conflicts.csv** file to record conflict locations indicating the start of conflicts in the simulation execution (represented as `1` or `1.0`). It is possible to use custom conflict intensities by defining values between `0.0` and `1.0` in the file:

| **#Day** | **name** | **A** | **B** | **C** | **Z** |
|:--:|:--:|:--:|:--:|:--:|:--:|
| 0 | 0 | 1 | 0 | 0 | 0 |
| 1 | 0 | 1 | 0 | 0 | 0 |
| 2 | 0 | 1 | 1 | 0 | 0 |
| 3 | 0 | 1 | 1 | 0 | 0 |
| 4 | 0 | 1 | 1 | 1 | 0 |
| 5 | 0 | 1 | 1 | 1 | 0 |
| ... | ... | ... | ... | ... | ... |

## **Construct a network map for a conflict situation**

You can construct an agent-based network map from locations.csv and routes.csv using the instructions in the [FabFlee section](https://flee.readthedocs.io/en/master/FabFlee_Automated_Flee_based_simulation/).

![](images/network.png)


## **Construct a location type changes file**

In some cases, you may want to specify that a location type changes during the simulation. You can do this by including a file names `location_changes.csv` in the main directory.

The format of this file is as follows:

| #location name | new location type | date (in simulation days) |
|:--:|:--:|:--:|
| location name | new type | day to make change |
| ... | ... | ... |


For example, the file below changes location C to an IDPCamp on Day 100, and location A to a town on Day 500.
```
#location name, new location type, date
C,idpcamp,100
A,town,500

```

Note that changes in `conflicts.csv` may override these change, triggering locations to become a conflict zone instead.


## **Construct validation data**

There are three CSV file formats required for validation of simulation outputs. CSV file containing total forced migrant counts **refugees.csv** comprises total counts of forcibly displaced people from `Refugees and asylum-seekers from 'chosen situation name' - Total` JSON file and has the format as demonstrated:

| ... | ... |
|:---:|:---:|
| YYYY-MM-DD | xxx |
| YYYY-MM-DD | xxx |
| ... | ... |

We obtain data for each camp using the format and label them as **country_name-camp_name.csv**:

| ... | ... |
|:---:|:---:|
| YYYY-MM-DD | xxx |
| YYYY-MM-DD | xxx |
| ... | ... |

**data_layout.csv** contains camp names for each camp/destination location:

| total | refugees.csv |
|:---:|:---:|
| camp_name1 | country_name-camp_name1.csv |
| camp_name2 | country_name-camp_name2.csv |
| ... | ... |



## **Construct input demographics profiles**

As of Flee 3.0, it is possible to define demographic attributes to newly spawned agents. Examples could include age, gender, ethnicity, religion or main language. You can define these attributes by placing files in the input\_csv subdirectory. For a given example attribute AAAyou can define the weighted probability profile as follows:

1. Create a file named `demographics_aaa.csv`

2. Within the file, use the following format to define the default values for all locations, and an override for example locations `loc1` and `loc2`:

| aaa | Default | loc1 | loc2 |
|:---:|:---:|:---:|:---:|
| V1 | 90 | 25 | 0 |
| V2 | 10 | 25 | 1000 |
| ... | ... | ... | ... |

In this example, agents spawned in loc1 are 50% likely to have the value V1 for attribute AAA, and 50% likely to have the value V2. All agents spawned in loc2 will have the value V2, while agents spawned in all other locations are 90% likely to have V1, and 10% likely to have V2.

## **Incorporating farmer harvesting trips**

In a range of settings, it is common for farmers in refugee camps to return to their original location during harvesting seasons. Within Flee 3, this behavior can be easily incorporated by adding the following attribute to `locations.csv`: `farmer_fraction`. This attribute will contain the population fraction for each location that consists of farmers. E.g. a value of `0.1` would indicate that `10%` of persons spawned in that location are farmers.

### Harvest time

To trigger the harvesting behaviors, you need to add the following entry to the `move_rules` setting of `simsetting.yml`:

* `harvest_months: [m1,m2,etc.]`

For instance, if harvest takes place in June and November, then the entry would look like this:

* `harvest_months: [6,11]`

At time of writing, **all** farmers return to their source location for harvesting. If you wish this to be different, then please raise a GitHub issue detailing your proposed mechanism.
