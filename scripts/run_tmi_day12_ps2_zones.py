#!/usr/bin/env python3
"""Day 12 Task C — zone-level P_S2 analysis (full-mixture mode, N=5).

Per timestep, per zone (active agents only): mean P_S2, std P_S2, fraction with
P_S2 > 0.5, the zone Omega value, and mean Psi. Computes the cross-domain
zone_ps2_spread(t) = std across the three zone-mean P_S2 values and contrasts it
with Fukushima.

Cross-domain note: a parameter-matched Fukushima comparison (locked Day-10
params) is not stored per-agent in results/fukushima/. We therefore report the
absolute TMI spread and, when figures/fukushima/agents_all_modes.csv is present,
an INDICATIVE Fukushima Day-3 spread (starting params alpha=1.0,beta=2.0) — the
parameter-matched comparison is flagged for Day 16.

Outputs:
  results/tmi/day12_ps2_zones.csv
  results/tmi/day12_ps2_spread_summary.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tmi_common_day12 import (  # noqa: E402
    REPO, MIXTURE_MODE, T_MAX, FROZEN_ALPHA, FROZEN_BETA, run_one,
)
from flee.dual_process_model import compute_capacity, compute_opportunity  # noqa: E402

RESULTS = REPO / "results" / "tmi"
SEEDS = [0, 1, 2, 3, 4]
N_AGENTS = 2000
ZONES = ["inner", "middle", "outer"]
ADVISORY_T = 10   # Governor advisory (c peak)
RECOVERY_T = 16   # Carter visit (Omega recovery onset)


def fukushima_indicative_spread():
    """Max zone-P_S2 spread from the Day-3 Fukushima blend run, if available."""
    path = REPO / "figures" / "fukushima" / "agents_all_modes.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    s2col = "s2_weight" if "s2_weight" in df.columns else "sys2_weight"
    blend = df[(df["decision_mode"] == "blend") & (df["zone"].isin(["inner", "mid", "outer"]))]
    if blend.empty:
        return None
    spreads = []
    for t, g in blend.groupby("timestep"):
        zmeans = [g[g["zone"] == z][s2col].mean() for z in ["inner", "mid", "outer"]]
        zmeans = [v for v in zmeans if not np.isnan(v)]
        if len(zmeans) == 3:
            spreads.append(np.std(zmeans))
    return float(np.nanmax(spreads)) if spreads else None


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)

    # Run mixture mode across seeds, concatenate active-agent rows.
    frames = []
    for seed in SEEDS:
        agents, _arr, _mob = run_one(MIXTURE_MODE, N_AGENTS, T_MAX, seed)
        frames.append(agents[~agents["in_camp"]])
    active = pd.concat(frames, ignore_index=True)

    rows = []
    for t in range(T_MAX + 1):
        at = active[active["timestep"] == t]
        for z in ZONES:
            zt = at[at["zone"] == z]
            if zt.empty:
                rows.append({"timestep": t, "zone": z, "mean_ps2": np.nan,
                             "std_ps2": np.nan, "frac_above_0p5": np.nan,
                             "omega_value": np.nan, "psi_mean": np.nan, "n": 0})
                continue
            c = zt["conflict_intensity"].values
            x = zt["experience_x"].values
            omega = np.mean([compute_opportunity(ci, FROZEN_BETA) for ci in c])
            psi = np.mean([compute_capacity(xi, FROZEN_ALPHA) for xi in x])
            rows.append({
                "timestep": t, "zone": z,
                "mean_ps2": float(zt["sys2_weight"].mean()),
                "std_ps2": float(zt["sys2_weight"].std(ddof=0)),
                "frac_above_0p5": float((zt["sys2_weight"] > 0.5).mean()),
                "omega_value": float(omega),
                "psi_mean": float(psi),
                "n": int(len(zt)),
            })
    zdf = pd.DataFrame(rows)
    zdf.to_csv(RESULTS / "day12_ps2_zones.csv", index=False)
    print(f"Wrote {RESULTS / 'day12_ps2_zones.csv'} ({len(zdf)} rows)")

    # zone_ps2_spread(t) = std across the three zone-mean P_S2 values.
    spread_by_t = {}
    for t in range(T_MAX + 1):
        means = zdf[(zdf["timestep"] == t)].set_index("zone")["mean_ps2"]
        vals = [means.get(z, np.nan) for z in ZONES]
        vals = [v for v in vals if not np.isnan(v)]
        spread_by_t[t] = float(np.std(vals)) if len(vals) == 3 else float("nan")

    tmi_spread_t10 = spread_by_t.get(ADVISORY_T, float("nan"))
    tmi_spread_max = float(np.nanmax(list(spread_by_t.values())))
    fuk = fukushima_indicative_spread()

    summary = {
        "mixture_mode": MIXTURE_MODE,
        "advisory_t": ADVISORY_T,
        "recovery_t": RECOVERY_T,
        "tmi_zone_ps2_spread_t10": tmi_spread_t10,
        "tmi_zone_ps2_spread_max": tmi_spread_max,
        "fukushima_indicative_spread_day3": fuk,
        "fukushima_comparison_basis": (
            "Day-3 starting params (alpha=1.0,beta=2.0); parameter-matched "
            "(locked Day-10) comparison DEFERRED to Day 16"),
        "spread_ratio_tmi_over_fuk": (
            tmi_spread_t10 / fuk if (fuk and fuk > 0) else None),
        "zone_means_t10": {
            z: float(zdf[(zdf.timestep == ADVISORY_T) & (zdf.zone == z)]["mean_ps2"].iloc[0])
            for z in ZONES},
        "verdict_uniform": bool(
            (tmi_spread_t10 < fuk) if fuk else (tmi_spread_t10 < 0.15)),
    }
    with (RESULTS / "day12_ps2_spread_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
