from flee import flee
from flee.datamanager import handle_refugee_data


def test_stay_close_to_home():
    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 100.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 100.0
    flee.SimulationSettings.move_rules["StayCloseToHome"] = True
    flee.SimulationSettings.move_rules["HomeDistancePower"] = 5.0

    end_time = 20
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", x=0.0, y=0.0, movechance=1.0, foreign=False)
    l2 = e.addLocation(name="B", x=1.0, y=1.0, movechance=1.0, foreign=False)
    l3 = e.addLocation(name="C", x=100.0, y=100.0, movechance=1.0, foreign=False)

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)
    e.linkUp(endpoint1="B", endpoint2="C", distance=100.0)

    # Insert refugee agents
    for _ in range(0, 100):
        e.addAgent(location=l1, attributes={})

    for t in range(0, end_time):
        # Propagate the model by one time step.
        e.evolve()

        print(
            t,
            l1.numAgents,
            l2.numAgents,
            l3.numAgents,
        )

    assert t == 19
    # With such a strong HomeDistancePower, not more than agent should reside in l3.
    assert l3.numAgents < 2


def test_scoring_foreign_weight():
    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["ForeignWeight"] = 0.0

    end_time = 10
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0, foreign=False)
    l2 = e.addLocation(name="B", movechance=0.0, foreign=False)
    l3 = e.addLocation(name="C", movechance=0.0, foreign=False)
    l4 = e.addLocation(name="D", movechance=0.0, foreign=True)

    e.linkUp(endpoint1="A", endpoint2="B", distance=834.0)
    e.linkUp(endpoint1="A", endpoint2="C", distance=1368.0)
    e.linkUp(endpoint1="A", endpoint2="D", distance=536.0)

    d = handle_refugee_data.RefugeeTable(
        csvformat="generic",
        data_directory="test_data",
        start_date="2010-01-01",
        data_layout="data_layout.csv",
    )

    for t in range(0, end_time):
        new_refs = d.get_new_refugees(day=t)

        # Insert refugee agents
        for _ in range(0, new_refs):
            e.addAgent(location=l1, attributes={})

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
    #Should be zero, as the foreign weight is set to zero.
    assert l4.numAgents == 0
    # 79 746 24601 14784 38188

    print("Test successful!")


def test_prune_routes():

    weights = [1,8,4,12]
    routes = ["A","B","C","D"]

    flee.moving.pruneRoutes(weights, routes)
    assert len(weights) == 2
    assert len(routes) == 2

    assert weights[1] == 4
    assert routes[1] == "C"


if __name__ == "__main__":
    test_stay_close_to_home()
    test_scoring_foreign_weight()
    test_prune_routes()
    pass
    
