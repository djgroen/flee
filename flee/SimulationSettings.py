import sys
import csv


class SimulationSettings:
    # KM added to every link distance to eliminate needless distinction
    # between very short routes.
    Softening = 40.0
    # TurnBackAllowed = True # feature disabled for now.
    AgentLogLevel = 0  # set to 1 for basic agent information.
    # set to 1 to obtain average times for agents to reach camps at any time
    # step (aggregate info).
    CampLogLevel = 0
    # set to 1 for basic information on locations added and conflict zones
    # assigned.
    InitLogLevel = 0
    TakeRefugeesFromPopulation = False

    sqrt_ten = 3.16227766017  # square root of ten (10^0.5).

    CampWeight = 1.0  # attraction factor for camps.
    # reduction factor for refugees entering conflict zones.
    ConflictWeight = 1.0 / sqrt_ten
    # most number of km that we expect refugees to traverse per time step (30
    # km/h * 12 hours).
    MaxMoveSpeed = 40
    # most number of km that we expect refugees to traverse per time step on
    # foot (3.5 km/h * 10 hours).
    MaxWalkSpeed = 35
    # most number of km that we expect refugees to traverse per time step on
    # boat/walk to cross river (2 km/h * 10 hours).
    MaxCrossingSpeed = 20
    # Agents walk on foot when they travers their very first link.
    StartOnFoot = True
    CapacityBuffer = 1.0

    # default move chance
    ConflictMoveChance = 1.0
    CampMoveChance = 0.001
    DefaultMoveChance = 0.01

    # Specific enhancements for the 2.0 ruleset.
    # This includes a movespeed of 420 and a walk speed of 42.
    # Displaced people will not take a break unless they at least travelled
    # for a full day's distance in the last two days.
    AvoidShortStints = False

    FlareConflictInputFile = ""
    # -1, no weighting at all, 0 = road only, 1 = location, 2 = neighbours, 3 = region.
    AwarenessLevel = 1

    PopulationScaledownFactor = 1 # Speed up execution by scaling down population numbers (inputs, capacities and validations)

    # NumProcs = 1 #This is not supported at the moment.

    UseV1Rules = False

    if UseV1Rules == True:
        MaxMoveSpeed = 200
        StartOnFoot = False
        # Displaced people will not take a break unless they at least travelled
        # for a full day's distance in the last two days.
        AvoidShortStints = False
        CampWeight = 2.0  # attraction factor for camps.
        # reduction factor for refugees entering conflict zones.
        ConflictWeight = 0.25

    def ReadFromCSV(csv_name):
        """
        Reads simulation settings from CSV
        """
        number_of_steps = -1

        with open(csv_name, newline='') as csvfile:
            values = csv.reader(csvfile)

            for row in values:
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
                    SimulationSettings.UseV1Rules = (row[1].lower() == "true")
                elif row[0].lower() == "startonfoot":
                    SimulationSettings.StartOnFoot = (row[1].lower() == "true")
                elif row[0].lower() == "avoidshortstints":
                    SimulationSettings.AvoidShortStints = (
                        row[1].lower() == "true")
                elif row[0].lower() == "maxwalkspeed":
                    SimulationSettings.MaxWalkSpeed = float(row[1])
                elif row[0].lower() == "maxcrossingspeed":
                    SimulationSettings.MaxCrossingSpeed = float(row[1])
                else:
                    print(
                        "FLEE Initialization Error: unrecognized simulation parameter:", row[0])
                    sys.exit()

        return number_of_steps
