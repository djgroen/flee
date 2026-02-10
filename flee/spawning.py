from flee.SimulationSettings import SimulationSettings
import flee.demographics as demographics
import numpy as np
import flee.lib_math as lm
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


def refresh_spawn_weights(e):
    """
    Summary:
        Refreshes the spawn weights for all locations.
        This function needs to be called when
        SimulationSettings.spawn_rules["TakeFromPopulation"] is set to True.
        Also needed to model the ConflictSpawnDecay.
        It will update the weights to reflect the new population numbers.
    
    Args:
        e (Ecosystem): Ecosystem object

    Returns:
        None.
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

            if SimulationSettings.spawn_rules["starvation_driven_spawning"] is True:
                if "region_IPC_level" not in e.locations[i].attributes.keys():
                    print("ERROR: spawn_rules.starvation_driven_spawning is set in simulationsetting.yml, but no IPC input data (region_attributes_IPC.csv) has been loaded.", file=sys.stderr)
                    print(f"INFO: Error occurred for Location {a.location.name}, region {a.location.region}.", file=sys.stderr)
                    sys.exit()

                e.spawn_weights[i] = min(e.locations[i].pop, e.spawn_weights[i] + (e.locations[i].pop * e.locations[i].attributes["region_IPC_level"] / 100.0))


    e.spawn_weight_total = sum(e.spawn_weights)


def add_initial_refugees(e, d, loc):
  """
  Summary:
      Add the initial refugees to a location, using the location name
      
  Args:
      e (Ecosystem): Ecosystem object
      d (DataTable): DataTable object
      loc (Location): Location object
  
  Returns:
      None.
  """

  if SimulationSettings.spawn_rules["EmptyCampsOnDay0"] is True:
      return

  num_refugees = 0

  if SimulationSettings.spawn_rules["InsertDayZeroRefugeesInCamps"] is True:
      num_refugees += int(d.get_field(loc.name, 0, FullInterpolation=True))

  num_refugees += int(loc.attributes.get("initial_idps",0))
  for i in range(0, num_refugees):
      attributes = demographics.draw_samples(e, loc)
      attributes["connections"] = np.random.poisson(SimulationSettings.spawn_rules["AverageSocialConnectivity"])
      e.insertAgent(location=loc, attributes=attributes) # Parallelization is incorporated in the addAgent function.


@check_args_type
def spawn_daily_displaced(e, t, d):
    """
    Summary:
        spawn_daily_displaced is called once per day, and spawns new agents
        according to the rules specified in SimulationSettings.spawn_rules.
    Args:
        e (Ecosystem): Ecosystem object
        t (int): Time step
        d (DataTable): DataTable object
        refugees_raw = raw refugee count
        refugee_debt = number of refugees that could not be spawned due to rounding errors
    
    Returns:
        Tuple[int, int, int]: Tuple containing the number of new agents, 
        the raw refugee count, and the refugee debt.
    """
    global __refugees_raw, __refugee_debt

    new_refs = 0

    SumFromCamps = SimulationSettings.spawn_rules["sum_from_camps"]

    if SimulationSettings.spawn_rules["conflict_driven_spawning"] is True:

      for i in range(0, len(e.locations)):

        num_spawned = 0
        if e.locations[i].conflict > 0.0:
 
            ## BASE RATES  
            if SimulationSettings.spawn_rules["conflict_spawn_mode"] == "constant":
                num_spawned = int(float(SimulationSettings.spawn_rules["displaced_per_conflict_day"]) * float(e.locations[i].conflict))
                #if e.locations[i].conflict > 0.0:
                #    print(num_spawned, SimulationSettings.spawn_rules["displaced_per_conflict_day"], e.locations[i].conflict, file=sys.stderr)

            elif SimulationSettings.spawn_rules["conflict_spawn_mode"] == "pop_ratio":
                num_spawned = int(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].pop * e.locations[i].conflict)

            elif SimulationSettings.spawn_rules["conflict_spawn_mode"].lower() == "poisson":
                num_spawned = np.random.poisson(SimulationSettings.spawn_rules["displaced_per_conflict_day"] * e.locations[i].conflict)

        ## Doing the actual spawning here.
        for j in range(0, num_spawned):
            attributes = demographics.draw_samples(e, e.locations[i])
            attributes["connections"] = np.random.poisson(SimulationSettings.spawn_rules["AverageSocialConnectivity"])
            e.addAgent(location=e.locations[i], attributes=attributes) # Parallelization is incorporated in the addAgent function.

        new_refs += num_spawned


    elif SimulationSettings.spawn_rules["flood_driven_spawning"] is True:

      for i in range(0, len(e.locations)):

        num_spawned = 0
        flood_level = e.locations[i].attributes.get("flood_level",0.0)
        #print(e.time, e.locations[i].name, e.locations[i].attributes, file=sys.stderr)
        if flood_level > 0.0:
            print(e.time, e.locations[i].name, e.locations[i].attributes, lm.interp(SimulationSettings.spawn_rules["displaced_per_flood_day"], flood_level), file=sys.stderr)
            ## BASE RATES  
            if SimulationSettings.spawn_rules["flood_spawn_mode"] == "constant":
                num_spawned = int(lm.interp(SimulationSettings.spawn_rules["displaced_per_flood_day"], flood_level)) 

            elif SimulationSettings.spawn_rules["flood_spawn_mode"] == "pop_ratio":
                num_spawned = int(lm.interp(SimulationSettings.spawn_rules["displaced_per_flood_day"], flood_level) * e.locations[i].pop)
    
            elif SimulationSettings.spawn_rules["flood_spawn_mode"].lower() == "poisson":
                num_spawned = np.random.poisson(int(lm.interp(SimulationSettings.spawn_rules["displaced_per_flood_day"], flood_level)))

        ## Doing the actual spawning here.
        for j in range(0, num_spawned):
            attributes = demographics.draw_samples(e, e.locations[i])
            attributes["connections"] = np.random.poisson(SimulationSettings.spawn_rules["AverageSocialConnectivity"])
            e.addAgent(location=e.locations[i], attributes=attributes) # Parallelization is incorporated in the addAgent function.

        new_refs += num_spawned


    else:

      # Determine number of new refugees to insert into the system.
      new_refs = d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=SumFromCamps) - __refugee_debt
      __refugees_raw += d.get_daily_difference(t, FullInterpolation=True, SumFromCamps=SumFromCamps)

      #Refugees are pre-placed in Mali, so set new_refs to 0 on Day 0.
      if SimulationSettings.spawn_rules["InsertDayZeroRefugeesInCamps"]:
        if t == 0:
          new_refs = 0
          #__refugees_raw = 0

          for l in e.locations:
              #print(l.name, l.capacity, d.day0pops.get(l.name,0),  file=sys.stderr)
              if l.capacity > 0 :
                  l.capacity -= int(float(d.day0pops.get(l.name,0)))
              #print(l.name, l.capacity, file=sys.stderr)


      if new_refs < 0:
        __refugee_debt = -new_refs
        new_refs = 0
      elif __refugee_debt > 0:
        __refugee_debt = 0

      #Insert refugee agents
      locs = e.pick_spawn_locations(new_refs)
      for i in range(0, new_refs):
        attributes = demographics.draw_samples(e, locs[i])
        attributes["connections"] = np.random.poisson(SimulationSettings.spawn_rules["AverageSocialConnectivity"])
        e.addAgent(location=locs[i], attributes=attributes) 

    return new_refs, __refugees_raw, __refugee_debt


def spawn_agents(e, number):
    """
    Summary:
        Spawn a given number of agents at random locations.
    
    Args:
        e (Ecosystem): Ecosystem object
        number (int): Number of agents to spawn

    Returns:
        None.
    """
    #Insert refugee agents
    for i in range(0, number):
        loc = e.pick_spawn_location()
        attributes = demographics.draw_samples(e, loc)
        attributes["connections"] = np.random.poisson(SimulationSettings.spawn_rules["AverageSocialConnectivity"])
        e.addAgent(location=loc, attributes=attributes) 

