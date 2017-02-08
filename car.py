import flee
import handle_refugee_data
import numpy as np
import analysis as a
import sys

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

#Central African Republic (CAR) Simulation

def date_to_sim_days(date):
  return handle_refugee_data.subtract_dates(date,"2013-12-01")

if __name__ == "__main__":

  if len(sys.argv)>1:
    end_time = int(sys.argv[1])
    last_physical_day = int(sys.argv[1])
  else:
    end_time = 820
    last_physical_day = 820

  RetroFitting = False
  if len(sys.argv)>2:
    if "-r" in sys.argv[2]:
      RetroFitting = True
      end_time *= 10

  e = flee.Ecosystem()

  locations = []

  #CAR
  locations.append(e.addLocation("Bangui", movechance=0.3, pop=734350-400000)) #Subtracting the number of IDPs from the population to reflect local shelter.
  locations.append(e.addLocation("Bimbo", movechance=0.3, pop=267859))
  locations.append(e.addLocation("Mbaiki", movechance=0.3))
  locations.append(e.addLocation("Boda", movechance=0.3, pop=11688))
  locations.append(e.addLocation("Nola", movechance=0.3, pop=41462))

  locations.append(e.addLocation("Bossembele", movechance=0.3, pop=37849))
  locations.append(e.addLocation("Berberati", movechance=0.3, pop=105155))
  locations.append(e.addLocation("Gamboula", movechance=0.3))
  locations.append(e.addLocation("Carnot", movechance=0.3, pop=54551))
  locations.append(e.addLocation("Bouar", movechance=0.3, pop=39205))

  locations.append(e.addLocation("Baboua", movechance=0.3))
  locations.append(e.addLocation("Bozoum", movechance=0.3, pop=22284))
  locations.append(e.addLocation("Paoua", movechance=0.3, pop=17370))
  locations.append(e.addLocation("Bossangoa", movechance=0.3, pop=38451))
  locations.append(e.addLocation("RN1", movechance=1.0)) #non-city junction, Coordinates = 7.112110, 17.030220

  locations.append(e.addLocation("Batangafo", movechance=0.3, pop=16420))
  locations.append(e.addLocation("Bouca", movechance=0.3, pop=12280))
  locations.append(e.addLocation("Kabo", movechance=0.3))
  locations.append(e.addLocation("Kaga Bandoro", movechance=0.3, pop=27797))
  locations.append(e.addLocation("Sibut", movechance=0.3, pop=24527))

  locations.append(e.addLocation("Bamingui", movechance=0.3, pop=6230))
  locations.append(e.addLocation("Dekoa", movechance=0.3, pop=12447))
  locations.append(e.addLocation("Ndele", movechance=0.3, pop=13704))
  locations.append(e.addLocation("Birao", movechance=0.3))
  locations.append(e.addLocation("Bria", movechance=0.3, pop=43322))

  locations.append(e.addLocation("Bambari", movechance=0.3, pop=41486))
  locations.append(e.addLocation("Grimari", movechance=0.3, pop=10822))
  locations.append(e.addLocation("Bangassou", movechance=0.3, pop=35305))
  locations.append(e.addLocation("Rafai", movechance=0.3, pop=13962))
  locations.append(e.addLocation("Obo", movechance=0.3, pop=36029))

  locations.append(e.addLocation("Mobaye", movechance=0.3))
  locations.append(e.addLocation("Bohong", movechance=0.3, pop=19700))
  locations.append(e.addLocation("Mbres", movechance=0.3, pop=20709))
  locations.append(e.addLocation("Damara", movechance=0.3, pop=32321))
  locations.append(e.addLocation("Bogangolo", movechance=0.3, pop=9966))

  locations.append(e.addLocation("Marali", movechance=0.3))
  locations.append(e.addLocation("Beboura", movechance=0.3))
  locations.append(e.addLocation("RN8", movechance=1.0)) #non-city junction, Coordinates = 9.560670, 22.140450
  locations.append(e.addLocation("Zemio", movechance=0.3))

  camp_movechance = 0.001

  #Chad, Cameroon & Demotratic R.of Congo & R. of Congo camps starting at index locations[39] (at time of writing).
  locations.append(e.addLocation("Amboko", movechance=camp_movechance, capacity=12405, foreign=True))
  locations.append(e.addLocation("Belom", movechance=camp_movechance, capacity=28483, foreign=True))

  locations.append(e.addLocation("Dosseye", movechance=camp_movechance, capacity=22925, foreign=True))
  locations.append(e.addLocation("Gondje", movechance=camp_movechance, capacity=12171, foreign=True))
  locations.append(e.addLocation("Moyo", movechance=camp_movechance, capacity=14969, foreign=True))
  locations.append(e.addLocation("Lolo", movechance=1.0, foreign=True)) #forwarding location (to aggreg. camp)
  locations.append(e.addLocation("Mbile", movechance=1.0, foreign=True)) #forwarding location (to aggreg. camp)

  locations.append(e.addLocation("Batouri", movechance=0.3)) #city on junction point
  locations.append(e.addLocation("Timangolo", movechance=1.0, foreign=True)) #forwarding location (to aggreg. camp)
  locations.append(e.addLocation("Gado-Badzere", movechance=1.0, foreign=True)) #forwarding location (to aggreg. camp)
  locations.append(e.addLocation("East", movechance=camp_movechance, capacity=180485, foreign=True)) #regional camp.
  locations.append(e.addLocation("D22", movechance=1.0)) #non-city junction, Coordinates = 6.559910, 14.126600

  locations.append(e.addLocation("Borgop", movechance=1.0, foreign=True)) #forwarding location (to aggreg. camp)
  locations.append(e.addLocation("Ngam", movechance=1.0, foreign=True)) #forwarding location (to aggreg. camp)
  locations.append(e.addLocation("Adamaoua", movechance=camp_movechance, capacity=71506, foreign=True))
  locations.append(e.addLocation("Mole", movechance=camp_movechance, capacity=20454, foreign=True))
  locations.append(e.addLocation("Gbadolite", movechance=0.3)) #city on junction point

  locations.append(e.addLocation("N24", movechance=1.0)) #non-city junction, Coordinates = 3.610560, 20.762290
  locations.append(e.addLocation("Bili", movechance=camp_movechance, capacity=10282, foreign=True))
  locations.append(e.addLocation("Bossobolo", movechance=camp_movechance, capacity=18054, foreign=True))
  locations.append(e.addLocation("Boyabu", movechance=camp_movechance, capacity=20393, foreign=True))
  locations.append(e.addLocation("Mboti", movechance=camp_movechance, capacity=704, foreign=True))

  locations.append(e.addLocation("Inke", movechance=camp_movechance, capacity=20365, foreign=True))
  locations.append(e.addLocation("Betou", movechance=camp_movechance, capacity=10232, foreign=True))
  locations.append(e.addLocation("Brazaville", movechance=camp_movechance, capacity=7221, foreign=True))

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
  e.linkUp("Bouar","Bohong","72.0")
  e.linkUp("Bohong","Bozoum","101.0")
  e.linkUp("Bouar","Bozoum","109.0")
  e.linkUp("Bozoum","Carnot","186.0")
  e.linkUp("Bozoum","Paoua","116.0")
  e.linkUp("Bozoum","Bossangoa","132.0")
  e.linkUp("Bossangoa","RN1","98.0")
  e.linkUp("Batangafo","RN1","154.0")
  e.linkUp("Beboura","RN1","54.0")
  e.linkUp("Bozoum","Bossembele","223.0")
  e.linkUp("Bossangoa","Bossembele","148.0")
  e.linkUp("Bossembele","Bogangolo","132.0")
  e.linkUp("Bossembele","Bangui","159.0")
  e.linkUp("Bossangoa","Bouca","98.0")
  e.linkUp("Bossangoa","Batangafo","147.0")
  e.linkUp("Bouca","Batangafo","84.0")
  e.linkUp("Batangafo","Kabo","60.0")
  e.linkUp("Kabo","Kaga Bandoro","107.0")
  e.linkUp("Batangafo","Kaga Bandoro","113.0")
  e.linkUp("Damara","Bogangolo","93.0")
  e.linkUp("Bangui","Damara","74.0")
  e.linkUp("Damara","Sibut","105.0")
  e.linkUp("Sibut","Bogangolo","127.0")
  e.linkUp("Bogangolo","Marali","55.0")
  e.linkUp("Marali","Bouca","58.0")
  e.linkUp("Marali","Sibut","89.0")
  e.linkUp("Sibut","Dekoa","69.0")
  e.linkUp("Dekoa","Kaga Bandoro","80.0")
  e.linkUp("Kaga Bandoro","Mbres","91.0")
  e.linkUp("Mbres","Bamingui","112.0")
  e.linkUp("Bamingui","Ndele","121.0")
  e.linkUp("Ndele","RN8","239.0")
  e.linkUp("RN8","Birao","114.0")
  e.linkUp("Birao","Bria","480.0")
  e.linkUp("Ndele","Bria","314.0")
  e.linkUp("Bria","Bambari","202.0")
  e.linkUp("Bambari","Grimari","77.0")
  e.linkUp("Grimari","Dekoa","136.0")
  e.linkUp("Grimari","Sibut","115.0")
  e.linkUp("Bria","Bangassou","282.0")
  e.linkUp("Bangassou","Rafai","132.0")
  e.linkUp("Bria","Rafai","333.0")
  e.linkUp("Rafai","Zemio","148.0")
  e.linkUp("Zemio","Obo","199.0")
  e.linkUp("Bangassou","Mobaye","224.0")
  e.linkUp("Mobaye","Bambari","213.0")
  e.linkUp("Mobaye","Gbadolite","146.0")
  e.linkUp("Gbadolite","Bangui","500.0")


  #Camps, starting at index locations[38] (at time of writing).
  e.linkUp("Kabo","Belom","87.0")
  e.linkUp("Ndele","Belom","299.0")
  e.linkUp("Paoua","Beboura","31.0")
  e.linkUp("Beboura","Amboko","76.0")
  e.linkUp("Amboko","Gondje","8.0")
  e.linkUp("Amboko","Dosseye","31.0")
  e.linkUp("RN1","Dosseye","108.0")
  e.linkUp("RN8","Moyo","176.0")
  e.linkUp("Gamboula","Lolo","41.0")
  e.linkUp("Lolo","Mbile","10.0")
  e.linkUp("Mbile","Batouri","53.0")
  e.linkUp("Batouri","East","26.0")
  e.linkUp("Batouri","Timangolo","24.0")
  e.linkUp("Baboua","Gado-Badzere","81.0")
  e.linkUp("Gado-Badzere","East","222.0")
  e.linkUp("Baboua","D22","181.0")
  e.linkUp("D22","Ngam","68.0")
  e.linkUp("Borgop","Ngam","41.0")
  e.linkUp("D22","Adamaoua","138.0")
  e.linkUp("Gbadolite","N24","93.0")
  e.linkUp("N24","Bili","20.0") #There is no road after 93km to the camp & the remaining 20km was found by distance calculator (www.movable-type.co.uk/scripts/latlong.html)
  e.linkUp("N24","Bossobolo","23.0")
  e.linkUp("Bangui","Mole","42.0")
  e.linkUp("Mole","Boyabu","25.0")
  e.linkUp("Zemio","Mboti","174.0")
  e.linkUp("Mobaye","Mboti","662.0")
  e.linkUp("Gbadolite","Inke","42.0")
  e.linkUp("Mbaiki","Betou","148.0")
  e.linkUp("Nola","Brazaville","1300.0")


  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory="car2014/", start_date="2013-12-01")

  #Correcting for overestimations due to inaccurate level 1 registrations in five of the camps.
  #These errors led to a perceived large drop in refugee population in all of these camps.
  #We correct by linearly scaling the values down to make the last level 1 registration match the first level 2 registration value.
  #To our knowledge, all level 2 registration procedures were put in place by the end of 2016.
  d.correctLevel1Registrations("Amboko","2015-09-30")
  d.correctLevel1Registrations("Belom","2015-08-31")
  d.correctLevel1Registrations("Dosseye","2015-01-01")
  d.correctLevel1Registrations("Gondje","2015-09-30")
  d.correctLevel1Registrations("Moyo","2015-06-02") #and also "2014-05-11"
  d.correctLevel1Registrations("East","2014-09-28")
  d.correctLevel1Registrations("Adamaoua","2014-10-19")
  d.correctLevel1Registrations("Mole","2016-02-29")
  d.correctLevel1Registrations("Bili","2016-06-30")
  #d.correctLevel1Registrations("Bossobolo","2016-05-20") #Data is only decreasing over time, so no grounds for a level1 corr.
  d.correctLevel1Registrations("Boyabu","2016-06-30")
  d.correctLevel1Registrations("Inke","2014-06-30")
  d.correctLevel1Registrations("Betou","2014-03-22")
  #d.correctLevel1Registrations("Brazaville","2016-04-30")

  locations[39].capacity = d.getMaxFromData("Amboko", last_physical_day)
  locations[40].capacity = d.getMaxFromData("Belom", last_physical_day)
  locations[41].capacity = d.getMaxFromData("Dosseye", last_physical_day)
  locations[42].capacity = d.getMaxFromData("Gondje", last_physical_day)
  locations[43].capacity = d.getMaxFromData("Moyo", last_physical_day)
  locations[49].capacity = d.getMaxFromData("East", last_physical_day)
  locations[53].capacity = d.getMaxFromData("Adamaoua", last_physical_day)
  locations[54].capacity = d.getMaxFromData("Mole", last_physical_day)
  locations[57].capacity = d.getMaxFromData("Bili", last_physical_day)
  locations[58].capacity = d.getMaxFromData("Bossobolo", last_physical_day)
  locations[59].capacity = d.getMaxFromData("Boyabu", last_physical_day)
  locations[60].capacity = d.getMaxFromData("Mboti", last_physical_day)
  locations[61].capacity = d.getMaxFromData("Inke", last_physical_day)
  locations[62].capacity = d.getMaxFromData("Betou", last_physical_day)
  locations[63].capacity = d.getMaxFromData("Brazaville", last_physical_day)



  list_of_cities = "Time"

  for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

  #print(list_of_cities)
  #print("Time, campname")
  print("Day,Amboko sim,Amboko data,Amboko error,Belom sim,Belom data,Belom error,Dosseye sim,Dosseye data,Dosseye error,Gondje sim,Gondje data,Gondje error,Moyo sim,Moyo data,Moyo error,East sim,East data,East error,Adamaoua sim,Adamaoua data,Adamaoua error,Bili sim,Bili data,Bili error,Bossobolo sim,Bossobolo data,Bossobolo error,Mole sim,Mole data,Mole error,Boyabu sim, Boyabu data,Boyabu error,Mboti sim,Mboti data,Mboti error,Inke sim,Inke data,Inke error,Betou sim,Betou data,Betou error,Brazaville sim,Brazaville data,Brazaville error,Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,retrofitted time,refugees in camps (simulation),refugee_debt,Total error (retrofitted)")


  #Set up a mechanism to incorporate temporary decreases in refugees
  refugee_debt = 0
  refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only

  #Append conflict_zones and weights to list from ACLED conflict database.
  #Conflict zones year before the start of simulation period
  #if t_data == date_to_sim_days("2012-12-10"):
  e.add_conflict_zone("Ndele")
  #if t_data == date_to_sim_days("2012-12-15"):
  e.add_conflict_zone("Bamingui")
  #if t_data == date_to_sim_days("2012-12-28"):
  e.add_conflict_zone("Bambari")
  #if t_data == date_to_sim_days("2013-01-18"):
  e.add_conflict_zone("Obo")
  #if t_data == date_to_sim_days("2013-03-11"):
  e.add_conflict_zone("Bangassou")
  #if t_data == date_to_sim_days("2013-03-24"):
  e.add_conflict_zone("Bangui") # Main capital entry. Bangui has 100,000s-500,000 IDPs though.
  #if t_data == date_to_sim_days("2013-04-17"):
  e.add_conflict_zone("Mbres")
  #if t_data == date_to_sim_days("2013-05-03"):
  e.add_conflict_zone("Bohong")
  #if t_data == date_to_sim_days("2013-05-17"):
  e.add_conflict_zone("Bouca")
  #if t_data == date_to_sim_days("2013-09-07"):
  e.add_conflict_zone("Bossangoa")
  #if t_data == date_to_sim_days("2013-09-14"):
  e.add_conflict_zone("Bossembele")
  #if t_data == date_to_sim_days("2013-10-10"):
  e.add_conflict_zone("Bogangolo")
  #if t_data == date_to_sim_days("2013-10-26"):
  e.add_conflict_zone("Bouar")
  #if t_data == date_to_sim_days("2013-11-10"):
  e.add_conflict_zone("Rafai")
  #if t_data == date_to_sim_days("2013-11-28"):
  e.add_conflict_zone("Damara")


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

    #CAR/DRC border is closed on the 5th of December 2013. Appears to remain closed until the 30th of June
    #Source: http://data.unhcr.org/car/download.php
    if t_data == date_to_sim_days("2013-12-05"):
      e.remove_link("Bangui","Mole")
      e.remove_link("Gbadolite","Inke")

    if t_data == date_to_sim_days("2013-06-30"):
      e.remove_link("Mole","Bangui")
      e.remove_link("Inke","Gbadolite")
      e.linkUp("Bangui","Mole","42.0")
      e.linkUp("Gbadolite","Inke","42.0")

    # 12 Feb. In Mole, refugees who were waiting to be registered and relocated received their food rations from the WFP.  
    # Source: http://data.unhcr.org/car/download.php?id=22

    # 19 Feb: drop of IDPs in Bangui from 400k to 273k.

    # Close borders here: On the 12th of May 2014, Chad closes border altogether.
    if t_data == date_to_sim_days("2014-05-12"):
      e.remove_link("Kabo","Belom")
      e.remove_link("Ndele","Belom")
      e.remove_link("Paoua","Dosseye")
      e.remove_link("RN1","Dosseye")

    #Conflict zones after the start of simulation period
    if t_data == date_to_sim_days("2013-12-06"): #A wave of reprisal attacks & escalating cycle of violence between Seleka militia and Anti-Balaka
      e.add_conflict_zone("Bozoum")

    #if t_data == date_to_sim_days("2013-12-21"): #MISCA: African-led International Support Mission against Anti-balaka (deaths & thousnads displaced)
    #  e.add_conflict_zone("Bossangoa")

    if t_data == date_to_sim_days("2014-01-01"): #Violence & death in battles between Seleka militia and Anti-Balaka
      e.add_conflict_zone("Bimbo")

    #if t_data == date_to_sim_days("2014-01-19"): #Violence & battles of Seleka militia with Anti-Balaka
    #  e.add_conflict_zone("Bambari")
    #if t_data == date_to_sim_days("2014-01-20"):
    #  e.add_conflict_zone("Bouar")

    if t_data == date_to_sim_days("2014-01-28"): #Battles between Seleka militia and Anti-Balaka
      e.add_conflict_zone("Boda")

    if t_data == date_to_sim_days("2014-02-06"): #Battles between Seleka militia and Anti-Balaka
      e.add_conflict_zone("Kaga Bandoro")

    if t_data == date_to_sim_days("2014-02-11"): ##Battles between Military forces and Anti-Balaka
      e.add_conflict_zone("Berberati")

    #if t_data == date_to_sim_days("2014-02-16"): #Battles between Seleka militia and Salanze Communal Militia
    #  e.add_conflict_zone("Bangassou")

    #if t_data == date_to_sim_days("2014-03-08"): #Battles between Seleka militia and Sangaris (French Mission)
    #  e.add_conflict_zone("Ndele")

    if t_data == date_to_sim_days("2014-03-11"): #MISCA: African-led International Support Mission against Anti-balaka
      e.add_conflict_zone("Nola")

    if t_data == date_to_sim_days("2014-04-08"): #Battles between Seleka militia and Anti-Balaka
      e.add_conflict_zone("Dekoa")

    if t_data == date_to_sim_days("2014-04-10"): #Battles of Bria Communal Militia (Seleka Militia) and MISCA (African-led International Support Mission)
      e.add_conflict_zone("Bria")

    if t_data == date_to_sim_days("2014-04-14"): #Battles between Anti-Balaka and Seleka militia
      e.add_conflict_zone("Grimari")

    #if t_data == date_to_sim_days("2014-04-23"): #Battles between Seleka militia and Anti-Balaka
    #  e.add_conflict_zone("Bouca")

    if t_data == date_to_sim_days("2014-04-26"): #Battles by unidentified Armed groups
      e.add_conflict_zone("Paoua")

    if t_data == date_to_sim_days("2014-05-23"): #MISCA: African-led International Support Mission against Anti-balaka
      e.add_conflict_zone("Carnot")

    if t_data == date_to_sim_days("2014-07-30"): #Battles between Anti-Balaka and Seleka militia
      e.add_conflict_zone("Batangafo")

    if t_data == date_to_sim_days("2014-10-10"): #MINUSCA: United Nations Multidimensional Integrated Stabilization Mission against Seleka militia (PRGF Faction)
      e.add_conflict_zone("Sibut")

    #Insert refugee agents
    for i in range(0, new_refs):
      e.addAgent(e.pick_conflict_location())

    #Propagate the model by one time step.
    e.evolve()

    #e.printInfo()


    #Validation/data comparison
    amboko_data = d.get_field("Amboko", t) #- d.get_field("Amboko", 0)
    belom_data = d.get_field("Belom", t) #- d.get_field("Belom", 0)
    dosseye_data = d.get_field("Dosseye", t) #- d.get_field("Dosseye", 0)
    gondje_data = d.get_field("Gondje", t) #- d.get_field("Gondje", 0)
    moyo_data = d.get_field("Moyo", t) #- d.get_field("Moyo", 0)
    east_data = d.get_field("East", t) #- d.get_field("East", 0)
    adamaoua_data = d.get_field("Adamaoua", t) #- d.get_field("Adamaoua", 0)
    bili_data = d.get_field("Bili", t) #- d.get_field("Bili", 0)
    bossobolo_data = d.get_field("Bossobolo", t) #- d.get_field("Bossobolo", 0)
    mole_data = d.get_field("Mole", t) #- d.get_field("Mole", 0)
    boyabu_data = d.get_field("Boyabu", t) #- d.get_field("Boyabu", 0)
    mboti_data = d.get_field("Mboti", t) #- d.get_field("Mboti", 0)
    inke_data = d.get_field("Inke", t) #- d.get_field("Inke", 0)
    betou_data = d.get_field("Betou", t) #- d.get_field("Betou", 0)
    brazaville_data = d.get_field("Brazaville", t) #- d.get_field("Brazaville", 0)

    #Calculation of error terms
    errors = []
    abs_errors = []
    loc_data = [amboko_data, belom_data, dosseye_data, gondje_data, moyo_data, east_data, adamaoua_data, bili_data, bossobolo_data, mole_data, boyabu_data, mboti_data, inke_data, betou_data, brazaville_data]
    camp_locations = [39, 40, 41, 42, 43, 49, 53, 54, 57, 58, 59, 60, 61, 62, 63]

    camps = []
    for i in camp_locations:
      camps += [locations[i]]
    camp_names = ["Amboko", "Belom", "Dosseye", "Gondje", "Moyo", "East", "Adamaoua", "Bili", "Bossobolo", "Mole", "Boyabu", "Mboti", "Inke", "Betou", "Brazaville"]

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




