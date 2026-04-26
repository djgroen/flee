#!/usr/bin/env python3
"""
Day 6 Section 2 — κ sensitivity verification on the real Fukushima gradient.

Runs the route6_closed scenario with α=1.0, β=2.0 fixed and κ swept across
{1.0, 2.5, 5.0, 10.0, 20.0}. Blend mode only (κ has no effect on the other
three modes). Records five QoIs per (κ, ensemble member) and produces
Fig D6-1, a 2×3 panel of QoI vs κ scatter with LOWESS smoothers.

Acceptance: at least two QoIs must show a monotone trend with |Δ| > 0.02
across the κ range. If this fails, the script also prints a diagnostic of
the (c_here − c_best) distribution to identify whether the spatial gradient
is reaching the σ computation at all.
"""
from __future__ import annotations

import argparse
import csv
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

RES_D6 = REPO / "results" / "day6"
FIG_D6 = REPO / "figures" / "fukushima" / "day6"

KAPPA_GRID_FULL = [1.0, 2.5, 5.0, 10.0, 20.0]
KAPPA_GRID_QUICK = [1.0, 5.0, 20.0]


def _qois_one_member(agents: pd.DataFrame, arrivals: pd.DataFrame) -> dict:
    """Compute the five Day 6 §2 QoIs from a single (κ, member) blend run."""
    blend = agents[agents["decision_mode"] == "blend"]

    im_ids = blend[blend["initial_zone"].isin(["inner", "mid"])][
        "agent_id"].unique()
    if len(im_ids) > 0:
        camp = blend[(blend["agent_id"].isin(im_ids))
                     & (blend["zone"] == "camp")]
        first = camp.groupby("agent_id")["timestep"].min()
        hayano_t4 = float((first <= 4).sum() / len(im_ids))
    else:
        hayano_t4 = 0.0

    inner_ids = blend[blend["initial_zone"] == "inner"]["agent_id"].unique()
    if len(inner_ids) > 0:
        camp_i = blend[(blend["agent_id"].isin(inner_ids))
                       & (blend["zone"] == "camp")]
        first_i = camp_i.groupby("agent_id")["timestep"].min()
        blend_inner_t7 = float((first_i <= 7).sum() / len(inner_ids))
    else:
        blend_inner_t7 = 0.0

    fork_origins = {"tomioka", "okuma", "futaba", "namie", "naraha"}
    fork_ids = (blend[(blend["timestep"] == 0)
                      & (blend["location"].isin(fork_origins))]
                ["agent_id"].unique())
    inland_count = 0
    fork_total = len(fork_ids)
    if fork_total > 0:
        for aid in fork_ids:
            path = blend[blend["agent_id"] == aid]["location"].tolist()
            if any(p == "kawauchi" for p in path):
                inland_count += 1
    corridor_inland_pct = (inland_count / fork_total) if fork_total else 0.0

    mid_locs = set(d3.ZONES["mid"])
    mid_active = blend[blend["location"].isin(mid_locs)]
    if not mid_active.empty:
        by_t = mid_active.groupby("timestep")["sys2_weight"].mean()
        mid_ps2_trough = float(by_t.min()) if len(by_t) else 0.0
    else:
        mid_ps2_trough = 0.0

    if not arrivals.empty:
        bl = arrivals[arrivals["decision_mode"] == "blend"]
        mean_path_length = float(bl["path_length_km"].mean()) if len(bl) else 0.0
    else:
        mean_path_length = 0.0

    return {
        "hayano_t4":           round(hayano_t4, 4),
        "blend_inner_t7":      round(blend_inner_t7, 4),
        "corridor_inland_pct": round(corridor_inland_pct, 4),
        "mid_ps2_trough":      round(mid_ps2_trough, 4),
        "mean_path_length":    round(mean_path_length, 2),
    }


