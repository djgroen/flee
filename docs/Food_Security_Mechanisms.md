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

Food-related rule sets can be enabled in `simulationsetting.yml`. 

These include the following rules inside the `move_rules` section:

* `flee_when_starving`: will linearly increase the Movechance according to the percentage of persons with critical food deprivation. Max is 1.0 in cases where everybody has critical food deprivation in that region.
