# covid_flee.py a.k.a. the Flatten code.
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
home_interaction_fraction = 0.05 # people are within 2m at home of a specific other person 5% of the time.

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
            #print(element,k)
          #print("NC:",needs_cols)
        else:
          for i in range(0,len(needs_cols)):
            self.needs[i,row_number-1] = int(row[needs_cols[i]])
        row_number += 1

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
num_infections_today = 0
num_hospitalisations_today = 0

def log_infection(t, x, y, loc_type):
  global num_infections_today
  out_inf = open("covid_out_infections.csv",'a')
  print("{},{},{},{}".format(t, x, y, loc_type), file=out_inf)
  num_infections_today += 1


class Person():
  def __init__(self, location, age):
    self.location = location # current location
    self.location.IncrementNumAgents()
    self.home_location = location

    self.status = "susceptible" # states: susceptible, exposed, infectious, recovered, dead.
    self.symptomatic = False # may be symptomatic if infectious
    self.status_change_time = -1

    self.age = age # age in years


  def plan_visits(self, e):
    personal_needs = needs.get_needs(self.age)
    for k,element in enumerate(personal_needs):
      nearest_locs = self.home_location.nearest_locations
      if nearest_locs[k]:
        location_to_visit = nearest_locs[k]
        location_to_visit.register_visit(e, self, element)

  def print_needs(self):
    print(self.age, needs.get_needs(self.age))

  def get_needs(self):
    return needs.get_needs(self.age)

  def infect(self, t, severity="exposed"):
    # severity can be overridden to infectious when rigidly inserting cases.
    # but by default, it should be exposed.
    self.status = severity
    self.status_change_time = t
    log_infection(t,self.location.x,self.location.y,"house")

  def progress_condition(self, t, disease):
    global num_hospitalisations_today
    if self.status == "exposed" and t-self.status_change_time > disease.incubation_period:
      self.status = "infectious"
      self.status_change_time = t
    if self.status == "infectious" and t-self.status_change_time > disease.recovery_period:
      self.status = "recovered"
      self.status_change_time = t
    if self.status == "infectious" and t-self.status_change_time == int(round(disease.period_to_hospitalisation-disease.incubation_period)):
      if random.random() < 0.06: #TODO: read from YML
        num_hospitalisations_today += 1
    if self.status == "infectious" and t-self.status_change_time == int(round(disease.mortality_period)):
      if random.random() < 0.0138:  
        self.status = "dead"
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
      self.agents.append(Person(self.house, random.randint(0,119)))

  def get_infectious_count(self):
    ic = 0
    for i in range(0,self.size):
      if self.agents[i].status == "infectious":
          ic += 1
    return 1

  def evolve(self, e, time, disease):
    ic = self.get_infectious_count()
    for i in range(0,self.size):
      if self.agents[i].status == "susceptible":
        if ic > 0:
          infection_chance = e.contact_rate_multiplier["house"] * disease.infection_rate * home_interaction_fraction * ic
          if random.random() < infection_chance:
            self.agents[i].status = "exposed"
            self.agents[i].status_change_time = time
            log_infection(time,self.house.x,self.house.y,"house")

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

  def evolve(self, e, time, disease):
    for hh in self.households:
      hh.evolve(e, time, disease)

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

    #for i in n:
    #  if i:  
    #    print(i.name, i.type)
    return n

  def add_infection(self, time): # used to preseed infections (could target using age later on)
    infection_pending = True
    while infection_pending:
      hh = random.randint(0, len(self.households)-1)
      p = random.randint(0, len(self.households[hh].agents)-1)
      if self.households[hh].agents[p].status == "susceptible": 
        # because we do pre-seeding we need to ensure we add exactly 1 infection.
        self.households[hh].agents[p].infect(time-5, severity="infectious")
        infection_pending = False

  def has_age(self, age):
    for hh in self.households:
      for a in hh.agents:
        if a.age == age:
          if a.status == "susceptible":
            return True
    return False

  def add_infection_by_age(self, time, age):
    for hh in self.households:
      for a in hh.agents:
        if a.age == age:
          if a.status == "susceptible":
            a.infect(time-5, severity="infectious")

