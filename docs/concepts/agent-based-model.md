# How the model works

Flee is an **agent-based model (ABM)**. Rather than tracking aggregate statistics (like total refugee counts), it simulates the behaviour of individual people — called *agents* — each making their own movement decisions at each time step.

---

## The simulation loop

Each simulation day, the following happens:

1. **Agents are spawned** at conflict or disaster locations according to population data and conflict schedules
2. **Each agent decides whether to move** based on where they are (conflict zone, camp, or regular location) and the `movechance` parameter for that location type
3. **Agents that move choose a destination** from their adjacent locations, weighted by a scoring function that considers distance, conflict levels, camp attractiveness, and awareness of the route network
4. **Counts are recorded** — how many agents are at each location at the end of the day

The simulation runs for a user-specified number of days.

---

## Key entities

### Agents (people)

Each agent represents one or more displaced individuals (depending on the `hasten` optimisation setting). Agents have a location, a set of known routes, and a movement chance that depends on where they are.

### Locations

Locations are nodes in a network graph. Each location has a type (see [location types](location-types.md)), a population, a conflict value, and optionally a capacity. The location type determines default movement behaviour.

**Location types:**

| Type | Description |
|------|-------------|
| `conflict` | A location experiencing conflict or disaster. High move chance — agents are likely to leave. |
| `camp` | A refugee or IDP camp. Very low move chance — agents are likely to stay once they arrive. |
| `town` | A regular urban location. Intermediate move chance. |
| `forwarding_hub` | A transit point; agents pass through but do not settle. |
| `marker` | Used for routing only; not a real location agents stop at. |

### Links (routes)

Links connect locations and represent roads or paths between them. Each link has a distance. Agents travel along links at a speed determined by `max_move_speed` or `max_walk_speed`.

---

## Movement decisions

Whether an agent moves is determined by the **move chance** of their current location type. If they decide to move, the destination is chosen based on a **scoring function** that weighs up:

- **Distance** — closer locations score higher (by default)
- **Conflict level** — agents avoid high-conflict locations
- **Camp attractiveness** — camps are weighted as desirable destinations
- **Awareness level** — how many hops ahead the agent can "see" in the network

See [Movement rule settings](../running/settings-move.md) for the parameters that control this behaviour.

---

## Spawning agents

Agents are created (spawned) at conflict or disaster locations. The number spawned per day is derived from population data in `locations.csv` and a conflict schedule (`conflicts.csv`). There are several spawning modes; see [Logging and spawning settings](../running/settings-basic.md) for details.

---

## Validation

After running a simulation, the output can be compared against real-world data (e.g. UNHCR camp registration figures). Flee includes plotting tools to produce these comparison graphs automatically. The degree of match between simulation and data is used to validate and calibrate the model.

---

## Parallel execution (pflee)

For large simulations, Flee can be run in parallel using MPI via `pflee`. The agent population is distributed across multiple processes. See [Running locally](../running/local.md) for parallel execution commands.

---

## Further reading

- [Journal of Computational Science publication (v3.0, 2024)](https://doi.org/10.1016/j.jocs.2024.102371)
- [Literature and citing](../about/literature.md)
