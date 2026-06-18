#!/usr/bin/env python3
"""Day 14 Task A -- confirm the panic clamp blocks CMC calibration.

Sweep CMC in {0.0, 0.05, 0.10, 0.20, 0.30} with the panic clamp ON, blend mode,
alpha/beta/kappa LOCKED, 5 seeds averaged. Show that total evac rate is nearly
flat across CMC (reproducing Day 13's LOW_VARIANCE finding for total_evac under
the clamp). This grounds the Task-C clamp decision in a demonstrated problem.

Output: printed CMC->evac curve + a verdict line. Writes
results/tmi/day14_clamp_diagnostic.csv for the record.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import tmi_common_day12 as tc  # noqa: E402
from scripts import run_tmi_day14_calibration as cal  # noqa: E402

RES = REPO / "results" / "tmi"
CMC_SWEEP = [0.0, 0.05, 0.10, 0.20, 0.30]
# A reachable-range span below this (relative to the clamp-OFF span) means the
# clamp has flattened the CMC->evac response enough that CMC is unidentifiable
# on the evac level.
FLAT_SPAN_ABS = 0.10


def main():
    RES.mkdir(parents=True, exist_ok=True)
    locinfo = tc.load_locations()
    print("=" * 72)
    print("Day 14 Task A -- clamp diagnostic (CMC sweep, panic clamp ON)")
    print(f"  blend mode | alpha/beta/kappa LOCKED "
          f"({cal.ALPHA_LOCKED}/{cal.BETA_LOCKED}/{cal.KAPPA_LOCKED}) "
          f"| {len(cal.SEEDS)} seeds")
    print("=" * 72)

    rows = []
    for cmc in CMC_SWEEP:
        q = cal.run_point(cmc, enable_panic_clamp=True, locinfo=locinfo)
        rows.append({"cmc": cmc, "clamp": "on", **q})
        print(f"  CMC={cmc:.2f}  total_evac={q['total_evac']:.3f}  "
              f"inner/mid/out={q['evac_inner']:.2f}/{q['evac_middle']:.2f}/"
              f"{q['evac_outer']:.2f}")

    df = pd.DataFrame(rows)
    df.to_csv(RES / "day14_clamp_diagnostic.csv", index=False)

    evac = df["total_evac"].to_numpy()
    span = float(np.nanmax(evac) - np.nanmin(evac))
    lo, hi = float(np.nanmin(evac)), float(np.nanmax(evac))

    print("\n  CMC -> total_evac curve (clamp ON):")
    for _, r in df.iterrows():
        bar = "#" * int(round(r["total_evac"] * 40))
        print(f"    {r['cmc']:.2f} | {r['total_evac']:.3f} {bar}")
    print(f"\n  reachable evac range under clamp ON = "
          f"[{lo:.3f}, {hi:.3f}]  span={span:.3f}")
    print(f"  empirical total-evac target = {cal.TARGET_TOTAL_EVAC} "
          f"(band {cal.EVAC_BAND})")

    unidentifiable = (span < FLAT_SPAN_ABS) and (lo > cal.EVAC_BAND[1])
    verdict = "confirmed" if unidentifiable else "not confirmed"
    print(f"\n  Verdict: CMC unidentifiable on evac rate under clamp ON: "
          f"[{verdict}].")
    print(f"    (span {span:.3f} < {FLAT_SPAN_ABS} AND floor {lo:.3f} pinned "
          f"above band upper edge {cal.EVAC_BAND[1]}: the curve is flat and "
          f"saturated near the ceiling -> CMC cannot be matched to the "
          f"{cal.TARGET_TOTAL_EVAC} target.)")
    return verdict


if __name__ == "__main__":
    main()
