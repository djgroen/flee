from flee import flee
from flee.datamanager import handle_refugee_data

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_toy_escape():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0

    end_time = 10
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0)
    l2 = e.addLocation(name="B", movechance=0.0)
    l3 = e.addLocation(name="C", movechance=0.0)
    l4 = e.addLocation(name="D", movechance=0.0)

    e.linkUp(endpoint1="A", endpoint2="B", distance=834.0)
    e.linkUp(endpoint1="A", endpoint2="C", distance=1368.0)
    e.linkUp(endpoint1="A", endpoint2="D", distance=536.0)

    d = handle_refugee_data.RefugeeTable(
        csvformat="generic",
        data_directory="../test_data",
        start_date="2010-01-01",
        data_layout="data_layout.csv",
    )

    for t in range(0, end_time):
        new_refs = d.get_new_refugees(day=t)

        # Insert refugee agents
        for _ in range(0, new_refs):
            e.addAgent(location=l1, age=20, gender="", attributes={})

        # Propagate the model by one time step.
        e.evolve()

        print(
            t,
            l1.numAgents + l2.numAgents + l3.numAgents + l4.numAgents,
            l1.numAgents,
            l2.numAgents,
            l3.numAgents,
            l4.numAgents,
            new_refs
        )

    assert t == 9
    # This includes refugee counts from Fassala as well
    assert l1.numAgents + l2.numAgents + l3.numAgents + l4.numAgents == 635
    # 79 746 24601 14784 38188

    print("Test successful!")


if __name__ == "__main__":
    test_toy_escape()
