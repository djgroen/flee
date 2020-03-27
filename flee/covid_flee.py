# covid_flee.py
# Covid-19 model, based on the general Flee paradigm.
import numpy as np
import sys
import random
from flee import SimulationSettings
from flee import flee
import array
import csv

# TODO: store all this in a YaML file
lids = {"park":0,"hospital":1,"supermarket":2,"office":3,"school":4,"leisure":5,"shopping":6} # location ids and labels
avg_visit_times = [90,60,60,360,360,60,60] #average time spent per visit
incubation_period = 5
recovery_period = 14

class Needs():
  def __init__(self, csvfile):
    self.add_needs(csvfile)

  def i(self, name):
    for k,e in enumerate(self.labels):
      if e == name:
        return k

  def add_needs(self, csvfile=""):
    if csvfile == "":
      self.add_hardcoded_needs()
      return
    self.needs = np.zeros((len(lids),120))
    needs_cols = [0,0,0,0,0,0,0]
    with open(csvfile) as csvfile:
      needs_reader = csv.reader(csvfile)
      row_number = 0
      for row in needs_reader:
        if row_number == 0:
          for k,element in enumerate(row):
            if element in lids.keys():
              needs_cols[lids[element]] = k
            print(element,k)
          print("NC:",needs_cols)
        else:
          for i in range(0,len(needs_cols)):
            self.needs[i,row_number-1] = int(row[needs_cols[i]])
        row_number += 1

  # Hard-coded draft file
  def add_hardcoded_needs(self):
    self.needs = np.zeros((len(lids),120))

    self.needs[lids["park"]][:] = 120
    
    self.needs[lids["hospital"]][:] = 10
    
    self.needs[lids["supermarket"]][:] = 60
    
    self.needs[lids["office"]][19:] = 1200
    self.needs[lids["office"]][:20] = 0

    self.needs[lids["school"]][19:] = 0
    self.needs[lids["school"]][:20] = 1200
    
    self.needs[lids["leisure"]][:] = 120
    
    self.needs[lids["shopping"]][:] = 60

  def get_need(self, age, need):
    return self.needs[need,age]

  def get_needs(self, age):
    return self.needs[:,age]

  def print(self):
    for i in range(0,119):
      print(i, self.get_needs(i))

# Global storage for needs now, to keep it simple.
needs = Needs("covid_data/needs.csv")
needs.print()

class Person():
  def __init__(self, location, age):
    self.location = location # current location
    self.location.IncrementNumAgents()
    self.home_location = location

    self.status = "susceptible" # states: susceptible, exposed, infectious, recovered, dead.
    self.symptomatic = False # may be symptomatic if infectious
    self.status_change_time = -1

    self.age = age # age in years


  def plan_visits(self):
    personal_needs = needs.get_needs(self.age)
    for k,element in enumerate(personal_needs):
      nearest_locs = self.home_location.nearest_locations
      if nearest_locs[k]:
        location_to_visit = nearest_locs[k]
        location_to_visit.register_visit(self, element)

  def get_needs(self):
    print(self.age, needs.get_needs(self.age))

  def infect(self, t, severity="exposed"):
    # severity can be overridden to infectious when rigidly inserting cases.
    # but by default, it should be exposed.
    self.status = severity
    self.status_change_time = t

  def progress_condition(self, t):
    if self.status == "exposed" and t-self.status_change_time > incubation_period:
      self.status = "infectious"
      self.status_change_time = t
    if self.status == "infectious" and t-self.status_change_time > recovery_period:
      self.status = "recovered"
      self.status_change_time = t

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
  def __init__(self, e, x, y, num_households=1):
    self.x = x
    self.y = y
    self.households = []
    self.numAgents = 0
    self.nearest_locations = self.find_nearest_locations(e)
    for i in range(0, num_households):
        self.households.append(Household(self))

  def IncrementNumAgents(self):
    self.numAgents += 1

  def DecrementNumAgents(self):
    self.numAgents -= 1

  def find_nearest_locations(self, e):
    """
    identify preferred locations for each particular purpose,
    and store in an array.
    """
    n = []
    for l in lids.keys():
      if l not in e.locations.keys():
        n.append(None)
      else:
        min_dist = 99999.0
        nearest_loc_index = 0
        for k,element in enumerate(e.locations[l]): # using 'element' to avoid clash with Ecosystem e.
          d = calc_dist(self.x, self.y, element.x, element.y)
          if d < min_dist:
            min_dist = d
            nearest_loc_index = k
        n.append(e.locations[l][nearest_loc_index])

    for i in n:
      if i:  
        print(i.name, i.type)
    return n

  def add_infection(self, time): # used to preseed infections (could target using age later on)
    infection_pending = True
    while infection_pending:
      hh = random.randint(0, len(self.households)-1)
      p = random.randint(0, len(self.households[hh].agents)-1)
      if self.households[hh].agents[p].status == "susceptible": 
        # because we do pre-seeding we need to ensure we add exactly 1 infection.
        self.households[hh].agents[p].infect(time, severity="infectious")
        infection_pending = False


