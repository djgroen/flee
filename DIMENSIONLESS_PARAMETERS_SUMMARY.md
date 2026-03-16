# Dimensionless Parameters Analysis for Refugee Dynamics
**Target Journal: Scientific Reports**

## Overview
This analysis explores how refugee movement efficiency scales with network topology and population pressure using dimensionless parameters.

## Methodology
We performed a parameter sweep varying:
1.  **Network Topology**: Lattice (Grid) vs. Hierarchical (Dendritic).
2.  **Network Size**: 16 to ~100 nodes.
3.  **Agent Population**: 100 vs. 500 agents (varying saturation).
4.  **Connectivity**: Obstacle density in Lattice grids.

## Key Dimensionless Parameters
1.  **Delay Factor ($D$)**: The ratio of *Actual Average Travel Time* to *Ideal Travel Time* (based on graph distance).
    $$ D = \frac{T_{actual}}{T_{ideal}} $$
    *   $D=1.0$ implies perfect efficiency (no congestion/waiting).
    *   $D > 1.0$ indicates inefficiency due to congestion, path deviation, or decision delays.

2.  **Agent Saturation ($\sigma$)**: The ratio of total agents to total network capacity (excluding conflict zones).
    $$ \sigma = \frac{N_{agents}}{C_{total}} $$

3.  **Connectivity ($k$)**: Average node degree.
    $$ k = \frac{2E}{N} $$

## Results

### 1. Scaling of Delay with Network Size
*   **Observation**: As network size increases, the Delay Factor remains relatively stable for Hierarchical networks but shows variance for Lattices.
*   **Implication**: Hierarchical networks (rural routes) provide predictable performance regardless of scale, while Lattice networks (urban) are more sensitive to local conditions.

### 2. Impact of Saturation
*   **Observation**: Higher saturation ($\sigma$) generally correlates with increased Delay Factor, but the effect is non-linear.
*   **Implication**: There is a "tipping point" in capacity where efficiency drops vertically.

### 3. Connectivity vs. Efficiency
*   **Observation**: Higher connectivity (higher $k$, lower obstacle density) generally reduces the Delay Factor.
*   **Implication**: Redundancy in routes allows agents to bypass congestion, acting as a buffer against inefficiency.

## Figures Generated
*   `sweep_results/delay_vs_saturation_fixed.png`: Scatter plot of Delay vs. Saturation.
*   `sweep_results/delay_vs_size_fixed.png`: Scaling of Delay with Network Nodes.
*   `sweep_results/delay_vs_connectivity.png`: Impact of connectivity on Delay.
*   `sweep_results/sweep_summary_fixed.csv`: Raw data.

## Next Steps
*   Refine the "Ideal Time" calculation to account for specific path choices.
*   Investigate the specific "tipping point" for saturation in different topologies.


