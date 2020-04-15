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

  if len(sys.argv) < 2:
    print("Usage: python3 c19_scenarios.py <location> <transition scenario> <transition day> <outdir>")
    sys.exit()

  end_time = 180
  if sys.argv[2] == "validation":
    end_time = 30
 
  scenario = sys.argv[2].lower()

  transition_mode = int(sys.argv[3])
  transition_day = -1
  if transition_mode == 1:
    transition_day = 62 # 30th of April
  if transition_mode == 2:
    transition_day = 77 # 15th of May
  if transition_mode == 3:
    transition_day = 93 # 31st of May
  if transition_mode > 10:
    transition_day = transition_mode


  e = flee.Ecosystem(end_time)
  outfile = "covid_out.csv"

  building_file = ""
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
      
  outfile = "{}/{}-{}-{}.csv".format(sys.argv[4], sys.argv[1], sys.argv[2], transition_day)
  log_prefix = sys.argv[4]

  e.ages = read_age_csv.read_age_csv("covid_data/age-distr.csv", sys.argv[1])
  print("age distribution in system:", e.ages, file=sys.stderr)

  e.disease = read_disease_yml.read_disease_yml("covid_data/disease_covid19.yml")
  read_building_csv.read_building_csv(e, building_file, "covid_data/building_types_map.yml", house_ratio=2)
  read_cases_csv.read_cases_csv(e, "covid_data/cases_ward.csv", start_date="3/1/2020", date_format="%m/%d/%Y") # Can only be done after houses are in.
 
  #e.print_validation()
  #e.print_needs()

  e.time = -30
  e.print_header(outfile)
  for i in range(0,30):
    e.evolve()
    print(e.time)
    e.print_status(outfile)

  #e.print_status(outfile)
  for t in range(0,end_time):

    if t == transition_day:
      if scenario == "extend-lockdown":
        pass
      elif scenario == "open-all":
        e.remove_all_measures()
      elif scenario == "open-schools":
        e.remove_closure("school")
      elif scenario == "open-shopping":
        e.undo_partial_closure("shopping", 0.8)
      elif scenario == "open-leisure":
        e.remove_closure("leisure")
      elif scenario == "work50":     
        e.remove_all_measures()
        e.add_closure("school", 0)
        e.add_closure("leisure", 0)
        e.add_partial_closure("shopping", 0.4)
        e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
        e.add_work_from_home(0.5) #light work from home instruction, with 50% compliance
        e.add_case_isolation()
        e.add_household_isolation()
      elif scenario == "work75":     
        e.remove_all_measures()
        e.add_partial_closure("leisure", 0.5)
        e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
        e.add_work_from_home(0.25) #light work from home instruction, with 25% compliance
        e.add_case_isolation()
        e.add_household_isolation()
      elif scenario == "work100":     
        e.remove_all_measures()
        e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
        e.add_case_isolation()
        e.add_household_isolation()


    

    # Recording of existing measures
    if scenario not in ["no-measures"]:
      if t == 15: # 16th of March
        e.remove_all_measures()
        e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
        e.add_work_from_home(0.5) #light work from home instruction, with 50% compliance
        e.add_partial_closure("leisure", 0.5)
        e.add_case_isolation()
        e.add_household_isolation()
      if t == 22: # 23rd of March
        e.remove_all_measures()
        e.add_closure("school", 0)
        e.add_closure("leisure", 0)
        e.add_partial_closure("shopping", 0.8)
        e.add_social_distance_imp9() #mimicking a 75% reduction in social contacts.
        e.add_work_from_home()
        e.add_case_isolation()
        e.add_household_isolation()

    # Propagate the model by one time step.
    e.evolve()

    print(t)
    e.print_status(outfile)

  print("Simulation complete.")

