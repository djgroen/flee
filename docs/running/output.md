# Output files

Every Flee simulation run produces one or more output files in the output directory you specify.

---

## out.csv — main results file

The primary output file used for validation, analysis, and plotting. It contains one row per simulation day.

For each day it records:

- Simulated agent counts at every camp/destination
- Real-world validation counts (if provided)
- Relative error between simulation and data
- Summary totals

**Key columns:**

| Column | Description |
|--------|-------------|
| `Day` | Simulation day number (starting at 0) |
| `Date` | Corresponding calendar date |
| `<camp> sim` | Simulated number of displaced people at that camp |
| `<camp> data` | Real-world count for that camp on that date (from validation data) |
| `<camp> error` | Relative error between simulated and reported counts |
| `Total error` | Average relative error across all camps on that day |
| `refugees in camps (e.g. UNHCR data)` | Total reported camp population (validation data) |
| `total refugees (simulation)` | Total agents across the entire simulation |
| `raw UNHCR refugee count` | Total reported count including those not yet in camps |
| `refugees in camps (simulation)` | Total agents currently inside any camp |
| `refugee_debt` | Mismatch tracker for agents that could not be spawned due to rounding |

---

## agents.out.N — per-agent log

A detailed log of every individual agent, one file per MPI rank (`N = 0, 1, 2, ...`). Tracks locations, coordinates, travel distance, and demographic attributes.

!!! note
    This file is only produced when `log_levels.agent` is set to 1 or higher in `simsetting.yml`. It can become very large for long simulations with many agents.

**Key columns:**

| Column | Description |
|--------|-------------|
| `#time` | Simulation day |
| `rank-agentid` | Unique agent ID (e.g. `0-42` = rank 0, agent 42) |
| `original_location` | Where the agent entered the simulation |
| `current_location` | Where the agent is on this day |
| `gps_x` / `gps_y` | Longitude / latitude of current location |
| `is_travelling` | Whether the agent is mid-journey |
| `distance_travelled` | Total cumulative distance (km) |
| `places_travelled` | Number of distinct locations visited |
| `distance_moved_this_timestep` | Distance moved today |
| `connections` | Number of onward routes from current location |
| `age`, `gender`, `ethnicity` | Demographic attributes (if defined in scenario) |

---

## links.out.N — route usage log

Records how many agents have used each link (route) between two locations, one file per MPI rank.

!!! note
    Only produced when `log_levels.link` is set to 1 in `simsetting.yml`.

**Key columns:**

| Column | Description |
|--------|-------------|
| `#time` | Simulation day |
| `start_location` | One end of the route |
| `end_location` | Other end of the route |
| `cum_num_agents` | Cumulative agents who have used this route up to this day |
| `attribute` | Category counted (e.g. `total`) |

---

## Plotting output

After a run, generate comparison graphs automatically:

```sh
python3 flee/postprocessing/plot_flee_output.py <output_dir>/ <output_dir>/
```

This produces:
- One graph per camp showing simulated vs reported counts over time
- An overall average relative error graph

---

## Next steps

- [Running locally](local.md) — run your simulation
- [Settings — logging and spawning](settings-basic.md) — control which output files are produced
