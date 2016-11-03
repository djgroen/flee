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
  def __init__(self, name="", csvformat="mali-pdf", data_directory="mali2012", data_layout="data_layout_refugee.csv", start_date="2012-02-29"):
    """
    read in TSV data files containing refugee data.
    """
    self.csvformat = csvformat
    self.total_refugee_column = 1
    self.days_column = 0

    """
    Obsolete code used for backwards compatibility
    """
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
    """
    END OF OBSOLETE CODE FOR BACKWARDS COMPATIBILITY.
    """


    if self.csvformat=="generic":
      self.header = []
      self.data_table = []
      with open("%s/%s" % (data_directory, data_layout), newline='') as csvfile:
        values = csv.reader(csvfile)
        first_line = True
        for row in values:
          if(len(row)==2):
            self.header.append(row[0])
            #print("%s/%s" % (data_directory, row[1]))

            self.data_table.append(ConvertCsvFileToNumPyTable("%s/%s" % (data_directory, row[1]), start_date))


  def get_new_refugees(self, day, format="mali-portal", Debug=False, FullInterpolation=False):
    """
    Extrapolates count of new refugees at a given time point, based on input data.
    FullInterpolation: when disabled, the function ignores any decreases in refugee count.
                       when enabled, the function can return negative numbers when the new total is lower in the data.
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


  def retrofit_time_to_refugee_count(self, refugee_count, camp_names):
    """
    Takes the total refugee count in camps (from simulation), and determines at which time this number of refugees
    are found in the data. It then returns this time, which can be fractional.
    refugee_count: number of refugees in camps in the simulation, and the value we seek to match time against.
    camp_names: list of names (strings) of the refugee camp locations.
    TODO: make camp_names list auto-detectable in the simulation. 

    LIMITATION: This approach assumes a continual increase in refugee populations. Long-term decreasing trends 
    in the data will cause the function to return garbage.
    """

    last_data_count = 0
    initial_data_count = 0
    last_t = 0
    last_time_in_data = int(self.data_table[0][-1][self.days_column])
    #print("LAST TIME IN DATA = ", int(self.data_table[0][-1][self.days_column]))

    for name in camp_names:
      # aggregate refugee counts from all camps in the simulation
      initial_data_count += self.get_field(name , 0)
    last_data_count = initial_data_count

    for t in range(1, last_time_in_data-1):
      data_count = 0
      for name in camp_names:
        # aggregate refugee counts from all camps in the simulation
        data_count += self.get_field(name , t)

      #print(last_data_count, refugee_count, data_count)
      if int(refugee_count) >= last_data_count:
        if data_count > refugee_count:
          # the current entry in the table has a number that exceeds the refugee count we're looking for.
          # action: interpolate between current and last entry to get the accurate fractional time.
          t_frac = float(refugee_count - last_data_count) / float(data_count - last_data_count)
          #print("RETURN t_corr = ", last_t + t_frac * (t - last_t), ", t = ", t, ", last_t = ", last_t, ", refugees in data = ", data_count, "refugees in sim = ", refugee_count)
          return last_t + t_frac * (t - last_t)

      if data_count > last_data_count:
        # Only when the current refugee count in the data exceeds the highest one found previously, 
        # will we make a new interpolation checkpoint.
        last_data_count = data_count
        last_t = t


  def get_interpolated_data(self, column, day):
    """
    Gets in a given column for a given day. Interpolates between days as needed.
    """

    if self.csvformat == "mali-pdf":

      old_val = self.data_table[0][column]
      old_day = self.data_table[0][self.days_column]
      if day <= old_day:
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

      print("warning: ref_table length exceeded for column: ",column,", given day: ",day,".")
      sys.exit()
      return ref_table[-1][self.total_refugee_column]


  def get_field(self, name, day):
    """
    Gets in a given named column for a given day. Interpolates between days as needed.
    """

    for i in range(0,len(self.header)):
      if self.header[i] == name:
        return self.get_interpolated_data(i, day)

    print("Unable to find header: %s" % (name))
    print(self.header)

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
