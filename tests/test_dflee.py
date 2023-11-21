import os
from flee import flee
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

    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    end_time = 11

    new_refs = 1

    # Insert refugee agents
    for _ in range(0, new_refs):
        e.addAgent(location=lm["A"], attributes={})

    for t in range(0, end_time):

        ig.AddNewConflictZones(e, t)

        # Check the floof levels at t=0
        if t == 0:
            assert lm["A"].attributes["flood_level"] == 0
            assert e.locations[1].attributes["flood_level"] == 1

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
    
    #Check the flood levels at the final time step
    assert lm["A"].attributes["flood_level"] == 1
    assert e.locations[1].attributes["flood_level"] == 1

    print("Test successful!! Flood attributes correctly set.")


if __name__ == "__main__":
    test_read_flood_csv()
    test_flood_level_location_attribute()
    pass
