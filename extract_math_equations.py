#!/usr/bin/env python3
"""
Extract all math equations from main.tex for PowerPoint conversion

Outputs equations in formats suitable for:
1. PowerPoint Equation Editor (LaTeX-style input)
2. MathType (if available)
3. Screenshot reference (with slide context)
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_equations(tex_file='main.tex'):
    """Extract all math equations with context."""
    with open(tex_file, 'r') as f:
        content = f.read()
    
    equations = []
    
    # Find frames and their content
    frame_pattern = r'\\begin\{frame\}(?:\{([^}]+)\})?(.*?)\\end\{frame\}'
    
    for match in re.finditer(frame_pattern, content, re.DOTALL):
        title = match.group(1) if match.group(1) else 'Untitled'
        frame_content = match.group(2)
        
        # Find inline math: $ ... $ or \( ... \)
        inline_matches = re.finditer(r'\$([^\$]+)\$|\\\(([^\)]+)\\\)', frame_content)
        for m in inline_matches:
            eq = m.group(1) or m.group(2)
            if eq and len(eq.strip()) > 0:
                equations.append({
                    'type': 'inline',
                    'equation': eq.strip(),
                    'slide': title,
                    'raw': m.group(0)
                })
        
        # Find display math: \[ ... \], $$ ... $$, or \begin{equation}
        display_patterns = [
            (r'\$\$([^\$]+)\$\$', 'display'),
            (r'\\\[([^\]]+)\\\]', 'display'),
            (r'\\begin\{equation\*\}(.*?)\\end\{equation\*\}', 'display'),
            (r'\\begin\{equation\}(.*?)\\end\{equation\}', 'display'),
        ]
        
        for pattern, eq_type in display_patterns:
            for m in re.finditer(pattern, frame_content, re.DOTALL):
                eq = m.group(1)
                if eq and len(eq.strip()) > 0:
                    equations.append({
                        'type': eq_type,
                        'equation': eq.strip(),
                        'slide': title,
                        'raw': m.group(0)
                    })
    
    return equations

def clean_equation(eq):
    """Clean LaTeX equation for PowerPoint input."""
    # Remove extra whitespace
    eq = ' '.join(eq.split())
    # Keep LaTeX commands (PowerPoint will convert)
    return eq

def generate_equation_list():
    """Generate formatted equation list."""
    equations = extract_equations()
    
    print("=" * 70)
    print("MATH EQUATIONS FOR POWERPOINT")
    print("=" * 70)
    print()
    
    # Group by slide
    by_slide = defaultdict(list)
    for eq in equations:
        by_slide[eq['slide']].append(eq)
    
    for slide_title, slide_eqs in by_slide.items():
        print(f"\n{'=' * 70}")
        print(f"SLIDE: {slide_title}")
        print(f"{'=' * 70}\n")
        
        for i, eq in enumerate(slide_eqs, 1):
            eq_type = eq['type'].upper()
            clean_eq = clean_equation(eq['equation'])
            
            print(f"{eq_type} EQUATION {i}:")
            print(f"  {clean_eq}")
            print()
            print("PowerPoint Equation Editor input:")
            print(f"  {clean_eq}")
            print()
            print("LaTeX original:")
            print(f"  {eq['raw'][:100]}...")
            print()
            print("-" * 70)
            print()
    
    print("=" * 70)
    print(f"Total equations: {len(equations)}")
    print("=" * 70)

if __name__ == "__main__":
    generate_equation_list()




