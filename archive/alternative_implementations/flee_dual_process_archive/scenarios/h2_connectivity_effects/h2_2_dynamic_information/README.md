# H2.2 Dynamic Information Sharing Scenario

## Overview

This scenario tests how real-time information sharing about camp capacities affects decision timing and accuracy. It implements dynamic camp capacity updates with information lag, testing whether connected agents can make better decisions based on shared real-time information.

## Network Structure

- **Origin**: Starting location with 6,000 population, experiences conflict
- **Camp_Alpha**: Initial high capacity (4,000), becomes overcrowded over time
- **Camp_Beta**: Initial medium capacity (2,500), capacity increases mid-simulation
- **Camp_Gamma**: Initial low capacity (1,500), remains stable
- **Info_Station**: Information sharing hub where connected agents exchange capacity updates

## Dynamic Information System

### Capacity Changes
- **Day 0-30**: Camp_Alpha at full capacity (4,000)
- **Day 30-60**: Camp_Alpha reduces to 2,000 due to resource constraints
- **Day 60-90**: Camp_Beta expands to 4,000 capacity
- **Day 90-120**: Camp_Alpha recovers to 3,000 capacity

### Information Lag
- **Real-time**: Actual capacity changes occur immediately
- **Official Updates**: Broadcast to all agents with 5-day delay
- **Social Network**: Connected agents share information with 1-day delay
- **Isolated Agents**: Only receive official updates

## Agent Network Protocols

### Information Sharing Rules
1. **Connected agents** visiting Info_Station learn current capacities
2. **Network propagation** spreads information to connected agents within 1 day
3. **Information accuracy** degrades over time without updates
4. **Capacity estimates** updated based on agent observations and network sharing

### Agent Types
- **S1 Baseline**: No social connections, relies on official updates only
- **S2 Isolated**: System 2 thinking but no network, official updates only
- **S2 Connected**: System 2 with network access, receives rapid information updates

## Conflict Timeline

- **Day 0**: Initial conflict intensity 0.3 at Origin
- **Day 20**: Escalation to intensity 0.6 at Origin
- **Day 40**: Peak conflict intensity 0.8 at Origin
- **Day 80**: Conflict reduction to intensity 0.4 at Origin

## Information Accuracy Metrics

### Capacity Tracking
- **Real Capacity**: Actual available spaces at each camp
- **Perceived Capacity**: What each agent believes is available
- **Information Age**: Days since last capacity update for each agent
- **Accuracy Score**: Correlation between perceived and real capacity

## Expected Results

### S1 Baseline Agents
- Rely on outdated official information
- Poor timing of movements (arrive at overcrowded camps)
- Higher probability of secondary displacement

### S2 Isolated Agents
- Better decision-making process but limited information
- Still affected by information lag
- Some improvement over S1 but constrained by data quality

### S2 Connected Agents
- Access to near real-time capacity information
- Better timing of movements to avoid overcrowded camps
- More efficient camp utilization and fewer secondary moves

## Key Metrics

1. **Information Accuracy**: Correlation between perceived and actual camp capacities
2. **Decision Timing**: Optimal timing of movements relative to capacity changes
3. **Secondary Displacement**: Rate of agents needing to move again due to overcrowding
4. **Network Information Value**: Advantage gained from social network information

## Files

- `locations.csv`: Network with information sharing capabilities
- `routes.csv`: Distance matrix including Info_Station
- `conflicts.csv`: Conflict timeline at Origin
- `capacity_timeline.csv`: Dynamic capacity changes over time
- `information_protocols.py`: Network information sharing implementation
- `h2_2_metrics.py`: Analysis tools for information sharing effectiveness