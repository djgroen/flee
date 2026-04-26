"""
Compatibility shim — the canonical module is now :mod:`flee.dual_process_model`.

The rename happened in Day 7b to remove the collision between the cognitive
"System 1 / System 2" notation (Kahneman 2011) and the sobol first-order
and total-order index notation (``S_first`` and ``ST`` in the post-Day-7b
remap convention). See ``results/day7b/COLUMN_CHANGELOG.md`` for full
notation rules.

This shim re-exports every public symbol from the new module so legacy
imports continue to work, but it should not be used by new code.
"""

from flee.dual_process_model import (  # noqa: F401
    PSI_MIN,
    RadiationField,
    compute_capacity,
    compute_deliberation_weight,
    compute_opportunity,
    compute_s2_move_probability,
)

__all__ = [
    "PSI_MIN",
    "RadiationField",
    "compute_capacity",
    "compute_deliberation_weight",
    "compute_opportunity",
    "compute_s2_move_probability",
]
