# Column-name and notation changelog

This file records every column rename adopted across `results/` from
**Day 7b** onward. The motivation is to remove a single ambiguity that ran
through the previous days' artifacts and prose:

> The string "S1" had two completely unrelated meanings in the same
> tables and figures: the **System 1** cognitive mode of the dual-process
> model (Kahneman 2011) **and** the **first-order Sobol sensitivity
> index** (SALib convention).

Both abbreviations occurred in the same documents, sometimes in the same
sentence. Day 7b adopts the conventions below and keeps them stable from
this point forward. Pre-Day-7b CSVs are **not rewritten** — they remain
on disk as historical artifacts with their original column names. Code
that consumes them does so via a thin compatibility wrapper.

## Notation rules

### Sobol sensitivity indices

| Concept                              | New token       | Where used               |
|--------------------------------------|-----------------|--------------------------|
| First-order index                    | `S_first`       | code, CSV columns, axis  |
| Total-order index                    | `ST`            | unchanged (no collision) |
| Second-order index (not yet computed) | `S_second`      | reserved                 |
| Bootstrap CI half-width              | `*_conf`        | unchanged                |
| Bootstrap CI low / high              | `*_CI_low/high` | new in Day 7b            |

In code, the SALib output dict is remapped immediately after `analyze()`:

```python
raw = sobol.analyze(problem, Y, calc_second_order=False, num_resamples=1000)
indices = {
    'S_first':      raw['S1'],      # remap
    'S_first_conf': raw['S1_conf'], # remap
    'ST':           raw['ST'],
    'ST_conf':      raw['ST_conf'],
}
```

`raw['S1']` is the **only** place in the codebase where the bare SALib key
is touched outside the remap. The audit script (`scripts/notation_audit.sh`)
enforces this.

### Cognitive systems

| Concept                          | New token (code/CSV)        | Mathematical notation       |
|----------------------------------|-----------------------------|-----------------------------|
| System 1 (intuitive)             | `sys1`                      | "System 1" in prose         |
| System 2 (deliberative)          | `sys2`                      | "System 2" in prose         |
| Decision-mode string (S1 only)   | `sys1_only`                 | (was `s1_only`)             |
| Decision-mode string (S2 only)   | `sys2_only`                 | (was `s2_only`)             |
| Per-agent System-2 weight        | `sys2_weight`               | `P_S2` (subscript retained) |
| Per-agent System-2 activation    | `sys2_activation_prob`      | `P_S2`                      |

The mathematical symbol `P_S2` is **kept** -- the subscript "S2" reads
unambiguously as "System 2" in equation context, where Sobol indices do
not appear. The methods section of the Day 7b paper draft will state
this explicitly.

## Affected files

### Code (renamed in place; back-compat aliases retained)

| Path                                                              | Change                                            |
|-------------------------------------------------------------------|---------------------------------------------------|
| `flee/s1s2_model.py`                                              | Replaced with shim re-exporting the new module    |
| `flee/dual_process_model.py`                                      | New canonical module name                         |
| `flee/decision_engine.py`                                         | Class `S1OnlyEngine` -> `Sys1OnlyEngine` (alias kept); mode string `s1_only` -> `sys1_only` (legacy alias accepted) |
| `flee/moving.py`                                                  | Local var/param `s2_weight` -> `sys2_weight`; attribute `s2_activation_prob` -> `sys2_activation_prob`; settings key `s2_weight_override` -> `sys2_weight_override` (legacy fallback) |
| `flee/flee.py`                                                    | `Person.s2_activation_prob` slot -> `sys2_activation_prob` |
| `flee/SimulationSettings.py`                                      | Mode string normalisation; `sys2_weight_override` canonical key |
| `flee/conflict_potential.py`                                      | Comments updated                                  |
| `tests/test_s1s2_v3.py`                                           | Imports + variable names; one fixture filename retained for back-compat |
| `tests/test_s1s2_integration.py`                                  | Same                                              |
| `scripts/run_fukushima_day3.py`                                   | Mode strings, columns, attribute names            |
| `scripts/run_day5_scenarios.py`                                   | Same                                              |
| `scripts/run_day6_kappa_sweep.py`                                 | Column name `sys2_weight`                         |
| `scripts/run_day6_regime_contrast.py`                             | Mode strings, columns                             |
| `scripts/run_day6_analysis.py`                                    | Mode string `sys1_only`                           |
| `scripts/run_day6_movechance_sweep.py`                            | Mode string `sys1_only` (no legacy reads)         |
| `scripts/run_sobol_day7b.py`                                      | Born clean: uses `S_first` / `ST` exclusively     |
| `scripts/run_cmc_separability_7b.py`                              | Same                                              |

