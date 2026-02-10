# Food Security Mechanisms

## Loading IPC Food Security data into Flee

IPC data tends to be provided on a regional level, and it can be incorporated into Flee locations by creating a file named `region_attributes_IPC.csv` in the `input_csv` directory.

Below is an example input file:

```
#Day,AB,C,D,EF
0,5.0,11.0,20.0,6.0
10,9.0,11.0,5.0,10.0
20,1.0,3.0,15.0,15.0
501,0.0,0.0,0.0,0.0
```

Here, `#Day` is the day in the simulation, while `AB`, `C` etc. are region names. The values in the cells indicate the percentage of persons with critical food deprivation (range 0-100). 

NOTE:: It is essential to include all regions in this file, although not all days need to be listed (Flee will interpolate values linearly between days).

## Applying Food-related rules

Food-related rule sets can be enabled in `simsetting.yml`. 

These include the following rules inside the `spawn_rules` section:

* `starvation_driven_spawning`: will increase spawn rate by `IPC_score * location_population / 100.0`, to a maximum value of `location_population`. [Vanhille Campos et al. 2019](https://doi.org/10.1007/978-3-030-22750-0_71)
  * Note that setting `conflict_zone_spawning_only` to True will disable this mechanism for non-conflict locations, and nullify this mechanism for conflict zones that have a conflict score of 1.0.

And these include the following rules inside the `move_rules` section:

* `flee_when_starving`: will linearly increase the Movechance according to the percentage of persons with critical food deprivation. Max is 1.0 in cases where everybody has critical food deprivation in that region. [Vanhille Campos et al. 2019](https://doi.org/10.1007/978-3-030-22750-0_71)
