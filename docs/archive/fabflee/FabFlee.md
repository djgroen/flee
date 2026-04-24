# FabFlee tutorial for Multiscale Migration Prediction
### A step-by-step guide for Execution of multiscale migration simulations and Execution of EasyVVUQ on local and HPC resources.

## Preface

In this tutorial, you will get step-by-step guidance on the usage of several VECMAtk components to simulate multiscale migration simulations, as well as perform uncertainty quantification calculations within a local and HPC execution environment. In this tutorial you will learn about the following VECMA software components and how these components are used in multiscale migration prediction application as shown in the Tube Map below:

![Graphical depiction of the VECMAtk components used in the FabFlee tutorial](https://raw.githubusercontent.com/djgroen/FabFlee/master/doc/FabFleeMap.png)

-   [FabSim3](https://fabsim3.readthedocs.io/) - an automation toolkit that features an integrated test infrastructure and a flexible plugin system. 
-   [EasyVVUQ](https://easyvvuq.readthedocs.io/en/latest/) - a Python3 library that aims to facilitate verification, validation and uncertainty quantification,
-   [QCG Pilot Job](https://wiki.vecma.eu/qcg-pilotjobs) - a Pilot Job system that allows to execute many subordinate jobs in a single scheduling system allocation,

    
    
## Contents
- [FabFlee tutorial for Multiscale Migration Prediction](#fabflee-tutorial-for-multiscale-migration-prediction)
    - [A step-by-step guide for Execution of multiscale migration simulations and Execution of EasyVVUQ on local and HPC resources.](#a-step-by-step-guide-for-execution-of-multiscale-migration-simulations-and-execution-of-easyvvuq-on-local-and-hpc-resources)
  - [Preface](#preface)
  - [Contents](#contents)
  - [Multiscale migration simulations](#multiscale-migration-simulations)
  - [Installation](#installation)
  - [Execution of migration simulations](#execution-of-migration-simulations)
    - [Execution of single-model migration simulations](#execution-of-single-model-migration-simulations)
    - [Ensemble execution of migration simulations](#ensemble-execution-of-migration-simulations)
    - [Execution of the Flee simulations or ensembles with replicated instances](#execution-of-the-flee-simulations-or-ensembles-with-replicated-instances)
    - [Execution of coupled migration simulations](#execution-of-coupled-migration-simulations)
  - [Execution on a supercomputer](#execution-on-a-supercomputer)
    - [Setup tasks for advanced use](#setup-tasks-for-advanced-use)
    - [Running an ensemble simulation on a supercomputer using QCG Broker and Pilot Jobs](#running-an-ensemble-simulation-on-a-supercomputer-using-qcg-broker-and-pilot-jobs)
    - [Running the coupled simulation on a supercomputer](#running-the-coupled-simulation-on-a-supercomputer)
  - [Sensitivity analysis of parameters using EasyVVUQ](#sensitivity-analysis-of-parameters-using-easyvvuq)
    - [Preparation of parameters for sensitivity analysis](#preparation-of-parameters-for-sensitivity-analysis)
    - [Run EasyVVUQ analysis on a localhost](#run-easyvvuq-analysis-on-a-localhost)
    - [Run EasyVVUQ analysis on a remote machine](#run-easyvvuq-analysis-on-a-remote-machine)
    - [Run EasyVVUQ analysis on a remote machine using QCG-Pilot Job](#run-easyvvuq-analysis-on-a-remote-machine-using-qcg-pilot-job)
    - [The execution of sensitivity analysis using a conflict scenario](#the-execution-of-sensitivity-analysis-using-a-conflict-scenario)
  - [Acknowledgements](#acknowledgements)

## Multiscale migration simulations
FabFlee is a FabSim3 toolkit plugin for multiscale migration simulations which automates complex simulation workflows. In this tutorial, we demonstrate different types of migration simulations. We explain how you can do basic analysis with an agent-based migration model [FLEE](https://github.com/djgroen/flee.git) using a single model. This tutorial also demonstrates how you can combine Flee with a simple stochastic conflict evolution model [Flare](https://github.com/djgroen/flare-release.git) to perform a set of runs based on different conflict evolutions, and visualize the migrant arrivals with confidence intervals. The FLEE agent-based migration model has been used in a *Scientific Reports* paper to make forecasts of forced migration in conflicts (https://www.nature.com/articles/s41598-017-13828-9), while the Flare model is still in the prototype stage. In addition, we explain how you can perform a coupled application run that features basic uncertainty quantification of input parameters in the Flee algorithm using EasyVVUQ and QCG Pilot Job. 

We use the 2012 Northern Mali Conflict as a simulation instance. Please refer to https://flee.readthedocs.io/en/latest/construction.html for details on how to construct these simulation instances.   

![Graphical depiction of population movements in Mali. The background image is courtesy of Orionist (Wikimedia)](https://raw.githubusercontent.com/djgroen/FabFlee/master/doc/mali-arrows-border.png)


## Installation
To perform this tutorial the following software packages are required:

1.  **FLEE**: To install the Flee code, see https://flee.readthedocs.io/en/latest/installation.html
   
2.  **Flare**: To install Flare, simply clone the repository: 
    ```
    git clone https://github.com/djgroen/flare-release.git
    ```
   
3.  **FabSim3**: To install FabSim3, see https://fabsim3.readthedocs.io/en/latest/installation.html#installing-fabsim3 

4.  **FabFlee**: To install the FabFlee plugin, simply go to the FabSim3 directory and type: 
    ```
    fabsim localhost install_plugin:FabFlee
    ```
    Once you have installed The FabFlee plugin, which will appear in `~/FabSim3/plugins/FabFlee`, you need to take a few small configuration steps:
    - Go to `(FabSim3 Home)/deploy`
    - Open `machines_user.yml`
    - Under the section **default:** please add the following lines:
      <br/> `flee_location: (FLEE Home)` 
      <br/> `flare_location: (Flare Home)`
      > NOTE: Please replace `FLEE Home` and `Flare Home` with your actual install directory.
 
 
## Execution of migration simulations

There are 4 different ways to execute multiscale migration simulations in FabFlee:

1. Single-model execution
2. Ensemble execution
3. Replica execution
4. Coupled execution

Each method has its unique purpose. The single-model execution can be easily performed on a laptop and instantly provide an overview to users. The ensemble execution may be useful for those who run multiple simulation instances simultaneously. The replica execution could be an interesting option for those who run simulations at once with identical inputs for analysis. The coupled execution can couple migration simulation with conflict evolution models in the context of multiscale uncertainty quantification (UQ).

In the next subsections, the step-by-step instructions are presented for each method of execution. The eventual choice of method should be based on the user’s preferences and requirements.


### Execution of single-model migration simulations

FabFlee comes with a range of sample simulation domains. 

1.  To run a single population displacement validation test, simply type:
    ```
    fabsim localhost sflee:<conflict_name>,simulation_period=<number>
    ```

    For instance, a basic model for the 2012 Mali conflict can be found in `(FabSim3 Home)/plugins/FabFlee/config_files/mali`.
    ```
    fabsim localhost sflee:mali2012,simulation_period=50
    ```
    > NOTE: Regular runs have a `simulation_period` of 300 days, but we use a simulation period of 50 days to reduce the execution time of each simulation in this tutorial.

2.  You can copy back any results from completed runs using:
    ```
    fabsim localhost fetch_results
    ```
    The results will then be in a directory inside `(FabSim3 Home)/results`, which is most likely called `mali_localhost_16`.                 This is a little redundant for runs on localhost, but essential if you run on any remote machines, so it is good to get into this habit.

3.  You can plot the simulation output using:
    ```
    fabsim localhost plot_output:mali_localhost_16,out
    ```
    Besides, if you want to compare different runs of a same cinflict scenario, you can run the simulation output comparison script using:
    ```
    fabsim localhost flee_compare:<model#1>,<model#2>,...,<model#n>
    ```
    
### Ensemble execution of migration simulations

To see to what extent the definition of the maximum run speed in Flee affects the overall results, simply run multiple simulations. To do so, you can create an ensemble definition.

1.  Your main configuration directory for this ensemble is in `config_files/mali`. To create a run speed test, it is best to  duplicate this directory by:
    ```
    cp -r (FabFlee Location)/config_files/mali (FabFlee Location)/config_files/mali_runspeed_test
    ```

2.  Create a directory named `SWEEP` inside this directory, e.g. through
    ```
    mkdir (FabFlee Location)/config_files/mali_runspeed_test/SWEEP
    ```
    Inside this SWEEP directory, you can then provide modified input files for each particular run instance by creating a   subdirectory for it.

    For instance, to create a run instance with a maximum movement speed of 200km/day for people escaping conflict, we can  create a subdirectory called `200`, and create a simsetting.csv file in it with the following contents:`"MaxMoveSpeed",200`

    To illustrate **simsetting.csv** file:

    |MaxMoveSpeed|200| 
    |------------|---|

    You can then create similar directories with inputs that have a run speed of 100, or 400. Or if you're too lazy to do   that, just copy the contents of `(FabFlee Location)/config_files/validation/SWEEP/mali/example_sweepdir` to `(FabFlee Location)/config_files/mali_runspeed_test/SWEEP`. 

3.  To run the ensemble of run speed tests, simply type:
    ```
    fabsim localhost flee_ensemble:mali_runspeed_test,simulation_period=50
    ```
4.  To analyze and visualise the output, copy back any results from completed runs using:
    ```
    fabsim localhost fetch_results
    ```
    The results will then be in a directory inside `(FabSim3 Home)/results` which is most likely called `mali_runspeed_test_localhost_16`.

    Next, plot the simulation output using:
    ```
    fabsim localhost plot_uq_output:mali_runspeed_test_localhost_16,out
    ```
    As a reminder: we use `plot_output` to visualize outputs of a single run, and `plot_uq_output` to collate and visualize results from an ensemble.

    As output, you will get a range of files in the `out` subfolder of your results directory. For example, the image `Niamey-4_V2.png`, which visualizes migrant arrivals in Niamey with 95% confidence intervals based on the move speed, might look like this:

    ![Arrivals with confidence interval based on movespeed](https://raw.githubusercontent.com/djgroen/FabFlee/master/doc/Niamey-4_V2.png)
5. To create videos from agents:
   ```
   fabsim localhost create_agents_video:<output_dir>
   ```
6. To create video from links:
   ```
   fabsim localhost create_links_video:<output_dir>
   ```
**Note**: Videos (.mp4) are generated from Flee `agents.out.*` and `links.out.*` log files. To enable the creation of these files, ensure the log_levels parameters for agent and link are set appropriately in the simsettings.yml configuration file. Additionally, the following Python packages are required: `basemap==1.4.1` and `moviepy==1.0.3`.

After generating videos for agents and links, users can combine them into a single video by overlaying the two.

Ensure both videos (agent_movements_animation.mp4 and link_movements_animation.mp4) are resized to the same resolution (e.g., 1280x720):
```
ffmpeg -i agents_movements_animation.mp4 -vf "scale=1280:720" agents_resized.mp4
ffmpeg -i links_movements_animation.mp4 -vf "scale=1280:720" links_resized.mp4
```
Combine the resized videos into a single video with adjustable transparency for both layers:
```
ffmpeg -i agents_resized.mp4 -i links_resized.mp4 -filter_complex \
"[0:v]format=rgba,colorchannelmixer=aa=0.5[bg]; \
[1:v]format=rgba,colorchannelmixer=aa=0.5[fg]; \
[bg][fg]overlay=0:0" combined_video.mp4
```
**Note:** If no admin privilege exist, download and extract binary by visiting the official FFmpeg download page, or for Linux, use a static build from johnvansickle.com.
```
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
```
Extract files:
```
tar -xvf ffmpeg-release-amd64-static.tar.xz
```
Test the installation and Full Path:
```
/path/to/ffmpeg-7.0.2-amd64-static/ffmpeg -version
```
After installation, use newly installed ffmpeg full path in the video editing commands.

### Execution of the Flee simulations or ensembles with replicated instances

Replicated instances, or *replicas*, are runs that have identical inputs. However, as the Flee code is stochastic, they will result in slightly different outputs.

To run a single population displacement validation test with 5 replicas, simply type:
```
fabsim localhost sflee:<conflict_name>,simulation_period=<number>,replicas=<number>
```
> NOTE: The output of each replica becomes a subdirectory in the main `results` directory. Therefore, to do ensemble analysis you may have to first move the runs into a common subfolder.

For instance, to run an ensemble of the Mali conflict with 3 replicas per ensemble instance, simply type:
```
fabsim localhost flee_ensemble:mali_runspeed_test,simulation_period=50,replicas=3
```
You can analyze the output of this simulation in the same way that you would analyze an ensemble, as replicated instance outputs are in the `RUNS/` dir as well.


### Execution of coupled migration simulations

To perform execution of coupled models, in the context of multiscale uncertainty quantification (UQ), the relevant workflow comprises the following:

1.  Run an ensemble of simple conflict evolution (Flare) simulations in the context of Mali, generating different conflict  evolutions, simply type:
    ```
    fabsim localhost flare_ensemble:mali,N=10,simulation_period=50,out_dir=flare-out-scratch
    ```
    This generates a range of CSV files, which you can find in `(FabFlee Home)/results-flare/flare-out-scratch`.


2.  Gather the conflict evolutions generated by this simulation, and convert them to create input for an ensemble of agent-based migration (Flee) simulation by executing
    ```
    fabsim localhost couple_flare_to_flee:mali,flare_out=flare-out-scratch
    ```
    This generates a SWEEP directory in `(FabFlee Home)/config_files/mali`, which contains all the different conflict evolutions.


3.  Run an ensemble of Flee simulations for each conflict evolution over all the different configurations, simply type:
    ```
    fabsim localhost flee_ensemble:mali,simulation_period=50
    ```
    > NOTE: For Flee ensembles, there is no need to specify the parameter `N`. It simply launches one run for every subdirectory in the `SWEEP` folder.


<br/> **Step 1-3 in a one-liner**: To run a coupled simulation with basic UQ, and basically repeat steps 1-3 in one go, just type:
```
fabsim localhost flee_conflict_forecast:mali,N=10,simulation_period=50
```

4.  Analyze and visualise the obtained output by coping back any results from runs using:
    ```
    fabsim localhost fetch_results
    ```
    The results will then be in a directory inside `(FabSim3 Home)/results` which is most likely called `mali_localhost_16`.

    Assuming this name, you can then run the following command to generate plots:
    ```
    fabsim localhost plot_uq_output:mali_localhost_16,out
    ```
    And you can inspect the plots by examining the `out` subdirectory of your results directory. For instance, if you look at `Bobo-Dioulasso-4_V2.png`, it might look like this:

    ![Arrivals in Bobo-Dioulasso with confidence interval based on conflict evolution](https://raw.githubusercontent.com/djgroen/FabFlee/master/doc/Bobo.png)



## Execution on a supercomputer

These advanced tasks are intended for those who have access to the Eagle supercomputer, and who would like to try some of the more advanced features of FabFlee.

### Setup tasks for advanced use
Before running any simulation on a remote supercomputer, you'll need to do the following:
- Make sure the target remote machine is properly defined in `(FabSim3 Home)/deploy/machines.yml` (see https://fabsim3.readthedocs.io/en/latest/remotemachineconfig.html#qcg-pilot-job-manager)
- Since that, in Flee, some python libraries such as `numpy` will be used for the job execution, in case of nonexistent of those packages, we recommended to install a virtual environment (venv) on the target machine. It can be done by running

For QCG machine:
```
fab qcg install_app:QCG-PilotJob,venv=True
```

For SLURM machine: 
```
fab <remote machine name> install_app:QCG-PilotJob,venv=True
```

> NOTE: The installation path (`virtual_env_path`) is set on `machines.yml` as one of the parameters for the target remote machine.

By installing this _venv_ on the target remote machine, the [QCG Pilot](https://github.com/vecma-project/QCG-PilotJob) Job service will be also installed alongside with other required dependencies. 


### Running an ensemble simulation on a supercomputer using QCG Broker and Pilot Jobs

1.  To run an ensemble of simulation using QCG Broker for the Mali simulation instance, simply run
    ```
    fabsim qcg flee_ensemble:mali,N=20,simulation_period=50,PJ=true
    ```
2.  To check if your jobs are finished or not, simply type
    ```
    fabsim qcg job_stat_update
    ```
3.  Once the jobs are finished, run the following command to copy back results from `qcg` machine
    ```
    fabsim qcg fetch_results
    ``` 
    The results will then be in a directory inside `(FabSim3 Home)/results`, which is most likely called `mali_eagle_16`
    
4.  To generate plots for the obtained output, simply run 
    ```
    fabsim localhost plot_uq_output:mali_qcg_16,out
    ```

### Running the coupled simulation on a supercomputer

1.  To run the coupled simulation on a remote supercomputer for the Mali simulation instance, simply execute the following
    ```
    fabsim <remote machine name> flee_conflict_forecast:mali,N=20,simulation_period=50
    ```
2.  To check if your jobs are finished or not, simply type
    ```
    fabsim <remote machine name> job_stat_update
    ```
3.  Once the jobs are finished, run the following command to copy back results from the remote machine
    ```
    fabsim <remote machine name> fetch_results
    ``` 
    The results will then be in a directory inside `(FabSim3 Home)/results`, which is most likely called `mali_eagle_16`
    
4.  To generate plots for the obtained output, simply run 
    ```
    fabsim localhost plot_uq_output:mali_qcg_16,out
    ```

## Sensitivity analysis of parameters using EasyVVUQ

The aim is to sample simulation input parameters and understand how identified assumptions in migration prediction are pivotal to the validation results.

### Preparation of parameters for sensitivity analysis

To perform sensitivity analysis on input parameters, use ``~/FabSim3/plugins/FabFlee/flee_easyvvuq.py`` script, which has two main functions:

- run_flee_easyvvuq allows to run SA for parameter exploration
- analyse_flee_easyvvuq provides an analysis of the obtained results.

There are six main input parameters in multiscale migration prediction, such as max_move_speed, conflict_move_chance, camp_move_chance, default_move_chance, camp_weight and conflict_weight, to analyse using Sobol's method and stochastic collocation.

In ``flee_easyvvuq.py``, we state all input parameters as follows:
```
          params = {
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
```         
          
To vary input parameters and their corresponding distributions using stochastic collocation sampler for sensitivity analysis, simply modify the following:

``` 
vary = {
    "max_move_speed": cp.Uniform(20, 500),
    "camp_move_chance": cp.Uniform(0.0001, 1.0),
    "conflict_move_chance": cp.Uniform(0.1, 1.0),
    "default_move_chance": cp.Uniform(0.1, 1.0),
    "camp_weight": cp.Uniform(1.0, 10.0),
    "conflict_weight": cp.Uniform(0.1, 1.0)
}
```
To change polynomial order:
```
my_sampler = uq.sampling.SCSampler(vary=vary, polynomial_order=3)
```

### Run EasyVVUQ analysis on a localhost

1.  To execute sensitivity analysis on localhost, simply run:
    ```
    fab localhost run_flee_easyvvuq:‘country1(;countryN)’,simulation_periods=‘day1(;dayN)’
    ```

2.  After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides. You can fetch results to ``~/FabSim3/results`` using
    ```
    fab localhost fetch_results
    ```

3.  To analyse the obtained results, simply execute  
    ```
    fab localhost analyse_flee_easyvvuq:‘country1(;countryN)’
    ```

### Run EasyVVUQ analysis on a remote machine

1.  To execute sensitivy analysis on a remote machine, simply run:
    ```
    fab <remote_machine_name> run_flee_easyvvuq:‘country1(;countryN)’,simulation_periods=‘day1(;dayN)’
    ```

2.  Run the following command to copy back results from the remote machine. The results will then be in a directory inside ``(FabSim3 Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16):
    ```
    fab <remote_machine_name> fetch_results
    ```     

3.  To analyse results, simply run:
    ```
    fab localhost analyse_flee_easyvvuq:‘country1(;countryN)’
    ```
    > NOTE: Analysis of the obtained results are performed on localhost.


### Run EasyVVUQ analysis on a remote machine using QCG-Pilot Job

For QCG-PilotJob installation, see https://github.com/vecma-project/QCG-PilotJob/blob/master/INSTALL.txt 

Note: If QCG-PJ is installed in the target remote machine, by using PJ=True, the native QCG-PilotJob will be launched for execution. Otherwise you require to install the QCG-PilotJob service in a virtual environment (venv) in the target machine, and then PJ=True option will load QCG-PJ services from venv. 


1.  To execute EasyVVUQ for migration prediction using Pilot Job, run:
    ```
    fab <remote machine name> run_flee_easyvvuq:‘country1(;countryN)’(,simulation_periods=‘day1(;dayN)’),PJ=True
    ```

2.  Run the following command to copy back results from the remote machine. The results will then be in a directory inside ``(FabSim3 Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16):
    ```
    fab <remote machine name> fetch_results
    ```

3.  To analyse results, simply run:
    ```
    fab localhost analyse_flee_easyvvuq:‘country1(;countryN)’
    ```
    > NOTE: Analysis of the obtained results are performed on localhost.


### The execution of sensitivity analysis using a conflict scenario

For 1 country scenario: 
```
fab localhost/<remote machine name> run_flee_easyvvuq:‘mali’,simulation_periods=‘300’
fab localhost/<remote machine name> fetch_results
fab localhost analyse_flee_easyvvuq:mali
```

For 2 or more countries: 
```
fab localhost/<remote machine name> run_flee_easyvvuq:‘mali;burundi’,simulation_periods=‘300;396’
fab localhost/<remote machine name> fetch_results
fab localhost analyse_flee_easyvvuq:mali,burundi
```
## Acknowledgements

This work was supported by the VECMA and HiDALGO projects, which have received funding from the European Union Horizon 2020 research and innovation programme under grant agreements No 800925 and 824115.

