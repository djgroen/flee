
### **Execute test instance**
Use the following command to run a Flee simulation with the test data set:

```sh
python3 runscripts/run.py test_data/test_input_csv test_data/test_input_csv/refugee_data 0 test_data/test_input_csv/simsettings.yml 
```

!!! note
	The `2>/dev/null` ensures that any diagnostics are not displayed on the screen. Instead, pure CSV output for the toy model should appear on the screen if this works correctly.

### **Execute a conflict scenario**

1. Create an output directory:
	```sh
	mkdir outcar
	```

2. Execute a conflict scenario by following the execution template demonstrated below:
	```sh
	python3 runscripts/run.py <input csv file directory> <validation data directory> <simulation_period> <location of your simsetting.yml> > <the name of the output directory you just created>/out.csv
	```

        The easiest example of this script to check is the test example above.


3. To plot the simulation output, simply follow the command template below:
	```sh
	python3 flee/postprocessing/plot_flee_output.py <input directory> <output directory>
	```

	where `<output directory>` represents the simulation output directory (Step 1). As an example, you can run and plot the test set by navigating to your root flee directory and using the following commands:
	```sh
        mkdir -p out
	python3 runscripts/run.py test_data/test_input_csv test_data/test_input_csv/refugee_data 0 test_data/test_input_csv/simsettings.yml > out/out.csv
        python3 flee/postprocessing/plot_flee_output.py out/ out/
	```	

4. To analyse and interpret simulation output, open your output directory , which will contain simulation output and UNHCR data comparison graphs for each camp, as well as average relative difference graph for the simulated conflict situation.

5. Flee can be used in parallel, using
        ```sh
        mpirun -np [number of cores] python3 runscripts/run_par.py [options]
        ```


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

















