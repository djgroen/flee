#!/usr/bin/env python3
"""Shared helpers for Day 15 TMI validation on the v2 network.

Mirrors scripts/tmi_common_day12.run_one but:
  * the network directory is a parameter (default input_data/tmi_v2),
  * supports an EXTENDED return horizon (conflict = 0 past the schedule),
  * threads the two Day-15 model flags through to SimulationSettings:
        enable_return            (Task C return mechanism)
        cmc_conflict_dependent   (Task B2 fallback System-1 form) + cmc_max,
  * records home_node and (for the return curve) per-step in_camp/at_home.

alpha/beta/kappa stay LOCKED at the Fukushima transfer values; CMC is the only
free System-1 parameter (re-fit in Task B / B2).
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
TMI_V2 = REPO / "input_data" / "tmi_v2"

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

# Locked Fukushima transfer parameters (DO NOT retune for TMI).
FROZEN_ALPHA = 1.6667
FROZEN_BETA = 2.1667
FROZEN_KAPPA = 18.407

MIXTURE_MODE = "blend"
T_SCHED = 19                     # native conflict-schedule horizon

PLANT_LON, PLANT_LAT = -76.726, 40.153
INNER_MAX_MI, MIDDLE_MAX_MI = 6.0, 12.0
POP_20MI = 663500.0
TOWN_POP = 258000.0
POP_SCALE = TOWN_POP / POP_20MI  # ~= 0.3889 (Day-12 total-evac convention)

NAVY, BLUE, LTBLUE, GOLD = "#1F3864", "#2E5FA3", "#D6E4F7", "#C9A227"
ZONE_COLORS = {"inner": "#C00000", "middle": "#C55A11", "outer": "#2E5FA3"}


def haversine_mi(lon1, lat1, lon2, lat2):
    R = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def load_locations(network: Path = TMI_V2):
    out = {}
    with (network / "locations.csv").open(encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            name = row[0]
            lon, lat = float(row[3]), float(row[4])
            ltype = row[5]
            pop = int(row[7]) if len(row) > 7 and row[7] else 0
            if ltype == "camp":
                zone, dist = "camp", float("nan")
            else:
                dist = haversine_mi(PLANT_LON, PLANT_LAT, lon, lat)
                zone = ("inner" if dist <= INNER_MAX_MI
                        else "middle" if dist <= MIDDLE_MAX_MI else "outer")
            out[name] = {"lon": lon, "lat": lat, "ltype": ltype,
                         "pop": pop, "dist_mi": dist, "zone": zone}
    return out


def zone_of(name, locinfo):
    info = locinfo.get(name)
    return info["zone"] if info else "unknown"


def load_config(network: Path = TMI_V2):
    SimulationSettings.ReadFromYML(str(network / "simsetting_tmi.yml"))
    SimulationSettings.log_levels["agent"] = 1
    SimulationSettings.log_levels["camp"] = 1
    SimulationSettings.log_levels["init"] = 0
    SimulationSettings.spawn_rules["TakeFromPopulation"] = False
    SimulationSettings.spawn_rules["conflict_driven_spawning"] = False


def distribute_agents_by_pop(e, lm, locinfo, n_total, seed):
    spawn = {name: loc for name, loc in lm.items()
             if not getattr(loc, "camp", False)}
    pops = {name: max(1, locinfo[name]["pop"]) for name in spawn}
    total_pop = sum(pops.values())
    counts, assigned = {}, 0
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


def _build_potential_field(network: Path, n_steps):
    conflicts_csv = str(network / "conflicts.csv")
    routes_csv = str(network / "routes.csv")
    zones_grid, grid = _read_conflict_grid_csv(conflicts_csv)
    awareness_s1 = int(SimulationSettings.move_rules.get("AwarenessLevel", 1))
    field = ConflictPotentialField.build(
        conflict_grid=grid, zones=zones_grid, routes_path=routes_csv,
        num_days=max(n_steps + 1, len(grid)), awareness_s1=awareness_s1,
    )
    return field


def run_one(mode, n_agents, t_max, seed,
            alpha=FROZEN_ALPHA, beta=FROZEN_BETA, kappa=FROZEN_KAPPA,
            cmc=0.0, enable_panic_clamp=False, network: Path = TMI_V2,
            enable_return=False, return_params=None,
            cmc_conflict_dependent=False, cmc_max=None):
    """Single TMI v2 run. Returns (agents_df, arrival_df, mobility_df).

    For t_max > T_SCHED the conflict schedule is extended with c=0 (return
    phase). When enable_return is True the return flags/params are threaded to
    SimulationSettings so camp agents can re-evaluate and return home.
    """
    locinfo = load_locations(network)
    load_config(network)
    SimulationSettings.move_rules["ConflictMoveChance"] = float(cmc)
    SimulationSettings.move_rules["enable_panic_clamp"] = bool(enable_panic_clamp)
    SimulationSettings.move_rules["ConflictInputFile"] = str(network / "conflicts.csv")
    SimulationSettings.ConflictInputFile = str(network / "conflicts.csv")
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = (mode != "original")
    SimulationSettings.move_rules["decision_mode"] = mode
    SimulationSettings.move_rules["s1s2_model_params"] = {
        "alpha": alpha, "beta": beta, "kappa": kappa}
    # Day-15 model flags (defaults keep prior behaviour / 84 tests green).
    SimulationSettings.move_rules["cmc_conflict_dependent"] = bool(cmc_conflict_dependent)
    SimulationSettings.move_rules["conflict_movechance_max"] = (
        float(cmc_max) if cmc_max is not None else float(cmc))
    SimulationSettings.move_rules["enable_return"] = bool(enable_return)
    rp = return_params or {}
    SimulationSettings.move_rules["return_conflict_threshold"] = float(
        rp.get("return_conflict_threshold", 0.15))
    SimulationSettings.move_rules["return_start_t"] = int(rp.get("return_start_t", 16))
    SimulationSettings.move_rules["return_rate"] = float(rp.get("return_rate", 0.5))

    SimulationSettings.move_rules["decision_engine"] = DecisionEngine.create(
        mode, {"s1s2_model_params": SimulationSettings.move_rules["s1s2_model_params"],
               "enable_panic_clamp": bool(enable_panic_clamp)})
    SimulationSettings.move_rules["sys2_weight_override"] = None

    random.seed(seed)
    np.random.seed(seed)

    cwd = Path.cwd()
    try:
        os.chdir(network)
        e = flee.Ecosystem()
        ig = InputGeography.InputGeography()
        ig.ReadLocationsFromCSV("locations.csv")
        ig.ReadLinksFromCSV("routes.csv")
        ig.ReadClosuresFromCSV("closures.csv")
        if Path(SimulationSettings.ConflictInputFile).exists():
            ig.ReadConflictInputCSV(SimulationSettings.ConflictInputFile)
        e, lm = ig.StoreInputGeographyInEcosystem(e)
        SimulationSettings.move_rules["potential_field"] = _build_potential_field(
            network, t_max)
        placed = distribute_agents_by_pop(e, lm, locinfo, n_agents, seed)
    finally:
        os.chdir(cwd)

    initial_zone = {id(a): z for (a, z, _n) in placed}
    home_node = {id(a): n for (a, z, n) in placed}
    init_exp = {id(a): float(getattr(a, "experience_index", 0.0))
                for (a, z, _n) in placed}

    agents_rows, arrival_rows, mobility_rows = [], [], []
    arrived = set()

    # length of native conflict schedule (per-town columns)
    sched_len = 0
    if hasattr(ig, "conflicts"):
        for _cn, cv in ig.conflicts.items():
            sched_len = max(sched_len, len(cv))

    for t in range(t_max + 1):
        prev_loc, prev_active = {}, {}
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
            if t < sched_len:
                ig.AddNewConflictZones(e, t)
            if hasattr(ig, "conflicts"):
                for cname, cvals in ig.conflicts.items():
                    cur = cvals[t] if t < len(cvals) else 0.0  # return phase: c=0
                    e.set_conflict_intensity(cname, float(cur))
        e.evolve()

        moved_active, denom_active = 0, 0
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
            hn = home_node.get(id(a), nm)
            at_home = (nm == hn) and (not is_camp)

            moved_step = (id(a) in prev_loc) and (prev_loc[id(a)] != nm)
            if prev_active.get(id(a), False):
                denom_active += 1
                if moved_step:
                    moved_active += 1

            if is_camp and id(a) not in arrived:
                arrived.add(id(a))
                arrival_rows.append({
                    "agent_id": id(a), "initial_zone": iz, "camp_node": nm,
                    "arrival_timestep": t,
                    "path_length_km": float(getattr(a, "distance_travelled", 0.0)),
                    "experience_x": init_exp.get(id(a), 0.0),
                    "decision_mode": mode, "seed": seed})

            agents_rows.append({
                "timestep": t, "agent_id": id(a), "location": nm, "zone": zone,
                "initial_zone": iz, "home_node": hn, "at_home": bool(at_home),
                "in_camp": is_camp, "sys2_weight": s2,
                "conflict_intensity": conflict,
                "experience_x": init_exp.get(id(a), 0.0),
                "moved_this_step": bool(moved_step),
                "decision_mode": mode, "seed": seed})

        mobility_rows.append({
            "decision_mode": mode, "seed": seed, "timestep": t,
            "mobility_rate": (moved_active / denom_active) if denom_active else 0.0,
            "n_active": denom_active})

    return (pd.DataFrame(agents_rows), pd.DataFrame(arrival_rows),
            pd.DataFrame(mobility_rows))
