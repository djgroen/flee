from flee import flee
from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable #DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import flee.postprocessing.analysis as a
import sys

from datetime import datetime,timedelta

def AddInitialRefugees(e, d, loc):
  """ Add the initial refugees to a location, using the location name"""
  num_refugees = int(d.get_field(loc.name, 0, FullInterpolation=True))
  for i in range(0, num_refugees):
    e.addAgent(location=loc)

insert_day0_refugees_in_camps = True

if __name__ == "__main__":

  start_date,end_time = read_period.read_conflict_period("{}/conflict_period.csv".format(sys.argv[1]))

  if len(sys.argv)<4:
    print("Please run using: python3 run.py <your_csv_directory> <your_refugee_data_directory> <duration in days> <optional: simulation_settings.csv> > <output_directory>/<output_csv_filename>")

  input_csv_directory = sys.argv[1]
  validation_data_directory = sys.argv[2]
  if int(sys.argv[3]) > 0:
    end_time = int(sys.argv[3])

  if len(sys.argv)==5:
    flee.SimulationSettings.ReadFromYML(sys.argv[4])
  flee.SimulationSettings.FlareConflictInputFile = "%s/conflicts.csv" % input_csv_directory

  e = flee.Ecosystem()

  ig = InputGeography.InputGeography()

  ig.ReadFlareConflictInputCSV(flee.SimulationSettings.FlareConflictInputFile)

  ig.ReadLocationsFromCSV("%s/locations.csv" % input_csv_directory)

  ig.ReadLinksFromCSV("%s/routes.csv" % input_csv_directory)

  ig.ReadClosuresFromCSV("%s/closures.csv" % input_csv_directory)

  e,lm = ig.StoreInputGeographyInEcosystem(e)

  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory=validation_data_directory, start_date=start_date, data_layout="data_layout.csv", population_scaledown_factor=flee.SimulationSettings.PopulationScaledownFactor)

  d.ReadL1Corrections("%s/registration_corrections.csv" % input_csv_directory)

  output_header_string = "Day,Date,"

  camp_locations      = e.get_camp_names()

  for l in camp_locations:
      if insert_day0_refugees_in_camps:  
          AddInitialRefugees(e,d,lm[l])
      output_header_string += "%s sim,%s data,%s error," % (lm[l].name, lm[l].name, lm[l].name)

  output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"

  print(output_header_string)

  # Set up a mechanism to incorporate temporary decreases in refugees
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

  for t in range(0,end_time):

    #if t>0:
    ig.AddNewConflictZones(e,t)

    # Determine number of new refugees to insert into the system.
    new_refs = d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=False) - refugee_debt
    refugees_raw += d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=False)

    #Refugees are pre-placed in Mali, so set new_refs to 0 on Day 0.
    if insert_day0_refugees_in_camps:  
        if t == 0:
            new_refs = 0
            #refugees_raw = 0

    if new_refs < 0:
      refugee_debt = -new_refs
      new_refs = 0
    elif refugee_debt > 0:
      refugee_debt = 0

    #Insert refugee agents
    for i in range(0, new_refs):
      e.addAgent(e.pick_conflict_location())

    e.refresh_conflict_weights()
    t_data = t

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
      output += ",0,0,0,0,0,0"

    print(output)
