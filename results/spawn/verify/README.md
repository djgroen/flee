# Decision-Driven Spawning — Verification Bundle (Prompt 4b)

Independent, multi-seed, adversarial verification of the Prompt-4 `dual_process`
spawn mode, run **before** any Day-18 Fukushima/TMI recalibration. This directory
is read-only + test-only: it finds problems, it does not patch the model.

## How to reproduce

```bash
pip install -r results/spawn/verify/requirements.lock   # exact pinned env
bash scripts/spawn/reproduce_all.sh
```

Pinned interpreter/deps: **Python 3.10.x**, `numpy==1.26.4`, `scipy==1.15.3`,
`pandas==2.3.2`, `matplotlib==3.10.5`, `PyYAML==6.0.3`, `networkx==3.4.2`
(full freeze in `requirements.lock`).

## Expected runtime (single modern laptop core)

| Step | Script | ~Runtime |
|------|--------|----------|
| synthetic tests | `test_synthetic.py` | ~20 s |
| gradient-attribution | `test_gradient_attribution.py` | ~20 s |
| multi-seed stats (12 seeds) | `verify_multiseed.py` | ~2.5–3 min |
| formal stats (perm + ANOVA) | `verify_stats.py` | ~30 s |
| adversarial probes | `verify_adversarial.py` | ~50 s |
| non-breaking fingerprint | `verify_nonbreaking.py` | ~8 s per leg |

## Expected output value ranges (from the 12-seed run; a reproduction is "good" if it lands here)

| Quantity | Expected | Source |
|---|---|---|
| Reduction `max|Δcumfrac|` (deterministic) | **0.0010** exactly (seed-invariant) | `multiseed_stats.txt` (1) |
| Reduction stochastic noise | mean ≈ 0.005, ≤ ~0.011 | `multiseed_stats.txt` (1) |
| Depletion `Σspawned ≤ pop` violations | **0 / all runs** (any violation = BLOCKER) | `multiseed_stats.txt` (2) |
| Ψ-ordering gap (ring, c=0.2) | mean ≈ **+0.039**, SD ≈ 0.004, range ≈ [0.032, 0.044], **> 0 in every seed** | `multiseed_stats.txt` (3) |
| Scale-invariance `|Δ|` (hasten 1/4/8) | ≤ ~0.003 | `multiseed_stats.txt` (4) |
| Gradient blend Ψ-corr (per steepness) | ≈ **−0.12 to −0.13**, SD ≈ 0.01, always clearly negative | `multiseed_stats.txt` (5) |
| Gradient sys1_only Ψ-corr | ≈ **0** (±0.01), never significantly negative | `multiseed_stats.txt` (5) |
| Permutation p (blend, Ψ-gap) | **p ≈ 0.001** (permutation floor) at every steepness | `statistical_tests.txt` (1) |
| Permutation p (sys1_only) | large / not significant (≈ 0.28–0.75) | `statistical_tests.txt` (1) |
| `step:mode` interaction | huge F, p ≈ 0 (n≈2.7e5) but **small effect** (partial η² ≈ 0.005) | `statistical_tests.txt` (2) |
| Bin sensitivity (3–15 bins) | Ψ-corr stays ≈ −0.13 to −0.14, no sign flip | `adversarial.txt` (4.1) |
| Extreme params | **0** NaN, **0** out-of-range hazards, **0** invalid sims | `adversarial.txt` (4.2) |
| Non-breaking diff | **exactly 0 lines** (all legacy modes + Fukushima) | `non_breaking_diff.txt` |

## How to interpret a FAILED reproduction

- **Non-breaking diff ≠ 0 lines** → STOP. A legacy mode changed. This is a blocker;
  do not proceed to Day 18. Re-check that `flee/spawning.py` diff is still additive
  (`git diff HEAD --numstat` should show `120  0`).
- **Any depletion violation (`Σspawned > pop`)** → STOP and report immediately; the
  reservoir accounting is broken.
