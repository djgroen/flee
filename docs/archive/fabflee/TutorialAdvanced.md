Going the extra mile (content for advanced users)
=========

These advanced tasks are intended for those who have access to the Eagle supercomputer, and who would like to try some of the more advanced features of FabSim3.

# Setup tasks for advanced use
Before running any simulation on a remote supercomputer, you'll need to do the following:
- Make sure the target remote machine is properly defined in `(FabSim Home)/deploy/machines.yml` 
- Since that, in Flee, some python libraries such as `numpy` will be used for the job execution, in case of nonexistent of those packages, we recommended to install a *_venv_* (virtual environment) on the target machine. It can be done by running

	> for QCG machine : `fab qcg install_app:QCG-PilotJob,venv=True`
	>
	> For SLURM machine : `fab eagle install_app:QCG-PilotJob,venv=True`
	> 
	> **NOTE** : the installation path (`virtual_env_path`) is set on `machines.yml` as one of parameters for the target remote machine
	> 
	> By installing this _venv_ on the target remote machine, the [QCG Pilot](https://github.com/vecma-project/QCG-PilotJob) Job service will be also installed alongside with other required dependencies 


# Running the coupled simulation on a supercomputer
```
fabsim eagle flee_conflict_forecast:mali,N=20,simulation_period=50
```
1. Run `fabsim eagle job_stat_update` to check if you jobs are finished or not
2. Run `fabsim eagle fetch_results` to copy back results from `eagle` machine. The results will then be in a directory inside `(FabSim Home)/results`, which is most likely called `mali_eagle_16`
3. Run `fabsim localhost plot_uq_output:mali_eagle_16,out` to generate plots


<!---
### Running an ensemble simulation on a supercomputer using Pilot Jobs
```
fabsim qcg flee_ensemble:mali,N=20,simulation_period=50,PJ=true
```
-->

# Running an ensemble simulation on a supercomputer using Pilot Jobs and QCG Broker

```
fabsim qcg flee_ensemble:mali,N=20,simulation_period=50,PJ=true
```
1. Run `fabsim qcg job_stat_update` to check if you jobs are finished or not
2. Run `fabsim qcg fetch_results` to copy back results from `qcg` machine. The results will then be in a directory inside `(FabSim Home)/results`, which is most likely called `mali_qcg_16`
3. Run `fabsim localhost plot_uq_output:mali_qcg_16,out` to generate plots


The advanced content in section 3, however, enables you to use several QCG tools as well.
