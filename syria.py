import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  #print("Syria Simulation")

  end_time = 301
  e = flee.Ecosystem()

  locations = []

  #Syria
  locations.append(e.addLocation("Aleppo", movechance=1.0))
  locations.append(e.addLocation("Damascus", movechance=0.3))
  locations.append(e.addLocation("Homs", movechance=0.3))
  locations.append(e.addLocation("Latakia", movechance=0.3))
  locations.append(e.addLocation("Hama", movechance=0.3))
  locations.append(e.addLocation("Ar-Raqqah", movechance=0.3))
  locations.append(e.addLocation("Deir ez-Zor", movechance=0.3))
  locations.append(e.addLocation("Al-Hasakah", movechance=0.3))
  locations.append(e.addLocation("Qamishli", movechance=0.3))
  locations.append(e.addLocation("Sayyidah Zaynab", movechance=0.3))
  locations.append(e.addLocation("Tall Halaf", movechance=0.3))
  locations.append(e.addLocation("Tall Tamir", movechance=0.3))
  locations.append(e.addLocation("Tadmuriyah", movechance=0.3))
  locations.append(e.addLocation("Shinshar", movechance=0.3))
  locations.append(e.addLocation("Qasim", movechance=0.3))
  locations.append(e.addLocation("Al-Thawrah", movechance=0.3))
  
  
  #Refugee destinatios in Lebanon
  locations.append(e.addLocation("North", movechance=0.001))
  locations.append(e.addLocation("South", movechance=0.001))
  locations.append(e.addLocation("Beirut", movechance=0.001))
  locations.append(e.addLocation("Bekaa", movechance=0.001))
  locations.append(e.addLocation("Mqaitaa", movechance=0.001))
  locations.append(e.addLocation("Tripoli", movechance=0.001))
  locations.append(e.addLocation("Damour", movechance=0.001))
  locations.append(e.addLocation("Tal Dar Zeinoun", movechance=0.001))
  
  #Refugee destinatios in Jordan
  locations.append(e.addLocation("Zarqa", movechance=0.001))
  locations.append(e.addLocation("Zaatari", movechance=0.001))
  locations.append(e.addLocation("Mafraq", movechance=0.001))
  locations.append(e.addLocation("Irbid", movechance=0.001))

"""  
  #Refugee destinatios in Turkey
  locations.append(e.addLocation("Kilis", movechance=0.001))
  locations.append(e.addLocation("Yayladagi", movechance=0.001))
  locations.append(e.addLocation("Akcakale", movechance=0.001))
"""
  
  #Refugee destinatios in Iraq
  locations.append(e.addLocation("Duhok", movechance=0.001))
  locations.append(e.addLocation("Anbar", movechance=0.001))
  locations.append(e.addLocation("Erbil", movechance=0.001))
  locations.append(e.addLocation("Sulaymaniyah", movechance=0.001))
  locations.append(e.addLocation("Telafar", movechance=0.001))
  locations.append(e.addLocation("Tishta", movechance=0.001))
x  locations.append(e.addLocation("Makhmur", movechance=0.001))

  #Distances obtained from bing maps and rounded
  
  #Syria distances
  e.linkUp("Aleppo","Hama","137.0")
  e.linkUp("Aleppo","Latakia","172.0")
  e.linkUp("Aleppo","Tall Halaf","316.0")
  e.linkUp("Qamishli","Tall Halaf","116.0")
  e.linkUp("Tall Tamir","Tall Halaf","116.0")
  e.linkUp("Hama","Latakia","114.0")
  e.linkUp("Homs","Latakia","138.0")
  e.linkUp("Ar-Raqqah","Deir ez-Zor","137.0")
  e.linkUp("Homs","Tadmuriyah","147.0")
  e.linkUp("Tadmuriyah","Deir ez-Zor","208.0")
  e.linkUp("Tall Tamir","Al-Hasakah","37.0")
  e.linkUp("Tall Tamir","Ar-Raqqah","164.0")
  e.linkUp("Sayyidah Zaynab","Damascus","10.0")
  e.linkUp("Hama","Al-Thawrah","206.0")
  e.linkUp("Aleppo","Al-Thawrah","112.0")
  e.linkUp("Ar-Raqqah","Al-Thawrah","87.0")
  e.linkUp("Al-Hasakah","Deir ez-Zor","148.0")
  e.linkUp("Qamishli","Al-Hasakah","86.0")
  e.linkUp("Damascus","Shinshar","145.0")
  e.linkUp("Homs","Shinshar","15.0")
  e.linkUp("Damascus","Qasim","58.0")
  
  #Jordan distances
  e.linkUp("Irbid","Qasim","71.0")
  e.linkUp("Qasim","Mafraq","77.0")
  e.linkUp("Zaatari","Mafraq","13.0")
  e.linkUp("Zarqa","Mafraq","46.0")

  #Lebanon distances
  e.linkUp("Homs","Mqaitaa","77.0")
  e.linkUp("Tripoli","Mqaitaa","20.0")
  e.linkUp("Mqaitaa","Latakia","119.0")
  e.linkUp("Tripoli","North","29.0")
  e.linkUp("Beirut","Damour","23.0")
  e.linkUp("South","Damour","53.0")
  e.linkUp("Shinshar","Bekaa","104.0")
  e.linkUp("Damascus","Tal Dar Zeinoun","52.0")
  e.linkUp("Bekaa","Tal Dar Zeinoun","28.0")
  e.linkUp("Beirut","Tal Dar Zeinoun","52.0")
  e.linkUp("South","Tal Dar Zeinoun","100.0")
  
