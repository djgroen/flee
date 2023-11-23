Advanced Simulation Settings (simsetting.yml)
=====

This page describes the full range of options that can be configured in `simsetting.yml`.

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
spawn_rules:
  take_from_population: False
  insert_day0: True
  conflict_zone_spawning_only: True
  conflict_spawn_decay: [1.0,1.0,1.0,0.5,0.1]
  conflict_spawn_decay_interval: 30
move_rules:
  max_move_speed: 360.0
  max_walk_speed: 35.0
  max_crossing_speed: 20.0
  foreign_weight: 1.0
  camp_weight: 1.0
  conflict_weight: 0.25
  conflict_movechance: 1.0
  camp_movechance: 0.001
  default_movechance: 0.3
  idpcamp_movechance: 0.1
  awareness_level: 1
  capacity_buffer: 0.9
  capacity_scaling: 1.0
  avoid_short_stints: False
  start_on_foot: False
  softening: 10.0
  weight_softening: 0.0
  weight_power: 1.0
  distance_power: 1.0
  home_distance_power: 0.0
optimisations:
  hasten: 1
```

!!! note
        The **simsetting.yml** file includes default values for each simulation setting parameters.

### Log levels (log_levels)

There are five log level variables, namely **agent**, **link**, **camp**,
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

### Spawn rules (spawn_rules)

Spawn rules focus on spawning agents within simulation runs based on several settings. There are several settings that can be set to `True` or `False`:

- **take_from_population** allows to subtract spawned agents from populations if the value is set to `True`. This can lead to crashes if the number of spawned agents exceeds the total population in conflict zones. Alternatively, you can remove the subtraction from populations by setting the value to `False`.
- **insert_day0** will place existing agents in camps on Day 0 according to the camp populations in the source data, if set to `True`. If set to `False` these agents will instead be spawned in conflict zones as normal.
- **empty_camps_on_day0** will start all simulations with 0 asylum seekers / unrecognized refugees in the destinations, and adjust any validation data accordingly. This setting can sometimes be useful for conflicts where there is a large static background population in destinations such as camps. 
- **conflict_zone_spawning_only** spawns agents only from conflict zones when set to `True`. Otherwise, it is set to `False` to spawn agents from other locations that are present in your model. 
- **camps_are_sinks** activates an attribute that you can add to locations.csv. If you set a location attribute named **deactivation_probability** to a value higher than 0.0, then there is a probability every time step that an agent in a **camp** location will be deactivated. Deactivated agents are no longer moved or changed, and are no longer logged individually although they do still count towards the totals. To have camps act as perfect sinks, simply set the **deactivation_probability** for each camp location to 1.0.
- **sum_from_camps** will, if set to True, sum total migrant numbers from camp CSV data numbers, instead of from refugees.csv. The list of camp data that it will use to sum up is defined in `data_layout.csv`.

In addition, there are more advanced parameters that can be set:

- If `conflict_driven_spawning` is disabled, then one can set `conflict_spawn_decay`. This variable manages the number of agents spawned from conflicts that can decay overtime. Importantly, `conflict_spawn_decay` is disabled by default. If you wish to enable it, we recommend setting it to the value `[1.0,1.0,1.0,0.5,0.1]`, which was empirically derived (see (ITFLOWS deliverable 3.4)[https://www.itflows.eu/wp-content/uploads/2022/06/25.-D3.4-ITFLOWS.pdf]. 
  - If `conflict_spawn_decay` is set, then `conflict_spawn_decay_interval` is parameter that stores the number of days after which the spawning weight multiplier will progress to the next element of the `conflict_spawn_decay` list. The default is 30 days, which (with the decay list above) indicates that the spawning weight is halved after 90 days.
 

#### Conflict-driven spawning

A new feature in Flee 3.0 is to spawn agents based solely on the presence of conflicts, rather than obtaining numbers from `refugees.csv`. To enable this, you need to add a subsection to the Spawn rules named `conflict_driven_spawning:`.

Within this subsection several spawn modes are possible, and as an illustration we provide two examples here.

1. 1% of a location's population is displaced per conflict day, for a conflict intensity of 1.0.
```
spawn_rules:
  conflict_driven_spawning:
    spawn_mode: "pop_ratio"
    displaced_per_conflict_day: 0.01
```

2. 500 persons are displaced per conflict day per location, for a conflict intensity of 1.0.
```
spawn_rules:
  conflict_driven_spawning:
    spawn_mode: "constant"
    displaced_per_conflict_day: 500
