# Topology Redesign for Nuclear Evacuations

## Current Problems

1. **All topologies look linear in visualizations** - Network structure not visible
2. **Agents not visible** - Too small, can't see individuals
3. **Unclear decision-making differences** - Simple topologies don't show meaningful S1/S2 differences
4. **No S1 flocking behavior** - Should see group/clustering for System 1

## Proposed Topology Redesigns

### 1. Ring Topology (Circular Evacuation Zones)
**Current**: Concentric rings, but visualization doesn't show it
**Redesign**: 
- Make rings more spread out (larger radius differences)
- Add connections between adjacent locations in same ring (creates circular paths)
- This creates decision complexity: agents can go around the ring or outward
- **S1 behavior**: Agents cluster together, follow others
- **S2 behavior**: Agents plan optimal path (shortest to safe zone)

### 2. Star Topology (Hub-and-Spoke)
**Current**: Good structure, but needs better visualization
**Redesign**:
- Make spokes more spread out (wider angles)
- Add decision points: multiple routes from center
- **S1 behavior**: Agents follow crowd, take most popular route
- **S2 behavior**: Agents evaluate all routes, choose optimal

### 3. Linear Topology (Single Corridor)
**Current**: Simple linear chain
**Redesign**:
- Keep simple (this is the baseline)
- Add side branches that lead to dead ends (creates decision complexity)
- **S1 behavior**: Agents follow the main path (herding)
- **S2 behavior**: Agents avoid dead ends, plan ahead

## Key Improvements Needed

1. **Visualization**:
   - Draw network edges clearly
   - Make agents LARGE and visible (size 150+)
   - Show S1 as clusters/groups (flocking)
   - Show S2 as individual dots (planning)

2. **Topology Complexity**:
   - Add decision points (multiple paths)
   - Create scenarios where S1 and S2 make different choices
   - Make network structure clearly visible

3. **Agent Behavior**:
   - Track actual S2 state per agent (not just location)
   - Show clustering for S1 agents
   - Show individual movement for S2 agents

