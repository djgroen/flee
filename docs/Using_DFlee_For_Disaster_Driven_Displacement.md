Using DFlee for Disaster-driven displacement
=====

## Introduction

DFlee is an extension of the Flee code to support disaster-driven population displacement.

### Current status
Currently, DFlee has limited support for flood-driven displacement.


## How to use

To introduce flood-driven displacement, you will need to change several settings in `simsetting.yml`.

In the section `spawn_rules`, you will need to add or set the following:
```yaml
  flood_driven_spawning: True
  flood_zone_spawning_only: True
  take_from_population: True
  flood_driven_spawning:
    flood_spawn_mode: "pop_ratio"
    displaced_per_flood_day: [0.0,0.1,0.2,0.5,0.9]
```

Here, `displaced_per_flood_day` contains a list of floats. Each float in the list indicates the fraction of remaining population that will be displaced during each flooding step. For instance, if the `flood_level=3` in a location with a population of 1,000 persons, then a fraction 0.5 will depart from that location per simulation step. This will equal to 500 persons during the first step, and 250 persons during the second step, if the `flood_level` then still has the same value.

!!! note
        * It is currently not possible to combine flood-driven and conflict-driven spawning. Any Flee simulation must use one or the other.
        * `take_from_population` may be set in `simsetting.yml` already, but for DFlee to work it needs to be set to True. This is to prevent unrealistically high spawning rates.
        * The first entry in the `displaced_per_flood_day` list is actually ignored by DFlee, as such locations are not flooded and regular rules apply fully.

In the section `move_rules`, you will need to add or set the following:
```yaml
  max_flood_level: 4
  flood_movechances: [0.3,0.4,0.7,1.0,1.0]
  flood_loc_weights: [1.0,0.5,0.2,0.0,0.0]
  # flood_link_weights is not supported yet.
```

Here, `flood_movechances` is a list that *overrides* existing move chances, depending on the `flood_level`. Again, the first value in the list is actually ignored, as regular rules apply for unflooded areas. `flood_loc_weights` is a list that *multiplies* location weights based on the `flood_level`. The first value is ignored, and locations with lower weights are less likely to be selected.

!!! note
        The values in the list for `displaced_per_flood_day`, `flood_movechances` and `flood_loc_weights` are no better than educated guesses, so feel free to test DFlee with using different values for the different flood levels. A completely inaccessible area should have a move chance of 1.0 and a location weight multiplier of 0.0.

#### Reading in flood levels.

Flood levels are attributes that change over time. They are indicated with integer values between 0 and `max_flood_level`. DFlee assumes that a flood level of 0 means no flooding, and will not change its decision-making behavior irrespective of what is put in `flood_movechances` or `flood_loc_weights` on that spot.

As DFlee does not contain a flooding forecasting model, the `flood_level` attribute values for each location need to be passed to the code using a `flood_level.csv` file.

Here is an example of a `flood_level.csv` file, containing flood values for locations `A` and `B`:

```csv
#Day, A, B
0,0,1
1,0,1
2,1,1
3,1,3
4,2,1
5,1,1
6,1,0
7,1,0
8,1,0
9,1,0
10,1,1
```
## Weather Forecaster 

### Example Config Files
The flood forecaster is demonstrated using the dflee_test_laura config files in flee/FabSim/config_files. This is the same set up as dflee_test, but with additional flood forecasting settings. 

###  Testing 

The flood forecast is tested in the flee/tests/test_dflee.py. This test now relies on dflee test files in test_data/test_data_dflee. 

###  Forecast Flood Data
The flood forecast relies on flood_level data in the flood_level.csv file for each day of the flood forecast.

### Forecast Agent Data
Agents in flood_zones can be assigned an awarenes of the flood based on the location.
This should be in a demographics_floodawareness.csv file with a format like this example below:
```
floodawareness,Default,F1,F2,F3
0.0,0.1,0.1,0.1,0.1
1.0,0.2,0.2,0.2,0.2
2.0,0.7,0.7,0.7,0.7
```
There are three groups of agents denoted by the first column. 
Each column is then the different levels of awareness of the flood for each flood_zone. 


### YML SimSettings File  
The YAML configuration file contains settings for flood forecasting and agent flood awareness. 

The `flood_forecaster` parameter determines whether flood forecasting is enabled (True) or disabled (False). To enable forecasting in `simsettings.yml` include the following:
```
flood_forecaster: True
```

The 'flood_forecaster_timescale' parameter specifies the timescale for flood forecasting, where 1 represents 1 day, 2 represents 2 days, and so on. A flood_forecaster_timescale' of 5 would be used for a 5 day weather forecast. A value of 0 essentially means no knoweldge of the future flood, as the forecast is known for zero days into the future. 
```
flood_forecaster_timescale: 5
```

The 'flood_forecaster_end_time' parameter sets the maximum number of days into the simulation that the forecast data extends. The default value should be (simulation length - flood forecaster timescale). The flood forecast would end on day 9 of the simulation. This may be useful if forecasting data is only available for the first 10 days of the simulation. 
```
flood_forecaster_end_time: 9
```

The 'flood_forecaster_weights' parameter is a list of weights which account for the importance of each day in the flood forecast. The first value represents today, and the weights range from 1.0 (maximum importance) to 0.0 (no importance). This can be used to simulate people taking the days shortly after the expected cyclone very seriously, and then no longer considering the weather forecast important for their decision making process. 
The length of this array is based on the number of days in the forecast, as the relative importance of each day is considered in the forecaster. 
```
flood_forecaster_weights: [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.1,0.3, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0]
```

The 'flood_awareness_weights' parameter is a list of weights representing the level of awareness or ability to adapt to flooding. The weights range from 0.0 (no awareness) to 1.0 (high awareness). In the dflee_test_laura config example files, there are three groups (0,1,2) of agents, with low, medium and high awareness of the flooding. This would mean the 0 group of agents, with low awareness, would have 0 weighting of the flood. 
```
flood_awareness_weights: [0.0,0.5,1.0] 
```