```

Instead of the `constant` mode, it's possible to use a `poisson` mode, which randomly generates numbers using a Poisson distribution with an average of 500 in this case.

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
- **max_crossing_speed** is the most number of kilometers (km) expected to traverse on boar or walk to cross river. The default value is `2 km/hour * 10 hours` equal to `20 km` per time step (day).

#### 2. Location weights

- **conflict_weight** is the attraction multiplier for conflict locations (conflict zones).
- **camp_weight** is the attraction multiplier for camp locations (camps).
- **foreign_weight** is the attraction multiplier for foreign locations that stacks with camp multiplier. 
- **use_pop_for_loc_weight** is an *advanced* parameter that, if set to `True` includes location population as a weighting factor for non-camp locations.
  - **pop_power_for_loc_weight** is a power factor that adjusts how heavily population is accounted for, when `use_pop_for_loc_weight` is enabled. By default it is set to 0.1, which weights a location with 1M population twice as heavily as a location with 1000 population. The scaling equation is `multiplier = <location_population>^pop_power_for_loc_weight`.

_Tip: if you use `use_pop_for_loc_weight`, the weight of non-camp locations will be increased relative to camp locations. It is therefore highly recommended to then also scale up the `camp_weight` parameter (e.g. by a factor 3 if `pop_power_for_loc_weight` is set to 0.1)._

#### 3. Location movechances

- **conflict_movechance** is the chance (probability) of agents (persons) leaving a conflict location (conflict zone) per day.
- **camp_movechance** refers to the chance (probability) of agents (persons) leaving a camp location per day. 
- **default_movechance** is the chance (probability) of agents (persons) leaving a regular location (i.e., town/intermediate location) per day. 
- **idpcamp_movechance** is the chance (probability) of agents (persons) leaving an internally discplaced camps per day.

_Advanced_: It is also possible to adjust move chances based on population size of each location. This can be done using the following parameters:

- **movechance_pop_base** is an *advanced* parameter. It indicates the population level in which all original movechances are kept constant. Default: `10000`.
- **movechance_pop_scale_factor** is the power factor with which movechances are scaled by population. A positive value will result in higher chances for more populous locations, and a negative value will result in a lower chance.  

The exact multiplier equation is: `movechance *= (float(max(location.pop, location.capacity)) / movechance_pop_base)**movechance_pop_scale_factor`.
Any movechance set to higher than 1.0 will simply indicate a 100% probability of moving.


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
- **start_on_foot** is a parameter allowing agents to traverse first link on foot.
- **stay_close_to_home** is a parameter adding a weight that favours locations closer to the persons home location.

To set the following parameters, please use values:

- **capacity_scaling** is a multiplier on the capacity values in `locations.csv`, which can be used to loosen or remove the assumptions about camp capacities.
- **capacity_buffer** refers to when a location or camp is beginning to be considered full, and will become less attractive.  Attractiveness will be 0 when the occupancy is more than `location.capacity * capacity_scaling`. The attractiveness will begin to be scaled down when the occupancy is higher than `capacity_buffer * location.capacity * capacity_scaling`. Values should range between 0.0 and 1.0.
- **softening** adds kilometers to every link distance to reduce the preference strength when choosing between very short routes. Default is 10.0.
- **weight_softening** adds a constant to *all* link weight values, increasing randomness of the algorithm. Default is 0.0.
- **weight_power** puts a power factor on the *total calculated weight*. A value of 0.0 indicates that the algorithm becomes a random walk, while a weight of 1.0 preserves the default behavior. If set to larger values then agents will be more aggressive in dismissing suboptimal routes.
- **distance_power** is a factor that indicates the importance of distance in weight calculations. Default is (inverse) linear (1.0). Change to 2.0 for a quadratic relation, 0.5 for a weaker square-root relation, or 0.0 if the distance to a destination should not be a factor in decision-making at all. Not that this only affects the link weighting calculation; agent perception can still be limited by the awareness level even when `distance_power` is set to 0.0. The scaling equation is `multiplier = 1 / <distance>^distance_power`.
- **home_distance_power** is a factor that indicates the importance of hone distance in weight calculations. Works the same as `distance_power` except that it is only triggered when `stay_close_to_home` is enabled. Default value is 0.5 (inverse sqrt relation).

### Optimisations
**hasten** takes value to improve runtime performance by decreasing the number of agents. 
