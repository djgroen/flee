# Day-18 Recalibration — Pre-Registration

**Status:** PRE-REGISTERED. Written and committed **before** any Day-18 fit is run
against real Fukushima/TMI data. The decision rules below are fixed in advance so
they cannot be quietly adjusted after seeing how the real fit looks.

**Date committed:** 2026-07-01
**Author:** verification pass (Prompt 4b), for review by M. Jackson; Flee coauthors
(Groen / Suleimenova) to countersign the `spawning.py` integration read.
**Scope:** the `conflict_spawn_mode = "dual_process"` decision-driven spawner.
**Parameters in play:**
- Locked cognitive params (from `results/tmi/day15_locked_params.json`, Fukushima
  transfer, *not* to be retuned casually): **α = 1.6667, β = 2.1667, κ = 18.407**.
- **ρ** (System-1 threat-sensitivity, `λ_S1 = 1 − exp(−ρc)`) — **NEW, uncalibrated**;
  Day-18 is its first real fit. Placeholder in all synthetic tests = 2.0.

κ is held fixed at the locked value throughout Day 18 (it governs the S2 move
probability σ, which the spawn recalibration does not re-identify).

---

## 1. Pre-specified tolerance band: "α, β re-fit near locked values"

**Criterion (chosen in advance):** α and β are declared "consistent with locked"
iff **both**:

- **(a) Point-estimate band:** the Day-18 MAP/point estimate lies within **±20%**
  of the locked value, i.e. α̂ ∈ [1.333, 2.000] and β̂ ∈ [1.733, 2.600]; **and**
- **(b) CI overlap:** the Day-18 95% interval for each parameter overlaps the
  Day-15 locked interval (or, if Day-15 gave a point value only, contains the
  locked point value).

**Justification for ±20%:** the Day-15 grid that produced the locked values used
coarse spacing (α grid step ≈ 0.5–1.0 around 1.67; β grid step ≈ 1.0 around 2.17),
so the locked point is itself only resolved to roughly ±one grid cell ≈ 15–30%.
A ±20% band is inside that grid resolution — tight enough to catch a genuine shift
(e.g. α doubling) but not so tight that it flags mere grid-quantization noise. The
CI-overlap clause (b) guards against a deceptively-narrow point estimate that
happens to sit at the band edge. Both must hold; passing only one is a "shift".

---

## 2. Pre-specified fallback if α/β do NOT land near locked values

Decision rule, fixed in advance (no post-hoc switching):

1. **If both α and β pass §1** → accept the joint fit; report ρ̂ with its CI as the
   headline new parameter. Proceed.
2. **If α and/or β fail §1** → do **NOT** silently accept the shifted values.
   Instead run **both** of the following and report the pair as a finding:
   - **(Primary) Constrained fit:** hold α, β fixed at the Day-15 locked values and
     fit **ρ only**. This is the headline Day-18 estimate. Rationale: the locked
     α/β are a cross-domain transfer we committed to defend; re-opening them on a
     single new data slice risks overfitting ρ↔α↔β collinearity (see §3).
   - **(Secondary, reported as sensitivity) Joint fit:** refit all three (α, β, ρ)
     and report the **magnitude and direction of the α/β shift** explicitly, with
     CIs, as a stated finding — not as the accepted parameters.
   The paper then reports the constrained-fit ρ as primary and the joint-fit shift
   as a robustness/limitations item. Which of the two becomes "the" number is
   decided by §3's collinearity check, pre-committed below — not by which looks
   nicer.
3. **Tie-breaker (pre-committed):** if §3 shows concerning collinearity (|corr|>0.7
   between any two of α, β, ρ), the **constrained fit (2-Primary) is authoritative**
   and the joint fit is demoted to sensitivity analysis. If §3 shows no concerning
   collinearity, the **joint fit is authoritative** and the shift (if any) is
   reported as a real, identifiable result.

---

## 3. Identifiability check to run FIRST (before any real data is touched)

**Synthetic parameter-recovery test — the very first Day-18 action.**

Procedure (must use the *identical* fitting pipeline Day-18 will apply to real data):

1. Fix known ground-truth **α\* = 1.6667, β\* = 2.1667, ρ\* = 2.0** (and κ locked).
2. Generate synthetic decision-driven spawn data from the `dual_process` spawner on
   the Fukushima network topology + conflict schedule (same `reset_dual_process_state()`
   discipline per run — see the F1 note below), at ≥ 10 seeds.
3. Refit **all three (α, β, ρ) jointly** via the same objective/optimizer Day-18 will
   use on the real data.
4. Report, per parameter:
   - **recovery error** = (θ̂ − θ\*)/θ\* (bias) and the SD of θ̂ across seeds; **and**
   - the **α–β–ρ correlation matrix and covariance** from the fit (posterior samples
     if Bayesian, or the inverse-Hessian / Fisher information if optimizing).

**Pre-specified pass thresholds (fixed now):**
- **Recovery:** |bias| ≤ **10%** for each of α, β, ρ, and the across-seed SD ≤ 15% of
  the true value. Larger → the procedure cannot even recover known parameters, so no
  real-data fit is trustworthy: STOP and fix the pipeline before touching real data.
- **Concerning collinearity:** **|corr| > 0.7** between **any** two of α, β, ρ in the
  fit. If triggered, the parameters are not jointly identifiable from spawn data
  alone; per §2.3 the **constrained (ρ-only) fit becomes authoritative** and the
  joint α/β/ρ fit is reported only as a sensitivity analysis with an explicit
  non-identifiability caveat.

**Why 0.7:** it is the conventional "strong correlation" threshold and, at |corr|>0.7,
> ~50% of one parameter's fitted variance is shared with another — enough that a
reported α/β "shift" could be a ρ↔α trade-off artifact rather than a real effect.
Anticipated risk: α (capacity sensitivity via Ψ) and ρ (S1 intensity) both modulate
*early* departures, so an α–ρ ridge is the most likely offender; the check is
designed to catch exactly that before it contaminates the headline.

---

## Required pre-conditions carried from verification (must be satisfied before Day 18)

- **F1 (blocker for the calibration loop):** the Day-18 fitting harness **must call
  `spawning.reset_dual_process_state()` at the start of every model evaluation.** The
  `dual_process` reservoirs are module-globals reset only by the test harness, not by
  production `run.py`; a calibration loop that omits the reset leaks a depleted
  reservoir between fits and silently biases the objective. Verify this in the harness
  before running §3.
- **Locked-params single home:** resolve the duplicated locked α/β/κ (results JSON +
  hardcoded harness dict; Fukushima `simsetting.yml` currently disagrees at
  2.0/4.0/1.0) into one committed config the fit reads, so §1's "locked value" is
  unambiguous. (Flagged in `README.md`; fix in a follow-up commit.)

## Go/No-Go (pre-committed)

Day-18 real-data calibration may begin **only after**: (i) Task-5 non-breaking diff is
zero (✔ this bundle), (ii) Task-2 multi-seed headline numbers are stable (✔ this
bundle), (iii) this file is committed (this commit), (iv) §3's synthetic-recovery test
passes its thresholds, and (v) the F1 reset is wired into the fitting harness.
