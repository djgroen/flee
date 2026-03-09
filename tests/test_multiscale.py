import subprocess
import time
import sys
from pathlib import Path


def test_file_coupling(tmp_path):

    repo_root = Path(__file__).resolve().parents[1]

    macro_script = repo_root / "multiscale" / "macro_model.py"
    micro_script = repo_root / "multiscale" / "micro_model.py"

    # Start first model
    p1 = subprocess.Popen(
        [sys.executable, str(macro_script)],
        cwd=repo_root,
    )

    # Start second model
    p2 = subprocess.Popen(
        [sys.executable, str(micro_script)],
        cwd=repo_root,
    )

    # Wait for completion
    p1.wait(timeout=120)
    p2.wait(timeout=120)

    # Check they finished successfully
    assert p1.returncode == 0
    assert p2.returncode == 0
