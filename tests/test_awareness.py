from flee import flee

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_awareness():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.MinMoveSpeed = 5000.0
    flee.SimulationSettings.MaxMoveSpeed = 5000.0
    flee.SimulationSettings.MaxWalkSpeed = 5000.0

    # end_time = 10
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=0.3)
    _ = e.addLocation(name="B", movechance=0.3)
    _ = e.addLocation(name="C", movechance=0.3)
    _ = e.addLocation(name="D", movechance=0.3)
    _ = e.addLocation(name="C2", movechance=0.3)
    _ = e.addLocation(name="D2", movechance=0.3)
    _ = e.addLocation(name="D3", location_type="camp")
    # l2 = e.addLocation(name="B", movechance=0.3)
    # l3 = e.addLocation(name="C", movechance=0.3)
    # l4 = e.addLocation(name="D", movechance=0.3)
    # l5 = e.addLocation(name="C2", movechance=0.3)
    # l6 = e.addLocation(name="D2", movechance=0.3)
    # l7 = e.addLocation(name="D3", location_type="camp")

    e.linkUp(endpoint1="A", endpoint2="B", distance=834.0)
    e.linkUp(endpoint1="A", endpoint2="C", distance=834.0)
    e.linkUp(endpoint1="A", endpoint2="D", distance=834.0)
    e.linkUp(endpoint1="C", endpoint2="C2", distance=834.0)
    e.linkUp(endpoint1="C", endpoint2="D2", distance=834.0)
    e.linkUp(endpoint1="D", endpoint2="D2", distance=834.0)
    e.linkUp(endpoint1="D2", endpoint2="D3", distance=834.0)
    e.linkUp(endpoint1="C2", endpoint2="D3", distance=834.0)

    e.addAgent(location=l1)

    e.agents[0].selectRouteRuleset2(time=0, debug=True)

    # for t in range(0,end_time):

    # Propagate the model by one time step.
    #  e.evolve()

    print("Test successful!")


if __name__ == "__main__":
    test_awareness()
