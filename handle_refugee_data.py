import numpy as np
import csv
from datetime import datetime

def subtract_dates(date1, date2):
  date_format = "%Y-%m-%d"
  a = datetime.strptime(date1, date_format)
  b = datetime.strptime(date2, date_format)
  delta = a - b
  return delta.days 

def date_num_csv_to_table(csv_name):
  """
  Converts a CSV file to a table with date offsets from 29 feb 2012.
  CSV format for each line is:
  yyyy-mm-dd,number

  (the first line is skipped)
  """
  table = np.zeros([0,2])

  with open(csv_name, 'rb') as csvfile:
    values = csv.reader(csvfile)
    first_line = True
    for row in values:

      if first_line == True:
        first_line = False
        continue

      table = np.vstack([table,[subtract_dates(row[0],"2012-02-29"), int(row[1])]])
  return table


class DataTable:
  def __init__(self, name, csvformat="mali-pdf"):
    """
    read in TSV data files containing refugee data.
    """
    self.csvformat = csvformat

    if self.csvformat=="mali-pdf":
      validation_data = np.loadtxt(name, dtype=np.int32,delimiter='\t', usecols=(1,2,3,4,5,6,7,8))
      """ validation_data[*][6] is the total number of refugees.
  
      """
      self.data_table = validation_data
      # first field ("date") is omitted.
      self.header = ["days","Niger","Burkina Faso","Mauritania","Togo","Guinea","total","internally displaced"] 
      self.total_refugee_column = 0
      self.days_column = 1

    if self.csvformat=="mali-portal":
      self.header = ["total","Bobo-Dioulasso","Mentao","Mbera"]

      self.data_table = [date_num_csv_to_table('mali2012/refugees.csv'),
      date_num_csv_to_table('mali2012/bf-bobo.csv'),
      date_num_csv_to_table('mali2012/bf-mentao.csv'),
      date_num_csv_to_table('mali2012/mau-mbera.csv')]

      #date_num_csv_to_table('mali2012/nig-abala.csv')
      #date_num_csv_to_table('mali2012/nig-mangaize.csv')



  def get_new_refugees(self, day, format="mali", Debug=False):
    """
    Function to extrapolate count of new refugees at a given time point, based on input data.
    """

    # Refugees only come in *after* day 0.
    if day==0:
      return 0

    if self.csvformat=="mali-pdf":
      self.total_refugee_column = 6
      self.days_column = 0
      ref_table = self.data_table

    if self.csvformat=="mali-portal":
      self.total_refugee_column = 1
      self.days_column = 0
      ref_table = self.data_table[0]

    old_refugees = ref_table[0][self.days_column] #set to initial value in table.
    old_day = 0
    for i in xrange (0,len(ref_table)):
      if day > ref_table[i][self.days_column]:
        old_refugees = ref_table[i][self.total_refugee_column]
        old_day = ref_table[i][self.days_column]
      else:
        time_fraction = 1.0 / float(ref_table[i][self.days_column] - old_day)

        # We calculate the number of new refugees using simple extrapolation
        new_refugees = int(time_fraction * (ref_table[i][self.total_refugee_column] - old_refugees))
        if Debug:
          print new_refugees, time_fraction, i, ref_table[i][self.total_refugee_column], old_refugees
        return new_refugees

    # If the day exceeds the validation data table, then we return 0
    return 0



  def get_interpolated_data(self, column, day):
    """
    Gets in a given column for a given day. Interpolates between days as needed.
    """

    old_val = self.data_table[0][column]
    old_day = self.data_table[0][self.days_column]
    if day == 0:
      return old_val

    for i in xrange(1, len(self.data_table)):
       #print day, self.data_table[i][self.days_column]
       if day < self.data_table[i][self.days_column]:

         old_val = self.data_table[i-1][column]
         old_day = self.data_table[i-1][self.days_column]

         fraction = float(day - old_day) / float(self.data_table[i][self.days_column] - old_day)
 
         if fraction > 1.0:
           print "Error with days_column: ", self.data_table[i][self.days_column]
           return -1

         return int(old_val + fraction * float(self.data_table[i][column] - old_val))

    return self.data_table[-1][column]



  def get_field(self, name, day):
    """
    Gets in a given named column for a given day. Interpolates between days as needed.
    """

    for i in xrange(0,len(self.header)):
      if self.header[i] == name:
        return self.get_interpolated_data(i, day)
