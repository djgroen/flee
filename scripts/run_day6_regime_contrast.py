#!/usr/bin/env python3
"""
Day 6 Section 3 — Information regime contrast.

Regime A = continuous gradient (the post-Day-4b default).
Regime B = official zone discretization: c_best is rounded to the
           administrative zone of the destination node where the BFS
           optimum was found ({inner: 0.9, mid: 0.5, outer: 0.1}). The
           zone of each node is read from locations.csv coordinates by
           great-circle distance from Daiichi (NOT hard-coded).

Both regimes use route6_closed at α=1.0, β=2.0, κ=5.0, all four modes,
with 10 ensemble members. Records the same QoIs as §2 plus corridor
usage, and produces Fig D6-2: side-by-side corridor stacks under A vs B.

The scientific question is whether the System-1/System-2 inland-route shift survives
when within-zone gradients are flattened. If Δ shrinks under B that means
official zoning obscures the gradient that drives deliberative routing —
a policy-relevant finding.
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
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import run_day5_scenarios as d5  # noqa: E402
from scripts import run_fukushima_day3 as d3  # noqa: E402
from flee.SimulationSettings import SimulationSettings  # noqa: E402
from flee.conflict_potential import (  # noqa: E402
    ConflictPotentialField,
    _read_conflict_grid_csv,
    read_zone_map_from_locations,
)

RES_D6 = REPO / "results" / "day6"
FIG_D6 = REPO / "figures" / "fukushima" / "day6"

CAT_COLORS = {"route6": "#C0392B", "inland": "#16A085",
              "both": "#9B59B6", "neither": "#BDC3C7"}
PALETTE = {"original": "#888780", "sys1_only": "#888780",
           "switch": "#BA7517", "blend": "#1D9E75"}
MODES = ["original", "sys1_only", "switch", "blend"]
FORK_ORIGINS = {"tomioka", "okuma", "futaba", "namie", "naraha"}
ROUTE6_NODES = {"naraha", "hirono"}
INLAND_NODES = {"kawauchi"}


def _classify_corridor(agents: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, sub in agents.groupby(
            ["regime", "member", "decision_mode", "agent_id"], sort=False):
        if sub["initial_zone"].iloc[0] not in ("inner", "mid"):
            continue
        path = sub.sort_values("timestep")["location"].tolist()
        used_r6 = any(p in ROUTE6_NODES for p in path)
        used_inl = any(p in INLAND_NODES for p in path)
        if used_r6 and used_inl:
            cat = "both"
        elif used_r6:
            cat = "route6"
        elif used_inl:
            cat = "inland"
        else:
            cat = "neither"
        origin = sub.sort_values("timestep")["location"].iloc[0]
        rows.append({"regime": keys[0], "member": keys[1],
                     "decision_mode": keys[2], "agent_id": keys[3],
                     "origin_town": origin, "corridor": cat})
    return pd.DataFrame(rows)


def _qois(agents: pd.DataFrame, arrivals: pd.DataFrame, regime: str) -> dict:
    blend = agents[(agents["regime"] == regime)
                   & (agents["decision_mode"] == "blend")]
    out: dict = {"regime": regime}

    im = blend[blend["initial_zone"].isin(["inner", "mid"])][
        "agent_id"].unique()
    if len(im):
        c = blend[(blend["agent_id"].isin(im)) & (blend["zone"] == "camp")]
        first = c.groupby(["member", "agent_id"])["timestep"].min()
        per = []
        for m in blend["member"].unique():
            m_im = blend[(blend["member"] == m)
                         & (blend["initial_zone"].isin(["inner", "mid"]))][
                "agent_id"].unique()
            if not len(m_im):
                continue
            try:
                mf = first.xs(m, level="member")
            except KeyError:
                mf = pd.Series([], dtype=int)
            per.append((mf <= 4).sum() / len(m_im))
        out["hayano_t4"] = float(np.mean(per)) if per else 0.0

    inner = blend[blend["initial_zone"] == "inner"]["agent_id"].unique()
    if len(inner):
        c = blend[(blend["agent_id"].isin(inner)) & (blend["zone"] == "camp")]
        first = c.groupby(["member", "agent_id"])["timestep"].min()
        per = []
        for m in blend["member"].unique():
            m_in = blend[(blend["member"] == m)
                         & (blend["initial_zone"] == "inner")][
                "agent_id"].unique()
            if not len(m_in):
                continue
            try:
                mf = first.xs(m, level="member")
            except KeyError:
                mf = pd.Series([], dtype=int)
            per.append((mf <= 7).sum() / len(m_in))
        out["blend_inner_t7"] = float(np.mean(per)) if per else 0.0

    mid = set(d3.ZONES["mid"])
    mid_active = blend[blend["location"].isin(mid)]
    if not mid_active.empty:
        by_t = mid_active.groupby("timestep")["sys2_weight"].mean()
        out["mid_ps2_trough"] = float(by_t.min())

    if not arrivals.empty:
        bl = arrivals[(arrivals["regime"] == regime)
                      & (arrivals["decision_mode"] == "blend")]
        if len(bl):
            out["mean_path_length"] = float(bl["path_length_km"].mean())
    return out


def _run_member(input_dir: Path, conflict_file: str, mode: str, regime: str,
                n_agents: int, n_steps: int,
                alpha: float, beta: float, kappa: float, seed: int,
                zone_of: dict):
    """Re-implement d5._run_member, but inject a zone-aware potential field."""
    import random
    import numpy as np
    from flee import flee, InputGeography
    from flee.decision_engine import DecisionEngine

    d3.load_config(str(input_dir))
    SimulationSettings.ConflictInputFile = str(input_dir / conflict_file)
    SimulationSettings.move_rules["TwoSystemDecisionMaking"] = True
    SimulationSettings.move_rules["decision_mode"] = mode
    SimulationSettings.move_rules["s1s2_model_params"] = {
        "alpha": alpha, "beta": beta, "kappa": kappa,
    }
    SimulationSettings.move_rules["decision_engine"] = DecisionEngine.create(
        mode,
        {"s1s2_model_params": SimulationSettings.move_rules["s1s2_model_params"]},
    )
    SimulationSettings.move_rules["sys2_weight_override"] = None

    random.seed(seed)
    np.random.seed(seed)
    e = flee.Ecosystem()
    ig = InputGeography.InputGeography()
    ig.ReadLocationsFromCSV(str(input_dir / "locations.csv"))
    ig.ReadLinksFromCSV(str(input_dir / "routes.csv"))
    ig.ReadClosuresFromCSV(str(input_dir / "closures.csv"))
    if Path(SimulationSettings.ConflictInputFile).exists():
        ig.ReadConflictInputCSV(SimulationSettings.ConflictInputFile)
    e, lm = ig.StoreInputGeographyInEcosystem(e)

    zones, grid = _read_conflict_grid_csv(str(input_dir / conflict_file))
    awareness_s1 = int(SimulationSettings.move_rules.get("AwarenessLevel", 1))
    field = ConflictPotentialField.build(
        conflict_grid=grid, zones=zones,
        routes_path=str(input_dir / "routes.csv"),
        num_days=max(n_steps + 1, len(grid)),
        awareness_s1=awareness_s1,
        zone_of=zone_of,
    )
    field.discretize_default = (regime == "B")
    SimulationSettings.move_rules["potential_field"] = field
    print(f"  [potential_field] regime={regime}, "
          f"discretize_default={field.discretize_default}, "
          f"zone_of_size={len(field.zone_of)}")

    agents_added = d3.distribute_agents_by_pop(e, lm, n_agents, seed)

    initial_zone = {}
    for aid, a in enumerate(e.agents):
        loc = a.location
        ep = getattr(loc, "endpoint", loc)
        loc_name = getattr(ep, "name", str(loc))
        initial_zone[aid] = d3.loc_to_zone(loc_name)

    agents_data = []
    arrival_records = []
    arrived_at_camp = set()

    for t in range(n_steps + 1):
        if t > 0:
            ig.AddNewConflictZones(e, t)
            if hasattr(ig, "conflicts"):
                for cname, cvals in ig.conflicts.items():
                    if t < len(cvals):
                        cur, prev = cvals[t], cvals[t - 1]
                        if prev > 1e-6 and cur > 1e-6 and abs(cur - prev) > 1e-6:
                            e.set_conflict_intensity(cname, cur)
        e.evolve()
        for aid, a in enumerate(e.agents):
            loc = a.location
            if loc is None:
                continue
            ep = getattr(loc, "endpoint", loc)
            name = getattr(ep, "name", str(loc))
            zone = d3.loc_to_zone(name)
            s2 = getattr(a, "sys2_activation_prob", 0.0)
            if zone == "camp" and aid not in arrived_at_camp:
                arrived_at_camp.add(aid)
                arrival_records.append({
                    "agent_id": aid,
                    "initial_zone": initial_zone.get(aid, "unknown"),
                    "arrival_timestep": t,
                    "path_length_km": float(getattr(a, "distance_travelled", 0.0)),
                    "decision_mode": mode,
                })
            agents_data.append({
                "timestep": t, "agent_id": aid, "location": name,
                "zone": zone,
                "initial_zone": initial_zone.get(aid, zone),
                "sys2_weight": s2,
                "decision_mode": mode,
            })

    return pd.DataFrame(agents_data), pd.DataFrame(arrival_records)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-agents", type=int, default=500)
    ap.add_argument("--n-steps",  type=int, default=72)
    ap.add_argument("--ensemble", type=int, default=10)
    ap.add_argument("--seed",     type=int, default=20260306)
    ap.add_argument("--alpha",    type=float, default=1.0)
    ap.add_argument("--beta",     type=float, default=2.0)
    ap.add_argument("--kappa",    type=float, default=5.0)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    if args.quick:
        args.n_agents = 200
        args.ensemble = 2
        print(f"[quick] n_agents={args.n_agents}, ensemble={args.ensemble}")

    spec = d5.scenario_specs(REPO)["route6_closed"]
    input_dir = spec["input_dir"]
    conflict_file = spec["conflict_file"]
    zone_of = read_zone_map_from_locations(str(input_dir / "locations.csv"))

    print(f"[Day 6 §3] regime contrast on {input_dir.name}/{conflict_file}")
    print(f"  derived zone map (from locations.csv coordinates):")
    for z in ("inner", "mid", "outer"):
        names = sorted(n for n, zz in zone_of.items() if zz == z)
        print(f"    {z}: {', '.join(names)}")

    all_agents = []
    all_arr = []
    for regime in ("A", "B"):
        for mi, mode in enumerate(MODES):
            for k in range(args.ensemble):
                seed = args.seed + 1000 * mi + 10000 * (1 if regime == "B" else 0) + k
                print(f"  -> regime={regime}, mode={mode}, member={k} "
                      f"(seed={seed})")
                adf, arr = _run_member(
                    input_dir, conflict_file, mode, regime,
                    args.n_agents, args.n_steps,
                    args.alpha, args.beta, args.kappa,
                    seed, zone_of,
                )
                adf["regime"] = regime
                adf["member"] = k
                arr["regime"] = regime
                arr["member"] = k
                all_agents.append(adf)
                all_arr.append(arr)

    agents = pd.concat(all_agents, ignore_index=True)
    arrivals = (pd.concat(all_arr, ignore_index=True)
                if all_arr else pd.DataFrame())

    RES_D6.mkdir(parents=True, exist_ok=True)
    agents.to_csv(RES_D6 / "regime_contrast_agents.csv", index=False)
    if not arrivals.empty:
        arrivals.to_csv(RES_D6 / "regime_contrast_arrivals.csv", index=False)
    print(f"\n  agents: {len(agents)} rows  arrivals: {len(arrivals)} rows")

    print("\nClassifying corridor usage...")
    corridor = _classify_corridor(agents)
    corridor.to_csv(RES_D6 / "regime_contrast_corridor.csv", index=False)

    qoi_rows = []
    for regime in ("A", "B"):
        rec = _qois(agents, arrivals, regime)
        qoi_rows.append(rec)
    qois_df = pd.DataFrame(qoi_rows)
    qois_df.to_csv(RES_D6 / "regime_contrast_qois.csv", index=False)
    print("\n=== Regime contrast QoIs ===")
    print(qois_df.to_string(index=False, float_format=lambda v: f"{v:7.4f}"))

    chi_results = {}
    for regime in ("A", "B"):
        sub = corridor[(corridor["regime"] == regime)
                       & (corridor["decision_mode"].isin(["sys1_only", "blend"]))
                       & (corridor["corridor"].isin(["route6", "inland"]))]
        if sub.empty:
            continue
        ct = pd.crosstab(sub["decision_mode"], sub["corridor"])
        for c in ["route6", "inland"]:
            if c not in ct.columns:
                ct[c] = 0
        ct = ct[["route6", "inland"]]
        chi2, p, _, _ = stats.chi2_contingency(ct.values)
        bl_in = (ct.loc["blend", "inland"] / max(1, ct.loc["blend"].sum())) * 100
        s1_in = (ct.loc["sys1_only", "inland"] / max(1, ct.loc["sys1_only"].sum())) * 100
        chi_results[regime] = {
            "blend_inland_pct": float(bl_in),
            "s1_inland_pct": float(s1_in),
            "shift_pp": float(bl_in - s1_in),
            "chi2": float(chi2), "p": float(p),
        }
        print(f"\n  Regime {regime}: blend_inland={bl_in:.1f}%, "
              f"s1_inland={s1_in:.1f}%, Δ={bl_in - s1_in:+.2f}pp, "
              f"χ²={chi2:.3f}, p={p:.4g}")

    (RES_D6 / "regime_contrast_chi2.json").write_text(
        json.dumps(chi_results, indent=2))

    _fig_d6_2(corridor, FIG_D6)
    return 0


def _fig_d6_2(corridor: pd.DataFrame, out_dir: Path) -> None:
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8,
        "axes.titlesize": 9, "axes.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.5, "figure.dpi": 150,
    })
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), sharey=True)
    cats = ["route6", "inland", "both", "neither"]
    for ax, regime in zip(axes, ("A", "B")):
        sub = corridor[corridor["regime"] == regime]
        counts = (sub.groupby(["decision_mode", "corridor"]).size()
                  .unstack(fill_value=0)
                  .reindex(MODES)
                  .reindex(columns=cats, fill_value=0))
        fracs = counts.div(counts.sum(axis=1), axis=0).fillna(0.0)
        bottoms = np.zeros(len(MODES))
        x = np.arange(len(MODES))
        for cat in cats:
            vals = fracs[cat].values
            ax.bar(x, vals, bottom=bottoms, width=0.6,
                   color=CAT_COLORS[cat], edgecolor="white", linewidth=0.5,
                   label=cat if regime == "A" else None)
            for xi, v, b in zip(x, vals, bottoms):
                if v > 0.05:
                    ax.text(xi, b + v / 2, f"{v*100:.0f}",
                            ha="center", va="center",
                            fontsize=7, color="white", fontweight="bold")
            bottoms += vals
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace("_", " ") for m in MODES],
                           fontsize=7, rotation=15)
        title = ("Regime A — continuous gradient"
                 if regime == "A"
                 else "Regime B — official zone discretization")
        ax.set_title(title, fontsize=9)
        ax.set_ylim(0, 1.0)
        ax.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Fraction of fork-origin agents")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right",
               fontsize=7, bbox_to_anchor=(0.998, 0.97))
    fig.suptitle("Day 6 §3 — corridor usage by mode under "
                 "continuous (A) vs zone-discretized (B) information regimes",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "D6-2_regime_contrast.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


if __name__ == "__main__":
    sys.exit(main())
