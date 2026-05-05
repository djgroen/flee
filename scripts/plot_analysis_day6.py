#!/usr/bin/env python3
"""Day 6 figures: D6-A, D6-B1, D6-B2, D6-C1, D6-C2, D6-C3."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO   = Path(__file__).resolve().parent.parent
RES_D6 = REPO / "results" / "day6"
FIG_D6 = REPO / "figures" / "fukushima" / "day6"

KAPPA_LOCKED = 18.40740740740741

ORIGIN_DISPLAY = {"namie_group": "Namie", "tomioka_group": "Tomioka",
                  "okuma_group": "Okuma"}
GROUP_ORDER = ["namie_group", "tomioka_group", "okuma_group"]


# --------------------------------------------------------------------------
# Figure D6-A: kappa routing sensitivity (3 panels)
# --------------------------------------------------------------------------

def fig_d6_a():
    summary = pd.read_csv(RES_D6 / "goal_a_summary.csv")
    verdict = json.loads((RES_D6 / "goal_a_verdict.json").read_text())

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), sharex=True)
    panels = [
        ("corridor_inland_pct", "Corridor inland fraction", axes[0]),
        ("mean_path_length",    "Mean path length (km)",    axes[1]),
        ("s2_signal_mean",      "S2 signal proxy (km^-1)",  axes[2]),
    ]
    for col, label, ax in panels:
        x = summary["kappa"].to_numpy()
        m = summary[f"{col}_mean"].to_numpy()
        s = summary[f"{col}_std"].to_numpy()
        ax.errorbar(x, m, yerr=s, fmt="o-", lw=1.4, ms=5, capsize=3,
                    color="#1f77b4")
        ax.axvline(KAPPA_LOCKED, color="red", ls="--", lw=1.2,
                   label=f"locked kappa = {KAPPA_LOCKED:.3f}")
        # +/-5% band around the locked-kappa value (FLAT threshold).
        i_locked = int(np.argmin(np.abs(x - KAPPA_LOCKED)))
        ref = float(m[i_locked])
        ax.axhspan(ref * 0.95, ref * 1.05,
                   color="#a6dba0", alpha=0.30,
                   label="+/-5% (FLAT band)")
        ax.set_xlabel("kappa")
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=7)
    fig.suptitle(
        "kappa sensitivity on real Fukushima OSM network (routing QoIs)\n"
        f"verdict: {verdict['verdict']}; "
        f"corridor range {verdict['corridor_inland_pct_range_pct']:.1f}%, "
        f"path range {verdict['path_length_range_pct']:.1f}%",
        y=1.02)
    fig.tight_layout()
    out = FIG_D6 / "D6-A_kappa_routing_sensitivity.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[d6-a] wrote {out}")


# --------------------------------------------------------------------------
# Figure D6-B1: regime P_S2 comparison (4 panels)
# --------------------------------------------------------------------------

def fig_d6_b1():
    ts_path = RES_D6 / "goal_b_zone_ps2_timeseries.csv"
    iitate_path = RES_D6 / "goal_b_iitate_ps2_timeseries.csv"
    if not ts_path.exists():
        print(f"[d6-b1] missing {ts_path}; skipping")
        return
    ts = pd.read_csv(ts_path)
    iit_ts = (pd.read_csv(iitate_path) if iitate_path.exists()
              else pd.DataFrame())

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.5),
                              sharex=True, sharey=True)
    zone_colors = {"inner": "#D35400", "mid": "#E67E22", "outer": "#2E86C1"}
    iit_color = "#9B26B6"

    combos = [
        ("official_zones", "blend",     axes[0, 0],
         "official_zones / blend"),
        ("dosimeter_proxy", "blend",    axes[0, 1],
         "dosimeter_proxy / blend"),
        ("official_zones", "sys1_only", axes[1, 0],
         "official_zones / sys1_only"),
        ("dosimeter_proxy", "sys1_only", axes[1, 1],
         "dosimeter_proxy / sys1_only"),
    ]
    for scen, mode, ax, title in combos:
        for zone in ("inner", "mid", "outer"):
            sub = ts[(ts["scenario"] == scen) & (ts["mode"] == mode)
                     & (ts["zone"] == zone)]
            if sub.empty:
                continue
            agg = sub.groupby("timestep")["mean_ps2"].agg(
                ["mean", "std"]).reset_index()
            t = agg["timestep"]
            m = agg["mean"]
            s = agg["std"].fillna(0.0)
            ax.fill_between(t, m - s, m + s, alpha=0.2,
                            color=zone_colors[zone])
            ax.plot(t, m, color=zone_colors[zone], lw=1.5, label=zone)
        # Iitate overlay.
        if not iit_ts.empty:
            isub = iit_ts[(iit_ts["scenario"] == scen)
                          & (iit_ts["mode"] == mode)]
            if not isub.empty:
                agg = isub.groupby("timestep")["mean_ps2"].agg(
                    ["mean", "std"]).reset_index()
                ax.plot(agg["timestep"], agg["mean"],
                        color=iit_color, lw=1.4, ls="--",
                        label="iitate (zone)")
        ax.set_xlim(0, 30)
        ax.set_ylim(0, 0.55)
        ax.set_title(title, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right", fontsize=7)
        if ax in axes[1, :]:
            ax.set_xlabel("timestep")
        if ax in axes[:, 0]:
            ax.set_ylabel("mean P_S2 (active agents)")
    fig.suptitle("P_S2 by zone (incl. Iitate) for the four "
                 "scenario / mode combinations", y=1.00)
    fig.tight_layout()
    out = FIG_D6 / "D6-B1_regime_ps2_comparison.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[d6-b1] wrote {out}")


# --------------------------------------------------------------------------
# Figure D6-B2: Iitate clearance violins (blend mode)
# --------------------------------------------------------------------------

def fig_d6_b2():
    df = pd.read_csv(RES_D6 / "goal_b_regime_comparison.csv")
    summ = json.loads((RES_D6 / "goal_b_summary.json").read_text())

    blend = df[df["mode"] == "blend"]
    data = []
    labels = []
    for scen in ("official_zones", "dosimeter_proxy"):
        sub = blend[blend["scenario"] == scen]
        vals = pd.to_numeric(sub["iitate_clearance_t4"],
                              errors="coerce").dropna().to_numpy()
        if len(vals):
            data.append(vals)
            labels.append(scen)
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    if data:
        parts = ax.violinplot(data, showmeans=True, showmedians=True,
                              widths=0.7)
        # Colour palette.
        colors = ["#A6CEE3", "#FB9A99"]
        for i, body in enumerate(parts["bodies"]):
            body.set_facecolor(colors[i % len(colors)])
            body.set_edgecolor("black")
            body.set_alpha(0.7)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels)
    # Reference line at the inner-zone clearance rate (official_zones blend).
    inner_ref = (summ.get("official_zones", {}).get("blend", {})
                 .get("inner_clearance_t7", {}).get("mean"))
    if inner_ref is not None:
        ax.axhline(inner_ref, color="#444", ls="--", lw=1.0,
                   label=f"inner_clearance_t7 ref = {inner_ref:.2f}")
    delta = summ.get("iitate_effect", {}).get("delta_pct")
    interp = summ.get("iitate_effect", {}).get("interpretation", "")
    ax.set_ylabel("Iitate clearance fraction at t = 4")
    ax.set_xlabel("Information regime (blend mode)")
    ax.set_title(
        "Iitate clearance at t=4 across information regimes\n"
        f"delta = {delta:+.2f}pp -- {interp[:90]}{'...' if interp and len(interp) > 90 else ''}",
        fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    out = FIG_D6 / "D6-B2_iitate_clearance.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[d6-b2] wrote {out}")


# --------------------------------------------------------------------------
# Figure D6-C1: origin routing bars (grouped)
# --------------------------------------------------------------------------

def fig_d6_c1():
    summ = pd.read_csv(RES_D6 / "goal_c_origin_summary.csv")
    v = json.loads((RES_D6 / "goal_c_verdict.json").read_text())
    aggregate = float(v.get("aggregate_inland_delta_day5", 9.3))

    groups = [g for g in GROUP_ORDER if g in summ["origin_group"].values]
    x = np.arange(len(groups))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    s1_vals = []
    bl_vals = []
    s1_err  = []
    bl_err  = []
    for g in groups:
        s1 = summ[(summ["origin_group"] == g) & (summ["mode"] == "sys1_only")]
        bl = summ[(summ["origin_group"] == g) & (summ["mode"] == "blend")]
        s1_vals.append(float(s1["inland_pct_mean"]) if len(s1) else 0.0)
        bl_vals.append(float(bl["inland_pct_mean"]) if len(bl) else 0.0)
        s1_err.append(float(s1["inland_pct_std"]) if len(s1) else 0.0)
        bl_err.append(float(bl["inland_pct_std"]) if len(bl) else 0.0)

    bars1 = ax.bar(x - width/2, s1_vals, width, yerr=s1_err,
                   color="#888780", capsize=4, label="sys1_only")
    bars2 = ax.bar(x + width/2, bl_vals, width, yerr=bl_err,
                   color="#1D9E75", capsize=4, label="blend")
    # Annotate per-group delta with bracket.
    for i, g in enumerate(groups):
        d = bl_vals[i] - s1_vals[i]
        y = max(s1_vals[i] + s1_err[i], bl_vals[i] + bl_err[i]) + 4
        ax.annotate(f"{d:+.1f}pp",
                    xy=(x[i], y), ha="center", fontsize=9,
                    color="#16A085" if d >= 0 else "#C0392B",
                    fontweight="bold")
    # Day-5 aggregate reference.
    ax.axhline(aggregate, color="red", ls=":", lw=1.0, alpha=0.8,
               label=f"Day 5 aggregate = {aggregate:.1f}pp (reference)")
    ax.set_xticks(x)
    ax.set_xticklabels([ORIGIN_DISPLAY.get(g, g) for g in groups])
    ax.set_ylabel("Inland fraction (%; conditional on fork-corridor use)")
    ax.set_title(
        f"Origin-disaggregated inland routing: blend vs sys1_only\n"
        f"verdict: {v.get('masking_verdict')}; "
        f"Tomioka delta = "
        f"{v['origin_group_deltas']['tomioka_group']['blend_vs_s1_inland_delta']:+.2f}pp")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    out = FIG_D6 / "D6-C1_origin_routing_bars.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[d6-c1] wrote {out}")


# --------------------------------------------------------------------------
# Figure D6-C2: origin path-length violins (per route_type)
# --------------------------------------------------------------------------

def fig_d6_c2():
    traj = pd.read_csv(RES_D6 / "goal_c_agent_trajectories.csv")
    if "origin_group" not in traj.columns:
        # Reconstruct from origin_town if needed.
        origin_to_group = {}
        from scripts.run_analysis_day6 import ORIGIN_GROUPS
        for g, towns in ORIGIN_GROUPS.items():
            for t in towns:
                origin_to_group[t] = g
        traj["origin_group"] = traj["origin_town"].map(origin_to_group)
    traj = traj[traj["origin_group"].notna()]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5),
                              sharey=True)
    for ax, grp in zip(axes, GROUP_ORDER):
        sub = traj[traj["origin_group"] == grp]
        data = []
        labels = []
        for rt in ("inland", "coastal", "north"):
            for mode in ("sys1_only", "blend"):
                vals = sub[(sub["route_type"] == rt)
                           & (sub["mode"] == mode)
                           ]["total_path_km"].dropna().to_numpy()
                if len(vals) >= 2:
                    data.append(vals)
                    labels.append(f"{rt}\n{mode}")
        if data:
            parts = ax.violinplot(data, showmeans=True, widths=0.8)
            colors_cycle = ["#888780", "#1D9E75"]
            for i, body in enumerate(parts["bodies"]):
                body.set_facecolor(colors_cycle[i % 2])
                body.set_edgecolor("black")
                body.set_alpha(0.7)
            ax.set_xticks(range(1, len(data) + 1))
            ax.set_xticklabels(labels, fontsize=7, rotation=30, ha="right")
        ax.set_title(ORIGIN_DISPLAY.get(grp, grp))
        ax.grid(True, alpha=0.3, axis="y")
        if ax is axes[0]:
            ax.set_ylabel("Total path length at arrival (km)")
    fig.suptitle("Path lengths by origin x route_type x mode "
                 "(transit-based corridor classification)", y=1.02)
    fig.tight_layout()
    out = FIG_D6 / "D6-C2_origin_path_lengths.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[d6-c2] wrote {out}")


# --------------------------------------------------------------------------
# Figure D6-C3: departure timing survival curves
# --------------------------------------------------------------------------

def fig_d6_c3():
    traj = pd.read_csv(RES_D6 / "goal_c_agent_trajectories.csv")
    if "origin_group" not in traj.columns:
        from scripts.run_analysis_day6 import ORIGIN_GROUPS
        origin_to_group = {}
        for g, towns in ORIGIN_GROUPS.items():
            for t in towns:
                origin_to_group[t] = g
        traj["origin_group"] = traj["origin_town"].map(origin_to_group)
    traj = traj[traj["origin_group"].notna()].copy()

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5),
                              sharey=True, sharex=True)
    mode_color = {"sys1_only": "#888780", "blend": "#1D9E75"}
    timesteps = np.arange(0, 21)
    for ax, grp in zip(axes, GROUP_ORDER):
        sub = traj[traj["origin_group"] == grp]
        for mode in ("sys1_only", "blend"):
            mdf = sub[sub["mode"] == mode]
            if mdf.empty:
                continue
            departures = mdf["departure_timestep"].copy()
            # Agents that never departed have departure_timestep = -1.
            departures = departures.replace(-1, np.nan)
            n_total = len(mdf)
            still_at_origin = []
            for t in timesteps:
                # Fraction whose departure_t > t (or never departed).
                after = ((departures > t) | departures.isna()).sum()
                still_at_origin.append(after / max(1, n_total))
            ax.step(timesteps, still_at_origin, where="post",
                    color=mode_color[mode], lw=1.6, label=mode)
        ax.set_title(ORIGIN_DISPLAY.get(grp, grp))
        ax.set_xlabel("timestep")
        ax.set_ylim(0, 1.05)
        ax.set_xlim(0, 20)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=8)
        if ax is axes[0]:
            ax.set_ylabel("Fraction still at origin")
    fig.suptitle(
        "Departure timing survival curves by origin group "
        "(fraction still at origin vs timestep)", y=1.02)
    fig.tight_layout()
    out = FIG_D6 / "D6-C3_departure_timing.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"[d6-c3] wrote {out}")


def main():
    FIG_D6.mkdir(parents=True, exist_ok=True)
    fig_d6_a()
    fig_d6_b1()
    fig_d6_b2()
    fig_d6_c1()
    fig_d6_c2()
    fig_d6_c3()


if __name__ == "__main__":
    main()
