import numpy as np
import csv
from datetime import datetime

def subtract_dates(date1, date2):
  date_format = "%Y-%m-%d"
  a = datetime.strptime(date1, date_format)
  b = datetime.strptime(date2, date_format)
  delta = a - b
  return delta.days 

def ConvertCsvFileToNumPyTable(csv_name, start_date="2012-02-29"):
  """
  Converts a CSV file to a table with date offsets from 29 feb 2012.
  CSV format for each line is:
  yyyy-mm-dd,number

  (the first line is skipped)
  """
  table = np.zeros([0,2])

  with open(csv_name, newline='') as csvfile:
    values = csv.reader(csvfile)
    first_line = True
    for row in values:

      if first_line == True:
        first_line = False
        continue

      table = np.vstack([table,[subtract_dates(row[0],start_date), int(row[1])]])
  return table


class DataTable:
  def __init__(self, name="", csvformat="mali-pdf", data_directory="mali2012"):
    """
    read in TSV data files containing refugee data.
    """
    self.csvformat = csvformat
    self.total_refugee_column = 1
    self.days_column = 0

    if self.csvformat=="mali-pdf":
      validation_data = np.loadtxt(name, dtype=np.int32,delimiter='\t', usecols=(1,2,3,4,5,6,7,8))
      """ validation_data[*][6] is the total number of refugees.
  
      """
      self.data_table = validation_data
      # first field ("date") is omitted.
      self.header = ["days","Niger","Burkina Faso","Mauritania","Togo","Guinea","total","internally displaced"] 


    # Example of loading in data from the mali2012 directory.
    if self.csvformat=="mali-portal":
      self.header = ["total","Bobo-Dioulasso","Mentao","Mbera","Fassala","Abala","Mangaize","Tabareybarey","Niamey"]

      self.data_table = [ConvertCsvFileToNumPyTable('mali2012/refugees.csv'),
      ConvertCsvFileToNumPyTable('mali2012/bf-bobo.csv'),
      ConvertCsvFileToNumPyTable('mali2012/bf-mentao.csv'),
      ConvertCsvFileToNumPyTable('mali2012/mau-mbera.csv'),
      ConvertCsvFileToNumPyTable('mali2012/mau-fassala.csv'),
      ConvertCsvFileToNumPyTable('mali2012/nig-abala.csv'),
      ConvertCsvFileToNumPyTable('mali2012/nig-mangaize.csv'),
      ConvertCsvFileToNumPyTable('mali2012/nig-tabareybarey.csv'),
      ConvertCsvFileToNumPyTable('mali2012/nig-niamey.csv')]

    if self.csvformat=="generic":
      self.header = []
      self.data_table = []
      with open("%s/data_layout.csv" % (data_directory), newline='') as csvfile:
        values = csv.reader(csvfile)
        first_line = True
        for row in values:
          if(len(row)==2):
            self.header.append(row[0])
            print("%s/%s" % (data_directory, row[1]))

            self.data_table.append(ConvertCsvFileToNumPyTable("%s/%s" % (data_directory, row[1])))


  def get_new_refugees(self, day, format="mali-portal", Debug=False, FullInterpolation=False):
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

    if self.csvformat == "mali-pdf":

      old_val = self.data_table[0][column]
      old_day = self.data_table[0][self.days_column]
      if day == 0:
        return old_val

      for i in range(1, len(self.data_table)):
         #print day, self.data_table[i][self.days_column]
         if day < self.data_table[i][self.days_column]:

           old_val = self.data_table[i-1][column]
           old_day = self.data_table[i-1][self.days_column]

           fraction = float(day - old_day) / float(self.data_table[i][self.days_column] - old_day)
 
           if fraction > 1.0:
             print("Error with days_column: ", self.data_table[i][self.days_column])
             return -1

           return int(old_val + fraction * float(self.data_table[i][column] - old_val))

      return self.data_table[-1][column]


    else:

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
