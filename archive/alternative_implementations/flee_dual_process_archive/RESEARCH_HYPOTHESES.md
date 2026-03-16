# Research Hypotheses: Dual-Process Theory in Refugee Movement

This document presents the four core research hypotheses that guide our experimental framework for testing dual-process cognitive theory in refugee movement simulations.

## Background: Dual-Process Theory

Dual-process theory proposes that human decision-making operates through two distinct cognitive systems:

- **System 1**: Fast, automatic, intuitive processing that relies on heuristics and emotional responses
- **System 2**: Slow, deliberate, analytical processing that involves conscious reasoning and planning

**Key Insight**: Each agent dynamically switches between System 1 and System 2 modes based on situational factors. When "cognitive pressure" (combining conflict intensity, social connectivity, and recovery time) exceeds a threshold, agents activate System 2 thinking. Otherwise, they operate in System 1 mode.

In refugee movement contexts, we hypothesize that this dynamic switching creates measurably different movement patterns depending on the conditions that trigger each cognitive mode.

## The Four Core Hypotheses

### H1: Speed vs. Optimality Trade-off

**Central Question**: Do System 1 and System 2 cognitive modes produce different trade-offs between decision speed and decision quality in refugee movement?

**Hypothesis**: System 1 processing leads to faster but less optimal movement decisions, while System 2 processing leads to slower but more optimal decisions.

**Theoretical Basis**: System 1's reliance on heuristics should enable rapid responses to threats but may miss better long-term options. System 2's analytical approach should identify superior destinations and routes but at the cost of delayed action.

**Testable Predictions**:

- Agents in System 1 mode will initiate movement earlier when conflict begins
- Agents in System 1 mode will choose closer, more obvious destinations even if suboptimal
- Agents in System 2 mode will select destinations with better safety/capacity trade-offs
- Under time pressure, System 1 mode becomes more prevalent while System 2 advantages decrease
- Individual agents will switch between modes based on changing cognitive pressure

**Experimental Scenarios**:

- **H1.1 Multi-Destination Choice**: Three camps with different distance/safety/capacity trade-offs
- **H1.2 Time Pressure Cascade**: Sequential conflicts that create increasing urgency

---

### H2: Social Connectivity Effects

**Central Question**: Does social connectivity enable more effective System 2 processing by providing access to better information?

**Hypothesis**: Social connectivity improves destination selection and movement efficiency, but primarily for agents capable of System 2 processing who can integrate and analyze social information.

**Theoretical Basis**: System 2's analytical capabilities should be enhanced by access to social information networks, while System 1's heuristic processing may not effectively utilize complex social information.

**Testable Predictions**:

- Agents with high social connectivity will more frequently activate System 2 mode
- Agents in System 2 mode will discover better destinations through information sharing
- Agents in System 1 mode will show minimal benefit from social connectivity
- Information sharing will create cascading improvements in destination selection
- Network structure will moderate both System 2 activation and information benefits

**Experimental Scenarios**:

- **H2.1 Hidden Information**: Better camps that are only discoverable through social networks
- **H2.2 Dynamic Information Sharing**: Real-time capacity updates transmitted through social connections

---

### H3: Cognitive Pressure and Phase Transitions

**Central Question**: Can we identify universal scaling laws that predict when agents transition between System 1 and System 2 processing?

**Hypothesis**: A dimensionless "cognitive pressure" parameter, combining conflict intensity, social connectivity, and recovery time, predicts the probability of System 2 activation across different scenarios.

**Theoretical Basis**: Cognitive load theory suggests that System 2 activation depends on the balance between environmental demands and available cognitive resources. This balance should follow predictable scaling relationships.

**Testable Predictions**:

- Individual agents' System 2 activation probability follows a sigmoid function of cognitive pressure
- The transition occurs at a universal critical pressure value across different scenarios
- Population-level phase transitions will show characteristic signatures (hysteresis, critical slowing down)
- Dimensionless scaling will enable predictions across different population sizes and time scales
- Individual switching patterns will aggregate to predictable population-level dynamics

**Dynamic Switching Mechanism**:
Each agent calculates cognitive pressure at every timestep:

```
Cognitive Pressure = (Conflict Intensity × Social Connectivity) / Recovery Time
```

