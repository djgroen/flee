#!/usr/bin/env python3
"""
Day 6 Section 4 — conflict_movechance sweep for Day 8 preparation.

Sweeps ConflictMoveChance ∈ {0.25, 0.35, 0.45, 0.55, 0.65, 0.75} on the
Baseline scenario with α=1.0, β=2.0, κ=5.0 fixed, blend mode only,
5 ensemble members. Records hayano_t4 per (cmc, member).

Produces Fig D6-3 (hayano_t4 vs ConflictMoveChance with ±1σ bars,
horizontal references at the Hayano-2013 target 0.78 and the Day 3 default
0.5). Linearly interpolates the cmc value that achieves hayano_t4 = 0.78
and writes results/day6/physical_param_target.json.

This is reconnaissance for Day 8 only — the live ConflictMoveChance is
NOT modified. If the target lies outside [0.25, 0.75], the script flags a
potential tension between Hayano timing and level data.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import run_day5_scenarios as d5  # noqa: E402
from scripts import run_fukushima_day3 as d3  # noqa: E402
from flee.SimulationSettings import SimulationSettings  # noqa: E402

RES_D6 = REPO / "results" / "day6"
FIG_D6 = REPO / "figures" / "fukushima" / "day6"

CMC_GRID_FULL = [0.25, 0.35, 0.45, 0.55, 0.65, 0.75]
CMC_GRID_QUICK = [0.25, 0.50, 0.75]
HAYANO_TARGET = 0.78
HAYANO_TIMING_FLOOR = 0.25  # empirically-grounded lower bound (Hayano timing)


def _hayano_t4_blend(agents: pd.DataFrame) -> float:
    blend = agents[agents["decision_mode"] == "blend"]
    im = blend[blend["initial_zone"].isin(["inner", "mid"])][
        "agent_id"].unique()
    if not len(im):
        return 0.0
    camp = blend[(blend["agent_id"].isin(im)) & (blend["zone"] == "camp")]
    first = camp.groupby("agent_id")["timestep"].min()
    return float((first <= 4).sum() / len(im))


def _run_member_with_cmc(input_dir: Path, conflict_file: str,
                         n_agents: int, n_steps: int,
                         alpha: float, beta: float, kappa: float,
                         cmc: float, seed: int):
    """Run one blend member with ConflictMoveChance overridden to ``cmc``."""
    # Use the d5 _run_member, then override CMC right before the simulation
    # starts. Easiest: monkey-patch d3.load_config to apply our cmc.
    orig_load = d3.load_config

    def patched(input_dir_str):
        orig_load(input_dir_str)
        SimulationSettings.move_rules["ConflictMoveChance"] = cmc

    d3.load_config = patched
    try:
        adf, _lm, arr = d5._run_member(
            input_dir, conflict_file, "blend",
            n_agents, n_steps,
            alpha, beta, kappa, seed, "beta",
        )
    finally:
        d3.load_config = orig_load
    return adf, arr


def _linear_interp_target(means: np.ndarray, cmc: np.ndarray,
                          target: float) -> float | None:
    """Return interpolated cmc where hayano_t4 == target, or None if out of range."""
    if target <= float(means.min()) or target >= float(means.max()):
        # Try monotone extrapolation if target above range
        if target > float(means.max()) and means[-1] >= means[-2]:
            slope = (means[-1] - means[-2]) / (cmc[-1] - cmc[-2])
            if slope > 1e-6:
                return float(cmc[-1] + (target - means[-1]) / slope)
        return None
    for i in range(len(cmc) - 1):
        if (means[i] - target) * (means[i + 1] - target) <= 0:
            x0, x1 = cmc[i], cmc[i + 1]
            y0, y1 = means[i], means[i + 1]
            if abs(y1 - y0) < 1e-9:
                return float(x0)
            return float(x0 + (target - y0) * (x1 - x0) / (y1 - y0))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-agents", type=int, default=500)
    ap.add_argument("--n-steps",  type=int, default=72)
    ap.add_argument("--ensemble", type=int, default=5)
    ap.add_argument("--seed",     type=int, default=20260406)
    ap.add_argument("--alpha",    type=float, default=1.0)
    ap.add_argument("--beta",     type=float, default=2.0)
    ap.add_argument("--kappa",    type=float, default=5.0)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    if args.quick:
        args.n_agents = 200
        args.ensemble = 2
        cmc_grid = CMC_GRID_QUICK
        print(f"[quick] n_agents={args.n_agents}, ensemble={args.ensemble}, "
              f"cmc-grid={cmc_grid}")
    else:
        cmc_grid = CMC_GRID_FULL

    spec = d5.scenario_specs(REPO)["baseline"]
    print(f"[Day 6 §4] cmc sweep on baseline scenario, "
          f"input={spec['input_dir'].name}")

    rows = []
    for ci, cmc in enumerate(cmc_grid):
        for m in range(args.ensemble):
            seed = args.seed + 100 * ci + m
            print(f"  -> cmc={cmc:.2f}, member={m} (seed={seed})")
            adf, arr = _run_member_with_cmc(
                spec["input_dir"], spec["conflict_file"],
                args.n_agents, args.n_steps,
                args.alpha, args.beta, args.kappa,
                cmc, seed,
            )
            h4 = _hayano_t4_blend(adf)
            rows.append({"cmc": cmc, "member": m, "seed": seed,
                         "hayano_t4": round(h4, 4)})

    df = pd.DataFrame(rows)
    RES_D6.mkdir(parents=True, exist_ok=True)
    csv_path = RES_D6 / "movechance_sweep.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n  wrote {csv_path}")

    summary = df.groupby("cmc")["hayano_t4"].agg(["mean", "std"]).reset_index()
    print("\n=== cmc sweep summary ===")
    print(summary.to_string(index=False, float_format=lambda v: f"{v:7.4f}"))

    cmcs = summary["cmc"].values.astype(float)
    means = summary["mean"].values.astype(float)
    stds = summary["std"].values.astype(float)
    target_cmc = _linear_interp_target(means, cmcs, HAYANO_TARGET)

    finding = {
        "hayano_target": HAYANO_TARGET,
        "cmc_grid": [float(c) for c in cmcs],
        "hayano_means": [float(m) for m in means],
        "hayano_stds": [float(s) for s in stds],
        "conflict_movechance_target": target_cmc,
        "in_physically_plausible_range":
            bool(target_cmc is not None and 0.25 <= target_cmc <= 0.75),
    }
    if target_cmc is None:
        finding["note"] = (
            "Could not interpolate cmc that yields hayano_t4=0.78 — target "
            "may be outside the swept range. Hayano timing-vs-level "
            "tension flagged; may require two-stage treatment in Day 8."
        )
    elif target_cmc > 0.65:
        finding["note"] = (
            f"Interpolated cmc target {target_cmc:.3f} exceeds 0.65, the "
            "soft upper bound. Possible tension between Hayano timing "
            "(per-step rate ~0.5) and Hayano level (78% by t=4); consider "
            "two-stage Day 8 calibration."
        )
    elif target_cmc < HAYANO_TIMING_FLOOR:
        finding["note"] = (
            f"Interpolated cmc target {target_cmc:.3f} is below the "
            f"empirical Hayano floor of {HAYANO_TIMING_FLOOR}; level can "
            "be matched but timing constraint will be violated."
        )
    else:
        finding["note"] = "Target within nominal physical range."

    out = RES_D6 / "physical_param_target.json"
    out.write_text(json.dumps(finding, indent=2))
    print(f"\n  wrote {out}")
    print(f"  conflict_movechance_target = "
          f"{target_cmc if target_cmc is not None else 'N/A'}")
    print(f"  → {finding['note']}")

    _fig_d6_3(cmcs, means, stds, target_cmc, FIG_D6)
    return 0


def _fig_d6_3(cmcs, means, stds, target_cmc, out_dir: Path) -> None:
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8,
        "axes.titlesize": 9, "axes.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.5, "figure.dpi": 150,
    })
    fig, ax = plt.subplots(figsize=(7.0, 4.2))

    ax.errorbar(cmcs, means, yerr=stds, fmt="o-",
                color="#1D9E75", lw=1.4, ms=6, capsize=3,
                label="hayano_t4 (mean ±1σ across members)")
    ax.axhline(HAYANO_TARGET, color="#C0392B", ls="--", lw=1.0,
               label=f"Hayano target = {HAYANO_TARGET}")
    ax.axhline(0.5, color="gray", ls=":", lw=0.8,
               label="Day 3 default cmc=0.5 (current)")
    ax.axhspan(HAYANO_TIMING_FLOOR, 0.65, color="#16A085",
               alpha=0.05, zorder=0,
               label="physically plausible cmc range")

    if target_cmc is not None:
        ax.axvline(target_cmc, color="#9B59B6", ls="-.", lw=1.0,
                   alpha=0.8,
                   label=f"interp cmc → 0.78 = {target_cmc:.3f}")
        ax.scatter([target_cmc], [HAYANO_TARGET],
                   marker="*", s=120, color="#9B59B6", zorder=5,
                   edgecolor="white", linewidth=0.8)

    ax.set_xlabel("ConflictMoveChance")
    ax.set_ylabel("Inner+mid blend departures by t=4 (hayano_t4)")
    ax.set_xlim(min(cmcs) - 0.05, max(cmcs) + 0.05)
    ax.set_ylim(0, 1.0)
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=7, loc="lower right")
    ax.set_title("Day 6 §4 — conflict_movechance vs Hayano-target hayano_t4 "
                 "(reconnaissance for Day 8)", fontsize=9)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "D6-3_movechance_target.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


if __name__ == "__main__":
    sys.exit(main())
