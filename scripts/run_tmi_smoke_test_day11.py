#!/usr/bin/env python3
"""TMI Day 11 smoke test: sys1-only, 3× replications, 20 timesteps, 300 agents."""

from __future__ import annotations

import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"
OUT = REPO / "results" / "tmi" / "smoke_test"

sys.path.insert(0, str(REPO))

from flee import InputGeography  # noqa: E402
from flee import flee  # noqa: E402
from flee.SimulationSettings import SimulationSettings  # noqa: E402


def _load_population_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    with (TMI / "population_tmi.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loc_key = "location"
        if reader.fieldnames:
            for k in reader.fieldnames:
                if k and k.lstrip("#") == "location":
                    loc_key = k
                    break
        n_key = "n_agents"
        if reader.fieldnames:
            for k in reader.fieldnames:
                if k and k.lstrip("#") == "n_agents":
                    n_key = k
                    break
        for row in reader:
            if not row or not row.get(loc_key) or row[loc_key].startswith("#"):
                continue
            loc = row[loc_key].strip()
            counts[loc] = int(row[n_key])
    return counts


def _build_ecosystem() -> tuple[flee.Ecosystem, InputGeography.InputGeography, dict]:
    """Must run with cwd = TMI (for location_changes.csv)."""
    SimulationSettings.ReadFromYML(str(TMI / "simsetting_tmi.yml"))
    SimulationSettings.ConflictInputFile = str(TMI / "conflicts.csv")

    e = flee.Ecosystem()
    ig = InputGeography.InputGeography()
    ig.ReadLocationsFromCSV("locations.csv")
    ig.ReadLinksFromCSV("routes.csv")
    ig.ReadClosuresFromCSV("closures.csv")
    e, lm = ig.StoreInputGeographyInEcosystem(e)

    pop = _load_population_counts()
    avg_conn = float(SimulationSettings.spawn_rules.get("AverageSocialConnectivity", 3.0))
    for loc_name, n in pop.items():
        loc = lm[loc_name]
        for _ in range(n):
            conn = int(np.random.poisson(avg_conn))
            e.insertAgent(location=loc, attributes={"connections": max(0, conn)})
    return e, ig, lm


def _run_replication(seed: int) -> tuple[list[dict[str, int]], list[float]]:
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))

    cwd = Path.cwd()
    try:
        import os

        os.chdir(TMI)
        e, ig, lm = _build_ecosystem()
    finally:
        os.chdir(cwd)

    n_agents = len(e.agents)
    loc_names = [loc.name for loc in e.locations]
    counts_series: list[dict[str, int]] = []
    dep_rates: list[float] = []

    for t in range(20):
        ig.AddNewConflictZones(e, t)

        before_loc = {
            id(a): a.location.name for a in e.agents if a.location is not None
        }
        before_non_camp = sum(
            1
            for a in e.agents
            if a.location is not None and not a.location.camp
        )
        e.enact_border_closures(t)
        e.evolve()

        moved = 0
        for a in e.agents:
            if a.location is None:
                continue
            prev = before_loc.get(id(a))
            if prev is not None and a.location.name != prev:
                moved += 1
        dep_rates.append(moved / max(1, before_non_camp))

        ct = {name: 0 for name in loc_names}
        for a in e.agents:
            if a.location is not None:
                ct[a.location.name] += 1
        counts_series.append(ct)

    return counts_series, dep_rates


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_counts: list[list[dict[str, int]]] = []
    all_dep: list[list[float]] = []
    for r in range(3):
        cs, dr = _run_replication(42 + r)
        all_counts.append(cs)
        all_dep.append(dr)

    loc_names = sorted(all_counts[0][0].keys())
    with (OUT / "agent_counts.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestep", "replication"] + loc_names)
        for rep, series in enumerate(all_counts):
            for t, row in enumerate(series):
                w.writerow([t, rep] + [row[k] for k in loc_names])

    mean_dep = [sum(all_dep[r][t] for r in range(3)) / 3.0 for t in range(20)]
    with (OUT / "departure_rates.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestep", "departure_rate"])
        for t, v in enumerate(mean_dep):
            w.writerow([t, f"{v:.6f}"])

    print("Smoke test done. Mean departures t=5:", mean_dep[5], "t=10:", mean_dep[10])
    camps = {"harrisburg_camp", "lancaster_camp", "york_camp"}
    last = all_counts[-1][-1]
    at_camp = sum(last[k] for k in camps)
    print("Agents in camps (last rep, t=19):", at_camp, "/", sum(last.values()))


if __name__ == "__main__":
    main()
