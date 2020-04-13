import pandas as pd
import numpy as np
import sys

def read_age_csv(csv_name, header_name=""):
  df = pd.read_csv(csv_name)
  df.columns = map(str.lower, df.columns)
  ages = df[header_name.lower()].to_numpy()
  return ages / np.sum(ages)

