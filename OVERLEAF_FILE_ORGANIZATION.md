# Overleaf File Organization Guide

## ✅ Fixed: Figure Paths Updated

I've updated `main.tex` to use simple filenames instead of subdirectory paths. The figure paths are now:
- `nuclear_evacuation_temporal_dynamics.png` (was `nuclear_evacuation_results/nuclear_evacuation_temporal_dynamics.png`)
- `nuclear_evacuation_topology_comparison.png` (was `nuclear_evacuation_results/nuclear_evacuation_topology_comparison.png`)
- `nuclear_evacuation_network_diagrams.png` (was `nuclear_evacuation_results/nuclear_evacuation_network_diagrams.png`)

## 📁 How to Organize Files in Overleaf

### Option 1: All Files in Root Directory (Recommended)
Upload all files to the **same directory** as `main.tex`:

```
Overleaf Project Root/
├── main.tex
├── nuclear_evacuation_temporal_dynamics.png
├── nuclear_evacuation_topology_comparison.png
├── nuclear_evacuation_network_diagrams.png
└── (other figures if needed)
```

**Steps:**
1. Upload `main.tex` to Overleaf
2. Upload all PNG figures to the **same directory** (root of your Overleaf project)
3. Compile - it should work!

### Option 2: Keep Subdirectory Structure
If you prefer to keep files in a subdirectory:

1. Create a folder in Overleaf called `nuclear_evacuation_results/`
2. Upload all PNG files to that folder
3. The paths in `main.tex` would need to be:
   ```latex
   \includegraphics[width=0.85\textwidth]{nuclear_evacuation_results/nuclear_evacuation_temporal_dynamics.png}
   ```

**Note:** I've already updated the paths to Option 1 (simple filenames), so use Option 1 unless you want to change the paths back.

## 📊 Required Figures

You need to upload these 3 figures (minimum):
1. `nuclear_evacuation_temporal_dynamics.png`
2. `nuclear_evacuation_topology_comparison.png`
3. `nuclear_evacuation_network_diagrams.png`

**Location:** All figures are in `nuclear_evacuation_results/` directory locally.

## 🚀 Quick Upload Steps

1. **In Overleaf:**
   - Click "Upload" button (top left)
   - Select `main.tex`
   - Upload all 3 PNG figures to the **root directory** (same level as `main.tex`)

2. **Compile:**
   - Click "Recompile" button
   - Should work now!

## ✅ Verification

After uploading, your Overleaf project should look like:
```
Project Root/
├── main.tex ✅
├── nuclear_evacuation_temporal_dynamics.png ✅
├── nuclear_evacuation_topology_comparison.png ✅
└── nuclear_evacuation_network_diagrams.png ✅
```

All files at the same level = paths will work!





