# Running simulations

This section covers how to run a Flee simulation and interpret its output.

## Pages in this section

- **[Running locally](local.md)** — command-line instructions for running a simulation on your laptop or workstation
- **[Settings — logging and spawning](settings-basic.md)** — configure what gets logged and how agents are created
- **[Settings — movement rules](settings-move.md)** — control how agents decide to move and which routes they take
- **[Settings — optimisation](settings-optimisation.md)** — speed up large simulations
- **[Settings — full reference](settings-reference.md)** — complete list of all `simsetting.yml` parameters
- **[Output files](output.md)** — description of every file produced by a simulation run

## The simsetting.yml file

All simulation behaviour is controlled by a configuration file called `simsetting.yml`. Every scenario has its own copy. The file is divided into four sections:

```yaml
log_levels:    # what to record during the run
spawn_rules:   # how and when agents are created
move_rules:    # how agents decide to move
optimisations: # performance tuning
```

See the individual pages above for details on each section.

## Parallel execution

Flee can be run in parallel across multiple CPU cores using MPI. This is called **pflee**. See [Running locally](local.md) for the parallel command syntax, and [FabFlee — HPC](../fabflee/hpc.md) for running on supercomputers.
