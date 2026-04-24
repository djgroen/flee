Sensitivity analysis of parameters using EasyVVUQ
=========

This tutorial uses VECMAtk components (https://www.vecma-toolkit.eu/) to perform parameter exploration using sensitivity analysis. The aim is to sample simulation input parameters and understand how identified assumptions in migration prediction are pivotal to the validation results. The additional components of this tutorial are:

- EasyVVUQ (https://easyvvuq.readthedocs.io/en/latest/installation.html): a Python3 library aiming to facilitate verification, validation and uncertainty quantification
- QCG-PilotJob (https://github.com/vecma-project/QCG-PilotJob): a Pilot Job system allowing execution of many subordinate jobs in a single scheduling system 

There is also a Python API for HPC execution of EasyVVUQ, which is a combination of EasyVVUQ and QCG-PilotJob. For more information, see https://easyvvuq-qcgpj.readthedocs.io/en/plugin/index.html

## Parameter Exploration

To perform sensitivity analysis on input parameters, there are two sampler examples, namely (a) SCSampler (Stochastic Collocation sampler) and (b) PCESampler (Polynomial Chaos Expansion sampler). Both approach are implemented in [flee_SA.py](https://github.com/djgroen/FabFlee/blob/master/flee_SA.py "flee_SA.py") script.
- `flee_init_SA` allows to run SA for parameter exploration.
 - `flee_analyse_SA` provides analysis of obtained results.

There are six main input parameters in multiscale migration prediction, such as _max_move_speed_, _conflict_move_chance_, _camp_move_chance_, _default_move_chance_, _camp_weight_ and _conflict_weight_, to analyse using Sobol's method and stochastic collocation.

In both of the sensitivity analysis scripts, we have all input parameters in ``(FabSim3 Home)/plugins/FabFlee/templates/params.json`` as follows:
```yml
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
``` 
The configuration for SA can be found in ``(FabSim3 Home)/plugins/FabFlee/SA/flee_SA_config.yml`` as follows:
 * _NOTE_ : here we only presented the most important config parameters to run a SA. The full list can be found in [flee_SA_config.yml](https://github.com/djgroen/FabFlee/blob/master/SA/flee_SA_config.yml "flee_SA_config.yml").
```yml
vary_parameters_range:
    # <parameter_name:>
    #   range: [<lower value>,<upper value>] 
    max_move_speed:
        range: [100, 500]
    max_walk_speed:
        range: [10, 100]
    camp_move_chance:
        range: [0.0, 0.1]
    conflict_move_chance:
        range: [0.1, 1.0]
    default_move_chance:
        range: [0.1, 1.0]
    camp_weight:
        range: [1.0, 10.0]
    conflict_weight:
        range: [0.1, 1.0]

selected_vary_parameters: ["max_move_speed",
                          "max_walk_speed"
                          ]

# available distribution type: [Uniform, DiscreteUniform]
distribution_type: "Uniform"

polynomial_order: 2

# available sampler: [SCSampler,PCESampler]
sampler_name: "SCSampler"
...
...
...
```
To vary input parameters and their corresponding distributions using stochastic collocation or polynomial chaos expansion samplers for sensitivity analysis, simply modify the `selected_vary_parameters` parameter in `flee_SA_config.yml` file:
```yml 
selected_vary_parameters: ["max_move_speed",
                          "max_walk_speed"
                          ]
```
To change the number of polynomial order, modify the  `polynomial_order` parameter in `flee_SA_config.yml` file

```yml 
polynomial_order: 2
```
And, by changing `sampler_name` parameter, you can select one of available `SCSampler` or `PCESampler`sampler for a SA run.
```yml 
# available sampler: [SCSampler,PCESampler]
sampler_name: "SCSampler"
```

## Run EasyVVUQ analysis 

### Execution on a localhost

1. To execute sensitivy analysis on a localhost, simply run:

```
fabsim localhost flee_init_SA:<conflict_name>,simulation_period=<number>
```
* _NOTE_ : the required parameters for sensitivy analysis, such as _sampler name_ , _vary input parameters_, and _the number of polynomial order_, will be loaded from `flee_SA_config.yml` file.

2. After the job has finished, the terminal becomes available again, and a message is printing indicating where the output data resides. Run the following command to copy back results from the remote machine and perform analysis. The results will then be in a directory inside `(FabSim Home)/results` and the obtained results can be analysed using 

```
fabsim localhost flee_analyse_SA:<conflict_name>
```    


### Execution on a remote machine

1. To execute sensitivy analysis on a remote machine, simply run:
```
fabsim <remote_machine_name> flee_init_SA:<conflict_name>,simulation_period=<number>
```


2. Run the following command to copy back results from the remote machine and perform analysis. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16).
```
fabsim <remote_machine_name> flee_analyse_SA:<conflict_name>
```
* _Note_: Analysis of the obtained results can be also performed on a localhost.


## Execution on a remote machine using QCG-Pilot Job

For QCG-PilotJob installation, see https://github.com/vecma-project/QCG-PilotJob/blob/master/INSTALL.txt 

.. note:: if QCG-PJ is installed in the target remote machine, by using PJ=True, the native QCG-PilotJob will be lunched for execution. Otherwise you require to install the QCG-PilotJob service in a virtual environment (venv) in the target machine, and then PJ=True option will load QCG-PilotJob services from venv. 

To install virtual environment on the remote machine alongside with QCG-PilotJob, just run: 

```
fabsim <remote machine name> install_app:QCG-PilotJob,venv=True
```

To execute easyvvuq for migration prediction using Pilot Job, run

```
fabsim <remote machine name> flee_init_SA:<conflict_name>,simulation_period=<number>,PJ=True
```
 

2. Run the following command to copy back results from the remote machine and perform analysis. The results will then be in a directory inside ``(FabSim Home)/results``, which is most likely called <conflict_name>_<remote_machine_name>_<number> (e.g. mali_eagle_vecma_16).

```
fabsim <remote_machine_name> flee_analyse_SA:<conflict_name>
```  
* _Note_: Analysis of the obtained results can be also performed on a localhost.


## The execution of sensitivity analysis using a conflict scenario

The following commands demonstrate the execution of Mali conflict for sensitivity analysis: 
```
fabsim localhost/vecma_eagle flee_init_SA:mali,simulation_period=100
fabsim localhost/vecma_eagle flee_analyse_SA:mali
```
