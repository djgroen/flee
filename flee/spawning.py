from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable
from flee.SimulationSettings import SimulationSettings
import numpy as np
import sys
import os
import pandas as pd

__refugees_raw = 0
__refugee_debt = 0

__demographics = {}


def refresh_conflict_spawn_weights(e):
    """
    This function needs to be called when
    SimulationSettings.spawn_rules["TakeFromPopulation"] is set to True.
    Also needed to model the ConflictSpawnDecay.
    It will update the weights to reflect the new population numbers.
    """
    for i in range(0, len(e.conflict_zones)):
        multiplier = 1.0
        if SimulationSettings.spawn_rules["conflict_spawn_decay"]:
            time_since_conflict = e.time - e.conflict_zones[i].time_of_conflict
            multiplier = SimulationSettings.get_conflict_decay(time_since_conflict)

        e.conflict_spawn_weights[i] = e.conflict_zones[i].pop * multiplier
    e.conflict_pop = sum(e.conflict_spawn_weights)



def read_demographic_csv(e, csvname):
  """
  Attribute CSV files have the following format:
  Value,Default,LocA,LocB,...
  ValueA,weight for that value by Default, ...
  """
  attribute = (csvname.split('.')[0]).split('_')[1]

  if not os.path.exists("input_csv/{}".format(csvname)):
      return

  df = pd.read_csv("input_csv/{}".format(csvname))

  if SimulationSettings.log_levels["init"] > 0:
    print("INFO: ", attribute, " attributes loaded, with columns:", file=sys.stderr)
    for col in df.columns:
      print(col, file=sys.stderr)
  
  __demographics[attribute] = df


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


def add_initial_refugees(e, d, loc):
  """ Add the initial refugees to a location, using the location name"""

  read_demographic_csv(e, 'demographics_age.csv')


  if SimulationSettings.spawn_rules["InsertDayZeroRefugeesInCamps"]:
    num_refugees = int(d.get_field(loc.name, 0, FullInterpolation=True))
    for i in range(0, num_refugees):
      age = draw_sample(e, loc, 'age')
      e.addAgent(location=loc, age=age, gender=np.random.random_integers(0,1), attributes={}) # Parallelization is incorporated *inside* the addAgent function.


def spawn_daily_displaced(e, t, d):
    global __refugees_raw, __refugee_debt
    """
    t = time
    e = Ecosystem object
    d = DataTable object
    refugees_raw = raw refugee count
    """

    if SimulationSettings.spawn_rules["conflict_driven_spawning"]:

      for i in range(0, len(e.conflict_zones)):
 
        ## BASE RATES  
        if SimulationSettings.spawn_rules["conflict_spawn_mode"] == "constant":
          num_spawned = SimulationSettings.spawn_rules["displaced_per_conflict_day"]

        elif SimulationSettings.spawn_rules["conflict_spawn_mode"] == "pop_ratio":
          num_spawned = int(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.conflict_zones[i].pop)

        elif SimulationSettings.spawn_rules["conflict_spawn_mode"].lower() == "Poisson":
          num_spawned = np.random.poisson(SimulationSettings.spawn_rules["displaced_per_conflict_day"])

        ## Doing the actual spawning here.
        for j in range(0, num_spawned):
          age = draw_sample(e, loc, 'age')
          e.addAgent(location=loc, age=age, gender=np.random.random_integers(0,1), attributes={}) # Parallelization is incorporated *inside* the addAgent function.

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
        e.addAgent(location=e.pick_conflict_location(), age=np.random.random_integers(1,90), gender=np.random.random_integers(0,1), attributes={}) # Parallelization is incorporated *inside* the addAgent function.

    return new_refs, __refugees_raw, __refugee_debt