""" 
  #Turkey distances
  e.linkUp("Aleppo","Kilis","65.0")
  e.linkUp("Latakia","Yayladagi","56.0")
  e.linkUp("Ar-Raqqah","Akcakale","93.0")
"""
  #Iraq distances
  e.linkUp("Duhok","Telafar","120.0")
  e.linkUp("Qamishli","Telafar","87.0")
  e.linkUp("Al-Hasakah","Telafar","134.0")
  e.linkUp("Tishta","Telafar","71.0")
  e.linkUp("Tishta","Makhmur","134.0")
  e.linkUp("Tishta","Deir ez-Zor","298.0")
  e.linkUp("Anbar","Deir ez-Zor","143.0")
  e.linkUp("Makhmur","Erbil","48.0")
  e.linkUp("Makhmur","Sulaymaniyah","182.0")
  e.linkUp("Tadmuriyah","Anbar","267.0")
  
  
  d = handle_refugee_data.DataTable(csvformat="generic", data_directory="Syria", start_date="2013-01-01")


  list_of_cities = "Time"
  
  for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

 
  #print(list_of_cities)
  #print("Time,",list_of_cities)
  
  
 
  conflict_zones = [locations[0]]
  conflict_weights = np.array([2132100])

  for t in range(0,end_time):
  
    
    if t == 37: #security forces kill 400 people in damascus
      locations[1].movechance = 1.0
      conflict_zones += [locations[1]]
      conflict_weights = np.append(conflict_weights, [1711000])


    elif t==109: #Intense fighting between military & mulineer military forces
      locations[2].movechance = 1.0
      conflict_zones += [locations[1]]
      conflict_weights = np.append(conflict_weights, [652609])



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
    
    duhok_data = d.get_field("Duhok", t) - d.get_field("Duhok", 0)
    erbil_data = d.get_field("Erbil", t) - d.get_field("Erbil", 0)
    anbar_data = d.get_field("Anbar", t) - d.get_field("Anbar", 0)
    sulaymaniyah_data = d.get_field("Sulaymaniyah", t) - d.get_field("Sulaymaniyah", 0)
   
    irbid_data = d.get_field("Irbid", t) - d.get_field("Irbid", 0)    
    mafraq_data = d.get_field("Mafraq", t) - d.get_field("Mafraq", 0)  
    zaatari_data = d.get_field("Zaatari", t) - d.get_field("Zaatari", 0)  
    zarqa_data = d.get_field("Zarqa", t) - d.get_field("Zarqa", 0)  
   
    beirut_data = d.get_field("Beirut", t) - d.get_field("Beirut", 0)    
    bekaa_data = d.get_field("Bekaa", t) - d.get_field("Bekaa", 0)  
    north_data = d.get_field("North", t) - d.get_field("North", 0)  
    south_data = d.get_field("South", t) - d.get_field("South", 0)  
  
""" 
    kilis_data = d.get_field("Turkey", t) - d.get_field("Turkey", 0)    
    yayladagi_data = d.get_field("Turkey", t) - d.get_field("Turkey", 0)  
    akcakale_data = d.get_field("Turkey", t) - d.get_field("Turkey", 0)  
"""

    errors = [a.rel_error(l.numAgents,duhok_data), a.rel_error(l.numAgents,erbil_data), a.rel_error(l.numAgents,anbar_data), a.rel_error(l.numAgents,sulaymaniyah_data), a.rel_error(l.numAgents,irbid_data), a.rel_error(l.numAgents,mafraq_data), a.rel_error(l.numAgents,zaatari_data), a.rel_error(l.numAgents,zarqa_data), a.rel_error(l.numAgents,beirut_data), a.rel_error(l.numAgents,bekaa_data), a.rel_error(l.numAgents,north_data), a.rel_error(l.numAgents,south_data)]

    #print("location: ", l.numAgents, ", data: ", duhok_data, ", error: ", errors[0])
    

  if np.abs(np.sum(errors) - 0.495521376979) > 0.1:
    print("TEST FAILED.")
  if np.sqrt(np.sum(np.power(errors,2))) > 0.33+0.03:
    print("TEST FAILED.")
  else:
    print("TEST SUCCESSFUL.")

