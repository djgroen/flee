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

  end_time = 90
  if sys.argv[2] == "post-lockdown" or sys.argv[2] == "lockSDCI":
    end_time = 180
 
  print("sys.argv = ", sys.argv, file=sys.stderr)
  print("end time = ", end_time, file=sys.stderr)

  e = flee.Ecosystem(end_time)
  outfile = "covid_out.csv"

  building_file = "covid_data/buildings.csv"
  if len(sys.argv)>1:
    if sys.argv[1] == "test":
      building_file = "covid_data/buildings_test.csv"
    if sys.argv[1] == "brent":
      building_file = "covid_data/brent_buildings.csv"
    if sys.argv[1] == "ealing":
      building_file = "covid_data/ealing_buildings.csv"

  if len(sys.argv)>2:
    if sys.argv[2] == "default":
      pass
    elif sys.argv[2] == "minorlock":
      e.add_closure("school", 0)
      e.add_closure("leisure", 0)
    elif sys.argv[2] == "minorlockSD":
      e.add_closure("school", 0)
      e.add_closure("leisure", 0)
      e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
    elif sys.argv[2] == "lockSDCI" or sys.argv[2] == "post-lockdown":
      e.add_closure("school", 0)
      e.add_closure("leisure", 0)
      e.add_partial_closure("shopping", 0.8)
      e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
      e.add_work_from_home()
      e.add_case_isolation()

  if len(sys.argv)>3:
    outfile = "{}/{}-{}.csv".format(sys.argv[3], sys.argv[1], sys.argv[2])

  e.disease = read_disease_yml.read_disease_yml("covid_data/disease_covid19.yml")
  read_building_csv.read_building_csv(e, building_file, "covid_data/building_types_map.yml")
  read_cases_csv.read_cases_csv(e, "covid_data/Actual Cases.csv", start_date="2020-03-18", date_format="%Y-%m-%d") # Can only be done after houses are in.
 
  #e.add_infections(10)

  #e.print_needs()

  e.print_status(outfile)
  for t in range(0,end_time):

    # Propagate the model by one time step.
    e.evolve()

    print(t)
    e.print_status(outfile)

    if t == 89 and sys.argv[2] == "post-lockdown": # move to post-lockdown scenario.
      e.remove_all_measures()

  print("Simulation complete.")

