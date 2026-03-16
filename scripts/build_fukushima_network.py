#!/usr/bin/env python3
"""
Build Fukushima 2011 conflict input from OSM road network.

Extracts road network, snaps municipalities to nearest nodes, computes
shortest-path distances, and writes all flee input files to
conflict_input/fukushima_2011/.

Usage: python scripts/build_fukushima_network.py
Run from repository root.
"""

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT))

# NPP location
NPP_LAT, NPP_LON = 37.4213, 141.0329

# Simulation parameters
TIMESTEP_HOURS = 2.0
T0_DATETIME = "2011-03-11 14:46"  # earthquake onset

# Evacuation order timesteps (hours since t=0 / TIMESTEP_HOURS, rounded up)
ORDERS = {
    "step_3km": 4,   # t=6.6h  -> step 3.3 -> step 4
    "step_10km": 8,  # t=15.0h -> step 7.5 -> step 8
    "step_20km": 14, # t=27.6h -> step 13.8 -> step 14
}

# Municipality definitions: name -> (lat, lon, location_type, population_2010)
# Population from 2010 Japanese census, residential (not daytime)
MUNICIPALITIES = {
    "Futaba": (37.4372, 141.0056, "conflict", 6900),
    "Okuma": (37.4067, 141.0278, "conflict", 11500),
    "Namie": (37.4833, 141.0000, "conflict", 20500),
    "Tomioka": (37.3431, 141.0167, "town", 15800),
    "Naraha": (37.2833, 141.0167, "town", 7700),
    "Minamisoma": (37.6417, 140.9578, "town", 70000),
    "Kawauchi": (37.3333, 140.8167, "town", 2800),
    "Iitate": (37.6500, 140.8000, "town", 6200),
    "Koriyama": (37.4019, 140.3633, "camp", 0),
    "Iwaki": (37.0500, 140.8833, "camp", 0),
    "Fukushima_City": (37.7608, 140.4747, "camp", 0),
    "Sendai": (38.2688, 140.8721, "camp", 0),
}

# Conflict intensity by zone and order step
CONFLICT_SCHEDULE = {
    "Futaba": [(1, 1.0)],
    "Okuma": [(1, 1.0)],
    "Namie": [(1, 0.8), (8, 1.0)],
    "Tomioka": [(8, 0.8), (14, 1.0)],
    "Naraha": [(8, 0.8), (14, 1.0)],
    "Minamisoma": [(14, 0.5)],
    "Iitate": [(14, 0.8)],
    "Kawauchi": [(14, 0.3)],
}

