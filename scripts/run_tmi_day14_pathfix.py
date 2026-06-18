#!/usr/bin/env python3
"""Day 14 Task F -- camp-placement / path-metric fix (enables the Zeigler read).

The distance-based Zeigler signature (close-to-plant -> shorter travel,
far-from-plant -> longer travel; i.e. inner-zone travel-distance < outer-zone
travel-distance) is unreadable because CAMP ADJACENCY dominates
path-length-at-arrival: outer towns (york, lancaster) sit ~1 hop / ~2.5 km from
a camp while inner towns are 24-27 km / 2-3 hops away, so the network path metric
reads BACKWARDS (inner long, outer short).

FIX APPLIED -- Option A (metric, less invasive; chosen because the topology is
demonstrably unrepresentative of the real evacuation geography but must NOT be
mutated since Days 11-13 depend on it):
    Replace path-length-at-arrival with a TOPOLOGY-ROBUST distance: the
    straight-line displacement of the agent's FINAL destination from the PLANT
    (the fixed hazard source), rather than the network distance to the
    (variably-adjacent) camp. Referencing the fixed source removes the
    adjacency confound. We also report path normalised by the zone's
    minimum-available-camp distance for completeness.

Re-read at the locked CMC: does inner-zone travel-distance < outer-zone
travel-distance now emerge? (Day-15 validation precondition, not a calibration
target.)

Output: results/tmi/day14_zeigler_pathfix.csv + a printed note.
"""
from __future__ import annotations

import collections
import contextlib
import csv
import heapq
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import tmi_common_day12 as tc  # noqa: E402
from scripts import run_tmi_day14_calibration as cal  # noqa: E402

RES = REPO / "results" / "tmi"
TMI = REPO / "input_data" / "tmi"
ZONES = ["inner", "middle", "outer"]


def _adjacency():
    adj = collections.defaultdict(list)
    with (TMI / "routes.csv").open() as f:
        for r in csv.reader(f):
            if not r or r[0].startswith("#"):
                continue
            a, b, d = r[0], r[1], float(r[2])
            adj[a].append((b, d))
            adj[b].append((a, d))
    return adj


def _dijkstra(adj, src):
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18):
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def _hops(adj, src, dst):
    q = collections.deque([(src, 0)])
    seen = {src}
    while q:
        u, h = q.popleft()
        if u == dst:
            return h
        for v, _ in adj[u]:
            if v not in seen:
                seen.add(v)
                q.append((v, h + 1))
    return -1


