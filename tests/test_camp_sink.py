from flee import flee

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_camp_sink():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["ForeignWeight"] = 0.0
    flee.SimulationSettings.spawn_rules["camps_are_sinks"] = True

    end_time = 10
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0, foreign=False)
    l2 = e.addLocation(name="B", movechance=0.0, foreign=True)
    l2.setAttribute("deactivation_probability", 1.0)

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    # Insert refugee agents
    for _ in range(0, 100):
        e.addAgent(location=l1, attributes={})


    for t in range(0, end_time):

        # Propagate the model by one time step.
        e.evolve()

    assert t == 9

    # All agents should have reached l2, and be deactivated.
    for a in e.agents:
        assert a.location is None

    print("Test successful!")


if __name__ == "__main__":
    test_scoring_foreign_weight()
