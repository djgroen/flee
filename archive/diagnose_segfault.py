# ARCHIVED: 2025-03-14
# Reason: Import-chain diagnostic for segfault debugging on macOS. Utility script, not part of active test suite.
# Do not import or run this file from the active test suite.

# tests/diagnose_segfault.py
"""
Run from your local terminal:
    python tests/diagnose_segfault.py 2>&1 | tee segfault_trace.log

The last printed line before crash = the guilty import.
"""
import sys

steps = [
    ("numpy",                    "import numpy; print(f'  numpy {numpy.__version__}')"),
    ("math",                     "import math"),
    ("yaml",                     "import yaml"),
    ("beartype",                 "import beartype; print(f'  beartype {beartype.__version__}')"),
    ("beartype.typing",          "from beartype.typing import List, Optional, Tuple"),
    ("flee (package init)",      "import flee; print(f'  flee from {flee.__file__}')"),
    ("flee.SimulationSettings",  "from flee.SimulationSettings import SimulationSettings"),
    ("flee.s1s2_model",          "from flee.s1s2_model import compute_deliberation_weight"),
    ("flee.lib_math",            "import flee.lib_math; print(f'  lib_math from {flee.lib_math.__file__}')"),
    ("flee.spawning",            "import flee.spawning"),
    ("flee.demographics",        "import flee.demographics"),
    ("flee.scoring",             "import flee.scoring"),
    ("flee.Diagnostics",         "from flee.Diagnostics import write_agents, write_links"),
    ("flee.moving",              "import flee.moving"),
    ("flee.flee",                "import flee.flee"),
]

for label, code in steps:
    print(f"TRYING: {label} ...", flush=True)
    try:
        exec(code)
        print(f"  OK", flush=True)
    except ImportError as e:
        print(f"  IMPORT ERROR: {e}", flush=True)
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}", flush=True)

print("\nAll imports completed without segfault.", flush=True)
