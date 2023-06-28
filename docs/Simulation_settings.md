Simulation Settings (simsettings.yml)
=====

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
  capacity_buffer: 1
  avoid_short_stints: False
  start_on_foot: False
  softening: 10.0
optimisations:
  hasten: 1
```

_NOTE_ : The **simsetting.yml** file includes default values for each simulation setting parameters.

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

Spawn rules focus on spawning agents within simulation runs based on several settings. The first set of parameters require `True` and `False` values:

- **take_from_population** allows to subtract spawned agents from populations if the value is set to `True`. This can lead to crashes if the number of spawned agents exceeds the total population in conflict zones. Alternatively, you can remove the subtraction from populations by setting the value to `False`.
- **insert_day0** accounts for a zero insertion of agents in camps at the start of simulations by setting the value to `True`. Please set to `False` if it is not required for your conflict instance. 
- **conflict_zone_spawning_only** spawns agents only from conflict zones when set to `True`. Otherwise, it is set to `False` to spawn agents from other locations that are present in your model. 
- **camps_are_sinks** activates an attribute that you can add to locations.csv. If you set a location attribute named **deactivation_probability** to a value higher than 0.0, then there is a probability every time step that an agent in a **camp** location will be deactivated. Deactivated agents are no longer moved or changed, and are no longer logged individually although they do still count towards the totals. To have camps act as perfect sinks, simply set the **deactivation_probability** for each camp location to 1.0.

The second set includes one variable, namely **conflict_spawn_decay**. It manages the number of agents spawned from conflicts that can decay overtime.

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

#### 3. Location movechances

- **conflict_movechance** is the chance (probability) of agents (persons) leaving a conflict location (conflict zone) per day.
- **camp_movechance** refers to the chance (probability) of agents (persons) leaving a camp location per day. 
- **default_movechance** is the chance (probability) of agents (persons) leaving a regular location (i.e., town/intermediate location) per day. 
- **idpcamp_movechance** is the chance (probability) of agents (persons) leaving an internally discplaced camps per day.

#### 4. Awareness level
We are able to adjuct the agents awareness of locations by incorporating a more wide or narrow awareness level (**awareness_level**). Agents can be aware of the presence of links steps by setting the following values:

Value | Description                                                        |
------|--------------------------------------------------------------------|
 -1   | No weighting at all (no awareness)                                 |
  0   | The length of the path to the nearest settlement (road only)       |
  1   | The type of nearest settlement (location)                          |
  2   | The type of settlements adjacent to neighbouring settlements       |
  3   | The type of settlements neighbouring those neighbours of neighbours|

#### 5. Other parameters

Set the following parameter to `True` or `False`:

- **avoid_short_stints** allows to restrict displaced people that will take a break unless they at least travelled for a full day's distance in the last two days.
- **start_on_foot** is a parameters allowing agents to traverse first link on foot.

To set the following parameters, please use values:

- **capacity_buffer** refers to a location or camp is beginning to be considered full if the number of agents there exceeds (capacity OR pop) * `CapacityBuffer`.
- **softening** adds kilometers to every link distance to eliminate needless distinction between very short routes.

### Optimisations
**hasten** takes value to improve runtime performance by decreasing the number of agents. 
