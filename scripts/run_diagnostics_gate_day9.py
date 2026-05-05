#!/usr/bin/env python3
"""Day 9 acceptance gate.

Checks (per Day 9 spec):

  [PASS/FAIL] kappa_verdict.json present with valid verdict field
  [PASS/FAIL] flat_onset_kappa recorded (regardless of verdict)
  [PASS/FAIL] paper_language field populated in kappa_verdict.json
  [PASS/FAIL] cmc_robustness_verdict.json present with valid stability_verdict
  [PASS/FAIL] consistency_check_passed = True
  [PASS/FAIL] stability_verdict is STABLE or MODERATE (SENSITIVE = FAIL)
  [PASS/FAIL] paper_language field populated in cmc_robustness_verdict.json
  [PASS/FAIL] if Task A verdict=UPDATED: day9_kappa_update in stage2_params_v2.json
  [PASS/FAIL] all Day 9 figures present in figures/fukushima/day9/
  [PASS/FAIL] pytest tests/ passes (84 passed, 2 skipped)

Writes results/day9/diagnostics_gate_day9.json and exits non-zero on hard
failure.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES_D8 = REPO / "results" / "day8"
RES_D9 = REPO / "results" / "day9"
FIG_D9 = REPO / "figures" / "fukushima" / "day9"

VALID_KAPPA_VERDICTS = {"FLAT", "CONFIRMED", "UPDATED"}
VALID_STABILITY = {"STABLE", "MODERATE"}  # SENSITIVE => FAIL


def _check(label: str, cond: bool, detail: str = "") -> dict:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}" + (f"  -- {detail}" if detail else ""))
    return {"label": label, "status": status, "passed": bool(cond),
            "detail": detail}


def _run_pytest() -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pytest", "tests/", "--no-header", "-q"]
    print(f"  [run]  {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True,
                              text=True, timeout=900)
    except Exception as exc:  # noqa: BLE001
        return False, f"pytest invocation failed: {exc!r}"
    out = (proc.stdout or "") + (proc.stderr or "")
    tail = "\n".join(out.strip().splitlines()[-20:])
    return proc.returncode == 0, tail


def main():
    print("=" * 72)
    print("Day 9 diagnostics gate")
    print("=" * 72)
    results: list[dict] = []

    kv_path = RES_D9 / "kappa_verdict.json"
    cv_path = RES_D9 / "cmc_robustness_verdict.json"

    kv = None
    if kv_path.exists():
        try:
            kv = json.loads(kv_path.read_text())
        except Exception as exc:  # noqa: BLE001
            kv = None
            print(f"  [WARN] kappa_verdict.json parse error: {exc!r}")

    results.append(_check(
        "kappa_verdict.json present with valid verdict field",
        kv is not None and kv.get("verdict") in VALID_KAPPA_VERDICTS,
        f"verdict = {kv.get('verdict') if kv else None}",
    ))

    fok = kv.get("flat_onset_kappa") if kv else None
    results.append(_check(
        "flat_onset_kappa recorded (regardless of verdict)",
        isinstance(fok, (int, float)),
        f"flat_onset_kappa = {fok}",
    ))

    pl_kv = kv.get("paper_language") if kv else None
    results.append(_check(
        "paper_language populated in kappa_verdict.json",
        isinstance(pl_kv, str) and len(pl_kv.strip()) > 20,
        f"len = {len(pl_kv) if isinstance(pl_kv, str) else 0}",
    ))

    cv = None
    if cv_path.exists():
        try:
            cv = json.loads(cv_path.read_text())
        except Exception as exc:  # noqa: BLE001
            cv = None
            print(f"  [WARN] cmc_robustness_verdict.json parse error: "
                  f"{exc!r}")

    results.append(_check(
        "cmc_robustness_verdict.json present with valid stability_verdict",
        cv is not None
        and cv.get("stability_verdict") in (VALID_STABILITY | {"SENSITIVE"}),
        f"stability_verdict = {cv.get('stability_verdict') if cv else None}",
    ))

    consistency = bool(cv.get("consistency_check_passed")) if cv else False
    results.append(_check(
        "consistency_check_passed = True",
        consistency,
        f"consistency_check_passed = {consistency}",
    ))

    sv = cv.get("stability_verdict") if cv else None
    results.append(_check(
        "stability_verdict is STABLE or MODERATE (SENSITIVE = FAIL)",
        sv in VALID_STABILITY,
        f"stability_verdict = {sv}",
    ))

    pl_cv = cv.get("paper_language") if cv else None
    results.append(_check(
        "paper_language populated in cmc_robustness_verdict.json",
        isinstance(pl_cv, str) and len(pl_cv.strip()) > 20,
        f"len = {len(pl_cv) if isinstance(pl_cv, str) else 0}",
    ))

    if kv and kv.get("verdict") == "UPDATED":
        s2_path = RES_D8 / "stage2_params_v2.json"
        s2 = {}
        if s2_path.exists():
            try:
                s2 = json.loads(s2_path.read_text())
            except Exception:  # noqa: BLE001
                s2 = {}
        results.append(_check(
            "day9_kappa_update appended to stage2_params_v2.json "
            "(Task A=UPDATED)",
            "day9_kappa_update" in s2,
            f"keys: day9_kappa_update={'day9_kappa_update' in s2}",
        ))
    else:
        verdict = kv.get("verdict") if kv else "<missing>"
        results.append(_check(
            f"Task C skip-check (verdict={verdict}): no update needed",
            True, "verdict != UPDATED, skipping day9_kappa_update check",
        ))

    expected_figs = [
        FIG_D9 / "D9-1_kappa_extension.png",
        FIG_D9 / "D9-2_cmc_robustness.png",
    ]
    missing = [str(p.relative_to(REPO))
               for p in expected_figs if not p.exists()]
    results.append(_check(
        "all Day 9 figures present in figures/fukushima/day9/",
        not missing,
        f"missing: {missing}" if missing else "",
    ))

    print("\nRunning pytest tests/ ...")
    pytest_ok, tail = _run_pytest()
    results.append(_check(
        "pytest tests/ passes (84 passed, 2 skipped)",
        pytest_ok,
        "see pytest_tail",
    ))

    all_passed = all(r["passed"] for r in results)
    payload = {
        "all_passed": bool(all_passed),
        "kappa_verdict": kv.get("verdict") if kv else None,
        "stability_verdict": cv.get("stability_verdict") if cv else None,
        "consistency_check_passed": consistency,
        "checks": results,
        "pytest_tail": tail,
    }
    out = RES_D9 / "diagnostics_gate_day9.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\n[gate] wrote {out}")
    print(f"[gate] all_passed = {all_passed}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
