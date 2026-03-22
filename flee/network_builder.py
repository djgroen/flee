"""
Synthetic topology builder for FLEE.
Outputs FLEE-native locations.csv and routes.csv.
No OSM — synthetic topologies only.
"""

import csv
import math
import os
from pathlib import Path
from typing import List, Tuple


def _write_locations(locations: List[dict], output_dir: Path) -> None:
    """Write locations.csv. Columns: name, region, country, gps_x, gps_y, location_type, conflict_date, pop/cap."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "locations.csv"
    columns = ["name", "region", "country", "gps_x", "gps_y", "location_type", "conflict_date", "pop/cap"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("#" + ",".join(f'"{c}"' for c in columns) + "\n")
        for loc in locations:
            row = [str(loc.get(c, "")) for c in columns]
            f.write(",".join(f'"{v}"' for v in row) + "\n")


def _write_routes(routes: List[Tuple[str, str, float]], output_dir: Path) -> None:
    """Write routes.csv. Columns: name1, name2, distance, forced_redirection."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "routes.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write('#"name1","name2","distance",forced_redirection\n')
        for a, b, dist in routes:
            f.write(f'"{a}","{b}",{dist},0\n')


def _write_closures(output_dir: Path) -> None:
    """Write empty closures.csv (no link closures)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "closures.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("#closure_type,name1,name2,closure_start,closure_end\n")


def _write_conflicts(location_names: List[str], conflict_schedule: dict, output_dir: Path) -> None:
    """Write conflicts.csv: Day column + per-location conflict columns. conflict_schedule: {loc: {step: value}}."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "conflicts.csv"
    if not conflict_schedule:
        return
    max_step = max(s for row in conflict_schedule.values() for s in row.keys()) if conflict_schedule else 72
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("Day," + ",".join(location_names) + "\n")
        for step in range(max_step + 1):
            row = [str(step)]
            for loc in location_names:
                row.append(str(conflict_schedule.get(loc, {}).get(step, 0.0)))
            f.write(",".join(row) + "\n")


def build_linear(output_dir: Path, n: int = 7, spacing_km: float = 50.0) -> dict:
    """
    Linear chain: source(conflict) — town_00 — town_01 — ... — camp
    Agents flee from source toward camp along single corridor.
    """
    output_dir = Path(output_dir)
    locations = []
    routes = []
    # Source at x=0, conflict
    locations.append({
        "name": "source", "region": "R1", "country": "C1",
        "gps_x": 0.0, "gps_y": 0.0, "location_type": "conflict",
        "conflict_date": 1, "pop/cap": 10000,
    })
    # Towns along x-axis
    for i in range(n - 2):
        x = (i + 1) * spacing_km
        locations.append({
            "name": f"town_{i:02d}", "region": "R1", "country": "C1",
            "gps_x": x, "gps_y": 0.0, "location_type": "town",
            "conflict_date": "", "pop/cap": "",
        })
    # Camp at end
    locations.append({
        "name": "camp", "region": "R1", "country": "C1",
        "gps_x": (n - 1) * spacing_km, "gps_y": 0.0, "location_type": "camp",
        "conflict_date": "", "pop/cap": 50000,
    })
    # Links: source-town_00-...-town_(n-3)-camp
    names = [loc["name"] for loc in locations]
    for i in range(len(names) - 1):
        routes.append((names[i], names[i + 1], spacing_km))
    _write_locations(locations, output_dir)
    _write_routes(routes, output_dir)
    _write_closures(output_dir)
    # Conflict: source has conflict 1.0 from step 1
    conflicts = {"source": {0: 0.0, 1: 1.0}}
    for step in range(2, 73):
        conflicts["source"][step] = 1.0
    _write_conflicts(names, conflicts, output_dir)
    return {"n_locations": len(locations), "n_links": len(routes)}


def build_ring(output_dir: Path, n: int = 6, radius_km: float = 150.0) -> dict:
    """
    Source at centre, n ring nodes, one is camp.
    Source connects to all ring nodes; ring nodes connect to neighbours.
    """
    output_dir = Path(output_dir)
    locations = []
    routes = []
    # Source at centre
    locations.append({
        "name": "source", "region": "R1", "country": "C1",
        "gps_x": 0.0, "gps_y": 0.0, "location_type": "conflict",
        "conflict_date": 1, "pop/cap": 10000,
    })
    # Ring nodes
    for i in range(n):
        angle = 2 * math.pi * i / n
        x = radius_km * math.cos(angle)
        y = radius_km * math.sin(angle)
        loc_type = "camp" if i == 0 else "town"
        pop = 50000 if i == 0 else ""
        locations.append({
            "name": f"node_{i}", "region": "R1", "country": "C1",
            "gps_x": x, "gps_y": y, "location_type": loc_type,
            "conflict_date": "", "pop/cap": pop,
        })
    names = [loc["name"] for loc in locations]
    # Source to all ring nodes
    for i in range(n):
        routes.append(("source", f"node_{i}", radius_km))
    # Ring connections
    for i in range(n):
        j = (i + 1) % n
        d = 2 * radius_km * math.sin(math.pi / n)
        routes.append((f"node_{i}", f"node_{j}", d))
    _write_locations(locations, output_dir)
    _write_routes(routes, output_dir)
    _write_closures(output_dir)
    conflicts = {"source": {0: 0.0, 1: 1.0}}
    for step in range(2, 73):
        conflicts["source"][step] = 1.0
    _write_conflicts(names, conflicts, output_dir)
    return {"n_locations": len(locations), "n_links": len(routes)}


