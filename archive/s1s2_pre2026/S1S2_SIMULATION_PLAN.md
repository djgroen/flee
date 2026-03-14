# S1/S2 Simulation Plan - Short-Term Goals (By Tomorrow)

## 🎯 Objective
Run and validate S1/S2 simulations with the new functions to demonstrate the dual-process decision-making system works correctly.

## ✅ Current Status
- ✅ S1/S2 code updated in `flee/moving.py` and `flee/flee.py`
- ✅ 5-parameter model implemented (`flee/s1s2_model.py`)
- ✅ Refactored system implemented (`flee/s1s2_refactored.py`)
- ✅ Bug fixes applied (boolean conversion, type safety, gitignore)
- ⏳ Need to verify simulations run correctly
- ⏳ Need to validate S1/S2 activation works

## 📋 Short-Term Goals (By Tomorrow)

### Goal 1: Verify S1/S2 System Loads Correctly ⏱️ 15 min
**Status**: In Progress
- [x] Check imports work (`flee.s1s2_model`, `flee.s1s2_refactored`)
- [ ] Run minimal import test
- [ ] Verify no import errors

**Success Criteria**: 
- All modules import without errors
- No segmentation faults
- Configuration parameters load correctly

---

### Goal 2: Create Minimal Test Simulation ⏱️ 30 min
**Status**: Pending
- [ ] Create `test_minimal_s1s2.py` script
- [ ] Test with 1 agent, 5 locations, 10 timesteps
- [ ] Verify S1/S2 activation logic executes
- [ ] Check decision logging works

**Success Criteria**:
- Simulation runs without errors
- S1/S2 activation is logged
- Cognitive pressure calculated correctly
- At least one S2 activation occurs

---

### Goal 3: Update Configuration Template ⏱️ 10 min
**Status**: Pending
- [ ] Update `flee/simsetting.yml` with S1/S2 parameters
- [ ] Document all S1/S2 configuration options
- [ ] Create example configurations (baseline, high S2, low S2)

**Success Criteria**:
- Template includes all S1/S2 parameters
- Clear documentation of each parameter
- Example configs work correctly

---

### Goal 4: Run Small-Scale Validation ⏱️ 45 min
**Status**: Pending
- [ ] Run test with 10 agents, simple topology (5 nodes)
- [ ] Verify S2 activation rates are reasonable (10-50%)
- [ ] Check cognitive pressure values are bounded [0, 1]
- [ ] Validate decision history is recorded

**Success Criteria**:
- Simulation completes successfully
- S2 activation rate between 10-50% (reasonable range)
- All cognitive pressure values in valid range
- Decision logs contain S1/S2 information

---

### Goal 5: Create Simple Experiment Runner ⏱️ 30 min
**Status**: Pending
- [ ] Create `run_simple_s1s2_test.py` script
- [ ] Support different S2 threshold values
- [ ] Generate basic output (S2 rate, pressure stats)
- [ ] Save results to CSV/JSON

**Success Criteria**:
- Script runs experiments with different parameters
- Outputs are saved and readable
- Can compare S1 vs S2 behavior

---

## 🔧 Technical Requirements

### Required Files
1. **`test_minimal_s1s2.py`** - Minimal test script
2. **`run_simple_s1s2_test.py`** - Simple experiment runner
3. **Updated `flee/simsetting.yml`** - With S1/S2 parameters

### Configuration Parameters to Test
```yaml
move_rules:
  two_system_decision_making: true  # Enable S1/S2
  conflict_threshold: 0.5           # S2 activation threshold
  connectivity_mode: "baseline"     # Connectivity calculation mode
  steepness: 6.0                    # Sigmoid steepness
  s1s2_model:
    enabled: false                  # Use 5-parameter model? (optional)
    alpha: 2.0
    beta: 2.0
    eta: 4.0
    theta: 0.5
    p_s2: 0.8
```

### Test Scenarios
1. **Baseline**: `two_system_decision_making: true`, default parameters
2. **High S2**: Lower threshold, higher steepness
3. **Low S2**: Higher threshold, lower steepness
4. **5-Parameter Model**: Enable `s1s2_model.enabled: true`

---

## 📊 Expected Outputs

### Minimal Test Output
- Console log showing:
  - S1/S2 activation events
  - Cognitive pressure values
  - Decision counts (S1 vs S2)
- Summary statistics:
  - Total S2 activations
  - Average cognitive pressure
  - S2 activation rate

### Simple Experiment Output
- CSV file with columns:
  - `experiment_id`
  - `s2_threshold`
  - `s2_activation_rate`
  - `avg_cognitive_pressure`
  - `num_agents`
  - `num_timesteps`

---

## 🚨 Risk Mitigation

### Risk 1: Import Errors
**Mitigation**: Test imports first, check Python path

### Risk 2: Segmentation Fault
**Mitigation**: Start with minimal test, check C extensions

### Risk 3: S2 Never Activates
**Mitigation**: Lower threshold, increase conflict intensity, check capability gates

### Risk 4: Configuration Not Loading
**Mitigation**: Verify YAML format, check parameter names match code

---

## 📝 Next Steps (After Tomorrow)

1. **Scale Up**: Run with 100-1000 agents
2. **Topology Tests**: Test different network topologies
3. **Parameter Sweeps**: Systematic parameter exploration
4. **Validation**: Compare S1 vs S2 behavior
5. **Documentation**: Document findings and parameter effects

---

## 🎯 Success Metrics

**By Tomorrow, We Should Have**:
- ✅ Working minimal test that runs without errors
- ✅ At least one successful S1/S2 simulation
- ✅ Basic output showing S2 activation
- ✅ Understanding of which parameters control S2 activation
- ✅ Confidence that the system works end-to-end

---

## 📞 Quick Reference

### Key Files
- `flee/moving.py` - Main S1/S2 logic
- `flee/flee.py` - Cognitive pressure calculation
- `flee/s1s2_model.py` - 5-parameter model
- `flee/s1s2_refactored.py` - Refactored implementation
- `flee/SimulationSettings.py` - Configuration loading

### Key Functions
- `calculateMoveChance()` - Main decision function
- `calculate_cognitive_pressure()` - Pressure calculation
- `calculate_systematic_s2_activation()` - S2 activation logic
- `calculate_move_probability_s1s2()` - 5-parameter model

### Key Parameters
- `TwoSystemDecisionMaking` - Enable/disable S1/S2
- `conflict_threshold` - S2 activation threshold
- `steepness` - Sigmoid steepness parameter
- `connectivity_mode` - How to calculate connectivity

---

*Last Updated: [Current Date]*
*Status: Ready to Execute*

