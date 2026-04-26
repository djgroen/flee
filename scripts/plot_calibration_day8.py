#!/usr/bin/env python3
"""Day 8 figure generation.

Reads from ``results/day8/`` and writes to ``figures/fukushima/day8/``.

  D8-1 : Stage-1 CMC grid search surface (hayano_t4, corridor_inland_pct).
  D8-2 : Stage-2 alpha-by-beta L2 heatmap at kappa=kappa*.
  D8-3 : Stage-2 L2 vs kappa slice at (alpha*, beta*).
  D8-4 : Validation violins for the six QoIs at locked parameters.
  D8-5 : Zone-level P_S2 timeseries at locked parameters (3 panels).

Use ``--v2`` for the revised Day 8 figures (CMC physically anchored at 0.25,
extended beta grid, boundary auto-extension). v2 outputs are written with
``_v2`` suffix; v1 figures are left untouched.

Usage::

  python3 scripts/plot_calibration_day8.py
  python3 scripts/plot_calibration_day8.py --v2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

RES = REPO / "results" / "day8"
FIG = REPO / "figures" / "fukushima" / "day8"

from scripts.run_calibration_day8 import (  # noqa: E402
    HAYANO_TARGET_USED, HAYANO_TARGET_RAW, CORRIDOR_TARGET,
    DIP_TARGET, TROUGH_TARGET,
    CMC_FIXED, MID_PS2_DIP_TARGET, MID_PS2_TROUGH_TARGET,
    HAYANO_T4_EXPECTED, HAYANO_T4_RAW_GAP_V2,
)

PROCESS_QOIS = {"mid_ps2_dip", "mid_ps2_trough"}
OUTCOME_QOIS = {"hayano_t4", "corridor_inland_pct", "mid_ps2_recovery"}
DIAG_QOIS    = {"blend_inner_t7"}
QOI_ORDER    = ["hayano_t4", "mid_ps2_dip", "mid_ps2_trough",
                "mid_ps2_recovery", "corridor_inland_pct", "blend_inner_t7"]
QOI_TARGETS  = {
    "hayano_t4":           HAYANO_TARGET_USED,
    "mid_ps2_dip":         DIP_TARGET,
    "mid_ps2_trough":      TROUGH_TARGET,
    "corridor_inland_pct": CORRIDOR_TARGET,
}


def _setup():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False,
    })


# ---------------------------------------------------------------------------
# D8-1
# ---------------------------------------------------------------------------

def fig_d8_1(v2: bool = False):
    summary = pd.read_csv(RES / "stage1_summary.csv")
    with (RES / "stage1_cmc_star.json").open() as fh:
        star = json.load(fh)
    cmc_star = star["cmc_star"]

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), sharex=True)
    cmc = summary["cmc"].values

    # Panel A: hayano_t4 vs CMC
    ax = axes[0]
    h = summary["hayano_t4_mean"].values
    hsd = summary["hayano_t4_std"].fillna(0).values
    ax.fill_between(cmc, h - hsd, h + hsd, alpha=0.20, color="#1f77b4")
    ax.plot(cmc, h, color="#1f77b4", lw=1.6, label="hayano_t4 (sim)")
    ax.axhline(HAYANO_TARGET_USED, ls="--", color="#222",
               label=f"proxy target {HAYANO_TARGET_USED:.2f}")
    ax.axhspan(HAYANO_TARGET_USED * 0.9, HAYANO_TARGET_USED * 1.1,
               color="#222", alpha=0.07)
    if v2:
        ax.axvline(cmc_star, ls=":", color="#d62728",
                   label=f"Stage 1 optimum {cmc_star:.2f} "
                         "(floor solution -- not used)")
        ax.axvline(CMC_FIXED, ls="-", color="#1B7838", lw=2.0,
                   label=f"Physical anchor CMC = {CMC_FIXED:.2f}")
    else:
        ax.axvline(cmc_star, ls=":", color="#d62728",
                   label=f"CMC* = {cmc_star:.2f}")
    ax.set_xlabel("CMC")
    ax.set_ylabel("hayano_t4")
    ax.set_title("Stage 1 -- Hayano t=4 vs CMC")
    ax.legend(loc="best", fontsize=7.5)
    if v2:
        textbox = (
            f"Raw Hayano target ({HAYANO_TARGET_RAW}) outside CMC range.\n"
            f"Model floor: hayano_t4 ~= 0.29 at CMC=0.10.\n"
            f"Proxy target {HAYANO_TARGET_USED:.2f} unreachable in [0,1].\n"
            f"CMC fixed at {CMC_FIXED:.2f} on physical grounds\n"
            f"(Hayano 2013 inner-zone clearing rate).\n"
            f"1.008 is outside physical range."
        )
    else:
        textbox = (
            f"Raw Hayano target ({HAYANO_TARGET_RAW}) is outside CMC range.\n"
            f"Calibrated against within-range proxy {HAYANO_TARGET_USED:.2f}."
        )
    ax.text(0.02, 0.97, textbox,
            transform=ax.transAxes, va="top", ha="left",
            fontsize=7, color="#a3070b",
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor="#FFF3CD", edgecolor="#a3070b", lw=0.8))

    # Panel B: corridor vs CMC
    ax = axes[1]
    c = summary["corridor_inland_pct_mean"].values
    csd = summary["corridor_inland_pct_std"].fillna(0).values
    ax.fill_between(cmc, c - csd, c + csd, alpha=0.20, color="#2ca02c")
    ax.plot(cmc, c, color="#2ca02c", lw=1.6, label="corridor (sim)")
    ax.axhline(CORRIDOR_TARGET, ls="--", color="#222",
               label=f"target {CORRIDOR_TARGET:.2f}")
    ax.axhspan(CORRIDOR_TARGET * 0.9, CORRIDOR_TARGET * 1.1,
               color="#222", alpha=0.07)
    if v2:
        ax.axvline(cmc_star, ls=":", color="#d62728",
                   label=f"Stage 1 optimum {cmc_star:.2f} (not used)")
        ax.axvline(CMC_FIXED, ls="-", color="#1B7838", lw=2.0,
                   label=f"Physical anchor {CMC_FIXED:.2f}")
    else:
        ax.axvline(cmc_star, ls=":", color="#d62728",
                   label=f"CMC* = {cmc_star:.2f}")
    ax.set_xlabel("CMC")
    ax.set_ylabel("corridor_inland_pct")
    ax.set_title("Stage 1 -- Inland-corridor share vs CMC")
    ax.legend(loc="best", fontsize=7.5)

    title = ("Fig D8-1v2 -- Stage 1 CMC grid (CMC anchored at 0.25 for v2)"
             if v2 else "Fig D8-1 -- Stage 1 CMC grid search (Day 8)")
    fig.suptitle(title, y=1.02)
    fig.tight_layout()
    fname = "D8-1v2_stage1_cmc_grid.png" if v2 else "D8-1_stage1_cmc_grid.png"
    fig.savefig(FIG / fname, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# D8-2
# ---------------------------------------------------------------------------

def fig_d8_2(v2: bool = False):
    suffix = "_v2" if v2 else ""
    fine = pd.read_csv(RES / f"stage2_fine_grid{suffix}.csv")
    with (RES / f"stage2_params{suffix}.json").open() as fh:
        s2 = json.load(fh)
    a_star, b_star, k_star = s2["alpha_star"], s2["beta_star"], s2["kappa_star"]
    L2_min = s2["L2_min"]

    grid = (fine.groupby(["alpha", "beta", "kappa"])["L2"]
            .mean().reset_index())
    closest_k = grid["kappa"].iloc[(grid["kappa"] - k_star).abs().argmin()]
    slab = grid[np.isclose(grid["kappa"], closest_k)]
    if slab.empty:
        print("[D8-2] no rows at kappa* slice; skipping")
        return
    pivot = slab.pivot(index="beta", columns="alpha", values="L2")

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    im = ax.imshow(pivot.values, origin="lower", aspect="auto",
                   extent=[pivot.columns.min(), pivot.columns.max(),
                           pivot.index.min(), pivot.index.max()],
                   cmap="viridis_r")
    levels = [1.5 * L2_min, 2.0 * L2_min]
    try:
        cs = ax.contour(pivot.columns.values, pivot.index.values, pivot.values,
                        levels=levels, colors=["white", "#bbb"],
                        linestyles=["--", ":"], linewidths=1.2)
        ax.clabel(cs, fmt={levels[0]: "1.5x", levels[1]: "2x"}, fontsize=7)
    except Exception:
        pass
    ax.scatter([a_star], [b_star], marker="x", s=120, color="red", lw=2.5,
               label=fr"$(\alpha^*, \beta^*) = ({a_star:.2f}, {b_star:.2f})$")
    ax.set_xlabel(r"$\alpha$")
    ax.set_ylabel(r"$\beta$")
    if v2:
        bw = s2.get("boundary_warning", "NONE")
        if "PERSISTENT" in bw:
            note = f"boundary -- see stage2_params_v2.json ({bw})"
        elif (b_star > 0.3 + 1e-9 and b_star < 10.0 - 1e-9
              and a_star > 0.5 + 1e-9 and a_star < 5.0 - 1e-9):
            note = "interior solution"
        else:
            note = f"boundary -- see stage2_params_v2.json ({bw})"
        ax.set_title(f"Fig D8-2v2 -- Stage 2 L2 slice at kappa = "
                     f"{closest_k:.2f}\n({note})")
    else:
        ax.set_title(f"Fig D8-2 -- Stage 2 L2 slice at kappa = {closest_k:.2f}")
    cbar = fig.colorbar(im, ax=ax, fraction=0.045)
    cbar.set_label("L2 (lower is better)")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fname = ("D8-2v2_stage2_alpha_beta_L2.png" if v2
             else "D8-2_stage2_alpha_beta_L2.png")
    fig.savefig(FIG / fname, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# D8-3
# ---------------------------------------------------------------------------

def fig_d8_3(v2: bool = False):
    suffix = "_v2" if v2 else ""
    fine = pd.read_csv(RES / f"stage2_fine_grid{suffix}.csv")
    with (RES / f"stage2_params{suffix}.json").open() as fh:
        s2 = json.load(fh)
    a_star, b_star, k_star = s2["alpha_star"], s2["beta_star"], s2["kappa_star"]

    sub = fine[np.isclose(fine["alpha"], a_star)
               & np.isclose(fine["beta"], b_star)]
    if sub.empty:
        # Snap to nearest grid (alpha, beta) in case of float-drift
        cand = fine.groupby(["alpha", "beta"])["L2"].mean().reset_index()
        cand["d"] = ((cand["alpha"] - a_star) ** 2
                     + (cand["beta"] - b_star) ** 2)
        ab = cand.loc[cand["d"].idxmin()]
        sub = fine[np.isclose(fine["alpha"], ab["alpha"])
                   & np.isclose(fine["beta"], ab["beta"])]

    grouped = sub.groupby("kappa")["L2"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.errorbar(grouped["kappa"], grouped["mean"],
                yerr=grouped["std"].fillna(0),
                fmt="o-", color="#1ABC9C", capsize=3)
    ax.axvline(k_star, ls=":", color="#d62728",
               label=fr"$\kappa^* = {k_star:.2f}$")
    span_lo = max(0.0, 0.5 * k_star)
    span_hi = 1.5 * k_star
    ax.axvspan(span_lo, span_hi, color="#1ABC9C", alpha=0.10,
               label=r"$\kappa \pm 50\%$")
    ax.set_xlabel(r"$\kappa$")
    ax.set_ylabel("L2 (mean +/- std)")
    title_prefix = "Fig D8-3v2" if v2 else "Fig D8-3"
    ax.set_title(f"{title_prefix} -- L2 vs kappa at "
                 fr"$\alpha^*={a_star:.2f}, \beta^*={b_star:.2f}$")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fname = ("D8-3v2_stage2_kappa_slice.png" if v2
             else "D8-3_stage2_kappa_slice.png")
    fig.savefig(FIG / fname, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# D8-4
# ---------------------------------------------------------------------------

def fig_d8_4(v2: bool = False):
    suffix = "_v2" if v2 else ""
    ens = pd.read_csv(RES / f"validation_ensemble{suffix}.csv")
    if ens.empty:
        print(f"[D8-4{suffix}] empty validation ensemble; skipping")
        return
    qoi_targets_local = dict(QOI_TARGETS)
    if v2:
        # In v2 the dip and trough targets shift to the forward-pass-anchored
        # values. hayano_t4 is no longer a calibration target -- show "N/A".
        qoi_targets_local["mid_ps2_dip"]    = MID_PS2_DIP_TARGET
        qoi_targets_local["mid_ps2_trough"] = MID_PS2_TROUGH_TARGET
        qoi_targets_local.pop("hayano_t4", None)
        qoi_targets_local.pop("corridor_inland_pct", None)
    fig, ax = plt.subplots(figsize=(11.0, 4.6))
    data = []
    labels = []
    colors = []
    for q in QOI_ORDER:
        if q not in ens.columns:
            continue
        vals = ens[q].dropna().values
        if len(vals) == 0:
            continue
        data.append(vals)
        labels.append(q)
        if q in PROCESS_QOIS:
            colors.append("#1f77b4")
        elif q in DIAG_QOIS:
            colors.append("#7f7f7f")
        else:
            colors.append("#E67E22")
    parts = ax.violinplot(data, showmeans=True, showmedians=False)
    for body, c in zip(parts["bodies"], colors):
        body.set_facecolor(c); body.set_alpha(0.55); body.set_edgecolor("k")
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=18, ha="right")
    for i, q in enumerate(labels, start=1):
        if q in qoi_targets_local:
            t = qoi_targets_local[q]
            ax.hlines(t, i - 0.4, i + 0.4, colors="k", linestyles="--", lw=1.0)
            ax.text(i, t, f" {t:.3f}", fontsize=7, va="bottom", color="#222")
        elif v2 and q == "hayano_t4":
            ax.text(i, ax.get_ylim()[1] * 0.95, "N/A",
                    fontsize=8, ha="center", color="#a3070b",
                    fontweight="bold")
            ax.annotate(
                "Model boundary condition\nsee hayano_tension in\n"
                "validation_summary_v2.json",
                xy=(i, np.median(data[i - 1])),
                xytext=(i + 0.4, ax.get_ylim()[1] * 0.75),
                fontsize=6.5, color="#a3070b",
                arrowprops=dict(arrowstyle="-", color="#a3070b", lw=0.6))
    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor="#1f77b4", alpha=0.55, label="process QoIs (calibration)"),
        Patch(facecolor="#E67E22", alpha=0.55, label="outcome QoIs (validation)"),
        Patch(facecolor="#7f7f7f", alpha=0.55, label="diagnostic"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=8)
    title = ("Fig D8-4v2 -- Validation ensemble at locked v2 parameters"
             if v2 else
             "Fig D8-4 -- Validation ensemble at locked parameters")
    ax.set_title(title)
    ax.set_ylabel("QoI value")
    fig.tight_layout()
    fname = ("D8-4v2_validation_violins.png" if v2
             else "D8-4_validation_violins.png")
    fig.savefig(FIG / fname, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# D8-5
# ---------------------------------------------------------------------------

def fig_d8_5(v2: bool = False):
    suffix = "_v2" if v2 else ""
    ts_path = RES / f"ps2_timeseries{suffix}.csv"
    if not ts_path.exists():
        print(f"[D8-5{suffix}] {ts_path.name} missing; skipping")
        return
    ts = pd.read_csv(ts_path)
    if ts.empty:
        print("[D8-5] ps2_timeseries empty; skipping")
        return

    zones = ["inner", "mid", "outer"]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), sharey=True)
    for ax, zone in zip(axes, zones):
        sub = ts[ts["zone"] == zone]
        if sub.empty:
            ax.text(0.5, 0.5, f"no data\n{zone}", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_title(zone)
            continue
        agg = (sub.groupby("timestep")["mean_ps2"]
                  .agg(["mean", "std"]).reset_index())
        m = agg["mean"].values
        s = agg["std"].fillna(0).values
        t = agg["timestep"].values
        ax.fill_between(t, m - s, m + s, color="#1f77b4", alpha=0.20)
        ax.plot(t, m, color="#1f77b4", lw=1.6,
                label="blend (locked)")
        if zone == "mid":
            ax.axvspan(0,  10, color="#888", alpha=0.05)
            ax.axvspan(10, 24, color="#E67E22", alpha=0.07)
            ax.axvspan(24, 72, color="#1ABC9C", alpha=0.05)
            ax.text(5,  0.95, "S1-dominated", fontsize=7, ha="center",
                    transform=ax.get_xaxis_transform())
            ax.text(17, 0.95, "differentiation", fontsize=7, ha="center",
                    transform=ax.get_xaxis_transform())
            ax.text(48, 0.95, "recovery", fontsize=7, ha="center",
                    transform=ax.get_xaxis_transform())
        ax.set_xlabel("timestep")
        ax.set_title(zone)
        if zone == "inner":
            ax.set_ylabel(r"mean $P_{S2}$")
        ax.set_ylim(0.0, 1.0)
    title = ("Fig D8-5v2 -- Zone-level P_S2 trajectories at locked v2 parameters"
             if v2 else
             "Fig D8-5 -- Zone-level P_S2 trajectories at locked parameters")
    fig.suptitle(title, y=1.02)
    fig.tight_layout()
    fname = ("D8-5v2_zone_ps2_timeseries.png" if v2
             else "D8-5_zone_ps2_timeseries.png")
    fig.savefig(FIG / fname, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Day 8 figure generation.")
    ap.add_argument("--v2", action="store_true",
                    help="Produce v2 figures (CMC anchored at 0.25, "
                         "extended beta grid).")
    args = ap.parse_args()

    _setup()
    FIG.mkdir(parents=True, exist_ok=True)
    fig_d8_1(v2=args.v2)
    fig_d8_2(v2=args.v2)
    fig_d8_3(v2=args.v2)
    fig_d8_4(v2=args.v2)
    fig_d8_5(v2=args.v2)
    suffix = "v2" if args.v2 else ""
    print(f"[plot] wrote D8-1..5{suffix} to {FIG}")


if __name__ == "__main__":
    main()
