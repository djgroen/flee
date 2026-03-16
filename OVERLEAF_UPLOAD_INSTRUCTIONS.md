# Overleaf Upload Instructions

## ✅ Updated `main.tex`

I've added a new **Results** section to your presentation with:
1. Temporal dynamics figure showing S2 activation over time
2. Ring topology explanation (98% S2 at Ring3, one step from SafeZone)
3. Topology comparison figure
4. Summary statistics table
5. Network diagrams figure

## 📤 Uploading to Overleaf

### Step 1: Upload Figures

Upload these 3 PNG files to Overleaf (drag-and-drop into the project):

```
nuclear_evacuation_results/nuclear_evacuation_temporal_dynamics.png
nuclear_evacuation_results/nuclear_evacuation_topology_comparison.png
nuclear_evacuation_results/nuclear_evacuation_network_diagrams.png
```

**Option A: Keep subdirectory structure**
- Create a folder `nuclear_evacuation_results/` in Overleaf
- Upload figures there
- Paths in `main.tex` will work as-is

**Option B: Put figures in root (simpler)**
- Upload figures directly to project root
- Update paths in `main.tex` to remove `nuclear_evacuation_results/` prefix

### Step 2: Compile

1. Upload `main.tex` to Overleaf
2. Click "Recompile"
3. Check for any errors (usually just missing figure files)

### Step 3: Verify

The new Results section should appear after "Implementation" and before "Validation Strategy" with:
- 5 new slides showing simulation results
- All figures displaying correctly
- Table with summary statistics

## 📊 What Was Added

### New Section: Results (5 slides)

1. **Temporal Dynamics**: S2 activation over time for all three topologies
2. **Ring Topology Finding**: Explanation of 98% S2 activation at Ring3 (one step from SafeZone)
3. **Topology Comparison**: Bar charts comparing S2 rates, evacuation success, and pressure
4. **Summary Statistics Table**: Numerical comparison across topologies
5. **Network Diagrams**: Schematic diagrams of each topology structure

### Key Content

- **Main Finding**: Ring3 shows 98% S2 activation when one step from SafeZone
- **Mechanism**: High Ψ (experience) × High Ω (low conflict) = High P_S2
- **Validation**: Results match model predictions $P_{S2} = \Psi \times \Omega$

## 🔧 If Figures Don't Display

1. **Check file paths**: Make sure figure paths match where you uploaded them
2. **Check file names**: Case-sensitive on some systems
3. **Check file format**: Should be PNG (not JPG or other formats)
4. **Recompile**: Sometimes Overleaf needs a refresh

## 📝 Notes

- All figures are 300 DPI, publication-ready
- Table uses `booktabs` package (already in your preamble)
- Figures are sized at 85% text width for good visibility
- Captions explain key findings and connect to model

