# micro_flee.py
# sequential microscale model.
import numpy as np
import sys
import random
from flee import SimulationSettings
from flee import flee
import array

loc_labels = ["park","hospital","supermarket","office","school","leisure","shopping"]

class Needs():
  def __init__(self):
    self.needs = {} # needs measured in minutes per week per category.

  def i(self, name):
    for k,e in enumerate(self.labels):
      if e == name:
        return k

  def add_needs(self, person):
    self.needs = np.zeros((len(loc_labels),120))

    self.needs[i("park")][:] = 120
    
    self.needs[i("hospital")][:] = 10
    
    self.needs[i("supermarket")][:] = 60
    
    self.needs[i("office")][19:] = 1200
    self.needs[i("office")][:20] = 0

    self.needs[i("school")][19:] = 0
    self.needs[i("school")][:20] = 1200
    
    self.needs[i("leisure")][:] = 120
    
    self.needs[i("shopping")][:] = 60

  def get_need(age, need):
    return self.needs[need][age]

  def get_needs(age):
    return self.needs[:][age]

# Global storage for needs now, to keep it simple.
needs = Needs()

class Person():
  def __init__(self, location, age):
    self.location = location # current location
    self.location.IncrementNumAgents()
    self.home_location = location

    self.status = "susceptible" # states: susceptible, exposed, infectious, recovered, dead.
    self.symptomatic = False # may be symptomatic if infectious

    self.age = age # age in years


  def plan_visits(self):
    personal_needs = needs.get_needs(self.age)
    for n in personal_needs:
      register_visit(self.home_location,self.)

  def evolve(self):


class Household():
  def __init__(self, house, size=-1):
    self.house = house
    if size>-1:
      self.size = size
    else:
      self.size = random.choice([1,2,3,4])

    self.agents = []
    for i in range(0,self.size):
      self.agents.append(Person(self.house, random.randint(0,100)))


def calc_dist(x1, y1, x2, y2):
    return (abs(x1-x2)**2 + abs(y1+y2)**2)**0.5

class House:
  def __init__(self, x, y, num_households=1):
    self.x = x
    self.y = y
    self.households = []
    self.numAgents = 0
    self.nearest_locations = calculate_nearest_locations()
    for i in range(0, num_households):
        self.households.append(Household(self))

  def IncrementNumAgents(self):
    self.numAgents += 1

  def DecrementNumAgents(self):
    self.numAgents -= 1

  def find_nearest_locations(self):
    """
    identify preferred locations for each particular purpose,
    and store in an array.
    """
    n = []
    for l in loc_labels:
      if len(e.locations[l]) == 0:
        n.append(None)
      else:
        min_dist = 99999.0
        nearest_loc_index = 0
        for k,e in enumerate(e.locations[l]):
          d = calc_dist(x, y, e.x, e.y)
          if d < min_dist:
            min_dist = d
            nearest_loc_index = k
        n.append(e.locations[l][k])




class Location:
  def __init__(self, name, loc_type="home", x=0.0, y=0.0, sqm=10000):
    self.name = name
    self.x = x
    self.y = y
    self.links = [] # paths connecting to other towns
    self.closed_links = [] #paths connecting to other towns that are closed.
    self.numAgents = 0 # refugee population
    self.capacity = capacity # refugee capacity
    self.type = loc_type # home, supermarket, park, hospital, shopping, school, office, leisure?
    self.sqm = sqm # size in square meters.

    self.print()

  def DecrementNumAgents(self):
    self.numAgents -= 1

  def IncrementNumAgents(self):
    self.numAgents += 1

  def print(self):
    for l in self.links:
      print("Link from %s to %s, dist: %s" % (self.name, l.endpoint.name, l.distance), file=sys.stderr)


class Ecosystem(flee.Ecosystem):
  def __init__(self):
    super().__init__()
    self.houses = []
    self.house_names = []

  def evolve(self):
    for h in self.houses:
      for hh in h.households:
        for a in hh.agents:
          a.plan_visits()
          a.evolve()

  def addHouse(self, name, x, y, num_households=1):
    self.houses.append(House(x, y, num_households))
    self.house_names.append(name)


if __name__ == "__main__":
  print("No testing functionality here yet.")
