# Audit Inventory — Test Suite and Related Scripts

**Date:** 2025-03-14  
**Scope:** tests/, run_*.py, analysis_*.py, run_comparison_ring.py

---

## tests/ directory

| File | Type | Description | Verdict |
|------|------|-------------|---------|
| `tests/test_s1s2_v3.py` | pytest | 31 unit tests for s1s2_model.py (Ψ, Ω, P_S2, σ, blend). Includes test_novice_in_calm (P_S2=Ψ_min at c=0), test_no_system2_active_boolean_in_codebase. | **UPDATE** |
| `tests/test_s1s2_integration.py` | pytest | 11 integration tests: calculateMoveChance return signature, _s2_route_context, boundary conditions, three-phase pattern (full_mixture CSV). | **UPDATE** |
| `tests/test_twosystem.py` | pytest | Two tests: test_system2_quick, test_system1_quick. Only checks conflict > 0.6; does not use actual model. Minimal value. | **ARCHIVE** |
| `tests/test_changes.py` | pytest | test_dynamic_social_connectivity, test_system2_activation, test_route_selection_differences — stubs with no implementation (pass by default). Tests removed/legacy S1/S2 API. | **DELETE** |
| `tests/diagnose_segfault.py` | utility | Import-chain diagnostic for segfault debugging. Not a test. | **ARCHIVE** |
| `tests/test_1_agent.py` | pytest | Basic 1-agent simulation. | **KEEP** |
| `tests/test_awareness.py` | pytest | Awareness level and marker location. | **KEEP** |
| `tests/test_camp_sink.py` | pytest | Camp sink behavior. | **KEEP** |
| `tests/test_changes.py` | pytest | See above. | **DELETE** |
| `tests/test_close_location.py` | pytest | Location closure. | **KEEP** |
| `tests/test_conflict_driven_spawning.py` | pytest | Conflict-driven spawning. | **KEEP** |
| `tests/test_crawling.py` | pytest | Location crawling. | **KEEP** |
| `tests/test_csv.py` | pytest | CSV output and location changes. | **KEEP** |
| `tests/test_datatable.py` | pytest | DataTable. | **KEEP** |
| `tests/test_demographics.py` | pytest | Demographics loading. | **KEEP** |
| `tests/test_dflee.py` | pytest | DFlee flood tests. | **KEEP** |
| `tests/test_flood_driven_spawning.py` | pytest | Flood-driven spawning. | **KEEP** |
| `tests/test_idp.py` | pytest | IDP tests. | **KEEP** |
| `tests/test_load_agent.py` | pytest | Agent loading. | **KEEP** |
| `tests/test_micro_model.py` | pytest | Micro model. | **KEEP** |
| `tests/test_moving.py` | pytest | Moving, scoring, prune routes. | **KEEP** |
| `tests/test_path_choice.py` | pytest | Path choice. | **KEEP** |
| `tests/test_removelink.py` | pytest | Link removal. | **KEEP** |
| `tests/test_spawning.py` | pytest | Spawning get_attribute_ratio. | **KEEP** |
| `tests/test_tiny_closure.py` | pytest | Tiny closure. | **KEEP** |
| `tests/test_toy_escape.py` | pytest | Toy escape scenario. | **KEEP** |
| `tests/empty.yml` | config | Empty YAML for test setup. | **KEEP** |
| `tests/__init__.py` | package | Package init. | **KEEP** |

---

## Standalone scripts (root)

| File | Type | Description | Verdict |
|------|------|-------------|---------|
| `run_comparison_ring.py` | simulation | Four-condition ring comparison (original_flee, s1_only, s2_only, full_mixture). Outputs to results/comparison_ring/. | **UPDATE** |
| `run_model_comparison.py` | simulation | Four variants across topologies (ring, linear, star). Uses alpha/beta hacks for s1_only/s2_only. Outputs to data/model_comparison/. | **KEEP** |
| `run_omega_diagnostic.py` | diagnostic | Omega diagnostic for S2. | **KEEP** |
| `run_easyvvuq_single.py` | simulation | EasyVVUQ single run. | **KEEP** |
| `run_easyvvuq_campaign.py` | simulation | EasyVVUQ campaign. | **KEEP** |
| `run_fork_experiments.py` | simulation | Fork experiments with S1/S2. | **KEEP** |
| `run_nuclear_parameter_sweep.py` | simulation | Nuclear parameter sweep. | **KEEP** |
| `run_pr_checklist.py` | utility | PR checklist runner. | **KEEP** |
| `analyze_fork_experiments.py` | analysis | Analyze fork experiment results. | **KEEP** |
| `create_model_diagnostic_plots.py` | analysis | Plots from run_model_comparison output. | **KEEP** |
| `create_experiment_comparison_figures.py` | analysis | Experiment comparison figures. | **KEEP** |

---

## Summary

- **DELETE:** 1 file — `tests/test_changes.py` (stub tests for removed system2_activation)
- **ARCHIVE:** 2 files — `tests/test_twosystem.py`, `tests/diagnose_segfault.py`
- **UPDATE:** 3 files — `tests/test_s1s2_v3.py`, `tests/test_s1s2_integration.py`, `run_comparison_ring.py`
- **KEEP:** All other listed files

---

*Inventory complete. Proceeding to Step 2 after implicit approval.*
