# Multi-objective optimisation

FabFlee includes multi-objective optimisation (MOO) functionality for camp location problems, using the [pymoo](https://pymoo.org/) framework (version 0.6.0+).

MOO can find optimal camp placements by simultaneously minimising/maximising multiple objectives — for example, minimising travel distance while maximising successful arrivals.

---

## Installation

```sh
pip install pymoo
```

Additional dependencies: `pandas`, `numpy`, `Cython`, `PyYAML`, `mpi4py`, `pyproj`, `shapely`, `Rtree`, `matplotlib`, `beartype`.

---

## Algorithms

Five MOO algorithms are implemented in FabFlee, all based on pymoo:

- **NSGA-II**
- **SPEA2**
- **NSGA-III**
- **MOEA/D**
- **BCE-MOEA/D** (custom implementation close to the original paper)

---

## Test problems

Ten test problems are provided in `~/FabSim3/plugins/FabFlee/config_files/`:

| Index | Problem | Objectives |
|-------|---------|------------|
| 1 | `moo_f1_c1_t3` | 3 |
| 2 | `moo_f1_c3_t4` | 3 |
| 3–6 | `moo_ssudan_H0/H10/R0/R10_3obj` | 3 |
| 7–10 | `moo_ssudan_H0/H10/R0/R10_5obj` | 5 |

### Three-objective problems

1. Minimise individual travel distance
2. Maximise number of successful camp arrivals
3. Minimise idle capacity in the new camp

### Five-objective problems

Objectives 1–3 as above, plus:

4. Minimise food insecurity level of a possible site
5. Maximise site accessibility

---

## Configuration

Edit `~/FabSim3/plugins/FabFlee/MOO_setting.yaml` to choose the algorithm and parameters:

```yaml
alg_name: "NSGA2"
pop_size: 4
n_gen: 2
```

For problems 3–10, the number of agents is scaled down using `hasten: 100` in `simsetting.yml` to improve runtime.

---

## Running MOO

```sh
fabsim localhost flee_MOO:<problem_name>,simulation_period=<days>
```

For HPC execution, configure `machines_FabFlee_user.yml` in `~/FabSim3/plugins/FabFlee/` with:

```yaml
localhost:
  flee_location: "<PATH_TO_FLEE>"
```

---

## See also

- [Sensitivity analysis](sensitivity.md) — parameter sensitivity with EasyVVUQ
- [HPC / supercomputer](hpc.md) — running on remote machines
