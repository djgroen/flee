# PR checklist for S1/S2 dual-process feature

Minimal local checks before opening a pull request to main FLEE (djgroen/flee).

## Command

From the repository root:

```bash
python run_pr_checklist.py
```

## What it does

1. **Default-off**: Runs one short simulation with `two_system_decision_making: false` (200 agents, 5 timesteps, ring topology). Confirms no crash and unchanged behavior when S1/S2 is disabled.
2. **Default-on**: Runs one short simulation with `two_system_decision_making: true` (same size). Confirms run completes and that the results CSV contains the `p_s2` column (S2 activation probability).

Outputs are written under `data/pr_checklist/` (default_off/, default_on/, configs/). Exit code 0 means the checklist passed; safe to open the PR.

## Config schema for PR description

When opening the PR, you can point reviewers to this snippet for the S1/S2 config schema:

```yaml
move_rules:
  two_system_decision_making: true   # Enable S1/S2 (default: false)
  s1s2_model:
    enabled: true
    alpha: 2.0    # Cognitive capacity sensitivity (Ψ)
    beta: 2.0     # Structural opportunity sensitivity (Ω)
    p_s2: 0.8     # S2 move probability
# P_S2 = Ψ(experience; α) × Ω(conflict; β). Agent uses S2 when P_S2 > 0.5.
```
