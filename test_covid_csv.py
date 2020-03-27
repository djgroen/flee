import flee.covid_flee as flee
import numpy as np
import outputanalysis.analysis as a
from datamanager import read_building_csv

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Testing basic Covid-19 simulation kernel.")

  end_time = 28
  e = flee.Ecosystem()

  read_building_csv.read_building_csv(e, "covid_data/buildings.csv", "covid_data/building_types_map.yml")
 
  #l3.add_infection(0)

  e.print_needs()

  for t in range(0,end_time):

    # Propagate the model by one time step.
    e.evolve()

    print(t)
    e.print_status()

  assert t==27

  print("Test successful!")

