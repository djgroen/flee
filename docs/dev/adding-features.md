# Adding features

This page provides guidance for extending Flee with new functionality.

---

## Before you start

- Read [Code architecture](architecture.md) to understand where things live
- Check the [GitHub issues](https://github.com/djgroen/flee/issues) to see if the feature is already being worked on
- For large changes, open a GitHub issue first to discuss the design

---

## Common extension points

### New spawn mechanism

Spawning logic lives in `flee/spawning.py`. To add a new trigger for agent creation:

1. Add parameters to `simsetting.yml` and document them in `SimulationSettings.py`
2. Implement a function in `spawning.py` that returns a count of agents to spawn
3. Call your function from `flee.py:Ecosystem.evolve()` in the spawn step
4. Add a test in `tests/`

### New movement rule

Movement decisions live in `flee/moving.py`. To modify how agents decide where to go:

1. Add any new parameters to `simsetting.yml` and `SimulationSettings.py`
2. Modify the relevant weight or move chance calculation in `moving.py`
3. Write tests that verify the expected change in agent behaviour

### New location attribute

Locations are defined in `InputGeography.py`. To add a new CSV column that gets loaded:

1. Add the column to `locations.csv` (with a clear header name)
2. Read it in `InputGeography.py` and store it on the `Location` object
3. Use it in your spawning or movement logic
4. Update the documentation in [locations](../conflict/locations.md)

### New simulation setting

1. Add the parameter to `SimulationSettings.py` with a sensible default
2. Load it from `simsetting.yml` in the settings parser
3. Add documentation to the relevant settings page under [Running simulations](../running/index.md)

---

## Style guidelines

- Follow the patterns already in the codebase for consistency
- Keep new parameters backwards-compatible (provide defaults so old configs still work)
- Add docstrings to all public functions
- Write tests before or alongside your implementation

---

## Submitting your contribution

See [Contributing](./contributing.md) for the pull request workflow.
