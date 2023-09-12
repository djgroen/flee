from flee import flee, datamanager

"""
Testing flood drive spawning for DFlee.
"""


def test_flood_driven_spawning():

    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["ForeignWeight"] = 0.0

    #These values are normally specified in simsetting.yml
    flee.SimulationSettings.spawn_rules["flood_driven_spawning"] = True
    flee.SimulationSettings.spawn_rules["flood_spawn_mode"] = "constant"
    flee.SimulationSettings.spawn_rules["displaced_per_flood_day"] = [0,100,200,300,400]


    end_time = 10
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=0.0, foreign=False, attributes={"flood_level": 1})
    l2 = e.addLocation(name="B", movechance=0.0, foreign=True, attributes={"flood_level": 0})
    l1.conflict = 1.0

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)

    for t in range(0, end_time):

        new_refs,refugees_raw,refugee_debt = flee.spawning.spawn_daily_displaced(e,t,None)
        print("new agents: {}".format(new_refs))

        flee.spawning.refresh_spawn_weights(e)

        # Propagate the model by one time step.
        e.evolve()

    assert t == 9

    # All agents should be spawned in l1 and not be in l2.
    assert len(e.agents) == 1000
    assert l1.numAgents == 1000


if __name__ == "__main__":
    test_conflict_driven_spawning()
