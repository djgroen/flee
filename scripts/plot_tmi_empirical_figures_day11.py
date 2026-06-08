#!/usr/bin/env python3
"""TMI empirical figure suite — all numbers from tmi_empirical_data.json."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"
OUT = REPO / "figures" / "tmi" / "empirical"

NAVY = "#1F3864"
BLUE = "#2E5FA3"
LTBLUE = "#D6E4F7"
GOLD = "#C9A227"
RED = "#C00000"
ORANGE = "#C55A11"
GREEN = "#375623"


def _load():
    with (TMI / "tmi_empirical_data.json").open(encoding="utf-8") as f:
        return json.load(f)


def fig_g1(d):
    dt = d["departure_timing"]
    zones = dt["zones_g1"]
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(14, 6))
    x = np.arange(len(zones))
    w = 0.35
    by_f = [z["pct_by_friday"] for z in zones]
    after = [100.0 - z["pct_by_friday"] for z in zones]
    colors = [RED if z["style"] == "inner" else ORANGE if z["style"] == "middle" else BLUE for z in zones]
    ax0.bar(x - w / 2, by_f, width=w, label="By Friday (t=10)", color=colors, edgecolor=NAVY)
    ax0.bar(
        x + w / 2,
        after,
        width=w,
        label="After Friday",
        color=colors,
        edgecolor=NAVY,
        hatch="//",
        alpha=0.85,
    )
    labels = [z["label"] + ("*" if z.get("interpolated") else "") for z in zones]
    ax0.set_xticks(x)
    ax0.set_xticklabels(labels, rotation=25, ha="right")
    ax0.set_ylabel("% of zone")
    ax0.set_title("Departure timing by residential zone")
    ax0.legend()
    ax0.text(0.02, 0.02, "* " + dt["footnote_interpolation"], transform=ax0.transAxes, fontsize=7, va="bottom")

    zt = d["evacuation_rates_comparison"]["zeigler_1981_table3"]
    ct = d["evacuation_rates_comparison"]["cutter_1982_table2"]
    xz = np.arange(len(zt))
    xc = np.linspace(-0.2, len(zt) - 0.8, len(ct))
    ax1.bar(xz, [r["rate_percent"] for r in zt], width=0.35, color=NAVY, label="Zeigler 1981")
    ax1.bar(xc + 0.35, [r["rate_percent"] for r in ct], width=0.35, facecolor="none", edgecolor=BLUE, linewidth=2, label="Cutter 1982")
    ax1.axvline(3.5, color=RED, linestyle="--")
    ax1.text(3.55, max(max(r["rate_percent"] for r in zt), 50), "12-mile discontinuity", color=RED, fontsize=8)
    adv = d["advisory_contrast"]
    ax1.axhline(adv["pct_within_15mi_evacuated"], color=NAVY, linestyle="--", alpha=0.7)
    ax1.text(
        0.5,
        adv["pct_within_15mi_evacuated"] + 1,
        f'{adv["pct_within_15mi_evacuated"]}% within 15 mi evacuated vs {adv["pct_officially_advised"]}% advised',
        fontsize=8,
    )
    ax1.set_xticks(xz)
    ax1.set_xticklabels([r["zone"] for r in zt])
    ax1.set_ylabel("Evacuation rate (%)")
    ax1.set_title("Evacuation rate by zone (cross-survey)")
    ax1.legend()
    fig.tight_layout()
    fig.savefig(OUT / "G1_zeigler_paradox.png", dpi=150)
    plt.close(fig)


def fig_g2(d):
    sc = d["stress_curves_g2"]
    sched = json.loads((TMI / "conflict_schedule_tmi.json").read_text(encoding="utf-8"))
    cvals = sched["c_values"]
    fig, ax = plt.subplots(figsize=(14, 6))
    te = np.array(sc["evacuees"])
    tr = np.array(sc["residual_population"])
    ax.plot(te[:, 0], te[:, 1], color=NAVY, lw=2.5, label="Evacuees stress (empirical curve)")
    ax.plot(tr[:, 0], tr[:, 1], color=BLUE, lw=1.5, label="Residual population stress")
    t_sched = np.arange(len(cvals), dtype=float)
    ax.step(t_sched, cvals, where="post", color=GOLD, linestyle="--", lw=2, label="c(t) — FLEE schedule")
    thr = float(sc["threshold"])
    ax.axhline(thr, color=RED, linestyle="--")
    ax.text(len(cvals) * 0.72, thr + 0.02, sc["threshold_citation"], fontsize=8)
    for m in sc["event_markers"]:
        ax.axvline(m["t"], color="gray", alpha=0.4, lw=0.8)
        ax.text(m["t"], 1.02, m["label"], fontsize=8, ha="center", rotation=0, color=m.get("emphasis", "black"))
    ax.set_xlim(0, 19)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("FLEE timestep (6 h)")
    ax.set_ylabel("Stress / c(t)")
    ax.legend(loc="upper left")
    ax.text(
        0.98,
        0.85,
        "P_S2 = Psi × Omega\nOmega collapse at t=10:\n→ S1-dominated rapid departure\n→ High-Psi outer-zone agents still cross CMC\nOmega recovery at t=16:\n→ S2-enabled deliberate return",
        transform=ax.transAxes,
        ha="right",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor=LTBLUE),
    )
    fig.tight_layout()
    fig.savefig(OUT / "G2_stress_curves_omega.png", dpi=150)
    plt.close(fig)


def fig_g3(d):
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    cd = d["departure_timing"]["cumulative_departure_g3"]
    ax = axs[0, 0]
    for key, col in [("0-6mi", RED), ("7-12mi", ORANGE), (">12mi", BLUE)]:
        pts = cd[key]["points"]
        xs = [p["date"] for p in pts]
        ys = [p["cumulative_pct"] for p in pts]
        ax.plot(xs, ys, "o-", color=col, label=key)
    ax.axvline(1.5, color="gray", linestyle="--", label="Governor's advisory (schematic)")
    ax.set_title("Cumulative departure (Zeigler + interpolation)")
    ax.legend()
    ax.tick_params(axis="x", rotation=30)

    rb = d["return_behavior"]
    ax = axs[0, 1]
    ax.plot(rb["weeks"], rb["cumulative_return_pct"], "o-", color=NAVY, lw=2)
    ax.set_xlabel("Weeks post-accident")
    ax.set_ylabel("Cumulative % returned")
    ax.set_title("Return behavior")

    ax = axs[1, 0]
    age = d["cutter_age_evacuation_rates"]
    ag = age["age_groups"]
    rates = age["rates_percent"]
    cmap = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(ag)))
    ax.bar(ag, rates, color=cmap, edgecolor=NAVY)
    ax.set_title(age["source"])

    ax2 = ax.inset_axes([0.52, 0.12, 0.45, 0.78])
    si = d["cutter_social_influence"]
    ax2.bar(
        ["Evacuees\n(neighbors left)", "Non-evacuees\n(neighbors stayed)"],
        [si["evacuees_neighbors_left_pct"], si["non_evacuees_neighbors_stayed_pct"]],
        color=[ORANGE, BLUE],
        edgecolor=NAVY,
    )
    ax2.set_title("Social influence\n" + si["source"], fontsize=8)

    ax = axs[1, 1]
    rfor = d["reasons_for_evacuating"]
    rnot = d["reasons_for_not_evacuating"]
    y_pos = np.arange(len(rfor))
    ax.barh(y_pos, [r["percent"] for r in rfor], color=RED, alpha=0.85, label="For evacuating")
    ax.barh(-np.arange(len(rnot)) - 1, [-r["percent"] for r in rnot], color=BLUE, alpha=0.85, label="Against")
    ax.set_yticks(list(y_pos) + list(-np.arange(len(rnot)) - 1))
    ax.set_yticklabels([r["reason"] for r in rfor] + [r["reason"] for r in rnot], fontsize=7)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("% of respondents")
    ax.set_title("Reasons butterfly (from JSON)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "G3_multi_panel_summary.png", dpi=150)
    plt.close(fig)


def fig_g4(d):
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={"width_ratios": [1.1, 0.9]})
    jz = d["johnson_zeigler_1986_panel"]
    fl = d["flee_dual_process_panel"]
    ax0.axis("off")
    ax0.set_title("Johnson & Zeigler (1986)")
    boxes = [
        (0.1, 0.75, "LOCATION\n(x1)"),
        (0.4, 0.75, "STAGE IN LIFE\n(x2)"),
        (0.7, 0.75, "SOCIAL STATUS\n(x3)"),
        (0.25, 0.5, "NUCLEAR ATTITUDE\n(x8)"),
        (0.55, 0.5, "TMI ATTITUDE\n(x9)"),
        (0.4, 0.28, "RISK PERCEPTION\n(x10)"),
        (0.4, 0.05, "EVACUATION\n(x11)", RED),
    ]
    for b in boxes:
        fc = b[3] if len(b) > 3 else "white"
        ax0.add_patch(
            FancyBboxPatch(
                (b[0], b[1]),
                0.18,
                0.12,
                boxstyle="round,pad=0.01",
                facecolor=fc,
                edgecolor=NAVY,
                linewidth=2,
                transform=ax0.transAxes,
            )
        )
        ax0.text(b[0] + 0.09, b[1] + 0.06, b[2], ha="center", va="center", fontsize=8, transform=ax0.transAxes)

    ax0.text(0.5, -0.02, jz["caption"], transform=ax0.transAxes, ha="center", fontsize=9)

    ax1.axis("off")
    ax1.set_title("FLEE Dual-Process (this paper)")
    for txt, xy, fc in [
        ("experience_index → Ψ(α)", (0.15, 0.82), "white"),
        ("conflict_level → Ω(β)", (0.55, 0.82), "white"),
        ("Ψ × Ω → P_S2", (0.35, 0.58), GOLD),
        ("Sys1 heuristic", (0.1, 0.35), NAVY),
        ("Sys2 deliberative", (0.55, 0.35), ORANGE),
        ("PATH_AT_ARRIVAL", (0.3, 0.08), GREEN),
    ]:
        ax1.add_patch(
            FancyBboxPatch(
                (xy[0], xy[1]),
                0.28,
                0.1,
                boxstyle="round,pad=0.02",
                facecolor=fc,
                edgecolor=NAVY,
                transform=ax1.transAxes,
            )
        )
        ax1.text(xy[0] + 0.14, xy[1] + 0.05, txt, ha="center", va="center", fontsize=8, transform=ax1.transAxes)
    ax1.text(0.5, -0.02, fl["caption"], transform=ax1.transAxes, ha="center", fontsize=9)

    fig.text(0.5, 0.48, d["bridging_model_text"], ha="center", fontsize=9, bbox=dict(facecolor=LTBLUE))
    fig.tight_layout()
    fig.savefig(OUT / "G4_model_comparison.png", dpi=150)
    plt.close(fig)


def fig_g5(d):
    rows = d["education_effect"]["finding_rutgers_weak"]["spatial_inconsistency"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ncol = 3
    nrow = len(rows)
    data = np.zeros((nrow, ncol))
    for i, r in enumerate(rows):
        data[i, 0] = r["chi_sq"]
        data[i, 1] = r["p_value"]
        data[i, 2] = r["gamma"]
    for i in range(nrow):
        for j in range(ncol):
            val = data[i, j]
            p = rows[i]["p_value"] if j != 1 else rows[i]["p_value"]
            bg = RED if p < 0.05 and j == 1 else GREEN if j == 1 else "white"
            if j == 2:
                bg = plt.cm.RdBu_r(0.5 + 0.5 * np.sign(val) * min(abs(val), 1.0))
            ax.text(
                j + 0.5,
                nrow - i - 0.5,
                f"{val:.3f}",
                ha="center",
                va="center",
                fontsize=10,
                bbox=dict(facecolor=bg, alpha=0.6, boxstyle="round,pad=0.2"),
            )
    ax.set_xlim(0, ncol)
    ax.set_ylim(0, nrow)
    ax.set_xticks([0.5, 1.5, 2.5])
    ax.set_xticklabels(["χ² statistic", "p-value", "γ coefficient"])
    ax.set_yticks([nrow - i - 0.5 for i in range(nrow)])
    ax.set_yticklabels([f'{r["zone"]}\n({r["zone_code"]})' for r in rows])
    ax.set_title("Education × zone (Cutter & Barnes 1982)")
    fig.tight_layout()
    fig.savefig(OUT / "G5_education_zone_heatmap.png", dpi=150)
    plt.close(fig)


def fig_g6(d):
    dm = d["destination_map_g6"]
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor("#F5F5F5")
    ax.axhline(40, color="#888888")
    ax.axvline(-76, color="#888888")
    plant = dm["plant"]
    ax.scatter([plant["lon"]], [plant["lat"]], s=300, marker="*", c=GOLD, edgecolors=NAVY, zorder=5)
    for c in dm["cities"]:
        ax.scatter([c["lon"]], [c["lat"]], s=20, color=NAVY)
        ax.text(c["lon"], c["lat"], c["name"] + ("\n" + c["note"] if c.get("note") else ""), fontsize=7)
    for arr in dm["flow_arrows"]:
        ax.annotate(
            "",
            xy=(plant["lon"] - 0.8, plant["lat"] + 0.5),
            xytext=(plant["lon"], plant["lat"]),
            arrowprops=dict(arrowstyle="->", lw=arr["lw"], color=NAVY if arr["lw"] > 3 else BLUE),
        )
    dists = "\n".join([x["label"] for x in dm["distance_estimates"]])
    ax.text(0.98, 0.95, dists, transform=ax.transAxes, ha="right", va="top", fontsize=8, bbox=dict(facecolor="white"))
    ax.set_title("Evacuation destination schematic (from JSON)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.tight_layout()
    fig.savefig(OUT / "G6_destination_map.png", dpi=150)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = _load()
    fig_g1(d)
    fig_g2(d)
    fig_g3(d)
    fig_g4(d)
    fig_g5(d)
    fig_g6(d)
    print("Wrote G1–G6 under", OUT)


if __name__ == "__main__":
    main()