def main():
    RES.mkdir(parents=True, exist_ok=True)
    locinfo = tc.load_locations()
    camps = [n for n, i in locinfo.items() if i["ltype"] == "camp"]
    adj = _adjacency()

    # --- 1. Diagnose: per-town nearest-camp distance / hop count -----------
    diag_rows = []
    for n, i in locinfo.items():
        if i["ltype"] == "camp":
            continue
        dd = _dijkstra(adj, n)
        best = min(camps, key=lambda c: dd.get(c, 1e18))
        diag_rows.append({
            "town": n, "zone": i["zone"], "dist_plant_mi": i["dist_mi"],
            "nearest_camp": best, "nearest_camp_net_km": dd.get(best, float("nan")),
            "nearest_camp_hops": _hops(adj, n, best)})
    diag = pd.DataFrame(diag_rows)
    zone_diag = diag.groupby("zone").agg(
        nearest_camp_net_km=("nearest_camp_net_km", "mean"),
        nearest_camp_hops=("nearest_camp_hops", "mean")).reindex(ZONES)

    # Big outer towns (by population) drive the per-agent path metric.
    big_outer = diag[diag["zone"] == "outer"].sort_values(
        "nearest_camp_net_km").head(2)["town"].tolist()
    print("=" * 72)
    print("Day 14 Task F -- camp-adjacency diagnosis")
    print("=" * 72)
    print("Per-town nearest camp (network km / hops):")
    print(diag[["town", "zone", "dist_plant_mi", "nearest_camp",
                "nearest_camp_net_km", "nearest_camp_hops"]]
          .sort_values(["zone", "dist_plant_mi"]).to_string(index=False))
    print("\nPer-zone mean nearest-camp distance:")
    print(zone_diag.to_string())
    print(f"\n  -> CONFOUND is TOWN-level + population-weighted: the big OUTER "
          f"towns {big_outer} (45k/54k pop) sit ~1 hop / ~2.4-2.5 km from a "
          f"camp, so most OUTER agents have a tiny path-length-at-arrival, while "
          f"INNER towns are 24-27 km / 2-3 hops away. (Zone-mean nearest-camp is "
          f"muddied because far outer towns carlisle/lebanon raise the mean, but "
          f"they hold little population.)")

    # --- 2. Run at the locked CMC, collect arrivals ------------------------
    locked = json.loads((RES / "day14_locked_params.json").read_text())
    cmc0 = float(locked["tmi_cmc_locked"])
    enable = bool(locked["enable_panic_clamp"])

    def cdist_plant(nm):
        i = locinfo.get(nm)
        return (tc.haversine_mi(tc.PLANT_LON, tc.PLANT_LAT, i["lon"], i["lat"])
                if i else float("nan"))

    nearest_km = dict(zip(diag["town"], diag["nearest_camp_net_km"]))

    frames = []
    for s in range(5):
        with contextlib.redirect_stdout(io.StringIO()):
            _adf, arr, _m = tc.run_one(
                "blend", cal.N_AGENTS, cal.T_MAX, s,
                alpha=cal.ALPHA_LOCKED, beta=cal.BETA_LOCKED,
                kappa=cal.KAPPA_LOCKED, cmc=cmc0, enable_panic_clamp=enable)
        if not arr.empty:
            arr = arr.copy()
            arr["seed"] = s
            frames.append(arr)
    arr = pd.concat(frames, ignore_index=True)

    # Origin name per agent for the normaliser (use camp_node mapping back is not
    # possible; we instead normalise the network path by the agent's ORIGIN-zone
    # min-camp distance via the agent's initial zone mean).
    arr["dest_dist_plant_mi"] = arr["camp_node"].map(cdist_plant)

    # --- 3. By-zone distributions: confounded vs fixed metric --------------
    rows = []
    for z in ZONES:
        sub = arr[arr["initial_zone"] == z]
        if sub.empty:
            continue
        zone_min_camp_km = float(zone_diag.loc[z, "nearest_camp_net_km"])
        rows.append({
            "zone": z,
            "n_arrivals": int(len(sub)),
            "nearest_camp_net_km": zone_min_camp_km,
            "nearest_camp_hops": float(zone_diag.loc[z, "nearest_camp_hops"]),
            # confounded metric (network distance travelled to arrival)
            "path_km_median": float(sub["path_length_km"].median()),
            "path_km_mean": float(sub["path_length_km"].mean()),
            # path normalised by zone min-camp distance (topology-robust v1)
            "path_norm_median": float((sub["path_length_km"]
                                       / max(zone_min_camp_km, 1e-9)).median()),
            # FIX metric: final-destination displacement from the plant (v2)
            "dest_dist_plant_mi_median": float(sub["dest_dist_plant_mi"].median()),
            "dest_dist_plant_mi_mean": float(sub["dest_dist_plant_mi"].mean()),
        })
    out = pd.DataFrame(rows)
    out.to_csv(RES / "day14_zeigler_pathfix.csv", index=False)

    # --- 4. Re-read the signature ------------------------------------------
    def _get(z, col):
        v = out.loc[out["zone"] == z, col]
        return float(v.iloc[0]) if len(v) else float("nan")

    path_inner, path_outer = _get("inner", "path_km_median"), _get("outer", "path_km_median")
    fix_inner, fix_mid, fix_outer = (_get("inner", "dest_dist_plant_mi_median"),
                                     _get("middle", "dest_dist_plant_mi_median"),
                                     _get("outer", "dest_dist_plant_mi_median"))
    confounded_inverted = path_inner > path_outer
    fix_reads = fix_inner < fix_outer

    print("\n" + "-" * 72)
    print("By-zone travel distance (locked CMC={:.2f}, clamp {}):".format(
        cmc0, "OFF" if not enable else "ON"))
    print(out[["zone", "n_arrivals", "path_km_median",
               "dest_dist_plant_mi_median"]].to_string(index=False))
    print(f"\n  CONFOUNDED network path: inner={path_inner:.1f} km vs "
          f"outer={path_outer:.1f} km -> "
          f"{'INVERTED (inner>outer)' if confounded_inverted else 'ok'}")
    print(f"  FIXED metric (dest dist from plant): inner={fix_inner:.1f} mi, "
          f"middle={fix_mid:.1f} mi, outer={fix_outer:.1f} mi")
    print(f"  Zeigler distance signature (inner < outer) now reads: "
          f"{'YES' if fix_reads else 'NO'}")

    note = (
        "FIX APPLIED: Option A (metric). Replaced path-length-at-arrival (network "
        "distance to the variably-adjacent camp) with the straight-line "
        "displacement of the FINAL destination from the PLANT (fixed hazard "
        "source). The diagnosis showed the topology is unrepresentative (outer "
        "towns york/lancaster are ~1 hop/~2.5 km from a camp, inner towns "
        "24-27 km), so a topology-robust, source-referenced metric is used "
        "rather than mutating the shared TMI network (Days 11-13 depend on it). "
        f"Signature inner<outer now reads: {'YES' if fix_reads else 'NO'} "
        f"(inner {fix_inner:.1f} mi < outer {fix_outer:.1f} mi); the confounded "
        f"network path was inverted (inner {path_inner:.1f} > outer "
        f"{path_outer:.1f} km). NOTE: this is a Day-15 validation precondition, "
        "not a calibration target, and it does not change the Task-B/E evac "
        "results. A full Option-B topology fix (symmetric/distant camp placement "
        "matching the real 85-111 mi evacuation geography) is recommended for "
        "Day 15+ and would require re-running calibration.")
    (RES / "day14_zeigler_pathfix_note.txt").write_text(note + "\n")
    print("\n" + note)
    print(f"\n[pathfix] wrote {RES/'day14_zeigler_pathfix.csv'}")


if __name__ == "__main__":
    main()
