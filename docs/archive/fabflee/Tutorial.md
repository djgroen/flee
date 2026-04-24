FabFlee coupled UQ tutorial for Multiscale Migration Prediction
=====

# 1. Setup

This tutorial uses a range of VECMAtk components, as shown in the Tube Map below.

![Graphical depiction of the VECMAtk components used in the FabFlee tutorial](https://raw.githubusercontent.com/djgroen/FabFlee/master/doc/FabFleeMap.png)

The basic tutorial relies primarily on [FabSim3](https://fabsim3.readthedocs.io/) that features an integrated test infrastructure and flexible plugin system. Specifically, we showcase the FabFlee plugin, which automates complex simulation workflows involving Multiscale Migration Prediction. 
Please refer to https://github.com/djgroen/FabFlee/blob/master/doc/TutorialSetup.md for details on how to download, install and configure the software required for this tutorial.

# 2. Multiscale migration simulations

In this section, we will show you how you can run different types of migration simulations. We first explain how you can do basic analysis using a single model, and then explain how you can perform a coupled application run that features basic uncertainty quantification. 

We will also explain how you can combine a simple stochastic conflict evolution model [Flare](https://github.com/djgroen/flare-release.git) with an agent-based migration model [FLEE](https://github.com/djgroen/flee-release.git), perform a set of runs based on different conflict evolutions, and visualize the migrant arrivals with confidence intervals. The FLEE agent-based migration model has been used in a *Scientific Reports* paper to make forecasts of forced migration in conflicts (https://www.nature.com/articles/s41598-017-13828-9), while the Flare model is still in prototype stage. 

We use the 2012 Northern Mali Conflict as a simulation instance. Please refer to https://github.com/djgroen/FabFlee/blob/master/doc/TutorialConstuct.md for details on how to construct these simulation instances.   

![Graphical depiction of population movements in Mali. Background image is courtesy of Orionist (Wikimedia)](https://raw.githubusercontent.com/djgroen/FabFlee/master/doc/mali-arrows-border.png)

## 2.1 Executing single-model migration simulations

FabFlee comes with a range of sample simulation domains. 
1. To run a single population displacement validation test, simply type:
```
fabsim localhost sflee:<conflict_name>,simulation_period=<number>
```

For instance, a basic model for the 2012 Mali conflict can be found in
`(FabSim3 Home)/plugins/FabFlee/config_files/mali`.
```
fabsim localhost sflee:mali2012,simulation_period=50
```
> _NOTE : regular runs have a `simulation_period` of 300 days, but we use a simulation period of 50 days to reduce the execution time of each simulation in this tutorial_

2. You can copy back any results from completed runs using:
```
fabsim localhost fetch_results
```
The results will then be in a directory inside `(FabSim3 Home)/results`, which is most likely called `mali_localhost_16`.

This is a little redundant for runs on localhost, but essential if you run on any remote machines, so it is good to get into this habit.

3. You can plot the simulation output using:
```
fabsim localhost plot_output:mali_localhost_16,out
```
Besides, if you want to compare different runs of a same cinflict scenario, you can run the simulation output comparison script using:
```
fabsim localhost flee_compare:<model#1>,<model#2>,...,<model#n>
```
The above command only compares runs of the same conflict scenario, with the same conflict dates and at the same geographical administrative level.

## 2.2 Ensembles

Now you may want to run multiple simulations, to see to what extent the definition of the maximum run speed in Flee affects the overall results. To do so, you can create an ensemble definition.

### Step 1: Duplicate configuration directory

Your main configuration directory for this ensemble is in `config_files/mali`. To create a run speed test, it is best to duplicate this directory by:
```
cp -r (FabFlee Location)/config_files/mali (FabFlee Location)/config_files/mali_runspeed_test
```

### Step 2: Create SWEEP directory

Next, you should create a directory named `SWEEP` inside this directory, e.g. through
```
mkdir (FabFlee Location)/config_files/mali_runspeed_test/SWEEP
```

Inside this SWEEP directory, you can then provide modified input files for each particular run instance by creating a subdirectory for it.

<br/> For instance, to create a run instance with a maximum movement speed of 200km/day for people escaping conflict, we can create a subdirectory called `200`, and create a simsetting.csv file in it with the following contents:`"MaxMoveSpeed",200`

To illustrate **simsetting.csv** file:

|MaxMoveSpeed |200 |
|-------------|----|

You can then create similar directories with inputs that have a run speed of 100, or 400. Or if you're too lazy to do that, just copy the contents of `(FabFlee Location)/config_files/validation/SWEEP/mali/example_sweepdir` to `(FabFlee Location)/config_files/mali_runspeed_test/SWEEP`. 

### Step 3: Run an ensemble of run speed tests

To run the ensemble, you can type:
```
fabsim localhost flee_ensemble:mali_runspeed_test,simulation_period=50
```

### Step 4: Analyze the output

You can copy back any results from completed runs using:
```
fabsim localhost fetch_results
```
The results will then be in a directory inside `(FabSim3 Home)/results` which is most likely called `mali_runspeed_test_localhost_16`.

And you can plot the simulation output using:
```
fabsim localhost plot_uq_output:mali_runspeed_test_localhost_16,out
```
As a reminder: we use `plot_output` to visualize outputs of a single run, and `plot_uq_output` to collate and visualize results from an ensemble.

As output you will get a range of files in the `out` subfolder of your results directory. For example, the image `Niamey-4_V2.png`, which visualizes migrant arrivals in Niamey with 95% confidence intervals based on the move speed, might look like this:

![Arrivals with confidence interval based on movespeed](https://raw.githubusercontent.com/djgroen/FabFlee/master/doc/Niamey-4_V2.png)

## 2.3 Executing Flee simulations or ensembles with replicated instances.

Replicated instances, or *replicas*, are runs that have identical inputs. However, as the Flee code is stochastic, they will result in slightly different outputs.

To run a single population displacement validation test with 5 replicas, simply type:
```
fabsim localhost sflee:<conflict_name>,simulation_period=<number>,replicas=5
```
Note that the output of each replica becomes a subdirectory in the main `results` directory. Therefore, to do ensemble analysis you may have to first move the runs into a common subfolder.

For instance, to run an ensemble of the Mali conflict with 3 replicas per ensemble instance, simply type:
```
fabsim localhost flee_ensemble:mali_runspeed_test,simulation_period=50,replicas=3
```
You can analyze the output of this simulation in the same way that you would analyze an ensemble, as replicated instance outputs are in the `RUNS/` dir as well.

## 2.4 Executing coupled migration simulations

We ultimately wish to perform of coupled models, in context of multiscale uncertainty quantification. The relevant workflow comprises the following:

1. We run a set of simple conflict evolution simulations (Flare) in the context of Mali.
2. We gather the conflict evolutions generated by this simulation, and convert them to create input for an ensemble of agent-based migration (Flee) simulation.
3. We run a Flee simulation for each conflict evolution generated.
4. We analyze and visualize a basic result.

### Step 1: Run a Flare ensemble

To run an ensemble of Flare simulations, generating different conflict evolutions, one can simply type:
```
fabsim localhost flare_ensemble:mali,N=10,simulation_period=50,out_dir=flare-out-scratch
```
This generates a range of CSV files, which you can find in `(FabFlee Home)/results-flare/flare-out-scratch`.


### Step 2: Convert Flare output to Flee input

To convert this output to Flee input you can then use.
```
fabsim localhost couple_flare_to_flee:mali,flare_out=flare-out-scratch
```
This generates a SWEEP directory in `(FabFlee Home)/config_files/mali`, which contains all the different conflict evolutions.


### Step 3: Run an ensemble of Flee simulations

To then run a Flee ensemble over all the different configurations, simply type:
```
fabsim localhost flee_ensemble:mali,simulation_period=50
```
Note that for Flee ensembles there is no need to specify the parameter `N`. It simply launches one run for every subdirectory in the `SWEEP` folder.

### Step 4: Analyze the output

You can copy back any results from runs using:
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

### Step 1-3 in a one-liner

To run a coupled simulation with basic UQ, and basically repeat steps 1-3 in one go, just type:
```
fabsim localhost flee_conflict_forecast:mali,N=10,simulation_period=50
```

# 3. Acknowledgements

This work was supported by the VECMA and HiDALGO projects, which have received funding from the European Union Horizon 2020 research and innovation programme under grant agreements No 800925 and 824115.