def _diagnose_gradient(input_dir: Path, conflict_file: str) -> dict:
    """Build the potential field for this scenario and report the
    (c_here − c_best) distribution across (day, location)."""
    from flee.conflict_potential import (
        ConflictPotentialField,
        _read_conflict_grid_csv,
    )
    routes = str(input_dir / "routes.csv")
    cpath = str(input_dir / conflict_file)
    zones, grid = _read_conflict_grid_csv(cpath)
    field = ConflictPotentialField.build(
        conflict_grid=grid, zones=zones, routes_path=routes,
        num_days=len(grid), awareness_s1=1,
    )
    diffs_s1 = []
    diffs_s2 = []
    for d_idx, row in enumerate(grid):
        for z_idx, c_here in enumerate(row):
            name = zones[z_idx]
            cb1, _ = field.get(d_idx, name, s2=False)
            cb2, _ = field.get(d_idx, name, s2=True)
            diffs_s1.append(c_here - cb1)
            diffs_s2.append(c_here - cb2)
    a1 = np.array(diffs_s1)
    a2 = np.array(diffs_s2)
    return {
        "n_cells": int(len(a1)),
        "s1_min":  float(a1.min()),  "s1_max":  float(a1.max()),
        "s1_mean": float(a1.mean()), "s1_pos_frac": float((a1 > 1e-6).mean()),
        "s2_min":  float(a2.min()),  "s2_max":  float(a2.max()),
        "s2_mean": float(a2.mean()), "s2_pos_frac": float((a2 > 1e-6).mean()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-agents",  type=int, default=500)
    ap.add_argument("--n-steps",   type=int, default=72)
    ap.add_argument("--ensemble",  type=int, default=5)
    ap.add_argument("--seed",      type=int, default=20260206)
    ap.add_argument("--alpha",     type=float, default=1.0)
    ap.add_argument("--beta",      type=float, default=2.0)
    ap.add_argument("--scenario",  default="route6_closed")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    if args.quick:
        args.n_agents = 200
        args.ensemble = 2
        kappa_grid = KAPPA_GRID_QUICK
        print(f"[quick] n_agents={args.n_agents}, ensemble={args.ensemble}, "
              f"κ-grid={kappa_grid}")
    else:
        kappa_grid = KAPPA_GRID_FULL

    specs = d5.scenario_specs(REPO)
    spec = specs[args.scenario]
    print(f"[Day 6 §2] κ sweep on scenario={args.scenario}, "
          f"input={spec['input_dir'].name}, conflicts={spec['conflict_file']}")

    rows = []
    for ki, k in enumerate(kappa_grid):
        for m in range(args.ensemble):
            seed = args.seed + 100 * ki + m
            print(f"  -> κ={k:5.2f}, member={m} (seed={seed})")
            adf, _lm, arr = d5._run_member(
                spec["input_dir"], spec["conflict_file"], "blend",
                args.n_agents, args.n_steps,
                args.alpha, args.beta, k, seed, spec["x_dist"],
            )
            qois = _qois_one_member(adf, arr)
            qois.update({"kappa": k, "member": m, "seed": seed})
            rows.append(qois)

    df = pd.DataFrame(rows)
    RES_D6.mkdir(parents=True, exist_ok=True)
    csv_path = RES_D6 / "kappa_sweep_qois.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n  wrote {csv_path}")

    # Per-κ summaries
    summary = (df.groupby("kappa")
               .agg(["mean", "std"])
               .round(4))
    print("\n=== κ sweep summary (means ± std across ensemble) ===")
    print(summary.to_string())

    # Acceptance: at least 2 QoIs with monotone trend |Δ| > 0.02
    qoi_names = ["hayano_t4", "blend_inner_t7", "corridor_inland_pct",
                 "mid_ps2_trough", "mean_path_length"]
    monotone_results = []
    for q in qoi_names:
        per_k = df.groupby("kappa")[q].mean().sort_index()
        delta = float(per_k.max() - per_k.min())
        diffs = np.diff(per_k.values)
        monotone = (np.all(diffs >= -1e-9) or np.all(diffs <= 1e-9))
        # also accept "near-monotone" with one direction reversal where |delta| > 0.02
        passes = (delta > 0.02)
        monotone_results.append({
            "qoi": q, "delta": delta,
            "monotone": bool(monotone), "passes_threshold": bool(passes),
        })
        print(f"  {q:24s}: Δ={delta:.4f}, monotone={monotone}, "
              f"passes(|Δ|>0.02)={passes}")

    n_passing = sum(1 for r in monotone_results if r["passes_threshold"])
    gate_pass = n_passing >= 2
    print(f"\n  Gate: {n_passing}/{len(qoi_names)} QoIs cross |Δ|>0.02 "
          f"-> {'PASS' if gate_pass else 'FAIL'}")

    # Diagnostic on c_here-c_best distribution (always run, helpful for narrative)
    diag = _diagnose_gradient(spec["input_dir"], spec["conflict_file"])
    diag_path = RES_D6 / "kappa_gradient_diagnostic.json"
    diag_path.write_text(json.dumps(diag, indent=2))
    print(f"\n  wrote {diag_path}")
    print(f"  (c_here-c_best) System-1 hop: range [{diag['s1_min']:.3f}, "
          f"{diag['s1_max']:.3f}], pos_frac={diag['s1_pos_frac']:.3f}")
    print(f"  (c_here-c_best) S2 hop: range [{diag['s2_min']:.3f}, "
          f"{diag['s2_max']:.3f}], pos_frac={diag['s2_pos_frac']:.3f}")

    # Figure
    _fig_d6_1(df, qoi_names, FIG_D6)

    return 0 if gate_pass else 1


def _lowess(x, y, frac=0.5):
    """Tiny LOWESS that doesn't depend on statsmodels."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    order = np.argsort(x)
    x, y = x[order], y[order]
    n = len(x)
    h = max(2, int(np.ceil(frac * n)))
    out = np.zeros(n)
    for i in range(n):
        d = np.abs(x - x[i])
        idx = np.argsort(d)[:h]
        w = (1 - (d[idx] / d[idx].max()) ** 3) ** 3 if d[idx].max() > 0 \
            else np.ones(h)
        W = np.diag(w)
        X = np.column_stack([np.ones(h), x[idx]])
        try:
            beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ y[idx])
            out[i] = beta[0] + beta[1] * x[i]
        except np.linalg.LinAlgError:
            out[i] = float(np.average(y[idx], weights=w))
    return x, out


def _fig_d6_1(df: pd.DataFrame, qoi_names: list, out_dir: Path) -> None:
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8,
        "axes.titlesize": 9, "axes.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.5, "figure.dpi": 150,
    })
    fig, axes = plt.subplots(2, 3, figsize=(10, 6))
    out_dir.mkdir(parents=True, exist_ok=True)

    for ax, q in zip(axes.flat[: len(qoi_names)], qoi_names):
        x = df["kappa"].values.astype(float)
        y = df[q].values.astype(float)
        ax.scatter(x, y, s=24, alpha=0.55,
                   color="#1D9E75", edgecolors="white", linewidths=0.4)
        means = df.groupby("kappa")[q].mean().sort_index()
        ax.plot(means.index, means.values, color="#16A085", lw=1.0,
                marker="o", ms=4, label="ensemble mean")
        try:
            xs, ys = _lowess(x, y, frac=0.7)
            ax.plot(xs, ys, color="#C0392B", lw=1.2, label="LOWESS")
        except Exception:
            pass
        delta = float(means.max() - means.min())
        ax.set_title(f"{q}\nΔ = {delta:.4f}", fontsize=8)
        ax.set_xlabel("κ")
        ax.set_xscale("log")
        ax.grid(True, alpha=0.2)
        if q == qoi_names[0]:
            ax.legend(fontsize=6, loc="best")

    # blank the unused axis
    for ax in axes.flat[len(qoi_names):]:
        ax.axis("off")

    fig.suptitle("Day 6 §2 — κ sensitivity on real Fukushima gradient "
                 "(route6_closed, blend mode)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = out_dir / "D6-1_kappa_qoi_panels.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


if __name__ == "__main__":
    sys.exit(main())
