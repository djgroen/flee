import numpy as np


ROUND_NDIGITS = 4
# Primitive error function for single values.


def rel_error(val, correct_val):
    if correct_val < 0.00001:
        return 0.0
    return round(
        np.abs(float(val) / float(correct_val) - 1),
        ROUND_NDIGITS
    )


def abs_error(val, correct_val):
    return round(
        np.abs(float(val) - float(correct_val)),
        ROUND_NDIGITS
    )


# Primitive error function for arrays.

def abs_diffs(forecast_vals, correct_vals):
    return np.round(
        np.abs(forecast_vals - correct_vals),
        ROUND_NDIGITS
    )


def mean_abs_diffs(forecast_vals, correct_vals):
    return np.round(
        np.mean(np.abs(forecast_vals - correct_vals)),
        ROUND_NDIGITS
    )


def calculate_ln_accuracy_ratio(forecast_vals, actual_vals):
    """
    Calculate the log of the accuracy ratio (forecast / actual)
    Return -1 if there is a 0 in the actual values
    """
    return np.round(
        np.mean(np.abs(np.log(forecast_vals / actual_vals))),
        ROUND_NDIGITS
    )


def calculate_MASE(forecast_vals, actual_vals, naieve_vals,
                   start_of_forecast_period=30):
    """
    Calculate the Mean Absolute Scaled Error.
    """
    if len(actual_vals) != len(naieve_vals):
        print("Error in calculate_MASE: len(actual_vals) != len(naieve_vals)",
              len(actual_vals), len(naieve_vals))

    if len(actual_vals) != len(forecast_vals):
        print("Error in calculate_MASE: len(actual_vals) != len(forecast_vals)",
              len(actual_vals), len(forecast_vals))

    offset = start_of_forecast_period + 1

    mean_naieve_error = np.sum(
        (np.abs(actual_vals[offset:] - naieve_vals[offset:]))
    ) / float(len(actual_vals[offset:]))

    # mean_forecast_error = np.mean(
    #     (
    #         np.abs(
    #             actual_vals[start_of_forecast_period:] -
    #             forecast_vals[start_of_forecast_period:]
    #         )
    #     ) / float(len(actual_vals[start_of_forecast_period:]))
    # )
    mean_forecast_error = np.sum(
        (np.abs(actual_vals - forecast_vals))
    ) / float(len(actual_vals))

    return round(
        mean_forecast_error / mean_naieve_error,
        ROUND_NDIGITS
    )
