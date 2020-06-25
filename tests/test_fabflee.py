import os
import sys
import subprocess
import pytest


base = os.path.join(os.environ['TRAVIS_BUILD_DIR'], "FabFlee/config_files")


def test_mali(run_py):
    ret = run_py("mali", "10")
    assert ret == "OK"


def test_par_mali(run_par):
    ret = run_par("mali", "10", "8")
    assert ret == "OK"


def test_burundi(run_py):
    ret = run_py("burundi", "10")
    assert ret == "OK"


def test_par_burundi(run_par):
    ret = run_par("burundi", "10", "8")
    assert ret == "OK"


def test_car(run_py):
    ret = run_py("car", "10")
    assert ret == "OK"


def test_par_car(run_par):
    ret = run_par("car", "10", "8")
    assert ret == "OK"


def test_ssudan(run_py):
    ret = run_py("ssudan", "10")
    assert ret == "OK"


def test_par_ssudan(run_par):
    ret = run_par("ssudan", "10", "8")
    assert ret == "OK"


@pytest.fixture
def run_py():
    def _run_py(config, simulation_period):
        config_path = os.path.join(base, config)
        current_dir = os.getcwd()
        os.chdir(config_path)

        cmd = ["python3",
               "run.py",
               "input_csv",
               "source_data",
               simulation_period,
               "simsetting.csv",
               "> out.csv"
               ]

        ret = "OK"
        try:
            output = subprocess.check_output(cmd).decode("utf-8")
        except subprocess.CalledProcessError as e:
            ret = "Command '%s' return non-zero exit status: %s\n%s".format(
                (" ".join(cmd), e.returncode, e.output))

        os.chdir(current_dir)
        return ret
        # assert(output.find('success') >= 0)
    return _run_py


@pytest.fixture
def run_par():
    def _run_par(config, simulation_period, cores):
        config_path = os.path.join(base, config)
        current_dir = os.getcwd()
        os.chdir(config_path)
        cmd = ["mpirun",
               "-n",
               cores,
               "python3",
               "run.py",
               "input_csv",
               "source_data",
               simulation_period,
               "simsetting.csv",
               "> out.csv"
               ]

        ret = "OK"
        try:
            output = subprocess.check_output(cmd).decode("utf-8")
        except subprocess.CalledProcessError as e:
            ret = "Command '%s' return non-zero exit status: %s\n%s".format(
                (" ".join(cmd), e.returncode, e.output))

        os.chdir(current_dir)
        return ret
        # assert(output.find('success') >= 0)
    return _run_par
