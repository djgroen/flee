# Systematic Topology Analysis
**Target Journal: Scientific Reports**

## 1. Experimental Design
We defined **8 Fundamental Topologies** to characterize refugee movement dynamics across different spatial structures:
1.  **Linear Chain**: Sequential towns (e.g., coastal road).
2.  **Dendritic (Hierarchical)**: River basin / Rural-to-Urban flow.
3.  **Lattice (Grid)**: Urban environment / Developed road network.
4.  **Star (Hub-and-Spoke)**: Centralized transit system.
5.  **Bottleneck**: Two clusters connected by a single bridge.
6.  **Parallel Routes**: Multiple distinct paths (choice).
7.  **Cycle (Ring)**: Closed loop (e.g., around a lake).
8.  **Small World**: High clustering with shortcuts.

## 2. Methodology: Sensitivity Sweep
For each topology, we varied:
*   **Size ($N$)**: 20, 50, 100 nodes.
*   **Connectivity ($K$)**: Sparse vs. Dense (Edge density).
*   **Conflict**: Randomized placement of conflict zones vs. Safe zones.

**Simulation Parameters**:
*   Population: 200 agents per conflict zone.
*   Duration: 100 Days.
*   Cognitive Model: Dual-Process (S1/S2).

## 3. Key Findings

### Scaling Laws
*   **Linear**: Fails at scale. At $N=100$, arrivals drop to near zero due to excessive travel distance/time.
*   **Dendritic**: Highly robust. Maintains efficiency even as $N$ increases, effectively funneling agents.
*   **Star**: "Hyper-efficient" ($T \approx 0$ days) due to direct 1-hop connections, representing an idealized transit scenario.
*   **Lattice**: Highly sensitive to connectivity. Sparse lattices see significant delays; Dense lattices approach theoretical efficiency.
*   **Cycle**: Poor performance for agents on the "wrong side" of the ring, leading to long traversal times.

### Impact of Density
*   **Redundancy**: Adding density (shortcuts) significantly improves **Small World** and **Lattice** performance (~30-50% reduction in travel time).
*   **Bottleneck**: Density *within* clusters does not alleviate the central bottleneck constraint.

## 4. Visualizations
*   **Animations**: Updated to explicitly visualize **Conflict Zones** (Orange/Red stars) and **Safe Zones** (Blue squares) with population counters.
*   **Plots**:
    *   `systematic_results/scaling_laws.png`: Delay vs Network Size.
    *   `systematic_results/density_impact.png`: Efficiency gain from density.

## 5. Next Steps
*   Draft the "Methods" section describing these 8 topologies.
*   Select 3-4 key topologies (likely Dendritic, Lattice, Bottleneck) for the main paper figures, moving others to Supplementary Material.


