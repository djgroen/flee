# Running Flee on HPC

FabFlee can run Flee on a remote high-performance computing (HPC) cluster. This allows you to run long simulations or large ensembles that would be too slow on a laptop.

---

## Prerequisites

- FabFlee installed and working locally (see [Setup](setup.md))
- SSH access to the target HPC system
- Python and required libraries available on the HPC system (or a virtual environment)

---

## Step 1 — Configure the remote machine

Open `~/FabSim3/fabsim/deploy/machines.yml` and ensure your target machine is defined. For example:

```yaml
eagle_vecma:
  host: eagle.man.poznan.pl
  username: your_username
  home_path: /home/your_username
  virtual_env_path: /home/your_username/venv
  flee_location: /home/your_username/flee
  ...
```

Also ensure your personal credentials and settings are in `machines_user.yml`.

---

## Step 2 — Set up a virtual environment on HPC (if needed)

If the required Python libraries are not available on the HPC system, install them in a virtual environment:

For SLURM-based machines:

```sh
fabsim eagle install_app:QCG-PilotJob,venv=True
```

For QCG machines:

```sh
fabsim qcg install_app:QCG-PilotJob,venv=True
```

This installs QCG-PilotJob alongside other required Python dependencies.

---

## Step 3 — Run a simulation on HPC

Replace `localhost` with your machine name:

```sh
fabsim eagle_vecma pflee:mali2012,simulation_period=300
```

---

## Step 4 — Check job status

```sh
fabsim eagle_vecma job_stat_update
```

---

## Step 5 — Fetch results

```sh
fabsim eagle_vecma fetch_results
```

Results are copied to `~/FabSim3/results/` locally.

---

## Running an ensemble with Pilot Jobs

For large ensembles on HPC, use QCG-PilotJob to submit all runs under a single scheduler allocation:

```sh
fabsim qcg flee_ensemble:mali2012,N=20,simulation_period=50,PJ=true
```

Check and fetch as above.

---

## Running a coupled simulation on HPC

```sh
fabsim eagle_vecma flee_conflict_forecast:mali2012,N=20,simulation_period=50
```

Then fetch and plot:

```sh
fabsim eagle_vecma fetch_results
fabsim localhost plot_uq_output:mali2012_eagle_16,out
```

---

## Troubleshooting

**SSH connection refused**: Ensure passwordless SSH keys are set up for the target machine.

**Missing Python packages**: Use the `install_app` command to set up a virtual environment on the remote machine.

**Job submission fails**: Check that `machines.yml` is configured with the correct scheduler settings for your HPC system.

---

!!! note "replicas vs N"
    The `replicas` parameter indicates the number of replicated Flee instances run to account for non-determinism in the simulation. The `N` parameter indicates the number of replicated Flare instances. In most scenarios, Flare will exhibit a much higher degree of aleatoric uncertainty than Flee, so `N` is typically larger than `replicas`.

---

## See also

- [FabSim3 remote machine configuration](https://fabsim3.readthedocs.io/en/latest/remote_machine_configuration.html)
- [Running locally with FabFlee](running-local.md) — all FabFlee run commands
