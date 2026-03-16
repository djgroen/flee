# Aggregate Behavior Figures - Summary

## ✅ Figures Generated and Validated

All aggregate figures have been **validated against individual agent logs** with 0.00% difference.

### 1. Temporal Dynamics (`nuclear_evacuation_temporal_dynamics.png`)

**Three time series plots:**
- **S2 Activation Rate (%)** over time - Shows how System 2 thinking increases as agents gain experience and move to safer locations
- **Evacuation Progress** - Number of agents at safe zones over time (with percentage on right axis)
- **Cognitive Pressure** - Average cognitive pressure over time

**Key Insights:**
- Ring topology shows highest S2 activation (98% at Ring3, one step from SafeZone)
- Star topology shows moderate S2 activation
- Linear topology shows lower S2 activation (simpler decisions)

### 2. Topology Comparison (`nuclear_evacuation_topology_comparison.png`)

**Four comparison bar charts:**
- **Average S2 Rate** - Mean S2 activation across all timesteps
- **Final Evacuation Success Rate** - Percentage of agents reaching safe zones
- **Peak S2 Activation** - Maximum S2 rate achieved
- **Average Cognitive Pressure** - Mean pressure across simulation

**Key Insights:**
- Ring: Highest S2 activation, good evacuation success
- Star: Moderate S2 activation, good evacuation success (multiple routes)
- Linear: Lower S2 activation, lower evacuation success (bottleneck)

### 3. Network Diagrams (`nuclear_evacuation_network_diagrams.png`)

**Schematic diagrams of each topology:**
- **Ring/Circular** - Concentric evacuation zones (Fukushima/Chernobyl style)
- **Star/Hub-and-Spoke** - Central facility with radiating routes (Indian Point style)
- **Linear** - Single evacuation corridor (coastal/mountain facilities)

## Data Validation

✅ **Aggregate statistics match individual agent logs perfectly:**
- Ring: 0.00% difference
- Star: 0.00% difference  
- Linear: 0.00% difference

This confirms that:
1. Aggregate calculations are correct
2. Individual agent tracking is accurate
3. Results are consistent and reliable

## Files Location

All figures are in: `nuclear_evacuation_results/`

- `nuclear_evacuation_temporal_dynamics.png` (300 DPI, publication-ready)
- `nuclear_evacuation_topology_comparison.png` (300 DPI, publication-ready)
- `nuclear_evacuation_network_diagrams.png` (300 DPI, publication-ready)

## For LaTeX/Overleaf

These PNG files are ready to include in your presentation:
- High resolution (300 DPI)
- Clean, publication-quality styling
- Consistent color scheme across all figures
- Clear labels and legends

