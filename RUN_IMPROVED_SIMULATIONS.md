# Running Improved Simulations with Decision-Rich Topologies

## Quick Start

### Option 1: Decision-Rich Mode (Recommended for Movies)

```bash
python3 nuclear_evacuation_simulations.py --decision-rich
```

or

```bash
python3 nuclear_evacuation_simulations.py -d
```

**What this does:**
- Ring topology: Multiple safe zones, multiple paths between rings
- More route choices at each decision point
- Agents will split between different routes
- S1 vs S2 differences become more visible

### Option 2: Standard Mode (Original)

```bash
python3 nuclear_evacuation_simulations.py
```

## Improvements Made

### 1. Ring Topology
- **6 locations per ring** (was 4) = more decision points
- **3 safe zones** at different angles (was 1) = destination choice
- **Multiple paths** between rings (direct + adjacent) = routing choice
- **Each outer location connects to 2 safe zones** = agents split

### 2. Parameters
- **`p_s2: 0.9`** (was 0.8) = S2 agents more likely to move
- **`awareness_level: 2`** (was 1) = S2 agents see more routes ahead

### 3. Expected Visual Differences

**Before (Standard):**
- All agents follow same path
- Hard to distinguish S1 vs S2
- Predictable movement

**After (Decision-Rich):**
- Agents split at decision points
- S1 agents: Clustered, follow main routes
- S2 agents: Spread out, take alternative routes
- Clear visual distinction

## Generate Movies

After running simulations:

```bash
python3 visualize_agent_movements_corrected.py nuclear_evacuation_results
```

## Testing with Fewer Agents

To test quickly with fewer agents:

```python
# Edit nuclear_evacuation_simulations.py, change:
simulator.run_all_topologies(num_agents=100, num_timesteps=30, decision_rich=True)
```

Then run:
```bash
python3 nuclear_evacuation_simulations.py
```

## Comparison

Run both modes and compare:

1. **Standard mode:**
   ```bash
   python3 nuclear_evacuation_simulations.py
   # Rename results
   mv nuclear_evacuation_results nuclear_evacuation_results_standard
   ```

2. **Decision-rich mode:**
   ```bash
   python3 nuclear_evacuation_simulations.py --decision-rich
   # Results in nuclear_evacuation_results/
   ```

3. **Compare movies:**
   - Standard: Predictable, all agents same path
   - Decision-rich: Dynamic, agents split, S1/S2 visible

## Next Steps

If decision-rich mode works well:
1. Keep it as default
2. Add more topologies (Grid/Maze)
3. Further parameter tuning
4. Add route quality indicators (distance, safety)

