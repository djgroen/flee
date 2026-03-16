#!/usr/bin/env python3
"""
Extract slide content from main.tex for PowerPoint conversion

This script extracts text content, figure references, and slide structure
to help with manual PowerPoint conversion.
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_slides(tex_file):
    """Extract slide content from Beamer presentation."""
    with open(tex_file, 'r') as f:
        content = f.read()
    
    slides = []
    sections = []
    
    # Find all sections
    section_pattern = r'\\section\{([^}]+)\}'
    for match in re.finditer(section_pattern, content):
        sections.append(match.group(1))
    
    # Find all frames
    frame_pattern = r'\\begin\{frame\}(?:\{([^}]+)\})?(.*?)\\end\{frame\}'
    for match in re.finditer(frame_pattern, content, re.DOTALL):
        title = match.group(1) if match.group(1) else 'Untitled'
        frame_content = match.group(2)
        
        # Extract figure references
        figures = re.findall(r'\\includegraphics(?:\[[^\]]+\])?\{([^}]+)\}', frame_content)
        
        # Extract text content (remove LaTeX commands)
        text_content = frame_content
        # Remove LaTeX commands but keep text
        text_content = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})*', '', text_content)
        text_content = re.sub(r'\{|\}', '', text_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        slides.append({
            'title': title,
            'content': text_content[:200] + '...' if len(text_content) > 200 else text_content,
            'figures': figures,
            'has_math': '\\(' in frame_content or '\\[' in frame_content or '\\begin{equation' in frame_content
        })
    
    return sections, slides

def generate_powerpoint_outline(tex_file='main.tex'):
    """Generate PowerPoint conversion outline."""
    sections, slides = extract_slides(tex_file)
    
    print("=" * 70)
    print("POWERPOINT CONVERSION OUTLINE")
    print("=" * 70)
    print()
    
    current_section = None
    slide_num = 1
    
    for slide in slides:
        # Check if this slide starts a new section
        section_idx = None
        for i, section in enumerate(sections):
            if section.lower() in slide['title'].lower():
                section_idx = i
                break
        
        if section_idx is not None and sections[section_idx] != current_section:
            current_section = sections[section_idx]
            print()
            print("=" * 70)
            print(f"SECTION: {current_section}")
            print("=" * 70)
            print()
        
        print(f"Slide {slide_num}: {slide['title']}")
        print(f"  Content preview: {slide['content'][:100]}...")
        
        if slide['figures']:
            print(f"  Figures ({len(slide['figures'])}):")
            for fig in slide['figures']:
                print(f"    - {fig}")
        
        if slide['has_math']:
            print("  ⚠️  Contains math equations (needs manual conversion)")
        
        print()
        slide_num += 1
    
    print("=" * 70)
    print(f"Total slides: {len(slides)}")
    print("=" * 70)

if __name__ == "__main__":
    generate_powerpoint_outline()




