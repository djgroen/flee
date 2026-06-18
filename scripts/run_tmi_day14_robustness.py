#!/usr/bin/env python3
"""Day 14 Task E -- CMC robustness around the locked value (mirror Day 9).

At the locked CMC +/- a neighbourhood (clamp OFF, alpha/beta/kappa LOCKED):
  1. Sensitivity of the PRIMARY QoIs (total evac + zone rates) to CMC
     perturbation -> verdict ROBUST / MODERATE / FRAGILE (same scheme spirit as
     Fukushima Day 9, where CMC was MODERATE).
  2. Confirm the locked alpha/beta/kappa still give sensible P_S2 dynamics at
     the calibrated CMC: uniform zone P_S2 (Day-12 finding P1 still holds) and a
     plausible peak P_S2.
  3. kappa: confirm flat / irrelevant at TMI (Day 13 ST=0.01) via a small kappa
     check at the locked CMC. No retune.

Output: results/tmi/day14_robustness.csv + printed verdict.
"""
from __future__ import annotations

import contextlib
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
NEIGH = 0.05            # CMC neighbourhood half-width
PEAK_T = 10
ROBUST_THR, MODERATE_THR = 0.15, 0.30   # max relative QoI change thresholds


def _ps2_dynamics(cmc: float, locinfo: dict, seeds=(0, 1, 2, 3, 4)) -> dict:
    """Zone-mean P_S2 over time at the locked params; peak + zone spread."""
    zone_peak = {"inner": [], "middle": [], "outer": []}
    peak_overall = []
    spread_t10 = []
    for s in seeds:
        with contextlib.redirect_stdout(io.StringIO()):
            adf, _a, _m = tc.run_one(
                "blend", cal.N_AGENTS, cal.T_MAX, s,
                alpha=cal.ALPHA_LOCKED, beta=cal.BETA_LOCKED,
                kappa=cal.KAPPA_LOCKED, cmc=cmc, enable_panic_clamp=False)
        active = adf[~adf["in_camp"]]
        by_t = active.groupby("timestep")["sys2_weight"].mean()
        peak_overall.append(float(by_t.max()) if len(by_t) else float("nan"))
        at_peak = active[active["timestep"] == PEAK_T]
        zmeans = []
        for z in ("inner", "middle", "outer"):
            zsub = at_peak[at_peak["initial_zone"] == z]
            v = float(zsub["sys2_weight"].mean()) if not zsub.empty else float("nan")
            zone_peak[z].append(v)
            if not np.isnan(v):
                zmeans.append(v)
        spread_t10.append(float(np.std(zmeans)) if len(zmeans) >= 2 else float("nan"))
    return {
        "peak_ps2": float(np.nanmean(peak_overall)),
        "zone_ps2_inner_t10": float(np.nanmean(zone_peak["inner"])),
        "zone_ps2_middle_t10": float(np.nanmean(zone_peak["middle"])),
        "zone_ps2_outer_t10": float(np.nanmean(zone_peak["outer"])),
        "zone_ps2_spread_t10": float(np.nanmean(spread_t10)),
    }


