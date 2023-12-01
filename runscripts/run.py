from flee import flee, spawning
from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable #DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import flee.postprocessing.analysis as a
from flee.SimulationSettings import SimulationSettings

from datetime import datetime, timedelta

class Simulation:



  # initialize simulation
  def __init__(self, input_csv_directory, validation_data_directory, duration, simsettings):
    # error handling
    if input_csv_directory is None:
      raise ValueError("input_csv_directory cannot be None")
    if validation_data_directory is None:
      raise ValueError("validation_data_directory cannot be None")
    if duration is None:
      raise ValueError("duration cannot be None")
    elif not isinstance(duration, int):
      raise ValueError("duration must be an integer")
    self.input_csv_directory = input_csv_directory
    self.validation_data_directory = validation_data_directory
    self.duration = duration
    self.simsettings = simsettings



  # setup simulation
  def setup(self):
    start_date,end_time = read_period.read_sim_period("{}/sim_period.csv".format(self.input_csv_directory))
    input_csv_directory = self.input_csv_directory
    validation_data_directory = self.validation_data_directory

    if int(self.duration) > 0:
      end_time = int(self.duration)

    if self.simsettings is not None:
      flee.SimulationSettings.ReadFromYML(self.simsettings)
    else:
      flee.SimulationSettings.ReadFromYML("simsetting.yml")

    # Conflict file will be read if modelling conflict-driven displacement. Ignored otherwise.
    flee.SimulationSettings.ConflictInputFile = "%s/conflicts.csv" % input_csv_directory

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

    output = [{"Day": []}, {"Date": []}]

    camp_locations = e.get_camp_names()

    for l in camp_locations:
        spawning.add_initial_refugees(e,d,lm[l])
        output.append({"%s Simulation" % lm[l].name: []})
        output.append({"%s Data" % lm[l].name: []})
        output.append({"%s Error" % lm[l].name: []})

    header = ["Total error" ,"refugees in camps (UNHCR)", "total refugees (simulation)", "raw UNHCR refugee count", "refugees in camps (simulation)", "refugee_debt"]
    for h in header:
      output.append({"%s" % h: []})

    if SimulationSettings.log_levels["idp_totals"] > 0:
      output.append({"total IDPs": []})

    return e, d, ig, lm, camp_locations, start_date, end_time, output, header
  


  # run simulation
  def run(self):
    e, d, ig, lm, camp_locations, start_date, end_time, output, header = self.setup()
    
    refugee_debt = 0
    refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

    for t in range(0,end_time):

      #if t>0:
      ig.AddNewConflictZones(e,t)

      _,refugees_raw,refugee_debt = spawning.spawn_daily_displaced(e,t,d)

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
      output[0]["Day"].append(t)
      output[1]["Date"].append(date.strftime("%Y-%m-%d"))

      # values for:
      # "Total error" ,"refugees in camps (UNHCR)", "total refugees (simulation)", "raw UNHCR refugee count", "refugees in camps (simulation)", "refugee_debt"
      results = [float(np.sum(abs_errors))/float(refugees_raw), int(sum(loc_data)), e.numAgents(), refugees_raw, refugees_in_camps_sim, refugee_debt]

      for i in range(0,len(errors)):
        output[2+i*3]["%s Simulation" % lm[camp_locations[i]].name].append(lm[camp_locations[i]].numAgents)
        output[3+i*3]["%s Data" % lm[camp_locations[i]].name].append(loc_data[i])
        output[4+i*3]["%s Error" % lm[camp_locations[i]].name].append(errors[i])

        # append at end of output
        if i == len(errors)-1:
          if refugees_raw>0:
            for j in range(0, len(results)):
              output[5+i*3+j]["%s" % header[j]].append(results[j])
          else:
            for j in range(0, len(results)):
              output[5+i*3+j]["%s" % header[j]].append(0)
              if j == 3:
                output[5+i*3+j]["%s" % header[j]].append(e.numAgents())
              if j == 5:
                output[5+i*3+j]["%s" % header[j]].append(refugees_in_camps_sim)
          
          if SimulationSettings.log_levels["idp_totals"] > 0:
            output[5+i*3+len(results)]["total IDPs"].append(e.numIDPs())

    return output