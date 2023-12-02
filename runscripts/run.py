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

    camp_locations = e.get_camp_names()

    for l in camp_locations:
        spawning.add_initial_refugees(e,d,lm[l])


    return e, d, ig, lm, camp_locations, start_date, end_time
  


  # run simulation
  def run(self):
    e, d, ig, lm, camp_locations, start_date, end_time = self.setup()
    
    refugee_debt = 0
    refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

    output = []

    for t in range(0,end_time):

      sim_result = {}

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

      # store day and date
      date = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=t)
      sim_result["Day"] = t
      sim_result["Date"] = date.strftime("%Y-%m-%d")

      # define output keys and calculate corrsponding values
      header = ["Total error" ,"refugees in camps (UNHCR)", "total refugees (simulation)", "raw UNHCR refugee count", "refugees in camps (simulation)", "refugee_debt"]
      results = [float(np.sum(abs_errors))/float(refugees_raw), int(sum(loc_data)), e.numAgents(), refugees_raw, refugees_in_camps_sim, refugee_debt]

      # Sim Result, Validation Data and Error for each camp
      for i in range(0,len(errors)):
        sim_result["%s Simulation" % lm[camp_locations[i]].name] = lm[camp_locations[i]].numAgents
        sim_result["%s Data" % lm[camp_locations[i]].name] = loc_data[i]
        sim_result["%s Error" % lm[camp_locations[i]].name] = errors[i]

      # fill output dictionary with results
      if refugees_raw>0:
        for j in range(0, len(header)):
          sim_result["%s" % header[j]] = results[j]
      else:
        for j in range(0, len(header)):
          sim_result["%s" % header[j]] = 0
          if j == 3:
            sim_result["%s" % header[j]] = e.numAgents()
          if j == 5:
            sim_result["%s" % header[j]] = refugees_in_camps_sim

      # total IDPs in simulation    
      if SimulationSettings.log_levels["idp_totals"] > 0:
        sim_result["total IDPs"] = e.numIDPs()


      output.append(sim_result)

    return output