import flee.flee as flee
import datamanager.handle_refugee_data as handle_refugee_data
import numpy as np
import outputanalysis.analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Testing basic data handling and simulation kernel.")

  flee.SimulationSettings.MinMoveSpeed=5000.0
  flee.SimulationSettings.MaxMoveSpeed=5000.0
  flee.SimulationSettings.MaxWalkSpeed=5000.0

  end_time = 10
  e = flee.Ecosystem()

  l1 = e.addLocation("A", movechance=0.3)

  l2 = e.addLocation("B", movechance=0.3)
  l3 = e.addLocation("C", movechance=0.3)
  l4 = e.addLocation("D", movechance=0.3)
  l5 = e.addLocation("E", movechance=0.3)
  l6 = e.addLocation("F", movechance=0.3)
  l7 = e.addLocation("G", movechance=0.3)
  l8 = e.addLocation("H", movechance=0.3)
  l9 = e.addLocation("I", movechance=0.3)
  l0 = e.addLocation("J", movechance=0.3)

  e.linkUp("A","B","834.0")
  e.linkUp("C","B","834.0")
  e.linkUp("D","C","834.0")
  e.linkUp("E","D","834.0")
  e.linkUp("F","E","834.0")
  e.linkUp("F","G","834.0")
  e.linkUp("H","I","834.0")
  e.linkUp("J","I","834.0")
  e.linkUp("A","C","834.0")
  e.linkUp("H","J","834.0")

  e.addAgent(location=l1)

  for t in range(0,end_time):

    # Propagate the model by one time step.
    e.evolve()

    print(t, l1.numAgents+l2.numAgents+l3.numAgents+l4.numAgents, l1.numAgents, l2.numAgents, l3.numAgents, l4.numAgents)

  print("Test successful!")

