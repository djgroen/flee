from flee.SimulationSettings import SimulationSettings
import numpy as np
import sys
import os     
import pandas as pd
import glob

__demographics = {}


def init_demographics(e):
    global __demographics
    if len(__demographics) == 0:
        print("Read demographics.", file=sys.stderr)
        read_demographics(e)



def get_attribute_ratio(location, attr_name):
    """
    Summary:
        Returns the ratio of the attribute value to the maximum value of the attribute in the location.

    Args:
        location (Location): Location object
        attr_name (str): Attribute name

    Returns:
        float: Ratio of attribute value to maximum attribute value in the location.
    """
    pop = location.pop
    if float(location.pop) < 1.0:
        pop = 100000000 #default to enormous pop to eliminate ethnicity bonus.

    if attr_name not in location.attributes:
        print(f"ERROR: Attribute name {attr_name} was missing for at least one location in the locations.csv file. Perhaps some of the CSV columns are misaligned or missing?", file=sys.stderr)
        sys.exit()

    return float(location.attributes[attr_name]) / pop


def _read_demographic_csv(e, csvname):
  """
  Summary:
        Reads a CSV file containing demographic information for a location.
        The CSV file should be named "demographics_<attribute>.csv".
        The attribute name is extracted from the filename.
        The CSV file should be located in the input_csv directory.
        Attribute CSV files have the following format:
        Value,Default,LocA,LocB,...
        ValueA,weight for that value by Default, ...

  Args:
        e (Ecosystem): Ecosystem object
        csvname (str): Name of the CSV file to read.

  Returns:
        None.
  """
  attribute = (csvname.split(os.sep)[-1].split('.')[0]).split('_')[1]

  if not os.path.exists(csvname):
      return

  df = pd.read_csv(csvname)

  if SimulationSettings.log_levels["init"] > -1:
    print(csvname, file=sys.stderr)
    print("INFO: ", attribute, " attributes loaded, with columns:", df.columns, file=sys.stderr)

  __demographics[attribute] = df


def get_attribute_values(attribute):
    return __demographics[attribute][attribute].to_list()

def read_demographics(e):
  """
  Summary:
      Reads all CSV files containing demographic information for a location.
      The CSV files should be named "demographics_<attribute>.csv".
      The attribute name is extracted from the filename.
      The CSV files should be located in the input_csv directory.
      Attribute CSV files have the following format:
      Value,Default,LocA,LocB,...R
      ValueA,weight for that value by Default, ...

  Args:
      e (Ecosystem): Ecosystem object

  Returns:
      None.
  """
  if not os.path.exists(f"{e.demographics_test_prefix}/input_csv"):
      return

  csv_list = glob.glob(os.path.join(e.demographics_test_prefix, "input_csv","demographics_*.csv"))

  print("Reading demographics information", file=sys.stderr)

  for csvname in csv_list:
      _read_demographic_csv(e, csvname)
      print(f"demographics file:{csvname}", file=sys.stderr)


def _draw_sample(e, loc, attribute):
  """
  Summary:
      Draw a sample from the attribute distribution for a location.
      If the attribute is not found, return -1.

  Args:
      e (Ecosystem): Ecosystem object
      loc (Location): Location object
      attribute (str): Attribute name

  Returns:
      float: Sample from the attribute distribution.
  """
  #print(__demographics[attribute], file=sys.stderr)
  #print(__demographics[attribute].iloc[0]['Default'], file=sys.stderr)
  if attribute in __demographics:
    if loc.name in __demographics[attribute].columns:
      a = __demographics[attribute].sample(n=1,weights=loc.name)
    else:
      a = __demographics[attribute].sample(n=1,weights='Default')
  else:
    return -1

  return a.iloc[0][attribute]


def draw_samples(e,loc):
    """
    Summary:
        Draw samples from all optional attributes.

    Args:
        e (Ecosystem): Ecosystem object
        loc (Location): Location object

    Returns:
        Dict: Dictionary of attribute names and values.
    """
    samples = {}
    for a in __demographics.keys():
        samples[a] = _draw_sample(e, loc, a)
    return samples

