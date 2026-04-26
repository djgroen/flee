#!/usr/bin/env python3
"""
Day 6 Section 1 — origin-disaggregated corridor analysis (Day 5 carryover).

Loads results/day5/{corridor_usage,agents_all_scenarios}.csv and breaks the
route6_closed corridor table down by origin town: tomioka alone,
okuma+futaba combined, namie alone, and the full Day 5 aggregate.

Reports a chi-square test for the Tomioka-fork group (tomioka + okuma + futaba)
between sys1_only and blend, separately from the aggregate.

No new simulations are required.
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
RES_D5 = REPO / "results" / "day5"
RES_D6 = REPO / "results" / "day6"
FIG_D6 = REPO / "figures" / "fukushima" / "day6"

ORIGIN_GROUPS = {
    "tomioka":          ["tomioka"],
    "okuma+futaba":     ["okuma", "futaba"],
    "namie":            ["namie"],
    "all_fork_origins": ["tomioka", "okuma", "futaba", "namie", "naraha"],
}
GROUP_ORDER = ["tomioka", "okuma+futaba", "namie", "all_fork_origins"]
MODES = ["original", "sys1_only", "switch", "blend"]
PALETTE = {"original": "#888780", "sys1_only": "#888780",
           "switch": "#BA7517", "blend": "#1D9E75"}
MODE_HATCH = {"original": "", "sys1_only": "//",
              "switch": "", "blend": ""}
CAT_COLORS = {"route6": "#C0392B", "inland": "#16A085",
              "both": "#9B59B6", "neither": "#BDC3C7"}


def _build_origin_table(corridor: pd.DataFrame,
                        agents: pd.DataFrame) -> pd.DataFrame:
    """Attach 'origin_town' (location at timestep 0) to each corridor row."""
    t0 = (agents[agents["timestep"] == 0]
          [["scenario", "member", "decision_mode", "agent_id", "location"]]
          .rename(columns={"location": "origin_town"}))
    merged = corridor.merge(
        t0,
        on=["scenario", "member", "decision_mode", "agent_id"],
        how="left",
    )
    return merged


def _summarize(merged: pd.DataFrame, scenario: str) -> pd.DataFrame:
    """Per (origin_group, mode) corridor fractions and N agents."""
    sub = merged[merged["scenario"] == scenario].copy()
    rows = []
    for grp in GROUP_ORDER:
        towns = ORIGIN_GROUPS[grp]
        gsub = sub[sub["origin_town"].isin(towns)]
        for mode in MODES:
            mdf = gsub[gsub["decision_mode"] == mode]
            n = len(mdf)
            r6 = (mdf["corridor"] == "route6").sum()
            inl = (mdf["corridor"] == "inland").sum()
            both = (mdf["corridor"] == "both").sum()
            nei = (mdf["corridor"] == "neither").sum()
            rows.append({
                "origin_group": grp, "mode": mode,
                "n_agents": n,
                "route6_pct":  100.0 * r6 / n if n else 0.0,
                "inland_pct":  100.0 * inl / n if n else 0.0,
                "both_pct":    100.0 * both / n if n else 0.0,
                "neither_pct": 100.0 * nei / n if n else 0.0,
            })
    return pd.DataFrame(rows)


def _chi2_for_group(merged: pd.DataFrame, scenario: str,
                    group: str) -> dict:
    """Chi-square sys1_only vs blend on {Route 6, inland} for the given group."""
    towns = ORIGIN_GROUPS[group]
    sub = merged[(merged["scenario"] == scenario)
                 & (merged["origin_town"].isin(towns))
                 & (merged["decision_mode"].isin(["sys1_only", "blend"]))
                 & (merged["corridor"].isin(["route6", "inland"]))]
    if sub.empty:
        return {"group": group, "n_s1": 0, "n_blend": 0,
                "chi2": float("nan"), "p": float("nan"),
                "blend_inland_pct": 0.0, "s1_inland_pct": 0.0,
                "shift_pp": 0.0}
    ct = pd.crosstab(sub["decision_mode"], sub["corridor"])
    for c in ["route6", "inland"]:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[["route6", "inland"]]
    try:
        chi2, p, _, _ = stats.chi2_contingency(ct.values)
    except ValueError:
        chi2, p = float("nan"), float("nan")
    blend_il = (ct.loc["blend", "inland"]
                / max(1, ct.loc["blend"].sum())) * 100
    s1_il = (ct.loc["sys1_only", "inland"]
             / max(1, ct.loc["sys1_only"].sum())) * 100
    return {
        "group": group,
        "n_s1": int(ct.loc["sys1_only"].sum()),
        "n_blend": int(ct.loc["blend"].sum()),
        "chi2": float(chi2),
        "p": float(p),
        "blend_inland_pct": float(blend_il),
        "s1_inland_pct": float(s1_il),
        "shift_pp": float(blend_il - s1_il),
    }


def _fig_d6_0(table: pd.DataFrame, out_dir: Path) -> None:
    """Grouped bar chart: corridor usage by origin group and mode."""
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8,
        "axes.titlesize": 9, "axes.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.5, "figure.dpi": 150,
    })
    fig, axes = plt.subplots(1, len(GROUP_ORDER),
                             figsize=(11.5, 3.5),
                             sharey=True)
    cats = ["route6", "inland", "both", "neither"]
    for ax, grp in zip(axes, GROUP_ORDER):
        gsub = table[table["origin_group"] == grp].set_index("mode")
        gsub = gsub.reindex(MODES)
        bottoms = np.zeros(len(MODES))
        x = np.arange(len(MODES))
        for cat in cats:
            col = f"{cat}_pct"
            vals = gsub[col].values / 100.0
            ax.bar(x, vals, bottom=bottoms, width=0.65,
                   color=CAT_COLORS[cat], edgecolor="white", linewidth=0.5,
                   label=cat if grp == GROUP_ORDER[0] else None)
            for xi, v, b in zip(x, vals, bottoms):
                if v > 0.06:
                    ax.text(xi, b + v / 2, f"{v*100:.0f}",
                            ha="center", va="center",
                            fontsize=6.5, color="white", fontweight="bold")
            bottoms += vals
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace("_", " ") for m in MODES],
                           rotation=20, fontsize=7)
        n_total = int(gsub["n_agents"].sum())
        ax.set_title(f"{grp}\n(N={n_total})", fontsize=8)
        ax.set_ylim(0, 1.0)
        ax.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Fraction of agents")
    fig.suptitle("Corridor usage by origin group and mode — "
                 "route6_closed scenario (Day 5 data, Day 6 disaggregation)",
                 fontsize=10)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", fontsize=7,
               bbox_to_anchor=(0.995, 0.97))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = out_dir / "D6-0_corridor_by_origin.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="route6_closed")
    ap.add_argument("--quick", action="store_true",
                    help="ignored (this script does no simulation)")
    args = ap.parse_args()

    if not (RES_D5 / "corridor_usage.csv").exists():
        print(f"ERROR: missing {RES_D5/'corridor_usage.csv'}; run Day 5 first.",
              file=sys.stderr)
        return 1

    print(f"[Day 6 §1] loading Day 5 outputs from {RES_D5}")
    corridor = pd.read_csv(RES_D5 / "corridor_usage.csv")
    agents = pd.read_csv(
        RES_D5 / "agents_all_scenarios.csv",
        usecols=["scenario", "member", "decision_mode", "agent_id",
                 "timestep", "location"],
    )

    merged = _build_origin_table(corridor, agents)
    table = _summarize(merged, args.scenario)

    RES_D6.mkdir(parents=True, exist_ok=True)
    out_csv = RES_D6 / "corridor_disaggregated.csv"
    table.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}")

    print("\n=== Origin-disaggregated corridor usage "
          f"({args.scenario}) ===")
    print(table.to_string(index=False, float_format=lambda v: f"{v:7.2f}"))

    print("\n=== Chi-square sys1_only vs blend by origin group ===")
    chi_rows = []
    for grp in ["tomioka", "okuma+futaba",
                "tomioka+okuma+futaba", "namie", "all_fork_origins"]:
        if grp == "tomioka+okuma+futaba":
            ORIGIN_GROUPS[grp] = ["tomioka", "okuma", "futaba"]
        rec = _chi2_for_group(merged, args.scenario, grp)
        chi_rows.append(rec)
        print(f"  {grp:25s}: blend_inland={rec['blend_inland_pct']:5.1f}%, "
              f"s1_inland={rec['s1_inland_pct']:5.1f}%, "
              f"Δ={rec['shift_pp']:+5.1f}pp, "
              f"χ²={rec['chi2']:6.3f}, p={rec['p']:.4g}, "
              f"N(s1={rec['n_s1']}, blend={rec['n_blend']})")

    chi_csv = RES_D6 / "corridor_chi2_by_origin.csv"
    pd.DataFrame(chi_rows).to_csv(chi_csv, index=False)
    print(f"\n  wrote {chi_csv}")

    FIG_D6.mkdir(parents=True, exist_ok=True)
    _fig_d6_0(table, FIG_D6)

    # Headline
    tomioka_fork = next(r for r in chi_rows
                        if r["group"] == "tomioka+okuma+futaba")
    aggregate = next(r for r in chi_rows
                     if r["group"] == "all_fork_origins")
    print("\n=== HEADLINE ===")
    print(f"  Tomioka-fork shift (tomioka+okuma+futaba): "
          f"{tomioka_fork['shift_pp']:+.2f}pp "
          f"(p={tomioka_fork['p']:.4g})")
    print(f"  Aggregate shift  (all fork origins):       "
          f"{aggregate['shift_pp']:+.2f}pp "
          f"(p={aggregate['p']:.4g})")
    ratio = (abs(tomioka_fork["shift_pp"]) / max(1e-9, abs(aggregate["shift_pp"])))
    print(f"  Tomioka/aggregate magnitude ratio: {ratio:.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
