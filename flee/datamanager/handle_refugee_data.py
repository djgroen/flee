import csv
import os
import sys
from functools import wraps

from flee.datamanager import DataTable

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class RefugeeTable(DataTable.DataTable):
    """
    the RefugeeTable Class.
    """

    @check_args_type
    def get_new_refugees(
        self, day: int, Debug: bool = False, FullInterpolation: bool = True
    ) -> int:
        """
        This function is in place to provide an intuitive naming convention,
        and to retain backwards compatibility.
        See the corresponding function in DataTable.py for exact details on how to use it.

        Args:
            day (int): Description
            Debug (bool, optional): Description
            FullInterpolation (bool, optional): Description

        Returns:
            int: Description
        """
        return self.get_daily_difference(
            day=day, day_column=0, count_column=1, Debug=Debug, FullInterpolation=FullInterpolation
        )

    @check_args_type
    def ReadL1Corrections(self, csvname: str) -> None:
        """
        Summary

        Args:
            csvname (str): Description
        """
        if os.path.isfile(csvname):
            with open(csvname, encoding="utf-8") as csvfile:
                l1reader = csv.reader(csvfile, delimiter=",")
                for row in l1reader:
                    if len(row) > 1:
                        self.correctLevel1Registrations(name=row[0], date=row[1])

    @check_args_type
    def correctLevel1Registrations(self, name: str, date: str) -> float:
        """
        Corrects for level 1 registration overestimations. Returns the scaling factor
        """
        hindex = self._find_headerindex(name=name)
        days = DataTable.subtract_dates(date1=date, date2=self.start_date)
        ref_table = self.data_table[hindex]

        if days < 0:
            #If the wrong data is before the simulation period, then ignore the correction altogether.
            return 1.0

        for i in range(0, len(ref_table)):
            if int(ref_table[i][0]) == int(days):
                # then scale all previous entries by ref_table[i][1]/ref_table[i-1][1]
                if i > 0:
                    first_level_2_value = ref_table[i, 1] + self.day0pops.get(name, 0)
                    last_level_1_value = ref_table[i - 1, 1] + self.day0pops.get(name, 0)

                    if last_level_1_value < 1:
                        print("Error in correctLevel1Registrations: last level 1 value is less than 1.", file=sys.stderr)
                        print(f"Name: {name}, date: {date} (Day {days})", file=sys.stderr)
                        print(f"Last level 1 value: {last_level_1_value} Last data value: {ref_table[i - 1, 1]} Day0Pop: {self.day0pops.get(name, 0)}", file=sys.stderr)
                        sys.exit()
                    # print(days, i, ref_table[0:i,1])
                    ref_table[0:i, 1] *= first_level_2_value / last_level_1_value
                    # print(first_level_2_value, last_level_1_value, ref_table[0:i,1])

        return float(first_level_2_value / last_level_1_value)

    @check_args_type
    def getMaxFromData(self, name: str, days: int) -> int:
        """
        Gets the maximum refugee count in a certain place within the timespan of "days" days
        since the start date.

        Args:
            name (str): Description
            days (int): Description

        Returns:
            int: Description
        """
        hindex = self._find_headerindex(name=name)
        ref_table = self.data_table[hindex]
        max_val = 0

        for i in range(0, len(ref_table)):

            if int(ref_table[i][0]) >= int(days):
                if int(ref_table[i, 1]) > max_val:
                    max_val = int(ref_table[i][1])
                break

            if int(ref_table[i, 1]) > max_val:
                max_val = int(ref_table[i][1])

        return max_val
