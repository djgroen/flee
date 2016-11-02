import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

#Central African Republic (CAR) Simulation

if __name__ == "__main__":

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
  locations.append(e.addLocation("Ippy", movechance=0.3))
  locations.append(e.addLocation("Mbres", movechance=0.3))
  locations.append(e.addLocation("Bossembele", movechance=0.3))
  locations.append(e.addLocation("Yaloke", movechance=0.3))
  locations.append(e.addLocation("Katakpo", movechance=0.3))
  locations.append(e.addLocation("Banga", movechance=0.3))
  locations.append(e.addLocation("Kago", movechance=0.3))
  locations.append(e.addLocation("Yapara", movechance=0.3))
  locations.append(e.addLocation("Beboura III", movechance=0.3))
  locations.append(e.addLocation("Gamboula", movechance=0.3))
  locations.append(e.addLocation("Baboua", movechance=0.3))

  #Chad, Cameroon & Demotratic R.of Congo & R. of Congo camps
  locations.append(e.addLocation("Belom", movechance=0.001, capacity=28483, foreign=True))
  locations.append(e.addLocation("Dosseye", movechance=0.001, capacity=22925, foreign=True))
  locations.append(e.addLocation("East", movechance=0.001, capacity=180485, foreign=True))
  locations.append(e.addLocation("Adamaoua", movechance=0.001, capacity=71506, foreign=True))
  locations.append(e.addLocation("Mole", movechance=0.001, capacity=20454, foreign=True))
  locations.append(e.addLocation("Gbadolite", movechance=0.3))
  locations.append(e.addLocation("Inke", movechance=0.001, capacity=20365, foreign=True))
  locations.append(e.addLocation("Betou", movechance=0.001, capacity=10232, foreign=True))
  locations.append(e.addLocation("Brazaville", movechance=0.001, capacity=8514, foreign=True))

  #Within CAR
  e.linkUp("Mobaye","Melego","67.0")
  e.linkUp("Melego","Bangassou","191.0")
  e.linkUp("Bangassou","Rafai","132.0")
  e.linkUp("Rafai","Obo","349.0")
  e.linkUp("Rafai","Ippy","394.0")
  e.linkUp("Melego","Bambari","153.0")
  e.linkUp("Bria","Ippy","96.0")
  e.linkUp("Ippy","Bambari","106.0")
  e.linkUp("Bambari","Bakala","168.0")
  e.linkUp("Ippy","Mbres","158.0")
  e.linkUp("Bambari","Sibut","191.0")
  e.linkUp("Sibut","Kaga Bandoro","148.0")
  e.linkUp("Mbres","Kaga Bandoro","91.0")
  e.linkUp("Mbres","Ndele","233.0")
  e.linkUp("Ndele","Birao","353.0")
  e.linkUp("Ndele","Bria","315.0")
  e.linkUp("Kaga Bandoro","Bossangoa","259.0")
  e.linkUp("Sibut","Bossangoa","244.0")
  e.linkUp("Sibut","Bangui","183.0")
  e.linkUp("Bangui","Bimbo","26.0")
  e.linkUp("Bangui","Bossembele","158.0")
  e.linkUp("Bossembele","Bossangoa","148.0")
  e.linkUp("Bimbo","Mbaiki","92.0")
  e.linkUp("Bossembele","Yaloke","66.0")
  e.linkUp("Yaloke","Bozoum","157.0")
  e.linkUp("Yaloke","Katakpo","219.0")
  e.linkUp("Mbaiki","Katakpo","258.0")
  e.linkUp("Katakpo","Nola","52.0")
  e.linkUp("Katakpo","Banga","35.0")
  e.linkUp("Banga","Berberati","47.0")
  e.linkUp("Berberati","Baoro","186.0")
  e.linkUp("Baoro","Bouar","56.0")
  e.linkUp("Baoro","Bozoum","89.0")
  e.linkUp("Bozoum","Bossangoa","132.0")
  e.linkUp("Bozoum","Bouar","110.0")

  #Camps, starting at index locations[30] (at time of writing).
  e.linkUp("Kaga Bandoro","Yapara","49.0")
  e.linkUp("Yapara","Kago","56.0")
  e.linkUp("Bossangoa","Kago","205.0")
  e.linkUp("Kago","Belom","89.0")
  e.linkUp("Ndele","Belom","298.0")
  e.linkUp("Bossangoa","Beboura III","151.0")
  e.linkUp("Bozoum","Beboura III","143.0")
  e.linkUp("Beboura III","Dosseye","118.0")
  e.linkUp("Nola","Gamboula","149.0")
  e.linkUp("Berberati","Gamboula","83.0")
  e.linkUp("Gamboula","East","135.0")
  e.linkUp("Bouar","Baboua","98.0")
  e.linkUp("Baboua","East","241.0")
  e.linkUp("Baboua","Adamaoua","311.0")
  e.linkUp("Bangui","Mole","42.0")
  e.linkUp("Mobaye","Gbadolite","146.0")
  e.linkUp("Gbadolite","Inke","23.0")
  e.linkUp("Mbaiki","Betou","148.0")
  e.linkUp("Nola","Brazaville","1300.0")

  d = handle_refugee_data.DataTable(csvformat="generic", data_directory="car2014", start_date="2013-12-01")

  list_of_cities = "Time"

  for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

  #print(list_of_cities)
  #print("Time, campname")
  print("Day,Belom sim,Belom data,Belom error,Dosseye sim,Dosseye data,Dosseye error,East sim,East data,East error,Adamaoua sim,Adamaoua data,Adamaoua error,Mole sim,Mole data,Mole error,Inke sim,Inke data,Inke error,Betou sim,Betou data,Betou error,Brazaville sim,Brazaville data,Brazaville error,Total error,refugees in camps (UNHCR),refugees in camps (simulation),raw UNHCR refugee count")


  #Bangui is in conflict area. All refugees want to leave this place.
  locations[0].movechance = 1.0

  #Set up a mechanism to incorporate temporary decreases in refugees
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only


  conflict_zones = [locations[0]]
  conflict_weights = np.array([734350])

  for t in range(0,end_time):

    #Append conflict_zone and weight to list.
    if t==31: #A wave of reprisal attacks & escalating cycle of violence
      locations[4].movechance = 1.0
      locations[5].movechance = 1.0
      locations[8].movechance = 1.0
      locations[9].movechance = 1.0
      locations[11].movechance = 1.0

      conflict_zones += [locations[4], locations[5], locations[8], locations[9], locations[11]]
      conflict_weights = np.append(conflict_weights, [233666,369220,356725,430506,276710])

    elif t==627: #Fighting between ex-Seleka & Anti-balaka (deaths & thousnads displaced)
      locations[11].movechance = 1.0

      conflict_zones += [locations[11]]
      conflict_weights = np.append(conflict_weights, [276710])

    elif t==742: #Violence & death during the constitutional referendum vote
      locations[12].movechance = 1.0

      conflict_zones += [locations[12]]
      conflict_weights = np.append(conflict_weights, [90316])



    #new_refs = d.get_new_refugees(t)
    new_refs = d.get_new_refugees(t, FullInterpolation=True) - refugee_debt
    refugees_raw += d.get_new_refugees(t, FullInterpolation=False)
    if new_refs < 0:
      refugee_debt = -new_refs
      new_refs = 0


    #Insert refugee agents
    for i in range(0, new_refs):
      e.addAgent(np.random.choice(conflict_zones, p=conflict_weights/sum(conflict_weights)))

    #Propagate the model by one time step.
    e.evolve()

    #e.printInfo()


    #Validation/data comparison
    belom_data = d.get_field("Belom", t) #- d.get_field("Belom", 0)
    dosseye_data = d.get_field("Dosseye", t) #- d.get_field("Dosseye", 0)
    east_data = d.get_field("East", t) #- d.get_field("East", 0)
    adamaoua_data = d.get_field("Adamaoua", t) #- d.get_field("Adamaoua", 0)
    mole_data = d.get_field("Mole", t) #- d.get_field("Mole", 0)
    inke_data = d.get_field("Inke", t) #- d.get_field("Inke", 0)
    betou_data = d.get_field("Betou", t) #- d.get_field("Betou", 0)
    brazaville_data = d.get_field("Brazaville", t) #- d.get_field("Brazaville", 0)


    errors = []
    abs_errors = []
    loc_data = [belom_data, dosseye_data, east_data, adamaoua_data, mole_data, inke_data, betou_data, brazaville_data]
    camp_locations = [30, 31, 32, 33, 34, 36, 37, 38]

    for i in range(0,len(camp_locations)):
      camp_number = camp_locations[i]
      errors += [a.rel_error(locations[camp_number].numAgents, loc_data[i])]
      abs_errors += [a.abs_error(locations[camp_number].numAgents, loc_data[i])]

    output_string = "%s" % t

    for i in range(0,len(errors)):
      camp_number = camp_locations[i]
      output_string += ",%s,%s,%s" % (locations[camp_number].numAgents, loc_data[i], errors[i])


    if e.numAgents()>0:
      output_string += ",%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(sum(loc_data)), int(sum(loc_data)), e.numAgents(), refugees_raw)
    else:
      output_string += ",0"


    print(output_string)




    #print(belom_data, dosseye_data, east_data, adamaoua_data, mole_data, inke_data, betou_data, brazaville_data)

    #print(t, locations[30].numAgents, belom_data, a.rel_error(locations[30].numAgents, belom_data))
    #print(t, locations[31].numAgents, dosseye_data, a.rel_error(locations[31].numAgents, dosseye_data))
    #print(t, locations[32].numAgents, east_data, a.rel_error(locations[32].numAgents, east_data))
    #print(t, locations[33].numAgents, adamaoua_data, a.rel_error(locations[33].numAgents, adamaoua_data))
    #print(t, locations[34].numAgents, mole_data, a.rel_error(locations[34].numAgents, mole_data))
    #print(t, locations[36].numAgents, inke_data, a.rel_error(locations[36].numAgents, inke_data))
    #print(t, locations[37].numAgents, betou_data, a.rel_error(locations[37].numAgents, betou_data))
    #print(t, locations[38].numAgents, brazaville_data, a.rel_error(locations[38].numAgents, brazaville_data))


    #print("location: ", l.numAgents, ", data: ", belom_data, ", error: ", errors[0])
    #print("location: ", l.numAgents, ", data: ", dosseye_data, ", error: ", errors[1])
    #print("location: ", l.numAgents, ", data: ", east_data, ", error: ", errors[2])
    #print("location: ", l.numAgents, ", data: ", adamaoua_data, ", error: ", errors[3])
    #print("location: ", l.numAgents, ", data: ", mole_data, ", error: ", errors[4])
    #print("location: ", l.numAgents, ", data: ", inke_data, ", error: ", errors[5])
    #print("location: ", l.numAgents, ", data: ", inke_data, ", error: ", errors[5])
    #print("location: ", l.numAgents, ", data: ", inke_data, ", error: ", errors[5])

    #print("Cumulative error: ", np.sum(errors), "Squared error: ", np.sqrt(np.sum(np.power(errors,2))))

    """
    if np.abs(np.sum(errors) - 0.495521376979) > 0.1:
      print("TEST FAILED.")
    if np.sqrt(np.sum(np.power(errors,2))) > 0.33+0.03:
      print("TEST FAILED.")
    else:
      print("TEST SUCCESSFUL.")
    """
