#!/usr/bin/env python3
"""Day 12 TMI diagnostics gate — extends the Day 11 gate (23 checks) with
checks 24-30. Writes results/tmi/diagnostics_gate_day12.json.

The 23 Day-11 checks are re-run via the Day 11 gate (which also runs pytest).
Day 12 analysis artifacts are produced on demand (run-if-missing) so the gate is
reproducible from a clean tree, then validated.

Honesty policy (per prompt): a failing new check is reported with its value, not
silently relaxed. Check 26 (total evac in [15%,30%]) is expected to FAIL at
frozen Fukushima parameters — the model over-mobilises TMI (CMC non-transfer).
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"
RESULTS = REPO / "results" / "tmi"
FIG = REPO / "figures" / "tmi"
SCRIPTS = REPO / "scripts"
LOGS = RESULTS / "logs"

PY = sys.executable


def _check(name, ok, detail=""):
    return {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}


def _run_script(script, primary_output, force=False):
    """Run a Day 12 script (output to log) if its primary output is missing."""
    if primary_output.exists() and not force:
        return True, "cached"
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / (Path(script).stem + ".log")
    with log.open("w") as fh:
        proc = subprocess.run([PY, str(script)], cwd=str(REPO),
                              stdout=fh, stderr=subprocess.STDOUT, timeout=1200)
    return proc.returncode == 0, f"ran (rc={proc.returncode}, log={log.name})"


def main() -> None:
    results = []

    # --- Inherited Day 11 gate (23 checks + pytest) ----------------------
    day11_gate = SCRIPTS / "run_diagnostics_gate_day11.py"
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / "gate_day11.log").open("w") as fh:
        subprocess.run([PY, str(day11_gate)], cwd=str(REPO),
                       stdout=fh, stderr=subprocess.STDOUT, timeout=1200)
    d11 = json.loads((RESULTS / "diagnostics_gate_day11.json").read_text())
    d11_pass = d11["pass_count"]
    d11_fail = d11["fail_count"]
    day11_all_ok = (d11_fail == 0)
    results.append(_check(
        f"Day 11 gate inherited ({d11_pass} checks)",
        day11_all_ok, f"pass={d11_pass} fail={d11_fail}"))

    # Ensure Day 12 analysis artifacts exist (run-if-missing).
    _run_script(SCRIPTS / "run_tmi_day12_first_run.py",
                RESULTS / "day12_first_run_qoi_table.csv")
    _run_script(SCRIPTS / "run_tmi_day12_ps2_zones.py",
                RESULTS / "day12_ps2_zones.csv")
    _run_script(SCRIPTS / "run_tmi_day12_zeigler.py",
                RESULTS / "day12_zeigler_metric.csv")
    _run_script(SCRIPTS / "plot_tmi_day12_ps2_figure.py",
                FIG / "day12_ps2_zones.png")

    # --- Check 24: OSM distances updated --------------------------------
    osm_csv = TMI / "routes_osm_day12.csv"
    backup = TMI / "routes_handcurated_day11.csv"
    diff_count = 0
    if osm_csv.exists() and backup.exists():
        def _dist_map(p):
            m = {}
            with p.open() as f:
                for r in csv.reader(f):
                    if not r or r[0].startswith("#"):
                        continue
                    m[(r[0], r[1])] = float(r[2])
            return m
        new_d, old_d = _dist_map(osm_csv), _dist_map(backup)
        diff_count = sum(1 for k in new_d if abs(new_d[k] - old_d.get(k, new_d[k])) > 1e-6)
    c24 = osm_csv.exists() and backup.exists() and diff_count >= 1
    results.append(_check("24 OSM distances updated (orig preserved, >=1 differs)",
                          c24, f"differs={diff_count}, backup={backup.exists()}"))

    # --- Check 25: QoI table generated ----------------------------------
    qoi_path = RESULTS / "day12_first_run_qoi_table.csv"
    c25 = False
    d25 = ""
    if qoi_path.exists():
        q = pd.read_csv(qoi_path)
        n_modes = q["mode"].nunique()
        n_qois = q["qoi_name"].nunique()
        has_cols = {"model_mean", "model_std"}.issubset(q.columns)
        c25 = (n_modes == 4) and (n_qois >= 6) and has_cols
        d25 = f"modes={n_modes}, qois={n_qois}, mean&std={has_cols}"
    results.append(_check("25 QoI table (4 modes x >=6 QoIs, mean & std)", c25, d25))

    # --- Check 26: total evac (mixture) in [15%,30%] of 20-mi pop --------
    summ = json.loads((RESULTS / "day12_first_run_summary.json").read_text())
    evac = float(summ["total_evac_rate_20mi_mean"])
    c26 = 0.15 <= evac <= 0.30
    if c26:
        d26 = f"evac={evac:.3f} in [0.15,0.30]"
    else:
        d26 = (f"evac={evac:.3f} OUT of [0.15,0.30] — frozen Fukushima CMC "
               "over-mobilises TMI (expected; Day 14 recalibration / Day 16)")
    results.append(_check(
        "26 total evac (mixture) in [15%,30%] of 20-mi pop", c26, d26))

    # --- Check 27: advisory-window mobility spike (mixture) -------------
    c27 = float(summ["mobility_t10"]) > float(summ["mobility_t5"])
    results.append(_check(
        "27 advisory mobility spike (mixture t10 > t5)", c27,
        f"t10={summ['mobility_t10']:.3f} vs t5={summ['mobility_t5']:.3f}"))

    # --- Check 28: zone P_S2 spread LOW ---------------------------------
    sp = json.loads((RESULTS / "day12_ps2_spread_summary.json").read_text())
    tmi_spread = float(sp["tmi_zone_ps2_spread_t10"])
    fuk = sp.get("fukushima_indicative_spread_day3")
    if fuk:
        c28 = tmi_spread < fuk
        d28 = f"tmi={tmi_spread:.4f} < fukushima(day3 indicative)={fuk:.4f}"
    else:
        c28 = tmi_spread < 0.15
        d28 = f"tmi={tmi_spread:.4f} < 0.15 (Fukushima ref NA, flagged Day 16)"
    results.append(_check("28 zone P_S2 spread LOW", c28, d28))

    # --- Check 29: Zeigler metric computed ------------------------------
    zpath = RESULTS / "day12_zeigler_metric.csv"
    c29 = False
    d29 = ""
    if zpath.exists():
        z = pd.read_csv(zpath)
        need = {"zone", "arrival_fraction", "mean_departure_t", "path_mean"}
        c29 = need.issubset(z.columns) and set(z["zone"]) >= {"inner", "middle", "outer"}
        d29 = f"zones={sorted(set(z['zone']))}, cols_ok={need.issubset(z.columns)}"
    results.append(_check("29 Zeigler metric (arrival+departure+path by zone)", c29, d29))

    # --- Check 30: P_S2 figure generated --------------------------------
    fig_path = FIG / "day12_ps2_zones.png"
    results.append(_check("30 P_S2 figure generated", fig_path.exists(),
                          str(fig_path.name)))

    # Compose. The "30/30" total counts the 23 inherited + 7 new; report the
    # inherited block as one umbrella check but expand the count for clarity.
    new_pass = sum(1 for r in results[1:] if r["status"] == "PASS")
    new_fail = sum(1 for r in results[1:] if r["status"] == "FAIL")
    total_checks = d11_pass + d11_fail + len(results[1:])
    total_pass = d11_pass + new_pass
    total_fail = d11_fail + new_fail

    summary = {
        "day11_inherited": {"pass": d11_pass, "fail": d11_fail},
        "day12_new_checks": results[1:],
        "umbrella_check_list": results,
        "new_pass": new_pass, "new_fail": new_fail,
        "total_checks": total_checks,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "verdict": f"{total_pass}/{total_checks} PASS",
        "known_expected_failures": (
            ["26 total evac in [15,30]: frozen Fukushima CMC over-mobilises TMI "
             f"(model evac {evac * 100:.1f}%); expected cross-domain finding, "
             "addressed in Day 14 recalibration / Day 16 comparison."]
            if not c26 else []),
    }
    (RESULTS / "diagnostics_gate_day12.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
