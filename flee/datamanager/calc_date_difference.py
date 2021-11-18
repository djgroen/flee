import sys

from flee.datamanager import DataTable

"""
calc_date_difference.py
Calculates the number of days between two dates.

Usage python3 calc_date_difference.py <YYYY-MM-DD earlier date> <YYYY-MM-DD later date>

"""


if __name__ == "__main__":
    print(DataTable.subtract_dates(date1=sys.argv[2], date2=sys.argv[1]))
