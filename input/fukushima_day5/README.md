# Fukushima Day 5 inputs — corridor effects and Route 6 closure

This directory contains the input files for the Day 5 scenario comparison runs.
It is a snapshot of `input/fukushima_day3/` plus one additional artifact:

* `conflicts_route6_closed.csv` — identical to `conflicts.csv` for days 0–2,
  then spikes the per-day conflict at `naraha` and `hirono` to **0.95** from
  day 3 onward. This implements the historical Route 6 closure as a soft
  closure via the conflict signal: high-S2 agents discover the inland
  Kawauchi alternative through the precomputed `ConflictPotentialField`,
  while pure-S1 agents continue to follow the shortest-distance heuristic
  toward Route 6 and are blocked by the elevated conflict at the corridor
  nodes.

## Why no separate "zone-level baseline" directory

The Day 5 prompt was written assuming the network still consisted of
zone-level macro-nodes. In this repository, the OSM build performed on
Day 3 already added the intermediate municipalities (Tomioka, Naraha,
Hirono, Kawauchi, Iwaki north/city, Minamisoma south/north, Tamura, Iitate)
and the corridor links between them. Section 1 of the Day 5 prompt is
therefore already satisfied by `input/fukushima_day3/`. As a result,
Scenario 1 ("baseline") and Scenario 2 ("full network") use the same
input directory in this codebase. Scenario 1 is preserved in the run
script as an explicit replication of the Day 3 result; Scenarios 3 and
4 are the new contributions of Day 5.

## Files

| file | purpose |
|------|---------|
| `locations.csv` | 15 municipalities + 3 receiving cities (camps), unchanged from Day 3 |
| `routes.csv`    | 21 OSM-verified corridor links, unchanged from Day 3 |
| `closures.csv`  | Empty (no hard closures used; Route 6 closure is modelled as a conflict spike) |
| `conflicts.csv` | Day 3 conflict schedule, unchanged |
| `conflicts_route6_closed.csv` | Route 6 closure variant — naraha/hirono at 0.95 from day 3 onward |
| `simsetting.yml` | Day 3 simulation settings, unchanged |
