import subprocess
import shlex
import time
import sys
import os
import shutil
from pathlib import Path


def test_file_coupling(tmp_path):

    repo_root = Path(__file__).resolve().parents[1]
    mscale_root = str(repo_root / "multiscale")

    macro_script = repo_root / "multiscale" / "run_mscale.py"
    micro_script = repo_root / "multiscale" / "run_mscale.py"

    shutil.rmtree(f"{mscale_root}/out/file")
    os.mkdir(f"{mscale_root}/out/file")         
    os.mkdir(f"{mscale_root}/out/file/micro")         
    os.mkdir(f"{mscale_root}/out/file/coupled")         
    os.mkdir(f"{mscale_root}/out/file/macro")         
    os.mkdir(f"{mscale_root}/out/file/log_exchange_data")         
    os.mkdir(f"{mscale_root}/out/file/plot_exchange_data")         

    cmdline_macro = f"{sys.executable} {str(micro_script)} --submodel macro --data_dir=test --instance_index 0 --coupling_type file --num_instances 1"
    cmdline_micro = f"{sys.executable} {str(micro_script)} --submodel micro --data_dir=test --instance_index 0 --coupling_type file --num_instances 1"

    # Start first model
    p1 = subprocess.Popen(
        shlex.split(cmdline_macro),
        cwd=repo_root / "multiscale",
    )

    # Start second model
    p2 = subprocess.Popen(
        shlex.split(cmdline_micro),
        cwd=repo_root / "multiscale",
    )

    # Wait for completion
    p1.wait(timeout=120)
    p2.wait(timeout=120)

    # Check they finished successfully
    assert p1.returncode == 0
    assert p2.returncode == 0
