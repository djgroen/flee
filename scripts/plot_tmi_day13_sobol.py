#!/usr/bin/env python3
"""Day 13 -- Sobol indices figure (Task E) -> figures/tmi/day13_sobol_indices.png.

Grouped horizontal bar charts of total-order ST with bootstrap-CI whiskers,
faceted by the four Tier-1 (clamp-insensitive) QoIs, plus an adjacent panel
contrasting clamp-ON vs clamp-OFF on the saturated total-evac QoI so the clamp's
masking of CMC sensitivity is visible. Columbia palette.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

RES = REPO / "results" / "tmi"
FIG = REPO / "figures" / "tmi"

NAVY, BLUE, LTBLUE, GOLD = "#1F3864", "#2E5FA3", "#D6E4F7", "#C9A227"
FACTORS = ["cmc", "alpha", "beta", "kappa"]
FACTOR_LABELS = {"cmc": "CMC", "alpha": r"$\alpha$",
                 "beta": r"$\beta$", "kappa": r"$\kappa$"}
FACTOR_COLORS = {"cmc": NAVY, "alpha": BLUE, "beta": GOLD, "kappa": LTBLUE}

TIER1 = ["frac_by_t8", "median_departure", "peak_ps2", "zone_ps2_spread_t10"]
QOI_LABELS = {
    "frac_by_t8": "Frac. departed by t=8\n(Tier 1, pre-clamp)",
    "median_departure": "Median departure t\n(Tier 1)",
    "peak_ps2": r"Peak mean $P_{S2}$" + "\n(Tier 1)",
    "zone_ps2_spread_t10": r"Zone $P_{S2}$ spread t=10" + "\n(Tier 1, P1)",
    "total_evac": "Total town evac rate\n(Tier 3, saturated)",
}
FUKU_LOCKED = {"alpha": 1.6667, "beta": 2.1667, "kappa": 18.407}


def _bars(ax, sub, title, low_var=False):
    y = np.arange(len(FACTORS))
    st = [float(sub[sub.factor == f]["ST"].iloc[0]) if len(sub[sub.factor == f]) else 0.0
          for f in FACTORS]
    lo = [float(sub[sub.factor == f]["ST_ci_low"].iloc[0]) if len(sub[sub.factor == f]) else 0.0
          for f in FACTORS]
    hi = [float(sub[sub.factor == f]["ST_ci_high"].iloc[0]) if len(sub[sub.factor == f]) else 0.0
          for f in FACTORS]
    err_lo = [max(0.0, s - l) for s, l in zip(st, lo)]
    err_hi = [max(0.0, h - s) for s, h in zip(st, hi)]
    colors = [FACTOR_COLORS[f] for f in FACTORS]
    ax.barh(y, st, color=colors, edgecolor=NAVY, linewidth=0.7,
            xerr=[err_lo, err_hi], capsize=3,
            error_kw={"ecolor": "#444", "elinewidth": 0.9})
    ax.axvline(0.10, ls=":", color="#999", lw=0.8)
    ax.axvline(0.0, ls="-", color="#222", lw=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([FACTOR_LABELS[f] for f in FACTORS])
    ax.set_xlim(-0.05, max(1.05, max(hi) + 0.1) if hi else 1.05)
    ax.set_title(title, fontsize=9)
    ax.set_xlabel(r"$S_T$ (total-order)")
    if low_var:
        ax.text(0.97, 0.04, "LOW_VARIANCE\n(indices unreliable)",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=7, color="#A30B0B", style="italic")
    for yi, s in zip(y, st):
        ax.text(s + 0.02, yi, f"{s:.2f}", va="center", fontsize=7, color="#333")


def main():
    idx_path = RES / "day13_sobol_indices.csv"
    if not idx_path.exists():
        sys.exit(f"Missing {idx_path}; run compute_tmi_day13_indices.py first.")
    FIG.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(idx_path)
    on = df[df.clamp == "on"]
    off = df[df.clamp == "off"]
    has_off = len(off) > 0

    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False,
    })
    fig, axes = plt.subplots(1, 5, figsize=(18, 3.8))

    # --- 4 Tier-1 facets (clamp ON) ---
    for ax, qoi in zip(axes[:4], TIER1):
        sub = on[on.qoi == qoi]
        low = len(sub) and sub["variance_flag"].iloc[0] in ("LOW_VARIANCE", "CONSTANT")
        _bars(ax, sub, QOI_LABELS[qoi], low_var=bool(low))

    # --- panel 5: clamp ON vs OFF on total_evac (Tier-3, saturated) ---
    ax = axes[4]
    y = np.arange(len(FACTORS))
    h = 0.38
    sub_on = on[on.qoi == "total_evac"]
    st_on = [float(sub_on[sub_on.factor == f]["ST"].iloc[0]) if len(sub_on[sub_on.factor == f]) else 0.0
             for f in FACTORS]
    ax.barh(y + h / 2, st_on, height=h, color=BLUE, edgecolor=NAVY,
            linewidth=0.7, label="clamp ON")
    if has_off:
        sub_off = off[off.qoi == "total_evac"]
        st_off = [float(sub_off[sub_off.factor == f]["ST"].iloc[0]) if len(sub_off[sub_off.factor == f]) else 0.0
                  for f in FACTORS]
        ax.barh(y - h / 2, st_off, height=h, color=GOLD, edgecolor=NAVY,
                linewidth=0.7, label="clamp OFF")
    ax.axvline(0.10, ls=":", color="#999", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([FACTOR_LABELS[f] for f in FACTORS])
    ax.set_xlim(-0.05, 1.05)
    ax.set_xlabel(r"$S_T$ (total-order)")
    ax.set_title(QOI_LABELS["total_evac"] + "\nclamp ON vs OFF", fontsize=9)
    ax.legend(loc="lower right", fontsize=7)

    locked = "  ".join(f"{FACTOR_LABELS[k]}={v:.3f}" for k, v in FUKU_LOCKED.items())
    fig.suptitle(
        "Day 13 - TMI four-factor Sobol total-order indices (95% bootstrap CIs); "
        "dotted line = ST 0.10 identifiability threshold.   "
        f"Fukushima-locked: {locked}",
        fontsize=10, y=1.04)
    fig.tight_layout()
    out = FIG / "day13_sobol_indices.png"
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] -> {out}")


if __name__ == "__main__":
    main()
