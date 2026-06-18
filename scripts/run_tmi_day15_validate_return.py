#!/usr/bin/env python3
"""Day 15 Task C/E -- return-mechanism checkpoint + return-curve validation.

Runs the v2 network with the LOCKED conflict-dependent System-1 form and
enable_return=True over an EXTENDED horizon (conflict schedule decays to 0 past
T_SCHED; the return phase runs at c~0 so Omega is recovered and return is
S2-driven). Records:
  * camp population per timestep        -> Checkpoint C (build then draw down)
  * cumulative % of evacuees returned   -> Task E vs empirical 53/90/98 %
  * P_S2 of returners vs non-returners  -> "return is S2-driven"

Timestep -> real-time: 1 step = 8 h (event spacing t10 Fri 03-30 -> t16 Sun
04-01); 1 week = 21 steps. Return onset = Carter visit t=16. Week-k boundary for
the cumulative-return curve = t16 + 21*k.

Outputs: results/tmi/day15_return_curve.csv  + printed Checkpoint C / Task E verdict.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from scripts import tmi_common_day15 as tc  # noqa: E402

RES = REPO / "results" / "tmi"
ALPHA, BETA, KAPPA = tc.FROZEN_ALPHA, tc.FROZEN_BETA, tc.FROZEN_KAPPA
MODE = "blend"
LOCK_BASE, LOCK_CMAX = 0.05, 0.50      # Task B2 locked conflict-dependent form
RETURN_START_T = 16                    # Carter visit
STEPS_PER_WEEK = 21                    # 8 h/step
EMPIRICAL_RETURN = {1: 0.53, 2: 0.90, 3: 0.98}


def _psi(x, alpha=ALPHA):
    return 0.1 + 0.9 * (1.0 - np.exp(-alpha * max(0.0, x)))


def camp_pop_and_return(adf: pd.DataFrame):
    """Return (camp_pop_series, cum_return_frac_series, evacuee_ids, return_time,
    exp_returners, exp_nonreturners)."""
    t_vals = sorted(adf["timestep"].unique())
    exp_by_agent = (adf.groupby("agent_id")["experience_x"].first().to_dict())
    camp_pop = {}
    ever_camp = set()
    returned = set()
    return_time = {}     # agent_id -> first timestep back home after a camp stay
    cum_return = {}
    for t in t_vals:
        sub = adf[adf["timestep"] == t]
        camp_now = set(sub[sub["in_camp"]]["agent_id"])
        camp_pop[t] = len(camp_now)
        ever_camp |= camp_now
        # agents back home this step that had been in a camp
        home_now = sub[(sub["at_home"]) & (~sub["in_camp"])]
        for aid in home_now["agent_id"]:
            if aid in ever_camp and aid not in returned:
                returned.add(aid)
                return_time[aid] = t
        cum_return[t] = len(returned)
    n_evac = max(1, len(ever_camp))
    cum_frac = {t: cum_return[t] / n_evac for t in t_vals}
    exp_ret = [exp_by_agent.get(a, 0.0) for a in returned]
    exp_non = [exp_by_agent.get(a, 0.0) for a in (ever_camp - returned)]
    return (pd.Series(camp_pop), pd.Series(cum_frac), ever_camp, return_time,
            exp_ret, exp_non)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    t_max = 80
    seeds, n_agents = [0, 1, 2, 3, 4], 1000
    if args.quick:
        seeds, n_agents, t_max = [0, 1], 600, 70

    print("=" * 76)
    print("Day 15 Task C/E -- return mechanism (enable_return=True) on v2")
    print(f"  conflict-dependent System-1 base={LOCK_BASE} cmax={LOCK_CMAX} "
          f"(a/b/k LOCKED)")
    print(f"  t_max={t_max} seeds={seeds} n_agents={n_agents} "
          f"return_start_t={RETURN_START_T}")
    print("=" * 76)

    camp_list, ret_list = [], []
    exp_ret_all, exp_non_all, return_times_all = [], [], []
    for s in seeds:
        with contextlib.redirect_stdout(io.StringIO()):
            adf, _arr, _mob = tc.run_one(
                MODE, n_agents, t_max, s, alpha=ALPHA, beta=BETA, kappa=KAPPA,
                cmc=LOCK_BASE, enable_panic_clamp=False, network=tc.TMI_V2,
                cmc_conflict_dependent=True, cmc_max=LOCK_CMAX,
                enable_return=True,
                return_params={"return_start_t": RETURN_START_T,
                               "return_conflict_threshold": 0.15,
                               "return_rate": 0.5})
        cp, cr, evac, rt, exp_ret, exp_non = camp_pop_and_return(adf)
        camp_list.append(cp)
        ret_list.append(cr)
        exp_ret_all += exp_ret
        exp_non_all += exp_non
        return_times_all += list(rt.values())
        print(f"  seed {s}: peak camp pop {cp.max():.0f} @t{cp.idxmax()}  "
              f"end camp pop {cp.iloc[-1]:.0f}  returned {cr.iloc[-1]*100:.0f}%")

    camp_mean = pd.concat(camp_list, axis=1).mean(axis=1)
    ret_mean = pd.concat(ret_list, axis=1).mean(axis=1)

    peak_t = int(camp_mean.idxmax())
    peak_pop = float(camp_mean.max())
    end_pop = float(camp_mean.iloc[-1])
    builds = peak_pop > camp_mean.iloc[0] + 1
    draws_down = end_pop < 0.5 * peak_pop and peak_t <= RETURN_START_T + STEPS_PER_WEEK
    cond_c = builds and (end_pop < peak_pop)

    # week-k cumulative return
    weeks = {}
    for k in (1, 2, 3):
        tt = RETURN_START_T + STEPS_PER_WEEK * k
        tt = min(tt, int(ret_mean.index.max()))
        weeks[k] = float(ret_mean.loc[tt])

    out = pd.DataFrame({"timestep": camp_mean.index,
                        "camp_pop_mean": camp_mean.values,
                        "cum_return_frac_mean": ret_mean.reindex(camp_mean.index).values})
    out.to_csv(RES / "day15_return_curve.csv", index=False)

    # S2-driven signal: returners deliberate (higher Psi -> higher P_S2 hazard);
    # in the return window c_home~0 so P_S2 ~ Psi(experience). Also returns must
    # concentrate after the Omega-recovery onset (t>=16 / post-Carter).
    ps2_ret = float(_psi(np.mean(exp_ret_all))) if exp_ret_all else float("nan")
    ps2_non = float(_psi(np.mean(exp_non_all))) if exp_non_all else float("nan")
    median_return_t = float(np.median(return_times_all)) if return_times_all else float("nan")
    s2_driven = (ps2_ret > ps2_non) and (median_return_t >= RETURN_START_T)

    print("\n" + "=" * 76)
    print("CHECKPOINT C (camp builds during crisis, draws down after t~16):")
    print(f"  camp pop: start {camp_mean.iloc[0]:.0f} -> peak {peak_pop:.0f} "
          f"@t{peak_t} -> end {end_pop:.0f}")
    print(f"  builds: {'yes' if builds else 'no'}   draws down after peak: "
          f"{'yes' if end_pop < peak_pop else 'no'}")
    print(f"  CHECKPOINT C: {'PASS' if cond_c else 'FAIL'}")
    print("\nTASK E -- cumulative return vs empirical (53/90/98 %):")
    for k in (1, 2, 3):
        print(f"  week {k} (t={RETURN_START_T + STEPS_PER_WEEK*k}): "
              f"model {weeks[k]*100:.0f}%  vs empirical "
              f"{EMPIRICAL_RETURN[k]*100:.0f}%")
    print(f"\n  return is S2-driven: P_S2(returners)~{ps2_ret:.3f} vs "
          f"P_S2(non-returners)~{ps2_non:.3f}; median return t={median_return_t:.0f} "
          f"(onset {RETURN_START_T})  -> {'S2-DRIVEN' if s2_driven else 'NOT confirmed'}")
    print("=" * 76)

    verdict = {
        "checkpoint_c_pass": bool(cond_c),
        "camp_pop_start": float(camp_mean.iloc[0]),
        "camp_pop_peak": peak_pop, "camp_pop_peak_t": peak_t,
        "camp_pop_end": end_pop,
        "week1_return": weeks[1], "week2_return": weeks[2], "week3_return": weeks[3],
        "empirical_week_1_2_3": [0.53, 0.90, 0.98],
        "ps2_returners_mean": ps2_ret, "ps2_nonreturners_mean": ps2_non,
        "median_return_t": median_return_t,
        "return_is_s2_driven": bool(s2_driven),
        "timestep_mapping": "1 step = 8 h; 1 week = 21 steps; return onset t=16",
        "locked_system1": {"base": LOCK_BASE, "cmax": LOCK_CMAX},
    }
    (RES / "day15_return_verdict.json").write_text(json.dumps(verdict, indent=2))
    print(f"[return] curve -> {RES / 'day15_return_curve.csv'}; "
          f"verdict -> {RES / 'day15_return_verdict.json'}")


if __name__ == "__main__":
    main()
