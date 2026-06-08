#!/usr/bin/env python3
"""Day 12 Task A — replace hand-curated TMI route distances with OSM road-km.

Routing method: OSRM (https://router.project-osrm.org) — this is the method
validated at the END of Day 11 (the committed figures/tmi/day11_network_map_osm.png
is OSRM-traced). OSRM avoids the one-way / divided-carriageway zig-zag artifact
that the raw osmnx.shortest_path(weight='travel_time') path can introduce, while
still being OSM-derived. osmnx travel-time routing is retained as an OFFLINE
FALLBACK so the script degrades gracefully without network access.

Outputs (originals preserved):
  input_data/tmi/routes_osm_day12.csv        <- new OSM distances
  input_data/tmi/routes_handcurated_day11.csv <- backup of the original routes.csv
  input_data/tmi/routes.csv                  <- overwritten with OSM distances

Cache: cache/tmi_osrm/<hash>.json (shared with the Day 11 plot script).
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"
OSRM_CACHE = REPO / "cache" / "tmi_osrm"
OSRM_HOST = os.environ.get("FLEE_OSRM_HOST", "https://router.project-osrm.org")


def _read_locations() -> dict[str, tuple[float, float]]:
    locs: dict[str, tuple[float, float]] = {}
    with (TMI / "locations.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            locs[row[0]] = (float(row[3]), float(row[4]))  # (lon, lat)
    return locs


def _read_routes() -> list[tuple[str, str, float, str]]:
    """Return (name1, name2, hand_curated_km, forced_redirection)."""
    out = []
    with (TMI / "routes.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            out.append((row[0], row[1], float(row[2]), row[3] if len(row) > 3 else "0"))
    return out


def _osrm_route(lon_a, lat_a, lon_b, lat_b, timeout=20) -> float:
    """Return OSRM driving distance (km). Cached by endpoint hash."""
    OSRM_CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(
        f"{lon_a:.6f},{lat_a:.6f}->{lon_b:.6f},{lat_b:.6f}".encode()
    ).hexdigest()[:16]
    cache_path = OSRM_CACHE / f"{key}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
    else:
        url = (
            f"{OSRM_HOST}/route/v1/driving/"
            f"{lon_a},{lat_a};{lon_b},{lat_b}"
            f"?overview=false&alternatives=false&steps=false"
        )
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        cache_path.write_text(json.dumps(data))
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM error: {data.get('code')}")
    return float(data["routes"][0]["distance"]) / 1000.0


def _build_osmnx_graph():
    """Fallback graph for offline osmnx travel-time routing (Day 11 method)."""
    import osmnx as ox

    north, south, east, west = 40.55, 39.78, -76.05, -77.45
    try:
        G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive")
    except TypeError:
        G = ox.graph_from_bbox(north, south, east, west, network_type="drive")
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    return G, ox


def _osmnx_route(G, ox, lon_a, lat_a, lon_b, lat_b) -> float:
    na = ox.distance.nearest_nodes(G, lon_a, lat_a)
    nb = ox.distance.nearest_nodes(G, lon_b, lat_b)
    path = ox.shortest_path(G, na, nb, weight="travel_time")
    total_m = 0.0
    for u, v in zip(path[:-1], path[1:]):
        total_m += float(G.edges[u, v, 0].get("length", 0.0))
    return total_m / 1000.0


def main() -> int:
    locs = _read_locations()
    routes = _read_routes()

    osm_km: dict[tuple[str, str], tuple[float, str]] = {}
    G = ox = None
    for a, b, hand_km, _fr in routes:
        la, lb = locs[a], locs[b]
        try:
            km = _osrm_route(la[0], la[1], lb[0], lb[1])
            src = "OSRM"
        except Exception as ex:
            print(f"  OSRM failed for {a}->{b} ({ex}); using osmnx fallback.",
                  file=sys.stderr)
            if G is None:
                G, ox = _build_osmnx_graph()
            km = _osmnx_route(G, ox, la[0], la[1], lb[0], lb[1])
            src = "osmnx_traveltime"
        osm_km[(a, b)] = (km, src)

    # Comparison table.
    print(f"\n{'route':32} {'hand_km':>9} {'osm_km':>9} {'delta_km':>9} {'pct':>8}  src")
    print("-" * 80)
    max_abs_delta = 0.0
    max_abs_route = ""
    n_changed = 0
    rows_out = []
    for a, b, hand_km, fr in routes:
        km, src = osm_km[(a, b)]
        delta = km - hand_km
        pct = (delta / hand_km * 100.0) if hand_km > 0 else float("nan")
        if abs(delta) > 1e-6:
            n_changed += 1
        if abs(delta) > abs(max_abs_delta):
            max_abs_delta = delta
            max_abs_route = f"{a}->{b}"
        print(f"{a + '->' + b:32} {hand_km:9.2f} {km:9.2f} {delta:9.2f} "
              f"{pct:7.1f}%  {src}")
        rows_out.append((a, b, f"{km:.3f}", fr))
    print("-" * 80)
    print(f"routes changed: {n_changed}/{len(routes)}   "
          f"max |delta|: {max_abs_delta:+.2f} km ({max_abs_route})")

    # Write routes_osm_day12.csv (same schema as routes.csv).
    osm_path = TMI / "routes_osm_day12.csv"
    with osm_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#name1", "name2", "distance", "forced_redirection"])
        for a, b, km_str, fr in rows_out:
            w.writerow([a, b, km_str, fr])
    print(f"\nWrote {osm_path}")

    # Preserve the hand-curated original, then promote OSM distances to routes.csv.
    backup = TMI / "routes_handcurated_day11.csv"
    if not backup.exists():
        shutil.copy2(TMI / "routes.csv", backup)
        print(f"Backed up original -> {backup}")
    else:
        print(f"Backup already exists -> {backup} (not overwritten)")
    shutil.copy2(osm_path, TMI / "routes.csv")
    print(f"Promoted OSM distances -> {TMI / 'routes.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
