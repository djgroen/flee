# Nuclear Evacuation Topologies: Rationale and Implementation

## Overview

This document explains why three specific network topologies are most relevant for nuclear-related evacuations and how they map to real-world scenarios.

---

## 1. Ring/Circular Topology

### Real-World Relevance

**Nuclear Scenario:** Circular evacuation zones around a nuclear facility

- **10-mile zone**: Immediate evacuation (highest danger)
- **20-mile zone**: Evacuation or shelter-in-place
- **50-mile zone**: Monitoring and potential evacuation

**Examples:**
- **Fukushima (2011)**: 20km evacuation zone, later expanded to 30km
- **Chernobyl (1986)**: 30km exclusion zone
- **Three Mile Island (1979)**: 5-mile evacuation zone

### Topology Characteristics

```
        Safe Zone
            |
    Ring 3 ─┼─ (Low conflict)
            |
    Ring 2 ─┼─ (Moderate conflict)
            |
    Ring 1 ─┼─ (High conflict)
            |
        Facility (Extreme conflict)
```

**Key Features:**
- Concentric rings at increasing distances
- Conflict intensity decreases with distance
- Multiple evacuation paths (any direction)
- Agents start at center, evacuate radially outward

**S1/S2 Implications:**
- **High conflict at center** → Low Ω → Low S2 activation (panic)
- **Moderate conflict at mid-rings** → Moderate Ω → **Peak S2 activation** (deliberation)
- **Low conflict at outer rings** → High Ω but low urgency → Moderate S2

**Expected Pattern:** Inverted-U relationship with distance from facility

---

## 2. Star/Hub-and-Spoke Topology

### Real-World Relevance

**Nuclear Scenario:** Central facility with designated evacuation routes

- **Primary evacuation routes**: Major highways/roads radiating from facility
- **Route-specific safe zones**: Designated shelters/camps along each route
- **Route capacity**: Different routes have different capacities

**Examples:**
- **Indian Point (NY)**: 10-mile radius, 4 primary evacuation routes
- **Palo Verde (AZ)**: 10-mile radius, 6 evacuation routes
- **Diablo Canyon (CA)**: 10-mile radius, multiple coastal and inland routes

### Topology Characteristics

```
        SafeZone1
            |
            |
    Route1 ─┼─ Mid
            |
        Facility ── Route2 ── Mid ── SafeZone2
            |
            |
        Route3 ── Mid ── SafeZone3
```

**Key Features:**
- Central facility (hub)
- Multiple evacuation routes (spokes)
- Intermediate towns along routes
- Safe zones at route endpoints
- Route-specific characteristics (distance, capacity)

**S1/S2 Implications:**
- **Route choice**: S2 agents evaluate routes, S1 agents follow nearest
- **Route capacity**: S2 agents consider congestion, S1 agents ignore
- **Route distance**: S2 agents optimize, S1 agents take shortest

**Expected Pattern:** Higher S2 activation due to route choice complexity

---

## 3. Linear Topology

### Real-World Relevance

**Nuclear Scenario:** Single evacuation corridor along major road

- **Highway evacuation**: Single major route away from facility
- **Sequential locations**: Towns/cities along the route
- **No alternative paths**: Must follow the linear route

**Examples:**
- **Coastal facilities**: Single highway along coast
- **Mountain facilities**: Single pass/valley route
- **Island facilities**: Single bridge/causeway

### Topology Characteristics

```
    NearFacility → Location1 → Location2 → ... → SafeZone
    (High conflict)  (Decreasing conflict)      (No conflict)
```

**Key Features:**
- Linear chain of locations
- Conflict decreases monotonically along route
- No alternative paths
- Sequential evacuation (bottleneck potential)

**S1/S2 Implications:**
- **Low route complexity** → Less need for S2 deliberation
- **Sequential decision-making**: Each location is a simple choice
- **Bottleneck effects**: S2 agents may wait, S1 agents may rush

**Expected Pattern:** Lower S2 activation (simpler decisions)

---

## Comparison: Expected S2 Activation Patterns

### Hypothesis 1: Topology Complexity → S2 Activation

| Topology | Complexity | Expected S2 Rate | Rationale |
|----------|-----------|------------------|------------|
| **Linear** | Low | 40-60% | Simple sequential decisions |
| **Ring** | Medium | 50-70% | Multiple paths, moderate complexity |
| **Star** | High | 60-80% | Route choice requires deliberation |

### Hypothesis 2: Conflict Gradient → S2 Activation

| Topology | Conflict Gradient | Expected Pattern |
|----------|------------------|------------------|
| **Ring** | Radial (center → edge) | Inverted-U: Peak at mid-distance |
| **Star** | Route-specific | Moderate: Route choice complexity |
| **Linear** | Monotonic (start → end) | Increasing: Less conflict → more deliberation |

### Hypothesis 3: Evacuation Success

| Topology | Expected Success | Rationale |
|----------|-----------------|-----------|
| **Star** | Highest | Multiple routes, less congestion |
| **Ring** | Medium | Multiple paths but potential bottlenecks |
| **Linear** | Lowest | Single route, bottleneck risk |

---

## Implementation Details

### Conflict Intensity Mapping

**Ring Topology:**
```python
conflict = 0.95 - (ring_number * 0.25)  # Decreases with distance
```

**Star Topology:**
```python
facility: conflict = 0.95
mid_route: conflict = 0.40  # Moderate danger
safe_zone: conflict = 0.00  # Safe
```

**Linear Topology:**
```python
conflict = max(0.1, 0.9 - (location_index * 0.15))  # Monotonic decrease
```

### Experience Index for Nuclear Evacuations

For nuclear scenarios, experience factors should emphasize:
- **Prior evacuation experience**: Has agent evacuated before?
- **Local knowledge**: Knowledge of evacuation routes
- **Emergency preparedness**: Training, drills
- **Social connections**: Information networks
- **Age/experience**: Older adults may have more experience

---

## Scientific Questions

1. **Does topology affect S2 activation rates?**
   - Test: Compare S2 rates across topologies
   - Prediction: Star > Ring > Linear

2. **Does conflict gradient shape S2 activation?**
   - Test: Track S2 rate vs. distance from facility
   - Prediction: Inverted-U for Ring, monotonic for Linear

3. **Does S2 activation improve evacuation success?**
   - Test: Compare evacuation rates for S1 vs S2 agents
   - Prediction: S2 agents have higher success (better route choice)

4. **Do bottlenecks emerge differently?**
   - Test: Track congestion at locations
   - Prediction: Linear has worst bottlenecks, Star has least

---

## Validation Against Real Events

### Fukushima (2011)
- **Topology**: Ring (20km zone)
- **Observed**: Initial panic (S1), later deliberation (S2)
- **Model prediction**: Low S2 at start (high conflict), increasing over time

### Three Mile Island (1979)
- **Topology**: Star (multiple routes from facility)
- **Observed**: Coordinated evacuation, route choice
- **Model prediction**: Moderate-high S2 activation

### Chernobyl (1986)
- **Topology**: Ring (30km exclusion zone)
- **Observed**: Delayed evacuation, confusion
- **Model prediction**: Low S2 initially (extreme conflict), increasing with distance

---

## Next Steps

1. **Run simulations** with all three topologies
2. **Compare S2 activation rates** across topologies
3. **Analyze evacuation success** (agents reaching safe zones)
4. **Identify bottlenecks** and congestion patterns
5. **Validate predictions** against empirical patterns

---

*This framework provides a rigorous test of how network topology affects dual-process decision-making in nuclear evacuation scenarios.*

