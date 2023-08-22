import sys
import yaml
import os

# pylint: skip-file

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


    @staticmethod
    def get_conflict_decay(time_since_conflict: int):

        if SimulationSettings.spawn_rules["conflict_spawn_decay"] is None:
            return 1.0

        spawn_len = len(SimulationSettings.spawn_rules["conflict_spawn_decay"])

        if spawn_len < 1:
            print("Warning: no conflict spawn decay set. Defaulting to no decay", file=sys.stderr)
            return 1.0
        else:
            i = min(int(time_since_conflict / 30), spawn_len-1)
            if SimulationSettings.log_levels["conflict"] > 0:
              print("Conflict zone spawn status: time elapsed {}, decay factor {}".format(time_since_conflict, float(SimulationSettings.spawn_rules["conflict_spawn_decay"][i])), file=sys.stderr)
            return float(SimulationSettings.spawn_rules["conflict_spawn_decay"][i])


    @staticmethod
    def get_location_conflict_decay(time: int, loc):
        """

        time: e.time (time in simulation)
        loc: location for which to calculate the decay multiplier.
        """
        time_since_conflict = time - loc.time_of_conflict
        multiplier = SimulationSettings.get_conflict_decay(time_since_conflict)
        return multiplier


    @staticmethod
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
        # set to 2 to obtain duplicate entries when agents do multiple hops in one timestep.
        # step (aggregate info).
        SimulationSettings.log_levels["link"] = int(fetchss(dpll,"link",0))
        # set to 1 to obtain cumulative agent counts on links at any time
        # step (aggregate info).
        SimulationSettings.log_levels["camp"] = int(fetchss(dpll,"camp",0))
        # set to 1 for basic information on locations added and conflict zones
        # assigned.
        SimulationSettings.log_levels["init"] = int(fetchss(dpll,"init",0))
        # set to 1 for information on conflict zone spawning
        SimulationSettings.log_levels["conflict"] = int(fetchss(dpll,"conflict",0))
        SimulationSettings.log_levels["idp_totals"] = int(fetchss(dpll,"idp_totals",0))



        dps = fetchss(dp,"spawn_rules",None)

        # Spawned agents are subtracted from populations. This can lead to crashes if the number of spawned agents
        # exceeds the total population in conflict zones.
        print("Take from population?", fetchss(dps,"take_from_population","false"), file=sys.stderr)

        SimulationSettings.spawn_rules["TakeFromPopulation"] = bool(fetchss(dps, "take_from_population", False))
        # Advanced settings
        SimulationSettings.spawn_rules["InsertDayZeroRefugeesInCamps"] = bool(fetchss(dps, "insert_day0", True))


        SimulationSettings.spawn_rules["conflict_zone_spawning_only"] = bool(fetchss(dps, "conflict_zone_spawning_only", True)) # Only spawn agents from conflict zones.
        SimulationSettings.spawn_rules["flood_zone_spawning_only"] = bool(fetchss(dps, "flood_zone_spawning_only", False)) # Only spawn agents from flood zones.

        if (SimulationSettings.spawn_rules["conflict_zone_spawning_only"] is True and SimulationSettings.spawn_rules["flood_zone_spawning_only"] is True):
            print("ERROR in simulationsetting.yml: both conflict_zone_spawning_only and flood_zone_spawning_only are enabled in the Flee configuration.", file=sys.stderr)
            print("Both parameters are defined in the spawn_rules section of simulationsetting.yml.", file=sys.stderr)
            print("NOTE: conflict_zone_spawning_only is enabled by default, and needs to be disabled when you define flood_zone_spawning_only to be true.", file=sys.stderr)
            sys.exit()

        SimulationSettings.spawn_rules["camps_are_sinks"] = bool(fetchss(dps, "camps_are_sicks", False)) # Camps can deactivate agents.
        SimulationSettings.spawn_rules["read_from_agents_csv_file"] = bool(fetchss(dps, "read_from_agents_csv_file", False)) # Load agents from agents.csv file.

        spawn_type = "conflict"
        if SimulationSettings.spawn_rules["flood_zone_spawning_only"] is True:
            spawn_type = "flood"

        if spawn_type == "conflict":
          dpsc = fetchss(dps,"conflict_driven_spawning",None)
          if dpsc is not None:
            SimulationSettings.spawn_rules["conflict_driven_spawning"] = True # Conflicts provide a direct push factor.
          
            SimulationSettings.spawn_rules["conflict_spawn_mode"] = fetchss(dpsc,"spawn_mode","constant") # constant, Poisson, pop_ratio

            if SimulationSettings.spawn_rules["conflict_spawn_mode"] == "pop_ratio":
              SimulationSettings.spawn_rules["displaced_per_conflict_day"] = float(fetchss(dpsc,"displaced_per_conflict_day", 0.01))
            else:
              SimulationSettings.spawn_rules["displaced_per_conflict_day"] = int(fetchss(dpsc,"displaced_per_conflict_day", 500))
          else:
            SimulationSettings.spawn_rules["conflict_driven_spawning"] = False

        elif spawn_type == "flood":
          dpsc = fetchss(dps,"flood_driven_spawning",None)
          if dpsc is not None:
            SimulationSettings.spawn_rules["flood_driven_spawning"] = True # Conflicts provide a direct push factor.

            SimulationSettings.spawn_rules["flood_spawn_mode"] = fetchss(dpsc,"spawn_mode","constant") # constant, Poisson, pop_ratio

            if SimulationSettings.spawn_rules["flood_spawn_mode"] == "pop_ratio":
              SimulationSettings.spawn_rules["displaced_per_flood_day"] = float(fetchss(dpsc,"displaced_per_conflict_day", 0.01))
            else:
              SimulationSettings.spawn_rules["displaced_per_flood_day"] = int(fetchss(dpsc,"displaced_per_conflict_day", 500))
          else:
            SimulationSettings.spawn_rules["flood_driven_spawning"] = False


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


        SimulationSettings.move_rules["ForeignWeight"] = float(fetchss(dpr,"foreign_weight", 1.0)) # attraction multiplier for foreign locations (stacks with camp multiplier).
        SimulationSettings.move_rules["CampWeight"] = float(fetchss(dpr,"camp_weight", 1.0)) # attraction multiplier for camps.
        SimulationSettings.move_rules["ConflictWeight"] = float(fetchss(dpr,"conflict_weight", 1.0 / SimulationSettings.sqrt_ten)) #attraction multiplier for source zones (conflict zones)


        SimulationSettings.move_rules["ConflictMoveChance"] = float(fetchss(dpr,"conflict_movechance", 1.0)) # chance of persons leaving a conflict zone per day.
        SimulationSettings.move_rules["CampMoveChance"] = float(fetchss(dpr,"camp_movechance", 0.001)) # chance of persons leaving a camp.
        SimulationSettings.move_rules["IDPCampMoveChance"] = float(fetchss(dpr,"idpcamp_movechance", 0.1)) # chance of persons leaving a camp.
        SimulationSettings.move_rules["DefaultMoveChance"] = float(fetchss(dpr,"default_movechance", 0.3)) # chance of persons leaving a regular location per day.
        

        SimulationSettings.move_rules["AwarenessLevel"] = int(fetchss(dpr,"awareness_level", 1)) # awareness of locations X link steps away by agents.
        # -1, no weighting at all, 0 = road only, 1 = location, 2 = neighbours, 3 = region.
       
        # A location or camp is beginning to be considered full if the number of agents there exceeds (capacity OR pop) * CapacityBuffer.
        SimulationSettings.move_rules["CapacityBuffer"] = float(fetchss(dpr,"capacity_buffer", 0.9)) # awareness of locations X link steps away by agents.

        # Displaced people will not take a break unless they at least travelled
        # for a full day's distance in the last two days.
        SimulationSettings.move_rules["AvoidShortStints"] = bool(fetchss(dpr,"avoid_short_stints",False))
      
        # Agents traverse first link on foot.
        SimulationSettings.move_rules["StartOnFoot"] = bool(fetchss(dpr,"start_on_foot",False))

        SimulationSettings.UseV1Rules = bool(fetchss(dpr,"use_v1_rules",False))
        
        # KM added to every link distance to eliminate needless distinction
        # between very short routes.
        SimulationSettings.move_rules["DistanceSoftening"] = float(fetchss(dpr,"softening",10.0))
        # Constant added to ALL weights irrespective of distance, to increase randomness in route selection.
        SimulationSettings.move_rules["WeightSoftening"] = float(fetchss(dpr,"weight_softening",0.0))
        # Power factor that amplifies or diminishes the weight difference. 0.0 means uniform weighting everywhere and 1.0 is the default.
        SimulationSettings.move_rules["WeightPower"] = float(fetchss(dpr,"weight_power",1.0))
        
        # Factor to increase or decrease importance of distance in weight calculations. Default is (inverse) linear)
        SimulationSettings.move_rules["DistancePower"] = float(fetchss(dpr,"distance_power",1.0))

        # A switch to enable weighting of distance to home location for different locations.
        # As well as a power factor to adjust the weight of it. Default is sqrt scaling of distance.
        SimulationSettings.move_rules["StayCloseToHome"] = bool(fetchss(dpr,"stay_close_to_home",False))
        SimulationSettings.move_rules["HomeDistancePower"] = float(fetchss(dpr,"home_distance_power",0.5))



        # Enable/disable location attractiveness weighting by population.
        SimulationSettings.move_rules["UsePopForLocWeight"] = bool(fetchss(dpr,"use_pop_for_loc_weight",False))
        # Factor to increase or decrease importance of population in location attractiveness. 
        # Default = 0.05, which doubles the weight of a town with 1M pop, compared to 1 pop.
        SimulationSettings.move_rules["PopPowerForLocWeight"] = float(fetchss(dpr,"pop_power_for_loc_weight",0.1))

       
        # Adjust to introduce population weighting in all move chances.
        SimulationSettings.move_rules["MovechancePopBase"] = float(fetchss(dpr,"movechance_pop_base",10000.0)) 
        SimulationSettings.move_rules["MovechancePopScaleFactor"] = float(fetchss(dpr,"movechance_pop_scale_factor",0.0))


        # Flee 3.0 Prototyping conditionals (see design focument)
        # TODO: embed these in a more flexible/powerful framework of conditionals
        for a in ["ChildrenAvoidHazards", "BoysTakeRisk", "MatchCampEthnicity", "MatchTownEthnicity", "MatchConflictEthnicity"]:
            SimulationSettings.move_rules[a] = bool(fetchss(dpr,a,False))

        dpf = fetchss(dp, "flood_rules", None)
        if dpf is not None:
          SimulationSettings.move_rules["FloodRulesEnabled"] = True
          SimulationSettings.spawn_rules["MaxFloodLevel"] = int(fetchss(dpf,"max_flood_level", -1))

          # Move rules
          SimulationSettings.move_rules["FloodMovechances"] = fetchss(dps,"flood_movechances", None) # Expect an array or dict
          print("Flood Movechances set to:", SimulationSettings.spawn_rules["FloodMovechances"], file=sys.stderr)
          SimulationSettings.move_rules["FloodLocWeights"] = fetchss(dps,"flood_loc_weights", None) # Expect an array or dict
          print("Flood Location Weights set to:", SimulationSettings.spawn_rules["FloodLocWeights"], file=sys.stderr)
          SimulationSettings.move_rules["FloodLinkWeights"] = fetchss(dps,"flood_link_weights", None) # Expect an array or dict
          print("Flood Link Weights set to:", SimulationSettings.spawn_rules["FloodLinkWeights"], file=sys.stderr)

          # Add verification code.

        else:
          SimulationSettings.move_rules["FloodRulesEnabled"] = False

        dpo = fetchss(dp, "optimisations", None)
        SimulationSettings.optimisations["PopulationScaleDownFactor"] = int(fetchss(dpo,"hasten",1))

        if SimulationSettings.UseV1Rules is True:
            SimulationSettings.move_rules["MaxMoveSpeed"] = 200
            SimulationSettings.move_rules["StartOnFoot"] = False
            # Displaced people will not take a break unless they at least travelled
            # for a full day's distance in the last two days.
            SimulationSettings.move_rules["AvoidShortStints"] = False
            SimulationSettings.move_rules["CampWeight"] = 2.0  # attraction factor for camps.
            # reduction factor for refugees entering conflict zones.
            SimulationSettings.move_rules["ConflictWeight"] = 0.25

        print("Move rules set to:", SimulationSettings.move_rules, file=sys.stderr)

        return number_of_steps

