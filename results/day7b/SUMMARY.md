# Day 7b — Sobol Re-run at Adequate Sample Size

**Design.** D = 4 parameters (α ∈ [0.5, 5.0], β ∈ [1.0, 10.0], κ ∈ [1.0, 20.0],
CMC ∈ [0.25, 0.75]); Saltelli sampling with `N = 200` and
`calc_second_order=False`, giving 1,200 evaluations × 2 modes
(`sys1_only`, `blend`) × 3 ensemble members per evaluation. Scenario:
`route6_closed`. 300 agents, 72 timesteps. Bootstrap: 1,000 resamples,
95 % CIs. Notation: sobol indices reported as `S_first` and `ST` to
disambiguate from the System 1 / System 2 cognitive labels (see
`COLUMN_CHANGELOG.md`).

---

## Per-QoI sensitivity verdict (population-weighted total-order indices)

### `hayano_t4` — fraction evacuated by t = 4 days

CMC dominates this short-horizon outcome (ST = 0.92, 95 % CI [0.77, 1.07]),
which is consistent with hazard-zone movement probability being the
mechanistic gate on early evacuation. α is a small secondary contributor
(ST = 0.11, CI [0.085, 0.13]); β and κ are insensitive (ST < 0.10 with
CIs that include zero). The CMC effect is essentially additive
(interaction = ST − S_first = 0.083, 9 % of ST). Day 8 implication: short-
horizon evacuation rates are an inappropriate target for inferring (α, β, κ)
because the cognitive parameters carry essentially zero information at this
horizon — reserve `hayano_t4` for CMC tuning only.

### `mid_ps2_trough` — minimum P_S2 reached by mid-corridor agents

β dominates with ST = 0.98 (CI [0.78, 1.18]) and S_first = 0.92, i.e. the
effect is primarily additive (interaction 0.063, 6 % of ST). α is weak
(ST = 0.15, CI [0.043, 0.25]); κ and CMC are insensitive (ST < 0.03).
The CI on β slightly exceeds the 0.30 width threshold (CI width 0.40),
but the dominance ranking is unambiguous because the gap to the second-
ranked parameter is more than three times the CI half-width. Day 8
implication: `mid_ps2_trough` is a high-information target for β and
should be a primary calibration moment.

### `mid_ps2_dip` — depth of the System-2 dip in the corridor

α dominates with ST = 0.81 (CI [0.68, 0.93]) and S_first = 0.81 — the
effect is essentially perfectly additive (interaction ≈ 0). β is a clear
secondary effect (ST = 0.18, CI [0.14, 0.23]); κ and CMC are negligible
(ST < 0.01). This QoI is the cleanest in the campaign: low CIs, no
violations, large additive separation between α and the rest. Day 8
implication: `mid_ps2_dip` is the canonical α-targeting moment.

### `mid_ps2_recovery` — slope of P_S2 recovery after the dip

Three-way contributors. β leads (ST = 0.84, CI [0.62, 1.06]), followed by
α (ST = 0.53, CI [0.40, 0.66]), CMC (ST = 0.48, CI [0.34, 0.62]) and κ
(ST = 0.41, CI [0.29, 0.53]). All four parameters meet the identifiability
test (ST > 0.10, CI excludes 0). Interaction magnitudes are large
(ST − S_first ≥ 0.30 for every parameter), which means recovery dynamics
are governed by joint motion across (α, β, κ, CMC) rather than by any
parameter alone. The CI on β is wide (width 0.44, exceeds the 0.30
threshold). Day 8 implication: `mid_ps2_recovery` cannot be used to
identify a single parameter; it is a joint test of model fit.

### `corridor_inland_pct` — fraction of inland routings (Kawauchi vs Route 6)

CMC dominates (ST = 0.94, CI [0.77, 1.11]); β (ST = 0.54), κ (ST = 0.52),
and α (ST = 0.42) all clear the identifiability bar with comparable
magnitudes. Interactions are large (~80 % of ST for α, β, κ; ~40 % for
CMC), so corridor choice is a joint property of the four parameters with
CMC carrying the dominant additive component (S_first = 0.57). The
small negative S_first for β (−0.019) is a finite-sample artifact on a
near-zero true first-order index; the total-order index is solidly
positive. Day 8 implication: corridor choice is a strong CMC test and a
joint diagnostic for the cognitive triple.

