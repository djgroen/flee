import flee
import handle_refugee_data
#handle_refugee_data.subtract_dates()
import numpy as np
import analysis as a
import sys

def linkBF(e):
  # bing based
  e.linkUp("Douentza","Mentao","487.0")
  e.linkUp("Mopti","Mentao","360.0")
  e.linkUp("Mopti","Bobo-Dioulasso","462.0")
  e.linkUp("Mentao","Bobo-Dioulasso","475.0")

def linkNiger(e):
  # bing based
  e.linkUp("Menaka","Abala","172.0")
  #e.linkUp("Gao","Mangaize","455.0")
  e.linkUp("Menaka","Mangaize","305.0")
  #e.linkUp("Gao","Niamey","444.0")
  #e.linkUp("Menaka","Niamey","559.0")
  e.linkUp("Gao","Tabareybarey","245.0")
  e.linkUp("Menaka","Tabareybarey","361.0")

  # All distances here are Bing-based.
  e.linkUp("Abala","Mangaize","256.0")
  e.linkUp("Abala","Niamey","253.0")
  e.linkUp("Abala","Tabareybarey","412.0")
  e.linkUp("Mangaize","Niamey","159.0")
  e.linkUp("Mangaize","Tabareybarey","217.0")
  e.linkUp("Niamey","Tabareybarey","205.0")


def AddInitialRefugees(e, d, loc):
  """ Add the initial refugees to a location, using the location name"""
  num_refugees = int(d.get_field(loc.name, 0))
  for i in range(0, num_refugees):
    e.addAgent(location=loc)


def remove_conflict_zone(location, conflict_zones, conflict_weights):
  """
  Shorthand function to remove a conflict zone from the list.
  (not used yet)
  """
  new_conflict_zones = []
  new_weights = np.array([])

  for i in range(0, len(conflict_zones)):
    if conflict_zones[i].name is not location.name:
      new_conflict_zones += [conflict_zones[i]]
      new_weights = np.append(new_weights, [conflict_weights[i]])

  return new_conflict_zones, new_weights

def date_to_sim_days(date):
  return handle_refugee_data.subtract_dates(date,"2012-02-29")


if __name__ == "__main__":

  if len(sys.argv)>1:
    end_time = int(sys.argv[1])
  else:
    end_time = 61

  e = flee.Ecosystem()

# Distances are estimated using Bing Maps.

# Mali
  
  lm = {}

  lm["Kidal"] = e.addLocation("Kidal", movechance=0.3, pop=25617)
  # pop. 25,617. GPS 18.444305 1.401523
  lm["Gao"] = e.addLocation("Gao", movechance=0.3, pop=86633)
  # pop. 86,633. GPS 16.270910 -0.040210
  lm["Timbuktu"] = e.addLocation("Timbuktu", movechance=0.3, pop=54453)
  # pop. 54,453. GPS 16.780260 -3.001590
  lm["Mopti"] = e.addLocation("Mopti", movechance=0.3, pop=108456)
  # pop. 108,456 (2009 census)
  lm["Douentza"] = e.addLocation("Douentza", movechance=0.3, pop=28005)
  # pop. 28,005 (2009 census), fell on 5th of April 2012.
  lm["Konna"] = e.addLocation("Konna", movechance=0.3, pop=36767)
  # pop. 36,767 (2009 census), captured in January 2013 by the Islamists.
  lm["Menaka"] = e.addLocation("Menaka", movechance=1.0, pop=20702)
  # pop. 20,702 (2009 census), captured in January 2012 by the Islamists.
  lm["Niafounke"] = e.addLocation("Niafounke", movechance=1.0, pop=1000)
  # pop. negligible. Added because it's a junction point, move chance set to 1.0 for that reason.
  lm["Bourem"] = e.addLocation("Bourem", movechance=0.3, pop=27486)
  # pop. 27,486. GPS 16.968122, -0.358435. No information about capture yet, but it's a sizeable town at a junction point.
  lm["Bamako"] = e.addLocation("Bamako", movechance=0.3, pop=1809106)
  # pop. 1,809,106 capital subject to coup d'etat between March 21st and April 8th 2012.
  

  # bing based
  e.linkUp("Kidal","Bourem", "308.0") #964.0
  e.linkUp("Gao","Bourem","97.0") #612
  e.linkUp("Timbuktu","Bourem","314.0")

  e.linkUp("Timbuktu", "Konna","303.0") #Mopti is literally on the way to Bobo-Dioulasso.
  e.linkUp("Gao", "Douentza","397.0") #Mopti is literally on the way to Bobo-Dioulasso.
  e.linkUp("Douentza","Konna","121.0") #Douentza is on the road between Gao and Mopti.
  e.linkUp("Konna","Mopti","70.0") #Douentza is on the road between Gao and Mopti.

  e.linkUp("Gao","Menaka","314.0")

  e.linkUp("Timbuktu","Niafounke","162.0")
  e.linkUp("Niafounke","Konna","153.0")

# Mauritania

  m1 = e.addLocation("Mbera", movechance=0.001, capacity=103731, foreign=True)
  # GPS 15.639012,-5.751422
  m2 = e.addLocation("Fassala", movechance=0.08, foreign=True)

  # bing based
  e.linkUp("Niafounke","Fassala","241.0")
  e.linkUp("Fassala","Mbera","25.0", forced_redirection=True)

