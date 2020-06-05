.. _easyvvuq-qcgpj:

Sensitivity analysis of parameters using EasyVVUQ
=================================================

This tutorial uses VECMAtk components (https://www.vecma-toolkit.eu/) to perform parameter exploration using sensitivity analysis. The aim is to sample simulation input parameters and understand how identified assumptions in migration prediction are pivotal to the validation results. The additional components of this tutorial are:

- EasyVVUQ (https://easyvvuq.readthedocs.io/en/latest/installation.html): a Python3 library aiming to facilitate verification, validation and uncertainty quantification
- QCG-PilotJob (https://github.com/vecma-project/QCG-PilotJob): a Pilot Job system allowing execution of many subordinate jobs in a single scheduling system 

There is also a Python API for HPC execution of EasyVVUQ, which is a combination of EasyVVUQ and QCG-PilotJob. For more information, see https://easyvvuq-qcgpj.readthedocs.io/en/plugin/index.html

Parameter Exploration
---------------------
To perform sensitivity analysis on input parameters, use ``~/FabSim3/plugins/FabFlee/flee_easyvvuq.py`` script, which has two main functions:

- run_flee_easyvvuq allows to run SA for parameter exploration
- analyse_flee_easyvvuq provides analysis of obtained results.

There are six main input parameters in multiscale migration prediction, such as max_move_speed, conflict_move_chance, camp_move_chance, default_move_chance, camp_weight and conflict_weight, to analyse using Sobol's method and stochastic collocation.

In ``flee_easyvvuq.py``, we state all input parameters as follows:

  .. code:: python

          params = {  
              "awareness_level": {
                  "type": "integer",
                  "min": 0, "max": 2,
                  "default": 1
              },
              "max_move_speed": {
                  "type": "float",
                  "min": 0.0, "max": 40000,
                  "default": 200
              },
              "camp_move_chance": {
                  "type": "float",
                  "min": 0.0, "max": 1.0,
                  "default": 0.001
              },
              "conflict_move_chance": {
                  "type": "float",
                  "min": 0.0,
                  "max": 1.0,
                  "default": 1.0
              },
              "default_move_chance": {
                  "type": "float",
                  "min": 0.0,
                  "max": 1.0,
                  "default": 0.3
              },
              "camp_weight": {
                  "type": "float",
                  "min": 1.0,
                  "max": 10.0,
                  "default": 2.0
              },
              "conflict_weight": {
                  "type": "float",
                  "min": 0.1,
                  "max": 1.0,
                  "default": 0.25
              }
          }
          
          
To vary input parameters and their corresponding distributions using stochastic collocation sampler for sensitivity analysis, simply modify the following:

  .. code:: python
          
          vary = {
              "max_move_speed": cp.Uniform(20, 500),
              "camp_move_chance": cp.Uniform(0.0001, 1.0),
              "conflict_move_chance": cp.Uniform(0.1, 1.0),
              "default_move_chance": cp.Uniform(0.1, 1.0),
              "camp_weight": cp.Uniform(1.0, 10.0),
              "conflict_weight": cp.Uniform(0.1, 1.0)
          }

To change polynomial order:

  .. code:: python
  
          my_sampler = uq.sampling.SCSampler(vary=vary, polynomial_order=3)


Run EasyVVUQ analysis 
---------------------

Execution on a localhost
~~~~~~~~~~~~~~~~~~~~~~~~
1. To execute sensitivy analysis on a localhost, simply run:

  .. code:: console
  
          fab localhost run_flee_easyvvuq:‘country1(;countryN)’,simulation_periods=‘day1(;dayN)’

2. After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides. You can fetch results to ``~/FabSim3/results`` using

  .. code:: console
  
          fab localhost fetch_results

3. To analyse the obtained results, simply execute  

  .. code:: console
  
          fab localhost analyse_flee_easyvvuq:‘country1(;countryN)’

Execution on a remote machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. To execute sensitivy analysis on a remote machine, simply run:

  .. code:: console
  
          fab <remote_machine_name> run_flee_easyvvuq:‘country1(;countryN)’,simulation_periods=‘day1(;dayN)’

2. Run the following command to copy back results from the remote machine. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16):

  .. code:: console

          fab <remote_machine_name> fetch_results
          
3. To analyse results, simply run

  .. code:: console
  
          fab localhost analyse_flee_easyvvuq:‘country1(;countryN)’

  .. note:: Analysis of the obtained results are performed on a localhost.

Execution on a remote machine using QCG-Pilot Job
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For QCG-PilotJob installation, see https://github.com/vecma-project/QCG-PilotJob/blob/master/INSTALL.txt 

.. note:: if QCG-PJ is installed in the target remote machine, by using PilotJob=True, the native QCG-PilotJob will be lunched for execution. Otherwise you require to install the QCG-PilotJob service in a VirtualEnv in the target machine, and then PilotJob=True option will load QCG-PJ services from VirtualEnv. 

To install virtual environment on the remote machine alongside with QCG-PilotJob, just run: 

  .. code:: console
  
          fab <remote machine name> install_app:QCG-PilotJob,virtual_env=True

To execute easyvvuq for migration prediction using Pilot Job, run

  .. code:: console
  
          fab <remote machine name> run_flee_easyvvuq:‘country1(;countryN)’(,simulation_periods=‘day1(;dayN)’),PilotJob=True

2. Run the following command to copy back results from the remote machine. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16):

  .. code:: console

          fab <remote machine name> fetch_results
          
3. To analyse results, simply run

  .. code:: console
  
          fab localhost analyse_flee_easyvvuq:‘country1(;countryN)’

  .. note:: Analysis of the obtained results are performed on a localhost.


The execution of sensitivity analysis using a conflict scenario
---------------------------------------------------------------
For 1 country scenario: 
  
  .. code:: console

          fab localhost/<remote machine name> run_flee_easyvvuq:‘mali’,simulation_periods=‘300’
          fab localhost/<remote machine name> fetch_results
          fab localhost analyse_flee_easyvvuq:mali
            
For 2 or more countries: 

  .. code:: console
  
          fab localhost/<remote machine name> run_flee_easyvvuq:‘mali;burundi’,simulation_periods=‘300;396’
          fab localhost/<remote machine name> fetch_results
          fab localhost analyse_flee_easyvvuq:mali,burundi
    