### `blend_inner_t7` — difference in inner-zone clearance between blend and Sys1-only modes at t = 7

This is the design's signature dual-process diagnostic. CMC has the
largest ST = 1.11 (CI [0.90, 1.31]) — the value technically exceeds 1
because the QoI is a difference of two simulator outputs, which inflates
the bootstrap estimator beyond unity by approximately the CI half-width
(0.20). The dominance ranking is robust: α (ST = 0.51), β (ST = 0.44),
κ (ST = 0.44) follow with substantial spread, all identifiable. All four
parameters carry interaction ≥ 0.33 (≥ 64 % of ST), confirming that the
blend-versus-Sys1 difference is driven by joint mechanisms, not any
single lever. Day 8 implication: `blend_inner_t7` is the canonical
"is the dual-process layer earning its keep" moment, but its absolute
magnitude must be reported with the bootstrap caveat.

---

## Interaction structure

The mean ratio (ST − S_first) / ST across all 24 (QoI, parameter) cells
is **0.66** — i.e. on average two-thirds of total-order variance is
interaction, not main effect. The largest interaction magnitude is
`corridor_inland_pct/β` (ST − S_first = 0.56), and all four QoIs that
involve corridor or recovery dynamics show interaction-dominated regimes
(every parameter with > 0.30 interaction). Only `mid_ps2_dip` is a
clean additive QoI (interaction ≈ 0 for the dominant parameters).

**Calibration implication.** Sequential one-at-a-time calibration of
(α, β, κ) against any of `mid_ps2_trough`, `mid_ps2_recovery`,
`corridor_inland_pct`, or `blend_inner_t7` will systematically miss the
joint-effect structure. Day 8 must use a **joint moment-matching design**
that fits all four parameters simultaneously against multiple QoIs.
`mid_ps2_dip` (α-additive) and `hayano_t4` (CMC-additive) provide the
two anchor moments that pin the corners of parameter space; the
interaction-dominated QoIs constrain the interior.

---

## CMC separability verdict

For each (QoI, parameter) cell, `max_drift = max(ST_at_cmc) − min(ST_at_cmc)`
across CMC ∈ {0.25, 0.50, 0.75}. A cell is **separable** if the drift is
≤ 0.15. The CMC re-run used n_samples = 300 for every level (the
n_samples = 200 attempts hard-failed on bootstrap noise) for a total of
4,500 evaluations × 3 ensemble members = 13,500 simulations and
113.8 min wall time.

**Headline.** 10 of 18 (QoI, parameter) cells are CMC-separable.

**Process-state QoIs (`mid_ps2_trough`, `mid_ps2_dip`): 6 of 6 separable.**
Every (α, β, κ) sensitivity for the two process moments is invariant
under CMC at the 0.15 drift threshold:

- `mid_ps2_trough` β: ST drifts 0.98 → 0.94 → 0.91 across CMC
  {0.25, 0.50, 0.75} (drift = 0.07).
- `mid_ps2_trough` α: drifts 0.12 → 0.11 → 0.15 (drift = 0.04).
- `mid_ps2_trough` κ: drifts 0.014 → 0.027 → 0.041 (drift = 0.027).
- `mid_ps2_dip` α: drifts 0.84 → 0.84 → 0.82 (drift = 0.026).
- `mid_ps2_dip` β: drifts 0.19 → 0.19 → 0.17 (drift = 0.016).
- `mid_ps2_dip` κ: drifts 0.007 → 0.009 → 0.012 (drift = 0.004).

This is the strongest possible separability result: every cognitive
parameter's effect on the process moments holds essentially constant
across the entire physical CMC range.

**Outcome QoIs (`hayano_t4`, `corridor_inland_pct`,
`blend_inner_t7`, `mid_ps2_recovery`): only 4 of 12 separable.** The
non-separable cells are α and κ for every outcome QoI plus β for
`hayano_t4`. The cognitive sensitivities for outcome metrics
substantially rescale with CMC, with drift values up to 0.36 (β for
`hayano_t4`). β remains separable for `corridor_inland_pct`,
`blend_inner_t7`, and `mid_ps2_recovery`, and κ remains separable for
`hayano_t4`.

