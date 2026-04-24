### 1. Initiation
To load conflict scenario, type `fabsim localhost load_conflict:<conflict_name>`. It duplicates all existing files from a base conflict directory to a working directory, namely active_conflict, inside conflict_data directory. The load command also generates a text file (i.e. commands.log.txt) that records command logs of commencing activities.

### 2. Refinement
To modify simulation and explore policy decisions, type `fabsim localhost <FabFlee_command>`. Each FabFlee command refines different actions and changes three main input CSV files (locations.csv, routes.csv and closures.csv).

|Actions                     |FabFlee command                                            |
|----------------------------|-----------------------------------------------------------|
|Change camp capacity        |change_capacities:camp_name=capacity(,came_name2=capacity2)|
|Add a new location          |add_camp:camp_name,region,country,lat,lon                  |
|Delete an existing location |delete_location:location_name                              |
|Camp closure                |close_camp:camp_name,country,closure_start,closure_end     |
|Border closure              |close_border:country1,country2,closure_start,closure_end   |
|Forced redirection          |redirect:source,destination,redirect_start,redirect_end    |
    
### 3. Instantiation
To instantiate Flee simulation, type `fabsim localhost instantiate:conflict_given_name`. It saves parameter changes of the simulation in a new directory of config_files including conflict name, version and date of instantiation on users insert choice. It also duplicates base files of conflict scenario. 

### 4. Cleaning and iteration
To create a clean slate for further work, type `fabsim localhost clear_active_conflict`. It clears the active conflict directory upon which you can reload the conflict and change other parameters (and instantiate and run a new simulation).


## Execution
1. To run a Flee job, type `fabsim localhost flee:<conflict_given_name>,simulation_period=<number>`. 
This does the following:
  - Copy your job input, which is in `plugins/FabFlee/config_files/<conflict_given_name>`, to the remote location specified in the variable `remote_path_template` in `deploy/machines.yml`.
  - Copy the input to the remote results directory.
  - Start the remote job.
2. Simply wait for it to finish, or cancel the job using Ctrl+C.
3. After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides remotely.
4. You can fetch the remote data using `fabsim localhost fetch_results`, and then use it as you see fit! Local results are typically locations in the `results/` subdirectory.

## Ensemble execution
1. To run an ensemble of Flee jobs, type `fabsim localhost flee_ensemble:<conflict_given_name>,simulation_period=<number>`.
This does the following:
  - Copy your job input, which is in `plugins/FabFlee/config_files/<conflict_given_name>`, to the remote location specified in the variable `remote_path_template` in `deploy/machines.yml`.
  - Copy the input to the remote results directory.
  - Start the remote job.
2. Simply wait for it to finish, or cancel the job.
3. After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides remotely.
4. You can then fetch the remote data using `fabsim localhost fetch_results`, and investigate the output as you see fit. Local results are typically locations in the `results/` subdirectory.

## Analysis
FabFlee uses [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ) library to facilitate verification, validation and uncertainty quantification (VVUQ) for simulation analysis. To convert an EasyVVUQ campaign run set to a FabFlee ensemble definition, type 
`fabsim localhost campaign2ensemble:<conflict_given_name>,campaign_dir=<EasyVVUQ_root_campaign_directory.>`.
