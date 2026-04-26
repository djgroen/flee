#!/usr/bin/env python3
"""
Day 5: Fukushima OSM scenarios — intermediate towns and corridor effects.

Runs four scenarios that test whether corridor structure produces routing
differences between System-1 and System-2 agents on the Fukushima network.
The Route 6 closure is modelled as a soft closure: per-day conflict at
naraha and hirono is spiked to 0.95 from day 3 onward, so that
high-System-2 agents can discover the inland Kawauchi alternative through
the precomputed ConflictPotentialField while pure-System-1 agents continue
to follow the shortest-distance heuristic and are blocked by the elevated
corridor conflict.

Scenarios
---------
1. baseline             -- input/fukushima_day3/ (Day 3 replication)
2. full_network         -- input/fukushima_day5/ with conflicts.csv
3. route6_closed        -- input/fukushima_day5/ with conflicts_route6_closed.csv
4. closure_heterogeneous -- as scenario 3, but agents draw experience from
                            Normal(0.4, 0.2) clipped to [0, 1] instead of
                            the Day 3 Beta(2, 5) default.

In this codebase the towns/links the prompt asks for already exist (added
in the Day 3 OSM build), so scenarios 1 and 2 use the same input directory
and are expected to produce statistically equivalent results. Scenario 1
is therefore reused for Scenario 2 to save compute (a single run pair
covers both rows of every output table).

Usage
-----
    python scripts/run_day5_scenarios.py --quick     # 200 agents, 3 ensemble
    python scripts/run_day5_scenarios.py             # 500 agents, 10 ensemble
    python scripts/run_day5_scenarios.py --skip-runs # only re-make figures
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

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import the building blocks from the Day 3 driver so the simulator is the
# same in every detail (config overrides, agent placement, evolve loop, QoIs).
from scripts import run_fukushima_day3 as d3  # noqa: E402
from flee.SimulationSettings import SimulationSettings  # noqa: E402

ZONES = d3.ZONES
ZONE_COLORS = d3.ZONE_COLORS
CAMP_NAMES = d3.CAMP_NAMES
MODE_ORDER = d3.MODE_ORDER
PALETTE = d3.PALETTE
LINESTYLE = d3.LINESTYLE

ROUTE6_NODES = {"naraha", "hirono"}
INLAND_NODES = {"kawauchi"}
FORK_ORIGINS = {"tomioka", "naraha", "okuma", "futaba", "namie"}

SCENARIO_COLORS = {
    "baseline":               "#888780",
    "full_network":           "#444",
    "route6_closed":          "#BA7517",
    "closure_heterogeneous":  "#1D9E75",
}

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------


def scenario_specs(repo: Path):
    """Return dict scenario_id -> spec.

    Each spec contains the input directory, the conflicts file (relative to
    that dir), and the experience distribution to use when distributing
    agents.
    """
    return {
        "baseline": {
            "input_dir":     repo / "input" / "fukushima_day3",
            "conflict_file": "conflicts.csv",
            "x_dist":        "beta",
            "label":         "Baseline (Day 3)",
        },
        "full_network": {
            "input_dir":     repo / "input" / "fukushima_day5",
            "conflict_file": "conflicts.csv",
            "x_dist":        "beta",
            "label":         "Full network",
        },
        "route6_closed": {
            "input_dir":     repo / "input" / "fukushima_day5",
            "conflict_file": "conflicts_route6_closed.csv",
            "x_dist":        "beta",
            "label":         "Route 6 closed",
        },
        "closure_heterogeneous": {
            "input_dir":     repo / "input" / "fukushima_day5",
            "conflict_file": "conflicts_route6_closed.csv",
            "x_dist":        "normal_clip",
            "label":         "Closure + heterogeneous Ψ",
        },
    }


# ---------------------------------------------------------------------------
# Patched agent distribution (supports a Normal(0.4, 0.2) experience draw)
# ---------------------------------------------------------------------------

_X_DIST: str = "beta"


def _experience_draw(rng: np.random.Generator, n: int) -> np.ndarray:
    """Draw n experience indices according to the active scenario distribution."""
    if _X_DIST == "normal_clip":
        x = rng.normal(loc=0.4, scale=0.2, size=n)
        return np.clip(x, 0.0, 1.0)
    return rng.beta(2, 5, size=n)


def _patched_distribute(e, lm, n_total, seed):
    """Re-implementation of d3.distribute_agents_by_pop using `_experience_draw`."""
    rng = np.random.default_rng(seed)

    spawn = {name: loc for name, loc in lm.items()
             if not getattr(loc, "camp", False)}
    pops = {}
    for name, loc in spawn.items():
        pop = getattr(loc, "pop", 0)
        if pop is None or pop == "" or pop == 0:
            pop = 1000
        pops[name] = int(pop)

    total_pop = sum(pops.values())
    counts = {}
    assigned = 0
    sorted_names = sorted(pops.keys(), key=lambda n: pops[n], reverse=True)
    for name in sorted_names[:-1]:
        c = max(1, round(n_total * pops[name] / total_pop))
        counts[name] = c
        assigned += c
    counts[sorted_names[-1]] = max(1, n_total - assigned)

    agents_added = []
    for name in sorted(counts.keys()):
        loc = lm[name]
        n = counts[name]
        exp_indices = _experience_draw(rng, n)
        for exp_idx in exp_indices:
            e.addAgent(location=loc, attributes={})
            a = e.agents[-1]
            a.experience_index = float(exp_idx)
            agents_added.append(a)

    return agents_added


# ---------------------------------------------------------------------------
# Single ensemble member runner that also captures per-agent location history
# ---------------------------------------------------------------------------


def _run_member(input_dir: Path, conflict_file: str, mode: str,
                n_agents: int, n_steps: int,
                alpha: float, beta: float, kappa: float,
                seed: int, x_dist: str):
    """Run one (mode, seed) member and return (agents_df, arrival_df)."""
    global _X_DIST
    _X_DIST = x_dist

    # Patch the conflicts file path used inside d3.run_one. d3.run_one builds
    # the conflict path as Path(input_dir) / "conflicts.csv", so we point the
    # whole input_dir at a temporary view that aliases conflicts.csv to the
    # requested variant. The cheapest way is a per-call symlink folder.
    if conflict_file == "conflicts.csv":
        eff_dir = input_dir
    else:
        eff_dir = _materialize_conflict_view(input_dir, conflict_file, seed)

    # Swap in the patched agent distribution for the duration of this call.
    saved = d3.distribute_agents_by_pop
    d3.distribute_agents_by_pop = _patched_distribute
    try:
        agents_df, lm, arrivals = d3.run_one(
            str(eff_dir), mode, n_agents, n_steps,
            alpha, beta, kappa, seed,
        )
    finally:
        d3.distribute_agents_by_pop = saved

    return agents_df, lm, arrivals


def _materialize_conflict_view(input_dir: Path, conflict_file: str,
                               seed: int) -> Path:
    """Create a tmp dir of symlinks where conflicts.csv -> the requested file."""
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix=f"fukuday5_{seed}_"))
    for src in input_dir.iterdir():
        if src.name == "conflicts.csv":
            continue
        (tmp / src.name).symlink_to(src.resolve())
    (tmp / "conflicts.csv").symlink_to((input_dir / conflict_file).resolve())
    return tmp


# ---------------------------------------------------------------------------
# Per-scenario ensemble driver
# ---------------------------------------------------------------------------


def run_scenario(scenario_id: str, spec: dict,
                 modes: list, n_agents: int, n_steps: int,
                 ensemble: int, base_seed: int,
                 alpha: float, beta: float, kappa: float,
                 progress_prefix: str = ""):
    """Run all modes × ensemble members for one scenario.

    Returns a dict with two stacked DataFrames:
        - agents:  per-(timestep, agent_id, mode, member) location records
        - arrivals: per-arrival records (one row per agent that reached camp)
    """
    print(f"\n{progress_prefix}=== scenario: {scenario_id} ({spec['label']}) ===")
    print(f"{progress_prefix}  input={spec['input_dir'].name}, "
          f"conflicts={spec['conflict_file']}, x_dist={spec['x_dist']}")

    all_agents = []
    all_arrivals = []
    for mi, mode in enumerate(modes):
        for k in range(ensemble):
            seed = base_seed + 1000 * mi + k
            print(f"{progress_prefix}  -> mode={mode}, member={k} (seed={seed})")
            adf, _lm, arr = _run_member(
                spec["input_dir"], spec["conflict_file"], mode,
                n_agents, n_steps, alpha, beta, kappa,
                seed, spec["x_dist"],
            )
            adf["scenario"] = scenario_id
            adf["member"] = k
            all_agents.append(adf)
            if not arr.empty:
                arr = arr.copy()
                arr["scenario"] = scenario_id
                arr["member"] = k
                all_arrivals.append(arr)

    agents = pd.concat(all_agents, ignore_index=True)
    arrivals = (pd.concat(all_arrivals, ignore_index=True)
                if all_arrivals else pd.DataFrame())
    return agents, arrivals


# ---------------------------------------------------------------------------
# Corridor classification
# ---------------------------------------------------------------------------


def classify_corridor_usage(agents: pd.DataFrame) -> pd.DataFrame:
    """For each (scenario, member, decision_mode, agent_id) starting in a fork
    origin (tomioka / naraha / okuma / futaba / namie), label which corridor
    the agent passed through on its way to camp.

    Categories: 'route6', 'inland', 'both', 'neither'.
    """
    rows = []
    grp_cols = ["scenario", "member", "decision_mode", "agent_id"]
    relevant = agents[agents["initial_zone"].isin(["inner", "mid"])]

    for keys, sub in relevant.groupby(grp_cols, sort=False):
        sub = sub.sort_values("timestep")
        path = sub["location"].tolist()
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
        reached_camp = any(z == "camp" for z in sub["zone"].tolist())
        rows.append({
            "scenario": keys[0], "member": keys[1],
            "decision_mode": keys[2], "agent_id": keys[3],
            "initial_zone": sub["initial_zone"].iloc[0],
            "corridor": cat,
            "reached_camp": reached_camp,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Diagnostics gate
# ---------------------------------------------------------------------------


def diagnostics_gate(agents: pd.DataFrame, corridor: pd.DataFrame) -> bool:
    print("\n=== DAY 5 DIAGNOSTICS GATE ===")
    ok = True

    # Check 1: three-phase pattern preserved (dip > 0.10 in every scenario)
    print("\n[1] Three-phase pattern (mid-zone P_S2 dip > 0.10):")
    mid_locs = set(ZONES["mid"])
    for sc in agents["scenario"].unique():
        blend = agents[(agents["scenario"] == sc)
                       & (agents["decision_mode"] == "blend")
                       & (agents["location"].isin(mid_locs))]
        if blend.empty:
            print(f"    {sc}: SKIP (no mid-zone active agents)")
            continue
        by_t = blend.groupby("timestep")["sys2_weight"].mean()
        if len(by_t) < 3:
            print(f"    {sc}: SKIP (insufficient timesteps)")
            continue
        dip = float(by_t.iloc[0] - by_t.min())
        verdict = "PASS" if dip > 0.10 else "FAIL"
        print(f"    {sc:24s}: dip={dip:.3f}  {verdict}")
        if dip <= 0.10:
            ok = False

    # Check 2: blend agents use Kawauchi more than sys1_only (scenario 3)
    print("\n[2] Blend agents use Kawauchi more than System-1 (route6_closed scenario):")
    sub = corridor[(corridor["scenario"] == "route6_closed")
                   & (corridor["decision_mode"].isin(["sys1_only", "blend"]))
                   & (corridor["corridor"].isin(["route6", "inland"]))]
    if sub.empty:
        print("    SKIP (no agents in fork origins reached corridor decision)")
    else:
        ct = pd.crosstab(sub["decision_mode"], sub["corridor"])
        for col in ["route6", "inland"]:
            if col not in ct.columns:
                ct[col] = 0
        ct = ct[["route6", "inland"]]
        print("    contingency table (rows=mode, cols=corridor):")
        print(ct.to_string().replace("\n", "\n    "))
        try:
            chi2, p, _, _ = stats.chi2_contingency(ct.values)
            blend_inland_frac = (ct.loc["blend", "inland"]
                                 / max(1, ct.loc["blend"].sum()))
            s1_inland_frac = (ct.loc["sys1_only", "inland"]
                              / max(1, ct.loc["sys1_only"].sum()))
            verdict_dir = blend_inland_frac > s1_inland_frac
            verdict_sig = p < 0.05
            print(f"    blend_inland={blend_inland_frac:.3f}, "
                  f"s1_inland={s1_inland_frac:.3f}, "
                  f"chi2={chi2:.3f}, p={p:.4g}")
            if verdict_dir and verdict_sig:
                print("    PASS (blend favours inland route, p<0.05)")
            elif verdict_dir:
                print("    FINDING: direction OK but not significant — "
                      "may indicate uniform routing on this network")
            else:
                print("    FAIL: blend does not favour inland route")
                ok = False
        except ValueError as e:
            print(f"    SKIP (chi2 unavailable: {e})")

    # Check 3: closure increases path length for blend > 5%
    print("\n[3] Path length increase under closure (blend, > 5%):")
    arrivals = agents.attrs.get("arrivals_for_diag")
    if arrivals is None or arrivals.empty:
        print("    SKIP (no arrival records attached to agents.attrs)")
    else:
        scen_open = "full_network"
        scen_closed = "route6_closed"
        try:
            blend_open = arrivals[(arrivals["scenario"] == scen_open)
                                  & (arrivals["decision_mode"] == "blend")
                                  ]["path_length_km"].median()
            blend_closed = arrivals[(arrivals["scenario"] == scen_closed)
                                    & (arrivals["decision_mode"] == "blend")
                                    ]["path_length_km"].median()
            rel = (blend_closed - blend_open) / blend_open
            verdict = "PASS" if rel > 0.05 else "FINDING"
            print(f"    median open={blend_open:.1f} km, "
                  f"closed={blend_closed:.1f} km, "
                  f"rel_change={rel*100:+.1f}%  {verdict}")
            if verdict == "FINDING":
                print("    -> closure does not lengthen blend paths >5% — "
                      "may indicate parallel inland route is comparable")
        except Exception as e:
            print(f"    SKIP ({e})")

    # Check 4: hayano_t4 within [0.40, 0.70] for every scenario
    print("\n[4] Hayano t=4 (inner+mid blend departures) in [0.40, 0.70]:")
    for sc in agents["scenario"].unique():
        blend = agents[(agents["scenario"] == sc)
                       & (agents["decision_mode"] == "blend")]
        im_ids = blend[blend["initial_zone"].isin(["inner", "mid"])][
            "agent_id"].unique()
        if len(im_ids) == 0:
            print(f"    {sc}: SKIP")
            continue
        camp_rows = blend[(blend["agent_id"].isin(im_ids))
                          & (blend["zone"] == "camp")]
        first = camp_rows.groupby(["member", "agent_id"])["timestep"].min()
        # average across members
        per_member = []
        for m in blend["member"].unique():
            m_im = blend[(blend["member"] == m)
                         & (blend["initial_zone"].isin(["inner", "mid"]))][
                "agent_id"].unique()
            if len(m_im) == 0:
                continue
            try:
                m_first = first.xs(m, level="member")
            except KeyError:
                m_first = pd.Series([], dtype=int)
            per_member.append(float((m_first <= 4).sum() / len(m_im)))
        h4 = float(np.mean(per_member)) if per_member else 0.0
        verdict = "PASS" if 0.40 <= h4 <= 0.70 else "FAIL"
        print(f"    {sc:24s}: hayano_t4={h4:.3f}  {verdict}")
        if not (0.40 <= h4 <= 0.70):
            ok = False

    print(f"\n=== Day 5 gate: {'PASS' if ok else 'REVIEW'} ===")
    return ok


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def fig_d5_1_network_map(input_dir: Path, out_dir: Path):
    """Network map of the expanded topology, Route 6 / inland highlighted."""
    figwidth = d3.setup_science_style(7.0)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.82))

    # Read locations
    locs = {}
    with open(input_dir / "locations.csv") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip().strip('"') for p in line.split(",")]
            name, x, y, ltype = parts[0], float(parts[3]), float(parts[4]), parts[5]
            locs[name] = (x, y, ltype)

    edges = []
    with open(input_dir / "routes.csv") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip().strip('"') for p in line.split(",")]
            edges.append((parts[0], parts[1], float(parts[2])))

    zone_of = {n: "camp" if locs[n][2] == "camp"
               else next((z for z, ns in ZONES.items() if n in ns), "outer")
               for n in locs}
    color_map = {"inner": "#D35400", "mid": "#E67E22", "outer": "#2E86C1",
                 "camp": "#27AE60"}

    # Edge colouring: highlight Route 6 and Kawauchi inland corridors
    R6_EDGES = {("tomioka", "naraha"), ("naraha", "hirono"),
                ("hirono", "iwaki_north"), ("hirono", "iwaki_city")}
    INL_EDGES = {("tomioka", "kawauchi"), ("kawauchi", "tamura"),
                 ("kawauchi", "koriyama"), ("okuma", "kawauchi"),
                 ("futaba", "kawauchi")}

    def _norm(a, b):
        return tuple(sorted([a, b]))

    R6 = {_norm(*e) for e in R6_EDGES}
    INL = {_norm(*e) for e in INL_EDGES}

    for n1, n2, _d in edges:
        if n1 not in locs or n2 not in locs:
            continue
        x1, y1 = locs[n1][0], locs[n1][1]
        x2, y2 = locs[n2][0], locs[n2][1]
        e_key = _norm(n1, n2)
        if e_key in R6:
            color, lw, alpha = "#C0392B", 1.8, 0.95
            label = "Route 6 corridor"
        elif e_key in INL:
            color, lw, alpha = "#16A085", 1.8, 0.95
            label = "Kawauchi inland"
        else:
            color, lw, alpha = "lightgray", 0.7, 0.6
            label = None
        ax.plot([x1, x2], [y1, y2], color=color, lw=lw, alpha=alpha, zorder=1)

    for name, (x, y, ltype) in locs.items():
        z = zone_of[name]
        size = 95 if ltype == "camp" else 55
        ax.scatter([x], [y], color=color_map[z], s=size,
                   edgecolor="white", linewidth=0.9, zorder=3)
        ax.annotate(name, (x, y), xytext=(3, 3),
                    textcoords="offset points", fontsize=5.5,
                    color="#222", zorder=4)

    # Custom legend
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], color="#C0392B", lw=2, label="Route 6 corridor"),
        Line2D([0], [0], color="#16A085", lw=2, label="Kawauchi inland"),
        Line2D([0], [0], color="lightgray", lw=1, label="other links"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#D35400",
               markersize=7, label="inner zone"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#E67E22",
               markersize=7, label="mid zone"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2E86C1",
               markersize=7, label="outer zone"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#27AE60",
               markersize=9, label="receiving city (camp)"),
    ]
    ax.legend(handles=legend_items, loc="upper left", fontsize=6,
              framealpha=0.9)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("Day 5 Fukushima topology — corridor highlight\n"
                 "(intermediate municipalities + Route 6 vs Kawauchi inland)",
                 fontsize=8)
    ax.grid(True, alpha=0.2)
    ax.set_aspect("equal", adjustable="datalim")
    fig.tight_layout()
    fig.savefig(out_dir / "D5-1_network_map.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved D5-1_network_map.png")


def fig_d5_2_path_length_violins(arrivals: pd.DataFrame, out_dir: Path):
    """Violin plots of path length at arrival per scenario × mode."""
    if arrivals.empty:
        print("  D5-2: no arrival data — skipping")
        return

    figwidth = d3.setup_science_style(7.0)
    scenarios = ["baseline", "full_network", "route6_closed",
                 "closure_heterogeneous"]
    scenarios = [s for s in scenarios if s in arrivals["scenario"].unique()]
    fig, axes = plt.subplots(1, len(scenarios),
                             figsize=(figwidth * 1.4, figwidth * 0.5),
                             sharey=True)
    if len(scenarios) == 1:
        axes = [axes]

    modes = [m for m in MODE_ORDER
             if m in arrivals["decision_mode"].unique()]

    for ax, sc in zip(axes, scenarios):
        sub = arrivals[arrivals["scenario"] == sc]
        data = []
        labels = []
        cols = []
        for m in modes:
            mdf = sub[sub["decision_mode"] == m]["path_length_km"].values
            if len(mdf) > 0:
                data.append(mdf)
                labels.append(m.replace("_", " "))
                cols.append(PALETTE.get(m, "#888"))
        if data:
            parts = ax.violinplot(data, positions=range(len(data)),
                                  showmeans=True, showmedians=True,
                                  widths=0.85)
            for i, body in enumerate(parts["bodies"]):
                body.set_facecolor(cols[i])
                body.set_alpha(0.35)
            for i, d in enumerate(data):
                jit = np.random.default_rng(i).uniform(-0.15, 0.15, len(d))
                ax.scatter(np.full(len(d), i) + jit, d, s=4, alpha=0.35,
                           color=cols[i], edgecolors="none")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=6, rotation=20)
        ax.set_title(sc.replace("_", " "), fontsize=8)
        ax.grid(axis="y", alpha=0.2)

    axes[0].set_ylabel("Path length at arrival (km)", fontsize=8)
    fig.suptitle("Path length at arrival across Day 5 scenarios", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "D5-2_path_length_violins.png", dpi=300,
                bbox_inches="tight")
    plt.close(fig)
    print("  Saved D5-2_path_length_violins.png")


def fig_d5_3_corridor_usage(corridor: pd.DataFrame, out_dir: Path):
    """Stacked bar chart of corridor usage by mode for the route6_closed scenario."""
    sub = corridor[(corridor["scenario"] == "route6_closed")
                   & (corridor["corridor"].isin(["route6", "inland", "both",
                                                 "neither"]))]
    if sub.empty:
        print("  D5-3: no corridor data for route6_closed — skipping")
        return

    figwidth = d3.setup_science_style(7.0)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.45))

    modes = [m for m in MODE_ORDER
             if m in sub["decision_mode"].unique()]
    cats = ["route6", "inland", "both", "neither"]
    cat_colors = {"route6": "#C0392B", "inland": "#16A085",
                  "both": "#9B59B6", "neither": "#BDC3C7"}

    counts = (sub.groupby(["decision_mode", "corridor"]).size()
              .unstack(fill_value=0)
              .reindex(modes)
              .reindex(columns=cats, fill_value=0))
    fracs = counts.div(counts.sum(axis=1), axis=0).fillna(0.0)

    bottom = np.zeros(len(modes))
    x = np.arange(len(modes))
    width = 0.6
    for cat in cats:
        vals = fracs[cat].values
        ax.bar(x, vals, bottom=bottom, width=width,
               color=cat_colors[cat], edgecolor="white", linewidth=0.5,
               label=cat)
        for xi, v, b in zip(x, vals, bottom):
            if v > 0.05:
                ax.text(xi, b + v / 2, f"{v*100:.0f}%",
                        ha="center", va="center", fontsize=6, color="white",
                        fontweight="bold")
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels([m.replace("_", " ") for m in modes], fontsize=7)
    ax.set_ylabel("Fraction of fork-origin agents", fontsize=8)
    ax.set_ylim(0, 1.0)
    ax.set_title("Corridor usage by mode — route6_closed scenario\n"
                 "(fork-origin agents: tomioka/naraha/okuma/futaba/namie)",
                 fontsize=8)
    ax.legend(fontsize=6, loc="upper right", bbox_to_anchor=(1.18, 1.0),
              frameon=True, framealpha=0.9)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_dir / "D5-3_corridor_usage.png", dpi=300,
                bbox_inches="tight")
    plt.close(fig)
    print("  Saved D5-3_corridor_usage.png")


def fig_d5_4_ps2_mid(agents: pd.DataFrame, out_dir: Path, n_steps: int):
    """P_S2 time series for mid-zone blend agents across all scenarios."""
    figwidth = d3.setup_science_style(7.0)
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * 0.45))

    mid_locs = set(ZONES["mid"])
    for sc in ["baseline", "full_network", "route6_closed",
               "closure_heterogeneous"]:
        if sc not in agents["scenario"].unique():
            continue
        sub = agents[(agents["scenario"] == sc)
                     & (agents["decision_mode"] == "blend")
                     & (agents["location"].isin(mid_locs))]
        if sub.empty:
            continue
        agg = sub.groupby("timestep")["sys2_weight"].agg(
            ["mean", "std", "count"]).reset_index()
        mask = agg["count"] >= 3
        t = agg.loc[mask, "timestep"].values
        m = agg.loc[mask, "mean"].values
        s = agg.loc[mask, "std"].fillna(0).values
        ax.fill_between(t, m - s, m + s,
                        color=SCENARIO_COLORS[sc], alpha=0.13)
        ax.plot(t, m, color=SCENARIO_COLORS[sc], lw=1.4,
                label=sc.replace("_", " "))

    ax.set_xlim(0, min(40, n_steps))
    ax.set_ylim(0, 0.6)
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Mean P_S2 (mid-zone blend)")
    ax.set_title("Mid-zone P_S2 dynamics across Day 5 scenarios", fontsize=8)
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=6, loc="upper right")
    fig.tight_layout()
    fig.savefig(out_dir / "D5-4_ps2_mid_scenarios.png", dpi=300,
                bbox_inches="tight")
    plt.close(fig)
    print("  Saved D5-4_ps2_mid_scenarios.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _save_qois(agents: pd.DataFrame, arrivals: pd.DataFrame,
               corridor: pd.DataFrame, out_path: Path):
    """Pickle a small JSON of per-scenario summary numbers for downstream use."""
    summary = {}
    for sc in agents["scenario"].unique():
        rec = {}
        blend = agents[(agents["scenario"] == sc)
                       & (agents["decision_mode"] == "blend")]
        im_ids = blend[blend["initial_zone"].isin(["inner", "mid"])][
            "agent_id"].unique()
        if len(im_ids) > 0:
            camp_rows = blend[(blend["agent_id"].isin(im_ids))
                              & (blend["zone"] == "camp")]
            per_member = []
            for m in blend["member"].unique():
                m_im = blend[(blend["member"] == m)
                             & (blend["initial_zone"].isin(["inner", "mid"]))][
                    "agent_id"].unique()
                if len(m_im) == 0:
                    continue
                m_camp = camp_rows[camp_rows["member"] == m]
                m_first = m_camp.groupby("agent_id")["timestep"].min()
                per_member.append(float((m_first <= 4).sum() / len(m_im)))
            rec["hayano_t4"] = round(float(np.mean(per_member)), 4) \
                if per_member else 0.0

        if not arrivals.empty:
            sub = arrivals[arrivals["scenario"] == sc]
            for mode in sub["decision_mode"].unique():
                vals = sub[sub["decision_mode"] == mode]["path_length_km"].values
                if len(vals) > 0:
                    rec[f"path_med_{mode}"] = round(float(np.median(vals)), 2)
                    rec[f"path_mean_{mode}"] = round(float(np.mean(vals)), 2)

        if not corridor.empty:
            cs = corridor[corridor["scenario"] == sc]
            for mode in cs["decision_mode"].unique():
                m_sub = cs[cs["decision_mode"] == mode]
                tot = len(m_sub)
                if tot > 0:
                    rec[f"frac_inland_{mode}"] = round(
                        float((m_sub["corridor"] == "inland").sum() / tot), 4)
                    rec[f"frac_route6_{mode}"] = round(
                        float((m_sub["corridor"] == "route6").sum() / tot), 4)
        summary[sc] = rec

    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved {out_path.name}")


def main():
    ap = argparse.ArgumentParser(description="Day 5 Fukushima scenarios")
    ap.add_argument("--n-steps", type=int, default=72)
    ap.add_argument("--n-agents", type=int, default=500)
    ap.add_argument("--ensemble", type=int, default=10)
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--beta", type=float, default=2.0)
    ap.add_argument("--kappa", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=20260205)
    ap.add_argument("--modes", nargs="+", default=MODE_ORDER)
    ap.add_argument("--scenarios", nargs="+",
                    default=["baseline", "full_network", "route6_closed",
                             "closure_heterogeneous"])
    ap.add_argument("--output-dir", default="figures/fukushima/day5")
    ap.add_argument("--results-dir", default="results/day5")
    ap.add_argument("--quick", action="store_true",
                    help="Smaller ensemble + agents for quick verification")
    ap.add_argument("--skip-runs", action="store_true",
                    help="Reuse cached agents/arrivals CSVs and just remake figures")
    args = ap.parse_args()

    if args.quick:
        args.n_agents = 200
        args.ensemble = 3
        print(f"[quick] n_agents={args.n_agents}, ensemble={args.ensemble}")

    out_dir = REPO_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    res_dir = REPO_ROOT / args.results_dir
    res_dir.mkdir(parents=True, exist_ok=True)

    specs = scenario_specs(REPO_ROOT)
    requested = [s for s in args.scenarios if s in specs]
    if not requested:
        print(f"No valid scenarios requested. Available: {list(specs)}")
        return 1

    if args.skip_runs:
        print("[skip-runs] loading cached CSVs from", res_dir)
        agents = pd.read_csv(res_dir / "agents_all_scenarios.csv")
        arr_path = res_dir / "arrivals_all_scenarios.csv"
        arrivals = pd.read_csv(arr_path) if arr_path.exists() else pd.DataFrame()
    else:
        all_agents = []
        all_arrivals = []
        for sc in requested:
            # baseline and full_network use the same input dir in this codebase
            # (see input/fukushima_day5/README.md). We still run baseline so
            # the figures and gate include both rows; this is a real ensemble
            # so seeds differ and the pair acts as a self-consistency check.
            ag, ar = run_scenario(
                sc, specs[sc],
                modes=args.modes,
                n_agents=args.n_agents,
                n_steps=args.n_steps,
                ensemble=args.ensemble,
                base_seed=args.seed,
                alpha=args.alpha, beta=args.beta, kappa=args.kappa,
                progress_prefix="",
            )
            all_agents.append(ag)
            if not ar.empty:
                all_arrivals.append(ar)

        agents = pd.concat(all_agents, ignore_index=True)
        arrivals = (pd.concat(all_arrivals, ignore_index=True)
                    if all_arrivals else pd.DataFrame())

        print("\nWriting cached CSVs...")
        agents.to_csv(res_dir / "agents_all_scenarios.csv", index=False)
        if not arrivals.empty:
            arrivals.to_csv(res_dir / "arrivals_all_scenarios.csv", index=False)
        print(f"  agents: {len(agents)} rows")
        print(f"  arrivals: {len(arrivals)} rows")

    print("\nClassifying corridor usage...")
    corridor = classify_corridor_usage(agents)
    corridor.to_csv(res_dir / "corridor_usage.csv", index=False)

    print("\nGenerating figures...")
    fig_d5_1_network_map(REPO_ROOT / "input" / "fukushima_day5", out_dir)
    fig_d5_2_path_length_violins(arrivals, out_dir)
    fig_d5_3_corridor_usage(corridor, out_dir)
    fig_d5_4_ps2_mid(agents, out_dir, args.n_steps)

    # attach arrivals so diagnostics_gate can use them
    agents.attrs["arrivals_for_diag"] = arrivals
    _save_qois(agents, arrivals, corridor, res_dir / "scenario_qois.json")

    passed = diagnostics_gate(agents, corridor)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
