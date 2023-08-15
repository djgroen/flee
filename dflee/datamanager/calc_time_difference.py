import sys

from flee.datamanager import DataTable

if __name__ == "__main__":
    print(DataTable.subtract_dates(date1=sys.argv[2], date2=sys.argv[1]))
