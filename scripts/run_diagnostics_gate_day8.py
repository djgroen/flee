#!/usr/bin/env python3
"""Day 8 acceptance gate.

v1 checks (default; reads stage1_cmc_star.json + validation_summary.json):

  [ ] CMC* in [0.10, 0.50]
  [ ] hayano_t4 (validation) in [0.20, 0.40]
  [ ] mid_ps2_dip (validation) in [0.15, 0.40]
  [ ] mid_ps2_trough (validation) in [0.05, 0.30]
  [ ] blend_inner_t7 (validation) > 0
  [ ] hayano_tension_flag documented with explicit text
  [ ] All six QoIs computed and stored
  [ ] pytest tests/ --no-header -q passes (84 passed, 2 skipped)

v2 checks (``--v2``; reads stage2_params_v2.json + validation_summary_v2.json):

  [ ] CMC fixed at 0.25 in stage2_params_v2.json
  [ ] hayano_t4 (validation mean) in [0.35, 0.55]
  [ ] mid_ps2_dip in [target * 0.75, target * 1.25]
  [ ] mid_ps2_trough in [target * 0.75, target * 1.25]
  [ ] blend_inner_t7 mean > 0  (NOT min; per-rep negatives allowed)
  [ ] hayano_tension flagged=true and note contains "1.008"
  [ ] boundary_warning is "NONE" or "EXTENDED: ..."  (PERSISTENT = FAIL)
  [ ] All six QoIs in validation_summary_v2.json
  [ ] pytest tests/ passes

Writes ``results/day8/diagnostics_gate_day8.json`` (v1) or
``results/day8/diagnostics_gate_day8_v2.json`` (v2) and exits non-zero on
hard failure.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "day8"

REQUIRED_QOIS = {
    "hayano_t4", "mid_ps2_dip", "mid_ps2_trough", "mid_ps2_recovery",
    "corridor_inland_pct", "blend_inner_t7",
}


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


def _gate_v1():
    print("=" * 72)
    print("Day 8 diagnostics gate (v1)")
    print("=" * 72)
    results: list[dict] = []

    s1_path = RES / "stage1_cmc_star.json"
    s2_path = RES / "stage2_params.json"
    val_path = RES / "validation_summary.json"
    ens_path = RES / "validation_ensemble.csv"

    artifacts_ok = all(p.exists() for p in
                       [s1_path, s2_path, val_path, ens_path])
    results.append(_check(
        "calibration artifacts present", artifacts_ok,
        f"missing: "
        f"{[str(p.relative_to(REPO)) for p in [s1_path, s2_path, val_path, ens_path] if not p.exists()]}"
        if not artifacts_ok else ""))
    if not artifacts_ok:
        with (RES / "diagnostics_gate_day8.json").open("w") as fh:
            json.dump({"all_passed": False, "checks": results}, fh, indent=2)
        sys.exit(2)

    s1 = json.loads(s1_path.read_text())
    s2 = json.loads(s2_path.read_text())
    val = json.loads(val_path.read_text())

    cmc_star = float(s1["cmc_star"])
    results.append(_check(
        "CMC* in [0.10, 0.50]",
        0.10 - 1e-9 <= cmc_star <= 0.50 + 1e-9,
        f"CMC* = {cmc_star:.3f}",
    ))

    def _q(name: str) -> float | None:
        v = val.get(name)
        if isinstance(v, dict):
            m = v.get("mean")
            return float(m) if m is not None else None
        return None

    h = _q("hayano_t4")
    results.append(_check(
        "hayano_t4 in [0.20, 0.40] (validation mean)",
        h is not None and 0.20 <= h <= 0.40,
        f"hayano_t4 = {h}",
    ))

    dip = _q("mid_ps2_dip")
    results.append(_check(
        "mid_ps2_dip in [0.15, 0.40] (alpha-anchor)",
        dip is not None and 0.15 <= dip <= 0.40,
        f"mid_ps2_dip = {dip}",
    ))

    trough = _q("mid_ps2_trough")
    results.append(_check(
        "mid_ps2_trough in [0.05, 0.30] (beta-anchor)",
        trough is not None and 0.05 <= trough <= 0.30,
        f"mid_ps2_trough = {trough}",
    ))

    bit = _q("blend_inner_t7")
    results.append(_check(
        "blend_inner_t7 mean > 0 (dual-process earns its keep)",
        bit is not None and bit > 0.0,
        f"blend_inner_t7 mean = {bit}",
    ))

    flag = val.get("hayano_tension_flag")
    note = val.get("hayano_tension_note", "")
    results.append(_check(
        "hayano_tension_flag documented with explicit text",
        flag is not None and isinstance(note, str) and "1.008" in note,
        f"flag={flag} note='{note[:80]}...'" if note else f"flag={flag}",
    ))

    qoi_keys_seen = {k for k in val if isinstance(val.get(k), dict)
                     and "mean" in val[k]}
    have_all = REQUIRED_QOIS.issubset(qoi_keys_seen)
    results.append(_check(
        "all six QoIs computed and stored",
        have_all,
        f"missing: {sorted(REQUIRED_QOIS - qoi_keys_seen)}"
        if not have_all else "",
    ))

    boundary = s2.get("boundary_flags", {})
    if any(boundary.values()):
        results.append({
            "label": "stage2 boundary advisory",
            "status": "WARN",
            "passed": True,
            "detail": s2.get("boundary_warning", "boundary solution detected"),
        })
        print(f"  [WARN] {results[-1]['detail']}")

    print("\nRunning pytest tests/ ...")
    pytest_ok, tail = _run_pytest()
    results.append(_check(
        "pytest tests/ passes",
        pytest_ok,
        "see pytest_tail",
    ))

    all_passed = all(r["passed"] for r in results)
    payload = {
        "all_passed": bool(all_passed),
        "cmc_star": cmc_star,
        "alpha_star": s2.get("alpha_star"),
        "beta_star":  s2.get("beta_star"),
        "kappa_star": s2.get("kappa_star"),
        "hayano_tension_flag": flag,
        "hayano_tension_note": note,
        "checks": results,
        "pytest_tail": tail,
    }
    out = RES / "diagnostics_gate_day8.json"
    with out.open("w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\n[gate] wrote {out}")
    print(f"[gate] all_passed = {all_passed}")
    sys.exit(0 if all_passed else 1)


def _gate_v2():
    print("=" * 72)
    print("Day 8 diagnostics gate (v2)")
    print("=" * 72)
    results: list[dict] = []

    s2_path  = RES / "stage2_params_v2.json"
    val_path = RES / "validation_summary_v2.json"
    ens_path = RES / "validation_ensemble_v2.csv"

    artifacts_ok = all(p.exists() for p in [s2_path, val_path, ens_path])
    results.append(_check(
        "v2 calibration artifacts present", artifacts_ok,
        f"missing: "
        f"{[str(p.relative_to(REPO)) for p in [s2_path, val_path, ens_path] if not p.exists()]}"
        if not artifacts_ok else ""))
    if not artifacts_ok:
        with (RES / "diagnostics_gate_day8_v2.json").open("w") as fh:
            json.dump({"all_passed": False, "checks": results}, fh, indent=2)
        sys.exit(2)

    s2  = json.loads(s2_path.read_text())
    val = json.loads(val_path.read_text())

    cmc_fixed = float(s2.get("cmc_fixed", -1))
    results.append(_check(
        "CMC fixed at 0.25 in stage2_params_v2.json",
        abs(cmc_fixed - 0.25) <= 1e-9,
        f"cmc_fixed = {cmc_fixed}",
    ))

    qois = val.get("qois", {})

    def _q(name: str) -> float | None:
        entry = qois.get(name)
        if isinstance(entry, dict):
            m = entry.get("mean")
            return float(m) if m is not None else None
        return None

    h = _q("hayano_t4")
    results.append(_check(
        "hayano_t4 (validation mean) in [0.35, 0.55]",
        h is not None and 0.35 <= h <= 0.55,
        f"hayano_t4 = {h}",
    ))

    dip = _q("mid_ps2_dip")
    dip_target = float(s2.get("targets", {}).get("mid_ps2_dip"))
    dip_lo = dip_target * 0.75
    dip_hi = dip_target * 1.25
    results.append(_check(
        f"mid_ps2_dip in [{dip_lo:.3f}, {dip_hi:.3f}] "
        f"(target {dip_target:.3f} +/-25%)",
        dip is not None and dip_lo <= dip <= dip_hi,
        f"mid_ps2_dip = {dip}",
    ))

    trough = _q("mid_ps2_trough")
    trough_target = float(s2.get("targets", {}).get("mid_ps2_trough"))
    trough_lo = trough_target * 0.75
    trough_hi = trough_target * 1.25
    results.append(_check(
        f"mid_ps2_trough in [{trough_lo:.3f}, {trough_hi:.3f}] "
        f"(target {trough_target:.3f} +/-25%)",
        trough is not None and trough_lo <= trough <= trough_hi,
        f"mid_ps2_trough = {trough}",
    ))

    bit = _q("blend_inner_t7")
    # Per spec: gate criterion is mean > 0 (NOT every individual replicate).
    # Negative replicates within the ensemble are allowed and reported.
    bit_min = qois.get("blend_inner_t7", {}).get("min")
    results.append(_check(
        "blend_inner_t7 mean > 0 (mean check, not min)",
        bit is not None and bit > 0.0,
        f"mean = {bit}, min replicate = {bit_min} "
        "(negative replicates allowed)",
    ))

    tension = val.get("hayano_tension", {})
    note = tension.get("note", "")
    flagged = tension.get("flagged")
    results.append(_check(
        'hayano_tension flagged=true and note contains "1.008"',
        flagged is True and "1.008" in str(note),
        f"flagged={flagged} note='{note[:80]}...'" if note
        else f"flagged={flagged}",
    ))

    bw = str(s2.get("boundary_warning", ""))
    bw_ok = (bw == "NONE") or bw.startswith("EXTENDED")
    if "PERSISTENT" in bw:
        bw_ok = False
    results.append(_check(
        'boundary_warning is "NONE" or "EXTENDED: ..." (PERSISTENT = FAIL)',
        bw_ok,
        f"boundary_warning = '{bw}'",
    ))

    qoi_keys_seen = {k for k in qois if isinstance(qois.get(k), dict)
                     and "mean" in qois[k]}
    have_all = REQUIRED_QOIS.issubset(qoi_keys_seen)
    results.append(_check(
        "all six QoIs in validation_summary_v2.json",
        have_all,
        f"missing: {sorted(REQUIRED_QOIS - qoi_keys_seen)}"
        if not have_all else "",
    ))

    if s2.get("unconstrained_axes"):
        results.append({
            "label": "stage2_v2 unconstrained-axes advisory",
            "status": "WARN",
            "passed": True,
            "detail": "; ".join(s2["unconstrained_axes"]),
        })
        print(f"  [WARN] {results[-1]['detail']}")

    print("\nRunning pytest tests/ ...")
    pytest_ok, tail = _run_pytest()
    results.append(_check(
        "pytest tests/ passes",
        pytest_ok,
        "see pytest_tail",
    ))

    all_passed = all(r["passed"] for r in results)
    payload = {
        "version": "v2",
        "all_passed": bool(all_passed),
        "cmc_fixed":  cmc_fixed,
        "alpha_star": s2.get("alpha_star"),
        "beta_star":  s2.get("beta_star"),
        "kappa_star": s2.get("kappa_star"),
        "hayano_tension": tension,
        "boundary_warning": bw,
        "checks": results,
        "pytest_tail": tail,
    }
    out = RES / "diagnostics_gate_day8_v2.json"
    with out.open("w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\n[gate v2] wrote {out}")
    print(f"[gate v2] all_passed = {all_passed}")
    sys.exit(0 if all_passed else 1)


def main():
    ap = argparse.ArgumentParser(description="Day 8 diagnostics gate.")
    ap.add_argument("--v2", action="store_true",
                    help="Apply revised v2 gate criteria.")
    args = ap.parse_args()
    if args.v2:
        _gate_v2()
    else:
        _gate_v1()


if __name__ == "__main__":
    main()