### Archived (audit-exempt)

| Path                                          | Reason                                         |
|-----------------------------------------------|------------------------------------------------|
| `scripts/_archived_docx_builders/build_day*.py` | One-shot Word-doc generators for Day 4b/5/6/7. Their output is already on disk under `output/`. Kept verbatim as an audit trail of pre-rename artifacts. |
| `scripts/_archived_legacy_sobol/run_sobol_day4.py`   | Day 4 Sobol, used the broken perception field. |
| `scripts/_archived_legacy_sobol/run_sobol_day7.py`   | Day 7 Sobol, used `n_samples=32`. Replaced by `run_sobol_day7b.py`. |

### Pre-Day-7b CSV outputs (not rewritten)

`results/day3/`, `results/day4/`, `results/day4b/`, `results/day5/`,
`results/day6/`, `results/day7/` retain the original column names
(`s2_weight`, `s2_weight_active`, mode string `s1_only`, etc.). When
Day 7b figures need to read these files, the loader normalises the
column names in-memory.

### Day 7b CSV outputs (clean)

| Path                                              | Header convention            |
|---------------------------------------------------|------------------------------|
| `results/day7b/sobol_indices_full.csv`            | `S_first`, `S_first_CI_low/high`, `ST`, `ST_CI_low/high`, `CI_width`, `Insensitive_flag` |
| `results/day7b/interaction_magnitudes.csv`        | `S_first`, `ST`, `interaction`, `interaction_pct` |
| `results/day7b/cmc_separability_full.csv`         | `ST_cmc025/050/075`, `Max_drift`, `Separable`, `Day7_verdict`, `Changed` |
| `results/day7b/day4_day7_day7b_comparison.csv`    | `ST_day4`, `ST_day7`, `ST_day7b`, `Delta_4_to_7b`, `Interpretation` |
| `results/day7b/day7_reliability_flags.csv`        | Per-cell flag list (Day 7 diagnostic only) |
| `results/day7b/raw_results.csv`                   | One row per Sobol evaluation, all six QoIs in `sys1_only` and `blend` modes |
| `results/day7b/raw_results_cmc_separability.csv`  | Same, with the fixed-CMC level appended |

### CSV mode-string compatibility table

| Pre-Day-7b value | Post-Day-7b canonical | Loader behaviour              |
|------------------|------------------------|-------------------------------|
| `original`       | `original`             | unchanged                     |
| `s1_only`        | `sys1_only`            | normalised on read            |
| `switch`         | `switch`               | unchanged                     |
| `blend`          | `blend`                | unchanged                     |
| `s2_only`        | `sys2_only`            | normalised on read (rare)     |

## Audit gate

`scripts/notation_audit.sh` exits non-zero if any of the following
appear outside the archive directories:

- bare `S1` token (cognitive context)
- `s1_only` / `s2_weight` / `s2_activation` tokens
- `raw['S1']` (SALib first-order key) outside an explicit remap line

Lines that legitimately need to mention `S1` in a sobol context (e.g.
documentation comments) include the word `sobol` so they are filtered
by the inner `grep -v`.
