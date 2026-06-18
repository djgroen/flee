#!/usr/bin/env python3
"""Day 15 Task A — build input_data/tmi_v2/ with ZONE-INDEPENDENT camp access.

The Day-14 calibration was confounded by camp adjacency: the big OUTER towns
(york, lancaster) sat ~1 hop / ~2.4 km from their own camp, inflating outer
evacuation and inverting the zone gradient. This script rebuilds the destination
camps as three DISTANT directional shelters at real evacuation-geography cities
(destination_map_g6), each reachable ONLY through the Harrisburg transit hub, so
camp access is dominated by a common long leg and is comparable across zones.

ORIGINAL input_data/tmi/ is left untouched (reproducibility of Days 11-14).

Outputs:
  input_data/tmi_v2/                      full copy of tmi/ with camps relocated
  results/tmi/day15_topology_checkpointA.csv   per-zone nearest-camp on v2

Checkpoint A: cross-zone nearest-camp spread < 2x (no zone has a >2x advantage).
"""
from __future__ import annotations

import csv
import hashlib
import json
import heapq
import math
import os
import shutil
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"
TMI_V2 = REPO / "input_data" / "tmi_v2"
RES = REPO / "results" / "tmi"
OSRM_CACHE = REPO / "cache" / "tmi_osrm"
OSRM_HOST = os.environ.get("FLEE_OSRM_HOST", "https://router.project-osrm.org")

PLANT_LON, PLANT_LAT = -76.726, 40.153
INNER_MAX_MI, MIDDLE_MAX_MI = 6.0, 12.0

# Distant directional shelter camps (destination_map_g6 cities).
# (name, lon, lat, capacity, direction)
NEW_CAMPS = [
    ("statecollege_camp", -77.860, 40.793, 200000, "NW"),
    ("philadelphia_camp", -75.164, 39.953, 200000, "SE"),
    ("baltimore_camp",    -76.612, 39.290, 200000, "S"),
]
HUB = "harrisburg"  # the documented "transit only" funnel hub
OLD_CAMPS = {"harrisburg_camp", "lancaster_camp", "york_camp"}


def haversine_mi(lon1, lat1, lon2, lat2):
    R = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def osrm_km(lon_a, lat_a, lon_b, lat_b, timeout=20):
    OSRM_CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(
        f"{lon_a:.6f},{lat_a:.6f}->{lon_b:.6f},{lat_b:.6f}".encode()
    ).hexdigest()[:16]
    cache_path = OSRM_CACHE / f"{key}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
    else:
        url = (f"{OSRM_HOST}/route/v1/driving/"
               f"{lon_a},{lat_a};{lon_b},{lat_b}"
               f"?overview=false&alternatives=false&steps=false")
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        cache_path.write_text(json.dumps(data))
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM error: {data.get('code')}")
    return float(data["routes"][0]["distance"]) / 1000.0


def camp_leg_km(lon_a, lat_a, lon_b, lat_b):
    """OSM road-km for the long camp leg; haversine*1.3 circuity fallback."""
    try:
        return osrm_km(lon_a, lat_a, lon_b, lat_b), "OSRM"
    except Exception as ex:
        km = haversine_mi(lon_a, lat_a, lon_b, lat_b) * 1.60934 * 1.3
        print(f"  OSRM failed ({ex}); haversine*1.3 fallback -> {km:.1f} km",
              file=sys.stderr)
        return km, "haversine*1.3"


def read_locations(path):
    """Return list of raw rows and a dict name -> (lon, lat, ltype)."""
    rows, info = [], {}
    with (path / "locations.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            rows.append(row)
            if not row or row[0].startswith("#"):
                continue
            info[row[0]] = (float(row[3]), float(row[4]), row[5])
    return rows, info


def zone_of(lon, lat):
    d = haversine_mi(PLANT_LON, PLANT_LAT, lon, lat)
    return ("inner" if d <= INNER_MAX_MI
            else "middle" if d <= MIDDLE_MAX_MI else "outer")


def dijkstra(adj, src):
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, math.inf):
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def hop_count(adj, src, dst):
    """Min hops (unit edges) from src to dst via BFS."""
    from collections import deque
    seen = {src}
    q = deque([(src, 0)])
    while q:
        u, h = q.popleft()
        if u == dst:
            return h
        for v, _w in adj.get(u, []):
            if v not in seen:
                seen.add(v)
                q.append((v, h + 1))
    return math.inf


