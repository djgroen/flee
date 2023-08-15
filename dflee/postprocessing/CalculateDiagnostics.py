# import matplotlib
import analysis as a
import matplotlib.pyplot as plt
import numpy as np
import StoreDiagnostics as dd

# flake8: noqa
# pylint: skip-file
# for now, I disabled Flake8 and pylint for this file,
# before enable Flake8 test, please first fix this error
# F821: undefined names n1, n2, n3, n4, and n5


def calculate_errors(out_dir, data, name, naieve_model=True):
    """
    Advanced plotting function for validation of refugee registration numbers in camps.
    """
    plt.clf()

    # data.loc[:,["%s sim" % name,"%s data" % name]]).as_matrix()
    y1 = data["%s sim" % name].as_matrix()

    y2 = data["%s data" % name].as_matrix()
    days = np.arange(len(y1))

    naieve_early_day = 7
    naieve_training_day = 30

    # Rescaled values
    plt.clf()

    plt.xlabel("Days elapsed")
    plt.ylabel("Number of refugees")

    simtot = data["refugees in camps (simulation)"].as_matrix().flatten()
    untot = data["refugees in camps (UNHCR)"].as_matrix().flatten()

    y1_rescaled = np.zeros(len(y1))
    for i in range(0, len(y1_rescaled)):
        # Only rescale if simtot > 0
        if simtot[i] > 0:
            y1_rescaled[i] = y1[i] * untot[i] / simtot[i]

    """
  Error quantification phase:
  - Quantify the errors and mismatches for this camp.
  """

    lerr = dd.LocationErrors()

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

    """ Errors of which I'm usure whether to report:
   - accuracy ratio (forecast / true value), because it crashes if denominator is 0.
   - ln(accuracy ratio).
  """

    # We can only calculate the Mean Absolute Scaled Error if we have a naieve model in our plot.
    if naieve_model:

        # Number of observations (aggrgate refugee days in UNHCR data set for this location)
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
            )
        )

    return lerr
