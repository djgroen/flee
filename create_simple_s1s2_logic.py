#!/usr/bin/env python3
"""
Create a simple, focused figure showing the S1/S2 logic flow.

This figure focuses on:
1. The decision flow
2. Key mathematical components
3. How it integrates with FLEE
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_simple_s1s2_logic():
    """Create a simple, focused S1/S2 logic figure."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('S1/S2 Dual-Process Decision-Making in FLEE', fontsize=20, fontweight='bold')
    
    # 1. Decision Flow (top left)
    create_decision_flow(ax1)
    
    # 2. Mathematical Components (top right)
    create_math_components(ax2)
    
    # 3. Pressure Dynamics (bottom left)
    create_pressure_dynamics(ax3)
    
    # 4. FLEE Integration (bottom right)
    create_flee_integration_simple(ax4)
    
    plt.tight_layout()
    return fig

def create_decision_flow(ax):
    """Create the decision flow diagram."""
    
    ax.set_title('S1/S2 Decision Flow', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Box styles
    start_style = dict(boxstyle="round,pad=0.3", facecolor='lightblue', edgecolor='navy', linewidth=2)
    process_style = dict(boxstyle="round,pad=0.3", facecolor='lightgray', edgecolor='black', linewidth=2)
    s1_style = dict(boxstyle="round,pad=0.3", facecolor='lightcoral', edgecolor='darkred', linewidth=2)
    s2_style = dict(boxstyle="round,pad=0.3", facecolor='lightgreen', edgecolor='darkgreen', linewidth=2)
    
    # Decision flow boxes
    boxes = [
        (4, 9, "Agent at Location\nwith Conflict", start_style),
        (4, 7.5, "Calculate\nCognitive Pressure\nP(t) = B(t) + C(t) + S(t)", process_style),
        (4, 6, "Check S2\nCapability", process_style),
        (2, 4.5, "System 1\nFast & Heuristic\nP(move) = location.movechance", s1_style),
        (6, 4.5, "System 2\nDeliberative\nP(move) = 0.9", s2_style),
        (4, 2.5, "Final Decision\nP(move) = P(S1)×(1-P(S2)) + P(S2)×0.9", process_style),
        (4, 1, "Agent Moves\nor Stays", start_style),
    ]
    
    # Draw boxes
    for x, y, text, style in boxes:
        bbox = FancyBboxPatch((x-1.2, y-0.4), 2.4, 0.8, **style)
        ax.add_patch(bbox)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw arrows
    arrows = [
        ((4, 8.6), (4, 7.9)),  # Start to pressure
        ((4, 7.1), (4, 6.4)),  # Pressure to capability
        ((3.2, 5.6), (2.8, 4.9)),  # Capability to S1
        ((4.8, 5.6), (5.2, 4.9)),  # Capability to S2
        ((2, 4.1), (3.2, 2.9)),  # S1 to final
        ((6, 4.1), (4.8, 2.9)),  # S2 to final
        ((4, 2.1), (4, 1.4)),  # Final to move
    ]
    
    for start, end in arrows:
        arrow = patches.FancyArrowPatch(start, end, 
                                      arrowstyle='->', mutation_scale=20, 
                                      color='black', linewidth=2)
        ax.add_patch(arrow)
    
    # Add decision point
    ax.text(4, 5.2, "S2 Capable?", ha='center', va='center', fontsize=9, 
            bbox=dict(boxstyle="round,pad=0.2", facecolor='yellow', edgecolor='orange'))

def create_math_components(ax):
    """Create mathematical components panel."""
    
    ax.set_title('Mathematical Components', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Mathematical formulas
    formulas = [
        (5, 9, "Cognitive Pressure:", "P(t) = B(t) + C(t) + S(t)", 12),
        (5, 7.5, "Base Pressure:", "B(t) = min(0.4, fc × 0.2 + T(t))", 10),
        (5, 6, "Time Stress:", "T(t) = 0.1 × (1-e^(-t/10)) × e^(-t/50)", 10),
        (5, 4.5, "Conflict Pressure:", "C(t) = min(0.4, I × fc × D(t))", 10),
        (5, 3, "Social Pressure:", "S(t) = min(0.2, fc × 0.1)", 10),
        (5, 1.5, "S2 Activation:", "P(S2) = 1/(1 + e^(-η×(P(t)-θ)))", 10),
    ]
    
    for x, y, label, formula, size in formulas:
        ax.text(x, y, label, ha='center', va='center', fontsize=size, fontweight='bold')
        ax.text(x, y-0.3, formula, ha='center', va='center', fontsize=size-1, 
                fontfamily='monospace', bbox=dict(boxstyle="round,pad=0.2", 
                facecolor='lightyellow', edgecolor='orange'))
    
    # Legend
    legend_text = """
    fc = connectivity factor (0-1)
    I = conflict intensity (0-1)
    D(t) = conflict decay function
    η = eta parameter (steepness)
    θ = S2 threshold
    """
    ax.text(0.5, 0.5, legend_text, ha='left', va='bottom', fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', edgecolor='gray'))

def create_pressure_dynamics(ax):
    """Create pressure dynamics visualization."""
    
    ax.set_title('Cognitive Pressure Dynamics', fontsize=14, fontweight='bold')
    
    # Time range
    t = np.linspace(0, 50, 1000)
    
    # Example parameters
    connectivity = 0.5
    conflict_intensity = 0.8
    
    # Calculate components
    time_stress = 0.1 * (1 - np.exp(-t/10)) * np.exp(-t/50)
    base_pressure = np.minimum(0.4, connectivity * 0.2 + time_stress)
    
    conflict_decay = np.exp(-np.maximum(0, t-5) / 20)  # Conflict starts at t=5
    conflict_pressure = np.minimum(0.4, conflict_intensity * connectivity * conflict_decay)
    
    social_pressure = np.minimum(0.2, connectivity * 0.1) * np.ones_like(t)
    
    total_pressure = base_pressure + conflict_pressure + social_pressure
    
    # Plot
    ax.plot(t, base_pressure, 'b-', linewidth=2, label='Base Pressure')
    ax.plot(t, conflict_pressure, 'r-', linewidth=2, label='Conflict Pressure')
    ax.plot(t, social_pressure, 'g-', linewidth=2, label='Social Pressure')
    ax.plot(t, total_pressure, 'k--', linewidth=3, label='Total Pressure')
    
    # Add S2 threshold line
    threshold = 0.5
    ax.axhline(threshold, color='orange', linestyle=':', linewidth=2, label=f'S2 Threshold = {threshold}')
    
    ax.set_xlabel('Time (timesteps)')
    ax.set_ylabel('Pressure (0-1)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.0)

def create_flee_integration_simple(ax):
    """Create simple FLEE integration diagram."""
    
    ax.set_title('FLEE Integration', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # FLEE integration flow
    boxes = [
        (2, 7, "FLEE Ecosystem.evolve()", 'lightblue'),
        (2, 5.5, "Person.evolve()", 'lightgreen'),
        (2, 4, "calculateMoveChance()", 'lightcoral'),
        (5, 4, "S1/S2 Logic\n(if TwoSystemDecisionMaking > 0)", 'lightyellow'),
        (8, 4, "selectRoute()", 'lightpink'),
        (5, 2, "Agent Movement", 'lightgray'),
        (5, 0.5, "Update Location", 'lightcyan'),
    ]
    
    for x, y, text, color in boxes:
        bbox = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                             boxstyle="round,pad=0.1", 
                             facecolor=color, edgecolor='black')
        ax.add_patch(bbox)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows
    arrows = [
        ((2, 6.7), (2, 5.8)),
        ((2, 5.2), (2, 4.3)),
        ((2.8, 4), (4.2, 4)),
        ((5.8, 4), (7.2, 4)),
        ((8, 3.7), (5.8, 2.3)),
        ((5, 1.7), (5, 0.8)),
    ]
    
    for start, end in arrows:
        arrow = patches.FancyArrowPatch(start, end, 
                                      arrowstyle='->', mutation_scale=15, 
                                      color='black', linewidth=2)
        ax.add_patch(arrow)
    
    # Configuration note
    config_text = """
    YAML Configuration:
    move_rules:
      TwoSystemDecisionMaking: 0.5
      connectivity_mode: "baseline"
      eta: 6.0
      steepness: 6.0
    """
    ax.text(0.5, 1.5, config_text, ha='left', va='top', fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', edgecolor='orange'))

def main():
    """Create and save the simple S1/S2 logic figure."""
    
    print("🎨 Creating Simple S1/S2 Logic Figure...")
    
    # Create the figure
    fig = create_simple_s1s2_logic()
    
    # Save as PNG and PDF
    png_file = "S1S2_Logic_Simple.png"
    pdf_file = "S1S2_Logic_Simple.pdf"
    
    fig.savefig(png_file, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf_file, bbox_inches='tight', facecolor='white')
    
    print(f"✅ Figure saved as:")
    print(f"   📊 {png_file}")
    print(f"   📄 {pdf_file}")
    
    # Show the figure
    plt.show()
    
    return fig

if __name__ == "__main__":
    main()




