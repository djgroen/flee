from flee import flee, spawning
from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable #DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import flee.postprocessing.analysis as a
import sys
import os
from flee.SimulationSettings import SimulationSettings

from datetime import datetime, timedelta
import pickle
import json

if __name__ == "__main__":
  print(os.getcwd())
  print(sys.argv)
  start_date,end_time = read_period.read_sim_period("{}/sim_period.csv".format(sys.argv[1]))

  if len(sys.argv)<4:
    print("Please run using: python3 run.py <your_csv_directory> <your_refugee_data_directory> <duration in days> <optional: simsettings.yml> > <output_directory>/<output_csv_filename>")

  input_csv_directory = sys.argv[1]
  validation_data_directory = sys.argv[2]
  if int(sys.argv[3]) > 0:
    end_time = int(sys.argv[3])

  if len(sys.argv)==5:
    flee.SimulationSettings.ReadFromYML(sys.argv[4])
  else:
    flee.SimulationSettings.ReadFromYML("simsetting.yml")

  # Conflict file will be read if modelling conflict-driven displacement. Ignored otherwise.
  flee.SimulationSettings.ConflictInputFile = "%s/conflicts.csv" % input_csv_directory
  # Flood file will be read if modelling flood-driven displacement. Ignored otherwise.
  flee.SimulationSettings.FloodLevelInputFile = "%s/flood_level.csv" % input_csv_directory

  e = flee.Ecosystem()

  ig = InputGeography.InputGeography()

  ig.ReadLocationsFromCSV("%s/locations.csv" % input_csv_directory)

  ig.ReadLinksFromCSV("%s/routes.csv" % input_csv_directory)

  ig.ReadClosuresFromCSV("%s/closures.csv" % input_csv_directory)

  e,lm = ig.StoreInputGeographyInEcosystem(e)

  if SimulationSettings.spawn_rules["read_from_agents_csv_file"] == True:
      ig.ReadAgentsFromCSV(e, "%s/agents.csv" % input_csv_directory)

  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory=validation_data_directory, start_date=start_date, data_layout="data_layout.csv", population_scaledown_factor=SimulationSettings.optimisations["PopulationScaleDownFactor"], start_empty=SimulationSettings.spawn_rules["EmptyCampsOnDay0"])

  d.ReadL1Corrections("%s/registration_corrections.csv" % input_csv_directory)

  output_header_string = "Day,Date,"

  camp_locations      = e.get_camp_names()

  for l in camp_locations:
      spawning.add_initial_refugees(e,d,lm[l])
      output_header_string += "%s sim,%s data,%s error," % (lm[l].name, lm[l].name, lm[l].name)

  output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"

  if SimulationSettings.log_levels["idp_totals"] > 0:
    output_header_string += ",total IDPs"
  print(output_header_string)
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

  for t in range(0,end_time):

    #if t>0:
    ig.AddNewConflictZones(e,t)

    new_refs,refugees_raw,refugee_debt = spawning.spawn_daily_displaced(e,t,d)

    spawning.refresh_spawn_weights(e)

    e.enact_border_closures(t)
    e.evolve()

    #Calculation of error terms
    errors = []
    abs_errors = []
    loc_data = []

    camps = []
    for i in camp_locations:
      camps += [lm[i]]
      loc_data += [d.get_field(i, t)]

    # calculate retrofitted time.
    refugees_in_camps_sim = 0
    for c in camps:
      refugees_in_camps_sim += c.numAgents

    # calculate errors
    j=0
    for i in camp_locations:
      errors += [a.rel_error(lm[i].numAgents, loc_data[j])]
      abs_errors += [a.abs_error(lm[i].numAgents, loc_data[j])]

      j += 1


    date = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=t)
    output = "%s,%s" % (t, date.strftime("%Y-%m-%d"))

    for i in range(0,len(errors)):
      output += ",%s,%s,%s" % (lm[camp_locations[i]].numAgents, loc_data[i], errors[i])

    if refugees_raw>0:
      output += ",%s,%s,%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(refugees_raw), int(sum(loc_data)), e.numAgents(), refugees_raw, refugees_in_camps_sim, refugee_debt)
    else:
      output += ",0.0,0,{},0,{},0".format(e.numAgents(), refugees_in_camps_sim)

    if SimulationSettings.log_levels["idp_totals"] > 0:
      output += ",{}".format(e.numIDPs())

    print(output)
    
  # Save
  with open("particle_001_ecosystem.pkl", "wb") as f_e:
      pickle.dump(e, f_e)
  # with open("particle_001_location_map.pkl", "wb") as f_lm:
  #     pickle.dump(lm, f_lm)
  with open("particle_001_data_table.pkl", "wb") as f_t:
      pickle.dump(d, f_t)
  # print(SimulationSettings.__dict__)
  # print("--------------------- e dict ---------------------")
  # print(e.__dict__)
  # print("--------------------------------------------------")
  # print("--------------------- lm dict ---------------------")
  # print(lm)
  # print("--------------------------------------------------")
  # print("--------------------- d datatable ---------------------")
  # print(d.__dict__)
  # print("--------------------------------------------------")
