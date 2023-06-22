import csv
import logging
import os
import subprocess
import sys

import pytest

base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "FabFlee/config_files")
rs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "runscripts")

logger = logging.getLogger(__name__)

# GitHub action = 2 cores
duration = 10

def test_mali(run_py):
    ret = run_py("mali2012", "10")
    assert ret == "OK"


def test_par_mali(run_par):
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)
    ret = run_par("mali2012", "10", "2")
    assert ret == "OK"


def test_burundi(run_py):
    ret = run_py("burundi", "10")
    assert ret == "OK"


def test_par_burundi(run_par):
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)
    ret = run_par("burundi", "10", "2")
    assert ret == "OK"


def test_car(run_py):
    ret = run_py("car", "5")
    assert ret == "OK"


def test_par_car(run_par):
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)
    ret = run_par("car", "5", "2")
    assert ret == "OK"


def test_ssudan(run_py):
    ret = run_py("ssudan", "5")
    assert ret == "OK"


def test_par_ssudan(run_par):
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)
    ret = run_par("ssudan", "5", "2")
    assert ret == "OK"


@pytest.fixture
def run_py():
    def _run_py(config, simulation_period):
        config_path = os.path.join(base, config)

        cmd = [
            "python3",
            "{}/run.py".format(rs_path),
            "input_csv",
            "source_data",
            simulation_period,
            "simsetting.yml",
            "> out.csv",
        ]
        cmd = " ".join([str(x) for x in cmd])
        try:
            proc = subprocess.Popen(
                [cmd],
                cwd=config_path,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout = proc.communicate()[0].decode("utf-8")
        except Exception as e:
            raise RuntimeError("Unexpected error: {}".format(e)) from e

        acceptable_err_subprocesse_ret_codes = [0]
        if proc.returncode not in acceptable_err_subprocesse_ret_codes:
            raise RuntimeError(
                "\njob execution encountered an error (return code {})"
                "while executing \ncmd = {}\nstdout = {}".format(proc.returncode, cmd, stdout)
            )

        proc.terminate()

        # checking out.csv
        if os.path.isfile(os.path.join(config_path, "out.csv")):
            with open(os.path.join(config_path, "out.csv"), encoding="utf_8") as csvfile:
                reader = csv.reader(csvfile)
                lines = len(list(reader))
                if lines - 1 != int(simulation_period):
                    raise RuntimeError(
                        "The generated days in out.csv file is {} which is less than "
                        "the target simulation_period = {}".format(lines - 1, simulation_period)
                    )

        # clean generated out.csv file
        if os.path.isfile(os.path.join(config_path, "out.csv")):
            os.remove(os.path.join(config_path, "out.csv"))

        return "OK"
        # assert(output.find('success') >= 0)

    return _run_py


@pytest.fixture
def run_par():
    def _run_par(config, simulation_period, cores):
        config_path = os.path.join(base, config)

        cmd = [
            "/usr/bin/mpirun",
            "-np",
            cores,
            "python3",
            "{}/run_par.py".format(rs_path),
            "input_csv",
            "source_data",
            simulation_period,
            "simsetting.yml",
            "> out.csv",
        ]
        cmd = " ".join([str(x) for x in cmd])

        try:
            proc = subprocess.Popen(
                [cmd],
                cwd=config_path,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout = proc.communicate()[0].decode("utf-8")
        except Exception as e:
            raise RuntimeError("Unexpected error: {}".format(e)) from e

        acceptable_err_subprocesse_ret_codes = [0]
        if proc.returncode not in acceptable_err_subprocesse_ret_codes:
            raise RuntimeError(
                "\njob execution encountered an error (return code {})"
                "while executing \ncmd = {}\ncwd = {},\nstdout = {}".format(proc.returncode, cmd, config_path, stdout)
            )

        # checking out.csv
        if os.path.isfile(os.path.join(config_path, "out.csv")):
            with open(os.path.join(config_path, "out.csv"), encoding="utf_8") as csvfile:
                reader = csv.reader(csvfile)
                lines = len(list(reader))
                if lines - 1 != int(simulation_period):
                    raise RuntimeError(
                        "The generated days in out.csv file is {} which is less than "
                        "the target simulation_period = {}".format(lines - 1, simulation_period)
                    )

        proc.terminate()

        # clean generated out.csv file
        if os.path.isfile(os.path.join(config_path, "out.csv")):
            os.remove(os.path.join(config_path, "out.csv"))

        return "OK"
        # assert(output.find('success') >= 0)

    return _run_par
