Using DFlee for Disaster-driven displacement
=====

## Introduction

DFlee is an extension of the Flee code to support disaster-driven population displacement.

### Current status
Currently, DFlee has limited support for flood-driven displacement.


## How to use

To introduce flood-driven displacement, you will need to change several settings in `simulationsetting.yml`.

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
        * `take_from_population` may be set in simulationsetting.yml already, but for DFlee to work it needs to be set to True. This is to prevent unrealistically high spawning rates.
        * The first entry in the `displaced_per_flood_day` list is actually ignored by DFlee, as such locations are not flooded and regular rules apply fully.

In the section `move_rules`, you will need to add or set the following:
```yaml
  max_flood_level: 4
  flood_movechances: [0.3,0.4,0.7,1.0,1.0]
  flood_loc_weights: [1.0,0.5,0.2,0.0,0.0]
  # flood_link_weights is not supported yet.
```

Here, `flood_movechances` is a list that *overrides* existing move chances, depending on the `flood_level`. Again, the first value in the list is actually ignore, as regular rules apply for unflooded areas. `flood_loc_weights` is a list that *multiplies* location weights based on the `flood_level`. The first value is ignored, and locations with lower weights are less likely to be selected.

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

