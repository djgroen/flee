import flee
import handle_refugee_data
import numpy as np
import analysis as a
import sys

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

#Burundi Simulation

if __name__ == "__main__":

  end_time = 1200 #396

  e = flee.Ecosystem()

  locations = []

  #Burundi
  locations.append(e.addLocation("Bujumbura", movechance=1.0))

  locations.append(e.addLocation("Bubanza", movechance=0.3))
  locations.append(e.addLocation("Cibitoke", movechance=0.3))
  locations.append(e.addLocation("Isale", movechance=0.3))
  locations.append(e.addLocation("Muramvya", movechance=0.3))
  locations.append(e.addLocation("Kayanza", movechance=0.3))
  locations.append(e.addLocation("Mwaro", movechance=0.3))
  locations.append(e.addLocation("Rumonge", movechance=0.3))
  locations.append(e.addLocation("Bururi", movechance=0.3))
  locations.append(e.addLocation("Rutana", movechance=0.3))
  locations.append(e.addLocation("Makamba", movechance=0.3))
  locations.append(e.addLocation("Gitega", movechance=0.3))
  locations.append(e.addLocation("Karuzi", movechance=0.3))
  locations.append(e.addLocation("Ruyigi", movechance=0.3))
  locations.append(e.addLocation("Cankuzo", movechance=0.3))
  locations.append(e.addLocation("Muyinga", movechance=0.3))
  locations.append(e.addLocation("Kirundo", movechance=0.3))
  locations.append(e.addLocation("Ngozi", movechance=0.3))
  locations.append(e.addLocation("Gashoho", movechance=0.3))
  locations.append(e.addLocation("Gitega-Ruyigi", movechance=0.3))
  locations.append(e.addLocation("Makebuko", movechance=0.3))
  locations.append(e.addLocation("Commune of Mabanda", movechance=0.3))

  #Rwanda, Tanzania, Uganda and DRCongo camps
  locations.append(e.addLocation("Mahama", movechance=0.001, capacity=49451, foreign=True))
  locations.append(e.addLocation("Nduta", movechance=0.001, capacity=55320, foreign=True))
  locations.append(e.addLocation("Kagunga", movechance=1/21.0, foreign=True))
  locations.append(e.addLocation("Nyarugusu", movechance=0.001, capacity=100925, foreign=True))
  locations.append(e.addLocation("Gashora", movechance=0.3, foreign=True))
  locations.append(e.addLocation("Kayonza", movechance=0.3, foreign=True))
  locations.append(e.addLocation("Kabarore", movechance=0.3, foreign=True))
  locations.append(e.addLocation("Kagitumba", movechance=0.3, foreign=True))
  locations.append(e.addLocation("Gitarama", movechance=0.3, foreign=True))
  locations.append(e.addLocation("Kigali", movechance=0.3, foreign=True))
  locations.append(e.addLocation("Kabale", movechance=0.3, foreign=True))
  locations.append(e.addLocation("Nakivale", movechance=0.001, capacity=18734, foreign=True))
  locations.append(e.addLocation("Lusenda", movechance=0.001, capacity=17210, foreign=True))

  #Within Burundi
  e.linkUp("Bujumbura","Bubanza","48.0")
  e.linkUp("Bujumbura","Cibitoke","64.0")
  e.linkUp("Bujumbura","Isale","11.0")
  e.linkUp("Isale","Muramvya","47.0")
  e.linkUp("Muramvya","Gitega","44.0")
  e.linkUp("Gitega","Gitega-Ruyigi","12.0")
  e.linkUp("Gitega-Ruyigi","Karuzi","42.0")
  e.linkUp("Gitega-Ruyigi","Ruyigi","43.0")
  e.linkUp("Karuzi","Muyinga","42.0")
  e.linkUp("Isale","Kayanza","84.0")
  e.linkUp("Kayanza","Ngozi","31.0")
  e.linkUp("Ngozi","Gashoho","41.0")
  e.linkUp("Gashoho","Kirundo","42.0")
  e.linkUp("Gashoho","Muyinga","34.0")
  e.linkUp("Bujumbura","Mwaro","67.0")
  e.linkUp("Mwaro","Gitega","46.0")
  e.linkUp("Bujumbura","Rumonge","75.0")
  e.linkUp("Rumonge","Bururi","31.0")
  e.linkUp("Rumonge","Commune of Mabanda","73.0")
  e.linkUp("Commune of Mabanda","Makamba","18.0")
  e.linkUp("Bururi","Rutana","65.0")
  e.linkUp("Makamba","Rutana","50.0")
  e.linkUp("Rutana","Makebuko","46.0")
  e.linkUp("Makebuko","Gitega","24.0")
  e.linkUp("Makebuko","Ruyigi","40.0")
  e.linkUp("Ruyigi","Cankuzo","51.0")
  e.linkUp("Cankuzo","Muyinga","63.0")

  #Camps, starting at index locations[22] (at time of writing).
  e.linkUp("Muyinga","Mahama","135.0")
  e.linkUp("Ruyigi","Nduta","90.0")
  e.linkUp("Commune of Mabanda","Kagunga","36.0")
  e.linkUp("Kagunga","Nyarugusu","91.0", forced_redirection=True) #From Kagunga to Kigoma by ship (Kagunga=Kigoma)
  e.linkUp("Kirundo","Gashora","55.0")
  e.linkUp("Gashora","Kayonza","81.0")
  e.linkUp("Kayonza","Kabarore","45.0")
  e.linkUp("Kabarore","Kagitumba","71.0")
  e.linkUp("Kagitumba","Nakivale","66.0")
  e.linkUp("Gashora","Kigali","57.0")
  e.linkUp("Kayanza","Gitarama","133.0")
  e.linkUp("Gitarama","Kigali","44.0")
  e.linkUp("Kigali","Kabale","96.0")
  e.linkUp("Kabale","Nakivale","140.0")
  e.linkUp("Bujumbura","Lusenda","53.0")


  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory="burundi2015", start_date="2015-05-01")

  list_of_cities = "Time"

  for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

  #print(list_of_cities)
  #print("Time, campname")
  print("Day,Mahama sim,Mahama data,Mahama error,Nduta sim,Nduta data,Nduta error,Nyarugusu sim,Nyarugusu data,Nyarugusu error,Nakivale sim,Nakivale data,Nakivale error,Lusenda sim,Lusenda data,Lusenda error,Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,retrofitted time,refugees in camps (simulation),refugee_debt,Total error (retrofitted)")


  #Bujumbura is in conflict area. All refugees want to leave this place.
  locations[0].movechance = 1.0

  #Set up a mechanism to incorporate temporary decreases in refugees
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only


  conflict_zones = [locations[0]]
  conflict_weights = np.array([497166])


  for t_retrofit in range(0,end_time):

    #Append conflict_zone and weight to list.
    if int(t_retrofit) == 70: #Intense fighting between military & multineer military forces
      locations[5].movechance = 1.0

      conflict_zones += [locations[5]]
      conflict_weights = np.append(conflict_weights, [585412])

    elif int(t_retrofit) == 71: #Intense fighting between military & mulineer military forces
      locations[2].movechance = 1.0

      conflict_zones += [locations[2]]
      conflict_weights = np.append(conflict_weights, [460435])

    elif int(t_retrofit) == 224: #Clashes, armed groups coordinately attacked military barracks; API Unit of police executed civilians; Military & police forces retaliate with violent raids
      locations[1].movechance = 1.0
      locations[11].movechance = 1.0
      locations[16].movechance = 1.0

      conflict_zones += [locations[1], locations[11], locations[16]]
      conflict_weights = np.append(conflict_weights, [338023,725223,628256])

    elif int(t_retrofit) == 269: #Clashes between RED-Tabara & government forces
      locations[8].movechance = 1.0

      conflict_zones += [locations[8]]
      conflict_weights = np.append(conflict_weights, [313102])


    #new_refs = d.get_new_refugees(t)
    new_refs = d.get_new_refugees(t_retrofit, FullInterpolation=True) - refugee_debt
    refugees_raw += d.get_new_refugees(t_retrofit, FullInterpolation=True)
    if new_refs < 0:
      refugee_debt = -new_refs
      new_refs = 0
    elif refugee_debt > 0:
      refugee_debt = 0

    #Insert refugee agents
    for i in range(0, new_refs):
      e.addAgent(np.random.choice(conflict_zones, p=conflict_weights/sum(conflict_weights)))

    #Propagate the model by one time step.
    e.evolve()

    #e.printInfo()

    #Validation/data comparison
    mahama_data = d.get_field("Mahama", t_retrofit) #- d.get_field("Mahama", 0)
    nduta_data = d.get_field("Nduta", t_retrofit) #-d.get_field("Nduta", 0)
    nyarugusu_data = d.get_field("Nyarugusu", t_retrofit) #- d.get_field("Nyarugusu", 0)
    nakivale_data = d.get_field("Nakivale", t_retrofit) #- d.get_field("Nakivale", 0)
    lusenda_data = d.get_field("Lusenda", t_retrofit) #- d.get_field("Lusenda", 0)

    errors = []
    abs_errors = []
    loc_data = [mahama_data, nduta_data, nyarugusu_data, nakivale_data, lusenda_data]
    camp_locations = [22, 23, 25, 33, 34]

    camps = []
    for i in camp_locations:
      camps += [locations[i]]
    camp_names = ["Mahama", "Nduta", "Nyarugusu", "Nakivale", "Lusenda"]

    camp_pops_retrofitted = []
    errors_retrofitted = []
    abs_errors_retrofitted = []

    # calculate retrofitted time.
    refugees_in_camps_sim = 0
    for c in camps:
      refugees_in_camps_sim += c.numAgents
    t_retrofitted = d.retrofit_time_to_refugee_count(refugees_in_camps_sim, camp_names)

    # calculate errors
    for i in range(0,len(camp_locations)):
      camp_number = camp_locations[i]
      errors += [a.rel_error(locations[camp_number].numAgents, loc_data[i])]
      abs_errors += [a.abs_error(locations[camp_number].numAgents, loc_data[i])]

      # errors when using retrofitted time stepping.
      camp_pops_retrofitted += [d.get_field(camp_names[i], t_retrofitted, FullInterpolation=True)]
      errors_retrofitted += [a.rel_error(camps[i].numAgents, camp_pops_retrofitted[-1])]
      abs_errors_retrofitted += [a.abs_error(camps[i].numAgents, camp_pops_retrofitted[-1])]

    output = "%s" % t_retrofit

    for i in range(0,len(errors)):
      camp_number = camp_locations[i]
      output += ",%s,%s,%s" % (locations[camp_number].numAgents, loc_data[i], errors[i])


    if refugees_raw>0:
      #output_string += ",%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(refugees_raw), int(sum(loc_data)), e.numAgents(), refugees_raw)
      output += ",%s,%s,%s,%s,%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(refugees_raw), int(sum(loc_data)), e.numAgents(), refugees_raw, t_retrofitted, refugees_in_camps_sim, refugee_debt, float(np.sum(abs_errors_retrofitted))/float(refugees_raw))
    else:
      output += ",0,0,0,0,0,0,0"
      #output_string += ",0"


    print(output)

