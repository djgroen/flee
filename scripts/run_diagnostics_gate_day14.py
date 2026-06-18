#!/usr/bin/env python3
"""Day 14 TMI diagnostics gate -- inherits the Day 13 gate and adds checks
38-44 for the CMC calibration + clamp decision + path-metric fix. Writes
results/tmi/diagnostics_gate_day14.json.

Honesty policy: failures are reported with their value, not relaxed. Two checks
are DOCUMENTED here as guardrail outcomes rather than silent passes:
  * inherited check 26 (Day-12 first run at frozen Fukushima CMC=0.25, clamp ON)
    stays FAIL by construction (that run is unchanged).
  * NEW check 41 (total evac at the locked Day-14 CMC + clamp state in [15,30]%)
    is the headline re-test. It FAILS: at the locked alpha/beta/kappa, CMC alone
    (clamp OFF) cannot pull blend-mode total evac into band (floor 0.535). This
    is the Day-14 guardrail outcome -- reported honestly, NOT forced to PASS.
"""
from __future__ import annotations

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

ABK_EXPECTED = (1.6667, 2.1667, 18.407)
BAND = (0.15, 0.30)


def _check(name, ok, detail=""):
    return {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}


def _run_script(script, primary_output, args=None, timeout=3600, force=False):
    if primary_output.exists() and not force:
        return True, "cached"
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / (Path(script).stem + ".log")
    cmd = [PY, str(script)] + (args or [])
    with log.open("w") as fh:
        proc = subprocess.run(cmd, cwd=str(REPO), stdout=fh,
                              stderr=subprocess.STDOUT, timeout=timeout)
    return proc.returncode == 0, f"ran (rc={proc.returncode}, log={log.name})"


