import os
from functools import wraps
from typing import List, Union

import numpy as np

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


ROUND_NDIGITS = 4
# Primitive error function for single values.


@check_args_type
def rel_error(val: Union[int, np.int32], correct_val: Union[float, int]) -> float:
    """
    Summary

    Args:
        val (np.int32): Description
        correct_val (Union[float, int]): Description

    Returns:
        float: Description
    """
    if correct_val < 0.00001:
        return 0.0
    return round(np.abs(float(val) / float(correct_val) - 1), ROUND_NDIGITS)


@check_args_type
def abs_error(val: Union[int, np.int32], correct_val: Union[float, int]) -> float:
    """
    Summary

    Args:
        val (np.int32): Description
        correct_val (Union[float, int]): Description

    Returns:
        float: Description
    """
    return round(np.abs(float(val) - float(correct_val)), ROUND_NDIGITS)


# Primitive error function for arrays.


@check_args_type
def abs_diffs(forecast_vals: np.ndarray, correct_vals: np.ndarray) -> np.ndarray:
    """
    Summary

    Args:
        forecast_vals (np.ndarray): Description
        correct_vals (np.ndarray): Description

    Returns:
        np.ndarray: Description
    """
    return np.round(np.abs(forecast_vals - correct_vals), ROUND_NDIGITS)


@check_args_type
def mean_abs_diffs(forecast_vals: np.ndarray, correct_vals: np.ndarray) -> np.ndarray:
    """
    Summary

    Args:
        forecast_vals (np.ndarray): Description
        correct_vals (np.ndarray): Description

    Returns:
        np.ndarray: Description
    """
    return np.round(np.mean(np.abs(forecast_vals - correct_vals)), ROUND_NDIGITS)


@check_args_type
def calculate_ln_accuracy_ratio(forecast_vals: np.ndarray, actual_vals: np.ndarray) -> np.ndarray:
    """
    Calculate the log of the accuracy ratio (forecast / actual)
    Return -1 if there is a 0 in the actual values

    Args:
        forecast_vals (np.ndarray): Description
        actual_vals (np.ndarray): Description

    Returns:
        np.ndarray: Description
    """
    return np.round(np.mean(np.abs(np.log(forecast_vals / actual_vals))), ROUND_NDIGITS)


@check_args_type
def calculate_MASE(
    forecast_vals: List[float],
    actual_vals: List[float],
    naieve_vals: List[float],
    start_of_forecast_period: int = 30,
) -> float:
    """
    Calculate the Mean Absolute Scaled Error.

    Args:
        forecast_vals (List[float]): Description
        actual_vals (List[float]): Description
        naieve_vals (List[float]): Description
        start_of_forecast_period (int, optional): Description

    Returns:
        float: Description
    """
    if len(actual_vals) != len(naieve_vals):
        print(
            "Error in calculate_MASE: len(actual_vals) != len(naieve_vals) {} != {}".format(
                len(actual_vals), len(naieve_vals)
            )
        )

    if len(actual_vals) != len(forecast_vals):
        print(
            "Error in calculate_MASE: len(actual_vals) != len(forecast_vals) {} != {}".format(
                len(actual_vals), len(forecast_vals)
            )
        )

    offset = start_of_forecast_period + 1

    mean_naieve_error = np.sum((np.abs(actual_vals[offset:] - naieve_vals[offset:]))) / float(
        len(actual_vals[offset:])
    )

    # mean_forecast_error = np.mean(
    #     (
    #         np.abs(
    #             actual_vals[start_of_forecast_period:] -
    #             forecast_vals[start_of_forecast_period:]
    #         )
    #     ) / float(len(actual_vals[start_of_forecast_period:]))
    # )
    mean_forecast_error = np.sum((np.abs(actual_vals - forecast_vals))) / float(len(actual_vals))

    return round(mean_forecast_error / mean_naieve_error, ROUND_NDIGITS)
