.. _fabflee:

.. FabFlee: Automated Flee-based simulation
.. ========================================

Overview
========

To automate the construction, execution and analysis of forced migration simulation, we use a FabSim3-based FabFlee plugin (https://github.com/djgroen/FabFlee). It provides an environment for researchers and organisations to construct and modify simulations, instantiate and execute multiple runs for different policy decisions, as well as to validate and visualise the obtained results against the existing data.


Installing the FabSim3 automation toolkit
=========================================

To install FabSim3, you need to install dependencies and clone the FabSim3 repository::

  git clone https://github.com/djgroen/FabSim3.git

For detailed installation instructions, see https://fabsim3.readthedocs.io/en/latest/index.html 


Installing the FabFlee plugin
=============================

Once you have installed FabSim3, you can install FabFlee by typing::

  fabsim localhost install_plugin:FabFlee

The FabFlee plugin will appear in ``~/FabSim3/plugins/FabFlee``.


Configuration
-------------

There are a few small configuration steps to follow:
1. Go to ``~/FabSim3/deploy``.

2. Open ``machines_user.yml``.

3. Under the section **default:**, please add the following lines::

   flee_location: (FLEE Home) 
   
.. note: Please replace (FLEE Home) with your actual install directory.
   
   flare_location: (Flare Home)
   
.. note: Please replace (Flare Home) with your actual install directory.


Executing forced migration simulation using FabFlee
===================================================

Initiation
----------
To load conflict scenario, simply type::

  fabsim localhost load_conflict:<conflict_name>
  
It duplicates all existing files from a base conflict directory to a working directory, namely **active_conflict**, inside **conflict_data** directory. The load command also generates a text file (i.e. commands.log.txt) that records command logs of commencing activities.


Refinement
----------
To modify simulation and explore policy decisions, simply type::
  
  fabsim localhost <FabFlee_command>

Each FabFlee command refines different actions and changes three main input CSV files (locations.csv, routes.csv and closures.csv)::

=============================  ============================================================
Actions                        FabFlee command                                            
-----------------------------  ------------------------------------------------------------
Change camp capacity           change_capacities:camp_name=capacity(,came_name2=capacity2)
Add a new location             add_camp:camp_name,region,country,lat,lon                  
Delete an existing location    delete_location:location_name                              
Camp closure                   close_camp:camp_name,country,closure_start,closure_end     
Border closure                 close_border:country1,country2,closure_start,closure_end   
Forced redirection             redirect:source,destination,redirect_start,redirect_end    
=============================  ============================================================
    
    
Instantiation
-------------
To instantiate Flee simulation, simply type::

  fabsim localhost instantiate:<conflict_name> 

It saves parameter changes of the simulation in a new directory of **config_files** including conflict name, version and date of instantiation on users insert choice. It also duplicates base files of conflict scenario. 


Cleaning and iteration
----------------------
To create a clean slate for further work, run the following command::

  fabsim localhost clear_active_conflict
  
It clears the active conflict directory upon which you can reload the conflict and change other parameters (and instantiate and run a new simulation).


Execution
---------

1. To run a Flee simulation::

  fabsim localhost flee:<conflict_name>,simulation_period=<number>
  
This does the following:
- Copy your job input, which is in ``~/FabSim3/plugins/FabFlee/config_files/<conflict_name>``, to the remote location specified in the variable **remote_path_template** in ``~/FabSim3/deploy/machines.yml``.
- Copy the input to the remote results directory.
- Start the remote job.

2. Simply wait for it to finish or to cancel the job press Ctrl+C.

3. After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides remotely.

4. You can fetch the remote data using::

  fabsim localhost fetch_results 
  
Local results are typically locations in the ``~/FabSim3/results/`` subdirectory.


Ensemble execution
------------------
1. To run an ensemble of Flee jobs, simply type::

  fabsim localhost flee_ensemble:<conflict_name>,simulation_period=<number>
  
This does the following:
- Copy your job input, which is in ``~/FabSim3/plugins/FabFlee/config_files/<conflict_name>``, to the remote location specified in the variable **remote_path_template** in ``~/FabSim3/deploy/machines.yml``.
- Copy the input to the remote results directory.
- Start the remote job.

2. Simply wait for it to finish, or to cancel the job press Ctrl+C.

3. After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides remotely.

4. You can then fetch the remote data using::

  fabsim localhost fetch_results
  
Local results are typically locations in the ``~/FabSim3/results/`` subdirectory.




