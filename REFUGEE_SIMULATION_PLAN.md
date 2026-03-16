# Refugee Movement Simulation Plan: 10-Minute Presentation

## 🎯 **Goal**
Create visually compelling simulations that clearly demonstrate:
1. **Context-dependent processing**: High conflict → System 1, Recovery → System 2
2. **Social connections enable System 2**: Connections prompt mental effort for analytical thinking
3. **System 1 vs System 2 route choices**: Nearest border (S1) vs. calculated routes (S2)

---

## 📊 **Four Key Scenarios**

### **Scenario 1: "Nearest Border" (System 1 Demonstration)**
**Purpose**: Show System 1 heuristic behavior - agents head toward nearest border

**Topology**:
```
    Border A (Safe)
        |
    Town 1
        |
    Conflict Zone (Origin)
        |
    Town 2
        |
    Border B (Safe) [FARTHER]
```

**Key Features**:
- Two safe borders at different distances
- Border A: 100 units away (nearest)
- Border B: 200 units away (farther but safer route)
- High conflict at origin (0.9)
- Agents start with low/no connections

**Expected Behavior**:
- **System 1 agents**: Head to Border A (nearest) - heuristic
- **System 2 agents**: May choose Border B if they calculate it's safer
- High conflict → Most agents use System 1 → Border A gets more traffic

**Visualization Needs**:
- Agent paths colored by cognitive state (red=S1, blue=S2)
- Heat map showing agent density at each border
- Time series: S1 vs S2 activation over time
- Route choice comparison: Border A vs Border B

---

### **Scenario 2: "Multiple Routes" (System 2 Demonstration)**
**Purpose**: Show System 2 deliberation - agents compare routes and choose optimal

**Topology**:
```
    Safe Zone A (Route 1: Short but risky)
        |
    Town 1 (High conflict: 0.6)
        |
    Conflict Zone (Origin)
        |
    Town 2 (Low conflict: 0.2)
        |
    Safe Zone B (Route 2: Longer but safer)
```

**Key Features**:
- Two routes with different characteristics:
  - Route 1: Short distance (100 units) but passes through high-conflict town
  - Route 2: Longer distance (200 units) but passes through low-conflict town
- Recovery zones (towns) allow S2 activation
- Agents can compare routes

**Expected Behavior**:
- **System 1 agents**: Choose Route 1 (shorter) - heuristic
- **System 2 agents**: May choose Route 2 (safer despite longer) - deliberation
- Recovery zones → S2 activation → More Route 2 choices

**Visualization Needs**:
- Network diagram showing both routes
- Agent decision tree: Route 1 vs Route 2 by cognitive state
- Conflict intensity map (heat map)
- S2 activation rate by location

---

### **Scenario 3: "Social Connections" (Connection Effects)**
**Purpose**: Show how social connections enable System 2 processing

**Topology**:
```
    Safe Zone
        |
    Recovery Camp (Builds connections over time)
        |
    Town (Transit)
        |
    Conflict Zone (Origin)
```

**Key Features**:
- Recovery camp where agents build connections over time
- Agents start with 0 connections (isolated)
- Connections increase in recovery camp (community building)
- Two agent groups:
  - Group A: Passes through recovery camp (builds connections)
  - Group B: Direct route (no recovery, stays isolated)

**Expected Behavior**:
- **Group A (with connections)**: Higher S2 activation after recovery camp
- **Group B (isolated)**: Lower S2 activation, stays System 1
- Connections → S2 capability → More deliberative decisions

**Visualization Needs**:
- Connection network visualization (nodes=agents, edges=connections)
- S2 activation rate: With connections vs. Without connections
- Time series: Connection count vs. S2 activation
- Side-by-side comparison: Connected vs. Isolated agents

---

### **Scenario 4: "Context Transition" (S1 → S2 Switch)**
**Purpose**: Show agents switching from System 1 to System 2 as context changes

**Topology**:
```
    Safe Zone
        |
    Recovery Zone (Low conflict: 0.1)
        |
    Transit Zone (Moderate conflict: 0.4)
        |
    Conflict Zone (High conflict: 0.9, Origin)
```

**Key Features**:
- Clear conflict gradient: High → Moderate → Low
- Recovery zone allows connection building
- Agents start in high conflict (S1), move to recovery (S2 possible)

**Expected Behavior**:
- **High conflict zone**: 0% S2 activation (hard constraint)
- **Transit zone**: Moderate S2 activation (context-dependent)
- **Recovery zone**: High S2 activation (low conflict + connections)
- Same agents, different contexts → Different cognitive modes

**Visualization Needs**:
- Agent movement animation colored by cognitive state
- Conflict intensity map with agent positions
- S2 activation rate by location (bar chart)
- Individual agent trajectories showing S1→S2 transitions

---

## 🎨 **Visualization Requirements**

### **1. Agent Movement Animations** (4 videos)
- Color coding:
  - **Red**: System 1 (fast, heuristic)
  - **Blue**: System 2 (deliberative, analytical)
  - **Yellow**: Transitioning between states
