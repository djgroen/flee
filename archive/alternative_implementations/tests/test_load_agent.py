from flee import flee, InputGeography
import os
"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_load_agent():
   
    ig = InputGeography.InputGeography()

    flee.SimulationSettings.ReadFromYML("empty.yml")

    csvname = os.path.join("test_data", "test_input_csv", "agents.csv")

    print("Testing basic data handling and simulation kernel.")
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=0.3)

    ig.ReadAgentsFromCSV(e, csvname)

    assert e.numAgents() == 1 
    # The agent in location A should be loaded.
    # The agent in location B should not be loaded, because B does not exist.

if __name__ == "__main__":
    test_load_agent()
