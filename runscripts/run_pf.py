from flee import flee, spawning
from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable #DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import flee.postprocessing.analysis as a
import sys
import pickle
from flee.SimulationSettings import SimulationSettings

from datetime import datetime, timedelta

if __name__ == "__main__":
  assimilation_directory = "data_assimilation/assimilation_test"
  input_csv_directory = "data_assimilation/assimilation_test/input_csv"
  start_date,end_time = read_period.read_sim_period("{}/sim_period.csv".format(input_csv_directory)) 
  validation_data_directory = "data_assimilation/assimilation_test/source_data"
  flee.SimulationSettings.ReadFromYML("data_assimilation/assimilation_test/simsetting.yml")

  # Conflict file will be read if modelling conflict-driven displacement. Ignored otherwise.
  flee.SimulationSettings.ConflictInputFile = "%s/conflicts.csv" % input_csv_directory
  # Flood file will be read if modelling flood-driven displacement. Ignored otherwise.
  flee.SimulationSettings.FloodLevelInputFile = "%s/flood_level.csv" % input_csv_directory
  
  # Probably in the wrong file
  # Observation file will be read if data assimilation is enabled.
  if SimulationSettings.spawn_rules["data_assimilation_enabled"] is True:
    SimulationSettings.ObservationsFile = "%s/observations.csv" % input_csv_directory
  # TODO: set number of particles in simsettings.yml and simsetting.py
  # particles_num = SimulationSettings.data_assimilation_settings["number_of_particles"]

  # Read in saved particle
  with open("%s/particle_001_ecosystem.pkl" % assimilation_directory, "rb") as f:
    e = pickle.load(f)

  # Start time is next timestep after saved ecosystem
  start_time = e.time
  end_time = start_time + 6 # TODO: read in from observations file or simsettings.yml
  ig = InputGeography.InputGeography()

  ig.ReadLocationsFromCSV("%s/locations.csv" % input_csv_directory)

  ig.ReadLinksFromCSV("%s/routes.csv" % input_csv_directory)

  ig.ReadClosuresFromCSV("%s/closures.csv" % input_csv_directory)

  e,lm = ig.StoreInputGeographyInEcosystem(e)

  if SimulationSettings.spawn_rules["read_from_agents_csv_file"] == True:
      ig.ReadAgentsFromCSV(e, "%s/agents.csv" % input_csv_directory)

  with open("%s/particle_001_data_table.pkl" % assimilation_directory, "rb") as f:
    d = pickle.load(f)

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
  
  for t in range(start_time, end_time):
    
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