def main():
    if TMI_V2.exists():
        shutil.rmtree(TMI_V2)
    shutil.copytree(TMI, TMI_V2)
    print(f"[A] copied {TMI} -> {TMI_V2} (original preserved)")

    loc_rows, info = read_locations(TMI)
    hub_lon, hub_lat, _ = info[HUB]

    # --- rewrite locations.csv: drop old camps, add distant camps ---
    out_rows = []
    for row in loc_rows:
        if row and not row[0].startswith("#") and row[0] in OLD_CAMPS:
            continue
        out_rows.append(row)
    for name, lon, lat, cap, _dir in NEW_CAMPS:
        out_rows.append([name, "PA", "USA", f"{lon}", f"{lat}", "camp", "-1",
                         f"{cap}"])
    with (TMI_V2 / "locations.csv").open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out_rows)

    # --- rewrite routes.csv: drop adjacent camp links, add hub->camp legs ---
    route_rows = []
    camp_leg_srcs = {}
    with (TMI / "routes.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                route_rows.append(row)
                continue
            if row[0] in OLD_CAMPS or row[1] in OLD_CAMPS:
                continue
            route_rows.append(row)
    for name, lon, lat, _cap, _dir in NEW_CAMPS:
        km, src = camp_leg_km(hub_lon, hub_lat, lon, lat)
        camp_leg_srcs[name] = (km, src)
        route_rows.append([HUB, name, f"{km:.3f}", "0"])
    with (TMI_V2 / "routes.csv").open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(route_rows)

    print("[A] hub camp legs (km):")
    for name, (km, src) in camp_leg_srcs.items():
        sl = haversine_mi(PLANT_LON, PLANT_LAT,
                          dict((n, (lo, la)) for n, lo, la, *_ in NEW_CAMPS)[name][0],
                          dict((n, (lo, la)) for n, lo, la, *_ in NEW_CAMPS)[name][1])
        print(f"     {HUB}->{name:18s} {km:8.2f} km  ({src})  "
              f"plant straight-line {sl:.1f} mi")

    # --- build undirected adjacency on v2 for nearest-camp checkpoint ---
    adj = {}
    camps = {n for n, *_ in NEW_CAMPS}
    towns = []
    _, info_v2 = read_locations(TMI_V2)
    with (TMI_V2 / "routes.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            a, b, w = row[0], row[1], float(row[2])
            adj.setdefault(a, []).append((b, w))
            adj.setdefault(b, []).append((a, w))
    for name, (lon, lat, ltype) in info_v2.items():
        if ltype != "camp":
            towns.append(name)

    # --- per-town nearest-camp, then per-zone summary ---
    rows_cp = []
    for t in sorted(towns):
        lon, lat, _ = info_v2[t]
        z = zone_of(lon, lat)
        dist = dijkstra(adj, t)
        best_km, best_camp = math.inf, None
        for c in camps:
            if dist.get(c, math.inf) < best_km:
                best_km, best_camp = dist[c], c
        hops = hop_count(adj, t, best_camp)
        rows_cp.append({"town": t, "zone": z, "nearest_camp": best_camp,
                        "nearest_camp_km": round(best_km, 3), "hops": hops})

    RES.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    df = pd.DataFrame(rows_cp)
    df.to_csv(RES / "day15_topology_checkpointA.csv", index=False)

    print("\n[A] per-town nearest-camp on v2:")
    for r in rows_cp:
        print(f"     {r['town']:16s} {r['zone']:6s} -> {r['nearest_camp']:18s}"
              f" {r['nearest_camp_km']:8.2f} km  {r['hops']} hops")

    zmean = df.groupby("zone")["nearest_camp_km"].mean()
    print("\n[A] per-zone mean nearest-camp (km):")
    for z in ["inner", "middle", "outer"]:
        if z in zmean.index:
            print(f"     {z:6s}: {zmean[z]:.1f}")
    tmin, tmax = df["nearest_camp_km"].min(), df["nearest_camp_km"].max()
    zmin, zmax = zmean.min(), zmean.max()
    town_spread = tmax / tmin
    zone_spread = zmax / zmin
    print(f"\n[A] per-TOWN spread  max/min = {tmax:.1f}/{tmin:.1f} = "
          f"{town_spread:.2f}x")
    print(f"[A] per-ZONE  spread  max/min = {zmax:.1f}/{zmin:.1f} = "
          f"{zone_spread:.2f}x")
    ok = zone_spread < 2.0
    print(f"\nCHECKPOINT A (cross-zone camp access < 2x): "
          f"{'PASS' if ok else 'FAIL'}  (zone spread {zone_spread:.2f}x)")
    # also assert no single zone enjoys a >2x advantage town-wise within a zone
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
