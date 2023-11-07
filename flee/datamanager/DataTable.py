import csv
import os
import sys
from datetime import datetime, timedelta
from functools import wraps

import numpy as np

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


@check_args_type
def subtract_dates(date1: str, date2: str) -> int:
    """
    Takes two dates %Y-%m-%d format. Returns date1 - date2, measured in days.

    Args:
        date1 (str): Description
        date2 (str): Description

    Returns:
        int: Description
    """
    date_format = "%Y-%m-%d"
    a = datetime.strptime(date1, date_format)
    b = datetime.strptime(date2, date_format)
    delta = a - b
    # print(date1,"-",date2,"=",delta.days)
    return delta.days


@check_args_type
def steps_to_date(steps: int, start_date: str):
    """
    Summary

    Args:
        steps (int): Description
        start_date (str): Description

    Returns:
        TYPE: Description
    """
    # date_format = "%Y-%m-%d"
    date_1 = datetime.strptime(start_date, "%Y-%m-%d")
    new_date = (date_1 + timedelta(days=steps)).date()
    return new_date


@check_args_type
def _processEntry(
    row: list,
    table: np.ndarray,
    data_type: str,
    date_column: int,
    count_column: int,
    start_date: str,
    population_scaledown_factor: int = 1,
) -> np.ndarray:
    """
    Code to process a population count from a CSV file.
    column <date_column> contains the corresponding date in %Y-%m-%d format.
    column <count_column> contains the population size on that date.

    Args:
        row (list): Description
        table (np.ndarray): Description
        data_type (str): Description
        date_column (int): Description
        count_column (int): Description
        start_date (str): Description
        population_scaledown_factor (int, optional): Description

    Returns:
        np.ndarray: Description
    """
    if len(row) < 2:
        return table

    if row[0][0] == "#":
        return table

    if row[1] == "":
        return table

    # Make sure the date column becomes an integer, which contains the offset
    # in days relative to the start date.
    row[date_column] = subtract_dates(date1=row[date_column], date2=start_date)

    if data_type == "int":
        table = np.vstack(
            [table, [int(row[date_column]), int(row[count_column]) / population_scaledown_factor]]
        )
    else:
        table = np.vstack(
            [
                table,
                [
                    float(row[date_column]),
                    float(row[count_column]) / float(population_scaledown_factor),
                ],
            ]
        )

    return table


@check_args_type
def AddCSVTables(table1: np.ndarray, table2: np.ndarray) -> np.ndarray:
    """
    Add two time series tables. This version does not yet support interpolation between values.
    (The UNHCR data website also does not do this, by the way)

    Args:
        table1 (np.ndarray): Description
        table2 (np.ndarray): Description

    Returns:
        np.ndarray: Description
    """
    table = np.zeros([0, 2])

    offset = 0
    last_c2 = np.zeros(([1, 2]))
    for c2 in table2:

        # If table 2 date value is higher, then keep adding entries from table
        # 1
        while c2[0] > table1[offset][0]:
            table = np.vstack([table, [table1[offset][0], last_c2[1] + table1[offset][1]]])
            if offset < len(table1) - 1:
                offset += 1
            else:
                break

        # If the two match, add a total.
        if c2[0] == table1[offset][0]:
            table = np.vstack([table, [c2[0], c2[1] + table1[offset][1]]])
            if offset < len(table1) - 1:
                offset += 1
            last_c2 = c2
            continue

        # If table 1 value is higher, add an aggregate entry, and go to the
        # next iteration without increasing the offset.
        if c2[0] < table1[offset][0]:
            table = np.vstack([table, [c2[0], c2[1] + table1[offset][1]]])
            last_c2 = c2
            continue

    return table


@check_args_type
def ConvertCsvFileToNumPyTable(
    csv_name: str,
    data_type: str = "int",
    date_column: int = 0,
    count_column: int = 1,
    start_date: str = "2012-02-29",
    population_scaledown_factor: int = 1,
) -> np.ndarray:
    """
    Converts a CSV file to a table with date offsets from start_date.
    CSV format for each line is:
    yyyy-mm-dd,number

    Default settings:
    - subtract_dates is used on column 0.
    - Use # sign to comment out lines. (first line is NOT ignored by default)
    """
    table = np.zeros([0, 2])

    with open(csv_name, newline="", encoding="utf_8") as csvfile:
        values = csv.reader(csvfile)

        row = next(values)

        if len(row) > 1:
            if len(row[0]) > 0 and row[0] not in ["DateTime", "Date"]:
                table = _processEntry(
                    row=row,
                    table=table,
                    data_type=data_type,
                    date_column=date_column,
                    count_column=count_column,
                    start_date=start_date,
                    population_scaledown_factor=population_scaledown_factor,
                )

        for row in values:
            table = _processEntry(
                row=row,
                table=table,
                data_type=data_type,
                date_column=date_column,
                count_column=count_column,
                start_date=start_date,
                population_scaledown_factor=population_scaledown_factor,
            )

    return table


