import os
from functools import wraps

import matplotlib
import matplotlib.pyplot as plt

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


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
def prepare_figure(
    xlabel: str = "Days elapsed", ylabel: str = "Number of refugees"
) -> "matplotlib.figure.Figure":
    """
    prepares and formats a basic flee visualization figure.

    Args:
        xlabel (str, optional): Description
        ylabel (str, optional): Description

    Returns:
        matplotlib.figure.Figure: Description
    """
    plt.clf()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    matplotlib.rcParams.update({"font.size": 20})
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)
    set_margins()
    return fig