# Hardcoded fallback distances (km) when OSMnx fails - from Google Maps road distances
FALLBACK_DISTANCES = [
    ("Futaba", "Okuma", 5.2),
    ("Futaba", "Namie", 8.1),
    ("Futaba", "Tomioka", 12.3),
    ("Futaba", "Naraha", 18.5),
    ("Futaba", "Minamisoma", 28.0),
    ("Futaba", "Kawauchi", 22.0),
    ("Futaba", "Iitate", 35.0),
    ("Futaba", "Koriyama", 55.0),
    ("Futaba", "Iwaki", 45.0),
    ("Futaba", "Fukushima_City", 65.0),
    ("Futaba", "Sendai", 95.0),
    ("Okuma", "Namie", 10.0),
    ("Okuma", "Tomioka", 11.0),
    ("Okuma", "Naraha", 16.0),
    ("Okuma", "Minamisoma", 25.0),
    ("Okuma", "Kawauchi", 25.0),
    ("Okuma", "Iitate", 38.0),
    ("Okuma", "Koriyama", 52.0),
    ("Okuma", "Iwaki", 42.0),
    ("Okuma", "Fukushima_City", 62.0),
    ("Okuma", "Sendai", 92.0),
    ("Namie", "Tomioka", 18.0),
    ("Namie", "Naraha", 24.0),
    ("Namie", "Minamisoma", 22.0),
    ("Namie", "Kawauchi", 32.0),
    ("Namie", "Iitate", 28.0),
    ("Namie", "Koriyama", 48.0),
    ("Namie", "Iwaki", 52.0),
    ("Namie", "Fukushima_City", 58.0),
    ("Namie", "Sendai", 88.0),
    ("Tomioka", "Naraha", 8.0),
    ("Tomioka", "Minamisoma", 35.0),
    ("Tomioka", "Kawauchi", 22.0),
    ("Tomioka", "Iitate", 42.0),
    ("Tomioka", "Koriyama", 48.0),
    ("Tomioka", "Iwaki", 38.0),
    ("Tomioka", "Fukushima_City", 58.0),
    ("Tomioka", "Sendai", 88.0),
    ("Naraha", "Minamisoma", 42.0),
    ("Naraha", "Kawauchi", 28.0),
    ("Naraha", "Iitate", 48.0),
    ("Naraha", "Koriyama", 55.0),
    ("Naraha", "Iwaki", 32.0),
    ("Naraha", "Fukushima_City", 65.0),
    ("Naraha", "Sendai", 95.0),
    ("Minamisoma", "Kawauchi", 45.0),
    ("Minamisoma", "Iitate", 35.0),
    ("Minamisoma", "Koriyama", 42.0),
    ("Minamisoma", "Iwaki", 62.0),
    ("Minamisoma", "Fukushima_City", 55.0),
    ("Minamisoma", "Sendai", 65.0),
    ("Kawauchi", "Iitate", 38.0),
    ("Kawauchi", "Koriyama", 55.0),
    ("Kawauchi", "Iwaki", 48.0),
    ("Kawauchi", "Fukushima_City", 65.0),
    ("Kawauchi", "Sendai", 105.0),
    ("Iitate", "Koriyama", 55.0),
    ("Iitate", "Iwaki", 72.0),
    ("Iitate", "Fukushima_City", 65.0),
    ("Iitate", "Sendai", 95.0),
    ("Koriyama", "Iwaki", 55.0),
    ("Koriyama", "Fukushima_City", 65.0),
    ("Koriyama", "Sendai", 95.0),
    ("Iwaki", "Fukushima_City", 85.0),
    ("Iwaki", "Sendai", 125.0),
    ("Fukushima_City", "Sendai", 95.0),
]

MAX_ROUTE_KM = 150
OUTPUT_DIR = REPO_ROOT / "conflict_input" / "fukushima_2011"


def verify_movechance_scaling():
    """Print movechance-to-daily-rate conversion for 2h timestep."""
    TIMESTEP_HOURS = 2.0
    checks = [
        ("conflict", 0.25, "~84% daily departure under conflict orders"),
        ("default", 0.005, "~5.5% daily departure (shelter-in-place)"),
        ("camp", 0.001, "~1.2% daily departure (near-zero)"),
    ]
    print("\n[MOVECHANCE SCALING VERIFICATION] (2h timestep)")
    for label, p, note in checks:
        f_daily = 1.0 - (1.0 - p) ** (24.0 / TIMESTEP_HOURS)
        print(f"  {label}_movechance={p} -> {f_daily:.1%} daily  ({note})")
    print()


def extract_network():
    """Download OSM road network."""
    try:
        import osmnx as ox
    except ImportError:
        return None
    print("Downloading OSM road network (45km radius from NPP)...")
    try:
        G = ox.graph_from_point(
            (NPP_LAT, NPP_LON),
            dist=45000,
            network_type="drive",
            custom_filter='["highway"~"motorway|trunk|primary|secondary"]'
        )
        G_proj = ox.project_graph(G)
        print(f"  Network: {len(G_proj.nodes)} nodes, {len(G_proj.edges)} edges")
        return G_proj
    except Exception as e:
        print(f"  OSMnx failed: {e}")
        return None


