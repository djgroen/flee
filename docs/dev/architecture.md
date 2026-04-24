# Code architecture

This page describes the structure of the Flee codebase to help new developers navigate it.

---

## Repository layout

```
flee/
├── flee/                      # Core Python package
│   ├── flee.py                # Serial simulation engine
│   ├── pflee.py               # Parallel simulation engine (MPI)
│   ├── moving.py              # Agent movement logic
│   ├── spawning.py            # Agent spawning logic
│   ├── SimulationSettings.py  # Settings loader (simsetting.yml)
│   ├── InputGeography.py      # Reads location/route/closure CSV files
│   ├── demographics.py        # Agent demographic attributes
│   ├── scoring.py             # Validation scoring
│   ├── crawling.py            # Path-finding / awareness level logic
│   ├── coupling.py            # Multiscale coupling logic
│   ├── lib_math.py            # Mathematical utilities
│   ├── datamanager/           # Data loading and management
│   ├── postprocessing/        # Output processing scripts
│   ├── preprocessing/         # Input data preprocessing scripts
│   └── runscripts/            # Entry-point run scripts
├── tests/                     # Unit and integration tests
├── tests_mpi/                 # Parallel (MPI) tests
├── conflict_input/            # Example conflict input datasets
├── conflict_validation/       # Example validation datasets
├── docs/                      # Documentation source (this site)
└── ...
```

---

## Key modules

### Flee.py / pflee.py

The main simulation engines. `flee.py` runs a single-threaded simulation; `pflee.py` uses MPI for parallel execution.

Both expose the same interface: you create a `Ecosystem` object, populate it with locations and agents, then call `flee.evolve()` each timestep.

### moving.py

Contains the logic for agent movement decisions:
- Choosing a destination based on location weights and awareness level
- Applying move chance
- Enforcing camp capacity via `getCapMultiplier()`
- Applying flood move chances (DFlee)

### spawning.py

Controls how agents are created (spawned) during the simulation:
- Conflict-driven spawning from conflict intensity
- Flood-driven spawning from flood levels (DFlee)
- Starvation-driven spawning from IPC data

### SimulationSettings.py

Loads `simsetting.yml` and provides global settings access throughout the simulation via `SimulationSettings.spawn_rules` and `SimulationSettings.move_rules`.

### InputGeography.py

Reads `locations.csv`, `routes.csv`, and `closures.csv` and constructs the location graph.

### scoring.py

Computes validation metrics comparing simulation output to UNHCR data.

---

## Simulation loop

At a high level, each timestep:

1. **Spawn** — create new agents at conflict/flood locations based on spawn rules
2. **Move** — each agent decides whether to move and, if so, where
3. **Record** — agent and location counts are logged to output files

This loop is in `flee.py:Ecosystem.evolve()`.

---

## Adding a new spawn mechanism

1. Add configuration parameters to `SimulationSettings.py`
2. Implement the spawning logic in `spawning.py`
3. Call it from `flee.py:Ecosystem.evolve()`
4. Add tests in `tests/`

---

## See also

- [Adding features](adding-features.md) — patterns to follow when extending Flee
- [Writing and running tests](testing.md) — how to test your changes
