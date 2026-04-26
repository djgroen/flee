"""
flee/conflict_potential.py

Precomputes a conflict potential field for the dual-process (System 1 /
System 2) model.

For each simulation day and each non-camp location, this module computes:
  - c_best_s1[day][loc]: minimum conflict reachable within awareness_level_s1 hops
  - c_best_s2[day][loc]: minimum conflict reachable within awareness_level_s2 hops
  - d_best_s1[day][loc]: cumulative km distance to that minimum-conflict node (System-1 depth)
  - d_best_s2[day][loc]: cumulative km distance to that minimum-conflict node (System-2 depth)

These replace the per-agent 1-hop c_best lookup in moving.py with an O(1) table query.
The System-2 depth is awareness_level_s1 + 1, capped at 3, matching the
System-2 override increment already in moving.py.

Input:
  conflict_grid : list[list[float]]  -- days x zones matrix from the conflict schedule.
                  Row index = simulation day (0-indexed). Column index matches zones list.
  zones         : list[str]          -- ordered zone (location) names.
  routes_path   : str                -- path to routes.csv for network topology.
  num_days      : int                -- simulation length (number of days to precompute).
  awareness_s1  : int                -- System-1 AwarenessLevel from simsetting.yml (typically 1).

Output:
  ConflictPotentialField object with a query method:
    .get(day, location_name, s2=False) -> (c_best: float, d_best: float)

Design notes:
  - BFS traversal uses the same link graph as FLEE route selection. Distance is
    accumulated in km by summing link distances (matching get_distance() in moving.py).
  - When no neighbor within k hops has lower conflict than the current location,
    c_best = c_here and d_best = 1.0 (matching the existing fallback in moving.py).
  - Conflict values are read directly from the conflict_grid, not from location objects,
    so this module is safe to call before flee.Ecosystem is initialized.
  - The graph is built once from routes.csv and reused across all days.
"""

from __future__ import annotations

import csv
import sys
from collections import deque
from typing import Dict, List, Optional, Tuple


def read_routes_graph(
    routes_path: str,
    zones: List[str],
) -> Dict[str, List[Tuple[str, float]]]:
    """Build an adjacency graph from routes.csv.

    Returns ``{location_name: [(neighbor_name, distance_km), ...]}`` for all
    locations that appear in ``zones``. Bidirectional links are added for both
    endpoints. Camp/unknown destinations may also appear as keys (so an agent
    can find a camp as the best destination), but their outgoing edges will be
    empty unless they are also in ``zones``.

    The routes.csv format is::

        #"name1","name2","distance",forced_redirection
        "A","B",10,0
    """
    zone_set = set(zones)
    graph: Dict[str, List[Tuple[str, float]]] = {z: [] for z in zones}

    with open(routes_path, newline="") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row:
                continue
            first = row[0].lstrip("\ufeff").strip()
            if not first or first.startswith("#"):
                continue
            try:
                n1 = row[0].strip().strip('"').strip("'")
                n2 = row[1].strip().strip('"').strip("'")
                dist = float(row[2].strip().strip('"'))
            except (IndexError, ValueError):
                continue
            if dist < 0:
                continue
            if n1 in zone_set:
                graph.setdefault(n1, []).append((n2, dist))
            if n2 in zone_set:
                graph.setdefault(n2, []).append((n1, dist))
    return graph


def _bfs_min_conflict(
    start: str,
    graph: Dict[str, List[Tuple[str, float]]],
    conflict_at: Dict[str, float],
    max_hops: int,
    return_name: bool = False,
) -> Tuple[float, float]:
    """BFS from ``start`` up to ``max_hops`` hops.

    Returns ``(c_best, d_best)`` where ``c_best`` is the minimum conflict found
    among all reachable nodes (including ``start``), and ``d_best`` is the
    cumulative km distance to that node (1.0 for start itself).

    If multiple nodes tie for minimum conflict, the closest one by distance is
    preferred (consistent with the safety-per-distance signal in sigma).

    If ``start`` has no links or ``max_hops == 0``, returns
    ``(conflict_at.get(start, 0.0), 1.0)``.
    """
    c_here = float(conflict_at.get(start, 0.0))
    if max_hops <= 0 or start not in graph or not graph[start]:
        if return_name:
            return c_here, 1.0, start  # type: ignore[return-value]
        return c_here, 1.0

    best_c = c_here
    best_d = 1.0
    best_name = start

    # Track shortest cumulative distance to each visited node within the hop
    # budget so we can revisit a node via a cheaper path if found.
    best_dist_to: Dict[str, float] = {start: 0.0}
    # Queue: (node, cumulative_distance_km, hops_used)
    queue: deque = deque([(start, 0.0, 0)])

    while queue:
        node, cum_d, hops = queue.popleft()
        if hops >= max_hops:
            continue
        for nbr, link_d in graph.get(node, ()):
            new_d = cum_d + max(0.0, link_d)
            prev = best_dist_to.get(nbr)
            if prev is not None and new_d >= prev:
                continue
            best_dist_to[nbr] = new_d

            c_n = float(conflict_at.get(nbr, 0.0))
            d_n = max(1.0, new_d)
            if (c_n < best_c) or (c_n == best_c and d_n < best_d):
                best_c = c_n
                best_d = d_n
                best_name = nbr

            queue.append((nbr, new_d, hops + 1))

    if return_name:
        return best_c, best_d, best_name  # type: ignore[return-value]
    return best_c, best_d


