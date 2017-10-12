from flee import flee
from datamanager import handle_refugee_data
from datamanager import DataTable #DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import outputanalysis.analysis as a
import sys

def AddInitialRefugees(e, d, loc):
  """ Add the initial refugees to a location, using the location name"""
  num_refugees = int(d.get_field(loc.name, 0, FullInterpolation=True))
  for i in range(0, num_refugees):
    e.addAgent(location=loc)

def date_to_sim_days(date):
  return DataTable.subtract_dates(date,"2013-12-01")


if __name__ == "__main__":

  end_time = 820
  last_physical_day = 820

  if len(sys.argv)>1:
    if (sys.argv[1]).isnumeric():
      end_time = int(sys.argv[1])
      last_physical_day = int(sys.argv[1])
    else:
      end_time = 820
      last_physical_day = 820
      duration = flee.SimulationSettings.SimulationSettings.ReadFromCSV(sys.argv[1])
      if duration>0:
        end_time = duration
        last_physical_day = end_time

  e = flee.Ecosystem()

  ig = InputGeography.InputGeography()

  ig.ReadLocationsFromCSV("examples/car_input_csv/locations.csv")

  ig.ReadLinksFromCSV("examples/car_input_csv/routes.csv")

  lm = ig.StoreInputGeographyInEcosystem(e)

  #print("Network data loaded")

  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory="source_data/car2014/", start_date="2013-12-01")

  #Correcting for overestimations due to inaccurate level 1 registrations in five of the camps.
  #These errors led to a perceived large drop in refugee population in all of these camps.
  #We correct by linearly scaling the values down to make the last level 1 registration match the first level 2 registration value.
  #To our knowledge, all level 2 registration procedures were put in place by the end of 2016.
  d.correctLevel1Registrations("Amboko","2015-09-30")
  d.correctLevel1Registrations("Belom","2015-08-31")
  d.correctLevel1Registrations("Dosseye","2015-09-30")
  d.correctLevel1Registrations("Gondje","2015-09-30")
  lm["Moyo"].capacity *= d.correctLevel1Registrations("Moyo","2015-06-02") #also "2014-05-11" and "2015-06-02"
  d.correctLevel1Registrations("East","2014-09-28")
  d.correctLevel1Registrations("Adamaoua","2014-10-19")
  #d.correctLevel1Registrations("Mole","2016-02-29") # no clear decrease visible.
  d.correctLevel1Registrations("Bili","2016-06-30")
  #d.correctLevel1Registrations("Bossobolo","2016-05-20") #Data is only decreasing over time, so no grounds for a level1 corr.
  d.correctLevel1Registrations("Boyabu","2016-06-30")
  d.correctLevel1Registrations("Inke","2014-06-30")
  d.correctLevel1Registrations("Betou","2014-03-22")
  #d.correctLevel1Registrations("Brazaville","2016-04-30")

  lm["Amboko"].capacity = d.getMaxFromData("Amboko", last_physical_day)
  lm["Belom"].capacity = d.getMaxFromData("Belom", last_physical_day) # set manually.
  lm["Dosseye"].capacity = d.getMaxFromData("Dosseye", last_physical_day)
  lm["Gondje"].capacity = d.getMaxFromData("Gondje", last_physical_day)
  #lm["Moyo"].capacity = d.getMaxFromData("Moyo", last_physical_day ) # blip in the data set, set capacity manually.
  lm["East"].capacity = d.getMaxFromData("East", last_physical_day)
  lm["Adamaoua"].capacity = d.getMaxFromData("Adamaoua", last_physical_day)
  lm["Mole"].capacity = d.getMaxFromData("Mole", last_physical_day)
  lm["Bili"].capacity = d.getMaxFromData("Bili", last_physical_day)
  #lm["Bossobolo"].capacity = d.getMaxFromData("Bossobolo", last_physical_day) #camp excluded
  lm["Boyabu"].capacity = d.getMaxFromData("Boyabu", last_physical_day)
  lm["Mboti"].capacity = d.getMaxFromData("Mboti", last_physical_day)
  lm["Inke"].capacity = d.getMaxFromData("Inke", last_physical_day)
  lm["Betou"].capacity = d.getMaxFromData("Betou", last_physical_day)
  lm["Brazaville"].capacity = d.getMaxFromData("Brazaville", last_physical_day)

  output_header_string = "Day,"

  for l in e.locations:
    AddInitialRefugees(e,d,l)
    output_header_string += "%s sim,%s data,%s error," % (l.name, l.name, l.name)

  output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"

  print(output_header_string)

  # Set up a mechanism to incorporate temporary decreases in refugees
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

  e.add_conflict_zone("Ndele")

  # Start with a refugee debt to account for the mismatch between camp aggregates and total UNHCR data.
  #refugee_debt = e.numAgents()

  for t in range(0,end_time):

    e.refresh_conflict_weights()

    t_data = t

    new_refs = 100
    """
    # Determine number of new refugees to insert into the system.
    new_refs = d.get_daily_difference(t, FullInterpolation=True, ZeroOnDayZero=False) - refugee_debt
    refugees_raw += d.get_daily_difference(t, FullInterpolation=True, ZeroOnDayZero=False)
    if new_refs < 0:
      refugee_debt = -new_refs
      new_refs = 0
    elif refugee_debt > 0:
      refugee_debt = 0
    """

    for l in e.locations:
      new_IDPs = int(d_spawn.get_field(l.name, t+1) - d_spawn.get_field(l.name, t))
      if new_IDPs > 0:
        l.movechance = 1.0
      else:
        l.movechance = 0.001
      for i in range(0, int(new_IDPs/6)):
        e.addAgent(l)

    e.evolve()

    #e.printInfo()

    # Validation / data comparison
    camps = e.locations
    camp_names = e.locationNames
    # TODO: refactor camp_names using list comprehension.

    # calculate retrofitted time.
    refugees_in_camps_sim = 0
    for c in camps:
      refugees_in_camps_sim += c.numAgents

    # calculate error terms.
    camp_pops = []
    errors = []
    abs_errors = []
    for i in range(0, len(camp_names)):
      # normal 1 step = 1 day errors.
      camp_pops += [d.get_field(camp_names[i], t, FullInterpolation=True)]
      errors += [a.rel_error(camps[i].numAgents, camp_pops[-1])]
      abs_errors += [a.abs_error(camps[i].numAgents, camp_pops[-1])]

    # Total error is calculated using float(np.sum(abs_errors))/float(refugees_raw))

    locations = camps
    loc_data = camp_pops

    #if e.numAgents()>0:
    #  print "Total error: ", float(np.sum(abs_errors))/float(e.numAgents())

    # write output (one line per time step taken.
    output = "%s" % (t)
    for i in range(0,len(locations)):
      output += ",%s,%s,%s" % (locations[i].numAgents, loc_data[i], errors[i])

    if float(sum(loc_data))>0:
      # Reminder: Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,retrofitted time,refugees in camps (simulation),Total error (retrofitted)
      output += ",%s,%s,%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(refugees_raw+1), int(sum(loc_data)), e.numAgents(), refugees_raw, refugees_in_camps_sim, refugee_debt)
    else:
      output += ",0,0,0,0,0,0,0"

    print(output)

