from flee import flee, datamanager

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""


def test_conflict_driven_spawning():
    print("Testing basic data handling and simulation kernel.")

    flee.SimulationSettings.ReadFromYML("empty.yml")

    flee.SimulationSettings.move_rules["MaxMoveSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["MaxWalkSpeed"] = 5000.0
    flee.SimulationSettings.move_rules["ForeignWeight"] = 0.0
    flee.SimulationSettings.spawn_rules["conflict_driven_spawning"] = True
    flee.SimulationSettings.spawn_rules["conflict_spawn_mode"] = "constant"
    flee.SimulationSettings.spawn_rules["displaced_per_conflict_day"] = 100


    end_time = 10
    e = flee.Ecosystem()

    l1 = e.addLocation(name="A", movechance=1.0, foreign=False)
    l2 = e.addLocation(name="B", movechance=0.0, foreign=True)
    l1.conflict = True

    e.linkUp(endpoint1="A", endpoint2="B", distance=100.0)

    for t in range(0, end_time):

        new_refs,refugees_raw,refugee_debt = flee.spawning.spawn_daily_displaced(e,t,None)
        print("new agents: {}".format(new_refs))

        flee.spawning.refresh_spawn_weights(e)

        # Propagate the model by one time step.
        e.evolve()

    assert t == 9

    # All agents should have reached l2, and be deactivated.
    assert len(e.agents) == 1000

    print("Test successful!")


if __name__ == "__main__":
    test_conflict_driven_spawning()
