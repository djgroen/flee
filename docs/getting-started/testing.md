# Running tests

Once Flee is installed, it is a good idea to run the test suite to confirm everything is working correctly.

## Basic tests

From inside your `flee/` directory, run:

```sh
pytest tests/
```

This runs the full suite of functional tests. All tests should pass if the installation was successful.

!!! note
    If all tests are failing, double-check that you have installed all dependencies with `pip install -r requirements.txt` and that `PYTHONPATH` includes the flee directory (see [Installation](installation.md)).

## Single test run

To run a minimal single test quickly:

```sh
python3 tests/test_csv.py
```

## Tests with FabFlee

If you have FabFlee installed, you can also run the FabFlee integration tests.

First, create a symbolic link from inside your Flee directory:

```sh
ln -s <path to FabFlee> FabFlee
```

Then run:

```sh
pytest tests_mpi/
```

## Getting help

If tests are still failing after following the above steps, consider:

- Checking the [GitHub Issues](https://github.com/djgroen/flee/issues) page to see if your problem is a known issue
- Opening a new issue with the error output attached
