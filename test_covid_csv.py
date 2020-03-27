import flee.covid_flee as flee
import numpy as np
import outputanalysis.analysis as a
from datamanager import read_building_csv

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Testing basic Covid-19 simulation kernel.")

  end_time = 90
  e = flee.Ecosystem()

  read_building_csv.read_building_csv(e, "covid_data/buildings_test.csv", "covid_data/building_types_map.yml")
 
  e.add_infections(10)

  #e.print_needs()

  e.print_status("covid_out.csv")
  for t in range(0,end_time):

    # Propagate the model by one time step.
    e.evolve()

    print(t)
    e.print_status("covid_out.csv")

  assert t==89

  print("Simulation complete.")

