import os
from flee import flee, moving
from flee import InputGeography
import sys

"""
Test cases for DFlee related functionalities.
"""

def test_read_flood_csv():
    """
    Summary: 
        Test reading of flood level csv file.txt
        Reads csv file then checks attributes.

    Args:
        None

    Returns:
        None
    """

    flee.SimulationSettings.ReadFromYML("empty.yml")

    e = flee.Ecosystem()

    ig = InputGeography.InputGeography()

    flee.SimulationSettings.move_rules["FloodRulesEnabled"] = True

    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/closures.csv"))

    ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data/test_data_dflee","test_input_csv","flood_level.csv"))

    print(ig.attributes["flood_level"])

    #ig.attributes["flood_level"] = {'A': [0, 0, 1, 1, 2, 1, 1, 1, 1, 1, 1], 'B': [1, 1, 1, 3, 1, 1, 0, 0, 0, 0, 1]}

    #Check the flood levels at locations A and B at t=0-10
    assert ig.attributes["flood_level"]['A'][10] == 1
    assert ig.attributes["flood_level"]['A'][4] == 2
    assert ig.attributes["flood_level"]['B'][10] == 1
    assert ig.attributes["flood_level"]['B'][0] == 1
    assert ig.attributes["flood_level"]['B'][9] == 0

    print("Test successful!! Flood levels CSV correctly read.")


def test_flood_level_location_attribute():
    """
    Summary:
        Test flood level location attribute.
        Reads test files then checks flood attributes.

    Args:
        None
    
    Returns:
        None
    """    
    flee.SimulationSettings.ReadFromYML("empty.yml")
    flee.SimulationSettings.move_rules["FloodRulesEnabled"] = True
    flee.SimulationSettings.move_rules["FloodLocWeights"] = [0.0,1.0,1.0,1.0,1.0]
    flee.SimulationSettings.move_rules["FloodMovechances"] = [0.0,1.0,1.0,1.0,1.0]

    e = flee.Ecosystem()

    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/closures.csv"))

    ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data/test_data_dflee","test_input_csv/flood_level.csv"))

    ig.ReadAttributeInputCSV("forecast_flood_levels", "int", os.path.join("test_data/test_data_dflee","test_input_csv/flood_level.csv"))

    ig.ReadAttributeInputCSV("floodawareness", "float", os.path.join("test_data/test_data_dflee","test_input_csv/demographics_floodawareness.csv"))

    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    end_time = 11

    new_refs = 1

    # Insert refugee agents
    for _ in range(0, new_refs):
        e.addAgent(location=lm["A"], attributes={})

    for t in range(0, end_time):

        ig.AddNewConflictZones(e, t)

        # Check the flood levels at t=0
        if t == 0:
            assert lm["A"].attributes["flood_level"] == 0
            assert e.locations[1].attributes["flood_level"] == 1
            #Check the flood levels at locations C a town and E a camp are 0 
            assert lm["C"].attributes["flood_level"] == 0
            assert lm["E"].attributes["flood_level"] == 0

        # Propagate the model by one time step.
        e.evolve()

        #Print the flood levels at each time step
        print("timestep(t)", t)
        print("Flood Level of Location A:",lm["A"].attributes["flood_level"])
        print("Flood Level of Location B:", e.locations[1].attributes["flood_level"])

        #Check the flood levels at t=3
        if t == 3:
            assert lm["A"].attributes["flood_level"] == 1
            assert e.locations[1].attributes["flood_level"] == 3
            #Check the flood levels at locations C a town and E a camp are 0 
            assert lm["C"].attributes["flood_level"] == 0
            assert lm["E"].attributes["flood_level"] == 0
    
    #Check the flood levels at the final time step
    assert lm["A"].attributes["flood_level"] == 1
    assert e.locations[1].attributes["flood_level"] == 1

    print("Test successful!! Flood level attribute correctly set.")


