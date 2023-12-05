import os
from flee import flee, moving
from flee import InputGeography


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

    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data", "test_input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data", "test_input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data", "test_input_csv/closures.csv"))

    ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data","test_input_csv","flood_level.csv"))

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
    """    
    flee.SimulationSettings.ReadFromYML("empty.yml")
    flee.SimulationSettings.move_rules["FloodRulesEnabled"] = True
    flee.SimulationSettings.move_rules["FloodLocWeights"] = [0.0,1.0,1.0,1.0,1.0]
    flee.SimulationSettings.move_rules["FloodMovechances"] = [0.0,1.0,1.0,1.0,1.0]

    e = flee.Ecosystem()

    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data", "test_input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data", "test_input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data", "test_input_csv/closures.csv"))

    ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data","test_input_csv","flood_level.csv"))

    ig.ReadAttributeInputCSV("forecast_flood_levels", "int", os.path.join("test_data","test_input_csv","flood_level.csv"))

    ig.ReadAttributeInputCSV("flood_awareness", "float", os.path.join("test_data","test_input_csv","demographics_floodawareness.csv"))

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


# def test_flood_forecaster():
    """
    Summary:
        Test flood level location attribute.
        Reads test files then checks flood attributes are being used to set the future flood levels atrribute.
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

    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data", "test_input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data", "test_input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data", "test_input_csv/closures.csv"))

    ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data","test_input_csv","flood_level.csv"))

    ig.ReadAttributeInputCSV("forecast_flood_levels", "int", os.path.join("test_data","test_input_csv","flood_level.csv"))
    
    ig.ReadAttributeInputCSV("floodawareness", "int", os.path.join("test_data","test_input_csv","demographics_floodawareness.csv"))
   
    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    end_time = 11

    new_refs = 1

    # Insert refugee agents
    # for _ in range(0, new_refs):
    #     e.addAgent(location=lm["A"], attributes={})
    #     e.agent.attrbute["flood_awareness"] = 1.0 #low, medium, high awareness or ability to adaptat to flooding (0.0 = no awareness, 1.0 = high awareness)

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
            assert lm["C"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0]
            assert lm["E"].attributes["forecast_flood_levels"] == [0.0,0.0,0.0,0.0,0.0,0.0]

    
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


# def test_agent_flood_awareness():
#     """
#     Summary:
#         Test flood level awareness level of agents. 

#     Args:   
#         None
    
#     Rturns: 
#         None
#     """
    
    
#     flee.SimulationSettings.ReadFromYML("empty.yml")

#     # flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
#     # flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0
    
#     #Flood rules
#     flee.SimulationSettings.ReadFromYML("empty.yml")
#     flee.SimulationSettings.move_rules["FloodRulesEnabled"] = True
#     flee.SimulationSettings.move_rules["FloodLocWeights"] = [0.0,1.0,1.0,1.0,1.0]
#     flee.SimulationSettings.move_rules["FloodMovechances"] = [0.0,1.0,1.0,1.0,1.0]

#     flee.SimulationSettings.move_rules["FloodForecaster"] = True
#     flee.SimulationSettings.move_rules["FloodForecasterTimescale"] = 2 # 1 = 1 day, 2 = 2 days, etc. 0 = no memory
#     flee.SimulationSettings.move_rules["FloodForecasterEndTime"] = 6 #The forcast data only extends this many days into the simulation. Default value should be (simulation length - flood forecaster timesale).
#     flee.SimulationSettings.move_rules["FloodForecasterWeights"] = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.1,0.3, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0] # weights for each day the flood forecaster. 1 = max importance, 0.0 = no importance. First value is today. 
#     flee.SimulationSettings.move_rules["FloodAwarenessWeights"] = [0.0,0.5,1.0] #low, medium, high awareness or ability to adaptat to flooding (0.0 = no awareness, 1.0 = high awareness)  
    
#     # Set simulation ecosystem and input geography
#     e = flee.Ecosystem()
#     ig = InputGeography.InputGeography()

#     #Read test data files:
#     ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data", "test_input_csv/locations.csv"))
#     ig.ReadLinksFromCSV(csv_name=os.path.join("test_data", "test_input_csv/routes.csv"))
#     ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data", "test_input_csv/closures.csv"))
#     ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data","test_input_csv","flood_level.csv"))
#     ig.ReadAttributeInputCSV("forecast_flood_levels", "int", os.path.join("test_data","test_input_csv","flood_level.csv"))
#     ig.ReadAttributeInputCSV("flood_awareness", "int", os.path.join("test_data","test_input_csv","demographics_floodawareness.csv"))


#     #Set the simulation length
#     end_time = 11

#     #Store input geography in the ecosystem
#     e, lm = ig.StoreInputGeographyInEcosystem(e=e)


#     #Add agents to the simulation in the towns
#     e.addAgent(location=lm["C"], attributes={})
#     e.addAgent(location=lm["C2"], attributes={})


#     for t in range(0, end_time):
#         if t == 0:
#             print("Agent 0 location:",e.agents[0].location.name)
#             print("Agent 0 attributes:",e.agents[0].attributes)

#         e.evolve()

#     print("Test successful! Flood awareness correctly set. ")




if __name__ == "__main__":
    test_read_flood_csv()
    test_flood_level_location_attribute()
    test_flood_forecaster()
    test_agent_flood_awareness()
    pass
