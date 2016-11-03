import DataTable
import numpy as np

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Testing basic data handling kernel.")

  d = DataTable.DataTable(csvformat="generic", data_directory="test_data", start_date="2010-06-01", data_layout="data_layout.csv")

  print(d.get_field("Total", 0))
  print(d.get_field("Total", 10))
  print(d.get_field("Total", 100))
  print(d.get_field("Total", 300))
  print(d.get_field("Total", 500))
  print(d.get_field("Total", 700))
  print(d.get_field("Total", 1000000))

  assert d.get_field("Total", 0) == 2775
  assert d.get_field("Total", 300) == 21079
  assert d.get_field("Total", 700) == 311338

  print("SUCCESS")