def main():
    RES.mkdir(parents=True, exist_ok=True)
    locinfo = tc.load_locations()
    locked = json.loads((RES / "day14_locked_params.json").read_text())
    cmc0 = float(locked["tmi_cmc_locked"])

    # Neighbourhood, clipped to [0, 0.30]; boundary lock -> one-sided.
    lo = max(0.0, round(cmc0 - NEIGH, 3))
    hi = min(0.30, round(cmc0 + NEIGH, 3))
    grid = sorted({lo, round((lo + hi) / 2, 3), hi,
                   max(0.0, round(cmc0 - NEIGH / 2, 3)),
                   min(0.30, round(cmc0 + NEIGH / 2, 3))})
    one_sided = abs(cmc0 - lo) < 1e-9 or abs(cmc0 - hi) < 1e-9
    print("=" * 72)
    print("Day 14 Task E -- CMC robustness (clamp OFF, alpha/beta/kappa LOCKED)")
    print(f"  locked CMC = {cmc0:.2f}  neighbourhood = {grid} "
          f"({'one-sided (boundary)' if one_sided else 'two-sided'})")
    print("=" * 72)

    rows = []
    for cmc in grid:
        q = cal.run_point(cmc, enable_panic_clamp=False, locinfo=locinfo)
        ps2 = _ps2_dynamics(cmc, locinfo)
        rows.append({"cmc": cmc, **{k: q[k] for k in (
            "total_evac", "evac_inner", "evac_middle", "evac_outer",
            "frac_inner_by_t10", "zeigler_gap", "misfit")}, **ps2})
        print(f"  CMC={cmc:.3f} total_evac={q['total_evac']:.3f} "
              f"in/mid/out={q['evac_inner']:.2f}/{q['evac_middle']:.2f}/"
              f"{q['evac_outer']:.2f} peakP_S2={ps2['peak_ps2']:.3f} "
              f"zoneP_S2spread={ps2['zone_ps2_spread_t10']:.4f}")

    df = pd.DataFrame(rows)
    df.to_csv(RES / "day14_robustness.csv", index=False)

    # --- 1. Sensitivity verdict (max relative change of primary QoIs) -------
    prim = ["total_evac", "evac_inner", "evac_middle", "evac_outer"]
    rel = {}
    for q in prim:
        v = df[q].to_numpy()
        base = df.loc[df["cmc"].sub(cmc0).abs().idxmin(), q]
        rel[q] = float(np.nanmax(np.abs(v - base)) / max(abs(base), 1e-9))
    max_rel = max(rel.values())
    if max_rel < ROBUST_THR:
        verdict = "ROBUST"
    elif max_rel < MODERATE_THR:
        verdict = "MODERATE"
    else:
        verdict = "FRAGILE"

    # --- 2. P_S2 dynamics at locked CMC -------------------------------------
    at_locked = df.loc[df["cmc"].sub(cmc0).abs().idxmin()]
    zone_vals = [at_locked["zone_ps2_inner_t10"],
                 at_locked["zone_ps2_middle_t10"],
                 at_locked["zone_ps2_outer_t10"]]
    zone_spread = float(at_locked["zone_ps2_spread_t10"])
    p1_holds = zone_spread < 0.05   # Day-12 P1: zone P_S2 spread LOW/uniform
    peak_ps2 = float(at_locked["peak_ps2"])
    peak_plausible = 0.0 < peak_ps2 < 1.0

    print("\n" + "-" * 72)
    print(f"1. CMC robustness verdict = {verdict}")
    for q in prim:
        print(f"     {q:14}: max relative change {rel[q]*100:5.1f}% "
              f"over CMC in [{df['cmc'].min():.2f},{df['cmc'].max():.2f}]")
    print(f"     (max {max_rel*100:.1f}%; ROBUST<{ROBUST_THR*100:.0f}% "
          f"MODERATE<{MODERATE_THR*100:.0f}% else FRAGILE)")
    print(f"2. P_S2 at locked CMC={cmc0:.2f}: zone means inner/mid/out = "
          f"{zone_vals[0]:.3f}/{zone_vals[1]:.3f}/{zone_vals[2]:.3f}")
    print(f"     zone P_S2 spread @t10 = {zone_spread:.4f}  -> P1 uniform "
          f"P_S2 {'HOLDS' if p1_holds else 'does NOT hold'} (<0.05)")
    print(f"     peak mean P_S2 = {peak_ps2:.3f}  "
          f"({'plausible' if peak_plausible else 'IMPLAUSIBLE'} in (0,1))")
    print("3. kappa: flat / irrelevant at TMI (Day 13 ST=0.01); not retuned. "
          "See kappa check below.")

    # --- 3. kappa flatness check at locked CMC ------------------------------
    kappa_rows = []
    for kappa in (10.0, cal.KAPPA_LOCKED, 30.0):
        per = []
        for s in (0, 1, 2):
            with contextlib.redirect_stdout(io.StringIO()):
                adf, _a, _m = tc.run_one(
                    "blend", cal.N_AGENTS, cal.T_MAX, s,
                    alpha=cal.ALPHA_LOCKED, beta=cal.BETA_LOCKED,
                    kappa=kappa, cmc=cmc0, enable_panic_clamp=False)
            per.append(cal.compute_qois(adf, locinfo)["total_evac"])
        kappa_rows.append({"kappa": kappa, "total_evac": float(np.nanmean(per))})
    kdf = pd.DataFrame(kappa_rows)
    kspan = float(kdf["total_evac"].max() - kdf["total_evac"].min())
    print(f"     kappa {kdf['kappa'].tolist()} -> total_evac "
          f"{[round(x,3) for x in kdf['total_evac']]}  span={kspan:.3f} "
          f"({'FLAT' if kspan < 0.05 else 'NOT flat'}; consistent with Day 13)")

    payload = {
        "locked_cmc": cmc0, "neighbourhood": grid, "one_sided": one_sided,
        "robustness_verdict": verdict,
        "max_relative_change": max_rel,
        "relative_change_by_qoi": rel,
        "p1_uniform_ps2_holds": bool(p1_holds),
        "zone_ps2_spread_t10": zone_spread,
        "peak_ps2": peak_ps2, "peak_ps2_plausible": bool(peak_plausible),
        "kappa_check": {"kappas": kdf["kappa"].tolist(),
                        "total_evac": kdf["total_evac"].tolist(),
                        "span": kspan, "flat": bool(kspan < 0.05)},
    }
    (RES / "day14_robustness_verdict.json").write_text(json.dumps(payload, indent=2))
    print(f"\n[robustness] wrote {RES/'day14_robustness.csv'} and verdict json")
    print(f"[robustness] VERDICT: CMC {verdict}; P1 uniform P_S2 "
          f"{'holds' if p1_holds else 'fails'}.")


if __name__ == "__main__":
    main()
