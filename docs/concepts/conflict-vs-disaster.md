# Conflict vs disaster use cases

Flee supports two main types of displacement simulation. They share the same underlying agent-based model, but differ in the input data used, the triggering mechanism for displacement, and some model settings.

---

## Conflict displacement (the default use case)

The standard Flee use case models displacement caused by **armed conflict**. Agents are spawned at locations that experience conflict events and move towards camps or safer areas.

**Key inputs:**

| File | Purpose |
|------|---------|
| `locations.csv` | All locations in the simulation (towns, camps, conflict zones) |
| `routes.csv` | Links between locations with distances |
| `conflicts.csv` | Conflict schedule — which locations have conflict on which days, and at what intensity (0–1) |
| `closures.csv` | Border or route closures |
| `simsetting.yml` | Model parameters |

**Validation data** typically comes from UNHCR camp registration figures.

**When to use:** modelling forced displacement during active or historical armed conflicts.

See the [Conflict use case section](../conflict/index.md) for a full guide on building a conflict scenario.

---

## DFlee — disaster-driven displacement

**DFlee** is a specialised configuration of Flee for modelling displacement driven by **natural disasters**, currently focused on flooding. Rather than a conflict schedule, displacement is driven by **flood level data** assigned to locations.

DFlee is presented as a separate use case because:

- The input data sources differ (flood/disaster data rather than ACLED conflict data)
- The triggering mechanism is flood level rather than conflict intensity
- Additional data layers such as food security indicators (IPC data) are often included
- The spatial structure may be different (e.g. using flood-affected zones as locations)

**Key additional inputs:**

| File | Purpose |
|------|---------|
| `flood_levels.csv` | Flood intensity per location per day (replaces `conflicts.csv`) |
| IPC data | Food security conditions that influence movement decisions |

**When to use:** modelling displacement caused by flooding or other disasters where spatial intensity data (rather than conflict event data) drives movement.

See the [DFlee section](../dflee/index.md) for a full guide.

---

## Feature comparison

| Feature | Conflict | DFlee |
|---------|----------|-------|
| Displacement trigger | Conflict events (ACLED-based) | Flood levels |
| Data source | ACLED + UNHCR | Disaster/flood datasets + IPC |
| Food security modelling | Optional | Often included |
| Validation data | UNHCR camp figures | Displacement surveys or estimates |
| Typical timescale | Months to years | Days to months |

---

## Which should I use?

- If you are modelling a conflict (civil war, insurgency, etc.) → use the **standard conflict** setup
- If you are modelling displacement from flooding or another natural disaster → use **DFlee**

If you are unsure, start with the [concepts overview](agent-based-model.md) and then look at the example scenarios in `conflict_input/` (conflict) or the DFlee documentation.
