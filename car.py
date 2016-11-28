import flee
import handle_refugee_data
import numpy as np
import analysis as a
import sys

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

#Central African Republic (CAR) Simulation

if __name__ == "__main__":


  if len(sys.argv)>1:
    end_time = int(sys.argv[1])
  else:
    end_time = 820

  RetroFitting = False
  if len(sys.argv)>2:
    if "-r" in sys.argv[2]:
      RetroFitting = True
      end_time *= 10

  e = flee.Ecosystem()

  locations = []

  #CAR
  locations.append(e.addLocation("Bangui", movechance=1.0))

  locations.append(e.addLocation("Bimbo", movechance=0.3))
  locations.append(e.addLocation("Mbaiki", movechance=0.3))
  locations.append(e.addLocation("Boda", movechance=0.3))
  locations.append(e.addLocation("Nola", movechance=0.3))
  locations.append(e.addLocation("Bossembele", movechance=0.3))
  locations.append(e.addLocation("Berberati", movechance=0.3))
  locations.append(e.addLocation("Gamboula", movechance=0.3))
  locations.append(e.addLocation("Carnot", movechance=0.3))
  locations.append(e.addLocation("Bouar", movechance=0.3))
  locations.append(e.addLocation("Baboua", movechance=0.3))
  locations.append(e.addLocation("Bozoum", movechance=0.3))
  locations.append(e.addLocation("Paoua", movechance=0.3))
  locations.append(e.addLocation("Bossangoa", movechance=0.3))
  locations.append(e.addLocation("RN1", movechance=0.3))
  locations.append(e.addLocation("Batangafo", movechance=0.3))
  locations.append(e.addLocation("Bouca", movechance=0.3))
  locations.append(e.addLocation("Kabo", movechance=0.3))
  locations.append(e.addLocation("Kaga Bandoro", movechance=0.3))
  locations.append(e.addLocation("Sibut", movechance=0.3))
  locations.append(e.addLocation("Dekoa", movechance=0.3))
  locations.append(e.addLocation("Ndele", movechance=0.3))
  locations.append(e.addLocation("Birao", movechance=0.3))
  locations.append(e.addLocation("Bria", movechance=0.3))
  locations.append(e.addLocation("Bambari", movechance=0.3))
  locations.append(e.addLocation("Grimari", movechance=0.3))
  locations.append(e.addLocation("Bangassou", movechance=0.3))
  locations.append(e.addLocation("Rafai", movechance=0.3))
  locations.append(e.addLocation("Obo", movechance=0.3))
  locations.append(e.addLocation("Mobaye", movechance=0.3))

  camp_movechance = 0.001

  #Chad, Cameroon & Demotratic R.of Congo & R. of Congo camps
  locations.append(e.addLocation("Belom", movechance=camp_movechance, capacity=28483, foreign=True))
  locations.append(e.addLocation("Dosseye", movechance=camp_movechance, capacity=22925, foreign=True))
  locations.append(e.addLocation("East", movechance=camp_movechance, capacity=180485, foreign=True))
  locations.append(e.addLocation("Adamaoua", movechance=camp_movechance, capacity=71506, foreign=True))
  locations.append(e.addLocation("Mole", movechance=camp_movechance, capacity=20454, foreign=True))
  locations.append(e.addLocation("Gbadolite", movechance=0.3))
  locations.append(e.addLocation("Inke", movechance=camp_movechance, capacity=20365, foreign=True))
  locations.append(e.addLocation("Betou", movechance=camp_movechance, capacity=10232, foreign=True))
  locations.append(e.addLocation("Brazaville", movechance=camp_movechance, capacity=8514, foreign=True))

  #Within CAR
  e.linkUp("Bangui","Bimbo","26.0")
  e.linkUp("Bimbo","Mbaiki","92.0")
  e.linkUp("Bangui","Boda","134.0")
  e.linkUp("Mbaiki","Boda","82.0")
  e.linkUp("Boda","Nola","221.0")
  e.linkUp("Boda","Bossembele","144.0")
  e.linkUp("Nola","Berberati","137.0")
  e.linkUp("Berberati","Gamboula","82.0")
  e.linkUp("Nola","Gamboula","148.0")
  e.linkUp("Berberati","Carnot","92.0")
  e.linkUp("Carnot","Bouar","140.0")
  e.linkUp("Bouar","Baboua","98.0")
  e.linkUp("Bouar","Bozoum","109.0")
  e.linkUp("Bozoum","Carnot","186.0")
  e.linkUp("Bozoum","Paoua","116.0")
  e.linkUp("Bozoum","Bossangoa","132.0")
  e.linkUp("Bossangoa","RN1","98.0")
  e.linkUp("Batangafo","RN1","154.0")
  e.linkUp("Paoua","RN1","82.0")
  e.linkUp("Bozoum","Bossembele","223.0")
  e.linkUp("Bossangoa","Bossembele","148.0")
  e.linkUp("Bossembele","Bangui","159.0")
  e.linkUp("Bossangoa","Bouca","98.0")
  e.linkUp("Bossangoa","Batangafo","147.0")
  e.linkUp("Bouca","Batangafo","84.0")
  e.linkUp("Batangafo","Kabo","60.0")
  e.linkUp("Kabo","Kaga Bandoro","107.0")
  e.linkUp("Batangafo","Kaga Bandoro","113.0")
  e.linkUp("Bangui","Sibut","183.0")
  e.linkUp("Bouca","Sibut","147.0")
  e.linkUp("Sibut","Dekoa","69.0")
  e.linkUp("Dekoa","Kaga Bandoro","80.0")
  e.linkUp("Kaga Bandoro","Ndele","324.0")
  e.linkUp("Ndele","Birao","352.0")
  e.linkUp("Birao","Bria","480.0")
  e.linkUp("Ndele","Bria","314.0")
  e.linkUp("Bria","Bambari","202.0")
  e.linkUp("Bambari","Grimari","77.0")
  e.linkUp("Grimari","Dekoa","136.0")
  e.linkUp("Grimari","Sibut","115.0")
  e.linkUp("Bria","Bangassou","282.0")
  e.linkUp("Bangassou","Rafai","132.0")
  e.linkUp("Bria","Rafai","333.0")
  e.linkUp("Rafai","Obo","349.0")
  e.linkUp("Bangassou","Mobaye","224.0")
  e.linkUp("Mobaye","Bambari","213.0")
  e.linkUp("Mobaye","Gbadolite","146.0")
  e.linkUp("Gbadolite","Bangui","500.0")


  #Camps, starting at index locations[30] (at time of writing).
  e.linkUp("Kabo","Belom","87.0")
  e.linkUp("Ndele","Belom","299.0")
  e.linkUp("Paoua","Dosseye","136.0")
  e.linkUp("RN1","Dosseye","108.0")
  e.linkUp("Gamboula","East","135.0")		
  e.linkUp("Baboua","East","241.0")
  e.linkUp("Baboua","Adamaoua","311.0")		
  e.linkUp("Bangui","Mole","42.0")
  e.linkUp("Gbadolite","Inke","42.0")
  e.linkUp("Mbaiki","Betou","148.0")
  e.linkUp("Nola","Brazaville","1300.0")


  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory="car2014", start_date="2013-12-01")

  # Correcting for overestimations due to inaccurate level 1 registrations in five of the camps.
  # These errors led to a perceived large drop in refugee population in all of these camps.
  # We correct by linearly scaling the values down to make the last level 1 registration match the first level 2 registration value.
  # To our knowledge, all level 2 registration procedures were put in place by the end of 2016.
  d.correctLevel1Registrations("Belom","2014-04-15")
  d.correctLevel1Registrations("Dosseye","2015-01-01")
  d.correctLevel1Registrations("East","2014-09-28")
  d.correctLevel1Registrations("Adamaoua","2014-10-19")
  d.correctLevel1Registrations("Mole","2016-02-29")
  d.correctLevel1Registrations("Inke","2014-06-30")
  d.correctLevel1Registrations("Betou","2014-03-22")
  d.correctLevel1Registrations("Brazaville","2016-04-30")

  last_physical_day = int(sys.argv[1])

  locations[30].capacity = d.getMaxFromData("Belom", last_physical_day)
  locations[31].capacity = d.getMaxFromData("Dosseye", last_physical_day)
  locations[32].capacity = d.getMaxFromData("East", last_physical_day)
  locations[33].capacity = d.getMaxFromData("Adamaoua", last_physical_day)
  locations[34].capacity = d.getMaxFromData("Mole", last_physical_day)
  locations[36].capacity = d.getMaxFromData("Inke", last_physical_day)
  locations[37].capacity = d.getMaxFromData("Betou", last_physical_day)
  locations[38].capacity = d.getMaxFromData("Brazaville", last_physical_day)

  list_of_cities = "Time"

  for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

  #print(list_of_cities)
  #print("Time, campname")
  print("Day,Belom sim,Belom data,Belom error,Dosseye sim,Dosseye data,Dosseye error,East sim,East data,East error,Adamaoua sim,Adamaoua data,Adamaoua error,Mole sim,Mole data,Mole error,Inke sim,Inke data,Inke error,Betou sim,Betou data,Betou error,Brazaville sim,Brazaville data,Brazaville error,Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,retrofitted time,refugees in camps (simulation),refugee_debt,Total error (retrofitted)")


  #Set up a mechanism to incorporate temporary decreases in refugees
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only

  #Bangui is in conflict area. All refugees want to leave this place.
  locations[0].movechance = 1.0

  conflict_zones = [locations[0]]
  conflict_weights = np.array([734350])

  # Start with a refugee debt to account for the mismatch between camp aggregates and total UNHCR data.
  refugee_debt = e.numAgents()


  t_retrofitted = 0

  for t in range(0,end_time):

    e.refresh_conflict_weights()

    if RetroFitting==False:
      t_data = t
    else:
      t_data = int(t_retrofitted)
      if t_data > end_time / 10:
        break


    # Determine number of new refugees to insert into the system.
    new_refs = d.get_daily_difference(t, FullInterpolation=True, ZeroOnDayZero=False) - refugee_debt
    refugees_raw += d.get_daily_difference(t, FullInterpolation=True, ZeroOnDayZero=False)
    if new_refs < 0:
      refugee_debt = -new_refs
      new_refs = 0
    elif refugee_debt > 0:
      refugee_debt = 0

    new_links = []
    # Close borders here: On the 12th of May, Chad closes border altogether.
    #if t_data == 163:
      #e.remove_link("Kago","Belom")
      #e.remove_link("Ndele","Belom")
      #e.remove_link("Beboura III","Dosseye")


    #Append conflict_zones and weights to list from ACLED conflict database.
    if t_data == 5: #A wave of reprisal attacks & escalating cycle of violence between Seleka militia and Anti-Balaka
      locations[11].movechance = 1.0

      conflict_zones += [locations[11]]
      conflict_weights = np.append(conflict_weights, [22284])

    elif t_data == 20: #MISCA: African-led International Support Mission against Anti-balaka (deaths & thousnads displaced)
      locations[13].movechance = 1.0

      conflict_zones += [locations[13]]
      conflict_weights = np.append(conflict_weights, [38451])

    elif t_data == 31: #Violence & death in battles between Seleka militia and Anti-Balaka
      locations[1].movechance = 1.0

      conflict_zones += [locations[1]]
      conflict_weights = np.append(conflict_weights, [267859])

    elif t_data == 50: #Violence & battles of Seleka militia with Anti-Balaka
      locations[24].movechance = 1.0
      locations[9].movechance = 1.0

      conflict_zones += [locations[24], locations[9]]
      conflict_weights = np.append(conflict_weights, [41486,39205])

    elif t_data == 58: #Battles between Seleka militia and Anti-Balaka
      locations[3].movechance = 1.0

      conflict_zones += [locations[3]]
      conflict_weights = np.append(conflict_weights, [11688])

    elif t_data == 67: #Battles between Seleka militia and Anti-Balaka
      locations[18].movechance = 1.0

      conflict_zones += [locations[18]]
      conflict_weights = np.append(conflict_weights, [27797])

    elif t_data == 72: ##Battles between Military forces and Anti-Balaka
      locations[6].movechance = 1.0

      conflict_zones += [locations[6]]
      conflict_weights = np.append(conflict_weights, [105155])

    elif t_data == 77: #Battles between Seleka militia and Salanze Communal Militia
      locations[26].movechance = 1.0

      conflict_zones += [locations[26]]
      conflict_weights = np.append(conflict_weights, [35305])

    elif t_data == 97: #Battles between Seleka militia and Sangaris (French Mission)
      locations[21].movechance = 1.0

      conflict_zones += [locations[21]]
      conflict_weights = np.append(conflict_weights, [13704])

    elif t_data == 100: #MISCA: African-led International Support Mission against Anti-balaka
      locations[4].movechance = 1.0

      conflict_zones += [locations[4]]
      conflict_weights = np.append(conflict_weights, [41462])

    elif t_data == 128: #Battles between Seleka militia and Anti-Balaka
      locations[20].movechance = 1.0

      conflict_zones += [locations[20]]
      conflict_weights = np.append(conflict_weights, [12447])

    elif t_data == 130: #Battles of Bria Communal Militia (Seleka Militia) and MISCA (African-led International Support Mission)
      locations[23].movechance = 1.0

      conflict_zones += [locations[23]]
      conflict_weights = np.append(conflict_weights, [43322])

    elif t_data == 134: #Battles between Anti-Balaka and Seleka militia
      locations[25].movechance = 1.0

      conflict_zones += [locations[25]]
      conflict_weights = np.append(conflict_weights, [10822])

    elif t_data == 143: #Battles between Seleka militia and Anti-Balaka
      locations[16].movechance = 1.0

      conflict_zones += [locations[16]]
      conflict_weights = np.append(conflict_weights, [12280])

    elif t_data == 146: #Battles by unidentified Armed groups 
      locations[12].movechance = 1.0

      conflict_zones += [locations[12]]
      conflict_weights = np.append(conflict_weights, [17370])

    elif t_data == 173: #MISCA: African-led International Support Mission against Anti-balaka
      locations[8].movechance = 1.0

      conflict_zones += [locations[8]]
      conflict_weights = np.append(conflict_weights, [54551])

    elif t_data == 241: #Battles between Anti-Balaka and Seleka militia
      locations[15].movechance = 1.0

      conflict_zones += [locations[15]]
      conflict_weights = np.append(conflict_weights, [16420])

    elif t_data == 313: #MINUSCA: United Nations Multidimensional Integrated Stabilization Mission against Seleka militia (PRGF Faction)
      locations[19].movechance = 1.0

      conflict_zones += [locations[19]]
      conflict_weights = np.append(conflict_weights, [24527])


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

    #Calculation of error terms
    errors = []
    abs_errors = []
    loc_data = [belom_data, dosseye_data, east_data, adamaoua_data, mole_data, inke_data, betou_data, brazaville_data]
    camp_locations = [30, 31, 32, 33, 34, 36, 37, 38]

    camps = []
    for i in camp_locations:
      camps += [locations[i]]
    camp_names = ["Belom", "Dosseye", "East", "Adamaoua", "Mole", "Inke", "Betou", "Brazaville"]

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

    output = "%s" % t

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




