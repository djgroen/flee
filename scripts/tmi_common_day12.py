#!/usr/bin/env python3
"""Shared helpers for Day 12 TMI runs (first run, P_S2 zones, Zeigler).

Centralises: zone assignment from coordinates (Task 0.4), simsetting overrides
with the frozen Fukushima parameters, and a single ``run_one`` simulation driver
that mirrors the Fukushima Day 3 protocol on the TMI network.

Pre-flight constants (results/tmi/day12_preflight.txt):
  modes      = original, sys1_only, switch, blend   (blend = full Psi x Omega mixture)
  t_max      = 19 (= T_SCHED)
  frozen     = alpha=1.6667, beta=2.1667, kappa=18.407, conflict_movechance=0.25
  zone bins  = inner<=6 mi, 6<middle<=12 mi, outer>12 mi (haversine to plant)
  Psi init   = Beta(2,5) i.i.d. (Person.__init__ default; Option B)
"""

from __future__ import annotations

import csv
import math
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"

import sys
sys.path.insert(0, str(REPO))

from flee import flee  # noqa: E402
from flee import InputGeography  # noqa: E402
from flee.SimulationSettings import SimulationSettings  # noqa: E402
from flee.decision_engine import DecisionEngine  # noqa: E402
from flee.conflict_potential import (  # noqa: E402
    ConflictPotentialField,
    _read_conflict_grid_csv,
)

# --- Pre-flight derived constants ------------------------------------------
MODE_ORDER = ["original", "sys1_only", "switch", "blend"]
MIXTURE_MODE = "blend"
T_MAX = 19  # = T_SCHED (conflict_schedule_tmi.json, c_values indices 0..19)

# Frozen Fukushima parameters (DO NOT retune for TMI).
FROZEN_ALPHA = 1.6667
FROZEN_BETA = 2.1667
FROZEN_KAPPA = 18.407
FROZEN_CMC = 0.250

# Plant location (tmi_empirical_data.json -> destination_map_g6).
PLANT_LON, PLANT_LAT = -76.726, 40.153

# Zone distance thresholds (miles) — Zeigler 1981 zone_group boundaries.
INNER_MAX_MI = 6.0
MIDDLE_MAX_MI = 12.0

# 20-mile-region population (empirical denominator for the total-evac sanity QoI).
POP_20MI = 663500.0

ZONE_COLORS = {"inner": "#C00000", "middle": "#C55A11", "outer": "#2E5FA3"}
# Columbia palette.
NAVY, BLUE, LTBLUE, GOLD = "#1F3864", "#2E5FA3", "#D6E4F7", "#C9A227"


