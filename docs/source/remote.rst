.. _remote:

Remote execution on a supercomputer
===================================

These advanced tasks are intended for those who have access to the Eagle supercomputer.

Setup tasks for advanced use
----------------------------
Before running any simulation on a remote supercomputer, the following is required:

- Make sure the target remote machine is properly defined in `(FabSim Home)/deploy/machines.yml` 

- In Flee, some python libraries such as `numpy` will be used for the job execution, in case of nonexistent of those packages, we recommended to install a *_virtualenv_* on the target machine. It can be done by running:

  - For QCG machine: 
  
  .. code:: console
   
          fab qcg install_app:QCG-PilotJob,virtual_env=True
	
  - For SLURM machine: 
  
  .. code:: console
   
          fab <remote_machine_name> install_app:QCG-PilotJob,virtual_env=True
          
  .. note:: The installation path (``virtual_env_path``) is set on ``machines.yml`` as one of parameters for the target remote machine. By installing this ``_virtualenv_`` on the target remote machine, the QCG Pilot Job (https://github.com/vecma-project/QCG-PilotJob) service will be also installed alongside with other required dependencies.


Running an ensemble simulation on a supercomputer using Pilot Jobs and QCG Broker
---------------------------------------------------------------------------------
1. To run an ensumble simulation on QCG machine using Pilot Jobs, run the following:

  .. code:: console

          fabsim qcg flee_ensemble:<conflict_name>,N=20,simulation_period=<number>,PilotJob=true

or 

  .. code:: console

          fabsim <remote_machine_name> flee_ensemble:<conflict_name>,N=20,simulation_period=<number>,PilotJob=true


To showcase the execution of ensemble simulation using Pilot Job, simply run Mali conflict instance:
 
  .. code:: console
   
          fabsim eagle_vecma flee_ensemble:mali,N=20,simulation_period=50,PilotJob=true

2. To check if your jobs are finished or not, simply run:

  .. code:: console
  
          fabsim qcg/<remote_machine_name> job_stat_update
          
2. Run the following command to copy back results from ``qcg`` or remote machine. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called ``<conflict_name>_qcg_<number>`` or ``<conflict_name>_<remote_machine_name>_<number>`` (e.g. ``mali_qcg_16`` or ``mali_eagle_vecma_16``)

  .. code:: console
  
          fabsim qcg/<remote_machine_name> fetch_results

3. To generate plots from the obtained results:

  .. code:: console
  
          fabsim localhost plot_uq_output:<conflict_name>_qcg_<number>,out
   

Running the coupled simulation on a supercomputer
-------------------------------------------------
1. To execute simulation jobs on a supercomputer, simply run: 

  .. code:: console
  
          fabsim <remote_machine_name> flee_conflict_forecast:<conflict name>,N=20,simulation_period=<number>

2. To check if your jobs are finished or not, simply type

  .. code:: console
  
          fabsim <remote_machine_name> job_stat_update
          
3. Run the following command to copy back results from `eagle` machine. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called ``<conflict_name>_<remote_machine_name>_<number>`` (e.g. ``mali_eagle_vecma_16``):

  .. code:: console
     
          fabsim <remote_machine_name> fetch_results

3. To generate plots from the obtained results, simply type:

  .. code:: console

          fabsim localhost plot_uq_output:<conflict_name>_<remote_machine_name>_<number>,out
