# LaTeX to PowerPoint: Copy-Paste Guide

## Method 1: Compile LaTeX → Copy from PDF

### Step 1: Compile Beamer to PDF
```bash
pdflatex main.tex
# Run twice to resolve references
pdflatex main.tex
```

### Step 2: Open PDF
- Open `main.pdf` in PDF viewer
- Use as reference while creating PowerPoint

### Step 3: Copy Content
- **Text**: Select and copy from PDF, paste into PowerPoint
- **Figures**: Right-click → Copy Image, paste into PowerPoint
- **Math**: Screenshot equations from PDF, insert as images

### Advantages
- ✅ Preserves formatting
- ✅ Easy to see final layout
- ✅ Figures are already rendered

### Disadvantages
- ⚠️ Math equations need to be recreated or screenshotted
- ⚠️ Some formatting may need adjustment

---

## Method 2: Copy Directly from LaTeX Source

### Step 1: Extract Text Content
Use the `extract_slides_for_powerpoint.py` script to get clean text:
```bash
python3 extract_slides_for_powerpoint.py
```

### Step 2: Copy-Paste Process

#### For Text:
1. Open `main.tex` in editor
2. Find the frame you want
3. Copy text content (skip LaTeX commands)
4. Paste into PowerPoint
5. Format manually

#### For Bullet Points:
LaTeX:
```latex
\begin{itemize}
    \item Point 1
    \item Point 2
\end{itemize}
```

PowerPoint:
- Just paste the text after `\item`
- PowerPoint will auto-format as bullets

#### For Math:
See `extract_math_equations.py` output for equations ready to paste into PowerPoint Equation Editor.

---

## Method 3: Hybrid Approach (Recommended)

### Best of Both Worlds:

1. **Compile PDF first** (reference)
   ```bash
   pdflatex main.tex
   ```

2. **Use PDF for:**
   - Layout reference
   - Figure placement
   - Overall structure

3. **Use LaTeX source for:**
   - Text content (copy-paste)
   - Math equations (use Equation Editor)
   - Precise wording

4. **Use extraction scripts for:**
   - Quick content overview
   - Equation list
   - Figure references

---

## Quick Copy-Paste Checklist

### Text Content
- [ ] Copy from LaTeX source (skip `\textbf{}`, `\textit{}`, etc.)
- [ ] Paste into PowerPoint
- [ ] Apply formatting manually (bold, italic)
- [ ] Check for special characters (quotes, dashes)

### Bullet Points
- [ ] Copy `\item` content
- [ ] Paste into PowerPoint
- [ ] PowerPoint auto-formats as bullets
- [ ] Adjust indentation if needed

### Figures
- [ ] Copy image from PDF, OR
- [ ] Insert from file: `refugee_simulation_results/figures/*.png`
- [ ] Resize to fit slide
- [ ] Add caption

### Math Equations
- [ ] Use `extract_math_equations.py` output
- [ ] Copy equation text
- [ ] Paste into PowerPoint Equation Editor
- [ ] Adjust formatting if needed

### Tables
- [ ] Copy table structure from LaTeX
- [ ] Recreate in PowerPoint (Insert → Table)
- [ ] Copy data values
- [ ] Format table

---

## Common LaTeX → PowerPoint Conversions

### Text Formatting
| LaTeX | PowerPoint |
|-------|------------|
| `\textbf{text}` | **text** (Ctrl+B) |
| `\textit{text}` | *text* (Ctrl+I) |
| `\alert{text}` | Red text or highlight |
| `\emph{text}` | *text* (italic) |

### Special Characters
| LaTeX | PowerPoint |
|-------|------------|
| `---` | — (em dash) |
| `--` | – (en dash) |
| `` `text' `` | 'text' (smart quotes) |
| `\&` | & |
| `\%` | % |

### Math Symbols (for Equation Editor)
| LaTeX | PowerPoint Input |
|-------|------------------|
| `\times` | \times |
| `\div` | \div |
| `\pm` | \pm |
| `\leq` | \leq |
| `\geq` | \geq |
| `\approx` | \approx |
| `\Psi` | \Psi |
| `\Omega` | \Omega |
| `\alpha` | \alpha |
| `\beta` | \beta |
| `\theta` | \theta |
| `\eta` | \eta |

---

## Step-by-Step: Converting One Slide

### Example: "Mathematical Framework" Slide

**LaTeX Source:**
```latex
\begin{frame}{Mathematical Framework}
\textbf{Cognitive Pressure} (determines S2 opportunity):
\begin{equation*}
P(t) = B(t) + C(t) + S(t)
\end{equation*}
where:
\begin{itemize}
    \item $B(t)$: Base pressure (internal stress)
    \item $C(t)$: Conflict pressure (external stress) 
    \item $S(t)$: Social pressure (network effects)
\end{itemize}
\end{frame}
```

**PowerPoint Steps:**
1. Create new slide
2. Add title: "Mathematical Framework"
3. Add text: "Cognitive Pressure (determines S2 opportunity):"
4. Insert equation: `P(t) = B(t) + C(t) + S(t)`
5. Add bullet points:
   - B(t): Base pressure (internal stress)
   - C(t): Conflict pressure (external stress)
   - S(t): Social pressure (network effects)

---

## Tips for Efficient Conversion

1. **Work slide-by-slide**: Don't try to convert everything at once
2. **Use PDF as reference**: Keep PDF open while creating PowerPoint
3. **Batch similar slides**: Do all figure slides together, all text slides together
4. **Save frequently**: PowerPoint can crash with large files
5. **Test on Windows**: Final check on Windows machine before submission

---

## File Organization

### Recommended Structure:
```
AGU_Presentation/
├── AGU2024_Puma_M.pptx          # Main presentation
├── AGU2024_Puma_M.pdf            # PDF backup
├── figures/                      # All figures
│   ├── dimensionless_parameters.png
│   ├── heuristic_decision_making.png
│   └── ...
├── animations/                   # Videos (optional)
│   └── ...
└── source/                       # LaTeX source (reference)
    └── main.tex
```

---

## Final Checklist

Before submitting:
- [ ] All slides are 16:9 aspect ratio
- [ ] All text is minimum 18pt
- [ ] All figures are embedded (not linked)
- [ ] All math equations are readable
- [ ] Tested on Windows machine
- [ ] PDF backup created
- [ ] File named correctly: `AGU2024_Puma_M.pptx`
- [ ] File size < 100 MB




