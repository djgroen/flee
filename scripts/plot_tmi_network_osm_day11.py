#!/usr/bin/env python3
"""TMI network map: OSM roads when available, else straight-line fallback.

Set ``FLEE_TMI_OSM=1`` to download and plot OSM geometry (slow, needs network).
Default is static geometry so CI and offline runs finish quickly.
"""

from __future__ import annotations

import csv
import os
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from pyproj import Transformer

# Web Mercator transformer — matches Fukushima F5_network_roads_osm.png CRS
# and gives contextily its native projection (full-color OSM tiles).
_T_FWD = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
_T_INV = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)


def _to_merc(lon, lat):
    return _T_FWD.transform(lon, lat)

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"
FIG = REPO / "figures" / "tmi"
OSRM_CACHE = REPO / "cache" / "tmi_osrm"
OSRM_HOST = os.environ.get(
    "FLEE_OSRM_HOST", "https://router.project-osrm.org"
)


def _osrm_route(lon_a, lat_a, lon_b, lat_b, timeout=20):
    """Fetch a driving route from OSRM. Returns (coords_lonlat, distance_m)
    or raises on failure. Cached to disk by endpoint hash."""
    import hashlib
    import json as _json
    import urllib.request

    OSRM_CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(
        f"{lon_a:.6f},{lat_a:.6f}->{lon_b:.6f},{lat_b:.6f}".encode()
    ).hexdigest()[:16]
    cache_path = OSRM_CACHE / f"{key}.json"
    if cache_path.exists():
        data = _json.loads(cache_path.read_text())
    else:
        url = (
            f"{OSRM_HOST}/route/v1/driving/"
            f"{lon_a},{lat_a};{lon_b},{lat_b}"
            f"?overview=full&geometries=geojson&alternatives=false&steps=false"
        )
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = _json.loads(resp.read().decode())
        cache_path.write_text(_json.dumps(data))
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM error: {data.get('code')} {data.get('message','')}")
    rt = data["routes"][0]
    coords = rt["geometry"]["coordinates"]  # [[lon, lat], ...]
    return coords, float(rt["distance"])

NAVY = "#1F3864"
BLUE = "#2E5FA3"
LTBLUE = "#D6E4F7"
GOLD = "#C9A227"
RED = "#C00000"
ORANGE = "#C55A11"
GREEN = "#375623"

INNER = {"middletown", "goldsboro", "royalton"}
MIDDLE = {
    "elizabethtown",
    "hershey",
    "harrisburg",
    "steelton",
    "new_cumberland",
}
OUTER = {"york", "lancaster", "carlisle", "lebanon"}
PLANT_LON, PLANT_LAT = -76.726, 40.153


def _zone(name: str) -> str:
    if name in INNER:
        return "inner"
    if name in MIDDLE:
        return "middle"
    if name in OUTER:
        return "outer"
    if name.endswith("_camp"):
        return "camp"
    return "other"


def _pair_route_color(a: str, b: str) -> tuple:
    za, zb = _zone(a), _zone(b)
    if za == "camp" or zb == "camp":
        return GREEN, 1.5, "--"
    if za == "inner" or zb == "inner":
        if za in ("inner", "middle") or zb in ("inner", "middle"):
            return RED, 2.5, "-"
    if za == "middle" and zb == "middle":
        return ORANGE, 2.5, "-"
    if (za == "middle" and zb == "outer") or (za == "outer" and zb == "middle"):
        return BLUE, 2.5, "-"
    return BLUE, 2.5, "-"


