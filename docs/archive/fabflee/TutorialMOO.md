# Multiobjective Optimization in FabFlee
This documentation details how to execute the multiobjective optimization (MOO) for camp location problems in FabFlee. For MOO functionalities, we integrate pymoo (Multi-objective Optimization in Python, https://github.com/anyoptimization/pymoo). Pymoo is an open-source framework that offers state of the art single- and multi-objective algorithms and many more features related to multi-objective optimization such as visualization and decision making. For further details about pymoo, please refer to https://pymoo.org/. Note that our MOO code in FabFlee is developed based on pymoo version 0.6.0. To install pymoo, simply run the following command:
```sh
pip install pymoo
```

## Dependencies
MOO functionalities requires the following Python modules:
* pymoo
* pandas 
* numpy
* Cython
* PyYAML
* mpi4py
* pyproj
* shapely
* Rtree
* Matplotlib
* beartype

## MOO functionalities in FabFlee
### Algorithms
To perform MOO in FabFlee, we implement five well-known MOO algorithms based on pymoo, including NSGA-II, SPEA2, NSGA-III, MOEA/D, BCE-MOEA/D. In particular, the BCE-MOEA/D is developed as close as possible to the proposed version, while the others are imported from pymoo.

### Test problems
In `~/FabSim3/plugins/FabFlee/config_files` folder, ten test problems regarding multiobjective camp location problems are constructed.

| **Index** | **Test Problem** | **Number of Objectives** |
|:----:|:----:|:------:|
| 1 | moo_f1_c1_t3 | 3 | 60 |
| 2 | moo_f1_c3_t4 | 3 | 60 |
| 3 | moo_ssudan_H0_3obj | 3 |
| 4 | moo_ssudan_H10_3obj | 3 | 
| 5 | moo_ssudan_R0_3obj | 3 | 
| 6 | moo_ssudan_R10_3obj | 3 | 
| 7 | moo_ssudan_H0_5obj | 5 |
| 8 | moo_ssudan_H10_5obj | 5 | 
| 9 | moo_ssudan_R0_5obj | 5 |
| 10 | moo_ssudan_R10_5obj | 5 |

#### Objectives for three-objective test problems
Among these test problems, six of them are tri-objective optimization problems (**test problems 1-6**). The three objectives are (1) minimizing individual travel distance, (2) maximizing the number of successful camp arrivals, and (3) minimizing the amount of idle capacity in the new camp. These objectives are calculated based on Flee simulation for each candidate solution obtained in each generation of the MOO algorithm.

#### Objectives for five-objective test problems
The remaining test problems are five-objective optimization problems (**test problems 7-10**). The five objectives are (1) minimizing individual travel distance, (2) maximizing the number of successful camp arrivals, and (3) minimizing the amount of idle capacity in the new camp, (4) minimizing the food insecurity level of a possible site, and (5) maximizing site accessibility. The first three objectives are calculated based on Flee simulation, while the last two objectives are based on external datasets.


## Execution
### Parameter settings
Before executing MOO in FabFlee, some algorithm parameters should be configured.
1. In `~/FabSim3/plugins/FabFlee/MOO_setting.yaml`, you can select an MOO algorithm (e.g., set `alg_name: "NSGA2"` to represent NSGA-II algorithm), and set relevant parameters, e.g., population size `pop_size: 4` and the number of generations `n_gen: 2`.

2. In `~/<problem_name>/simsetting.yml`, you can change the parameter settings regarding conflict simulation for a test problem. More details regarding the simulation settings can be found here https://flee.readthedocs.io/en/master/Simulation_settings/. In particular, for **test problems 3-10**, we scale down the number of agents by setting the parameter `hasten: 100` to improve runtime performance.

_NOTE_ : The **simsetting.yml** file includes default values for simulation setting parameters.

### Preparation for remote execution on ARCHER2
Create `machines_FabFlee_user.yml` located in `~/FabSim3/plugins/FabFlee` folder. Under the section localhost, please add the following lines: 
```sh
flee_location: "<PATH_TO_FLEE>"
username: "<your-username>"
budget: "<your-budget>"
project: "<your-project>"
```

### Optimization

1.  To submit and execute multiobjective optimization for an camp location problem, you can type:
	
 	```sh
	# to execute on localhost
	fabsim localhost flee_MOO:<problem_name>,simulation_period=<number>,cores=<number>,job_desc="<description>"
	# to execute on remote machine
	fabsim archer2 flee_MOO:<problem_name>,simulation_period=<number>,cores=<number>,job_desc="<description>"
	```
	where

- `problem_name` denotes the test problem to be optimized, 
- `cores` represents the number of cores for execution (default value is 1),
- `job_desc` stands for the description of a submitted job.
 
3.  Simply wait for it to finish or to cancel the job press Ctrl+C.
4.  After the job has finished, a message is printed indicating where the output data resides remotely.
5.  You can fetch the remote data using:
	```sh
	fabsim localhost fetch_results
	```
	Local results are typically locations in the `~/FabSim3/results/` subdirectory, which are called in the format `<problem_name>_<machine_name>_<number_of_cores>_<description>`, e.g., `moo_ssudan_H0_5obj_localhost_1_nsga2`.


Within this subdirectory,
-  `log_MOO.txt` includes the historical data during the optimization process of an MOO algorithm.
-  `population.csv` stores those obtained solutions (camp locations) and corresponding objective values. These solutions represent different trade-offs among those objectives.
-  `SWEEP` directory contains the ensemble simulation results for different conflict instances generated during the optimization process. Each conflict instance `SWEEP/<number>` is different with different location generated for establishing a new refugee camp (named **Z**). Thus, two input files `locations.csv` and `routes.csv` are different for each migration simulation.