- Show agent paths over time
- Include conflict intensity background (heat map)
- Add population counters at key locations

### **2. Network Diagrams** (4 static figures)
- Show topology structure
- Color nodes by conflict intensity
- Label key locations (Conflict Zone, Recovery Zone, Safe Zone)
- Show route options clearly

### **3. Decision Analysis Plots** (4 static figures)
- Route choice comparison (S1 vs S2)
- S2 activation rate by location
- Connection count vs. S2 activation
- Context-dependent processing evidence

### **4. Summary Comparison** (1 static figure)
- Side-by-side comparison of all 4 scenarios
- Key metrics: S2 activation, route choices, connection effects

---

## 📐 **Topology Specifications**

### **Scenario 1: Nearest Border**
```python
locations = [
    {'name': 'ConflictZone', 'x': 0, 'y': 0, 'conflict': 0.9, 'type': 'conflict'},
    {'name': 'Town1', 'x': 50, 'y': 0, 'conflict': 0.3, 'type': 'town'},
    {'name': 'BorderA', 'x': 100, 'y': 0, 'conflict': 0.0, 'type': 'camp'},  # Nearest
    {'name': 'Town2', 'x': 0, 'y': 50, 'conflict': 0.3, 'type': 'town'},
    {'name': 'BorderB', 'x': 0, 'y': 200, 'conflict': 0.0, 'type': 'camp'},  # Farther
]
routes = [
    {'from': 'ConflictZone', 'to': 'Town1', 'distance': 50},
    {'from': 'Town1', 'to': 'BorderA', 'distance': 50},
    {'from': 'ConflictZone', 'to': 'Town2', 'distance': 50},
    {'from': 'Town2', 'to': 'BorderB', 'distance': 150},
]
```

### **Scenario 2: Multiple Routes**
```python
locations = [
    {'name': 'ConflictZone', 'x': 0, 'y': 0, 'conflict': 0.9, 'type': 'conflict'},
    {'name': 'Town1', 'x': 50, 'y': 0, 'conflict': 0.6, 'type': 'town'},  # High conflict
    {'name': 'SafeZoneA', 'x': 100, 'y': 0, 'conflict': 0.0, 'type': 'camp'},  # Short route
    {'name': 'Town2', 'x': 0, 'y': 50, 'conflict': 0.2, 'type': 'town'},  # Low conflict
    {'name': 'SafeZoneB', 'x': 0, 'y': 200, 'conflict': 0.0, 'type': 'camp'},  # Longer but safer
]
routes = [
    {'from': 'ConflictZone', 'to': 'Town1', 'distance': 50},
    {'from': 'Town1', 'to': 'SafeZoneA', 'distance': 50},  # Route 1: 100 total
    {'from': 'ConflictZone', 'to': 'Town2', 'distance': 50},
    {'from': 'Town2', 'to': 'SafeZoneB', 'distance': 150},  # Route 2: 200 total
]
```

### **Scenario 3: Social Connections**
```python
locations = [
    {'name': 'ConflictZone', 'x': 0, 'y': 0, 'conflict': 0.9, 'type': 'conflict'},
    {'name': 'Town', 'x': 50, 'y': 0, 'conflict': 0.3, 'type': 'town'},
    {'name': 'RecoveryCamp', 'x': 100, 'y': 0, 'conflict': 0.1, 'type': 'camp'},  # Builds connections
    {'name': 'SafeZone', 'x': 200, 'y': 0, 'conflict': 0.0, 'type': 'camp'},
    # Alternative direct route (no recovery)
    {'name': 'DirectRoute', 'x': 0, 'y': 50, 'conflict': 0.4, 'type': 'town'},
    {'name': 'SafeZoneDirect', 'x': 150, 'y': 50, 'conflict': 0.0, 'type': 'camp'},
]
routes = [
    # Route with recovery camp
    {'from': 'ConflictZone', 'to': 'Town', 'distance': 50},
    {'from': 'Town', 'to': 'RecoveryCamp', 'distance': 50},
    {'from': 'RecoveryCamp', 'to': 'SafeZone', 'distance': 100},
    # Direct route (no recovery)
    {'from': 'ConflictZone', 'to': 'DirectRoute', 'distance': 50},
    {'from': 'DirectRoute', 'to': 'SafeZoneDirect', 'distance': 100},
]
```

### **Scenario 4: Context Transition**
```python
locations = [
    {'name': 'ConflictZone', 'x': 0, 'y': 0, 'conflict': 0.9, 'type': 'conflict'},
    {'name': 'TransitZone', 'x': 50, 'y': 0, 'conflict': 0.4, 'type': 'town'},
    {'name': 'RecoveryZone', 'x': 100, 'y': 0, 'conflict': 0.1, 'type': 'town'},
    {'name': 'SafeZone', 'x': 200, 'y': 0, 'conflict': 0.0, 'type': 'camp'},
]
routes = [
    {'from': 'ConflictZone', 'to': 'TransitZone', 'distance': 50},
    {'from': 'TransitZone', 'to': 'RecoveryZone', 'distance': 50},
    {'from': 'RecoveryZone', 'to': 'SafeZone', 'distance': 100},
]
```

