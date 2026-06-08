#!/usr/bin/env python3
"""Day 11 TMI diagnostics gate — writes results/tmi/diagnostics_gate_day11.json"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"
SMOKE = REPO / "results" / "tmi" / "smoke_test"
FIG = REPO / "figures" / "tmi"
EMP = FIG / "empirical"
FIG_SCRIPT = REPO / "scripts" / "plot_tmi_empirical_figures_day11.py"

FORBIDDEN = ("46.8", "13.72", "0.003")


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}


def main() -> None:
    results = []
    # JSON
    emp_path = TMI / "tmi_empirical_data.json"
    try:
        d = json.loads(emp_path.read_text(encoding="utf-8"))
        results.append(_check("tmi_empirical_data.json valid JSON", True))
    except Exception as e:
        results.append(_check("tmi_empirical_data.json valid JSON", False, str(e)))
        d = {}

    nq = len(d.get("flee_model_qois_summary", {}).get("primary_qois", []))
    results.append(_check("8 primary QoIs", nq == 8, f"count={nq}"))

    # Locations
    with (TMI / "locations.csv").open(encoding="utf-8") as f:
        loc_rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    results.append(_check("15 location rows (12 towns + 3 camps)", len(loc_rows) == 15))

    with (TMI / "routes.csv").open(encoding="utf-8") as f:
        rte_rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    results.append(_check("18 route rows (spec+1 split for New Cumberland)", len(rte_rows) == 18))

    # Conflicts
    with (TMI / "conflicts.csv").open(encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header = [h.strip().lstrip("#") for h in rows[0]]
    body = [r for r in rows[1:] if r]
    uniform_ok = True
    c10_ok = True
    c16_ok = True
    for r in body:
        t = int(r[0])
        vals = [float(x) for x in r[1:]]
        if len(set(vals)) != 1:
            uniform_ok = False
        if t == 10 and abs(vals[0] - 1.0) > 1e-6:
            c10_ok = False
        if t == 16 and vals[0] > 0.10 + 1e-6:
            c16_ok = False
    results.append(_check("conflicts.csv present", len(body) >= 20))
    results.append(_check("spatial uniformity (population nodes)", uniform_ok))
    results.append(_check("c(t=10)==1.00", c10_ok))
    results.append(_check("c(t=16)<=0.10", c16_ok))

    sched = json.loads((TMI / "conflict_schedule_tmi.json").read_text(encoding="utf-8"))
    results.append(_check("conflict_schedule omega_type", "omega_type" in sched))

    results.append(_check("psi_initialization_note.txt", (TMI / "psi_initialization_note.txt").exists()))

    # Smoke
    smoke_ok = (SMOKE / "agent_counts.csv").exists() and (SMOKE / "departure_rates.csv").exists()
    results.append(_check("smoke CSV outputs exist", smoke_ok))

    dep_spike = False
    at_camp_frac = 0.0
    if smoke_ok:
        df = pd.read_csv(SMOKE / "departure_rates.csv")
        rates = df["departure_rate"].tolist()
        win = max(rates[8:13]) if len(rates) >= 13 else 0.0
        dep_spike = win > rates[5] if len(rates) > 10 else False
        results.append(
            _check(
                "advisory-window mobility > t=5",
                dep_spike,
                f"max(t=8..12)={win:.4f} vs t=5={rates[5]:.4f}",
            )
        )
        ac = pd.read_csv(SMOKE / "agent_counts.csv")
        last_t = int(ac["timestep"].max())
        last_rep = int(ac["replication"].max())
        row = ac[(ac["timestep"] == last_t) & (ac["replication"] == last_rep)].iloc[0]
        camps = {"harrisburg_camp", "lancaster_camp", "york_camp"}
        camp_cols = [c for c in row.index if c in camps]
        loc_cols = [c for c in row.index if c not in ("timestep", "replication")]
        tot = float(row[loc_cols].sum())
        at_camp = float(row[camp_cols].sum())
        at_camp_frac = at_camp / max(1.0, tot)
        results.append(
            _check(
                "agents mostly in camps by t=20",
                at_camp_frac >= 0.95,
                f"fraction={at_camp_frac:.3f}",
            )
        )

    for stem in ["day11_network_map_osm.png", "day11_network_map_static.png"]:
        results.append(_check(f"figure {stem}", (FIG / stem).exists()))
    gnames = [
        "G1_zeigler_paradox.png",
        "G2_stress_curves_omega.png",
        "G3_multi_panel_summary.png",
        "G4_model_comparison.png",
        "G5_education_zone_heatmap.png",
        "G6_destination_map.png",
    ]
    for gn in gnames:
        results.append(_check(f"empirical {gn}", (EMP / gn).exists()))

    # Grep forbidden literals in figure script
    text = FIG_SCRIPT.read_text(encoding="utf-8")
    bad = [s for s in FORBIDDEN if s in text]
    results.append(_check("no forbidden hardcoded literals in figure script", len(bad) == 0, str(bad)))

    # pytest
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=600,
        )
        # accept 84 passed 2 skipped pattern loosely
        ok = proc.returncode == 0
        results.append(_check("pytest tests/", ok, proc.stdout[-500:] if proc.stdout else proc.stderr[-500:]))
    except Exception as e:
        results.append(_check("pytest tests/", False, str(e)))

    summary = {
        "checks": results,
        "pass_count": sum(1 for r in results if r["status"] == "PASS"),
        "fail_count": sum(1 for r in results if r["status"] == "FAIL"),
    }
    out_path = REPO / "results" / "tmi" / "diagnostics_gate_day11.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
