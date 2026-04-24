# DFlee — disaster-driven displacement

**DFlee** is a use case of Flee for modelling displacement caused by natural disasters, currently focused on **flood-driven displacement**.

DFlee uses the same agent-based model as the conflict use case, but replaces conflict events with flood level data as the mechanism that drives people to move. It is treated as a separate use case because the input data, triggering mechanisms, and relevant settings differ significantly.

!!! note
    Conflict-driven and flood-driven spawning cannot currently be combined in a single simulation. Choose one or the other for your scenario.

---

## Pages in this section

- **[Getting started with DFlee](overview.md)** — key settings and how to configure DFlee
- **[Data files](data-files.md)** — how to obtain and format flood and IDP data
- **[Food security](food-security.md)** — incorporating IPC food security data
- **[Building a DFlee scenario](construction.md)** — step-by-step guide

---

## How DFlee differs from the conflict use case

| Aspect | Conflict | DFlee |
|--------|----------|-------|
| Displacement trigger | Conflict events (ACLED-based) | Flood levels (from `flood_level.csv`) |
| Spawning mechanism | `conflict_driven_spawning` | `flood_driven_spawning` |
| Data sources | ACLED, UNHCR | Flood datasets, IDP surveys |
| Optional extra data | — | IPC food security data |
| Agent awareness | Movement cost, camp attractiveness | Flood level, flood forecast awareness |

---

## Example configuration

A working example DFlee scenario is available in:
```
~/FabSim3/plugins/FabFlee/config_files/dflee_test/
```

Use this as a template for building your own DFlee scenario.
