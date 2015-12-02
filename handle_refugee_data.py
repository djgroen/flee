import numpy as np

class DataTable:
  def __init__(self, name, format="mali"):
    """
    read in TSV data files containing refugee data.
    """
    if format=="mali":
      validation_data = np.loadtxt(name, dtype=np.int32,delimiter='\t', usecols=(1,2,3,4,5,6,7,8))
      """ validation_data[*][6] is the total number of refugees.
  
      """
      self.data_table = validation_data
      # first field ("date") is omitted.
      self.header = ["days","Niger","Burkina Faso","Mauritania","Togo","Guinea","total","internally displaced"] 
      self.total_refugee_column = 0
      self.days_column = 1



  def get_new_refugees(self, day, format="mali", Debug=False):
    """
    Function to extrapolate count of new refugees at a given time point, based on input data.
    """

    # Refugees only come in *after* day 0.
    if day==0:
      return 0

    if format=="mali":
      self.total_refugee_column = 6
      self.days_column = 0

      old_refugees = self.data_table[0][self.days_column] #set to initial value in table.
      old_day = 0
      for i in xrange (0,len(self.data_table)):
        if day > self.data_table[i][self.days_column]:
          old_refugees = self.data_table[i][self.total_refugee_column]
          old_day = self.data_table[i][self.days_column]
        else:
          time_fraction = 1.0 / float(self.data_table[i][self.days_column] - old_day)

          # We calculate the number of new refugees using simple extrapolation
          new_refugees = int(time_fraction * (self.data_table[i][self.total_refugee_column] - old_refugees))
          if Debug:
            print new_refugees, time_fraction, i, self.data_table[i][self.total_refugee_column], old_refugees
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
