# QCG Pilot Job

[QCG-PilotJob](https://github.com/vecma-project/QCG-PilotJob) is a pilot job system that allows many subordinate jobs to be submitted under a single HPC scheduler allocation. FabFlee supports QCG-PilotJob for running large ensembles efficiently on HPC systems.

---

## Installation

On the target HPC machine:

```sh
fabsim qcg install_app:QCG-PilotJob,venv=True
```

This installs QCG-PilotJob and its dependencies in a virtual environment on the remote machine.

---

## Running an ensemble with QCG Pilot Job

```sh
fabsim qcg flee_ensemble:<scenario_name>,N=20,simulation_period=50,PJ=true
```

### Check job status

```sh
fabsim qcg job_stat_update
```

### Fetch results

```sh
fabsim qcg fetch_results
```

Results appear in `~/FabSim3/results/<scenario>_qcg_<id>/`.

---

## Running EasyVVUQ with QCG Pilot Job

For sensitivity analysis using QCG-PilotJob on HPC:

```sh
fabsim qcg flee_init_SC:<scenario_name>
fabsim qcg job_stat_update
fabsim qcg fetch_results
fabsim localhost flee_analyse_SC:<scenario_name>
```

---

## Further reading

- [QCG-PilotJob documentation](https://qcg-pilotjob.readthedocs.io/)
- [EasyVVUQ + QCG-PilotJob](https://easyvvuq-qcgpj.readthedocs.io/)
- [HPC / supercomputer](hpc.md) — general HPC setup
- [Sensitivity analysis](sensitivity.md) — EasyVVUQ workflow
