import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  #print("Simulating Burundi.")

  end_time = 396
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

  #Rwanda, Tanzania, Uganda and Congo camps
  locations.append(e.addLocation("Mahama", movechance=0.001, capacity=49105, foreign=True))
  locations.append(e.addLocation("Nduta", movechance=0.001, capacity=55320, foreign=True))
  locations.append(e.addLocation("Kagunga", movechance=1/21.0, foreign=True))
  locations.append(e.addLocation("Nyarugusu", movechance=0.001, capacity=64198, foreign=True))
  locations.append(e.addLocation("Nakivale", movechance=0.001, capacity=18734, foreign=True))
  locations.append(e.addLocation("Kigali", movechance=0.001, foreign=True))
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
  e.linkUp("Kagunga","Nyarugusu","105.0", forced_redirection=True)
  #e.linkUp("Kagunga","Nyarugusu","91.0", forced_redirection=True) #From Kagunga to Kigoma by ship (Kagunga/Kigoma)
  e.linkUp("Kirundo","Nakivale","307.0")
  e.linkUp("Kirundo","Kigali","88.0")
  e.linkUp("Kigali","Nakivale","247.0")
  e.linkUp("Kayanza","Nakivale","426.0")
  e.linkUp("Bujumbura","Lusenda","53.0")


  d = handle_refugee_data.DataTable(csvformat="generic", data_directory="burundi2015", start_date="2015-05-01")

  list_of_cities = "Time"

  for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

  print(list_of_cities)
  #print("Time,",list_of_cities)
  #print("Time, campname")


  conflict_zones = [locations[0]]
  conflict_weights = np.array([497166])

  for t in range(0,end_time):

    #Append conflict_zone and weight to list.
    if t == 70: #Intense fighting between military & multineer military forces
      locations[5].movechance = 1.0

      conflict_zones += [locations[5]]
      conflict_weights = np.append(conflict_weights, [585412])

    elif t==71: #Intense fighting between military & mulineer military forces
      locations[2].movechance = 1.0

      conflict_zones += [locations[2]]
      conflict_weights = np.append(conflict_weights, [460435])
    elif t==224: #Clashes, armed groups coordinately attacked military barracks; API Unit of police executed civilians; Military & police forces retaliate with violent raids
      locations[1].movechance = 1.0
      locations[11].movechance = 1.0
      locations[16].movechance = 1.0

      conflict_zones += [locations[1], locations[11], locations[16]]
      conflict_weights = np.append(conflict_weights, [338023,725223,628256])

    elif t==269: #Clashes between RED-Tabara & government forces
      locations[8].movechance = 1.0

      conflict_zones += [locations[8]]
      conflict_weights = np.append(conflict_weights, [313102])


    new_refs = d.get_new_refugees(t)
    #chosen_location = locations[0]

    #Insert refugee agents
    for i in range(0, new_refs):
      #e.addAgent(location = chosen_location)
      e.addAgent(np.random.choice(conflict_zones, p=conflict_weights/sum(conflict_weights)))

    #Propagate the model by one time step.
    e.evolve()

    #e.printInfo()

    output_string = "%s" % t

    for l in locations:
      output_string = "%s,%s" % (output_string, l.numAgents)

    print(output_string)

    mahama_data = d.get_field("Mahama", t) - d.get_field("Mahama", 0)
    nduta_data = d.get_field("Nduta", t) - d.get_field("Nduta", 0)
    nyarugusu_data = d.get_field("Nyarugusu", t) - d.get_field("Nyarugusu", 0)
    nakivale_data = d.get_field("Nakivale", t) - d.get_field("Nakivale", 0)
    lusenda_data = d.get_field("Lusenda", t) - d.get_field("Lusenda", 0)

    #print(mahama_data, nduta_data, nyarugusu_data, nakivale_data, lusenda_data)

    #print(t, locations[22].numAgents, mahama_data, a.rel_error(locations[22].numAgents, mahama_data))
    #print(t, locations[23].numAgents, nduta_data, a.rel_error(locations[23].numAgents, nduta_data))
    #print(t, locations[25].numAgents, nyarugusu_data, a.rel_error(locations[25].numAgents, nyarugusu_data))
    #print(t, locations[26].numAgents, nakivale_data, a.rel_error(locations[26].numAgents, nakivale_data))
    #print(t, locations[28].numAgents, lusenda_data, a.rel_error(locations[28].numAgents, lusenda_data))

    errors = [a.rel_error(l.numAgents,mahama_data), a.rel_error(l.numAgents,nduta_data), a.rel_error(l.numAgents,nyarugusu_data), a.rel_error(l.numAgents,nakivale_data),a.rel_error(l.numAgents,lusenda_data)]

    #print("location: ", l.numAgents, ", data: ", mahama_data, ", error: ", errors[0])
    #print("location: ", l.numAgents, ", data: ", nduta_data, ", error: ", errors[1])
    #print("location: ", l.numAgents, ", data: ", nyarugusu_data, ", error: ", errors[2])
    #print("location: ", l.numAgents, ", data: ", nakivale_data, ", error: ", errors[3])
    #print("location: ", l.numAgents, ", data: ", lusenda_data, ", error: ", errors[4])


    #print("Cumulative error: ", np.sum(errors), "Squared error: ", np.sqrt(np.sum(np.power(errors,2))))

  if np.abs(np.sum(errors) - 0.495521376979) > 0.1:
    print("TEST FAILED.")
  if np.sqrt(np.sum(np.power(errors,2))) > 0.33+0.03:
    print("TEST FAILED.")
  else:
    print("TEST SUCCESSFUL.")