def _read_locations():
    rows = []
    with (TMI / "locations.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            name = row[0]
            lon, lat = float(row[3]), float(row[4])
            pop = int(row[7]) if row[7] else 0
            rows.append((name, lon, lat, pop, row[5]))
    return {r[0]: r for r in rows}


def _read_routes():
    out = []
    with (TMI / "routes.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            out.append((row[0], row[1], float(row[2])))
    return out


def _plot_static(ax, locs, routes):
    for a, b, dist in routes:
        la, lb = locs[a], locs[b]
        xa, ya = _to_merc(la[1], la[2])
        xb, yb = _to_merc(lb[1], lb[2])
        col, lw, ls = _pair_route_color(a, b)
        ax.plot(
            [xa, xb], [ya, yb],
            color=col, linewidth=lw, linestyle=ls,
            alpha=0.85, zorder=4,
        )
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        ax.annotate(
            f"{dist:.1f} km", (mx, my), fontsize=7,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9),
            zorder=5,
        )


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    locs = _read_locations()
    routes = _read_routes()
    emp_path = TMI / "tmi_empirical_data.json"
    with emp_path.open(encoding="utf-8") as f:
        empirical = json.load(f)

    use_osm = os.environ.get("FLEE_TMI_OSM", "").lower() in ("1", "true", "yes")
    if use_osm:
        try:
            import osmnx as ox  # noqa: F401
        except Exception:
            use_osm = False
            print("WARNING: osmnx unavailable — using straight-line routes.", file=sys.stderr)
    if not use_osm:
        print("INFO: Using straight-line routes (set FLEE_TMI_OSM=1 for OSM).", file=sys.stderr)

    # Tile basemap (contextily) — mirrors Fukushima F5_network_map_osm.png.
    # FLEE_TMI_BASEMAP=0 disables, otherwise enabled when contextily is importable.
    use_basemap = os.environ.get("FLEE_TMI_BASEMAP", "1").lower() in ("1", "true", "yes")
    cx = None
    if use_basemap:
        try:
            import contextily as cx  # type: ignore
        except Exception:
            use_basemap = False
            cx = None
            print("WARNING: contextily unavailable — no tile basemap.", file=sys.stderr)

    fig, ax = plt.subplots(figsize=(16, 12), dpi=150)
    fig.patch.set_facecolor("white")

    osm_road_segments = []  # populated when osmnx is available; reused for static
    if use_osm:
        try:
            import osmnx as ox

            north, south, east, west = 40.55, 39.78, -76.05, -77.45
            try:
                G = ox.graph_from_bbox(
                    bbox=(west, south, east, north), network_type="drive"
                )
            except TypeError:
                G = ox.graph_from_bbox(north, south, east, west, network_type="drive")
            # Augment with travel-time weights so shortest_path prefers
            # highways (US-15, US-22/322, I-83, I-81, PA-283) over local roads.
            try:
                G = ox.add_edge_speeds(G)
                G = ox.add_edge_travel_times(G)
                route_weight = "travel_time"
            except Exception as ex:
                print("WARNING: travel-time augmentation failed:", ex, file=sys.stderr)
                route_weight = "length"
            _, edges = ox.graph_to_gdfs(G)
            for _, e in edges.iterrows():
                h = e.get("highway", "other")
                if isinstance(h, list):
                    h = h[0] if h else "other"
                if h in ("motorway", "motorway_link"):
                    lw_, col_ = 1.6, "#888888"
                elif h in ("trunk", "trunk_link", "primary", "primary_link"):
                    lw_, col_ = 1.1, "#A0A0A0"
                elif h == "secondary":
                    lw_, col_ = 0.7, "#B8B8B8"
                else:
                    lw_, col_ = 0.3, "#D0D0D0"
                xs_lon, ys_lat = e.geometry.xy
                xs_m, ys_m = _T_FWD.transform(list(xs_lon), list(ys_lat))
                osm_road_segments.append((xs_m, ys_m, col_, lw_))

            Gp = G
            osrm_distances = {}
            for a, b, dist in routes:
                la = (float(locs[a][1]), float(locs[a][2]))
                lb = (float(locs[b][1]), float(locs[b][2]))

                coords_lonlat = None
                path_len_m = None
                source_tag = ""

                # Primary: OSRM (matches Fukushima F5_network_roads_osm).
                try:
                    coords_lonlat, path_len_m = _osrm_route(la[0], la[1], lb[0], lb[1])
                    source_tag = "OSRM"
                except Exception as ex:
                    print(
                        f"WARNING: OSRM route {a}->{b} failed ({ex}); "
                        "falling back to osmnx.",
                        file=sys.stderr,
                    )

                # Fallback: osmnx travel-time shortest path.
                if coords_lonlat is None:
                    na = ox.distance.nearest_nodes(Gp, la[0], la[1])
                    nb = ox.distance.nearest_nodes(Gp, lb[0], lb[1])
                    path = ox.shortest_path(Gp, na, nb, weight=route_weight)
                    coords_lonlat = []
                    path_len_m = 0.0
                    for u, v in zip(path[:-1], path[1:]):
                        d = Gp.edges[u, v, 0].get("length", 0.0)
                        path_len_m += float(d)
                        coords_lonlat.append((Gp.nodes[u]["x"], Gp.nodes[u]["y"]))
                    coords_lonlat.append(
                        (Gp.nodes[path[-1]]["x"], Gp.nodes[path[-1]]["y"])
                    )
                    source_tag = "osmnx"

                osrm_distances[(a, b)] = (path_len_m / 1000.0, source_tag)

                xs_lon, ys_lat = zip(*coords_lonlat)
                xs, ys = _T_FWD.transform(list(xs_lon), list(ys_lat))
                col, lw, ls = _pair_route_color(a, b)
                ax.plot(xs, ys, color=col, linewidth=lw, linestyle=ls,
                        zorder=4, alpha=0.9)
                mx, my = xs[len(xs) // 2], ys[len(ys) // 2]
                ax.annotate(
                    f"{path_len_m / 1000.0:.1f} km", (mx, my), fontsize=7,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9),
                    zorder=5,
                )

            # Persist OSRM-derived distances as a sibling to routes.csv so
            # Day 14 calibration can opt into road-km if desired.
            try:
                out = TMI / "routes_osrm_distances.csv"
                with out.open("w", encoding="utf-8") as f:
                    f.write("name1,name2,osrm_km,source\n")
                    for (a, b), (km, src) in osrm_distances.items():
                        f.write(f"{a},{b},{km:.3f},{src}\n")
            except Exception as ex:
                print("WARNING: could not write OSRM distances CSV:", ex,
                      file=sys.stderr)
        except Exception as ex:
            use_osm = False
            print("WARNING: OSM plotting failed — using straight-line routes.", ex, file=sys.stderr)

    if not use_osm:
        _plot_static(ax, locs, routes)

    # Distance rings (miles, dashed red — mirrors Fukushima F5_network_roads_osm
    # which shows 3/10/20 km arcs around Daiichi). Drawn in Web Mercator so
    # the radius is in metres (rings appear ~circular at this latitude).
    plant_x, plant_y = _to_merc(PLANT_LON, PLANT_LAT)
    M_PER_MILE = 1609.344
    for mi in (5, 10, 20):
        r = mi * M_PER_MILE
        circ = Circle(
            (plant_x, plant_y), radius=r,
            fill=False, linestyle="--",
            edgecolor=RED, linewidth=1.0, alpha=0.55, zorder=2,
        )
        ax.add_patch(circ)
        ax.text(
            plant_x + r, plant_y, f" {mi} mi",
            fontsize=8, color=RED, va="center", ha="left", zorder=3,
        )

    # Plot nodes; collect (text, x, y) tuples for adjustText.
    try:
        from adjustText import adjust_text
        have_adjust = True
    except Exception:
        have_adjust = False

    texts = []
    for name, lon, lat, pop, ltype in locs.values():
        x, y = _to_merc(lon, lat)
        z = _zone(name)
        if z == "camp":
            ax.scatter(
                x, y, s=110, marker="s", c=GREEN,
                edgecolors="white", linewidths=1.5, zorder=6,
            )
            face, fg = GREEN, "white"
        else:
            col = RED if z == "inner" else ORANGE if z == "middle" else BLUE
            ax.scatter(
                x, y, s=90, c=col,
                edgecolors="white", linewidths=1.5, zorder=6,
            )
            face, fg = col, "white"
        label = name.replace("_camp", " Camp").replace("_", " ").title()
        t = ax.text(
            x, y, label,
            fontsize=8, fontweight="bold", color=fg,
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.25", facecolor=face,
                      edgecolor="white", linewidth=0.8, alpha=0.95),
            zorder=7,
        )
        texts.append(t)

    # TMI plant marker (red star, like Daiichi NPP).
    ax.scatter(
        [plant_x], [plant_y], s=300, marker="*",
        c=RED, edgecolors="white", linewidths=1.5, zorder=8,
    )
    t_plant = ax.text(
        plant_x, plant_y, "TMI\nPlant",
        fontsize=8, fontweight="bold", color="white",
        ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.25", facecolor=RED,
                  edgecolor="white", linewidth=0.8, alpha=0.95),
        zorder=9,
    )
    texts.append(t_plant)

    if have_adjust:
        adjust_text(
            texts,
            ax=ax,
            expand_points=(1.4, 1.6),
            expand_text=(1.2, 1.4),
            force_points=(0.4, 0.6),
            force_text=(0.5, 0.7),
            arrowprops=dict(arrowstyle="-", color=NAVY, lw=0.6, alpha=0.7),
            only_move={"points": "y", "texts": "xy"},
        )

    n_routes = len(routes)
    n_nodes = len(locs)

    legend_elems = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=RED,
               markeredgecolor="white", label="Inner zone (0–5 mi)", markersize=10),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=ORANGE,
               markeredgecolor="white", label="Middle zone (5–15 mi)", markersize=10),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=BLUE,
               markeredgecolor="white", label="Outer zone (>15 mi)", markersize=10),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=GREEN,
               markeredgecolor="white", label="Camp destination", markersize=10),
        Line2D([0], [0], marker="*", color="w", markerfacecolor=RED,
               markeredgecolor="white", label="TMI plant", markersize=14),
        Line2D([0], [0], color=NAVY, lw=1.8, label="Road route (OSM-traced)"),
    ]
    ax.legend(handles=legend_elems, loc="lower left", fontsize=8,
              framealpha=0.92)

    ax.set_title(
        "Three Mile Island Evacuation Network — Actual Road Routes (OSM)\n"
        f"{n_nodes} nodes, {n_routes} routes, distances in road-km",
        fontsize=12, fontweight="bold",
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")

    # Set extent in Web Mercator metres.
    merc_xs, merc_ys = zip(*(_to_merc(v[1], v[2]) for v in locs.values()))
    merc_xs = list(merc_xs) + [plant_x]
    merc_ys = list(merc_ys) + [plant_y]
    pad_x = max(8_000.0, (max(merc_xs) - min(merc_xs)) * 0.06)
    pad_y = max(6_000.0, (max(merc_ys) - min(merc_ys)) * 0.08)
    ax.set_xlim(min(merc_xs) - pad_x, max(merc_xs) + pad_x)
    ax.set_ylim(min(merc_ys) - pad_y, max(merc_ys) + pad_y)

    # Tick labels in degrees (inverse-project mercator back to lon/lat).
    def _fmt_lon(x, _pos):
        lon, _lat = _T_INV.transform(x, (ax.get_ylim()[0] + ax.get_ylim()[1]) / 2)
        return f"{lon:.2f}"

    def _fmt_lat(y, _pos):
        _lon, lat = _T_INV.transform((ax.get_xlim()[0] + ax.get_xlim()[1]) / 2, y)
        return f"{lat:.2f}"

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt_lon))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_lat))

    static_path = FIG / "day11_network_map_static.png"
    osm_path = FIG / "day11_network_map_osm.png"

    # Static deliverable: draw grey OSM road vectors as background context
    # (no tile basemap, so offline-safe). Lowest zorder so the colored FLEE
    # routes and node chips remain readable.
    road_artists = []
    for xs_m, ys_m, col_, lw_ in osm_road_segments:
        ln, = ax.plot(
            xs_m, ys_m, color=col_, linewidth=lw_,
            solid_capstyle="round", zorder=0.5,
        )
        road_artists.append(ln)
    fig.savefig(static_path, bbox_inches="tight")
    # Remove grey road context before adding the tile basemap.
    for ln in road_artists:
        ln.remove()

    # OSM deliverable: add a no-labels tile basemap so the town-name chips
    # we draw are the only labels visible.
    if use_basemap and cx is not None:
        try:
            source = cx.providers.CartoDB.VoyagerNoLabels
        except Exception:
            source = cx.providers.OpenStreetMap.Mapnik
        try:
            cx.add_basemap(
                ax, crs="EPSG:3857", source=source,
                attribution_size=6, zorder=0,
            )
        except Exception as ex:
            print("WARNING: contextily basemap failed:", ex, file=sys.stderr)

    fig.savefig(osm_path, bbox_inches="tight")
    plt.close(fig)
    print("Wrote", static_path, "and", osm_path)


if __name__ == "__main__":
    main()