def build_star(output_dir: Path, n_spokes: int = 6, spoke_km: float = 100.0) -> dict:
    """
    Source at hub, n_spokes leaves, one is camp.
    No lateral connectivity — pure hub-and-spoke.
    """
    output_dir = Path(output_dir)
    locations = []
    routes = []
    locations.append({
        "name": "source", "region": "R1", "country": "C1",
        "gps_x": 0.0, "gps_y": 0.0, "location_type": "conflict",
        "conflict_date": 1, "pop/cap": 10000,
    })
    for i in range(n_spokes):
        x = spoke_km if i == 0 else spoke_km * math.cos(2 * math.pi * i / n_spokes)
        y = 0.0 if i == 0 else spoke_km * math.sin(2 * math.pi * i / n_spokes)
        loc_type = "camp" if i == 0 else "town"
        pop = 50000 if i == 0 else ""
        locations.append({
            "name": f"spoke_{i}", "region": "R1", "country": "C1",
            "gps_x": x, "gps_y": y, "location_type": loc_type,
            "conflict_date": "", "pop/cap": pop,
        })
        routes.append(("source", f"spoke_{i}", spoke_km))
    names = [loc["name"] for loc in locations]
    _write_locations(locations, output_dir)
    _write_routes(routes, output_dir)
    _write_closures(output_dir)
    conflicts = {"source": {0: 0.0, 1: 1.0}}
    for step in range(2, 73):
        conflicts["source"][step] = 1.0
    _write_conflicts(names, conflicts, output_dir)
    return {"n_locations": len(locations), "n_links": len(routes)}


def build_fully_connected(output_dir: Path, nodes: int = None, max_radius_km: float = 200.0) -> dict:
    """All pairs within radius directly linked. Placeholder for Day 3."""
    if nodes is None:
        nodes = 6
    # Use simple layout: nodes on circle, link all pairs
    output_dir = Path(output_dir)
    locations = []
    routes = []
    radius = max_radius_km / 2
    for i in range(nodes):
        angle = 2 * math.pi * i / nodes
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        loc_type = "camp" if i == 0 else ("conflict" if i == 1 else "town")
        pop = 50000 if i == 0 else (10000 if i == 1 else "")
        locations.append({
            "name": f"node_{i}", "region": "R1", "country": "C1",
            "gps_x": x, "gps_y": y, "location_type": loc_type,
            "conflict_date": 1 if i == 1 else "", "pop/cap": pop,
        })
    names = [loc["name"] for loc in locations]
    for i in range(nodes):
        for j in range(i + 1, nodes):
            d = math.sqrt((locations[i]["gps_x"] - locations[j]["gps_x"])**2 +
                         (locations[i]["gps_y"] - locations[j]["gps_y"])**2)
            if d <= max_radius_km:
                routes.append((names[i], names[j], d))
    _write_locations(locations, output_dir)
    _write_routes(routes, output_dir)
    _write_closures(output_dir)
    conflicts = {names[1]: {0: 0.0, 1: 1.0}}
    for step in range(2, 73):
        conflicts[names[1]][step] = 1.0
    _write_conflicts(names, conflicts, output_dir)
    return {"n_locations": len(locations), "n_links": len(routes)}


def build_network(topology: str, output_dir: Path, **kwargs) -> dict:
    """
    Factory: 'linear' | 'ring' | 'star' | 'fully_connected'
    Returns network_stats dict.
    """
    output_dir = Path(output_dir)
    if topology == "linear":
        return build_linear(output_dir, **kwargs)
    elif topology == "ring":
        return build_ring(output_dir, **kwargs)
    elif topology == "star":
        return build_star(output_dir, **kwargs)
    elif topology == "fully_connected":
        return build_fully_connected(output_dir, **kwargs)
    else:
        raise ValueError(f"Unknown topology: {topology}")