When cognitive pressure > threshold (typically 0.5), the agent switches to System 2 mode for that decision. Otherwise, it operates in System 1 mode. This creates dynamic, context-dependent switching within individual agents.

**Experimental Scenarios**:

- **H3.1 Parameter Grid Search**: Systematic exploration of the cognitive pressure parameter space
- **H3.2 Phase Transition Detection**: High-resolution mapping of the System 1/System 2 transition boundary

---

### H4: Population Diversity Advantage

**Central Question**: Do mixed populations containing both System 1 and System 2 agents outperform homogeneous populations?

**Hypothesis**: Heterogeneous populations with both cognitive modes achieve better collective outcomes than populations dominated by either System 1 or System 2 alone.

**Theoretical Basis**: System 1 agents can serve as "scouts" who rapidly explore options, while System 2 agents can serve as "analyzers" who evaluate and optimize choices. This division of cognitive labor should improve collective performance.

**Testable Predictions**:

- Populations with diverse cognitive switching patterns will show higher overall evacuation efficiency
- Agents operating in System 1 mode will discover new options that agents in System 2 mode then optimize
- Information cascades will emerge where System 1 exploration informs System 2 analysis
- Optimal cognitive diversity will depend on scenario characteristics and switching thresholds
- Individual agents' switching capabilities will create emergent collective intelligence

**Experimental Scenarios**:

- **H4.1 Adaptive Shock Response**: Dynamic events that test population resilience and adaptation
- **H4.2 Information Cascade**: Scout-follower dynamics in information discovery and sharing

## Cross-Hypothesis Interactions

These hypotheses are designed to be complementary and mutually reinforcing:

- **H1 + H2**: Social connectivity may help System 2 agents overcome their speed disadvantage by providing better information faster
- **H1 + H3**: The speed-optimality trade-off should vary predictably with cognitive pressure
- **H2 + H4**: Population diversity may be most beneficial when social connectivity enables information sharing between cognitive modes
- **H3 + H4**: The optimal population composition may depend on the cognitive pressure regime

## Methodological Approach

Each hypothesis will be tested through:

1. **Dynamic Switching Experiments**: Agents switch between System 1 and System 2 based on cognitive pressure, creating natural variation in cognitive modes within the same simulation
2. **Controlled Comparisons**: Compare scenarios with different cognitive pressure profiles (e.g., high vs. low conflict intensity, connected vs. isolated populations)
3. **Parameter Sweeps**: Exploration of cognitive pressure parameter space to identify critical values and scaling relationships
4. **Individual Tracking**: Monitor individual agents' cognitive state transitions and decision-making patterns over time
5. **Statistical Analysis**: Rigorous hypothesis testing with appropriate controls for multiple comparisons
6. **Replication**: Multiple experimental designs testing the same theoretical predictions
7. **Validation**: Testing predictions against real-world refugee movement data where possible

**Key Advantage**: This approach tests dual-process theory as it actually operates - with individuals dynamically switching between cognitive modes based on situational demands, rather than being permanently assigned to one mode or another.

## Expected Outcomes and Implications

### If Hypotheses Are Supported:

- **Theoretical**: Strong evidence for dual-process theory in crisis decision-making contexts
- **Practical**: Design principles for information systems and aid distribution that account for cognitive differences
- **Methodological**: A validated framework for incorporating cognitive theory into agent-based models

### If Hypotheses Are Not Supported:

- **Alternative Explanations**: Other factors (resource constraints, social norms, etc.) may dominate cognitive effects
- **Boundary Conditions**: Dual-process effects may be context-dependent or require different experimental conditions
- **Model Limitations**: The simulation framework may not capture essential aspects of real-world decision-making

## Research Significance

This research addresses fundamental questions about human decision-making under extreme stress while providing practical insights for humanitarian response. By testing dual-process theory in a realistic, high-stakes context, we can:

1. **Advance Cognitive Science**: Extend dual-process theory to collective behavior and crisis situations
2. **Improve Humanitarian Practice**: Inform aid distribution and information dissemination strategies
3. **Enhance Simulation Models**: Develop more psychologically realistic agent-based models
4. **Bridge Theory and Practice**: Connect laboratory findings to real-world applications

The systematic, hypothesis-driven approach ensures that results will contribute meaningfully to both theoretical understanding and practical applications, regardless of whether the specific predictions are confirmed or refuted.
