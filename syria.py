import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("SYRIA SIMULATION")

  end_time = 80
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
  
  #Camps in Iraq
  locations.append(e.addLocation("Arbat", movechance=0.001)
  locations.append(e.addLocation("Duhok", movechance=0.001)
  locations.append(e.addLocation("Akre", movechance=0.001)
  locations.append(e.addLocation("Al-Obaidi", movechance=0.001)
  locations.append(e.addLocation("Anbar", movechance=0.001)
  locations.append(e.addLocation("Kawergosk", movechance=0.001)
  locations.append(e.addLocation("Basirma", movechance=0.001)
  locations.append(e.addLocation("Darashakran", movechance=0.001)
  locations.append(e.addLocation("Domiz1", movechance=0.001)
  locations.append(e.addLocation("Domiz2", movechance=0.001)
  locations.append(e.addLocation("Erbil", movechance=0.001)
  locations.append(e.addLocation("Gawilan", movechance=0.001)
  locations.append(e.addLocation("Qushtapa", movechance=0.001)
  locations.append(e.addLocation("Sulaymaniyah", movechance=0.001)
  
  #Destiations in jordan
  locations.append(e.addLocation("Irbid", movechance=0.001)
  locations.append(e.addLocation("Mafraq", movechance=0.001)
  locations.append(e.addLocation("Zarqa", movechance=0.001)
  locations.append(e.addLocation("Zaatari", movechance=0.001)
  
  #Destiations in Lebanon
  locations.append(e.addLocation("Beirut", movechance=0.001)
  locations.append(e.addLocation("North", movechance=0.001)
  locations.append(e.addLocation("South", movechance=0.001)
  locations.append(e.addLocation("Bekaa", movechance=0.001)
  
  
  
  e.linkUp("A","B","834.0")
  e.linkUp("A","C","1368.0")
  e.linkUp("A","D","536.0")
  e.linkUp("A","B","834.0")
  e.linkUp("A","C","1368.0")
  e.linkUp("A","D","536.0")
  
  
  
  
  
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
