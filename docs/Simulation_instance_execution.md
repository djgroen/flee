
### **Execute test instance**
To run simulation instance using Flee with test, simply type:

```sh
python3 run_csv_vanilla.py test_data/test_input_csv test_data/test_input_csv/refugee_data 5 2010-01-01 2>/dev/null
```

!!! note
	The `2>/dev/null` ensures that any diagnostics are not displayed on the screen. Instead, pure CSV output for the toy model should appear on the screen if this works correctly.

### **Execute a conflict scenario**

1. Create an output directory **`out<country_name>`**, where `<country_name>` refers to a conflict instance name. For instance, create an output directory `outcar` for the Central African Republic (CAR) situation.
	```sh
	mkdir outcar
	```

2. Execute a conflict scenario by following the execution template demonstrated below:
	```sh
	python3 conflicts/<country_name>.py <simulation_period> > out<country_name>/out.csv
	```
	where `conflicts/<country_name>.py` is a conflict instance script, `<simulation_period>` represents the simulation duration and `out<country_name>/out.csv` stores the simulation output.

	For example, execute `car-csv.py` in the conflicts directory for the simulation duration of 50 days and store the simulation output in `outcar/out.csv`:
	```sh
	python3 conflicts/car-csv.py 50 > outcar/out.csv
	```

3. To plot the simulation output, simply follow the command template below:
	```sh
	python3 plot-flee-output.py out<country_name>
	```

	where `out<country_name>` represents the simulation output directory (Step 1). To illustrate, plot the simulation output for CAR, simply execute:
	```sh
	python3 plot-flee-output.py outcar
	```	

4. To analyse and interpret simulation output, open `out<country_name>` , which will contain simulation output and UNHCR data comparison graphs for each camp, as well as average relative difference graph for the simulated conflict situation. To illustrate, analyse and interpret simulation output graphs in the `outcar` directory.


### **Parallel Performance Testing**
Parallel tests can be performed using test_par.py. The interface is as follows:
```sh
mpirun -np [number of cores] python3 tests/test_par.py [options]
```
Options can be as follows:

```sh
"-p", "--parallelmode" - Parallelization mode ([advanced], classic, cl-hilat OR adv-lowlat).
"-N", "--initialagents" - Number of agents at the start of the simulation [100000].
"-d", "--newagentsperstep", Number of agents added per time step [1000].
"-t", "--simulationperiod", Duration of the simulation in days [10].
```
Here are a few settings good for benchmarking:
```sh
mpirun -np <cores> python3 test_par.py -N 500000 -p advanced -d 10000 -t 10
mpirun -np <cores> python3 test_par.py -N 500000 -p classic -d 10000 -t 10
mpirun -np <cores> python3 test_par.py -N 500000 -p cl-hilat -d 10000 -t 10
mpirun -np <cores> python3 test_par.py -N 500000 -p adv-lowlat -d 10000 -t 10
```

















