from flee import flee

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_tiny_closure():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.MinMoveSpeed = 10.0
    flee.SimulationSettings.MaxMoveSpeed = 10.0

    end_time = 100
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0)
    l2 = e.addLocation(name="B", movechance=0.0)

    e.linkUp(endpoint1="A", endpoint2="B", distance=5.0)

    for t in range(0, end_time):
        # Insert refugee agents
        e.addAgent(location=l1, age=20, gender="", attributes={})

        # Propagate the model by one time step.
        e.evolve()

        if t == 2:
            assert e.close_location(location_name="B")

        print("t = {}, l1.numAgents = {}, l2.numAgents = {}".format(t, l1.numAgents, l2.numAgents))
        e.printComplete()

    assert t == 99
    # Location is closed after 3 steps, refugees underway will still arrive
    # but others are blocked.
    assert l2.numAgents == 3
    assert l1.numAgents == 97

    print("Test successful!")


if __name__ == "__main__":
    test_tiny_closure()
