import os
import sys
from errno import EEXIST
from functools import wraps
from os import makedirs, path
from os.path import basename, isfile, normpath

import plotly.express as px
import plotly.graph_objects as go

import numpy as np
import pandas as pd
from flee.postprocessing import analysis as a

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class LocationErrors:
    """
    Class containing a dictionary of errors and diagnostics pertaining
    a single location.
    """

    def __init__(self):
        self.errors = {}


class SimulationErrors:
    """
    Class containing all error measures within a single simulation.
    It should be initialized with a Python list of the LocationErrors
    structure for all of the relevant locations.
    """

    def __init__(self, location_errors):
        self.location_errors = location_errors

    @check_args_type
    def abs_diff(self, rescaled: bool = True):
        """
        Summary

        Args:
            rescaled (bool, optional): Description

        Returns:
            TYPE: Description
        """
        # true_total_refs is the number of total refugees according to the data.

        errtype = "absolute difference"
        if rescaled:
            errtype = "absolute difference rescaled"

        self.tmp = self.location_errors[0].errors[errtype]

        for lerr in self.location_errors[1:]:
            self.tmp = np.add(self.tmp, lerr.errors[errtype])

        return self.tmp

    @check_args_type
    def get_error(self, err_type: str) -> float:
        """
        Summary

        Args:
            err_type (str): Description

        Returns:
            float: Description
        """
        # Here err_type is the string name of the error that needs to be aggregated.

        self.tmp = self.location_errors[0].errors[err_type] * self.location_errors[0].errors["N"]
        N = self.location_errors[0].errors["N"]

        for lerr in self.location_errors[1:]:
            self.tmp = np.add(self.tmp, lerr.errors[err_type] * lerr.errors["N"])
            N += lerr.errors["N"]

        # print(self.tmp, N, self.tmp/ N)
        return self.tmp / N


