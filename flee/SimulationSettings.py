import sys
import csv

class SimulationSettings:
  Softening = 0.0
  #TurnBackAllowed = True # feature disabled for now.
  AgentLogLevel = 0 # set to 1 for basic agent information.
  CampLogLevel = 0  # set to 1 to obtain average times for agents to reach camps at any time step (aggregate info).
  InitLogLevel  = 0 # set to 1 for basic information on locations added and conflict zones assigned.
  TakeRefugeesFromPopulation = True

  sqrt_ten = 3.16227766017 # square root of ten (10^0.5).

  CampWeight = sqrt_ten # attraction factor for camps.
  ConflictWeight = 1.0 / sqrt_ten # reduction factor for refugees entering conflict zones.
  MaxMoveSpeed = 420 # most number of km that we expect refugees to traverse per time step (35 km/h * 12 hours).
  MaxWalkSpeed = 42 # most number of km that we expect refugees to traverse per time step on foot (3.5 km/h * 12 hours).
  #UseDynamicCampWeights = True # overrides CampWeight depending on characteristics of the ecosystem.
  StartOnFoot = True # Agents walk on foot when they travers their very first link.
  CapacityBuffer = 1.0

  #default move chances
  ConflictMoveChance = 1.0
  CampMoveChance = 0.001
  DefaultMoveChance = 0.3

  # Specific enhancements for the 2.0 ruleset.
  # This includes a movespeed of 420 and a walk speed of 42.
  AvoidShortStints = True # Displaced people will not take a break unless they at least travelled for a full day's distance in the last two days.

  FlareConflictInputFile = ""

  #NumProcs = 1 #This is not supported at the moment.

  UseV1Rules = False

  if UseV1Rules == True:
    MaxMoveSpeed = 200
    StartOnFoot = False
    AvoidShortStints = False # Displaced people will not take a break unless they at least travelled for a full day's distance in the last two days.
    CampWeight = 2.0 # attraction factor for camps.
    ConflictWeight = 0.25 # reduction factor for refugees entering conflict zones.


  AwarenessLevel = 1 #-1, no weighting at all, 0 = road only, 1 = location, 2 = neighbours, 3 = region.

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
        elif row[0].lower() == "flareconflictinputfile":
          SimulationSettings.FlareConflictInputFile = row[1]
        else:
          print("FLEE Initialization Error: unrecognized simulation parameter:",row[0])
          sys.exit()

    return number_of_steps

