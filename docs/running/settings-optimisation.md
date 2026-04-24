# Settings — optimisation

This page covers the `optimisations` section of `simsetting.yml`.

---

## Example

```yaml
optimisations:
  hasten: 1
```

---

## hasten

`hasten` speeds up the simulation by reducing the number of individual agents tracked, while keeping the total simulated population the same. Each agent represents `hasten` people instead of one.

| Value | Effect |
|-------|--------|
| 1 (default) | Full resolution — each agent represents one person |
| 10 | Each agent represents 10 people — 10× faster |
| 100 | Each agent represents 100 people — 100× faster, less precise |

!!! warning
    flee is not deterministic. Even with `hasten = 1`, results can vary by up to ~1% between identical runs due to random sampling. With larger `hasten` values, variability increases further. Use ensemble runs (multiple repeat simulations) when `hasten > 1` to get reliable estimates.

Typical values for large-scale runs: `hasten = 10` to `hasten = 100`, depending on the required precision and available compute time.

---

## Next steps

- [Settings — full reference](settings-reference.md) — complete parameter list
- [Advanced — ensemble simulations](../advanced/ensemble.md) — how to use `hasten` in ensemble context
