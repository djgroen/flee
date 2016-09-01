import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  #print("Central African Republic (CAR) Simulation")

  end_time = 820
  e = flee.Ecosystem()

  locations = []

  #CAR
  locations.append(e.addLocation("Bangui", movechance=1.0))

  locations.append(e.addLocation("Bangassou", movechance=0.3))
  locations.append(e.addLocation("Mobaye", movechance=0.3))
  locations.append(e.addLocation("Sibut", movechance=0.3))
  locations.append(e.addLocation("Bouar", movechance=0.3))
  locations.append(e.addLocation("Bossangoa", movechance=0.3))
  locations.append(e.addLocation("Nola", movechance=0.3))
  locations.append(e.addLocation("Mbaiki", movechance=0.3))
  locations.append(e.addLocation("Bimbo", movechance=0.3))
  locations.append(e.addLocation("Bozoum", movechance=0.3))
  locations.append(e.addLocation("Obo", movechance=0.3))
  locations.append(e.addLocation("Bambari", movechance=0.3))
  locations.append(e.addLocation("Bria", movechance=0.3))
  locations.append(e.addLocation("Ndele", movechance=0.3))
  locations.append(e.addLocation("Birao", movechance=0.3))
  locations.append(e.addLocation("Kaga Bandoro", movechance=0.3))
  locations.append(e.addLocation("Berberati", movechance=0.3))

  locations.append(e.addLocation("Melego", movechance=0.3))
  locations.append(e.addLocation("Rafai", movechance=0.3))
  locations.append(e.addLocation("Bakouma", movechance=0.3))
  locations.append(e.addLocation("Abrou", movechance=0.3))
  locations.append(e.addLocation("RN5", movechance=0.3))
  locations.append(e.addLocation("Ippy", movechance=0.3))
  locations.append(e.addLocation("Bakala", movechance=0.3))
  locations.append(e.addLocation("Mbres", movechance=0.3))
  locations.append(e.addLocation("Dekoa", movechance=0.3))
  locations.append(e.addLocation("Bossembele", movechance=0.3))
  locations.append(e.addLocation("Yaloke", movechance=0.3))
  locations.append(e.addLocation("Katakpo", movechance=0.3))
  locations.append(e.addLocation("Banga", movechance=0.3))
  locations.append(e.addLocation("Baoro", movechance=0.3))
  locations.append(e.addLocation("Batangafo", movechance=0.3))
  locations.append(e.addLocation("Kago", movechance=0.3))
  locations.append(e.addLocation("Yapara", movechance=0.3))
  locations.append(e.addLocation("Beboura III", movechance=0.3))
  locations.append(e.addLocation("Gamboula", movechance=0.3))
  locations.append(e.addLocation("Baboua", movechance=0.3))

  #Chad, Cameroon and Congo camps
  locations.append(e.addLocation("Belom", movechance=0.001))
  locations.append(e.addLocation("Dosseye", movechance=0.001))
  locations.append(e.addLocation("East", movechance=0.001))
  locations.append(e.addLocation("Adamaoua", movechance=0.001))
  locations.append(e.addLocation("Monga", movechance=0.001))
  locations.append(e.addLocation("Mole", movechance=0.001))
  locations.append(e.addLocation("Gbadolite", movechance=0.001))
  locations.append(e.addLocation("Inke", movechance=0.001))

  """ #Chad, Cameroon and Congo camps
  locations.append(e.addLocation("Belom", movechance=0.001, capacity=19172, foreign=True))
  locations.append(e.addLocation("Dosseye", movechance=0.001, capacity=12449, foreign=True))
  locations.append(e.addLocation("East", movechance=0.001, capacity=180485, foreign=True))
  locations.append(e.addLocation("Adamaoua", movechance=0.001, capacity=71506, foreign=True))
  locations.append(e.addLocation("Monga", movechance=0.001))
  locations.append(e.addLocation("Mole", movechance=0.001, capacity=20454, foreign=True))
  locations.append(e.addLocation("Gbadolite", movechance=0.001))
  locations.append(e.addLocation("Inke", movechance=0.001, capacity=20365, foreign=True))
  """

  #Within CAR
  e.linkUp("Mobaye","Melego","67.0")
  e.linkUp("Melego","Bangassou","191.0")
  e.linkUp("Bangassou","Rafai","132.0")
  e.linkUp("Rafai","Obo","349.0")
  e.linkUp("Rafai","Bakouma","173.0")
  e.linkUp("Bakouma","Abrou","91.0")
  e.linkUp("Abrou","Bria","70.0")
  e.linkUp("Melego","Bambari","153.0")
  e.linkUp("Bria","Ippy","96.0")
  e.linkUp("Ippy","Bambari","106.0")
  e.linkUp("Bambari","Bakala","168.0")
  e.linkUp("Ippy","Bakala","114.0")
  e.linkUp("Bakala","Mbres","78.0")
  e.linkUp("Bambari","Sibut","191.0")
  e.linkUp("Sibut","Dekoa","69.0")
  e.linkUp("Dekoa","Mbres","94.0")
  e.linkUp("Mbres","Kaga Bandoro","91.0")
  e.linkUp("Dekoa","Kaga Bandoro","80.0")
  e.linkUp("Mbres","Ndele","233.0")
  e.linkUp("Ndele","Birao","353.0")
  e.linkUp("Ndele","RN5","225.0")
  e.linkUp("RN5","Birao","390.0")
  e.linkUp("RN5","Bria","90.0")
  e.linkUp("Kaga Bandoro","Yapara","49.0")
  e.linkUp("Yapara","Batangafo","64.0")
  e.linkUp("Batangafo","Bossangoa","146.0")
  e.linkUp("Sibut","Bossangoa","244.0")
  e.linkUp("Sibut","Bangui","183.0")
  e.linkUp("Bangui","Bimbo","26.0")
  e.linkUp("Bimbo","Bossembele","159.0")
  e.linkUp("Bimbo","Mbaiki","92.0")
  e.linkUp("Bossembele","Bossangoa","148.0")
  e.linkUp("Bossembele","Yaloke","66.0")
  e.linkUp("Mbaiki","Katakpo","258.0")
  e.linkUp("Katakpo","Nola","52.0")
  e.linkUp("Katakpo","Banga","35.0")
  e.linkUp("Katakpo","Yaloke","219.0")
  e.linkUp("Yaloke","Bozoum","157.0")
  e.linkUp("Banga","Berberati","47.0")
  e.linkUp("Berberati","Baoro","186.0")
  e.linkUp("Baoro","Bouar","56.0")
  e.linkUp("Baoro","Bozoum","89.0")
  e.linkUp("Bozoum","Bossangoa","132.0")
  e.linkUp("Bozoum","Bouar","110.0")

  #Camps, starting at index locations[37] (at time of writing).
  e.linkUp("Batangafo","Kago","58.0")
  e.linkUp("Kago","Belom","89.0")
  e.linkUp("Yapara","Kago","56.0")
  e.linkUp("Ndele","Belom","298.0")
  e.linkUp("Bossangoa","Beboura III","151.0")
  e.linkUp("Bozoum","Beboura III","143.0")
  e.linkUp("Beboura III","Dosseye","118.0")
  e.linkUp("Bouar","Baboua","98.0")
  e.linkUp("Baboua","East","241.0")
  e.linkUp("Gamboula","East","135.0")
  e.linkUp("Nola","Gamboula","149.0")
  e.linkUp("Berberati","Gamboula","83.0")
  e.linkUp("Baboua","Adamaoua","311.0")
  e.linkUp("Bangassou","Monga","87.0")
  e.linkUp("Mobaye","Monga","205.0")
  e.linkUp("Monga","Mole","1814.0")
  e.linkUp("Bangui","Gbadolite","314.0")
  e.linkUp("Gbadolite","Inke",".0")
  e.linkUp("Gbadolite","Mobaye","146.0")


  d = handle_refugee_data.DataTable(csvformat="generic", data_directory="car2014", start_date="2013-12-01")

  list_of_cities = "Time"

  for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

  #print("Time,",list_of_cities)
  #print(list_of_cities)
  print("Time, Belom")

  conflict_zones = [locations[0]]
  conflict_weights = np.array([734350])

  for t in range(0,end_time):

    #Append conflict_zone and weight to list.
    if t==10: #Clashes between Seleka & Anti-Balaka, 100s of people died
      locations[0].movechance = 1.0

      conflict_zones += [locations[5]]
      conflict_weights = np.append(conflict_weights, [734350])

    elif t==31: #A wave of reprisal attacks & escalating cycle of violence
      locations[5].movechance = 1.0
      locations[8].movechance = 1.0
      locations[9].movechance = 1.0
      locations[11].movechance = 1.0

      conflict_zones += [locations[5], locations[8], locations[9], locations[11]]
      conflict_weights = np.append(conflict_weights, [38451,267859,22284,41486])


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

    #print(output_string)

    belom_data = d.get_field("Belom", t) - d.get_field("Belom", 0)
    dosseye_data = d.get_field("Dosseye", t) - d.get_field("Dosseye", 0)
    east_data = d.get_field("East", t) - d.get_field("East", 0)
    adamaoua_data = d.get_field("Adamaoua", t) - d.get_field("Adamaoua", 0)
    mole_data = d.get_field("Mole", t) - d.get_field("Mole", 0)
    inke_data = d.get_field("Inke", t) - d.get_field("Inke", 0)

    #print(belom_data, dosseye_data, east_data, adamaoua_data, mole_data, inke_data)

    print(t, locations[37].numAgents, belom_data, a.rel_error(locations[37].numAgents, belom_data))
    #print(t, locations[38].numAgents, dosseye_data, a.rel_error(locations[38].numAgents, dosseye_data))
    #print(t, locations[39].numAgents, east_data, a.rel_error(locations[39].numAgents, east_data))
    #print(t, locations[40].numAgents, adamaoua_data, a.rel_error(locations[40].numAgents, adamaoua_data))
    #print(t, locations[42].numAgents, mole_data, a.rel_error(locations[42].numAgents, mole_data))
    #print(t, locations[44].numAgents, inke_data, a.rel_error(locations[44].numAgents, inke_data))

    errors = [a.rel_error(l.numAgents,belom_data), a.rel_error(l.numAgents,dosseye_data), a.rel_error(l.numAgents,east_data), a.rel_error(l.numAgents,adamaoua_data), a.rel_error(l.numAgents,mole_data), a.rel_error(l.numAgents,inke_data)]

    #print("location: ", l.numAgents, ", data: ", belom_data, ", error: ", errors[0])
    #print("location: ", l.numAgents, ", data: ", dosseye_data, ", error: ", errors[1])
    #print("location: ", l.numAgents, ", data: ", east_data, ", error: ", errors[2])
    #print("location: ", l.numAgents, ", data: ", adamaoua_data, ", error: ", errors[3])
    #print("location: ", l.numAgents, ", data: ", mole_data, ", error: ", errors[4])
    #print("location: ", l.numAgents, ", data: ", inke_data, ", error: ", errors[5])


    #print("Cumulative error: ", np.sum(errors), "Squared error: ", np.sqrt(np.sum(np.power(errors,2))))

  if np.abs(np.sum(errors) - 0.495521376979) > 0.1:
    print("TEST FAILED.")
  if np.sqrt(np.sum(np.power(errors,2))) > 0.33+0.03:
    print("TEST FAILED.")
  else:
    print("TEST SUCCESSFUL.")


