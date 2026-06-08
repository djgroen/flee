#!/usr/bin/env python3
"""Day 12 Task D — Zeigler paradox metric (full-mixture mode, N=5).

Per agent: origin zone, departure timestep (first step leaving origin),
path-length-at-arrival (ONLY for agents who reach a camp). Reports by zone:
arrival fraction, mean departure timestep (over departers), and the
path-length-at-arrival distribution (min/25/median/75/max over arrivers).

P3 verdict: mean_departure(inner) < mean_departure(outer)
        AND  mean_path(inner)      < mean_path(outer).

NOT CONFIRMED at frozen params is acceptable/expected (Day 14 may sharpen it);
the quantitative gap is recorded either way.

Outputs:
  results/tmi/day12_zeigler_metric.csv
  results/tmi/day12_zeigler_verdict.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tmi_common_day12 import (  # noqa: E402
    REPO, MIXTURE_MODE, T_MAX, run_one,
)

RESULTS = REPO / "results" / "tmi"
SEEDS = [0, 1, 2, 3, 4]
N_AGENTS = 2000
ZONES = ["inner", "middle", "outer"]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)

    # Per-agent records pooled across seeds (agent_id is unique within a seed
    # only, so namespace by (seed, agent_id)).
    recs = []
    for seed in SEEDS:
        agents, arrivals, _mob = run_one(MIXTURE_MODE, N_AGENTS, T_MAX, seed)
        init_zone = agents.groupby("agent_id")["initial_zone"].first()
        # Departure timestep = first step the agent moved off its origin.
        moved = agents[agents["moved_this_step"]]
        dep_t = moved.groupby("agent_id")["timestep"].min()
        arr_map = (arrivals.set_index("agent_id")[["arrival_timestep", "path_length_km"]]
                   if not arrivals.empty else pd.DataFrame())
        exp_map = agents.groupby("agent_id")["experience_x"].first()
        for aid, z in init_zone.items():
            d = dep_t.get(aid, np.nan)
            if not arr_map.empty and aid in arr_map.index:
                at = float(arr_map.loc[aid, "arrival_timestep"])
                pl = float(arr_map.loc[aid, "path_length_km"])
                arrived = True
            else:
                at, pl, arrived = np.nan, np.nan, False
            recs.append({"seed": seed, "agent_id": aid, "zone": z,
                         "experience_x": float(exp_map.get(aid, np.nan)),
                         "departure_t": d, "arrived": arrived,
                         "arrival_t": at, "path_length_km": pl})
    df = pd.DataFrame(recs)

    # Per-zone aggregates.
    rows = []
    zstat = {}
    for z in ZONES:
        zz = df[df["zone"] == z]
        n = len(zz)
        arr = zz[zz["arrived"]]
        n_arr = len(arr)
        arrival_frac = n_arr / n if n else float("nan")
        mean_dep = float(zz["departure_t"].mean())  # over departers (NaN if never moved drop)
        mean_dep = float(zz["departure_t"].dropna().mean()) if zz["departure_t"].notna().any() else float("nan")
        pl = arr["path_length_km"].dropna()
        dist = {
            "path_min": float(pl.min()) if len(pl) else float("nan"),
            "path_p25": float(pl.quantile(0.25)) if len(pl) else float("nan"),
            "path_median": float(pl.median()) if len(pl) else float("nan"),
            "path_p75": float(pl.quantile(0.75)) if len(pl) else float("nan"),
            "path_max": float(pl.max()) if len(pl) else float("nan"),
            "path_mean": float(pl.mean()) if len(pl) else float("nan"),
        }
        zstat[z] = {"arrival_frac": arrival_frac, "mean_dep": mean_dep, **dist}
        rows.append({"zone": z, "n_agents": n, "n_arrived": n_arr,
                     "arrival_fraction": round(arrival_frac, 4),
                     "mean_departure_t": round(mean_dep, 3),
                     **{k: round(v, 3) for k, v in dist.items()}})
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "day12_zeigler_metric.csv", index=False)
    print(f"Wrote {RESULTS / 'day12_zeigler_metric.csv'}")

    dep_gap = zstat["inner"]["mean_dep"] - zstat["outer"]["mean_dep"]
    path_gap = zstat["inner"]["path_mean"] - zstat["outer"]["path_mean"]
    confirmed = (dep_gap < 0) and (path_gap < 0)

    # P2: Psi as primary differentiator. With near-uniform Omega, agent-level
    # Psi (experience) should explain MORE departure-timing variation than the
    # spatial zone does. Compare variance of group-mean departure_t across
    # Psi-quintiles vs across the 3 zones.
    dfd = df.dropna(subset=["departure_t"]).copy()
    zone_means = dfd.groupby("zone")["departure_t"].mean()
    var_zone = float(np.var(zone_means.values, ddof=0))
    try:
        dfd["psi_q"] = pd.qcut(dfd["experience_x"], 5, labels=False, duplicates="drop")
        psi_means = dfd.groupby("psi_q")["departure_t"].mean()
        var_psi = float(np.var(psi_means.values, ddof=0))
    except Exception:
        var_psi = float("nan")
    p2_confirmed = bool(var_psi > var_zone)

    verdict = {
        "mixture_mode": MIXTURE_MODE,
        "inner": zstat["inner"], "outer": zstat["outer"], "middle": zstat["middle"],
        "departure_gap_inner_minus_outer": dep_gap,
        "path_gap_inner_minus_outer_km": path_gap,
        "signature_confirmed": bool(confirmed),
        "p2_var_departure_by_psi_quintile": var_psi,
        "p2_var_departure_by_zone": var_zone,
        "p2_psi_is_primary_differentiator": p2_confirmed,
        "note": ("path-length-at-arrival is dominated by network topology "
                 "(outer towns york/lancaster have ADJACENT camps; inner towns "
                 "traverse multi-hop routes to harrisburg_camp). At frozen params "
                 "the cognitive Zeigler gradient is not isolated — expected; "
                 "Day 14 calibration may sharpen it."),
    }
    with (RESULTS / "day12_zeigler_verdict.json").open("w") as f:
        json.dump(verdict, f, indent=2)

    print("\nZeigler Paradox P3 (frozen Fukushima params, default TMI run):")
    for z in ("inner", "outer"):
        s = zstat[z]
        print(f"  {z}: arrivals {s['arrival_frac']*100:.0f}%, "
              f"mean departure t={s['mean_dep']:.1f}, "
              f"mean path {s['path_mean']:.1f} km")
    print(f"  Signature: [{'CONFIRMED' if confirmed else 'NOT CONFIRMED'}] "
          f"(gap: departure dT={dep_gap:+.2f}, path dkm={path_gap:+.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