class ConflictPotentialField:
    """Precomputed lookup table for ``(c_best, d_best)`` by day and location.

    Usage::

        field = ConflictPotentialField.build(
            conflict_grid, zones, routes_path, num_days, awareness_s1,
        )
        c_best, d_best = field.get(day=3, location_name="Minamisoma", s2=True)
    """

    # Discretization map for Regime B (Day 6 §3): zone -> rounded conflict.
    # The keys ("inner", "mid", "outer") match the convention used by the
    # Fukushima drivers; "camp" and unknown destinations map to 0.0.
    ZONE_DISCRETIZATION: Dict[str, float] = {
        "inner": 0.9,
        "mid":   0.5,
        "outer": 0.1,
    }

    def __init__(
        self,
        table_s1: Dict[int, Dict[str, Tuple[float, float, str]]],
        table_s2: Dict[int, Dict[str, Tuple[float, float, str]]],
        num_days: int,
        zones: List[str],
        awareness_s1: int,
        awareness_s2: int,
        zone_of: Optional[Dict[str, str]] = None,
    ) -> None:
        self._s1 = table_s1
        self._s2 = table_s2
        self.num_days = num_days
        self.zones = list(zones)
        self.awareness_s1 = awareness_s1
        self.awareness_s2 = awareness_s2
        # Optional location -> administrative-zone map. Used by get() when
        # discretize_by_zone=True (Day 6 information regime contrast).
        self.zone_of: Dict[str, str] = dict(zone_of) if zone_of else {}
        # When True, every get() call discretizes by destination zone unless
        # the caller explicitly passes discretize_by_zone=False. Lets the
        # Day 6 information-regime runs swap regimes without touching
        # moving.py / _lookup_potential.
        self.discretize_default: bool = False

    @classmethod
    def build(
        cls,
        conflict_grid: List[List[float]],
        zones: List[str],
        routes_path: str,
        num_days: int,
        awareness_s1: int = 1,
        zone_of: Optional[Dict[str, str]] = None,
    ) -> "ConflictPotentialField":
        """Build the potential field for all days and all zone locations.

        ``awareness_s2 = min(3, awareness_s1 + 1)`` -- matches the S2_OVERRIDES
        AwarenessLevel increment already in moving.py.
        """
        if num_days <= 0:
            raise ValueError(f"num_days must be > 0, got {num_days}")
        if not zones:
            raise ValueError("zones list is empty")

        awareness_s1 = max(0, int(awareness_s1))
        awareness_s2 = min(3, awareness_s1 + 1)

        graph = read_routes_graph(routes_path, zones)

        table_s1: Dict[int, Dict[str, Tuple[float, float]]] = {}
        table_s2: Dict[int, Dict[str, Tuple[float, float]]] = {}

        for day in range(num_days):
            if day < len(conflict_grid):
                row = conflict_grid[day]
            else:
                row = conflict_grid[-1] if conflict_grid else []

            conflict_at: Dict[str, float] = {}
            for j, z in enumerate(zones):
                conflict_at[z] = float(row[j]) if j < len(row) else 0.0

            day_s1: Dict[str, Tuple[float, float, str]] = {}
            day_s2: Dict[str, Tuple[float, float, str]] = {}
            for z in zones:
                day_s1[z] = _bfs_min_conflict(
                    z, graph, conflict_at, awareness_s1, return_name=True)
                day_s2[z] = _bfs_min_conflict(
                    z, graph, conflict_at, awareness_s2, return_name=True)
            table_s1[day] = day_s1
            table_s2[day] = day_s2

        return cls(
            table_s1=table_s1,
            table_s2=table_s2,
            num_days=num_days,
            zones=zones,
            awareness_s1=awareness_s1,
            awareness_s2=awareness_s2,
            zone_of=zone_of,
        )

    def get(
        self,
        day: int,
        location_name: str,
        s2: bool = False,
        discretize_by_zone: Optional[bool] = None,
    ) -> Tuple[float, float]:
        """Return ``(c_best, d_best)`` for the given day and location.

        Falls back to ``(1.0, 1.0)`` -- maximum conflict, unit distance -- if the
        location is not in the table (e.g. it is a camp or was not in zones).
        This is conservative: an agent at an unknown location will behave as if
        no improvement is available, defaulting to System-1 heuristic response.

        ``discretize_by_zone`` (Day 6 §3 — Regime B): if True, the returned
        ``c_best`` is rounded to ``ZONE_DISCRETIZATION[zone]`` of the
        destination node where the BFS optimum was found, using the
        ``zone_of`` map provided at build time. ``d_best`` is unchanged.
        Falls back to the continuous c_best if the destination's zone is not
        registered in ``zone_of``.
        """
        table = self._s2 if s2 else self._s1
        if not table:
            return (1.0, 1.0)
        if day < 0:
            day = 0
        elif day >= self.num_days:
            day = self.num_days - 1
        day_table = table.get(day)
        if day_table is None:
            return (1.0, 1.0)
        entry = day_table.get(location_name)
        if entry is None:
            return (1.0, 1.0)
        # Stored as (c_best, d_best, best_name); legacy 2-tuples are tolerated.
        if len(entry) == 2:
            c_best, d_best = entry  # type: ignore[misc]
            best_name = location_name
        else:
            c_best, d_best, best_name = entry
        do_disc = self.discretize_default if discretize_by_zone is None \
            else bool(discretize_by_zone)
        if do_disc and self.zone_of:
            zone = self.zone_of.get(best_name)
            if zone in self.ZONE_DISCRETIZATION:
                c_best = self.ZONE_DISCRETIZATION[zone]
        return c_best, d_best