- **Ψ-ordering gap ≤ 0 in any seed, or blend Ψ-corr not negative** → the headline
  architectural signal is not robust; recalibration should not lean on it.
- **NaN / out-of-range hazard in the extreme-param probe** → numerical bug in the
  hazard blend; STOP.
- **Small numeric drift only** (e.g. Ψ-corr −0.11 vs −0.13, gap 0.036 vs 0.039)
  across a *different* interpreter/BLAS is acceptable "match in kind"; exact
  byte-reproduction is only guaranteed on the pinned env + same seeds.

## Files

| File | Task | Contents |
|---|---|---|
| `code_review.txt` | 0 | Cold PR review; answers to the 5 questions + findings F1–F4 |
| `rerun_diff.txt` | 1 | Same-seed byte-identical + different-seed match-in-kind |
| `multiseed_stats.txt` | 2 | Mean/SD/range over 12 seeds for all headline numbers |
| `corr_vs_steepness.{png,pdf}` | 2 | Ψ-corr vs steepness, blend vs sys1_only, error bars |
| `multiseed_raw.npz` | 2 | Raw per-seed arrays (consumed by Task 3) |
| `statistical_tests.txt` | 3 | Permutation test + `mode×steepness` interaction (F, df, effect size) |
| `adversarial.txt` | 4 | Bin sensitivity, extreme params, counterexample search |
| `non_breaking_diff.txt` | 5 | Source (+120/−0) + zero-line trajectory diff + runtime config values |
| `requirements.lock` | 6 | Full pinned dependency freeze |
| `day18_preregistration.md` | 7 | Pre-committed Day-18 tolerance/fallback/identifiability rules |

## Key findings to carry into Day 18

1. **All headline numbers are stable and pass** (multi-seed, permutation, ANOVA).
2. **Refinement (Task 4.3, honest negative):** only the **Ψ-ordering** is uniquely
   architectural. The Zeigler **timing/distance crossover** is largely
   gradient/schedule-driven and is reproduced by the `sys1_only` baseline — the
   paper should attribute crossover *timing* to the gradient and reserve the
   architectural claim for the Ψ-ordering.
3. **Effect-size caveat (Task 3):** the `step:mode` interaction is unambiguously
   significant but explains only ~0.5% of per-agent experience variance; lead with
   the permutation test on the aggregate gap, not the per-agent p-value.
4. **F1 (latent, HIGH for Day 18):** `dual_process` module-globals (`_pools`,
   `__dual_process_configured`) are reset only by the test harness, not production
   `run.py`. A Day-18 calibration loop **must** call
   `spawning.reset_dual_process_state()` per model evaluation, or the reservoir
   leaks between fits.
5. **F2:** `spawn_dynamics.return_to_pool` (Task-2.5 return composition) is defined
   but **never called** and **untested**; enable_return re-entry is not wired. Fine
   for single-crisis nuclear runs; must be wired + tested before return-enabled use.

## Locked-params config: still has no single committed home (Task 6.3 — flag, do not fix)

Confirmed still true. The canonical locked cognitive parameters
`α=1.6667, β=2.1667, κ=18.407` currently exist in **two duplicated places** and no
canonical config that the spawn path reads:

- `results/tmi/day15_locked_params.json` — a **TMI-domain results artifact** (not a
  simulation config), and
- hardcoded in `scripts/spawn/spawn_harness.py` (`LOCKED = {...}`).

Meanwhile `conflict_input/fukushima_2011/simsetting.yml` sets **different** values
(`alpha: 2.0, beta: 4.0, kappa: 1.0`) under `move_rules.s1s2_model`.

**What's missing:** a single committed config (e.g. `conflict_input/_shared/locked_params.yml`
or a `flee` constants module) that both the production `dual_process` run path and
the test harness read, so the locked values are defined once. Until then, Day-18
runs risk silently using the wrong (Fukushima-simsetting) α/β/κ. Fix in a follow-up
commit before Day-18 calibration.
