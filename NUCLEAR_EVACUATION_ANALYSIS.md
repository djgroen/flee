# Nuclear Evacuation Simulation Analysis

## Understanding the Results

### 1. Ring Topology Structure

The ring topology creates **concentric evacuation zones** around a nuclear facility:

```
                    SafeZone (150, 0)
                         |
                    Ring3_Loc1
                    /    |    \
              Ring2_Loc1 ... Ring2_Loc4
              /    |    \
         Ring1_Loc1 ... Ring1_Loc4
              \    |    /
                 Facility (0, 0)
```

**Structure:**
- **Center (Facility)**: Conflict = 0.95 (extreme danger), all agents start here
- **Ring 1** (radius ~33): 4 locations, Conflict ~0.70, connected to center
- **Ring 2** (radius ~67): 4 locations, Conflict ~0.45, connected to Ring 1
- **Ring 3** (radius ~100): 4 locations, Conflict ~0.20, connected to Ring 2
- **Safe Zone** (radius 150): Conflict = 0.0, connected to Ring3_Loc1

**✅ FIXED:** All 4 Ring 3 locations now connect to SafeZone (routes increased from 13 to 16). This improved evacuation rate from 9% to 25%!

### 2. S2 Activation Interpretation

#### Formula: P_S2 = Ψ × Ω

**Ψ (Cognitive Capacity)** = sigmoid(α × experience_index)
- **experience_index** includes:
  - `prior_displacement` = `timesteps_since_departure / 30.0` (25% weight)
  - `local_knowledge` (25% weight)
  - `conflict_exposure` (20% weight)
  - `connections` (15% weight)
  - `age_factor` (10% weight)
  - `education_level` (5% weight)

**Ω (Structural Opportunity)** = sigmoid(β × (1 - conflict))
- Depends on conflict intensity at current location
- Higher conflict → Lower opportunity for deliberation

#### Why S2 Increases Over Time

**At t=0 (Start):**
- `timesteps_since_departure = 0` → Low experience_index → Low Ψ
- Agents at Facility (conflict = 0.95) → Low Ω
- **Result:** P_S2 = Low × Low = **Very Low** (~0%)

**At t=30 (Later):**
- `timesteps_since_departure = 30` → High experience_index → High Ψ
- Agents moved to safer locations (conflict < 0.5) → High Ω
- **Result:** P_S2 = High × High = **High** (~76-93%)

#### Interpretation

**Yes, at later times people have more time to be rational, but it's more nuanced:**

1. **Experience Accumulation:**
   - As agents travel, they gain `prior_displacement` experience
   - This increases their cognitive capacity (Ψ)
   - They become better at planning and decision-making

2. **Environmental Safety:**
   - As agents move away from conflict zones, conflict intensity decreases
   - Lower conflict → Higher structural opportunity (Ω)
   - Safer environments allow for more deliberative thinking

3. **Combined Effect:**
   - Both factors multiply: P_S2 = Ψ × Ω
   - Early: Low experience + High conflict = Low S2
   - Later: High experience + Low conflict = High S2

**This represents a realistic pattern:**
- In immediate crisis (t=0): Agents rely on System 1 (fast, reactive)
- After gaining experience and reaching safety (t=30): Agents use System 2 (deliberative, planning)

### 3. Topology Comparison

| Topology | Final S2 | Avg S2 | Evacuated | Interpretation |
|----------|----------|--------|-----------|----------------|
| **Star** | 93.0% | 81.0% | 23.0% | Multiple clear paths → High rationality |
| **Linear** | 88.0% | 66.5% | 16.0% | Single corridor → Moderate rationality |
| **Ring** | 76.0% | 66.3% | 25.0% | Circular structure → Moderate rationality (improved after fix) |

**Key Insights:**

1. **Star Topology** performs best:
   - Multiple evacuation routes reduce decision complexity
   - Clear hub-and-spoke structure → Easy path-finding
   - Highest S2 activation and evacuation success

2. **Linear Topology** is moderate:
   - Single evacuation corridor
   - Less choice complexity → Moderate S2 activation
   - Moderate evacuation success

3. **Ring Topology** (FIXED):
   - Circular structure with all outer ring locations connected to safe zone
   - Routes: 16 (was 13 before fix)
   - Evacuation improved from 9% to 25% after fixing bottleneck
   - Moderate S2 activation (76%) and moderate evacuation (25%)

### 4. Recommendations

1. **✅ Ring Topology Fixed:**
   - All 4 Ring 3 locations now connect to SafeZone
   - Routes increased from 13 to 16
   - Evacuation rate improved from 9% to 25% (16 percentage point improvement!)

2. **S2 Activation Interpretation:**
   - The increasing S2 over time is **scientifically valid**
   - It represents agents becoming more rational as they:
     - Gain travel experience
     - Move to safer environments
   - This aligns with dual-process theory: experience enables System 2

3. **Visualization Improvements:**
   - Show network structure more clearly
   - Add arrows showing evacuation paths
   - Color-code by conflict intensity
   - Show S2 activation heatmap over network

### 5. Questions Answered

**Q: Why is S2 activation 0% at t=0?**
A: Agents just started, have no travel experience (timesteps_since_departure = 0), and are at high-conflict location. Both Ψ and Ω are low.

**Q: Does higher S2 at later times mean people have more time to be rational?**
A: Yes, but it's both:
- **Time** → More experience → Higher cognitive capacity (Ψ)
- **Safety** → Lower conflict → Higher structural opportunity (Ω)
- Both factors multiply to increase S2 activation

**Q: Why was ring topology evacuation rate so low (9%)?**
A: **FIXED!** The issue was:
- Only one connection from Ring 3 to SafeZone (bottleneck) ✅ **FIXED**
- After connecting all 4 outer ring locations to SafeZone:
  - Routes: 13 → 16
  - Evacuation: 9% → 25% (16 percentage point improvement!)

