import os
import sys
import warnings
from functools import wraps
from typing import Type

import flee.postprocessing.analysis as a
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flee.datamanager.DataTable import DataTable

warnings.filterwarnings("ignore")
matplotlib.use("Pdf")

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


"""
This is a generic plotting program.
See an example of the output format used in test-output/out.csv
Example use:
  python3 plot-flee-output.py test-output
"""


class LocationErrors:
    """
    Class containing a dictionary of errors and diagnostics
    pertaining a single location.
    """

    def __init__(self):
        self.errors = {}


class SimulationErrors:
    """
    Class containing all error measures within a single simulation.
    It should be initialized with a Python list of the LocationErrors structure
    for all of the relevant locations.
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
        # true_total_refs is the number of total refugees according to the
        # data.

        errtype = "absolute difference"
        if rescaled:
            errtype = "absolute difference rescaled"

        self.tmp = self.location_errors[0].errors[errtype]

        for lerr in self.location_errors[1:]:
            self.tmp = np.add(self.tmp, lerr.errors[errtype])

        return self.tmp

    @check_args_type
    def get_error(self, err_type: str):
        """
        Here err_type is the string name of the error that
        needs to be aggregated.

        Args:
            err_type (str): Description

        Returns:
            TYPE: Description
        """
        self.tmp = self.location_errors[0].errors[err_type] * self.location_errors[0].errors["N"]
        N = self.location_errors[0].errors["N"]

        for lerr in self.location_errors[1:]:
            self.tmp = np.add(self.tmp, lerr.errors[err_type] * lerr.errors["N"])
            N += lerr.errors["N"]

        # print(self.tmp, N, self.tmp/ N)
        return self.tmp / N


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
def plotme_minimal(out_dir: str, data: Type[pd.DataFrame], name: str) -> None:
    """
    Explaining minimal graphs: populating data points
    to generate graphs and an example

    Args:
        out_dir (str): Description
        data (Type[pd.DataFrame]): Description
        name (str): Description
    """

    plt.clf()

    data_x = []
    data_y = []

    d = DataTable(data_layout="mali2012/refugees.csv", csvformat="mali-portal")

    # Loop - taking the length of dataset for x and y rays
    for day in range(0, len(data["%s data" % name])):
        if d.is_interpolated(name=name, day=day) is False:
            # draw a point
            data_x.append(day)
            data_y.append(data.at[day, "%s data" % name])

    # data.loc[:,["%s sim" % name,"%s data" % name]]).to_numpy()
    y1 = data["%s sim" % name].to_numpy()
    y2 = data["%s data" % name].to_numpy()
    days = np.arange(len(y1))

    matplotlib.rcParams.update({"font.size": 18})

    max_val = max([max(y1), max(y2)])

    # Graph labels
    plt.xticks([])
    plt.yticks([2000, 5000])
    plt.ylim([0, 1.1 * max_val])

    # Plotting lines representing simulation results and UNHCR data
    # labelsim, = plt.plot(days, y1, linewidth=10, label="%s simulation" % (name.title()))
    # labeldata, = plt.plot(days, y2, linewidth=10, label="%s UNHCR data" % (name.title()))
    plt.plot(days, y1, linewidth=10, label="%s simulation" % (name.title()))
    plt.plot(days, y2, linewidth=10, label="%s UNHCR data" % (name.title()))

    plt.plot(data_x, data_y, "ob")

    # Text labels
    # plt.legend(handles=[labelsim, labeldata],loc=4,prop={"size":20})
    plt.gca().legend_ = None

    plt.text(295, 0.02 * plt.ylim()[1], "%s" % (name.title()), size=24, ha="right")
    # plt.text(200, 0.02*plt.ylim()[1], "Max: %s" % (max(y1)), size=24)

    # Size of plots/graphs
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(7, 6)
    # adjust margins.
    set_margins(left=0.14, bottom=0.13, right=0.96, top=0.96)

    fig.savefig("%s/min-%s_V2.png" % (out_dir, name))


@check_args_type
def plotme(
    out_dir: str,
    data: Type[pd.DataFrame],
    name: str,
    offset: int = 0,
    legend_loc: int = 4,
    naieve_model: bool = True,
    UNHCR: bool = True,
    Filled: bool = False,
    marker_size: int = 3,
    Marker: str = "+",
    errlinewidth: int = 1,
    line_width: int = 2,
    Alpha: float = 0.8,
) -> "LocationErrors":
    """
    Advanced plotting function for validation of
    refugee registration numbers in camps.

    Args:
        out_dir (str): Description
        data (Type[pd.DataFrame]): Description
        name (str): Description
        offset (int, optional): Description
        legend_loc (int, optional): Description
        naieve_model (bool, optional): Description
        UNHCR (bool, optional): Description
        Filled (bool, optional): Description
        marker_size (int, optional): Description
        Marker (str, optional): Description
        errlinewidth (int, optional): Description
        line_width (int, optional): Description
        Alpha (float, optional): Description

    Returns:
        LocationErrors: Description
    """
    plt.clf()
    # TODO: Add figure plotting individual lines for each run.
    # print("plot me data",data[["Day","run_id" ,"%s sim" % name,"%s data" % name]])
    # print("plot me data columns",data.columns)
    # print("plot me data filtered",data["%s sim" % name])
    # y_sim = data["%s sim" % name].to_numpy()
    y1 = data.groupby(["Day"]).mean(numeric_only=True)["%s sim" % name].to_numpy()
    y2 = data.groupby(["Day"]).mean(numeric_only=True)["%s data" % name].to_numpy()

    # calculate error bar based on the standard deviation
    # as the height of our error bars
    y1err = data.groupby(["Day"]).std(numeric_only=True)["%s sim" % name].to_numpy() * 2.0
    y2err = data.groupby(["Day"]).std(numeric_only=True)["%s data" % name].to_numpy() * 2.0

    days = np.arange(len(y1))

    naieve_early_day = 7
    naieve_training_day = 30

    plt.xlabel("Days elapsed")

    matplotlib.rcParams.update({"font.size": 20})

    handles_set = []
    # Plotting lines representing simulation results.
    if offset == 0:
        if Filled is False:
            labelsim = plt.errorbar(
                days,
                y1,
                elinewidth=errlinewidth,
                yerr=y1err,
                fmt=Marker,
                markersize=marker_size,
                label="%s simulation" % (name.title()),
            )
        else:
            (labelsim,) = plt.plot(
                days, y1, linewidth=line_width, label="%s simulation" % (name.title())
            )
            ymin = y1 - y1err
            ymax = y1 + y1err
            # color=None
            plt.fill_between(days, ymax, ymin, color=None, alpha=Alpha)

    if offset > 0:
        if Filled is False:
            labelsim = plt.errorbar(
                days[:-offset],
                y1[offset:],
                yerr=y1err,
                markersize=marker_size,
                fmt=Marker,
                elinewidth=errlinewidth,
                label="%s simulation" % (name.title()),
            )
        else:
            (labelsim,) = plt.plot(
                days[:-offset],
                y1[offset:],
                linewidth=line_width,
                label="%s simulation" % (name.title()),
            )
            ymin = y1 - y1err
            ymax = y1 + y1err
            # color=None
            plt.fill_between(days, ymax, ymin, color=None, alpha=Alpha)

    handles_set.append(labelsim)
    if UNHCR is True:
        # Plotting line representing UNHCR data.
        if Filled is False:
            labeldata = plt.errorbar(
                days,
                y2,
                elinewidth=errlinewidth,
                yerr=y2err,
                markersize=marker_size,
                fmt=Marker,
                label="%s UNHCR data" % (name.title()),
            )
        else:
            (labeldata,) = plt.plot(
                days, y2, linewidth=line_width, label="%s UNHCR data" % (name.title())
            )
            ymin = y2 - y2err
            ymax = y2 + y2err
            # color=None
            plt.fill_between(days, ymax, ymin, color=None, alpha=Alpha)

        handles_set.append(labeldata)

    # Add label for the naieve model if it is enabled.
    plt.legend(handles=handles_set, loc=legend_loc, prop={"size": 18})

    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)
    # adjust margins
    set_margins()

    if offset == 0:
        fig.savefig("%s/%s-%s_V2.png" % (out_dir, name, legend_loc))
    else:
        fig.savefig("%s/%s-offset-%s_V2.png" % (out_dir, name, offset))

    # Plot ensemble members
    plt.clf()
    for run, run_group in data.groupby("run_id"):
        if run == "observations":
            plt.plot(run_group["Day"], 
                    run_group["%s sim" % name], 
                    #  alpha=0.3, 
                    linewidth=0, 
                    marker="*", 
                    markersize=50,
                    color="black",
                    label=f"Run {run}")
        else:
            plt.plot(run_group["Day"], 
                    run_group["%s sim" % name], 
                    #  alpha=0.3, 
                    linewidth=3, 
                    label=f"Run {run}")
        
    plt.legend(bbox_to_anchor=(1.1, 1.05))
    plt.title("%s simulation" % name.title())
    plt.xlabel("Days")
    plt.ylabel("Population")
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(20, 15)
    # adjust margins
    set_margins()
    plt.tight_layout()
    fig.savefig("%s/%s_ensemble.png" % (out_dir, name))
    
    # breakpoint()
    
    # Rescaled values
    plt.clf()

    plt.xlabel("Days elapsed")
    plt.ylabel("Number of refugees")
    handles_set = []

    untot = data.groupby(["Day"]).mean(numeric_only=True)["refugees in camps (UNHCR)"].to_numpy().flatten()
    y1_rescaled = data.groupby(["Day"]).mean(numeric_only=True)["%s sim rescaled" % name].to_numpy()
    y1_rescalederr = data.groupby(["Day"]).std(numeric_only=True)["%s sim rescaled" % name].to_numpy() * 2.0

    if Filled is False:
        labelsim = plt.errorbar(
            days,
            y1_rescaled,
            yerr=y1_rescalederr,
            fmt=Marker,
            markersize=marker_size,
            elinewidth=errlinewidth,
            label="%s simulation" % (name.title()),
        )
    else:
        (labelsim,) = plt.plot(
            days, y1_rescaled, linewidth=line_width, label="%s simulation" % (name.title())
        )
        ymin = y1_rescaled - y1_rescalederr
        ymax = y1_rescaled + y1_rescalederr
        # color=None
        plt.fill_between(days, ymax, ymin, color=None, alpha=Alpha)

    handles_set.append(labelsim)

    # Plotting line representing naieve model
    if naieve_model:
        # Flat line from day 7
        n1 = np.empty(len(days))
        n1.fill(y2[naieve_early_day])
        # Flat line from day 30
        n2 = np.empty(len(days))
        n2.fill(y2[naieve_training_day])
        # Sloped line from day 7
        n3 = np.empty(len(days))
        n3.fill(y2[naieve_early_day])
        for i, _ in enumerate(n3):
            if y2[naieve_early_day] > 0:
                n3[i] *= i * y2[naieve_early_day] / y2[naieve_early_day]
            else:
                n3[i] = 0
        # Sloped line from day 30
        n4 = np.empty(len(days))
        n4.fill(y2[naieve_training_day])
        for i, _ in enumerate(n4):
            if y2[naieve_early_day] > 0:
                n4[i] *= i * y2[naieve_training_day] / y2[naieve_training_day]
            else:
                n4[i] = 0
        # Flat ratio from day 7
        n5 = np.empty(len(days))
        for i, _ in enumerate(n5):
            n5[i] = untot[i] * (y2[naieve_early_day] / untot[naieve_early_day])
        # Flat ratio from day 7
        n6 = np.empty(len(days))
        for i, _ in enumerate(n6):
            n6[i] = untot[i] * (y2[naieve_training_day] / untot[naieve_training_day])

        (labelnaieve,) = plt.plot(
            days, n1, linewidth=line_width, label="%s naieve model" % (name.title())
        )
        (labelnaieve,) = plt.plot(
            days, n2, linewidth=line_width, label="%s naieve early" % (name.title())
        )

        handles_set.append(labelnaieve)
        plt.axvline(x=naieve_early_day, linewidth=line_width, ls="dotted", c="grey")
        plt.axvline(x=naieve_training_day, linewidth=line_width, ls="dotted", c="grey")

    if UNHCR is True:
        if Filled is False:
            labeldata = plt.errorbar(
                days,
                y2,
                yerr=y2err,
                markersize=marker_size,
                fmt=Marker,
                elinewidth=errlinewidth,
                label="%s UNHCR data" % (name.title()),
            )
        else:
            (labeldata,) = plt.plot(
                days, y2, linewidth=line_width, label="%s UNHCR data" % (name.title())
            )
            ymin = y2 - y2err
            ymax = y2 + y2err
            # color=None
            plt.fill_between(days, ymax, ymin, color=None, alpha=Alpha)

        handles_set.append(labeldata)

    plt.legend(handles=handles_set, loc=legend_loc, prop={"size": 18})

    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)
    # adjust margins
    set_margins()

    if naieve_model:
        fig.savefig("%s/%s-%s-rescaled-N_V2.png" % (out_dir, name, legend_loc))
    else:
        fig.savefig("%s/%s-%s-rescaled_V2.png" % (out_dir, name, legend_loc))

    """
    Error quantification phase:
    - At the end of the plotme command we wish to quantify the errors
    - and mismatches for this camp.
    """

    lerr = LocationErrors()

    if offset > 0:
        y1 = y1[offset:]
        y1_rescaled = y1_rescaled[offset:]
        y2 = y2[:-offset]
        untot = untot[:-offset]

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

    """
    Errors of which I'm usure whether to report:
    - accuracy ratio (forecast / true value), because it crashes
    - if denominator is 0.
    - ln(accuracy ratio).
    """

    # We can only calculate the Mean Absolute Scaled Error if we have a naieve
    # model in our plot.
    if naieve_model:

        # Number of observations (aggrgate refugee days in UNHCR data set for
        # this location)
        lerr.errors["N"] = np.sum(y2)

        # flat naieve model (7 day)
        lerr.errors["MASE7"] = a.calculate_MASE(
            forecast_vals=y1_rescaled,
            actual_vals=y2,
            naieve_vals=n1,
            start_of_forecast_period=naieve_early_day,
        )
        lerr.errors["MASE7-sloped"] = a.calculate_MASE(
            forecast_vals=y1_rescaled,
            actual_vals=y2,
            naieve_vals=n3,
            start_of_forecast_period=naieve_early_day,
        )
        lerr.errors["MASE7-ratio"] = a.calculate_MASE(
            forecast_vals=y1_rescaled,
            actual_vals=y2,
            naieve_vals=n5,
            start_of_forecast_period=naieve_early_day,
        )

        # flat naieve model (30 day)
        lerr.errors["MASE30"] = a.calculate_MASE(
            forecast_vals=y1_rescaled,
            actual_vals=y2,
            naieve_vals=n2,
            start_of_forecast_period=naieve_training_day,
        )
        lerr.errors["MASE30-sloped"] = a.calculate_MASE(
            forecast_vals=y1_rescaled,
            actual_vals=y2,
            naieve_vals=n4,
            start_of_forecast_period=naieve_training_day,
        )
        lerr.errors["MASE30-ratio"] = a.calculate_MASE(
            forecast_vals=y1_rescaled,
            actual_vals=y2,
            naieve_vals=n6,
            start_of_forecast_period=naieve_training_day,
        )

        # Accuracy ratio doesn't work because of 0 values in the data.
        # ln_accuracy_ratio = calculate_ln_accuracy_ratio(y1, y2)
        # ln_accuracy_ratio_30 = calculate_ln_accuracy_ratio(y1[30:], y2[30:])
        # print(out_dir, name, "MASE7: ", lerr.errors["MASE7"], ", MASE30: ",
        # lerr.errors["MASE30"], ", abs. diff. 30: ",
        # np.mean(lerr.errors["absolute difference"]))
        print(
            "{},{},{},{},{},{},{},{},{}".format(
                out_dir,
                name,
                lerr.errors["MASE7"],
                lerr.errors["MASE7-sloped"],
                lerr.errors["MASE7-ratio"],
                lerr.errors["MASE30"],
                lerr.errors["MASE30-sloped"],
                lerr.errors["MASE30-ratio"],
                lerr.errors["N"],
            ),
        )

    return lerr


@check_args_type
def plot_flee_uq_output(in_dir: str, out_dir: str) -> None:
    """
    Summary

    Args:
        in_dir (str): Description
        out_dir (str): Description
    """
    matplotlib.style.use("ggplot")

    # find all out.csv files from input directory
    csv_file_address = []
    # r=root, d=directories, f = files
    for r, _, f in os.walk(in_dir):
        for file in f:
            if file == "out.csv":
                csv_file_address.append(os.path.join(r, file))
    
    csv_file_address.sort()
    
    li = []
    for filename in csv_file_address:
        df = pd.read_csv(filename, index_col=None, header=0, sep=",", encoding="latin1")
        print("file",filename)
        run_id = filename.split("/")[-2]
        print("run_id",run_id)
        df["run_id"] = run_id
        li.append(df)

    refugee_data = pd.concat(li, axis=0, ignore_index=True)
    
    # Identifying location names for graphs
    rd_cols = list(refugee_data.columns.values)

    location_names = []
    for i in rd_cols:
        if " sim" in i:
            if "numAgents" not in i:
                location_names.append(" ".join(i.split()[:-1]))

    for name in location_names:
        refugee_data["%s sim rescaled" % name] = refugee_data["%s sim" % name]
    
    end_ch = "\r"
    for i in range(0, len(refugee_data)):
        if i == len(refugee_data) - 1:
            end_ch = "\n"
        print("index %d of %d" % (i, len(refugee_data)), end=end_ch)
        if refugee_data["refugees in camps (simulation)"][i] > 0:
            for name in location_names:
                # continue

                refugee_data.loc[i, "%s sim rescaled" % name] = (
                    refugee_data["%s sim" % name][i]
                    * refugee_data["refugees in camps (UNHCR)"][i]
                    / refugee_data["refugees in camps (simulation)"][i]
                )

                """
                refugee_data["%s sim rescaled" % name][i] = \
                    refugee_data["%s sim" % name][i] * \
                    refugee_data["refugees in camps (UNHCR)"][i] / \
                    refugee_data["refugees in camps (simulation)"][i]
                """
    
    # Plotting and saving numagents (total refugee numbers) graph
    # TODO: These labels need to be more flexible/modifiable.
    plt.xlabel("Days elapsed")

    matplotlib.rcParams.update({"font.size": 20})
    # print("Here info",refugee_data.info())
    # print("Here info",refugee_data.describe())
    # my model
    if "refugee_debt" in refugee_data.columns:
        numagents_data = (
            refugee_data.groupby(["Day"])
            .mean(numeric_only=True)
            .loc[
                :,
                [
                    "total refugees (simulation)",
                    "refugees in camps (simulation)",
                    "raw UNHCR refugee count",
                    "refugee_debt",
                ],
            ]
        )
    else:
        numagents_data = (
            refugee_data.groupby(["Day"])
            .mean(numeric_only=True)
            .loc[
                :,
                [
                    "total refugees (simulation)",
                    "refugees in camps (UNHCR)",
                    "raw UNHCR refugee count",
                ],
            ]
        )
    numagents_data.plot(linewidth=3)

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)

    set_margins()
    plt.savefig("%s/numagents_V2.png" % out_dir)

    # Plots for all locations, one .png file for every time plotme is called.
    # Also populated LocationErrors classes.

    loc_errors = []
    nmodel = False

    for i in location_names:
        loc_errors.append(
            plotme(
                out_dir, refugee_data, i, legend_loc=4, naieve_model=nmodel, UNHCR=True, Filled=True
            )
        )

        # plotme(out_dir, refugee_data, i, legend_loc=1)

        # plotme(out_dir, refugee_data, i, legend_loc=4, naieve_model=nmodel)
        # loc_errors.append(plotme(out_dir, refugee_data, i, legend_loc=4,
        # naieve_model=True))

    sim_errors = SimulationErrors(location_errors=loc_errors)

    # print(sim_errors.abs_diff())
    if nmodel:
        print(
            "{} & {} & {} & {} & {} & {} & {}\\\\".format(
                out_dir,
                sim_errors.get_error(err_type="MASE7"),
                sim_errors.get_error(err_type="MASE7-sloped"),
                sim_errors.get_error(err_type="MASE7-ratio"),
                sim_errors.get_error(err_type="MASE30"),
                sim_errors.get_error(err_type="MASE30-sloped"),
                sim_errors.get_error(err_type="MASE30-ratio"),
            )
        )

    matplotlib.rcParams.update({"font.size": 20})

    plt.clf()

    # ERROR PLOTS

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)

    # Plotting and saving error (differences) graph
    plt.ylabel("Averaged relative difference")
    plt.xlabel("Days elapsed")

    un_refs = (
        refugee_data.groupby(["Day"])
        .mean(numeric_only=True)
        .loc[:, ["refugees in camps (UNHCR)"]]
        .to_numpy()
        .flatten()
    )

    diffdata = sim_errors.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))

    diffdata_rescaled = sim_errors.abs_diff() / np.maximum(un_refs, np.ones(len(un_refs)))

    print(
        out_dir,
        ": Averaged error normal: ",
        np.mean(diffdata),
        ", rescaled: ",
        np.mean(diffdata_rescaled),
        ", len: ",
        len(diffdata),
    )

    # labeldiff, = plt.plot(np.arange(len(diffdata)), diffdata, linewidth=5,
    # label="error (not rescaled)")
    (labeldiff2,) = plt.plot(
        np.arange(len(diffdata_rescaled)), diffdata_rescaled, linewidth=5, label="error"
    )
    # labeldiff2, = plt.plot(np.arange(len(diffdata)), ref_mismatch_error,
    # linewidth=5, label="total refugee difference")

    plt.legend(handles=[labeldiff2], loc=1, prop={"size": 14})

    set_margins()
    plt.savefig("%s/error_V2.png" % out_dir)

    (labeldiff,) = plt.plot(
        np.arange(len(diffdata)), diffdata, linewidth=5, label="error (not rescaled)"
    )

    plt.legend(handles=[labeldiff, labeldiff2], loc=1, prop={"size": 14})

    set_margins()
    plt.savefig("%s/error-comparison_V2.png" % out_dir)

    plt.clf()


"""
----------------------------------------------------------------------
            Start of the code,
            assuring arguments of out-folder & csv file are kept
----------------------------------------------------------------------
"""
if __name__ == "__main__":

    if len(sys.argv) > 1:
        in_dir = sys.argv[1]
    else:
        in_dir = "out"

    if len(sys.argv) > 2:
        out_dir = sys.argv[2]
    else:
        out_dir = "out"

    plot_flee_uq_output(in_dir, out_dir)
