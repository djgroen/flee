#!/usr/bin/env python3
"""Day 15 Task F -- P_S2 trajectory comparison: TMI (uniform/volatile) vs
Fukushima (graded/stable).

Left  : TMI zone-P_S2 trajectories on v2 (simulated, locked conflict-dependent
        System-1 + locked alpha/beta/kappa). Expected SPATIALLY UNIFORM (zone
        lines on top of each other) and TEMPORALLY VOLATILE (collapse at the
        advisory spike, recover after Carter).
Right : Fukushima zone-P_S2 -- a PARAMETER-BASED reference (no committed
        Fukushima trajectory CSV exists). Built from P_S2 = Psi(x)*Omega(c_zone)
        with the LOCKED alpha/beta on a SPATIAL conflict gradient (inner high ->
        outer low) that is TEMPORALLY STABLE (sustained plume). Expected
        SPATIALLY GRADED (separated lines) and TEMPORALLY STABLE. Labelled as a
        reference; a simulation-derived, parameter-matched Fukushima spread is a
        Day-16 item.

Output: figures/tmi/day15_ps2_comparison.png  (Columbia palette).
"""
from __future__ import annotations

import contextlib
import io
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from scripts import tmi_common_day15 as tc  # noqa: E402

FIG = REPO / "figures" / "tmi"
ALPHA, BETA, KAPPA = tc.FROZEN_ALPHA, tc.FROZEN_BETA, tc.FROZEN_KAPPA
LOCK_BASE, LOCK_CMAX = 0.05, 0.50
NAVY, BLUE, LTBLUE, GOLD = "#1F3864", "#2E5FA3", "#D6E4F7", "#C9A227"
ZONE_COLORS = {"inner": "#C00000", "middle": "#C55A11", "outer": "#2E5FA3"}


def _psi(x, alpha=ALPHA):
    return 0.1 + 0.9 * (1.0 - math.exp(-alpha * max(0.0, x)))


def _omega(c, beta=BETA):
    return math.exp(-beta * max(0.0, min(1.0, c)))


def tmi_zone_ps2():
    """Mean P_S2 (sys2_weight) by initial_zone over time on v2 (5 seeds)."""
    frames = []
    for s in [0, 1, 2, 3, 4]:
        with contextlib.redirect_stdout(io.StringIO()):
            adf, _arr, _mob = tc.run_one(
                "blend", 1000, tc.T_SCHED, s, alpha=ALPHA, beta=BETA, kappa=KAPPA,
                cmc=LOCK_BASE, enable_panic_clamp=False, network=tc.TMI_V2,
                cmc_conflict_dependent=True, cmc_max=LOCK_CMAX)
        g = (adf.groupby(["timestep", "initial_zone"])["sys2_weight"]
             .mean().reset_index())
        frames.append(g)
    allg = pd.concat(frames).groupby(["timestep", "initial_zone"])["sys2_weight"].mean()
    return allg.reset_index()


def fukushima_reference():
    """Parameter-based Fukushima zone-P_S2 (graded, stable). Mean Psi from
    Beta(2,5) experience; spatial conflict gradient, temporally sustained."""
    x_mean = 2.0 / (2.0 + 5.0)               # Beta(2,5) mean experience
    psi = _psi(x_mean)
    # sustained plume: each zone holds a near-constant conflict level.
    zone_c = {"inner": 0.90, "middle": 0.50, "outer": 0.20}
    t = np.arange(0, tc.T_SCHED + 1)
    # gentle sustained profile (ramp to plateau) -- temporally STABLE vs TMI spike
    ramp = np.clip(t / 3.0, 0, 1)
    out = {}
    for z, c in zone_c.items():
        c_t = c * ramp                       # reach plateau by t~3, then hold
        out[z] = np.array([psi * _omega(ci) for ci in c_t])
    return t, out, psi


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    tmi = tmi_zone_ps2()
    fk_t, fk, psi = fukushima_reference()

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    # --- Left: TMI (uniform, volatile) ---
    for z in ("inner", "middle", "outer"):
        sub = tmi[tmi["initial_zone"] == z].sort_values("timestep")
        axL.plot(sub["timestep"], sub["sys2_weight"], "-o", ms=3,
                 color=ZONE_COLORS[z], label=f"{z}", lw=2)
    axL.axvline(10, color=GOLD, ls="--", lw=1.5)
    axL.text(10.2, axL.get_ylim()[1] * 0.95, "advisory (t10)", color=GOLD,
             fontsize=8, va="top")
    axL.axvline(16, color="#2E7D32", ls="--", lw=1.5)
    axL.text(16.2, axL.get_ylim()[1] * 0.80, "Carter (t16)", color="#2E7D32",
             fontsize=8, va="top")
    axL.set_title("TMI (v2): zone $P_{S2}$ — spatially UNIFORM, temporally VOLATILE",
                  color=NAVY, fontsize=11)
    axL.set_xlabel("timestep")
    axL.set_ylabel("$P_{S2} = \\Psi \\cdot \\Omega$")
    axL.legend(title="origin zone", fontsize=8)
    axL.grid(alpha=0.3)

    # --- Right: Fukushima reference (graded, stable) ---
    for z in ("inner", "middle", "outer"):
        axR.plot(fk_t, fk[z], "-", color=ZONE_COLORS[z], lw=2.5, label=f"{z}")
    axR.set_title("Fukushima (parameter reference): spatially GRADED, "
                  "temporally STABLE", color=NAVY, fontsize=11)
    axR.set_xlabel("timestep")
    axR.legend(title="zone", fontsize=8)
    axR.grid(alpha=0.3)
    axR.text(0.5, 0.02,
             "Parameter-based (locked $\\alpha,\\beta$) on a spatial conflict\n"
             "gradient; simulation-derived parameter-matched spread = Day-16 item.",
             transform=axR.transAxes, fontsize=7.5, color="#555555", ha="center")

    fig.suptitle("Day 15 — $P_{S2}$ trajectories: uniform-$\\Omega$ (TMI, info) "
                 "vs spatial-$\\Omega$ (Fukushima, plume)",
                 color=NAVY, fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIG / "day15_ps2_comparison.png"
    fig.savefig(out, dpi=150)
    print(f"[figure] -> {out}")

    # quick uniformity / volatility report for the verdict
    piv = tmi.pivot(index="timestep", columns="initial_zone", values="sys2_weight")
    spread = float((piv.max(axis=1) - piv.min(axis=1)).mean())
    volatility = float(piv.mean(axis=1).std())
    print(f"[TMI] mean cross-zone P_S2 spread = {spread:.4f} (small => uniform)")
    print(f"[TMI] temporal std of mean P_S2  = {volatility:.4f} (large => volatile)")
    fk_spread = float(np.mean([abs(fk['inner'][i] - fk['outer'][i])
                               for i in range(len(fk_t))]))
    print(f"[Fukushima ref] mean inner-outer P_S2 gap = {fk_spread:.4f} (graded)")


if __name__ == "__main__":
    main()
