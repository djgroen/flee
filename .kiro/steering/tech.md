# Technology Stack

## Core Technologies

- **Language**: Python 3.8+
- **Parallel Computing**: MPI (Message Passing Interface) via mpi4py
- **Scientific Computing**: NumPy, pandas, matplotlib, seaborn
- **Network Analysis**: NetworkX for graph-based location modeling
- **Multiscale Coupling**: MUSCLE3 for macro-micro model integration
- **Configuration**: YAML for simulation settings
- **Type Checking**: beartype (optional, controlled by FLEE_TYPE_CHECK env var)

## Build System & Package Management

- **Setup**: setuptools with setup.py
- **Version Management**: versioneer for automatic versioning from git tags
- **Dependencies**: requirements.txt for core dependencies
- **Testing**: pytest framework
- **Documentation**: MkDocs with Material theme

## Code Quality Tools

All linting configurations are in `.linter_cfg/`:
- **Code Formatting**: black
- **Import Sorting**: isort
- **Style Checking**: flake8
- **Static Analysis**: pylint
- **Testing**: pytest with custom configuration

## Common Commands

### Development
```bash
# Install package in development mode
python setup.py install

# Run all linting checks
make lint

# Run individual linters
make lint/black
make lint/flake8
make lint/isort
make lint/pylint

# Run tests
make test
python3 -m pytest

# Clean build artifacts
make clean
```

### Parallel Testing
```bash
# Basic parallel performance test
mpirun -np <cores> python3 tests/test_par.py

# Benchmark configurations
mpirun -np <cores> python3 test_par.py -N 500000 -p advanced -d 10000 -t 10
mpirun -np <cores> python3 test_par.py -N 500000 -p classic -d 10000 -t 10
```

### Documentation
```bash
# Serve documentation locally
make servedocs
mkdocs serve
```

## Environment Variables

- `FLEE_TYPE_CHECK`: Set to "true" to enable beartype runtime type checking
- Standard MPI environment variables for parallel execution