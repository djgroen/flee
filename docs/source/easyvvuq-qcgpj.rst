.. _easyvvuq-qcgpj:

Sensitivity analysis of parameters using EasyVVUQ
=================================================

This tutorial uses VECMAtk components (https://www.vecma-toolkit.eu/) to perform parameter exploration using sensitivity analysis. The aim is to sample simulation input parameters and understand how identified assumptions in migration prediction are pivotal to the validation results. The additional components of this tutorial are:

- EasyVVUQ (https://easyvvuq.readthedocs.io/en/dev/installation.html): a Python3 library aiming to facilitate verification, validation and uncertainty quantification.
- QCG-PilotJob (https://github.com/vecma-project/QCG-PilotJob): a Pilot Job system allowing execution of many subordinate jobs in a single scheduling system.

There is also a Python API for HPC execution of EasyVVUQ, which is a combination of EasyVVUQ and QCG-PilotJob. For more information, see https://easyvvuq-qcgpj.readthedocs.io/en/plugin/index.html

Parameter Exploration
---------------------
To perform sensitivity analysis on input parameters, there are two sampler examples, namely 

- ``flee_easyvvuq_SCSampler.py`` script for Stochastic Collocation sampling with two functions:
    - ``flee_init_SC`` allows to run SA for parameter exploration;
    - ``flee_analyse_SC`` provides analysis of obtained results.
    
- ``flee_easyvvuq_PCESampler.py`` script for Polynomial Chaos Expansion sampling;
    - ``flee_init_PCE`` allows to run SA for parameter exploration;
    - ``flee_analyse_PCE`` provides analysis of obtained results.

There are six main input parameters in multiscale migration prediction, such as max_move_speed, conflict_move_chance, camp_move_chance, default_move_chance, camp_weight and conflict_weight, to analyse using Sobol's method and stochastic collocation.

In both of the sensitivity analysis scripts, we have all input parameters in ``(FabSim3 Home)/plugins/FabFlee/templates/params.json`` as follows:

  .. code:: python

          {
            "awareness_level": {
              "type": "integer",
              "min": 0,
              "max": 2,
              "default": 1
            },
            "max_move_speed": {
              "type": "float",
              "min": 0.0,
              "max": 40000,
              "default": 200
            },
            "max_walk_speed": {
              "type": "float",
              "min": 0.0,
              "max": 40000,
              "default": 35
            },
            "camp_move_chance": {
              "type": "float",
              "min": 0.0,
              "max": 1.0,
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
         
To vary input parameters and their corresponding distributions using stochastic collocation or polynomial chaos expansion samplers for sensitivity analysis, simply use the following parameters or comment out inessential parameters:

  .. code:: python
          
          vary = {
              "max_move_speed": cp.Uniform(100, 500),
              "max_walk_speed": cp.Uniform(10, 100),
              "camp_move_chance": cp.Uniform(0.0001, 1.0),
              "conflict_move_chance": cp.Uniform(0.1, 1.0),
              "default_move_chance": cp.Uniform(0.1, 1.0),
              "camp_weight": cp.Uniform(1.0, 10.0),
              "conflict_weight": cp.Uniform(0.1, 1.0)
          }

To change the number of polynomial order, modify the number ``1`` in the following code according to your interest: 

  .. code:: python
  
          my_sampler = uq.sampling.SCSampler(vary=vary, polynomial_order=1)


Run EasyVVUQ analysis 
---------------------

Execution on a localhost
~~~~~~~~~~~~~~~~~~~~~~~~
1. To execute sensitivy analysis on a localhost, simply run:

   .. code:: console
  
           fab localhost flee_init_SC:<conflict_name>,simulation_period=<number>
           
   or 

   .. code:: console
  
           fab localhost flee_init_PCE:<conflict_name>,simulation_period=<number>


2. After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides. Run the following command to copy back results from the remote machine and perform analysis. The results will then be in a directory inside ``(FabSim Home)/results`` and the obtained results can be analysed using 

   .. code:: console
  
           fab localhost flee_analyse_SC:<conflict_name>
    
   or 

   .. code:: console
  
           fab localhost flee_analyse_PCE:<conflict_name>


Execution on a remote machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. To execute sensitivy analysis on a remote machine, simply run:

   .. code:: console
  
           fab <remote_machine_name> flee_init_SC:<conflict_name>,simulation_period=<number>

   or 

   .. code:: console
  
           fab <remote_machine_name> flee_init_PCE:<conflict_name>,simulation_period=<number>


2. Run the following command to copy back results from the remote machine and perform analysis. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16).

   .. code:: console
  
          fab <remote_machine_name> flee_analyse_SC:<conflict_name>

   or 

   .. code:: console
  
           fab <remote_machine_name> flee_analyse_PCE:<conflict_name>

   . . note:: Analysis of the obtained results can be also performed on a localhost.


Execution on a remote machine using QCG-Pilot Job
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For QCG-PilotJob installation, see https://github.com/vecma-project/QCG-PilotJob/blob/master/INSTALL.txt 

.. note:: if QCG-PJ is installed in the target remote machine, by using PilotJob=True, the native QCG-PilotJob will be lunched for execution. Otherwise you require to install the QCG-PilotJob service in a VirtualEnv in the target machine, and then PilotJob=True option will load QCG-PJ services from VirtualEnv. 

To install virtual environment on the remote machine alongside with QCG-PilotJob, just run: 

  .. code:: console
  
          fab <remote machine name> install_app:QCG-PilotJob,virtual_env=True

To execute easyvvuq for migration prediction using Pilot Job, run

  .. code:: console
  
          fab <remote machine name> flee_init_SC:<conflict_name>,simulation_period=<number>,PilotJob=True
          
  or 
  
  .. code:: console
  
          fab <remote machine name> flee_init_PCE:<conflict_name>,simulation_period=<number>,PilotJob=True
  

2. Run the following command to copy back results from the remote machine and perform analysis. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16).

  .. code:: console
  
          fab <remote_machine_name> flee_analyse_SC:<conflict_name>
  
  or

  .. code:: console
  
          fab <remote_machine_name> flee_analyse_PCE:<conflict_name>
  
  .. note:: Analysis of the obtained results can be also performed on a localhost.


The execution of sensitivity analysis using a conflict scenario
---------------------------------------------------------------
The following commands demonstrate the execution of Mali conflict for sensitivity analysis:
  
  .. code:: console

          fab localhost/vecma_eagle flee_init_SC:mali,simulation_period=100
          fab localhost/vecma_eagle flee_analyse_SC:mali
  
  or
  
  .. code:: console
          
          fab localhost/vecma_eagle flee_init_PCE:mali,simulation_period=100
          fab localhost/vecma_eagle flee_analyse_PCE:mali
