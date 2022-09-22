# Flee
[![Build Status](https://travis-ci.com/djgroen/flee.svg?branch=master)](https://travis-ci.com/djgroen/flee)
[![GitHub Issues](https://img.shields.io/github/issues/djgroen/flee.svg)](https://github.com/djgroen/flee/issues)
[![GitHub last-commit](https://img.shields.io/github/last-commit/djgroen/flee.svg)](https://github.com/djgroen/flee/commits/master)


Flee is an agent-based modelling toolkit which is purpose-built for simulating
the movement of individuals across geographical locations. Flee is currently
used primarily for modelling the movements of forcibly displaced
persons (FDPs).

Full documentation of Flee is available at https://flee.readthedocs.io.

Official releases will be done on https://www.github.com/djgroen/flee. (flee-release is deprecated and will be removed in due course.)

## Parallel performance testing

Parallel tests can be performed using test_par.py. The interface is as follows:

mpirun -np <cores> python3 tests/test_par.py [options]
  
Options can be as follows:

* "-p", "--parallelmode" - Parallelization mode ([advanced], classic, cl-hilat OR adv-lowlat).
* "-N", "--initialagents" - Number of agents at the start of the simulation [100000].
* "-d", "--newagentsperstep", Number of agents added per time step [1000].
* "-t", "--simulationperiod", Duration of the simulation in days [10].

Here are a few settings good for benchmarking:

* `mpirun -np <cores> python3 test_par.py -N 500000 -p advanced -d 10000 -t 10`
* `mpirun -np <cores> python3 test_par.py -N 500000 -p classic -d 10000 -t 10`
* `mpirun -np <cores> python3 test_par.py -N 500000 -p cl-hilat -d 10000 -t 10`
* `mpirun -np <cores> python3 test_par.py -N 500000 -p adv-lowlat -d 10000 -t 10`


# Acknowledgements
The development on Flee has been made possible through funding from the Horizon 2020 funded HiDALGO project (grant no. 824115, https://hidalgo-project.eu) and VECMA (grant no. 800925, https://www.vecma.eu).
