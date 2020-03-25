# micro_flee.py
# sequential microscale model.
import numpy as np
import sys
import random
from flee import SimulationSettings
from flee import flee
import array


class Needs():
  def __init__(self):
    self.needs = {} # needs measured in minutes per week per category.

  def i(self, name):
    if k,e in enumerate(self.labels):
      if e == name:
        return k

  def add_needs(self, person):
    self.labels = ["park","hospital","supermarket","office","school","leisure","shopping"]

    self.needs = np.zeros((len(self.labels),120))

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


class Person():
  def __init__(self, location, age):
    self.location = location # current location
    self.location.IncrementNumAgents()
    self.home_location = location

    self.status = "susceptible" # states: susceptible, exposed, infectious, recovered, dead.
    self.symptomatic = False # may be symptomatic if infectious

    self.age = age # age in years


  def do_visits(self):
    pass 

  def evolve(self):
    self.plan_visits()
    self.do_visits()

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


class House:
  def __init__(self, x, y, num_households=1):
    self.x = x
    self.y = y
    self.households = []
    self.numAgents = 0
    for i in range(0, num_households):
        self.households.append(Household(self))

  def IncrementNumAgents(self):
    self.numAgents += 1

  def DecrementNumAgents(self):
    self.numAgents -= 1


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
    super().evolve()

  def addHouse(self, name, x, y, num_households=1):
    self.houses.append(House(x, y, num_households))
    self.house_names.append(name)


if __name__ == "__main__":
  print("No testing functionality here yet.")
