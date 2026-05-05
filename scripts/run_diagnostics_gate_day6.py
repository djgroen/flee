#!/usr/bin/env python3
"""Day 6 acceptance gate.

Checks (per Day 6 spec):

  [PASS/FAIL] goal_a_verdict.json present with valid verdict + paper_language
  [PASS/FAIL] goal_b_summary.json present with valid zone_discretization_verdict
  [PASS/FAIL] iitate_effect documented with delta_pct and interpretation
  [PASS/FAIL] goal_c_verdict.json present with valid masking_verdict
  [PASS/FAIL] tomioka_group blend_vs_s1_inland_delta computed
  [PASS/FAIL] all 6 Day 6 figures present
  [PASS/FAIL] no modification to flee/, tests/, qoi_definitions.py
  [PASS/FAIL] pytest tests/ passes (84 passed, 2 skipped)

Writes results/day6/diagnostics_gate_day6.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO   = Path(__file__).resolve().parent.parent
RES_D6 = REPO / "results" / "day6"
FIG_D6 = REPO / "figures" / "fukushima" / "day6"

VALID_GOAL_A   = {"ROUTING_FLAT", "ROUTING_SENSITIVE"}
VALID_GOAL_B   = {"SHARPENS", "WEAKENS", "NEUTRAL"}
VALID_GOAL_C   = {"LARGE_MASKING", "MODERATE_MASKING", "NO_MASKING"}

PROTECTED_FILES = [
    "flee/s1s2_model.py",
    "flee/moving.py",
    "flee/decision_engine.py",
    "flee/agent.py",
    "tests/test_s1s2_v3.py",
    "scripts/qoi_definitions.py",
]


def _check(label: str, cond: bool, detail: str = "") -> dict:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}" + (f"  -- {detail}" if detail else ""))
    return {"label": label, "status": status, "passed": bool(cond),
            "detail": detail}


def _git_clean(rel_path: str) -> tuple[bool, str]:
    """Return (clean, status_line)."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", rel_path],
            cwd=REPO, capture_output=True, text=True, timeout=30)
    except Exception as exc:  # noqa: BLE001
        return False, f"git error: {exc!r}"
    out = (proc.stdout or "").strip()
    return out == "", out


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
    print("Day 6 diagnostics gate")
    print("=" * 72)
    results: list[dict] = []

    # Goal A
    a_path = RES_D6 / "goal_a_verdict.json"
    a = json.loads(a_path.read_text()) if a_path.exists() else None
    a_ok = (a is not None
            and a.get("verdict") in VALID_GOAL_A
            and isinstance(a.get("paper_language"), str)
            and len(a["paper_language"].strip()) > 20)
    results.append(_check(
        "goal_a_verdict.json with valid verdict + paper_language",
        a_ok,
        f"verdict = {a.get('verdict') if a else None}",
    ))

    # Goal B
    b_path = RES_D6 / "goal_b_summary.json"
    b = json.loads(b_path.read_text()) if b_path.exists() else None
    b_ok = (b is not None
            and b.get("zone_discretization_verdict") in VALID_GOAL_B
            and isinstance(b.get("paper_language"), str)
            and len(b["paper_language"].strip()) > 20)
    results.append(_check(
        "goal_b zone_discretization_verdict in {SHARPENS, WEAKENS, NEUTRAL}",
        b_ok,
        f"verdict = "
        f"{b.get('zone_discretization_verdict') if b else None}",
    ))
    results.append(_check(
        "goal_b verdict_basis field present",
        bool((b or {}).get("verdict_basis")),
        f"basis len = {len((b or {}).get('verdict_basis', '') or '')}",
    ))
    iit = (b or {}).get("iitate_effect", {})
    results.append(_check(
        "goal_b iitate_effect.methodological_note present",
        bool(iit.get("methodological_note")),
        "",
    ))
    rd = (b or {}).get("blend_minus_sys1_inland_delta_pct", {})
    results.append(_check(
        "goal_b routing differential documented (both scenarios)",
        ("official_zones" in rd) and ("dosimeter_proxy" in rd),
        f"keys = {list(rd.keys())}",
    ))
    iit_ok = (iit.get("delta_pct") is not None
              and isinstance(iit.get("interpretation"), str)
              and len(iit["interpretation"].strip()) > 10)
    results.append(_check(
        "goal_b iitate_effect documented with delta_pct + interpretation",
        iit_ok,
        f"delta_pct = {iit.get('delta_pct')}",
    ))

    # Goal C
    c_path = RES_D6 / "goal_c_verdict.json"
    c = json.loads(c_path.read_text()) if c_path.exists() else None
    c_ok = (c is not None
            and c.get("masking_verdict") in VALID_GOAL_C
            and isinstance(c.get("paper_language"), str)
            and len(c["paper_language"].strip()) > 20)
    results.append(_check(
        "goal_c masking_verdict valid + paper_language populated",
        c_ok,
        f"verdict = {c.get('masking_verdict') if c else None}",
    ))
    results.append(_check(
        "goal_c route_type_method = transit_based (...)",
        bool((c or {}).get("route_type_method", "").startswith(
            "transit_based")),
        f"method = {(c or {}).get('route_type_method', '')[:80]}",
    ))
    eff = (c or {}).get("coastal_route_efficiency_check", {})
    results.append(_check(
        "goal_c coastal_route_efficiency_check block present",
        bool(eff),
        f"keys = {list(eff.keys()) if eff else None}",
    ))
    results.append(_check(
        "goal_c coastal_route_efficiency_check.blend_prefers_shorter_route "
        "(bool)",
        isinstance(eff.get("blend_prefers_shorter_route"), bool),
        f"value = {eff.get('blend_prefers_shorter_route')}",
    ))
    results.append(_check(
        "goal_c coastal_route_efficiency_check.interpretation populated",
        bool(eff.get("interpretation"))
        and len(eff["interpretation"].strip()) > 20,
        f"len = {len(eff.get('interpretation', '') or '')}",
    ))
    results.append(_check(
        "goal_c route_type_dest_delta preserved for audit",
        isinstance((c or {}).get("route_type_dest_delta"), dict),
        f"keys = {list(((c or {}).get('route_type_dest_delta') or {}).keys())}",
    ))

    tom = ((c or {}).get("origin_group_deltas", {})
                    .get("tomioka_group", {}))
    tom_delta = tom.get("blend_vs_s1_inland_delta")
    tom_ok = isinstance(tom_delta, (int, float))
    results.append(_check(
        "goal_c tomioka_group blend_vs_s1_inland_delta recorded",
        tom_ok,
        f"delta = {tom_delta}",
    ))

    # Figures (6 expected)
    expected_figs = [
        FIG_D6 / "D6-A_kappa_routing_sensitivity.png",
        FIG_D6 / "D6-B1_regime_ps2_comparison.png",
        FIG_D6 / "D6-B2_iitate_clearance.png",
        FIG_D6 / "D6-C1_origin_routing_bars.png",
        FIG_D6 / "D6-C2_origin_path_lengths.png",
        FIG_D6 / "D6-C3_departure_timing.png",
    ]
    missing = [str(p.relative_to(REPO))
               for p in expected_figs if not p.exists()]
    results.append(_check(
        "all 6 Day 6 figures present in figures/fukushima/day6/",
        not missing,
        f"missing: {missing}" if missing else "",
    ))

    # Protected files unchanged
    dirty = []
    for rel in PROTECTED_FILES:
        clean, status_line = _git_clean(rel)
        if not clean:
            dirty.append(f"{rel}: {status_line}")
    results.append(_check(
        "no modifications to flee/ tests/ qoi_definitions.py",
        not dirty,
        "; ".join(dirty) if dirty else "",
    ))

    # pytest
    print("\nRunning pytest tests/ ...")
    pytest_ok, tail = _run_pytest()
    results.append(_check(
        "pytest tests/ passes (84 passed, 2 skipped)",
        pytest_ok,
        "see pytest_tail",
    ))

    all_passed = all(r["passed"] for r in results)
    payload = {
        "all_passed":          bool(all_passed),
        "goal_a_verdict":      a.get("verdict") if a else None,
        "goal_b_verdict":      b.get("zone_discretization_verdict")
                               if b else None,
        "goal_c_verdict":      c.get("masking_verdict") if c else None,
        "iitate_delta_pct":    iit.get("delta_pct"),
        "tomioka_inland_delta_pp": tom_delta,
        "checks":              results,
        "pytest_tail":         tail,
    }
    out = RES_D6 / "diagnostics_gate_day6.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\n[gate] wrote {out}")
    print(f"[gate] all_passed = {all_passed}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