# Burkina Faso

  b1 = e.addLocation("Mentao", movechance=0.001, capacity=10038, foreign=True)
  # GPS 13.999700,-1.680371
  b2 = e.addLocation("Bobo-Dioulasso", movechance=0.001, capacity=1926, foreign=True)
  # GPS 11.178103,-4.291773

  # No linking up yet, as BF border was shut prior to March 21st 2012.

# Niger
  n1 = e.addLocation("Abala", movechance=0.001, capacity=18573, foreign=True)
  # GPS 14.927683 3.433727
  n2 = e.addLocation("Mangaize", movechance=0.001, capacity=4356, foreign=True)
  # GPS 14.684030 1.882720
  n3 = e.addLocation("Niamey", movechance=0.001, capacity=6327, foreign=True)

  n4 = e.addLocation("Tabareybarey", movechance=0.001, capacity=9189, foreign=True)
  # GPS 14.754761 0.944773

  d = handle_refugee_data.DataTable(csvformat="generic", data_directory="mali2012/")

  print("Day,Mbera sim,Mbera data,Mbera error,Fassala sim,Fassala data,Fassala error,Mentao sim,Mentao data,Mentao error,Bobo-Dioulasso sim,Bobo-Dioulasso data,Bobo-Dioulasso error,Abala sim,Abala data,Abala error,Mangaize sim,Mangaize data,Mangaize error,Niamey sim,Niamey data,Niamey error,Tabareybarey sim,Tabareybarey data,Tabareybarey error,Total error,refugees in camps (UNHCR),refugees in camps (simulation),raw UNHCR refugee count,retrofitted time,camps_sim_count")

  # Kidal has fallen. All refugees want to leave this place.
  lm["Kidal"].movechance = 1.0

  # Set up a mechanism to incorporate temporary decreases in refugees 
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.
 
  # Add initial refugees to the destinations. 
  AddInitialRefugees(e,d,m1)
  AddInitialRefugees(e,d,m2)
  AddInitialRefugees(e,d,b1)
  AddInitialRefugees(e,d,b2)
  AddInitialRefugees(e,d,n1)
  AddInitialRefugees(e,d,n2)
  AddInitialRefugees(e,d,n3)
  AddInitialRefugees(e,d,n4)

  e.add_conflict_zone("Menaka")

  for t in range(0,end_time):

    # Close/open borders here.
    if t == date_to_sim_days("2012-03-19"): #On the 19th of March, Fassala closes altogether, and instead functions as a forward to Mbera (see PDF report 1 and 2).
      m2.movechance = 1.0
    if t == date_to_sim_days("2012-03-21"): #On the 21st of March, Burkina Faso opens its borders (see PDF report 3).
      linkBF(e)   
    if t == date_to_sim_days("2012-04-01"): #Starting from April, refugees appear to enter Niger again (on foot, report 4).
      linkNiger(e)


    new_refs = d.get_new_refugees(t, FullInterpolation=True) - refugee_debt
    refugees_raw += d.get_new_refugees(t, FullInterpolation=False)
    if new_refs < 0:
      refugee_debt = -new_refs
      new_refs = 0

    if t == date_to_sim_days("2012-02-03"):
      lm["Kidal"].movechance = 1.0
      e.add_conflict_zone("Kidal")

    if t == date_to_sim_days("2012-03-23"): #Kidal has fallen, but Gao and Timbuktu are still controlled by Mali
      lm["Gao"].movechance = 1.0 # Refugees now want to leave Gao.
      e.add_conflict_zone("Gao")  
 
 
    # Here we use the random choice to make a weighted choice between the source locations.
    total_conflict_pop = sum(e.conflict_weights)
    for i in range(0, new_refs):
      e.addAgent(e.pick_conflict_location())

    e.evolve()

    # Basic output
    # e.printInfo()

    
    # Validation / data comparison
    camps = [m1,m2,b1,b2,n1,n2,n3,n4]
    camp_names = ["Mbera", "Fassala", "Mentao", "Bobo-Dioulasso", "Abala", "Mangaize", "Niamey", "Tabareybarey"]
    # TODO: refactor camp_names using list comprehension.
 
    camp_pops = []
    errors = []
    abs_errors = []
    for i in range(0, len(camp_names)):
      camp_pops += [d.get_field(camp_names[i], t)]
      errors += [a.rel_error(camps[i].numAgents, camp_pops[-1])]
      abs_errors += [a.abs_error(camps[i].numAgents, camp_pops[-1])]

    locations = camps
    loc_data = camp_pops

    #if e.numAgents()>0:
    #  print "Total error: ", float(np.sum(abs_errors))/float(e.numAgents())

    # calculate retrofitted time.
    refugees_in_camps_sim = 0
    for c in camps:
      refugees_in_camps_sim += c.numAgents
    t_retrofitted = d.retrofit_time_to_refugee_count(refugees_in_camps_sim, camp_names)

    # write output (one line per time step taken.
    output = "%s" % (t)
    for i in range(0,len(locations)):
      output += ",%s,%s,%s" % (locations[i].numAgents, loc_data[i], errors[i])

    if e.numAgents()>0:
      output += ",%s,%s,%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(sum(loc_data)), int(sum(loc_data)), e.numAgents(), refugees_raw, t_retrofitted, refugees_in_camps_sim)
    else:
      output += ",0"

    print(output)
