import flee.covid_flee as flee
import numpy as np
import outputanalysis.analysis as a

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Testing basic Covid-19 simulation kernel.")

  end_time = 10
  e = flee.Ecosystem()

  l1 = e.addLocation("A", "supermarket", 6, 6)
  lp1 = e.addLocation("lp1", "park", 4, 4)
  lp2 = e.addLocation("lp2", "park", 1, 4)

  l3 = e.addHouse("H1", 1, 5)
  l4 = e.addHouse("H2", 4, 5)

  e.print_needs()

  for t in range(0,end_time):

    # Propagate the model by one time step.
    e.evolve()

    print(t)

  assert t==9

  print("Test successful!")

