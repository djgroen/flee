# ✅ Flee Experiments Running!

**Status**: RUNNING  
**Time Started**: Just now  
**Expected Duration**: ~2-3 hours for all 20 experiments

---

## 🚀 **What's Running**

### **Experiments**:
- **5 Topologies**: star, linear, hierarchical, regular_grid, irregular_grid
- **4 S2 Scenarios**: baseline (θ=0.0), low_s2 (θ=0.3), medium_s2 (θ=0.5), high_s2 (θ=0.7)
- **Total**: 20 experiments
- **Population**: 5,000 agents per experiment
- **Duration**: 20 days per simulation
- **Agent Tracking**: Enabled (log_levels.agent: 1)

### **Key Features**:
✅ **Real Flee simulations** (NO synthetic data)  
✅ **Single origin** for all agents  
✅ **Individual agent tracking** enabled  
✅ **S1/S2 switching** with proper parameterization  
✅ **Normalized metrics** for fair comparison

---

## 📊 **Check Progress**

```bash
# Check how many experiments have completed
find colleague_meeting_experiments -name "experiment_results.json" | wc -l

# View the log
tail -f results/reports/colleague_meeting_experiments_log.txt

# Check status
./check_experiment_status.sh
```

---

## 📁 **Output Structure**

```
colleague_meeting_experiments/
├── star_baseline/
│   ├── input_csv/
│   │   ├── locations.csv
│   │   ├── routes.csv
│   │   ├── conflicts.csv
│   │   └── ...
│   ├── source_data/
│   ├── simsetting.yml
│   └── experiment_results.json  ← Generated after run
├── star_low_s2/
├── star_medium_s2/
├── star_high_s2/
├── linear_baseline/
... (20 total)

results/
└── data/
    └── colleague_meeting_results.json  ← Summary of all experiments
```

---

## ⏳ **What Happens Next**

1. **Experiments complete** (~2-3 hours)
2. **Generate figures** (`python generate_colleague_meeting_figures.py`)
3. **Review results**
4. **Present to colleagues**

---

## 🎯 **Expected Results**

### **Topology Sensitivity**:
- **Star**: High S2 activation (many options from center)
- **Linear**: Low S2 activation (limited options)
- **Hierarchical**: Medium S2 activation (structured choices)
- **Grids**: Variable S2 activation (depends on connectivity)

### **S2 Threshold Effects**:
- **Baseline (θ=0.0)**: Minimal S2 (~0-5%)
- **Low S2 (θ=0.3)**: High S2 (~30-50%)
- **Medium S2 (θ=0.5)**: Moderate S2 (~15-30%)
- **High S2 (θ=0.7)**: Low S2 (~5-15%)

---

## ✅ **Fixed Issues**

1. ✅ Flee imports working (was sandbox issue)
2. ✅ `conflict_date` CSV format fixed
3. ✅ All agents start from single origin
4. ✅ Individual agent tracking enabled
5. ✅ S1/S2 switching properly configured

---

**Flee is running! Real simulations with individual agents!** 🎉




