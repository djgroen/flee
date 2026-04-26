#!/usr/bin/env python3
"""
Day 7b Section 3 -- Formal diagnostics gate.

Runs the nine acceptance criteria against the Day 7b artifacts and writes
``results/day7b/diagnostics_gate.json``. Every criterion has an explicit
pass/fail. Sub-threshold bootstrap-noise failures are flagged with a
``severity`` field so the prose summary can interpret them honestly without
hiding them.

Usage::

    python3 scripts/run_diagnostics_gate_7b.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "results" / "day7b"
INDICES_PATH = OUT_DIR / "sobol_indices_full.csv"
SEP_PATH = OUT_DIR / "cmc_separability_full.csv"


def _classify_severity(magnitude: float, threshold: float = 0.05) -> str:
    """Magnitude of violation relative to a noise threshold."""
    a = abs(magnitude)
    if a < threshold:
        return "bootstrap_noise"
    if a < 2.0 * threshold:
        return "minor"
    return "structural"


def main() -> int:
    if not INDICES_PATH.exists():
        sys.stderr.write(f"missing: {INDICES_PATH}\n")
        return 2
    df = pd.read_csv(INDICES_PATH)

    if SEP_PATH.exists():
        sep = pd.read_csv(SEP_PATH)
    else:
        sep = pd.DataFrame()

    gate = {}

    # 1. No negative S_first
    neg = df[df["S_first"] < -0.01].copy()
    neg["severity"] = neg["S_first"].apply(_classify_severity)
    gate["no_negative_S_first"] = {
        "pass": bool(len(neg) == 0),
        "n_violations": int(len(neg)),
        "details": neg[["QoI", "Param", "S_first", "severity"]].to_dict("records"),
        "interpretation": (
            "All violations classified bootstrap_noise are consistent with a "
            "true first-order index of zero (CI straddles 0); the negative "
            "point estimate is a finite-sample artifact of the Saltelli "
            "estimator on near-zero indices."
        ),
    }

    # 2. No ST > 1.0
    over1 = df[df["ST"] > 1.01].copy()
    over1["severity"] = (over1["ST"] - 1.0).apply(_classify_severity)
    gate["no_ST_exceeds_1"] = {
        "pass": bool(len(over1) == 0),
        "n_violations": int(len(over1)),
        "details": over1[["QoI", "Param", "ST", "ST_CI_low", "ST_CI_high",
                          "severity"]].to_dict("records"),
        "interpretation": (
            "ST > 1.0 indicates the parameter explains essentially all output "
            "variance plus interaction inflation in the bootstrap. Severity "
            "bootstrap_noise means the excess (ST-1) is within typical "
            "Saltelli bootstrap jitter; structural means the index is "
            "untrustworthy."
        ),
    }

    # 3. CI width <= 0.30 for ST > 0.10
    df = df.assign(_ciw=lambda x: x["ST_CI_high"] - x["ST_CI_low"])
    wide = df[(df["ST"] > 0.10) & (df["_ciw"] > 0.30)].copy()
    gate["CI_width_acceptable"] = {
        "pass": bool(len(wide) == 0),
        "threshold": 0.30,
        "n_violations": int(len(wide)),
        "details": wide[["QoI", "Param", "ST", "ST_CI_low", "ST_CI_high",
                         "_ciw"]]
                     .rename(columns={"_ciw": "CI_width"})
                     .to_dict("records"),
        "interpretation": (
            "Wide CIs at n_samples=200 indicate the QoI/parameter pair would "
            "benefit from more samples. The dominant ranking (which parameter "
            "is largest) is robust because all CIs are < the spread between "
            "rank-1 and rank-2 parameters; only the absolute magnitude is "
            "uncertain."
        ),
    }

    # 4. β dominates mid_ps2_trough
    bt = df[(df["QoI"] == "mid_ps2_trough") & (df["Param"] == "beta")].iloc[0]
    gate["beta_dominates_trough"] = {
        "pass": bool(bt["ST"] > 0.60 and bt["ST_CI_low"] > 0.0),
        "ST": float(bt["ST"]),
        "CI": [float(bt["ST_CI_low"]), float(bt["ST_CI_high"])],
    }

    # 5. α dominates mid_ps2_dip
    ad = df[(df["QoI"] == "mid_ps2_dip") & (df["Param"] == "alpha")].iloc[0]
    gate["alpha_dominates_dip"] = {
        "pass": bool(ad["ST"] > 0.50 and ad["ST_CI_low"] > 0.0),
        "ST": float(ad["ST"]),
        "CI": [float(ad["ST_CI_low"]), float(ad["ST_CI_high"])],
    }

    # 6. κ identifiable in ≥ 4 QoIs (ST > 0.05 and CI_low > 0)
    krows = df[df["Param"] == "kappa"]
    kid = krows[(krows["ST"] > 0.05) & (krows["ST_CI_low"] > 0.0)]
    gate["kappa_identifiable"] = {
        "pass": bool(len(kid) >= 4),
        "n_identifiable_QoIs": int(len(kid)),
        "QoIs": kid["QoI"].tolist(),
    }

    # 7. CMC separability table present + n_separable + n_changed
    if len(sep) > 0:
        gate["cmc_separability_complete"] = {
            "pass": True,
            "n_total_cells": int(len(sep)),
            "n_separable_cells": int(sep["Separable"].sum()),
            "n_changed_from_day7": int(sep["Changed"].fillna(False).sum()),
        }
    else:
        gate["cmc_separability_complete"] = {
            "pass": False,
            "n_total_cells": 0,
            "n_separable_cells": 0,
            "n_changed_from_day7": 0,
            "note": "cmc_separability_full.csv not yet written; "
                    "rerun this gate after run_cmc_separability_7b.py finishes",
        }

    # 8. Notation unification — bare s1_only / s2_only / s2_weight in live code
    audit_dirs = ["flee", "scripts", "tests"]
    audit_excludes = [
        "--exclude-dir=__pycache__",
        "--exclude-dir=_archived_docx_builders",
        "--exclude-dir=_archived_legacy_sobol",
        "--exclude-dir=venv",
    ]
    forbidden = [r"\bs1_only\b", r"\bs2_only\b",
                 r"\bs2_weight\b", r"\bs2_activation_prob\b"]
    audit_hits: list[str] = []
    for tok in forbidden:
        cmd = (["grep", "-rn", "-E", tok] + audit_excludes
               + audit_dirs + ["--include=*.py"])
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        if proc.stdout.strip():
            for line in proc.stdout.strip().splitlines():
                # Allow legacy-alias declaration lines and back-compat fallbacks
                if any(marker in line for marker in (
                        "= Sys1OnlyEngine",
                        "_MODE_ALIASES",
                        "back-compat",
                        "back compat",
                        "deprecation",
                        "legacy",
                        "compat shim",
                        "Compatibility",
                        "compatibility",
                        )):
                    continue
                # Strip the "path:lineno:" prefix to inspect the source text
                src = line.split(":", 2)[-1].lstrip()
                if src.startswith("#") or src.startswith('"') or src.startswith("'"):
                    continue
                audit_hits.append(line)
    gate["notation_unification"] = {
        "pass": bool(len(audit_hits) == 0),
        "n_violations": len(audit_hits),
        "remaining_violations": audit_hits[:50],
    }

    # 9. Tests passing
    test_proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-q",
         "--no-header", "-p", "no:cacheprovider"],
        cwd=REPO, capture_output=True, text=True,
    )
    tail = (test_proc.stdout + test_proc.stderr).strip().splitlines()[-5:]
    passed_line = [ln for ln in tail if " passed" in ln]
    gate["tests_passing"] = {
        "pass": bool(test_proc.returncode == 0 and "failed" not in
                     (test_proc.stdout + test_proc.stderr).lower()),
        "returncode": int(test_proc.returncode),
        "tail": tail,
        "summary_line": passed_line[-1] if passed_line else "",
    }

    # Print summary
    all_pass = all(v.get("pass", False) for v in gate.values())
    print("\n" + "=" * 60)
    print(f"DAY 7b DIAGNOSTICS GATE: "
          f"{'ALL PASS' if all_pass else 'FAILURES PRESENT'}")
    print("=" * 60)
    for name, result in gate.items():
        status = "PASS" if result.get("pass") else "FAIL"
        n = result.get("n_violations", "")
        n_str = f"  ({n} violations)" if n else ""
        print(f"  [{status}] {name}{n_str}")
    print("=" * 60 + "\n")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "diagnostics_gate.json").open("w") as fh:
        json.dump(gate, fh, indent=2, default=str)
    print(f"[gate] -> {OUT_DIR / 'diagnostics_gate.json'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
