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


class Link(flee.Link):
  def __init__(self, endpoint, distance, link_type="drive", forced_redirection=False):
    super().__init__(endpoint, distance, forced_redirection)
    self.link_type = link_type


class Ecosystem(flee.Ecosystem):
  def __init__(self):
    super().__init__()

  def evolve(self):
    super().evolve()


if __name__ == "__main__":
  print("No testing functionality here yet.")