---

## 🔬 **Simulation Parameters**

### **Agent Initialization**
- **Number of agents**: 500 per scenario (enough for clear patterns, not too many for visualization)
- **Initial connections**: 
  - Scenario 1 & 2: 0-2 connections (low, isolated)
  - Scenario 3: 0 connections (to show connection building)
  - Scenario 4: 0-1 connections (varied)
- **Experience index**: Varied (0.2 to 0.8) to show heterogeneity

### **Connection Building Rules**
- **Recovery camps**: Connections increase by +1 every 5 timesteps (max 8)
- **High population areas**: Connections increase by +1 if population > 100
- **High conflict zones**: Connections decrease by -2 (network disruption)
- **Time decay**: Connections decrease by -1 every 20 timesteps if not maintained

### **S2 Activation Parameters**
- **High conflict threshold**: conflict > 0.5 → Hard constraint (always S1)
- **S2 capability requirement**: connections >= 2
- **Cognitive pressure calculation**: Standard Flee implementation
- **S2 activation threshold**: 0.5 (moderate pressure needed)

### **Simulation Duration**
- **Timesteps**: 40 (long enough to see transitions and patterns)
- **Output frequency**: Every 2 timesteps for animations

---

## 📈 **Metrics to Track**

### **Per Scenario**
1. **S2 activation rate** by location and time
2. **Route choice distribution** (which routes agents choose)
3. **Connection count** over time
4. **Agent distribution** by location type (conflict, town, camp)
5. **Cognitive state transitions** (S1→S2, S2→S1)

### **Comparison Metrics**
1. **S2 activation**: With connections vs. Without connections
2. **Route choices**: System 1 agents vs. System 2 agents
3. **Context effects**: High conflict vs. Recovery zones
4. **Social effects**: Connected agents vs. Isolated agents

---

## 🎬 **Presentation Flow (10 minutes)**

### **Slide 1: Title** (30 sec)
- Context-Dependent Decision-Making in Crisis

### **Slide 2: The Question** (1 min)
- How do people decide where to go?
- System 1 vs System 2 explanation
- **Visual**: Side-by-side comparison diagram

### **Slide 3: Core Principle** (1 min)
- High conflict → System 1
- Recovery + connections → System 2
- **Visual**: Context transition diagram

### **Slide 4: Scenario 1 - Nearest Border** (1.5 min)
- Show topology diagram
- Show agent movement animation (S1 agents → Border A)
- Show route choice comparison
- **Key message**: System 1 uses heuristics (nearest border)

### **Slide 5: Scenario 2 - Multiple Routes** (1.5 min)
- Show topology diagram
- Show agent movement animation (S2 agents compare routes)
- Show decision analysis (S1 vs S2 route choices)
- **Key message**: System 2 deliberates (chooses safer route)

### **Slide 6: Scenario 3 - Social Connections** (1.5 min)
- Show connection network visualization
- Show S2 activation: With vs. Without connections
- Show time series (connections → S2 activation)
- **Key message**: Connections enable System 2

### **Slide 7: Scenario 4 - Context Transition** (1.5 min)
- Show conflict intensity map
- Show agent movement animation (S1→S2 transitions)
- Show S2 activation by location
- **Key message**: Same agents, different contexts → different cognitive modes

### **Slide 8: Summary Comparison** (1 min)
- Side-by-side comparison of all scenarios
- Key metrics table
- **Key message**: Context and social resources shape cognitive availability

### **Slide 9: Humanitarian Implications** (1 min)
- Phase-based interventions
- Social connection support
- Context-aware modeling

### **Slide 10: Conclusion** (30 sec)
- Key takeaways
- Questions

---

## 🛠️ **Implementation Plan**

### **Phase 1: Topology Creation** (1-2 hours)
- Create `refugee_simulations.py` with 4 scenario topologies
- Test topology connectivity
- Verify conflict gradients and route options

### **Phase 2: Simulation Runs** (2-3 hours)
- Run all 4 scenarios with S1/S2 enabled
- Collect detailed metrics (S2 activation, route choices, connections)
- Generate agent movement data

### **Phase 3: Visualization** (3-4 hours)
- Create agent movement animations (4 videos)
- Create network diagrams (4 static figures)
- Create decision analysis plots (4 static figures)
- Create summary comparison (1 static figure)

### **Phase 4: Presentation Integration** (1-2 hours)
- Update LaTeX presentation with new visuals
- Add scenario descriptions
- Create comparison slides

---

## ✅ **Success Criteria**

1. **Clear visual demonstration** of System 1 vs System 2 behavior
2. **Obvious connection effects** on S2 activation
3. **Clear context-dependent processing** (high conflict → S1, recovery → S2)
4. **Compelling animations** that tell the story
5. **Ready for 10-minute presentation** with all visuals

---

## 📝 **Next Steps**

1. ✅ Create this plan document
2. ⏳ Implement topology creation code
3. ⏳ Run simulations
4. ⏳ Generate visualizations
5. ⏳ Update presentation