class Location:
  def __init__(self, name, loc_type="park", x=0.0, y=0.0, sqm=400):

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

    #print(self.avg_visit_time)

  def DecrementNumAgents(self):
    self.numAgents -= 1

  def IncrementNumAgents(self):
    self.numAgents += 1

  def clear_visits(self):
    self.visits = []
    self.visit_minutes = 0 # total number of minutes of all visits aggregated.

  def register_visit(self, e, person, need):
    visit_time = self.avg_visit_time
    if person.status == "dead":
      visit_time = 0.0
    if person.status == "infectious":
      visit_time *= e.self_isolation_multiplier # implementing case isolation (CI)

    if visit_time > 0.0:
      visit_probability = need/(visit_time * 7) # = minutes per week / (average visit time * days in the week)
    else:
      return

    if random.random() < visit_probability:
      self.visits.append([person, visit_time])
      if person.status == "infectious":
        self.inf_visit_minutes += visit_time

  def evolve(self, e, verbose=True, ultraverbose=False):
    minutes_opened = 12*60
    for v in self.visits:
      if v[0].status == "susceptible":
        infection_probability = e.contact_rate_multiplier[self.type] * (e.disease.infection_rate/360.0) * (v[1] / minutes_opened) * (self.inf_visit_minutes / self.sqm)
        # For Covid-19 this should be 0.07 (infection rate) for 1 infectious person, and 1 susceptible person within 2m for a full day.
        # I assume they can do this in a 4m^2 area.
        # So 0.07 = x * (24*60/24*60) * (24*60/4) -> 0.07 = x * 360 -> x = 0.07/360 = 0.0002
        if ultraverbose:
          if infection_probability > 0.0:
            print(infection_probability, v[1], minutes_opened, self.inf_visit_minutes, self.sqm)
        if random.random() < infection_probability:
          v[0].status = "exposed"
          v[0].status_change_time = e.time
          if verbose:
            log_infection(e.time, self.x, self.y, self.type)