def snap_municipalities(G_proj):
    """Snap each municipality centroid to nearest network node."""
    import osmnx as ox
    from shapely.geometry import Point

    snapped = {}
    for name, (lat, lon, loc_type, pop) in MUNICIPALITIES.items():
        point = ox.projection.project_geometry(
            Point(lon, lat),
            crs="EPSG:4326",
            to_crs=G_proj.graph["crs"]
        )[0]
        node = ox.distance.nearest_nodes(G_proj, point.x, point.y)
        snapped[name] = node
        print(f"  {name}: snapped to node {node}")
    return snapped


def compute_distances(G_proj, snapped):
    """Compute shortest road distances (km) between all municipality pairs."""
    import networkx as nx
    import pandas as pd

    rows = []
    names = list(snapped.keys())
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            try:
                dist_m = nx.shortest_path_length(
                    G_proj,
                    snapped[name_a],
                    snapped[name_b],
                    weight="length"
                )
                dist_km = round(dist_m / 1000, 1)
                if dist_km < MAX_ROUTE_KM:
                    rows.append((name_a, name_b, dist_km))
                    print(f"  {name_a} -> {name_b}: {dist_km} km")
                else:
                    print(f"  {name_a} -> {name_b}: {dist_km} km (SKIP - exceeds {MAX_ROUTE_KM}km)")
            except nx.NetworkXNoPath:
                print(f"  WARNING: No path {name_a} -> {name_b}, skipping")
    return pd.DataFrame(rows, columns=["name1", "name2", "distance"])


def use_fallback_distances():
    """Use hardcoded fallback distances when OSMnx fails."""
    import pandas as pd

    print("WARNING: OSMnx failed. Using hardcoded fallback distances from Google Maps.")
    rows = []
    for a, b, d in FALLBACK_DISTANCES:
        if d < MAX_ROUTE_KM:
            rows.append({"name1": a, "name2": b, "distance": d})
    df = pd.DataFrame(rows)
    fallback_path = OUTPUT_DIR / "distances_fallback.csv"
    df.to_csv(fallback_path, index=False)
    print(f"Wrote {fallback_path} for documentation")
    return df


