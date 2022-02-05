import os
import sys
import warnings
from functools import wraps
from typing import Type

# from flee.datamanager import handle_refugee_data
import flee.postprocessing.analysis as a
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

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
    Class containing a dictionary of errors and diagnostics pertaining a single location.
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
    def abs_diff(self, rescaled=True):
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
    def get_error(self, err_type: str) -> float:
        """
        Here err_type is the string name of the error that needs to be aggregated.

        Args:
            err_type (str): Description

        Returns:
            float: Description
        """
        self.tmp = self.location_errors[0].errors[err_type] * self.location_errors[0].errors["N"]
        N = self.location_errors[0].errors["N"]

        for lerr in self.location_errors[1:]:
            self.tmp = np.add(self.tmp, lerr.errors[err_type] * lerr.errors["N"])
            N += lerr.errors["N"]

        # print(self.tmp, N, self.tmp/ N)
        return self.tmp / N


@check_args_type
def plotme(data: Type[pd.DataFrame], name: str, naieve_model: bool = True) -> "LocationErrors":
    """
    Advanced plotting function for validation of refugee registration numbers in camps.

    Args:
        data (DataFrame): Description
        name (str): Description
        naieve_model (bool, optional): Description

    Returns:
        LocationErrors: Description
    """

    # data.loc[:,["%s sim" % name,"%s data" % name]]).values
    y1 = data["%s sim" % name].values

    y2 = data["%s data" % name].values
    days = np.arange(len(y1))

    naieve_early_day = 7
    naieve_training_day = 30

    simtot = data["refugees in camps (simulation)"].values.flatten()
    untot = data["refugees in camps (UNHCR)"].values.flatten()

    y1_rescaled = np.zeros(len(y1))
    for i, _ in enumerate(y1_rescaled):
        # Only rescale if simtot > 0
        if simtot[i] > 0:
            y1_rescaled[i] = y1[i] * untot[i] / simtot[i]

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

    """
  Error quantification phase:
  - At the end of the plotme command we wish to quantify the errors and mismatches for this camp.
  """

    lerr = LocationErrors()

    # absolute difference
    lerr.errors["absolute difference"] = a.abs_diffs(forecast_vals=y1, correct_vals=y2)
    lerr.errors["absolute difference ave"] = np.mean(lerr.errors["absolute difference"])

    # absolute difference (rescaled)
    lerr.errors["absolute difference rescaled"] = a.abs_diffs(
        forecast_vals=y1_rescaled, correct_vals=y2
    )
    lerr.errors["absolute difference rescaled ave"] = np.mean(
        lerr.errors["absolute difference rescaled"]
    )

    # ratio difference
    lerr.errors["ratio difference"] = a.abs_diffs(forecast_vals=y1, correct_vals=y2) / (
        np.maximum(untot, np.ones(len(untot)))
    )
    lerr.errors["ratio difference ave"] = np.mean(lerr.errors["ratio difference"])

    """ Errors of which I'm usure whether to report:
   - accuracy ratio (forecast / true value), because it crashes if denominator is 0.
   - ln(accuracy ratio).
  """

    # We can only calculate the Mean Absolute Scaled Error if we have a naieve
    # model in our plot.
    if naieve_model:

        # Number of observations (aggrgate refugee days in UNHCR data set for
        # this location)
        lerr.errors["N"] = np.sum(y2)

        # flat naieve model (7 day)
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

        print(
            "  {}:\n\tmase7: {}\n  mase7-sloped: {}\n  mase7-ratio: {}\n  mase30: {}\n"
            "  mase30-sloped: {}\n  mase30-ratio: {}\n  N: {}".format(
                name,
                lerr.errors["MASE7"],
                lerr.errors["MASE7-sloped"],
                lerr.errors["MASE7-ratio"],
                lerr.errors["MASE30"],
                lerr.errors["MASE30-sloped"],
                lerr.errors["MASE30-ratio"],
                lerr.errors["N"],
            )
        )
        print(
            "\tabsolute difference ave: {absolute difference ave}\n"
            "\tabsolute difference rescaled ave: {absolute difference rescaled ave}\n"
            "\tratio difference ave: {ratio difference ave}".format(**lerr.errors)
        )

    return lerr


# Start of the code, assuring arguments of out-folder & csv file are kept
if __name__ == "__main__":

    if len(sys.argv) > 1:
        in_dir = sys.argv[1]
    else:
        in_dir = "out"

    refugee_data = pd.read_csv("%s/out.csv" % (in_dir), sep=",", encoding="latin1", index_col="Day")

    # Identifying location names for graphs
    rd_cols = list(refugee_data.columns.values)
    location_names = []
    for i in rd_cols:
        if " sim" in i:
            if "numAgents" not in i:
                location_names.append(" ".join(i.split()[:-1]))

    if "refugee_debt" in refugee_data.columns:
        refugee_data.loc[
            :,
            [
                "total refugees (simulation)",
                "refugees in camps (simulation)",
                "raw UNHCR refugee count",
                "refugee_debt",
            ],
        ].plot(linewidth=5)
    else:
        refugee_data.loc[
            :,
            ["total refugees (simulation)", "refugees in camps (UNHCR)", "raw UNHCR refugee count"],
        ].plot(linewidth=5)

    # Calculate the best offset.

    sim_refs = refugee_data.loc[:, ["refugees in camps (simulation)"]].values.flatten()
    un_refs = refugee_data.loc[:, ["refugees in camps (UNHCR)"]].values.flatten()
    raw_refs = refugee_data.loc[:, ["raw UNHCR refugee count"]].values.flatten()

    # Plots for all locations, one .png file for every time plotme is called.
    # Also populated LocationErrors classes.

    loc_errors = []
    nmodel = True

    print("measurements:")
    for i in location_names:
        loc_errors.append(plotme(refugee_data, i, naieve_model=nmodel))

    sim_errors = SimulationErrors(location_errors=loc_errors)

    print("input directory: {}".format(in_dir))

    print("totals:")
    if nmodel:
        print(
            "  mase7: {}\n  mase7-sloped: {}\n  mase7-ratio: {}\n  mase30: {}\n"
            "  mase30-sloped: {}\n  mase30-ratio: {}".format(
                sim_errors.get_error(err_type="MASE7"),
                sim_errors.get_error(err_type="MASE7-sloped"),
                sim_errors.get_error(err_type="MASE7-ratio"),
                sim_errors.get_error(err_type="MASE30"),
                sim_errors.get_error(err_type="MASE30-sloped"),
                sim_errors.get_error(err_type="MASE30-ratio"),
            )
        )

    diffdata = sim_errors.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))
    diffdata_rescaled = sim_errors.abs_diff() / np.maximum(un_refs, np.ones(len(un_refs)))

    print(
        "  Error (normal): {}\n  Error (rescaled): {}\n  Simulation Period: {}".format(
            np.mean(diffdata), np.mean(diffdata_rescaled), len(diffdata)
        )
    )
