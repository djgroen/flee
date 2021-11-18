import csv
import os
from functools import wraps
from typing import Tuple

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


@check_args_type
def read_conflict_period(fname: str) -> Tuple[str, int]:
    """
    Reads in a conflict_period.csv file.

    Args:
        fname (str): Description

    Returns:
        Tuple[str, int]: Description
    """
    startdate = ""
    length = 0
    with open(fname, encoding="utf-8") as csvfile:
        confl_reader = csv.reader(csvfile, delimiter=",")
        for row in confl_reader:
            if row[0].lower() == "startdate":
                startdate = row[1]
            if row[0].lower() == "length":
                length = int(row[1])
    return startdate, length
