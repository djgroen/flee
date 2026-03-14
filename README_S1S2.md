# S1/S2 Dual-Process Decision-Making in FLEE

Dual-process (System 1 / System 2) cognitive model for refugee movement decisions, based on Kahneman's framework. When merged to main FLEE, this document can become a section in the main README or live in `docs/`.

---

## Overview

Agents switch between two modes each timestep:

- **System 1 (S1):** Heuristic, fast — uses location `movechance` and standard route selection.
- **System 2 (S2):** Deliberative — move probability σ from safety differential; enhanced route awareness.

Move probability is a continuous blend: **P_move = (1−P_S2)·P_S1 + P_S2·σ**, where P_S2 = Ψ×Ω.

---

## Model

- **P_S2 = Ψ(experience; α) × Ω(conflict; β)**
  - Ψ: cognitive capacity (sigmoid in experience index)
  - Ω: structural opportunity (sigmoid in 1−conflict)
- **S2 move probability:** `sigmoid(β × (conflict_current − conflict_best_neighbour))` — no extra parameters.
- **Parameters:** α, β only (parsimonious).

---

## Configuration

Enable in `simsetting.yml` or your config:

```yaml
move_rules:
  two_system_decision_making: true
  s1s2_model:
    enabled: true
    alpha: 2.0   # Ψ sensitivity
    beta: 2.0    # Ω sensitivity
```

---

## Quick Start

```bash
# Validation (default-off + default-on)
python run_pr_checklist.py

# Run experiments (ring, star, linear)
python run_fork_experiments.py
python analyze_fork_experiments.py

# Animate agents
python animate_agents.py --topology ring --results data/experiments/ring/results_a2.0_b2.0_s0.csv -o ring_anim.mp4
```

See **SCRIPTS_CATALOGUE.md** for full script list.

---

## Merge Notes for Main FLEE

When merging this branch:

1. **Core code:** `flee/moving.py`, `flee/s1s2_model.py`, `flee/SimulationSettings.py` — S1/S2 is off by default (`two_system_decision_making: false`).
2. **Docs:** Add an S1/S2 section to the main README, or keep this as `docs/S1S2.md`.
3. **Scripts:** `run_pr_checklist.py`, `run_nuclear_parameter_sweep.py`, `run_fork_experiments.py`, `animate_agents.py` — optional; can live in `examples/` or `scripts/` if main FLEE prefers.
4. **Tests:** `tests/test_twosystem.py` and `run_pr_checklist.py` cover the feature.
