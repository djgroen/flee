### **Output File Descriptions**

#### `out.csv`

The main results file used for validation, analysis and plotting. For each day of the simulation it records, for every refugee camp or destination in the conflict scenario:

- The simulated number of refugees present at that location, the total number of simulated refugees, and a `refugee_debt` counter that tracks any mismatch in how many agents have been introduced into the simulation.
- If validation data is provided, the real-world count reported for the same location and date. The relative error between simulation and reality, and an overall daily error across all camps. The total reported count in the validation data.

**Column descriptions:**

| Column | Description |
|--------|-------------|
| `Day` | The simulation day number, starting at 0. |
| `Date` | The corresponding calendar date. |
| `<location> sim` | The number of refugees at that location according to the simulation. |
| `<location> data` | The real-world reported count for that location on that date (if validation data is provided). |
| `<location> error` | The relative error between the simulated and reported counts for that location. |
| `Total error` | The average relative error across all locations on that day. |
| `refugees in camps (e.g. UNHCR data)` | The total number of refugees recorded in camps according to the validation data. |
| `total refugees (simulation)` | The total number of refugees across the entire simulation. |
| `raw UNHCR refugee count` | The total reported refugee count from the validation data, including those not yet in camps. |
| `refugees in camps (simulation)` | The total number of simulated refugees who are currently inside a camp. |
| `refugee_debt` | A counter tracking any mismatch in how many agents have been introduced into the simulation (e.g. due to rounding when converting real-world counts into individual agents). |

---

#### `agents.out.N`

A detailed log of every individual refugee, separated by MPI rank (e.g. `N=0`, `1`, `2`, etc.). It tracks unique IDs, origin/current locations, GPS coordinates, travel distance, and movement status. It also includes specified demographic attributes such as age, gender, and ethnicity for every agent on each day. This file can become quite large depending on the duration of the simulation and the total population size.

**Column descriptions:**

| Column | Description |
|--------|-------------|
| `#time` | The simulation day number. |
| `rank-agentid` | A unique identifier for each agent, prefixed by the parallel process (rank) managing them, e.g. `0-42`. |
| `original_location` | The location where the agent first entered the simulation (their origin). |
| `current_location` | The location where the agent is on this day. |
| `gps_x` | Longitude of the agent's current location. |
| `gps_y` | Latitude of the agent's current location. |
| `is_travelling` | Whether the agent is currently mid-journey between two locations (`True`/`False`). |
| `distance_travelled` | The total distance the agent has travelled since the start of the simulation. |
| `places_travelled` | The number of distinct locations the agent has visited so far. |
| `distance_moved_this_timestep` | The distance the agent moved on this particular day. |
| `connections` | The number of onward routes available from the agent's current location. |
| `age` | The agent's age. |
| `gender` | The agent's gender. |
| `ethnicity` | The agent's ethnicity. |

---

#### `links.out.N`

Tracks route usage across the network, separated by MPI rank. It records the cumulative number of people who have traveled along specific roads between two locations, identifying the most heavily used movement patterns over time.

**Column descriptions:**

| Column | Description |
|--------|-------------|
| `#time` | The simulation day number. |
| `start_location` | The location at one end of the road. |
| `end_location` | The location at the other end of the road. |
| `cum_num_agents` | The cumulative number of refugees who have travelled along this road up to and including this day. |
| `attribute` | The category of agents counted (e.g. `total`). |
