# AGU PowerPoint Conversion Guide

## Current Format
- **Source**: LaTeX Beamer (`main.tex`)
- **Aspect Ratio**: 16:9 (already correct for AGU)
- **Target**: PowerPoint (.pptx) for AGU presentation

## Conversion Checklist

### ✅ 1. Font Compatibility
- **Current**: LaTeX default fonts (Computer Modern)
- **PowerPoint**: Use standard fonts (Arial, Calibri, Times New Roman)
- **Action**: Replace LaTeX math fonts with PowerPoint-compatible equivalents
- **Math**: Use PowerPoint's Equation Editor or MathType

### ✅ 2. Image & Video
- **Current**: PNG figures in `refugee_simulation_results/figures/`
- **Format**: PNG (300 DPI) - ✅ PowerPoint compatible
- **Videos**: MP4 animations - ✅ PowerPoint compatible
- **Action**: 
  - Embed images directly (not linked)
  - Test video playback on Windows
  - Ensure all images are high resolution (300 DPI)

### ✅ 3. Animations & Transitions
- **Current**: Beamer overlays and transitions
- **PowerPoint**: 
  - Use "Appear" animations for bullet points
  - Use "Fade" transitions between slides
  - Test all animations work on Windows

### ✅ 4. Layout and Slide Size
- **Current**: 16:9 aspect ratio (correct)
- **AGU Standard**: 16:9 (1920×1080 or 10×5.625 inches)
- **Action**: 
  - Set PowerPoint slide size to 16:9
  - Ensure all content fits within safe margins
  - Test on Windows to verify layout

### ✅ 5. PDF Backup
- **Action**: 
  - Export Beamer to PDF first (backup)
  - Test PDF in Adobe Reader
  - Use PDF as reference during conversion

### ✅ 6. Final Check
- [ ] All fonts render correctly on Windows
- [ ] All images display properly
- [ ] Videos play correctly
- [ ] Animations work as expected
- [ ] Slide size is 16:9
- [ ] Math equations are readable
- [ ] Colors are consistent
- [ ] No broken links

## Conversion Methods

### Method 1: Manual Recreation (Recommended for AGU)
**Pros**: Full control, perfect formatting, AGU-compliant
**Cons**: Time-consuming

**Steps**:
1. Compile Beamer to PDF (reference)
2. Create new PowerPoint presentation (16:9)
3. Copy content slide-by-slide
4. Recreate figures/tables in PowerPoint
5. Add animations manually

### Method 2: PDF to PowerPoint Conversion
**Pros**: Faster, preserves layout
**Cons**: May need manual fixes

**Tools**:
- Adobe Acrobat Pro (Export to PowerPoint)
- Online converters (PDF2PPT, etc.)
- Note: Math may need manual recreation

### Method 3: Pandoc Conversion (if available)
**Pros**: Automated, preserves structure
**Cons**: May need post-processing

**Command** (if pandoc installed):
```bash
pandoc main.tex -o presentation.pptx --slide-level=2
```

## AGU-Specific Requirements

### Slide Format
- **Size**: 16:9 (1920×1080 pixels)
- **Font**: Minimum 18pt for body text
- **Title**: 24-36pt
- **Margins**: Safe area (avoid edges)

### Content Guidelines
- **10-minute presentation**: ~10-12 slides
- **Key points**: 3-5 bullet points per slide
- **Figures**: High resolution, clear labels
- **Animations**: Simple, professional

### File Naming
- **Format**: `AGU2024_LastName_FirstInitial.pptx`
- **Example**: `AGU2024_Puma_M.pptx`

## Key Files to Include

### Figures (PNG, 300 DPI)
- `dimensionless_parameters.png`
- `heuristic_decision_making.png`
- `run_Nearest_Border_*_network.png`
- `run_Nearest_Border_*_decisions.png`
- `run_Multiple_Routes_*_network.png`
- `run_Multiple_Routes_*_decisions.png`
- `run_Social_Connections_*_network.png`
- `run_Social_Connections_*_decisions.png`
- `run_Context_Transition_*_network.png`
- `run_Context_Transition_*_decisions.png`

### Videos (MP4, optional)
- `animations/Nearest_Border_*.mp4`
- `animations/Multiple_Routes_*.mp4`
- `animations/Social_Connections_*.mp4`
- `animations/Context_Transition_*.mp4`

## Quick Start: Manual Conversion Template

### Slide 1: Title Slide
```
Title: Context-Dependent Decision-Making in Crisis
Subtitle: System 1 vs System 2 Processing in Forced Displacement
Author: Michael Puma
Institution: Columbia University Climate School
```

### Slide Structure (10-12 slides for 10 minutes)
1. Title
2. Outline
3. The Question
4. Dual-Process Theory
5. Our Model
6. Implementation
7. Results (4 slides: scenarios)
8. Dimensionless Parameters
9. South Sudan Application
10. Humanitarian Implications
11. Contributions
12. Conclusion

## Math Equations in PowerPoint

### Option 1: PowerPoint Equation Editor
- Insert → Equation
- Type LaTeX-style: `P_{S2} = \Psi \times \Omega`
- PowerPoint will convert automatically

### Option 2: MathType (if available)
- Better LaTeX compatibility
- Professional formatting

### Option 3: Screenshot from PDF
- Export equations as images
- Insert as pictures
- Ensure high resolution

## Color Scheme
- **Current Beamer**: Madrid theme (blue/white)
- **PowerPoint**: Use similar color scheme
- **Recommendation**: 
  - Background: White or light blue
  - Text: Dark blue or black
  - Accents: Blue (#3498db) for consistency

## Testing Checklist
- [ ] Open on Windows machine
- [ ] Test all fonts render
- [ ] Verify all images display
- [ ] Check video playback
- [ ] Test animations
- [ ] Verify slide size (16:9)
- [ ] Check math readability
- [ ] Print preview (if needed)
- [ ] Test on presentation computer (if possible)




