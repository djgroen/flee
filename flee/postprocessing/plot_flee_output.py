import os
import sys
from errno import EEXIST
from functools import wraps
from os import makedirs, path
from os.path import basename, isfile, normpath

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flee.postprocessing import analysis as a

matplotlib.use("Pdf")

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

        # Fix for camp cluster names - extract camp name from columns like "Kubwa (Camp Cluster) sim"
        if cols[i].endswith(" sim"):
            camp_name = cols[i][:-4]  # Remove " sim" suffix
            sim_col = cols[i]
            data_col = camp_name + " data"
            
            # Extract display name (first word for title)
            name = cols[i].split()
            display_name = name[0]
            
            if display_name == "Date":  # Date is not a camp field.
                continue
                
            if data_col not in data_filtered.columns:
                continue  # Skip if corresponding data column doesn't exist
                
            y1 = data_filtered[sim_col]
            y2 = data_filtered[data_col]
        else:
            continue  # Skip non-simulation columns
          
        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(10, 8)

        plt.xlabel("Days elapsed", fontsize=14)
        plt.ylabel("Number of asylum seekers / unrecognised refugees", fontsize=14)
        plt.title("{}".format(display_name), fontsize=18)

        (label1,) = plt.plot(data_filtered.index, y1, "r", linewidth=5, label="{} simulation".format(display_name))
        
        (label2,) = plt.plot(data_filtered.index, y2, "b", linewidth=5, label="{} UNHCR data".format(display_name))

        plt.legend(handles=[label1, label2], loc=0, prop={"size": 14})

        plt.savefig("{}/{}.png".format(output, display_name), bbox_inches = 'tight')

        plt.clf()


@check_args_type
def plot_numagents(data: pd.DataFrame, config: str, output: str) -> None:
    """
    Summary

    Args:
        data (DataFrame): Description
        config (str): Description
        output (str): Description
    """
    # Plotting and saving NUMAGENTS (total refugee numbers) graph #

    output = os.path.join(output, "numagents")

    mkdir_p(output)

    if "refugee_debt" in data.columns:
        data.loc[
            :,
            [
                "total refugees (simulation)",
                "refugees in camps (simulation)",
                "raw UNHCR refugee count",
                "refugee_debt",
            ],
        ].plot(linewidth=5)
        """
        plt.legend(handles=[total_refugees1, total_refugees2,
                            refugees_in_camps1, refugees_in_camps2,
                            raw_refugee_count, refugee_debt_simulation],
                   loc=0, prop={"size": 14})
        """

    else:
        data.loc[
            :,
            ["total refugees (simulation)", "refugees in camps (UNHCR)", "raw UNHCR refugee count"],
        ].plot(linewidth=5)

        """
        plt.legend(handles=[total_refugees1, total_refugees2,
                            refugees_in_camps1, refugees_in_camps2,
                            raw_refugee_count],
                   loc=0, prop={"size": 14})
        """

    plt.xlabel("Days elapsed")
    plt.ylabel("Number of asylum seekers / unrecognised refugees")
    plt.title("{} number of agents".format(config))

    matplotlib.rcParams.update({"font.size": 14})

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)

    set_margins()

    plt.savefig("{}/numagents.png".format(output), bbox_inches = 'tight')

    plt.clf()


@check_args_type
def plot_errors(data, config: str, output: str, model: str = "macro") -> None:
    """
    Summary

    Args:
        data (TYPE): Description
        config (str): Description
        output (str): Description
        model (str, optional): Description
    """
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

    matplotlib.rcParams.update({"font.size": 16})

    plt.clf()

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()

    fig.set_size_inches(12, 8)

    set_margins()

    #################################################
    # Plotting and saving error (differences) graph #
    #################################################

    plt.ylabel("Averaged relative difference")
    plt.xlabel("Days elapsed")
    #plt.title("{}".format(config))

    diffdata = sim_errors.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))
    diffdata_rescaled = sim_errors.abs_diff(rescaled=True) / np.maximum(un_refs, np.ones(len(un_refs)))

    #print(sim_errors.location_errors)
    #print(diffdata)
    #print(diffdata_rescaled)

    print(
        "%s - %s model: Averaged error normal: " % (config, model),
        np.mean(diffdata),
        ", rescaled: ",
        np.mean(diffdata_rescaled),
        ", len: ",
        len(diffdata),
    )

    (labeldiff_rescaled,) = plt.plot(
        np.arange(len(diffdata_rescaled)), diffdata_rescaled, linewidth=5, label="Error (rescaled)"
    )

    plt.legend(handles=[labeldiff_rescaled], loc=7, prop={"size": 14})

    set_margins()

    plt.savefig("{}/error.png".format(output), bbox_inches = 'tight')

    ###############################################
    #               ERROR COMPARISON              #
    ###############################################

    (labeldiff,) = plt.plot(
        np.arange(len(diffdata)), diffdata, linewidth=5, label="Error (non-rescaled)"
    )

    plt.legend(handles=[labeldiff, labeldiff_rescaled], loc=1, prop={"size": 14})

    set_margins()

    plt.savefig("{}/error_comparison.png".format(output), bbox_inches = 'tight')

    plt.clf()


def error_quantification(config, data, name, naieve_model=True):
    """
    Error quantification function to quantify the errors and mismatches
    for camps.
    """
    y1 = data["%s sim" % name].to_numpy()

    y2 = data["%s data" % name].to_numpy()

    simtot = data["refugees in camps (simulation)"].to_numpy().flatten()

    untot = data["refugees in camps (UNHCR)"].to_numpy().flatten()

    y1_rescaled = np.zeros(len(y1), dtype=np.int64)

    for i in range(0, len(y1_rescaled)):
        # Only rescale if simtot > 0
        if simtot[i] > 0:
            y1_rescaled[i] = y1[i] * untot[i] / simtot[i]

    # days = np.arange(len(y1))

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
    left: float = 0.13, bottom: float = 0.13, right: float = 0.96, top: float = 0.96
) -> None:
    """
    adjust margins - Setting margins for graphs

    Args:
        left (float, optional): Description
        bottom (float, optional): Description
        right (float, optional): Description
        top (float, optional): Description
    """
    fig = plt.gcf()
    fig.subplots_adjust(bottom=bottom, top=top, left=left, right=right)


@check_args_type
def plot_flee_output(input_dir: str, output_dir: str, mscale: bool = False) -> None:
    """
    Summary

    Args:
        input_dir (str): Description
        output_dir (str): Description
        mscale (bool, optional): Description
    """
    matplotlib.style.use("ggplot")
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

    plot_flee_output(input_dir, output_dir)
