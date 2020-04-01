import flee.covid_flee as flee
import numpy as np
import outputanalysis.analysis as a
from datamanager import read_building_csv
from datamanager import read_cases_csv
from datamanager import read_disease_yml
import sys

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Testing basic Covid-19 simulation kernel.")

  building_file = "covid_data/buildings.csv"
  if len(sys.argv)>1:
    building_file = "covid_data/buildings_test.csv"

  end_time = 90
  e = flee.Ecosystem()

  e.disease = read_disease_yml.read_disease_yml("covid_data/disease_covid19.yml")
  read_building_csv.read_building_csv(e, building_file, "covid_data/building_types_map.yml")
  read_cases_csv.read_cases_csv(e, "covid_data/cases.csv") # Can only be done after houses are in.
 
  #e.add_infections(10)

  #e.print_needs()

  e.print_status("covid_out.csv")
  for t in range(0,end_time):

    # Propagate the model by one time step.
    e.evolve()

    print(t)
    e.print_status("covid_out.csv")

  assert t==89

  print("Simulation complete.")

