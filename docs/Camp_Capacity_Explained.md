# FLEE: Camp Capacity Logic

This document explains how **camp capacity** is handled in the FLEE simulation framework, focusing on the logic implemented in `flee/flee/moving.py`.

---

## 1. What is Camp Capacity?

Each camp (a `Location` with `camp=True`) has a **capacity** attribute, representing the maximum number of agents (refugees) it can hold. This is typically set from input data (e.g., CSV files).

---

## 2. Capacity Enforcement: `getCapMultiplier`

The function that enforces camp capacity is:

```python
def getCapMultiplier(location, numOnLink: int) -> float:
    """
    Checks whether a given location has reached full capacity or is close to it.
    Returns a value between 0.0 and 1.0:
      - 1.0 if occupancy < nearly_full_occ (default 0.9).
      - 0.0 if occupancy >= 1.0.
      - Value in between for intermediate values.
    """
    nearly_full_occ = SimulationSettings.move_rules["CapacityBuffer"]  # e.g., 0.9
    cap_scale = SimulationSettings.move_rules["CapacityScaling"]       # e.g., 1.0
    cap = location.capacity * float(cap_scale)

    if cap < 1:
        return 1.0

    if location.numAgents <= nearly_full_occ * cap:
        return 1.0

    if location.numAgents >= 1.0 * cap:
        return 0.0

    residual = location.numAgents - (nearly_full_occ * cap)
    weight = 1.0 - (residual / (cap * (1.0 - nearly_full_occ)))

    assert weight >= 0.0
    assert weight <= 1.0

    return weight
```

### **How it works:**
- **Below 90% full:** Agents can enter freely (`1.0` multiplier).
- **Between 90% and 100%:** Entry is gradually restricted (multiplier decreases from 1.0 to 0.0).
- **At or above 100%:** No more agents can enter (`0.0` multiplier).

---

## 3. Where is `getCapMultiplier` Used?

It is used in the movement logic, specifically in the calculation of link weights for agent movement:

```python
weight = ( ... ) * getCapMultiplier(link.endpoint, numOnLink=int(link.numAgents))
```

If a camp is full or nearly full, the chance of agents moving there is reduced or eliminated.

---

## 4. Settings That Affect Capacity

- **`CapacityBuffer`**: Fraction of capacity considered "nearly full" (default: 0.9).
- **`CapacityScaling`**: Multiplier to adjust effective capacity (default: 1.0).

These are set in the simulation settings (e.g., `simsetting.yml`).

---

## 5. Summary

- **Camp capacity** is enforced by reducing the probability of agents entering as the camp fills up.
- **Agents are prevented from entering full camps** by the movement logic.
- **Settings** allow you to tune how strict the capacity enforcement is.

---

**References:**
- [`flee/flee/moving.py`](flee/flee/moving.py): `getCapMultiplier` and movement logic.
- Simulation settings: `CapacityBuffer`, `CapacityScaling`.