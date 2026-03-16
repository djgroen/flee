#!/usr/bin/env python3
"""
Create a comprehensive figure demonstrating the S1/S2 logic in FLEE.

This figure shows:
1. The complete decision-making flow
2. Mathematical formulas for each component
3. How the system integrates with FLEE
4. Key parameters and their effects
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np
import seaborn as sns

# Set style
plt.style.use('default')
sns.set_palette("husl")

def create_s1s2_logic_figure():
    """Create a comprehensive S1/S2 logic demonstration figure."""
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # Main title
    fig.suptitle('S1/S2 Dual-Process Decision-Making in FLEE', 
                 fontsize=24, fontweight='bold', y=0.95)
    
    # Create a grid layout
    gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, 1], width_ratios=[1, 1, 1],
                         hspace=0.3, wspace=0.3)
    
    # 1. Main Decision Flow (top row, spans 2 columns)
    ax1 = fig.add_subplot(gs[0, :2])
    create_decision_flow_diagram(ax1)
    
    # 2. Mathematical Framework (top right)
    ax2 = fig.add_subplot(gs[0, 2])
    create_mathematical_framework(ax2)
    
    # 3. Cognitive Pressure Components (second row, left)
    ax3 = fig.add_subplot(gs[1, 0])
    create_pressure_components(ax3)
    
    # 4. S2 Activation Logic (second row, middle)
    ax4 = fig.add_subplot(gs[1, 1])
    create_s2_activation_logic(ax4)
    
    # 5. Move Probability Calculation (second row, right)
    ax5 = fig.add_subplot(gs[1, 2])
    create_move_probability_logic(ax5)
    
    # 6. Parameter Effects (third row, spans all columns)
    ax6 = fig.add_subplot(gs[2, :])
    create_parameter_effects(ax6)
    
    # 7. Integration with FLEE (bottom row, spans all columns)
    ax7 = fig.add_subplot(gs[3, :])
    create_flee_integration(ax7)
    
    plt.tight_layout()
    return fig

def create_decision_flow_diagram(ax):
    """Create the main decision flow diagram."""
    
    ax.set_title('S1/S2 Decision Flow in FLEE', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Define box properties
    box_style = dict(boxstyle="round,pad=0.3", facecolor='lightblue', edgecolor='navy', linewidth=2)
    s1_style = dict(boxstyle="round,pad=0.3", facecolor='lightcoral', edgecolor='darkred', linewidth=2)
    s2_style = dict(boxstyle="round,pad=0.3", facecolor='lightgreen', edgecolor='darkgreen', linewidth=2)
    
    # Main flow boxes
    boxes = [
        (1, 7, "Agent at Location\nwith Conflict", box_style),
        (1, 5.5, "Calculate\nCognitive Pressure", box_style),
        (1, 4, "Check S2\nCapability", box_style),
        (3, 4, "S2 Capable?\nYes", s2_style),
        (5, 4, "Calculate S2\nActivation Prob", s2_style),
        (7, 4, "S2 Active?\nYes", s2_style),
        (7, 2, "System 2:\nDeliberative\nRoute Planning", s2_style),
        (3, 2, "System 1:\nHeuristic\nQuick Decision", s1_style),
        (5, 0.5, "Calculate Final\nMove Probability", box_style)
    ]
    
    # Draw boxes
    for x, y, text, style in boxes:
        bbox = FancyBboxPatch((x-0.8, y-0.4), 1.6, 0.8, **style)
        ax.add_patch(bbox)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw arrows
    arrows = [
        ((1, 6.6), (1, 5.9)),  # Start to pressure
        ((1, 5.1), (1, 4.4)),  # Pressure to capability
        ((1.8, 4), (2.2, 4)),  # Capability to S2 capable
        ((3.8, 4), (4.2, 4)),  # S2 capable to activation
        ((5.8, 4), (6.2, 4)),  # Activation to S2 active
        ((7, 3.6), (7, 2.4)),  # S2 active to S2 decision
        ((1.8, 4), (2.2, 2)),  # Capability to S1 decision
        ((3, 1.6), (4.2, 0.9)),  # S1 to final
        ((7, 1.6), (5.8, 0.9)),  # S2 to final
    ]
    
    for start, end in arrows:
        arrow = patches.FancyArrowPatch(start, end, 
                                      arrowstyle='->', mutation_scale=20, 
                                      color='black', linewidth=2)
        ax.add_patch(arrow)
    
    # Add decision points
    ax.text(1, 3.2, "No", ha='center', va='center', fontsize=9, 
            bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='gray'))
    ax.text(7, 3.2, "No", ha='center', va='center', fontsize=9,
            bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='gray'))

def create_mathematical_framework(ax):
    """Create the mathematical framework panel."""
    
    ax.set_title('Mathematical Framework', fontsize=14, fontweight='bold', pad=15)
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
        (5, 1.5, "S2 Activation:", "P(S2) = σ(η × (P(t) - θ))", 10),
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
    σ = sigmoid function
    """
    ax.text(0.5, 0.5, legend_text, ha='left', va='bottom', fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', edgecolor='gray'))

def create_pressure_components(ax):
    """Create the pressure components visualization."""
    
    ax.set_title('Cognitive Pressure Components', fontsize=14, fontweight='bold')
    
    # Time range
    t = np.linspace(0, 50, 1000)
    
    # Calculate components
    connectivity = 0.5  # Example value
    conflict_intensity = 0.8  # Example value
    
    # Base pressure
    time_stress = 0.1 * (1 - np.exp(-t/10)) * np.exp(-t/50)
    base_pressure = np.minimum(0.4, connectivity * 0.2 + time_stress)
    
    # Conflict pressure
    conflict_decay = np.exp(-np.maximum(0, t-5) / 20)  # Conflict starts at t=5
    conflict_pressure = np.minimum(0.4, conflict_intensity * connectivity * conflict_decay)
    
    # Social pressure
    social_pressure = np.minimum(0.2, connectivity * 0.1) * np.ones_like(t)
    
    # Total pressure
    total_pressure = base_pressure + conflict_pressure + social_pressure
    
    # Plot
    ax.plot(t, base_pressure, 'b-', linewidth=2, label='Base Pressure')
    ax.plot(t, conflict_pressure, 'r-', linewidth=2, label='Conflict Pressure')
    ax.plot(t, social_pressure, 'g-', linewidth=2, label='Social Pressure')
    ax.plot(t, total_pressure, 'k--', linewidth=3, label='Total Pressure')
    
    ax.set_xlabel('Time (timesteps)')
    ax.set_ylabel('Pressure (0-1)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.0)

def create_s2_activation_logic(ax):
    """Create the S2 activation logic visualization."""
    
    ax.set_title('S2 Activation Probability', fontsize=14, fontweight='bold')
    
    # Pressure range
    pressure = np.linspace(0, 1, 100)
    
    # Different eta values
    eta_values = [2, 4, 6, 8]
    threshold = 0.5
    
    for eta in eta_values:
        s2_prob = 1 / (1 + np.exp(-eta * (pressure - threshold)))
        ax.plot(pressure, s2_prob, linewidth=2, label=f'η = {eta}')
    
    ax.axvline(threshold, color='red', linestyle='--', alpha=0.7, label=f'Threshold = {threshold}')
    ax.axhline(0.5, color='gray', linestyle=':', alpha=0.7)
    
    ax.set_xlabel('Cognitive Pressure')
    ax.set_ylabel('S2 Activation Probability')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

def create_move_probability_logic(ax):
    """Create the move probability calculation logic."""
    
    ax.set_title('Move Probability Calculation', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Boxes for move probability logic
    boxes = [
        (5, 8, "S1 Move Probability\n(Location-based)", 'lightcoral'),
        (5, 6, "S2 Move Probability\n(High, ~0.9)", 'lightgreen'),
        (5, 4, "S2 Activation\nProbability", 'lightblue'),
        (5, 2, "Final Move Probability\nP(move) = P(S1)×(1-P(S2)) + P(S2)×P(S2)", 'lightyellow'),
    ]
    
    for x, y, text, color in boxes:
        bbox = FancyBboxPatch((x-1.5, y-0.4), 3, 0.8, 
                             boxstyle="round,pad=0.2", 
                             facecolor=color, edgecolor='black')
        ax.add_patch(bbox)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Arrows
    arrows = [
        ((5, 7.6), (5, 6.4)),
        ((5, 5.6), (5, 4.4)),
        ((5, 3.6), (5, 2.4)),
    ]
    
    for start, end in arrows:
        arrow = patches.FancyArrowPatch(start, end, 
                                      arrowstyle='->', mutation_scale=15, 
                                      color='black', linewidth=2)
        ax.add_patch(arrow)

def create_parameter_effects(ax):
    """Create parameter effects visualization."""
    
    ax.set_title('Key Parameter Effects', fontsize=16, fontweight='bold')
    
    # Create subplots for different parameters
    sub_axes = []
    for i in range(4):
        sub_ax = plt.subplot2grid((1, 4), (0, i), fig=ax.figure)
        sub_axes.append(sub_ax)
    
    # 1. Eta effect
    pressure = np.linspace(0, 1, 100)
    eta_values = [2, 4, 6, 8]
    threshold = 0.5
    
    for eta in eta_values:
        s2_prob = 1 / (1 + np.exp(-eta * (pressure - threshold)))
        sub_axes[0].plot(pressure, s2_prob, linewidth=2, label=f'η={eta}')
    
    sub_axes[0].set_title('Eta (Steepness)')
    sub_axes[0].set_xlabel('Pressure')
    sub_axes[0].set_ylabel('S2 Probability')
    sub_axes[0].legend()
    sub_axes[0].grid(True, alpha=0.3)
    
    # 2. Threshold effect
    eta = 6
    thresholds = [0.3, 0.5, 0.7]
    
    for thresh in thresholds:
        s2_prob = 1 / (1 + np.exp(-eta * (pressure - thresh)))
        sub_axes[1].plot(pressure, s2_prob, linewidth=2, label=f'θ={thresh}')
    
    sub_axes[1].set_title('Threshold')
    sub_axes[1].set_xlabel('Pressure')
    sub_axes[1].set_ylabel('S2 Probability')
    sub_axes[1].legend()
    sub_axes[1].grid(True, alpha=0.3)
    
    # 3. Connectivity effect
    t = np.linspace(0, 30, 100)
    connectivity_values = [0.2, 0.5, 0.8]
    
    for conn in connectivity_values:
        time_stress = 0.1 * (1 - np.exp(-t/10)) * np.exp(-t/50)
        base_pressure = np.minimum(0.4, conn * 0.2 + time_stress)
        sub_axes[2].plot(t, base_pressure, linewidth=2, label=f'fc={conn}')
    
    sub_axes[2].set_title('Connectivity Factor')
    sub_axes[2].set_xlabel('Time')
    sub_axes[2].set_ylabel('Base Pressure')
    sub_axes[2].legend()
    sub_axes[2].grid(True, alpha=0.3)
    
    # 4. Conflict intensity effect
    conflict_intensity = np.linspace(0, 1, 100)
    connectivity = 0.5
    conflict_pressure = np.minimum(0.4, conflict_intensity * connectivity)
    
    sub_axes[3].plot(conflict_intensity, conflict_pressure, 'r-', linewidth=2)
    sub_axes[3].set_title('Conflict Intensity')
    sub_axes[3].set_xlabel('Conflict Intensity')
    sub_axes[3].set_ylabel('Conflict Pressure')
    sub_axes[3].grid(True, alpha=0.3)
    
    # Hide the main axis
    ax.axis('off')

def create_flee_integration(ax):
    """Create the FLEE integration diagram."""
    
    ax.set_title('Integration with FLEE Framework', fontsize=16, fontweight='bold')
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # FLEE integration flow
    boxes = [
        (1, 5, "FLEE Ecosystem.evolve()", 'lightblue'),
        (2, 4, "Person.evolve()", 'lightgreen'),
        (3, 3, "calculateMoveChance()", 'lightcoral'),
        (5, 3, "S1/S2 Logic\n(if enabled)", 'lightyellow'),
        (7, 3, "selectRoute()", 'lightpink'),
        (9, 3, "Agent Movement", 'lightgray'),
        (11, 3, "Update Location", 'lightcyan'),
    ]
    
    for x, y, text, color in boxes:
        bbox = FancyBboxPatch((x-0.6, y-0.3), 1.2, 0.6, 
                             boxstyle="round,pad=0.1", 
                             facecolor=color, edgecolor='black')
        ax.add_patch(bbox)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows
    arrows = [
        ((1.6, 4.7), (1.4, 4.3)),
        ((2.6, 3.7), (2.4, 3.3)),
        ((3.6, 3), (4.4, 3)),
        ((5.6, 3), (6.4, 3)),
        ((7.6, 3), (8.4, 3)),
        ((9.6, 3), (10.4, 3)),
    ]
    
    for start, end in arrows:
        arrow = patches.FancyArrowPatch(start, end, 
                                      arrowstyle='->', mutation_scale=15, 
                                      color='black', linewidth=2)
        ax.add_patch(arrow)
    
    # Configuration note
    config_text = """
    Configuration in YAML:
    move_rules:
      TwoSystemDecisionMaking: 0.5  # Enable S1/S2
      connectivity_mode: "baseline"  # or "diminishing"
      soft_capability: false  # or true for soft gates
      eta: 6.0  # S2 activation steepness
      steepness: 6.0  # General steepness
    """
    ax.text(1, 1.5, config_text, ha='left', va='top', fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', edgecolor='orange'))

def main():
    """Create and save the S1/S2 logic figure."""
    
    print("🎨 Creating S1/S2 Logic Demonstration Figure...")
    
    # Create the figure
    fig = create_s1s2_logic_figure()
    
    # Save as PNG and PDF
    png_file = "S1S2_Logic_Demonstration.png"
    pdf_file = "S1S2_Logic_Demonstration.pdf"
    
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




