import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("SYRIA SIMULATION")

  end_time = 365
  e = flee.Ecosystem()

  #cities in syria
  locations.append(e.addLocation("Aleppo", movechance=1.0)
  locations.append(e.addLocation("Damascus", movechance=0.3)
  locations.append(e.addLocation("Homs", movechance=1.0)
  locations.append(e.addLocation("Hama", movechance=1.0)
  locations.append(e.addLocation("Latakia", movechance=0.3)
  locations.append(e.addLocation("Deir ez-Zor", movechance=1.0)
  locations.append(e.addLocation("Al-Hasakah", movechance=0.3)
  locations.append(e.addLocation("Qamishli", movechance=0.3)
  locations.append(e.addLocation("Sayyidah Zaynab", movechance=0.3)
  locations.append(e.addLocation("Ar-Raqqah", movechance=1.0)
  locations.append(e.addLocation("Saraqib", movechance=0.3)
  locations.append(e.addLocation("Salamiyah", movechance=0.3)
  locations.append(e.addLocation("Harasta al Bas", movechance=0.3)
  
  #Camps and cities Iraq
 
  locations.append(e.addLocation("Mosul", movechance=1.0)
  locations.append(e.addLocation("Sulaymaniyah", movechance=0.001)
  locations.append(e.addLocation("Duhok", movechance=0.001)
  locations.append(e.addLocation("Erbil", movechance=0.001)
  locations.append(e.addLocation("Anbar", movechance=0.001)
 
  #Camps and cities in jordan
  locations.append(e.addLocation("Irbid", movechance=0.001)
  locations.append(e.addLocation("Mafraq", movechance=0.001)
  locations.append(e.addLocation("Zarqa", movechance=0.001)
  locations.append(e.addLocation("Zaatari", movechance=0.001)
  
  #Camps and cities in Lebanon
  locations.append(e.addLocation("Beirut", movechance=0.001)
  locations.append(e.addLocation("North", movechance=0.001)
  locations.append(e.addLocation("South", movechance=0.001)
  locations.append(e.addLocation("Bekaa", movechance=0.001)
  locations.append(e.addLocation("Tripoli", movechance=0.001)
  locations.append(e.addLocation("Chekka", movechance=0.001)
  locations.append(e.addLocation("Mqaitaa", movechance=0.001)
  
  
  
  
  #distances obtained from bing maps annd rounded
  #still under costruction
  
  e.linkUp("Homs","Salamiyah","45.0")
  e.linkUp("Hama","Homs","46.0")
  e.linkUp("Salamiyah","Homs","45.0")
  e.linkUp("Irbid","Zaatari","834.0")
  e.linkUp("Dayr az Zawr ","Dahuk","426.0")
  e.linkUp("Damascus ","South Lebanon","140.0")
  e.linkUp("Damascus ","Bekka Valley","81.0")
  e.linkUp("Dayr az Zawr ","Erbil","419.0")
  e.linkUp("Aleppo","Saraqib","53.0")
  e.linkUp("Saraqib","Latakia","124.0")
  e.linkUp("Ar Raqqah","Deir ez-Zor","137.0")
  e.linkUp("Sayyidah Zaynab ","Zarqa","185.0")
  e.linkUp("Sayyidah Zaynab ","Zaatari Camp","152.0")
  e.linkUp("Hama","Saraqib","86.0")
  e.linkUp("Mosul","D","536.0")
  e.linkUp("Damascus","Salamiyah","23.0")
  e.linkUp("Tripoli","Homs","46.0")
  e.linkUp("Salamiyah","Homs","45.0")
  e.linkUp("Irbid","Zaatari","834.0")
  e.linkUp("Dayr az Zawr ","As Sulaymanah","612.0")
  e.linkUp("Sayyidah Zaynab ","Amman","202.0")
  e.linkUp("Sayyidah Zaynab ","Irbid","133.0")
  e.linkUp("Damascus ","Beirut","105.0")
  e.linkUp("Damascus ","North Lebanon","161.0")
  
  
  
  d = handle_refugee_data.DataTable("source-data-unhcr.txt", csvformat="syria-pdf")
  
  list_of_cities= "Time"
  
  for l in locations:
  list_of_cities = "%s,%s" % (list_of_cities, l.name)
  
  print(list_of_cities)

  for t in range(0,end_time):
    new_refs = d.get_new_refugees(t)

    # Insert refugee agents
    for i in range(0, new_refs):
      e.addAgent(location=locations[0])

    # Propagate the model by one time step.
    e.evolve()

    e.printInfo()
    
    output_string = "%s" % t
    
        for l in locations[0]:
          output_string = "%s,%s" % (output_string, l.numAgents)

   

    """
    l2_data = d.get_field("Mauritania", t) - d.get_field("Mauritania", 0)
    l3_data = d.get_field("Niger", t) - d.get_field("Niger", 0)
    l4_data = d.get_field("Burkina Faso", t) - d.get_field("Burkina Faso", 0)

    errors = [a.rel_error(l2.numAgents,l2_data), a.rel_error(l3.numAgents,l3_data), a.rel_error(l4.numAgents,l4_data)]

    print "Kiffa: ", l2.numAgents, ", data: ", l2_data, ", error: ", errors[0]
    print "Niamey: ", l3.numAgents, ", data: ", l3_data, ", error: ", errors[1]
    print "Bobo-Dioulasso: ", l4.numAgents,", data: ", l4_data, ", error: ", errors[2]
    print "Cumulative error: ", np.sum(errors), ", Squared error: ", np.sqrt(np.sum(np.power(errors,2)))

  if np.abs(np.sum(errors) - 0.495521376979) > 0.1:
    print "TEST FAILED."
  if np.sqrt(np.sum(np.power(errors,2))) > 0.33+0.03:
    print "TEST FAILED."
  else:
    print "TEST SUCCESSFUL."
    """
