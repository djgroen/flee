#!/usr/bin/env python3
"""Canonical Quantity-of-Interest definitions for the dual-process Fukushima
campaign. Recreated for Day 8 from the Day 7b ``run_sobol_day7b.py``
definitions; the underlying logic is delegated to that module so the QoI
formulas are identical across Day 4, Day 7, Day 7b, and Day 8.

Public surface used by Day 8 calibration::

    compute_hayano_t4(adf)                 -> float
    compute_mid_ps2_trough(adf)            -> float
    compute_mid_ps2_dip(adf)               -> float
    compute_mid_ps2_recovery(adf)          -> float
    compute_corridor_inland_pct(adf)       -> float
    compute_blend_inner_t7(adf_sys1, adf_blend) -> float
    compute_zone_ps2_timeseries(adf)       -> pandas.DataFrame

``adf`` is the agents-dataframe returned by ``scripts.run_day5_scenarios.
_run_member`` and contains at least the columns: ``decision_mode``,
``agent_id``, ``initial_zone``, ``zone``, ``timestep``, ``location``,
``sys2_weight``.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# NOTE: the four primitives below are copied byte-identically from
# ``scripts/run_sobol_day7b.py`` (Day 7b campaign). They are inlined here so
# that Day 8 calibration does not transitively import SALib (which is only
# needed for Sobol analysis). If the Day 7b primitives ever change, update
# both copies in lock-step. The functions are simple enough that drift is
# easy to audit.

from scripts import run_fukushima_day3 as d3  # noqa: E402

FORK_ORIGINS = {"tomioka", "okuma", "futaba", "namie", "naraha"}
INLAND_NODES = {"kawauchi"}


def _inner_clearance_at_t7(adf: pd.DataFrame) -> float:
    """Fraction of agents starting in the inner zone that arrive at a camp by t=7."""
    inner_ids = adf[adf["initial_zone"] == "inner"]["agent_id"].unique()
    if len(inner_ids) == 0:
        return 0.0
    arrived = adf[(adf["agent_id"].isin(inner_ids)) & (adf["zone"] == "camp")]
    first = arrived.groupby("agent_id")["timestep"].min()
    return float((first <= 7).sum() / len(inner_ids))


def _hayano_t4(adf: pd.DataFrame) -> float:
    """Inner+mid blend departures by t=4 (matches the synoptic Hayano statistic)."""
    im = adf[adf["initial_zone"].isin(["inner", "mid"])]["agent_id"].unique()
    if len(im) == 0:
        return 0.0
    arrived = adf[(adf["agent_id"].isin(im)) & (adf["zone"] == "camp")]
    first = arrived.groupby("agent_id")["timestep"].min()
    return float((first <= 4).sum() / len(im))


def _corridor_inland_pct(adf: pd.DataFrame) -> float:
    fork = adf[(adf["timestep"] == 0) & (adf["location"].isin(FORK_ORIGINS))]
    fork_ids = set(fork["agent_id"].unique())
    if not fork_ids:
        return 0.0
    used = (adf[(adf["agent_id"].isin(fork_ids))
                & (adf["location"].isin(INLAND_NODES))]
            ["agent_id"].unique())
    return float(len(used) / len(fork_ids))


def _ps2_metrics(adf: pd.DataFrame):
    """Return (trough, dip, recovery) for the mid-zone blend P_S2 trace."""
    mid_locs = set(d3.ZONES["mid"])
    mid = adf[adf["location"].isin(mid_locs)]
    if mid.empty:
        return 0.0, 0.0, 0.0
    by_t = mid.groupby("timestep")["sys2_weight"].mean()
    if by_t.empty:
        return 0.0, 0.0, 0.0
    trough = float(by_t.min())
    p0 = float(by_t.iloc[0])
    p28 = float(by_t.loc[28]) if 28 in by_t.index else float(by_t.iloc[-1])
    dip = max(0.0, p0 - trough)
    recovery = max(0.0, p28 - trough)
    return trough, dip, recovery


def _maybe_blend(adf: pd.DataFrame) -> pd.DataFrame:
    """If ``adf`` has a ``decision_mode`` column, restrict to ``blend`` rows.
    Otherwise pass through (for callers who already filtered)."""
    if "decision_mode" in adf.columns:
        sub = adf[adf["decision_mode"] == "blend"]
        return sub if not sub.empty else adf
    return adf


def compute_hayano_t4(adf: pd.DataFrame) -> float:
    return _hayano_t4(_maybe_blend(adf))


def compute_mid_ps2_trough(adf: pd.DataFrame) -> float:
    trough, _, _ = _ps2_metrics(_maybe_blend(adf))
    return trough


def compute_mid_ps2_dip(adf: pd.DataFrame) -> float:
    _, dip, _ = _ps2_metrics(_maybe_blend(adf))
    return dip


def compute_mid_ps2_recovery(adf: pd.DataFrame) -> float:
    _, _, rec = _ps2_metrics(_maybe_blend(adf))
    return rec


def compute_corridor_inland_pct(adf: pd.DataFrame) -> float:
    return _corridor_inland_pct(_maybe_blend(adf))


def compute_blend_inner_t7(adf_sys1: pd.DataFrame,
                           adf_blend: pd.DataFrame) -> float:
    """Behavioural differential: blend inner-zone t=7 clearance minus the
    Sys1-only inner-zone t=7 clearance. >0 means the dual-process layer
    accelerates evacuation in the inner zone."""
    blend = _maybe_blend(adf_blend)
    if "decision_mode" in adf_sys1.columns:
        sys1 = adf_sys1[adf_sys1["decision_mode"] == "sys1_only"]
        if sys1.empty:
            sys1 = adf_sys1
    else:
        sys1 = adf_sys1
    return float(_inner_clearance_at_t7(blend) - _inner_clearance_at_t7(sys1))


def compute_zone_ps2_timeseries(adf: pd.DataFrame,
                                zones: Iterable[str] = ("inner", "mid", "outer"),
                                ) -> pd.DataFrame:
    """Mean ``sys2_weight`` per (timestep, zone) for the blend-mode rows.

    Returns a long-format dataframe with columns ``timestep``, ``zone``,
    ``mean_ps2``, ``n``.
    """
    sub = _maybe_blend(adf)
    rows = []
    for zone in zones:
        locs = set(d3.ZONES.get(zone, []))
        if not locs:
            continue
        z = sub[sub["location"].isin(locs)]
        if z.empty:
            continue
        g = z.groupby("timestep")["sys2_weight"].agg(["mean", "count"])
        for t, r in g.iterrows():
            rows.append({"timestep": int(t), "zone": zone,
                         "mean_ps2": float(r["mean"]),
                         "n": int(r["count"])})
    return pd.DataFrame(rows)


__all__ = [
    "compute_hayano_t4",
    "compute_mid_ps2_trough",
    "compute_mid_ps2_dip",
    "compute_mid_ps2_recovery",
    "compute_corridor_inland_pct",
    "compute_blend_inner_t7",
    "compute_zone_ps2_timeseries",
]