class DataTable:
    """
    the DataTable class
    """

    @check_args_type
    def __init__(
        self,
        data_directory: str = "mali2012",
        data_layout: str = "data_layout_refugee.csv",
        start_date: str = "2012-02-29",
        csvformat: str = "generic",
        population_scaledown_factor: int = 1,
        start_empty: bool = False
    ):
        """
        read in CSV data files containing refugee data.
        """
        self.total_refugee_column = 1
        self.days_column = 0
        self.header = []
        self.data_table = []
        self.start_date = start_date
        # Use modified input data for FLEE simulations
        self.override_refugee_input = False
        self.override_refugee_input_file = ""
        self.data_directory = data_directory
        self.population_scaledown_factor = population_scaledown_factor
        self.offsets = {}
        # if set to 1, then all files are corrected such that existing refugees
        # on Day 0 are left out of the simulation and the validation data.
        if start_empty is False:
            self.start_empty = 0
        else:
            self.start_empty = 1

        with open(
            os.path.join(data_directory, data_layout), newline="", encoding="utf-8"
        ) as csvfile:
            values = csv.reader(csvfile)
            for row in values:
                if len(row) > 1:
                    if row[0][0] == "#":
                        continue
                    self.header.append(row[0])

                    # print("%s/%s" % (data_directory, row[1]))
                    csv_total = ConvertCsvFileToNumPyTable(
                        csv_name=os.path.join(data_directory, row[1]),
                        start_date=start_date,
                        population_scaledown_factor=population_scaledown_factor,
                    )

                    # The loop below is for rare cases where multiple CSV files need
                    # to be aggregated for the same camp. In the test cases this only
                    # apply to CAR at time of writing.
                    for added_csv in row[2:]:
                        csv_total = AddCSVTables(
                            table1=csv_total,
                            table2=ConvertCsvFileToNumPyTable(
                                csv_name=os.path.join(data_directory, added_csv),
                                start_date=start_date,
                                population_scaledown_factor=population_scaledown_factor,
                            ),
                        )

                    self.data_table.append(csv_total)

        # print(self.header, self.data_table)

    @check_args_type
    def override_input(self, data_file_name: str) -> None:
        """
        Do not use the total refugee count data as the input value, but instead take values
        from a separate file.

        Args:
            data_file_name (str): Description
        """
        self.override_refugee_input_file = data_file_name
        self.override_refugee_input = True

        self.header.append("total (modified input)")
        self.data_table.append(
            ConvertCsvFileToNumPyTable(
                csv_name=data_file_name,
                start_date=self.start_date,
                population_scaledown_factor=self.population_scaledown_factor,
            )
        )

    @check_args_type
    def get_daily_difference(
        self,
        day: int,
        day_column: int = 0,
        count_column: int = 1,
        Debug: bool = False,
        FullInterpolation: bool = True,
        SumFromCamps: bool = True,
    ) -> int:
        """
        Extrapolate count of new refugees at a given time point, based on input data.
        count_column = column which contains the relevant difference.
        FullInterpolation: when disabled, the function ignores any decreases in refugee count.
        when enabled, the function can return negative numbers when the new total is higher
        than the older one.
        SumFromCamps: when enabled, adds up all the camp numbers when calculating totals.
        When disabled, simply takes the value from the "total" field
        (which usually maps to refugees.csv).

        Args:
            day (int): Description
            day_column (int, optional): Description
            count_column (int, optional): Description
            Debug (bool, optional): Description
            FullInterpolation (bool, optional): Description
            SumFromCamps (bool, optional): Description

        Returns:
            int: Description
        """
        self.total_refugee_column = count_column
        self.days_column = day_column

        # ref_table = self.data_table[0]
        # if self.override_refugee_input is True:
        #   ref_table = self.data_table[self._find_headerindex("total (modified input)")]


        # Refugees only come in *after* day 0.
        if int(day) == 0:
            # ref_table = self.data_table[0]

            new_refugees = 0
            self.offsets["total"] = 0

            for i in self.header:
                camp_pop = self.get_field(
                    name=i, day=0, FullInterpolation=FullInterpolation
                )
                # This function is called multiple times, sometimes with 0 camp pop.
                # So we make sure that the offset is indeed equal to the initial camp
                # popi only once, and not set to 0 again.
                if self.offsets.get(i,0) == 0:
                    self.offsets[i] = camp_pop

                if SumFromCamps is True:
                    new_refugees += camp_pop
                    self.offsets["total"] += camp_pop

            if SumFromCamps is False:
                new_refugees = self.get_field(
                    name="total", day=0, FullInterpolation=FullInterpolation
                )
                self.offsets["total"] = new_refugees

            # Don't have new refugees on Day 0 if we start empty
            new_refugees *= (1 - self.start_empty)

            # return int(new_refugees)

        else:

            new_refugees = 0
            if SumFromCamps is True:
                for i in self.header[1:]:
                    new_refugees += self.get_field(
                        name=i, day=day, FullInterpolation=FullInterpolation
                    ) - self.get_field(i, day - 1, FullInterpolation)
            else:
                new_refugees += self.get_field(
                    name="total", day=day, FullInterpolation=FullInterpolation
                ) - self.get_field("total", day - 1, FullInterpolation)

            # return int(new_refugees)

        return int(new_refugees)

    @check_args_type
    def dump(self, day: int, length: int) -> None:
        """
        Summary

        Args:
            day (int): Description
            length (int): Description
        """
        print("Agent count data table DUMP:")
        for i in range(0, length):
            print(self.get_daily_difference(day=day + i))

    @check_args_type
    def get_interpolated_data(self, column: int, day: int) -> int:
        """
        Gets in a given column for a given day. Interpolates between days as needed.

        Args:
            column (int): Description
            day (int): Description

        Returns:
            int: Description
        """
        ref_table = self.data_table[column]

        old_val = ref_table[0, self.total_refugee_column]
        # print(ref_table[0][self.days_column])
        old_day = ref_table[0, self.days_column]
        if day <= old_day:
            return int(old_val)

        for i in range(1, len(ref_table)):
            # print(day, ref_table[i][self.days_column])
            if day < ref_table[i, self.days_column]:

                old_val = ref_table[i - 1, self.total_refugee_column]
                old_day = ref_table[i - 1, self.days_column]

                fraction = float(day - old_day) / float(ref_table[i, self.days_column] - old_day)

                if fraction > 1.0:
                    print("Error with days_column: ", ref_table[i, self.days_column])
                    return -1

                # print(day, old_day, ref_table[i][self.total_refugee_column], old_val)
                return int(
                    old_val + fraction * float(ref_table[i, self.total_refugee_column] - old_val)
                )

        # print("# warning: ref_table length exceeded for column: ",day,
        # self.header[column], ", last ref_table values: ",
        # ref_table[i-1][self.total_refugee_column],
        # ref_table[i][self.days_column])
        return int(ref_table[-1, self.total_refugee_column])

    @check_args_type
    def get_raw_data(self, column: int, day: int) -> int:
        """
        Gets in a given column for a given day. Does not Interpolate.

        Args:
            column (int): Description
            day (int): Description

        Returns:
            int: Description
        """

        ref_table = self.data_table[column]

        old_val = ref_table[0][self.total_refugee_column]
        # old_day = 0

        for i in range(0, len(ref_table)):
            if day >= ref_table[i][self.days_column]:
                old_val = ref_table[i][self.total_refugee_column]
                # old_day = ref_table[i][self.days_column]
            else:
                break
        return int(old_val)

    @check_args_type
    def _find_headerindex(self, name: str) -> int:
        """
        Finds matching index number for a particular name in the list of headers.

        Args:
            name (str): Description

        Returns:
            int: Description
        """
        for i in range(0, len(self.header)):
            if self.header[i] == name:
                return i

        print(self.header, file=sys.stderr)
        sys.exit("Error: can't find the header %s in the header list" % (name))

    @check_args_type
    def get_field(self, name: str, day: int, FullInterpolation=True) -> int:
        """
        Gets in a given named column for a given day. Interpolates between days if needed.

        Args:
            name (str): Description
            day (int): Description
            FullInterpolation (bool, optional): Description

        Returns:
            int: Description
        """
        i = self._find_headerindex(name=name)

        if FullInterpolation:
            # print(name, day, self.offsets.get(name,0), self.start_empty, file=sys.stderr)
            return self.get_interpolated_data(column=i, day=day) - (self.offsets.get(name,0) * self.start_empty)

        return self.get_raw_data(column=i, day=day) - (self.offsets.get(name,0) * self.start_empty)

    @check_args_type
    def print_data_values_for_location(self, name: str, last_day: int) -> None:
        """
        print all data values for selected location.

        Args:
            name (str): Description
            last_day (int): Description
        """
        for i in range(0, last_day):
            print(i, self.get_field(name=name, day=i))

    @check_args_type
    def is_interpolated(self, name: str, day: int) -> bool:
        """
        Checks if data for a given day is inter/extrapolated or not.

        Args:
            name (str): Description
            day (int): Description

        Returns:
            bool: Description
        """
        for i in range(0, len(self.header)):
            if self.header[i] == name:
                ref_table = self.data_table[i]
                for j in range(0, len(ref_table)):
                    if int(day) == int(ref_table[j][self.days_column]):
                        return False
                    if int(day) < int(ref_table[j][self.days_column]):
                        return True

        return True

    # def d.correctLevel1Registrations(name, date):
    # correct for start date.