def haversine_mi(lon1, lat1, lon2, lat2):
    R = 3958.7613  # Earth radius, miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_locations():
    """Return dict name -> {lon, lat, ltype, pop, dist_mi, zone}."""
    out = {}
    with (TMI / "locations.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            name = row[0]
            lon, lat = float(row[3]), float(row[4])
            ltype = row[5]
            pop = int(row[7]) if len(row) > 7 and row[7] else 0
            if ltype == "camp":
                zone = "camp"
                dist = float("nan")
            else:
                dist = haversine_mi(PLANT_LON, PLANT_LAT, lon, lat)
                zone = ("inner" if dist <= INNER_MAX_MI
                        else "middle" if dist <= MIDDLE_MAX_MI
                        else "outer")
            out[name] = {"lon": lon, "lat": lat, "ltype": ltype,
                         "pop": pop, "dist_mi": dist, "zone": zone}
    return out


def zone_of(name, locinfo):
    info = locinfo.get(name)
    return info["zone"] if info else "unknown"


def load_config():
    """ReadFromYML then apply frozen-parameter overrides (Day 1 fix-sequence)."""
    SimulationSettings.ReadFromYML(str(TMI / "simsetting_tmi.yml"))
    # Frozen calibration parameter.
    SimulationSettings.move_rules["ConflictMoveChance"] = FROZEN_CMC
    # Enable per-agent distance tracking (needed for path-length-at-arrival).
    SimulationSettings.log_levels["agent"] = 1
    SimulationSettings.log_levels["camp"] = 1
    SimulationSettings.log_levels["init"] = 0
    # Spawn rules: explicit placement, no take-from-population.
    SimulationSettings.spawn_rules["TakeFromPopulation"] = False
    SimulationSettings.spawn_rules["conflict_driven_spawning"] = False


def distribute_agents_by_pop(e, lm, locinfo, n_total, seed):
    """Place n_total agents across non-camp nodes proportional to population.

    Returns list of (agent, initial_zone, node_name). experience_index is the
    Person.__init__ default Beta(2,5) draw (Option B); we seed `random` first
    for reproducibility.
    """
    spawn = {name: loc for name, loc in lm.items()
             if not getattr(loc, "camp", False)}
    pops = {name: max(1, locinfo[name]["pop"]) for name in spawn}
    total_pop = sum(pops.values())

    counts = {}
    assigned = 0
    sorted_names = sorted(pops, key=lambda n: pops[n], reverse=True)
    for name in sorted_names[:-1]:
        c = max(1, round(n_total * pops[name] / total_pop))
        counts[name] = c
        assigned += c
    counts[sorted_names[-1]] = max(1, n_total - assigned)

    placed = []
    for name in sorted(counts):
        loc = lm[name]
        z = locinfo[name]["zone"]
        for _ in range(counts[name]):
            e.addAgent(location=loc, attributes={})
            a = e.agents[-1]
            placed.append((a, z, name))
    return placed


def _build_potential_field(n_steps):
    conflicts_csv = str(TMI / "conflicts.csv")
    routes_csv = str(TMI / "routes.csv")
    zones_grid, grid = _read_conflict_grid_csv(conflicts_csv)
    awareness_s1 = int(SimulationSettings.move_rules.get("AwarenessLevel", 1))
    field = ConflictPotentialField.build(
        conflict_grid=grid,
        zones=zones_grid,
        routes_path=routes_csv,
        num_days=max(n_steps + 1, len(grid)),
        awareness_s1=awareness_s1,
    )
    return field


def run_one(mode, n_agents, t_max, seed,
            alpha=FROZEN_ALPHA, beta=FROZEN_BETA, kappa=FROZEN_KAPPA):
    """Run a single TMI simulation in one decision mode.

    Returns (agents_df, arrival_df, mobility_df).
      agents_df : per (timestep, agent) — location, zone, initial_zone,
                  sys2_weight (P_S2), conflict_intensity, experience_x,
                  moved_this_step, in_camp, mode, seed
      arrival_df: per agent first camp arrival — initial_zone, arrival_timestep,
                  path_length_km, experience_x, mode, seed
      mobility_df: per timestep — mode, seed, timestep, mobility_rate, n_active
    """
    locinfo = load_locations()
    load_config()
    SimulationSettings.ConflictInputFile = str(TMI / "conflicts.csv")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = (mode != "original")
    SimulationSettings.move_rules["decision_mode"] = mode
    SimulationSettings.move_rules["s1s2_model_params"] = {
        "alpha": alpha, "beta": beta, "kappa": kappa,
    }
    SimulationSettings.move_rules["decision_engine"] = DecisionEngine.create(
        mode, {"s1s2_model_params": SimulationSettings.move_rules["s1s2_model_params"]},
    )
    SimulationSettings.move_rules["sys2_weight_override"] = None

    random.seed(seed)
    np.random.seed(seed)

    cwd = Path.cwd()
    try:
        os.chdir(TMI)
        e = flee.Ecosystem()
        ig = InputGeography.InputGeography()
        ig.ReadLocationsFromCSV("locations.csv")
        ig.ReadLinksFromCSV("routes.csv")
        ig.ReadClosuresFromCSV("closures.csv")
        if Path(SimulationSettings.ConflictInputFile).exists():
            ig.ReadConflictInputCSV(SimulationSettings.ConflictInputFile)
        e, lm = ig.StoreInputGeographyInEcosystem(e)

        SimulationSettings.move_rules["potential_field"] = _build_potential_field(t_max)

        placed = distribute_agents_by_pop(e, lm, locinfo, n_agents, seed)
    finally:
        os.chdir(cwd)

    initial_zone = {id(a): z for (a, z, _n) in placed}
    init_exp = {id(a): float(getattr(a, "experience_index", 0.0)) for (a, z, _n) in placed}

    agents_rows = []
    arrival_rows = []
    mobility_rows = []
    arrived = set()

    for t in range(t_max + 1):
        # Snapshot pre-evolve location for per-step mobility.
        prev_loc = {}
        prev_active = {}
        for a in e.agents:
            loc = a.location
            if loc is None:
                continue
            ep = getattr(loc, "endpoint", loc)
            nm = getattr(ep, "name", str(loc))
            is_camp = bool(getattr(ep, "camp", False))
            prev_loc[id(a)] = nm
            prev_active[id(a)] = not is_camp

        if t > 0:
            ig.AddNewConflictZones(e, t)
            if hasattr(ig, "conflicts"):
                for cname, cvals in ig.conflicts.items():
                    if t < len(cvals):
                        cur = cvals[t]
                        e.set_conflict_intensity(cname, float(cur))
        e.evolve()

        moved_active = 0
        denom_active = 0
        for a in e.agents:
            loc = a.location
            if loc is None:
                continue
            ep = getattr(loc, "endpoint", loc)
            nm = getattr(ep, "name", str(loc))
            zone = zone_of(nm, locinfo)
            is_camp = bool(getattr(ep, "camp", False)) or zone == "camp"
            s2 = float(getattr(a, "sys2_activation_prob", 0.0))
            conflict = max(0.0, float(getattr(ep, "conflict", 0.0)))
            iz = initial_zone.get(id(a), zone)

            moved_step = (id(a) in prev_loc) and (prev_loc[id(a)] != nm)
            if prev_active.get(id(a), False):
                denom_active += 1
                if moved_step:
                    moved_active += 1

            # First camp arrival -> path length.
            if is_camp and id(a) not in arrived:
                arrived.add(id(a))
                arrival_rows.append({
                    "agent_id": id(a),
                    "initial_zone": iz,
                    "camp_node": nm,
                    "arrival_timestep": t,
                    "path_length_km": float(getattr(a, "distance_travelled", 0.0)),
                    "experience_x": init_exp.get(id(a), 0.0),
                    "decision_mode": mode,
                    "seed": seed,
                })

            agents_rows.append({
                "timestep": t,
                "agent_id": id(a),
                "location": nm,
                "zone": zone,
                "initial_zone": iz,
                "in_camp": is_camp,
                "sys2_weight": s2,
                "conflict_intensity": conflict,
                "experience_x": init_exp.get(id(a), 0.0),
                "moved_this_step": bool(moved_step),
                "decision_mode": mode,
                "seed": seed,
            })

        mobility_rows.append({
            "decision_mode": mode,
            "seed": seed,
            "timestep": t,
            "mobility_rate": (moved_active / denom_active) if denom_active else 0.0,
            "n_active": denom_active,
        })

    return (pd.DataFrame(agents_rows),
            pd.DataFrame(arrival_rows),
            pd.DataFrame(mobility_rows))
