# η (eta) and θ (theta) Audit Report

## Task 1 — Codebase Audit Summary

| Location | Variable | Feeds P_S2/Ψ/Ω? | Affects movement? | Read but unused? |
|----------|----------|-----------------|-------------------|------------------|
| `flee/SimulationSettings.py` | `move_rules["eta"]` | No | No | **Yes** (removed) |
| `flee/SimulationSettings.py` | `s1s2_model_params["eta"]` | No | No | **Yes** (removed) |
| `flee/SimulationSettings.py` | `s1s2_model_params["theta"]` | No | No | **Yes** (removed) |
| `flee/simsetting.yml` | `eta` | No | No | **Yes** (removed) |
| `flee/s1s2_model.py` | — | — | — | **Never used** (core model uses only α, β, p_s2) |
| `flee/moving.py` | — | — | — | **Never used** (uses only alpha, beta, p_s2 from s1s2_params) |
| `flee/s1s2_refactored.py` | `eta`, `theta` (threshold) | Yes (alternative path) | No (path not invoked for movement) | Used in legacy module only |

**Core model path:** `moving.py` → `compute_deliberation_probability(experience_index, conflict, alpha, beta)` → P_S2 = Ψ × Ω. No eta, no theta.

## Task 2 — Avg Pressure Metric

**Where computed:** `nuclear_evacuation_simulations.py` (lines 467–561), `simple_topology_s1s2_experiments.py` (lines 195–206).

**Formula:** `P(t) = min(1, B(t) + C(t) + S(t))` where:
- B(t) = base pressure (time stress, connectivity)
- C(t) = conflict pressure (conflict intensity × connectivity × decay)
- S(t) = social pressure (connectivity)

**Source:** `agent.calculate_cognitive_pressure(t)` → `s1s2_refactored.total_pressure(...)`.

**Role:** **Derived diagnostic only.** Logged for visualization and analysis. Does **not** affect agent movement decisions. Movement uses the parsimonious model (Ψ × Ω) in `moving.py`.

## Task 3 — Actions Taken

**Conclusion:** η and θ are genuinely unused (legacy) in the core model.

- Removed `eta` and `theta` from `flee/SimulationSettings.py` (s1s2_model_params and move_rules)
- Removed `eta` from `flee/simsetting.yml` and commented s1s2_model schema
- Added comment in `flee/s1s2_model.py` documenting legacy params
- `run_pr_checklist.py` passes after removal

## Task 4 — Methods Footnote (Plain-English Summary)

**For the Science paper:**

> The parameters η (eta, pressure sensitivity) and θ (theta, pressure threshold) appeared in an earlier pressure-based formulation of the dual-process model (see s1s2_refactored), where pressure P(t) = B(t) + C(t) + S(t) combined base, conflict, and social pressure, and S2 activation used sigmoid(P − θ) with η scaling the S2 move probability. The current parsimonious model reduces to two free parameters (α, β) with P_S2 = Ψ × Ω, where Ψ and Ω are sigmoid functions of experience and conflict respectively. η and θ were removed from the model and configuration; they are not used in any movement decisions. The "Avg Pressure" metric reported in some outputs is a diagnostic only—it is computed from the pressure formula for logging and visualization but does not influence agent behavior.
