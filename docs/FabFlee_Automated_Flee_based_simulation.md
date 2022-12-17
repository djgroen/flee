
# **FabFlee: Automated Flee-based simulation**

To automate the construction, execution and analysis of forced migration simulation, we use a FabSim3-based FabFlee plugin (<https://github.com/djgroen/FabFlee>). It provides an environment for researchers and organisations to construct and modify simulations, instantiate and execute multiple runs for different policy decisions, as well as to validate and visualise the obtained results against the existing data.

## **Installing the FabSim3 automation toolkit**
To install FabSim3, you need to clone the FabSim3 repository:
```sh
git clone https://github.com/djgroen/FabSim3.git
```
To configure FabSim3 and install required dependencies, go to <https://fabsim3.readthedocs.io/en/latest/index.html> that provides detailed instructions.

## **Installing the FabFlee plugin**
Once you have installed FabSim3, you can install FabFlee by typing:
```sh
fabsim localhost install_plugin:FabFlee
```
The FabFlee plugin will appear in `~/FabSim3/plugins/FabFlee`.

### *Configuration*
There are a few small configuration steps to follow:

1.  Go to `~/FabSim3/plugins/FabFlee`.
2.  Open `machines_FabFlee_user.yml`.
3.  Under the section **localhost:**, please add the following lines:
	```yaml
	flee_location: (FLEE Home)
	```

## **Automated construction of a new conflict scenario using FabFlee**

### *Step 1: Create a new conflict instance*
To create a new conflict instance for simulation in `~/FabSim3/plugins/FabFlee/config_files` directory, execute the following command:
```sh
fabsim localhost new_conflict:<conflict_name>
```
which will automatically generate required input and validation files, as well as execution scripts in
`~/FabSim3/plugins/FabFlee/config_files/<conflict_name\>`, as presented in the [simulation instance construction](https://flee.readthedocs.io/en/latest/construction.html) section.

### *Step 2: Extract conflict zones from ACLED database*

-   Go to <https://acleddata.com/data-export-tool/>, complete fields with conflict instance details and download ACLED data.
-   Rename downloaded file as acled.csv and place it in `~/FabSim3/plugins/FabFlee/config_files/<conflcit_name>`
-   In your terminal, go to your `~/FabSim3/plugins/FabFlee` directory and execute the following command with your conflict instance details:
	```sh
	fabsim localhost process_acled:country=<conflict_name>,start_date=<DD-MM-YYYY>,filter=earliest/fatalities,admin_level=admin1/admin2/admin3/location
	```

	!!! note
		-   **country** is the name of the country directory the acled.csv is stored in.
		-   **start_date** uses DD-MM-YYYY format and is the date which conflict_date will be calculated from.
		-   **filter** takes earliest or fatalities. Earliest will keep the first occurring (using date) location and remove all occurrences that location after that date. Fatalities will keep the highest fatalities of each location and remove all other occurrences of that location.
		-   **admin_level** has 4 divisions of conflict locations for you to choose and process, where *ADMIN1* is the largest sub-national administrative region, *ADMIN2* is the second largest sub-national administrative region, *ADMIN3* is the third largest sub-national administrative region or *LOCATION* is the location in which the event took place.

This will produce the locations.csv into the `input_csv` directory in `~/FabSim3/plugins/FabFlee/config_files/<conflict_name>/input_csv`for the given country.

To demonstrate, the following command uses the Mali conflict situation:
```sh
fabsim localhost process_acled:country=mali,start_date=20-01-2010,filter=earliest,admin_level=location    
```
which creates the locations.csv file in `~/FabSim3/plugins/FabFlee/config_files/mali/input_csv`.

### *Step 3: Extract population data for your conflict instance using OpenRouteService API*

1.  Obtain OpenRouteService API key
	-   Go to <https://openrouteservice.org/dev/#/signup> and sign up using your Github account or by filling the registration form to obtain OpenRouteService API key
	-   After registration, click Tokens window (next to Profile in Dev Dashboard) and request a Token by specifying a name (e.g. API key) and clicking Create Token, which will provide an API Key (e.g. `5b3ce3597851110...`)

2.  Install Java JRE or openJDK version 8 or later
	-   For Linux, execute the following command to install OpenJDK:
		```sh
		sudo apt-get install openjdk-11-jdk
		```
	-   For MacOS: download and install <https://www.java.com/en/download/manual.jsp> for MacOS, then open terminal and type:
		```sh
		java -version
		```
3.  Download Citygraph.zip
	-   Go to <https://github.com/qusaizakir/CityGraph/releases/tag/v0.7.0>, download `citygraph.zip` and extract to your working directory

4.  Extract population data for your conflict instance
	-   Add CityGraph directory location and API key details under `localhost:` in `~/FabSim3/plugins/FabFlee/machines_FabFlee_user.yml`:
		```yaml
		localhost:
		...

		# location of City Graph application,
		# you can download it from 
		# https://github.com/qusaizakir/CityGraph/releases
		cityGraph_location: "your citygraph directory location"
		cityGraph_API_KEY: "your API key"
		cityGraph_COUNTRY_CODE: ""
		cityGraph_POPULATION_LIMIT: ""
		cityGraph_CITIES_LIMIT: ""  
		```
	-   Execute the following command to extract population numbers for your conflict instance:
		```sh
		fabsim localhost add_population:<conflict_name>
		```
		which will populate locations.csv in `~/FabSim3/plugins/FabFlee/config_files/<conflict_name>/input_csv`

## **Initiate, refine and instantiate a conflict instance using FabFlee**

### *Initiation*
To load conflict scenario, simply type:
```sh
fabsim localhost load_conflict:<conflict_name>
```
It duplicates all existing files from a base conflict directory to a working directory, namely `active_conflict`, inside `conflict_data` directory. The load command also generates a text file (i.e. `commands.log.txt`) that records command logs of commencing activities.

### *Refinement*

To modify simulation and explore policy decisions, simply type:
```sh
fabsim localhost <FabFlee_command>
```
Each FabFlee command refines different actions and changes three main input CSV files (`locations.csv`, `routes.csv` and `closures.csv`):

| **Actions**                   | **FabFlee command**                                              |
|:------------------------------|:-----------------------------------------------------------------|
| Change camp capacity          | change_capacities:camp_name=capacity(,came_name2=capacity2)      |
| Add a new location            | add_camp:camp_name,region,country,lat,lon                        |
| Delete an existing location   | delete_location:location_name                                    |
| Camp closure                  | close_camp:camp_name,country,closure_start,closure_end           |
| Border closure                | close_border:country1,country2,closure_start,closure_end         |
| Forced redirection            | redirect:source,destination,redirect_start,redirect_end          |

### *Instantiation*

To instantiate Flee simulation, simply type:
```sh
fabsim localhost instantiate:<conflict_name> 
```
It saves parameter changes of the simulation in a new directory of `config_files` including conflict name, version and date of instantiation on users insert choice. It also duplicates base files of conflict scenario.

### *Cleaning and iteration*
To create a clean slate for further work, run the following command:
```sh
fabsim localhost clear_active_conflict
```
It clears the active conflict directory upon which you can reload the conflict and change other parameters (and instantiate and run a new simulation).

### *Execution*

1.  To run a Flee simulation:
	```sh
	fabsim localhost flee:<conflict_name>,simulation_period=<number>
	```
	This does the following: - Copy your job input, which is in `~/FabSim3/plugins/FabFlee/config_files/<conflict_name>`, to the remote location specified in the variable **remote_path_template** in `~/FabSim3/deploy/machines.yml`. - Copy the input to the remote results directory. - Start the remote job.

2.  Simply wait for it to finish or to cancel the job press Ctrl+C.
3.  After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides remotely.
4.  You can fetch the remote data using:
	```sh
	fabsim localhost fetch_results
	```
	Local results are typically locations in the `~/FabSim3/results/` subdirectory.
5.  To plot the results use:
	```sh
	fabsim localhost plot_output:<conflict_name>,out
	```
	If the results directory includes Multiscale results, it will plot them too. Otherwise, it only plots serial mode results.

### *Ensemble execution*

1.  To run an ensemble of Flee jobs, simply type:
	```sh
	fabsim localhost flee_ensemble:<conflict_name>,simulation_period=<number>
	```
	This does the following: - Copy your job input, which is in `~/FabSim3/plugins/FabFlee/config_files/<conflict_name>`, to the remote location specified in the variable **remote\_path\_template** in `~/FabSim3/deploy/machines.yml`. - Copy the input to the remote results directory. - Start the remote job.

2.  Simply wait for it to finish, or to cancel the job press Ctrl+C.
3.  After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides remotely.
4.  You can then fetch the remote data using:
	```sh
	fabsim localhost fetch_results
	```
	Local results are typically locations in the `~/FabSim3/results/` subdirectory.

### *Plotting link graphs for quick visual inspection*

1. To quickly plot a link graph, simply type:
        ```sh
        fabsim localhost plot_flee_links:<config_name>
        ```

