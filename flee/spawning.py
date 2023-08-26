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


def getAttributeRatio(location, attribute):
    return 1.0

def refresh_spawn_weights(e):
    """
    This function needs to be called when
    SimulationSettings.spawn_rules["TakeFromPopulation"] is set to True.
    Also needed to model the ConflictSpawnDecay.
    It will update the weights to reflect the new population numbers.
    """

    conflict_pop_weight = 1.0
    attribute_weights = {} #TODO: Implement (food security stretch goal)


    for i in range(0, len(e.locations)):

        # First reset weight to 0.0.
        e.spawn_weights[i] = 0.0

        # Conflict-driven spawning
        if not SimulationSettings.spawn_rules["conflict_driven_spawning"]: # This branch should be skipped if conflicts spawn fixed numbers of agents.

            if SimulationSettings.spawn_rules["conflict_zone_spawning_only"]: # This option reduces spawning to 0 in non-conflict zones.
                if e.locations[i].conflict <= 0.0:
                    continue

            if e.locations[i].conflict > 0.0: # Adding conflict-based weighting for spawning.
                # Conflict decay multiplier
                multiplier = e.locations[i].conflict
                if SimulationSettings.spawn_rules["conflict_spawn_decay"]:
                    multiplier = e.locations[i].conflict * SimulationSettings.get_location_conflict_decay(e.time, e.locations[i])

                # Pop+conflict weight
                e.spawn_weights[i] = e.locations[i].pop * conflict_pop_weight * multiplier


    e.spawn_weight_total = sum(e.spawn_weights)



def read_demographic_csv(e, csvname):
  """
  Attribute CSV files have the following format:
  Value,Default,LocA,LocB,...
  ValueA,weight for that value by Default, ...
  """
  attribute = (csvname.split(os.sep)[1].split('.')[0]).split('_')[1]

  if not os.path.exists(csvname):
      return

  df = pd.read_csv(csvname)

  if SimulationSettings.log_levels["init"] > -1:
    print("INFO: ", attribute, " attributes loaded, with columns:", df.columns, file=sys.stderr)
  
  __demographics[attribute] = df


def read_demographics(e):
  if not os.path.exists("input_csv"):
      return

  csv_list = glob.glob(os.path.join("input_csv","demographics_*.csv"))

  for csvname in csv_list:
      read_demographic_csv(e, csvname)
  


def draw_sample(e, loc, attribute):
  #print(__demographics[attribute], file=sys.stderr)
  #print(__demographics[attribute].iloc[0]['Default'], file=sys.stderr)

  if attribute in __demographics:
    if loc.name in __demographics[attribute].columns:
      a = __demographics[attribute].sample(n=1,weights=loc.name)
    else:
      a = __demographics[attribute].sample(n=1,weights='Default')
  else:
    return -1

  return a.iloc[0][attribute]


def draw_samples(e,loc):
    """
    Draw samples from all optional attributes.
    """
    samples = {}
    for a in __demographics.keys():
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
          attributes = draw_samples(e, loc)
          e.addAgent(location=loc, attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.


def spawn_daily_displaced(e, t, d, SumFromCamps=False):
    global __refugees_raw, __refugee_debt
    """
    t = time
    e = Ecosystem object
    d = DataTable object
    refugees_raw = raw refugee count
    """
    new_refs = 0

    if SimulationSettings.spawn_rules["conflict_driven_spawning"] is True:

      for i in range(0, len(e.locations)):

        num_spawned = 0
        if e.locations[i].conflict > 0.0:
 
            ## BASE RATES  
            if SimulationSettings.spawn_rules["conflict_spawn_mode"] == "constant":
                num_spawned = int(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].conflict)

            elif SimulationSettings.spawn_rules["conflict_spawn_mode"] == "pop_ratio":
                num_spawned = int(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].pop * e.locations[i].conflict)

            elif SimulationSettings.spawn_rules["conflict_spawn_mode"].lower() == "poisson":
                num_spawned = np.random.poisson(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].conflict)

        ## Doing the actual spawning here.
        for j in range(0, num_spawned):
            attributes = draw_samples(e, e.locations[i])
            e.addAgent(location=e.locations[i], attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.

        new_refs = num_spawned


    elif SimulationSettings.spawn_rules["flood_driven_spawning"] is True:

      for i in range(0, len(e.locations)):

        num_spawned = 0
    
        if e.locations[i].attributes["flood_level"] > 0:
            ## BASE RATES  
            if SimulationSettings.spawn_rules["flood_spawn_mode"] == "constant":
                num_spawned = int(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].conflict)

            elif SimulationSettings.spawn_rules["flood_spawn_mode"] == "pop_ratio":
                num_spawned = int(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].pop * e.locations[i].conflict)
    
            elif SimulationSettings.spawn_rules["flood_spawn_mode"].lower() == "poisson":
                num_spawned = np.random.poisson(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].conflict)

        ## Doing the actual spawning here.
        for j in range(0, num_spawned):
            attributes = draw_samples(e, e.locations[i])
            e.addAgent(location=e.locations[i], attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.

        new_refs = num_spawned


    else:

      # Determine number of new refugees to insert into the system.
      new_refs = d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=SumFromCamps) - __refugee_debt
      __refugees_raw += d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=SumFromCamps)

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
        attributes = draw_samples(e, loc)
        e.addAgent(location=loc, attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.

    return new_refs, __refugees_raw, __refugee_debt


def spawn_agents(e, number):

    #Insert refugee agents
    for i in range(0, number):
        loc = e.pick_spawn_location()
        attributes = draw_samples(e, loc)
        e.addAgent(location=loc, attributes=attributes) # Parallelization is incorporated *inside* the addAgent function.

