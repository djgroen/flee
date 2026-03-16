# Updating LaTeX Overleaf Presentation - Guide

## Recommendation: **Use Cursor (Ask Model) for Code-Related Updates**

### Why Cursor is Better for This Task:

1. **Context Awareness**: Cursor has full access to your codebase, simulation results, and figure files
2. **Code Understanding**: Can read and understand your LaTeX files, Python scripts, and data structures
3. **Consistency**: Ensures figures, data, and code references are all aligned
4. **Efficiency**: Can generate LaTeX code snippets, update figure paths, and format tables directly

### When to Use Claude Separately:

- **Pure LaTeX formatting** (spacing, alignment, typography)
- **Writing narrative text** (abstract, discussion, conclusions)
- **Citation management** (BibTeX, references)
- **Complex LaTeX packages** (tikz, pgfplots, beamer themes)

## Recommended Workflow

### Step 1: Update Figures in Cursor (Current Session)

✅ **Already Done:**
- Aggregate figures generated and validated
- Individual agent animations created (MP4)
- All results match between aggregate and individual data

### Step 2: Prepare LaTeX Content in Cursor

**Ask Cursor to:**
1. **Read your existing Overleaf `.tex` files** (if you share them)
2. **Generate updated figure inclusion code** with correct paths
3. **Create tables** from simulation results (CSV/JSON data)
4. **Update methodology section** to match current code implementation
5. **Generate results section** with key findings

**Example prompts for Cursor:**
```
"Read my presentation.tex file and update the results section with the new 
nuclear evacuation simulation results. Include the three aggregate figures 
and create a table comparing S2 activation rates across topologies."

"Generate LaTeX code to include the temporal dynamics figure with a caption 
explaining the S2 activation pattern (98% at Ring3, one step from SafeZone)."
```

### Step 3: Copy to Overleaf

1. **Copy updated LaTeX code** from Cursor
2. **Upload figure files** to Overleaf (drag-and-drop PNG files)
3. **Compile in Overleaf** to check formatting
4. **Fine-tune in Overleaf** if needed (spacing, alignment)

## What Cursor Can Help With Now

### 1. Generate LaTeX Figure Code

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{nuclear_evacuation_temporal_dynamics.png}
    \caption{System 2 activation and evacuation progress over time for three 
    topologies. Ring topology shows highest S2 activation (98\% at Ring3, 
    one step from SafeZone), consistent with the model $P_{S2} = \Psi \times \Omega$.}
    \label{fig:temporal_dynamics}
\end{figure}
```

### 2. Create Results Tables

```latex
\begin{table}[htbp]
    \centering
    \begin{tabular}{lccc}
        \toprule
        Topology & Avg S2 Rate (\%) & Final Evacuation (\%) & Peak S2 (\%) \\
        \midrule
        Ring     & XX.X            & XX.X                & XX.X \\
        Star     & XX.X            & XX.X                & XX.X \\
        Linear   & XX.X            & XX.X                & XX.X \\
        \bottomrule
    \end{tabular}
    \caption{Comparison of S2 activation and evacuation success across topologies.}
    \label{tab:topology_comparison}
\end{table}
```

### 3. Update Methodology

Cursor can read your current code and generate accurate methodology text that matches the implementation.

## Files Ready for Overleaf

### Figures (PNG, 300 DPI):
- `nuclear_evacuation_temporal_dynamics.png`
- `nuclear_evacuation_topology_comparison.png`
- `nuclear_evacuation_network_diagrams.png`

### Animations (MP4, for supplementary material):
- `ring_agent_movements_corrected.mp4`
- `star_agent_movements_corrected.mp4`
- `linear_agent_movements_corrected.mp4`

### Data Files (for tables):
- `nuclear_evacuation_detailed_*.json` - Full results
- `nuclear_evacuation_summary_*.csv` - Summary statistics

## Next Steps

1. **Share your Overleaf `.tex` files** with Cursor (or paste relevant sections)
2. **Ask Cursor to update** the results section with new figures and data
3. **Copy the generated LaTeX** to Overleaf
4. **Upload figure files** to Overleaf
5. **Compile and fine-tune** formatting if needed

## Example Cursor Prompt

```
I need to update my LaTeX presentation with the new nuclear evacuation 
simulation results. Please:

1. Read my presentation.tex file (or I'll paste it)
2. Update the results section with:
   - The three aggregate figures (temporal dynamics, topology comparison, network diagrams)
   - A table comparing S2 activation rates
   - Text explaining the key finding: 98% S2 activation at Ring3 (one step from SafeZone)
3. Generate the LaTeX code for figure inclusion and table
4. Update the methodology to match the current code implementation
```

This approach leverages Cursor's code understanding while keeping Overleaf for final formatting and compilation.

