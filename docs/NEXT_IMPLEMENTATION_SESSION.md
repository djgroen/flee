# Next Implementation Session — Prompts 4–9

Components designed in Prompts 1–9 that do **not** yet exist in the repo.
Implement these on top of the committed dual-process base.

## Missing Files

| File | Purpose |
|------|---------|
| `flee/decision_engine.py` | BlendEngine + SwitchEngine factory pattern |
| `flee/network_builder.py` | OSM + synthetic topology builder |
| `flee/verify_implementation.py` | 31-check verification script |
| `flee/postprocessing/compare_modes.py` | Analysis pipeline + figures |

## Notes

- **decision_engine.py**: The current implementation uses blend mode integrated directly into `moving.py`. Refactoring into the factory pattern will not change the math.
- **verify_implementation.py**: Run with `python -m flee.verify_implementation`; expected output: all 31 checks pass.

## GitHub Issue Template

**Title:** Implement Prompts 4-9: network builder, decision engine factory, verification script, analysis pipeline

**Body:**
- [ ] `flee/decision_engine.py` — BlendEngine + SwitchEngine factory (Prompt 4–5)
- [ ] `flee/network_builder.py` — OSM + synthetic topology builder (Prompt 6)
- [ ] `flee/verify_implementation.py` — 31-check verification script (Prompt 7)
- [ ] `flee/postprocessing/compare_modes.py` — Analysis pipeline + figures (Prompt 8–9)
