import random
import numpy as np

class SimulationSettings:
  Softening = 0.0 # Offset added to distance calculation to lighten distance-based weighting.
  UseForeign = True # Foreign countries have double weights.
  TurnBackAllowed = True # Refugees can flee from A to B, and then back to A.
  AgentLogLevel = 0 # Higher is mode verbosity.
  InitLogLevel  = 0 # set to 1 for basic information on locations added and conflict zones assigned.
  TakeRefugeesFromPopulation = False
  EnableConstrainedMoveSpeed = False #Impose limited movespeed. Otherwise agents traverse one link per iteration.
  MoveSpeed = 100.0 # Move speed in kilometers per iteration (typically a day).


class Person:
  def __init__(self, location):
    self.health = 1

    self.injured = 0
    
    self.age = 35
    self.location = location
    self.home_location = location
    self.location.numAgents += 1

    # Set to true when an agent resides on a link.
    self.travelling = False

    if not SimulationSettings.TurnBackAllowed:
      self.last_location = None

    if SimulationSettings.AgentLogLevel > 0:
      self.distance_travelled = 0
      self.places_travelled = 1

    if SimulationSettings.EnableConstrainedMoveSpeed:
      self.distance_remaining_on_link = 0
      self.move_speed = SimulationSettings.MoveSpeed

  def evolve(self):
    if self.travelling == False:
      movechance = self.location.movechance
      outcome = random.random()
      if outcome < movechance:
        # determine here which route to take?
        chosenRoute = self.selectRoute()

        # if there is a viable route to a different location.
        if chosenRoute >= 0:
          # update location to link endpoint
          self.location.numAgents -= 1
          self.location = self.location.links[chosenRoute]
          self.location.numAgents += 1
          self.travelling = True

          if SimulationSettings.EnableConstrainedMoveSpeed:
            # With movespeeds enabled, we set the distance remaining initially to the length of the link.
            self.distance_remaining_on_link = self.location.links[chosenRoute].distance

  def finish_travel(self):
    if self.travelling:
      
      if SimulationSettings.EnableConstrainedMoveSpeed:      
        self.distance_remaining_on_link -= self.move_speed

        # In this case, the agent stays on the link, and travel is not finished.
        if self.distance_remaining_on_link > 0.0:
          return

        # In this case, we set the remaining distance to exactly 0 and continue finishing travel.
        else:
          self.distance_remaining_on_link = 0

      # update last location of agent.
      if not SimulationSettings.TurnBackAllowed:
        self.last_location = self.location

      # update agent logs
      if SimulationSettings.AgentLogLevel > 0:
        self.places_travelled += 1
        self.distance_travelled += self.location.distance

      # update location (which is on a link) to link endpoint
      self.location.numAgents -= 1
      self.location = self.location.endpoint
      self.location.numAgents += 1
      self.travelling = False
      
  def selectRoute(self):
    total_score = 0.0
    for i in range(0,len(self.location.links)):
      # forced redirection: if this is true for a link, return its value immediately.
      if self.location.links[i].forced_redirection == True:
        return i

      # If turning back is NOT allowed, remove weight from the last location.
      if not SimulationSettings.TurnBackAllowed:
        if self.location.links[i].endpoint == self.last_location:
          total_score += 0
          continue

      # else, use the normal algorithm.
      if self.location.links[i].endpoint.isFull(self.location.links[i].numAgents):
        total_score += 0
      else:
        weight = 1.0
        if SimulationSettings.UseForeign == True and self.location.links[i].endpoint.foreign == True:
          weight = 2.0
        total_score += weight / (SimulationSettings.Softening + self.location.links[i].distance)


    selected_value = random.random() * total_score

    checked_score = 0.0
    for i in range(0,len(self.location.links)):
      if(self.location.links[i].endpoint.isFull(self.location.links[i].numAgents)):
        checked_score += 0
      else:
        weight = 1.0
        if SimulationSettings.UseForeign == True and self.location.links[i].endpoint.foreign == True:
          weight = 2.0
        checked_score += weight / (SimulationSettings.Softening + self.location.links[i].distance)
        if selected_value < checked_score:
          return i

    return -1

class Location:
  def __init__(self, name, x=0.0, y=0.0, movechance=0.001, capacity=-1, pop=0, foreign=False):
    self.name = name
    self.x = x
    self.y = y
    self.movechance = movechance
    self.links = [] # paths connecting to other towns
    self.numAgents = 0 # refugee population
    self.capacity = capacity # refugee capacity
    self.pop = pop # non-refugee population
    self.foreign = foreign

  def isFull(self, numOnLink):
    """ Checks whether a given location has reached full capacity. In this case it will no longer admit persons."""
    if self.capacity < 0:
      return False
    elif self.numAgents + numOnLink >= self.capacity:
      return True
    return False

