Simulation Settings (simsetting.yml)
=====

This file summarizes the basic settings in `simsetting.yml`. An example simsetting.yml can for example be found here: <https://github.com/djgroen/FabFlee/blob/master/config_files/mali2012/simsetting.yml>

## Introduction

An agent-based model for forced displacement requires an initial model construction for conflict instances. Subsequently, these models are refined to accommodate each unique conflict situation and to modify default simulation settings that may not satisfy or fit all scenarios. Hence, **SimulationSettings.py** includes parameters that can be modified to the desired settings. There are four main themes:

- **log_levels** contain log level variables.
- **spawn_rules** include agent-based spawning rules.
- **move_rules** refer to agent-based movement rules.
- **optimisations** provide settings to improve runtime performance.

Each theme has its own set of variables or parameters with predefined values. The values can be configured in the **simsetting.yml** file for each conflict as shown below:
 
```yml
log_levels:
  agent: 0 
  link: 0 
  camp: 0
  conflict: 0 
  init: 0
  granularity: location 
spawn_rules:
  take_from_population: False
  insert_day0: True
move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 1.0
  camp_movechance: 0.001
  default_movechance: 0.3
  awareness_level: 1
  capacity_scaling: 1.0
  avoid_short_stints: False
  start_on_foot: False
  weight_power: 1.0
optimisations:
  hasten: 1
```

!!! note
        The **simsetting.yml** file includes default values for each simulation setting parameters.

### Log levels (log_levels)

There are several logging level variables, such as **agent**, **link**, **camp**,
**conflict** and **init**. If the value is set to `0` for these log levels,
then no information is obtained from simulation runs. To obtain information,
the values should be set to `1` (or `2` or `3` for agent log level). You can refer to
the table below to gain an understanding of the type of information that is
obtained from each log level (when set to `1` or `2`).

 Variable | Values | Obtained information                                                |
----------|--------|---------------------------------------------------------------------|
 agent    |    1   | Average times for agents to reach camps at any timestep (aggregated)|
 agent    |    2   | Duplicate entries when agents do multiple hops in one timestep      |
 agent    |    3   | Duplicated entries have the hop number as part of the time step.    |
 link     |    1   | Cumulative agent counts on links at any timestep (aggregated)       |
 camp     |    1   | Locations added and conflict zones assigned per timestep            |
 conflict |    1   | Conflict zone spawning     			                 |
 init     |    1   | Initialisation                                                      |
 idp\_totals |    1   | Add a "total IDPs" column at the end of out.csv.                  |


In some cases, it is not desirable to output geographical information on the `location` scale. This can be toggled using an additional variable:

- `granularity` is a String variable that can be set either to `location`, to write logs by location, or to `region`. In the latter case, both the agent and link logs will contain the region name of agents, instead of their location names. The region name can be at any admin level, and is read from the `region` field for each location in `locations.csv`.  

### Spawn rules (spawn_rules)

Spawn rules focus on spawning agents within simulation runs based on several settings. There are several settings that can be set to `True` or `False`:

- **take_from_population** allows to subtract spawned agents from populations if the value is set to `True`. This can lead to crashes if the number of spawned agents exceeds the total population in conflict zones. Alternatively, you can remove the subtraction from populations by setting the value to `False`.
- **insert_day0** accounts for a zero insertion of agents in camps at the start of simulations by setting the value to `True`. Please set to `False` if it is not required for your conflict instance. 

#### Spawning agents from file.

Flee has the option to read in agents from a CSV file (named `agents.csv`) and place these directly into the simulation at startup. This mode can be activated by toggling the following setting:
```
spawn_rules:
  read_from_agents_csv_file: True
```

When this is enabled, agents will be read in from `agents.csv` and added to the simulation. _This mechanism complements any other spawning mechanism, so if you only wish to spawn agents from the CSV file, then you must disable all other spawning mechanisms._

The formatting of `agents.csv` should be as follows:

- 1st line should contain "location name", followed by the name of all agent attribute types in a comma separated list.
- All other lines contain information for the agents, one agent per line, with its location name followed with all the attribute values, all separated by commas.

An example `agents.csv` file is provided as part of the Flee installation. It can be found in `$FLEE/test_data/test_input_csv/agents.csv`.  

### Movement rules (move_rules)
We can modify the movement rules of agents based on the movement speed, location weights, movechance (probability) of locations, agents' awareness levels and other parameters. 

#### 1. Movement speeds
There are three movement types in the Flee code, which can :

- **max_move_speed** refers to the most number of kilometers (km) expected to traverse by agents per time step. The default value is `360 km` per time step (`30 km/hour * 12 hours`). 
- **max_walk_speed** is the most number of kilometers (km) expected to traverse per time step on foot. The default value is `3.5 km/hour * 10 hours` equal to `35 k`m per time step (day).

#### 2. Location weights

- **conflict_weight** is the attraction multiplier for conflict locations (conflict zones).
- **camp_weight** is the attraction multiplier for camp locations (camps).
- **foreign_weight** is the attraction multiplier for foreign locations that stacks with camp multiplier. 

#### 3. Location movechances

- **conflict_movechance** is the chance (probability) of agents (persons) leaving a conflict location (conflict zone) per day.
- **camp_movechance** refers to the chance (probability) of agents (persons) leaving a camp location per day. 
- **default_movechance** is the chance (probability) of agents (persons) leaving a regular location (i.e., town/intermediate location) per day. 

#### 4. Awareness level
We are able to adjuct the agents awareness of locations by incorporating a more wide or narrow awareness level (**awareness_level**). Agents can be aware of the presence of links steps by setting the following values:

Value | Description                                                        |
------|--------------------------------------------------------------------|
 -1   | No weighting at all (no awareness)                                 |
  0   | The length of the path to the nearest settlement (road only)       |
  1   | The type of nearest settlement (location)                          |
  2   | The type of settlements adjacent to neighbouring settlements       |
  3   | The type of settlements neighbouring those neighbours of neighbours|

#### 5. Movement Rule Parameters for Advanced Users

Set the following parameter to `True` or `False`:

- **avoid_short_stints** allows to restrict displaced people that will take a break unless they at least travelled for a full day's distance in the last two days.
- **start_on_foot** is a parameters allowing agents to traverse first link on foot.
- **stay_close_to_home** is a parameter adding a weight that favours locations closer to the persons home location.

To set the following parameters, please use values:

- **capacity_scaling** is a multiplier on the capacity values in `locations.csv`, which can be used to loosen or remove the assumptions about camp capacities.
- **softening** adds kilometers to every link distance to reduce the preference strength when choosing between very short routes. Default is 10.0.
- **weight_power** puts a power factor on the *total calculated weight*. A value of 0.0 indicates that the algorithm becomes a random walk, while a weight of 1.0 preserves the default behavior. If set to larger values then agents will be more aggressive in dismissing suboptimal routes.

### Optimisations
**hasten** is a parameter that can be used to speed up the simulation. The default is 1.0. By setting it to a larger value, the simulation will proportionally reduce its number of agents, speeding up execution. When using a value for `hasten` larger than 1.0, the simulation becomes gradually less accurate and will exhibit more variability in its results between individual runs.

!!! note
        Flee is not a deterministic code, and even without hasten, results can fluctuate by as much as 1% between identically configured simulation runs.
