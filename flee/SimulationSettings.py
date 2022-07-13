import csv
import sys
import yaml
import os

# pylint: skip-file

from typing import List, Optional, Tuple

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


@check_args_type
def fetchss(dataset,name: str,default):

    if dataset is None:
        return default

    if(name in dataset):
        return dataset[name]
    else:
        return default


class SimulationSettings:
    """
    The SimulationSettings class
    """

    log_levels = {} #log level variables
    spawn_rules = {} # ABM spawning rules
    move_rules = {} # ABM movement rules
    optimisations = {} # Settings to improve runtime performance

    sqrt_ten = 3.16227766017  # square root of ten (10^0.5).


    @check_args_type
    def get_conflict_decay(time_since_conflict: int):

        spawn_len = len(SimulationSettings.spawn_rules["conflict_spawn_decay"])

        if spawn_len < 1:
            print("Warning: no conflict spawn decay set. Defaulting to no decay", file=sys.stderr)
            return 1.0
        else:
            i = min(int(time_since_conflict / 30), spawn_len-1)
            if SimulationSettings.log_levels["conflict"] > 0:
              print("Conflict zone spawn status: time elapsed {}, decay factor {}".format(time_since_conflict, float(SimulationSettings.spawn_rules["conflict_spawn_decay"][i])), file=sys.stderr)
            return float(SimulationSettings.spawn_rules["conflict_spawn_decay"][i])


    @check_args_type
    def get_location_conflict_decay(time: int, loc):
        """

        time: e.time (time in simulation)
        loc: location for which to calculate the decay multiplier.
        """
        time_since_conflict = time - loc.time_of_conflict
        multiplier = SimulationSettings.get_conflict_decay(time_since_conflict)
        return multiplier


    @check_args_type
    def ReadFromYML(ymlfile: str):

        print("YAML file:", ymlfile, file=sys.stderr)
        with open(ymlfile) as f:
            dp = yaml.safe_load(f)

        number_of_steps = float(fetchss(dp,"number_of_steps",-1))
        SimulationSettings.FlareConflictInputFile = fetchss(dp,"conflict_input_file","")

        print("YAML:", dp, file=sys.stderr)

        dpll = fetchss(dp,"log_levels",None)

        SimulationSettings.log_levels["agent"] = int(fetchss(dpll,"agent",0))
        # set to 1 to obtain average times for agents to reach camps at any time
        # step (aggregate info).
        SimulationSettings.log_levels["camp"] = int(fetchss(dpll,"camp",0))
        # set to 1 for basic information on locations added and conflict zones
        # assigned.
        SimulationSettings.log_levels["init"] = int(fetchss(dpll,"init",0))
        # set to 1 for information on conflict zone spawning
        SimulationSettings.log_levels["conflict"] = int(fetchss(dpll,"conflict",0))



        dps = fetchss(dp,"spawn_rules",None)

        # Spawned agents are subtracted from populations. This can lead to crashes if the number of spawned agents
        # exceeds the total population in conflict zones.
        print("Take from population?", fetchss(dps,"take_from_population","false"), file=sys.stderr)

        SimulationSettings.spawn_rules["TakeFromPopulation"] = bool(fetchss(dps, "take_from_population", False))
        # Advanced settings
        SimulationSettings.spawn_rules["InsertDayZeroRefugeesInCamps"] = bool(fetchss(dps, "insert_day0", True))


        dpsc = fetchss(dps,"conflict_driven_spawning",None)
        if dpsc is not None:
          SimulationSettings.spawn_rules["conflict_driven_spawning"] = True
          
          SimulationSettings.spawn_rules["conflict_spawn_mode"] = fetchss(dpsc,"spawn_mode","constant") # constant, Poisson, pop_ratio

          if SimulationSettings.spawn_rules["conflict_spawn_mode"] == "pop_ratio":
            SimulationSettings.spawn_rules["displaced_per_conflict_day"] = float(fetchss(dpsc,"displaced_per_conflict_day", 0.01))
          else:
            SimulationSettings.spawn_rules["displaced_per_conflict_day"] = int(fetchss(dpsc,"displaced_per_conflict_day", 500))
        else:
          SimulationSettings.spawn_rules["conflict_driven_spawning"] = False

        SimulationSettings.spawn_rules["conflict_spawn_decay"] = fetchss(dps,"conflict_spawn_decay", None) # Expect an array or dict
        print("Spawn decay set to:", SimulationSettings.spawn_rules["conflict_spawn_decay"], file=sys.stderr)


        dpr = fetchss(dp,"move_rules",None)

        # most number of km that we expect refugees to traverse per time step (30
        # km/h * 12 hours).
        SimulationSettings.move_rules["MaxMoveSpeed"] = float(fetchss(dpr,"max_move_speed", 360.0))
        
        # most number of km that we expect refugees to traverse per time step on
        # foot (3.5 km/h * 10 hours).
        SimulationSettings.move_rules["MaxWalkSpeed"] = float(fetchss(dpr,"max_walk_speed", 35.0))

        # most number of km that we expect refugees to traverse per time step on
        # boat/walk to cross river (2 km/h * 10 hours).
        SimulationSettings.move_rules["MaxCrossingSpeed"] = float(fetchss(dpr,"max_crossing_speed", 20.0))


        SimulationSettings.move_rules["CampWeight"] = float(fetchss(dpr,"camp_weight", 1.0)) # attraction multiplier for camps.
        SimulationSettings.move_rules["ConflictWeight"] = float(fetchss(dpr,"conflict_weight", 1.0 / SimulationSettings.sqrt_ten)) #attraction multiplier for source zones (conflict zones)


        SimulationSettings.move_rules["ConflictMoveChance"] = float(fetchss(dpr,"conflict_movechance", 1.0)) # chance of persons leaving a conflict zone per day.
        SimulationSettings.move_rules["CampMoveChance"] = float(fetchss(dpr,"camp_movechance", 0.001)) # chance of persons leaving a camp.
        SimulationSettings.move_rules["DefaultMoveChance"] = float(fetchss(dpr,"default_movechance", 0.3)) # chance of persons leaving a regular location per day.
        

        SimulationSettings.move_rules["AwarenessLevel"] = float(fetchss(dpr,"awareness_level", 1)) # awareness of locations X link steps away by agents.
        # -1, no weighting at all, 0 = road only, 1 = location, 2 = neighbours, 3 = region.
       
        # A location or camp is considered full if the number of agents there exceeds (capacity OR pop) * CapacityBuffer.
        SimulationSettings.move_rules["CapacityBuffer"] = float(fetchss(dpr,"capacity_buffer", 1.0)) # awareness of locations X link steps away by agents.

        # Displaced people will not take a break unless they at least travelled
        # for a full day's distance in the last two days.
        SimulationSettings.move_rules["AvoidShortStints"] = fetchss(dpr,"avoid_short_stints","false").lower() == "true"
      
        # Agents traverse first link on foot.
        SimulationSettings.move_rules["StartOnFoot"] = fetchss(dpr,"start_on_foot","false").lower() == "true"

        SimulationSettings.UseV1Rules = fetchss(dpr,"use_v1_rules","false").lower() == "true"
        
        # KM added to every link distance to eliminate needless distinction
        # between very short routes.
        SimulationSettings.move_rules["Softening"] = float(fetchss(dpr,"softening",10.0))

        dpo = fetchss(dp, "optimisations", None)
        SimulationSettings.optimisations["PopulationScaleDownFactor"] = float(fetchss(dpo,"hasten",1.0))

        if SimulationSettings.UseV1Rules is True:
            SimulationSettings.move_rules["MaxMoveSpeed"] = 200
            SimulationSettings.move_rules["StartOnFoot"] = False
            # Displaced people will not take a break unless they at least travelled
            # for a full day's distance in the last two days.
            SimulationSettings.move_rules["AvoidShortStints"] = False
            SimulationSettings.move_rules["CampWeight"] = 2.0  # attraction factor for camps.
            # reduction factor for refugees entering conflict zones.
            SimulationSettings.move_rules["ConflictWeight"] = 0.25

        return number_of_steps

