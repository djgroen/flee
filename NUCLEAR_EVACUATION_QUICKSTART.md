# Nuclear Evacuation Simulations - Quick Start

## 🎯 Purpose

Test the parsimonious dual-process S1/S2 model (`P_S2 = Ψ × Ω`) with three topologies relevant for nuclear evacuations.

## 📋 Three Topologies

1. **Ring/Circular** - Evacuation zones (Fukushima, Chernobyl style)
2. **Star/Hub-and-Spoke** - Central facility with radiating routes (Indian Point style)
3. **Linear** - Single evacuation corridor (coastal/mountain facilities)

## 🚀 Quick Start

### Step 1: Run Simulations
```bash
python nuclear_evacuation_simulations.py
```

**What it does:**
- Creates 3 network topologies
- Runs 100 agents for 30 timesteps each
- Tracks S2 activation, evacuation progress, cognitive pressure
- Saves results to `nuclear_evacuation_results/`

### Step 2: Visualize Results
```bash
python visualize_nuclear_evacuations.py
```

**What it creates:**
- Temporal dynamics plots (S2 rate, evacuation progress, pressure)
- Topology comparison charts
- Network diagrams

## 📊 Expected Outputs

### Summary CSV
- `nuclear_evacuation_summary_YYYYMMDD_HHMMSS.csv`
- Columns: topology, S2 rates, evacuation success, etc.

### Detailed JSON
- `nuclear_evacuation_detailed_YYYYMMDD_HHMMSS.json`
- Full time series data for each topology

### Visualizations
- `nuclear_evacuation_temporal_dynamics.png` - Time series
- `nuclear_evacuation_topology_comparison.png` - Bar charts
- `nuclear_evacuation_network_diagrams.png` - Topology diagrams

## 🔬 Scientific Questions

1. **Does topology affect S2 activation?**
   - Prediction: Star > Ring > Linear (complexity)

2. **Does conflict gradient shape S2?**
   - Prediction: Inverted-U for Ring, monotonic for Linear

3. **Does S2 improve evacuation success?**
   - Prediction: Higher S2 → better route choice → higher success

## ⚙️ Configuration

Edit `nuclear_evacuation_simulations.py` to change:
- `num_agents`: Number of agents (default: 100)
- `num_timesteps`: Simulation length (default: 30)
- Topology parameters (locations, distances, etc.)
- S1/S2 model parameters (alpha, beta, p_s2)

## 📚 Documentation

- `NUCLEAR_EVACUATION_TOPOLOGIES.md` - Detailed rationale for each topology
- `CODE_ALIGNMENT_SUMMARY.md` - Model implementation details
- `PRESENTATION_VS_CODE_COMPARISON.md` - Theory vs code comparison

---

**Ready to run!** Start with `python nuclear_evacuation_simulations.py`