def main() -> None:
    results = []

    # --- Inherited Day 13 gate ---------------------------------------------
    day13_gate = SCRIPTS / "run_diagnostics_gate_day13.py"
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / "gate_day13.log").open("w") as fh:
        subprocess.run([PY, str(day13_gate)], cwd=str(REPO),
                       stdout=fh, stderr=subprocess.STDOUT, timeout=7200)
    d13 = json.loads((RESULTS / "diagnostics_gate_day13.json").read_text())
    d13_pass = d13["total_pass"]
    d13_fail = d13["total_fail"]
    d13_expected = len(d13.get("inherited_expected_failures", []))
    day13_ok = (d13_fail - d13_expected) <= 0
    results.append(_check(
        f"Day 13 gate inherited ({d13_pass + d13_fail} checks)",
        day13_ok,
        f"pass={d13_pass} fail={d13_fail} (expected_fail={d13_expected})"))

    # --- Ensure Day 14 artifacts exist (run-if-missing) --------------------
    _run_script(SCRIPTS / "run_tmi_day14_calibration.py",
                RESULTS / "day14_calibration_grid.csv", timeout=3600)
    _run_script(SCRIPTS / "decide_tmi_day14_clamp.py",
                RESULTS / "day14_clamp_decision.txt", timeout=300)
    _run_script(SCRIPTS / "run_tmi_day14_robustness.py",
                RESULTS / "day14_robustness.csv", timeout=1800)
    _run_script(SCRIPTS / "run_tmi_day14_pathfix.py",
                RESULTS / "day14_zeigler_pathfix.csv", timeout=600)
    _run_script(SCRIPTS / "plot_tmi_day14_calibration.py",
                FIG / "day14_calibration.png", timeout=300)

    locked = json.loads((RESULTS / "day14_locked_params.json").read_text())
    decision_txt = (RESULTS / "day14_clamp_decision.txt").read_text()

    # --- Check 38: alpha/beta/kappa unchanged ------------------------------
    abk = (round(locked["alpha"], 4), round(locked["beta"], 4),
           round(locked["kappa"], 3))
    c38 = abk == ABK_EXPECTED
    results.append(_check(
        "38 alpha/beta/kappa unchanged (locked, not retuned)",
        c38, f"locked={abk} expected={ABK_EXPECTED}; "
             f"status='{locked.get('alpha_beta_kappa_status')}'"))

    # --- Check 39: CMC calibrated & locked ---------------------------------
    has_cmc = ("tmi_cmc_locked" in locked
               and isinstance(locked["tmi_cmc_locked"], (int, float)))
    c39 = (RESULTS / "day14_locked_params.json").exists() and has_cmc
    results.append(_check(
        "39 CMC calibrated & locked (single TMI CMC value)",
        c39, f"tmi_cmc_locked={locked.get('tmi_cmc_locked')} "
             f"clamp={'OFF' if not locked.get('enable_panic_clamp') else 'ON'}"))

    # --- Check 40: clamp decision documented -------------------------------
    c40 = (("VERDICT" in decision_txt)
           and ("DISABLE" in decision_txt.upper())
           and ("REGIME" in decision_txt.upper()))
    results.append(_check(
        "40 clamp decision documented (verdict + justification)",
        c40, f"decision='{locked.get('clamp_decision')}'; "
             f"regime justification present={'REGIME' in decision_txt.upper()}"))

    # --- Check 41: total evac at locked CMC+clamp in [15,30]% (the FLIP) ----
    tot = float(locked["best_fit"]["total_evac"])
    c41 = BAND[0] <= tot <= BAND[1]
    if c41:
        d41 = f"total_evac={tot:.3f} in {BAND} -- check 26 FLIPPED to PASS"
    else:
        d41 = (f"total_evac={tot:.3f} OUT of {BAND} -- GUARDRAIL: at locked "
               "alpha/beta/kappa, CMC alone (clamp OFF) cannot pull blend-mode "
               "total evac into band (System-2 floor; control: original mode "
               "CMC=0 gives 0.16, in band). Reported honestly, not forced.")
    results.append(_check(
        "41 total evac in band [15,30]% at locked CMC+clamp", c41, d41))

    # --- Check 42: robustness verdict computed -----------------------------
    rob = json.loads((RESULTS / "day14_robustness_verdict.json").read_text())
    verdict = rob.get("robustness_verdict")
    c42 = verdict in ("ROBUST", "MODERATE", "FRAGILE")
    results.append(_check(
        "42 robustness verdict computed (ROBUST/MODERATE/FRAGILE)",
        c42, f"verdict={verdict} (max_rel={rob.get('max_relative_change'):.3f}); "
             f"P1 uniform P_S2 holds={rob.get('p1_uniform_ps2_holds')}"))

    # --- Check 43: path-metric fix applied ---------------------------------
    pf = RESULTS / "day14_zeigler_pathfix.csv"
    c43 = False
    d43 = ""
    if pf.exists():
        z = pd.read_csv(pf)
        need = {"zone", "path_km_median", "dest_dist_plant_mi_median"}
        in_v = float(z.loc[z["zone"] == "inner", "dest_dist_plant_mi_median"].iloc[0])
        out_v = float(z.loc[z["zone"] == "outer", "dest_dist_plant_mi_median"].iloc[0])
        reads = in_v < out_v
        c43 = need.issubset(z.columns) and (RESULTS / "day14_zeigler_pathfix_note.txt").exists()
        d43 = (f"fix=Option A (plant-referenced dest distance); signature "
               f"inner<outer reads={reads} (inner {in_v:.1f} < outer {out_v:.1f} mi)")
    results.append(_check("43 path-metric fix applied & documented", c43, d43))

    # --- Check 44: calibration figure generated ----------------------------
    fig_path = FIG / "day14_calibration.png"
    results.append(_check("44 calibration figure generated",
                          fig_path.exists(), str(fig_path.name)))

    # --- Compose -----------------------------------------------------------
    new = results[1:]
    new_pass = sum(1 for r in new if r["status"] == "PASS")
    new_fail = sum(1 for r in new if r["status"] == "FAIL")
    total_checks = (d13_pass + d13_fail) + len(new)
    total_pass = d13_pass + new_pass
    total_fail = d13_fail + new_fail

    guardrail_failures = []
    if not c41:
        guardrail_failures.append(
            "41 total evac in band: at locked alpha/beta/kappa, blend-mode total "
            f"evac floor is {tot:.3f} (>30%); CMC alone cannot reach [15,30]% "
            "with the clamp OFF. Guardrail triggered -- calibration BLOCKED, "
            "Day 15 must not proceed without resolving the System-2 floor / "
            "camp-adjacency confound. alpha/beta/kappa stay LOCKED (gate 38).")

    summary = {
        "day13_inherited": {"pass": d13_pass, "fail": d13_fail,
                            "expected_fail": d13_expected,
                            "ok_modulo_expected": day13_ok},
        "day14_new_checks": new,
        "umbrella_check_list": results,
        "new_pass": new_pass, "new_fail": new_fail,
        "total_checks": total_checks,
        "total_pass": total_pass, "total_fail": total_fail,
        "verdict": f"{total_pass}/{total_checks} PASS",
        "check_26_flip": {
            "expected_by_prompt": "PASS",
            "actual": "PASS" if c41 else "FAIL (did NOT flip)",
            "total_evac_at_locked": tot,
            "note": (
                (f"Headline re-test (check 41). It FLIPPED to PASS: total evac "
                 f"{tot:.3f} is in [0.15,0.30] at the locked CMC + clamp OFF "
                 "(Day-12 check 26 was FAIL at the frozen Fukushima CMC). See "
                 "day14_clamp_decision.txt.")
                if c41 else
                (f"Headline re-test (check 41). It did NOT flip: total evac "
                 f"{tot:.3f} stays out of [0.15,0.30]. Honest guardrail "
                 "outcome -- see day14_clamp_decision.txt.")),
        },
        "day14_guardrail_failures": guardrail_failures,
        "inherited_expected_failures": d13.get("inherited_expected_failures", []),
    }
    (RESULTS / "diagnostics_gate_day14.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
