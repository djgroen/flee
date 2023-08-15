from dflee import dflee, spawning
from dflee.datamanager import handle_refugee_data, read_period
from dflee.datamanager import DataTable #DataTable.subtract_times()
from dflee import dInputGeography
import numpy as np
import dflee.postprocessing.analysis as a
import sys
import time
from dflee.SimulationSettings import SimulationSettings



from datetime import datetime, timedelta

if __name__ == "__main__":

  start_date,end_time = read_period.read_flood_period("{}/flood_period.csv".format(sys.argv[1]))

  start = time.time()
  original_stdout = sys.stdout # Save a reference to the original standard output

  if len(sys.argv)<4:
    print("Please run using: python3 run.py <your_csv_directory> <your_refugee_data_directory> <duration in days> <optional: simsettings.yml> > <output_directory>/<output_csv_filename>")

  input_csv_directory = sys.argv[1]
  validation_data_directory = sys.argv[2]
  if int(sys.argv[3]) > 0:
    end_time = int(sys.argv[3])

  if len(sys.argv)==5:
    dflee.SimulationSettings.ReadFromYML(sys.argv[4])
  else:
    dflee.SimulationSettings.ReadFromYML("simsettings.yml")

  dflee.SimulationSettings.FloodInputFile = "%s/floods.csv" % input_csv_directory

  e = dflee.Ecosystem()

  ig = dInputGeography.InputGeography()

  ig.ReadFloodInputCSV(dflee.SimulationSettings.FloodInputFile)

  ig.ReadLocationsFromCSV("%s/locations.csv" % input_csv_directory)

  ig.ReadLinksFromCSV("%s/routes.csv" % input_csv_directory)

  ig.ReadClosuresFromCSV("%s/closures.csv" % input_csv_directory)

  e,lm = ig.StoreInputGeographyInEcosystem(e)

  if SimulationSettings.spawn_rules["read_from_agents_csv_file"] == True:
    ig.ReadAgentsFromCSV(e, "%s/agents.csv" % input_csv_directory)


  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory=validation_data_directory, start_date=start_date, data_layout="data_layout.csv", population_scaledown_factor=SimulationSettings.optimisations["PopulationScaleDownFactor"])

  d.ReadL1Corrections("%s/registration_corrections.csv" % input_csv_directory)

  output_header_string = "Day,Date,"

  camp_locations      = e.get_camp_names()

  for l in camp_locations:
      spawning.add_initial_refugees(e,d,lm[l])
      output_header_string += "%s sim,%s data,%s error," % (lm[l].name, lm[l].name, lm[l].name)

  output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"

  print(output_header_string)
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

  for t in range(0,end_time):

    #if t>0:
    ig.AddNewFloodZones(e,t)

    new_refs,refugees_raw,refugee_debt = spawning.spawn_daily_displaced(e,t,d)

    spawning.refresh_spawn_weights(e)
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

    if SimulationSettings.log_levels["idp_totals"] > 0:
      output += ",{}".format(e.numIDPs())

    print(output)

  with open('execution_time.txt', 'w') as f:
        sys.stdout = f # Change the standard output to the file we created.
        print('The execution time is:--- %s seconds ---' % (time.time() - start))
        sys.stdout = original_stdout # Reset the standard output to its original value
