# H2.1 Hidden Information Scenario

## Overview

This scenario tests whether socially connected agents can discover better destinations that are not immediately visible to isolated agents. It implements an Origin→Obvious_Camp (visible, limited capacity) vs Origin→Hidden_Camp (better conditions, requires social knowledge) setup.

## Network Structure

- **Origin**: Starting location with 8,000 population, experiences conflict
- **Obvious_Camp**: Highly visible camp (2,000 capacity, safety 0.6, distance 40km)
- **Hidden_Camp**: Better but hidden camp (4,000 capacity, safety 0.9, distance 60km)
- **Information_Hub**: Intermediate location where connected agents can learn about Hidden_Camp

## Information Access Rules

### Visibility Parameters
- **Obvious_Camp**: `visibility=1.0` (all agents can see it)
- **Hidden_Camp**: `visibility=0.0` (only discoverable through social connections)
- **Information_Hub**: `info_source=true` (provides information about Hidden_Camp)

### Agent Types
- **S1 Baseline**: No social connections, can only see Obvious_Camp
- **S2 Isolated**: System 2 thinking but no social connections, can only see Obvious_Camp  
- **S2 Connected**: System 2 with social connections, can discover Hidden_Camp through network

## Conflict Timeline

- **Day 0**: Initial conflict intensity 0.4 at Origin
- **Day 45**: Escalation to intensity 0.7 at Origin
- **Day 90**: Peak conflict intensity 1.0 at Origin

## Information Sharing Mechanics

1. **Connected agents** visiting Information_Hub learn about Hidden_Camp
2. **Information propagation** occurs when connected agents share knowledge
3. **Discovery probability** increases with network connectivity and time
4. **Information decay** simulates forgetting over time

## Expected Results

### S1 Baseline Agents
- Only discover Obvious_Camp
- Quick but suboptimal decisions
- Higher overcrowding at Obvious_Camp

### S2 Isolated Agents
- Only discover Obvious_Camp despite deliberative thinking
- Better timing but limited destination options
- Similar overcrowding issues

### S2 Connected Agents
- Higher probability of discovering Hidden_Camp
- Better overall outcomes (safety + capacity)
- More efficient population distribution

## Key Metrics

1. **Discovery Rate**: Percentage of agents discovering Hidden_Camp by agent type
2. **Information Propagation Speed**: Time for Hidden_Camp knowledge to spread
3. **Destination Quality**: Average safety and capacity utilization by agent type
4. **Network Effect Size**: Difference in outcomes between connected vs isolated agents

## Files

- `locations.csv`: Network with visibility and information parameters
- `routes.csv`: Distance matrix including Information_Hub
- `conflicts.csv`: Escalating conflict at Origin
- `agent_config.py`: Agent type definitions with connectivity parameters
- `h2_1_metrics.py`: Analysis tools for information sharing measurement