class Ecosystem:
  def __init__(self, duration):
    self.locations = {}
    self.houses = []
    self.house_names = []
    self.time = 0
    self.disease = None
    self.closures = {}
    self.validation = np.zeros(duration+1)
    self.contact_rate_multiplier = {}
    self.initialise_social_distance() # default: no social distancing.
    self.self_isolation_multiplier = 1.0
    self.work_from_home = False

    #Make header for infections file
    out_inf = open("covid_out_infections.csv",'w')
    print("#time,x,y,location_type", file=out_inf)

  def print_contact_rate(self, measure):
    print("Enacted measure:", measure)
    print("contact rate multipliers set to:")
    print(self.contact_rate_multiplier)

  def print_isolation_rate(self, measure):
    print("Enacted measure:", measure)
    print("isolation rate multipliers set to:")
    print(self.self_isolation_multiplier)

  def add_infections(self, num):
    """
    Randomly add an infection.
    """
    for i in range(0, num):
      house = random.randint(0, len(self.houses)-1)
      self.houses[house].add_infection(self.time)

  def add_infection(self, x, y, age, day):
    """
    Add an infection to the nearest person of that age.
    """
    selected_house = None
    min_dist = 99999
    print("add_infection:",x,y,age,len(self.houses))
    for h in self.houses:
      dist_h = calc_dist(h.x, h.y, x, y)
      if dist_h < min_dist:
        if h.has_age(age):
          selected_house = h
          min_dist = dist_h

    # Make sure that cases that are likely recovered 
    # already are not included.
    if day < -self.disease.recovery_period:
      day = -int(self.disease.recovery_period)
      
    selected_house.add_infection_by_age(day, age)

  def evolve(self):
    global num_infections_today
    global num_hospitalisations_today
    num_infections_today = 0
    num_hospitalisations_today = 0 

    # remove visits from the previous day
    for lk in self.locations.keys():
      for l in self.locations[lk]:
        l.clear_visits()

    # collect visits for the current day
    for h in self.houses:
      for hh in h.households:
        for a in hh.agents:
          a.plan_visits(self)
          a.progress_condition(self.time, self.disease)

    # process visits for the current day (spread infection).
    for lk in self.locations:
      if lk in self.closures:
        if self.closures[lk] < self.time:
          continue
      for l in self.locations[lk]:
        l.evolve(self)

    # process intra-household infection spread.
    for h in self.houses:
      h.evolve(self, self.time, self.disease)
    
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

  def add_closure(self, loc_type, time):
    self.closures[loc_type] = time

  def add_partial_closure(self, loc_type, fraction=0.8):
    needs.needs[lids[loc_type],:] *= (1.0 - fraction)

  def initialise_social_distance(self, contact_ratio=1.0): 
    for l in lids:
      self.contact_rate_multiplier[l] = contact_ratio
    self.contact_rate_multiplier["house"] = 1.0
    self.print_contact_rate("Reset to no measures")

  def reset_case_isolation(self):
    self.self_isolation_multiplier=1.0
    self.print_isolation_rate("Removing CI, now multiplier is {}".format(self.self_isolation_multiplier))

  def remove_social_distance(self):
    self.initialise_social_distance()
    if self.work_from_home:
      self.add_work_from_home(self.work_from_home_compliance)
    self.print_contact_rate("Removal of SD")

  def remove_all_measures(self):
    global needs
    self.initialise_social_distance()
    self.reset_case_isolation()
    needs = Needs("covid_data/needs.csv")

  def add_social_distance_imp9(self): # Add social distancing as defined in Imperial Report 0.
    # The default values are chosen to give a 75% reduction in social interactions,
    # as assumed by Ferguson et al., Imperial Summary Report 9, 2020.
    self.contact_rate_multiplier["hospital"] *= 0.25
    self.contact_rate_multiplier["leisure"] *= 0.25
    self.contact_rate_multiplier["shopping"] *= 0.25
    self.contact_rate_multiplier["park"] *= 0.25
    self.contact_rate_multiplier["supermarket"] *= 0.25
   
    # Values are different for three location types.
    # Setting values as described in Table 2, Imp Report 9. ("SD")
    self.contact_rate_multiplier["office"] *= 0.75
    self.contact_rate_multiplier["school"] *= 1.0
    self.contact_rate_multiplier["house"] *= 1.25
    self.print_contact_rate("SD (Imperial Report 9)")

  def add_work_from_home(self, compliance=0.75):
    self.contact_rate_multiplier["office"] *= 1.0 - compliance
    self.work_from_home = True
    self.work_from_home_compliance = compliance
    self.print_contact_rate("Work from home with {} compliance".format(compliance))

  def add_social_distance(self, distance=2, compliance=0.8571):
    dist_factor = (0.5 / distance)**2
    # 0.5 is seen as a rough border between intimate and interpersonal contact, 
    # based on proxemics (Edward T Hall).
    # The -2 exponent is based on the observation that particles move linearly in
    # one dimension, and diffuse in the two other dimensions.
    # gravitational effects are ignored, as particles on surfaces could still
    # lead to future contamination through surface contact.
    for l in lids:
      self.contact_rate_multiplier[l] *= dist_factor * compliance + (1.0-compliance)
    self.contact_rate_multiplier["house"] *= 1.25
    self.print_contact_rate("SD (covid_flee method) with distance {} and compliance {}".format(distance, compliance))

  def add_case_isolation(self, multiplier=0.475):
    # default value is derived from Imp Report 9.
    # 75% reduction is social contacts for 70 percent of the cases.
    # (0.75*0.7)+0.3
    self.self_isolation_multiplier=multiplier
    self.print_isolation_rate("CI with multiplier {}".format(multiplier))

  def print_needs(self):
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          print(k, a.get_needs())

  def print_status(self, outfile):
    out = None
    if self.time == 0:
      out = open(outfile,'w')
      print("#time,susceptible,exposed,infectious,recovered,dead,num infections today,num hospitalisations today,num hospitalisations today (data)",file=out)
    else:
      out = open(outfile,'a')
    status = {"susceptible":0,"exposed":0,"infectious":0,"recovered":0,"dead":0}
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          status[a.status] += 1
    print("{},{},{},{},{},{},{},{},{}".format(self.time,status["susceptible"],status["exposed"],status["infectious"],status["recovered"],status["dead"],num_infections_today,num_hospitalisations_today,self.validation[self.time]), file=out)


  def add_validation_point(self, time):
    self.validation[time] += 1

if __name__ == "__main__":
  print("No testing functionality here yet.")