def test_flood_forecaster():
    """
    Summary:
        Test flood level location attribute.
        Reads test files then checks flood attributes are being used to set the future flood levels atrribute.
    
    Returns:
        None
    
    Args:
        None
    """    
    flee.SimulationSettings.ReadFromYML("empty.yml")
    flee.SimulationSettings.move_rules["FloodRulesEnabled"] = True
    flee.SimulationSettings.move_rules["FloodLocWeights"] = [0.0,1.0,1.0,1.0,1.0]
    flee.SimulationSettings.move_rules["FloodMovechances"] = [0.0,1.0,1.0,1.0,1.0]

    flee.SimulationSettings.move_rules["FloodForecaster"] = True
    flee.SimulationSettings.move_rules["FloodForecasterTimescale"] = 2 # 1 = 1 day, 2 = 2 days, etc. 0 = no memory
    flee.SimulationSettings.move_rules["FloodForecasterEndTime"] = 6 #The forcast data only extends this many days into the simulation. Default value should be (simulation length - flood forecaster timesale).
    flee.SimulationSettings.move_rules["FloodForecasterWeights"] = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.1,0.3, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0] # weights for each day the flood forecaster. 1 = max importance, 0.0 = no importance. First value is today. 
    flee.SimulationSettings.move_rules["FloodAwarenessWeights"] = [0.0,0.5,1.0] #low, medium, high awareness or ability to adaptat to flooding (0.0 = no awareness, 1.0 = high awareness)  
    
    e = flee.Ecosystem()

    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/closures.csv"))

    ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data/test_data_dflee","test_input_csv/flood_level.csv"))

    ig.ReadAttributeInputCSV("forecast_flood_levels", "int", os.path.join("test_data/test_data_dflee","test_input_csv/flood_level.csv"))

    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    end_time = 11

    for t in range(0, end_time):

        ig.AddNewConflictZones(e, t)

        # Check the flood levels at t=0
        if t == 0:
            #Check the flood levels at locations A and B, the flood zones are non-zero
            assert lm["A"].attributes["flood_level"] == 0
            assert e.locations[1].attributes["flood_level"] == 1
            #Check the flood levels at locations C a town and E a camp are 0 
            assert lm["C"].attributes["flood_level"] == 0
            assert lm["E"].attributes["flood_level"] == 0
            #Check the flood forecast at locations A and B, the flood zones are non-zero
            assert lm["A"].attributes["forecast_flood_levels"] == [0.0,0.0,1.0,1.0,2.0,1.0,1.0,1.0,1.0,1.0,1.0]
            assert e.locations[1].attributes["forecast_flood_levels"] == [1.0,1.0,1.0,3.0,1.0,1.0,0.0,0.0,0.0,0.0,1.0]
            #Check forecast at locations C a town and E a camp are 0 
            assert lm["C"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
            assert lm["E"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

        # Propagate the model by one time step.
        e.evolve()

        #Print the flood levels at each time step
        print("timestep(t)", t)
        print("Flood Level of Location A:",lm["A"].attributes["flood_level"])
        print("Flood Level of Location B:", e.locations[1].attributes["flood_level"])

        #Check the flood levels at t=3
        if t == 3:
            #Check the flood levels at locations A and B, the flood zones are non-zero
            assert lm["A"].attributes["flood_level"] == 1
            assert e.locations[1].attributes["flood_level"] == 3
            #Check the flood levels at locations C a town and E a camp are 0 
            assert lm["C"].attributes["flood_level"] == 0
            assert lm["E"].attributes["flood_level"] == 0
            #Check the flood forecast at locations A and B, the flood zones are non-zero
            assert lm["A"].attributes["forecast_flood_levels"] == [0.0,0.0,1.0,1.0,2.0,1.0,1.0,1.0,1.0,1.0,1.0]
            assert e.locations[1].attributes["forecast_flood_levels"] == [1.0,1.0,1.0,3.0,1.0,1.0,0.0,0.0,0.0,0.0,1.0]
            #Check forecast at locations C a town and E a camp are 0
            assert lm["C"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
            assert lm["E"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

    
    #Check the flood levels at the final time step
    assert lm["A"].attributes["flood_level"] == 1
    assert e.locations[1].attributes["flood_level"] == 1

    print("flood forecast len", len(lm["A"].attributes["forecast_flood_levels"]))
    #Check the flood forecast at the final time step
    assert lm["A"].attributes["forecast_flood_levels"] == [0.0,0.0,1.0,1.0,2.0,1.0,1.0,1.0,1.0,1.0,1.0]
    assert e.locations[1].attributes["forecast_flood_levels"] == [1.0,1.0,1.0,3.0,1.0,1.0,0.0,0.0,0.0,0.0,1.0]
    assert lm["C"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    assert lm["E"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

    print("Test successful!! Flood Forecaster Working.")


def test_agent_flood_awareness():
    """
    Summary:
        Test flood level awareness level of agents. 

    Args:   
        None
    
    Rturns: 
        None
    """

    #Flood rules
    flee.SimulationSettings.ReadFromYML("empty.yml")
    flee.SimulationSettings.move_rules["FloodRulesEnabled"] = True
    flee.SimulationSettings.move_rules["FloodLocWeights"] = [0.0,1.0,1.0,1.0,1.0]
    flee.SimulationSettings.move_rules["FloodMovechances"] = [0.0,1.0,1.0,1.0,1.0]

    flee.SimulationSettings.move_rules["FloodForecaster"] = True
    flee.SimulationSettings.move_rules["FloodForecasterTimescale"] = 2 # 1 = 1 day, 2 = 2 days, etc. 0 = no memory
    flee.SimulationSettings.move_rules["FloodForecasterEndTime"] = 6 #The forcast data only extends this many days into the simulation. Default value should be (simulation length - flood forecaster timesale).
    flee.SimulationSettings.move_rules["FloodForecasterWeights"] = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.1,0.3, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0] # weights for each day the flood forecaster. 1 = max importance, 0.0 = no importance. First value is today. 
    flee.SimulationSettings.move_rules["FloodAwarenessWeights"] = [0.0,0.5,1.0] #low, medium, high awareness or ability to adaptat to flooding (0.0 = no awareness, 1.0 = high awareness)  
    flee.SimulationSettings.spawn_rules["TakeFromPopulation"] = True

    #Spawn rules
    flee.SimulationSettings.spawn_rules["flood_driven_spawning"] = True
    flee.SimulationSettings.spawn_rules["flood_zone_spawning_only"] = True
    flee.SimulationSettings.spawn_rules["conflict_zone_spawning_only"] = False
    flee.SimulationSettings.spawn_rules["flood_spawn_mode"] = "pop_ratio"
    flee.SimulationSettings.spawn_rules["displaced_per_flood_day"] = [0.0,0.1,0.2,0.5,0.9]

    #Define flood level file location for ReadAttributeInputCSV called in AddNewConflictZones
    flee.SimulationSettings.FloodLevelInputFile = os.path.join("test_data/test_data_dflee","test_input_csv/flood_level.csv")

    # Set simulation ecosystem and input geography
    e = flee.Ecosystem()
    ig = InputGeography.InputGeography()

    #Read test data files:
    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data/test_data_dflee", "test_input_csv/closures.csv"))
    
    ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data/test_data_dflee","test_input_csv/flood_level.csv"))

    ig.ReadAttributeInputCSV("forecast_flood_levels", "int",os.path.join("test_data/test_data_dflee","test_input_csv/flood_level.csv"))

    ig.ReadAttributeInputCSV("age", "float", os.path.join("test_data/test_data_dflee","test_input_csv/demographics_age.csv")) 
   
    ig.ReadAttributeInputCSV("floodawareness", "float", os.path.join("test_data/test_data_dflee","test_input_csv/demographics_floodawareness.csv"))

    print("locations", ig.locations)
    print(ig.attributes["flood_level"])
    print(ig.attributes["forecast_flood_levels"])
    #Set the simulation length
    end_time = 11

    #Store input geography in the ecosystem
    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    #Add Dynamic Attibrutes e.g. Flood Zone Levels to the Locations
    
    ig.AddNewConflictZones(e=e, time=0)

    # Add agents to the simulation in the towns
    for i in range(0,100):
        e.addAgent(location=lm["A"], attributes={"floodawareness": 1.0, "flood_level": 1.0, "forecast_flood_levels": [0, 0, 1, 1, 2, 1, 1, 1, 1, 1, 1]})
        e.addAgent(location=lm["B"], attributes={"floodawareness": 0.5, "flood_level": 1.0, "forecast_flood_levels":  [1, 1, 1, 3, 1, 1, 0, 0, 0, 0, 1]})
        e.addAgent(location=lm["C"], attributes={"floodawareness": 0.5, "flood_level": 0.0, "forecast_flood_levels": [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]})
        e.addAgent(location=lm["C2"], attributes={"floodawareness": 1.0, "flood_level": 0.0, "forecast_flood_levels": [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]})
        e.addAgent(location=lm["D"], attributes={"floodawareness": 1.0, "flood_level": 0.0, "forecast_flood_levels": [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]})
        e.addAgent(location=lm["E"], attributes={"floodawareness": 1.0, "flood_level": 0.0, "forecast_flood_levels": [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]})
        e.addAgent(location=lm["F"], attributes={"floodawareness": 1.0, "flood_level": 0.0, "forecast_flood_levels": [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]})
    
    for t in range(0, end_time):

        ig.AddNewConflictZones(e=e, time=t) #Adds dynamic attributes to the locations

        print(
            t,
            lm["A"].numAgents,
            lm["B"].numAgents,
            lm["C"].numAgents,
            lm["C2"].numAgents,
            lm["D"].numAgents,
            lm["E"].numAgents,
            lm["F"].numAgents,
        )

        #Check the flood level attributes at t=0
        if t == 0:
            #Check the flood level at flood zones A and B
            assert lm["A"].attributes["flood_level"] == 0.0
            assert lm["B"].attributes["flood_level"] == 1.0
            #Check the forecast flood levels at flood zone B on days 0,1,3
            assert lm["B"].attributes["forecast_flood_levels"][0] == 1.0
            assert lm["B"].attributes["forecast_flood_levels"][1] == 1.0
            assert lm["B"].attributes["forecast_flood_levels"][2] == 1.0
            assert lm["B"].attributes["forecast_flood_levels"][3] == 3.0
            #Check the forecast flood levels at flood zone A on days 0,1,2,3
            assert lm["A"].attributes["forecast_flood_levels"][0] == 0.0
            assert lm["A"].attributes["forecast_flood_levels"][1] == 0.0
            assert lm["A"].attributes["forecast_flood_levels"][2] == 1.0
            assert lm["A"].attributes["forecast_flood_levels"][3] == 1.0
            #Check the forecast flood levels at flood zone C on days 0,1,2,3
            assert lm["C"].attributes["forecast_flood_levels"][0] == 0.0
            assert lm["C"].attributes["forecast_flood_levels"][1] == 0.0
            assert lm["C"].attributes["forecast_flood_levels"][2] == 0.0
            assert lm["C"].attributes["forecast_flood_levels"][3] == 0.0
            #Check the agents flood awareness at flood zones A and B
            assert e.agents[0].location.name == "A"
            assert e.agents[0].attributes["floodawareness"] == 1.0
            assert e.agents[1].location.name == "B"
            assert e.agents[1].attributes["floodawareness"] == 0.5
             #Check the agents flood awareness at flood zones C,C2,D,E,F
            assert e.agents[2].location.name == "C"
            assert e.agents[2].attributes["floodawareness"] == 0.5
            assert e.agents[3].location.name == "C2"
            assert e.agents[3].attributes["floodawareness"] == 1.0
            assert e.agents[4].location.name == "D"
            assert e.agents[4].attributes["floodawareness"] == 1.0
            assert e.agents[5].location.name == "E"
            assert e.agents[5].attributes["floodawareness"] == 1.0

        e.evolve()  


    #Check flood forecaster is calculating the correct base score
    #Choose a day, e.g. day 4, and a location, flood zone A, and calcualted the flood move chance based on different flood awareness levels
    #Given an agent awareness weight of 0.5, check the flood move chance is 0.5
    if t == 4:
        forecast_day = 4
        #Check the flood level at flood zones A 
        assert lm["A"].attributes["flood_level"] == 1.0

        #Check the movechance for flood level 1 
        assert float(flee.SimulationSettings.move_rules["FloodMovechances"][1.0]) == 0.5
        
        #Check the forecast floof level on the forecast day for flood zone A
        assert lm["A"].attributes["forecast_flood_levels"][forecast_day] == 2.0
        
        #Check forecast_timescale = SimulationSettings.move_rules["FloodForecasterTimescale"] = 2
        assert flee.SimulationSettings.move_rules["FloodForecasterTimescale"] == 2

        #Check forecast_end_time = SimulationSettings.move_rules["FloodForecasterEndTime"] = 6
        forecast_end_time = flee.SimulationSettings.move_rules["FloodForecasterEndTime"]
        assert flee.SimulationSettings.move_rules["FloodForecasterEndTime"] == 6

        # Check agent_awareness_weight = float(SimulationSettings.move_rules["FloodAwarenessWeights"][int(a.attributes["floodawareness"])]) = 0.5
        agent_awareness_weight = flee.SimulationSettings.move_rules["FloodAwarenessWeights"][int(e.agents[0].attributes["floodawareness"])]
        assert flee.SimulationSettings.move_rules["FloodAwarenessWeights"][int(e.agents[0].attributes["floodawareness"])] == 0.5

        # Check forecast_flood_level_weight = float(SimulationSettings.move_rules["FloodLocWeights"][forecast_flood_level]) = 0.0 
        forecast_flood_level_weight = flee.SimulationSettings.move_rules["FloodLocWeights"][2.0]  
        assert flee.SimulationSettings.move_rules["FloodLocWeights"][lm["A"].attributes["forecast_flood_levels"][0]] == 0.0

        # Check flood_forecaster_weight = float(SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day])
        flood_forecaster_weight = flee.SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day]
        assert flee.SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day] == 1.0

        # Check flood_forecast_base += forecast_flood_level_weight * flood_forecaster_weight
        assert  flee.SimulationSettings.move_rules["FloodLocWeights"][lm["A"].attributes["forecast_flood_levels"][0]] * flee.SimulationSettings.move_rules["FloodForecasterWeights"][0] == 0.0

        # Check break forecast_day == forecast_end_time
        if t == 6:
            assert t == flee.SimulationSettings.move_rules["FloodForecasterEndTime"]
        else:
            assert t != flee.SimulationSettings.move_rules["FloodForecasterEndTime"]
        
        # Check flood_forecast_movechance *= float(flood_forecast_movechance/forecast_timescale)
        assert flee.SimulationSettings.move_rules["FloodMovechances"][0] == 0.0

        # Check flood_forecast_movechance *= float(agent_awareness_weight) 
        assert float(flee.SimulationSettings.move_rules["FloodMovechances"][1]) == flee.SimulationSettings.move_rules["FloodAwarenessWeights"][int(e.agents[0].attributes["floodawareness"])]

    #Check agents have been added to the locations. 
    assert lm["A"].numAgents > 0   

    print("Test successful! Flood awareness correctly set. Weather forecaster working.")




if __name__ == "__main__":
    test_read_flood_csv()
    test_flood_level_location_attribute()
    test_flood_forecaster()
    test_agent_flood_awareness()
    pass
