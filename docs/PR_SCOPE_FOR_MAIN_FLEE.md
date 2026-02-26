# PR scope for main FLEE (djgroen/flee)

When opening a pull request from your fork to **origin** (djgroen/flee), include only the following so the PR stays minimal and reviewable.

## Include (core S1/S2 feature)

| Path | Purpose |
|------|---------|
| `flee/moving.py` | S1/S2 branch in `calculateMoveChance`, use of `s1s2_model_params`, S2 route selection |
| `flee/flee.py` | Person attributes `s2_activation_prob`, `cognitive_state`; wiring for `log_decision` / `system2_active` |
| `flee/s1s2_model.py` | `compute_capacity`, `compute_opportunity`, `compute_deliberation_probability` |
| `flee/SimulationSettings.py` | Reading `two_system_decision_making` and `s1s2_model` (alpha, beta, eta, theta, p_s2) from YML |
| `flee/simsetting.yml` | Optional: example schema for `move_rules.two_system_decision_making` and `move_rules.s1s2_model` |

## Exclude (keep in fork or separate repos)

- `configs/`, `topologies/`, `parameter_sweep.py`, `run_nuclear_parameter_sweep.py`, `run_pr_checklist.py`
- All experiment/visualization scripts, AGU/colleague docs, and large data under `data/`, `results/`, etc.
- `flee/s1s2_refactored.py` unless maintainers ask for it (one implementation in `s1s2_model.py` is enough)

## Suggested PR workflow

1. Sync with upstream: `git fetch origin && git merge origin/master` (or `origin/main`).
2. Create a branch for the PR, e.g. `feature/s1s2-dual-process` (or reuse `feature/dual-process-experiments` and ensure only the “Include” files are in the commits you push).
3. Push that branch to **myfork** (not origin): `git push myfork feature/s1s2-dual-process`.
4. Open a pull request **from** your fork **to** djgroen/flee (origin).
5. In the PR description: short summary of S1/S2 (P_S2 = Ψ×Ω, threshold 0.5), link to config schema (e.g. [docs/PR_CHECKLIST_S1S2.md](PR_CHECKLIST_S1S2.md)), and note that FabFlee can add these parameters to SA later.

## Checklist before opening

- [ ] `python run_pr_checklist.py` passes (default-off and default-on runs).
- [ ] Only “Include” files are in the PR diff (no configs/topologies/sweep scripts).
