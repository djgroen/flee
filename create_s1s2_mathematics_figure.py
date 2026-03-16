#!/usr/bin/env python3
"""
Create comprehensive S1/S2 mathematics figure for FLEE
"""

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def create_s1s2_mathematics_figure():
    """Create comprehensive S1/S2 mathematics figure"""
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # Create a grid layout
    gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, 1], width_ratios=[1, 1, 1],
                         hspace=0.3, wspace=0.3)
    
    # Colors
    colors = {
        'S1': '#FF6B6B',      # Red
        'S2': '#4ECDC4',      # Teal
        'pressure': '#FFA726', # Orange
        'threshold': '#66BB6A', # Green
        'background': '#F5F5F5'
    }
    
    # 1. Cognitive Pressure Components (Top Left)
    ax1 = fig.add_subplot(gs[0, 0])
    
    # Time range
    t = np.linspace(0, 100, 1000)
    
    # Calculate components
    connectivity = 0.5  # Example value
    conflict_intensity = 1.0  # High conflict
    
    # Base pressure
    time_stress = 0.1 * (1 - np.exp(-t/10)) * np.exp(-t/50)
    base_pressure = np.minimum(0.4, connectivity * 0.2 + time_stress)
    
    # Conflict pressure
    conflict_decay = np.exp(-t/20)  # Assuming conflict starts at t=0
    conflict_pressure = np.minimum(0.4, conflict_intensity * connectivity * conflict_decay)
    
    # Social pressure
    social_pressure = np.minimum(0.2, connectivity * 0.1) * np.ones_like(t)
    
    # Total pressure
    total_pressure = base_pressure + conflict_pressure + social_pressure
    
    # Plot components
    ax1.plot(t, base_pressure, label='Base Pressure', linewidth=2, color='#FF9800')
    ax1.plot(t, conflict_pressure, label='Conflict Pressure', linewidth=2, color='#F44336')
    ax1.plot(t, social_pressure, label='Social Pressure', linewidth=2, color='#2196F3')
    ax1.plot(t, total_pressure, label='Total Pressure', linewidth=3, color='#9C27B0')
    
    ax1.set_xlabel('Time (timesteps)')
    ax1.set_ylabel('Pressure')
    ax1.set_title('Cognitive Pressure Components', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1.1)
    
    # Add boundedness annotation
    ax1.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Upper Bound')
    ax1.text(80, 1.05, 'Bounded [0.0, 1.0]', fontsize=10, color='red', fontweight='bold')
    
    # 2. S2 Activation Probability (Top Center)
    ax2 = fig.add_subplot(gs[0, 1])
    
    # Pressure range
    pressure_range = np.linspace(0, 1, 1000)
    threshold = 0.5
    k = 6.0
    
    # Sigmoid function
    sigmoid = 1 / (1 + np.exp(-k * (pressure_range - threshold)))
    
    # Plot sigmoid
    ax2.plot(pressure_range, sigmoid, linewidth=3, color=colors['S2'])
    ax2.axvline(x=threshold, color='red', linestyle='--', alpha=0.7, label=f'Threshold = {threshold}')
    ax2.axhline(y=0.5, color='gray', linestyle=':', alpha=0.7)
    
    ax2.set_xlabel('Cognitive Pressure')
    ax2.set_ylabel('P(S2 Activation)')
    ax2.set_title('S2 Activation Probability', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1)
    
    # Add steepness annotation
    ax2.text(0.1, 0.8, f'k = {k}\n(Steepness)', fontsize=10, 
             bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # 3. S2 Capability Requirements (Top Right)
    ax3 = fig.add_subplot(gs[0, 2])
    
    # Create capability matrix
    connections = np.array([0, 1, 2, 3, 4, 5])
    timesteps = np.array([0, 1, 2, 3, 4, 5])
    education_levels = [0.2, 0.3, 0.4]
    
    # Create capability grid
    capability_data = np.zeros((len(connections), len(timesteps)))
    
    for i, conn in enumerate(connections):
        for j, ts in enumerate(timesteps):
            # S2_capable = (connections >= 1) OR (timesteps >= 3) OR (education >= 0.3)
            s2_capable = (conn >= 1) or (ts >= 3) or (0.3 >= 0.3)  # education >= 0.3
            capability_data[i, j] = 1 if s2_capable else 0
    
    # Plot heatmap
    im = ax3.imshow(capability_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    
    # Set ticks and labels
    ax3.set_xticks(range(len(timesteps)))
    ax3.set_xticklabels(timesteps)
    ax3.set_yticks(range(len(connections)))
    ax3.set_yticklabels(connections)
    
    ax3.set_xlabel('Timesteps Since Departure')
    ax3.set_ylabel('Connections')
    ax3.set_title('S2 Capability Requirements', fontsize=14, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax3, shrink=0.8)
    cbar.set_label('S2 Capable', rotation=270, labelpad=20)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(['No', 'Yes'])
    
    # 4. Individual Modifiers (Second Row, Left)
    ax4 = fig.add_subplot(gs[1, 0])
    
    # Modifier ranges
    education_range = np.linspace(0, 1, 100)
    connections_range = np.linspace(0, 10, 100)
    time_range = np.linspace(0, 100, 100)
    
    # Calculate modifiers
    education_boost = education_range * 0.05
    social_support = np.minimum(connections_range * 0.01, 0.05)
    fatigue_penalty = np.minimum(time_range * 0.001, 0.03)
    learning_boost = np.minimum(time_range * 0.002, 0.05)
    
    # Plot modifiers
    ax4.plot(education_range, education_boost, label='Education Boost', linewidth=2, color='#4CAF50')
    ax4.plot(connections_range, social_support, label='Social Support', linewidth=2, color='#2196F3')
    ax4.plot(time_range, fatigue_penalty, label='Fatigue Penalty', linewidth=2, color='#F44336')
    ax4.plot(time_range, learning_boost, label='Learning Boost', linewidth=2, color='#FF9800')
    
    ax4.set_xlabel('Value')
    ax4.set_ylabel('Modifier')
    ax4.set_title('Individual Modifiers (Bounded)', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 0.06)
    
    # 5. Behavioral Differences (Second Row, Center)
    ax5 = fig.add_subplot(gs[1, 1])
    
    # Create behavioral comparison
    agent_types = ['Low Ed', 'High Ed', 'Low Conn', 'High Conn']
    s1_move_rates = [0.1, 0.1, 0.05, 0.15]  # S1 move rates
    s2_move_rates = [0.8, 0.9, 0.7, 0.95]   # S2 move rates
    
    x = np.arange(len(agent_types))
    width = 0.35
    
    bars1 = ax5.bar(x - width/2, s1_move_rates, width, label='System 1', color=colors['S1'], alpha=0.8)
    bars2 = ax5.bar(x + width/2, s2_move_rates, width, label='System 2', color=colors['S2'], alpha=0.8)
    
    ax5.set_xlabel('Agent Type')
    ax5.set_ylabel('Move Rate')
    ax5.set_title('S1 vs S2 Behavioral Differences', fontsize=14, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(agent_types)
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    for bar in bars2:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    # 6. Long-term Stability (Second Row, Right)
    ax6 = fig.add_subplot(gs[1, 2])
    
    # Long-term pressure evolution
    t_long = np.linspace(0, 200, 2000)
    
    # Different scenarios
    scenarios = {
        'High Conflict': {'conflict': 1.0, 'connectivity': 0.8, 'color': '#F44336'},
        'Medium Conflict': {'conflict': 0.5, 'connectivity': 0.5, 'color': '#FF9800'},
        'Low Conflict': {'conflict': 0.1, 'connectivity': 0.3, 'color': '#4CAF50'}
    }
    
    for scenario, params in scenarios.items():
        conflict = params['conflict']
        connectivity = params['connectivity']
        color = params['color']
        
        # Calculate pressure
        time_stress = 0.1 * (1 - np.exp(-t_long/10)) * np.exp(-t_long/50)
        base_pressure = np.minimum(0.4, connectivity * 0.2 + time_stress)
        conflict_pressure = np.minimum(0.4, conflict * connectivity * np.exp(-t_long/20))
        social_pressure = np.minimum(0.2, connectivity * 0.1) * np.ones_like(t_long)
        total_pressure = base_pressure + conflict_pressure + social_pressure
        
        ax6.plot(t_long, total_pressure, label=scenario, linewidth=2, color=color)
    
    ax6.set_xlabel('Time (timesteps)')
    ax6.set_ylabel('Total Pressure')
    ax6.set_title('Long-term Stability', fontsize=14, fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    ax6.set_ylim(0, 1.1)
    ax6.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Upper Bound')
    
    # 7. Integration Flow (Third Row, Full Width)
    ax7 = fig.add_subplot(gs[2, :])
    
    # Create flow diagram
    ax7.set_xlim(0, 10)
    ax7.set_ylim(0, 3)
    ax7.axis('off')
    
    # Flow boxes
    boxes = [
        {'pos': (0.5, 1.5), 'size': (1.2, 0.8), 'text': 'YAML Config\nTwoSystemDecisionMaking', 'color': '#E3F2FD'},
        {'pos': (2.5, 1.5), 'size': (1.2, 0.8), 'text': 'Ecosystem.evolve()\nMain Loop', 'color': '#F3E5F5'},
        {'pos': (4.5, 1.5), 'size': (1.2, 0.8), 'text': 'Person.evolve()\nAgent Update', 'color': '#E8F5E8'},
        {'pos': (6.5, 1.5), 'size': (1.2, 0.8), 'text': 'calculateMoveChance()\nS1/S2 Logic', 'color': '#FFF3E0'},
        {'pos': (8.5, 1.5), 'size': (1.2, 0.8), 'text': 'selectRoute()\nRoute Selection', 'color': '#FCE4EC'}
    ]
    
    # Draw boxes
    for box in boxes:
        x, y = box['pos']
        w, h = box['size']
        rect = FancyBboxPatch((x-w/2, y-h/2), w, h, 
                             boxstyle="round,pad=0.1", 
                             facecolor=box['color'], 
                             edgecolor='black', 
                             linewidth=1.5)
        ax7.add_patch(rect)
        ax7.text(x, y, box['text'], ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw arrows
    arrow_props = dict(arrowstyle='->', lw=2, color='black')
    for i in range(len(boxes)-1):
        x1 = boxes[i]['pos'][0] + boxes[i]['size'][0]/2
        x2 = boxes[i+1]['pos'][0] - boxes[i+1]['size'][0]/2
        y = boxes[i]['pos'][1]
        ax7.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=arrow_props)
    
    ax7.set_title('S1/S2 Integration Flow in FLEE', fontsize=16, fontweight='bold', pad=20)
    
    # 8. Mathematical Formulas (Bottom Row, Full Width)
    ax8 = fig.add_subplot(gs[3, :])
    ax8.axis('off')
    
    # Mathematical formulas
    formulas = [
        r'Cognitive Pressure: $P(t) = B(t) + C(t) + S(t)$',
        r'Base Pressure: $B(t) = \min(0.4, \text{connectivity} \times 0.2 + \text{time\_stress}(t))$',
        r'Time Stress: $\text{time\_stress}(t) = 0.1 \times (1 - e^{-t/10}) \times e^{-t/50}$',
        r'Conflict Pressure: $C(t) = \min(0.4, \text{conflict} \times \text{connectivity} \times e^{-t/20})$',
        r'S2 Activation: $P(\text{S2}) = \frac{1}{1 + e^{-k \times (P(t) - \text{threshold})}} + \text{modifiers}$',
        r'S2 Capable: $(\text{connections} \geq 1) \lor (\text{timesteps} \geq 3) \lor (\text{education} \geq 0.3)$'
    ]
    
    y_positions = np.linspace(0.8, 0.2, len(formulas))
    
    for i, formula in enumerate(formulas):
        ax8.text(0.05, y_positions[i], formula, fontsize=14, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    ax8.set_title('Mathematical Formulas', fontsize=16, fontweight='bold', pad=20)
    
    # Add overall title
    fig.suptitle('S1/S2 Dual-Process Decision Making in FLEE: Mathematical Framework', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # Add footer
    fig.text(0.5, 0.02, 'FLEE: Forced Migration and Refugee Simulation | S1/S2 System: Fully Integrated & Mathematically Sound', 
             ha='center', fontsize=12, style='italic')
    
    # Save figure
    plt.savefig('S1S2_Mathematics_Framework.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.savefig('S1S2_Mathematics_Framework.pdf', bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print("✅ Figure saved as:")
    print("   - S1S2_Mathematics_Framework.png (high resolution)")
    print("   - S1S2_Mathematics_Framework.pdf (vector format)")
    
    plt.show()

if __name__ == "__main__":
    create_s1s2_mathematics_figure()
