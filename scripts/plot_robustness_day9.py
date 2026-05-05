#!/usr/bin/env python3
"""Day 9 figures: kappa extension (D9-1) and CMC robustness (D9-2)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
RES_D9 = REPO / "results" / "day9"
FIG_D9 = REPO / "figures" / "fukushima" / "day9"

KAPPA_LOCKED = 18.40740740740741
ALPHA_LOCKED = 1.6666666666666667
BETA_LOCKED  = 2.1666666666666665
FLAT_THRESHOLD = 0.0005


def plot_d9_1():
    summary = pd.read_csv(RES_D9 / "kappa_extension_summary.csv")
    payload = json.loads((RES_D9 / "kappa_verdict.json").read_text())

    L2_min = float(payload["L2_at_min"])
    kappa_at_min = float(payload["kappa_at_L2_min"])
    flat_onset = float(payload["flat_onset_kappa"])
    flat_region = payload["flat_region"]
    flat_strict = payload.get("flat_onset_strict_algorithm")
    verdict = payload["verdict"]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.errorbar(summary["kappa"], summary["L2_mean"],
                yerr=summary["L2_std"],
                fmt="o-", lw=1.4, ms=4, capsize=3,
                color="#1f77b4", ecolor="#1f77b4",
                label="L2_mean +/- 1sigma (10 reps)")

    # Shaded horizontal band: flat-threshold region above L2_min.
    ax.axhspan(L2_min, L2_min + FLAT_THRESHOLD,
               color="#cccccc", alpha=0.35,
               label=f"L2_min .. L2_min+{FLAT_THRESHOLD} (flat threshold)")
    # Shaded vertical region: flat region (manual / strict).
    ax.axvspan(flat_region[0], flat_region[1],
               color="#a6cee3", alpha=0.20,
               label=f"flat region [{flat_region[0]:.0f}, {flat_region[1]:.0f}]")

    # Vertical line at Day 8 v2 operating point.
    ax.axvline(KAPPA_LOCKED, color="red", ls="--", lw=1.5,
               label=f"Day 8 v2 kappa* = {KAPPA_LOCKED:.3f}")
    if abs(kappa_at_min - KAPPA_LOCKED) > 1e-3:
        ax.axvline(kappa_at_min, color="green", ls="--", lw=1.3,
                   label=f"kappa@L2_min = {kappa_at_min:.2f}")
    if flat_strict is not None and abs(flat_strict - flat_onset) > 1e-3:
        ax.axvline(flat_strict, color="#888888", ls=":", lw=1.0,
                   label=f"strict-algo flat_onset = {flat_strict:.0f}")

    ax.set_xlabel("kappa")
    ax.set_ylabel("L2_mean")
    ax.set_title("kappa characterisation: L2 vs kappa at locked "
                 "(CMC=0.25, alpha=1.67, beta=2.17)")
    ax.text(0.02, 0.98,
            f"verdict: {verdict}\n"
            f"flat_onset_kappa = {flat_onset:.1f}\n"
            f"L2_min = {L2_min:.4g}\n"
            f"L2 @ kappa~18 = {payload['L2_at_day8_kappa']:.4g}",
            transform=ax.transAxes, va="top", ha="left",
            fontsize=9,
            bbox=dict(boxstyle="round", facecolor="white",
                      edgecolor="#888888", alpha=0.85))
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = FIG_D9 / "D9-1_kappa_extension.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[d9-1] wrote {out}")


def plot_d9_2():
    payload = json.loads(
        (RES_D9 / "cmc_robustness_verdict.json").read_text())
    cmcs = np.array(payload["cmc_values_tested"], dtype=float)
    res = payload["results"]
    alphas = np.array([res[f"{c:.3f}"]["alpha_star"] for c in cmcs])
    betas  = np.array([res[f"{c:.3f}"]["beta_star"] for c in cmcs])
    kappas = np.array([res[f"{c:.3f}"]["kappa_star"] for c in cmcs])

    fine = payload["fine_grid_axes_default"]
    a_step = abs(fine["alpha"][1] - fine["alpha"][0])
    b_step = abs(fine["beta"][1] - fine["beta"][0])
    k_step = abs(fine["kappa"][1] - fine["kappa"][0])

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), sharex=True)

    panels = [
        ("alpha*", alphas, ALPHA_LOCKED, a_step, axes[0]),
        ("beta*",  betas,  BETA_LOCKED,  b_step, axes[1]),
        ("kappa*", kappas, KAPPA_LOCKED, k_step, axes[2]),
    ]
    for label, vals, locked, step, ax in panels:
        ax.errorbar(cmcs, vals, yerr=step, fmt="o-",
                    color="#1f77b4", capsize=4, ms=6, lw=1.5)
        ax.axhline(locked, color="black", ls="--", lw=1.2,
                   label=f"Day 8 v2 = {locked:.3f}")
        # +/-15% STABLE band
        ax.axhspan(locked * 0.85, locked * 1.15,
                   color="#a6dba0", alpha=0.30,
                   label="+/-15% (STABLE band)")
        ax.axvline(0.25, color="red", ls="--", lw=1.0)
        ax.set_xlabel("CMC")
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=8)
    fig.suptitle(
        "CMC robustness: cognitive parameters vs CMC perturbation "
        f"(verdict: {payload['stability_verdict']})", y=1.02)
    fig.tight_layout()
    out = FIG_D9 / "D9-2_cmc_robustness.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[d9-2] wrote {out}")


def main():
    FIG_D9.mkdir(parents=True, exist_ok=True)
    if (RES_D9 / "kappa_extension_summary.csv").exists():
        plot_d9_1()
    else:
        print("[plot] Task A summary missing; skipping D9-1")
    if (RES_D9 / "cmc_robustness_verdict.json").exists():
        plot_d9_2()
    else:
        print("[plot] Task B verdict missing; skipping D9-2")


if __name__ == "__main__":
    main()