class Link:
  def __init__(self, endpoint, distance, forced_redirection=False):

    # distance in km.
    self.distance = float(distance)

    # links for now always connect two endpoints
    self.endpoint = endpoint

    # number of agents that are in transit.
    self.numAgents = 0

    # if True, then all Persons will go down this link.
    self.forced_redirection = forced_redirection

class Ecosystem:
  def __init__(self):
    self.locations = []
    self.locationNames = []
    self.agents = []
    self.time = 0

    # Bring conflict zone management into FLEE.
    self.conflict_zones = []
    self.conflict_weights = np.array([])
    self.conflict_pop = 0


  def add_conflict_zone(self, name, change_movechance=True):
    """
    Adds a conflict zone. Default weight is equal to population of the location.
    """
    for i in range(0, len(self.locationNames)):
      if self.locationNames[i] is name:
        if change_movechance:
          self.locations[i].movechance = 1.0
        self.conflict_zones += [self.locations[i]]
        self.conflict_weights = np.append(self.conflict_weights, [self.locations[i].pop])
        self.conflict_pop = sum(self.conflict_weights)
        if SimulationSettings.InitLogLevel > 0:
          print("Added conflict zone:", name, ", pop. ", self.locations[i].pop)
          print("New total pop. in conflict zones: ", self.conflict_pop) 
        return
    
    print("ERROR in flee.add_conflict_zone: location with name ", name, " appears not to exist in the FLEE ecosystem.")
    print("Existing locations include: ", self.locationNames)
  

  def remove_conflict_zone(self, name):
    """
    Shorthand function to remove a conflict zone from the list.
    (not used yet)
    """
    new_conflict_zones = []
    new_weights = np.array([])

    for i in range(0, len(self.conflict_zones)):
      if conflict_zones[i].name is not name:
        new_conflict_zones += [self.conflict_zones[i]]
        new_weights = np.append(new_weights, [self.conflict_weights[i]])

    self.conflict_zones = new_conflict_zones
    self.conflict_weights =  new_weights
    self.conflict_pop = sum(self.conflict_weights)


  def pick_conflict_location(self):
    """
    Returns a weighted random element from the list of conflict locations.
    This function returns a number, which is an index in the array of conflict locations.
    """
    return np.random.choice(self.conflict_zones, p=self.conflict_weights/self.conflict_pop)


  def refresh_conflict_weights(self):
    """
    This function needs to be called when SimulationSettings.TakeRefugeesFromPopulation is set to True.
    It will update the weights to reflect the new population numbers.
    """
    for i in range(0,len(self.conflict_zones)):
      self.conflict_weights[i] = self.conflict_zones[i].pop
    self.conflict_pop = sum(self.conflict_weights)


  def evolve(self):
    #update agent locations
    for a in self.agents:
      a.evolve()

    for a in self.agents:
      a.finish_travel()

    #update link properties

    self.time += 1

  def addLocation(self, name, x="0.0", y="0.0", movechance=0.1, capacity=-1, pop=0, foreign=False):
    l = Location(name, x, y, movechance, capacity, pop, foreign)
    if SimulationSettings.InitLogLevel > 0:
      print("Location:", name, x, y, movechance, capacity, ", pop. ", pop, foreign)
    self.locations.append(l)
    self.locationNames.append(l.name)
    return l
   

  def addAgent(self, location):
    if SimulationSettings.TakeRefugeesFromPopulation:
      if location.pop > 0:
        location.pop -= 1
    self.agents.append(Person(location))

  def numAgents(self):
    return len(self.agents)

  def linkUp(self, endpoint1, endpoint2, distance="1.0", forced_redirection=False):
    """ Creates a link between two endpoint locations
    """
    endpoint1_index = 0
    endpoint2_index = 0
    for i in range(0, len(self.locationNames)):
      if(self.locationNames[i] == endpoint1):
        endpoint1_index = i
      if(self.locationNames[i] == endpoint2):
        endpoint2_index = i


    self.locations[endpoint1_index].links.append( Link(self.locations[endpoint2_index], distance, forced_redirection) )
    self.locations[endpoint2_index].links.append( Link(self.locations[endpoint1_index], distance) )


  def printInfo(self):

    print("Time: ", self.time, ", # of agents: ", len(self.agents))
    for l in self.locations:
      print(l.name, l.numAgents)


if __name__ == "__main__":
  print("Flee, prototype version.")

  end_time = 50
  e = Ecosystem()

  l1 = e.addLocation("Source")
  l2 = e.addLocation("Sink1")
  l3 = e.addLocation("Sink2")

  e.linkUp("Source","Sink1","10.0")
  e.linkUp("Source","Sink2","5.0")

  for i in range(0,100):
    e.addAgent(location=l1)

  for t in range(0,end_time):
    e.evolve()
    e.printInfo()
    
