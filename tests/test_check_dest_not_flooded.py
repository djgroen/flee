# LAURA
# Delete entirely if not used. 


# import os #used by inputgeography
# from flee import flee
# from flee import InputGeography

# """
# Testing check destionation is not flooded (check_dest_not_flooded) for DFlee.
# Utilises the dflee_test input files.
# """


# def test_check_dest_not_flooded():
#     """
#     Summary: 
#         Test check destination is not flooded (check_dest_not_flooded) for DFlee.
#     """

#     #Simulation legnth
#     end_time = 11 #days

#     flee.SimulationSettings.set_end_time(end_time)

#     #Read empty simulation settings file 
#     flee.SimulationSettings.ReadFromYML("empty.yml")

#     #Create ecosystem
#     e = flee.Ecosystem()

#     #Create input geography
#     ig = InputGeography.InputGeography()

    
    

#     #These values are normally specified in simsetting.yml

#     #Spawning rules
#     flee.SimulationSettings.spawn_rules["flood_driven_spawning"] = True
#     flee.SimulationSettings.spawn_rules["flood_zone_spawning_only"] = True
#     flee.SimulationSettings.spawn_rules["conflict_zone_spawning_only"] = False
#     flee.SimulationSettings.spawn_rules["flood_spawn_mode"] = "pop_ratio"
#     flee.SimulationSettings.spawn_rules["displaced_per_flood_day"] = [0.0,0.1,0.2,0.5,0.9]

#     #Move rules
#     flee.SimulationSettings.move_rules["FloodForecaster"] = True
#     flee.SimulationSettings.move_rules["FloodRulesEnabled"] = True
#     flee.SimulationSettings.move_rules["FloodLocWeights"] = [0.0,1.0,1.0,1.0,1.0]
#     flee.SimulationSettings.move_rules["FloodMovechances"] = [0.0,1.0,1.0,1.0,1.0]
#     flee.SimulationSettings.move_rules["max_flood_level"] = 4
#     flee.SimulationSettings.move_rules["FloodForecasterTimescale"] = 5
#     flee.SimulationSettings.move_rules["FloodForecasterWeights"] = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3, 0.1, 0.0, 0.0]


#     #Read input geography (locations, routes, closures, flood levels) from csv files in test_data folder
#     ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data", "test_input_csv/locations.csv"))
#     ig.ReadLinksFromCSV(csv_name=os.path.join("test_data", "test_input_csv/routes.csv"))
#     ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data", "test_input_csv/closures.csv"))
#     ig.ReadAttributeInputCSV("flood_level", "int", os.path.join("test_data","test_input_csv/flood_level.csv"))

#     #Print flood levels
#     print(ig.attributes["flood_level"])

#     #Store input geography in ecosystem
#     e, lm = ig.StoreInputGeographyInEcosystem(e=e) #lm is a dictionary of locations in the ecosystem


#     # Insert refugee agents
#     new_refs = 10
#     for _ in range(0, new_refs):
#         e.addAgent(location=lm["A"], attributes={})

#     #Iterate over the simulation time steps
#     for t in range(0, end_time):

#         #Add new conflict zones
#         ig.AddNewConflictZones(e, t)

#         #Check the flood levels initially
#         if t == 0:
#             #Check the flood level of location A is 0 (not flooded)
#             assert lm["A"].attributes["flood_level"] == 0  #lm is a dictionary of locations in the ecosystem
#             #Check the flood level of location B is 1 (flooded) 
#             assert e.locations[1].attributes["flood_level"] == 1 #e.locations is a list of locations in the ecosystem, location 1 is the second location in the list (B)

#         # Propagate the model by one time step.
#         e.evolve()

#         print(lm["A"].attributes["flood_level"])
#         print(e.locations[1].attributes["flood_level"])

#         if t == 3:
#             #Check the flood level of the location is 1 (flooded)
#             assert lm["A"].attributes["flood_level"] == 1
#             #Check the flood level of the location is 3 (flooded)
#             assert e.locations[1].attributes["flood_level"] == 3
    
#     #Check the flood level of the location is 1 (flooded)
#     assert lm["A"].attributes["flood_level"] == 1
#     assert e.locations[1].attributes["flood_level"] == 1

#     #Check the simulation evolved to the end_time. Minus 1 as it starts at zero. 
#     assert t == end_time-1

   

        
#     #Test complete 
#     print("Test check_dest_not_flooded successful!")
  

# if __name__ == "__main__":
#     test_check_dest_not_flooded()
#     pass
