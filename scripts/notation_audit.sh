#!/usr/bin/env bash
#
# notation_audit.sh -- Day 7b notation unification gate.
#
# Verifies that the codebase no longer collides cognitive System-1 / System-2
# tokens (s1_only, s2_weight, s2_activation, bare S1) with sobol first-order
# index notation. Prints offending lines and exits non-zero on any hit.
#
# Excluded paths (intentional):
#   - flee/venv/                          third-party dependencies
#   - scripts/_archived_*/                pre-rename historical scripts
#   - **/__pycache__/                     compiled bytecode
#
# Allowed exemptions on a matching line (filtered by inner grep):
#   - "sobol"   the line is talking about sobol indices, not cognitive systems
#   - "saltelli"/"sensitivity"/"SALib"    sobol library context
#   - "S1_conf"  legacy SALib raw output key (only allowed inside one
#                remap line per script)
#   - "#.*Sobol" or "#.*sobol"  in-line comment annotation
#
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PATTERN='\bS1\b\|\bs1_only\b\|\bs2_weight\b\|\bs2_activation\b'
EXEMPT='sobol\|saltelli\|sensitivity\|SALib\|S1_conf\|#.*[Ss]obol'

echo "[audit] scanning flee/ scripts/ tests/ for cognitive-S1/S2 tokens..."

HITS=$(
  grep -rn \
    --include='*.py' \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude-dir=_archived_docx_builders \
    --exclude-dir=_archived_legacy_sobol \
    "$PATTERN" \
    "$ROOT/flee" "$ROOT/scripts" "$ROOT/tests" 2>/dev/null \
  | grep -v "$EXEMPT" || true
)

if [ -n "$HITS" ]; then
  echo "[audit] FAIL -- cognitive S1/S2 tokens still present:"
  echo "$HITS"
  exit 1
fi

echo "[audit] no cognitive-S1/S2 hits in production sources."

# Second gate: raw SALib 'S1' dict access outside an explicit remap line.
echo "[audit] scanning scripts/ for raw SALib S1 keys..."

RAW_HITS=$(
  grep -rn \
    --include='*.py' \
    --exclude-dir=_archived_docx_builders \
    --exclude-dir=_archived_legacy_sobol \
    "'S1'\|\"S1\"" \
    "$ROOT/scripts" 2>/dev/null \
  | grep -v "remap\|raw\[.S1.\][[:space:]]*#\|# *sobol\|# *SALib" || true
)

if [ -n "$RAW_HITS" ]; then
  echo "[audit] FAIL -- raw SALib S1 keys outside remap line:"
  echo "$RAW_HITS"
  exit 1
fi

echo "[audit] no raw SALib S1 keys outside remap lines."
echo "[audit] PASS"
exit 0
