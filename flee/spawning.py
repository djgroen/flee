from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable
from flee.SimulationSettings import SimulationSettings
import numpy as np
import sys
import os
import pandas as pd
import glob

from typing import List, Optional, Tuple

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


__refugees_raw = 0
__refugee_debt = 0

__demographics = {}


def refresh_spawn_weights(e):
    """
    This function needs to be called when
    SimulationSettings.spawn_rules["TakeFromPopulation"] is set to True.
    Also needed to model the ConflictSpawnDecay.
    It will update the weights to reflect the new population numbers.
    """

    conflict_spawning_only = True
    pop_weight = 1.0
    attribute_weights = {}


    for i in range(0, len(e.locations)):

        if conflict_spawning_only and e.locations[i].conflict == False:
            e.spawn_weights[i] = 0.0
            continue

        # Conflict decay multiplier
        multiplier = 1.0
        if SimulationSettings.spawn_rules["conflict_spawn_decay"]:
            multiplier = SimulationSettings.get_location_conflict_decay(e.time, e.locations[i])

        # Pop+conflict weight
        e.spawn_weights[i] = e.locations[i].pop * pop_weight * multiplier


    e.spawn_weight_total = sum(e.spawn_weights)



def read_demographic_csv(e, csvname):
  """
  Attribute CSV files have the following format:
  Value,Default,LocA,LocB,...
  ValueA,weight for that value by Default, ...
  """
  attribute = (csvname.split('/')[1].split('.')[0]).split('_')[1]

  if not os.path.exists(csvname):
      return

  df = pd.read_csv(csvname)

  if SimulationSettings.log_levels["init"] > -1:
    print("INFO: ", attribute, " attributes loaded, with columns:", df.columns, file=sys.stderr)
  
  __demographics[attribute] = df


def read_demographics(e):
  if not os.path.exists("input_csv"):
      return

  csv_list = glob.glob("input_csv/demographics_*.csv")

  for csvname in csv_list:
      read_demographic_csv(e, csvname)
  


def draw_sample(e, loc, attribute):
  #print(__demographics[attribute], file=sys.stderr)
  #print(__demographics[attribute].iloc[0]['Default'], file=sys.stderr)

  if attribute in __demographics:
    if loc.name in __demographics[attribute].columns:
      a = __demographics[attribute].sample(n=1,weights=loc)
    else:
      a = __demographics[attribute].sample(n=1,weights='Default')
  else:
    return -1

  return a.iloc[0][attribute]


def draw_samples(e,loc):
    """
    Draw samples from all optional attributes, except age and gender (which are always provided).
    """
    samples = {}
    for a in __demographics.keys():
        if a == "age" or a == "gender":
            continue
        else:
            samples[a] = draw_sample(e, loc, a)
    return samples


def add_initial_refugees(e, d, loc):
  """ Add the initial refugees to a location, using the location name"""

  # Only initialize demographics when first called.
  if len(__demographics) == 0:
      read_demographics(e)


  if SimulationSettings.spawn_rules["InsertDayZeroRefugeesInCamps"]:
      num_refugees = int(d.get_field(loc.name, 0, FullInterpolation=True))
      for i in range(0, num_refugees):
          age = draw_sample(e, loc, 'age')
          gender = draw_sample(e, loc, 'gender')
          attributes = draw_samples(e, loc)
          e.addAgent(location=loc, age=age, gender=gender, attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.


def spawn_daily_displaced(e, t, d):
    global __refugees_raw, __refugee_debt
    """
    t = time
    e = Ecosystem object
    d = DataTable object
    refugees_raw = raw refugee count
    """

    if SimulationSettings.spawn_rules["conflict_driven_spawning"]:

      for i in range(0, len(e.locations)):
 
        ## BASE RATES  
        if SimulationSettings.spawn_rules["conflict_spawn_mode"] == "constant":
            num_spawned = SimulationSettings.spawn_rules["displaced_per_conflict_day"]

        elif SimulationSettings.spawn_rules["conflict_spawn_mode"] == "pop_ratio":
            if e.locations[i].conflict:  
                num_spawned = int(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].pop)
            else: 
                num_spawned = 0

        elif SimulationSettings.spawn_rules["conflict_spawn_mode"].lower() == "Poisson":
            if e.locations[i].conflict:  
                num_spawned = np.random.poisson(SimulationSettings.spawn_rules["displaced_per_conflict_day"])
            else: 
                num_spawned = 0

        ## Doing the actual spawning here.
        for j in range(0, num_spawned):
            age = draw_sample(e, e.locations[i], 'age')
            gender = draw_sample(e, e.locations[i], 'gender')
            attributes = draw_samples(e, loc)
            e.addAgent(location=e.locations[i], age=age, gender=gender, attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.

    else:

      # Determine number of new refugees to insert into the system.
      new_refs = d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=False) - __refugee_debt
      __refugees_raw += d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=False)

      #Refugees are pre-placed in Mali, so set new_refs to 0 on Day 0.
      if SimulationSettings.spawn_rules["InsertDayZeroRefugeesInCamps"]:
        if t == 0:
          new_refs = 0
          #refugees_raw = 0

      if new_refs < 0:
        __refugee_debt = -new_refs
        new_refs = 0
      elif __refugee_debt > 0:
        __refugee_debt = 0

      #Insert refugee agents
      for i in range(0, new_refs):
        loc = e.pick_spawn_location()
        age = draw_sample(e, loc, 'age')
        gender = draw_sample(e, loc, 'gender')
        attributes = draw_samples(e, loc)
        e.addAgent(location=loc, age=age, gender=gender, attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.

    return new_refs, __refugees_raw, __refugee_debt
