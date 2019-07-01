# Flee

Flee is an agent-based modelling toolkit which is purpose-built for simulating the movement of individuals across geographical locations. Flee is currently used primarily for modelling the movements of refugees and internally displaces persons (IDPs).

Flee is currently is released periodically under a BSD 3-clause license once the first journal paper is accepted.

## Parallel performance testing

Parallel tests can be performed using test_par.py. The interface is as follows:

* "-p", "--parallelmode" - Parallelization mode ([advanced], classic, cl-hilat OR adv-lowlat).
* "-N", "--initialagents" - Number of agents at the start of the simulation [10000].
* "-d", "--newagentsperstep", Number of agents added per time step [1000].
* "-t", "--simulationperiod", Duration of the simulation in days [10].


