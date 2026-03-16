# Dimensionless Parameters Analysis Guide

## Overview

This document explains the dimensionless parameters tracked in the S1/S2 evacuation model and how they evolve over time. Dimensionless parameters are essential for:
- **Cross-scenario comparison**: Compare results across different conflict scales
- **Scale invariance**: Generalize findings to different population sizes
- **Universal patterns**: Identify fundamental cognitive constants
- **Model validation**: Verify mathematical consistency (e.g., P_S2 = Ψ × Ω)

## Key Dimensionless Parameters

### 1. **P_S2: S2 Activation Probability** [0, 1]
- **Definition**: Probability that an agent engages in System 2 (deliberative) thinking
- **Formula**: P_S2 = Ψ × Ω (multiplicative form)
- **Evolution**: Typically increases over time as agents gain experience and move to safer locations
- **Interpretation**: Higher P_S2 indicates more deliberative decision-making

### 2. **Ψ (Psi): Cognitive Capacity** [0, 1]
- **Definition**: Agent's ability to engage in deliberative thinking
- **Formula**: Ψ(x; α) = 1/(1 + e^(-αx)) where x = experience index
- **Evolution**: Increases as agents gain experience (travel time, local knowledge, etc.)
- **Interpretation**: Higher Ψ means agent has more cognitive resources for deliberation

### 3. **Ω (Omega): Structural Opportunity** [0, 1]
- **Definition**: Whether the situation permits deliberative thinking
- **Formula**: Ω(c; β) = 1/(1 + e^(-β(1-c))) where c = conflict intensity
- **Evolution**: Increases as agents move to safer locations (lower conflict)
- **Interpretation**: Higher Ω means environment allows time for deliberation

### 4. **Experience Index** [0, ∞)
- **Definition**: Composite measure of agent's relevant experience
- **Formula**: x = 0.25×prior_displacement + 0.25×local_knowledge + 0.20×conflict_exposure + 0.15×connections + 0.10×age_factor + 0.05×education_level
- **Evolution**: Increases over time as agents travel and gain experience
- **Interpretation**: Higher experience index → higher cognitive capacity (Ψ)

### 5. **Cognitive Pressure** [0, 1]
- **Definition**: Normalized measure of stress/urgency
- **Components**: Base pressure + conflict pressure + social pressure
- **Evolution**: Varies with conflict intensity and agent location
- **Interpretation**: Higher pressure → less opportunity for deliberation (lower Ω)

### 6. **Normalized Time** [0, 1]
- **Definition**: t* = t / T_max where T_max = total simulation timesteps
- **Purpose**: Enables comparison across simulations of different durations
- **Evolution**: Linear from 0 to 1

### 7. **Evacuation Efficiency** [0, 1]
- **Definition**: η_evac = agents_at_safe / agents_total
- **Evolution**: Increases over time as agents reach safe zones
- **Interpretation**: Fraction of population successfully evacuated

### 8. **Experience-to-Pressure Ratio**
- **Definition**: R = experience_index / cognitive_pressure
- **Evolution**: Increases as agents gain experience faster than pressure increases
- **Interpretation**: Higher ratio → agents better equipped to handle pressure

### 9. **S2 Efficiency** [0, 1]
- **Definition**: η_S2 = P_S2 × evacuation_efficiency
- **Evolution**: Combines S2 activation with evacuation success
- **Interpretation**: Measures effectiveness of deliberative decision-making

### 10. **Experience Heterogeneity**
- **Definition**: Standard deviation of experience index across agents
- **Evolution**: May increase or decrease depending on agent distribution
- **Interpretation**: Higher heterogeneity → more diverse decision-making patterns

## Model Validation: P_S2 = Ψ × Ω

The model predicts that S2 activation probability equals the product of cognitive capacity and structural opportunity:

**P_S2 = Ψ × Ω**

This is validated by comparing:
- **Observed P_S2**: Directly measured from agent decisions
- **Calculated Ψ × Ω**: Product of calculated capacity and opportunity

High correlation (>0.9) confirms model consistency.

## Evolution Patterns

### Typical Evolution (Ring/Star Topology):
1. **Early (t* < 0.3)**:
   - Low P_S2 (agents just spawned, high conflict)
   - Low Ψ (no experience yet)
   - Low Ω (high conflict at facility)
   - Low evacuation efficiency

2. **Middle (0.3 < t* < 0.7)**:
   - Increasing P_S2 (agents gaining experience, moving to safer areas)
   - Increasing Ψ (experience accumulating)
   - Increasing Ω (conflict decreasing)
   - Moderate evacuation efficiency

3. **Late (t* > 0.7)**:
   - High P_S2 (experienced agents, low conflict)
   - High Ψ (high experience)
   - High Ω (low conflict near safe zones)
   - High evacuation efficiency

### Linear Topology (Bottleneck Effects):
- May show different patterns due to bottleneck at safe zone
- Cognitive pressure may increase even as conflict decreases (agents stuck)
- Experience still increases, but Ω may be constrained

## Dimensionless Parameter Files

### Generated Visualizations:

1. **`dimensionless_parameters_evolution.png`**
   - 9-panel plot showing evolution of all key parameters
   - Normalized time on x-axis (enables cross-scenario comparison)
   - Comparison across topologies

2. **`dimensionless_psi_omega_validation.png`**
   - Validates model consistency: P_S2 = Ψ × Ω
   - Shows correlation between observed and calculated values
   - One panel per topology

3. **`dimensionless_parameters_comparison.png`**
   - Final values of all parameters across topologies
   - Bar charts for easy comparison
   - Identifies which topology produces best outcomes

## Usage

```bash
# Generate dimensionless parameter analysis
python3 analyze_dimensionless_parameters.py
```

The script automatically:
1. Loads the most recent simulation results
2. Calculates all dimensionless parameters
3. Generates evolution plots
4. Validates model consistency
5. Creates comparison charts

## Scientific Significance

### Universal Patterns:
- **Inverted-U in P_S2**: Deliberation maximized at intermediate conflict (moderate Ω, increasing Ψ)
- **Experience Accumulation**: Ψ increases monotonically with experience
- **Conflict Decay**: Ω increases as agents move away from conflict zones
- **Multiplicative Constraint**: P_S2 limited by the smaller of Ψ or Ω

### Scale Invariance:
All parameters are dimensionless, enabling:
- Comparison across different conflict scales
- Generalization to different population sizes
- Application to different geographic contexts
- Validation against empirical data from various crises

## References

- **Buckingham π Theorem**: Dimensional analysis for scale-invariant modeling
- **Kahneman (2011)**: Dual-process theory foundation
- **Rodriguez-Iturbe**: Parsimony principle for parameter selection

