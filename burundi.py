import flee
import handle_refugee_data
import numpy as np
import analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Simulating Burundi.")

  end_time = 396
  e = flee.Ecosystem()

  l1 = e.addLocation("Bujumbura", movechance=1.0)

  l2 = e.addLocation("Bubanza", movechance=0.3)
  l3 = e.addLocation("Cibitoke", movechance=0.3)
  l4 = e.addLocation("Isale", movechance=0.3)
  l5 = e.addLocation("Muramvya", movechance=0.3)
  l6 = e.addLocation("Kayanza", movechance=0.3)
  l7 = e.addLocation("Mwaro", movechance=0.3)
  l8 = e.addLocation("Rumonge", movechance=0.3)
  l9 = e.addLocation("Bururi", movechance=0.3)
  l10 = e.addLocation("Rutana", movechance=0.3)
  l11 = e.addLocation("Makamba", movechance=0.3)
  l12 = e.addLocation("Gitega", movechance=0.3)
  l13 = e.addLocation("Karuzi", movechance=0.3)
  l14 = e.addLocation("Ruyigi", movechance=0.3)
  l15 = e.addLocation("Cankuzo", movechance=0.3)
  l16 = e.addLocation("Muyinga", movechance=0.3)
  l17 = e.addLocation("Kirundo", movechance=0.3)
  l18 = e.addLocation("Ngozi", movechance=0.3)
  l19 = e.addLocation("Gashoho", movechance=0.3)
  l20 = e.addLocation("Gitega-Ruyigi", movechance=0.3)
  l21 = e.addLocation("Makebuko", movechance=0.3)

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
  e,linkUp("Makebuko","Ruyigi","40.0")
  e.linkUp("Ruyigi","Cankuzo","51.0")
  e.linkUp("Cankuzo","Muyinga","63.0")

  d = handle_refugee_data.DataTable("source-data-unhcr.txt", csvformat="burundi-pdf")

  for t in range(0,end_time):
    new_refs = d.get_new_refugees(t)

    # Insert refugee agents
    for i in range(0, new_refs):
      e.addAgent(location=l1)

    # Propagate the model by one time step.
    e.evolve()

    e.printInfo()
    print("t, l1.numAgents, l2.numAgents, l3.numAgents, l4.numAgents, l5.numAgents, l6.numAgents, l7.numAgents, l8.numAgents, l9.numAgents, l10.numAgents, l11.numAgents, l12.numAgents, l13.numAgents, l14.numAgents, l15.numAgents, l16.numAgents, l17.numAgents, l18.numAgents, l19.numAgents, l20.numAgents, l21.numAgents")

    """
    l2_data = d.get_field("Mahama", t) - d.get_field("Mahama", 0)
    l3_data = d.get_field("Nduta", t) - d.get_field("Nduta", 0)
    l4_data = d.get_field("Nakivale", t) - d.get_field("Nakivale", 0)
    l5_data = d.get_field("Lusenda", t) - d.get_field("Lusenda", 0)

    errors = [a.rel_error(l2.numAgents,l2_data), a.rel_error(l3.numAgents,l3_data), a.rel_error(l4.numAgents,l4_data), a.rel_error(l5.numAgents,l5_data)]

    print "Bubanza: ", l2.numAgents, ", data: ", l2_data, ", error: ", errors[0]
    print "Cibitoke: ", l3.numAgents, ", data: ", l3_data, ", error: ", errors[1]
    print "Isale: ", l4.numAgents, ", data: ", l4_data, ", error: ", errors[2]
    print "Muramvya: ", l5.numAgents, ", data: ", l5_data, ", error: ", errors[3]
    print "Kayanza: ", l6.numAgenta, ", data: ", l6_data, ", error: ", errors[4]
    print "Mwaro:






    print "Cumulative error: ", np.sum(errors), ", Squared error: ", np.sqrt(np.sum(np.power(errors,2)))

  if np.abs(np.sum(errors) - 0.495521376979) > 0.1:
    print "TEST FAILED."
  if np.sqrt(np.sum(np.power(errors,2))) > 0.33+0.03:
    print "TEST FAILED."
  else:
    print "TEST SUCCESSFUL."
    """
