# Writing and running tests

Flee uses [pytest](https://pytest.org) for testing. This page explains how to run the existing tests and how to add your own.

---

## Running all tests

From the root of the Flee repository:

```sh
pytest tests/
```

To run a specific test file:

```sh
pytest tests/test_flee.py
```

To run a single test by name:

```sh
pytest tests/test_flee.py::test_move_to_camp
```

---

## Running DFlee tests

DFlee-specific tests use test data in `test_data/test_data_dflee/`:

```sh
pytest tests/test_dflee.py
```

---

## Running parallel (MPI) tests

Tests for `pflee.py` are in `tests_mpi/`. These require `mpi4py` and an MPI installation:

```sh
mpirun -n 4 pytest tests_mpi/
```

---

## Test data

Test data is stored in `test_data/`. Each subdirectory contains a small set of input CSV files and a `simsetting.yml` for use in tests.

---

## Writing new tests

Tests follow the standard pytest pattern. Place new tests in `tests/` and name the file `test_<module>.py`.

Example test:

```python
import flee.flee as flee
import flee.SimulationSettings as SimulationSettings

def test_location_created():
    SimulationSettings.read_settings("flee/simsetting.yml")
    e = flee.Ecosystem()
    e.addLocation("TownA", location_type="town", pop=1000)
    assert len(e.locations) == 1
    assert e.locations[0].name == "TownA"
```

### Tips

- Keep tests small and focused on one behaviour
- Use the minimal input data needed — don't load large real scenarios in unit tests
- If you add a new simsetting.yml parameter, add a test that verifies it loads correctly
- For new spawning or movement mechanisms, add a test that checks agents are created/moved as expected

---

## Continuous integration

Flee uses GitHub Actions to run tests automatically on every pull request. The workflow is defined in `.github/workflows/`.

---

## See also

- [Getting started — testing](../getting-started/testing.md) — running tests as a new user
- [Code architecture](architecture.md) — where each module lives
