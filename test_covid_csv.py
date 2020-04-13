import flee.covid_flee as flee
from datamanager import read_age_csv
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
  if sys.argv[2] in ["post-lockdown","lockSDCI","london-lock","post-london-lock"]:
    end_time = 180
  if sys.argv[2] == "validation":
    end_time = 30
 
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
    if sys.argv[1] == "harrow":
      building_file = "covid_data/harrow_buildings.csv"
    if sys.argv[1] == "ealing":
      building_file = "covid_data/ealing_buildings.csv"
    if sys.argv[1] == "hillingdon":
      building_file = "covid_data/hillingdon_buildings.csv"
      
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
    elif sys.argv[2] in ["london-lock","post-london-lock"]:
      e.add_work_from_home()
      e.add_case_isolation()

  if len(sys.argv)>3:
    outfile = "{}/{}-{}.csv".format(sys.argv[3], sys.argv[1], sys.argv[2])

  e.ages = read_age_csv.read_age_csv("covid_data/age-distr.csv", sys.argv[1])
  print("age distribution in system:", e.ages, file=sys.stderr)

  e.disease = read_disease_yml.read_disease_yml("covid_data/disease_covid19.yml")
  read_building_csv.read_building_csv(e, building_file, "covid_data/building_types_map.yml", house_ratio=100)
  read_cases_csv.read_cases_csv(e, "covid_data/cases_ward.csv", start_date="3/1/2020", date_format="%m/%d/%Y") # Can only be done after houses are in.
 
  #e.add_infections(10)
  #e.print_validation()
  #e.print_needs()

  e.time = -30
  for i in range(0,30):
    e.evolve()

  e.print_status(outfile)
  for t in range(0,end_time):

    # Propagate the model by one time step.
    e.evolve()

    print(t)
    e.print_status(outfile)

    if t == 89 and sys.argv[2] in ["post-lockdown","post-london-lock"]: # move to post-lockdown scenario.
      e.remove_all_measures()
      e.add_work_from_home()
      e.add_case_isolation()

    if t == 15 and sys.argv[2] in ["validation","london-lock","post-london-lock"]:
      e.remove_all_measures()
      e.add_closure("school", 0)
      e.add_closure("leisure", 0)
      e.add_partial_closure("shopping", 0.8)
      e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
      e.add_work_from_home()
      e.add_case_isolation()

  print("Simulation complete.")

