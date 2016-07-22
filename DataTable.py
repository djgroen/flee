import numpy as np
import csv
from datetime import datetime

def subtract_dates(date1, date2):
  date_format = "%Y-%m-%d"
  a = datetime.strptime(date1, date_format)
  b = datetime.strptime(date2, date_format)
  delta = a - b
  return delta.days 

def ConvertCsvFileToNumPyTable(csv_name, data_type="int", date_column=0, start_date="2012-02-29"):
  """
  Converts a CSV file to a table with date offsets from 29 feb 2012.
  CSV format for each line is:
  yyyy-mm-dd,number

  Default settings:
  - the first line is skipped.
  - subtract_dates is used on column 0.
  """
  table = np.zeros([0,2])

  with open(csv_name, newline='') as csvfile:
    values = csv.reader(csvfile)
    first_line = True
    for row in values:
      # Make sure the date column becomes an integer, which contains the offset in days relative to the start date.
      row[date_column] = subtract_dates(row[date_column], start_date)

      if first_line == True:
        first_line = False
        continue

      if data_type == "int":
        table = np.vstack([table,[int(row[0]), int(row[1])]])
      else:
        table = np.vstack([table,[float(row[0]), float(row[1])]])
  return table


class DataTable:
  def __init__(self, data_directory="mali2012", data_layout="data_layout_refugee.csv", start_date="2012-02-29", csvformat="generic"):
    """
    read in CSV data files containing refugee data.
    """
    self.csvformat = csvformat
    self.total_refugee_column = 1
    self.days_column = 0

    if self.csvformat=="generic":
      self.header = []
      self.data_table = []
      with open("%s/%s" % (data_directory, data_layout), newline='') as csvfile:
        values = csv.reader(csvfile)
        for row in values:
          if(len(row)==2):
            if(row[0][0] == "#"):
              continue
            self.header.append(row[0])
            #print("%s/%s" % (data_directory, row[1]))

            self.data_table.append(ConvertCsvFileToNumPyTable("%s/%s" % (data_directory, row[1]), start_date=start_date))


  def get_daily_difference(self, day, day_column=0, count_column=1, Debug=False, FullInterpolation=False):
    """
    Function to extrapolate count of new refugees at a given time point, based on input data.
    count_column = column which contains the relevant difference.
    """

    # Refugees only come in *after* day 0.
    if day==0:
      return 0

    else:
      self.total_refugee_column = 1
      self.days_column = 0
      ref_table = self.data_table[0]

      if FullInterpolation:
        new_refugees = 0
        for i in self.header[1:]:
           new_refugees += self.get_field(i, day) - self.get_field(i, day-1)

        #print self.get_field("Mbera", day), self.get_field("Mbera", day-1)
        return int(new_refugees)


    old_refugees = ref_table[0][self.days_column] #set to initial value in table.
    old_day = 0
    for i in range (0,len(ref_table)):
      if day > ref_table[i][self.days_column]:
        old_refugees = ref_table[i][self.total_refugee_column]
        old_day = ref_table[i][self.days_column]
      else:
        time_fraction = 1.0 / float(ref_table[i][self.days_column] - old_day)

        # We calculate the number of new refugees using simple extrapolation
        new_refugees = int(time_fraction * (ref_table[i][self.total_refugee_column] - old_refugees))
        if Debug:
          print(new_refugees, time_fraction, i, ref_table[i][self.total_refugee_column], old_refugees)
        return new_refugees

    # If the day exceeds the validation data table, then we return 0
    return 0



  def get_interpolated_data(self, column, day):
    """
    Gets in a given column for a given day. Interpolates between days as needed.
    """

    ref_table = self.data_table[column]

    old_val = ref_table[0][self.total_refugee_column]
    old_day = ref_table[0][self.days_column]
    if day == 0:
      return old_val

    for i in range(1, len(ref_table)):
      #print day, ref_table[i][self.days_column]
      if day < ref_table[i][self.days_column]:

        old_val = ref_table[i-1][self.total_refugee_column]
        old_day = ref_table[i-1][self.days_column]

        fraction = float(day - old_day) / float(ref_table[i][self.days_column] - old_day)

        if fraction > 1.0:
          print("Error with days_column: ", ref_table[i][self.days_column])
          return -1

        return int(old_val + fraction * float(ref_table[i][self.total_refugee_column] - old_val))

    print("warning: ref_table length exceeded for column: ",column,".")
    return ref_table[-1][self.total_refugee_column]


  def get_field(self, name, day):
    """
    Gets in a given named column for a given day. Interpolates between days as needed.
    """

    for i in range(0,len(self.header)):
      if self.header[i] == name:
        return self.get_interpolated_data(i, day)

  def is_interpolated(self, name, day):
    """
    Checks if data for a given day is inter/extrapolated or not.
    """
    for i in range(0,len(self.header)):
      if self.header[i] == name:
        ref_table = self.data_table[i]
        for j in range(0, len(ref_table)):
          if int(day) == int(ref_table[j][self.days_column]):
            return False
          if int(day) < int(ref_table[j][self.days_column]):
            return True

    return True
