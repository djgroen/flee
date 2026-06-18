#!/usr/bin/env python3
"""Day 13 -- Sobol indices, bootstrap CIs, sanity checks, verdict (Task D).

Reads the Task A/C raw evaluations (clamp ON + OFF), averages the 3 fixed seeds
per Saltelli sample, runs SALib first/total-order Sobol with bootstrap CIs
(matching the Day-7b convention: raw['S1'] -> S_first immediately), evaluates the
per-QoI sanity checks, and emits an identifiability verdict per factor.

Outputs:
  results/tmi/day13_sobol_indices.csv   (qoi, factor, clamp, S_first, CIs, ST, CIs, variance_flag)
  results/tmi/day13_sobol_sanity.csv    (per QoI x clamp: S_first<=ST, sum S_first, neg S_first)
  results/tmi/day13_sobol_verdict.json  (per-factor verdict + clamp-effect summary)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from SALib.analyze import sobol as sobol_analyze  # noqa: E402

from scripts.run_tmi_day13_sobol import (  # noqa: E402
    PROBLEM, QOI_KEYS, QOI_TIERS,
)

RES = REPO / "results" / "tmi"
N_RESAMPLES = 1000          # >= 500 (Day-7b convention)
CONF_LEVEL = 0.95
LOW_VAR_CV = 0.02           # coefficient-of-variation threshold for LOW_VARIANCE
ABS_VAR_FLOOR = 1.0e-4      # absolute-variance floor; below this indices unreliable
INVALID_ST = 1.05           # ST above this is a numerical artifact (undersampling)
IDENTIFIABLE_ST = 0.10      # ST threshold for "identifiable"
CLAMP_DELTA = 0.15          # |ST_off - ST_on| threshold for clamp-dependence
FACTORS = PROBLEM["names"]
TIER1 = [q for q, t in QOI_TIERS.items() if t == 1]


def _per_sample_means(df: pd.DataFrame) -> pd.DataFrame:
    """Mean QoI across the fixed seeds, ordered by Saltelli sample index."""
    return (df.groupby("sample_idx")[QOI_KEYS].mean()
              .sort_index())


def _variance_flag(y_raw: np.ndarray) -> tuple[str, float, float]:
    """Return (flag, variance, cv) for a per-sample QoI vector (pre-impute)."""
    finite = y_raw[np.isfinite(y_raw)]
    if finite.size == 0:
        return "CONSTANT", 0.0, 0.0
    var = float(np.var(finite))
    mean = float(np.mean(finite))
    cv = float(np.std(finite) / abs(mean)) if abs(mean) > 1e-12 else float("inf")
    if np.allclose(finite, finite[0]):
        return "CONSTANT", var, 0.0
    # Flag if EITHER the relative spread (CV) is tiny OR the absolute variance is
    # near-degenerate (e.g. zone P_S2 spread ~0.002, the Day-12 P1 finding):
    # both regimes make Sobol indices numerically unreliable.
    if cv < LOW_VAR_CV or var < ABS_VAR_FLOOR:
        return "LOW_VARIANCE", var, cv
    return "ok", var, cv


def _analyze_qoi(y_raw: np.ndarray) -> dict | None:
    """SALib first/total-order with bootstrap CIs; NaN imputed by nanmean."""
    if np.all(~np.isfinite(y_raw)) or np.allclose(
            y_raw[np.isfinite(y_raw)], y_raw[np.isfinite(y_raw)][0]
            if np.any(np.isfinite(y_raw)) else 0.0):
        return None
    y = y_raw.copy()
    if np.any(~np.isfinite(y)):
        y[~np.isfinite(y)] = np.nanmean(y_raw)
    raw = sobol_analyze.analyze(
        PROBLEM, y, calc_second_order=True,
        num_resamples=N_RESAMPLES, conf_level=CONF_LEVEL,
        print_to_console=False, seed=0,
    )
    return {
        "S_first": np.asarray(raw["S1"], dtype=float),
        "S_first_conf": np.asarray(raw["S1_conf"], dtype=float),
        "ST": np.asarray(raw["ST"], dtype=float),
        "ST_conf": np.asarray(raw["ST_conf"], dtype=float),
    }


def analyze_dataset(df: pd.DataFrame, clamp: str) -> tuple[list[dict], list[dict]]:
    means = _per_sample_means(df)
    index_rows: list[dict] = []
    sanity_rows: list[dict] = []
    for qoi in QOI_KEYS:
        y_raw = means[qoi].values.astype(float)
        flag, var, cv = _variance_flag(y_raw)
        n_nan = int(np.sum(~np.isfinite(y_raw)))
        idx = _analyze_qoi(y_raw)
        if idx is None:
            for f in FACTORS:
                index_rows.append({
                    "qoi": qoi, "factor": f, "clamp": clamp,
                    "S_first": 0.0, "S_first_ci_low": 0.0, "S_first_ci_high": 0.0,
                    "ST": 0.0, "ST_ci_low": 0.0, "ST_ci_high": 0.0,
                    "variance_flag": "CONSTANT", "variance": var, "cv": cv,
                    "n_nan": n_nan,
                })
            sanity_rows.append({
                "qoi": qoi, "clamp": clamp, "variance_flag": "CONSTANT",
                "sum_S_first": 0.0, "sum_S_first_ok": True,
                "all_S_first_le_ST": True, "any_neg_S_first": False,
                "min_S_first": 0.0,
            })
            continue

        sum_sf = float(np.sum(idx["S_first"]))
        all_le = True
        any_neg = False
        min_sf = float("inf")
        for j, f in enumerate(FACTORS):
            sf = float(idx["S_first"][j]); sfc = float(idx["S_first_conf"][j])
            st = float(idx["ST"][j]); stc = float(idx["ST_conf"][j])
            min_sf = min(min_sf, sf)
            if sf > st + 0.05:
                all_le = False
            if sf < -0.05 and sf < -sfc:   # strongly negative beyond CI noise
                any_neg = True
            index_rows.append({
                "qoi": qoi, "factor": f, "clamp": clamp,
                "S_first": sf, "S_first_ci_low": sf - sfc, "S_first_ci_high": sf + sfc,
                "ST": st, "ST_ci_low": st - stc, "ST_ci_high": st + stc,
                "variance_flag": flag, "variance": var, "cv": cv, "n_nan": n_nan,
            })
        sanity_rows.append({
            "qoi": qoi, "clamp": clamp, "variance_flag": flag,
            "sum_S_first": sum_sf, "sum_S_first_ok": bool(sum_sf <= 1.10),
            "all_S_first_le_ST": bool(all_le), "any_neg_S_first": bool(any_neg),
            "min_S_first": float(min_sf),
        })
    return index_rows, sanity_rows


def build_verdict(idx_df: pd.DataFrame) -> dict:
    """Per-factor identifiability verdict (clamp ON primary; clamp effect noted)."""
    verdict = {}
    on = idx_df[idx_df["clamp"] == "on"]
    off = idx_df[idx_df["clamp"] == "off"]

    def _st(d, qoi, f):
        r = d[(d["qoi"] == qoi) & (d["factor"] == f)]
        return float(r["ST"].iloc[0]) if len(r) else float("nan")

    for f in FACTORS:
        # Best Tier-1 signal, ignoring LOW_VARIANCE/CONSTANT QoIs.
        carriers = []
        best_st, best_qoi = 0.0, None
        for qoi in TIER1:
            r = on[(on["qoi"] == qoi) & (on["factor"] == f)]
            if not len(r):
                continue
            if r["variance_flag"].iloc[0] in ("LOW_VARIANCE", "CONSTANT"):
                continue
            st = float(r["ST"].iloc[0])
            if st > INVALID_ST:            # numerical artifact -> not a carrier
                continue
            if st >= IDENTIFIABLE_ST:
                carriers.append((qoi, round(st, 3)))
            if st > best_st:
                best_st, best_qoi = st, qoi
        status = "identifiable" if best_st >= IDENTIFIABLE_ST else "flat"

        # Clamp dependence on the saturated total-evac QoI.
        st_on = _st(on, "total_evac", f)
        st_off = _st(off, "total_evac", f) if len(off) else float("nan")
        clamp_dep = (not np.isnan(st_off)
                     and abs(st_off - st_on) >= CLAMP_DELTA)
        verdict[f] = {
            "status": status,
            "best_tier1_ST": round(best_st, 4),
            "best_tier1_qoi": best_qoi,
            "carriers": carriers,
            "total_evac_ST_clamp_on": round(st_on, 4) if not np.isnan(st_on) else None,
            "total_evac_ST_clamp_off": round(st_off, 4) if not np.isnan(st_off) else None,
            "clamp_dependent_on_total_evac": bool(clamp_dep),
        }
    return verdict


def main():
    on_csv = RES / "day13_sobol_evals.csv"
    off_csv = RES / "day13_sobol_evals_noclamp.csv"
    if not on_csv.exists():
        sys.exit(f"Missing {on_csv}; run scripts/run_tmi_day13_sobol.py first.")

    all_idx, all_san = [], []
    df_on = pd.read_csv(on_csv)
    idx, san = analyze_dataset(df_on, "on")
    all_idx += idx; all_san += san

    if off_csv.exists():
        df_off = pd.read_csv(off_csv)
        idx, san = analyze_dataset(df_off, "off")
        all_idx += idx; all_san += san
    else:
        print(f"[warn] {off_csv} missing -- clamp-off indices skipped (Task C not run).")

    idx_df = pd.DataFrame(all_idx)
    out_cols = ["qoi", "factor", "clamp", "S_first", "S_first_ci_low",
                "S_first_ci_high", "ST", "ST_ci_low", "ST_ci_high",
                "variance_flag", "variance", "cv", "n_nan"]
    idx_df[out_cols].to_csv(RES / "day13_sobol_indices.csv", index=False)
    san_df = pd.DataFrame(all_san)
    san_df.to_csv(RES / "day13_sobol_sanity.csv", index=False)

    verdict = build_verdict(idx_df)
    with (RES / "day13_sobol_verdict.json").open("w") as fh:
        json.dump(verdict, fh, indent=2)

    # ---- printed summary ----
    print("=" * 74)
    print("Day 13 Sobol indices -- identifiability verdict (clamp ON primary)")
    print("=" * 74)
    for f, v in verdict.items():
        car = ", ".join(f"{q}({s})" for q, s in v["carriers"]) or "-"
        print(f"  {f:6s}: {v['status']:13s} best Tier-1 ST={v['best_tier1_ST']:.3f}"
              f" on {v['best_tier1_qoi']};  carriers: {car}")
        print(f"          total_evac ST  clamp ON={v['total_evac_ST_clamp_on']}"
              f"  OFF={v['total_evac_ST_clamp_off']}"
              f"  clamp-dependent={v['clamp_dependent_on_total_evac']}")

    print("-" * 74)
    print("Sanity checks (per QoI):")
    for _, r in san_df.iterrows():
        tag = []
        if not r["all_S_first_le_ST"]: tag.append("S_first>ST!")
        if not r["sum_S_first_ok"]:    tag.append(f"sumS_first={r['sum_S_first']:.2f}>1!")
        if r["any_neg_S_first"]:       tag.append("neg S_first!")
        status = "PASS" if not tag else "WARN(" + ",".join(tag) + ")"
        print(f"  [{r['clamp']:3s}] {r['qoi']:22s} sumS_first={r['sum_S_first']:5.2f}"
              f"  var_flag={r['variance_flag']:12s} {status}")

    low_var = sorted(set(san_df[san_df["variance_flag"].isin(
        ["LOW_VARIANCE", "CONSTANT"])]["qoi"]))
    print("-" * 74)
    print(f"LOW_VARIANCE / CONSTANT QoIs (indices caveated): {low_var}")
    print(f"[out] indices -> {RES/'day13_sobol_indices.csv'}")
    print(f"[out] sanity  -> {RES/'day13_sobol_sanity.csv'}")
    print(f"[out] verdict -> {RES/'day13_sobol_verdict.json'}")


if __name__ == "__main__":
    main()
