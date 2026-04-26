# Column Name Changelog — Day 7b Notation Unification

Applied in Day 7b to eliminate the collision between `S1` (sobol first-order
index) and `S1` (System 1 cognition). All Day 7b output files use the new
names. Day 1–7 output files retain their original column names and are not
retroactively modified — see *Files NOT retroactively modified* below.

## Sobol index columns (all sobol results CSVs)

| Old name      | New name        | Reason                                     |
|---------------|-----------------|--------------------------------------------|
| `S1`          | `S_first`       | "S1" collides with System 1 cognition      |
| `S1_conf`     | `S_first_conf`  | Same                                       |
| `S1_CI_low`   | `S_first_CI_low`  | Same                                     |
| `S1_CI_high`  | `S_first_CI_high` | Same                                     |
| `ST`, `ST_conf`, `ST_CI_low`, `ST_CI_high` | unchanged | No collision (no "T1/T2" cognitive system in FLEE) |

The `SALib.analyze.sobol` library still emits raw keys `S1`, `S1_conf`, `ST`,
`ST_conf`. Day 7b analysis scripts therefore remap immediately after every
`analyze()` call and never use the raw `'S1'` key downstream. The shared
helper is `scripts/run_sobol_day7b.py::_analyze_one`.

## Decision-mode columns and identifiers (agent output CSVs and configs)

| Old name              | New name                | Reason                                         |
|-----------------------|-------------------------|------------------------------------------------|
| `s1_only` (mode str)  | `sys1_only`             | "S1" collides with sobol first-order index     |
| `s2_only` (mode str)  | `sys2_only`             | Same                                           |
| `s2_weight`           | `sys2_weight`           | "S2" collides with sobol notation              |
| `s2_activation_prob`  | `sys2_activation_prob`  | Same                                           |
| `s2_weight_override` (yaml key) | `sys2_weight_override` | Same                                  |
| `S1OnlyEngine` (class)| `Sys1OnlyEngine`        | Same                                           |

Compatibility:
- `flee/decision_engine.py` keeps a legacy alias `S1OnlyEngine = Sys1OnlyEngine`
  and an `_MODE_ALIASES` dict that accepts the old mode strings on input.
- `flee/SimulationSettings.py` and `flee/moving.py` accept the old
  `s2_weight_override` yaml key with a deprecation-style fallback.
- `flee/s1s2_model.py` is now a re-export shim; the canonical module is
  `flee/dual_process_model.py`.

## Affected Day 7b output files (new names from this day onward)

- `results/day7b/sobol_indices_full.csv` — uses `S_first`, `S_first_conf`,
  `S_first_CI_low`, `S_first_CI_high`, `ST`, `ST_conf`, `ST_CI_low`,
  `ST_CI_high`, `CI_width`, `Insensitive_flag`.
- `results/day7b/interaction_magnitudes.csv` — uses `S_first` and `ST`.
- `results/day7b/cmc_separability_full.csv` — uses `ST_cmc025`,
  `ST_cmc025_CI`, `ST_cmc050`, `ST_cmc050_CI`, `ST_cmc075`, `ST_cmc075_CI`,
  `Max_drift`, `Separable`, `Day7_verdict`, `Changed`.
- `results/day7b/sobol_indices_cmc_025.csv` (and 050, 075) — uses `S_first`
  and `ST` family.
- `results/day7b/day4_day7_day7b_comparison.csv` — uses `S_first` and `ST`.
- `results/day7b/raw_results.csv` and `raw_results_cmc_separability.csv` —
  agent run outputs use `sys1_only` / `blend` mode labels.
- All figures D7b-1 .. D7b-5 — axis labels use *"First-order index
  (S_first)"* and *"Total-order index (ST)"*.

## Files NOT retroactively modified

- `results/day1/` through `results/day7/` — retained as-is for reproducibility.
  Any script that reads a Day 1–7 CSV must account for the **old** column
  names (`S1`, `S1_conf`, `s1_only`, `s2_weight`, etc.).
- Pre-Day-7b scripts archived under `scripts/_archived_legacy_sobol/` and
  `scripts/_archived_docx_builders/` — kept for the historical record only.

## Paper notation convention (established Day 7b)

- **Sobol first-order index:** `S_first` in code/tables; *"first-order index"*
  in prose. Never `S1`.
- **Sobol total-order index:** `ST` in code/tables/prose (no collision).
- **System 1 / System 2 cognition (Kahneman 2011):** *"System 1"* / *"System
  2"* in prose; `Sys1` / `Sys2` in identifiers. Never bare `S1` / `S2`.
- **Mathematical notation:** the `P_S2` notation (probability of activating
  System 2 reasoning) and `compute_s2_move_probability` function name are
  retained inside `flee/dual_process_model.py` because they are part of the
  published equations of the dual-process model. The module docstring
  explicitly disambiguates them from sobol indices.
- **Paper methods section:** the first use of `S_first` should carry a
  footnote: *"`S_first` denotes the sobol first-order index. We avoid `S1`
  because Kahneman's (2011) System 1 is also a central object of this paper."*

## Audit

The shell script `scripts/notation_audit.sh` enforces the convention by
grepping `flee/`, `scripts/`, `tests/` for forbidden tokens
(`\bs1_only\b`, `\bs2_only\b`, `\bs2_weight\b`, `\bs2_activation_prob\b`,
and raw `\['S1'\]` access) outside of explicitly exempted regions. It
must exit 0 in CI.
