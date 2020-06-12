# micro_flee.py
# sequential microscale model.
import numpy as np
import sys
import random
from flee import SimulationSettings
from flee import flee


class Person(flee.Person):
  def __init__(self, location):
    super().__init__(location)

  def evolve(self):
    super().evolve()


class Location(flee.Location):
  def __init__(self, cur_id, name, x=0.0, y=0.0, movechance=0.001, capacity=-1, pop=0, foreign=False, country="unknown"):
    super().__init__(name, x, y, movechance, capacity, pop, foreign, country)
    self.marker = False
    
    if isinstance(movechance, str):
      if "marker" in movechance.lower():
        self.movechance = 1.0
        self.marker= True
      else:
        print("Error in creating Location() object: cannot parse movechance value of ", movechance, " for location object with name ", name, ".")


class Link(flee.Link):
  def __init__(self, endpoint, distance, link_type="drive", forced_redirection=False):
    super().__init__(endpoint, distance, forced_redirection)
    self.link_type = link_type
    self.speed = speed

    if islink(link_type, str):
      if "drive" in link_type.lower():
        self.speed = SimulationSettings.MaxMoveSpeed
      elif "walk" in link_type.lower():
        self.speed = SimulationSettings.MaxWalkSpeed
      elif "crossing" in link_type.lower():
        self.speed = SimulationSettings.MaxCrossingSpeed
      else:
        print("Error in identifying link_type() object: cannot parse the type of link ", link_type, " for location object with name ", name, ".")

        
class Ecosystem(flee.Ecosystem):
  def __init__(self):
    super().__init__()

  def evolve(self):
    super().evolve()


if __name__ == "__main__":
  print("No testing functionality here yet.")
