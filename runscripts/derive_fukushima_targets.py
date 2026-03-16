#!/usr/bin/env python3
"""
Derive Fukushima 2011 calibration targets from Hayano & Adachi (2013) Fig 3 data.

Reads: conflict_validation/fukushima_2011/hayano_2013_fig3_hourly.csv
Writes: data/calibration_targets/fukushima_2011_targets.csv

Usage: python runscripts/derive_fukushima_targets.py
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OBS_PATH = PROJECT_ROOT / "conflict_validation" / "fukushima_2011" / "hayano_2013_fig3_hourly.csv"
TARGETS_PATH = PROJECT_ROOT / "data" / "calibration_targets" / "fukushima_2011_targets.csv"

T0 = pd.Timestamp("2011-03-11 14:46")  # earthquake onset
BASELINE_TIME = pd.Timestamp("2011-03-11 04:00")  # residential pre-earthquake night
OUTAGE_START = pd.Timestamp("2011-03-13 06:00")
OUTAGE_END = pd.Timestamp("2011-03-14 12:00")

# Zone column names in the CSV (may use en-dash)
ZONE_COLS = ["<5km", "5–10km", "10–15km", "15–20km", "20–25km", "25–30km", "30–35km", "35–40km"]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Proceed even if targets not satisfied")
    args = parser.parse_args()

    if not OBS_PATH.exists():
        print(f"ERROR: Observation file not found: {OBS_PATH}")
        return 1

    df = pd.read_csv(OBS_PATH)

    # 2a — Parse timestamps and convert to hours since t=0
    def parse_dt(s):
        return pd.to_datetime(f"2011-{s.strip()}", format="%Y-%m/%d %H:%M", errors="coerce")

    df["datetime"] = df["Date/Time"].apply(parse_dt)
    df = df.dropna(subset=["datetime"])
    df["hours_since_t0"] = (df["datetime"] - T0).dt.total_seconds() / 3600.0

    # 2b — Compute fraction remaining per zone
    baseline_row = df[df["datetime"] == BASELINE_TIME].iloc[0]
    baseline = {col: baseline_row[col] for col in ZONE_COLS if col in df.columns}

    for col in ZONE_COLS:
        if col in df.columns and col in baseline and baseline[col] > 0:
            df[f"frac_{col}"] = df[col] / baseline[col]
        elif col in df.columns:
            df[f"frac_{col}"] = np.nan

    # 2c — Flag network outage window
    df["usable"] = ~((df["datetime"] >= OUTAGE_START) & (df["datetime"] <= OUTAGE_END))

    # Interpolate frac_remaining at target hours for evaluation
    def interp_at_hours(zone_col, target_hours):
        """Linear interpolation of frac_remaining at target hours (using usable rows only)."""
        usable_df = df[df["usable"]].sort_values("hours_since_t0")
        frac_col = f"frac_{zone_col}" if zone_col in ZONE_COLS else zone_col
        if frac_col not in usable_df.columns:
            return {}
        vals = np.interp(
            target_hours,
            usable_df["hours_since_t0"].values,
            usable_df[frac_col].values,
        )
        return dict(zip(target_hours, vals))

    # 2d — Derive the five calibration targets
    # Get empirical values at target times (interpolate from usable data)
    def get_empirical_at_t(zone_col, t_hours):
        usable_df = df[df["usable"]].sort_values("hours_since_t0")
        frac_col = f"frac_{zone_col}"
        if frac_col not in usable_df.columns:
            return np.nan
        return np.interp(t_hours, usable_df["hours_since_t0"].values, usable_df[frac_col].values)

    def get_empirical_sum_at_t(zone_cols, t_hours):
        """Sum of populations at t, divided by sum of baselines."""
        usable_df = df[df["usable"]].sort_values("hours_since_t0")
        total_baseline = sum(baseline.get(c, 0) for c in zone_cols if c in df.columns)
        if total_baseline <= 0:
            return np.nan
        total_pop = 0
        for col in zone_cols:
            if col in usable_df.columns:
                total_pop = np.interp(
                    t_hours,
                    usable_df["hours_since_t0"].values,
                    usable_df[col].values,
                )
                break
        # Actually we need sum across zones at each time
        pop_at_t = 0
        for col in zone_cols:
            if col in usable_df.columns:
                pop_at_t += np.interp(t_hours, usable_df["hours_since_t0"].values, usable_df[col].values)
        return pop_at_t / total_baseline

    # Fix: get_empirical_sum_at_t needs to sum populations at the same timestamp
    def get_empirical_sum_at_t_fixed(zone_cols, t_hours):
        usable_df = df[df["usable"]].sort_values("hours_since_t0")
        total_baseline = sum(baseline.get(c, 0) for c in zone_cols if c in df.columns)
        if total_baseline <= 0:
            return np.nan
        total_pop = 0
        for col in zone_cols:
            if col in usable_df.columns:
                total_pop += np.interp(
                    t_hours,
                    usable_df["hours_since_t0"].values,
                    usable_df[col].values,
                )
        return total_pop / total_baseline

    inner_zones = ["<5km", "5–10km", "10–15km", "15–20km"]
    total_baseline_inner = sum(baseline.get(c, 0) for c in inner_zones if c in baseline)

    targets = [
        {
            "target_id": "T1",
            "zone": "<5km",
            "metric": "frac_remaining",
            "threshold": 0.40,
            "hours_since_t0": 15.0,
            "notes": "Inner zone rapid self-evacuation (S1 Phase 1); <=40% by t=15h",
        },
        {
            "target_id": "T2",
            "zone": "<5km",
            "metric": "frac_remaining",
            "threshold": 0.10,
            "hours_since_t0": 20.0,
            "notes": "Inner zone near-complete evacuation; <=10% by t=20h",
        },
        {
            "target_id": "T3",
            "zone": "15–20km",
            "metric": "frac_remaining",
            "threshold": 0.50,
            "hours_since_t0": 33.0,
            "notes": "Outer zone delayed departure (S2 Phase 2); <=50% by t=33h",
        },
        {
            "target_id": "T4",
            "zone": "<20km_combined",
            "metric": "frac_remaining",
            "threshold": 0.05,
            "hours_since_t0": 72.0,
            "notes": "Near-complete evacuation of full <20km zone; <=5% by t=72h",
        },
        {
            "target_id": "T5",
            "zone": "all",
            "metric": "exclude",
            "threshold": np.nan,
            "hours_since_t0": np.nan,
            "notes": "Network outage artifact window; exclude from fitting",
        },
    ]

    # Compute empirical values and uncertainty (20% per paper for n~10k)
    for t in targets[:4]:
        if t["zone"] == "<20km_combined":
            emp = get_empirical_sum_at_t_fixed(inner_zones, t["hours_since_t0"])
        else:
            emp = get_empirical_at_t(t["zone"], t["hours_since_t0"])
        t["empirical_value"] = emp
        t["uncertainty"] = 0.20  # ±20% per Hayano paper
        t["usable"] = True

    targets[4]["empirical_value"] = np.nan
    targets[4]["uncertainty"] = np.nan
    targets[4]["usable"] = False

    # Write targets CSV
    TARGETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    targets_df = pd.DataFrame(targets)
    targets_df.to_csv(TARGETS_PATH, index=False)
    print(f"Wrote {TARGETS_PATH}")

    # Summary table and validation
    print("\n=== Calibration target summary ===")
    print(f"{'ID':<4} {'Zone':<16} {'t(h)':<8} {'Threshold':<12} {'Empirical':<12} {'Satisfied':<10}")
    print("-" * 65)

    all_satisfied = True
    for t in targets[:4]:
        sat = t["empirical_value"] <= t["threshold"] if not np.isnan(t["empirical_value"]) else False
        if not sat:
            all_satisfied = False
        emp_str = f"{t['empirical_value']:.4f}" if not np.isnan(t["empirical_value"]) else "N/A"
        print(f"{t['target_id']:<4} {t['zone']:<16} {t['hours_since_t0']:<8.1f} {t['threshold']:<12.2f} {emp_str:<12} {'YES' if sat else 'NO':<10}")

    print(f"\nT5: Network outage window (excluded from fitting)")

    if not all_satisfied:
        print("\n*** WARNING: One or more calibration targets NOT satisfied by empirical data. ***")
        if not args.force:
            print("Cannot proceed to Step 3. Fix data or relax targets. Use --force to override.")
            return 1
        print("Proceeding with --force.")
    else:
        print("\nAll calibration targets satisfied. Proceed to Step 3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
