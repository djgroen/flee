from flee import flee

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_1_agent():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxCrossingSpeed"] = 42.0

    end_time = 30
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=0.3)
    l2 = e.addLocation(name="B", movechance=0.0)
    l3 = e.addLocation(name="C", movechance=0.0)
    l4 = e.addLocation(name="D", movechance=0.0)

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    e.linkUp(endpoint1="A", endpoint2="C", distance=100.0)
    e.linkUp(endpoint1="A", endpoint2="D", distance=100.0)

    new_refs = 1

    # Insert refugee agents
    for _ in range(0, new_refs):
        e.addAgent(location=l1, attributes={})

    for t in range(0, end_time):

        # Propagate the model by one time step.
        e.evolve()

        print("Our single agent is at", e.agents[0].location.name)

        print(
            t,
            l1.numAgents + l2.numAgents + l3.numAgents + l4.numAgents,
            l1.numAgents,
            l2.numAgents,
            l3.numAgents,
            l4.numAgents,
        )

    assert t == end_time - 1
    assert l1.numAgents + l2.numAgents + l3.numAgents + l4.numAgents == 1

    print("Test successful!")


if __name__ == "__main__":
    test_1_agent()