class Location:
  def __init__(self, name, loc_type="park", x=0.0, y=0.0, sqm=10000):

    if loc_type not in lids.keys():
      print("Error: location type {} is not in the recognised lists of location ids (lids).".format(loc_type))
      sys.exit()

    self.name = name
    self.x = x
    self.y = y
    self.links = [] # paths connecting to other locations
    self.closed_links = [] #paths connecting to other locations that are closed.
    self.type = loc_type # supermarket, park, hospital, shopping, school, office, leisure? (home is a separate class, to conserve memory)
    self.sqm = sqm # size in square meters.
    self.visits = []
    self.inf_visit_minutes = 0 # aggregate number of visit minutes by infected people.
    self.avg_visit_time = avg_visit_times[lids[loc_type]] # using averages for all visits for now. Can replace with a distribution later.

    print(self.avg_visit_time)

  def DecrementNumAgents(self):
    self.numAgents -= 1

  def IncrementNumAgents(self):
    self.numAgents += 1

  #def print(self):
  #  for l in self.links:
  #    print("Link from %s to %s, dist: %s" % (self.name, l.endpoint.name, l.distance), file=sys.stderr)

  def clear_visits(self):
    self.visits = []
    self.visit_minutes = 0 # total number of minutes of all visits aggregated.

  def register_visit(self, person, need):
    visit_probability = need/(self.avg_visit_time * 7) # = minutes per week / (average visit time * days in the week)
    if random.random() < visit_probability:
      self.visits.append([person, self.avg_visit_time])
      if person.status == "infected":
        self.inf_visit_minutes += self.avg_visit_time

  def evolve(self):
    minutes_opened = 12*60
    for v in self.visits:
      if v[0].status == "susceptible":
        infection_probability = (v[1] / self.sqm) * (self.inf_visit_minutes / minutes_opened)
        print(v, infection_probability, v[1], self.sqm, self.inf_visit_minutes, minutes_opened)
        if random.random() < infection_probability:
          v[0].status = "exposed"
          print("Infection event at {}".format(self.name))


class Ecosystem:
  def __init__(self):
    self.locations = {}
    self.houses = []
    self.house_names = []
    self.time = 0

  def evolve(self):
    # remove visits from the previous day
    for lk in self.locations.keys():
      for l in self.locations[lk]:
        l.clear_visits()

    # collect visits for the current day
    for h in self.houses:
      for hh in h.households:
        for a in hh.agents:
          a.plan_visits()
          a.progress_condition(self.time)

    # process visits for the current day (spread infection).
    for lk in self.locations.keys():
      for l in self.locations[lk]:
        l.evolve()

    self.time += 1

  def addHouse(self, name, x, y, num_households=1):
    h = House(self, x, y, num_households)
    self.houses.append(h)
    self.house_names.append(name)
    return h

  def addLocation(self, name, loc_type, x, y, sqm=10000):
    l = Location(name, loc_type, x, y, sqm)
    if loc_type in self.locations.keys():
      self.locations[loc_type].append(l)
    else:
      self.locations[loc_type] = [l]
    return l

  def print_needs(self):
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          print(k, a.get_needs())

  def print_status(self):
    status = {"susceptible":0,"exposed":0,"infectious":0,"recovered":0,"dead":0}
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          status[a.status] += 1
    print(status)


if __name__ == "__main__":
  print("No testing functionality here yet.")