def write_flee_inputs(routes_df):
    """Write all four flee input files."""
    import pandas as pd

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # locations.csv - flee 3.0 format. conflict_intensity=0 so conflicts.csv controls onset
    loc_rows = []
    for name, (lat, lon, loc_type, pop) in MUNICIPALITIES.items():
        loc_rows.append({
            "name": name,
            "region": "Fukushima",
            "country": "Japan",
            "gps_x": lon,
            "gps_y": lat,
            "location_type": loc_type,
            "conflict_date": -1,
            "pop/cap": pop if loc_type in ("conflict", "town") else 500000,
            "conflict_intensity": 0,  # conflicts.csv controls onset; avoid default 1.0
        })
    loc_df = pd.DataFrame(loc_rows)
    loc_path = OUTPUT_DIR / "locations.csv"
    # flee expects header to start with # to skip it. First 8 cols fixed; conflict_intensity is attribute
    with open(loc_path, "w") as f:
        f.write("#" + ",".join(loc_df.columns) + "\n")
        for _, row in loc_df.iterrows():
            f.write(",".join(str(v) for v in row) + "\n")
    print(f"Wrote {loc_path} ({len(loc_rows)} locations)")

    # routes.csv - flee 3.0 format with forced_redirection
    route_rows = []
    for _, row in routes_df.iterrows():
        route_rows.append({
            "name1": row["name1"],
            "name2": row["name2"],
            "distance": row["distance"],
            "forced_redirection": 0,
        })
    route_df = pd.DataFrame(route_rows)
    route_path = OUTPUT_DIR / "routes.csv"
    with open(route_path, "w") as f:
        f.write("#" + ",".join(route_df.columns) + "\n")
        for _, row in route_df.iterrows():
            f.write(",".join(str(v) for v in row) + "\n")
    print(f"Wrote {route_path} ({len(route_rows)} routes)")

    # conflicts.csv - flee format: rows=timesteps, columns=locations
    # Need one row per timestep. Steps 0-36 (37 rows) for loop t=1..36
    N_STEPS = 37
    conflict_locs = list(CONFLICT_SCHEDULE.keys())
    conflict_names = [n for n in MUNICIPALITIES if n in conflict_locs or MUNICIPALITIES[n][2] in ("conflict", "town")]
    all_locs = list(MUNICIPALITIES.keys())
    conflict_cols = [n for n in all_locs if n in CONFLICT_SCHEDULE]

    # Build conflict value for each (location, step)
    def get_conflict(name, step):
        if name not in CONFLICT_SCHEDULE:
            return 0.0
        val = 0.0
        for s, intensity in CONFLICT_SCHEDULE[name]:
            if step >= s:
                val = intensity
        return val

    conflict_rows = []
    for step in range(N_STEPS):
        row = {col: get_conflict(col, step) for col in conflict_cols}
        conflict_rows.append(row)

    # flee format: #Day, Loc1, Loc2, ...
    conflicts_path = OUTPUT_DIR / "conflicts.csv"
    with open(conflicts_path, "w") as f:
        header = "#Day," + ",".join(conflict_cols)
        f.write(header + "\n")
        for step in range(N_STEPS):  # 0-36 inclusive
            vals = [str(get_conflict(c, step)) for c in conflict_cols]
            f.write(f"{step}," + ",".join(vals) + "\n")
    print(f"Wrote conflicts.csv ({len(conflict_rows)} timesteps, {len(conflict_cols)} conflict locations)")

    # Print conflict schedule
    print("\nConflict schedule (step, intensity):")
    for name, schedule in CONFLICT_SCHEDULE.items():
        for step, intensity in schedule:
            print(f"  {name}: step {step} -> {intensity}")

    # closures.csv - header with # so flee skips it
    with open(OUTPUT_DIR / "closures.csv", "w") as f:
        f.write("#closure_type,name1,name2,closure_start,closure_end\n")
    print("Wrote closures.csv (empty)")

    # simsetting.yml
    simsetting = """# Fukushima 2011 — realistic municipality network
# Timestep: 2 hours. Simulation period: 72h = 36 steps after crisis onset.
# Conflict onset via conflicts.csv (evacuation orders as step changes).

move_rules:
  max_move_speed: 40.0        # km/timestep (2h): ~20 km/h avg under congestion
  max_walk_speed: 7.0         # km/timestep: 3.5 km/h walking
  conflict_movechance: 0.5
  camp_movechance: 0.001
  default_movechance: 0.3
  awareness_level: 2          # look-ahead 2 links for S2 routing
  two_system_decision_making: true
  s1s2_model:
    alpha: 2.0
    beta: 4.0
    kappa: 5.0

spawn_rules:
  take_from_population: True
  insert_day0: True

log_levels:
  agent: 0
  link: 0
  camp: 0
  conflict: 0
  init: 0
"""
    with open(OUTPUT_DIR / "simsetting.yml", "w") as f:
        f.write(simsetting)
    print("Wrote simsetting.yml")


def main():
    print("=== Building Fukushima 2011 network ===\n")

    G_proj = extract_network()
    if G_proj is None:
        routes_df = use_fallback_distances()
    else:
        snapped = snap_municipalities(G_proj)
        routes_df = compute_distances(G_proj, snapped)
        if routes_df.empty:
            print("No routes from OSM; falling back to hardcoded distances")
            routes_df = use_fallback_distances()

    print("\n=== Distance matrix (km) ===")
    for _, row in routes_df.iterrows():
        print(f"  {row['name1']} <-> {row['name2']}: {row['distance']} km")

    print(f"\nTotal routes (< {MAX_ROUTE_KM} km): {len(routes_df)}")

    write_flee_inputs(routes_df)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
