#!/usr/bin/env python3
"""Day 12 Task E — publication figure: TMI zone P_S2 + cumulative departure.

Two panels (Fukushima F5/F6 style, Columbia palette):
  Left  : P_S2 time series by zone (full-mixture). Vertical markers at t=10
          (Governor advisory, c=1.0) and t=16 (Carter visit, Omega recovery).
          Peak P_S2 at t=10 annotated per zone. Lines sit close together
          (uniform Omega) — the visual inverse of Fukushima's diverging zones.
  Right : cumulative departure fraction by zone (mixture), with the Governor's
          advisory line and empirical zone evac targets as horizontal references.

Reads:  results/tmi/day12_ps2_zones.csv, results/tmi/day12_departure_by_zone.csv
Writes: figures/tmi/day12_ps2_zones.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tmi_common_day12 import REPO, MIXTURE_MODE, NAVY, BLUE, GOLD  # noqa: E402

RESULTS = REPO / "results" / "tmi"
FIG = REPO / "figures" / "tmi"
ZONES = ["inner", "middle", "outer"]
ZONE_COLORS = {"inner": "#C00000", "middle": "#C55A11", "outer": BLUE}
ADVISORY_T, RECOVERY_T = 10, 16
# Empirical zone evac targets (Zeigler 1981 zone_group midpoints).
EMP_TARGET = {"inner": 0.55, "middle": 0.50, "outer": 0.16}


def main() -> int:
    FIG.mkdir(parents=True, exist_ok=True)
    zdf = pd.read_csv(RESULTS / "day12_ps2_zones.csv")
    ddf = pd.read_csv(RESULTS / "day12_departure_by_zone.csv")
    dmix = ddf[ddf["decision_mode"] == MIXTURE_MODE]

    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "figure.dpi": 150, "savefig.dpi": 300,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    })
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.2))

    # ---- Left: P_S2 by zone ----
    tmax = int(zdf["timestep"].max())
    for z in ZONES:
        sub = zdf[zdf["zone"] == z].sort_values("timestep")
        axL.plot(sub["timestep"], sub["mean_ps2"], color=ZONE_COLORS[z],
                 lw=2.0, marker="o", ms=3, label=z)
        peak = sub[sub["timestep"] == ADVISORY_T]["mean_ps2"]
        if not peak.empty:
            axL.annotate(f"{peak.iloc[0]:.3f}",
                         (ADVISORY_T, peak.iloc[0]),
                         textcoords="offset points", xytext=(4, 6),
                         fontsize=7, color=ZONE_COLORS[z])
    axL.axvline(ADVISORY_T, color=GOLD, ls="--", lw=1.2)
    axL.text(ADVISORY_T + 0.2, axL.get_ylim()[1] * 0.92,
             "Governor advisory\n(c=1.0, t=10)", fontsize=7, color="#7a6300", va="top")
    axL.axvline(RECOVERY_T, color="#375623", ls=":", lw=1.2)
    axL.text(RECOVERY_T + 0.2, axL.get_ylim()[1] * 0.55,
             "Carter visit\n(Omega recovery, t=16)", fontsize=7, color="#375623", va="top")
    axL.set_xlim(0, tmax)
    axL.set_ylim(0, max(0.12, zdf["mean_ps2"].max() * 1.25))
    axL.set_xlabel("Timestep (6 h)")
    axL.set_ylabel(r"Mean $P_{S2}$ (active agents)")
    axL.set_title("A. Zone $P_{S2}$ — spatially uniform (uniform $\\Omega$)")
    axL.legend(title="origin zone", fontsize=8, loc="upper left")
    axL.grid(alpha=0.2)

    # Spread annotation.
    t10 = zdf[zdf["timestep"] == ADVISORY_T].set_index("zone")["mean_ps2"]
    spread = np.std([t10.get(z, np.nan) for z in ZONES])
    axL.text(0.98, 0.04, f"zone spread @t=10 = {spread:.4f}",
             transform=axL.transAxes, ha="right", fontsize=7.5,
             bbox=dict(boxstyle="round", fc="white", ec=NAVY, alpha=0.9))

    # ---- Right: cumulative departure by zone ----
    for z in ZONES:
        sub = dmix[dmix["zone"] == z].groupby("timestep")["cum_departed_frac"]
        m = sub.mean()
        s = sub.std().fillna(0)
        axR.plot(m.index, m.values, color=ZONE_COLORS[z], lw=2.0, label=z)
        axR.fill_between(m.index, m.values - s.values, m.values + s.values,
                         color=ZONE_COLORS[z], alpha=0.15)
        axR.axhline(EMP_TARGET[z], color=ZONE_COLORS[z], ls=":", lw=1.0, alpha=0.7)
        axR.text(0.3, EMP_TARGET[z] + 0.01, f"Zeigler {z} {EMP_TARGET[z]*100:.0f}%",
                 fontsize=6.5, color=ZONE_COLORS[z])
    axR.axvline(ADVISORY_T, color=GOLD, ls="--", lw=1.2, label="Governor's advisory")
    axR.set_xlim(0, tmax)
    axR.set_ylim(0, 1.05)
    axR.set_xlabel("Timestep (6 h)")
    axR.set_ylabel("Cumulative departed (reached camp)")
    axR.set_title("B. Cumulative departure by zone (mixture)")
    axR.legend(fontsize=8, loc="lower right")
    axR.grid(alpha=0.2)

    fig.suptitle(
        "TMI First Run — Uniform-$\\Omega$ Signature (frozen Fukushima params: "
        r"$\alpha$=1.667, $\beta$=2.167, $\kappa$=18.407, CMC=0.25)",
        fontsize=10.5, y=1.02)
    fig.tight_layout()
    out = FIG / "day12_ps2_zones.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
