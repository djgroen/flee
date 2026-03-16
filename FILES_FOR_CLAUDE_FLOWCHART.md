# Files to Upload to Claude AI for S1/S2 Flow Chart

## 🎯 **Essential Files** (Upload these)

### **1. Core S1/S2 Logic**
📄 **`flee/moving.py`** - Main decision-making logic
- Contains `calculateMoveChance()` function
- Contains `calculate_systematic_s2_activation()` function
- This is WHERE S1/S2 switching happens

### **2. Agent Class & Cognitive Pressure**
📄 **`flee/flee.py`** - Agent (Person) class
- Contains `Person` class definition
- Contains `calculate_cognitive_pressure()` method
- Contains `get_system2_capable()` method
- Contains `log_decision()` method

### **3. Alternative Models (Optional but useful)**
📄 **`flee/s1s2_model.py`** - 5-parameter mathematical model
- Alternative implementation
- Shows cleaner mathematical formulation
- Good for understanding the theory

📄 **`flee/s1s2_refactored.py`** - Refactored implementation
- Modular pressure calculation
- Shows component breakdown

---

## 📊 **What to Ask Claude to Create**

### **Flow Chart 1: S1/S2 Decision Process**
```
"Create a flow chart showing:
1. How an agent decides whether to move (S1 vs S2)
2. Starting from calculateMoveChance()
3. Showing cognitive pressure calculation
4. Showing S2 activation check
5. Showing final move probability calculation
6. Include all key parameters and thresholds"
```

### **Flow Chart 2: Cognitive Pressure Calculation**
```
"Create a flow chart showing:
1. How cognitive_pressure is calculated in calculate_cognitive_pressure()
2. Components: base pressure, conflict pressure, social pressure
3. How each component is bounded
4. How they combine to total pressure [0.0, 1.0]"
```

### **Flow Chart 3: S2 Activation Logic**
```
"Create a flow chart showing:
1. The systematic S2 activation process
2. Sigmoid function application
3. Individual difference modifiers (education, stress, etc.)
4. Random activation based on probability
5. Decision logging"
```

---

## 📝 **Prompt for Claude AI**

Copy and paste this to Claude AI after uploading the files:

```
I'm working on a dual-process (System 1/System 2) cognitive model in a 
refugee agent-based model. I need you to create flowcharts from the code.

I've uploaded:
1. flee/moving.py - Main decision-making logic
2. flee/flee.py - Agent class with cognitive pressure calculation

Please create 3 flowcharts:

FLOWCHART 1: "S1/S2 Decision-Making Process"
- Start: Agent considers moving
- Show: calculateMoveChance() function flow
- Include: cognitive_pressure calculation, S2 activation check, 
  final move probability
- Highlight: Key decision points and parameter values

FLOWCHART 2: "Cognitive Pressure Calculation"
- Start: Agent calls calculate_cognitive_pressure()
- Show: Base pressure, conflict pressure, social pressure components
- Include: Bounding [0.0, 1.0] and combination logic
- Highlight: Time-based effects, connectivity effects

FLOWCHART 3: "S2 Activation Mechanism"
- Start: Cognitive pressure value
- Show: Sigmoid activation function
- Include: Individual modifiers (education, stress tolerance, etc.)
- Include: Random probability check
- End: S2 activated True/False

Use clear boxes for processes, diamonds for decisions, and arrows 
showing flow. Label all parameters and thresholds.
```

---

## 🔍 **Key Functions to Highlight in Flowchart**

### **From flee/moving.py:**
1. `calculateMoveChance(agent, time)` - Line ~450
   - Entry point for all move decisions
   - Checks if S2 switching is enabled
   - Calls cognitive pressure calculation
   - Calls S2 activation function
   - Returns final move probability

2. `calculate_systematic_s2_activation(agent, pressure, base_threshold, time)` - Line ~400
   - Sigmoid activation curve
   - Individual difference modifiers
   - Time-based effects
   - Random activation

### **From flee/flee.py:**
1. `calculate_cognitive_pressure(self, time)` - Line ~300
   - Get conflict intensity
   - Get connectivity
   - Calculate base pressure (bounded 0.4)
   - Calculate conflict pressure (bounded 0.4)
   - Calculate social pressure (bounded 0.2)
   - Return total (bounded 1.0)

2. `get_system2_capable(self)` - Line ~250
   - Check connections >= 2
   - Enhanced capability check

---

## 📦 **Files to Upload**

**Essential (2 files)**:
```
flee/moving.py
flee/flee.py
```

**Optional for context (2 files)**:
```
flee/s1s2_model.py
flee/s1s2_refactored.py
```

---

## 🎨 **Suggested Flowchart Style**

Ask Claude to create:
- **Swimlane diagram** (Agent → Cognitive Pressure → S2 Check → Decision)
- **Color coding**: 
  - Green for S1 (fast/reactive)
  - Blue for S2 (slow/deliberative)
  - Yellow for cognitive pressure calculation
  - Red for decision points
- **Clear labels** for all parameters:
  - `TwoSystemDecisionMaking` threshold
  - `connections` count
  - `education_level`
  - `cognitive_pressure` value
  - etc.

---

## ✅ **Summary**

**Upload these 2-4 files to Claude AI:**
1. ✅ `flee/moving.py` (REQUIRED)
2. ✅ `flee/flee.py` (REQUIRED)
3. ⭐ `flee/s1s2_model.py` (HELPFUL)
4. ⭐ `flee/s1s2_refactored.py` (HELPFUL)

**Ask for 3 flowcharts:**
1. S1/S2 Decision-Making Process
2. Cognitive Pressure Calculation
3. S2 Activation Mechanism

**Result:** Clear visual representation of your cognitive model for slides!



