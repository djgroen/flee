import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  #print("SYRIA SIMULATION")

  end_time = 396
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
  locations.append(e.addLocation("Salamiyah", movechance=0.3))
  locations.append(e.addLocation("Saraqib", movechance=0.3))
  locations.append(e.addLocation("H",  movechance=0.3))
  locations.append(e.addLocation("i", movechance=0.3))
  locations.append(e.addLocation("o", movechance=0.3))
  locations.append(e.addLocation("a", movechance=0.3))
  locations.append(e.addLocation("o", movechance=0.3))
  locations.append(e.addLocation("l", movechance=0.3))
  locations.append(e.addLocation("G", movechance=0.3))
  locations.append(e.addLocation("G", movechance=0.3))
  locations.append(e.addLocation("M", movechance=0.3))
  locations.append(e.addLocation("C", movechance=0.3))

  #Jordan camps and cities
  locations.append(e.addLocation("Zaatari", movechance=0.01))
  locations.append(e.addLocation("Mafraq", movechance=0.01))
  locations.append(e.addLocation("Irbid", movechance=0.01))
  locations.append(e.addLocation("Zarqa", movechance=0.01))
  locations.append(e.addLocation("Kigali", movechance=0.01))
  locations.append(e.addLocation("Lusenda", movechance=0.01))

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
  e.linkUp("Rumonge","Makamba","91.0")
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
  e.linkUp("Bujumbura","Commune of Mabanda","150.0")
  e.linkUp("Commune of Mabanda","Nyarugusu","71.0")
  e.linkUp("Kirundo","Nakivale","307.0")
  e.linkUp("Kirundo","Kigali","88.0")
  e.linkUp("Kigali","Nakivale","247.0")
  e.linkUp("Kayanza","Nakivale","426.0")
  e.linkUp("Bujumbura","Lusenda","53.0")


  d = handle_refugee_data.DataTable(csvformat="generic", data_directory="syria2013", start_date="2015-05-01")

  list_of_cities = "Time"

for l in locations:
    list_of_cities = "%s,%s" % (list_of_cities, l.name)

print(list_of_cities)
  #print("Time,",list_of_cities[192:])


for t in range(0,end_time):
  new_refs = d.get_new_refugees(t)


  # Insert refugee agents
for i in range(0, new_refs):
    e.addAgent(location = chosen_location])


  #e.addAgent(location=locations[0])

  # Propagate the model by one time step.
  e.evolve()

  e.printInfo()

  output_string = "%s" % t

for l in locations[0]:
  output_string = "%s,%s" % (output_string, l.numAgents)

print(output_string)

    mahama_data = d.get_field("Mahama", t) - d.get_field("Mahama", 0)
    nduta_data = d.get_field("Nduta", t) - d.get_field("Nduta", 0)
    nyarugusu_data = d.get_field("Nyarugusu", t) - d.get_field("Nyarugusu", 0)
    nakivale_data = d.get_field("Nakivale", t) - d.get_field("Nakivale", 0)
    lusenda_data = d.get_field("Lusenda", t) - d.get_field("Lusenda", 0)

print(mahama_data, nduta_data, nyarugusu_data, nakivale_data, lusenda_data)

    #print(t, locations[22].numAgents, mahama_data, a.rel_error(locations[22].numAgents, mahama_data))
    #print(t, locations[23].numAgents, nduta_data, a.rel_error(locations[23].numAgents, nduta_data))
    #print(t, locations[24].numAgents, nyarugusu_data, a.rel_error(locations[24].numAgents, nyarugusu_data))
    #print(t, locations[25].numAgents, nakivale_data, a.rel_error(locations[25].numAgents, nakivale_data))
    #print(t, locations[27].numAgents, lusenda_data, a.rel_error(locations[27].numAgents, lusenda_data))

  errors = [a.rel_error(l.numAgents,mahama_data), a.rel_error(l.numAgents,nduta_data), a.rel_error(l.numAgents,nyarugusu_data), a.rel_error(l.numAgents,nakivale_data),a.rel_error(l.numAgents,lusenda_data)]

    #print("location: ", l.numAgents, ", data: ", mahama_data, ", error: ", errors[0])
    #print("location: ", l.numAgents, ", data: ", nduta_data, ", error: ", errors[1])
    #print("location: ", l.numAgents, ", data: ", nyarugusu_data, ", error: ", errors[2])
    #print("location: ", l.numAgents, ", data: ", nakivale_data, ", error: ", errors[3])
    #print("location: ", l.numAgents, ", data: ", lusenda_data, ", error: ", errors[4])


print("Cumulative error: ", np.sum(errors), "Squared error: ", np.sqrt(np.sum(np.power(errors,2))))

if np.abs(np.sum(errors) - 0.495521376979) > 0.1:
  print("TEST FAILED.")
if np.sqrt(np.sum(np.power(errors,2))) > 0.33+0.03:
  print("TEST FAILED.")
else:
  print("TEST SUCCESSFUL.")