@check_args_type
def plot_camps(data: pd.DataFrame, config: str, output: str) -> None:
    """
    Summary

    Args:
        data (pd.DataFrame): Description
        config (str): Description
        output (str): Description
    """
    # Plotting function for camps. #

    data_filtered = data.drop(
        [
            "Total error",
            "refugees in camps (UNHCR)",
            "total refugees (simulation)",
            "raw UNHCR refugee count",
            "refugees in camps (simulation)",
            "refugee_debt",
        ],
        axis=1,
    )

    cols = list(data_filtered.columns.values)

    output = os.path.join(output, "camps")

    mkdir_p(output)

    for i in range(len(cols)):

        name = cols[i].split()

        if name[0]=="Date": #Date is not a camp field.
            continue
        
        fig = px.line(data_filtered, x=data_filtered.index, y=[f"{name[0]} sim", f"{name[0]} data"],
                      labels={"x": "Days elapsed", "y": "Number of asylum seekers / unrecognised refugees"},
                      title=f"{name[0]} camp")

        fig.update_layout(showlegend=True, legend_title_text='', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_xaxes(title_text="Days elapsed")
        fig.update_yaxes(title_text="Refugees")
        fig.write_html("{}/{}.html".format(output, name[0]))

@check_args_type
def plot_numagents(data: pd.DataFrame, config: str, output: str) -> None:
    output = os.path.join(output, "numagents")
    mkdir_p(output)

    if "refugee_debt" in data.columns:
        fig = px.line(data, x=data.index,
                      y=["total refugees (simulation)", "refugees in camps (simulation)", "raw UNHCR refugee count"],
                      labels={"x": "Days elapsed", "y": "Number of asylum seekers / unrecognised refugees"},
                      title="{}".format(config))
    else:
        fig = px.line(data, x=data.index,
                      y=["total refugees (simulation)", "refugees in camps (UNHCR)", "raw UNHCR refugee count"],
                      labels={"x": "Days elapsed", "y": "Number of asylum seekers / unrecognised refugees"},
                      title="{}".format(config))

    fig.update_layout(showlegend=True, legend_title_text='', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title_text="Days elapsed")
    fig.update_yaxes(title_text="Refugees")
    fig.write_html("{}/numagents.html".format(output))

@check_args_type
def plot_errors(data, config: str, output: str, model: str = "macro") -> None:
    output = os.path.join(output, "errors")
    mkdir_p(output)

    un_refs = data.loc[:, ["refugees in camps (UNHCR)"]].to_numpy().flatten()

    loc_errors = []

    nmodel = False

    cols = list(data.columns.values)

    location_names = []

    for i in cols:
        if " sim" in i:
            if "numAgents" not in i:
                location_names.append(" ".join(i.split()[:-1]))

    for i in location_names:
        loc_errors.append(error_quantification(output, data, i, naieve_model=nmodel))

    sim_errors = SimulationErrors(location_errors=loc_errors)

    diffdata = sim_errors.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))
    diffdata_rescaled = sim_errors.abs_diff() / np.maximum(un_refs, np.ones(len(un_refs)))

    fig = px.line(data, x=np.arange(len(diffdata_rescaled)), y=diffdata_rescaled,
                  labels={"x": "Days elapsed", "y": "Averaged relative difference"},
                  title="{}".format(config))

    fig.update_layout(showlegend=True, legend_title_text='', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.write_html("{}/error.html".format(output))

    fig = px.line(data, x=np.arange(len(diffdata)), y=diffdata,
                  labels={"x": "Days elapsed", "y": "Averaged relative difference"},
                  title="{}".format(config))

    fig.update_layout(showlegend=True, legend_title_text='', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.write_html("{}/error_comparison.html".format(output))

def error_quantification(config, data, name, naieve_model=True):
    """
    Error quantification function to quantify the errors and mismatches
    for camps.
    """
    y1 = data["%s sim" % name].to_numpy()

    y2 = data["%s data" % name].to_numpy()

    simtot = data["refugees in camps (simulation)"].to_numpy().flatten()

    untot = data["refugees in camps (UNHCR)"].to_numpy().flatten()

    y1_rescaled = np.zeros(len(y1))

    for i in range(0, len(y1_rescaled)):
        # Only rescale if simtot > 0
        if simtot[i] > 0:
            y1_rescaled[i] = y1[i] * untot[i] / simtot[i]

    lerr = LocationErrors()

    # absolute difference
    lerr.errors["absolute difference"] = a.abs_diffs(forecast_vals=y1, correct_vals=y2)

    # absolute difference (rescaled)
    lerr.errors["absolute difference rescaled"] = a.abs_diffs(
        forecast_vals=y1_rescaled, correct_vals=y2
    )

    # ratio difference
    lerr.errors["ratio difference"] = a.abs_diffs(forecast_vals=y1, correct_vals=y2) / (
        np.maximum(untot, np.ones(len(untot)))
    )

    return lerr

@check_args_type
def mkdir_p(mypath: str) -> None:
    """
    Creates a directory. equivalent to using mkdir -p on the command line

    Args:
        mypath (TYPE): Description
    """
    try:
        makedirs(mypath)
    except OSError as exc:  # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else:
            raise

@check_args_type
def set_margins(
    fig: go.Figure, left: float = 0.13, bottom: float = 0.13, right: float = 0.96, top: float = 0.96
) -> None:
    """
    adjust margins - Setting margins for graphs

    Args:
        fig (go.Figure): The Plotly figure object to adjust margins for.
        left (float, optional): Description
        bottom (float, optional): Description
        right (float, optional): Description
        top (float, optional): Description
    """
    fig.update_layout(margin=dict(l=left, b=bottom, r=right, t=top))

@check_args_type
def plotly_flee_output(input_dir: str, output_dir: str, mscale: bool = False) -> None:
    """
    Summary

    Args:
        input_dir (str): Description
        output_dir (str): Description
        mscale (bool, optional): Description
    """
    config = basename(normpath(input_dir)).split("_")[0]

    # mscale_micro = False
    # mscale_macro = False

    #############################################
    #   micro Multiscale results preparation    #
    #############################################
    micro_input_dir = os.path.join(input_dir, "micro")
    micro_output_dir = os.path.join(output_dir, "micro")
    micro_df_PATH = os.path.join(micro_input_dir, "out.csv")

    #############################################
    #   macro Multiscale results preparation    #
    #############################################
    macro_input_dir = os.path.join(input_dir, "macro")
    macro_output_dir = os.path.join(output_dir, "macro")
    macro_df_PATH = os.path.join(macro_input_dir, "out.csv")

    #############################################
    #   normal results preparation    #
    #############################################
    whole_df_PATH = os.path.join(input_dir, "out.csv")

    #################################################################
    #   Plotting serial mode simulation results (without Multiscale)     #
    #################################################################

    if isfile(whole_df_PATH):
        whole_df = pd.read_csv(whole_df_PATH, sep=",", encoding="latin1", index_col="Day")
        plot_camps(whole_df, config, output_dir)
        plot_numagents(whole_df, config, output_dir)
        plot_errors(whole_df, config, output_dir, model="single-scale")
        print("The results of Serial mode simulation are stored in %s directory." % (output_dir))

    #####################################################
    #   Plotting micro Multiscale simulation results    #
    #####################################################
    if isfile(micro_df_PATH):
        micro_df = pd.read_csv(micro_df_PATH, sep=",", encoding="latin1", index_col="Day")
        plot_camps(micro_df, config, micro_output_dir)
        # RAW UNHCR Counts need to be addressed
        plot_numagents(micro_df, config, micro_output_dir)
        plot_errors(micro_df, config, micro_output_dir, model="micro")
        print("The results of micro simulation are stored in %s directory." % (micro_output_dir))

    #####################################################
    #   Plotting macro Multiscale simulation results    #
    #####################################################
    if isfile(macro_df_PATH):
        macro_df = pd.read_csv(macro_df_PATH, sep=",", encoding="latin1", index_col="Day")
        plot_camps(macro_df, config, macro_output_dir)
        # RAW UNHCR Counts need to be addressed
        plot_numagents(macro_df, config, macro_output_dir)
        plot_errors(macro_df, config, macro_output_dir)
        print("The results of macro simulation are stored in %s directory." % (macro_output_dir))


if __name__ == "__main__":

    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = "out"

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "out"

    plotly_flee_output(input_dir, output_dir)