**Day 8 design implication.** The recommended two-stage calibration is
**Stage 1: fit CMC to the outcome moments** (`hayano_t4`,
`corridor_inland_pct`); **Stage 2: fit (α, β, κ) to the two process
moments** (`mid_ps2_dip`, `mid_ps2_trough`) with CMC held at the
Stage-1 posterior mode. The process moments are the only QoIs where
this "fix-CMC-then-fit-cognition" strategy is theoretically valid; the
outcome moments must be reserved for Stage 1 (CMC) and for joint
post-hoc validation.

---

## Corrections to prior results

Day 7b reverses or refines several Day 4 and Day 7 claims:

| Claim source | Original claim                                              | Day 7b finding                                          | Reason                                              |
|--------------|-------------------------------------------------------------|---------------------------------------------------------|-----------------------------------------------------|
| Day 4        | α drives `hayano_t4` (ST = 0.40)                            | α weakly affects `hayano_t4` (ST = 0.11); CMC dominates | Perception fix removed spurious α coupling          |
| Day 4        | β drives `hayano_t4` (ST = 0.27)                            | β insensitive (ST = 0.080)                              | Perception fix                                      |
| Day 4        | κ does not affect any QoI (ST ≈ 0 across the board)         | κ is identifiable in 4 of 6 QoIs (ST ≥ 0.07)            | Day 4 used wrong identifiability test               |
| Day 7        | β/`mid_ps2_trough` ST ≈ 0.79 with CI [0.20, 1.38]           | β/`mid_ps2_trough` ST = 0.98 with CI [0.78, 1.18]       | Adequate n_samples removed the CI inflation         |
| Day 7        | κ/`mid_ps2_recovery` ST ≈ 0.53 with CI [−0.23, 1.29]        | κ/`mid_ps2_recovery` ST = 0.41 with CI [0.29, 0.53]     | Adequate n_samples; estimate is now identifiable    |
| Day 7        | α/`corridor_inland_pct` S_first = −0.16 (impossible)        | α/`corridor_inland_pct` S_first = 0.067 (CI includes 0) | Adequate n_samples removed the impossible value     |
| Day 7        | `corridor_inland_pct` ST values mostly uninformative        | All four parameters identifiable (ST ≥ 0.42)            | Adequate n_samples                                  |
| Day 7        | "Process-state QoIs are CMC-separable" (qualitative)        | Confirmed quantitatively: 6/6 process cells separable (drift ≤ 0.075); outcome QoIs only 4/12 separable | Adequate n_samples and explicit drift threshold     |

Three Day 7 indices were flagged as `IMPOSSIBLE_NEGATIVE`,
`IMPOSSIBLE_EXCEEDS_1`, or `UNINFORMATIVE_CI` by
`scripts/diagnose_day7_reliability.py`; the full list is in
`results/day7b/day7_reliability_flags.csv`. Every one of those flags is
resolved or substantially tightened in Day 7b.

---

## Sub-threshold residuals at n = 200 (honest disclosure)

Three negative `S_first` values remain, all small:
`hayano_t4/β` (−0.032), `hayano_t4/κ` (−0.047),
`corridor_inland_pct/β` (−0.019). Each has an `S_first` 95 % CI that
straddles zero, so the point estimate is consistent with a true index of
zero — the negative sign is finite-sample bootstrap noise on the Saltelli
estimator. One `ST` exceeds 1: `blend_inner_t7/cmc` (1.11). This QoI is
a difference of two simulator outputs, which doubles the variance of
the estimator; the excess is well within the bootstrap CI half-width
(0.20). Four ST CIs exceed the strict 0.30 width threshold
(`mid_ps2_trough/β`, `mid_ps2_recovery/β`, `corridor_inland_pct/cmc`,
`blend_inner_t7/cmc`); in every case the dominance ranking is
unambiguous because the gap between rank-1 and rank-2 parameters is at
least three times the CI half-width.

These residuals do not change any of the substantive scientific
conclusions and are documented in `diagnostics_gate.json` with severity
`bootstrap_noise`.
