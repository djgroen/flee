# Quick Start: S1/S2 Simulations

## 🚀 Get Started in 3 Steps

### Step 1: Test Imports (2 minutes)
```bash
python -c "from flee import flee; from flee.s1s2_model import *; from flee.s1s2_refactored import *; print('✅ All imports work!')"
```

### Step 2: Run Minimal Test (5 minutes)
```bash
python test_minimal_s1s2.py
```

**Expected Output:**
- ✅ All imports successful
- ✅ Simulation runs
- ✅ S2 activation rate shown
- ✅ Cognitive pressure values in [0, 1]

### Step 3: Run Simple Experiments (10 minutes)
```bash
python run_simple_s1s2_test.py
```

**Expected Output:**
- CSV file: `s1s2_results_YYYYMMDD_HHMMSS.csv`
- JSON file: `s1s2_results_YYYYMMDD_HHMMSS.json`
- Summary table with S2 rates for different thresholds

---

## 📋 What You Have Now

### ✅ Files Created
1. **`S1S2_SIMULATION_PLAN.md`** - Complete plan with short-term goals
2. **`test_minimal_s1s2.py`** - Minimal test script (1 agent, 10 timesteps)
3. **`run_simple_s1s2_test.py`** - Simple experiment runner (multiple thresholds)
4. **`flee/simsetting.yml`** - Updated with all S1/S2 parameters

### ✅ Configuration
- S1/S2 system enabled by default
- All parameters documented
- Example configurations included

---

## 🎯 Tomorrow's Goals Checklist

- [ ] **Goal 1**: Verify imports work (15 min)
  - Run: `python -c "from flee import flee; print('OK')"`
  
- [ ] **Goal 2**: Run minimal test (30 min)
  - Run: `python test_minimal_s1s2.py`
  - Verify: S2 activates, pressure in [0,1]
  
- [ ] **Goal 3**: Update config template (10 min) ✅ DONE
  - File: `flee/simsetting.yml` already updated
  
- [ ] **Goal 4**: Run small-scale validation (45 min)
  - Run: `python run_simple_s1s2_test.py`
  - Verify: S2 rates reasonable (10-50%)
  
- [ ] **Goal 5**: Create experiment runner (30 min) ✅ DONE
  - File: `run_simple_s1s2_test.py` already created

---

## 🔧 Key Parameters

### Enable S1/S2
```yaml
move_rules:
  two_system_decision_making: true  # Enable/disable
```

### Control S2 Activation
```yaml
move_rules:
  conflict_threshold: 0.5    # Lower = more S2 activation
  steepness: 6.0              # Higher = sharper transition
  connectivity_mode: baseline # How connectivity calculated
```

### Optional: 5-Parameter Model
```yaml
move_rules:
  s1s2_model:
    enabled: true
    alpha: 2.0
    beta: 2.0
    eta: 4.0
    theta: 0.5
    p_s2: 0.8
```

---

## 📊 Understanding Results

### Minimal Test Output
- **S2 activation rate**: Should be 10-50% (reasonable range)
- **Cognitive pressure**: Should be in [0.0, 1.0]
- **Decision history**: Should contain S2 entries

### Experiment Runner Output
- **S2 rate vs threshold**: Lower threshold → higher S2 rate
- **Average pressure**: Should increase with conflict
- **Agents at camp**: Final destination distribution

---

## 🚨 Troubleshooting

### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Test individual imports
python -c "from flee.s1s2_model import sigmoid; print('OK')"
```

### S2 Never Activates
- Lower `conflict_threshold` (try 0.3 or 0.0)
- Increase conflict intensity at origin
- Check agent has connections/education (S2 capability)

### Configuration Not Loading
- Check YAML syntax (indentation matters!)
- Verify parameter names match exactly
- Check `SimulationSettings.move_rules` after loading

---

## 📚 Next Steps

After tomorrow's validation:
1. Scale up to 100-1000 agents
2. Test different topologies
3. Parameter sweeps
4. Compare S1 vs S2 behavior
5. Generate publication figures

---

## 📞 Quick Reference

**Key Files:**
- `flee/moving.py` - Main S1/S2 logic
- `flee/flee.py` - Cognitive pressure
- `flee/s1s2_model.py` - 5-parameter model
- `flee/s1s2_refactored.py` - Refactored system

**Key Functions:**
- `calculateMoveChance()` - Main decision
- `calculate_cognitive_pressure()` - Pressure calc
- `calculate_systematic_s2_activation()` - S2 activation

---

*Ready to run! Start with `python test_minimal_s1s2.py`*

