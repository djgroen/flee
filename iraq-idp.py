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
  return DataTable.subtract_dates(date,"2014-05-01")


if __name__ == "__main__":

  if len(sys.argv)>1:
    end_time = int(sys.argv[1])
    last_physical_day = int(sys.argv[1])
  else:
    end_time = 300
    last_physical_day = 300

  RetroFitting = False
  if len(sys.argv)>2:
    if "-r" in sys.argv[2]:
      RetroFitting = True
      end_time *= 10

  e = flee.Ecosystem()
  flee.SimulationSettings.UseIDPMode = True


  ig = InputGeography.InputGeography()

  ig.ReadLocationsFromCSV("iraq/iraq-locations.csv", columns=["region","area (km^2)","pop/cap","name","capital pop.","gps_x","gps_y"])

  ig.ReadLinksFromCSV("iraq/iraq-links.csv")

  lm = ig.StoreInputGeographyInEcosystem(e)

  #print("Network data loaded")

  d_spawn = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory="iraq/spawn_data",start_date="2014-05-01")
  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory="iraq/idp_counts",start_date="2014-05-01")


  output_header_string = "Day,"

  for l in e.locations:
    AddInitialRefugees(e,d,l)
    output_header_string += "%s sim,%s data,%s error," % (l.name, l.name, l.name)

  output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"

  print(output_header_string)

  # Set up a mechanism to incorporate temporary decreases in refugees
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

  e.add_conflict_zone("Baghdad")

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

