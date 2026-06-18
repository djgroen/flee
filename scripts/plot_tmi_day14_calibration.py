#!/usr/bin/env python3
"""Day 14 Task G -- TMI CMC calibration figure.

Left : CMC misfit curve, clamp ON vs OFF, with the locked CMC marked and the
       Fukushima CMC=0.25 marked for contrast.
Right: matched zone evacuation rates at the locked CMC vs empirical targets
       (grouped bars, inner/middle/outer), plus the total-evac band annotation.

Output: figures/tmi/day14_calibration.png  (Columbia palette).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from scripts import run_tmi_day14_calibration as cal  # noqa: E402

RES = REPO / "results" / "tmi"
FIG = REPO / "figures" / "tmi"

NAVY, BLUE, LTBLUE, GOLD = "#1F3864", "#2E5FA3", "#D6E4F7", "#C9A227"


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RES / "day14_calibration_grid.csv")
    locked = json.loads((RES / "day14_locked_params.json").read_text())
    cmc0 = float(locked["tmi_cmc_locked"])

    on = df[df["clamp"] == "on"].sort_values("cmc")
    off = df[df["clamp"] == "off"].sort_values("cmc")
    best_off = off.loc[off["misfit"].idxmin()]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 5.2))

    # --- Left: misfit curves ----------------------------------------------
    axL.plot(on["cmc"], on["misfit"], "-o", color=GOLD, ms=4,
             label="clamp ON")
    axL.plot(off["cmc"], off["misfit"], "-o", color=BLUE, ms=4,
             label="clamp OFF")
    axL.axvline(cmc0, color=NAVY, ls="--", lw=1.8,
                label=f"locked TMI CMC = {cmc0:.2f}")
    axL.axvline(0.25, color="#C00000", ls=":", lw=1.8,
                label="Fukushima CMC = 0.25")
    axL.set_xlabel("conflict_movechance (CMC)")
    axL.set_ylabel("misfit (weighted SSE: total + zone evac)")
    axL.set_title("CMC calibration misfit (blend, $\\alpha\\beta\\kappa$ locked)",
                  color=NAVY)
    axL.legend(frameon=False, fontsize=9)
    axL.grid(alpha=0.25)

    # --- Right: zone evac at locked CMC vs empirical -----------------------
    zones = ["inner", "middle", "outer"]
    model = [float(best_off[f"evac_{z}"]) for z in zones]
    target = [cal.TARGET_EVAC[z] for z in zones]
    x = np.arange(len(zones))
    w = 0.38
    axR.bar(x - w / 2, target, w, color=LTBLUE, edgecolor=NAVY,
            label="empirical (Zeigler 1981)")
    axR.bar(x + w / 2, model, w, color=BLUE, edgecolor=NAVY,
            label=f"model @ locked CMC={cmc0:.2f} (clamp OFF)")
    for xi, (m, t) in enumerate(zip(model, target)):
        axR.text(xi + w / 2, m + 0.01, f"{m:.2f}", ha="center", fontsize=8,
                 color=NAVY)
        axR.text(xi - w / 2, t + 0.01, f"{t:.2f}", ha="center", fontsize=8,
                 color=NAVY)
    axR.set_xticks(x)
    axR.set_xticklabels([z.capitalize() for z in zones])
    axR.set_ylabel("evacuation rate")
    axR.set_ylim(0, 1.0)
    axR.set_title("Zone evacuation: model vs empirical", color=NAVY)
    axR.legend(frameon=False, fontsize=9, loc="upper left")
    axR.grid(alpha=0.25, axis="y")

    tot = float(best_off["total_evac"])
    in_band = cal.EVAC_BAND[0] <= tot <= cal.EVAC_BAND[1]
    axR.text(0.5, 0.88,
             f"total evac = {tot:.0%}  (target ~21%, band 15-30%): "
             f"{'IN BAND' if in_band else 'OUT OF BAND'}",
             transform=axR.transAxes, fontsize=9, va="top", ha="center",
             color=("#1a7a1a" if in_band else "#C00000"),
             bbox=dict(boxstyle="round", fc="white", ec=NAVY, alpha=0.85))

    fig.suptitle("TMI Day 14 — CMC calibration (clamp disabled for the "
                 "information regime)", color=NAVY, fontsize=13, y=1.00)
    fig.tight_layout()
    out = FIG / "day14_calibration.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"[plot] wrote {out}")


if __name__ == "__main__":
    main()
