#!/usr/bin/env python3
"""
Day 7b Section 2 -- diagnostic on Day 7 sobol indices.

Loads ``results/day7/sobol_indices.csv`` and flags every cell whose value is
mathematically impossible or uninformative under SALib's estimator
assumptions. Prints a per-QoI / per-parameter table and writes the flag
list to ``results/day7b/day7_reliability_flags.csv``.

Flag conventions (matching Day 7b prompt Section 2):

    IMPOSSIBLE_NEGATIVE     S_first < 0  (estimator noise; true value ~ 0)
    IMPOSSIBLE_EXCEEDS_1    ST > 1.0     (variance estimator overflow)
    UNINFORMATIVE_CI        2 * ST_conf > 0.50
    EFFECTIVELY_ZERO        ST CI includes 0.0  (insensitive)

Run:  python3 scripts/diagnose_day7_reliability.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DAY7_INDICES = ROOT / "results" / "day7" / "sobol_indices.csv"
OUT_DIR = ROOT / "results" / "day7b"
OUT_FILE = OUT_DIR / "day7_reliability_flags.csv"


def flag_row(row: pd.Series) -> list[str]:
    flags: list[str] = []
    s_first = float(row["S1"])
    s_first_conf = float(row["S1_conf"])
    st = float(row["ST"])
    st_conf = float(row["ST_conf"])
    ci_low = st - st_conf
    ci_high = st + st_conf
    if s_first < -1e-3:
        flags.append("IMPOSSIBLE_NEGATIVE")
    if st > 1.0 + 1e-3:
        flags.append("IMPOSSIBLE_EXCEEDS_1")
    if 2.0 * st_conf > 0.50:
        flags.append("UNINFORMATIVE_CI")
    if ci_low <= 0.0 <= ci_high:
        flags.append("EFFECTIVELY_ZERO")
    return flags


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not DAY7_INDICES.exists():
        raise FileNotFoundError(f"Cannot find {DAY7_INDICES}")

    df = pd.read_csv(DAY7_INDICES)
    rows = []
    for _, r in df.iterrows():
        flags = flag_row(r)
        rows.append({
            "qoi": r["qoi"],
            "parameter": r["parameter"],
            "S_first": float(r["S1"]),
            "S_first_conf": float(r["S1_conf"]),
            "ST": float(r["ST"]),
            "ST_conf": float(r["ST_conf"]),
            "CI_width": 2.0 * float(r["ST_conf"]),
            "n_flags": len(flags),
            "flags": ";".join(flags) if flags else "",
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_FILE, index=False)

    print(f"\n=== Day 7 reliability flags (n_samples=32, 192 evaluations) ===\n")
    print(f"{'QoI':<22} {'Param':<8} {'S_first':>9} {'ST':>9} "
          f"{'CI_w':>7}  {'flags'}")
    print("-" * 90)
    for _, r in out.iterrows():
        print(f"{r['qoi']:<22} {r['parameter']:<8} "
              f"{r['S_first']:>+9.3f} {r['ST']:>9.3f} "
              f"{r['CI_width']:>7.3f}  {r['flags']}")

    per_qoi = (out.groupby("qoi")["n_flags"]
               .agg(["sum", "max", "count"]).reset_index())
    per_qoi.columns = ["qoi", "total_flags", "max_per_cell", "n_cells"]
    print("\n=== Flag count per QoI ===\n")
    print(per_qoi.to_string(index=False))

    per_param = (out.groupby("parameter")["n_flags"]
                 .agg(["sum", "max", "count"]).reset_index())
    per_param.columns = ["parameter", "total_flags", "max_per_cell", "n_cells"]
    print("\n=== Flag count per parameter ===\n")
    print(per_param.to_string(index=False))

    qoi_unreliable = per_qoi[per_qoi["total_flags"] > 2]["qoi"].tolist()
    print("\n=== Verdict ===\n")
    if qoi_unreliable:
        print(f"  UNRELIABLE for calibration (>2 flags): {qoi_unreliable}")
    else:
        print("  No QoI exceeds the >2-flag unreliable threshold.")
    clean = per_qoi[per_qoi["total_flags"] == 0]["qoi"].tolist()
    if clean:
        print(f"  Fully clean (0 flags), can be trusted at n=32: {clean}")

    print(f"\n[diagnose] wrote per-cell flag table to {OUT_FILE}")


if __name__ == "__main__":
    main()