def read_zone_map_from_locations(
    locations_path: str,
    inner_km: float = 20.0,
    mid_km: float = 30.0,
    plant_lon: float = 141.033,
    plant_lat: float = 37.421,
) -> Dict[str, str]:
    """Compute a per-location administrative-zone map from locations.csv.

    Reads ``gps_x`` (longitude) and ``gps_y`` (latitude) from each row and
    classifies each location by great-circle distance from the Fukushima
    Daiichi plant: ``inner`` (≤ inner_km), ``mid`` (≤ mid_km), ``outer``
    (otherwise). Camp locations (``location_type == "camp"``) get ``outer``,
    consistent with the Day 6 §3 information-regime definition.

    No hard-coded zone assignments — the map is derived purely from the
    coordinates already present in the input file.
    """
    import math

    R_EARTH_KM = 6371.0

    def _haversine_km(lon1, lat1, lon2, lat2):
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = (math.sin(dphi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
        return 2 * R_EARTH_KM * math.asin(min(1.0, math.sqrt(a)))

    out: Dict[str, str] = {}
    with open(locations_path, newline="") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row or row[0].strip().startswith("#"):
                continue
            try:
                name = row[0].strip().strip('"')
                lon = float(row[3])
                lat = float(row[4])
                ltype = row[5].strip().strip('"') if len(row) > 5 else ""
            except (IndexError, ValueError):
                continue
            d = _haversine_km(plant_lon, plant_lat, lon, lat)
            if ltype == "camp":
                zone = "outer"
            elif d <= inner_km:
                zone = "inner"
            elif d <= mid_km:
                zone = "mid"
            else:
                zone = "outer"
            out[name] = zone
    return out


def _read_conflict_grid_csv(path: str) -> Tuple[List[str], List[List[float]]]:
    """Read a wide-format conflict CSV: ``Day, loc1, loc2, ...``.

    Returns ``(zones, grid)`` where ``zones`` is the ordered list of column
    names (excluding ``Day``) and ``grid[day_index]`` is the list of conflict
    values for that day, in the same column order.
    """
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        header[0] = header[0].lstrip("\ufeff")
        zones = [h.strip() for h in header[1:]]
        grid: List[List[float]] = []
        for row in reader:
            if not row or not row[0].strip():
                continue
            try:
                vals = [float(x) for x in row[1:]]
            except ValueError:
                continue
            grid.append(vals)
    return zones, grid


def _main() -> int:
    """CLI: build the field from a conflicts.csv + routes.csv pair, print summary."""
    import argparse

    ap = argparse.ArgumentParser(description="Build ConflictPotentialField and print summary")
    ap.add_argument("--conflicts", required=True, help="Path to conflicts.csv (wide format)")
    ap.add_argument("--routes", required=True, help="Path to routes.csv")
    ap.add_argument("--num-days", type=int, default=None, help="Override number of days")
    ap.add_argument("--awareness-s1", type=int, default=1)
    ap.add_argument("--preview-days", type=int, default=5)
    args = ap.parse_args()

    zones, grid = _read_conflict_grid_csv(args.conflicts)
    num_days = args.num_days if args.num_days is not None else len(grid)
    field = ConflictPotentialField.build(
        conflict_grid=grid,
        zones=zones,
        routes_path=args.routes,
        num_days=num_days,
        awareness_s1=args.awareness_s1,
    )

    header = ("day", "location", "c_here", "c_best_s1", "d_best_s1",
              "c_best_s2", "d_best_s2")
    print(",".join(header))
    days_to_show = min(args.preview_days, num_days)
    for day in range(days_to_show):
        row_vals = grid[day] if day < len(grid) else grid[-1]
        for j, loc in enumerate(zones):
            c_here = row_vals[j] if j < len(row_vals) else 0.0
            c_s1, d_s1 = field.get(day, loc, s2=False)
            c_s2, d_s2 = field.get(day, loc, s2=True)
            print(f"{day},{loc},{c_here:.3f},{c_s1:.3f},{d_s1:.1f},{c_s2:.3f},{d_s2:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
