import csv
import sys
import yaml

# pylint: skip-file

def fetchss(dataset,name,default):
    if(name in dataset):
        return dataset[name]
    else:
        return default


class SimulationSettings:
    """
    The SimulationSettings class
    """

    log_evels = {} #log level variables
    spawn_rules = {} # ABM spawning rules
    move_rules = {} # ABM movement rules

    sqrt_ten = 3.16227766017  # square root of ten (10^0.5).

    CapacityBuffer = 1.0


    def ReadFromYML(ymlfile):
        with open(ymlfile) as f:
            dp = yaml.safe_load(f)

        number_of_steps = float(fetchss(dp,"number_of_steps",-1)
        SimulationSettings.FlareConflictInputFile = fetchss(dp,"conflict_input_file","")

        dpll = dp["log_levels"]
        SimulationSettings.log_levels["agent"] = int(fetchss(dpll,"agent",0))
        # set to 1 to obtain average times for agents to reach camps at any time
        # step (aggregate info).
        SimulationSettings.log_levels["camp"] = int(fetchss(dpll,"camp",0))
        # set to 1 for basic information on locations added and conflict zones
        # assigned.
        SimulationSettings.log_levels["init"] = int(fetchss(dpll,"init",0))



        dps = dp["spawn_rules"]
            SimulationSettings.move_rules["TakeFromPopulation"] = fetchss(dpr,"take_from_population").lower() == "true" 




        dpr = dp["move_rules"]

        # most number of km that we expect refugees to traverse per time step (30
        # km/h * 12 hours).
        SimulationSettings.move_rules["MaxMoveSpeed"] = float(fetchss(dpr,"max_move_speed"), 360.0)
        
        # most number of km that we expect refugees to traverse per time step on
        # foot (3.5 km/h * 10 hours).
        SimulationSettings.move_rules["MaxWalkSpeed"] = float(fetchss(dpr,"max_walk_speed"), 35.0)

        # most number of km that we expect refugees to traverse per time step on
        # boat/walk to cross river (2 km/h * 10 hours).
        SimulationSettings.move_rules["MaxCrossingSpeed"] = float(fetchss(dpr,"max_crossing_speed", 20.0))


        SimulationSettings.move_rules["CampWeight"] = float(fetchss(dpr,"camp_weight"), 1.0) # attraction multiplier for camps.
        SimulationSettings.move_rules["ConflictWeight"] = float(fetchss(dpr,"conflict_weight"), 1.0 / sqrt_ten) #attraction multiplier for source zones (conflict zones)


        SimulationSettings.move_rules["ConflictMoveChance"] = float(fetchss(dpr,"conflict_movechance"), 1.0) # chance of persons leaving a conflict zone per day.
        SimulationSettings.move_rules["CampMoveChance"] = float(fetchss(dpr,"camp_movechance"), 0.001) # chance of persons leaving a camp.
        SimulationSettings.move_rules["DefaultMoveChance"] = float(fetchss(dpr,"default_movechance"), 0.3) # chance of persons leaving a regular location per day.
        

        SimulationSettings.move_rules["AwarenessLevel"] = float(fetchss(dpr,"awareness_level"), 1) # awareness of locations X link steps away by agents.
        # -1, no weighting at all, 0 = road only, 1 = location, 2 = neighbours, 3 = region.
        

        # Displaced people will not take a break unless they at least travelled
        # for a full day's distance in the last two days.
        SimulationSettings.move_rules["AvoidShortStints"] = fetchss(dpr,"avoid_short_stints").lower() == "true"
      
        # Agents traverse first link on foot.
        SimulationSettings.move_rules["StartOnFoot"] = fetchss(dpr,"start_on_foot").lower() == "true"

        SimulationSettings.UseV1Rules = fetchss(dpr,"use_v1_rules").lower() == "true"
        
        # KM added to every link distance to eliminate needless distinction
        # between very short routes.
        SimulationSettings.move_rules["Softening"] = fetchss(dpr,"softening").lower() == "true"

        dpo = dp["optimisations"]
        SimulationSettings.optimisations["PopulationScaleDownFactor"] = float(fetchss(dpo,"hasten"))

        if self.UseV1Rules is True:
            self.move_rules["MaxMoveSpeed"] = 200
            self.move_rules["StartOnFoot"] = False
            # Displaced people will not take a break unless they at least travelled
            # for a full day's distance in the last two days.
            self.move_rules["AvoidShortStints"] = False
            self.move_rules["CampWeight"] = 2.0  # attraction factor for camps.
            # reduction factor for refugees entering conflict zones.
            self.move_rules["ConflictWeight"] = 0.25

        return number_of_steps


    def ReadFromCSV(csv_name):
        """
        Reads simulation settings from CSV
        """
        number_of_steps = -1

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)
            for row in values:
                # ignore getting IndexError in case of having empty line in
                # simsetting.csv file
                if len(row) == 0:
                    continue

                if row[0][0] == "#":
                    pass
                elif row[0].lower() == "agentloglevel":
                    SimulationSettings.AgentLogLevel = int(row[1])
                elif row[0].lower() == "camploglevel":
                    SimulationSettings.CampLogLevel = int(row[1])
                elif row[0].lower() == "initloglevel":
                    SimulationSettings.InitLogLevel = int(row[1])
                elif row[0].lower() == "minmovespeed":
                    SimulationSettings.MinMoveSpeed = float(row[1])
                elif row[0].lower() == "maxmovespeed":
                    SimulationSettings.MaxMoveSpeed = float(row[1])
                elif row[0].lower() == "numberofsteps":
                    number_of_steps = int(row[1])
                elif row[0].lower() == "campweight":
                    SimulationSettings.CampWeight = float(row[1])
                elif row[0].lower() == "conflictweight":
                    SimulationSettings.ConflictWeight = float(row[1])
                elif row[0].lower() == "conflictmovechance":
                    SimulationSettings.ConflictMoveChance = float(row[1])
                elif row[0].lower() == "campmovechance":
                    SimulationSettings.CampMoveChance = float(row[1])
                elif row[0].lower() == "defaultmovechance":
                    SimulationSettings.DefaultMoveChance = float(row[1])
                elif row[0].lower() == "awarenesslevel":
                    SimulationSettings.AwarenessLevel = int(row[1])
                elif row[0].lower() == "populationscaledownfactor":
                    SimulationSettings.PopulationScaledownFactor = int(row[1])
                elif row[0].lower() == "flareconflictinputfile":
                    SimulationSettings.FlareConflictInputFile = row[1]
                elif row[0].lower() == "usev1rules":
                    SimulationSettings.UseV1Rules = row[1].lower() == "true"
                elif row[0].lower() == "startonfoot":
                    SimulationSettings.StartOnFoot = row[1].lower() == "true"
                elif row[0].lower() == "avoidshortstints":
                    SimulationSettings.AvoidShortStints = row[1].lower() == "true"
                elif row[0].lower() == "maxwalkspeed":
                    SimulationSettings.MaxWalkSpeed = float(row[1])
                elif row[0].lower() == "maxcrossingspeed":
                    SimulationSettings.MaxCrossingSpeed = float(row[1])
                else:
                    print("FLEE Initialization Error: unrecognized simulation parameter:", row[0])
                    sys.exit()

        return number_of_steps
